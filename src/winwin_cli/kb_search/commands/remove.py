"""Remove command for kb_search CLI."""

import sys

import click

from winwin_cli.kb_search.config import KnowledgeBaseLoader


@click.command()
@click.argument("name", required=True)
def remove(name: str):
    """移除知识库

    用法：winwin-cli kb-search remove my-kb
    """
    try:
        loader = KnowledgeBaseLoader()
        configs = loader.load()

        new_configs = [c for c in configs if c.name != name]
        if len(new_configs) == len(configs):
            click.echo(f"未找到知识库: {name}", err=True)
            sys.exit(1)

        loader.save(new_configs)
        click.echo(f"✓ 移除知识库: {name}")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


def register(group: click.Group):
    """Register the remove command with the Click group."""
    group.add_command(remove)


__all__ = ["remove"]
