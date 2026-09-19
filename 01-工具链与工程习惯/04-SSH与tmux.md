# 04-SSH与tmux

## 学习目标

- 理解 SSH 是什么、为什么远程登录是安全的
- 理解密钥认证原理：公钥、私钥、authorized_keys、known_hosts
- 会写 `~/.ssh/config` 别名，简化登录命令
- 会用 scp/sftp 传文件，会用 ssh-copy-id 分发公钥
- 会做最基本的本地端口转发 `ssh -L`
- 掌握 tmux 会话、窗口、面板的使用与常用快捷键
- 会用 tmux 跑长任务，断开后重连不丢任务
- 会写简单的 tmux 配置与状态栏

## 前置知识

- 01、02 课：Linux 命令与 Shell 基础
- 阶段 00 已完成：`sudo apt install openssh-server` 未安装过也没关系，本课第一步就装
- 阶段 00 已生成 SSH 密钥（`~/.ssh/id_ed25519` 与 `.pub`）；没生成过按本课第 2 节做

## 建议用时

6~8 小时。tmux 部分建议连续使用一周形成肌肉记忆。

## 正文

### 1. SSH 是什么

SSH（Secure Shell）是在两台机器之间建立加密通道的协议。你在本地终端敲的命令通过加密通道
发到远程主机执行，返回结果同样加密传回。它替代了早期明文传输的 telnet/rlogin，是远程计算、
集群登录、代码托管（GitHub 的 `git@github.com`）的通用基础设施。
```bash
ssh 用户名@主机地址           # 最常用形式
# 例：ssh wang@10.0.0.12
# 例：ssh wang@lab-server.example.edu -p 2222   # 非默认端口用 -p

exit                          # 退出远程会话，或按 Ctrl+D
```
第一次连接某主机时，会提示确认主机指纹，输入 `yes` 后写入 `~/.ssh/known_hosts`；
以后主机密钥变化会给出醒目的警告（可能是对方重装，也可能是中间人攻击）。
常见错误：

- 把「保存私钥」当成「记住密码」，私钥泄漏等于账号泄漏
- 看到 `REMOTE HOST IDENTIFICATION HAS CHANGED` 就照着网上说的删 known_hosts，应先确认对方是否重装过系统
- 用 root 直接登录远程，日常操作应使用普通账号加 sudo

### 2. 密钥认证原理与 authorized_keys

密码可以暴力猜解，密钥认证则是数学上几乎无法伪造的「挑战-应答」：

1. 本地有私钥（`~/.ssh/id_ed25519`，绝不外传）和公钥（`id_ed25519.pub`，可以随便发）
2. 把公钥追加到远程主机的 `~/.ssh/authorized_keys`
3. 登录时，远程主机用公钥加密一段随机数据，只有持有私钥的人能正确解密应答
4. 私钥本身始终不离开你的电脑，网络上传输的只是签名结果
```bash
# 生成密钥（阶段 00 已做过可跳过；推荐 ed25519 算法）
ssh-keygen -t ed25519 -C "wang@laptop"
# 一路回车：默认位置 ~/.ssh/id_ed25519，passphrase 可留空或设置

ls -l ~/.ssh
# id_ed25519       私钥，权限必须是 600
# id_ed25519.pub   公钥，可以给别人
# known_hosts      记录连接过的主机指纹
# config           别名配置（见下一节）
# authorized_keys  本机作为服务器时，保存允许登录的公钥

# 查看公钥内容（就是一行以 ssh-ed25519 开头的文本）
cat ~/.ssh/id_ed25519.pub
```
常见错误：

- 把 `id_ed25519.pub` 和 `id_ed25519` 搞混，把私钥贴到服务器或聊天软件里
- 私钥权限不是 600（或目录不是 700），SSH 会拒绝使用并报 `UNPROTECTED PRIVATE KEY FILE`
- 公钥粘贴时换行丢字符，authorized_keys 里变成一行乱码
- passphrase 设为空虽然方便，但笔记本丢了就等于密钥丢了；可以用 `ssh-add` 管理密钥解锁

