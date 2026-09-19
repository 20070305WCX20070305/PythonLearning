# 02 Slurm 任务调度

## 学习目标

- 说清集群的登录节点 / 计算节点 / 调度器 / 共享存储分工，遵守登录节点使用规矩。
- 会用 sbatch 提交、squeue 查看、scancel 取消、sacct 统计作业。
- 会写 SBATCH 指令并解释 `--nodes` / `--ntasks` / `--cpus-per-task` / `--mem` / `--time` 的含义。
- 会根据测试作业实测资源来申请 CPU、内存与时间。
- 会写数组任务与 `afterok` 依赖链，会用 `srun` 申请交互式资源。
- 能排查 OOM、超时、命令报错等常见失败。

## 前置知识

- 阶段 01：ssh/rsync 基础；bash 脚本（变量、退出码）。
- 本阶段 01：SSH config 与 rsync（作业结束后拉结果要用）。
- 阶段 02/03：subprocess 与进程概念，理解「一个作业就是一批进程」。

## 建议用时

8~10 小时（含练习）。

## 正文

### 1. 集群架构与登录节点规矩

**概念讲解**

一个典型的高性能计算集群由四部分组成：

```text
                ssh                        sbatch
[你的笔记本/WSL] ----> [登录节点 login] ----> [调度器 slurmctld]
                          |  编辑/提交/查看        |
                          |                        | 按资源需求分配
                          v                        v
                    [共享存储 home/scratch/project] <---> [计算节点 compute01..N]
```

- 登录节点（login node）：你 ssh 进来的地方。用于编辑脚本、提交作业、查看状态、传数据。**所有用户共享，CPU/内存很有限。**
- 计算节点（compute node）：真正跑作业的机器，可能几十到几千台；多数集群不允许直接 ssh 进入。
- 调度器（slurmctld 等）：负责排队与分配资源，Slurm 是最流行的实现。
- 共享存储：家目录（home）、临时大空间（scratch）、项目目录（project）。各集群命名不同，入职时先问清配额与清理策略。

登录节点规矩（几乎所有集群通用）：

- 不要在登录节点跑超过几分钟的 CPU/内存密集型命令，会被管理员警告甚至封号。
- 编译小项目、编辑文件、提交作业、`srun` 小测试可以。
- 需要在计算节点上调试时，用 `srun --pty bash` 申请交互式会话（见第 6 节）。

**常见错误**

- 在登录节点直接 `python3 train.py` 跑几小时，被系统监控记录。
- 以为 ssh 进计算节点就能随便用（多数集群禁止直连或直接没有路由）。
- 把大量中间数据写进 home 且不问配额，把家目录写满导致之后所有作业失败。

### 2. 第一个作业：hello.sbatch

**概念讲解**

Slurm 作业脚本就是一个 bash 脚本，开头用 `#SBATCH` 注释行告诉调度器资源需求。注意 `#SBATCH` 必须写在脚本开头、`#!` 之后、任何命令之前。

**示例：hello.sbatch**（在集群登录节点创建并提交）

```bash
#!/bin/bash
#SBATCH --job-name=hello              # 作业名，出现在 squeue/sacct 里
#SBATCH --partition=compute           # 分区（队列），可用名字以 sinfo 为准
#SBATCH --nodes=1                     # 节点数
#SBATCH --ntasks=1                    # 任务（进程）数
#SBATCH --cpus-per-task=2             # 每个任务的 CPU 核数
#SBATCH --mem=4G                      # 总内存
#SBATCH --time=00:30:00               # 最长运行时间，超时会被杀掉
#SBATCH --output=%x-%j.out            # 标准输出：作业名-作业号.out
#SBATCH --error=%x-%j.err             # 标准错误

set -euo pipefail                     # 出错即停；未定义变量报错；管道错误不吞

echo "作业号: $SLURM_JOB_ID"
echo "运行在: $(hostname)"
echo "分配核数: $SLURM_CPUS_PER_TASK"
cd "$SLURM_SUBMIT_DIR"                # 回到提交目录（默认已在此，显式更稳）

python3 - <<'EOF'
import socket
print("hello from", socket.gethostname())
EOF
```

