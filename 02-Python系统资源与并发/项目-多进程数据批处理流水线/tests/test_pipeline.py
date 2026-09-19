"""pipeline.py 的纯函数测试（函数式 pytest，不使用 class）。

运行:
    pytest -q
说明:
    - 已实现并验证 discover_files / parse_file / aggregate
    - write_sqlite / write_hdf5 / build_report 对应用例先 skip，
      补全 pipeline.py 里的 TODO 后删掉 skip 装饰器即可
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "starter"))

import pytest

from pipeline import (aggregate, build_report, discover_files, parse_file,
                      write_hdf5, write_sqlite)

HEADER = ["time_s", "temperature_K", "voltage_V", "current_A"]


def write_csv(path: Path, rows: list) -> None:
    """写一个测试 CSV，rows 为 (time_s, temperature_K) 序列，后两列填常量。"""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for time_s, temp in rows:
            writer.writerow([time_s, temp, "1.0e-03", "1.0e-03"])


def make_stats(name: str, count: int, mean: float, tmin: float,
               tmax: float) -> dict:
    """构造一个 parse_file 风格的统计字典，用于测试 aggregate。"""
    return {
        "file": name, "count": count, "skipped": 0,
        "temp_mean": mean, "temp_min": tmin, "temp_max": tmax,
        "time_min": 0.0, "time_max": 10.0,
        "time_s": [], "temperature_K": [],
    }


def test_discover_files_sorted(tmp_path):
    """只发现 CSV，并且按路径排序。"""
    (tmp_path / "b.csv").write_text("x", encoding="utf-8")
    (tmp_path / "a.csv").write_text("x", encoding="utf-8")
    (tmp_path / "note.txt").write_text("x", encoding="utf-8")

    found = discover_files(tmp_path)
    assert [p.name for p in found] == ["a.csv", "b.csv"]


def test_discover_files_missing_dir(tmp_path):
    """目录不存在时返回空列表而不是抛异常。"""
    assert discover_files(tmp_path / "not-there") == []


def test_parse_file_stats(tmp_path):
    """正常文件的点数、均值与极值。"""
    path = tmp_path / "run_001.csv"
    write_csv(path, [(0, 300.0), (1, 200.0), (2, 100.0)])

    stats = parse_file(str(path))
    assert stats["file"] == "run_001.csv"
    assert stats["count"] == 3
    assert stats["skipped"] == 0
    assert stats["temp_mean"] == pytest.approx(200.0)
    assert stats["temp_min"] == 100.0
    assert stats["temp_max"] == 300.0
    assert stats["time_min"] == 0.0
    assert stats["time_max"] == 2.0
    assert stats["temperature_K"] == [300.0, 200.0, 100.0]


def test_parse_file_skips_bad_rows(tmp_path):
    """温度为空或不是数字的行被跳过，并计入 skipped。"""
    path = tmp_path / "run_002.csv"
    write_csv(path, [(0, 300.0), (1, ""), (2, "abc"), (3, 100.0)])

    stats = parse_file(str(path))
    assert stats["count"] == 2
    assert stats["skipped"] == 2
    assert stats["temp_mean"] == pytest.approx(200.0)
    assert stats["temperature_K"] == [300.0, 100.0]


def test_parse_file_header_only(tmp_path):
    """只有表头的文件：count=0，统计值为 None，数组为空。"""
    path = tmp_path / "empty_001.csv"
    write_csv(path, [])

    stats = parse_file(str(path))
    assert stats["count"] == 0
    assert stats["temp_mean"] is None
    assert stats["temp_min"] is None
    assert stats["temperature_K"] == []


def test_aggregate_weighted_mean():
    """整体均值应按点数加权，而不是简单平均。"""
    a = make_stats("a.csv", count=2, mean=100.0, tmin=80.0, tmax=120.0)
    b = make_stats("b.csv", count=3, mean=200.0, tmin=150.0, tmax=250.0)

    summary = aggregate([a, b])
    assert summary["files"] == 2
    assert summary["ok_files"] == 2
    assert summary["failed_files"] == 0
    assert summary["total_points"] == 5
    assert summary["temp_mean"] == pytest.approx((100.0 * 2 + 200.0 * 3) / 5)
    assert summary["temp_min"] == 80.0
    assert summary["temp_max"] == 250.0


def test_aggregate_skips_empty_files():
    """count=0 的文件不参与加权平均与极值，但计入总数。"""
    good = make_stats("ok.csv", count=4, mean=180.0, tmin=100.0, tmax=300.0)
    empty = make_stats("empty.csv", count=0, mean=None, tmin=None, tmax=None)
    # make_stats 不接受 None，这里手动覆盖
    empty["temp_mean"] = None
    empty["temp_min"] = None
    empty["temp_max"] = None

    summary = aggregate([good, empty])
    assert summary["files"] == 2
    assert summary["ok_files"] == 1
    assert summary["failed_files"] == 1
    assert summary["total_points"] == 4
    assert summary["temp_mean"] == pytest.approx(180.0)


def test_aggregate_empty_input():
    """空输入不报错，均值与极值为 None。"""
    summary = aggregate([])
    assert summary["files"] == 0
    assert summary["total_points"] == 0
    assert summary["temp_mean"] is None
    assert summary["temp_max"] is None


@pytest.mark.skip(reason="TODO: 实现 pipeline.write_sqlite 后删除本行")
def test_write_sqlite_rows(tmp_path):
    """写入 2 行后用 sqlite3 查回验证，重复写入不产生重复行。"""
    import sqlite3

    db = tmp_path / "runs.db"
    rows = [
        {"file": "run_001.csv", "count": 3, "temp_mean": 200.0,
         "temp_min": 100.0, "temp_max": 300.0, "time_min": 0.0,
         "time_max": 1.0},
        {"file": "run_002.csv", "count": 0, "temp_mean": None,
         "temp_min": None, "temp_max": None, "time_min": None,
         "time_max": None},
    ]
    write_sqlite(rows, db)
    write_sqlite(rows, db)                    # 重复运行不应报错

    with sqlite3.connect(db) as conn:
        found = conn.execute(
            "SELECT file, count FROM runs ORDER BY file").fetchall()
    assert found == [("run_001.csv", 3), ("run_002.csv", 0)]


@pytest.mark.skip(reason="TODO: 实现 pipeline.write_hdf5 后删除本行（需 h5py）")
def test_write_hdf5_arrays(tmp_path):
    """HDF5 里每个成功文件都有一维数组，长度等于 count。"""
    h5py = pytest.importorskip("h5py")

    h5_path = tmp_path / "runs.h5"
    rows = [
        {"file": "run_001.csv", "count": 3, "temp_mean": 200.0,
         "temp_min": 100.0, "temp_max": 300.0, "time_min": 0.0,
         "time_max": 1.0, "time_s": [0.0, 0.5, 1.0],
         "temperature_K": [300.0, 200.0, 100.0]},
    ]
    write_hdf5(rows, h5_path)

    with h5py.File(h5_path, "r") as f:
        temps = f["runs/run_001/temperature_K"][:]
    assert len(temps) == 3
    assert float(temps[0]) == pytest.approx(300.0)


@pytest.mark.skip(reason="TODO: 实现 pipeline.build_report 后删除本行")
def test_build_report_csv(tmp_path):
    """报告 CSV 的表头与行数正确。"""
    report = tmp_path / "report.csv"
    rows = [
        {"file": "run_001.csv", "count": 3, "temp_mean": 200.0,
         "temp_min": 100.0, "temp_max": 300.0},
        {"file": "empty_001.csv", "count": 0, "temp_mean": None,
         "temp_min": None, "temp_max": None},
    ]
    build_report(rows, report)

    lines = report.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("file")
    assert len(lines) == 3
