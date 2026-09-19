/*
 * shell.c —— 「简易 Shell」项目骨架（阶段 03）
 *
 * 编译:
 *   make            # 生成可执行文件 myshell
 *   ./myshell       # 运行
 *
 * 当前已经实现（对应 README 的 M1）:
 *   - REPL 循环：打印提示符、fgets 读取一行、Ctrl+D 退出
 *   - 命令行解析：按空白切分成 argv 数组
 *   - 内建命令: help / exit / cd
 *
 * 需要你实现的 TODO（按 README 里程碑顺序）:
 *   - M2: execute_external() 里的 fork + execvp + waitpid
 *   - M3: 行过长处理、错误信息、空命令等细节
 *   - M4: 重定向 > <（在 execute_external 里先扫描重定向符号）
 *   - M5: 管道 |（需要把命令拆成多段，pipe + 多次 fork）
 *   - 进阶: 后台 &、SIGINT 处理、history 历史记录
 *
 * 约束: 只使用 C 标准库与 POSIX 接口；不要调用 system() / popen()。
 *       读取输入用 fgets，永远不要用 gets。
 */
#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

#define MAX_LINE 1024
#define MAX_ARGS 64

/* 打印提示符，例如  myshell:/home/you$  */
static void print_prompt(void)
{
    char cwd[512];

    if (getcwd(cwd, sizeof(cwd)) == NULL) {
        /* getcwd 失败不致命，退回一个简单提示符 */
        fputs("myshell$ ", stdout);
        return;
    }
    printf("myshell:%s$ ", cwd);
    fflush(stdout);
}

/*
 * 读取一行输入。
 * 返回 1 表示成功；返回 0 表示遇到 EOF（Ctrl+D），调用者应退出 shell。
 * TODO(M3): 如果一行超过 size-1，fgets 只读了前半段，剩下的会当成下一条
 *           命令。可以检测行尾没有 '\n' 并吃掉剩余字符（选做）。
 */
static int read_line(char *buf, size_t size)
{
    if (fgets(buf, (int)size, stdin) == NULL)
        return 0;

    size_t len = strlen(buf);
    if (len > 0 && buf[len - 1] == '\n')
        buf[len - 1] = '\0';        /* 去掉换行符 */
    return 1;
}

/*
 * 解析命令行: 把 line 按空白切分成 argv 数组。
 * 注意: strtok 会就地修改 line（把分隔符替换成 '\0'），
 *       所以 argv 里的指针都指向 line 内部，line 必须保持有效。
 * 返回参数个数（不含结尾的 NULL）。
 * TODO(M4/M5): 现在 '>' '<' '|' 只是普通参数，等你实现重定向与管道时，
 *              需要在这里先把它们识别出来（或单独写一个扫描函数）。
 */
static int parse_line(char *line, char *argv[], int max_args)
{
    int argc = 0;
    char *token = strtok(line, " \t\r\n");

    while (token != NULL && argc < max_args - 1) {
        argv[argc] = token;
        argc++;
        token = strtok(NULL, " \t\r\n");
    }
    argv[argc] = NULL;              /* execvp 要求参数数组以 NULL 结尾 */
    return argc;
}

static void builtin_help(void)
{
    printf("内建命令:\n"
           "  help        显示本帮助\n"
           "  exit        退出 shell\n"
           "  cd [目录]   切换目录（不带参数时回到 HOME）\n");
    printf("其他输入会作为外部命令执行（M2 待实现）。\n");
}

/* 执行 cd。返回 0 表示成功，-1 表示失败 */
static int builtin_cd(char *argv[], int argc)
{
    const char *target;

    if (argc > 2) {
        fprintf(stderr, "cd: 参数过多（本 shell 暂不支持带空格的路径）\n");
        return -1;
    }

    if (argc == 2) {
        target = argv[1];
    } else {
        target = getenv("HOME");
        if (target == NULL) {
            fprintf(stderr, "cd: 未设置 HOME 环境变量\n");
            return -1;
        }
    }

    if (chdir(target) < 0) {
        fprintf(stderr, "cd: %s: %s\n", target, strerror(errno));
        return -1;
    }
    return 0;
}

/*
 * 判断并执行内建命令。
 * 返回 1: 已处理（exit 会直接结束进程）
 * 返回 0: 不是内建命令，调用者应交给外部命令执行
 */
static int run_builtin(char *argv[], int argc)
{
    if (strcmp(argv[0], "help") == 0) {
        builtin_help();
        return 1;
    }
    if (strcmp(argv[0], "exit") == 0) {
        exit(0);
    }
    if (strcmp(argv[0], "cd") == 0) {
        builtin_cd(argv, argc);
        return 1;
    }
    return 0;
}

/*
 * 执行外部命令。
 * 返回 0 表示命令成功结束，非 0 表示失败。
 *
 * TODO(M2): 按下面步骤实现本函数，替换现在的提示输出。
 *   1. pid = fork(); 检查返回值:
 *        pid < 0  -> perror("fork")，返回 1
 *        pid == 0 -> 子进程: 调用 execvp(argv[0], argv)
 *                    如果 execvp 返回（说明失败），打印错误信息，
 *                    然后用 _exit(127) 结束子进程（127 是约定值）
 *        pid > 0  -> 父进程: waitpid(pid, &status, 0) 回收子进程，
 *                    检查返回值，用 WIFEXITED / WEXITSTATUS 取出退出码
 *   2. 需要的头文件已经在本文件顶部包含（sys/wait.h、unistd.h、errno.h）。
 *   3. execvp 成功后整个进程映像被替换，后面的代码只在失败时执行。
 *
 * 提示: 先让 `ls` 和 `/bin/echo hi` 能跑通，再做 M3 的错误细节，
 *       最后才考虑 M4 重定向与 M5 管道。
 */
static int execute_external(char *argv[])
{
    /* TODO(M2): 在这里实现 fork + execvp + waitpid */
    fprintf(stderr, "myshell: 暂未实现外部命令执行: %s\n", argv[0]);
    fprintf(stderr, "提示: 完成 execute_external() 后即可运行外部命令。\n");
    return 1;
}

int main(void)
{
    char line[MAX_LINE];
    char *argv[MAX_ARGS];

    printf("简易 Shell 骨架（阶段 03）。输入 help 查看内建命令，Ctrl+D 退出。\n");

    for (;;) {
        print_prompt();

        if (!read_line(line, sizeof(line))) {
            putchar('\n');          /* Ctrl+D: 换行，避免和终端提示符连在一起 */
            break;
        }

        int argc = parse_line(line, argv, MAX_ARGS);
        if (argc == 0)
            continue;               /* 空行或只有空白，直接回到提示符 */

        /* TODO(进阶): 在这里把非空命令行保存进历史记录（存副本！） */

        if (run_builtin(argv, argc))
            continue;

        execute_external(argv);
    }
    return 0;
}
