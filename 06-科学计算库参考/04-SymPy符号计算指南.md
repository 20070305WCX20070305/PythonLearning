# 04 SymPy 符号计算指南（计算物理方向）

## 学习目标

- 会创建符号、表达式，做化简、展开、因式分解、代入求值；
- 会做符号微积分：求导、积分（定/不定）、极限、泰勒展开、求和；
- 会解代数方程、方程组、常微分方程；
- 会用符号矩阵做行列式、逆、本征值；
- 能用拉格朗日力学推导运动方程、验证量子对易关系；
- 会用 `lambdify` 把符号表达式转成 NumPy/SciPy 可用的数值函数；
- 知道符号计算的性能边界，什么该交给数值方法。

## 前置知识

- Python 基础、微积分与线性代数基础。
- 数值部分需要 NumPy（[01-NumPy](01-NumPy数值计算指南.md)）。

## 建议用法

- 最适合的场景：**推导公式、验证解析结果、生成可复用代码**。
- 在 Jupyter 里用 `sp.init_printing()` 获得漂亮的排版；脚本里用 `sp.latex(expr)` 输出公式。

## 正文

### 4.1 符号、表达式与基本操作

```python
import sympy as sp

sp.init_printing()                       # Jupyter 中启用排版（脚本中可省）

x, y, t = sp.symbols("x y t", real=True)
n = sp.symbols("n", integer=True, positive=True)   # 带假设的符号

expr = (x + y)**2
print(sp.expand(expr))                   # x² + 2xy + y²
print(sp.factor(x**2 - 1))               # (x-1)(x+1)
print(sp.simplify(sp.sin(x)**2 + sp.cos(x)**2))    # 1
print(sp.apart(1/(x**2 - 1), x))         # 部分分式

# 代入与数值化
f = sp.exp(-x**2)
print(f.subs(x, 1))                      # e^{-1}
print(f.subs(x, 1).evalf())              # 0.367879441171442
print(f.subs(x, sp.Rational(1, 2)).evalf())   # 用有理数更干净
```

**关键习惯**

- 符号计算里**不要用浮点数**（如 `0.5`）：结果会退化成数值近似。用 `sp.Rational(1, 2)`、`sp.sqrt(2)`、`sp.pi`。
- 给符号加假设（`real=True, positive=True`）能显著加快化简并避免错误分支。
  `sp.sqrt(x**2)` 对一般 `x` 不化简，对 `positive=True` 的 `x` 直接得 `x`。
- `simplify` 是万能但慢的最后一招；优先用目标明确的 `expand/factor/trigsimp/cancel`。

### 4.2 微积分

```python
f = sp.sin(x) * sp.exp(-x)

print(sp.diff(f, x))                     # 一阶导
print(sp.diff(f, x, 2))                  # 二阶导
print(sp.diff(sp.exp(-x**2), x))         # -2x e^{-x²}

# 不定积分与定积分
print(sp.integrate(sp.exp(-x**2), x))                    # √π/2 · erf(x)
print(sp.integrate(sp.exp(-x**2), (x, -sp.oo, sp.oo)))   # √π
print(sp.integrate(sp.sin(x)**2, (x, 0, sp.pi)))         # π/2

# 极限
print(sp.limit(sp.sin(x)/x, x, 0))                       # 1
print(sp.limit((1 + 1/n)**n, n, sp.oo))                  # e

# 泰勒展开与求和
print(sp.series(sp.cos(x), x, 0, 6))                     # 1 - x²/2 + x⁴/24 + O(x⁶)
print(sp.summation(1/n**2, (n, 1, sp.oo)))               # π²/6
```

物理用途：**验证数值结果**。例如把解析导数与数值差分对比：

```python
import numpy as np

f = sp.exp(-x**2)
dfdx = sp.diff(f, x)
f_num = sp.lambdify(x, f, modules="numpy")
df_num = sp.lambdify(x, dfdx, modules="numpy")

xs = np.linspace(-2, 2, 101)
fd = (f_num(xs[2:]) - f_num(xs[:-2])) / (xs[2:] - xs[:-2])
print(np.abs(fd - df_num(xs[1:-1])).max())     # 约 1e-4，符合中心差分误差
```

### 4.3 解方程与微分方程

