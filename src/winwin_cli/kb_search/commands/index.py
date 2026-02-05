"""Index command for kb_search CLI."""

import sys
from typing import Optional

import click

from winwin_cli.kb_search.config import load_global_config
from winwin_cli.kb_search.indexer import KnowledgeBaseIndexer


@click.command()
@click.argument("name", required=False)  # 可选，默认索引所有
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="强制重建",
)
def index(name: Optional[str], force: bool):
    """构建索引

    用法：
        winwin-cli kb-search index              # 索引所有
        winwin-cli kb-search index docs         # 索引指定知识库
        winwin-cli kb-search index -f           # 强制重建所有
    """
    try:
        configs = load_global_config()

        if name:
            targets = [c for c in configs if c.name == name]
            if not targets:
                click.echo(f"未找到知识库: {name}", err=True)
                sys.exit(1)
        else:
            targets = configs
            if not targets:
                click.echo("未配置知识库", err=True)
                sys.exit(1)

        for config in targets:
            indexer = KnowledgeBaseIndexer(config)
            info = indexer.create_index() if force else indexer.update_index()
            click.echo(f"✓ {config.name}: {info.document_count} 个文档")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


def register(group: click.Group):
    """Register the index command with the Click group."""
    group.add_command(index)


__all__ = ["index"]
