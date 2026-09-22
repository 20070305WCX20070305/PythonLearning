# 01 NumPy 数值计算指南（计算物理方向）

## 学习目标

- 会用 `ndarray` 表示物理量（采样序列、空间网格、多分量场），读懂 `shape/dtype/ndim`；
- 掌握切片、布尔索引、花式索引，分清**视图**与**副本**；
- 掌握广播、`reshape/transpose`、`meshgrid`，能把双重循环改写成向量化写法；
- 会做统计聚合、掩码筛选、`nan` 系列处理坏点；
- 会用 `np.linalg` 解线性方程组、求本征值/本征向量（含一维谐振子的有限差分矩阵）；
- 会用多项式拟合实验数据、用 FFT 做频谱分析、用随机数做蒙特卡洛；
- 会读写 `.npy/.npz/.txt`，并知道计算物理里的常见陷阱。

## 前置知识

- Python 基础：函数、列表、循环、`import`。
- 不需要先读阶段 02：本文件从计算物理视角讲 NumPy，与 [阶段 02 的 NumPy 课](../02-Python系统资源与并发/01-NumPy与Pandas.md) 是互补关系（那篇偏数据整理）。

## 建议用法

- 从头到尾把示例敲一遍；以后当参考手册用，按节跳查。
- 约定：长度单位用无单位化的自然单位为例，时间为任意单位；物理量数组一律 `float64`。

## 正文

### 1.1 数组创建：把物理量放进网格

```python
import numpy as np

print(np.__version__)

# 一维：空间网格上的波函数（高斯波包）
N = 1000
x = np.linspace(-10.0, 10.0, N)          # N 个等间距格点
psi = np.exp(-x**2 / 2) / np.pi**0.5     # 归一化 Gaussian

print(x.shape, psi.dtype, psi.nbytes)    # (1000,) float64 8000
print(np.trapezoid(psi**2, x))           # 约 1.0，验证归一化

# 其他常用创建方式
zeros = np.zeros((3, 4))                 # 3×4 全 0
ones = np.ones_like(x)                   # 与 x 同形状全 1
eye = np.eye(3)                          # 单位矩阵
y, z = np.mgrid[-1:1:5j, -1:1:5j]        # 两维网格，5×5
idx = np.arange(0, 10, 2)                # [0 2 4 6 8]
```

需要一次性生成大型网格时，`ogrid` 比 `meshgrid` 更省内存（它返回可广播的「开口」数组）：

```python
y, z = np.ogrid[-1:1:200j, -1:1:200j]    # 形状 (200,1) 与 (1,200)
r = np.sqrt(y**2 + z**2)                 # 广播成 (200,200)，不产生多余副本
```

### 1.2 dtype：精度、内存与复数

物理计算默认 `float64`（约 16 位有效数字）；只有内存紧张且精度要求低时才用 `float32`。量子力学、波动问题需要 `complex128`。

```python
n = np.arange(10)              # int64
q = n / 3                      # 整数除法自动升级为 float64
c = np.array([1.0 + 2.0j])     # complex128

print(n.dtype, q.dtype, c.dtype)
print(np.array([1.2345678901234567]).astype("float32"))
# [1.2345679]  float32 只有约 7 位有效数字，大数相减会严重丢精度

# 复数数组：实部/虚部/模/相位
print(c.real, c.imag, np.abs(c), np.angle(c))
```

**常见陷阱**

- 两个大数相减（如 `1e10 + 1 - 1e10`）在 `float32` 下会得到 0：物理量保持 `float64`。
- 整数数组做除法得到浮点数组，但**整除 `//` 会截断**；索引用 `//`、物理量用 `/`。

### 1.3 索引、切片、视图与副本

