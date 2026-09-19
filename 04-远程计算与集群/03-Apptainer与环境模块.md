# 03 环境模块与 Apptainer 容器

## 学习目标

- 会用 Lmod 的 `module avail/load/list/purge/spider/show` 管理软件环境。
- 能说明集群为什么用容器，以及 SIF、.def 各是什么。
- 会用 `apptainer pull/exec/run/shell` 运行镜像。
- 能写一个最小的 .def 文件并构建、运行。
- 会把容器与 sbatch 组合，形成可复现的作业。

## 前置知识

- 阶段 01：Linux 权限、bash；阶段 02：subprocess 概念。
- 本阶段 01/02：ssh/rsync 与 sbatch 基础。

## 建议用时

6~8 小时（含练习）。

## 正文

### 1. 环境模块：module 命令

**概念讲解**

集群上同一个软件往往装了多个版本（gcc、python、cuda 等），Lmod / Environment Modules 用环境变量来切换：`module load python/3.12` 会修改 PATH、LD_LIBRARY_PATH 等。具体模块名与版本以各集群为准。

```bash
# 以下命令在集群登录节点（或任何装了 Lmod 的机器）执行
module avail                # 列出可加载模块（输出通常进 less，按 q 退出）
module avail python         # 只看 python 相关
module spider python        # 搜索「隐藏」模块（avail 看不到的依赖链）
module show python/3.12     # 看这个模块改了哪些环境变量
module load python/3.12     # 加载
module list                 # 当前已加载的模块
module purge                # 全部卸载，回到干净环境
module swap gcc/12 gcc/13   # 换成另一个版本
```

注意：`module` 是 shell 函数，只在当前 shell 有效；每个新终端、每个 sbatch 脚本都要重新 load。

**常见错误**

- 在 `.bashrc` 里交互式 load 一堆模块，导致作业环境不可控——脚本里显式 load 更可靠。
- 只 load 了 python，没 load 对应的编译器等依赖（用 `module spider` 看依赖链）。
- 作业脚本里 load 失败后继续跑，结果用了错误版本——配合 `set -euo pipefail` 让失败立刻暴露。

### 2. 为什么集群用容器

**概念讲解**

集群操作系统版本往往较旧、软件由管理员统一管理，而你的代码可能需要特定 Python / 库版本；同时集群一般不允许普通用户用 root 安装系统包。容器把「操作系统 + 依赖 + 代码」打包成镜像，在用户态运行，既不动系统环境，又能在任何节点得到一致环境。Apptainer 是 Singularity 的社区后继（SingularityCE 是姊妹项目，命令基本兼容），专为 HPC 设计：单文件镜像、无需守护进程、默认以普通用户运行。

（Docker 本路线不展开：它面向服务部署、需要守护进程，集群上通常不可用；本项目用 Apptainer，Docker 后置到以后按需学习。）

**常见错误**

- 以为必须 root 才能在集群装包——先问 module 与 Apptainer。
- 把 `pip install --user` 装到家目录当作「永久方案」，其实换节点/换模块就出问题（见第 7 节）。
- 直接把 Docker 工作流搬过来，在集群上找不到 docker 命令。

### 3. Apptainer 基本概念：SIF 与 .def

**概念讲解**

- SIF（Singularity Image Format）：单文件、只读、可校验的镜像，例如 `python.sif`。
- `.def` 文件：构建镜像的「配方」，分段书写：`Bootstrap/From`（基础镜像）、`%post`（构建时安装命令）、`%environment`（运行时环境变量）、`%runscript`（`apptainer run` 的入口）、`%files`、`%labels`、`%help`。
- 镜像通常从容器仓库拉取：`docker://ubuntu:24.04` 表示以 OCI/Docker 镜像为基础，Apptainer 负责转换（这里只是复用镜像格式，不是使用 Docker 工具）。
- 构建一般在登录节点执行；多数集群提供 `--fakeroot` 让普通用户无需真正 root 即可构建。

```bash
# 在集群登录节点执行
apptainer pull ubuntu.sif docker://ubuntu:24.04   # 拉一个基础镜像
apptainer inspect ubuntu.sif                      # 查看镜像元数据/标签
file ubuntu.sif                                   # 确认是 SIF 文件
```

保底方案：若网络受限但已有别人下载好的镜像归档（例如 docker save 出来的 tar），可用 `apptainer build x.sif docker-archive://image.tar` 转换，不必联网。

**常见错误**

- 把 `docker://` 与 `apptainer://` 前缀写混。
- 在计算节点构建镜像（多数集群要求在登录节点构建或需要特定配置）。
- SIF 文件名不带版本，几个月后无法和 .def 对应。

### 4. 常用命令：exec / run / shell

**概念讲解**

```bash
apptainer exec python.sif python3 -V          # 在镜像里执行一条命令
apptainer exec python.sif python3 script.py   # 跑自己的脚本（文件需能看见）
apptainer run  python.sif                     # 执行镜像的 %runscript
apptainer shell python.sif                    # 进入镜像内交互 shell（exit 退出）

# 把宿主机目录挂进容器（默认会自动挂载 home、/tmp 等）
apptainer exec --bind /scratch/$USER/data:/data python.sif python3 /data/run.py

# 看看容器里是什么系统
apptainer exec ubuntu.sif cat /etc/os-release
```

要点：

