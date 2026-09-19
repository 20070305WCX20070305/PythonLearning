# 01 NumPy 与 Pandas：多通道数据与实验记录

## 学习目标

- 会用 NumPy ndarray 表示多通道测量数据，读懂 shape/dtype/ndim，会切片与布尔索引；
- 掌握 reshape/transpose/concatenate 与广播规则，能用向量化替代 Python 循环；
- 会用 timeit 对比循环与向量化的耗时，并解释加速从何而来；
- 会用 mean/std/sum（含 axis、ddof）做误差统计，会用 default_rng 产生可复现随机数；
- 会读写 CSV 与 .npy，会用 Pandas 完成筛选、缺失值、groupby、merge 与 resample。

## 前置知识

- 阶段 01：venv/pip、pytest 基础；能用 Python 读写 txt/json/csv。
- Python 基础：列表、字典、函数、循环；知道平均值、标准差、标准误差的含义。

## 建议用时

3~4 周，每周 6~10 小时。建议逐节动手敲代码，最后集中做练习。

## 正文

### 1.1 ndarray：创建与基本属性

NumPy 的 `ndarray` 把同类型数据放在连续内存中，用编译层循环完成批量运算，是「多通道 × 采样点」数据的默认容器。

```python
import numpy as np

# 模拟 8 通道、2000 个采样点的电压数据，固定种子保证可复现
rng = np.random.default_rng(42)
voltage = rng.normal(loc=0.0, scale=1e-3, size=(8, 2000))   # 单位：V

print(voltage.shape)     # (8, 2000)：行是通道，列是采样点
print(voltage.dtype)     # float64
print(voltage.ndim)      # 2
print(voltage.size)      # 16000
print(voltage.nbytes)    # 128000（16000 个元素 × 8 字节）

t = np.arange(0, 0.2, 0.001)      # [0, 0.2) 步长 1 ms，共 200 点
ones = np.ones(5, dtype="int32")  # 全 1，指定整数类型
print(t.shape, ones.dtype)        # (200,) int32
```

`dtype` 决定内存与精度：

```python
a = np.array([1.2345678901234567, 2.0])
b = a.astype("float32")
print(a.nbytes, b.nbytes)   # 16 8
print(b)                    # [1.2345679 2.       ]（float32 约 7 位有效数字）
print((np.array([1, 2, 3]) / 2).dtype)   # float64，整数除法自动升级
```

**常见错误**

- 把 `voltage.shape[0]` 当采样点数：这里行是通道，多打印 shape 确认方向。
- 为了省内存全部 `astype("float32")`：统计精度下降，物理量建议保持 float64。

### 1.2 索引、切片与布尔索引

```python
import numpy as np

rng = np.random.default_rng(42)
voltage = rng.normal(size=(8, 2000)) * 1e-3     # V

ch0 = voltage[0]              # 第 0 通道，shape (2000,)
first10 = voltage[0, :10]     # 第 0 通道前 10 点，shape (10,)
sparse = voltage[:, ::100]    # 每 100 点取一个，shape (8, 20)

# 布尔索引：找出幅度超过 3 mV 的采样点
outlier_mask = np.abs(voltage) > 3e-3
print(outlier_mask.sum())     # 例如 43（正态噪声下约占 0.27%）
outliers = voltage[outlier_mask]
print(outliers.shape)         # (43,) 展平成一维

# 花式索引：按通道编号挑选
picked = voltage[[0, 3, 5]]
print(picked.shape)           # (3, 2000)

# 提示：切片是视图，改切片会改到原数组；布尔索引的结果是副本
```

**常见错误**

- 想保留原数据却在视图上改：先 `a[2:5].copy()` 再修改。
- 多条件布尔索引用 `and`/`or` 报 ValueError：必须用 `(a > 0) & (a < 1)`，每个条件加括号。
- 多维布尔索引结果被展平：要保持形状用 `np.where` 或掩码赋值。

### 1.3 形状操作与广播

