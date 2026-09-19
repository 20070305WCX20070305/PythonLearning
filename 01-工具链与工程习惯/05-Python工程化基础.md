# 05-Python工程化基础

## 学习目标

- 会用 venv 创建/激活/退出虚拟环境，用 pip 与 requirements.txt 管理依赖
- 会用 pathlib 写路径相关代码，不再拼接字符串路径
- 掌握 os / shutil / hashlib 常用函数，会做文件遍历、复制、哈希去重
- 会写 try/except/else/finally 与 raise，设计清晰的错误信息
- 会用 logging 替代 print：分级、时间、同时输出控制台与文件
- 会用 argparse 写规范的命令行工具
- 会把脚本拆成模块与函数，会用 `if __name__ == "__main__"`
- 会写函数式 pytest 测试，会使用参数化与 tmp_path

## 前置知识

- Python 基础语法、函数、文件读写（txt/json/csv）
- 01~04 课：Linux、Shell、Git 与远程会话基础
- 本课所有命令都在 WSL2 Ubuntu 24.04 中执行

## 建议用时

8~12 小时。建议边学边把项目骨架补全。

## 正文

### 1. venv 与依赖管理

系统 Python 被操作系统与其他工具共用，直接 `pip install` 会污染环境、造成版本冲突；
每个项目一个独立虚拟环境是标准做法。
```bash
cd ~/projects/data-organizer
python3 -m venv .venv              # 创建
source .venv/bin/activate          # 激活，提示符前出现 (.venv)
python -m pip install --upgrade pip
pip install pytest                 # 第三方依赖都装进 .venv
pip freeze > requirements.txt      # 冻结依赖版本
deactivate                         # 退出
# 重建环境：python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```
`.venv/` 不要提交进 Git（写进 .gitignore），`requirements.txt` 要提交。
常见错误：

- 忘记激活就 pip install，装进系统环境；用 `which python` 确认指向 `.venv/bin/python`
- 用 `sudo pip` 安装，这是把系统环境搅乱的最快方式
- 不写 requirements.txt，几天后自己都不知道装过哪些版本

### 2. pathlib：现代路径操作
```python
from pathlib import Path

data_dir = Path.home() / "lab-data" / "raw"    # / 运算符拼接，跨平台
print(data_dir)                                # /home/you/lab-data/raw
data_dir.mkdir(parents=True, exist_ok=True)    # 递归创建，已存在不报错

for p in sorted(data_dir.glob("*.csv")):       # 只找一层
    print(p.name, p.stat().st_size)
for p in sorted(data_dir.rglob("*.json")):     # 递归所有子目录
    print(p.relative_to(data_dir))             # 报告里显示相对路径更清晰

f = data_dir / "scan_001.txt"
f.write_text("温度=25.3\n", encoding="utf-8")   # 写文本必须显式指定编码
print(f.name, f.stem, f.suffix, f.parent)      # scan_001.txt scan_001 .txt 目录
```
常见错误：

- 读写中文不写 `encoding="utf-8"`，会出现乱码
- `p.parent.mkdir()` 忘了 `parents=True, exist_ok=True`
- 把 `glob("*")` 当递归，递归要用 `rglob` 或 `glob("**/*")`

### 3. os / shutil / hashlib 常用函数
```python
import hashlib
import shutil
from pathlib import Path

src = Path.home() / "lab-data/raw/scan_001.txt"
dst = Path.home() / "lab-data/processed/scan_001.txt"
shutil.copy2(src, dst)             # 复制文件并保留时间戳等元数据
shutil.move(str(src), str(dst))    # 移动/重命名，参数传字符串最稳（去重在项目里用）

def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """分块计算 SHA-256，大文件不会一次性读入内存。"""
    digest = hashlib.sha256()
    with path.open("rb") as f:     # 二进制模式读
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()

print(hash_file(dst))              # 内容相同则哈希相同，可据此去重
```
常见错误：

- 用文件名判断重复，同名文件内容可能不同；去重要用内容哈希
- 一次 `f.read()` 读几 GB 的大文件导致内存爆炸，必须分块；目标目录不存在时复制也会失败

### 4. 异常处理：try/except/else/finally 与 raise

原则：能处理的处理，处理不了就带着清晰信息抛出，绝不静默失败。
```python
from pathlib import Path

def read_value(path: Path) -> float:
    """读取单行测量值；失败时抛出带文件名的异常。"""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"数据文件不存在: {path}") from exc
    except OSError as exc:                 # 权限、磁盘等其他 IO 问题
        raise OSError(f"读取文件失败: {path} ({exc})") from exc
    else:
        return float(text.strip())         # 只有 try 成功才执行
    finally:
        print(f"已尝试读取: {path.name}")   # 无论成功失败都会执行

try:                                   # 调用方决定跳过还是退出
    value = read_value(Path("measurement.txt"))
except (FileNotFoundError, OSError) as exc:
    print(f"跳过: {exc}")
```
常见错误：

