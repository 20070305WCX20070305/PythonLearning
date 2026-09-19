# 03-multiprocessing 与 subprocess

## 学习目标

- 理解 GIL，会判断任务属于 CPU 密集还是 IO 密集
- 会用 ProcessPoolExecutor 的 submit / map / imap 并行处理一批文件
- 会根据核数选择进程数，理解 pickle 对参数与返回值的限制
- 会收集结果、隔离单个文件的异常，并用 tqdm 显示进度
- 会用 subprocess.run / Popen 安全地调用外部程序
- 完成一个并行处理一批实验 CSV 的完整小工具

## 前置知识

- Python 基础语法、函数、文件读写（txt/json/csv）
- 阶段 01：Linux 命令行（`nproc` 等）、pathlib、logging、argparse、pytest
- 第三方库 tqdm：`pip install tqdm`（装进项目的 .venv）

## 建议用时

6~9 小时。把综合示例完整敲一遍，并在自己的机器上对比串行与并行的耗时。

## 正文

### 1. GIL 与两类任务

CPython 解释器有一把全局锁（GIL）：同一时刻只允许一个线程执行 Python 字节码，
所以多线程做纯计算时线程轮流抢锁，总耗时几乎不变。线程只在「等待」时有价值：
等磁盘、等网络、等仪器应答时 GIL 会被释放。判断标准是时间花在计算还是等待：
计算多用多进程，等待多用线程 / 进程 / 异步。
```python
import time
from concurrent.futures import ThreadPoolExecutor

def count_squares(n: int) -> int:
    """纯计算的 CPU 密集任务：累加平方和。"""
    total = 0
    for i in range(n):
        total += i * i
    return total

if __name__ == "__main__":
    tasks = [2_000_000] * 4
    start = time.perf_counter()                    # 串行
    for n in tasks:
        count_squares(n)
    serial = time.perf_counter() - start
    start = time.perf_counter()                    # 4 个线程
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(count_squares, tasks))
    threaded = time.perf_counter() - start
    print(f"串行: {serial:.2f} s，4 线程: {threaded:.2f} s")
    # 输出示例（i5-13420H）: 串行: 1.62 s，4 线程: 1.61 s
```
常见错误：

- 用多线程做批量数值计算，发现一点没变快，还以为是代码写错了
- 任务只有几十毫秒也开进程池，进程启动与 pickle 的开销超过收益

### 2. 进程与进程数：不要盲目开 100 个

进程之间内存独立、各自有解释器与 GIL，能真正并行使用多核。
```bash
nproc          # WSL2 输出 12；i5-13420H 是 8 核 12 线程
```
选择经验：CPU 密集从 `os.cpu_count()` 或 `os.cpu_count() - 1` 起步；
IO 密集可略多，但文件读写受磁盘限制；绝不要 `max_workers=100`——
12 个核同时只跑 12 个，其余进程排队还各自占用内存（一套解释器与数据副本）。
拿不准就做 A/B 对比，选耗时最低的进程数。
常见错误：

- 进程数写死 100，24 GB 内存被几十份数据副本吃光
- 每个文件都创建一个进程池，启动开销巨大；应创建一个池提交一批任务
- 忘记 `with` 或异常退出，进程没被回收

### 3. ProcessPoolExecutor：submit / map / imap

```python
import time
from concurrent.futures import ProcessPoolExecutor

def count_squares(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total

def main() -> None:
    tasks = [2_000_000] * 4
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as pool:      # 建一次，复用
        results = list(pool.map(count_squares, tasks))
    print("用时: %.2f s，结果个数: %d"
          % (time.perf_counter() - start, len(results)))

if __name__ == "__main__":        # 必须：不能 import 时就创建进程池
    main()
# 输出示例: 用时: 0.47 s，结果个数: 4
```
`submit` 立即返回 future；`map` 按输入顺序返回；`imap` 谁先完成谁先出：
```python
with ProcessPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(count_squares, n) for n in tasks]
    for fut in futures:
        fut.result()                    # 需要时再等，按提交顺序
with ProcessPoolExecutor(max_workers=4) as pool:
    for value in pool.imap(count_squares, tasks, chunksize=1):
        print(value)                    # 边完成边处理
```
常见错误：