```python
import numpy as np

rng = np.random.default_rng(42)
voltage = rng.normal(size=(8, 2000)) * 1e-3

print(voltage.reshape(4, 4000).shape)   # (4, 4000)
print(voltage.reshape(-1).shape)        # (16000,)  -1 表示自动推导
print(voltage.T.shape)                  # (2000, 8) 时间 × 通道

batch2 = rng.normal(size=(8, 2000)) * 1e-3
both = np.concatenate([voltage, batch2], axis=1)   # 沿采样点拼接
print(both.shape)                                  # (8, 4000)

# 广播：每通道减去自己的均值（(8,1) 广播到 (8,2000)）
centered = voltage - voltage.mean(axis=1, keepdims=True)
print(np.abs(centered.mean(axis=1)).max())         # 约 1e-19（浮点误差内为 0）
z = centered / (voltage.std(axis=1, keepdims=True) + 1e-12)   # 标准化
```

广播规则：从最后一维对齐，逐维比较；相等或其中一方为 1 就能广播，否则报错。

**常见错误**

- `voltage - voltage.mean(axis=1)` 报 ValueError：(8,2000) 与 (8,) 无法广播，需要 `keepdims=True`。
- reshape 元素总数必须一致：8×2000 不能 reshape 成 4×4001。
- 一维数组转置没有效果：`t.T` 仍是 (200,)；要变列向量用 `t.reshape(-1, 1)`。

### 1.4 向量化与 timeit 计时

```python
import timeit
import numpy as np

rng = np.random.default_rng(42)
voltage = rng.normal(size=(8, 200000)) * 1e-3

def rms_loop(data):
    """纯 Python 双层循环：逐点平方求和再开方。"""
    result = []
    for row in data:
        total = 0.0
        for x in row:
            total += x * x
        result.append((total / len(row)) ** 0.5)
    return result

def rms_vectorized(data):
    """NumPy 向量化：先平方、再按行求均值、最后开方。"""
    return np.sqrt((data ** 2).mean(axis=1))

print(np.allclose(rms_loop(voltage), rms_vectorized(voltage)))   # True

n = 3
t_loop = timeit.timeit(lambda: rms_loop(voltage), number=n) / n
t_vec = timeit.timeit(lambda: rms_vectorized(voltage), number=n) / n
print(f"纯循环: {t_loop * 1000:8.1f} ms/次")   # 例如  760.5 ms/次
print(f"向量化: {t_vec * 1000:8.2f} ms/次")    # 例如    3.42 ms/次
print(f"加速比: {t_loop / t_vec:6.0f}x")       # 例如  222x
```

嫌慢可以把 size 改成 `(8, 20000)`、number 改成 1。

**常见错误**

- 在 Python 循环里逐元素操作 ndarray，可能比列表还慢。
- timeit 次数太少（如 number=1）波动大：至少 3 次取平均，或看多次中的最小值。
- 循环里 `result = result + [x]` 反复新建列表：应 append，或整体改成向量化。

### 1.5 统计、误差与随机数

```python
import numpy as np

rng = np.random.default_rng(42)

# 同一电压重复测 20 次：真值 1.250 V，噪声 0.5 mV
measurements = rng.normal(loc=1.250, scale=5e-4, size=20)
std = measurements.std(ddof=1)                  # 样本无偏标准差
sem = std / np.sqrt(measurements.size)          # 标准误差
print(f"均值 {measurements.mean():.6f} V, 标准差 {std:.2e} V, 标准误差 {sem:.2e} V")
# 例如：均值 1.250170 V, 标准差 4.35e-04 V, 标准误差 9.73e-05 V

voltage = rng.normal(size=(8, 2000)) * 1e-3
print(voltage.mean(axis=1).shape)                  # (8,) 每通道均值
print(voltage.std(axis=1, ddof=1).shape)           # (8,) 每通道标准差
print(voltage.max(axis=1) - voltage.min(axis=1))   # 每通道峰峰值

# 坏点置 NaN 后用 nan 系列函数统计
bad = voltage.copy()
bad[0, 100:110] = np.nan
print(np.isnan(bad).sum())                         # 10
print(np.nanmean(bad, axis=1)[0].round(6))         # 忽略 NaN 的通道 0 均值

# 随机数统一用 default_rng，同一 seed 结果完全一致
rng = np.random.default_rng(2026)
print(rng.random(3))                 # [0,1) 均匀：例如 [0.289 0.077 0.632]
print(rng.choice(["A", "B", "C"], size=6, p=[0.5, 0.3, 0.2]))   # 按概率抽样
print(np.array_equal(np.random.default_rng(7).normal(size=3),
                     np.random.default_rng(7).normal(size=3)))  # True
```

