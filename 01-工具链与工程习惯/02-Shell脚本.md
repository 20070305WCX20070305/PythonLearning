# 02-Shell脚本

## 学习目标

- 会写 shebang，分清 `bash script.sh` 与 `./script.sh`
- 掌握变量、引号、命令替换的正确写法
- 会用 if / test / `[ ]` / `[[ ]]` 做条件判断
- 会用 for、while 循环处理文件，会用 case 与函数
- 会使用位置参数、`$@` 与退出码 `$?`
- 会写 `set -euo pipefail`，掌握文件名安全写法
- 理解 Shell 与 Python 的分工
- 能写出批量重命名、按日期归档、生成清单、参数解析四类脚本

## 前置知识

- 01-Linux基础：路径、通配符、管道与重定向、权限、find/grep
- 会使用文本编辑器（VSCode 打开 WSL 目录，或 nano/vim 任选其一）
- 在 01 中见过命令退出码 `$?` 的用法（本课详细讲）

## 建议用时

8~12 小时。每读一节就写一个脚本并在 WSL2 中运行验证。

## 正文

### 1. shebang 与运行方式

脚本第一行的 `#!/usr/bin/env bash` 叫 shebang，告诉系统用哪个解释器执行本文件；
用 `env bash` 而不是写死 `/bin/bash`，兼容性更好。
```bash
# 用编辑器创建 hello.sh，内容：第一行 #!/usr/bin/env bash，第二行 echo "你好，Shell"
bash hello.sh        # 方式一：显式调用解释器，不需要执行权限
chmod +x hello.sh    # 方式二：赋予执行权限后直接运行
./hello.sh
bash -n hello.sh     # 语法检查：只解析不执行，写脚本前先跑一遍很省时间
```
常见错误：

- 脚本里的相对路径是相对于「运行脚本时的当前目录」，不是脚本所在目录；关键路径写成变量并固定
- 忘了 `chmod +x`，直接 `./hello.sh` 报 `Permission denied`
- 用中文全角引号或分号，Shell 无法识别

### 2. 变量、引号与命令替换
```bash
name="实验数据"                  # 等号两边不能有空格
dir="$HOME/lab-data"
echo "$name 目录: $dir"          # 双引号：变量会展开
echo '$name 不展开'              # 单引号：原样输出
echo "第 ${count} 次测量"        # ${} 划清变量名边界，推荐写法

today=$(date +%F)                # 命令替换：把命令输出当字符串用
n=$(ls "$dir/raw" | wc -l)
stamp=$(date +%Y%m%d-%H%M%S)
tar -czvf "backup-$stamp.tar.gz" -C "$dir" raw
```
| 写法 | 变量是否展开 | 何时使用 |
| --- | --- | --- |
| `"$var"` | 展开 | 默认选择，最安全 |
| `'$var'` | 不展开 | 需要字面量时 |
| `$var` | 展开 | 仅当确定值中无空格、无通配符时 |
常见错误：

- `name = "值"` 等号两边加空格，Shell 会把它当成命令 `name` 执行
- 变量后紧跟字符不加 `{}`，如 `$count次` 会被解析成变量 `count次`
- 把命令替换结果当算术用，`total=$($n + 1)` 应写 `total=$((n + 1))`；命令输出很大时别全塞进变量

### 3. 条件判断：if / test / `[ ]` / `[[ ]]`

`if` 判断的是「命令的退出码」：0 为真，非 0 为假；`test`、`[ ]`、`[[ ]]` 都是产生退出码的命令。
```bash
if [ -d "$dir/raw" ]; then
    echo "raw 目录存在"
else
    echo "目录结构不完整"
fi

[ -e "$f" ]      # 存在（文件或目录）
[ -f "$f" ]      # 是普通文件
[ -d "$d" ]      # 是目录
[ -z "$s" ]      # 字符串为空
[ "$a" = "$b" ]  # 字符串相等，注意两边和方括号内都有空格
[ "$n" -gt 10 ]  # 数值比较：-eq -ne -lt -le -gt -ge

# [[ ]] 是 bash 增强版，支持 && || 与通配符匹配
if [[ "$name" == *.csv && -s "$name" ]]; then
    echo "非空 CSV 文件"
fi
```
常见错误：

