# 04-asyncio 与系统监控

## 学习目标

- 分清同步、异步与并发，会判断何时用 asyncio、何时用多进程
- 理解事件循环，会写 `async def` / `await` / `asyncio.run`
- 会用 `gather` 与 `create_task` 并发任务，用 `wait_for` 控制超时
- 会用 `asyncio.subprocess` 调外部命令、用 `asyncio.to_thread` 包装阻塞函数
- 会用 psutil 采集资源并写 CSV，会把 tqdm 与异步任务配合
- 完成「异步并发读取多个大文件并统计」的综合示例

## 前置知识

- 阶段 01：文件读写、logging、argparse、pytest 基础
- 03 课：CPU 密集 / IO 密集、进程与并行的基本概念
- 第三方库 psutil 与 tqdm：`pip install psutil tqdm`

## 建议用时

6~8 小时。语法不多，难在「什么时候该用」以及不把事件循环堵住。

## 正文

### 1. 同步、异步与并发：该选哪一个

同步像只有一个服务员的餐厅：给 1 号桌点完菜，站着等厨房做好才去 2 号桌；
异步是一次给十桌点完菜，谁做好去端谁——只有一个线程，但等待时间全被利用。
纯计算用多进程（03 课）；少量并发等待用线程或 `to_thread`；大量并发等待
（上百个请求、上百个通道）用 asyncio；混合场景可以 asyncio + 进程池。
```python
import asyncio
import time

async def measure(name: str, seconds: float) -> str:
    await asyncio.sleep(seconds)        # 只让出等待时间，不阻塞别人
    return f"{name} 完成"

async def main() -> None:
    start = time.perf_counter()
    results = await asyncio.gather(
        measure("通道A", 1.0), measure("通道B", 1.0), measure("通道C", 1.0))
    print(results, f"总耗时 {time.perf_counter() - start:.2f} s")
asyncio.run(main())
# 输出示例: ['通道A 完成', '通道B 完成', '通道C 完成'] 总耗时 1.01 s
```
常见错误：

- 以为 asyncio 能让单个任务变快；它只能让等待时间重叠
- 在异步函数里调用 `requests.get` / `time.sleep` 把事件循环整个卡住

### 2. 事件循环与 async def / await / asyncio.run

事件循环是 asyncio 的调度器：遇到 `await` 就切到别的任务。`async def` 定义
协程函数，调用它不会执行，只返回协程对象，必须交给事件循环。
```python
import asyncio

async def read_temperature() -> float:
    print("开始采集")
    await asyncio.sleep(1)          # 模拟仪器通信等待
    return 25.3
coro = read_temperature()           # 只是协程对象，不会执行
print(coro)                         # <coroutine object read_temperature ...>
print(asyncio.run(read_temperature()))
# 输出示例: <coroutine object ...> / 开始采集 / 25.3
```
`asyncio.run` 从同步入口调用一次，自动创建并关闭事件循环，不要在它里面再调用。
常见错误：

- 忘记 `await`，出现 `RuntimeWarning: coroutine was never awaited`
- 在 `async def` 里用 `time.sleep(1)`，应写 `await asyncio.sleep(1)`
- 在已运行的循环里（如 Jupyter）再 `asyncio.run`，报 loop is already running

### 3. 并发多个任务：gather 与 create_task

`gather` 的结果顺序与传入顺序一致；`create_task` 立即把协程排进循环，
可以先去干别的事再回来 `await`。
```python
import asyncio

async def read_channel(name: str, n: int) -> tuple:
    total = 0.0
    for _ in range(n):
        await asyncio.sleep(0.01)       # 模拟每次通信等待
        total += 1.0
    return name, total

async def main() -> None:
    results = await asyncio.gather(
        read_channel("A", 10), read_channel("B", 10), read_channel("C", 10))
    for name, total in results:
        print(name, total)              # A 10.0 / B 10.0 / C 10.0
    task = asyncio.create_task(read_channel("D", 5))   # 立即开始调度
    await asyncio.sleep(0.02)                          # 主流程先做别的事
    print("后台任务完成:", await task)
asyncio.run(main())
```
一个任务抛异常会让 `gather` 立刻抛错；想让异常变成结果、不影响别人，
加 `return_exceptions=True`，之后用 `isinstance(item, Exception)` 判断。
常见错误：

