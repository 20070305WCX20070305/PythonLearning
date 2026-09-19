# 阶段 01：工具链与工程习惯

本阶段用 1~2 个月（每周 6~10 小时）补齐科研计算中每天都要用的工具链：
Linux 命令行、Shell 脚本、Git、SSH/tmux、Python 工程化（venv/pytest/logging/argparse），
并以产出项目「实验数据文件整理 CLI」收尾。

## 阶段目标

1. 能在 WSL2 Ubuntu 24.04 中熟练完成文件整理、查找、过滤、打包等日常操作。
2. 能独立编写带参数、错误处理与日志的 Shell 脚本，明确 Shell 与 Python 的分工。
3. 能用 Git 完成提交、分支、合并、解决冲突，并把代码推送到 GitHub。
4. 能用 SSH 密钥登录远程主机、配置别名，用 tmux 保持长任务不中断。
5. 能用 venv / pytest / logging / argparse 把脚本工程化，并独立完成本阶段项目。

## 学习顺序（文件清单）

1. [01-Linux基础.md](./01-Linux基础.md)：文件系统与路径、权限、查找、管道、文本处理、进程与打包。
2. [02-Shell脚本.md](./02-Shell脚本.md)：shebang、变量、条件、循环、函数、位置参数与退出码。
3. [03-Git版本控制.md](./03-Git版本控制.md)：三区模型、提交、撤销、分支、远程仓库与冲突解决。
4. [04-SSH与tmux.md](./04-SSH与tmux.md)：密钥登录原理、ssh config、传文件、端口转发与 tmux 会话。
5. [05-Python工程化基础.md](./05-Python工程化基础.md)：venv、pathlib、异常、logging、argparse、pytest 入门。
6. [项目-实验数据文件整理CLI/README.md](./项目-实验数据文件整理CLI/README.md)：本阶段综合产出项目的需求与里程碑。

建议顺序：01 → 02 → 03 → 04 → 05 → 项目。03 可以提前开始，越早用 Git 管住练习代码越好。

## 如何使用本阶段材料

每一课按同一个循环推进，不要跳步：

1. 读一遍「学习目标」，确认自己知道这一课要解决什么问题。
2. 阅读「正文」，把所有示例命令在 WSL2 终端里亲手敲一遍，包括输出核对。
3. 完成「练习」（先看提示，卡住再看验收标准倒推做法），把脚本保存到练习目录。
4. 对照「自测清单」逐条打勾，有做不到的条目就回到对应小节重读。
5. 把当天成果 `git add` + `git commit`，提交信息写清「做了什么」。

练习目录建议：

- `~/lab-practice/`：存放各课临时脚本与数据。
- `~/projects/data-organizer/`：本阶段项目的 Git 仓库。

## 六周节奏建议（每周 6~10 小时）

| 周次 | 主题 | 建议用时 | 本周产出 |
| --- | --- | --- | --- |
| 第 1 周 | 01-Linux基础 | 8~10 h | 用命令行整理好一个模拟实验数据目录 |
| 第 2 周 | 02-Shell脚本 | 8~10 h | 4 个可运行的小脚本（重命名/归档/清单/参数解析） |
| 第 3 周 | 03-Git版本控制 | 6~8 h | 项目仓库、清晰提交历史、GitHub 远程仓库 |
| 第 4 周 | 04-SSH与tmux | 6~8 h | `ssh localhost` 密钥登录 + tmux 长任务 |
| 第 5 周 | 05-Python工程化基础 | 8~10 h | 重构后的模块 + 通过的 pytest 测试 |
| 第 6 周 | 项目实战与收尾 | 8~12 h | 实验数据文件整理 CLI（MVP + 测试 + 文档） |

每周结束时用下面一句话自检：

- 第 1 周：我能否不查笔记完成「找文件、看内容、改权限、打包」这套动作？
- 第 2 周：我能否写出一个带参数校验和错误退出的脚本？
- 第 3 周：我能否看着 `git log --oneline --graph` 讲清楚每条分支的来龙去脉？
- 第 4 周：我能否在 tmux 里跑长任务，然后关掉终端再回来继续看输出？
- 第 5 周：我能否把任意一个一次性脚本改造成「有 main、有测试、有日志」的模块？
- 第 6 周：新同学能否只读 README 就把我的项目跑起来？

