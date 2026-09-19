# 05 - gcc、make 与 gdb

## 学习目标

- 掌握 gcc 常用选项，能读懂并消除 `-Wall -Wextra` 的警告。
- 理解多文件编译与链接的过程，知道 `undefined reference` 从哪来。
- 会打包和使用静态库（`.a`）与动态库（`.so`）。
- 会写 Makefile：目标、依赖、命令、变量、模式规则、`.PHONY` 与增量构建。
- 会用 gdb 的基本命令定位段错误：`break / run / next / step / print / backtrace / frame / watch`。
- 知道 ASan 与 valgrind 各自适合什么场景。
- 了解 CSAPP 需要选读哪些章节、做哪些 lab。

## 前置知识

- 01~04 篇：会写多文件 C 程序，遇见过段错误与警告。
- 阶段 01：Shell 命令与文件组织、`man`。

## 建议用时

2 周，约 14~18 小时。

## 正文

### 5.1 gcc 常用选项

```c
/* warn_demo.c —— 故意写出几个典型问题 */
#include <stdio.h>
int main(void)
{
    int unused = 42;                 /* 未使用变量 */
    unsigned int u = 1;
    int s = -1;
    printf("hello %d\n", "world");   /* 格式串与参数类型不匹配 */
    if (u > s)                       /* 有符号与无符号比较 */
        printf("u > s\n");
    return 0;
}
```

编译 `gcc -Wall -Wextra -std=c11 warn_demo.c -o warn_demo`，会看到 `unused variable`、`format '%d' expects argument of type 'int'`、`comparison of integer expressions of different signedness` 三条警告（不同 gcc 版本措辞略有差异）。

常用选项速查：

| 选项 | 作用 |
| --- | --- |
| `-Wall -Wextra` | 打开绝大多数警告；学习期必加 |
| `-Werror` | 把警告当错误（强制自己清零，选加） |
| `-std=c11` / `-std=c17` | 选择语言标准，避免用到编译器方言 |
| `-g` | 生成调试信息，gdb / valgrind 要靠它给行号 |
| `-O0` / `-O2` / `-O3` | 优化等级；调试用 `-O0`，发布用 `-O2` |
| `-o file` | 指定输出文件名 |
| `-c` | 只编译成 `.o`，不链接 |
| `-I dir` | 增加头文件搜索目录 |
| `-L dir` / `-lname` | 增加库搜索目录 / 链接 `libname` |
| `-DNAME=值` | 定义预处理宏 |
| `-fsanitize=address,undefined` | 打开 ASan 与 UB 检查 |
| `-pthread` | 编译与链接线程程序（编译和链接都要加） |

常见错误：

- 只写 `-pthread` 在链接命令而编译命令忘了加：宏定义不一致，可能出现奇怪问题。
- 用 `-O2` 配上 gdb 调试：变量被优化掉，`print x` 显示 `<optimized out>`。
- 忽略警告：`-Wall -Wextra` 报的「有符号/无符号比较」「格式串不匹配」往往是真实 bug。

### 5.2 多文件编译与链接

回顾 01 的 `math_utils` 例子，分步编译：

```bash
gcc -Wall -Wextra -std=c11 -g -c math_utils.c -o math_utils.o
gcc -Wall -Wextra -std=c11 -g -c main.c -o main.o
gcc main.o math_utils.o -o app
./app        # add(2, 3) = 5 与 square(12) = 144
```

链接器的工作是「把每个 `.o` 里未定义的符号，用其他 `.o` 或库里的定义补上」。用 `nm main.o | grep -E ' U | T '` 查看符号（`U` 未定义、`T` 已定义），典型输出：

```
                 U add
                 U printf
0000000000000000 T main
```

`main.o` 用到 `add`（定义在 `math_utils.o`）和 `printf`（定义在 libc）。链接命令里少了 `math_utils.o` 就会 `undefined reference to 'add'`。

常见错误：

- `undefined reference`：某个符号只有声明没有定义，或链接时漏了对应的 `.o` / 库。
- 头文件路径找不到：`fatal error: math_utils.h: No such file or directory`；用 `-I` 指定目录。
- 同一函数在两个 `.c` 里都定义了：`multiple definition`；定义只留一处，其余用声明。

### 5.3 静态库与动态库

把 `math_utils.c` 打包成库，给别人用时只需 `.h` + 库文件。

静态库（`.a`，链接时被复制进可执行文件）：

```bash
gcc -Wall -Wextra -std=c11 -c math_utils.c -o math_utils.o
ar rcs libmathutils.a math_utils.o
gcc -Wall -Wextra -std=c11 main.c -L. -lmathutils -o app_static
./app_static
```