**常见错误**

- 新旧接口混用：`np.random.seed(0)` 与 `default_rng(0)` 不是同一套流，混用后不可复现。
- 忘记 `ddof=1`：NumPy 默认 `ddof=0`（总体标准差），报告测量结果通常要样本标准差。
- `rng.choice(..., p=[...])` 概率和不是 1 会报 ValueError。

### 1.6 读写 CSV 与 .npy

```python
import numpy as np

rng = np.random.default_rng(42)
voltage = rng.normal(size=(8, 5)) * 1e-3

# CSV：delimiter 指定分隔符，header 写一行表头，fmt 控制有效数字
np.savetxt("voltage.csv", voltage, delimiter=",", fmt="%.6e",
           header="ch0,ch1,ch2,ch3,ch4", comments="")
loaded = np.loadtxt("voltage.csv", delimiter=",", skiprows=1)
print(loaded.shape)                    # (8, 5)
print(np.allclose(loaded, voltage))    # True

# .npy：二进制，保留 shape/dtype，读写最快
np.save("voltage.npy", voltage)
print(np.load("voltage.npy").shape)    # (8, 5)
```

需要把波形画出来时，自行查阅 matplotlib 文档；本阶段只负责把数据整理好。

**常见错误**

- `loadtxt` 遇到表头/空行报错：用 `skiprows=` / `comments=` 处理。
- `savetxt` 默认 `fmt="%.18e"` 文件很大：按需要指定 `fmt`（如 `%.6e`）。
- 把 .npy 当文本文件编辑会损坏数据：要交换用 CSV，要存档用 .npy。

### 1.7 Pandas：DataFrame、读取、筛选与缺失值

```python
import numpy as np
import pandas as pd

# Series：带标签索引的一维数据
volts = pd.Series([1.2501, 1.2498, 1.2503], index=["run1", "run2", "run3"])
print(volts.mean())          # 1.2500666...

# DataFrame：二维表格，每列共享行索引
records = pd.DataFrame({
    "sample":      ["S01", "S01", "S02", "S02", "S03"],
    "temperature": [290.0, 300.0, 290.0, 300.0, 300.0],
    "voltage":     [1.2501, 1.2593, 1.2450, 1.2541, 1.2449],
    "uncertainty": [0.0004, 0.0005, 0.0003, 0.0004, 0.0006],
})
records.to_csv("records.csv", index=False, encoding="utf-8")   # 写 CSV
df = pd.read_csv("records.csv")                                # 读 CSV
print(df.shape, list(df.columns))       # (5, 4) ['sample', 'temperature', ...]

# loc 按标签、iloc 按位置
print(df.loc[0, "voltage"], df.iloc[0, 2])                # 1.2501 1.2501
# 布尔过滤：300 K 且电压高于 1.25 V
print(df[(df["temperature"] == 300.0) & (df["voltage"] > 1.25)].shape)   # (2, 4)

# 缺失值：统计、删除、均值填充、线性插值
dirty = pd.DataFrame({
    "sample": ["S01", "S01", "S02", "S02"],
    "voltage": [1.2501, np.nan, 1.2541, 1.2450],
})
print(dirty.isna().sum()["voltage"])       # 1
print(dirty.dropna().shape)                # (3, 2)
filled = dirty.copy()
filled["voltage"] = filled["voltage"].fillna(filled["voltage"].mean())
print(filled["voltage"].round(6).tolist()) # [1.2501, 1.249733, 1.2541, 1.245]
print(pd.Series([1.0, np.nan, np.nan, 4.0]).interpolate().tolist())  # [1.0, 2.0, 3.0, 4.0]
```

