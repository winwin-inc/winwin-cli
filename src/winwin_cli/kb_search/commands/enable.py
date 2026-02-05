"""Enable command for kb_search CLI."""

import sys

import click

from winwin_cli.kb_search.config import KnowledgeBaseLoader


@click.command()
@click.argument("name", required=True)
def enable(name: str):
    """启用知识库

    用法：winwin-cli kb-search enable my-kb
    """
    try:
        loader = KnowledgeBaseLoader()
        configs = loader.load()

        for c in configs:
            if c.name == name:
                c.enabled = True
                loader.save(configs)
                click.echo(f"✓ 启用: {name}")
                return

        click.echo(f"未找到知识库: {name}", err=True)
        sys.exit(1)

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


def register(group: click.Group):
    """Register the enable command with the Click group."""
    group.add_command(enable)


__all__ = ["enable"]
