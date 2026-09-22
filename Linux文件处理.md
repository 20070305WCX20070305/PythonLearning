# Linux 文件处理常用命令

> 本篇按「基础文本工具 → awk → sed → 管道与协作工具」的顺序，介绍 Linux 下最常用的文件处理命令。clear
> 示例统一以 `example.txt`、`data.csv` 等文件为例，建议边看边在终端里练习。

---

## 目录

1. [基础文本工具](#一基础文本工具)
   - [cut](#1-cut按列剪切)
   - [sort](#2-sort排序)
   - [uniq](#3-uniq去重)
   - [wc](#4-wc统计)
   - [head](#5-head查看开头)
   - [tail](#6-tail查看结尾)
2. [awk：按列处理的瑞士军刀](#二awk按列处理的瑞士军刀)
3. [sed：流式编辑器](#三sed流式编辑器)
4. [管道 |、xargs、tee](#四管道-xargs-tee)
5. [综合实战](#五综合实战)
6. [速查表](#六速查表)

---

## 一、基础文本工具

假设有一个文件 `data.csv`，内容如下：

```
1,alice,90,beijing
2,bob,75,shanghai
3,carol,88,beijing
4,dave,60,guangzhou
5,alice,95,beijing
```

### 1. cut（按列剪切）

`cut` 用于从每一行中「剪切」出指定的部分（按字节、字符或字段）。

| 选项                   | 含义                                       |
| ---------------------- | ------------------------------------------ |
| `-d`                 | 指定分隔符（默认是制表符`\t`）           |
| `-f`                 | 指定要保留的字段编号，如`1,3` 或 `2-4` |
| `-c`                 | 按字符位置剪切                             |
| `--complement`       | 取反，保留未被选中的部分                   |
| `--output-delimiter` | 指定输出分隔符                             |

**常用示例：**

```bash
# 取出第 1 列和第 3 列（逗号分隔）
cut -d, -f1,3 data.csv
# 输出：
# 1,90
# 2,75
# ...

# 取出第 2 到第 4 列
cut -d, -f2-4 data.csv

# 取出除第 4 列以外的所有列
cut -d, -f4 --complement data.csv

# 改变输出分隔符
cut -d, -f1,2 --output-delimiter=' | ' data.csv

# 按字符取前 5 个字符
cut -c1-5 data.csv
```

**注意：** `cut` 对「连续多个空格」不友好，它把每个空格都当作独立分隔符。遇到空格对齐的文本，更适合用 `awk`。

```bash
# 错误示范：多个空格时 cut 会切出空字段
echo "alice    90" | cut -d' ' -f2   # 输出空行
# 正确做法
echo "alice    90" | awk '{print $2}' # 输出 90
```

---

### 2. sort（排序）

`sort` 对文本行排序，默认按字典序（ASCII）升序。

| 选项     | 含义                            |
| -------- | ------------------------------- |
| `-n`   | 按数值排序                      |
| `-r`   | 逆序（降序）                    |
| `-k N` | 按第 N 列排序                   |
| `-t`   | 指定字段分隔符                  |
| `-u`   | 排序并去重（等价于 `sort        |
| `-f`   | 忽略大小写                      |
| `-h`   | 按人类可读数值排序（如 1K、2M） |

**常用示例：**

```bash
# 按第 3 列（分数）数值降序排序
sort -t, -k3 -nr data.csv

# 按第 2 列姓名排序，姓名相同时按第 3 列分数排序
sort -t, -k2,2 -k3,3n data.csv

# 去重排序
sort -u data.csv

# 按文件大小排序（配合 du）
du -h * | sort -h
```

**常见坑：**

- `sort` 默认按字符串比较，`10` 会排在 `9` 前面，数值排序必须加 `-n`。
- `-k3` 表示「从第 3 列一直比较到行尾」，若只想按第 3 列比较，写作 `-k3,3`。

---

### 3. uniq（去重）

`uniq` 只能去除**相邻的**重复行，所以通常先 `sort` 再用 `uniq`。

| 选项   | 含义                           |
| ------ | ------------------------------ |
| `-c` | 统计每行出现次数               |
| `-d` | 只显示重复的行                 |
| `-u` | 只显示不重复（仅出现一次）的行 |
| `-i` | 忽略大小写                     |

**常用示例：**

```bash
# 统计姓名出现次数，按次数降序
cut -d, -f2 data.csv | sort | uniq -c | sort -nr
# 输出：
#   2 alice
#   1 dave
#   1 carol
#   1 bob

# 找出出现次数大于 1 的行
sort data.csv | uniq -d

# 只保留唯一行
sort data.csv | uniq -u
```

**注意：** 直接 `uniq data.csv` 不会去除不相邻的重复行，请务必先排序：

```bash
uniq data.csv            # 可能去不干净
sort data.csv | uniq     # 正确姿势
```

---

### 4. wc（统计）

`wc` 统计文件的行数、单词数、字节数。

| 选项   | 含义         |
| ------ | ------------ |
| `-l` | 行数         |
| `-w` | 单词数       |
| `-c` | 字节数       |
| `-m` | 字符数       |
| `-L` | 最长行的长度 |

**常用示例：**

```bash
wc -l data.csv          # 5 data.csv
wc -l < data.csv        # 5（只输出数字，方便脚本取值）

# 统计当前目录下 .py 文件的行数
find . -name "*.py" | xargs wc -l

# 统计登录用户数（相当于 who | wc -l）
who | wc -l
```

---

### 5. head（查看开头）

`head` 默认显示文件前 10 行。

```bash
head data.csv          # 前 10 行
head -n 3 data.csv     # 前 3 行（-3 的写法也支持）
head -c 50 data.csv    # 前 50 个字节
head -q a.txt b.txt    # 多个文件时不显示文件名标题
```

---

### 6. tail（查看结尾）

`tail` 默认显示文件最后 10 行。

```bash
tail data.csv          # 最后 10 行
tail -n 3 data.csv     # 最后 3 行
tail -n +3 data.csv    # 从第 3 行开始显示到结尾

# 实时跟踪日志（排查问题时最常用）
tail -f /var/log/syslog
tail -F /var/log/app.log   # 文件被轮转后仍能继续跟踪
```

**记忆技巧：** `head -n +K` 从头数，`tail -n +K` 从第 K 行开始；`-f` 的 f 是 follow（跟随）。

---

## 二、awk（按列处理的瑞士军刀）

`awk` 是一门面向文本行的迷你编程语言，语法为：

```
awk 'pattern { action }' file
```

- **pattern**：匹配条件（可省略，省略时每行都执行 action）。
- **action**：对匹配行执行的操作（可省略，省略时默认 `print $0`）。

### 2.1 内置变量

| 变量            | 含义                                 |
| --------------- | ------------------------------------ |
| `$0`          | 当前整行                             |
| `$1, $2, ...` | 第 1、2… 个字段                     |
| `NF`          | 当前行的字段总数（Number of Fields） |
| `NR`          | 当前处理的行号（Number of Records）  |
| `FNR`         | 当前文件内的行号（多文件时有用）     |
| `FS`          | 输入字段分隔符（默认为空白）         |
| `OFS`         | 输出字段分隔符（默认为空格）         |
| `RS`          | 输入记录分隔符（默认换行）           |

### 2.2 常用示例

```bash
# 打印第 1、3 列（等效于 cut，但对多空格更智能）
awk -F, '{print $1, $3}' data.csv

# 指定输入/输出分隔符
awk -F, 'BEGIN{OFS="\t"} {print $1, $2}' data.csv

# 打印行号
awk '{print NR, $0}' data.csv

# 条件过滤：分数大于 80 的行
awk -F, '$3 > 80 {print $2, $3}' data.csv

# 按姓名匹配
awk -F, '$2 == "alice" {print $0}' data.csv

# 打印最后一列（不用数第几列）
awk -F, '{print $NF}' data.csv

# 打印倒数第二列
awk -F, '{print $(NF-1)}' data.csv

# 求和 / 平均值 / 最大值
awk -F, '{sum += $3} END {print "总分:", sum, "平均分:", sum/NR}' data.csv

# 分组统计：每个城市的分数总和
awk -F, '{city[$4] += $3} END {for (c in city) print c, city[c]}' data.csv

# 去重（保留首次出现）
awk -F, '!seen[$2]++ {print $2}' data.csv

# 格式化输出
awk -F, '{printf "%-10s %5d\n", $2, $3}' data.csv

# 多条件与逻辑运算
awk -F, '$3 > 70 && $4 == "beijing" {print $2}' data.csv
```

### 2.3 pattern 的几种写法

```bash
awk 'NR==1' data.csv                # 只处理第 1 行
awk 'NR>=2 && NR<=4' data.csv       # 处理第 2~4 行
awk '/alice/' data.csv              # 匹配包含 alice 的行
awk '!/alice/' data.csv             # 不包含 alice 的行
awk '/alice/,/dave/' data.csv       # 从 alice 行到 dave 行
```

### 2.4 BEGIN 与 END

```bash
awk -F, '
BEGIN { print "开始统计"; sum = 0 }
      { sum += $3 }
END   { print "总分:", sum }
' data.csv
```

- `BEGIN`：处理任何行之前执行，常用于初始化、打印表头。
- `END`：所有行处理完后执行，常用于汇总输出。

**小结：** `cut` 能做的 awk 都能做，且更灵活；awk 还能做过滤、计算、分组、格式化，是文本处理的第一利器。

---

## 三、sed（流式编辑器）

`sed`（Stream Editor）按行流式处理文本，适合做替换、删除、插入、提取。

基本语法：

```
sed [选项] '脚本' 文件
```

常用选项：

| 选项            | 含义                                     |
| --------------- | ---------------------------------------- |
| `-n`          | 不自动打印模式空间内容（配合`p` 使用） |
| `-e`          | 指定多个脚本                             |
| `-i`          | 直接修改文件（原地编辑）                 |
| `-r` / `-E` | 使用扩展正则                             |

### 3.1 替换（s 命令）

语法：`s/原内容/新内容/[标志]`

```bash
# 每行第一个 alice 替换为 ALICE
sed 's/alice/ALICE/' data.csv

# 每行所有匹配都替换（g = global）
sed 's/alice/ALICE/g' data.csv

# 只替换第 2 行
sed '2s/alice/ALICE/' data.csv

# 替换第 2 行之后的所有行
sed '2,$s/alice/ALICE/g' data.csv

# 引用匹配内容（& 表示整个匹配）
sed 's/[0-9]\+/[&]/' data.csv

# 分组引用（\1、\2）
sed -E 's/([0-9]+),([a-z]+)/\2:\1/' data.csv

# 原地修改文件（先备份）
sed -i.bak 's/beijing/BEIJING/g' data.csv
```

### 3.2 删除（d 命令）

```bash
sed '3d' data.csv            # 删除第 3 行
sed '2,4d' data.csv          # 删除第 2~4 行
sed '/alice/d' data.csv      # 删除包含 alice 的行
sed '/^$/d' data.csv         # 删除空行
sed '/^#/d;/^$/d' config.ini # 删除注释行和空行
```

### 3.3 打印（p 命令，配合 -n）

```bash
sed -n '3p' data.csv         # 只打印第 3 行
sed -n '2,4p' data.csv       # 打印第 2~4 行
sed -n '/alice/p' data.csv   # 打印包含 alice 的行
sed -n '$p' data.csv         # 打印最后一行
```

### 3.4 插入与追加（i / a 命令）

```bash
sed '1i\姓名,分数' data.csv       # 在第 1 行前插入
sed '$a\—— 文件结束 ——' data.csv   # 在最后一行后追加
```

### 3.5 其他技巧

```bash
# 大小写转换
sed 's/.*/\U&/' data.csv     # 转大写
sed 's/.*/\L&/' data.csv     # 转小写

# 多个替换一起做（-e 可写多个）
sed -e 's/alice/ALICE/g' -e 's/bob/BOB/g' data.csv

# 只输出匹配的部分（类似 grep -o）
echo "id=42" | sed -n 's/.*id=\([0-9]*\).*/\1/p'   # 输出 42
```

**注意：** macOS 的 `sed -i` 需要跟一个参数（如 `sed -i ''`），Linux 不需要；`\+`、`\?` 等转义在扩展正则下写作 `+`、`?`。

---

## 四、管道、xargs、tee

### 4.1 管道 `|`

管道把前一个命令的**标准输出**作为后一个命令的**标准输入**，是 Unix 的核心哲学：小工具组合出大功能。

```bash
# 组合示例：统计每个城市的平均分
awk -F, '{sum[$4]+=$3; cnt[$4]++} END {for (c in sum) print c, sum[c]/cnt[c]}' data.csv \
  | sort -k2 -nr

# 统计出现次数最多的 3 个姓名
cut -d, -f2 data.csv | sort | uniq -c | sort -nr | head -n 3

# 查看占用端口 8080 的进程
ss -lntp | grep ':8080'

# 管道 + grep + awk 的组合拳
ps aux | grep python | grep -v grep | awk '{print $2}'
```

**常见错误：**

- `ls | cd` 之类内置命令无法接收管道输入（`cd` 不是外部命令）。
- 管道默认只传 stdout，**stderr 不会自动进入管道**。需要时用 `2>&1`：

```bash
command1 2>&1 | command2
```

### 4.2 xargs

`xargs` 把标准输入转换为**命令行参数**。很多命令（如 `rm`、`mkdir`）不从 stdin 读数据，只接受参数，这时就需要 xargs。

| 选项      | 含义                                          |
| --------- | --------------------------------------------- |
| `-n N`  | 每次传 N 个参数                               |
| `-d`    | 指定输入分隔符（默认空白/换行）               |
| `-0`    | 输入以`\0` 分隔，常与 `find -print0` 搭配 |
| `-I {}` | 占位符，把参数放到命令中任意位置              |
| `-p`    | 执行前询问确认                                |
| `-t`    | 执行前打印命令                                |

```bash
# 删除所有 .tmp 文件
find . -name "*.tmp" | xargs rm -f

# 文件名含空格时（安全做法）
find . -name "*.tmp" -print0 | xargs -0 rm -f

# 每次只处理 2 个文件
echo a b c d e | xargs -n 2 echo

# 用占位符构造任意位置参数
ls *.txt | xargs -I {} mv {} backup_{}

# 批量下载
cat urls.txt | xargs -n 1 -P 4 wget   # -P 4 表示 4 个并发

# 与 awk 配合杀掉进程
ps aux | grep myapp | grep -v grep | awk '{print $2}' | xargs kill -9
```

**何时不用 xargs：** 若目标命令本身支持从 stdin 读，就不要绕弯，例如 `wc -l` 直接接受管道输入。

### 4.3 tee

`tee` 把标准输入**同时**写到屏幕（stdout）和文件，像一个「T 形三通」。

```bash
# 一边看输出，一边保存
ls -l | tee files.txt

# 追加而不是覆盖（-a）
make 2>&1 | tee -a build.log

# 配合 sudo：tee 以 root 权限写文件
echo "export PATH=$PATH:/opt/bin" | sudo tee -a /etc/profile

# 在管道中间存一份中间结果，继续往下传
cat data.csv | tee backup.csv | awk -F, '$3 > 80 {print $2}'
```

**常见组合：** `command | tee out.log | grep Error` —— 既完整保存日志，又实时过滤查看。

---

## 五、综合实战

### 实战 1：分析访问日志

假设 `access.log` 每行形如：

```
192.168.1.1 - - [21/Sep/2026:10:00:01] "GET /index.html" 200 1024
```

```bash
# 访问量 Top 10 的 IP
awk '{print $1}' access.log | sort | uniq -c | sort -nr | head -n 10

# 统计各状态码数量
awk '{print $9}' access.log | sort | uniq -c | sort -nr

# 找出 5xx 错误的请求路径
awk '$9 ~ /^5/ {print $7}' access.log | sort | uniq -c | sort -nr
```

### 实战 2：处理 CSV 数据

```bash
# 计算每个城市总分，按总分降序，只显示前 2 名
awk -F, '{sum[$4] += $3} END {for (c in sum) printf "%s\t%d\n", c, sum[c]}' data.csv \
  | sort -k2 -nr | head -n 2

# 把 CSV 转成 JSON 风格输出
awk -F, 'BEGIN{print "["} {printf "  {\"id\":%s,\"name\":\"%s\",\"score\":%s},\n", $1, $2, $3} END{print "]"}' data.csv
```

### 实战 3：清理与备份文件

```bash
# 找出 7 天前的日志并压缩归档
find /var/log -name "*.log" -mtime +7 -print0 \
  | xargs -0 tar -czf old_logs.tar.gz

# 批量重命名：给所有 .txt 加前缀
ls *.txt | xargs -I {} mv {} "backup_{}"

# 清空大日志同时保留权限（> 重定向比 rm 更安全）
: > /var/log/app.log
```

---

## 六、速查表

| 命令      | 一句话说明             | 高频用法                            |
| --------- | ---------------------- | ----------------------------------- |
| `cut`   | 按列剪切               | `cut -d, -f1,3 file`              |
| `sort`  | 排序                   | `sort -t, -k3 -nr file`           |
| `uniq`  | 去重/计数（需先排序）  | `sort file \| uniq -c`             |
| `wc`    | 统计行/词/字节         | `wc -l file`                      |
| `head`  | 看开头                 | `head -n 20 file`                 |
| `tail`  | 看结尾/跟踪日志        | `tail -f app.log`                 |
| `awk`   | 按列处理 + 计算 + 过滤 | `awk -F, '$3>80 {print $2}' file` |
| `sed`   | 流式替换/删除/插入     | `sed -i 's/old/new/g' file`       |
| `\|`     | 串联命令               | `cmd1 \| cmd2`                     |
| `xargs` | stdin 转命令行参数     | `find . -name "*.tmp" \| xargs rm` |
| `tee`   | 输出同时写屏幕和文件   | `cmd \| tee out.log`               |

**组合套路：**

```
过滤 grep → 取列 cut/awk → 排序 sort → 去重计数 uniq -c → 再排序 sort -nr → 看头部 head
```

掌握这条流水线，绝大多数日志分析、数据清洗任务都能搞定。