- 忘记 `if __name__ == "__main__"` 保护，Windows/macOS 上进程池会递归启动自身
- worker 里 print / 改全局变量，父进程看不到（进程内存独立）
- 任务太碎（每个 1 ms）时进程间通信开销大于计算本身，可给 `chunksize`

### 4. 异常传播与任务隔离

worker 抛出的异常随 future 传回父进程，在 `result()` 处重新抛出。
```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
# 先造两个测试文件，让本节示例可以单独运行
Path("run_001.csv").write_text("0,300.0\n1,250.0\n", encoding="utf-8")
Path("empty.csv").write_text("", encoding="utf-8")

def read_temperature(path_str: str) -> float:
    path = Path(path_str)
    with path.open(encoding="utf-8") as f:
        first_line = f.readline()
    if not first_line.strip():
        raise ValueError(f"空文件: {path.name}")
    return float(first_line.split(",")[1])

def safe_parse(path_str: str) -> tuple:
    """worker 内部消化异常，返回 (路径, 结果, 错误)。"""
    try:
        return path_str, read_temperature(path_str), None
    except Exception as exc:          # 兜底，保留类型与文件名
        return path_str, None, f"{type(exc).__name__}: {exc}"

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2) as pool:
        good = pool.submit(read_temperature, "run_001.csv")
        bad = pool.submit(read_temperature, "empty.csv")
        print(good.result())                      # 300.0
        try:
            bad.result()                          # 子进程异常在此重抛
        except ValueError as exc:
            print("任务失败:", exc)               # 任务失败: 空文件: empty.csv
        print(safe_parse("empty.csv")[2])         # ValueError: 空文件: empty.csv
```
原则：批量任务里一个坏文件不能炸掉整批，让 worker 返回结构化结果、父进程
统一记录；确实需要中断（配置写错等）时就让异常抛出来，用 `logging.exception`
保留 traceback。
常见错误：

- worker 里 `except Exception: pass`，坏文件被静默忽略，报告数量对不上
- 父进程只打印 `exc`，丢了异常类型与文件名
- 一个文件失败就 `sys.exit`，其余几百个文件白算

### 5. pickle 限制：什么能跨进程传递

进程间传递的函数、参数、返回值都要被 pickle 序列化。列表/元组/字典/集合、
数字、字符串、`pathlib.Path`、numpy 数组都可以；打开的文件对象、数据库连接、
`lambda`、生成器都不行。worker 必须是模块顶层可 import 的函数。
```python
import pickle
from pathlib import Path

def is_picklable(obj) -> bool:
    try:
        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, TypeError, AttributeError):
        return False
print(is_picklable({"file": "run_001.csv", "mean": 25.3}))   # True
print(is_picklable(Path("run_001.csv")))                     # True
print(is_picklable(lambda x: x))                             # False
```
Linux 用 fork 时嵌套函数可能侥幸能跑，但换平台或 Python 版本就报错，
一律按可移植写法。
常见错误：

- worker 返回文件对象或 sqlite3 连接，父进程报 `TypeError`
- 大数组在进程间反复传输；更省事的做法是 worker 自己读文件、只传回小统计

### 6. tqdm 与并行

进度条只能在父进程更新：用 `as_completed` 谁先完成先计数。
```python
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
paths = [f"run_{i:03d}.csv" for i in range(1, 101)]
results, errors = [], []
with ProcessPoolExecutor(max_workers=8) as pool:
    futures = {pool.submit(safe_parse, p): p for p in paths}
    with tqdm(total=len(futures), desc="解析 CSV", unit="个") as pbar:
        for future in as_completed(futures):
            path_str, stats, error = future.result()
            if error is None:
                results.append(stats)
            else:
                errors.append((path_str, error))
            pbar.update(1)
print(f"成功 {len(results)}，失败 {len(errors)}")
# 输出示例: 解析 CSV: 100%|██████████| 100/100 [00:02<00:00, 38.5个/s]
```
`tqdm(pool.map(...), total=len(paths))` 也能用，但 `map` 按输入顺序产出，
慢任务会拖住进度；`imap_unordered` 则谁先完成谁先出。
常见错误：

- 在 worker 里更新进度条，子进程各画一条，输出全乱
- 没给 `total`，进度条不显示百分比与预计剩余时间

