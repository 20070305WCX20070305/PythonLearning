# 04 - 进程、线程与 socket

## 学习目标

- 把 Python 里用过的 `subprocess` / `multiprocessing` / `threading` 对应到操作系统的真实机制。
- 会用 `fork` 创建子进程，用 `waitpid` 回收并读取退出状态；用 `execvp` 替换进程映像。
- 会用 `pipe` 在两个进程之间传数据。
- 理解信号的基本用法（`SIGINT`、处理函数、`sig_atomic_t`）。
- 会用 `pthread_create / pthread_join` 写多线程程序，用互斥锁修复竞争条件。
- 能写出一个 TCP echo 服务器与客户端，理解 `socket / bind / listen / accept / connect`。

## 前置知识

- 阶段 02：多进程概念、`subprocess`、`ProcessPoolExecutor` 的使用经验。
- 01~03 篇：指针、字符串、文件描述符、返回值检查与 `errno`。

## 建议用时

3 周，约 22~28 小时。按 4.2 → 4.7 顺序，每个示例跑两遍（一遍故意出错，一遍正确）。

## 正文

### 4.1 从 Python 的并发回到操作系统

阶段 02 你用过的 Python 工具，背后都是本节的系统机制：

| Python（阶段 02） | 操作系统机制 | 本节接口 |
| --- | --- | --- |
| `multiprocessing.Process` | 复制出一个新进程 | `fork` |
| `subprocess.run` | fork + exec + 等待 + 收退出码 | `fork` + `execvp` + `waitpid` |
| `multiprocessing.Pipe/Queue` | 管道 | `pipe` |
| `signal` 模块 | 信号 | `signal` / `kill` |
| `threading.Thread` | 内核线程 | `pthread_create` |
| `threading.Lock` | 互斥锁 | `pthread_mutex_t` |
| `socket` 模块 | BSD socket | `socket / bind / connect` |

常见错误：

- 把进程和线程混为一谈：出错的形态完全不同。
- 以为 `fork` 会执行两次 `main`：它复制的是「调用点之后的整个进程状态」，每个进程各返回一次。

### 4.2 fork 与 waitpid

`fork()` 调用一次、返回两次：父进程里返回子进程 pid，子进程里返回 0，失败返回 -1。父进程必须用 `waitpid` 回收子进程，否则会产生僵尸进程（zombie）。

```c
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    fflush(stdout);                  /* fork 前刷缓冲，避免输出重复 */
    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 1; }

    if (pid == 0) {                  /* 子进程：fork 返回 0 */
        printf("子进程: pid=%d, 父进程 pid=%d\n",
               (int)getpid(), (int)getppid());
        _exit(7);                    /* 子进程用 _exit 结束 */
    }
    /* 父进程：fork 返回子进程 pid */
    int status = 0;
    if (waitpid(pid, &status, 0) < 0) { perror("waitpid"); return 1; }
    if (WIFEXITED(status))
        printf("父进程: 子进程 %d 退出，退出码 %d\n",
               (int)pid, WEXITSTATUS(status));
    return 0;
}
```

预期输出（两行顺序可能互换）：`子进程: pid=12346, 父进程 pid=12345`，随后 `父进程: 子进程 12346 退出，退出码 7`。

`status` 不是退出码本身，要用宏解读：`WIFEXITED` / `WEXITSTATUS`（正常退出）、`WIFSIGNALED` / `WTERMSIG`（被信号杀死）。子进程拿到的是父进程内存的副本（写时复制），之后两者互不影响；fd 表也会复制。

常见错误：

- `fork` 前用了 `printf` 没换行/没 `fflush`：缓冲区被子进程复制，输出出现两遍。
- 该 `wait` 不 `wait`：僵尸进程堆积，`ps` 里看到一堆 `Z` 状态。
- 子进程里用 `exit` 而不是 `_exit`：会重复刷父进程遗留的 stdio 缓冲。

### 4.3 exec 家族：替换进程映像

`execvp(file, argv)` 用新程序**替换**当前进程的内存与代码；成功后函数不返回（pid 不变，跑的是别的程序）。

```c
#include <stdio.h>
#include <unistd.h>
int main(void)
{
    char *args[] = {"ls", "-l", NULL};   /* 参数数组必须以 NULL 结尾 */
    execvp(args[0], args);               /* 在 PATH 中找 ls */
    perror("execvp");                    /* 只有失败才执行到这里 */
    return 1;
}
```

