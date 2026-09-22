# 05 Numba 加速计算指南（计算物理方向）

## 学习目标

- 理解 Numba 做什么：把纯 Python/NumPy 函数 **JIT 编译**成机器码，让显式循环接近 C 的速度；
- 会用 `@njit` 改写「向量化不掉」的循环（分子动力学、伊辛模型、显式时间推进）；
- 知道编译开销、类型推断、`cache=True` 预热与缓存；
- 会用 `parallel=True` + `prange` 做并行，并遵守并行安全规则；
- 会读 `TypingError`、用 `NUMBA_DISABLE_JIT=1` 等工具排查问题；
- 知道 Numba 的边界（哪些语法/库不支持），以及何时该改用 Cython/JAX/C。

## 前置知识

- Python 函数、循环；NumPy 基础（[01-NumPy](01-NumPy数值计算指南.md)）。
- 不需要 CUDA 或并行计算基础；并行部分只需要知道「多线程」的直观概念。

## 什么情况该用 Numba

| 场景                                         | 首选方案                                     |
| -------------------------------------------- | -------------------------------------------- |
| 公式能写成数组运算                           | NumPy 向量化（[01](01-NumPy数值计算指南.md)） |
| 循环依赖前一步状态、逐格点/逐粒子更新        | **Numba**                              |
| 每步操作太碎，NumPy 每步的临时数组开销占主导 | **Numba**                              |
| 需要调用任意第三方库（pandas、网络、文件）   | 纯 Python，把热点函数抽出用 Numba            |
| 计算瓶颈能靠矩阵乘法解决                     | NumPy/BLAS（`@`、`np.dot`）              |
| 集群上还能改写算法                           | 先考虑算法（FFT、稀疏矩阵），再考虑 Numba    |

一句话：**Numba 是「写起来像 Python、跑起来像 C」的局部加速器**，不是通用万能药；调用一次的开销约微秒级，只值得用在「被调用次数少、内部循环次数多」的函数上。

## 正文

### 5.1 安装与第一个例子

```bash
python -m pip install numba
python -c "import numba; print(numba.__version__)"
```

- Numba 依赖 `llvmlite`；pip 在 Windows/Linux x86_64 上有预编译包，conda/mamba 更省心。
- **Python 版本兼容性**：Numba 支持的 Python 版本通常比官方最新版滞后，安装失败优先怀疑版本不匹配。
- 检查环境：`python -m numba.runtests -m 1 numba.tests.test_basic` 或 `numba -s`。

对比三种写法：纯 Python 循环、NumPy 向量化、Numba 编译。

```python
import random
import time
import numpy as np
import numba
from numba import njit, prange


def mc_pi_py(n):
    random.seed(42)
    cnt = 0
    for _ in range(n):
        x = random.random()
        y = random.random()
        if x*x + y*y <= 1.0:
            cnt += 1
    return 4.0*cnt/n


@njit
def mc_pi_numba(n, seed):
    np.random.seed(seed)          # 注意：只有 jit 函数内部调用才能给 Numba 随机数播种
    cnt = 0
    for _ in range(n):
        x = np.random.random()
        y = np.random.random()
        if x*x + y*y <= 1.0:
            cnt += 1
    return 4.0*cnt/n


def mc_pi_numpy(n, seed):
    rng = np.random.default_rng(seed)
    x = rng.random(n)
    y = rng.random(n)
    return 4.0*np.mean(x*x + y*y <= 1.0)


n = 5_000_000
t0 = time.perf_counter(); mc_pi_py(n);      print("python ", time.perf_counter() - t0)
t0 = time.perf_counter(); mc_pi_numpy(n, 42); print("numpy  ", time.perf_counter() - t0)

mc_pi_numba(1, 42)              # 预热：触发编译（第一次调用含编译时间）
t0 = time.perf_counter(); mc_pi_numba(n, 42); print("numba  ", time.perf_counter() - t0)
```

典型结果（量级）：纯 Python 慢十倍以上，Numba 与 NumPy 同量级或更快；大 `n` 时 Numba 不需要一次分配两个长度为 `n` 的随机数组，更省内存。

要点：

- `@njit` 等价于 `@jit(nopython=True)`：**禁止回退到 Python 解释执行**，类型不合法直接报错。
- 第一次调用会编译（可能几秒），之后调用只跑机器码。**计时前要预热**。
- `np.random.seed(seed)` 必须在被编译的函数内部调用；在外部调用只影响 NumPy 自己的随机数（见 Numba 文档说明）。

