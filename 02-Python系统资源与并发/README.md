# 阶段 02：Python 系统资源与并发

本阶段用 2~3 个月（每周 6~10 小时）把 Python 从「会写脚本」升级为「能处理科研数据、吃满本机资源」：
先用 NumPy/Pandas 做数值与表格分析，再用 HDF5/SQLite 存储，最后用 multiprocessing、subprocess、asyncio、
psutil 把批量处理自动化，并以项目「多进程数据批处理流水线」收尾。

## 阶段目标

1. 能用 NumPy 向量化完成多通道数据的选取、变换与统计，避免 Python 循环瓶颈。
2. 能用 Pandas 完成批量实验记录的读取、清洗、分组聚合、合并与时间重采样。
3. 能按数据形态选择存储：大数组写 HDF5（h5py），关系表格写 SQLite（标准库 sqlite3）。
4. 能用 multiprocessing 让批量处理吃满多核，用 subprocess 调用外部命令并解析输出与退出码。
5. 能用 asyncio 处理大量 IO 等待，用 psutil 观察 CPU/内存/磁盘状态，用 tqdm 给长任务加进度条。
6. 能用 pytest 测试数据处理函数，独立完成本阶段项目（阶段 01 的工程习惯全部延续）。

## 阶段产出与项目

学完本阶段，你手里会有：

- 一套向量化的多通道数据处理脚本（选取、去均值、标准化、误差统计）；
- 一份可复现的汇总流程：实验记录 CSV → 清洗 → 分组统计 → 结果表（Pandas）；
- 一个可扩展的 HDF5 数据文件（波形 + 属性元数据）和一个 SQLite 实验台账；
- 一个并行批处理流水线（带日志、进度条、资源监控）；
- 项目「多进程数据批处理流水线」：`starter/gen_data.py` 生成模拟数据，`starter/pipeline.py`
  批量处理后写入存储，`tests/test_pipeline.py` 用 pytest 验证结果；具体需求与验收以项目 README 为准。

## 前置知识

- 阶段 00：WSL2 + Ubuntu 24.04 环境、VSCode Remote 工作流。
- 阶段 01：Linux 命令行、Shell 脚本、Git、SSH/tmux、venv/pip、pytest、logging、argparse。
- Python 基础：函数（默认参数、返回值）、列表/字典/集合、文件读写（txt/json/csv）、requests。
- 本阶段全部示例使用函数式写法；每个示例都可在 WSL2 的 venv 里直接运行。

## 学习顺序（文件清单）

本阶段共 9 个文件，按下表顺序使用：

| 顺序 | 文件 | 内容 | 建议用时 |
| --- | --- | --- | --- |
| — | [README.md](./README.md) | 本文件：阶段导航与验收标准 | — |
| 1 | [01-NumPy与Pandas.md](./01-NumPy与Pandas.md) | ndarray、广播、向量化、统计、CSV/.npy；DataFrame、清洗、聚合、合并、resample | 3~4 周 |
| 2 | [02-HDF5与SQLite.md](./02-HDF5与SQLite.md) | h5py 层次结构、追加写入、压缩分块；sqlite3 建表、查询、事务、索引、CSV 导入 | 2 周 |
| 3 | [03-multiprocessing与subprocess.md](./03-multiprocessing与subprocess.md) | 进程与 CPU 并行、批量任务并行化；外部命令调用与返回码 | 2 周 |
| 4 | [04-asyncio与系统监控.md](./04-asyncio与系统监控.md) | 异步 IO 与并发等待；psutil 资源观测、tqdm 进度条 | 1.5 周 |
| 5 | [项目 README](./项目-多进程数据批处理流水线/README.md) | 项目需求、里程碑与验收清单 | 1~2 周（与前面交叉） |
| 6 | [starter/gen_data.py](./项目-多进程数据批处理流水线/starter/gen_data.py) | 生成模拟实验数据的脚本 | 随项目 |
| 7 | [starter/pipeline.py](./项目-多进程数据批处理流水线/starter/pipeline.py) | 批处理流水线骨架（待补全） | 随项目 |
| 8 | [tests/test_pipeline.py](./项目-多进程数据批处理流水线/tests/test_pipeline.py) | 流水线测试（pytest） | 随项目 |

## 十周节奏建议（每周 6~10 小时）

| 周次 | 主题 | 建议用时 | 本周产出 |
| --- | --- | --- | --- |
| 第 1 周 | NumPy 基础：ndarray、索引、形状、广播 | 8~10 h | 能把一段嵌套循环改成向量化写法 |
| 第 2 周 | NumPy 进阶：统计、随机数、CSV/.npy、timeit | 6~8 h | 多通道统计小脚本 + 计时对比记录 |
| 第 3 周 | Pandas 基础：DataFrame、筛选、缺失值 | 8~10 h | 清洗好一份实验记录 CSV |
| 第 4 周 | Pandas 进阶：groupby、merge、resample | 6~8 h | 按样品/温度汇总的统计表 |
| 第 5 周 | HDF5：文件/组/数据集/属性/层次结构 | 8~10 h | 把多通道波形写成 .h5 文件 |
| 第 6 周 | HDF5 追加与压缩 + SQLite 建表查询 | 6~8 h | 可扩展数据集 + lab.db 初版 |
| 第 7 周 | SQLite 事务/索引 + CSV 批量导入 | 6~8 h | CSV→SQLite 导入脚本（argparse） |
| 第 8 周 | multiprocessing 与 subprocess | 8~10 h | 并行批处理脚本 + 外部命令封装 |
| 第 9 周 | asyncio 与 psutil、tqdm | 6~8 h | 资源监控小工具、并发 IO 脚本 |
| 第 10 周 | 项目整合、测试、文档与验收 | 8~12 h | 项目验收清单全部勾选 |

