"""Status command for kb_search CLI.

This is an example command that demonstrates how to add a new command.
To add this command, simply create this file in the commands/ directory
with a register() function. No other files need to be modified!
"""

import sys

import click

from winwin_cli.kb_search.config import load_global_config


@click.command()
@click.option(
    "--json",
    "-j",
    "output_json",
    is_flag=True,
    help="JSON output",
)
def status(output_json: bool):
    """显示知识库状态

    显示所有知识库的统计信息，包括：
    - 总数和启用/禁用数量
    - 每个知识库的文档数量
    - 索引状态

    用法：winwin-cli kb-search status
    """
    try:
        import json
        from winwin_cli.kb_search.indexer import KnowledgeBaseIndexer

        configs = load_global_config()

        if not configs:
            click.echo("未配置知识库")
            return

        # Calculate statistics
        total = len(configs)
        enabled = sum(1 for c in configs if c.enabled)
        disabled = total - enabled

        # Get document counts
        kb_stats = []
        total_docs = 0

        for config in configs:
            try:
                indexer = KnowledgeBaseIndexer(config)
                index_info = indexer.get_index_info()
                doc_count = index_info.document_count if index_info else 0
                total_docs += doc_count

                kb_stats.append({
                    "name": config.name,
                    "enabled": config.enabled,
                    "documents": doc_count,
                    "path": config.path,
                })
            except Exception:
                # If index doesn't exist or can't be read
                kb_stats.append({
                    "name": config.name,
                    "enabled": config.enabled,
                    "documents": 0,
                    "path": config.path,
                })

        if output_json:
            result = {
                "total_knowledge_bases": total,
                "enabled": enabled,
                "disabled": disabled,
                "total_documents": total_docs,
                "knowledge_bases": kb_stats,
            }
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            click.echo(f"知识库状态统计")
            click.echo(f"=" * 50)
            click.echo(f"总计: {total} 个知识库")
            click.echo(f"启用: {enabled} 个")
            click.echo(f"禁用: {disabled} 个")
            click.echo(f"索引文档总数: {total_docs} 个")
            click.echo()

            if kb_stats:
                click.echo(f"{'状态':<6} {'文档数':<8} {'名称':<20} {'路径'}")
                click.echo("-" * 80)
                for stat in kb_stats:
                    status_sym = "✓" if stat["enabled"] else "✗"
                    click.echo(f"{status_sym:<6} {stat['documents']:<8} {stat['name']:<20} {stat['path']}")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


def register(group: click.Group):
    """Register the status command with the Click group."""
    group.add_command(status)


__all__ = ["status"]
