# PythonLearning

python是一门重要的且广泛使用的计算机编程语言，本仓库用于存储我在学习python过程中的笔记以及相应代码练习。

自 2026 年 9 月起，本仓库按 [`learning guide.md`](learning%20guide.md) 的路线重组为**物理科研计算基础设施**学习仓库：

> 用 Python + Shell + C + SQL，打造服务物理科研的「计算基础设施」能力；不学前端、不刷算法题、不系统学计算物理；最终独立完成 1000+ 行、可维护、能自动化处理数据和远程跑任务的项目。

## 一、学习大纲总索引

| 阶段 | 建议时长 | 主题 | 阶段入口 | 代表项目 |
| --- | --- | --- | --- | --- |
| 00 | 3~7 天 | 环境准备：WSL2+Ubuntu、终端、VSCode、Git/GitHub、磁盘评估 | [00-环境准备](00-环境准备/README.md) | — |
| 01 | 1~2 个月 | 工具链与工程习惯 | [01-工具链与工程习惯](01-工具链与工程习惯/README.md) | [实验数据文件整理 CLI](01-工具链与工程习惯/项目-实验数据文件整理CLI/README.md) |
| 02 | 2~3 个月 | Python 系统资源与并发 | [02-Python系统资源与并发](02-Python系统资源与并发/README.md) | [多进程数据批处理流水线](02-Python系统资源与并发/项目-多进程数据批处理流水线/README.md) |
| 03 | 3~4 个月 | C 与计算机系统 | [03-C与计算机系统](03-C与计算机系统/README.md) | [简易 Shell](03-C与计算机系统/项目-简易Shell/README.md) |
| 04 | 2~3 个月 | 远程计算与集群 | [04-远程计算与集群](04-远程计算与集群/README.md) | [Slurm 远程任务管理 CLI](04-远程计算与集群/项目-Slurm任务管理CLI/README.md) |
| 05 | 3~6 个月 | 软件工程与千行项目 | [05-软件工程与千行项目](05-软件工程与千行项目/README.md) | [最终千行项目](05-软件工程与千行项目/项目-最终千行项目/README.md) |

各阶段内的主题文件（点阶段入口看详细说明与学习顺序）：

- **00 环境准备**：WSL2 与 Ubuntu 安装 / VSCode 与 Windows Terminal 配置 / Git 与 GitHub 配置 / 磁盘评估与外接硬盘建议
- **01 工具链与工程习惯**：Linux 基础 / Shell 脚本 / Git 版本控制 / SSH 与 tmux / Python 工程化基础
- **02 Python 系统资源与并发**：NumPy 与 Pandas / HDF5 与 SQLite / multiprocessing 与 subprocess / asyncio 与系统监控
- **03 C 与计算机系统**：C 语言基础 / 指针与内存 / 文件 IO 与系统调用 / 进程线程与 socket / gcc-make-gdb
- **04 远程计算与集群**：SSH 与 rsync / Slurm 任务调度 / Apptainer 与环境模块
- **05 软件工程与千行项目**：模块化与 OOP / 测试与 CI / 文档打包与性能分析

## 二、目录结构

```
PythonLearning/
├── README.md                  # 本文件：总索引
├── learning guide.md          # 学习规划（原始需求与路线）
├── 00-环境准备/               # 装 WSL2、VSCode、Git；磁盘评估
├── 01-工具链与工程习惯/       # Linux、Shell、Git、SSH、tmux、venv、pytest、logging、argparse
│   └── 项目-实验数据文件整理CLI/
├── 02-Python系统资源与并发/   # NumPy/Pandas、HDF5、SQLite、multiprocessing、asyncio
│   └── 项目-多进程数据批处理流水线/
├── 03-C与计算机系统/          # C、指针内存、系统调用、进程线程 socket、gcc/make/gdb
│   └── 项目-简易Shell/
├── 04-远程计算与集群/         # SSH、rsync、Slurm、Apptainer、环境模块
│   └── 项目-Slurm任务管理CLI/
└── 05-软件工程与千行项目/     # 模块化、OOP、测试、CI、文档、打包、性能分析
    └── 项目-最终千行项目/
```

## 三、环境现状（2026-09-19 实测）

| 项目 | 现状 | 说明 |
| --- | --- | --- |
| 操作系统 | Windows 11（build 26200） | 支持 WSL2 |
| CPU / 内存 | i5-13420H / 12 线程 / 24 GB | 虚拟化已在 BIOS 开启 |
| C 盘 | 300 GB，剩余 **156.7 GB** | WSL2 默认安装位置 |
| D 盘 | 174.7 GB，剩余 **94.9 GB** | 数据与备份 |
| WSL2 / Ubuntu | **未安装** | 见 [00-环境准备/01](00-环境准备/01-WSL2与Ubuntu安装.md) |
| VSCode | 已安装（`D:\Microsoft VS Code`） | 需配置 PATH 与 WSL 扩展，见 00/02 |
| Git | 已安装（Windows 2.55.0） | WSL 内需再装一次，见 00/03 |
| Windows Terminal | 已安装（1.24） | 见 00/02 |
| Python（Windows 侧） | MSYS2 3.14.6 + Store 3.12 | **保留不动**；本路线统一使用 WSL 内 python3 |
| 磁盘评估结论 | **暂时不需要外接固态硬盘** | 详见 [00-环境准备/04](00-环境准备/04-磁盘评估与外接硬盘建议.md) |

## 四、使用说明

1. 按 00 → 01 → … → 05 顺序推进；每阶段先读该阶段 `README.md` 的说明与验收标准。
2. 每个主题文件按「学习目标 → 正文 → 练习 → 自测清单」使用；练习先自己写，再对照资料。
3. 项目驱动：每阶段项目从 `starter/` 骨架开始，以该阶段 README 的验收标准为准。
4. 知识边界：材料严格按顺序编写，前面的内容不会用到后面才学的知识。

## 五、进度打卡

- [ ] 00 环境准备完成（WSL2 Ubuntu 可用、VSCode Remote 连通、GitHub SSH 可用）
- [ ] 01 工具链与工程习惯 + [实验数据文件整理 CLI](01-工具链与工程习惯/项目-实验数据文件整理CLI/README.md)
- [ ] 02 Python 系统资源与并发 + [多进程数据批处理流水线](02-Python系统资源与并发/项目-多进程数据批处理流水线/README.md)
- [ ] 03 C 与计算机系统 + [简易 Shell](03-C与计算机系统/项目-简易Shell/README.md)
- [ ] 04 远程计算与集群 + [Slurm 远程任务管理 CLI](04-远程计算与集群/项目-Slurm任务管理CLI/README.md)
- [ ] 05 软件工程 + [最终千行项目](05-软件工程与千行项目/项目-最终千行项目/README.md)

## 六、核心原则（摘自 learning guide.md）

- 项目驱动：边做边查，不等学完再做。
- Git 管理一切：每个项目一个仓库，写清楚 commit。
- 先跑通再优化：先简单实现，再测量性能，再并行/加速。
- AI 辅助：生成模板、解释库、调试错误；但并发安全、死锁、权限、系统调用必须自己理解。
- 每周 6~10 小时，保持节奏。
- 明确不学：前端 HTML/CSS/JS、React/Vue、移动开发、游戏、区块链、微服务、Kubernetes、LeetCode 刷题；Docker、MPI/OpenMP/C++/Fortran/Julia 按需后置。
