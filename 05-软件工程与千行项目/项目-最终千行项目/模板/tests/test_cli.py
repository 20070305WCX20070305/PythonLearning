"""cli 模块的测试模板（函数式与类式混用均可，本文件两种都演示了）。

运行：

    pytest
    pytest --cov=myproject --cov-report=term-missing
"""

from __future__ import annotations

import pytest

from myproject import __version__
from myproject.cli import build_parser, greet, main


class TestGreet:
    """greet 是纯函数，用类式写法分组。"""

    def test_contains_name(self) -> None:
        assert "张三" in greet("张三")

    def test_default_ends_with_period(self) -> None:
        assert greet("张三").endswith("。")

    def test_excited_ends_with_marks(self) -> None:
        assert greet("张三", excited=True).endswith("！！")

    def test_excited_changes_output(self) -> None:
        assert greet("张三") != greet("张三", excited=True)


def test_parser_requires_subcommand() -> None:
    """不提供子命令时，argparse 应以退出码 2 报错。"""
    parser = build_parser()
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args([])
    assert excinfo.value.code == 2


@pytest.mark.parametrize(
    ("argv", "expected_name"),
    [
        (["hello", "世界"], "世界"),
        (["hello", "李四"], "李四"),
        (["hello"], "世界"),  # 使用默认值
    ],
    ids=["default-name-given", "other-name", "fallback-default"],
)
def test_parse_hello_name(argv: list[str], expected_name: str) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    assert args.name == expected_name


@pytest.mark.parametrize(
    ("argv", "excited"),
    [
        (["hello", "王五"], False),
        (["hello", "王五", "-e"], True),
        (["hello", "王五", "--excited"], True),
    ],
)
def test_parse_hello_excited(argv: list[str], excited: bool) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    assert args.excited is excited


def test_main_hello_prints_and_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["hello", "王五"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "王五" in captured.out


def test_main_excited_output(capsys: pytest.CaptureFixture[str]) -> None:
    main(["hello", "王五", "-e"])
    assert capsys.readouterr().out.endswith("！！\n")


def test_main_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out
