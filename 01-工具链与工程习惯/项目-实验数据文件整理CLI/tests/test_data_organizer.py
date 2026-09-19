"""data_organizer 的函数式测试（pytest）。

运行方式（在项目根目录，已激活 venv）:
    pytest -q

说明:
- 已实现函数的用例应当通过；骨架中标注 TODO 的函数对应用例暂时 skip，
  实现完成后删掉对应的 skip 装饰器，让测试真正跑起来。
- 测试只使用 tmp_path 构造临时数据，不依赖本机真实目录。
"""

import sys
from pathlib import Path

import pytest

# 让测试能找到 starter/ 下的 data_organizer.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "starter"))

import data_organizer as org


def make_text(path: Path, content: str) -> Path:
    """测试辅助函数：写文本文件（自动建父目录）并返回路径。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ---------- classify ----------

@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("run1.csv", "tables"),
        ("RUN_02.CSV", "tables"),
        ("note.txt", "text"),
        ("measurement.json", "structured"),
        ("picture.png", "images"),
        ("unknown.xyz", "other"),
    ],
)
def test_classify_by_extension(name, expected):
    assert org.classify_by_extension(Path(name)) == expected


def test_match_keyword_category():
    assert org.match_keyword_category("扫描记录 温度 2026-03-15.txt") == "temperature"
    assert org.match_keyword_category("temp_data_copy.csv") == "temperature"
    assert org.match_keyword_category("电压曲线.csv") == "voltage"
    assert org.match_keyword_category("run1.csv") is None


def test_classify_file_keyword_before_extension():
    # 关键词优先于扩展名
    assert org.classify_file(Path("温度记录.csv")) == "temperature"
    assert org.classify_file(Path("run1.csv")) == "tables"


def test_is_temp_file():
    assert org.is_temp_file(Path("~$scan_002.txt"))
    assert org.is_temp_file(Path("data.csv.bak"))
    assert org.is_temp_file(Path(".hidden_notes.txt"))
    assert not org.is_temp_file(Path("run1.csv"))


# ---------- hashlib 与去重 ----------

def test_hash_file_same_content(tmp_path):
    a = make_text(tmp_path / "a.txt", "温度=25.3\n")
    b = make_text(tmp_path / "b.txt", "温度=25.3\n")
    assert org.hash_file(a) == org.hash_file(b)


def test_hash_file_different_content(tmp_path):
    a = make_text(tmp_path / "a.txt", "25.3")
    b = make_text(tmp_path / "b.txt", "25.4")
    assert org.hash_file(a) != org.hash_file(b)


def test_find_duplicates(tmp_path):
    a = make_text(tmp_path / "a.txt", "same")
    b = make_text(tmp_path / "sub" / "b.txt", "same")
    c = make_text(tmp_path / "c.txt", "different")
    groups = org.find_duplicates([a, b, c])
    assert len(groups) == 1
    only_group = next(iter(groups.values()))
    assert sorted(p.name for p in only_group) == ["a.txt", "b.txt"]


def test_find_duplicates_none(tmp_path):
    a = make_text(tmp_path / "a.txt", "a")
    b = make_text(tmp_path / "b.txt", "b")
    assert org.find_duplicates([a, b]) == {}


def test_resolve_conflict_without_conflict(tmp_path):
    target = tmp_path / "new.csv"
    assert org.resolve_conflict(target) == target


def test_resolve_conflict_adds_suffix(tmp_path):
    existing = make_text(tmp_path / "run1.csv", "a")
    first = org.resolve_conflict(existing)
    assert first == tmp_path / "run1_1.csv"
    first.write_text("b", encoding="utf-8")
    second = org.resolve_conflict(existing)
    assert second == tmp_path / "run1_2.csv"


# ---------- 报告 ----------

def test_build_report_counts():
    records = [
        {"source": "a.csv", "category": "tables", "status": "ok", "size_bytes": 10},
        {"source": "b.csv", "category": "tables", "status": "ok", "size_bytes": 20},
        {
            "source": "b_copy.csv",
            "category": "tables",
            "status": "duplicate",
            "duplicate_of": "a.csv",
            "size_bytes": 10,
        },
        {"source": "c.xyz", "category": "other", "status": "error", "size_bytes": 0},
    ]
    report = org.build_report(records)
    assert report["total_files"] == 4
    assert report["processed"] == 2
    assert report["duplicates"] == 1
    assert report["errors"] == 1
    assert report["by_category"]["tables"] == 2
    assert report["duplicate_files"][0]["name"] == "b_copy.csv"
    assert report["duplicate_files"][0]["same_as"] == "a.csv"


def test_build_report_empty():
    report = org.build_report([])
    assert report["total_files"] == 0
    assert report["by_category"] == {}


# ---------- argparse ----------

def test_parse_args_defaults():
    args = org.parse_args(["--source", "sample-data"])
    assert args.source == Path("sample-data")
    assert args.dest == Path("organized")
    assert args.mode == "copy"
    assert args.dry_run is False
    assert args.report == Path("report")


def test_parse_args_options():
    args = org.parse_args(["--source", "in", "--dest", "out", "--mode", "move", "--dry-run", "-v"])
    assert args.dest == Path("out")
    assert args.mode == "move"
    assert args.dry_run is True
    assert args.verbose is True


def test_parse_args_requires_source():
    with pytest.raises(SystemExit):
        org.parse_args([])


# ---------- TODO 函数的用例（实现后请删掉 skip） ----------

@pytest.mark.skip(reason="TODO(M1): 实现 scan_files 后移除 skip")
def test_scan_files_recursive_and_filter(tmp_path):
    make_text(tmp_path / "raw" / "a.csv", "x")
    make_text(tmp_path / "notes.txt", "x")
    make_text(tmp_path / "~$temp.csv", "")
    make_text(tmp_path / "data.csv.bak", "")
    files = org.scan_files(tmp_path)
    assert [p.name for p in files] == ["a.csv", "notes.txt"]


@pytest.mark.skip(reason="TODO(M1): 实现 scan_files 后移除 skip")
def test_scan_files_missing_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        org.scan_files(tmp_path / "not-exist")


@pytest.mark.skip(reason="TODO(M2): 实现 plan_actions 后移除 skip")
def test_plan_actions_marks_duplicates(tmp_path):
    a = make_text(tmp_path / "temp_a.csv", "same")
    b = make_text(tmp_path / "temp_b.csv", "same")
    records = org.plan_actions([a, b], tmp_path, tmp_path / "out", mode="copy")
    assert len(records) == 2
    statuses = sorted(r["status"] for r in records)
    assert statuses == ["duplicate", "planned"]
    kept = [r for r in records if r["status"] == "planned"][0]
    assert kept["category"] == "temperature"
    assert kept["dest"].endswith("temperature/temp_a.csv") or kept["dest"].endswith(
        "temperature\\temp_a.csv"
    )


@pytest.mark.skip(reason="TODO(M3): 实现 execute_actions 后移除 skip")
def test_execute_actions_dry_run_keeps_files(tmp_path):
    src = make_text(tmp_path / "run1.csv", "x")
    records = [
        {
            "source": str(src),
            "dest": str(tmp_path / "out" / "tables" / "run1.csv"),
            "category": "tables",
            "size_bytes": 1,
            "sha256": "abc",
            "action": "copy",
            "status": "planned",
            "duplicate_of": "",
            "message": "",
        }
    ]
    result = org.execute_actions(records, dry_run=True)
    assert result[0]["status"] == "planned"
    assert not (tmp_path / "out").exists()


@pytest.mark.skip(reason="TODO(M3): 实现 write_report 后移除 skip")
def test_write_report_creates_files(tmp_path):
    records = [
        {
            "source": "a.csv",
            "dest": "out/tables/a.csv",
            "category": "tables",
            "size_bytes": 3,
            "sha256": "abc",
            "action": "copy",
            "status": "ok",
            "duplicate_of": "",
            "message": "",
        }
    ]
    csv_path, json_path = org.write_report(records, tmp_path / "report")
    assert csv_path.exists() and json_path.exists()
    assert "a.csv" in csv_path.read_text(encoding="utf-8")
    assert '"total_files": 1' in json_path.read_text(encoding="utf-8")
