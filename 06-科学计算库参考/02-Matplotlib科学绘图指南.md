# 02 Matplotlib 科学绘图指南（计算物理方向）

## 学习目标

- 掌握「Figure + Axes」面向对象接口，能画多子图、共享坐标轴；
- 会画曲线、散点、误差棒、直方图、对数坐标图；
- 会画二维场（`imshow/pcolormesh`）、等高线、三维曲面；
- 会用 `FuncAnimation` 做演化动画；
- 会配置字体、数学公式、dpi 与矢量图导出，产出论文级插图；
- 知道无显示器环境下如何画图（`Agg` 后端）。

## 前置知识

- Python 基础、NumPy 基础（[01-NumPy](01-NumPy数值计算指南.md)）。

## 建议用法

- 把示例存成 `.py` 运行；每节末尾的图都用 `fig.savefig` 保存下来对照。
- 以后画图时直接来查「某类图的模板」。

## 正文

### 2.1 两种接口与最小示例

Matplotlib 有两套接口：

- `plt.plot(...)` 状态机接口（脚本里快速画图）；
- `fig, ax = plt.subplots()` 面向对象接口（**推荐**，复杂图、多子图、封装函数都靠它）。

```python
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 2*np.pi, 400)
y = np.sin(x)

fig, ax = plt.subplots(figsize=(6, 4), dpi=120)   # 画布与坐标区
ax.plot(x, y, label=r"$\sin x$")                   # 画曲线
ax.set(xlabel="x (rad)", ylabel="y", title="正弦曲线")
ax.legend()
ax.grid(alpha=0.3)

fig.tight_layout()
fig.savefig("sin.png", dpi=300, bbox_inches="tight")
```

要点：

- `fig` 是整张图，`ax` 是坐标区；所有画图命令都挂在 `ax` 上。
- `r"$\sin x$"` 是 LaTeX 数学文本，`r` 前缀避免转义。
- 画完用 `plt.close(fig)` 释放内存，批量画图时尤其重要。

### 2.2 曲线图与常见修饰

```python
t = np.linspace(0, 10, 1000)
gamma, w0 = 0.3, 2.0
w = np.sqrt(w0**2 - (gamma/2)**2)
y = np.exp(-gamma*t/2) * np.cos(w*t)
env = np.exp(-gamma*t/2)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(t, y, color="C0", lw=1.5, label="阻尼振子 x(t)")
ax.plot(t, env, "k--", lw=1.0, label="包络")
ax.plot(t, -env, "k--", lw=1.0)                     # 无标签则不进入 legend
ax.axhline(0, color="gray", lw=0.8)                 # 水平参考线
ax.annotate("振幅衰减 $e^{-\\gamma t/2}$", xy=(3.5, 0.25),
            xytext=(4.5, 0.6), arrowprops=dict(arrowstyle="->"))
ax.set(xlabel="t (s)", ylabel="x (arb. units)", xlim=(0, 10), ylim=(-1.1, 1.1))
ax.legend(loc="upper right", frameon=False)
fig.tight_layout()
```

常用修饰速查：

| 需求 | 写法 |
| --- | --- |
| 线型/颜色/线宽 | `ls="--"`, `color="C1"`, `lw=2` |
| 标记点 | `marker="o"`, `ms=4`, `mec="k"` |
| 标签与图例 | `label=...` + `ax.legend()` |
| 坐标范围 | `ax.set_xlim(...)`, `ax.set_ylim(...)` |
| 参考线 | `ax.axhline / axvline / axhspan` |
| 箭头与文字 | `ax.annotate(...)`, `ax.text(...)` |
| 网格 | `ax.grid(alpha=0.3)` |
| 刻度朝内 | `ax.tick_params(direction="in", top=True, right=True)` |

### 2.3 多子图与共享坐标轴

