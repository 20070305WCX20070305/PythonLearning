# 01-Linux基础

## 学习目标

- 理解 Linux 文件系统是一棵以 `/` 为根的树，分清绝对路径与相对路径
- 熟练使用导航与查看命令：`pwd ls cd cat less head tail`
- 会做文件操作：`cp mv rm mkdir touch ln`
- 理解 rwx 权限模型，会用 `chmod`，理解 `chown` 与 `sudo`
- 会用 `find`、`grep` 与通配符查找文件与内容
- 会用管道 `|` 与重定向 `> >> 2> <` 组合命令
- 会用 `wc sort uniq cut tr`，看懂最基础的一行 `awk`/`sed`
- 会用 `apt` 安装软件，理解环境变量与 PATH
- 会查看进程并用 `kill` 终止，会用 `tar`/`gzip` 打包解包

## 前置知识

- 阶段 00 已完成：WSL2 + Ubuntu 24.04，已安装 `build-essential git curl wget tmux htop unzip`
- 会在 Windows Terminal 中打开 WSL2 的 Ubuntu 终端
- 知道「文件」「目录」「路径」的基本概念，有使用图形文件管理器的经验即可

## 建议用时

8~12 小时，建议分 3~4 次完成，每次 2~3 小时。所有命令都要亲手敲一遍。

## 正文

### 1. 文件系统与路径

Linux 把一切组织在一棵以 `/` 为根的树里。几个科研中会碰到的目录：

| 路径 | 作用 |
| --- | --- |
| `/` | 根目录，所有路径的起点 |
| `/home/你的用户名` | 你的家目录，写作 `~` |
| `/tmp` | 临时文件，重启可能被清空 |
| `/etc` | 系统与软件配置 |
| `/var/log` | 系统日志 |
| `/opt` | 额外安装的软件 |

路径分两种：以 `/` 开头的是绝对路径，例如 `/home/you/lab-data`；否则是相对路径，
相对于当前目录解析。`.` 表示当前目录，`..` 表示上级目录，`-` 表示上一次所在目录。

```bash
# 创建本节使用的练习目录结构，不输出任何内容说明成功
mkdir -p ~/lab-data/{raw,processed,logs}

cd ~/lab-data
pwd              # 输出: /home/you/lab-data
cd raw           # 相对路径：进入 lab-data 下的 raw
pwd              # 输出: /home/you/lab-data/raw
cd ..            # 返回上级
cd -             # 回到 raw，输出: /home/you/lab-data/raw
cd ~             # 回家目录
```

常见错误：

- 把 Windows 的 `\` 当分隔符写进路径，Linux 只认 `/`
- 路径含空格不加引号，例如 `cd my data` 会被当成两个参数，应写 `cd "my data"`
- 在不确定的目录里执行删除，先 `pwd` 确认位置

### 2. 导航与查看文件

```bash
ls                  # 列出当前目录
ls -lh ~/lab-data   # -l 详细信息，-h 人类可读大小
ls -lt              # 按修改时间排序，最新在前
ls -a               # 显示以 . 开头的隐藏文件

cat  ~/lab-data/README.txt      # 适合小文件
less ~/lab-data/logs/run.log    # 适合大文件：q 退出，/关键词 搜索，G 到末尾，g 到开头
head -n 5  data.csv             # 前 5 行
tail -n 20 data.csv             # 后 20 行
tail -f logs/run.log            # 持续输出新行，Ctrl+C 退出，常用来盯日志
file  data.csv                  # 看文件真实类型
stat  data.csv                  # 看大小、权限、修改时间
```

常见错误：

- 用 `cat` 打开几百 MB 的日志，终端刷屏，应该用 `less` 或 `head`
- 在 `less` 里忘了按 `q` 退出
- 想找文件却用 `ls` 猜路径，应该用下一小节的 `find`

### 3. 文件操作

```bash
mkdir -p processed/2026-03-15      # -p 自动创建多层目录
touch  raw/scan_001.txt            # 创建空文件

cp raw/scan_001.txt processed/                  # 复制文件
cp -r raw processed/backup_raw                  # 复制目录必须加 -r
cp -i raw/scan_001.txt processed/               # 覆盖前询问

