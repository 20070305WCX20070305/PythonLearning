# 01 SSH 进阶与 rsync 数据传输

## 学习目标

- 会用 `~/.ssh/config` 定义主机别名、端口、密钥、跳板机与保活参数。
- 会用 ssh-agent 缓存私钥口令，并知道代理转发的风险。
- 能在 scp 与 rsync 之间做选择，用 rsync 完成增量同步、排除、dry-run、断点续传。
- 会用 tar/gzip 打包大量小文件，并用 sha256sum 在两端校验完整性。
- 知道 WSL2 与集群互传数据的坑：换行符、跨盘性能、文件权限。

## 前置知识

- 阶段 01：ssh 登录、ssh-keygen、scp 基础、Linux 文件权限（chmod）。
- 会用 `man` 与 `--help` 查命令；会写简单的 bash 循环。

## 建议用时

6~8 小时（含练习）。

## 正文

### 1. SSH config：把长命令变成别名

**概念讲解**

每次输入 `ssh -i ~/.ssh/id_ed25519 -p 22 student42@login.hpc.example.edu` 很低效，也容易写错。OpenSSH 会读取 `~/.ssh/config`，把常用主机定义成别名。参数优先级：命令行 > `~/.ssh/config` > `/etc/ssh/ssh_config`，所以别名可以被临时覆盖。

**示例 1：一份够用的 config**（在本地 WSL 中创建）

```text
# 文件：~/.ssh/config
# 第一个匹配的 Host 段生效，段落顺序有讲究

Host cluster
    HostName login.hpc.example.edu
    User student42
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 30
    ServerAliveCountMax 6

Host jump
    HostName gw.example.edu
    User student42

# 没有公网直连时：先连 jump，再从 jump 连 lab
Host lab
    HostName cluster.lab.example.edu
    User student42
    IdentityFile ~/.ssh/id_ed25519
    ProxyJump jump
    ServerAliveInterval 30
```

```bash
chmod 600 ~/.ssh/config     # 权限必须是 600

ssh cluster                 # 等价于上面那条很长的 ssh 命令
scp report.pdf lab:~/       # scp 与 rsync 都会读取这个别名
ssh -G cluster              # 打印最终生效的配置，用来检查有没有写错
```

参数说明：

- `ServerAliveInterval 30` + `ServerAliveCountMax 6`：每 30 秒发一次保活包，累计 6 次无响应才断开，避免会话假死。
- `ProxyJump jump`：本地 → jump → lab。私钥只放在本地，跳板机上不需要。
- 需要频繁建立连接时可加 `ControlMaster auto` 与 `ControlPersist 10m` 复用连接；排障阶段建议先不开，报错更直观。

**常见错误**

- 权限不是 600：报 `Bad owner or permissions on ~/.ssh/config`，ssh 直接拒绝使用。
- `Host` 与 `HostName` 写反：`Host` 是别名，`HostName` 才是真实地址。
- 在 `Host *` 段里写了 `ProxyJump`，导致所有主机都走跳板机。
- config 从 Windows 复制过来带 CRLF，行尾多出 `^M`（见第 5 节）。

### 2. ssh-agent：口令只输一次

**概念讲解**

私钥设置口令（passphrase）更安全，但每次登录都输入很烦。ssh-agent 在内存中缓存已解锁的私钥，之后的 ssh/scp/rsync/git 都自动使用。

```bash
# 启动 agent 并把环境变量注入当前 shell
eval "$(ssh-agent -s)"

# 添加私钥；-t 2h 表示 2 小时后自动过期
ssh-add -t 2h ~/.ssh/id_ed25519

ssh-add -l                  # 列出已加载的密钥
ssh-add -D                  # 全部移除（例如离开电脑前）
```

注意：agent 是「每个登录会话」的，新开终端需要重新 `eval`。最省事的做法是把下面两行写进 `~/.bashrc`（登录时只弹一次口令）：

```bash
# ~/.bashrc 末尾
eval "$(ssh-agent -s)" >/dev/null
ssh-add -t 8h ~/.ssh/id_ed25519 2>/dev/null
```

代理转发（`ssh -A cluster`）可以把本地 agent 借给远程主机用，方便在集群上执行 git 拉取；但同机上拥有权限的人都可能借用你的密钥，默认不要开，需要时再用、用完即退。

**常见错误**

- 忘记 `eval "$(ssh-agent -s)"` 就 `ssh-add`，报 `Could not open a connection to your authentication agent`。
- 在跳板机上放自己的私钥并 `ssh-add`（正确做法是私钥只在本地，用 ProxyJump）。
- 为图省事把带口令私钥改成无口令（至少保留 passphrase + agent）。

