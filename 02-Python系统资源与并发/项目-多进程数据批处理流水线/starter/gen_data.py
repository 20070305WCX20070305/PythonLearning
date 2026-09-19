#!/usr/bin/env python3
"""生成模拟实验数据 CSV（仅使用标准库）。

每个文件模拟一次「R-T 扫描」：温度从 300 K 匀速降到 77 K（液氮温区），
在 1 mA 恒流下测量电压，电压含高斯噪声，并以 bad_rate 的概率插入
「温度缺失」的坏行，方便测试流水线的容错能力。

用法示例:
    python3 gen_data.py --target sample-data --files 60 --rows 5000 \
        --seed 42 --bad-rate 0.02

注意: 同名文件会被覆盖；输出由 --seed 决定，结果可复现。
"""
import argparse
import csv
import random
from pathlib import Path

COLUMNS = ["time_s", "temperature_K", "voltage_V", "current_A"]
T_START = 300.0        # 起始温度 (K)
T_END = 77.0           # 终止温度 (K)
CURRENT = 1e-3         # 恒流 1 mA
ROW_INTERVAL = 0.5     # 相邻数据点间隔 0.5 s


def resistance(temperature: float) -> float:
    """简化的 R-T 模型：温度越低电阻越大，用于生成形状合理的模拟数据。"""
    return 0.5 + 120.0 / (temperature - 70.0)


def write_one_file(path: Path, rows: int, rng: random.Random,
                   bad_rate: float) -> None:
    """写入一个模拟扫描文件；坏行表现为 temperature_K 列为空。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        for i in range(rows):
            time_s = i * ROW_INTERVAL
            if rows == 1:
                temp = T_START
            else:
                temp = T_START + (T_END - T_START) * i / (rows - 1)
            voltage = CURRENT * resistance(temp) * rng.gauss(1.0, 0.01)
            if rng.random() < bad_rate:
                # 模拟采集丢数：温度缺失，电压仍在
                writer.writerow([f"{time_s:.1f}", "",
                                 f"{voltage:.6e}", f"{CURRENT:.1e}"])
            else:
                writer.writerow([f"{time_s:.1f}", f"{temp:.3f}",
                                 f"{voltage:.6e}", f"{CURRENT:.1e}"])


def write_header_only(path: Path) -> None:
    """写一个只有表头的空数据文件，用于测试 count=0 的情况。"""
    path.write_text(",".join(COLUMNS) + "\n", encoding="utf-8")


def parse_args(argv=None):
    """解析命令行参数；argv 为 None 时读取 sys.argv[1:]，便于测试。"""
    parser = argparse.ArgumentParser(description="生成模拟 R-T 扫描实验数据 CSV")
    parser.add_argument("--target", type=Path, default=Path("sample-data"),
                        help="输出目录（默认 sample-data）")
    parser.add_argument("--files", type=int, default=20,
                        help="生成文件数（默认 20）")
    parser.add_argument("--rows", type=int, default=1000,
                        help="每个文件的数据行数（默认 1000）")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机种子，保证结果可复现")
    parser.add_argument("--bad-rate", type=float, default=0.02,
                        help="坏行（温度缺失）比例，默认 0.02")
    parser.add_argument("--empty-files", type=int, default=0,
                        help="额外生成 N 个只有表头的空文件（默认 0）")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """程序入口，返回退出码。"""
    args = parse_args(argv)
    if args.files < 0 or args.empty_files < 0 or args.rows < 1 \
            or not 0.0 <= args.bad_rate < 1.0:
        print("参数不合法：files/empty-files >= 0，rows >= 1，"
              "0 <= bad-rate < 1")
        return 2

    rng = random.Random(args.seed)
    target = args.target
    target.mkdir(parents=True, exist_ok=True)

    for i in range(1, args.files + 1):
        write_one_file(target / f"run_{i:03d}.csv", args.rows, rng,
                       args.bad_rate)
    for i in range(1, args.empty_files + 1):
        write_header_only(target / f"empty_{i:03d}.csv")

    bad_rows = round(args.files * args.rows * args.bad_rate)
    print(f"已生成 {args.files} 个文件（约 {bad_rows} 个坏行）"
          f" + {args.empty_files} 个空文件到 {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
