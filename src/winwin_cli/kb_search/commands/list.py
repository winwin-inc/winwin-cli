"""List command for kb_search CLI."""

import sys
import json

import click

from winwin_cli.kb_search.config import load_global_config


@click.command(name="list")  # Use name="list" to avoid conflict with built-in
@click.option(
    "--json",
    "-j",
    "output_json",  # 重命名参数避免与 json 模块冲突
    is_flag=True,
    help="JSON 输出",
)
def list_kb(output_json: bool):
    """列出知识库

    用法：winwin-cli kb-search list
    """
    try:
        configs = load_global_config()

        if output_json:
            result = {
                "knowledge_bases": [
                    {
                        "name": c.name,
                        "path": c.path,
                        "enabled": c.enabled,
                    }
                    for c in configs
                ]
            }
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if not configs:
                click.echo("未配置知识库")
                return

            for c in configs:
                status = "✓" if c.enabled else "✗"
                click.echo(f"{status} {c.name} -> {c.path}")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


def register(group: click.Group):
    """Register the list command with the Click group."""
    group.add_command(list_kb)


__all__ = ["list_kb"]