**常见错误**

- 中文 CSV 乱码：明确 `encoding="utf-8"`；Windows 老工具导出的可能是 gbk。
- 读进来是字符串却直接比大小：先看 `dtypes`，必要时 `astype(float)`。
- 直接 `dropna()` 删掉太多行：先 `isna().sum()` 看分布，再用 `subset=` 精准删除。
- `fillna(0)` 当成「没有影响」：对均值/拟合有系统偏差，除非物理上 0 与缺失等价。

### 1.8 groupby 聚合与 merge/concat

```python
import pandas as pd

# 批量实验记录：3 个样品 × 2 个温度 × 5 次重复，共 30 行
df = pd.DataFrame({
    "sample": ["S01"] * 10 + ["S02"] * 10 + ["S03"] * 10,
    "temperature": [290.0, 300.0] * 15,
    "voltage": [
        1.2501, 1.2593, 1.2499, 1.2591, 1.2503, 1.2595, 1.2498, 1.2589, 1.2500, 1.2594,
        1.2450, 1.2541, 1.2448, 1.2540, 1.2452, 1.2543, 1.2449, 1.2539, 1.2451, 1.2542,
        1.2401, 1.2489, 1.2399, 1.2488, 1.2402, 1.2491, 1.2400, 1.2487, 1.2398, 1.2490,
    ],
})

# 分组聚合：每组重复次数、均值、样本标准差（std 默认 ddof=1）
summary = (df.groupby(["sample", "temperature"])["voltage"]
             .agg(["count", "mean", "std"]).round(6))
print(summary)
#                   count     mean      std
# sample temperature
# S01    290.0          5  1.25002  0.000192
#        300.0          5  1.25924  0.000241
# ...（S02、S03 各组同样是 count=5）

# merge：把样品信息表按 sample 列并进来
samples = pd.DataFrame({"sample": ["S01", "S02", "S03"],
                        "material": ["GaAs", "Si", "SiC"]})
merged = df.merge(samples, on="sample", how="left")
print(merged.shape)                                       # (30, 4)
print(merged.groupby("material")["voltage"].mean().round(6))
# material
# GaAs    1.254630
# Si      1.249550
# SiC     1.244450

# concat：拼接两批数据，先重置索引避免重复
both = pd.concat([df.iloc[:15], df.iloc[15:]], ignore_index=True)
print(both.shape)                                         # (30, 3)
```

**常见错误**

- 分组结果的索引是分组键（MultiIndex）：取列用 `summary["mean"]`，需要时 `reset_index()`。
- merge 的键两侧都重复会行数膨胀（多对多）：先比较 merge 前后 shape。
- concat 默认保留原索引，出现重复索引：按需 `ignore_index=True`。

### 1.9 时间序列 resample 基础

```python
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
times = pd.date_range("2026-09-19 08:00:00", periods=60, freq="10s")   # 10 分钟
ts = pd.DataFrame({"time": times, "voltage": 1.25 + rng.normal(0, 5e-4, 60)})

ts = ts.set_index("time")               # 时间必须是索引才能 resample
print(ts.index.dtype)                   # datetime64[ns]

per_minute = ts.resample("1min")["voltage"].mean()     # 10 秒 -> 1 分钟
print(per_minute.size)                  # 10
```

**常见错误**

- 时间列是字符串时 resample 报错：先 `pd.to_datetime(df["time"])`。
- 忘记 `set_index("time")`。
- 升采样会产生 NaN：按需 `interpolate()` 或 `ffill()` 处理。