## 本阶段需要安装的软件

阶段 02 的库统一装进 venv（venv 的创建、激活与 requirements.txt 用法见阶段 01 的 05 课）。

```bash
# 确认已进入虚拟环境：命令行提示符前应出现 (.venv)
source .venv/bin/activate

pip install numpy pandas h5py psutil tqdm
```

| 软件包 | 用途 | 对应内容 |
| --- | --- | --- |
| numpy | 数组与向量化计算 | 01 |
| pandas | 表格数据与时间序列 | 01 |
| h5py | HDF5 文件读写 | 02 |
| psutil | CPU/内存/磁盘监控 | 04 |
| tqdm | 长循环进度条 | 03/04 与项目 |

说明：

- sqlite3 是 Python 标准库，不需要 pip 安装，`import sqlite3` 即可。
- 建议把依赖固定下来：`pip freeze > requirements.txt`，换机器时 `pip install -r requirements.txt`。
- 验证安装：

```bash
python -c "import numpy, pandas, h5py, psutil, tqdm; print(numpy.__version__, pandas.__version__)"
```

练习与项目目录建议：

- `~/lab-practice-02/`：本阶段练习数据与脚本。
- `~/projects/data-pipeline/`：本阶段项目的 Git 仓库（从 starter/ 骨架开始，见项目 README）。

## 如何使用本阶段材料

1. 每课按「学习目标 → 正文示例（全部亲手敲一遍）→ 练习 → 自测清单」推进，不跳步。
2. 示例里的输出示例只给量级，实际数值以你机器上的运行为准；对不上时先检查输入数据形状。
3. 练习先自己写，再看「验收方式」倒推；不要直接抄答案。
4. 每完成一课提交一次 Git，提交信息写清「做了什么」，例如「完成 NumPy 广播练习」。
5. 项目与正文交叉进行：学过 HDF5 和 SQLite 就可以先把项目的存储部分做起来。

## Git 提交建议

- 每完成一节示例或一道练习就提交一次，不要攒到周末。
- 提交信息用「动词 + 对象」，例如「添加多通道 RMS 向量化脚本」。
- `.gitignore` 挡住 `.venv/`、`__pycache__/`、`*.h5`、`*.db`、`large-data/`。
- 项目按里程碑打 tag，例如 `v0.1.0`（能生成数据）到 `v0.4.0`（测试全绿）。

## 常见问题

- numpy/pandas 导入失败：先 `source .venv/bin/activate`，再用 `python -c "import numpy"` 看具体报错。
- h5py 打不开文件（文件锁）：确认没有另一个进程正以写模式打开它。
- `resize` 报 "Only chunked datasets can be resized"：建数据集时忘了 `maxshape` 或 `chunks`。
- SQLite 数据没保存：检查是否 `commit()`，或改用 `with conn:`。
- 插入 numpy 数值报绑定错误：插入前用 `int()`/`float()` 转成 Python 标量。
- resample 报错：时间列要先转成 datetime 并设为索引。

## 验收标准

- [ ] NumPy：能解释 shape/axis/广播，能用向量化替换双层循环并用 timeit 证明提速
- [ ] NumPy：会读写 CSV、.npy/.npz，会用 nan 系列函数处理坏点，会用固定随机种子
- [ ] Pandas：会 loc/iloc、布尔过滤、缺失值处理、groupby 聚合、merge/concat 与 resample
- [ ] HDF5：会用组组织层次数据、写属性、用 maxshape 分批追加、设置分块与 gzip 压缩
- [ ] SQLite：会建表、参数化插入、条件查询、聚合、建索引，会写 CSV 批量导入脚本
- [ ] 存储选型：能说清什么数据放 HDF5、什么数据放 SQLite，并给出理由
- [ ] 并行：能把一个串行批处理脚本改成多进程版本，结果与原版一致
- [ ] 外部命令：能用 subprocess 调用命令并区分 stdout/stderr、检查返回码
- [ ] 异步与监控：能写简单的 asyncio 并发等待，能用 psutil 打印系统资源快照
- [ ] 工程：脚本有函数拆分、logging、argparse（阶段 01 习惯的延续）
- [ ] 项目：项目 README 中的验收清单全部通过，`pytest` 全绿
- [ ] 所有练习与项目提交进 Git，提交信息可读

## 参考资料

- NumPy 官方文档：https://numpy.org/doc/stable/
- Pandas 官方文档：https://pandas.pydata.org/docs/
- h5py 官方文档：https://docs.h5py.org/en/stable/
- Python sqlite3 文档：https://docs.python.org/3/library/sqlite3.html
