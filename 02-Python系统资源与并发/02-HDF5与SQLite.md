# 02 HDF5 与 SQLite：大数组与关系表格的存储

## 学习目标

- 会用 h5py 创建文件、组、数据集与属性，用路径组织层次结构；
- 会设计可扩展数据集（maxshape + resize），实现分批追加写入；
- 会设置 chunks 与 gzip 压缩，理解分块与压缩对读写的意义；
- 会用 sqlite3 标准库建表、参数化插入、条件查询与聚合；
- 会用事务与索引，会写 CSV 批量导入脚本（配合 argparse）；
- 能根据数据形态在 HDF5 与 SQLite 之间做出选择，并说清理由。

## 前置知识

- 阶段 02 的 [01-NumPy与Pandas.md](./01-NumPy与Pandas.md)：ndarray、CSV 读写；
- 阶段 01：函数、with 语句、异常处理、argparse、logging 基础。

## 建议用时

2 周，每周 6~10 小时。

## 正文

### 2.1 为什么要用专门的存储格式

CSV/JSON 人可读、通用，但文件大了读取慢、没有类型、无法只读一部分；.npy 读写快，却只能装单个数组，
没有元数据与层次结构。实验数据大致分两类，各有一种更合适的本地格式：

- 数组型数据（多通道波形、图像、参数扫描网格）→ HDF5：层次路径、按块读写、压缩、属性；
- 表格型数据（实验记录、样品清单、运行台账）→ SQLite：SQL 查询、事务、索引、单文件。

两者都只需一个文件，方便拷贝和归档；本课先分别学会，最后讲怎么选。

**常见错误**

- 什么数据都存 CSV：几百 MB 后每次分析都浪费几分钟。
- 在 HDF5 上手工遍历所有组来找「温度 300 K 的记录」——这类条件筛选是 SQLite 的活。

### 2.2 h5py：文件、组、数据集与属性

```python
import h5py
import numpy as np

rng = np.random.default_rng(42)
waveform = rng.normal(size=(8, 2000)) * 1e-3    # 8 通道波形，单位 V

# "w"：新建/覆盖；with 块结束自动关闭文件
with h5py.File("experiment.h5", "w") as f:
    dset = f.create_dataset("waveform", data=waveform)
    dset.attrs["unit"] = "V"                    # 属性：给数据贴元数据
    dset.attrs["sample_rate_hz"] = 10000

# "a"：追加；用组组织层次：日期/样品/运行编号/数据集
with h5py.File("experiment.h5", "a") as f:
    run = f.create_group("2026-09-19/S01/run001")
    run.create_dataset("repeat", data=waveform)
    run.attrs["operator"] = "wang"

# "r"：只读；可以只读取需要的一小段
with h5py.File("experiment.h5", "r") as f:
    f.visit(print)                        # 按名称顺序打印所有路径
    # 2026-09-19
    # 2026-09-19/S01/run001/repeat
    # waveform
    print(sorted(f.keys()))               # ['2026-09-19', 'waveform']
    print(f["waveform"][0, :3].round(6))  # 例如 [-0.000418 -0.000128  0.001273]
    print(f["waveform"].attrs["unit"])    # V
    print(f["2026-09-19/S01/run001"].attrs["operator"])   # wang
```

**常见错误**

- 忘记 with/close 导致文件句柄不释放：再次以写模式打开会报文件锁错误。
- 用 "w" 打开已有文件会清空全部数据：日常追加必须用 "a"；路径写错报 KeyError，先 `visit` 查看。
- 同名 `create_dataset` 报错：先 `if "name" in f:` 判断，或 `del f["name"]` 后重建。

### 2.3 追加写入：可扩展数据集

采集是分批到来的，先建一个 0 行、可扩展的数据集，每批到齐后追加：

```python
import h5py
import numpy as np

rng = np.random.default_rng(42)

with h5py.File("stream.h5", "w") as f:
    # shape=(0, 8)：初始 0 行；maxshape=(None, 8)：第 0 维可无限增长；必须分块
    dset = f.create_dataset("samples", shape=(0, 8), maxshape=(None, 8),
                            dtype="float64", chunks=(1024, 8))
    for batch in range(3):
        block = rng.normal(size=(500, 8))
        old_n = dset.shape[0]
        dset.resize(old_n + block.shape[0], axis=0)   # 扩展第 0 维
        dset[old_n:] = block                          # 写入新块
        print(batch, dset.shape)
# 0 (500, 8)
# 1 (1000, 8)
# 2 (1500, 8)

with h5py.File("stream.h5", "r") as f:
    d = f["samples"]
    print(d.shape)               # (1500, 8)
    print(d[-1, :3].round(4))    # 例如 [-0.0005 -0.0015 -0.0005]
```

