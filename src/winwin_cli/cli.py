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
    from winwin_cli.convert.cli import convert
    return convert


def _import_skills():
    """延迟导入 skills 模块"""
    from winwin_cli.skills.cli import skills
    return skills


def _import_web_search():
    """延迟导入 web_search 模块"""
    from winwin_cli.web_search.cli import web_search
    return web_search


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

try:
    skills_cmd = _import_skills()
    main.add_command(skills_cmd, "skills")
except ImportError:
    pass

try:
    web_search_cmd = _import_web_search()
    main.add_command(web_search_cmd, "web-search")
except ImportError:
    pass


if __name__ == "__main__":
    main()
