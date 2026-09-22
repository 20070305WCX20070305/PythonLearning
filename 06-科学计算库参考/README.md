# 06 科学计算库参考（计算物理方向）

本目录是**速查与参考**，不是新的学习阶段。当你要「用 Python 算物理」时，按主题直接查阅：

- 阶段 02 的 [01-NumPy与Pandas](../02-Python系统资源与并发/01-NumPy与Pandas.md) 侧重**数据处理**（实验记录、表格、存储）；
- 本目录侧重**数值计算、物理绘图、符号推导与性能加速**，面向计算物理的常见任务。

## 一、文件清单

| 文件 | 内容 | 典型用途 |
| --- | --- | --- |
| [01-NumPy数值计算指南](./01-NumPy数值计算指南.md) | ndarray、广播、向量化、统计、线性代数、拟合、随机模拟、FFT、文件读写 | 数值实验、网格与场、蒙特卡洛 |
| [02-Matplotlib科学绘图指南](./02-Matplotlib科学绘图指南.md) | 曲线/误差棒/直方图、场分布、等高线、三维图、动画、论文出图 | 画数据、画解、画势场与波函数 |
| [03-SciPy数值算法指南](./03-SciPy数值算法指南.md) | 积分、插值、优化与拟合、ODE 求解、稀疏矩阵本征值、特殊函数 | 解方程、解微分方程、拟合实验数据 |
| [04-SymPy符号计算指南](./04-SymPy符号计算指南.md) | 符号微积分、解方程、微分方程、矩阵、拉格朗日力学推导 | 推导公式、验证解析结果 |
| [05-Numba加速计算指南](./05-Numba加速计算指南.md) | `@njit` 编译加速、`prange` 并行、编译选项、CUDA 入门 | 纯 Python 循环太慢、逐粒子/逐格点模拟 |

「我该看哪个文件」速查：

| 任务 | 去这里 |
| --- | --- |
| 把公式写成数组运算、算统计量 | 01-NumPy |
| 解线性方程组、求本征值、FFT | 01-NumPy、03-SciPy |
| 随机模拟、蒙特卡洛 | 01-NumPy、05-Numba |
| 拟合实验数据、求极小值、求根 | 03-SciPy |
| 解常微分方程（初值问题） | 03-SciPy（`solve_ivp`） |
| 推导公式、符号积分/微分 | 04-SymPy |
| 画图、动画、论文插图 | 02-Matplotlib |
| 纯 Python 循环太慢 | 05-Numba |

## 二、安装与验证

五个库都可以 pip 安装（建议装在阶段 01 建的 venv 里）：

```bash
python -m pip install numpy scipy matplotlib sympy numba
```

| 库 | 用途 | 备注 |
| --- | --- | --- |
| numpy | 数组与数值计算 | 其余库的基础 |
| scipy | 数值算法（积分/优化/ODE/稀疏矩阵） | 依赖 numpy |
| matplotlib | 绘图 | WSL2 + Windows 11 支持 WSLg 可直接弹窗 |
| sympy | 符号计算 | 纯 Python，无编译依赖 |
| numba | JIT 编译加速 | 依赖 llvmlite；若 pip 安装失败优先用 conda/mamba |

验证：

```bash
python -c "import numpy, scipy, matplotlib, sympy, numba; print(numpy.__version__, scipy.__version__, matplotlib.__version__, sympy.__version__, numba.__version__)"
```

以下情况不必强求版本一致，以官方文档为准：

- **Python 版本过新**：numba 支持的 Python 版本通常滞后于官方最新版，安装失败多半是版本不匹配，可换用 conda 或使用较旧的 Python（如 3.11/3.12）。
- **无显示器环境**（SSH 到集群）：绘图前用 `matplotlib.use("Agg")` 只保存文件，见 02 文件第 10 节。

## 三、使用建议

1. 每个文件都按「学习目标 → 正文示例 → 常见陷阱 → 练习 → 自测清单」组织，示例可直接复制到 `.py` 文件或 Jupyter 里运行。
2. 物理例子的数值只给量级，实际结果以你机器上的运行为准。
3. 参考用法：做计算物理作业或项目时，先想清楚「数学上要做什么」，再到对应文件里找 API 和写法。
4. 本目录的例子只依赖 numpy/scipy/matplotlib/sympy/numba，不依赖阶段 02 的 h5py、pandas；数据存储问题请回到 [阶段 02](../02-Python系统资源与并发/README.md)。
5. 项目环境建议把依赖固定：`pip freeze > requirements.txt`。

## 四、计算物理常用工具链（本目录覆盖范围）

```
数据/模型
   │
   ├─ 数组与向量化 ……………… NumPy（01）
   ├─ 符号推导 ……………………… SymPy（04）
   ├─ 数值算法 ……………………… SciPy（03）
   │     ├─ 积分/插值
   │     ├─ 优化/拟合/求根
   │     ├─ ODE 初值问题
   │     └─ 稀疏矩阵本征值
   ├─ 逐格点/逐粒子循环 ……… Numba（05）
   └─ 可视化 …………………………… Matplotlib（02）
```

## 五、参考资料

- NumPy 官方文档：https://numpy.org/doc/stable/
- SciPy 官方文档：https://docs.scipy.org/doc/scipy/
- Matplotlib 官方文档：https://matplotlib.org/stable/
- SymPy 官方文档：https://docs.sympy.org/
- Numba 官方文档：https://numba.readthedocs.io/