**常见错误**

- 忘记 maxshape：`resize` 会报错（只有可扩展的分块数据集才能改形状）。
- 每写一行 resize 一次：元数据操作太多、极慢；按批（几百到几万行）扩展。
- 多进程同时写同一个 HDF5 文件：同一文件同一时刻只应由一个写入者写入。

### 2.4 分块与压缩

chunk 是 HDF5 内部读写的最小单位；compression 在写入时压缩每个 chunk，二者在创建数据集时设定。

```python
import h5py
import numpy as np
import os

rng = np.random.default_rng(42)

# 200 通道 × 20000 点：约 32 MB
signal = np.sin(2 * np.pi * 5 * np.linspace(0, 10, 20_000)) \
         + 0.05 * rng.normal(size=(200, 20_000))

with h5py.File("raw.h5", "w") as f:
    f.create_dataset("signal", data=signal)

with h5py.File("compressed.h5", "w") as f:
    f.create_dataset("signal", data=signal, compression="gzip",
                     compression_opts=6, chunks=(50, 1000))

print(f"raw.h5        {os.path.getsize('raw.h5') / 1e6:6.1f} MB")         # 例如 32.0 MB
print(f"compressed.h5 {os.path.getsize('compressed.h5') / 1e6:6.1f} MB")  # 例如 12.5 MB

with h5py.File("compressed.h5", "r") as f:
    d = f["signal"]
    print(d.chunks, d.compression, d.compression_opts)   # (50, 1000) gzip 6
    print(d[0, 1000:1005].round(4))   # 只解压涉及的分块，不用读整个数据集
```

平滑信号压缩率高；换成纯噪声几乎压不动——压缩率取决于数据内容，不取决于参数。

**常见错误**

- chunk 太大（几十 MB）或太小（几十字节）都拖慢性能：目标是每个 chunk 几十 KB 到几 MB。
- 压缩参数只在创建时生效：已有数据集改不了，需要重建或复制。
- 分块形状与访问方式不匹配：总是按行批读，就把行方向的 chunk 设大一些。

### 2.5 sqlite3 基础：连接、建表、插入、查询

```python
import sqlite3

# 文件不存在会自动创建：整个数据库就是一个 .db 文件
conn = sqlite3.connect("lab.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS measurement (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sample      TEXT    NOT NULL,
    temperature REAL    NOT NULL,
    voltage     REAL,
    measured_at TEXT    DEFAULT (datetime('now'))
)
""")

# ? 是占位符，值放在第二个参数里（参数化查询，2.6 展开讲）
conn.execute(
    "INSERT INTO measurement (sample, temperature, voltage) VALUES (?, ?, ?)",
    ("S01", 290.0, 1.2501),
)
conn.commit()

rows = conn.execute(
    "SELECT id, sample, temperature, voltage FROM measurement"
).fetchall()
print(rows)     # [(1, 'S01', 290.0, 1.2501)]

conn.close()
```

**常见错误**

- 忘记 `commit()`：数据可能没落盘；配合 `with conn:` 可以自动提交/回滚（2.6）。
- 重复执行脚本时表已存在报错：建表语句加 `IF NOT EXISTS`。

### 2.6 参数化查询、批量插入与事务

```python
import sqlite3

conn = sqlite3.connect("lab.db")

records = [
    ("S01", 300.0, 1.2593),
    ("S02", 290.0, 1.2450),
    ("S02", 300.0, 1.2541),
    ("S03", 290.0, 1.2401),
]
conn.executemany(
    "INSERT INTO measurement (sample, temperature, voltage) VALUES (?, ?, ?)",
    records,
)
conn.commit()

# with conn：块内操作要么全部生效，要么出错时全部回滚
with conn:
    conn.execute("UPDATE measurement SET voltage = ? WHERE sample = ?",
                 (1.2600, "S01"))

rows = conn.execute(
    "SELECT sample, temperature, voltage FROM measurement "
    "WHERE sample = ? AND temperature > ?",
    ("S02", 295.0),
).fetchall()
print(rows)     # [('S02', 300.0, 1.2541)]

conn.close()
```

**常见错误**

- 用 f-string 拼 SQL：注入风险，名称里有单引号就出错；永远用 `?` 占位符。
- 逐行 `execute` 插入十几万行：应 `executemany` 并放在一次事务（`with conn:`）里。
- numpy 整数直接绑定可能报绑定错误：插入前用 `int()` / `float()` 转成 Python 标量。