### 7. subprocess：安全地调用外部程序

压缩归档、仪器厂商自带的 CLI、格式转换工具，交给现成命令往往更省事。
```python
import subprocess
result = subprocess.run(
    ["df", "-h", "/"],          # 参数列表：程序名 + 逐个参数
    capture_output=True,        # 捕获 stdout/stderr
    text=True,                  # 解码成 str
    timeout=30,                 # 超时抛 TimeoutExpired 并终止子进程
    check=False,                # 不自动抛异常，自己检查 returncode
)
print("返回码:", result.returncode)      # 0 成功，非 0 失败
print(result.stdout)
try:
    subprocess.run(["sleep", "5"], timeout=1, check=True)
except subprocess.TimeoutExpired:
    print("命令超时，已终止")
except subprocess.CalledProcessError as exc:
    print("命令失败:", exc.returncode, exc.stderr)
```
`shell=True` 会把字符串交给 shell 解释，文件名里的空格、引号、分号都可能
被执行，存在注入风险；优先用列表形式：
```python
name = "data 2026; rm -rf ~.csv"                  # 假设来自不可信输入
# subprocess.run(f"wc -l {name}", shell=True)      # 危险，不要写
subprocess.run(["wc", "-l", name], check=False)    # 安全，shell 不解释参数
```
需要实时读取输出（日志跟随、长时间采集）时用 `Popen` 逐行读：
```python
proc = subprocess.Popen(["tail", "-f", "acquisition.log"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1)
for line in proc.stdout:            # 逐行读，不会占满内存
    print("实时:", line.rstrip())
    if "SCAN_DONE" in line:
        proc.terminate()            # 主动结束
        break
proc.wait()                         # 回收子进程，避免僵尸
```
常见错误：

- 用 `shell=True` 拼接用户输入的文件名或参数
- 不设 `timeout`，外部程序卡死时脚本永远挂住
- 只看 stdout 不看 `returncode`；不 `wait()` 产生僵尸进程；
  命令不存在时忘记处理 `FileNotFoundError`

### 8. 综合示例：并行处理一批 CSV

`parallel_csv.py`：发现文件、并行解析、加权汇总、进度条、错误隔离、JSON 报告。
数据用阶段项目里的 `starter/gen_data.py` 生成。
```python
# parallel_csv.py
"""并行统计一批实验 CSV：点数、温度均值与极值。"""
import argparse
import csv
import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from tqdm import tqdm

def parse_file(path_str: str) -> dict:
    """解析单个 CSV（子进程执行，参数与返回值都会被 pickle）。"""
    path = Path(path_str)
    temps = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                temps.append(float(row["temperature_K"]))
            except (KeyError, ValueError):
                continue                                  # 跳过坏行
    if not temps:
        return {"file": path.name, "count": 0, "temp_mean": None}
    return {"file": path.name, "count": len(temps),
            "temp_mean": round(sum(temps) / len(temps), 3)}

def safe_parse(path_str: str) -> tuple:
    """把单个文件的异常挡在子进程内。"""
    try:
        return path_str, parse_file(path_str), None
    except Exception as exc:
        return path_str, None, f"{type(exc).__name__}: {exc}"

def main() -> int:
    parser = argparse.ArgumentParser(description="并行统计实验 CSV")
    parser.add_argument("input", type=Path, help="数据目录")
    parser.add_argument("--workers", type=int, default=0,
                        help="进程数，0 表示按核数自动")
    parser.add_argument("--out", type=Path, default=Path("summary.json"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    files = sorted(args.input.glob("*.csv"))
    if not files:
        logging.error("目录里没有 CSV: %s", args.input)
        return 1
    workers = args.workers or max(1, (os.cpu_count() or 2) - 1)
    logging.info("共 %d 个文件，使用 %d 个进程", len(files), workers)

    results, errors = [], []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(safe_parse, str(p)): p for p in files}
        with tqdm(total=len(futures), desc="解析 CSV", unit="个") as pbar:
            for future in as_completed(futures):
                path_str, stats, error = future.result()
                if error is None:
                    results.append(stats)
                else:
                    errors.append({"file": path_str, "error": error})
                    logging.warning("解析失败 %s: %s", path_str, error)
                pbar.update(1)

    ok = [r for r in results if r["count"] > 0]
    total_points = sum(r["count"] for r in ok)
    weighted = (sum(r["temp_mean"] * r["count"] for r in ok) / total_points
                if total_points else None)
    summary = {"files": len(files), "ok": len(ok), "failed": len(errors),
               "total_points": total_points,
               "temp_mean": round(weighted, 3) if weighted is not None else None,
               "details": results, "errors": errors}
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    logging.info("完成：%d 个文件，%d 个数据点，写入 %s",
                 len(ok), total_points, args.out)
    return 0

if __name__ == "__main__":        # 进程池必须在 __main__ 保护下创建
    raise SystemExit(main())
```
运行与输出示例：
```bash
python3 starter/gen_data.py --target sample-data --files 60 --rows 5000 --seed 42
python3 parallel_csv.py sample-data --workers 11
# 2026-03-15 21:03:11 [INFO] 共 60 个文件，使用 11 个进程
# 解析 CSV: 100%|██████████| 60/60 [00:00<00:00, 71.4个/s]
# 2026-03-15 21:03:12 [INFO] 完成：60 个文件，300000 个数据点，写入 summary.json
```
常见错误：