mv raw/scan_001.txt raw/scan_001_v2.txt         # 重命名
mv raw/scan_002.txt processed/                  # 移动
rm processed/scan_002.txt                       # 删除文件，没有回收站
rm -r processed/backup_raw                      # 删除目录要加 -r

ln -s ~/lab-data/raw/scan_001.txt latest.txt    # 创建符号链接（快捷方式）
ls -l latest.txt                                # 输出中有 -> 指向目标
```

常见错误：

- 忘记 `rm` 没有回收站，删了就没了；拿不准时先 `ls` 同通配符确认会匹配到什么
- `rm -rf $dir/*` 里变量为空时变成 `rm -rf /*` 级别的灾难，脚本里要加引号并检查变量
- `cp` 目录不加 `-r`，报 `omitting directory`
- 符号链接指向的路径被删后变成「断链」，`ls -l` 里显示红色

### 4. 权限：rwx、chmod、chown、sudo

`ls -l` 的第一列形如 `-rw-r--r--`，9 个字符分三组，依次是文件属主、属组、其他人的权限：

- `r` 读（4）、`w` 写（2）、`x` 执行（1）；对目录而言 `x` 表示可以进入
- `-` 表示没有该权限

```bash
chmod +x backup.sh          # 所有身份加执行权限，脚本才能 ./backup.sh 运行
chmod 644 data.csv          # 属主可读写，其他人只读（文件常用）
chmod 755 scripts           # 目录常用：属主全权，其他人可读可进入
chmod 600 ~/.ssh/id_ed25519 # 私钥只能自己读写，OpenSSH 会检查这一点
chown -R you:you processed  # 修改属主与属组，通常需要管理员权限
sudo apt update             # sudo：以管理员身份执行这一条命令
```

常见错误：

- 遇事不决 `chmod 777`：这等于对所有人开放写权限，是安全隐患，要按最小权限原则给
- `sudo` 运行的程序创建的文件属主是 root，之后普通用户可能改不动
- 目录缺少 `x` 权限时，`cd` 和访问内部文件都会失败
- 私钥权限过宽（如 644），`ssh` 会直接拒绝使用它

### 5. 查找与过滤：find 与 grep

```bash
# 查找：find 从目录出发按条件找文件
find ~/lab-data -name "*.csv"              # 按文件名模式
find ~/lab-data -type f -size +100M        # 大于 100 MB 的普通文件
find ~/lab-data -type f -mtime -7          # 最近 7 天修改过的文件
find ~/lab-data -maxdepth 2 -name "*.log"  # 最多下探两层

# 过滤：grep 在文件内容里找
grep "温度" raw/scan_001.txt               # 找包含"温度"的行
grep -rn "ERROR" logs/                     # -r 递归，-n 显示行号
grep -i "error" logs/run.log               # 忽略大小写
grep -v "^#" data.csv                      # 反向选择：输出不以 # 开头的行
grep -l "温度" raw/*.txt                   # 只列出匹配的文件名
```

通配符由 Shell 展开：`*` 任意多个字符，`?` 恰好一个字符，`[0-9]` 一个数字。

```bash
ls raw/scan_*.txt        # scan_001.txt scan_002.txt ...
ls raw/run?.csv          # run1.csv run2.csv，不匹配 run10.csv
ls raw/data_2026-0[12]*  # 2026 年 1、2 月
```

常见错误：

- `find -name` 的模式一定要加引号，否则会被 Shell 提前展开
- 只写 `grep "温度"` 不指定文件或 `-r`，grep 会等待标准输入，看起来像卡住
- 通配符没有匹配项时，bash 默认把模式原样传给命令（配合 `nullglob` 后的行为要小心）
- 用 `grep` 搜二进制文件会输出乱码，加 `-I` 跳过二进制文件

### 6. 管道与重定向

```bash
grep "ERROR" logs/run.log | wc -l        # 管道：上一条命令的输出成为下一条的输入
sort data.csv > sorted.csv               # > 覆盖写入文件
echo "整理完成" >> logs/run.log           # >> 追加到文件末尾
python3 analyze.py < data.csv            # < 把文件内容作为标准输入
python3 organizer.py > out.log 2> err.log  # 标准输出与标准错误分别写入两个文件
python3 organizer.py > all.log 2>&1      # 标准错误合并进标准输出
grep "ERROR" logs/run.log | tee errors.txt   # 同时显示在屏幕并写入文件
```

常见错误：

- `>` 会直接覆盖原文件内容，想追加必须用 `>>`
- `2>&1` 顺序很重要，写在 `> all.log` 之后才是「错误跟随输出」；顺序反了会写错地方
- 管道中前面的命令失败不会自动停止后面的命令（下节课用 `set -o pipefail` 解决）

### 7. 文本处理入门

```bash
wc -l data.csv                 # 行数；-c 字节数，-w 单词数
sort -n values.txt             # 按数值排序（默认按字典序）
sort -k2 -n data.csv           # 按第 2 列数值排序
sort values.txt | uniq -c      # 去重并计数：必须先 sort 再 uniq
cut -d, -f1,3 data.csv         # 以逗号分隔，取第 1、3 列
tr ',' '\t' < data.csv         # 把逗号替换成制表符
tr -d '\r' < data.csv > clean.csv  # 删除 Windows 换行残留的 \r

# awk 一行式：按列计算，列号从 1 开始，$0 是整行
awk -F, 'NR>1 {sum+=$2; n+=1} END {printf "平均: %.3f\n", sum/n}' data.csv

# sed 一行式：替换与取行
sed 's/old/new/g' file.txt            # 全局替换，输出到屏幕
sed -n '1,5p' file.txt                # 只打印前 5 行
```

awk 与 sed 都是独立的小语言，本阶段「够用即可」，会读会改简单一行式就行，
阶段 04/05 再深入。

常见错误：

- `uniq` 只合并相邻重复行，不先 `sort` 的结果几乎总是错的
- `cut -d` 只能处理单个字符分隔符，多个空格分隔时用 awk 更可靠
- 修改文件时直接 `sed -i` 又没备份，改错了难以恢复；重要文件先 `cp` 一份

### 8. 软件包管理：apt

```bash
sudo apt update                  # 刷新软件索引，安装前先做
apt search htop                  # 搜索包
apt show htop                    # 查看包信息
sudo apt install -y tree         # 安装（-y 自动确认）
sudo apt remove tree             # 卸载
apt list --installed | grep gcc  # 查看已安装
```

常见错误：

- 刚装完系统不 `apt update` 就安装，可能提示找不到包
- 忘记 `sudo`，install/remove 都会失败
- 用 apt 安装 Python 第三方库（如 `python3-pytest`）而不是用 venv + pip，版本容易混乱；Python 依赖统一交给 pip

### 9. 环境变量与 PATH

环境变量是 Shell 传给程序的一组键值对：

```bash
echo "$HOME"        # /home/you
echo "$USER"        # you
echo "$PATH"        # 用冒号分隔的目录列表
which python3       # 查看 python3 实际来自哪个目录
export LAB_DATA=~/lab-data       # 定义变量并导出给子进程，仅当前终端有效
echo "$LAB_DATA"
ls "$LAB_DATA/raw"

# 让自定义脚本目录长期可用：追加到 ~/.bashrc
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc                 # 让修改立即生效
```

常见错误：

- 写 `PATH=/new/dir` 覆盖整个 PATH，导致系统命令找不到；永远要 `PATH="/new/dir:$PATH"` 追加
- 单引号里的 `$HOME` 不会展开，需要展开时用双引号
- 改完 `~/.bashrc` 忘记 `source`，新开的终端才生效，当前终端没有变化

### 10. 进程查看与终止

```bash
ps aux | grep python            # 查看所有进程并过滤
htop                            # 交互式进程管理器，F9 发送信号，q 退出
kill 12345                      # 向 PID 12345 发送 TERM 信号，让它自行退出
kill -9 12345                   # 强制杀死（最后手段）
Ctrl+C                          # 终止当前前台任务
```

常见错误：

- `kill` 错 PID，先核对 `ps` 输出里的命令行再动手
- 一上来就 `kill -9`，程序没机会保存和清理；先普通 `kill`
- 在 SSH 会话里直接跑几小时的任务，网络一断任务就没了（第 04 课用 tmux 解决）

### 11. 打包与压缩：tar 与 gzip

```bash
tar -czvf raw-2026-03.tar.gz -C ~/lab-data raw   # 创建 gzip 压缩包
tar -tzf  raw-2026-03.tar.gz                     # 只列出内容，不解压
tar -xzvf raw-2026-03.tar.gz -C ~/lab-data/backup # 解压到指定目录
gzip data.csv                 # 压缩成 data.csv.gz，删除原文件
gunzip data.csv.gz            # 解压
du -sh ~/lab-data             # 目录总大小
df -h                         # 磁盘剩余空间
```

参数记忆：`-c` 创建、`-x` 解包、`-t` 列出、`-z` gzip、`-v` 显示过程、`-f` 指定文件名（必须紧跟压缩包名）。

常见错误：

- 打包时用了绝对路径，解包会还原出整条路径；用 `-C` 进入目标目录再打包
- `-f` 后面必须是压缩包名，其他参数顺序写错会报错
- 磁盘满了还继续产生数据，先用 `df -h` 和 `du -sh` 检查

## 练习

1. 基础：在 `~/lab-data` 下创建 `processed/2026-03-15`，在其中生成 3 个文件（内容自定），
   再用一条 `tar` 命令把 `processed` 打包为 `processed.tar.gz`。
   提示：`mkdir -p`、`echo ... >`、`tar -czvf`。
   验收：`tar -tzf processed.tar.gz` 列出 3 个文件且路径以 `processed/` 开头。

2. 查找：在 `~/lab-data` 中找出最近 7 天内修改过的 `.csv` 文件并计数。
   提示：`find ... -mtime -7 -name "*.csv" | wc -l`。
   验收：屏幕上只输出一个数字，且与你手动确认的数量一致。

3. 管道：模拟一个 CSV 文件（两列：样品名,测量值），用管道组合统计测量值总行数，
   并用 awk 输出测量值的平均值。
   提示：`awk -F, 'NR>1 {sum+=$2; n+=1} END {print sum/n}' data.csv`。
   验收：输出结果是合理范围内的一个数字，并能解释 `NR>1` 的作用。

4. 权限：编写 `hello.sh`（内容为一行 `echo 你好, Linux`），赋予执行权限后运行；
   再改成 `600` 观察运行结果有什么变化，最后改回 `755`。
   提示：`chmod +x`、`./hello.sh`、`ls -l`。
   验收：能说明为什么 600 时不能直接 `./hello.sh`。

5. 综合：把 `~/lab-data` 中所有 `.log` 文件里包含 `ERROR` 的行汇总到一个文件，
   同时统计出现次数最多的前 5 条错误信息。
   提示：`grep -r`、`sort`、`uniq -c`、`sort -nr | head -n 5`。
   验收：命令用管道串联、不使用临时中间文件，输出形如「次数 错误信息」的 5 行。

## 自测清单

- [ ] 我能解释 `/`、`~`、`.`、`..` 的含义，并能区分绝对路径与相对路径
- [ ] 我能在不看笔记的情况下用 `find` + `-name`/`-mtime`/`-size` 找到目标文件
- [ ] 我能读懂 `ls -l` 输出并说明权限位含义，会用 chmod 修改权限
- [ ] 我能用管道与重定向把 `grep`、`sort`、`uniq`、`wc` 串成一条统计命令
- [ ] 我能用 `cut` 或 `awk` 从 CSV 中提取指定列并计算简单统计量
- [ ] 我知道 `>` 与 `>>` 的区别，会用 `2>&1` 合并标准错误
- [ ] 我会用 `apt update` 和 `apt install` 安装软件
- [ ] 我理解 PATH 的作用，知道怎样安全地追加自定义目录
- [ ] 我会用 `ps aux`/`htop` 找到进程并用 `kill` 安全终止
- [ ] 我会用 `tar -czvf/-xzvf/-tzf` 完成打包、解包与查看
- [ ] 我知道 rm 没有回收站，删除前会用通配符先确认匹配范围

## 参考资料

- Linux man-pages 官方手册：https://man7.org/linux/man-pages/
- GNU Coreutils 手册（ls/cp/mv/rm/sort/uniq/cut/wc 等）：https://www.gnu.org/software/coreutils/manual/coreutils.html
- GNU Bash 手册（重定向、通配符、变量展开）：https://www.gnu.org/software/bash/manual/bash.html
- GNU Findutils 手册（find）：https://www.gnu.org/software/findutils/manual/find.html