### 3. 基本用法与 `~/.ssh/config` 别名

每次敲 `ssh wang@10.0.0.12 -p 2222 -i ~/.ssh/id_ed25519` 太麻烦，用配置文件起别名：
```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
nano ~/.ssh/config
```
```sshconfig
Host lab
    HostName 10.0.0.12
    User wang
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60

Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
```
之后直接：
```bash
ssh lab            # 等价于上面一长串
scp data.csv lab:~/lab-data/raw/
```
`ServerAliveInterval 60` 每 60 秒发一次心跳，能减少长时间无操作被防火墙断开的情况。
常见错误：

- config 缩进用 Tab 或四个空格都行，但每条 `Host` 块内键值不要写错拼写（如 `Hostname` 无效，正确是 `HostName`）
- 多个 Host 块之间不要用逗号；匹配多个主机用空格分隔，如 `Host lab server1`
- `~/.ssh/config` 权限过宽（组可写）也会被拒绝，`chmod 600 ~/.ssh/config` 最稳

### 4. 传文件：scp、sftp 与 ssh-copy-id
```bash
# 本地 -> 远程
scp data.csv lab:~/lab-data/raw/
scp -r raw/ lab:~/lab-data/          # 传目录加 -r

# 远程 -> 本地
scp lab:~/lab-data/raw/result.csv .
scp lab:~/logs/run.log ./local-run.log

# sftp 交互式传文件
sftp lab
# sftp> pwd / ls / cd     查看远程
# sftp> lls / lcd         查看本地（l 前缀表示 local）
# sftp> get result.csv    下载
# sftp> put data.csv      上传
# sftp> bye               退出

# 把本机公钥安装到远程，实现免密登录
ssh-copy-id lab
# 若没有这个命令：cat ~/.ssh/id_ed25519.pub | ssh lab "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```
大文件、断点续传、增量同步需要 `rsync`，它会在阶段 04（远程计算与集群）学习。
常见错误：

- scp 冒号后面的路径含空格忘记转义或用引号
- `scp -r a/ b/` 尾部的 `/` 影响结果：`scp -r raw lab:~/x` 与 `scp -r raw lab:~/x/` 目标结构可能不同，先在小文件上验证
- 传完不校验，科研数据应对比大小或哈希（05 课用 hashlib 算哈希）
- 用 scp 覆盖远程同名文件且无提示；重要结果先改名备份

### 5. 本地端口转发 `-L`

`ssh -L 本地端口:目标主机:目标端口 跳板机` 把远程服务「搬到」本地端口。
例如远程服务器上跑了一个 Web 服务（8000 端口），但它没有对公网开放：
```bash
# 在 WSL2 本机先开一个测试用的 8000 端口服务（python 自带）
python3 -m http.server 8000

# 另开一个终端，把本机 9000 转发到 localhost 的 8000
ssh -L 9000:localhost:8000 localhost

# 第三个终端里验证：访问本地 9000 就等于访问远端的 8000
curl -s http://localhost:9000 | head -n 5
```
工作后访问实验室内部网页、数据库、Jupyter 等常用这种「隧道」，本课只要求会读、会照着填参数。
常见错误：

- `-L` 的三个地址写反顺序，记住格式是「本地监听端口:目标地址:目标端口」
- 转发命令所在的终端一关，隧道就断；配合 tmux 保持
- 把内部服务误配置成对全网开放，转发默认只监听本机（127.0.0.1），不要随手加 `-g`

### 6. tmux：会话、窗口、面板

tmux（terminal multiplexer）让你在一个终端里管理多个会话，并且**会话与终端窗口解耦**：
关掉终端、断开 SSH，服务器上的会话照常运行，下次 `attach` 回来即可。
```bash
tmux new -s work          # 新建名为 work 的会话
tmux ls                   # 列出所有会话
tmux attach -t work       # 重新连接会话（可简写 tmux a -t work）
tmux kill-session -t work # 结束整个会话
tmux rename-session -t work experiment   # 重命名会话
```
三层结构：