`ar rcs` 的三个参数：`r` 插入/替换成员，`c` 库不存在就创建，`s` 建立索引。

动态库（`.so`，运行时才加载）：

```bash
gcc -Wall -Wextra -std=c11 -fPIC -shared math_utils.c -o libmathutils.so
gcc -Wall -Wextra -std=c11 main.c -L. -lmathutils -o app_shared
LD_LIBRARY_PATH=. ./app_shared
```

两点差别：编译动态库必须加 `-fPIC`（位置无关代码）；运行时要让系统找得到 `.so`，临时办法是 `LD_LIBRARY_PATH=.`，永久办法是装到系统目录或编译时加 `-Wl,-rpath,/绝对路径`。验证：

```bash
ldd app_shared | grep mathutils     # 显示 libmathutils.so => ...
ldd app_static | grep mathutils     # 无输出，已打包进可执行文件
```

常见错误：

- 链接库时 `-lname` 写在源文件前面：链接器按顺序处理，`-lmathutils` 应在用到它的目标文件之后。
- 动态库忘了 `-fPIC`：链接时报 `relocation ... can not be used when making a shared object`。
- 运行时 `error while loading shared libraries: libxxx.so`：`LD_LIBRARY_PATH` 或 `-Wl,-rpath` 没设置。

### 5.4 Makefile 入门

Makefile 由「规则」组成：目标、依赖、命令。**命令行前必须是 Tab，不能是空格**。

```makefile
# 变量：改了这里，用到的地方都跟着变
CC      = gcc
CFLAGS  = -Wall -Wextra -g -std=c11
TARGET  = app
OBJS    = main.o math_utils.o

all: $(TARGET)                       # 默认目标

$(TARGET): $(OBJS)                   # $@ = 目标名；$^ = 所有依赖
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c                             # 模式规则：$< = 第一个依赖
	$(CC) $(CFLAGS) -c $< -o $@

main.o math_utils.o: math_utils.h    # 头文件变了也要重编

clean:                               # 伪目标：不对应真实文件
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean
```

使用与输出：

```bash
make            # gcc ... -c main.c -o main.o; gcc ... -c math_utils.c -o math_utils.o; gcc ... -o app main.o math_utils.o
./app
make clean      # 清理
```

**增量构建**：make 比较目标与依赖的时间戳，只重编过期的文件。`make` 第二次会输出 `make: 'app' is up to date.`；`touch math_utils.h` 后再 `make`，两个 `.o` 都会重新编译（头文件依赖生效）。常用自动变量：`$@` 目标名、`$^` 全部依赖、`$<` 第一个依赖。变量赋值 `=` 与 `:=` 有细微区别（递归展开 vs 立即展开），初学用哪个都行。

常见错误：

- 命令行前面是空格而不是 Tab：`Makefile:12: *** missing separator. Stop.`
- `clean` 没写 `.PHONY`，而恰好存在一个叫 `clean` 的文件：命令不执行。
- 命令里用 shell 变量 `$VAR` 却写成 `$(VAR)` 被 make 展开：shell 变量要写 `$$VAR`。
- 改了 `.h` 却忘记把 `.h` 写进依赖：make 不重编，运行旧代码——很多「灵异现象」的来源。

### 5.5 gdb 常用命令

调试版程序 `segv.c`：

```c
#include <stdio.h>
static int sum_to(int n)
{
    int *p = NULL;
    int s = 0;
    for (int i = 1; i <= n; i++)
        s += i;
    *p = s;          /* 向空指针写入，必然段错误 */
    return s;
}
int main(void)
{
    printf("%d\n", sum_to(10));
    return 0;
}
```

编译并进入 gdb：`gcc -Wall -Wextra -std=c11 -g -O0 segv.c -o segv`，然后 `gdb ./segv`。一次典型会话：

```
(gdb) break sum_to            # 在函数入口下断点
Breakpoint 1 at 0x1139: file segv.c, line 4.
(gdb) run
Breakpoint 1, sum_to (n=10) at segv.c:4
4           int *p = NULL;
(gdb) next
5           int s = 0;
(gdb) print n                 # 打印变量
$1 = 10
(gdb) continue
Program received signal SIGSEGV, Segmentation fault.
sum_to (n=10) at segv.c:8
8           *p = s;
(gdb) print p
$2 = (int *) 0x0              # 空指针，原因一目了然
(gdb) backtrace               # 调用栈
#0  sum_to (n=10) at segv.c:8
#1  0x000055555555517b in main () at segv.c:13
(gdb) frame 1                 # 切到 main 这一帧
#1  0x000055555555517b in main () at segv.c:13
13          printf("%d\n", sum_to(10));
(gdb) quit
```