### 2.7 索引与聚合查询

```python
import sqlite3

conn = sqlite3.connect("lab.db")

# 经常按 (sample, temperature) 过滤，就为这两列建复合索引
conn.execute("CREATE INDEX IF NOT EXISTS idx_measurement_sample "
             "ON measurement (sample, temperature)")
conn.commit()

# 聚合：每组记录数、均值、极值
rows = conn.execute("""
    SELECT sample, temperature,
           COUNT(*)               AS n,
           ROUND(AVG(voltage), 6) AS v_mean,
           ROUND(MIN(voltage), 6) AS v_min,
           ROUND(MAX(voltage), 6) AS v_max
    FROM measurement
    GROUP BY sample, temperature
    ORDER BY sample, temperature
""").fetchall()
for row in rows:
    print(row)
# 依次运行 2.5、2.6 后的前两行例如：
# ('S01', 290.0, 1, 1.26, 1.26, 1.26)
# ('S01', 300.0, 1, 1.26, 1.26, 1.26)

top = conn.execute(
    "SELECT sample, voltage FROM measurement ORDER BY voltage DESC LIMIT 3"
).fetchall()
print(top)      # 例如 [('S01', 1.26), ('S01', 1.26), ('S02', 1.2541)]

conn.close()
```

索引像书的目录，能加速 WHERE/ORDER BY 查询，代价是插入变慢、文件变大，因此只给高频查询的条件建。

**常见错误**

- 给每一列都建索引：写入变慢、数据库变大，收益很小。
- 聚合时 SELECT 了没有分组的列：SQLite 可能不报错，但结果含义不确定。

### 2.8 从 CSV 批量导入（脚本）

把 01 文件里生成的 records.csv（列：sample、temperature、voltage、uncertainty）导入 SQLite：

```python
import argparse
import csv
import sqlite3

def import_csv(conn, csv_path):
    """读取 CSV 并批量写入 measurement 表，返回导入行数。"""
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)          # 第一行作为列名
        rows = []
        for r in reader:
            if r["voltage"] in ("", None):   # 空值跳过（也可以置 None）
                continue
            rows.append((r["sample"], float(r["temperature"]), float(r["voltage"])))
    with conn:                               # 一次事务写完，失败自动回滚
        conn.executemany(
            "INSERT INTO measurement (sample, temperature, voltage) VALUES (?, ?, ?)",
            rows,
        )
    return len(rows)

def main():
    parser = argparse.ArgumentParser(description="把实验记录 CSV 导入 SQLite")
    parser.add_argument("csv_path", help="待导入的 CSV 文件")
    parser.add_argument("--db", default="lab.db", help="目标数据库文件")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)          # 表沿用 2.5 的建表语句创建
    n = import_csv(conn, args.csv_path)
    print(f"导入 {n} 行到 {args.db}")
    conn.close()

if __name__ == "__main__":
    main()
```

运行：`python import_records.py records.csv --db lab.db`（argparse 的完整写法见阶段 01）。

**常见错误**

- 有表头却用 `csv.reader`：第一行被当数据，之后 `float("temperature")` 报错。
- 数值列里有空串或 "NA" 占位：`float()` 抛 ValueError，要先判断或转换。
- 脚本重复运行产生重复数据：先 `DELETE FROM measurement`，或给关键列加 UNIQUE 约束。

### 2.9 对比与选择

| 维度 | HDF5（h5py） | SQLite（sqlite3） |
| --- | --- | --- |
| 数据形态 | 多维数组（波形、图像、网格） | 行记录（台账、样品清单、参数） |
| 查询方式 | 路径 + 切片，部分读取 | SQL：条件、排序、聚合、JOIN |
| 元数据 | 层次结构 + 丰富属性 | 表结构 + 附加表 |
| 压缩 | 内置分块压缩 | 无内置，依赖文件系统 |
| 写入并发 | 同一文件同一时刻只能一个写入者 | 事务支持，多读单写可控 |
| 典型体量 | MB ~ TB | KB ~ GB |
| 是否标准库 | 否，需 pip 安装 h5py | 是，Python 自带 |

选择口诀：**原始数组进 HDF5，记录表格进 SQLite**。两者也能组合：SQLite 存测量记录和
「HDF5 文件路径 + 内部路径」，波形本体留在 HDF5 里。

