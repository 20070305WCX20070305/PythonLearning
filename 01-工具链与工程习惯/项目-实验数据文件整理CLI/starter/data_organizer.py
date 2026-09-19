#!/usr/bin/env python3
"""实验数据文件整理 CLI —— 骨架代码（阶段 01 项目）。

用法示例:
    python3 starter/data_organizer.py --source sample-data --dest organized --dry-run -v

说明:
- 标注 TODO 的函数需要你按里程碑补全；未标 TODO 的函数已实现，可直接运行与测试
- 约束: 不使用 class（阶段 05 才学），除 pytest 外只用标准库
- 数据流: scan_files -> plan_actions -> execute_actions -> build_report -> write_report
"""

import argparse
import csv
import hashlib
import json
import logging
import shutil
from pathlib import Path

# 扩展名 -> 分类名（可按需扩充）
DEFAULT_RULES = {
    ".csv": "tables",
    ".tsv": "tables",
    ".json": "structured",
    ".xml": "structured",
    ".txt": "text",
    ".log": "text",
    ".md": "text",
    ".png": "images",
    ".jpg": "images",
}

# 关键词 -> 分类名；关键词规则优先于扩展名规则
DEFAULT_KEYWORDS = {
    "temperature": ("温度", "temp"),
    "voltage": ("电压", "volt"),
}

# 临时文件特征：名字以此开头，或扩展名命中，扫描时忽略
TEMP_PREFIXES = ("~$", ".")
TEMP_SUFFIXES = (".bak", ".tmp", ".swp")


def parse_args(argv=None) -> argparse.Namespace:
    """解析命令行参数。argv 为 None 时读取 sys.argv[1:]，测试时可传入列表。"""
    parser = argparse.ArgumentParser(
        prog="data_organizer",
        description="整理实验数据文件：按类型/关键词分类、去重、生成报告",
    )
    parser.add_argument("--source", type=Path, required=True, help="待整理的源目录")
    parser.add_argument(
        "--dest", type=Path, default=Path("organized"), help="输出目录（默认 organized）"
    )
    parser.add_argument(
        "--mode", choices=("copy", "move"), default="copy", help="处理方式（默认 copy）"
    )
    parser.add_argument("--dry-run", action="store_true", help="只预览，不实际复制/移动")
    parser.add_argument(
        "--report", type=Path, default=Path("report"), help="报告文件名前缀（生成 .csv 与 .json）"
    )
    parser.add_argument(
        "--log", type=Path, default=Path("organizer.log"), help="日志文件路径"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="输出调试日志")
    return parser.parse_args(argv)


def setup_logging(log_file: Path, verbose: bool = False) -> None:
    """配置日志：同时输出到控制台与文件。verbose 为 True 时输出 DEBUG。"""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler()
    console.setFormatter(fmt)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()  # 避免重复调用时日志重复输出
    root.addHandler(console)
    root.addHandler(file_handler)


def is_temp_file(path: Path) -> bool:
    """判断是否临时文件：以 ~$ 或 . 开头，或以 .bak/.tmp/.swp 结尾。"""
    name = path.name
    if name.startswith(TEMP_PREFIXES):
        return True
    return path.suffix.lower() in TEMP_SUFFIXES


def classify_by_extension(path: Path, rules=None) -> str:
    """按扩展名返回分类名，未命中返回 other。"""
    active_rules = DEFAULT_RULES if rules is None else rules
    return active_rules.get(path.suffix.lower(), "other")


def match_keyword_category(name: str, keywords=None) -> str:
    """按文件名中的关键词返回分类名，未命中返回 None。"""
    active = DEFAULT_KEYWORDS if keywords is None else keywords
    lowered = name.lower()
    for category, words in active.items():
        for word in words:
            if word.lower() in lowered:
                return category
    return None


def classify_file(path: Path, rules=None, keywords=None) -> str:
    """分类入口：先匹配关键词，未命中再按扩展名。"""
    by_keyword = match_keyword_category(path.name, keywords)
    if by_keyword is not None:
        return by_keyword
    return classify_by_extension(path, rules)


def scan_files(source: Path) -> list:
    """递归扫描 source，返回所有普通文件（过滤临时文件），按字符串排序。

    TODO(M1):
    - source 不存在或不是目录时抛出 FileNotFoundError
    - 用 source.rglob("*") 遍历，path.is_file() 过滤目录
    - 用 is_temp_file 过滤临时文件
    - 返回 list[Path]，排序保证结果稳定
    """
    raise NotImplementedError("TODO(M1): 请实现 scan_files")


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """分块计算文件的 SHA-256，返回 64 位十六进制字符串。"""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicates(paths) -> dict:
    """按内容哈希分组，返回 {sha256: [路径, ...]}，只保留多于一个文件的组。"""
    groups = {}
    for path in paths:
        digest = hash_file(path)
        groups.setdefault(digest, []).append(path)
    return {digest: items for digest, items in groups.items() if len(items) > 1}


