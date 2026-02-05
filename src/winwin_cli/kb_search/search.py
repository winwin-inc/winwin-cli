"""知识库检索工具 - 搜索模块"""

from typing import List, Optional
import json
import sys

from winwin_cli.kb_search.models import (
    KnowledgeBaseConfig,
    SearchRequest,
    SearchResult,
)
from winwin_cli.kb_search.indexer import KnowledgeBaseIndexer


class KnowledgeBaseSearcher:
    """知识库搜索器"""

    def __init__(self, configs: List[KnowledgeBaseConfig]):
        """初始化搜索器

        Args:
            configs: 知识库配置列表
        """
        self.configs = configs
        self._indexers: dict = {}

    def _get_indexer(self, config: KnowledgeBaseConfig) -> KnowledgeBaseIndexer:
        """获取或创建索引器

        Args:
            config: 知识库配置

        Returns:
            KnowledgeBaseIndexer 实例
        """
        if config.name not in self._indexers:
            self._indexers[config.name] = KnowledgeBaseIndexer(config)
        return self._indexers[config.name]

    def search(
        self,
        query: str,
        knowledge_bases: Optional[List[str]] = None,
        dirs: Optional[List[str]] = None,
        limit: int = 10,
        threshold: float = 0.1,
        highlight: bool = True,
        with_content: bool = False,
    ) -> List[SearchResult]:
        """搜索知识库

        Args:
            query: 搜索查询
            knowledge_bases: 要搜索的知识库名称列表，None 表示搜索所有
            dirs: 要搜索的子目录列表（相对于知识库根目录）
            limit: 最大返回结果数
            threshold: 最低匹配分数阈值
            highlight: 是否返回高亮片段
            with_content: 是否返回文档完整内容

        Returns:
            搜索结果列表
        """
        if not query:
            return []

        # 过滤要搜索的知识库
        configs_to_search = self._filter_configs(knowledge_bases)

        all_results: List[SearchResult] = []
        for config in configs_to_search:
            if not config.enabled:
                continue
            indexer = self._get_indexer(config)
            results = indexer.search(query, limit=limit, highlight=highlight, dirs=dirs, with_content=with_content)
            # 应用阈值过滤
            results = [r for r in results if r.score >= threshold]
            all_results.extend(results)

        # 按分数排序
        all_results.sort(key=lambda r: r.score, reverse=True)

        return all_results[:limit]

    def _filter_configs(
        self, knowledge_bases: Optional[List[str]]
    ) -> List[KnowledgeBaseConfig]:
        """过滤知识库配置

        Args:
            knowledge_bases: 知识库名称列表，None 表示返回所有启用的配置

        Returns:
            过滤后的配置列表
        """
        if knowledge_bases is None:
            return [c for c in self.configs if c.enabled]

        name_set = set(knowledge_bases)
        return [c for c in self.configs if c.name in name_set and c.enabled]

    def list_knowledge_bases(self) -> List[dict]:
        """列出所有已配置的知识库

        Returns:
            知识库信息列表
        """
        return [
            {
                "name": config.name,
                "path": config.path,
                "description": config.description,
                "enabled": config.enabled,
            }
            for config in self.configs
        ]


class SearchEngine:
    """搜索引擎"""

    def __init__(self):
        """初始化搜索引擎"""
        self.searcher: Optional[KnowledgeBaseSearcher] = None

    def execute(
        self,
        request: SearchRequest,
        configs: List[KnowledgeBaseConfig],
    ) -> dict:
        """执行搜索

        Args:
            request: 搜索请求
            configs: 知识库配置列表

        Returns:
            搜索结果字典
        """
        self.searcher = KnowledgeBaseSearcher(configs)
        results = self.searcher.search(
            query=request.query,
            knowledge_bases=request.knowledge_bases if request.knowledge_bases else None,
            dirs=request.dirs if request.dirs else None,
            limit=request.max_results,
            threshold=request.threshold,
            highlight=request.highlight,
            with_content=request.with_content,
        )

        if request.format == "json":
            return self._format_json_output(request, results)
        else:
            return self._format_text_output(results)

    def _format_json_output(
        self,
        request: SearchRequest,
        results: List[SearchResult],
    ) -> dict:
        """格式化 JSON 输出

        Args:
            request: 搜索请求
            results: 搜索结果

        Returns:
            JSON 格式的结果字典
        """
        return {
            "format": "json",
            "query": request.query,
            "total_results": len(results),
            "knowledge_bases": request.knowledge_bases or "all",
            "dirs": request.dirs or [],
            "results": [
                {
                    "title": r.document.title,
                    "path": r.document.path,
                    "score": round(r.score, 4),
                    "highlights": r.highlights,
                    "content": r.document.content if request.with_content else None,
                }
                for r in results
            ],
        }

    def _format_text_output(self, results: List[SearchResult]) -> dict:
        """格式化文本输出

        Args:
            results: 搜索结果

        Returns:
            文本格式的结果字典
        """
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r.document.title}")
            lines.append(f"   路径: {r.document.path}")
            lines.append(f"   相关度: {r.score:.2%}")
            if r.document.content:
                # 截取内容前 200 字
                content_preview = r.document.content[:200]
                if len(r.document.content) > 200:
                    content_preview += "..."
                lines.append(f"   内容: {content_preview}")
            if r.highlights:
                for h in r.highlights[:2]:
                    lines.append(f"   片段: {h}")
            lines.append("")

        return {
            "format": "text",
            "output": "\n".join(lines),
            "total_results": len(results),
        }