- 会话（session）：一个工作场景，如「数据分析」「论文实验」
- 窗口（window）：会话里的标签页，如「编辑代码」「看日志」
- 面板（pane）：窗口里的分屏，如左边编辑器、右边运行输出
```bash
# 会话内也可以执行管理命令
tmux new -s second        # 在会话里再开会话（少见）
```
常见错误：

- 不建会话直接在终端跑长任务，SSH 一断任务就没了
- 把 tmux 当成必须一直开着的窗口，其实正确姿势是随时 `detach`，需要时再 `attach`
- 会话命名用 `vim`、`1` 这类无意义名字，几天后自己都不知道哪个是哪个

### 7. tmux 常用快捷键

所有快捷键都先按前缀 `Ctrl+b`（写作 C-b），松开后再按功能键：
| 快捷键 | 作用 |
| --- | --- |
| `C-b c` | 新建窗口 |
| `C-b n` / `C-b p` | 下一个 / 上一个窗口 |
| `C-b 0`~`9` | 跳到指定编号窗口 |
| `C-b d` | 分离会话（detach），回到普通终端 |
| `C-b %` | 左右分面板 |
| `C-b "` | 上下分面板 |
| `C-b 方向键` | 在面板间移动 |
| `C-b z` | 当前面板全屏 / 还原（zoom） |
| `C-b x` | 关闭当前面板（需确认） |
| `C-b ,` | 重命名当前窗口 |
| `C-b $` | 重命名当前会话 |
| `C-b [` | 进入滚动模式（用方向键/PageUp 翻历史，q 退出） |
| `C-b t` | 显示时钟（好玩但没用） |
| `C-b ?` | 查看全部快捷键 |
```bash
tmux new -s work      # 1. 进入会话
# 2. C-b c 再开一个窗口写代码，C-b n/p 切换
# 3. C-b d 分离，回到普通终端
tmux ls               # 4. 会话仍在后台运行
tmux attach -t work   # 5. 重新接入
```
常见错误：

- 按了 `C-b` 才发现键盘布局冲突（某些终端把 C-b 用于翻页），可在配置文件里换前缀键
- 在面板里想滚动看输出，忘了要先 `C-b [` 进入复制模式
- 以为 `C-b x` 是关窗口，实际关的是当前面板，窗口里最后一个面板被关才算窗口关闭
- 在普通终端窗口按快捷键没反应，快捷键只在 tmux 会话内生效

### 8. 断开重连与长任务

tmux 的核心价值：任务在服务器上跑，与你的网络连接无关。
```bash
# 在 tmux 会话里启动一个耗时任务
tmux new -s long-run
python3 - <<'PY'
import time
for i in range(1, 11):
    print(f"第 {i} 步完成", flush=True)
    time.sleep(5)
PY

# 任务跑着的时候：C-b d 分离，或直接关掉终端 / 断网
# 重新连上服务器后：
tmux ls
tmux attach -t long-run
```
配合日志更稳：`python3 long_job.py 2>&1 | tee -a run.log`，即使终端输出被冲掉，日志文件里也有记录。
常见错误：

- 在 tmux 之外跑长任务，以为「后台 `&`」就万事大吉；断开终端时没有 nohup 的进程会被终止，tmux 才是可靠做法
- detach 后忘了会话名，`tmux ls` 能看到全部
- 任务在 tmux 里跑完，输出滚屏找不到；用 `tee` 或重定向留档

### 9. tmux 配置与状态栏基础

把常用设置写进 `~/.tmux.conf`，然后用 `tmux source-file ~/.tmux.conf` 重新加载：
```tmuxconfig
# 允许鼠标选择面板、滚轮滚动、拖动边框
set -g mouse on

# 窗口和面板编号从 1 开始，键盘上 1 更好按
set -g base-index 1
setw -g pane-base-index 1
set -g renumber-windows on

# 增大回滚历史行数，方便翻看长输出
set -g history-limit 20000

# 状态栏：左边显示会话名，右边显示时间
set -g status-bg colour235
set -g status-fg colour250
set -g status-left "[#S] "
set -g status-right "%Y-%m-%d %H:%M"
set -g status-interval 30
```
```bash
tmux source-file ~/.tmux.conf   # 已处于 tmux 中时重新加载配置
tmux show -g | grep mouse       # 检查配置是否生效
```
常见错误：