- `create_task` 后不保存返回值，任务可能被垃圾回收提前取消
- 忘记 `await task`，主协程结束后台任务被取消

### 4. 超时控制：wait_for

```python
import asyncio

async def slow_read() -> str:
    await asyncio.sleep(5)
    return "数据"

async def main() -> None:
    try:
        value = await asyncio.wait_for(slow_read(), timeout=1.0)
        print("读到:", value)
    except asyncio.TimeoutError:
        print("读取超时，准备重试")     # 重试与退避留给练习完成
asyncio.run(main())
# 输出示例: 读取超时，准备重试
```
超时后会取消内部任务并抛出 `asyncio.TimeoutError`（3.11 起是内置
`TimeoutError` 的别名）；重试时用有限次数与逐渐加长的间隔。
常见错误：

- 超时设得比任务正常耗时还短，把正常任务都取消
- 超时后以为原任务还在跑；它已被取消，资源会自动回收

### 5. asyncio.subprocess：异步调用外部命令

```python
import asyncio

async def run_cmd(*args: str) -> tuple:
    """异步执行命令，返回 (returncode, stdout, stderr)。"""
    proc = await asyncio.create_subprocess_exec(
        *args,                          # 参数列表形式，不用 shell 字符串
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()               # 回收，避免僵尸
        raise
    return proc.returncode, stdout.decode(), stderr.decode()

async def main() -> None:
    print(await run_cmd("nproc"))                  # (0, '12\n', '')
    results = await asyncio.gather(                # 多个命令并发
        run_cmd("df", "-h", "/"), run_cmd("uname", "-r"))
    for code, out, err in results:
        print(code, out.strip().splitlines()[0])
asyncio.run(main())
```
`create_subprocess_shell` 与 `shell=True` 一样有注入风险，优先用参数列表。
常见错误：

- 写成 `create_subprocess_exec(["nproc"])`，多套了一层列表（应写 `*args`）
- 不加超时，命令卡住整条流水线
- 用 `proc.stdout.read()` 读大量输出导致死锁；用 `communicate()`

### 6. asyncio.to_thread：把阻塞函数挪进线程

已有的同步函数（读文件、`requests.get`）不想重写时，用 `to_thread`
丢进线程池，事件循环就不会被堵住。
```python
import asyncio
from pathlib import Path

def read_stats(path: Path) -> dict:
    """同步阻塞的读取与统计（沿用阶段 01 的写法）。"""
    text = path.read_text(encoding="utf-8")
    return {"file": path.name, "lines": len(text.splitlines())}

async def main() -> None:
    files = [Path(f"run_{i:03d}.csv") for i in range(1, 5)]   # 假设存在
    results = await asyncio.gather(
        *(asyncio.to_thread(read_stats, p) for p in files))
    for item in results:
        print(item)
asyncio.run(main())
```
`to_thread` 只解决等待型阻塞；CPU 密集函数放进去仍受 GIL 限制，应交给进程池。
常见错误：

- 在 `async def` 里直接调用 `read_stats(p)`，一个文件卡住所有任务
- 把大量浮点运算塞进 `to_thread`，线程被 GIL 串行化，白忙
- 线程里修改全局变量，多线程下顺序不确定

### 7. psutil：系统监控与 CSV 采样日志