常用命令表：

| 命令 | 缩写 | 作用 |
| --- | --- | --- |
| `break 位置` | `b` | 下断点：函数名、`file.c:行号` |
| `run [参数]` | `r` | 启动程序，可带命令行参数 |
| `next` / `step` | `n` / `s` | 执行下一行（不进入 / 进入函数） |
| `continue` | `c` | 运行到下一个断点/信号 |
| `print 表达式` | `p` | 打印变量、解引用、`p arr[0]@5` |
| `ptype` / `info locals` | | 显示类型定义 / 当前所有局部变量 |
| `backtrace` | `bt` | 打印调用栈 |
| `frame N` | `f` | 切换到第 N 层栈帧 |
| `watch 表达式` | | 表达式变化时停下（适合抓「谁改了它」） |
| `list` / `quit` | `l` / `q` | 显示源码 / 退出 |

修好 `segv.c`（删掉 `*p = s;` 一行）后，程序应输出 `55`。

常见错误：

- 编译没加 `-g`：gdb 里看不到源码行号。
- 用了 `-O2` 调试：变量被优化掉，行为对不上源码；先 `-O0` 确认。
- 段错误发生在库函数里（`bt` 顶帧是 libc）：用 `frame` 往下翻，找到你自己的代码。

### 5.6 ASan 与 valgrind 的使用时机

| 对比项 | AddressSanitizer | valgrind |
| --- | --- | --- |
| 使用方式 | 编译时加 `-fsanitize=address,undefined` | 直接 `valgrind ./程序` |
| 运行速度 | 约 2 倍开销 | 慢 10~50 倍 |
| 能否查栈越界 | 能 | 不能（主要管堆） |
| 能否查内存泄漏 | 能（程序退出时） | 能，报告更细 |
| 需要重编译 | 需要 | 不需要 |
| 适用 | 日常开发、调试 | 交付前验收、没源码时 |

推荐流程：开发中一直用 ASan 版本（`make debug`），提交/交付前再用 valgrind 跑一遍验收命令。两者不要同时开启。

常见错误：

- ASan 报错后直接忽略：它的每条 `ERROR` 都是真实 bug，按行号修。
- valgrind 报告的 `still reachable` 当成泄漏：真正要清零的是 `definitely lost` 与 `indirectly lost`。
- 用 ASan 版本测性能：结果没有参考价值。

### 5.7 从 -O0 到 -O2：性能意识

```c
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char *argv[])
{
    long long n = (argc > 1) ? atoll(argv[1]) : 200000000LL;
    volatile unsigned long long sum = 0;   /* volatile 保证循环真的执行 */
    for (long long i = 0; i < n; i++)
        sum += (unsigned long long)i;
    printf("sum = %llu\n", (unsigned long long)sum);
    return 0;
}
```

对比：

```bash
gcc -std=c11 -O0 bench.c -o bench_O0
gcc -std=c11 -O2 bench.c -o bench_O2
time ./bench_O0 200000000   # 再对 bench_O2 做同样的计时
```

两者输出相同（`sum = 19999999900000000`），`-O2` 明显更快。阶段 01 学过的 `time` 命令在这里正式派上用场，之后写 Python 批处理时也应保持「先测量，再优化」的习惯。

常见错误：

- 用 `time` 量一个只运行几毫秒的程序：误差太大；让程序跑到几百毫秒以上再比较。
- 被优化掉的代码测不出差别：把结果打印出来，或用 `volatile`（如示例）。
- 只看优化等级不看算法：先改进算法与 IO，再谈 `-O2`。

### 5.8 CSAPP 选读与 lab 建议

《深入理解计算机系统》（CS:APP 3e）不需要通读，按下面的顺序选读：

| 章节 | 主题 | 与哪篇对应 |
| --- | --- | --- |
| 第 1 章 | 计算机系统漫游（编译流程、存储层次） | 01 |
| 第 3 章 | 程序的机器级表示（汇编、栈帧、指针） | 01、02 |
| 第 8 章 | 异常控制流（进程、fork、信号） | 04 |
| 第 9 章 | 虚拟内存（栈/堆、malloc 实现） | 02 |
| 第 10 章 | 系统级 I/O（fd、缓冲、重定向） | 03 |
| 第 11 章 | 网络编程（socket） | 04 |
| 第 12 章 | 并发编程（线程、锁、竞争） | 04 |

官方 lab 建议（做完本阶段后选 2~3 个）：Data Lab（位运算）、Bomb Lab（汇编 + gdb）、Malloc Lab（实现 malloc）、Shell Lab（本项目的完整版）、Proxy Lab（网络）。课程主页：https://csapp.cs.cmu.edu/

