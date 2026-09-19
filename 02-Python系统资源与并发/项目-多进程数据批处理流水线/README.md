# 项目：多进程数据批处理流水线

## 背景与目标

实验室的自动采集程序每天产出几十到几百个 CSV：每次 R-T 扫描一个文件，
每行是时间、温度、电压、电流。分析前需要统一完成：解析、坏行清理、统计、
入库、归档与报告。串行处理 60 个文件要十几秒，数据量再涨就会浪费大量时间。

本项目把阶段 02 的知识串起来，写一条「发现文件 -> 并行解析与统计 ->
写 SQLite + HDF5 -> 生成报告」的流水线，并用进度条与日志让长时间运行可观察。

学习目标（对应本阶段各课）：

- 用 ProcessPoolExecutor 并行处理 CPU 密集的解析与统计任务，控制进程数
- 用 tqdm 显示进度，用 logging 记录错误与摘要，异常隔离到单个文件
- 理解 pickle 边界：worker 只回传小统计结果与数组，不回传文件对象/连接
- 用标准库 sqlite3 入库，用 h5py 保存逐点数据（阶段 02 其他课内容，直接用）
- 用 argparse 组织 CLI，用 pytest（函数式）测试纯函数
- 全程函数式写法，不使用 class（阶段 05 再学）

## 流程

```text
sample-data/*.csv
      |
      v
[1] discover_files            发现并排序 CSV 文件
      |
      v
[2] parse_file (进程池并行)    逐行读取、跳过坏行、计算文件级统计
      |                        每个 worker 返回统计字典 + 逐点数组
      v
[3] aggregate                  合并统计：总点数、加权温度均值、极值
      |
      v
[4] write_sqlite  write_hdf5   统计入 runs 表；逐点数组写入 /runs/<文件名>/
      |
      v
[5] build_report               生成 report.csv 与文本摘要
      |
      v
进度条（tqdm）+ 日志（logging，控制台与文件）
```

## MVP（必须完成）

1. **发现文件**：`discover_files(root)` 返回排序后的 `list[Path]`，
   支持 `--pattern`（默认 `*.csv`），无文件时返回码 1 并写 ERROR 日志。
2. **并行解析**：用 `ProcessPoolExecutor` 调用 `parse_file`；
   `--workers 0` 表示 `max(1, os.cpu_count() - 1)`；必须写在
   `if __name__ == "__main__"` 保护的调用链里。
3. **坏行与坏文件**：坏行（温度/时间转不成 float、列缺失）直接跳过并计数；
   整个文件失败（不存在、无权限、空文件）记入错误列表，不影响其他文件。
4. **汇总**：`aggregate(rows)` 输出文件数、成功/失败数、总点数、
   按点数加权的温度均值与全局极值。
5. **入库**：SQLite 表 `runs`，重复运行用 `INSERT OR REPLACE`；
   HDF5 保存每个文件的 `time_s` 与 `temperature_K` 数组，外加 summary 属性。
6. **报告**：`report.csv` 一行一个文件；标准输出与日志给出总体摘要。
7. **可观察**：主进程用 tqdm 更新进度；日志同时写控制台与 `logs/pipeline.log`，
   失败文件逐条 WARNING。
8. **CLI**：参数见下，`--verbose` 打开 DEBUG。

### CLI 设计

```text
用法: python starter/pipeline.py --input 数据目录 [选项]

必选参数:
  --input DIR       数据目录（含 CSV）

可选参数:
  --pattern GLOB    文件模式，默认 *.csv
  --workers N       进程数，0 表示按 CPU 核数自动（默认 0）
  --db PATH         SQLite 输出，默认 output/runs.db
  --hdf5 PATH       HDF5 输出，默认 output/runs.h5
  --report PATH     CSV 报告，默认 output/report.csv
  --verbose, -v     输出 DEBUG 日志
```

### 数据与输出格式约定

输入 CSV（`starter/gen_data.py` 生成，温度列可能为空行）：

```csv
time_s,temperature_K,voltage_V,current_A
0.0,300.000,3.601e-01,0.001
0.5,299.955,3.598e-01,0.001
```

SQLite `runs` 表：

```sql
CREATE TABLE IF NOT EXISTS runs (
    file TEXT PRIMARY KEY,
    count INTEGER,
    temp_mean REAL,
    temp_min REAL,
    temp_max REAL,
    time_min REAL,
    time_max REAL
);
```

HDF5 结构：

```text
/                       (根)
├── summary             各文件统计（可选，属性或数据集）
└── runs/
    ├── run_001/
    │   ├── time_s          float64 一维数组
    │   └── temperature_K   float64 一维数组
    └── run_002/...
```

`report.csv` 每行一个文件：

```csv
file,count,temp_mean,temp_min,temp_max,status
run_001.csv,5000,188.421,77.012,300.000,ok
run_017.csv,0,,,,empty
```

字段可以微调，但必须包含：文件名、点数、均值、极值、状态（ok/empty/error）。

## 里程碑