## 练习

1. （基础）用 `np.random.default_rng(12345)` 生成 16 通道 × 5000 点的高斯噪声（每通道加不同偏置），计算每通道 mean、std(ddof=1)、峰峰值与标准误差，并按噪声从大到小打印通道号。
   提示：`np.argsort`/`np.sort`；输出用 f-string 对齐。
   验收：全程无 Python 循环完成逐通道统计；抽查 2 个通道与手算一致。

2. （基础）把每通道超过 ±3σ 的点置为 NaN，用 nan 系列函数重新统计，再标准化为均值 0、标准差 1，验证 `np.nanmean(z, axis=1)` 接近 0。
   提示：`np.where(cond, np.nan, data)`；`np.nanstd`；广播用 keepdims。
   验收：打印坏点数量与标准化前后统计量；没有任何 Python 循环。

3. （中级）对 8×200000 数据，分别用纯 Python 双层循环与 NumPy 向量化计算「相邻采样点差分的均方根」，用 timeit 各测 3 次取平均，验证结果一致并输出加速比。
   提示：`np.diff(data, axis=1)` → 平方 → 按行均值 → 开方；用 `np.allclose` 核对。
   验收：加速比 ≥ 50 倍（记录实际值），并在注释里写一句加速来源。

4. （中级）构造 3 样品 × 3 温度 × 4 重复的记录表（sample、temperature、voltage、run_id），完成分组 count/mean/std，与样品信息表（sample、material、thickness_nm）merge，输出每种材料在各温度下的平均电压，并检查 merge 前后行数一致。
   提示：`groupby([...]).agg([...])`；`merge(..., on="sample", how="left")`；用 `shape` 检查。
   验收：汇总行数 = 样品数 × 温度数；merge 后仍为 36 行；能解释 std 与 count。

5. （综合）生成 2 小时、每 10 秒一点的反应腔温度记录（缓慢漂移 + 噪声），设几处 NaN，转 datetime 索引后重采样为 5 分钟均值，对缺失做线性插值，报告最小值、最大值与整体漂移速率。
   提示：`pd.date_range`、`resample("5min").mean()`、`interpolate()`；注意单位。
   验收：索引 dtype 为 datetime64；重采样后 24 行；插值后中间无 NaN；漂移速率量纲正确。

## 自测清单

- [ ] 能说出 ndarray 与 list 的两点本质区别（同类型连续内存、支持向量化运算）
- [ ] 会读 shape/dtype/ndim/size/nbytes，并能判断 axis=0/1 的聚合方向
- [ ] 会切片、布尔索引、花式索引，知道切片是视图、布尔索引是副本
- [ ] 会用 reshape/transpose/concatenate 完成形状变换与拼接
- [ ] 会用 keepdims + 广播写出去均值、标准化
- [ ] 会用 timeit 对比循环与向量化，并用 allclose 验证结果一致
- [ ] 会用 mean/std/sum 的 axis 与 ddof 参数，知道 sem 怎么算
- [ ] 会用 default_rng 产生可复现随机数，知道新旧随机接口不能混用
- [ ] 会读写 CSV、.npy
- [ ] 会用 loc/iloc 与布尔条件筛选行/列
- [ ] 会用 isna/dropna/fillna/interpolate 处理缺失值
- [ ] 会 groupby 聚合与 merge/concat，并检查行数是否异常
- [ ] 会把时间列转 datetime 并用 resample 降采样

## 参考资料

- NumPy 绝对初学者指南：https://numpy.org/doc/stable/user/absolute_beginners.html
- NumPy 随机数指南：https://numpy.org/doc/stable/reference/random/index.html
- pandas 十分钟入门：https://pandas.pydata.org/docs/user_guide/10min.html
- pandas 索引与选取：https://pandas.pydata.org/docs/user_guide/indexing.html
- pandas 时间序列：https://pandas.pydata.org/docs/user_guide/timeseries.html
