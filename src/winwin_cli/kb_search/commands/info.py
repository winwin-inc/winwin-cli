"""Info command for kb_search CLI.

This is another simple example showing how easy it is to add commands.
"""

import click


@click.command()
def info():
    """显示系统信息

    显示知识库检索工具的版本和配置信息。

    用法：winwin-cli kb-search info
    """
    click.echo("知识库检索工具 v1.0")
    click.echo()
    click.echo("功能特性:")
    click.echo("  - 全文搜索 (BM25)")
    click.echo("  - 多知识库管理")
    click.echo("  - Markdown 文档索引")
    click.echo("  - AI 友好的 JSON 输出")
    click.echo()
    click.echo("配置文件: ~/.config/winwin-cli/kb_search.json")
    click.echo("索引目录: ~/.cache/winwin-cli/kb_search/")


def register(group: click.Group):
    """Register the info command with the Click group."""
    group.add_command(info)


__all__ = ["info"]