```python
a = np.arange(10)

b = a[2:5]        # 切片：视图（view），共享底层内存
b[:] = 0
print(a)          # [0 1 0 0 0 5 6 7 8 9]，原数组被改

c = a[2:5].copy() # 副本：独立内存
c[:] = 9
print(a)          # 原数组不变

# 多通道数据：行 = 通道，列 = 采样点
rng = np.random.default_rng(42)
voltage = rng.normal(scale=1e-3, size=(8, 2000))   # 8 通道 × 2000 点，V

ch0 = voltage[0]                # (2000,)
first10 = voltage[0, :10]       # (10,)
every100 = voltage[:, ::100]    # (8, 20)

mask = np.abs(voltage) > 3e-3           # 布尔掩码
voltage[mask] = 0.0                     # 掩码赋值：坏点清零
picked = voltage[[0, 3, 5]]             # 花式索引：挑 3 个通道，结果是副本
```

**常见陷阱**

- 函数返回数组切片时，调用方修改会影响原数组：对外返回前 `copy()`。
- 花式索引、布尔索引的结果是副本，`voltage[[0, 3]][:] = 0` 不会改原数组。
- 多条件必须写 `(a > 0) & (a < 1)`，不能用 `and`/`or`。

### 1.4 广播与形状操作

广播规则：从**最后一维**开始对齐，逐维比较；两维相等或其中一个是 1 即可广播。

```python
r = np.linspace(0, 1, 50).reshape(-1, 1)   # (50,1)
theta = np.linspace(0, 2*np.pi, 100)       # (100,)
rho = r * np.cos(theta)                    # (50,100)，极坐标 → 笛卡尔
print(rho.shape)

# 去掉每通道均值（去基线）：注意 keepdims
centered = voltage - voltage.mean(axis=1, keepdims=True)   # (8,1) 广播到 (8,2000)
print(np.abs(centered.mean(axis=1)).max())                 # 约 1e-19（浮点误差内为 0）

print(voltage.reshape(4, 4000).shape)   # 形状可改，元素总数不变
print(voltage.T.shape)                  # (2000, 8)
print(np.concatenate([voltage, voltage], axis=1).shape)    # (8, 4000)
```

**常见陷阱**

- `voltage - voltage.mean(axis=1)` 会报错（(8,2000) 与 (8,) 无法广播）：要加 `keepdims=True`。
- 一维数组转置没有效果：`t.T` 仍是 `(N,)`；要列向量用 `t.reshape(-1, 1)` 或 `t[:, None]`。
- 形状不匹配的报错信息会列出两侧形状，先检查「哪一维没对齐」。

### 1.5 向量化：把物理公式写成数组表达式

以数值求导为例。中心差分公式：

$$
f'(x_i) \approx \frac{f(x_{i+1}) - f(x_{i-1})}{x_{i+1} - x_{i-1}}
$$

```python
x = np.linspace(0, 2*np.pi, 1001)
f = np.sin(x)

# 向量化：整条数组一次算完
df = (f[2:] - f[:-2]) / (x[2:] - x[:-2])
err = np.abs(df - np.cos(x[1:-1])).max()
print(err)        # 约 1e-6，二阶精度 O(h²)
```

对比循环写法与计时（数组越大差距越明显）：

```python
import timeit

def deriv_loop(x, f):
    out = np.empty(x.size - 2)
    for i in range(1, x.size - 1):
        out[i-1] = (f[i+1] - f[i-1]) / (x[i+1] - x[i-1])
    return out

t_loop = timeit.timeit(lambda: deriv_loop(x, f), number=100)
t_vec  = timeit.timeit(lambda: (f[2:] - f[:-2]) / (x[2:] - x[:-2]), number=100)
print(t_loop / t_vec)   # 通常快 10~100 倍，视机器而定
```

更多物理公式的向量化模板：

```python
# 势能与力 F = -dV/dx
V = 0.5 * x**2
F = -(V[2:] - V[:-2]) / (x[2:] - x[:-2])

# 洛伦兹力：v × B
v = rng.normal(size=(1000, 3))
B = np.array([0.0, 0.0, 1.0])
F = np.cross(v, B)                          # 逐行叉乘

# 库仑势：所有粒子对的距离矩阵
pos = rng.normal(size=(200, 3))
d = pos[:, None, :] - pos[None, :, :]       # (200,200,3)
dist = np.linalg.norm(d, axis=-1)           # (200,200)
```

