# 简易 Shell 的 Makefile（阶段 03）
#
# 用法:
#   make        编译，生成可执行文件 myshell
#   make clean  删除中间文件与可执行文件
#
# 注意: 规则下面的命令行必须用 Tab 开头，不能用空格！

CC      = gcc
CFLAGS  = -Wall -Wextra -g -std=c11

TARGET  = myshell
OBJS    = shell.o

# 默认目标: 直接执行 make 时构建 myshell
all: $(TARGET)

# $@ = 目标名(myshell); $^ = 全部依赖(shell.o)
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

# 模式规则: 任意 .o 由同名 .c 编译而来; $< = 第一个依赖(shell.c)
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# 以后拆分多个 .c 时，把新的 .o 加到 OBJS（例如 shell.o parse.o execute.o）
# 以后用线程时，在 CFLAGS 里追加 -pthread

# clean 不是真实文件，所以声明为伪目标，保证每次都执行
clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean
