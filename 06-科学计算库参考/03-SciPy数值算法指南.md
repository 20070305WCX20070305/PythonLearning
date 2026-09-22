# 03 SciPy 数值算法指南（计算物理方向）

## 学习目标

- 知道 SciPy 各子模块对应什么计算物理任务，能按需查找 API；
- 会用 `constants` 与 `special`（物理常数、特殊函数）；
- 会用 `integrate` 做数值积分（函数式与采样点式）；
- 会用 `interpolate` 做插值（样条、多维网格）；
- 会用 `optimize` 求极小值、求根、拟合实验数据（`curve_fit`）；
- 会用 `solve_ivp` 解常微分方程初值问题（含事件检测）；
- 会用 `sparse` + `eigsh` 处理大规模本征值问题；
- 了解 `fft`、`spatial`、`stats` 的常用入口。

## 前置知识

- NumPy 基础（[01-NumPy](01-NumPy数值计算指南.md)）：数组、切片、广播、`linalg`。
- 微积分与常微分方程基础：知道「初值问题」「本征值问题」的含义。

## 建议用法

- 先通读一遍模块总览（第 1 节），知道「有什么」；用到时再精读对应小节。
- 所有示例都可以直接运行，建议自己改参数做收敛性测试。

## 正文

### 3.1 模块总览：什么任务找哪个模块

| 子模块 | 功能 | 计算物理典型用途 |
| --- | --- | --- |
| `scipy.constants` | 物理常数、单位换算 | 代入真实常数计算 |
| `scipy.special` | 特殊函数 | 误差函数、贝塞尔函数、伽马函数、拉盖尔多项式 |
| `scipy.integrate` | 积分、ODE 初值问题 | 定积分、归一化常数、动力学演化 |
| `scipy.interpolate` | 插值 | 补齐稀疏数据、网格数据查询 |
| `scipy.optimize` | 优化、求根、拟合 | 变分求极小、解超越方程、拟合实验数据 |
| `scipy.linalg` | 稠密线性代数 | 比 `np.linalg` 更全（分解、矩阵函数） |
| `scipy.sparse` / `sparse.linalg` | 稀疏矩阵与迭代解法 | 有限差分/有限元、大本征值问题 |
| `scipy.fft` | 傅里叶变换 | 频谱、谱方法（比 numpy 更快） |
| `scipy.spatial` | 空间算法 | 最近邻、周期性距离、凸包、几何 |
| `scipy.stats` | 统计分布与检验 | 分布拟合、置信区间、假设检验 |

约定：`import scipy as sp` 会引入顶层命名空间，但各子模块需要显式导入，例如 `from scipy.integrate import quad`。

### 3.2 物理常数与特殊函数

```python
from scipy import constants as C

print(C.c)                 # 光速 299792458.0 m/s
print(C.h)                 # 普朗克常数
print(C.hbar)              # 约化普朗克常数
print(C.e)                 # 元电荷
print(C.k)                 # 玻尔兹曼常数
print(C.N_A)               # 阿伏伽德罗常数
print(C.electron_mass)     # 电子质量

# 含不确定度的常数
val, unit, unc = C.physical_constants["fine-structure constant"]
print(val, unit, unc)

# 单位换算
print(C.k * 300.0 / C.e)                          # 300 K 热能 ≈ 0.02585 eV
print(C.convert_temperature(300.0, "K", "C"))     # 26.85 °C
```

```python
from scipy import special
import numpy as np

x = np.linspace(0, 3, 200)
print(special.erf(x[:3]))          # 误差函数
print(special.gamma(5.0))          # 伽马函数：4! = 24
print(special.jv(0, x[:3]))        # 第一类贝塞尔函数 J0
print(special.laguerre(2)(1.0))    # 拉盖尔多项式 L2(1)

# 氢原子 1s 径向波函数（a0 = 1）
r = np.linspace(0, 10, 300)
R10 = 2*np.exp(-r)
dens = 4*np.pi*r**2 * R10**2         # 径向概率密度
print(np.trapezoid(dens, r))         # 归一化：约 1.0
```

