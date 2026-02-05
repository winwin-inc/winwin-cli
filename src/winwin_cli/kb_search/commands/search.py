"""Search command for kb_search CLI."""

import sys
import json

import click

from winwin_cli.kb_search.config import load_global_config
from winwin_cli.kb_search.search import SearchEngine
from winwin_cli.kb_search.models import SearchRequest


@click.command()
@click.argument("query", required=False)  # 改为位置参数，可选
@click.option(
    "--kb",
    "-k",
    multiple=True,
    help="指定知识库（默认：所有启用的知识库）",
)
@click.option(
    "--limit",
    "-l",
    default=10,
    type=int,
    help="最大结果数（默认：10）",
)
@click.option(
    "--json",
    "-j",
    "output_json",  # 重命名参数避免与 json 模块冲突
    is_flag=True,
    default=False,
    help="JSON 输出（AI 调用）",
)
@click.option(
    "--content",
    "-c",
    is_flag=True,
    default=False,
    help="返回完整内容",
)
def search(query: str, kb: tuple, limit: int, output_json: bool, content: bool):
    """搜索知识库

    简化用法：
        winwin-cli kb-search search "关键词"
        winwin-cli kb-search search "API" --kb docs
        winwin-cli kb-search search "配置" -l 5 --json
    """
    if not query:
        click.echo("请输入搜索关键词", err=True)
        sys.exit(1)

    try:
        configs = load_global_config()

        request = SearchRequest(
            query=query,
            knowledge_bases=list(kb) if kb else None,
            max_results=limit,
            format="json" if output_json else "text",
            highlight=True,
            with_content=content,
        )

        engine = SearchEngine()
        result = engine.execute(request, configs)

        if output_json:
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if "output" in result:
                click.echo(result["output"])

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


def register(group: click.Group):
    """Register the search command with the Click group."""
    group.add_command(search)


__all__ = ["search"]
