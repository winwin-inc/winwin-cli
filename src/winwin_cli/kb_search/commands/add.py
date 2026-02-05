"""Add command for kb_search CLI."""

import sys
import os
from typing import Optional

import click

from winwin_cli.kb_search.config import KnowledgeBaseLoader
from winwin_cli.kb_search.models import KnowledgeBaseConfig
from winwin_cli.kb_search.indexer import KnowledgeBaseIndexer


@click.command()
@click.argument("name", required=True)
@click.argument("path", required=True)
@click.option(
    "--desc",
    "-d",
    help="描述",
)
@click.option(
    "--init",
    is_flag=True,
    help="初始化并构建索引",
)
def add(name: str, path: str, desc: Optional[str], init: bool):
    """添加知识库

    用法：
        winwin-cli kb-search add my-kb /path/to/docs
        winwin-cli kb-search add docs /docs --init
    """
    try:
        abs_path = os.path.abspath(path)

        if not os.path.exists(abs_path):
            click.echo(f"错误: 路径不存在: {abs_path}", err=True)
            sys.exit(1)

        loader = KnowledgeBaseLoader()
        configs = loader.load()

        # 检查重名
        for c in configs:
            if c.name == name:
                click.echo(f"错误: 知识库 '{name}' 已存在", err=True)
                sys.exit(1)

        # 创建配置（使用默认扩展名）
        new_config = KnowledgeBaseConfig(
            name=name,
            path=abs_path,
            description=desc,
        )
        configs.append(new_config)
        loader.save(configs)

        click.echo(f"✓ 添加知识库: {name}")
        click.echo(f"  路径: {abs_path}")
        click.echo(f"  支持: {len(new_config.extensions)} 种格式")

        # 初始化索引
        if init:
            click.echo("\n正在构建索引...")
            indexer = KnowledgeBaseIndexer(new_config)
            info = indexer.create_index()
            click.echo(f"✓ 索引完成: {info.document_count} 个文档")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


def register(group: click.Group):
    """Register the add command with the Click group."""
    group.add_command(add)


__all__ = ["add"]