| 里程碑 | 内容 | 完成标志 |
| --- | --- | --- |
| M1 单进程跑通 | 实现 discover_files、parse_file、aggregate、report，串行处理 10 个文件 | 命令行输出统计摘要，report.csv 字段齐全，坏行被跳过 |
| M2 并行化 | 接入 ProcessPoolExecutor、tqdm、错误隔离与 `--workers` | 60 个文件明显快于串行，进度条正常，坏文件只影响自己 |
| M3 入库 | 实现 write_sqlite 与 write_hdf5，处理重复运行与目录创建 | 用 `sqlite3` 命令能查到 runs 行数；h5py 能列出 `/runs` 下的组 |
| M4 测试与收尾 | pytest 覆盖纯函数、README 更新、打 tag `v0.1.0` | `pytest -q` 全绿，文档与代码一致 |
| M5 进阶（可选） | 断点续跑（跳过已入库文件）、psutil 资源采样日志、增量报告 | 中断后重跑不重复处理，日志里有资源曲线数据 |

建议每个里程碑一个 Git 提交或分支，完成后打 tag。

## 建议目录结构

```text
multiprocess-pipeline/
├── README.md
├── requirements.txt              # numpy pandas h5py tqdm pytest
├── starter/
│   ├── gen_data.py               # 生成模拟数据（已提供）
│   └── pipeline.py               # 主程序骨架（已提供，补全 TODO）
├── tests/
│   └── test_pipeline.py          # 测试骨架（已提供，补全 TODO）
├── sample-data/                  # 生成的 CSV（gitignore）
├── output/                       # runs.db / runs.h5 / report.csv（gitignore）
└── logs/                         # pipeline.log（gitignore）
```

## 运行方法

```bash
cd ~/projects/multiprocess-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt          # numpy pandas h5py tqdm pytest

# 1. 生成模拟数据：60 个文件，每个 5000 行，约 5% 坏行
python3 starter/gen_data.py --target sample-data --files 60 --rows 5000 \
    --seed 42 --bad-rate 0.02

# 2. 跑流水线（先用小数据试，再加 --workers）
python3 starter/pipeline.py --input sample-data --workers 8 -v

# 3. 查看结果
ls -lh output/
sqlite3 output/runs.db "SELECT COUNT(*), ROUND(AVG(temp_mean),2) FROM runs;"
python3 -c "import h5py; f=h5py.File('output/runs.h5'); print(list(f['runs'])[:3])"

# 4. 测试
pytest -q
```

## 技术约束

- 只使用阶段 00~02 的知识与工具：标准库 + numpy/pandas/h5py/tqdm/pytest
- 不使用 class / 面向对象写法，全部函数式；不使用 C、集群工具、CI
- 不使用 matplotlib
- 进程池只能出现在 `if __name__ == "__main__"` 保护的代码路径里
- worker 函数必须是模块顶层函数，参数与返回值必须可 pickle
- 不在子进程里写 SQLite / HDF5 / 报告；这些只在主进程做
- 不盲目开进程：默认 `os.cpu_count() - 1`，`--workers` 可覆盖
- 大文件处理要逐行读，避免一次性 `read()` 把内存吃满
- 输出目录不存在要自动创建；重复运行不允许报错（用 INSERT OR REPLACE）

## 验收标准

- [ ] `python starter/gen_data.py --help` 与 `pipeline.py --help` 参数说明完整
- [ ] `pipeline.py` 对 60 个样本文件跑通，退出码 0
- [ ] report.csv 行数等于输入文件数，含 ok/empty/error 状态
- [ ] 至少有一个文件包含坏行时，统计结果正确且进程不崩溃
- [ ] `--workers 0` 与 `--workers 4` 都能跑，且并行版明显快于串行版
- [ ] SQLite `runs` 表的行数与成功文件数一致，重复运行结果不翻倍
- [ ] HDF5 中每个成功文件都有 `time_s` 与 `temperature_K`，长度等于 count
- [ ] 日志含时间、级别、文件数与耗时摘要，失败文件有可定位信息
- [ ] `pytest -q` 全部通过（至少 8 个用例，覆盖发现/解析/汇总/入库）
- [ ] Git 提交记录清楚，至少打一个 tag

## 进阶功能（选做）

1. **断点续跑**：读取 SQLite 里已成功处理的文件名，跳过它们，只处理新增文件。
2. **资源采样**：后台用 psutil 每 2 秒记录 CPU/内存到 CSV，与本批处理的时间轴对齐。
3. **增量报告**：`--since` 只报告指定时间之后修改的文件。
4. **多目录输入**：`--input` 接受多个目录，统一汇总到一份报告。
5. **大文件分块**：对超大 CSV 使用 `csv.reader` 流式统计，报告里加分位数。

## 提示

- 先把 `parse_file`、`aggregate` 这类纯函数测透，再接入进程池；
  并行只是编排，逻辑错了一并行只会更乱
- 进程池报 `PicklingError` 时，先检查 worker 是否顶层函数、返回值有没有
  文件对象/连接
- 数据先用 10 个文件调试，确认无误再放大到几百个
- SQLite 与 HDF5 的连接只在主进程打开；子进程只做纯计算
- 注意 WSL2 的 IO 性能：数据放在 Linux 文件系统（`~/projects`）下，
  不要放在 `/mnt/c/...`，并行读文件会快很多