**fork + exec + wait** 是 shell 执行外部命令的骨架，思路示意（项目里请自己实现）：fork 后子进程 `execvp(argv[0], argv)`，失败则打印错误并 `_exit(127)`；父进程 `waitpid(pid, &status, 0)`，再用 `WIFEXITED / WEXITSTATUS` 取出退出码。

`exec` 家族日常用得最多的是 `execvp`（按 PATH 找、参数数组），另有 `execlp`（参数逐个列出）与 `execv`（用路径）。

常见错误：

- `args` 最后忘记 `NULL`：`execvp` 会一直读到越界，行为不可预测。
- exec 失败后不让子进程退出：子进程继续跑父进程的代码，出现「一条命令执行两次」。
- 子进程失败直接用 `exit`：应该 `_exit(127)`，127 是「命令找不到」的约定退出码。

### 4.4 pipe：进程间通信

`pipe(fds)` 创建一条单向管道：`fds[0]` 读端，`fds[1]` 写端。典型用法是 fork 后一个进程写、另一个读。

```c
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    int fds[2];
    if (pipe(fds) < 0) { perror("pipe"); return 1; }

    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 1; }

    if (pid == 0) {
        close(fds[0]);                       /* 子进程只写，先关读端 */
        const char *msg = "hello from child";
        if (write(fds[1], msg, strlen(msg)) < 0)
            perror("write");
        close(fds[1]);                       /* 写完就关，读端才会看到 EOF */
        _exit(0);
    }

    close(fds[1]);                           /* 父进程只读，先关写端 */
    char buf[64];
    ssize_t n = read(fds[0], buf, sizeof(buf) - 1);
    if (n < 0) { perror("read"); return 1; }
    buf[n] = '\0';    printf("父进程收到: %s\n", buf);
    close(fds[0]);
    waitpid(pid, NULL, 0);
    return 0;
}
```

预期输出：`父进程收到: hello from child`。管道是**字节流**，没有消息边界；写端全部关闭后，`read` 才返回 0（EOF）。shell 的 `|` 就是「创建管道 + 两个子进程分别把 stdout/stdin 接上去」（项目的管道里程碑）。

常见错误：

- 忘记关闭不用的那一端：读端永远等不到 EOF，程序挂住。
- 父子同时读或同时写一条管道：方向混乱；一条管道只做单向。

### 4.5 信号基础

信号是内核发给进程的「异步通知」。最熟悉的例子是 Ctrl+C 给前台进程发 `SIGINT`。可以在程序里注册处理函数，做优雅退出。

```c
#include <signal.h>
#include <stdio.h>
#include <unistd.h>

static volatile sig_atomic_t stop = 0;    /* 处理函数只能安全地改这种变量 */

static void handle_sigint(int signo)
{
    (void)signo;
    stop = 1;                              /* 只做最简单的事，不做 printf/malloc */
}

int main(void)
{
    if (signal(SIGINT, handle_sigint) == SIG_ERR) { perror("signal"); return 1; }

    printf("按 Ctrl+C 结束循环（pid=%d）\n", (int)getpid());
    while (!stop) {
        sleep(1);
        printf(".");
        fflush(stdout);
    }
    printf("\n收到 SIGINT，干净退出\n");
    return 0;
}
```

运行：按几次 Ctrl+C，程序打印提示后退出；也可以从另一个终端 `kill -INT <pid>`（等价）、`kill -TERM <pid>`（可捕获）或 `kill -KILL <pid>`（强杀，无法捕获）。处理函数里只能调用「异步信号安全」的函数；常用 `sig_atomic_t` 标志位，主循环里做真正的处理。`signal()` 是老接口，更严谨的写法用 `sigaction()`，需要时查 `man 7 signal`。

常见错误：

- 在处理函数里 `printf` / `malloc` / `free`：可能死锁或崩溃。
- 用普通 `int` 而不是 `sig_atomic_t` 作为标志：编译器可能优化成死循环。
- 忘了某些系统调用被信号打断会返回 -1 且 `errno == EINTR`：要么重试，要么用 `SA_RESTART`。

### 4.6 pthread：线程与互斥锁

线程共享同一进程的地址空间，创建和通信比进程便宜，但共享数据必须加锁。先看竞争条件（race condition）：

```c
#include <pthread.h>
#include <stdio.h>

static long counter = 0;          /* 两个线程共享它 */

static void *worker(void *arg)
{
    (void)arg;
    for (int i = 0; i < 1000000; i++)
        counter++;                /* 读-改-写不是原子操作 */
    return NULL;
}

int main(void)
{
    pthread_t t1, t2;
    if (pthread_create(&t1, NULL, worker, NULL) != 0) return 1;
    if (pthread_create(&t2, NULL, worker, NULL) != 0) return 1;
    if (pthread_join(t1, NULL) != 0) return 1;   /* 等两个线程结束 */
    if (pthread_join(t2, NULL) != 0) return 1;
    printf("counter = %ld（期望 2000000）\n", counter);
    return 0;
}
```