```bash
sbatch hello.sbatch        # 提交，输出 "Submitted batch job 12345"
squeue -u $USER            # 看状态：PD 排队 / R 运行
cat hello-12345.out        # 作业结束后查看输出
```

输出文件名占位符：`%x` 作业名，`%j` 作业号，`%A` 数组总作业号，`%a` 数组下标，`%N` 第一个节点名。不写 `--output` 时默认是提交目录下的 `slurm-%j.out`。

**常见错误**

- `#SBATCH` 行写在命令之后，被当作普通注释忽略，资源参数没有生效。
- 脚本带 CRLF（Windows 编辑），报 `bad interpreter: /bin/bash^M`。
- 不写 `--time`，用了分区默认值（可能很短），作业中途被杀。
- 用相对路径找输入文件：作业的工作目录可能不是脚本所在目录，用 `$SLURM_SUBMIT_DIR` 或绝对路径。
- 输出文件写在家目录又忘了清理，长期积累占满配额。

### 3. 资源申请：别多也别少

**概念讲解**

- `--nodes=1 --ntasks=1 --cpus-per-task=4`：一个节点上一个任务、每个任务 4 核。纯 Python + numpy 多线程程序适合这样申请。
- `--nodes=1 --ntasks=8`：8 个进程（多进程并行；MPI 一类本路线不展开）。
- `--mem=8G` 与 `--mem-per-cpu=2G` 二选一，不要同时给；含义不同，以集群文档为准。
- `--time=HH:MM:SS`：请求过小会被超时杀掉，请求过大排队更久。经验做法：先用小规模测试作业实测，再把内存乘 1.5~2 倍、时间乘 1.5~2 倍。
- `--partition`：登录后用 `sinfo -s` 查看可用分区与时间上限；常见有 debug/短作业队列与普通队列。

**示例：用 sacct 实测上一个作业用掉多少**（在集群登录节点执行）

```bash
sacct -j 12345 --format=JobID,JobName,State,Elapsed,MaxRSS,ReqMem,ExitCode

# 若集群装了 seff（Slurm 自带小工具），一行就能看总结
seff 12345
```

得到 `MaxRSS=3.1G`、`Elapsed=00:17:42` 后，下一个同规模作业就申请 `--mem=6G --time=00:30:00`。

**常见错误**

- 申请 `--mem=100G` 实际只用 3G，排队很久，浪费自己也浪费队列。
- 时间正好卡在实测值上，稍有波动就被超时杀掉。
- 想要 8 核却写 `--ntasks=8`，程序实际单线程，白占 7 个核。
- 不写 `--partition`，落到默认分区（可能是给短作业的 debug 区）。

### 4. 监控与查账：squeue / sinfo / sacct

**概念讲解与示例**（全部在集群登录节点执行）

```bash
# 我的作业队列
squeue -u $USER
squeue -u $USER -o "%.10i %.20j %.8T %.10M %.6D %R"
# 列含义：JobID JobName State Time Nodes Reason/NodeList

squeue -j 12345            # 单个作业
squeue --start             # 估计排队作业的开始时间

# 分区与节点概览
sinfo -s                   # 每个分区的空闲/占用/总节点数与时间上限
sinfo -p compute -N        # 看具体节点

# 作业详情：依赖、工作目录、资源、命令行
scontrol show job 12345

# 取消
scancel 12345                            # 取消单个
scancel --state=PENDING -u $USER         # 只取消还在排队的
scancel -u $USER                         # 取消自己全部作业（慎用）

# 历史与统计（作业结束后 squeue 就看不到了，用 sacct）
sacct -j 12345
sacct -u $USER --starttime today --format=JobID,JobName,State,Elapsed,MaxRSS,ExitCode
```

状态速查：`PD` 排队、`R` 运行、`CG` 收尾中、`CD` 完成、`F` 失败、`CA` 被取消、`TO` 超时、`OOM` 内存超限。