特殊函数清单很长，查官方文档的 [Special functions](https://docs.scipy.org/doc/scipy/reference/special.html) 页面即可。

### 3.3 数值积分 `integrate`

函数式积分（被积函数已知）：

```python
from scipy.integrate import quad
import numpy as np

# ∫₀^∞ e^{-x²} dx = √π/2
val, abserr = quad(lambda x: np.exp(-x**2), 0, np.inf)
print(val, abserr, np.sqrt(np.pi)/2)

# 带参数：partition function ∫₀^∞ x² e^{-x²} dx = √π/4
val, err = quad(lambda x: x**2*np.exp(-x**2), 0, 50.0)

# 二维积分：dblquad（被积函数签名为 f(y, x)）
from scipy.integrate import dblquad
vol, err = dblquad(lambda y, x: np.exp(-(x**2 + y**2)), 0, 5, 0, 5)
print(vol, err)                     # ≈ (√π/2 · erf(5))² ≈ π/4
```

采样点积分（数据只有离散点，或函数在网格上取值）：

```python
from scipy.integrate import trapezoid, simpson

x = np.linspace(0, np.pi, 11)
y = np.sin(x)
print(trapezoid(y, x))    # 梯形法
print(simpson(y, x))      # 辛普森法，精度更高
print(2.0)                # 解析值
```

多点采样优先 `simpson`（误差 `O(h⁴)`），数据含噪声时 `trapezoid` 更稳。

**常见陷阱**

- `quad` 返回 `(值, 误差估计)` 元组，误把整个元组当数值用。
- 积分区间无穷用 `np.inf`，不要用 `1e300`。
- 被积函数有奇点/尖峰时，用 `points=` 参数提示积分器，或分段积分。

### 3.4 插值 `interpolate`

```python
from scipy.interpolate import CubicSpline, interp1d
import numpy as np

xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
ys = np.array([0.0, 0.8, 0.9, -0.6, -0.8])

cs = CubicSpline(xs, ys)                 # 三次样条：二阶导连续
xx = np.linspace(0, 4, 200)
print(cs(xx[:3]))
print(cs.derivative()(2.0))              # 求导
print(cs.integrate(0, 4))                # 积分

# 线性插值（旧接口，新代码推荐 numpy.interp 或 CubicSpline）
f = interp1d(xs, ys, kind="linear", bounds_error=False, fill_value="extrapolate")
print(f([0.5, 3.5]))
```

二维网格数据查询（例如势能面）：

```python
from scipy.interpolate import RegularGridInterpolator

x = np.linspace(-2, 2, 200)
y = np.linspace(-2, 2, 150)
X, Y = np.meshgrid(x, y, indexing="ij")
V = np.exp(-(X**2 + Y**2))               # (200,150)

interp = RegularGridInterpolator((x, y), V)          # 默认越界报错
print(interp((0.3, -0.2)))
print(interp(np.array([[0.0, 0.0], [1.0, 1.0]])))    # 批量查询
```

**常见陷阱**

- `CubicSpline` **默认外推**，数据范围外结果可能毫无物理意义；需要时传 `extrapolate=False`。
- `RegularGridInterpolator` 默认越界报 `ValueError`（这是好事，防止静默出错）。
- 采样点太少不要用高阶样条：会过冲（Runge 现象）。

### 3.5 优化、求根与拟合 `optimize`

**求极小值 `minimize`**：以 Lennard-Jones 势的平衡距离为例。

```python
from scipy.optimize import minimize
import numpy as np

def V(r):
    return 4.0*(r**-12 - r**-6)          # L-J 势，ε = σ = 1

res = minimize(V, x0=1.2, method="Nelder-Mead")
print(res.x, res.fun)                    # x ≈ [1.1225]，V ≈ -1.0
print(2**(1/6))                          # 解析平衡距离 1.1225
```

多维优化、带约束优化用同一接口：`method="BFGS"`、`bounds=[...]`、`constraints=[...]`。有梯度表达式时传给 `jac=` 会快很多。

**求根 `brentq/root_scalar`**：解开普勒方程 `M = E - e sin E`。

```python
from scipy.optimize import brentq

e, M = 0.5, 1.0
E = brentq(lambda E: E - e*np.sin(E) - M, 0.0, np.pi)
print(E)
```

**拟合 `curve_fit`**：高斯峰 + 常数背景。

```python
from scipy.optimize import curve_fit

def gauss(x, A, mu, sigma, c):
    return A*np.exp(-(x-mu)**2/(2*sigma**2)) + c

rng = np.random.default_rng(0)
x = np.linspace(-5, 5, 200)
y = gauss(x, 2.0, 0.5, 0.8, 0.2) + rng.normal(0, 0.05, x.size)

popt, pcov = curve_fit(gauss, x, y, p0=[2.0, 0.0, 1.0, 0.0])
perr = np.sqrt(np.diag(pcov))            # 1σ 参数误差
for name, v, s in zip(["A", "mu", "sigma", "c"], popt, perr):
    print(f"{name} = {v:.3f} ± {s:.3f}")
```

**常见陷阱**

- 极小化可能停在局部极小：多起点（`for x0 in ...`）比较，或用全局方法 `differential_evolution`。
- `curve_fit` 的初值 `p0` 很重要：物理上先估计量级；参数相差太多数量级时先做无量纲化。
- `pcov` 是参数协方差矩阵；若出现 `OptimizeWarning`，通常意味着参数不可辨识或数据不足。
- 拟合不是验证：永远画「数据 + 拟合曲线 + 残差」。

### 3.6 解常微分方程 `solve_ivp`

`solve_ivp` 解一阶方程组 `dy/dt = f(t, y)`；高阶方程先化成一阶方程组。

**阻尼振子**：`x'' + 2γx' + ω₀²x = 0`，令 `y = [x, v]`：

```python
from scipy.integrate import solve_ivp
import numpy as np

def rhs(t, y):
    x, v = y
    gamma, w0 = 0.3, 2.0
    return [v, -2*gamma*v - w0**2*x]

sol = solve_ivp(rhs, (0.0, 20.0), [1.0, 0.0],
                rtol=1e-9, atol=1e-12, dense_output=True)
print(sol.t.shape, sol.y.shape)          # (n,) (2, n)，每列一个时刻
tt = np.linspace(0, 20, 500)
x, v = sol.sol(tt)                       # 连续解插值
```

**事件检测**：自由落体到地面的时间。

```python
def ball(t, y):
    h, v = y
    return [v, -9.8]

def hit_ground(t, y):
    return y[0]                          # 触发条件：高度过零

hit_ground.terminal = True               # 触发后停止积分
hit_ground.direction = -1                # 只检测下降方向

sol = solve_ivp(ball, (0.0, 10.0), [1.0, 0.0], events=hit_ground)
print(sol.t_events[0], np.sqrt(2/9.8))   # 落地时刻 ≈ 0.4518 s
```

**方法与误差控制**：

| 情况 | 选择 |
| --- | --- |
| 默认（非刚性） | `method="RK45"`（默认） |
| 高精度需求 | `"DOP853"` |
| 刚性方程（快慢尺度差很大） | `"BDF"`、`"Radau"`、`"LSODA"` |
| 需要高精度守恒 | 调小 `rtol/atol`（如 `1e-10`）并检查守恒量漂移 |

物理上重要的是**收敛性测试**：把 `rtol/atol` 减半再算一遍，结果变化应在允许误差内（例如能量守恒漂移）。

**常见陷阱**

- `rhs(t, y)` 的参数顺序是 `(t, y)`，写反会报形状错误或算出错误结果。
- `y0` 必须是一维序列（或 `solve_ivp` 能转成一维的数组）；返回的 `sol.y` 是 `(n 分量, m 时刻)`，用 `sol.y[0]` 取第一个分量。
- 能量/角动量等守恒量要单独画图检查，别只看解的曲线「像不像」。
- 刚性方程用 RK45 会极慢甚至失败：换 BDF。
- 长时间积分到无穷不用 `t_span=(0, np.inf)`：自己定合理终点，或用事件终止。

### 3.7 稀疏矩阵与大本征值问题

有限差分、有限元离散化出来的矩阵绝大多数元素是 0，必须用稀疏格式，否则内存和时间都爆炸。

```python
import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh

N, L = 2000, 20.0
x = np.linspace(-L, L, N)
dx = x[1] - x[0]

diag = 1.0/dx**2 + 0.5*x**2          # H = -1/2 d²/dx² + x²/2（自然单位）
off = -0.5/dx**2 * np.ones(N - 1)
H = diags([off, diag, off], [-1, 0, 1], format="csr")

vals = eigsh(H, k=5, which="SA", return_eigenvectors=False)   # 最小的 5 个
print(np.round(np.sort(vals), 4))    # [0.5 1.5 2.5 3.5 4.5]
```

常用格式：`csr`（行压缩，矩阵向量乘最快）、`csc`（列压缩，适合切片）、`dia`（对角）、`lil`（逐项构建）。构建时用坐标格式 `coo` 最方便。

**常见陷阱**

- `eigsh` 是迭代法：`k` 必须远小于矩阵维度，且只能求部分本征值；要全部本征值就回退到稠密 `np.linalg.eigh`（维度小才行）。
- `which="SA"`（最小代数）与 `"SM"`（最小模）含义不同：求基态用 `SA`。
- 稀疏矩阵运算（`*`）是矩阵乘法，逐元素乘法要用 `A.multiply(B)`。

### 3.8 傅里叶变换与空间算法速览

```python
from scipy import fft
import numpy as np

fs = 1000.0
t = np.arange(0, 1.0, 1/fs)
sig = np.sin(2*np.pi*50*t) + 0.01*np.random.default_rng(0).normal(size=t.size)

Y = fft.rfft(sig)
freqs = fft.rfftfreq(t.size, d=1/fs)
print(freqs[np.argmax(np.abs(Y))])       # 50.0
```

`scipy.fft` 与 `numpy.fft` API 基本相同，通常更快，且支持多线程（`workers=`）。物理例子：二维衍射、谱方法求解 PDE。

```python
from scipy.spatial import cKDTree, ConvexHull
import numpy as np

# 周期性边界下的最近邻距离（如粒子模拟）
rng = np.random.default_rng(3)
pos = rng.random((500, 3)) * 10.0
tree = cKDTree(pos, boxsize=10.0)        # boxsize 表示周期立方盒
d, idx = tree.query(pos, k=2)            # 最近的是自己，k=2 取真正邻居
print(d[:, 1].mean())

# 点集凸包体积（如粒子团几何分析）
hull = ConvexHull(rng.random((200, 3)))
print(hull.volume)
```

### 3.9 统计分布与检验 `stats`

```python
from scipy import stats
import numpy as np

rng = np.random.default_rng(5)
data = rng.normal(loc=2.0, scale=0.5, size=200)

mu, sigma = stats.norm.fit(data)         # 分布拟合
print(mu, sigma)

print(stats.norm.pdf(2.0, mu, sigma))    # 概率密度
print(stats.norm.cdf(2.5, mu, sigma))    # 累积分布
print(stats.norm.interval(0.95, mu, sigma))   # 95% 区间

print(stats.shapiro(data).pvalue)        # 正态性检验：p > 0.05 不拒绝正态

# 线性回归（含标准误）
x = np.linspace(0, 10, 50)
y = 1.5*x + 2.0 + rng.normal(0, 1.0, x.size)
res = stats.linregress(x, y)
print(res.slope, res.intercept, res.stderr, res.rvalue**2)
```

### 3.10 综合示例：有限差分 + 稀疏本征值 + 拟合

目标：解一维量子势阱基态能量随势阱宽度的变化，并拟合出 `E ∝ 1/L²`。

```python
import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
from scipy.optimize import curve_fit

def ground_energy(L, N=800):
    x = np.linspace(-L/2, L/2, N)
    dx = x[1] - x[0]
    diag = 1.0/dx**2                       # 无限深势阱内的自由粒子
    off = -0.5/dx**2 * np.ones(N - 1)
    H = diags([off, diag, off], [-1, 0, 1], format="csr")
    e = eigsh(H, k=1, which="SA", return_eigenvectors=False)
    return e[0]

Ls = np.linspace(1.0, 4.0, 16)
Es = np.array([ground_energy(L) for L in Ls])
print(Es[:3])

popt, pcov = curve_fit(lambda L, a: a/L**2, Ls, Es, p0=[5.0])
print(popt, np.sqrt(np.diag(pcov)))        # 接近 π²/2 ≈ 4.9348
```

## 练习

1. 用 `quad` 计算 `∫₋∞^∞ e^{-x²} dx`、`∫₀^π sin²x dx`，并验证与解析值 `√π`、`π/2` 的误差。
2. 用 `simpson` 和 `trapezoid` 分别积分 `sin(x)` 在 `[0, π]` 上的 11 个采样点，比较误差量级，验证辛普森法的阶数。
3. 给 3.5 节的高斯拟合并加入 `sigma=1` 的离群点，观察 `popt` 与 `perr` 的变化；再用 `stats` 做残差正态性检验。
4. 用 `solve_ivp` 解受迫振子 `x'' + 0.2x' + x = cos(0.9t)`，画振幅随时间的变化；扫描驱动频率找到共振峰。
5. 用 `eigsh` 求一维谐振子的前 10 个本征值，并与解析值 `n + 1/2` 比较误差；研究误差随 `N` 的收敛。
6. 用 `stats.norm.fit` 拟合一组模拟测量数据，并用 `stats.ttest_1samp` 检验均值是否等于真值。

## 自测清单

- [ ] 能说出各子模块对应的任务，遇到新问题知道去查哪个模块
- [ ] 会用 `quad/dblquad` 与 `trapezoid/simpson`
- [ ] 会用 `CubicSpline`、`RegularGridInterpolator`，知道外推风险
- [ ] 会用 `minimize/brentq/curve_fit`，并会报告参数误差与残差
- [ ] 会用 `solve_ivp` 化一阶方程组、设 `rtol/atol`、用事件检测
- [ ] 能判断刚性并选择合适的方法
- [ ] 会用 `diags` + `eigsh` 处理大规模本征值问题
- [ ] 知道 `scipy.fft`、`cKDTree`、`stats` 的入门用法

## 参考资料

- SciPy 官方文档：https://docs.scipy.org/doc/scipy/
- `solve_ivp` 教程：https://docs.scipy.org/doc/scipy/reference/integrate.html
- `curve_fit` 文档：https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html
- Newman, *Computational Physics*（SciPy 风格的计算物理教材）