编译运行（**注意 `-pthread`**）：`gcc -Wall -Wextra -std=c11 -g race.c -o race -pthread`，多跑几次 `./race`，`counter` 多数情况下小于 2000000，且每次不同——这就是竞争条件。修复：在文件顶部加锁定义，把 `counter++` 两端改成下面三行（临界区尽量短）：

```c
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;   /* 放在文件顶部 */
...
pthread_mutex_lock(&lock);
counter++;                        /* 临界区尽量短 */
pthread_mutex_unlock(&lock);
```

要点：`pthread_create` 成功返回 0，失败返回错误码（不是 -1，也不设置 `errno`）；线程函数签名固定为 `void *(*)(void *)`；`pthread_join` 回收线程资源。需要「等待某个条件成立」时用条件变量 `pthread_cond_t` + `pthread_cond_wait`，先了解名字，用到再学。

常见错误：

- 编译/链接漏掉 `-pthread`：报 `undefined reference to pthread_create`。
- 忘记 `pthread_join`：线程资源不回收，主线程可能先退出导致进程结束。
- 多个锁的加锁顺序不一致：死锁（deadlock），两个线程互等。

### 4.7 socket：TCP echo 服务器与客户端

socket 是网络通信的「文件描述符」：连上以后用 `read`/`write` 读写。服务器流程是 `socket → bind → listen → accept`，客户端是 `socket → connect`。网络用大端字节序，用 `htons/htonl` 转换。

`echo_server.c`：

```c
#define _POSIX_C_SOURCE 200809L
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define PORT 9000
#define BUF_SIZE 1024

int main(void)
{
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd < 0) { perror("socket"); return 1; }

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);   /* 监听所有网卡 */
    addr.sin_port = htons(PORT);                /* 主机字节序 -> 网络字节序 */
    if (bind(listen_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); close(listen_fd); return 1;
    }
    if (listen(listen_fd, 8) < 0) { perror("listen"); close(listen_fd); return 1; }
    for (;;) {
        struct sockaddr_in peer;
        socklen_t peer_len = sizeof(peer);
        int conn_fd = accept(listen_fd, (struct sockaddr *)&peer, &peer_len);
        if (conn_fd < 0) { perror("accept"); continue; }

        char buf[BUF_SIZE];
        ssize_t n;
        while ((n = read(conn_fd, buf, sizeof(buf) - 1)) > 0) {
            buf[n] = '\0';
            if (write(conn_fd, buf, (size_t)n) < 0) { perror("write"); break; }
        }
        close(conn_fd);
    }
    return 0;
}
```

`echo_client.c`：

```c
#define _POSIX_C_SOURCE 200809L
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define PORT 9000
#define BUF_SIZE 1024

int main(int argc, char *argv[])
{
    const char *server_ip = (argc > 1) ? argv[1] : "127.0.0.1";

    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) { perror("socket"); return 1; }

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(PORT);
    if (inet_pton(AF_INET, server_ip, &addr.sin_addr) != 1) {
        fprintf(stderr, "无效地址: %s\n", server_ip);
        close(fd); return 1;
    }
    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("connect"); close(fd); return 1;
    }

    char buf[BUF_SIZE];
    while (fgets(buf, sizeof(buf), stdin) != NULL) {
        if (write(fd, buf, strlen(buf)) < 0) { perror("write"); break; }
        ssize_t n = read(fd, buf, sizeof(buf) - 1);
        if (n < 0) { perror("read"); break; }
        if (n == 0) { printf("服务器关闭连接\n"); break; }
        buf[n] = '\0';
        printf("echo: %s", buf);
    }
    close(fd);
    return 0;
}
```

编译与测试（两个终端）：

```bash
gcc -Wall -Wextra -std=c11 -g echo_server.c -o echo_server   # 终端 1 运行 ./echo_server
gcc -Wall -Wextra -std=c11 -g echo_client.c -o echo_client   # 终端 2 运行 ./echo_client 后可输入 hello
```

也可以用 netcat 测试（可选安装）：`printf 'hi\n' | nc 127.0.0.1 9000`。服务器启动后打印 `监听 0.0.0.0:9000 ...`，客户端输入 `hello` 得到 `echo: hello`。