时间紧时优先保证：Linux 命令、Git、venv + argparse，再补 Shell 与 tmux 的进阶部分。
时间宽裕时把项目进阶功能（配置驱动规则、undo）做完。

## 本阶段需要安装的软件

00 阶段已安装（无需重复）：

```
build-essential git curl wget tmux htop unzip
```

需要补充安装（在 WSL2 Ubuntu 24.04 中执行）：

```bash
sudo apt update
sudo apt install -y openssh-server python3-venv python3-pip tree
```

| 软件 | 用途 | 来源 |
| --- | --- | --- |
| openssh-server | 04 课练习 `ssh localhost` 密钥登录 | apt（本次安装） |
| python3-venv / python3-pip | 05 课虚拟环境与依赖管理 | apt（本次安装） |
| tree | 以树形查看目录结构，便于写报告 | apt（本次安装，可选） |
| pytest | 05 课与项目的测试 | pip（在 venv 里安装） |

## 常见问题

- `sudo apt update` 很慢或失败：检查网络后重试；也可以换用国内镜像源后再 `sudo apt update`。
- `ssh localhost` 提示拒绝连接：说明服务没启动，执行 `sudo service ssh start`，04 课第一步会做。
- `python3 -m venv` 报 ensurepip 错误：说明缺少 venv 组件，执行 `sudo apt install -y python3-venv`。
- 激活虚拟环境后命令还是系统版本：用 `which python` 确认路径里有 `.venv`，不对就重新 `source .venv/bin/activate`。
- `pytest` 报 ModuleNotFoundError：从项目根目录运行；测试文件里要先把被测模块目录加入 `sys.path`。
- 命令不知道参数怎么写：先 `命令 --help`，再 `man 命令`（`q` 退出）。
- 路径或文件名含空格报错：给变量和路径加双引号，脚本里用 `--` 结束选项解析。

## Git 提交建议

- 完成一个练习或一个函数就提交一次，不要攒到周末一次性提交。
- 提交信息用「动词 + 对象」，例如「添加按日期归档脚本」「修复 CSV 空行解析」。
- 新功能用 `feature/xxx` 分支，合并回 main 前先自查 `git diff`。
- `.gitignore` 里挡住 `.venv/`、`__pycache__/`、`sample-data/`、`organized/`、`*.log`。
- 每个里程碑打 tag，例如 `v0.1.0` 到 `v0.4.0`，便于回看进度。

## 验收标准

- [ ] 会用 `pwd/ls/cd/cat/less/head/tail/cp/mv/rm/mkdir` 完成日常文件操作
- [ ] 理解 rwx 权限与三个身份组，会用 `chmod`、知道 `sudo` 的作用与风险
- [ ] 会用 `find`、`grep`、管道与重定向组合命令，会用 `wc/sort/uniq/cut/tr` 做基础统计
- [ ] 会 `tar` 打包与解包，会查看进程并安全地终止进程
- [ ] 能写带 shebang、`set -euo pipefail`、参数解析的 Shell 脚本
- [ ] Git：会 add/commit/status/log/diff，会 restore/reset/revert，会分支与合并，解决过一次冲突
- [ ] Git：本地仓库推送到 GitHub，能 clone/pull；理解 `.gitignore` 的写法
- [ ] 会用密钥登录，会写 `~/.ssh/config` 别名，会用 scp 传文件
- [ ] tmux：会创建会话、分离、重连、分窗口与分面板
- [ ] 会用 venv 创建/激活/退出环境，并用 requirements.txt 记录依赖
- [ ] 会用 pathlib / shutil / hashlib 写文件处理函数，用 logging 写日志，用 argparse 写 CLI
- [ ] 会用 pytest 写函数式测试并运行（含 tmp_path 与参数化）
- [ ] 完成「实验数据文件整理 CLI」MVP：扫描、分类、去重、报告、日志、dry-run
- [ ] 每个练习和项目都提交进 Git，有可读的提交信息

最终判断标准很简单：把项目仓库地址发给一个同学，对方照着 README
能在一台新机器上跑通你的工具，并看懂你的提交历史。

后续阶段会讲到进程与并发（02）、C 与计算机系统（03）、远程集群与 rsync（04）、软件工程与千行项目（05）。
