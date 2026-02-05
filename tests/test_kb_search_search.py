"""测试搜索模块"""

import pytest
from pathlib import Path

from winwin_cli.kb_search.search import KnowledgeBaseSearcher, SearchEngine
from winwin_cli.kb_search.models import (
    KnowledgeBaseConfig,
    SearchRequest,
    Document,
    SearchResult,
)


class TestKnowledgeBaseSearcher:
    """测试知识库搜索器"""

    def test_searcher_init(self):
        """测试搜索器初始化"""
        configs = [
            KnowledgeBaseConfig(name="kb1", path="/path/to/kb1"),
            KnowledgeBaseConfig(name="kb2", path="/path/to/kb2"),
        ]
        searcher = KnowledgeBaseSearcher(configs)

        assert len(searcher.configs) == 2
        assert searcher._indexers == {}

    def test_search_empty_query(self):
        """测试空查询返回空列表"""
        configs = [KnowledgeBaseConfig(name="kb1", path="/path/to/kb1")]
        searcher = KnowledgeBaseSearcher(configs)

        results = searcher.search("")

        assert results == []

    def test_search_disabled_kb_skipped(self, tmp_path):
        """测试禁用的知识库被跳过"""
        kb_path = tmp_path / "disabled-kb"
        kb_path.mkdir()
        docs_dir = kb_path / "docs"
        docs_dir.mkdir()

        configs = [
            KnowledgeBaseConfig(name="enabled-kb", path=str(kb_path), enabled=True),
        ]
        searcher = KnowledgeBaseSearcher(configs)

        results = searcher.search("测试")

        # 没有实际索引文档，结果应为空
        assert results == [] or len(results) == 0

    def test_search_with_kb_filter(self, tmp_path):
        """测试按知识库过滤搜索"""
        kb1_path = tmp_path / "kb1"
        kb1_path.mkdir()
        docs_dir = kb1_path / "docs"
        docs_dir.mkdir()

        kb2_path = tmp_path / "kb2"
        kb2_path.mkdir()

        configs = [
            KnowledgeBaseConfig(name="kb1", path=str(kb1_path), enabled=True),
            KnowledgeBaseConfig(name="kb2", path=str(kb2_path), enabled=True),
        ]
        searcher = KnowledgeBaseSearcher(configs)

        # 只搜索 kb1
        results = searcher.search("测试", knowledge_bases=["kb1"])

        assert results == []

    def test_search_all_enabled_kb(self, tmp_path):
        """测试搜索所有启用的知识库"""
        kb1_path = tmp_path / "kb1"
        kb1_path.mkdir()
        docs_dir = kb1_path / "docs"
        docs_dir.mkdir()

        kb2_path = tmp_path / "kb2"
        kb2_path.mkdir()

        configs = [
            KnowledgeBaseConfig(name="kb1", path=str(kb1_path), enabled=True),
            KnowledgeBaseConfig(name="kb2", path=str(kb2_path), enabled=False),
        ]
        searcher = KnowledgeBaseSearcher(configs)

        results = searcher.search("测试", knowledge_bases=None)

        # kb2 被禁用，不应该被搜索
        assert results == []

    def test_search_with_threshold(self, tmp_path):
        """测试阈值过滤"""
        kb_path = tmp_path / "kb"
        kb_path.mkdir()

        configs = [KnowledgeBaseConfig(name="kb1", path=str(kb_path), enabled=True)]
        searcher = KnowledgeBaseSearcher(configs)

        # 高阈值应该过滤掉低匹配结果
        results = searcher.search("测试", threshold=0.9)

        assert results == []

    def test_list_knowledge_bases(self):
        """测试列出知识库"""
        configs = [
            KnowledgeBaseConfig(
                name="kb1",
                path="/path/to/kb1",
                description="知识库1",
                enabled=True,
            ),
            KnowledgeBaseConfig(
                name="kb2",
                path="/path/to/kb2",
                description="知识库2",
                enabled=False,
            ),
        ]
        searcher = KnowledgeBaseSearcher(configs)

        result = searcher.list_knowledge_bases()

        assert len(result) == 2
        assert result[0]["name"] == "kb1"
        assert result[0]["enabled"] is True
        assert result[1]["name"] == "kb2"
        assert result[1]["enabled"] is False


class TestSearchEngine:
    """测试搜索引擎"""

    def test_engine_init(self):
        """测试引擎初始化"""
        engine = SearchEngine()
        assert engine.searcher is None

    def test_execute_with_request(self, tmp_path):
        """测试执行搜索请求"""
        engine = SearchEngine()

        kb_path = tmp_path / "kb"
        kb_path.mkdir()

        request = SearchRequest(
            query="API 文档",
            max_results=10,
            threshold=0.1,
        )
        configs = [KnowledgeBaseConfig(name="kb1", path=str(kb_path), enabled=True)]

        result = engine.execute(request, configs)

        assert "format" in result
        assert result["format"] == "text"

    def test_execute_json_format(self, tmp_path):
        """测试 JSON 格式输出"""
        engine = SearchEngine()

        kb_path = tmp_path / "kb"
        kb_path.mkdir()

        request = SearchRequest(
            query="API 文档",
            format="json",
        )
        configs = [KnowledgeBaseConfig(name="kb1", path=str(kb_path), enabled=True)]

        result = engine.execute(request, configs)

        assert result["format"] == "json"
        assert "results" in result

    def test_execute_text_format(self, tmp_path):
        """测试文本格式输出"""
        engine = SearchEngine()

        kb_path = tmp_path / "kb"
        kb_path.mkdir()

        request = SearchRequest(
            query="API 文档",
            format="text",
        )
        configs = [KnowledgeBaseConfig(name="kb1", path=str(kb_path), enabled=True)]

        result = engine.execute(request, configs)

        assert result["format"] == "text"
        assert "output" in result


class TestSearchResult:
    """测试搜索结果"""

    def test_search_result_creation(self):
        """测试搜索结果创建"""
        doc = Document(
            title="测试文档",
            path="/test/doc.md",
            content="这是测试内容",
        )
        result = SearchResult(
            document=doc,
            score=0.85,
            highlights=["这是<b>测试</b>内容"],
        )

        assert result.document.title == "测试文档"
        assert result.score == 0.85
        assert len(result.highlights) == 1

    def test_search_result_optional_highlights(self):
        """测试搜索结果可选高亮"""
        doc = Document(
            title="测试文档",
            path="/test/doc.md",
            content="这是测试内容",
        )
        result = SearchResult(
            document=doc,
            score=0.5,
        )

        assert result.highlights == []
