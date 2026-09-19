# 项目：Slurm 远程任务管理 CLI

## 背景与目标

在集群上跑批量计算时，手工流程是：改脚本 → scp 上传 → sbatch 提交 → squeue 盯着 → 失败重来 → rsync 拉结果。作业一多就会乱。本项目写一个命令行工具，把这条链路自动化：

1. 读取一个 JSON 作业清单（名称、命令、CPU、内存、时间、重试次数、结果目录）。
2. 为每个作业生成 sbatch 脚本。
3. 通过 ssh 提交到集群（ssh 使用阶段 01 学过的 `~/.ssh/config` 别名）。
4. 轮询 squeue/sacct 获取状态。
5. 失败的作业自动重试（不超过配置的次数）。
6. 完成后用 rsync 把结果归档回本地。

目标不是「万能调度器」，而是把本阶段的技能串成一个可复用的函数式小工具，并保证在没有集群账号时也能完整开发和测试（dry-run 模式）。

## 前置知识

- 阶段 01/02/03 全部；本阶段 01（ssh/rsync）、02（Slurm）、03（Apptainer，可选）。
- Python：argparse、logging、subprocess、json、pathlib、time、shlex。

## 建议用时

2~3 周（与 02/03 主题交叉推进），合计约 20~30 小时。

## 总体流程

```text
jobs.json --> load_jobs --> render_sbatch --> build/<name>.sbatch
                                                |
                          dry-run（安全）        |  真实执行
                                                v
                                       submit(ssh + scp + sbatch) --> job_id
                                                |
                                       poll_status(squeue/sacct)
                                                |
                          +---------------------+---------------------+
                          |                                           |
                     成功/失败                                    失败且重试未用完
                          |                                           |
                   archive_results(rsync) <---------------- retry_failed --> 重新 submit
                          |
                   report.json / 控制台总结
```

## MVP 与进阶

MVP（必须完成）：

- 读取 jobs.json：合并 defaults、校验必填字段（name、command）。
- 为每个作业生成语法正确的 sbatch 脚本并写入本地 `build/` 目录。
- `--dry-run`：不执行任何 ssh/scp/rsync/sbatch，打印「将要执行的命令」并模拟状态流转。
- 有账号时：真实提交、轮询到最终状态。
- 日志（logging）同时输出到控制台与 `logs/job_manager.log`。

进阶（选做）：

- 失败自动重试（`retries` 字段），记录每次尝试次数。
- 用 rsync 归档结果目录，成功/失败汇总写入 `report.json`。
- `--only 名称` 过滤、`--retry-failed` 只重试失败作业。
- 数组作业支持（把某个作业配置渲染成 `--array` 形式）。
- 生成的脚本做明显规则检查（缺 `--time`、输出路径为绝对路径等）。

## 技术约束

- Python 只用已学内容：argparse、logging、subprocess、json、pathlib、time、shlex；**函数式写法，不定义 class**；不引入第三方库。
- 远程操作一律通过命令行程序：ssh、scp（只用于上传脚本）、rsync、sbatch、squeue、sacct。
- 不自己实现 SSH 协议，不调用集群 API；主机别名来自 `~/.ssh/config`。
- 若写测试，用函数式 pytest，且测试必须能在 dry-run 下运行。
- 不写 GitHub Actions（阶段 05 内容）。

## dry-run 模式

- `--dry-run` 下不调用 ssh/scp/rsync/sbatch 中的任何一个。
- 生成 sbatch 脚本到 `build/`，并用 `shlex.join(...)` 打印「将执行的命令」，方便人工核对。
- 用内存中的状态流转模拟作业生命周期：PENDING → RUNNING → COMPLETED；可加一个时间参数控制模拟速度。
- 进阶：可用 `--simulate-fail 作业名:次数` 注入失败，用来测试重试逻辑（自己设计，不强制）。
- 所有测试只在 dry-run 下跑，保证开发期完全不需要集群。

## 里程碑

1. 里程碑 1：配置读取 + 脚本渲染。`python3 job_manager.py --config jobs.example.json --dry-run --render-only` 能生成 3 个 sbatch 脚本并打印将执行的命令。
2. 里程碑 2：dry-run 调度模拟。submit/poll_status 的 dry-run 分支跑通完整生命周期，输出每个作业的最终状态总结。
3. 里程碑 3：真实远程（有账号）。用 ssh 别名提交一个作业、轮询到 COMPLETED、rsync 拉回结果；无账号者用「将执行的命令」逐条人工核对替代。
4. 里程碑 4：重试与报告。失败作业按 `retries` 自动重试；生成 `report.json`（最终状态、尝试次数、耗时）。
5. 里程碑 5（进阶）：CLI 打磨（`--only`、`--retry-failed`、日志级别）并写一页使用说明。

## 建议目录结构

```text
04-远程计算与集群/项目-Slurm任务管理CLI/
├── README.md              # 本文件
├── starter/
│   ├── jobs.example.json  # 示例作业配置
│   └── job_manager.py     # 函数骨架，从填 TODO 开始
├── build/                 # dry-run 生成的 sbatch 脚本（运行时创建）
├── logs/                  # 日志（运行时创建）
└── results/               # 归档回本地的结果（运行时创建）
```

建议把 `starter/job_manager.py` 复制一份作为工作副本（例如放到项目根），保留 starter 原样。

## 运行方法

```bash
# 语法检查（无需集群）
python3 -m py_compile job_manager.py

# dry-run：生成脚本 + 模拟状态，全程不联网
python3 job_manager.py --config jobs.example.json --dry-run

# 只渲染脚本，不做状态模拟
python3 job_manager.py --config jobs.example.json --dry-run --render-only

# 真实提交（需要集群账号，且 ssh config 中有 cluster 别名）
python3 job_manager.py --config jobs.json --host cluster

# 只重试上次失败的作业并写报告（进阶）
python3 job_manager.py --config jobs.json --host cluster --retry-failed --report report.json
```

## 验收标准

- [ ] `python3 -m py_compile job_manager.py` 通过
- [ ] 代码中没有 class，只使用已学标准库
- [ ] dry-run 下完整跑通：读配置 → 生成脚本 → 模拟状态 → 重试 → 报告，且没有任何真实远程调用
- [ ] 生成的 sbatch 脚本包含完整 SBATCH 头（job-name/partition/cpus/mem/time/output）
- [ ] 有账号时：至少完成一次真实提交并拿到最终状态
- [ ] 失败重试有日志、有次数上限、不会无限循环
- [ ] 归档使用 rsync，且真实执行前先跑一次 `--dry-run`
- [ ] README 与代码注释能让他人复现你的运行过程（为阶段 05 的协作打底）

## 参考资料

- Slurm 官方文档：https://slurm.schedmd.com/documentation.html
- sbatch：https://slurm.schedmd.com/sbatch.html
- sacct：https://slurm.schedmd.com/sacct.html
- rsync 官方网站：https://rsync.samba.org/