**什么时候向量化会失效**：逐粒子、逐格点的**依赖前一步状态**的循环（如分子动力学、伊辛模型、显式时间推进）。这类问题看 [05-Numba](05-Numba加速计算指南.md)。

### 1.6 聚合、统计与坏点处理

```python
rng = np.random.default_rng(7)
E = rng.normal(loc=1.0, scale=0.1, size=(100, 50))   # 100 组 × 50 次测量

print(E.mean(), E.std(), E.min(), E.max())
print(E.mean(axis=1).shape)                 # 每组均值：(100,)
print(E.std(axis=1, ddof=1).shape)          # 样本标准差（无偏）：(100,)

# 标准误：σ/√n
sem = E.std(axis=1, ddof=1) / np.sqrt(E.shape[1])
print(sem.shape)

# 分位数与协方差
print(np.percentile(E, [16, 50, 84]))       # 1σ 区间
print(np.cov(E[:, :2].T).shape)             # (2,2)
```

坏点（NaN）处理：

```python
data = np.array([1.0, 2.0, np.nan, 4.0])
print(np.nanmean(data), np.nanstd(data))    # 忽略 NaN
print(np.isnan(data).sum())                 # NaN 个数
print(np.nan_to_num(data, nan=0.0))         # 替换 NaN
```

**常见陷阱**

- `axis` 的含义：`axis=0` 沿行方向压缩（对每列算），`axis=1` 对每行算；不确定就打印 `shape` 验证。
- 有 NaN 时普通 `mean()` 返回 NaN；用 `nanmean` 或先清洗。
- 概率密度做直方图时要传 `density=True`，并注意分箱宽度影响。

### 1.7 线性代数：解方程、本征值、本征向量

```python
A = np.array([[3.0, -1.0], [-1.0, 2.0]])
b = np.array([1.0, 0.0])

x = np.linalg.solve(A, b)      # 解 A x = b（不要用 inv(A) @ b）
print(x, A @ x)                # 验证 A x == b

print(np.linalg.det(A))                    # 行列式
print(np.linalg.norm(x))                   # 2-范数
w, V = np.linalg.eigh(A)                   # 对称矩阵：升序实本征值
print(w)

# SVD 与条件数
U, s, Vt = np.linalg.svd(A)
print(s, np.linalg.cond(A))
```

计算物理核心例子：**一维谐振子基态与激发态**。哈密顿量

$$
H = -\frac{1}{2}\frac{d^2}{dx^2} + \frac{1}{2}x^2 \quad (\hbar = m = \omega = 1)
$$

在均匀网格上做中心差分，得三对角矩阵，对角元 `1/dx² + x_i²/2`，非对角元 `-1/(2dx²)`：

```python
N, L = 500, 6.0
x = np.linspace(-L, L, N)
dx = x[1] - x[0]

diag = 1.0/dx**2 + 0.5*x**2
off = -0.5/dx**2 * np.ones(N - 1)

H = np.diag(diag) + np.diag(off, 1) + np.diag(off, -1)
vals, vecs = np.linalg.eigh(H)

print(np.round(vals[:5], 4))    # [0.5 1.5 2.5 3.5 4.5]，与解析解 (n+1/2) 一致
```

二维或更大规模的本征值问题（稀疏矩阵）用 [SciPy](03-SciPy数值算法指南.md) 的 `eigsh`，不要建满矩阵。

**常见陷阱**

- 解方程用 `solve`，不用 `inv`：更快也更稳定。
- 本征值问题对矩阵是否对称很敏感：对称/厄米用 `eigh/eigvalsh`，一般矩阵用 `eig/eigvals`（可能返回复数）。
- 有限差分本征值会随网格变细收敛，但网格太密时 `1/dx²` 很大、条件数变差；先做收敛性测试（换 `N` 看结果变化）。

### 1.8 拟合与多项式

