# 项目：简易 Shell

## 背景与目标

你每天都在用 Shell（`bash`、`zsh`），阶段 01 还写过脚本。这个项目要求你亲手实现一个 mini shell，把「用户在命令行敲的一行字，如何变成一个正在运行的进程」完整走一遍：

- 用 `fgets` 读取命令行（替代已被淘汰的 `gets`）；
- 自己切分参数（`strtok` 或手写扫描）；
- 用 `fork + execvp + waitpid` 执行外部命令；
- 用 `open + dup2` 实现重定向 `>` `<`；
- 用 `pipe + fork` 实现管道 `|`；
- 用信号与后台运行让 shell 更接近真实使用体验。

这个项目是 CSAPP Shell Lab 的简化版；做完之后再去挑战官方 lab，你会从容很多。

## 前置知识

- 03 篇：文件描述符、`open/close/dup2`、重定向在 fd 层面的含义。
- 04 篇：`fork` / `execvp` / `waitpid` / `pipe` / 信号 / 进程组概念。
- 05 篇：gcc 选项、Makefile、gdb、ASan 与 valgrind。
- 阶段 01：`ls`、`grep`、`wc`、重定向、管道这些命令的日常用法。

## 建议用时

4~5 周，约 25~35 小时。M1~M3 约 2 周，M4~M5 约 2 周，收尾与验收约 1 周。

## 技术约束

1. 只使用 C 标准库与 POSIX 接口（`unistd.h`、`sys/wait.h`、`fcntl.h`、`signal.h` 等）。
2. **禁止**用 `system()`、`popen()`、`/bin/sh -c` 等「让别的 shell 替你执行」的取巧方式——那样这个项目就没有意义了。
3. 不使用 `gets`；读输入统一用 `fgets`（并处理行过长的情况）。
4. 每个可能失败的系统调用都要检查返回值（`fork`、`execvp`、`pipe`、`open`、`dup2` 等），失败信息走 stderr。
5. 编译必须干净：`make` 在 `-Wall -Wextra -std=c11` 下无警告。
6. 内存与进程纪律：不泄漏（valgrind `definitely lost: 0`）、不留僵尸进程（每个前台子进程都要 `waitpid`）。

## 功能清单

### MVP（必须完成）

- REPL 循环：打印提示符（建议包含当前目录），读一行，执行，回到提示符。
- 解析：按空白切分，支持多个参数（如 `ls -l /tmp`）。
- 内建命令：`help`、`exit`、`cd`（`cd` 必须改 shell 自己的目录，不能用子进程做）。
- 外部命令：`fork` + `execvp` + `waitpid`，命令不存在时打印错误且不退出。
- Ctrl+D（EOF）退出，退出码为 0。

### 进阶（至少完成两项）

- 重定向：`>`、`<`（`>>` 追加为可选加分项）。
- 管道：`|`，至少支持两级，如 `ls | grep c`。
- 后台运行：`&`，父进程不等待，且后台进程结束后要回收（不能留僵尸）。
- 信号：Ctrl+C 只终止正在运行的前台命令，不终止 shell 本身。
- 历史记录：`history` 命令列出最近 10 条非空命令。

## 里程碑

| 里程碑 | 目标 | 完成标志（可验证） |
| --- | --- | --- |
| M1 | REPL、解析、内建命令 | `./myshell` 提示符出现；`help` 输出帮助；`exit` 退出；`cd /tmp` 后提示符变成 `/tmp` |
| M2 | 执行外部命令 | `ls -l`、`/bin/echo hi` 有正确输出；输入 `nosuchcmd` 打印错误且 shell 不退出 |
| M3 | 错误处理与细节 | 空行/连续空格/首尾空格不崩溃；`execvp` 失败用 `_exit(127)`；`valgrind` 无 `definitely lost` |
| M4 | 重定向 | `echo hello > out.txt` 后 `cat out.txt` 得到 `hello`；`wc -l < out.txt` 结果正确；`>` 两侧有无空格都能解析 |
| M5 | 管道 | `ls \| grep c \| wc -l` 与系统 shell 结果一致；管道链中每个子进程都正确关闭 fd、被 `waitpid` 回收 |
| 进阶 | `&` / 信号 / `history` | 至少两项可用：后台任务不阻塞；Ctrl+C 不杀 shell；`history` 列出最近命令 |

建议顺序：M1 → M2 → M3 → M4 → M5 →（进阶）。每个里程碑完成就 Git 提交一次，提交信息写清楚「M几 + 做了什么」。

## 验收标准

- [ ] `make` 无警告、无错误；`make clean` 能清理干净。
- [ ] 启动后依次执行都能得到正确结果：
  - `ls`、`ls -l /tmp`
  - `/bin/echo hello world`
  - `cd /tmp` 后提示符变化，且 `cd` 出错时（如 `cd /no/such/dir`）打印错误不退出
  - `help`、`exit`