### 5.2 编译开销与缓存

```python
@njit(cache=True)
def slow_function(x):
    s = 0.0
    for i in range(x.size):
        s += x[i]*x[i]
    return s
```

- `cache=True`：把编译结果写到 `__pycache__/*.nbi/*.nbc`，同一函数下次启动进程直接加载，不再编译。
- 缓存键与函数源码、参数类型、Numba 版本有关；改了源码就会重新编译。
- 只被调用一两次的短函数不值得 Numba；把「外层一次调用、内部大循环」的部分作为 jit 函数。

### 5.3 支持的类型与语法边界

**支持得好**：

- NumPy 数组、标量（int/float/complex/bool）、元组、`namedtuple`、`range/prange`；
- NumPy 的大部分数组方法与 ufunc（`np.exp/sin/sqrt`、`np.dot`、`np.linalg` 的常见函数）；
- 老式 `np.random.*` 顶层函数（线程安全，见 5.5）。

**支持有限或要注意**：

- Python 容器：`list`、`dict`、`set` 可以使用，但**容器元素类型必须一致**；嵌套 `list[list[float]]` 性能差，建议换成二维数组；跨 jit 边界的 list 是「反射列表」（reflected list），很慢，最好传数组。
- 类的支持有限：`@jitclass` 可定义数据结构；一般 OOP 代码不要指望直接 `@njit`。
- pandas、SymPy、大部分第三方库**不支持**；把数据先转成 NumPy 数组，只把数值内核放进 Numba。
- 字符串处理、异常、`try/except`、生成器、装饰器（多数）不支持或受限。
- 并非全部 NumPy API 支持：例如 `np.einsum`、部分 `axis` 参数、`np.linalg` 的个别函数可能报 `TypingError`。遇到不支持的函数，症状是编译期错误，把它改写成循环即可。

**类型推断**：Numba 根据实参类型编译专门版本。`mc_pi_numba(1_000_000, 42)` 与 `mc_pi_numba(np.int64(1), 42)` 是两次编译；`int` 与 `float` 混用没问题，但不要让同一个函数一会儿收标量一会儿收数组。

```python
print(mc_pi_numba.signatures)     # 已编译的签名列表
```

### 5.4 显式签名与编译选项

```python
from numba import njit
import numba

@njit("float64(int64, int64)")     # 显式签名：参数类型与返回类型
def add_int(a, b):
    return a + b

@njit(numba.float64(numba.int64, numba.int64))
def add_int2(a, b):
    return a + b
```

常用选项：

| 选项            | 默认         | 作用与注意                                         |
| --------------- | ------------ | -------------------------------------------------- |
| `cache`       | `False`    | 缓存编译结果到磁盘                                 |
| `fastmath`    | `False`    | 允许重排浮点运算（更快）；可能牺牲精度与 IEEE 语义 |
| `boundscheck` | `False`    | `True` 做数组越界检查，便于调试，但变慢          |
| `error_model` | `"python"` | 除零抛异常；`"numpy"` 按 NumPy 语义返回 inf/nan  |
| `nogil`       | `False`    | 释放 GIL，可与`threading` 配合                   |
| `parallel`    | `False`    | 启用`prange` 与自动并行                          |
| `inline`      | `"never"`  | `"always"` 内联小函数，减少调用开销              |

生产代码推荐组合：`@njit(cache=True, fastmath=True)`（精度敏感的任务慎用 `fastmath`）。

### 5.5 并行：`parallel=True` 与 `prange`

`prange` 只在 `parallel=True` 下并行；否则等价于 `range`。并行安全的第一条：**迭代之间不能有数据依赖**（不能读别人正在写的元素）。

安全的并行：蒙特卡洛。

```python
@njit(parallel=True)
def mc_pi_parallel(n):
    cnt = 0
    for _ in prange(n):
        x = np.random.random()
        y = np.random.random()
        if x*x + y*y <= 1.0:
            cnt += 1
    return 4.0*cnt/n
```

- `cnt += 1` 是 Numba 自动处理的**归约**（支持 `+= -= *= /=`、`min/max`）：多个线程各累各的，最后合并，安全。
- 老式 `np.random.*` 的随机数生成器是线程安全的，**每个线程有独立的随机流**；但正因如此，并行版本的数值与串行版本不同，也不能保证逐位复现。
- **不要**在并行代码里用 `np.random.Generator`（`default_rng`）：Numba 文档明确说明它不线程安全。

**反例**（会得到错误结果，Numba 文档专门警告）：

```python
@njit(parallel=True)
def wrong(x):
    n = x.shape[0]
    y = np.zeros(4)
    for i in prange(n):
        y[i % 4] += x[i]          # 多个线程同时写 y 的同一个元素：竞态
    return y
```

并行规则速查：

- 迭代只写自己负责的数组位置（`out[i] = f(x[i])`）→ 安全；
- 标量归约（`s += x[i]`）→ 安全（Numba 自动处理）；
- 向 `list/dict/set` 写是**不线程安全**的，禁止；
- 嵌套 `prange` 不会嵌套并行，内层会被串行化；
- 需要线程数控制：`numba.set_num_threads(8)`、`numba.get_num_threads()`。

调试并行是否正确：

```python
mc_pi_parallel.parallel_diagnostics(level=4)     # 打印哪个循环被并行/融合/串行化
# 或运行前设置环境变量 NUMBA_PARALLEL_DIAGNOSTICS=4
```

### 5.6 实战案例：一维扩散方程的时间推进

问题：显式差分求解 `∂u/∂t = D ∂²u/∂x²`，中心差分、双缓冲 Jacobi 更新。

```python
import numpy as np
import time
from numba import njit


@njit(cache=True)
def diffuse_numba(nx, nt, c):
    u = np.zeros(nx)
    u[nx//2] = 1.0                       # 初始时刻中心一个脉冲
    v = np.zeros_like(u)
    for _ in range(nt):
        for i in range(1, nx - 1):
            v[i] = u[i] + c*(u[i-1] - 2.0*u[i] + u[i+1])
        u, v = v, u
    return u


def diffuse_numpy(nx, nt, c):
    u = np.zeros(nx)
    u[nx//2] = 1.0
    v = np.zeros_like(u)
    for _ in range(nt):
        v[1:-1] = u[1:-1] + c*(u[:-2] - 2.0*u[1:-1] + u[2:])
        u, v = v, u
    return u


nx, nt, c = 500, 20_000, 0.4             # 稳定性要求 c ≤ 0.5

t0 = time.perf_counter(); a = diffuse_numpy(nx, nt, c);  print("numpy ", time.perf_counter()-t0)
diffuse_numba(10, 10, 0.4)               # 预热
t0 = time.perf_counter(); b = diffuse_numba(nx, nt, c);  print("numba ", time.perf_counter()-t0)
print(np.allclose(a, b))                 # True：两种实现结果一致
```

- 网格越小、时间步越多，Numba 优势越明显：NumPy 每一步都要建临时数组、走 Python 解释器，而 Numba 把整个双循环编译成紧凑机器码。
- 物理提示：显式扩散方程要求 `c = D·dt/dx² ≤ 1/2`，否则数值不稳定；加速不改变稳定性条件。

### 5.7 调试常见错误

**`TypingError`**：编译期类型错误，最常见。

- 报错信息会给出函数名和源码行号；先看第一处「Failed in nopython mode pipeline」。
- 常见原因：用了不支持的库/方法（pandas、`np.einsum` 的某些用法）、传了 Python 容器而不是数组、变量类型前后不一致（先赋值整数后赋值数组）。
- 解决套路：把不支持的调用移到 jit 函数外；把 list 换成 `np.asarray`；把类型固定下来。

**调试技巧**：

```python
# 1) 用原始 Python 版本排查逻辑错误（不是类型错误）
#    运行前设置环境变量 NUMBA_DISABLE_JIT=1，@njit 函数会按普通 Python 执行
#    Windows PowerShell:  $env:NUMBA_DISABLE_JIT = "1"
#    Linux/WSL:           export NUMBA_DISABLE_JIT=1

# 2) 直接调用未编译版本
mc_pi_numba.py_func(1000, 42)

# 3) 查看已编译签名与中间类型
print(mc_pi_numba.signatures)
mc_pi_numba.inspect_types()      # 输出较长，重定向到文件查看
```

**静默回退**：用 `@jit`（不带 `nopython`）时，类型不支持会回退到 object mode，速度可能比纯 Python 还慢。**统一用 `@njit`**，让问题在编译期暴露。

