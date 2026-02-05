"""知识库检索工具 - CLI 模块（简化版）"""

import click

from winwin_cli.kb_search.commands import discover_commands


@click.group()
def kb_search():
    """知识库检索工具 - 快速搜索你的文档"""
    pass


# Auto-discover and register all commands from the commands/ directory
discovered = discover_commands(kb_search)


# Export command functions for backward compatibility with tests
# These are re-exported from their respective modules
from winwin_cli.kb_search.commands.search import search
from winwin_cli.kb_search.commands.list import list_kb
from winwin_cli.kb_search.commands.index import index
from winwin_cli.kb_search.commands.add import add
from winwin_cli.kb_search.commands.remove import remove
from winwin_cli.kb_search.commands.enable import enable
from winwin_cli.kb_search.commands.disable import disable
from winwin_cli.kb_search.commands.status import status
from winwin_cli.kb_search.commands.info import info


__all__ = [
    "kb_search",
    "search",
    "list_kb",
    "index",
    "add",
    "remove",
    "enable",
    "disable",
    "status",
    "info",
]