- `[ ]` 里少了空格：`[$a = $b]` 会被当成一个不存在的命令
- 整数比较写成 `[ "$n" > 10 ]`，`>` 被当成重定向；数值一定用 `-gt`
- 变量未加引号时，空值会让 `[ -z $s ]` 变成参数个数错误

### 4. 循环：for 与 while
```bash
# for 遍历文件：科研脚本最常见的模式
for f in "$HOME/lab-data/raw"/*.csv; do
    [ -e "$f" ] || continue         # 没有任何匹配时保护
    echo "处理: $(basename -- "$f")"
done

# while 按行读文件：IFS= 保留行首空白，-r 不解释反斜杠
while IFS= read -r line; do
    [ -z "$line" ] && continue
    echo "读到: $line"
done < "$HOME/lab-data/samples.txt"

# while 条件循环
n=0
while [ "$n" -lt 3 ]; do
    n=$((n + 1))
done
```
常见错误：

- 算术写成 `n = n + 1`，应写 `n=$((n + 1))`
- `for f in $(ls ...)` 在文件名含空格时出错，直接 `for f in dir/*` 更好
- 没有空匹配保护，会把字面量 `*.csv` 当文件名处理

### 5. case 分支
```bash
ext="${1##*.}"      # 取文件名最后一个点后面的部分
case "$ext" in
    csv|tsv)  echo "表格数据" ;;
    json)     echo "结构化数据" ;;
    txt|log)  echo "文本数据" ;;
    *)        echo "未知类型: $ext" ;;
esac
```
模式支持通配符（`*.csv`、`[0-9]`），多个模式用 `|` 分隔，`;;` 结束一个分支。
常见错误：

- 每个分支结尾必须是 `;;`，最后用 `esac` 收尾
- case 匹配的是整个字符串，要写 `*.csv` 才能匹配 `data.csv`
- 忘记 `*)` 兜底分支，遇到意外输入时静默什么都不做

### 6. 函数

bash 函数只能通过 `return` 返回退出码（0~255），想返回字符串就用 `echo` 配合命令替换。
```bash
log() {
    echo "[$(date +%H:%M:%S)] $*"
}

check_dir() {
    local dir="$1"                  # local 让变量只在函数内有效
    if [ -d "$dir" ]; then
        return 0
    fi
    echo "目录不存在: $dir" >&2      # 错误信息写标准错误
    return 1
}

log "开始整理"
if check_dir "$HOME/lab-data/raw"; then
    log "目录检查通过"
else
    log "目录检查失败"
fi
```
常见错误：

- 函数定义 `{` 后要有空格或换行，结尾 `}` 前要有分号或换行
- 忘了 `local`，函数内变量污染全局，后续代码行为诡异
- 用 `return "字符串"` 试图返回字符串，返回值只能是整数

### 7. 位置参数、`$@` 与退出码
```bash
# 用法: args_demo.sh <输入> [输出] ...
echo "脚本名: $0；参数个数: $#；第一个: $1"

src="${1:?用法: args_demo.sh <源目录> [目标目录]}"   # 没传参数就报错退出
dst="${2:-$HOME/lab-data/processed}"                  # 默认值

for arg in "$@"; do                 # 处理含空格的参数要用 "$@"
    echo "参数: $arg"
done
shift                               # 参数整体左移，用于解析完选项后处理剩余参数

grep -q "ERROR" run.log
echo $?                             # 0 表示找到，1 表示没找到
exit 0                              # 脚本自己的退出码：0 成功，非 0 失败
```
常见错误：

- 用 `$*` 会把参数拼成一个字符串，处理含空格参数要用 `"$@"`
- 在 `if` 里执行命令后又在外面检查 `$?`，中间命令会覆盖退出码
- 随手 `exit 0` 掩盖失败，导致上层调度无法发现错误

### 8. `set -euo pipefail`：让脚本尽早失败

