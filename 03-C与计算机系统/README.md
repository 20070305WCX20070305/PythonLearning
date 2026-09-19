# 阶段 03：C 与计算机系统

> 用 C 亲手写出「内存、指针、系统调用、进程与并发」的底层直觉，最后完成一个能执行外部命令、支持重定向与管道的简易 Shell。

## 一、阶段目标

学完本阶段，你应当能够：

1. 独立写出、编译、调试几十到几百行的 C 程序，能读懂 `-Wall -Wextra` 的警告并主动检查返回值。
2. 用指针和动态内存解释清楚：变量存在哪里、数组名为什么能当指针用、`malloc` 之后为什么必须 `free`。
3. 区分「标准库（stdio）」与「系统调用」，会用 `open/read/write/close/stat/opendir` 直接操作文件与目录。
4. 理解 `fork / exec / wait / pipe / signal`，能解释 Python 的 `subprocess`、`ProcessPoolExecutor` 在操作系统层面做了什么。
5. 会用 `pthread` 写多线程程序，理解竞争条件并用互斥锁修复。
6. 会用 gcc / make / gdb / valgrind / ASan 这套工具链，能独立定位段错误与内存泄漏。
7. 完成产出项目：[简易 Shell](项目-简易Shell/README.md)（MVP 必须完成：REPL、解析、内建命令、fork+exec、重定向、管道）。

本阶段的目的不是「精通 C 语言」，而是借助 C 看清 Python 帮你隐藏掉的东西：内存布局、缓冲区、进程、文件描述符。学完之后回到 Python 写多进程流水线，你会知道每一步背后发生了什么。

## 二、学习顺序

按顺序阅读，不要跳读；每个主题文件末尾都有练习，做完再进入下一篇。

| 序号 | 文件 | 一句话说明 | 建议用时 |
| --- | --- | --- | --- |
| 1 | [01-C语言基础](01-C语言基础.md) | 编译流程、类型、控制流、函数、数组字符串、struct、stdio、多文件编译 | 2 周 |
| 2 | [02-指针与内存](02-指针与内存.md) | 地址与指针、指针运算、传址、栈与堆、malloc/free、valgrind/ASan | 2~3 周 |
| 3 | [03-文件IO与系统调用](03-文件IO与系统调用.md) | 用户态/内核态、文件描述符、open/read/write/stat、缓冲、目录遍历、简化 wc | 2 周 |
| 4 | [04-进程线程与socket](04-进程线程与socket.md) | fork/wait/exec、pipe、信号、pthread 与互斥锁、TCP echo 服务器 | 3 周 |
| 5 | [05-gcc-make-gdb](05-gcc-make-gdb.md) | gcc 选项、多文件编译、静态/动态库、Makefile、gdb、性能与 CSAPP 选读 | 2 周 |
| 6 | [项目-简易Shell](项目-简易Shell/README.md) | 产出项目：从 REPL 到管道与重定向 | 4~5 周 |

推荐节奏：前 5 篇边学边练约 11 周，项目约 5 周，中间留缓冲；总 12~16 周，每周 6~10 小时。

## 三、需要安装的软件（在 WSL2 Ubuntu 24.04 内执行）

阶段 00 已经装好 WSL2 + Ubuntu；本阶段在 Ubuntu 里执行：

```bash
sudo apt update
sudo apt install -y build-essential gdb valgrind
```

说明：

- `build-essential` 包含 gcc、make、libc 开发头文件与 binutils（`nm`、`ldd` 等）。
- `gdb` 是调试器；`valgrind` 用来查内存错误与泄漏。
- 可选（做 socket 实验时方便测试）：`sudo apt install -y netcat-openbsd manpages-dev`。

安装后验证：

```bash
gcc --version        # 应输出 gcc (Ubuntu ...) 13.x 或更新
make --version
gdb --version
valgrind --version
```

如果某条命令提示 `command not found`，回到本文上半部分重新执行 apt 命令。

## 四、12~16 周节奏建议（每周 6~10 小时）

| 周次 | 内容 | 本周产出（可验收） |
| --- | --- | --- |
| 第 1 周 | 安装工具链；01 前半：编译流程、类型与 sizeof、运算符、控制流 | hello、类型表、素数/乘法表小程序 |
| 第 2 周 | 01 后半：函数、数组与字符串、struct/enum、printf/scanf、多文件编译 | 温度转换、粒子结构体排序、多文件编译通过 |
| 第 3 周 | 02 前半：地址与指针、指针与数组、指针运算、传址、const | 指针版 swap、find_min、指针遍历字符串 |
| 第 4 周 | 02 后半：栈与堆、malloc/calloc/realloc/free、常见内存错误 | my_strdup、动态数组 |
| 第 5 周 | 02 收尾：valgrind 与 `-fsanitize=address` 修 bug | 用 ASan 定位越界/泄漏并修复 |
| 第 6 周 | 03 前半：系统调用、fd、open/read/write/close、errno | mycat、简化 cp |
| 第 7 周 | 03 后半：stat、stdio 缓冲、目录遍历 | 目录统计器、简化 wc |
| 第 8 周 | 04 前半：fork、wait/waitpid、exec 家族 | 多子进程实验、fork+exec 执行 ls |
| 第 9 周 | 04 中段：pipe、信号基础 | 父子管道通信、Ctrl+C 处理 |
| 第 10 周 | 04 中段：pthread 与互斥锁 | 竞争条件复现 + 加锁修复 |
| 第 11 周 | 04 后半：socket 基础 | echo 服务器 + 客户端 |
| 第 12 周 | 05 前半：gcc 选项、多文件、静态/动态库 | 库打包实验 |
| 第 13 周 | 05 后半：Makefile、gdb | Makefile 构建 + gdb 定位段错误 |
| 第 14 周 | 项目 M1~M3：REPL、内建命令、fork+exec | 能运行 `ls -l`、`cd`、`exit` |
| 第 15 周 | 项目 M4~M5：重定向、管道 | `ls \| grep c \| wc -l` 正确 |
| 第 16 周 | 项目收尾（进阶项）、复盘、可选 CSAPP lab | 验收 checklist 全部勾选 |

