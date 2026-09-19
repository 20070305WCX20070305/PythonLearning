# 阶段 05：软件工程与千行项目

前四个阶段你学会的是"写代码"：函数、脚本、并发、集群。本阶段解决的是另一个问题：
**当代码长到没人（包括三个月后的你自己）能一口气读懂时，怎么办？**

答案是一套工程手段：模块化、面向对象、自动化测试、持续集成、文档、打包、性能分析。
本阶段结束时，你要独立完成一个 1000 行以上、有测试、有文档、能安装运行的科研项目。
注意：这是整个路线中第一次正式使用 `class`，前面的代码全部是函数式写法。

## 阶段目标

1. 能把函数式脚本重构为模块化的小包，说清楚每个模块的职责与边界；
2. 第一次系统使用面向对象：类、属性、方法、`@property`、`@dataclass`、继承、多态、组合、魔术方法；
3. 会用 pytest 进阶功能（fixture、参数化、tmp_path、monkeypatch/mock、approx）与覆盖率工具；
4. 会配置 GitHub Actions，让每次 push / PR 自动在多个 Python 版本上跑测试；
5. 会写 Google 风格 docstring，会用 MkDocs 生成文档站点；
6. 会用 `pyproject.toml` 打包，`pip install -e ".[dev]"` 开发安装，理解语义化版本；
7. 会先测量再优化：timeit、cProfile/pstats、tracemalloc、py-spy；
8. 独立交付"最终千行项目"，并通过最后的总验收。

## 学习顺序

| 顺序 | 文件 | 一句话说明 | 建议用时 |
| --- | --- | --- | --- |
| 1 | [01-模块化与OOP.md](./01-模块化与OOP.md) | 从单文件脚本到模块化小包，第一次引入 class | 3 周 |
| 2 | [02-测试与CI.md](./02-测试与CI.md) | pytest 进阶、覆盖率、GitHub Actions | 3 周 |
| 3 | [03-文档打包与性能分析.md](./03-文档打包与性能分析.md) | docstring、MkDocs、pyproject 打包、性能分析 | 3 周 |
| 4 | [项目-最终千行项目/README.md](./项目-最终千行项目/README.md) | 三个候选项目的需求书、架构模板、验收标准 | 7 周 |

学习方式建议：

- 每读一节先跑通示例代码，然后关掉文件自己重写一遍，写不出来就回去重读；
- 练习只给提示与验收方式，不给答案；做完用"验收方式"逐条检查；
- 从第 4 周开始边学边搭最终项目的骨架，不要等"全部学完再做"。

## 与前四个阶段的衔接

本阶段不引入全新的基础知识，而是把已有能力"工程化"：

| 前序阶段 | 在本阶段被用在哪里 |
| --- | --- |
| 01：venv / Git / logging / argparse / pytest | 包结构、日志模块、CLI 层、测试与 CI 的基础 |
| 02：pandas / HDF5 / SQLite / multiprocessing / psutil / tqdm | 项目的核心数据处理与并发逻辑 |
| 03：C、内存、进程、gcc/make/gdb | 性能分析章节的直觉来源；理解进程池与 IO 的代价 |
| 04：SSH / rsync / Slurm / Apptainer | 候选项目 B（远程任务管理器）的实现手段 |

## 需要安装的软件

只使用 Python 标准库与主流、轻量的公开工具。建议在虚拟环境中安装：

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
# source .venv/bin/activate

# 必装（测试）
pip install pytest pytest-cov

