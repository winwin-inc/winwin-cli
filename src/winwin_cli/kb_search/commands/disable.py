"""Disable command for kb_search CLI."""

import sys

import click

from winwin_cli.kb_search.config import KnowledgeBaseLoader


@click.command()
@click.argument("name", required=True)
def disable(name: str):
    """禁用知识库

    用法：winwin-cli kb-search disable my-kb
    """
    try:
        loader = KnowledgeBaseLoader()
        configs = loader.load()

        for c in configs:
            if c.name == name:
                c.enabled = False
                loader.save(configs)
                click.echo(f"✓ 禁用: {name}")
                return

        click.echo(f"未找到知识库: {name}", err=True)
        sys.exit(1)

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


def register(group: click.Group):
    """Register the disable command with the Click group."""
    group.add_command(disable)


__all__ = ["disable"]