**常见错误**

- 作业结束后 `squeue -u $USER` 空了，以为作业丢了——历史要用 `sacct` 查。
- 看不懂 `NODELIST(REASON)`：`Resources` 表示资源不足在排队，`Priority` 表示优先级低，`PartitionTimeLimit` 表示所请求时间超过分区上限。
- 用 `scancel -u $USER` 把正在跑的重要作业一起取消了。
- 只看 State 不看 ExitCode：`FAILED` + `ExitCode=1:0` 说明程序自己报错，不是集群问题。

### 5. 数组任务与依赖

**概念讲解**

超算最典型的用法：同一个程序跑上百组参数。数组任务把「一个脚本 × N 个下标」交给调度器统一管理，并可用 `%` 限制并行度。

**示例：array.sbatch**

```bash
#!/bin/bash
#SBATCH --job-name=sweep
#SBATCH --partition=compute
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=01:00:00
#SBATCH --array=1-20%5              # 下标 1~20，同时最多跑 5 个
#SBATCH --output=logs/sweep-%A_%a.out

set -euo pipefail
mkdir -p logs results
cd "$SLURM_SUBMIT_DIR"

# 无集群时可在本地模拟第 3 个任务：
#   SLURM_ARRAY_TASK_ID=3 bash array.sbatch
idx=${SLURM_ARRAY_TASK_ID:-1}

python3 sim.py --param-id "$idx" --out "results/out-$idx.csv"
```

```bash
sbatch array.sbatch
squeue -u $USER -r                    # -r 把数组按元素展开显示
scancel 12345_7                       # 只取消第 7 个数组元素
sacct -j 12345 --format=JobID,State,Elapsed,MaxRSS | tail -25
```

依赖作业：等前一步成功再跑后一步。

```bash
# --parsable 让 sbatch 只输出作业号，方便脚本接收
pre=$(sbatch --parsable preprocess.sbatch)
echo "预处理作业号: $pre"

# afterok：前置作业成功后才启动；afterany 则无论成败都启动
sbatch --dependency=afterok:"$pre" main.sbatch
```

**常见错误**

- 20 个数组元素全提交又都申请大资源，把队列占满被管理员提醒——用 `%` 限制并发。
- 每个数组元素输出到同一个文件，内容互相覆盖（用 `%A_%a` 区分文件名）。
- 前置作业 `FAILED` 后，用 `afterok` 的后继作业永远不启动（先修前置，或改用 `afterany`）。
- `$SLURM_ARRAY_TASK_ID` 忘了设默认值，本地模拟时因 `set -u` 直接报错。

### 6. 交互式作业：srun 与 salloc

**概念讲解**

需要在计算节点上边调试边改代码时，申请一个交互式 shell，而不是把调试循环塞进 sbatch 反复排队。

```bash
# 申请 1 节点、1 核、2G、30 分钟的交互 shell（在集群登录节点执行）
srun --pty --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=2G --time=00:30:00 bash

# 进入后 hostname 会显示计算节点名；退出用 exit

# salloc 先占资源，再在分配的资源上多次 srun
salloc --nodes=1 --cpus-per-task=4 --mem=8G --time=01:00:00
srun hostname          # 在已分配的资源上执行命令
exit                   # 释放资源
```

交互式作业同样占用队列资源和时间额度，调试完请及时 `exit`。

**常见错误**

- 用 `ssh compute01` 直接连计算节点（多数集群不允许）。
- 交互式会话申请 24 小时占着不用，被管理员清理。
- 在交互式会话里跑到 `--time` 限额被强制结束，忘了保存中间结果。

### 7. 失败排查清单

按顺序排查（命令在集群登录节点执行）：

```bash
# 1) 状态与退出码
sacct -j <jobid> --format=JobID,State,ExitCode,Elapsed,MaxRSS,ReqMem,MaxVMSize

# 2) 输出与错误文件
cat <jobname>-<jobid>.out
cat <jobname>-<jobid>.err

# 3) 详细信息：工作目录、命令行、依赖
scontrol show job <jobid>
```