常见错误：

- 一上来啃完第 3 章汇编却不动手：配合 Bomb Lab 边玩边学。
- 直接做 Shell Lab 再做本项目：先把自己的简化版写完，再看 Shell Lab 的框架。
- 只看书不写代码：每章至少配一个可运行的小程序。

### 5.9 与 Python 的对照

| 主题 | Python | C 工具链 |
| --- | --- | --- |
| 运行方式 | 解释器直接执行 | 编译 + 链接 |
| 依赖管理 | `pip` + `venv` | 系统库 + `-I/-L/-l` |
| 构建脚本 | 通常不需要 | Makefile |
| 调试 | `print` / `pdb` | gdb / ASan / valgrind |
| 性能分析 | `time` / `cProfile` | `-O2` + `time` |
| 交付 | 源码 + 环境 | 可执行文件 + 动态库 |

Python 里「改完直接跑」是常态；C 里「构建」是一等公民。把 Makefile 写顺，是你从「写脚本」迈向「做工程」的第一步。

## 练习

1. 找一个之前写的 C 程序，用 `gcc -Wall -Wextra -std=c11` 编译，把所有警告分类记录（未使用变量 / 签名比较 / 格式串 / 其他），逐条修掉，直到没有输出。
   提示：不要用强制类型转换糊弄签名比较，先想清楚变量该不该是有符号。验收：编译输出为空；把至少 3 类警告与修法写进笔记。

2. 为 `math_utils` 例子写 Makefile，包含 `all`、`clean` 和一个 `debug` 目标（`debug` 用 `-fsanitize=address,undefined` 编译出 `app_debug`）。
   提示：可以定义 `DEBUG_FLAGS` 变量。验收：`make` 生成 `app`；`make debug` 生成 `app_debug` 且运行无 ASan 报错；`make clean` 清掉全部产物。

3. 用 gdb 调试 5.5 的 `segv.c`：在 `sum_to` 处下断点，单步到崩溃行，用 `print p` 与 `backtrace` 说明原因；修改代码使其正确输出 `55`。
   提示：`run` 后程序收到 SIGSEGV 时，用 `bt` 看栈顶；`frame` 切换上下文。验收：提交一段 5~10 行的 gdb 会话记录（命令 + 关键输出）与修复后的源码。

4. 给 `math_utils` 分别做静态库和动态库两个版本，编译出 `app_static` 与 `app_shared`，用 `ldd` 验证差异。
   提示：动态库需要 `-fPIC -shared`；运行 `app_shared` 前设置 `LD_LIBRARY_PATH=.`。验收：`ldd app_shared | grep mathutils` 有输出，`ldd app_static | grep mathutils` 无输出，两个程序运行结果一致。

5. 用 5.7 的 `bench.c` 对比 `-O0` 与 `-O2`：各运行 3 次取大概范围，写 5 行结论（差距倍数、原因猜测、对 Python 优化的启示）。
   提示：`time` 输出的 real 时间就够用；保证两次运行参数相同。验收：`sum` 输出一致；结论里出现具体时间数字。

## 自测清单

- [ ] 我能解释 `-Wall -Wextra -g -O2 -std=c11 -c -o` 每个选项的作用。
- [ ] 我能说出从 `.c` 到可执行文件的四个阶段，并用 `nm` 查看未定义符号。
- [ ] 我能独立写出一个含 `all / clean / 模式规则 / .PHONY` 的 Makefile，并解释 `$@ $^ $<`。
- [ ] 我知道 Makefile 命令前必须是 Tab，以及头文件依赖为什么重要。
- [ ] 我会用 gdb 的 `break / run / next / step / print / backtrace / frame / watch / continue`。
- [ ] 我能用 gdb 定位一个空指针解引用，并说出是哪一行、哪个变量。
- [ ] 我能说出 ASan 与 valgrind 各自适合的场景，不会同时使用。
- [ ] 我会用 `time` 对比 `-O0` 与 `-O2`，并知道先改算法再谈优化。
- [ ] 我能列出静态库与动态库各自的优缺点。
- [ ] 我大致知道 CSAPP 哪些章节对应本阶段哪些内容，并选好了 2~3 个 lab。

## 参考资料

- GCC 官方文档：https://gcc.gnu.org/onlinedocs/
- GNU Make 官方手册：https://www.gnu.org/software/make/manual/
- GDB 官方文档：https://sourceware.org/gdb/documentation/
- man7.org 在线手册：https://man7.org/linux/man-pages/
- CS:APP 课程主页（教材与 lab）：https://csapp.cs.cmu.edu/
