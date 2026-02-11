"""Web Search CLI 命令 - 网络搜索工具"""

import sys
import json
from typing import Optional

import click

from winwin_cli.web_search.providers import (
    PROVIDERS,
    DEFAULT_PROVIDER,
    DEFAULT_FETCH_PROVIDER,
    get_provider,
)


@click.group()
def web_search():
    """网络搜索与网页抓取工具

    支持多种搜索引擎后端（search）和网页抓取后端（fetch）。
    """
    pass


@web_search.command()
@click.argument("query")
@click.option(
    "--provider", "-p",
    type=click.Choice([k for k, v in PROVIDERS.items() if hasattr(v, 'search') and not k == "markitdown"]),
    default=DEFAULT_PROVIDER,
    help=f"搜索引擎后端（默认: {DEFAULT_PROVIDER}）",
)
@click.option(
    "--limit", "-l",
    type=int,
    default=5,
    show_default=True,
    help="返回结果数量",
)
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="以 JSON 格式输出（用于 AI 调用）",
)
@click.option(
    "--api-key",
    envvar=["TAVILY_API_KEY"],
    help="API Key（也可通过环境变量设置，如 TAVILY_API_KEY）",
)
def search(query: str, provider: str, limit: int, output_json: bool, api_key: Optional[str]):
    """搜索互联网内容"""
    try:
        # 获取搜索引擎实例
        search_provider = get_provider(provider, api_key=api_key)

        # 执行搜索
        results = search_provider.search(query, limit=limit)

        if not results:
            if output_json:
                click.echo(json.dumps([], ensure_ascii=False))
            else:
                click.echo("未找到相关结果")
            return

        if output_json:
            # JSON 格式输出
            output = [r.to_dict() for r in results]
            click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            # 可读文本格式输出
            click.echo(f"\n🔍 搜索: \"{query}\"（{search_provider.name}）")
            click.echo(f"   找到 {len(results)} 条结果\n")

            for i, r in enumerate(results, 1):
                click.echo(f"  {i}. {r.title}")
                click.echo(f"     🔗 {r.url}")
                if r.snippet:
                    # 截取摘要，避免过长
                    snippet = r.snippet[:200] + "..." if len(r.snippet) > 200 else r.snippet
                    click.echo(f"     📝 {snippet}")
                click.echo()

    except Exception as e:
        click.echo(f"❌ 搜索失败: {e}", err=True)
        sys.exit(1)


@web_search.command()
@click.argument("url")
@click.option(
    "--provider", "-p",
    type=click.Choice(["markitdown", "tavily"]),
    default=DEFAULT_FETCH_PROVIDER,
    help=f"抓取引擎后端（默认: {DEFAULT_FETCH_PROVIDER}）",
)
@click.option(
    "--output", "-o",
    type=click.Path(writable=True),
    help="输出文件路径（默认输出到控制台）",
)
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="以 JSON 格式输出（包含元数据）",
)
@click.option(
    "--api-key",
    envvar=["TAVILY_API_KEY"],
    help="API Key（如使用 Tavily）",
)
def fetch(url: str, provider: str, output: Optional[str], output_json: bool, api_key: Optional[str]):
    """抓取网页内容并转换为 Markdown

    用例：
        winwin-cli web-search fetch https://example.com
        winwin-cli web-search fetch https://example.com -o content.md
        winwin-cli web-search fetch https://example.com --provider tavily
    """
    try:
        # 获取 Provider 实例
        fetch_provider = get_provider(provider, api_key=api_key)
        
        if not output_json:
            click.echo(f"⏳ 正在抓取: {url} ({fetch_provider.name})...", err=True)
            
        result = fetch_provider.fetch(url)

        if output_json:
            click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(result.content)
                click.echo(f"✅ 内容已保存至: {output}")
            else:
                click.echo(f"\n--- 内容开始 ---")
                click.echo(result.content)
                click.echo(f"--- 内容结束 ---\n")

    except Exception as e:
        click.echo(f"❌ 抓取失败: {e}", err=True)
        sys.exit(1)


@web_search.command()
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="以 JSON 格式输出",
)
def providers(output_json: bool):
    """列出可用的搜索引擎与抓取后端"""
    provider_list = []
    for name, cls in PROVIDERS.items():
        can_search = hasattr(cls, 'search') and not name == 'markitdown'
        can_fetch = name in ['markitdown', 'tavily']
        
        provider_list.append({
            "name": name,
            "description": cls.description,
            "requires_api_key": cls.requires_api_key,
            "capabilities": {
                "search": can_search,
                "fetch": can_fetch
            }
        })

    if output_json:
        click.echo(json.dumps(provider_list, ensure_ascii=False, indent=2))
    else:
        click.echo("\n可用的后端服务：\n")
        for p in provider_list:
            caps = []
            if p["capabilities"]["search"]: caps.append("🔍 搜索")
            if p["capabilities"]["fetch"]: caps.append("📄 抓取")
            
            key_tag = " 🔑 需要 API Key" if p["requires_api_key"] else " ✅ 免费"
            click.echo(f"  • {p['name']} [{', '.join(caps)}]")
            click.echo(f"    {p['description']}{key_tag}")
            click.echo()