- 改完配置不 source，也不重启 tmux，以为没生效
- 从网上整段复制配置，包含未安装插件的指令，tmux 启动报错；配置要一行一行加
- 状态栏塞太多内容反而看不清；先保持简洁，需要什么加什么

## 练习

1. 基础：确认 `~/.ssh/id_ed25519.pub` 存在（没有就生成），在 WSL2 中安装并启动 SSH 服务：
   `sudo apt install -y openssh-server`、`sudo service ssh start`，然后用
   `ssh-copy-id localhost` 把公钥装到本机，最后 `ssh localhost` 免密登录。
   提示：检查 `ls -l ~/.ssh/id_ed25519` 权限是否为 600。
   验收：`ssh localhost` 不要求输入密码即可登录，`exit` 能正常退出。

2. 配置：在 `~/.ssh/config` 里添加一个 `Host wsl` 别名指向 localhost（含 User 与 IdentityFile），
   然后用 `ssh wsl` 登录。
   提示：`HostName localhost`、`User 你的用户名`（用 `whoami` 查）。
   验收：`ssh -v wsl` 的输出中能看到 `~/.ssh/config` 被读取，登录后 `hostname` 输出一致。

3. tmux 长任务：在 tmux 会话里运行一个每 3 秒打印一行、共打印 20 行的 Python 一行式脚本，
   分离会话，关闭当前终端窗口（或断开 SSH），重新打开后 attach 回去，确认输出仍在继续。
   提示：`tmux new -s long-run`、`C-b d`、`tmux ls`、`tmux attach -t long-run`。
   验收：能指出 attach 前后的输出行数变化，任务从未被中断。

4. 分屏与传输：在 tmux 里左右分两个面板，左边运行 `python3 -m http.server 8000`，
   右边用 `curl -s localhost:8000 | head` 验证；再用 scp 把一个文件传到 `~/lab-data/processed`。
   提示：`C-b %`、`C-b 方向键`、`scp 文件 wsl:~/lab-data/processed/`。
   验收：curl 能取到 HTML，scp 后用 `ssh wsl ls ~/lab-data/processed` 能看到文件。

5. 配置：按第 9 节写一份 `~/.tmux.conf`（鼠标、编号从 1、历史 20000、状态栏显示时间），
   重新加载并验证至少三项生效。
   提示：`tmux show -g mouse`、`tmux show -g base-index`、`tmux show -g history-limit`。
   验收：新开窗口编号从 1 开始，滚轮能滚动，状态栏显示日期时间。

## 自测清单

- [ ] 我能解释 SSH 加密通道的作用，知道第一次连接为什么要点 yes
- [ ] 我能说清私钥、公钥、authorized_keys、known_hosts 各自的作用与权限要求
- [ ] 我会用 `ssh-keygen` 生成密钥、`ssh-copy-id` 分发公钥
- [ ] 我会写 `~/.ssh/config` 别名并用它登录
- [ ] 我会用 scp 双向传文件和目录，知道 sftp 的基本用法
- [ ] 我能读懂 `ssh -L 本地端口:目标主机:目标端口 主机` 的含义
- [ ] 我会创建、列出、attach、kill tmux 会话
- [ ] 我会用 C-b c/n/p/d/%/" 与方向键完成窗口与面板操作
- [ ] 我习惯把长任务放进 tmux，并会用 detach/attach 保护任务
- [ ] 我会写简单的 tmux 配置并重新加载
- [ ] 我知道 rsync 属于阶段 04 的内容，现阶段只用 scp

## 参考资料

- OpenSSH 官方站（手册与发布说明）：https://www.openssh.com/
- OpenSSH ssh 手册页：https://man7.org/linux/man-pages/man1/ssh.1.html
- OpenSSH ssh_config 手册页：https://man7.org/linux/man-pages/man5/ssh_config.5.html
- tmux 官方源码与文档：https://github.com/tmux/tmux