# 按需安装
pip install mkdocs mkdocs-material "mkdocstrings[python]"   # 文档（第 3 篇）
pip install build twine                                    # 打包与发布（第 3 篇）
pip install pre-commit                                     # 提交前自动检查（可选）
pip install py-spy                                         # 采样式性能分析（可选）
```

不需要安装：Django / Flask / FastAPI 等 Web 框架。本路线不涉及 Web 开发，
做本地 CLI 工具已经足够服务科研；以后有兴趣可以自行了解。

## 学习前的能力自检

开始本阶段之前，先确认前四个阶段的成果还在（下面的问题都答"是"再继续）：

- [ ] 我能在 Linux/WSL 里用 shell 管道、重定向完成文件批量操作；
- [ ] 我能创建 venv、安装依赖、用 Git 提交并 push 到 GitHub；
- [ ] 我能用 pandas 完成读取、清洗、分组统计，并写入 SQLite 或 HDF5；
- [ ] 我知道 multiprocessing 与线程池分别适合什么任务；
- [ ] 我能用 pytest 写基本的单元测试，并解释 `pytest.raises` 的用法；
- [ ] 我能用 logging 记录日志、用 argparse 写过一个命令行脚本；
- [ ] 我能用 SSH 登录远程机器、用 rsync 同步文件（或读过阶段 04 的材料）。

如果有两条以上答"否"，先回对应阶段复习；本阶段会直接使用这些能力，不会重新讲解。

## 环境自检

开始前，在已激活的虚拟环境中逐条确认（都能正常输出即可）：

```bash
python -V                      # 应为 3.10 及以上
python -m pip -V               # 输出的路径里应包含 .venv，确认没有用错环境
pytest --version               # pytest 已安装
git --version
git config user.name           # Git 身份已配置
python -m build --version      # 可选：打包工具已安装
mkdocs --version               # 可选：文档工具已安装
```

如果 `pytest --version` 报错，回到上一节重新安装；如果 `python -m pip -V` 的路径
不含 `.venv`，说明虚拟环境没有激活，先激活再继续。

## 16 周节奏建议（每周 6~10 小时）

| 周次 | 主题 | 本周产出 | 里程碑 |
| --- | --- | --- | --- |
| 第 1 周 | 模块与 import、类型注解 | 重写 01 篇 1.1~1.2 的全部示例 | |
| 第 2 周 | 类、`@property`、`@dataclass` | 用类封装实验数据对象 | |
| 第 3 周 | 继承/多态、组合、配置管理 | 完成 01 篇 1.9 的重构案例 | |
| 第 4 周 | pytest fixture 与参数化 | 为重构后的小包写 20 个以上测试 | |
| 第 5 周 | mock、tmp_path、覆盖率 | 生成覆盖率报告，核心模块 >= 80% | |
| 第 6 周 | GitHub Actions | CI 首次变绿，README 加徽章 | |
| 第 7 周 | docstring 与 MkDocs | `mkdocs serve` 能打开 API 文档 | |
| 第 8 周 | pyproject 打包与版本号 | `pip install -e .` 成功，CLI 可用 | |
| 第 9 周 | 性能分析 | 一份优化前后对比报告 | |
| 第 10 周 | 项目选型与架构设计 | 需求书 + 骨架 + CI 跑通 | 里程碑 1 |
| 第 11~12 周 | 核心功能开发 | 能端到端处理小样本数据 | |
| 第 13 周 | 补测试、修 bug | MVP 完成，覆盖率达标 | 里程碑 2 |
| 第 14 周 | 健壮性：异常、日志、边界 | 错误场景不崩溃且日志可读 | |
| 第 15 周 | 文档、打包、演示数据 | 别人能按 README 复现 | |
| 第 16 周 | 收尾 | 打 tag v1.0.0，写项目总结 | 里程碑 3 |

三个里程碑的判定标准：

- **里程碑 1（第 10 周）**：需求书写清楚（做什么 + 不做什么），src 布局建好，
  CLI 能 `--help`，配置与日志模块可用，CI 在空测试下变绿。
- **里程碑 2（第 13 周）**：MVP 功能全部跑通，端到端能在示例数据上产出结果；
  核心模块有单元测试，覆盖率 >= 70%。
- **里程碑 3（第 16 周）**：文档站点可构建，README 有安装/使用/示例，
  `pip install -e .` 后在任意目录可用 CLI，仓库有 `v1.0.0` 标签。

## 阶段产出物

阶段结束时，你的仓库里应该有这样一组可以展示的成果：

| 产出 | 位置 | 说明 |
| --- | --- | --- |
| 重构后的小包 | 独立目录或仓库 | 阶段 02 脚本的模块化版本，带测试 |
| 最终千行项目 | 独立 Git 仓库 | 1000+ 行、有测试与文档、可安装 |
| 测试与覆盖率 | `tests/` | pytest 全绿，核心模块覆盖率 >= 70% |
| CI 配置 | `.github/workflows/ci.yml` | push / PR 自动跑多版本测试 |
| 文档站点 | `docs/` 与 `mkdocs.yml` | `mkdocs build` 成功 |
| 打包配置 | `pyproject.toml` | `pip install -e ".[dev]"` 可用 |
| 性能报告 | 项目文档中一节 | 优化前后的耗时/内存对比 |
| 里程碑标签 | Git tags | v0.1.0 / v0.5.0 / v1.0.0 |

## 每周执行清单（可反复使用）

- [ ] 本周计划的小节读完，示例代码全部手敲并跑通；
- [ ] 向最终项目推进了至少一个可演示的小功能；
- [ ] 新写的核心逻辑有对应测试，`pytest` 全绿；
- [ ] 提交 3 次以上有意义的 commit 并 push，CI 通过；
- [ ] 更新了项目 TODO / 已知问题列表；
- [ ] 记录了本周卡住超过 1 小时的问题及解决方法。

## 时间不够时怎么办

本科课业紧张时按下面的优先级做减法，但**不要跳过最终项目**：

1. 优先级最高：01 篇的类与模块化、02 篇的 pytest 基础与 CI、最终项目 MVP；
2. 优先级次高：覆盖率报告、文档站点、性能分析；
3. 可以后补：MkDocs 主题美化、pre-commit、PyPI 发布实操、py-spy；
4. 无论如何都要保留：测试与 CI——这是本阶段与"随便写写"的分界线。

## 验收标准

完成本阶段时逐条检查：

- [ ] 能解释模块、包、`import` 机制与 `__init__.py` 的作用，并能把脚本改成包；
- [ ] 能独立定义类（含 `@property`、`@dataclass`），并用继承或组合组织代码；
- [ ] 能设计与实现 1000+ 行（不含第三方与自动生成代码）的可运行项目，职责清晰；
- [ ] 测试覆盖核心逻辑：`pytest` 全绿，`--cov` 报告核心模块 >= 70%；
- [ ] GitHub Actions CI 在 push / PR 时自动运行且通过，README 有状态徽章；
- [ ] 文档齐全：docstring、README、可用 `mkdocs build` 生成的文档站点；
- [ ] 能打包安装：`pip install -e .` 后命令行工具可运行；
      `python -m build` 能产出 wheel 与 sdist；
- [ ] 能用 timeit / cProfile 说明项目里至少一处性能优化，并给出前后数据；
- [ ] Git 历史清晰：功能分支、有意义的 commit、里程碑 tag。

## 常见误区

- **等学完再做项目**：本阶段一半的学习发生在项目里，第 10 周必须动工；
- **为了 OOP 而 OOP**：纯计算、无状态的逻辑继续用函数，类只用于"有状态/有资源/多协作对象"的场景；
- **追求覆盖率数字**：写没有断言的测试凑数，不如少写几个但测在刀刃上；
- **跳过测量直接优化**：没有 cProfile 数据的优化都是猜；
- **把示例当答案**：示例是讲解用的，项目里的需求要自己拆解；
- **只交代码不交测试**：别人与 CI 都无法验证结果，项目就失去了可复现性；
- **所有东西塞进一个文件**：超过 500 行的单文件就该拆分，模块化从第一天开始；
- **不留演示数据**：没有样本数据，别人无法复现你的端到端流程。

## 参考资料

- Python 官方教程：模块 <https://docs.python.org/zh-cn/3/tutorial/modules.html>
- Python 官方教程：类 <https://docs.python.org/zh-cn/3/tutorial/classes.html>
- pytest 官方文档 <https://docs.pytest.org/>
- coverage.py 文档 <https://coverage.readthedocs.io/>
- GitHub Actions 文档 <https://docs.github.com/zh/actions>
- Python 打包用户指南 <https://packaging.python.org/>
- MkDocs 官方文档 <https://www.mkdocs.org/>
- Sphinx 官方文档 <https://www.sphinx-doc.org/>
- Python 性能分析工具 <https://docs.python.org/3/library/profile.html>