### 5.8 CUDA 入门（有 NVIDIA GPU 再看）

Numba 能把 kernel 编译到 GPU。需要 NVIDIA 显卡与驱动；用 `numba -s` 查看 CUDA 是否可用。

```python
from numba import cuda
import numpy as np

@cuda.jit
def add_kernel(a, b, c):
    i = cuda.grid(1)                 # 全局线程编号
    if i < c.size:
        c[i] = a[i] + b[i]

n = 1 << 20
a = np.ones(n)
b = np.ones(n)
c = np.zeros(n)

threads = 256
blocks = (n + threads - 1)//threads
add_kernel[blocks, threads](a, b, c)   # 启动：自动完成主机↔设备拷贝
print(c[:3], c.sum())                  # [2. 2. 2.] 2097152.0
```

概念对应：`@cuda.jit` 相当于 `@njit(parallel=True)` 的 GPU 版；`[blocks, threads]` 是网格配置；kernel 内要自己做边界判断 `if i < size`。物理上适合逐格点的显式更新（格子玻尔兹曼、热扩散、波场模拟）。入门阶段先把 CPU 上的 Numba 用熟，GPU 需要额外处理内存拷贝与线程块设计。

### 5.9 Numba 之外的选择

| 方案         | 适合                    | 代价                         |
| ------------ | ----------------------- | ---------------------------- |
| NumPy 向量化 | 公式可写成数组运算      | 迭代依赖问题不适用           |
| Numba        | 数值循环、逐粒子/逐格点 | 只能编译支持的语法，编译开销 |
| Cython       | 需要精细控制、调用 C 库 | 需要编译配置与类型声明       |
| C/C++ 扩展   | 极致性能、复用现有代码  | 工程量大，见阶段 03          |
| JAX          | 需要自动微分 + GPU/TPU  | 编程范式不同，需改写代码     |

路线建议：先 NumPy，再 Numba，仍不够再考虑 C 或 GPU。

## 练习

1. 把 [01-NumPy](01-NumPy数值计算指南.md) 练习 3 的「随机撒点求球体积」写成 `@njit` 版本，与 NumPy 向量化版本对比 `n = 10^7` 时的耗时（注意先预热）。
2. 用 Numba 写一维伊辛模型的 Metropolis 单自旋翻转（`N = 1000` 格点，周期性边界），计算能量与磁化强度随步数的变化；再用 `parallel=True` 并行跑 8 个独立样本取平均，注意每个样本的随机流相互独立。
3. 用 Numba 写速度 Verlet 的二维 Lennard-Jones 分子动力学（`N = 200` 粒子、周期性边界、只算截断半径内的力），统计动能随时间的漂移，验证能量守恒。
4. 给 5.6 节的扩散方程加上固定边界条件 `u(0) = u(L) = 0` 之外的两种边界（绝热：`u[0] = u[1]`），比较结果。
5. 把 5.5 节的 `wrong` 函数与修正版（每个线程写自己的数组、最后合并）都跑一遍，观察错误结果出现的概率，并解释为什么「有时看起来是对的」。

## 自测清单

- [ ] 能说清什么时候用向量化、什么时候用 Numba
- [ ] 会写 `@njit` 函数，知道首次调用含编译时间，会预热与 `cache=True`
- [ ] 知道 `np.random.seed` 要在 jit 函数内部调用，`Generator` 不能在并行区用
- [ ] 会写 `prange` 并行，能判断归约与竞态，会用 `parallel_diagnostics`
- [ ] 遇到 `TypingError` 能定位并改写代码，知道 `NUMBA_DISABLE_JIT=1` 与 `.py_func`
- [ ] 知道 Numba 不支持 pandas、SymPy 等库，数据要先转数组
- [ ] 了解 CUDA kernel 的基本写法与适用场景（即使没有 GPU）
- [ ] 知道 Numba 的替代方案（Cython、C、JAX）各自的位置

## 参考资料

- Numba 官方文档：https://numba.readthedocs.io/
- 支持的 Python 特性：https://numba.readthedocs.io/en/stable/reference/pysupported.html
- 支持的 NumPy 特性：https://numba.readthedocs.io/en/stable/reference/numpysupported.html
- 自动并行化：https://numba.readthedocs.io/en/stable/user/parallel.html
- CUDA 入门：https://numba.readthedocs.io/en/stable/cuda/index.html