```python
t = np.linspace(0, 5, 30)
y_true = 3.0 - 2.0*t + 0.5*t**2              # 二次模型
rng = np.random.default_rng(1)
y = y_true + rng.normal(0, 0.5, t.size)      # 加噪声

# 推荐的新式 API：Polynomial.fit（数值稳定性更好）
p = np.polynomial.Polynomial.fit(t, y, deg=2)
coef = p.convert().coef                       # 转回标准幂次基
print(np.round(coef, 3))                      # 接近 [3, -2, 0.5]

# 旧式 API 仍可用
coef2 = np.polyfit(t, y, 2)
print(np.round(coef2, 3))

# 求根与求值
print(np.roots(coef2))
print(np.polyval(coef2, t[:3]))
```

指数衰减/幂律这类非线性模型先用 SciPy 的 `curve_fit`（见 [03-SciPy](03-SciPy数值算法指南.md) 第 5 节），不要硬用多项式。

### 1.9 随机数与蒙特卡洛

用新式 `Generator`（`np.random.default_rng`），不要用旧式 `np.random.seed/rand`。

```python
rng = np.random.default_rng(2026)

# 常用分布
u = rng.random(5)                          # [0,1) 均匀
g = rng.normal(loc=0.0, scale=1.0, size=5) # 高斯
p = rng.poisson(lam=3.0, size=5)           # 泊松
c = rng.choice([-1.0, 1.0], size=5)        # 离散取值

# 蒙特卡洛求 π：单位正方形内随机撒点
n = 1_000_000
x = rng.random(n)
y = rng.random(n)
pi_est = 4.0 * np.mean(x**2 + y**2 <= 1.0)
print(pi_est, np.pi)

# 蒙特卡洛积分：∫₀¹ e^(-x²) dx ≈ 0.7468
v = rng.random(n)
I = np.mean(np.exp(-v**2))
print(I)

# 二维随机游走：<R²> ≈ 步数
steps = rng.integers(0, 2, size=(10_000, 2)) * 2 - 1   # 每步 ±1
path = np.cumsum(steps, axis=0)
r2 = np.sum(path**2, axis=1)
print(r2.mean())                           # 约 1e4
```

**为什么用 `default_rng`**：它是基于 PCG64 的独立随机流，速度快、可复现；固定种子（如 42、2026）保证每次运行结果一致。

**常见陷阱**

- 把 `rng.normal(size=n)` 写成 `rng.normal(n)`：后者把 `n` 当 `loc`（均值），得到的是标量，用错会静默算出错误结果。
- 蒙特卡洛误差按 `1/√n` 收敛：想多一位有效数字，点数要 ×100。需要更高效率时用重要性抽样。
- 大数组 `rng.random((n, 3))` 一次生成，不要循环里一个个生成。

### 1.10 FFT：频谱分析

```python
fs = 1000.0                                  # 采样率 1 kHz
t = np.arange(0, 1.0, 1/fs)
sig = 0.8*np.sin(2*np.pi*50*t) + 0.3*np.sin(2*np.pi*120*t)

Y = np.fft.rfft(sig)                         # 实信号用 rfft，只算正频率
freqs = np.fft.rfftfreq(t.size, d=1/fs)
amp = 2.0 * np.abs(Y) / t.size               # 单边幅度谱

peak = freqs[np.argmax(amp)]
print(np.round(peak, 1))                     # 50.0
top2 = freqs[np.argsort(amp)[-2:]]
print(np.round(np.sort(top2), 1))            # [50. 120.]

# 逆变换验证
sig_back = np.fft.irfft(Y, n=t.size)
print(np.abs(sig_back - sig).max())          # 约 1e-15
```

物理用途：分析周期信号、做谱密度、卷积（`np.fft` 与卷积定理）、求解周期性边界条件的问题。

**常见陷阱**

- 频率轴必须用 `rfftfreq/fftfreq` 生成，不要自己猜。
- 幅度归一化与信号长度有关；比较不同长度数据时先归一化。
- 信号非整周期时会有频谱泄漏：加窗（`np.hanning`）再变换。
- SciPy 的 `scipy.fft` 是同一套 API 的更快实现，参数更多，可直接替换。

### 1.11 文件读写