```python
x = np.linspace(0, 2*np.pi, 400)

fig, axes = plt.subplots(2, 1, figsize=(6, 5), sharex=True,
                         gridspec_kw=dict(height_ratios=[2, 1]))
axes[0].plot(x, np.sin(x), label=r"$\sin x$")
axes[0].plot(x, np.cos(x), label=r"$\cos x$")
axes[0].legend(ncol=2, fontsize=9)
axes[1].plot(x, np.sin(2*x), color="C3")

axes[1].set_xlabel("x (rad)")
axes[0].set_ylabel("振幅")
axes[1].set_ylabel(r"$\sin 2x$")
fig.tight_layout()
```

不规则布局用 `gridspec`：

```python
fig = plt.figure(figsize=(7, 4))
gs = fig.add_gridspec(2, 2, width_ratios=[2, 1])
ax_main = fig.add_subplot(gs[:, 0])       # 左列跨两行
ax_top  = fig.add_subplot(gs[0, 1])
ax_bot  = fig.add_subplot(gs[1, 1])
```

### 2.4 误差棒、散点与直方图

```python
# 误差棒：带误差的实验数据点
t = np.linspace(0, 5, 12)
y = 2.5*np.exp(-0.4*t)
sigma = 0.05 + 0.02*y
fig, ax = plt.subplots(figsize=(6, 4))
ax.errorbar(t, y, yerr=sigma, fmt="o", ms=4, capsize=3,
            color="C0", ecolor="0.4", label="测量值")
ax.plot(t, y, ls="--", lw=1, color="C1", label=r"$2.5e^{-0.4t}$")
ax.set(xlabel="t (s)", ylabel="A(t)")
ax.legend()

# 直方图 + 正态拟合曲线
rng = np.random.default_rng(0)
data = rng.normal(1.0, 0.2, 2000)
fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(data, bins=50, density=True, alpha=0.6, color="C0", label="样本")
xs = np.linspace(0.2, 1.8, 200)
mu, sig = data.mean(), data.std(ddof=1)
ax.plot(xs, np.exp(-(xs-mu)**2/(2*sig**2))/(sig*np.sqrt(2*np.pi)),
        lw=2, color="C1", label="正态拟合")
ax.set(xlabel="测量值", ylabel="概率密度")
ax.legend()
```

### 2.5 对数坐标、刻度与双轴

```python
x = np.linspace(1, 100, 200)

fig, ax = plt.subplots(figsize=(6, 4))
ax.loglog(x, x**-2, label=r"$x^{-2}$")          # 双对数
ax.loglog(x, x**-1, label=r"$x^{-1}$")
ax.set(xlabel="x", ylabel="y")
ax.legend()

# 半对数 + 自定义刻度
fig, ax = plt.subplots(figsize=(6, 4))
t = np.linspace(0, 10, 300)
ax.semilogy(t, np.exp(-t), label=r"$e^{-t}$")
ax.set_yticks([1e-4, 1e-3, 1e-2, 1e-1, 1])
ax.set_xticks(np.arange(0, 11, 2))
ax.minorticks_on()

# 双 y 轴
fig, ax1 = plt.subplots(figsize=(6, 4))
ax2 = ax1.twinx()
ax1.plot(t, np.sin(t), color="C0")
ax2.plot(t, np.exp(-t), color="C1")
ax1.set_xlabel("t")
ax1.set_ylabel("sin t", color="C0")
ax2.set_ylabel(r"$e^{-t}$", color="C1")
```

### 2.6 二维场：`imshow` 与 `pcolormesh`

适合画波函数、势场、温度场、干涉条纹。注意 `imshow` 默认原点在左上角，物理图一般要 `origin="lower"`。