- 容器内默认能访问你的家目录；`--bind 宿主机目录:容器目录` 显式挂载其他路径（如 scratch）。
- `exec` 适合「一条命令跑完就走」，是作业脚本里最常用的形式。
- `--cleanenv` 可隔离宿主机环境变量（作业中常加，配合 `--env KEY=VALUE` 传参）。

**常见错误**

- 容器里写数据写到挂载点之外，作业结束文件「消失」——输出要写到 bind 的目录。
- 用 `exec` 却忘了 `--bind`，容器里看不到 scratch 上的大数据。
- 把 `run` 与 `exec` 混用：`run` 执行的是 `%runscript`，不是你的任意命令。

### 5. 写一个最小 .def

**示例：python.def**

```text
Bootstrap: docker
From: ubuntu:24.04

%post
    apt-get update
    apt-get install -y --no-install-recommends python3 python3-numpy
    rm -rf /var/lib/apt/lists/*

%environment
    export LC_ALL=C.UTF-8
    export PYTHONUNBUFFERED=1

%runscript
    exec python3 "$@"

%labels
    Author WangChenxuan
    Version 0.1

%help
    最小示例镜像：提供 python3 与 numpy。
```

构建与运行（在集群登录节点执行；本地 WSL 若装了 Apptainer 同理）：

```bash
apptainer build python.sif python.def     # 集群支持时建议加 --fakeroot
apptainer exec python.sif python3 -c "import numpy; print(numpy.__version__)"
apptainer run  python.sif -c "print('hello from container')"
apptainer shell python.sif                # 进入后 exit 退出
```

**常见错误**

- `%post` 里 apt 源不可达：登录节点一般能联网；若不能，改用学校镜像站或 `Bootstrap: localimage` 从已有镜像修改。
- 忘记写 `%runscript`，`apptainer run` 没有输出。
- 在 `%post` 里装 GUI / 系统服务，既装不上也没必要。
- 基础镜像用 `ubuntu:latest`，可复现性下降（固定标签更好）。

### 6. 在作业中使用容器

```bash
#!/bin/bash
#SBATCH --job-name=cont
#SBATCH --partition=compute
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --output=cont-%j.out

set -euo pipefail
module purge
module load apptainer          # 模块名以集群为准
cd "$SLURM_SUBMIT_DIR"

# 数据在 $SLURM_SUBMIT_DIR（家目录/项目目录），显式 bind 到 /work
apptainer exec --cleanenv \
    --bind "$SLURM_SUBMIT_DIR":/work \
    python.sif python3 /work/analysis.py --out /work/results/out.csv
```

**常见错误**

- sbatch 脚本里不 `module load apptainer`，计算节点找不到命令（ExitCode=127）。
- 容器内用绝对路径访问宿主机文件却没有 bind。
- 同一作业里既 load 系统 python 又在容器里跑 python，版本混淆。

### 7. 可复现环境的意义

**概念讲解**

容器镜像是一份「配方 + 固化产物」，把操作系统、依赖、版本全部锁住；配合后续会讲的依赖版本锁定与回归测试，别人（或三个月后的你）能在任何节点复现同一结果。可复现性是计算科学的基本功，本阶段只需做到：分析代码配有形如 `python.def` 的配方，并随项目一起版本管理（阶段 05 会系统展开工程化做法）。

**常见错误**

- 镜像更新了但文件名/版本没变，几天后结果对不上。
- 把镜像在家目录拷贝多份，浪费配额；镜像应放项目目录或共享位置。

## 练习

1. （无账号替代）模块命令纸面练习：写出完成「查看集群有哪些 python 模块 → 看依赖关系 → 加载 python/3.12 → 确认已加载 → 全部卸载」的 5 条命令，并解释 `avail` 与 `spider` 的区别。
2. （无账号替代）为常用的分析脚本写一个 .def：固定基础镜像标签，`%post` 里安装 numpy，`%runscript` 接收参数；逐段用中文注释说明作用（可以只交文档与 .def，不构建）。
3. 容器命令辨析：写出完成下列任务的命令：(a) 在容器里查 python 版本；(b) 交互进入容器；(c) 把 scratch 目录挂进容器跑脚本；(d) 执行镜像默认入口。
4. （无账号替代）作业脚本审查：找出下面脚本的至少 4 个问题——没有 `module load apptainer`、没有 `cd $SLURM_SUBMIT_DIR`、`--bind` 漏了、容器内用了不存在的 `python` 命令、结果写到容器内 `/root`。
5. （有账号）构建并运行你的 .def：完成 `apptainer build` 与 `apptainer exec python.sif python3 -V`，把版本输出记到笔记；若构建受限，询问管理员支持的构建方式并记录。

## 自测清单

- [ ] 我能用 module 命令切换软件版本，并知道它只影响当前 shell
- [ ] 我能说出集群用容器的三个原因
- [ ] 我能解释 SIF 与 .def 的区别
- [ ] 我会 exec/run/shell 三种运行方式并知道何时用哪个
- [ ] 我会写 %post/%environment/%runscript 三段并完成构建
- [ ] 我能在 sbatch 中正确使用容器并 bind 数据目录
- [ ] 我知道可复现环境需要「配方 + 版本固定」

## 参考资料

- Apptainer 用户文档：https://apptainer.org/docs/user/latest/
- 定义文件（.def）参考：https://apptainer.org/docs/user/latest/definition_files.html
- Apptainer 官网：https://apptainer.org/