```python
# 代数方程
print(sp.solve(x**2 - 2, x))                            # [-√2, √2]
print(sp.solve([x + y - 3, x - y - 1], [x, y]))         # {x: 2, y: 1}

# 超越方程（符号解不存在时）
print(sp.solveset(sp.exp(x) - 3, x, domain=sp.S.Reals)) # {log(3)}
print(sp.nsolve(sp.cos(x) - x, x, 1))                   # 0.739085...（数值解）

# 常微分方程
y = sp.Function("y")
ode = sp.Eq(y(t).diff(t, 2) + 4*y(t), 0)
print(sp.dsolve(ode, y(t)))                             # C₁ sin2t + C₂ cos2t

# 带初值
sol = sp.dsolve(ode, y(t), ics={y(0): 1, y(t).diff(t).subs(t, 0): 0})
print(sol)                                              # cos(2t)
```

**常见陷阱**

- `solve` 适合多项式/方程组；超越方程可能返回空或不完整，改用 `solveset`（给定义域）或 `nsolve`（给初值）。
- `dsolve` 的初值条件用 `ics={...}`；求 `y'(0)` 要写 `y(t).diff(t).subs(t, 0)`。
- 解里的常数写成 `C1, C2`；要让 SymPy 按物理条件定常数，先代入条件再 `solve`。

### 4.4 符号矩阵与线性代数

```python
A = sp.Matrix([[2, 1], [1, 2]])

print(A.det())                       # 3
print(A.inv())
print(A.eigenvects())                # [(1, 1, [...]), (3, 1, [...])]

b = sp.Matrix([1, 0])
print(A.solve(b))                    # 解 Ax = b

# 符号矩阵（例如含参数的本征值）
a = sp.symbols("a", positive=True)
M = sp.Matrix([[a, 1], [1, a]])
print(M.eigenvals())                 # {a-1: 1, a+1: 1}
```

### 4.5 物理推导实例

**（1）拉格朗日力学：单摆运动方程**

拉格朗日量 `L = T - V = ½ml²θ̇² + mgl cosθ`，欧拉-拉格朗日方程：

$$
\frac{d}{dt}\frac{\partial L}{\partial \dot\theta} - \frac{\partial L}{\partial \theta} = 0
$$

```python
t = sp.symbols("t", positive=True)
m, l, g = sp.symbols("m l g", positive=True)
theta = sp.Function("theta")(t)

L = m*l**2*sp.diff(theta, t)**2 / 2 + m*g*l*sp.cos(theta)
EL = sp.diff(sp.diff(L, sp.diff(theta, t)), t) - sp.diff(L, theta)

print(sp.simplify(EL))                                    # m l (l θ̈ + g sinθ)
sol = sp.solve(sp.Eq(EL, 0), sp.diff(theta, t, 2))
print(sol)                                                # [-g sin(θ)/l]
```

用同样流程可以推导耦合振子、双摆、圆环上的珠子等系统的运动方程，再把结果 `lambdify` 后交给 `solve_ivp` 数值求解（[03-SciPy](03-SciPy数值算法指南.md)）。

**（2）量子力学：验证对易关系 `[x, p] = iħ`**

把算符作用在测试函数 ψ(x) 上：

```python
x = sp.Symbol("x", real=True)
hbar = sp.Symbol("hbar", positive=True)
psi = sp.Function("psi")(x)

def X(f):                                # 位置算符：乘 x
    return x*f

def P(f):                                # 动量算符：-iħ d/dx
    return -sp.I*hbar*sp.diff(f, x)

comm = sp.simplify(X(P(psi)) - P(X(psi)))
print(comm)                              # I*hbar*psi(x)，即 [x,p] = iħ
```

更系统的量子算符代数（对易子、产生/湮灭算符、角动量）可查 `sympy.physics.quantum` 模块。

**（3）统计物理：配分函数与热力学量**

以一维谐振子 `E_n = ħω(n + 1/2)` 为例：

```python
beta, hbar, omega, kb, T = sp.symbols("beta hbar omega k_B T", positive=True)
n = sp.symbols("n", integer=True, nonnegative=True)

Z = sp.summation(sp.exp(-beta*hbar*omega*(n + sp.Rational(1, 2))), (n, 0, sp.oo))
print(sp.simplify(Z))                    # e^{-βħω/2} / (1 - e^{-βħω})

U_beta = sp.simplify(-sp.diff(sp.log(Z), beta))
U = sp.simplify(U_beta.subs(beta, 1/(kb*T)))
Cv = sp.simplify(sp.diff(U, T))
print(U)                                 # 平均能量 ħω/2 + ħω/(e^{ħω/kT} - 1)
print(Cv)                                # 热容，低频极限趋于 k_B
```