```python
# 单个数组：.npy（二进制、快、保精度）
np.save("psi.npy", psi)
psi2 = np.load("psi.npy")

# 多个数组打包：.npz
np.savez("run.npz", x=x, psi=psi, E0=0.5)
data = np.load("run.npz")
print(list(data.keys()), data["E0"])

# 文本格式：可读但慢，适合小数据与交换
np.savetxt("curve.txt", np.column_stack([t[:5], sig[:5]]),
           header="t signal", fmt="%.6f")
back = np.loadtxt("curve.txt")
print(back.shape)

# 带缺失值的表格：genfromtxt
```

大数组、多组数据集请用 HDF5，见 [阶段 02 的 HDF5 课](../02-Python系统资源与并发/02-HDF5与SQLite.md)。

### 1.12 性能习惯与常见陷阱汇总

- **能向量化就向量化**：先写清楚公式，再找对应的数组操作。
- **避免在循环里 append**：预分配 `np.empty(n)`，或者用列表收集后一次转换。
- **原地运算省内存**：`a *= 2`、`np.add(a, b, out=a)`。
- **广播不要制造超大中间数组**：`(n,1) - (1,m)` 会产生 `(n,m)`，内存爆掉就分块循环。
- **`float64` 优先**；确需省内存时才降精度，并检查结果差异。
- **随机数固定种子**，保证结果可复现。
- **网格类问题先做收敛性测试**（改 N、改 dt 看结果是否稳定）。
- **`np.set_printoptions` 只影响显示，不影响精度**。

## 练习

1. **向量化**：用 `np.linspace` 生成 `x ∈ [0, 10]` 的 1000 个点，向量化计算

   $$
   f(x) = \frac{\sin x}{x} e^{-x/5}
   $$
   并求 `f` 的最大值与对应的 `x`（用 `argmax`）。
2. **本征值**：把 1.7 节的谐振子改成势 `V(x) = |x|`（线性势），画出前 5 个本征值随 `L` 和 `N` 的变化，观察收敛。
3. **蒙特卡洛**：用随机撒点法计算半径为 1 的球的体积（提示：在 `[-1,1]³` 内撒点），与解析值 `4π/3` 比较，并统计不同 `n` 下的相对误差，验证 `1/√n`。
4. **FFT**：生成频率为 7 Hz、时长 2 s、采样率 100 Hz 的信号，加上高斯白噪声，找出主频；再给信号加 `np.hanning` 窗，比较主峰宽度。
5. **统计**：模拟 200 组、每组 30 次的测量（真值 10，σ=0.3），画出「组均值」的分布，验证其标准差约为 `0.3/√30`。

## 自测清单

- [ ] 能解释 `shape/dtype/ndim/nbytes`，知道 `float32` 与 `float64` 的取舍
- [ ] 能说明哪些操作返回视图、哪些返回副本，并知道何时 `.copy()`
- [ ] 能写出 `(8,2000)` 去均值、标准化、掩码筛选的向量化代码
- [ ] 能解释广播规则并用 `keepdims`、`meshgrid/ogrid` 构造网格
- [ ] 会用 `np.linalg.solve/eigh/svd`，能建一维问题的有限差分矩阵并求本征值
- [ ] 会用 `Polynomial.fit` 或 `polyfit` 拟合、`roots/polyval` 求根求值
- [ ] 会用 `default_rng` 做蒙特卡洛，知道误差随 `1/√n`
- [ ] 会用 `rfft/rfftfreq` 做频谱，并知道泄漏与加窗
- [ ] 会 `save/load`（npy/npz）、`savetxt/loadtxt`
- [ ] 知道逐格点/逐粒子循环该转投 Numba（[05](05-Numba加速计算指南.md)）

## 参考资料

- NumPy 官方文档：https://numpy.org/doc/stable/
- NumPy 广播规则：https://numpy.org/doc/stable/user/basics.broadcasting.html
- NumPy 随机数新接口：https://numpy.org/doc/stable/reference/random/index.html
- Gould & Tobochnik, *Statistical and Thermal Physics*（配套计算练习常用 NumPy）