| 症状 | 可能原因 | 处理 |
| --- | --- | --- |
| State=OUT_OF_MEMORY 或输出被截断 | 内存不够 | 提高 --mem；先用测试作业实测 MaxRSS |
| State=TIMEOUT / CANCELLED | 超过 --time | 提高时间；程序定期保存中间结果 |
| State=FAILED, ExitCode=1:0 | 程序自身报错 | 看 .err 末尾；用 `srun --pty` 复现 |
| State=FAILED, ExitCode=127 | 命令找不到 | 检查 module load 与 PATH，或用绝对路径 |
| 一直 PD，Reason=Resources | 资源暂时不足 | 等待或降低请求；`squeue --start` 估算 |
| .out 为空 | 输出路径或缓冲问题 | 显式 --output；Python 用 `flush=True` |
| 提交后立刻退出 | 脚本语法或换行符 | `bash -n` 检查；处理 CRLF |

**常见错误**

- 不看 `.err` 就重新提交，同一错误反复发生。
- 在登录节点反复重跑调试，而不是用 `srun` 申请交互资源。
- 把 home 配额写满（例如把几十 GB 中间文件留在 home），导致后续所有作业失败；中间文件应写到 scratch 并定期清理。
- 超时被杀后不加检查点就简单加倍 `--time`，再次超时浪费排队时间。

## 练习

1. （无账号替代）写一个 hello.sbatch，逐行给每个 `#SBATCH` 指令加中文注释，说明为什么需要它；用 `bash -n hello.sbatch` 做语法检查。
2. （无账号替代）数组脚本本地模拟：写一个使用 `${SLURM_ARRAY_TASK_ID:-1}` 的脚本，用 `for i in $(seq 1 10); do SLURM_ARRAY_TASK_ID=$i bash sim.sh; done` 在 WSL 里跑一遍，产出 10 个结果文件。
3. 资源估算：测试作业 `MaxRSS=3.2G`、`Elapsed=00:17:42`，下一次提交你会写什么 `--mem` 与 `--time`？写出完整 SBATCH 头并说明理由。
4. （无账号替代）脚本审查：程序是单线程 numpy，实测需约 20 分钟、4G 内存；下面 SBATCH 头至少有 5 个问题，请找出并改正：`--partition=debug`、`--time=00:05:00`、`--mem=1G`、`--ntasks=16`、`--output=/home/user/a.out`（且该用户除家目录外没有其他可写路径）。
5. （有账号）提交一个 1-10 的数组作业，用 `sacct -j <作业号> --format=JobID,State,Elapsed,MaxRSS` 汇总每个元素状态；若有失败的，写出你的排查过程。

## 自测清单

- [ ] 我能画出登录节点/计算节点/调度器/存储的关系，并说出登录节点禁忌
- [ ] 我能独立写出带资源、时间、输出重定向的 sbatch 脚本
- [ ] 我理解 nodes/ntasks/cpus-per-task 的区别，知道何时用哪种
- [ ] 我能在作业结束后用 sacct 查到状态与 MaxRSS
- [ ] 我会写数组任务并用 `%` 限制并发
- [ ] 我会用 `afterok` 串联依赖
- [ ] 我会用 `srun --pty` 申请交互式调试
- [ ] 我有一张自己的失败排查清单（OOM/超时/退出码/排队）

## 参考资料

- Slurm 官方文档：https://slurm.schedmd.com/documentation.html
- Slurm 快速入门：https://slurm.schedmd.com/quickstart.html
- sbatch：https://slurm.schedmd.com/sbatch.html
- squeue：https://slurm.schedmd.com/squeue.html
- sacct：https://slurm.schedmd.com/sacct.html
- srun：https://slurm.schedmd.com/srun.html
- sinfo：https://slurm.schedmd.com/sinfo.html
- 数组任务：https://slurm.schedmd.com/job_array.html