- `except:` 一把抓然后什么都不做，或只 print 不 raise，上层以为一切正常
- 错误信息不带文件名、数值等上下文，事后无法定位
- 本阶段只用内置异常类型（`ValueError`、`OSError`、`FileNotFoundError` 等）

### 5. logging：用日志替代 print

`print` 没有时间、级别与文件输出，标准库 logging 一次解决。
```python
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,          # 常见级别：DEBUG<INFO<WARNING<ERROR
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),                                # 控制台
        logging.FileHandler("organizer.log", encoding="utf-8"), # 文件
    ],
)
logging.debug("调试信息，排错时才需要")
logging.info("扫描目录: %s", Path.home() / "lab-data")
# 输出示例: 2026-03-15 21:03:11 [INFO] root: 扫描目录: /home/you/lab-data
try:
    (Path("nope") / "x.txt").read_text(encoding="utf-8")
except OSError:
    logging.exception("读取失败")     # 自动附带 traceback，适合 except 内使用
```
需要自定义时间格式时用 `logging.Formatter` 配 `datefmt="%Y-%m-%d %H:%M:%S"`；
`-v` 开关控制级别：`level=logging.DEBUG if verbose else logging.INFO`。
常见错误：

- 循环里对每个文件都 INFO 输出，应 INFO 记摘要、DEBUG 记细节
- print 与 logging 混用，输出格式混乱
- `logging.exception` 用在 `except` 块之外，拿不到 traceback

### 6. argparse：命令行参数
```python
import argparse
from pathlib import Path

def parse_args(argv=None):
    """解析参数；argv 为 None 时读取 sys.argv[1:]，便于测试。"""
    parser = argparse.ArgumentParser(description="整理实验数据文件：分类、去重、生成报告")
    parser.add_argument("source", type=Path, help="待整理的源目录")
    parser.add_argument("--dest", type=Path, default=Path("organized"),
                        help="输出目录（默认 organized）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只预览，不实际复制/移动")
    return parser.parse_args(argv)

if __name__ == "__main__":
    args = parse_args()
    print(args.source, args.dest, args.dry_run, args.verbose)
```
`python organizer.py --help` 会自动列出全部参数、默认值与帮助文本。
`type=Path` 自动把字符串转成 Path；`action="store_true"` 表示开关参数；
把 `argv` 作为参数传入，测试时能传假参数列表，不必改 `sys.argv`。
常见错误：

- 参数名用中文、空格，命令行难用；用短横线连接的小写英文
- 忘记 `action="store_true"`，写出 `--dry-run 1` 这种别扭用法
- 在函数里直接读全局 `sys.argv`，导致无法测试
- 破坏性操作是默认行为且没有 `--dry-run`，一条命令误删数据

### 7. 代码组织：模块与 `if __name__ == "__main__"`

一个 `.py` 文件就是一个模块，可以被别的文件 `import`。可复用的写法：
```python
# organizer.py
"""实验数据文件整理工具（本文件是一个可复用模块）。"""
import logging
from pathlib import Path

DEFAULT_RULES = {".csv": "tables", ".json": "structured", ".txt": "text"}

def classify_by_extension(path: Path, rules=None) -> str:
    """根据扩展名返回分类名，未命中返回 other。"""
    active = DEFAULT_RULES if rules is None else rules
    return active.get(path.suffix.lower(), "other")

def main(argv=None) -> int:
    """程序入口，返回退出码。"""
    args = parse_args(argv)
    logging.info("准备整理 %s", args.source)
    return 0

if __name__ == "__main__":     # 只有直接运行本文件才执行
    raise SystemExit(main())
```
好处：其他脚本可以 `from organizer import classify_by_extension`，测试能直接调用函数；
`python organizer.py` 仍然是命令行工具。
常见错误：

- 没有 `__main__` 保护，模块一被 import 就执行抓数据、发请求等副作用
- 所有逻辑堆在 `main` 里，应把可独立测试的逻辑拆成纯函数
- 文件与标准库重名（`json.py`、`logging.py`），import 会指向错误文件

### 8. pytest 入门

pytest 把 `test_` 开头的函数当作用例，直接 `assert`，失败时打印详细差异。
```python
# tests/test_organizer.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "starter"))

import pytest
from data_organizer import classify_by_extension, hash_file

@pytest.mark.parametrize(
    ("name", "expected"),
    [("a.txt", "text"), ("b.CSV", "tables"), ("c.json", "structured")],
)
def test_classify_param(name, expected):
    assert classify_by_extension(Path(name)) == expected

def test_hash_same_content(tmp_path):
    """tmp_path 是 pytest 提供的临时目录，每个用例一个，互不干扰。"""
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("温度=25.3\n", encoding="utf-8")
    b.write_text("温度=25.3\n", encoding="utf-8")
    assert hash_file(a) == hash_file(b)
```
```bash
pytest -q                          # 简洁模式（-v 详细模式、-k 按名字筛选用例）
pytest -v tests/test_organizer.py  # 指定文件运行
```

一个用例只测一件事；边界情况（空目录、重名、大写扩展名）单独写用例。
常见错误：