```python
import h5py
import sqlite3

def load_waveform(conn, row_id):
    """按 measurement.id 读取对应的 HDF5 波形，记录不存在时返回 None。"""
    row = conn.execute("SELECT h5_path FROM measurement WHERE id = ?",
                       (row_id,)).fetchone()   # h5_path 形如 "runs.h5:/.../waveform"
    if row is None or row[0] is None:
        return None
    file_path, internal_path = row[0].split(":", 1)
    with h5py.File(file_path, "r") as f:
        return f[internal_path][:]     # [:] 把数据读进内存（ndarray）
```

**常见错误**

- 把大数组当 BLOB 整块塞进 SQLite：失去分块与压缩优势（很小的块可以接受）。
- 在 HDF5 里存几十万条小记录再想按条件筛选：应该用 SQLite。

## 练习

1. （基础）把 4 通道 × 10000 点波形写入 `practice.h5` 的 `/run001/waveform`，给数据集写属性 `unit="V"`、`sample_rate_hz=50000`，给 `/run001` 组写属性 `date="2026-09-19"`；重新打开文件，用 `visit` 打印全部路径与属性，并只读取第 0 通道最后 100 个点。
   提示：`create_group`、`create_dataset`、`attrs`，部分读取用切片；验收：`visit` 至少输出 2 条路径，属性读回一致，第 0 通道最后 100 点的 shape 为 `(100,)`。

2. （基础）建一个 `shape=(0, 4)`、`maxshape=(None, 4)` 的数据集，分 5 批各追加 300 行（每批用不同固定种子生成），记录每批起始行号；写完后验证 shape 为 `(1500, 4)`，并抽查第 3 批第一行与原数据一致。
   提示：`resize` + 切片赋值，把每批数据在内存里留一份用于核对；验收：shape 正确、抽查一致，能说出去掉 maxshape 后报什么错。

3. （中级）为实验台账建表 `run_log(id, sample, temperature, voltage, note)`，用 `executemany` 插入至少 20 行，完成三个查询并打印：某样品全部记录按 temperature 排序；每个样品的平均电压与记录数；温度在 295~305 K 的记录按电压降序取前 3 条。
   提示：参数化查询、GROUP BY、ORDER BY、LIMIT；验收：所有查询使用 `?` 占位符，抽查 1~2 个分组与手算一致。

4. （中级）给 2.8 的导入函数加 argparse 参数：`csv_path`、`--db`、`--reset`（先清空表再导入）；对 5 万行以上数据，用 `time.perf_counter` 对比建索引前后按 (sample, temperature) 查询的耗时，并用 `EXPLAIN QUERY PLAN` 观察是否走索引。
   提示：先用脚本批量生成大 CSV，索引用 `CREATE INDEX`；验收：`--reset` 可重复运行不产生重复数据，记录建索引前后两个耗时并解释差异来源。

5. （综合）实现 `load_waveform(conn, row_id)`：从 SQLite 的 `measurement.h5_path`（形如 `runs.h5:/2026-09-19/S01/run001/waveform`）读出波形并返回 ndarray；记录不存在或文件缺失时返回 None 并打印提示；用正常、缺记录、缺文件三个用例验证。
   提示：`split(":", 1)`，`with h5py.File(...)`，返回前用 `[:]` 取出数据；验收：三个用例都符合预期，只用函数实现，缺失场景不抛出未处理异常。

## 自测清单

- [ ] 会用 `with h5py.File` 的 "w"/"a"/"r" 三种模式，知道 "w" 会清空已有文件
- [ ] 会用组和路径组织层次结构，会 `visit`/`keys` 查看全貌
- [ ] 会用 maxshape + resize 分批追加，理解为什么必须分块
- [ ] 会设置 chunks 与 gzip 压缩，能说出二者对性能的影响
- [ ] 会用 sqlite3 建表、executemany 插入、fetchall 查询
- [ ] 会用 `?` 参数化查询，知道为什么不能拼字符串
- [ ] 会用 `with conn:` / `commit()` 控制事务，出错会回滚
- [ ] 会建索引，会用 GROUP BY/COUNT/AVG/MIN/MAX 做聚合
- [ ] 会写 CSV→SQLite 导入脚本，并用 argparse 传参
- [ ] 能说出 HDF5 与 SQLite 各自适合的数据形态，并给出理由

## 参考资料

- h5py 快速入门：https://docs.h5py.org/en/stable/quick.html
- h5py 数据集（chunks 与 Compression）：https://docs.h5py.org/en/stable/high/dataset.html
- h5py 组与属性：https://docs.h5py.org/en/stable/high/group.html
- Python sqlite3 文档：https://docs.python.org/3/library/sqlite3.html
- Python csv 文档：https://docs.python.org/3/library/csv.html