- [ ] `echo hello > out.txt` 后 `cat out.txt` 输出 `hello`；`wc -l < out.txt` 输出 `1`。
- [ ] `ls | grep c | wc -l` 的结果与系统 bash 执行同样命令一致。
- [ ] 输入不存在的命令与空行不会崩溃、不会退出。
- [ ] `printf 'echo hi\nexit\n' | ./myshell` 能正常执行并退出（非交互模式）。
- [ ] `valgrind --leak-check=full` 跑一遍典型命令序列，`definitely lost: 0 bytes`。
- [ ] 没有僵尸进程残留（`ps` 检查；后台任务也已被回收）。
- [ ] 至少有 5 次有意义的 Git 提交，且仓库里有本 README 的验收记录或测试命令。
- [ ] 能用 3~5 句话向别人解释：重定向和管道在文件描述符层面分别做了什么。

## 建议目录结构

`starter/` 里已经放好可编译的骨架，可以直接在它上面迭代；如果代码超过 400 行，建议拆成多个文件：

```
项目-简易Shell/
├── README.md              # 本文件
├── starter/
│   ├── shell.c            # 骨架：REPL + 解析 + 内建命令 + TODO
│   └── Makefile
└── （可选，迭代过程中新增）
    ├── shell.c            # 主循环与内建命令
    ├── parse.c            # 解析（管道、重定向可以在这里拆出来）
    ├── execute.c          # fork/exec/wait 与管道、重定向
    └── Makefile           # 增加对应的目标文件
```

## 编译与运行

```bash
# 进入 starter 目录（在 WSL2 Ubuntu 里）
cd ~/PythonLearning/03-C与计算机系统/项目-简易Shell/starter
make
./myshell
```

预期会话（M2 完成后）：

```
myshell:/home/you$ ls
shell.c  Makefile  myshell
myshell:/home/you$ echo hello world
hello world
myshell:/home/you$ nosuchcmd
myshell: nosuchcmd: No such file or directory
myshell:/home/you$ exit
```

非交互测试：

```bash
printf 'echo hi\ncd /tmp\npwd\nexit\n' | ./myshell
```

会看到提示符与命令输出交替出现（因为提示符也写进 stdout），这是正常的。

## 测试建议

1. 每完成一个里程碑，把下面的检查跑一遍（手动或写成脚本都行）：

```bash
# 重定向
printf 'echo hello > out.txt\ncat out.txt\nexit\n' | ./myshell | grep hello

# 管道
printf 'ls | grep c\nexit\n' | ./myshell > mine.txt
ls | grep c > real.txt
diff <(grep -v 'myshell:' mine.txt) real.txt
```

2. 用 valgrind 跑典型序列：

```bash
printf 'echo hi\ncd /tmp\nexit\n' | valgrind --leak-check=full ./myshell
```

3. 故意输入坏数据：空行、超长行（超过 1024 字符）、只有空格的行、`|` 开头、`>` 后面没有文件名——shell 应该报错或忽略，绝不崩溃。

4. 用 gdb 或 ASan 定位任何崩溃：`make ASAN=1`（自己在 Makefile 里加这个开关，属于 05 篇练习的延伸）。

## 常见坑

- `fork` 之后子进程要用 `_exit(127)` 而不是 `exit(127)`，避免重复刷新父进程的 stdio 缓冲；`execvp` 返回后必须退出。
- 解析结果 `argv` 指向输入缓冲区内部（`strtok` 就地修改字符串），在命令执行完成前不要把缓冲区复用/释放。
- 重定向顺序：先 `open` 目标文件拿到 fd，再 `dup2(fd, 1)`，然后 `close` 原 fd，最后 `exec`；检查每一步返回值。
- 管道：n 个进程需要 n-1 条管道；每个子进程只保留自己用到的两端，其余全部关闭，否则 `read` 等不到 EOF。
- `>` 和 `|` 两侧可能紧贴变量（`echo hi>out.txt`），初期可以要求空格，进阶再支持紧贴写法。
- Ctrl+C：如果 shell 用 `signal(SIGINT, SIG_IGN)`，这个「忽略」会被 `exec` 继承给子进程，导致子进程也杀不掉；正确做法是注册一个空处理函数（handler 只设置标志或什么都不做），子进程 `exec` 后会恢复默认行为。
- 后台 `&`：必须回收子进程（`waitpid(-1, &status, WNOHANG)` 或 `SIGCHLD`），否则僵尸堆积。
- 历史记录只存副本，不存指向输入缓冲区的指针，否则内容会被下一次输入覆盖。

## 参考资料

- man7.org 在线手册（`fork(2)`、`exec(3)`、`waitpid(2)`、`pipe(2)`、`dup2(2)`、`signal(7)`）：https://man7.org/linux/man-pages/
- GNU Bash 官方手册（对照真实 shell 的行为）：https://www.gnu.org/software/bash/manual/
- CS:APP 第 8 章「异常控制流」与 Shell Lab 说明：https://csapp.cs.cmu.edu/