正式脚本开头都加上这一行，配合 shebang 使用：
```bash
#!/usr/bin/env bash
set -euo pipefail
```
- `-e`：任何命令返回非 0 立即退出，不带着错误继续跑
- `-u`：引用未定义变量时报错退出，防止把变量名当字面量用
- `-o pipefail`：管道中任意一段失败，整条管道就算失败（否则只看最后一段）
常见错误：

- 单独的 `[ -e "$f" ]` 在 `-e` 下失败会退出脚本；要写成 `[ -e "$f" ] || continue`
- `-u` 下 `"$@"` 是安全的（bash 4.4+ 特殊处理），但 `$1` 直接用会报错
- 把 `set -e` 当万能保险：命令替换里的失败在部分场景仍不会终止脚本，关键步骤要显式判断

### 9. 通配符与文件名安全
```bash
for f in "$dir"/*; do
    [ -e "$f" ] || continue
    mv -- "$f" "$dst/"          # -- 防止文件名以 - 开头时被当成选项
done
```
三条铁律：

1. 所有变量引用都加双引号，尤其是文件名。
2. 命令中涉及用户提供的文件名时，在文件名前加 `--`。
3. 不要解析 `ls` 的输出，需要遍历用通配符或 `find -print0`。
常见错误：

- `for f in $dir/*.csv`（dir 没加引号），目录名含空格时直接散架
- 用 `rm $f` 删含空格的文件，实际删掉了别的文件
- 在脚本里 `cd $dir || exit`，应写 `cd "$dir" || exit 1`

### 10. Shell 与 Python 的分工
| 任务 | 首选 |
| --- | --- |
| 遍历文件、调用其他程序、环境准备、定时任务 | Shell |
| 字符串处理、复杂条件、数据统计、生成报告 | Python |
| CSV/JSON 解析、去重、哈希、日志格式化 | Python |
| 打包、权限、进程管理 | Shell |
经验法则：脚本超过约 100 行、需要嵌套数据结构或复杂错误处理时，把核心逻辑放进 Python，
Shell 只保留「调度和文件流转」。本阶段项目就是这种结构：Shell 负责准备数据、调用、归档，
Python 负责扫描、分类、去重与报告。
常见错误：

- 用 Shell 手搓复杂 JSON/CSV 处理，越写越脆弱
- 两边重复实现同一逻辑，后期改一处忘一处

### 11. 综合示例：四个实用脚本

**脚本一：批量重命名实验数据**（run1_data.csv -> run01_data.csv）
```bash
#!/usr/bin/env bash
# 用法: rename_runs.sh <目录>
set -euo pipefail
dir="${1:?用法: rename_runs.sh <目录>}"
for f in "$dir"/run[0-9]_*.csv; do
    [ -e "$f" ] || continue
    base=$(basename -- "$f")
    new=$(printf '%s\n' "$base" | sed -E 's/^run([0-9])_/run0\1_/')
    if [ "$base" != "$new" ]; then
        mv -- "$f" "$dir/$new"
        echo "重命名: $base -> $new"
    fi
done
```
**脚本二：按修改日期归档**
```bash
#!/usr/bin/env bash
# 用法: archive.sh <源目录> [归档目录]
set -euo pipefail
src="${1:?用法: archive.sh <源目录> [归档目录]}"
dst="${2:-$HOME/lab-data/archive}"
count=0
for f in "$src"/*; do
    [ -f "$f" ] || continue
    month=$(date -r "$f" +%Y-%m)
    mkdir -p "$dst/$month"
    mv -- "$f" "$dst/$month/"
    count=$((count + 1))
done
echo "已归档 $count 个文件到 $dst"
```
**脚本三：生成文件清单**（大小 + 路径，按大小降序）
```bash
#!/usr/bin/env bash
# 用法: manifest.sh <目录> [输出文件]
set -euo pipefail
dir="${1:?用法: manifest.sh <目录> [输出文件]}"
out="${2:-manifest.tsv}"
find "$dir" -type f -printf '%s\t%p\n' | sort -nr > "$out"
echo "清单已写入 $out，共 $(wc -l < "$out") 个文件"
```
**脚本四：简单参数解析**（getopts）
```bash
#!/usr/bin/env bash
# 用法: topfiles.sh [-n 数量] [-d 目录] -> 列出目录中最大的 N 个文件
set -euo pipefail
count=5
dir="."
while getopts ":n:d:h" opt; do
    case "$opt" in
        n) count="$OPTARG" ;;
        d) dir="$OPTARG" ;;
        h) echo "用法: $0 [-n 数量] [-d 目录]"; exit 0 ;;
        \?) echo "未知选项: -$OPTARG" >&2; exit 1 ;;
        :)  echo "选项 -$OPTARG 需要一个参数" >&2; exit 1 ;;
    esac
done
find "$dir" -type f -printf '%s\t%p\n' | sort -nr | head -n "$count"
```
常见错误：