### 3. scp 与 rsync：各有用途

**概念讲解**

`scp` 是「网络版 cp」：简单、直接、每次全量；`rsync` 会先比较两端差异，只传变化部分，适合重复同步、大目录、弱网。

| 对比项 | scp | rsync |
| --- | --- | --- |
| 传输方式 | 每次全量 | 增量（默认比大小+时间，`-c` 比校验和） |
| 断点续传 | 不支持 | `--partial` 保留半成品，重跑续传 |
| 排除/过滤 | 无 | `--exclude` / `--exclude-from` / `--include` |
| 删除目标多余文件 | 无 | `--delete`（危险，必须先 --dry-run） |
| 压缩 | `-C` | `-z` |
| 适用场景 | 单个小文件、一次性拷贝 | 反复同步的代码/数据/结果目录 |

**示例 2：本地模拟「远程同步」**（无账号也能练）

```bash
# 用两个本地目录模拟本地与远端
mkdir -p ~/rsync-lab/src ~/rsync-lab/dst
echo "hello" > ~/rsync-lab/src/a.txt
echo "temp"  > ~/rsync-lab/src/b.tmp
echo "old"   > ~/rsync-lab/dst/old.txt

# 尾部斜杠语义不同：
rsync -av ~/rsync-lab/src  ~/rsync-lab/dst   # 结果：dst/src/a.txt（连目录本身一起放）
rsync -av ~/rsync-lab/src/ ~/rsync-lab/dst/  # 结果：dst/a.txt（只放目录内容）

# 排除 *.tmp，先 dry-run 看看会做什么
rsync -av --dry-run --exclude '*.tmp' ~/rsync-lab/src/ ~/rsync-lab/dst/

# 确认无误后执行；--delete 会删掉 dst/old.txt，务必先 dry-run
rsync -av --delete --exclude '*.tmp' ~/rsync-lab/src/ ~/rsync-lab/dst/
```

**示例 3：与集群同步**（有账号时在本地 WSL 中执行）

```bash
# 上传：本地 -> 集群（-P 等价于 --progress --partial）
rsync -avzP --exclude '.git' --exclude '__pycache__' \
    ./myproject/ cluster:~/myproject/

# 下载：集群 -> 本地
rsync -avzP cluster:~/myproject/results/ ./results/

# 删除远端多余文件前，先 dry-run 检查清单
rsync -avz --dry-run --delete cluster:~/myproject/results/ ./results/

# 未配 config 时用 -e 指定 ssh 参数（注意端口 2222 仅为示例）
rsync -avzP -e 'ssh -p 2222' ./data/ student42@login.hpc.example.edu:~/data/
```

小技巧：

- `--info=progress2` 显示整体进度，比逐个文件的 `--progress` 清爽。
- `--bwlimit=10M` 限速，避免占满实验室共享链路。
- 弱网大文件先 `--partial` 保留半成品再重跑；文件正在被追写时不要用 `--append`，重传更安全。

**常见错误**

- 源目录尾部斜杠漏写或多写，目标端多出一层目录（最常见的 rsync 事故）。
- 对结果目录直接 `--delete` 而没先 `--dry-run`，误删数据。
- 作业还在写结果时就 rsync，得到不完整副本（应等作业结束后同步）。
- 忘记 `-a` 导致权限/时间丢失；或加了 `-a` 但目标在 `/mnt/d` 上，权限本就不生效，属正常现象。

### 4. tar 与校验：大量小文件的正确姿势

**概念讲解**

大量小文件逐个 rsync 时每个文件都要往返握手，速度极慢。先打包成单个归档再传，通常快一个量级；传输后用 sha256sum 校验，确认没有损坏。

```bash
# 打包 + gzip
tar -czf results-2026-09.tar.gz results/

# 查看归档内容（不解压）
tar -tzf results-2026-09.tar.gz | head

# 解压到指定目录
mkdir -p /tmp/check && tar -xzf results-2026-09.tar.gz -C /tmp/check

# 生成校验和并校验
sha256sum results-2026-09.tar.gz > results-2026-09.tar.gz.sha256
sha256sum -c results-2026-09.tar.gz.sha256    # 输出 OK 表示一致
```

传输两端都算一遍哈希再对比，是最直接的数据完整性保证（在集群登录节点执行第二条）：