长时间批处理时记录资源占用，事后能解释「为什么变慢」。
```python
import csv
import time
from datetime import datetime
from pathlib import Path
import psutil

def sample_once() -> dict:
    """采集一次系统状态（CPU、内存、磁盘），返回一行数据。"""
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "mem_percent": vm.percent,
        "mem_used_gb": round(vm.used / 1024 ** 3, 2),
        "disk_free_gb": round(disk.free / 1024 ** 3, 1),
    }

def monitor(duration_s: int, interval_s: float, out_path: Path) -> None:
    """按固定间隔采样 duration_s 秒，写入 CSV。"""
    fields = ["time", "cpu_percent", "mem_percent", "mem_used_gb",
              "disk_free_gb"]
    psutil.cpu_percent(interval=None)      # 第一次调用只初始化，返回 0.0
    time.sleep(0.1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        end = time.monotonic() + duration_s
        while time.monotonic() < end:
            row = sample_once()
            writer.writerow(row)
            f.flush()                       # 及时落盘，进程被杀也不丢数据
            print(row)
            time.sleep(interval_s)
```
查单个进程用 `psutil.Process(os.getpid())`，它的 `memory_info().rss`
是进程常驻内存；遍历全系统进程用
`psutil.process_iter(["pid", "name", "memory_info"])`，注意捕获
`psutil.NoSuchProcess` 与 `psutil.AccessDenied`（进程刚好退出或没权限）。
常见错误：

- 把 `psutil.cpu_percent(interval=1)` 写进异步循环，阻塞整整 1 秒
- 不开 `flush()`，监控日志缺最后几行，恰好是关键数据
- 用 `vm.used / 1e9` 当 GB（实际是 GiB 与 GB 的差别）

### 8. tqdm 与异步的简单配合

进度条在协程完成时更新即可；用包装协程把「await + update」绑在一起。
```python
import asyncio
from tqdm import tqdm

async def tracked(coro, pbar):
    """执行一个协程，完成后推进进度条。"""
    try:
        return await coro
    finally:
        pbar.update(1)

async def main() -> None:
    coros = [read_channel(f"通道{i}", 5) for i in range(10)]
    with tqdm(total=len(coros), desc="采集通道", unit="个") as pbar:
        results = await asyncio.gather(*(tracked(c, pbar) for c in coros))
    print("完成:", len(results))
asyncio.run(main())
# 输出示例: 采集通道: 100%|██████████| 10/10 [00:00<00:00, 96.2个/s]
```
常见错误：

- 失败分支忘记推进进度条，进度永远差几个
- 不封装 `finally`，异常时进度条停在半路

### 9. 综合示例：异步并发读取多个大文件并统计

并发扫描 `sample-data/*.csv`，后台每 0.5 秒采样一次系统资源，输出 JSON 报告；
数据用阶段项目的 `starter/gen_data.py` 生成。
```python
# async_scan.py
"""异步并发统计一批实验 CSV，并后台采样系统资源。"""
import asyncio
import csv
import json
import time
from pathlib import Path
import psutil
from tqdm import tqdm

def scan_file(path: Path) -> dict:
    """阻塞式读取一个 CSV，返回点数与温度均值。"""
    count, temp_sum = 0, 0.0
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                temp_sum += float(row["temperature_K"])
                count += 1
            except (KeyError, ValueError):
                continue
    return {"file": path.name, "count": count,
            "temp_mean": round(temp_sum / count, 3) if count else None}

async def sample_system(stop_event: asyncio.Event, rows: list) -> None:
    """后台采样：每 0.5 秒记录一次 CPU 与进程内存。"""
    process = psutil.Process()
    while not stop_event.is_set():
        rows.append({"t": round(time.monotonic(), 2),
                     "cpu_percent": psutil.cpu_percent(interval=None),
                     "rss_mb": round(process.memory_info().rss / 1024 ** 2, 1)})
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=0.5)
        except asyncio.TimeoutError:
            pass

async def main() -> int:
    files = sorted(Path("sample-data").glob("*.csv"))
    if not files:
        print("没有找到 CSV，请先用 starter/gen_data.py 生成数据")
        return 1
    psutil.cpu_percent(interval=None)          # 初始化 CPU 采样基线
    stop, samples = asyncio.Event(), []

    async def scan_all() -> list:
        with tqdm(total=len(files), desc="扫描文件", unit="个") as pbar:
            async def one(path: Path) -> dict:
                try:
                    return await asyncio.to_thread(scan_file, path)
                finally:
                    pbar.update(1)             # 失败也推进
            return await asyncio.gather(*(one(p) for p in files))

    async def orchestrate() -> list:
        monitor = asyncio.create_task(sample_system(stop, samples))
        try:
            return await scan_all()
        finally:
            stop.set()
            await monitor                       # 等后台采样退出

    start = time.perf_counter()
    results = asyncio.run(orchestrate())
    elapsed = time.perf_counter() - start
    report = {"files": len(results),
              "total_rows": sum(r["count"] for r in results),
              "elapsed_s": round(elapsed, 2),
              "details": results, "resource_samples": samples}
    Path("scan_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成 {len(results)} 个文件，耗时 {elapsed:.2f} s，"
          "报告写入 scan_report.json")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
```
```bash
python3 starter/gen_data.py --target sample-data --files 40 --rows 20000 --seed 42
python3 async_scan.py
# 扫描文件: 100%|██████████| 40/40 [00:01<00:00, 21.5个/s]
# 完成 40 个文件，耗时 1.86 s，报告写入 scan_report.json
```
常见错误：