- 测试函数名不以 `test_` 开头，pytest 直接忽略
- 依赖本机已有文件（如 `~/lab-data`），换机器就失败；用 `tmp_path` 造数据
- 忘记把被测模块所在目录加入 `sys.path`，import 报 ModuleNotFoundError

### 9. 重构示例：脚本到可复用模块

**重构前**：逻辑混在一起，无法测试与复用。
```python
# 坏味道版本：统计 txt 文件行数
from pathlib import Path
import sys
src = Path(sys.argv[1])
total = 0
for p in src.glob("*.txt"):
    lines = p.read_text(encoding="utf-8").splitlines()
    total += len(lines)
print("总行数:", total)
```
**重构后**：纯函数 + 入口 + 日志，可测试、可复用。
```python
# line_counter.py
"""统计目录下 txt 文件行数的小工具。"""
import argparse
import logging
from pathlib import Path

def count_lines(path: Path) -> int:
    """返回文件行数（空行也算）。"""
    return len(path.read_text(encoding="utf-8").splitlines())

def count_dir(src: Path) -> dict:
    """返回 {文件名: 行数}，按名字排序。"""
    return {p.name: count_lines(p) for p in sorted(src.glob("*.txt"))}

def parse_args(argv=None):     # 与第 6 节相同：位置参数 source（实现略）
    ...

def main(argv=None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    counts = count_dir(args.source)
    logging.info("共 %d 个文件，%d 行", len(counts), sum(counts.values()))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```
`count_lines`、`count_dir` 现在都能被测试与其他脚本直接调用；项目的 `data_organizer.py`
采用同样的结构：每个函数单独可测，`main` 只负责编排。
常见错误：

- 重构时一次改太多、行为也变了；应「输入输出不变，只改结构」，改完立刻跑测试
- 函数职责过多（读文件 + 打印 + 统计混在一起），拆到单一职责为止
- 不给重构后的代码补测试，下次改动没有安全网

## 练习

1. 环境：为项目创建 `.venv`，安装 pytest，生成 `requirements.txt`，写出「删除后再重建」的命令序列。
   提示：`python3 -m venv .venv`、`pip freeze`、`pip install -r`；验收：`which python` 指向 `.venv/bin/python`，`requirements.txt` 已提交 Git。
2. pathlib：写函数 `list_by_suffix(root: Path, suffix: str) -> list[Path]`，
   返回 root 下（含子目录）所有指定扩展名文件，按路径排序。
   提示：`rglob(f"*{suffix}")`、`sorted`；验收：对 `sample-data` 的结果与 `find sample-data -name "*.csv" | wc -l` 一致。
3. 异常与日志：给 `hash_file` 加错误处理：文件不存在时抛出带路径的 `FileNotFoundError`；
   调用方用 logging 记录错误并继续处理下一个文件。
   提示：`try/except`、`raise ... from exc`、`logging.exception`；验收：输入含一个不存在文件与一个正常文件，日志有一条 ERROR 且正常文件仍被处理。
4. argparse 与 pytest：为统计脚本添加 `source`、`--dry-run`、`-v` 三个参数，
   并写测试 `parse_args(["--dry-run", "-v", "some-dir"])` 的断言。
   提示：`action="store_true"`、`argv` 参数化；验收：`--help` 列出全部参数，测试通过。
5. 测试：为 `count_dir` 写 3 个用例：两个正常文件、空目录、含非 txt 文件不统计；
   用 `tmp_path` 构造数据，至少一个用例使用参数化。
   提示：`tmp_path / "a.txt"`、`write_text`、`@pytest.mark.parametrize`；验收：`pytest -v` 全部通过，改错期望值能看到清晰失败信息。

## 自测清单

- [ ] 我能用一条命令序列在新机器上重建虚拟环境
- [ ] 我读写文本都显式指定 `encoding="utf-8"`
- [ ] 我会用 pathlib 拼接、遍历、读写，会用分块哈希处理大文件
- [ ] 我的异常信息包含文件名、数值等定位信息，且不吞异常
- [ ] 我用 logging 同时写控制台与文件，级别使用合理
- [ ] 我会用 argparse 写位置参数、默认值、开关与帮助文本
- [ ] 我的脚本有 `main` 与 `if __name__ == "__main__"`，逻辑拆成纯函数
- [ ] 我会用 pytest 写测试，会用 tmp_path 与 parametrize，并做过一次脚本重构

## 参考资料

- Python 官方教程（虚拟环境与包管理）：https://docs.python.org/zh-cn/3/tutorial/venv.html
- pathlib 官方文档：https://docs.python.org/zh-cn/3/library/pathlib.html
- logging 官方指南：https://docs.python.org/zh-cn/3/howto/logging.html
- argparse 官方文档：https://docs.python.org/zh-cn/3/library/argparse.html
- hashlib 官方文档：https://docs.python.org/zh-cn/3/library/hashlib.html
- pytest 官方文档：https://docs.pytest.org/en/stable/

面向对象（class）、自定义异常与更复杂的工程组织会在阶段 05 展开。