- 先写完整脚本再调试，一次引入多个错误；应一小段一运行，逐步添加
- 脚本里硬编码 `/home/you/lab-data`，换机器就坏；用参数与默认值
- 执行破坏性操作前不打印「将要做什么」，项目里用 `--dry-run` 解决

## 练习

1. 基础：把 `hello.sh` 改成接收一个名字参数，输出「你好，<名字>」；不传参数时给出用法提示并退出码 1。
   提示：`${1:?用法: ...}`、`exit 1`。
   验收：`bash hello.sh` 与 `bash hello.sh 王晨暄` 结果正确，`echo $?` 分别是 1 和 0。

2. 统计：写脚本统计一个目录中每种扩展名的文件数量，按数量降序输出。
   提示：`for f in "$dir"/*` 配合 `"${f##*.}"`、`case`，再用 `sort | uniq -c | sort -nr`。
   验收：对项目 `sample-data` 目录运行，输出不少于 3 行「数量 扩展名」。

3. 参数：写 `backup.sh <目录>`，把目录打包成 `目录名-日期.tar.gz`，完成后打印压缩包大小。
   提示：`tar -czvf`、`date +%Y-%m-%d`、`du -h`、`basename`。
   验收：打印的大小与 `du -h` 一致，重复运行不会报错。

4. 安全：写脚本给一个目录下所有文件加前缀 `exp_`，默认只打印将执行的操作，加 `--run` 才真正执行；
   文件名含空格也要正常工作。
   提示：`while getopts` 或 `case "${1:-}"`、`[ -e "$f" ] || continue`。
   验收：先用含空格文件名测试预览，输出与真正执行后的结果一致。

5. 综合：把脚本二（按日期归档）改造成支持 `-s 源目录 -d 目标目录 -n`（只预览）。
   提示：`getopts ":s:d:nh"`，把 `mv` 替换为「预览时 echo，执行时才 mv」。
   验收：对一个含 5 个以上文件的目录预览，再实际执行，结果与预览一致。

## 自测清单

- [ ] 我能写出带 shebang 与 `set -euo pipefail` 的脚本并赋予执行权限
- [ ] 我知道 `"$var"`、`'$var'`、`$var` 的区别，默认用双引号
- [ ] 我会用 `$( )` 做命令替换、`$(( ))` 做算术
- [ ] 我会用 `[ ]` 与 `[[ ]]` 判断文件、字符串、数字，并注意空格
- [ ] 我会用 for 遍历文件、while 按行读文件、case 与函数
- [ ] 我会用 `${1:?}`、`${2:-默认值}` 处理位置参数，用 `"$@"` 传递参数
- [ ] 我理解退出码 `$?` 与 `exit N`，知道在 `-e` 下哪些写法会意外退出
- [ ] 我的脚本能正确处理含空格、以 `-` 开头的文件名
- [ ] 我能判断一个任务该用 Shell 还是 Python 实现
- [ ] 我写破坏性脚本时一定先做 dry-run 或先备份

## 参考资料

- GNU Bash 参考手册：https://www.gnu.org/software/bash/manual/bash.html
- Bash 官方手册（man 页入口）：https://man7.org/linux/man-pages/man1/bash.1.html
- GNU Coreutils 手册（date/find/sort/head 等命令行为）：https://www.gnu.org/software/coreutils/manual/coreutils.html