```python
x = np.linspace(-3, 3, 200)
y = np.linspace(-3, 3, 200)
X, Y = np.meshgrid(x, y)
Z = np.sin(X) * np.exp(-(X**2 + Y**2)/4)

fig, ax = plt.subplots(figsize=(5.5, 4.5))
im = ax.imshow(Z, extent=(-3, 3, -3, 3), origin="lower",
               cmap="RdBu_r", aspect="equal")
fig.colorbar(im, ax=ax, label="Z")
ax.set(xlabel="x", ylabel="y")

# 非均匀网格或需要精确坐标时用 pcolormesh
fig, ax = plt.subplots(figsize=(5.5, 4.5))
mesh = ax.pcolormesh(X, Y, Z, shading="auto", cmap="viridis")
fig.colorbar(mesh, ax=ax, label="Z")
```

常用 colormap：连续量 `viridis`；正负对称量 `RdBu_r`、`coolwarm`；感知均匀且适合灰度打印优先 `viridis`。

**常见陷阱**

- `imshow` 与 `pcolormesh` 对**行/列**的理解与 `meshgrid` 默认 `indexing="xy"` 有关；如果图像上下/左右颠倒，检查是否要 `origin="lower"` 或转置 `Z.T`。
- `imshow` 要设 `aspect="auto"` 才能自由拉伸长宽比，否则保持像素为正方形。

### 2.7 等高线

```python
fig, ax = plt.subplots(figsize=(5.5, 4.5))
cs = ax.contourf(X, Y, Z, levels=20, cmap="viridis")     # 填充
cl = ax.contour(X, Y, Z, levels=20, colors="k", linewidths=0.4)
ax.clabel(cl, inline=True, fontsize=8, fmt="%.1f")
fig.colorbar(cs, ax=ax, label="Z")
ax.set(xlabel="x", ylabel="y")
```

等势面、相空间轨道、能带图都常用 `contour`。想突出某条等值线（例如势能零点）只需 `levels=[0.0]`。

### 2.8 三维图

```python
fig = plt.figure(figsize=(6, 5))
ax = fig.add_subplot(projection="3d")

x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 80)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))

surf = ax.plot_surface(X, Y, Z, cmap="viridis", rcount=50, ccount=50,
                       linewidth=0, antialiased=True)
fig.colorbar(surf, ax=ax, shrink=0.6, label="Z")
ax.set(xlabel="x", ylabel="y", zlabel="z")
ax.view_init(elev=30, azim=-60)          # 视角
```

三维曲线（例如洛伦兹吸引子的轨迹）：

```python
from scipy.integrate import solve_ivp    # 解法见 03-SciPy 第 6 节

def lorenz(t, s):
    x, y, z = s
    return [10*(y - x), x*(28 - z) - y, x*y - 8*z/3]

sol = solve_ivp(lorenz, (0, 40), [1, 1, 1], rtol=1e-9, dense_output=True)
tt = np.linspace(0, 40, 20000)
xx, yy, zz = sol.sol(tt)

fig = plt.figure(figsize=(6, 5))
ax = fig.add_subplot(projection="3d")
ax.plot(xx, yy, zz, lw=0.5, color="C0")
ax.set(xlabel="x", ylabel="y", zlabel="z")
```

### 2.9 动画：`FuncAnimation`

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

x = np.linspace(0, 2*np.pi, 400)
fig, ax = plt.subplots(figsize=(6, 3.5))
(line,) = ax.plot([], [], lw=2)
ax.set(xlim=(0, 2*np.pi), ylim=(-1.3, 1.3), xlabel="x", ylabel="y")

def update(frame):
    line.set_data(x, np.sin(x - 0.05*frame))
    return (line,)

ani = FuncAnimation(fig, update, frames=200, interval=30, blit=True)

# 保存为 GIF（需要 pillow）或 mp4（需要 ffmpeg）
# ani.save("wave.gif", fps=30, dpi=100)
plt.show()
```

在 Jupyter 中播放：`from IPython.display import HTML; HTML(ani.to_jshtml())`。

动画适合展示波包演化、振动模式、时间推进结果；论文插图一般用「几个时刻的快照拼成多子图」的形式，比动画更清楚。

### 2.10 样式、字体与论文出图

统一配置（放在脚本开头或 `plt.rcParams.update`）：

```python
import matplotlib as mpl

mpl.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "mathtext.fontset": "cm",       # 数学字体风格接近 LaTeX
    "axes.labelsize": 11,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.5,
    "figure.figsize": (6, 4),
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.unicode_minus": False,    # 负号显示正常
})
```

中文标签（论文里建议用英文，内部报告可用中文）：

```python
mpl.rcParams["font.sans-serif"] = ["Microsoft YaHei",   # Windows
                                   "Noto Sans CJK SC",  # Linux/WSL
                                   "SimHei"]
mpl.rcParams["axes.unicode_minus"] = False
# WSL 上若缺中文字体：sudo apt install fonts-noto-cjk
```

导出：

```python
fig.savefig("fig1.png", dpi=600)          # 位图，预览用
fig.savefig("fig1.pdf")                   # 矢量，投稿首选
fig.savefig("fig1.svg")                   # 矢量，方便后期编辑
```

**无显示器环境**（SSH 到集群、WSL 无 WSLg）在 `import pyplot` **之前**设置：

```python
import matplotlib
matplotlib.use("Agg")                     # 只画不弹窗，savefig 正常工作
import matplotlib.pyplot as plt
```

出图检查清单：

- [ ] 坐标轴有物理量和单位（如 `E (eV)`、`t (fs)`）
- [ ] 不同曲线可区分（颜色/线型/标记 + 图例），黑白打印也能分辨
- [ ] 字号与图宽匹配：单栏图约 3.5 in，双栏约 7 in
- [ ] 分辨率 ≥ 300 dpi，需要缩放时用矢量格式
- [ ] 图上没有无意义留白（`tight_layout` 或 `bbox_inches="tight"`）

## 常见陷阱

- 在循环里 `plt.plot` 成百上千次：应复用 `ax.plot` 或收集数据后一次画。
- `plt.show()` 后继续画图：脚本模式下会阻塞；先 `savefig` 再 `show`。
- `imshow` 的图像方向不对：`origin`、`extent`、`Z.T` 三个东西一起检查。
- 标签里的下划线没转义：`"E_0"` 会被当数学模式，写成 `r"$E_0$"`。
- 中文变方框：字体没设或系统没装中文字体。
- 图像/直方图看起来「太糊」：提高 `dpi`；但矢量图不涉及 dpi，别用 dpi 解决矢量图问题。

## 练习

1. 画一维无限深势阱的前 3 个本征函数（`ψ_n = √(2/L) sin(nπx/L)`），用多子图上下排列，共享 x 轴。
2. 用 [01-NumPy](01-NumPy数值计算指南.md) 的蒙特卡洛程序，画「π 的估计值随点数变化」的收敛图（横轴对数），并画 `±1/√n` 误差带。
3. 画二维高斯波包 `|ψ|²` 的 `imshow` 图与 `contour` 图，标出 colorbar。
4. 用 `solve_ivp` 解阻尼振子，把「位移-时间」和「相图（x–v）」画成两个子图。
5. 用 `FuncAnimation` 做一个「绳上驻波」动画（`sin(kx)cos(ωt)`），保存为 GIF。

## 自测清单

- [ ] 能解释 Figure/Axes 与 `plt` 状态机的区别，能写多子图布局
- [ ] 会画误差棒、直方图、对数坐标、双 y 轴
- [ ] 会用 `imshow/pcolormesh/contour` 画二维场，方向正确
- [ ] 会画三维曲面与三维轨迹
- [ ] 会用 `FuncAnimation` 做动画并保存
- [ ] 会配置 rcParams、字体与 LaTeX 标签，导出 300 dpi 位图与矢量图
- [ ] 知道无显示器环境用 `Agg` 后端

## 参考资料

- Matplotlib 官方文档：https://matplotlib.org/stable/
- 图库（找图抄代码）：https://matplotlib.org/stable/gallery/index.html
- 配色参考：https://matplotlib.org/stable/users/explain/colors/colormaps.html
- 科研绘图建议：https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003833