要点：TCP 是字节流，一次 `read` 不保证对上对端的一次 `write`；服务器一次只处理一个连接（accept 循环里串行处理），想并发就把每个连接交给线程。socket 不需要额外链接库，线程才需要 `-pthread`。

常见错误：

- 端口被占：`bind: Address already in use`；加 `SO_REUSEADDR` 或换端口。
- 把 `bind` 的地址/端口写反：端口用 `htons`，IP 用 `htonl`/`inet_pton`。
- 忘记 `memset` 结构体，残留垃圾导致 `bind` 失败。
- 客户端和服务端都跑在 WSL 里时，连接 `127.0.0.1` 即可，不要写 Windows 主机 IP。

### 4.8 与 Python 的对照

| 主题 | Python | C |
| --- | --- | --- |
| 创建进程 | `multiprocessing.Process(target=...)` | `fork()` + 分支代码 |
| 执行外部程序 | `subprocess.run(["ls", "-l"])` | `fork` + `execvp` + `waitpid` |
| 进程间数据 | `Pipe` / `Queue` | `pipe` + `read/write` |
| 退出码 | `result.returncode` | `WEXITSTATUS(status)` |
| 信号 | `signal.signal` | `signal` / `sigaction` + `kill` |
| 线程与锁 | `threading.Thread` / `Lock` | `pthread_create/join` / `pthread_mutex_t` |
| 网络 | `socket` 模块 | BSD socket API |
| 错误处理 | 异常 | 返回值 + `errno` |

一个直接体会：Python 的 `threading` 因为 GIL，纯计算多线程不提速，但**锁的用法与 C 的 pthread 一模一样**；C 的线程是真并行，所以竞争条件更隐蔽、更需要工具与纪律。

## 练习

1. fork 三个子进程：每个子进程打印自己的序号（0/1/2）与 pid，父进程用 `waitpid` 依次回收，最后打印「全部子进程结束」。
   提示：循环里 fork，子进程 `_exit(0)`，父进程把 pid 存数组再等。验收：至少看到 3 条子进程输出与 1 条父进程结束输出，`ps` 无僵尸残留。

2. 双向管道：父进程写一个小写字符串给子进程，子进程用 `toupper`（`<ctype.h>`）改成大写后经第二条管道写回，父进程打印结果。
   提示：`pipe` 调用两次得到两条单向管道；父子各自关掉不用的端。验收：输入 `hello wsl` 输出 `HELLO WSL`。

3. 多线程分段累加：把 `long long a[4000000]` 填 1，用 4 个线程各累加一段，主线程 `join` 后汇总，与单线程结果对比。
   提示：参数用结构体传（数组指针、起点、终点、结果）；各线程写不同结果变量，不用加锁。验收：结果等于 4000000，多次运行一致。

4. 并发 echo 服务器：把 4.7 的服务器改成「每个连接一个线程」：`accept` 后用 `malloc` 一个 `int` 保存 `conn_fd`，传给线程函数，线程处理完关闭 fd 并 `free`。
   提示：编译加 `-pthread`；线程函数里不要碰主线程的局部变量地址。验收：开两个客户端同时连接，两边都能正常 echo 且互不阻塞。

## 自测清单

- [ ] 我能说出 `fork` 的三种返回值以及父子进程各拿到什么；能解释僵尸进程与 `waitpid` + `WIFEXITED`。
- [ ] 我能写出 fork + execvp + waitpid 的执行外部命令流程，并解释 `_exit(127)`。
- [ ] 我会用 `pipe` 做父子进程单向通信，并知道为什么要关掉不用的端。
- [ ] 我能说出信号处理函数的限制（`sig_atomic_t`、不能 `printf`）。
- [ ] 我会用 `-pthread` 编译并写出 `pthread_create` + `pthread_join`；能解释竞争条件并会用互斥锁修复。
- [ ] 我能画出 TCP 服务器 `socket→bind→listen→accept` 与客户端 `socket→connect` 的流程。
- [ ] 我能解释 `htons` / `htonl` / `inet_pton` 各自解决什么问题，并把 Python 多进程脚本对应到 C 的系统调用组合。

## 参考资料

- man7.org 在线手册（`fork(2)`、`exec(3)`、`pipe(2)`、`signal(7)`、`pthreads(7)`、`socket(7)`、`tcp(7)`）：https://man7.org/linux/man-pages/
- GNU C Library 手册（进程、线程、socket 章节）：https://www.gnu.org/software/libc/manual/
- CS:APP 第 8 章「异常控制流」、第 11 章「网络编程」、第 12 章「并发编程」（选读）：https://csapp.cs.cmu.edu/
