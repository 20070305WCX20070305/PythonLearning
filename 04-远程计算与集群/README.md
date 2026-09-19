# 阶段 04：远程计算与集群

> 从「会 ssh 登录」到「在集群上管理批量计算任务」：用 SSH config、rsync、Slurm、Apptainer 把本地和集群连成一条自动化流水线，最后完成一个支持 dry-run 的 Slurm 远程任务管理 CLI。

## 一、阶段目标

学完本阶段，你应当能够：

1. 熟练使用 SSH 进阶功能：config 别名、ProxyJump 跳板机、ssh-agent、保活参数，不再手打长命令。
2. 用 rsync 完成增量同步、排除规则、dry-run 预演、断点续传，并会用 tar + sha256sum 归档校验数据。
3. 说清集群架构（登录节点 / 计算节点 / 调度器 / 共享存储）与登录节点使用规矩。
4. 会写 SBATCH 作业脚本，能提交、监控、取消、统计作业，处理数组任务与 afterok 依赖。
5. 能根据测试作业实测资源（MaxRSS、Elapsed）来申请 CPU、内存与时间，避免 OOM 与超时。
6. 会用 Lmod 环境模块与 Apptainer 容器固定软件环境，并在 sbatch 中组合使用。
7. 完成产出项目：[Slurm 远程任务管理 CLI](项目-Slurm任务管理CLI/README.md)（MVP：读取配置 → 渲染 sbatch → 提交 → 轮询 → 重试 → rsync 归档；全程支持 --dry-run）。

## 二、前置说明：关于集群账号

- 已有所在学校计算集群账号：按顺序全部做完，优先做标有「（有账号）」的练习。
- 暂时没有账号：先做标有「（无账号替代）」的练习，用本地目录模拟远程路径、用 `--dry-run` 模拟提交；项目开发可以在 dry-run 模式下完整完成。拿到账号后补做真实提交与 rsync 环节即可。
- 申请账号通常需要：导师/课题组同意、学校 HPC 中心网站提交申请、签署使用协议。建议尽早向导师或师兄师姐确认：集群名称、登录地址、文档入口、分区与配额规则。
- 本阶段所有命令默认在 WSL2 Ubuntu 24.04 中执行；涉及集群的命令会标注「在集群登录节点/计算节点执行」。
- 前置阶段：00 环境 → 01 工具链 → 02 Python 系统资源与并发 → 03 C 与计算机系统。本阶段：04 远程计算与集群 → 05 软件工程与千行项目。

开课前请自检（任一不满足，先回对应阶段复习）：

- [ ] 能在 WSL 中熟练使用管道、重定向、权限与进程查看命令（阶段 01/02）
- [ ] 能读懂并修改 bash 脚本，知道 `set -euo pipefail` 的作用（阶段 01/03）
- [ ] 能用 `subprocess.run` 执行外部命令并取回输出与退出码（阶段 02）
- [ ] 知道进程、文件描述符、标准输入输出的含义（阶段 03）

没有账号时的替代路径（按优先级）：

1. 用 WSL 本地目录模拟远端：把 `cluster:~/xxx` 换成 `~/fake-cluster/xxx`，rsync / scp / tar 的操作全部可以照常练习。
2. 所有 Slurm 作业脚本先做「纸面运行」与 `bash -n` 语法检查，再用环境变量（如 `SLURM_ARRAY_TASK_ID`）在本地模拟执行。
3. 项目全程使用 `--dry-run`，把「将执行的命令」整理成核对清单；拿到账号后按清单逐条执行即可。

## 三、学习顺序

| 序号 | 文件 | 一句话说明 | 建议用时 |
| --- | --- | --- | --- |
| 1 | [01-SSH与rsync.md](01-SSH与rsync.md) | SSH config / 跳板机 / 密钥代理，rsync 传输与归档校验 | 1 周 |
| 2 | [02-Slurm任务调度.md](02-Slurm任务调度.md) | 集群架构与 sbatch/squeue/sacct，数组与依赖，失败排查 | 2 周 |
| 3 | [03-Apptainer与环境模块.md](03-Apptainer与环境模块.md) | Lmod 环境模块与 Apptainer 容器，可复现运行环境 | 1~2 周 |
| 4 | [项目-Slurm任务管理CLI/README.md](项目-Slurm任务管理CLI/README.md) | 综合项目：配置 → 生成脚本 → 提交 → 监控 → 重试 → 归档 | 3 周 |

建议：前三篇按顺序学；项目从第 2 周起同步推进（先 dry-run，后真实提交）。