- 忘记在 `finally` 里 `stop.set()`，后台任务永不退出，程序挂住
- 后台采样里写 `time.sleep(0.5)`，把事件循环整个堵死
- IO 任务很少（比如 3 个文件）时异步提升有限，直接串行更简单

## 练习

1. 基准对比：同一目录下 10 个 CSV，分别写同步版与 `gather + to_thread` 版本，
   打印耗时。提示：`time.perf_counter`；验收：异步版接近单文件耗时。
2. 超时重试：把 `read_with_retry` 改成带统计的版本，返回
   `(结果或 None, 超时次数)`。提示：`wait_for`、退避等待、`logging.warning`；
   验收：对「总是超时」「第三次成功」两种假仪器行为都正确。
3. 监控脚本：写 `monitor.py`，argparse 接收 `--interval`（默认 2）、
   `--duration`（默认 10）、`--out`（默认 monitor.csv）；跑完用
   `wc -l monitor.csv` 检查行数约为 `duration / interval + 1`（含表头）。
   验收：首行数据 cpu_percent 不为 0.0，CSV 能正常打开。
4. 外部命令并发：用 `asyncio.subprocess` 同时执行 3 个 `sleep 2`，整体耗时约
   2 秒；再给其中一个加 1 秒超时，确认被 kill 且无僵尸进程
   （`ps aux | grep sleep` 检查）。提示：`gather`、`wait_for`、`proc.kill()`；
   验收：总耗时约 2 秒，超时任务抛 `TimeoutError`。
5. 综合：给综合示例加 `--pattern` 参数，并给 `scan_file` 写 3 个 pytest 用例
   （正常、空文件、坏行跳过）。提示：`tmp_path`、`pytest.approx`；
   验收：`pytest -q` 全绿，空文件返回 `count=0` 且 `temp_mean=None`。

## 自测清单

- [ ] 我能说清同步、异步、并发的区别，并判断任务该用哪种方式
- [ ] 我会写 `async def` / `await` / `asyncio.run`，不把协程对象当结果用
- [ ] 我会用 `gather` 与 `create_task`，知道 `return_exceptions=True` 的作用
- [ ] 我会用 `wait_for` 加超时，并会做有限次数退避重试
- [ ] 我会用 `asyncio.subprocess` 并发调用外部命令并回收子进程
- [ ] 我会用 `asyncio.to_thread` 包装阻塞函数，并知道它不能加速 CPU 计算
- [ ] 我会用 psutil 写 CPU/内存/磁盘采样日志，采样前先初始化 cpu_percent
- [ ] 我能独立完成「异步并发读取多个大文件并统计」的脚本

## 参考资料

- asyncio 官方文档：https://docs.python.org/3/library/asyncio.html
- subprocess 官方文档（含 asyncio.subprocess 的底层说明）：https://docs.python.org/3/library/subprocess.html
- psutil 项目主页：https://pypi.org/project/psutil
- tqdm 项目主页：https://pypi.org/project/tqdm
- tqdm 官方文档：https://tqdm.github.io

异步适合等待型任务；一旦出现重计算，回到 03 课的进程池，两者可以组合使用。
