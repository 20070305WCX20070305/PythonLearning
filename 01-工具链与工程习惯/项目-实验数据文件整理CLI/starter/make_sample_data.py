#!/usr/bin/env python3
"""生成模拟的混乱实验数据，用于测试「实验数据文件整理 CLI」。

用法示例:
    python3 starter/make_sample_data.py --target sample-data --seed 42

生成内容:
- txt/csv/json 三种格式，命名混乱（大小写、空格、中文、复制品）
- 3 个内容完全相同的 CSV，用于测试基于哈希的去重
- 若干应被忽略的临时文件（~$ 开头、.bak 结尾、隐藏文件）
- 一个子目录，用于验证递归扫描

只用标准库，可重复运行（同一 seed 生成同样的数据）。
"""

import argparse
import json
import random
from pathlib import Path


def parse_args(argv=None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="生成模拟实验数据")
    parser.add_argument(
        "--target",
        type=Path,
        default=Path("sample-data"),
        help="输出目录（默认 sample-data）",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子，保证每次生成的数据一致（默认 42）",
    )
    parser.add_argument(
        "--extra",
        type=int,
        default=3,
        help="额外生成的测量文件数量（默认 3）",
    )
    return parser.parse_args(argv)


def text_content(rng: random.Random, index: int) -> str:
    """生成一段实验记录文本。"""
    lines = [
        f"# 实验记录 {index}",
        f"样品编号: S{index:03d}",
        f"温度: {rng.uniform(20.0, 30.0):.2f} C",
        f"湿度: {rng.uniform(30.0, 60.0):.1f} %",
        f"备注: {'稳定' if index % 2 == 0 else '需要复测'}",
    ]
    return "\n".join(lines) + "\n"


def csv_content(rng: random.Random, index: int, rows: int = 5) -> str:
    """生成一段 CSV 测量数据（时间, 电压, 电流）。"""
    lines = ["time_s,voltage_V,current_mA"]
    for i in range(1, rows + 1):
        voltage = rng.uniform(0.0, 5.0)
        current = rng.uniform(0.0, 20.0)
        lines.append(f"{i}, {voltage:.3f}, {current:.2f}")
    return "\n".join(lines) + "\n"


def json_content(rng: random.Random, index: int) -> str:
    """生成一段 JSON 测量结果。"""
    data = {
        "sample": f"S{index:03d}",
        "timestamp": f"2026-03-{10 + index:02d}T09:30:00",
        "temperature_C": round(rng.uniform(20.0, 30.0), 2),
        "voltage_V": round(rng.uniform(0.0, 5.0), 3),
        "operator": "wang",
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def write_text(path: Path, content: str) -> Path:
    """写文本文件（自动创建父目录），返回写入的路径。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def create_text_files(root: Path, rng: random.Random) -> list[Path]:
    """生成命名混乱的文本类文件（含应被忽略的临时文件）。"""
    names = [
        "扫描记录 温度 2026-03-15.txt",
        "scan1.txt",
        "Scan_002.TXT",
        "untitled.txt",
        "data.csv.bak",
        "~$scan_002.txt",
        ".hidden_notes.txt",
    ]
    created = []
    for i, name in enumerate(names, start=1):
        # 以 ~$ 开头的文件模拟 Office/仪器软件残留的临时文件，内容留空
        content = "" if name.startswith("~$") else text_content(rng, i)
        created.append(write_text(root / name, content))
    return created


def create_csv_files(root: Path, rng: random.Random) -> list[Path]:
    """生成 CSV 文件；其中 3 个文件内容完全相同，用于测试去重。"""
    created = [
        write_text(root / "run1.csv", csv_content(rng, 1)),
        write_text(root / "RUN_02.CSV", csv_content(rng, 2)),
    ]
    duplicate_content = csv_content(rng, 3)
    for name in ("temp_data.csv", "temp_data_copy.csv", "测量数据.csv"):
        created.append(write_text(root / name, duplicate_content))
    return created


def create_json_files(root: Path, rng: random.Random) -> list[Path]:
    """生成 JSON 文件，其中一个放在子目录里，用于验证递归扫描。"""
    created = [
        write_text(root / "measurement_2026-03-14.json", json_content(rng, 4)),
        write_text(root / "config_snapshot.json", '{"instrument": "XRD-7", "mode": "scan"}\n'),
        write_text(root / "raw" / "2026-03-14" / "测量结果 电压.json", json_content(rng, 5)),
    ]
    return created


def create_extra_files(root: Path, rng: random.Random, count: int) -> list[Path]:
    """生成若干 .dat 文件，模拟其他仪器导出格式。"""
    kinds = ["temp", "volt", "press"]
    created = []
    for i in range(1, count + 1):
        kind = rng.choice(kinds)
        name = f"auto_{i:02d}_{kind}.dat"
        created.append(write_text(root / name, text_content(rng, 100 + i)))
    return created


def main(argv=None) -> int:
    """生成数据并打印摘要，返回退出码。"""
    args = parse_args(argv)
    rng = random.Random(args.seed)
    root = args.target
    root.mkdir(parents=True, exist_ok=True)

    created = []
    created += create_text_files(root, rng)
    created += create_csv_files(root, rng)
    created += create_json_files(root, rng)
    created += create_extra_files(root, rng, args.extra)

    print(f"已生成 {len(created)} 个文件到: {root.resolve()}")
    print("其中 3 个 CSV 内容完全相同（temp_data.csv / temp_data_copy.csv / 测量数据.csv），用于测试去重")
    print("临时文件 ~$scan_002.txt、data.csv.bak、.hidden_notes.txt 应被整理工具忽略")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