## 四、需要安装的软件

本地（WSL Ubuntu 中执行；集群侧一般已装好 ssh / rsync / Slurm / Apptainer，无需自己装）：

```bash
sudo apt update
sudo apt install -y rsync openssh-client

# 验证
ssh -V                 # 应输出 OpenSSH_9.x
rsync --version | head -1
```

不要求本地安装 Slurm 与 Apptainer：没有集群时用 dry-run 与脚本审查练习替代（见各篇练习）。

说明：

- `openssh-client` 提供 ssh、scp、ssh-keygen、ssh-agent。
- `rsync` 是独立程序，传输两端都需要；学校集群通常已装好，直接使用即可。
- 可选：`sudo apt install -y dos2unix` 用于修复 Windows 侧编辑产生的 CRLF 换行符。

## 五、约 10 周节奏建议（每周 6~10 小时）

| 周次 | 内容 | 本周产出（可验收） |
| --- | --- | --- |
| 第 1 周 | SSH config、ssh-agent、跳板机；rsync 基础与本地模拟 | 一份可用的 ~/.ssh/config + 本地 rsync 实验记录 |
| 第 2 周 | rsync 排除/断点/校验、tar + sha256sum；项目里程碑 1 启动 | 传输检查清单 + sbatch 渲染雏形 |
| 第 3 周 | Slurm 架构与登录节点规矩、hello.sbatch | 注释版 hello.sbatch |
| 第 4 周 | 资源参数：nodes/ntasks/mem/time，squeue/sinfo/sacct 监控 | 资源估算笔记 |
| 第 5 周 | 数组任务与依赖；项目里程碑 2 | 数组作业脚本 + 依赖链 + dry-run 状态模拟 |
| 第 6 周 | 失败排查（OOM/超时/退出码）；模块与 Apptainer 入门 | 失败排查表 + 最小 .def |
| 第 7 周 | Apptainer 与 sbatch 组合；项目里程碑 3 | 容器化作业脚本 |
| 第 8 周 | 项目里程碑 4：重试与报告 | 模拟失败重试 + report.json |
| 第 9 周 | 项目里程碑 5：CLI 打磨与端到端测试 | 完整 dry-run 跑通 |
| 第 10 周 | 复盘；（有账号）真实提交与归档 | 项目验收 + 全部自测清单 |

学习方式建议：

- 每周固定两段「动手时间」：一段学新主题，一段推进项目里程碑；不要只看不敲。
- 每篇主题的练习至少完成 3 题，标有「（无账号替代）」的必做。
- 把每次实验的命令与输出贴进自己的笔记，形成可回放的记录（阶段 05 会用上）。
- 有账号后，先用最小的 1 分钟作业跑通全流程，再逐步加大规模。

## 六、验收标准

- [ ] 能用 `ssh 别名` 直接登录，且 scp/rsync 能复用该别名
- [ ] 能完成一次带排除规则、先 --dry-run 确认、支持断点续传的 rsync 同步
- [ ] 能用 tar 打包大量小文件并用 sha256sum 在两端校验
- [ ] 能写出包含资源、时间、输出重定向的 sbatch 脚本并逐行解释
- [ ] 能用 squeue/sacct 查到作业状态与 MaxRSS，并会安全取消作业
- [ ] 会写数组任务（含 % 并发限制）与 afterok 依赖
- [ ] 会写最小 Apptainer .def，能在 sbatch 中 `apptainer exec` 运行
- [ ] 项目能在无集群环境下以 --dry-run 完整跑通；有集群时完成一次真实提交、重试与归档
- [ ] 本阶段三篇主题的自测清单全部勾选

说明：前三篇的自测清单是过程性验收，项目 README 的验收标准是结果性验收；两者都完成才算通过本阶段。

## 七、学完之后

- 你应该能独立完成「写好本地代码 → 打包环境 → 提交集群批量跑 → 失败自动重试 → 结果归档校验」的完整闭环。
- 这些能力会直接用于阶段 05 的千行项目：工程化、测试与协作开发都将建立在「能可靠跑起来」的基础之上。
- 建议持续维护本阶段的项目：后续课程中的数值实验都可以用它提交到集群。

## 参考资料

- OpenSSH 手册：https://www.openssh.com/manual.html
- rsync 官方网站：https://rsync.samba.org/
- Slurm 官方文档：https://slurm.schedmd.com/documentation.html
- Apptainer 用户文档：https://apptainer.org/docs/user/latest/