```bash
# 本地（WSL）计算
sha256sum results-2026-09.tar.gz
# 集群上计算
sha256sum results-2026-09.tar.gz
# 两行哈希应完全一致
```

**常见错误**

- 打包时把旧归档也收进去：`tar -czf r.tar.gz .` 会把已存在的 r.tar.gz 再装进去，用明确目录名而不是 `.`。
- 归档名没有日期/版本，几周后分不清哪份是哪份。
- 只算一端哈希就宣布「完整」，必须两端对比。
- 对已压缩数据（图片、.npz）再 gzip，慢且收益小，可改用 `tar -cf` 不压缩。

### 5. 大文件、大量文件与 WSL 注意事项

**概念讲解**

- 大文件：优先 rsync `--partial` 允许续传；弱网加 `-z` 可能反而更慢（压缩耗 CPU），可先不加试试。
- 大量小文件：先 tar 再传，或用 `rsync -a --info=progress2` 慢慢跑。
- WSL 访问 Windows 盘（/mnt/c、/mnt/d）走 9p 文件系统，大量小文件 I/O 很慢；先在 WSL 家目录打包，再传到集群。
- 换行符：Windows 侧编辑过的 `.sh` 脚本带 CRLF，集群执行时报 `bad interpreter: /bin/bash^M`。
- 文件权限：`/mnt/d` 上 chmod 不生效，私钥、脚本应放在 WSL 家目录（`~/`）。

```bash
# 检查脚本是否含 CRLF（输出带 \r 即中招）
file scripts/run.sh
sed -n '1p' scripts/run.sh | od -c | head -1

# 修复：删除行尾 \r
sed -i 's/\r$//' scripts/run.sh
dos2unix scripts/run.sh          # 若已安装 dos2unix

# 查看磁盘与配额（第二条在集群登录节点执行，具体命令因集群而异）
df -h ~
quota -s 2>/dev/null || true
```

**常见错误**

- 在 `/mnt/d` 上直接 rsync 几万个小文件到集群，速度慢且中途易报错。
- 上传了带 CRLF 的作业脚本，sbatch 报奇怪的解释器错误。
- 私钥放在 `/mnt/d`，WSL 权限检查失败无法使用。
- 传输结束后没有校验，几天后才发现文件损坏。

## 练习

1. （无账号替代）本地 rsync 实验：按示例 2 操作，然后回答：`rsync -av src dst` 与 `rsync -av src/ dst/` 的结果差异是什么？把观察写进笔记。
2. （无账号替代）写一份 `~/.ssh/config`，包含两个主机（其中一个走 ProxyJump），用 `ssh -G 别名 | grep -Ei 'hostname|user|proxyjump'` 自查。
3. 打包校验：在 WSL 家目录造 100 个小文件（`for i in $(seq 1 100); do echo "$i" > "f$i.txt"; done`），tar+gzip 后生成 sha256；故意改一个字节再校验，观察报错并记录。
4. （无账号替代）审查下面这段「从集群拉结果」的假想脚本，列出至少 4 个问题：`rsync -a --delete cluster:~/results/ /mnt/d/results/` 直接执行、没有 dry-run、没有校验、中断后从头再来、作业还在写结果。
5. （有账号）真实往返：用 `rsync -avzP` 上传一个约 10 MB 的文件到集群家目录，`ssh cluster sha256sum 文件` 后与本地对比；再拉回本地并再次校验。

## 自测清单

- [ ] 我能说清 Host、HostName、ProxyJump 的作用并写出正确的 config
- [ ] 我能用 ssh-agent 让一天内只输一次口令
- [ ] 我能解释 rsync 源目录尾部斜杠的区别
- [ ] 我会先 `--dry-run` 再用 `--delete`
- [ ] 我知道 `--partial` 的用途和适用场景
- [ ] 我能用 tar 打包并说出「不解压查看内容」的命令
- [ ] 我会用 sha256sum 在传输两端校验
- [ ] 我知道 `/mnt/d` 慢与 CRLF 两个 WSL 坑

## 参考资料

- OpenSSH 手册与各命令手册：https://www.openssh.com/manual.html
- ssh_config(5)：https://man7.org/linux/man-pages/man5/ssh_config.5.html
- ssh-agent(1)：https://man7.org/linux/man-pages/man1/ssh-agent.1.html
- rsync 官方网站（含手册入口）：https://rsync.samba.org/
- tar(1)：https://man7.org/linux/man-pages/man1/tar.1.html
- sha256sum(1)：https://man7.org/linux/man-pages/man1/sha256sum.1.html