def resolve_conflict(dest: Path) -> Path:
    """若目标路径已存在，返回带 _1、_2... 后缀的可用路径，绝不覆盖已有文件。"""
    if not dest.exists():
        return dest
    parent = dest.parent
    stem = dest.stem
    suffix = dest.suffix
    index = 1
    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def plan_actions(paths, source: Path, dest: Path, mode: str = "copy") -> list:
    """把扫描结果转成操作计划（只规划，不写文件系统）。

    返回记录列表，每条记录字段:
      source, dest, category, size_bytes, sha256, action, status, duplicate_of, message

    规则:
    - 重复文件（find_duplicates 的结果）只保留排序后的第一个，其余 action="skip",
      status="duplicate"，duplicate_of 填保留文件的路径
    - 其余文件 action=mode，status="planned"，dest 为 dest/分类/文件名
    - 大小用 path.stat().st_size

    TODO(M2): 用 find_duplicates 标记重复，按上面的字段构造记录。
    """
    raise NotImplementedError("TODO(M2): 请实现 plan_actions")


def execute_actions(actions, dry_run: bool = False) -> list:
    """执行操作计划，返回更新后的记录列表。

    - dry_run=True 时只写日志，不做任何文件操作，status 保持 "planned"
    - 复制用 shutil.copy2，移动用 shutil.move
    - 目标已存在时用 resolve_conflict 生成不冲突的路径并更新记录
    - 单文件失败时 status="error"，message 记录原因，不中断整体流程
    - 成功后 status="ok"

    TODO(M3): 实现执行循环与错误处理。
    """
    raise NotImplementedError("TODO(M3): 请实现 execute_actions")


def build_report(records) -> dict:
    """汇总记录，生成报告字典（纯函数，便于测试）。

    返回字段: total_files, processed, duplicates, errors, by_category, duplicate_files
    """
    total = len(records)
    processed = sum(1 for r in records if r.get("status") == "ok")
    duplicates = [r for r in records if r.get("status") == "duplicate"]
    errors = [r for r in records if r.get("status") == "error"]

    by_category = {}
    for record in records:
        if record.get("status") in ("ok", "planned"):
            category = record.get("category", "other")
            by_category[category] = by_category.get(category, 0) + 1

    return {
        "total_files": total,
        "processed": processed,
        "duplicates": len(duplicates),
        "errors": len(errors),
        "by_category": by_category,
        "duplicate_files": [
            {"name": r.get("source"), "same_as": r.get("duplicate_of", "")}
            for r in duplicates
        ],
    }


def write_report(records, prefix: Path):
    """把明细写入 prefix.csv，把汇总写入 prefix.json，返回 (csv 路径, json 路径)。

    - CSV 表头: source,dest,category,size_bytes,sha256,action,status,message
      用 csv.DictWriter 写入（extra 字段忽略）
    - JSON: build_report 的结果，另加 generated_at 字段
    - 父目录不存在时先创建

    TODO(M3): 用 csv 与 json 模块实现，注意 ensure_ascii=False 和 indent=2。
    """
    raise NotImplementedError("TODO(M3): 请实现 write_report")


def main(argv=None) -> int:
    """程序入口：扫描 -> 计划 -> 执行 -> 报告。返回退出码（0 成功，1 有错误，2 参数/路径错误）。"""
    args = parse_args(argv)
    setup_logging(args.log, args.verbose)

    logging.info("源目录: %s", args.source)
    logging.info("目标目录: %s（模式: %s）", args.dest, args.mode)
    if args.dry_run:
        logging.info("dry-run: 只预览，不会修改任何文件")

    try:
        files = scan_files(args.source)
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 2

    logging.info("扫描到 %d 个文件", len(files))
    actions = plan_actions(files, args.source, args.dest, args.mode)
    records = execute_actions(actions, dry_run=args.dry_run)

    report = build_report(records)
    logging.info(
        "完成: 总数=%d 处理=%d 重复=%d 错误=%d",
        report["total_files"],
        report["processed"],
        report["duplicates"],
        report["errors"],
    )

    if not args.dry_run:
        csv_path, json_path = write_report(records, args.report)
        logging.info("报告已生成: %s, %s", csv_path, json_path)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