### 4.6 `lambdify`：符号 → 数值

```python
import numpy as np

x, a = sp.symbols("x a", real=True)
expr = sp.exp(-a*x**2)

f = sp.lambdify((x, a), expr, modules="numpy")    # 两个参数
xs = np.linspace(-3, 3, 200)
print(f(xs, 0.5).shape)                           # (200,)

# 也可以用 "scipy" 模块生成可用 quad 的被积函数
g = sp.lambdify(x, expr.subs(a, 1.0), modules="scipy")
from scipy.integrate import quad
print(quad(g, 0, np.inf))                         # (√π/2, ...)
```

**性能提示**

- `lambdify` 生成的函数是普通 Python/NumPy 调用，速度快，适合放进循环。
- 不要在数值循环里调用 `expr.subs(...).evalf()`：那会逐点走符号引擎，慢几个数量级。

### 4.7 输出公式：LaTeX 与代码

```python
expr = sp.Integral(sp.exp(-x**2), (x, -sp.oo, sp.oo))
print(sp.latex(expr))                    # \int_{-\infty}^{\infty} e^{- x^{2}}\, dx

# 生成 C/Fortran/NumPy 代码
from sympy.printing import pycode, ccode, fcode
print(pycode(sp.diff(sp.cos(x), x)))
print(ccode(sp.diff(sp.cos(x), x)))
```

做笔记/写论文（LaTeX）时用 `sp.latex(...)` 把结果贴进公式环境；代码生成用于把推导结果嵌进高性能程序。

### 4.8 性能与常见陷阱

- 符号计算复杂度随表达式规模爆炸：**先代入数值再化简**往往更快；能用数值方法（SciPy）就不要硬做符号积分。
- 大矩阵的符号本征值/逆可能极慢：先化成小参数问题或数值求解。
- `sp.simplify` 慢且不一定成功：用 `sp.cancel`（有理函数）、`sp.trigsimp`（三角）、`sp.expand` 等定向化简。
- 假设（`positive`、`real`）能避免 `sqrt(x²)` 不分岔、`abs` 不化简等问题，务必显式声明。
- 浮点数污染：`sp.sin(0.1)` 不会保持符号；改写 `sp.sin(sp.Rational(1, 10))`。
- SymPy 与 NumPy 混用要看类型：`np.sin(sp.Symbol("x"))` 会报错；反过来 `sp.sin(np.array(...))` 会逐元素走符号引擎（很慢）。

## 练习

1. 用 SymPy 推导**受阻尼的单摆**运动方程（加入与角速度成正比的阻力矩），并验证 `g/l → 0` 时退化为 `θ̈ = -γθ̇`。
2. 求 `∫₀^π x sin(nx) dx` 的符号结果（`n` 为整数），并讨论 `n` 为偶数/奇数时的差异。
3. 用 `sp.solve` 解两体碰撞的动量与能量守恒方程组，求碰后速度的符号表达式。
4. 推导一维无限深势阱 `ψ_n = √(2/L) sin(nπx/L)` 的正交归一性 `∫₀^L ψ_m ψ_n dx = δ_{mn}`。
5. 用 `lambdify` 把双原子分子 Morse 势 `V(r) = D(1 - e^{-a(r-r0)})²` 转成 NumPy 函数，并用 `minimize` 验证极小点在 `r = r0`。
6. 用 `dsolve` 解 RC 电路方程 `V' = (V_in - V)/(RC)`，再代入阶跃输入求响应。

## 自测清单

- [ ] 会创建带假设的符号，知道为什么避免使用浮点数
- [ ] 会 `diff/integrate/limit/series/summation`，能验证解析导数
- [ ] 会用 `solve/solveset/nsolve`，知道各自适用场景
- [ ] 会用 `dsolve` 解 ODE 并代入初值条件
- [ ] 会用符号矩阵求行列式、逆、本征值
- [ ] 能用拉格朗日方法推导运动方程并转数值求解
- [ ] 会用 `lambdify` 转 NumPy/SciPy 函数，知道数值循环里别用 `subs`
- [ ] 知道符号计算的性能边界，该转数值时转数值

## 参考资料

- SymPy 官方文档：https://docs.sympy.org/
- SymPy 教程：https://docs.sympy.org/latest/tutorials/intro-tutorial/index.html
- 量子模块：https://docs.sympy.org/latest/modules/physics/quantum/index.html
- 力学模块：https://docs.sympy.org/latest/modules/physics/mechanics/index.html