- 忘记 `raise SystemExit(main())`，退出码永远是 0，Shell 无法判断成败
- `Path.glob` 只匹配一层，子目录里的数据要用 `rglob("*.csv")`
- 报告只存均值不存点数，加权平均就没法算（示例故意保留 `count`）

## 练习

1. 任务分类：列出 5 个日常任务（如「下载 100 篇文献」「拟合 1 万条谱线」），
   标注 CPU / IO 密集并写出并行方式。提示：看时间花在计算还是等待；
   验收：能讲清每个选择的原因。
2. 计时对比：用 `count_squares` 做串行、4 线程、4 进程三个版本，打印耗时表。
   提示：`time.perf_counter`；验收：进程版明显快于串行，线程版与串行接近。
3. 异常隔离：给 `safe_parse` 增加「列缺失」与「空文件」两种情况，用 `tmp_path`
   写 pytest 用例，再加一条「好文件照常返回」的用例。
   提示：`pytest.approx`；验收：坏文件返回错误字符串，好文件返回统计，整批不中断。
4. subprocess：写函数 `run_command(args: list, timeout: float)`，返回
   `(returncode, stdout)`；命令不存在时捕获 `FileNotFoundError`，超时捕获
   `TimeoutExpired` 并返回特殊标记。提示：`check=False`、`text=True`；
   验收：`["nproc"]`、`["sleep", "5"]`（timeout=1）、`["no-such-cmd"]` 行为正确。
5. 综合：给 `parallel_csv.py` 增加 `--pattern`（默认 `*.csv`）与
   `--max-fail`（允许失败文件比例，超过则返回码 2），并为参数解析写测试。
   提示：`parse_args([...])`；验收：失败超阈值时返回码为 2，日志有失败清单。

## 自测清单

- [ ] 我能用自己的话解释 GIL，并说明为什么多线程对纯计算无效
- [ ] 我能迅速判断一个任务是 CPU 密集还是 IO 密集
- [ ] 我会用 `nproc` / `os.cpu_count()` 查核数，并据此选择进程数
- [ ] 我会写带 `if __name__ == "__main__"` 保护的进程池代码
- [ ] 我会用 `submit` + `as_completed` 收集结果，也会用 `map` / `imap`
- [ ] 我知道哪些对象可以 pickle，worker 函数必须放在模块顶层
- [ ] 我的批量任务能隔离单个文件的异常，并在报告里留下错误信息
- [ ] 我会用 tqdm 在父进程更新进度，并解释为什么不放在 worker 里
- [ ] 我会用 `subprocess.run` 的参数列表、`timeout` 与 `returncode`，理解 `shell=True` 的风险
- [ ] 我能把「并行处理一批 CSV」从头到尾写出来并解释每一步

## 参考资料

- concurrent.futures 官方文档：https://docs.python.org/3/library/concurrent.futures.html
- subprocess 官方文档：https://docs.python.org/3/library/subprocess.html
- tqdm 项目主页：https://pypi.org/project/tqdm
- tqdm 官方文档：https://tqdm.github.io

异步（asyncio）适合大量等待型任务，是下一篇 04 的主题。
