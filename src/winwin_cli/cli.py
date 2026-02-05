"""winwin-cli 主入口"""

import sys
from typing import Optional
import click


@click.group()
@click.version_option(version="0.1.0")
def main():
    """winwin-cli - CLI 封装工具，专为 AI 使用设计

    提供各种命令行工具的封装，支持 AI 自动化调用。
    """
    pass


def _import_kb_search():
    """延迟导入 kb-search 模块"""
    from winwin_cli.kb_search.cli import kb_search
    return kb_search


def _import_convert():
    """延迟导入 convert 模块"""
    from winwin_cli.convert import convert
    return convert


# 注册子命令
try:
    kb_search = _import_kb_search()
    main.add_command(kb_search, "kb-search")
except ImportError:
    pass

try:
    convert_cmd = _import_convert()
    main.add_command(convert_cmd)
except ImportError:
    pass


if __name__ == "__main__":
    main()
