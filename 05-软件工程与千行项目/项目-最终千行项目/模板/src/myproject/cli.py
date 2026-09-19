"""myproject 的命令行入口。

设计约定：
- 本模块只负责"解析参数 -> 调用逻辑 -> 打印结果"，不写业务细节；
- 可直接测试的核心逻辑（如 greet）写成纯函数；
- 运行方式：
    * 安装后：myproject ...
    * 模块方式：python -m myproject.cli ...
"""

from __future__ import annotations

import argparse
import logging

from myproject import __version__

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """配置根日志。

    Args:
        verbose: 为 True 时输出 DEBUG 级别日志，否则输出 INFO。
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def greet(name: str, excited: bool = False) -> str:
    """生成问候语（纯函数，方便单元测试）。

    Args:
        name: 名字。
        excited: 为 True 时用两个感叹号结尾。

    Returns:
        问候语字符串。
    """
    suffix = "！！" if excited else "。"
    return f"你好，{name}！欢迎使用 myproject{suffix}"


def cmd_hello(args: argparse.Namespace) -> int:
    """hello 子命令的处理函数，返回进程退出码。"""
    print(greet(args.name, excited=args.excited))
    logger.debug("已处理 hello 子命令，name=%s", args.name)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """构造参数解析器。

    单独成函数，便于在测试中检查各子命令的参数解析结果。
    """
    parser = argparse.ArgumentParser(
        prog="myproject",
        description="科研数据处理项目模板的命令行工具。",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="显示版本号并退出",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="输出调试日志",
    )

    # 子命令集合；required=True 表示必须给出一个子命令
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="命令")

    # 子命令：hello（示例）
    p_hello = subparsers.add_parser("hello", help="打印一句问候语（示例子命令）")
    p_hello.add_argument("name", nargs="?", default="世界", help="要问候的名字（默认：世界）")
    p_hello.add_argument("-e", "--excited", action="store_true", help="更热情一点")
    p_hello.set_defaults(func=cmd_hello)

    return parser


def main(argv: list[str] | None = None) -> int:
    """程序入口。

    Args:
        argv: 参数列表；None 表示使用 sys.argv[1:]。

    Returns:
        进程退出码（0 表示成功）。
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose)
    logger.debug("解析到参数：%s", args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