进度落后时优先保项目 M1~M5，把 04 的 socket 与 05 的库演示减到「跑通理解」即可；不要压缩 02（指针与内存是本阶段的核心）。

## 五、验收标准

阶段完成时，逐项确认：

- [ ] `gcc / make / gdb / valgrind` 全部可用，版本命令有输出。
- [ ] 01~05 每篇的自测清单至少 90% 能勾选，练习完成 4/5 以上。
- [ ] 能口头解释：栈与堆的区别、指针与数组的关系、为什么 `free` 之后指针要置 `NULL`。
- [ ] 能不看资料写出：遍历目录统计文件数的程序、fork+exec+wait 执行外部命令的程序。
- [ ] 用 `valgrind --leak-check=full` 检查过自己写的动态内存程序，无 `definitely lost`。
- [ ] 用 gdb 独立定位过至少一个段错误（能给出 `backtrace` 与出错行）。
- [ ] 项目 `myshell` 的 M1~M5 全部完成，`make` 在 `-Wall -Wextra` 下无警告。
- [ ] `printf 'echo hi\nexit\n' | ./myshell` 能正确回显；`ls | grep c | wc -l` 与系统 shell 结果一致。
- [ ] 项目与练习都用 Git 提交（延续阶段 01 的习惯），提交信息能说明改了什么。
- [ ] 写一段 200 字左右的复盘：C 与 Python 在你眼里的最大三个差异。

## 六、与 Python 的对照学习建议

学习 C 时，每遇到一个特性就回想 Python 的写法，把差异写在笔记里。下面是最值得对照的几组：

| 任务 | Python 写法 | C 写法 | 差异要点 |
| --- | --- | --- | --- |
| 变量 | `x = 42`，类型动态 | `int x = 42;`，类型固定 | C 的类型决定字节数与溢出行为 |
| 字符串 | 不可变对象，自动管理 | `char` 数组 + `'\0'` | 要自己保证长度、防止越界 |
| 列表 | `list` 自动扩容 | `malloc` + `realloc` 手动扩容 | 忘记 `free` 就泄漏；忘记检查返回值就崩溃 |
| 字典 | `dict` | 无内建，需自己用数组/哈希实现 | C 的标准库非常小 |
| 文件 | `open()` + `with` | `open()` 返回 fd 或 `FILE *` | 句柄要手动关闭，缓冲要自己理解 |
| 错误 | 异常 | 返回 -1 + `errno` | 每个可能失败的调用都要检查 |
| 并发 | `ProcessPoolExecutor` | `fork` / `pthread` | 进程/线程代价与共享内存要自己管理 |
| 构建 | 解释执行，无需构建 | 编译 + 链接 | Makefile 描述构建规则 |
| 调试 | `print` / `pdb` | gdb / valgrind / ASan | 能看到内存与调用栈 |

建议用「同一任务两语言各写一遍」的方式加深理解，推荐三个任务：

1. 字数统计：Python 的 `len(open(f).read().split())` 对比 C 的 read 循环计数（03 正文里有完整示例）。
2. 批量文件处理：Python 用 `pathlib` 遍历目录，C 用 `opendir/readdir` 遍历，比较代码量。
3. 并发执行命令：Python 用 `subprocess.run`，C 用 `fork+execvp+waitpid`，比较进程视角的差别。

写 C 代码时保持三个习惯：编译永远加 `-Wall -Wextra`；所有可能失败的调用都检查返回值；动态内存的程序在提交前跑一次 valgrind 或 ASan。

## 七、目录结构

```
03-C与计算机系统/
├── README.md              # 本文件
├── 01-C语言基础.md
├── 02-指针与内存.md
├── 03-文件IO与系统调用.md
├── 04-进程线程与socket.md
├── 05-gcc-make-gdb.md
└── 项目-简易Shell/
    ├── README.md          # 项目说明与验收标准
    └── starter/
        ├── shell.c        # 可编译骨架（含 TODO）
        └── Makefile
```

## 八、常见问题（FAQ）

- `gcc: command not found`：说明还没装 build-essential，或没有在 WSL2 的 Ubuntu 终端里执行；回到第三节。
- `apt install` 很慢或失败：先 `sudo apt update`；网络问题可参考阶段 00 的镜像设置。
- 编译输出一大片错误：先看**第一条** error，后面的往往是它的连锁反应。
- 段错误但没有行号：编译加 `-g`，调试用 `-O0`，再用 gdb 的 `backtrace` 定位。
- 中文注释导致编译错：源文件保存为 UTF-8（不要存成 GBK）；报 `stray '\'` 通常是混入了全角符号。
- `undefined reference`：先确认所有 `.c` 文件都参与了编译/链接，再检查函数名拼写与声明。
- 练习卡住多久算正常：先查 `man` 与本文示例，超过 40 分钟就把「命令、报错、已尝试的做法」写清楚再求助。

## 九、边界说明

本阶段只使用阶段 00~02 已建立的知识（Linux 命令行、Git、Python 基础与多进程概念）。C 的 `struct` 只当作「打包数据」来用，本阶段不引入「用函数指针模拟对象」的写法；其他进阶特性留到之后按需再学。
