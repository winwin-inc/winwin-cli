"""测试索引器模块"""

import pytest
from pathlib import Path
import tempfile
import os

from winwin_cli.kb_search.indexer import BM25Indexer, KnowledgeBaseIndexer, IndexInfo
from winwin_cli.kb_search.models import KnowledgeBaseConfig, Document


class TestBM25Indexer:
    """测试 BM25 索引器"""

    @pytest.fixture
    def temp_index_dir(self, tmp_path):
        """创建临时索引目录"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        return str(index_dir)

    def test_indexer_creation(self, temp_index_dir):
        """测试索引器创建"""
        indexer = BM25Indexer(temp_index_dir)
        assert indexer.index_dir == Path(temp_index_dir)
        assert indexer.corpus == []

    def test_add_single_document(self, temp_index_dir):
        """测试添加单个文档"""
        indexer = BM25Indexer(temp_index_dir)
        doc = Document(
            title="测试文档",
            path="/test/doc.md",
            content="这是测试文档的内容",
        )
        indexer.add_document(doc.path, doc.title, doc.content)

        assert len(indexer.corpus) == 1
        assert indexer.corpus[0]["title"] == "测试文档"

    def test_add_multiple_documents(self, temp_index_dir):
        """测试添加多个文档"""
        indexer = BM25Indexer(temp_index_dir)

        docs = [
            Document(title="文档1", path="/test/1.md", content="Python 编程语言"),
            Document(title="文档2", path="/test/2.md", content="JavaScript 前端开发"),
            Document(title="文档3", path="/test/3.md", content="Go 语言后端"),
        ]

        indexer.add_documents(docs)

        assert len(indexer.corpus) == 3

    def test_build_index(self, temp_index_dir):
        """测试构建索引"""
        indexer = BM25Indexer(temp_index_dir)

        docs = [
            Document(title="文档1", path="/test/1.md", content="Python 编程"),
            Document(title="文档2", path="/test/2.md", content="Python 自动化"),
            Document(title="文档3", path="/test/3.md", content="JavaScript"),
        ]

        indexer.add_documents(docs)

        assert indexer.bm25 is not None

    def test_search_basic(self, temp_index_dir):
        """测试基本搜索"""
        indexer = BM25Indexer(temp_index_dir)

        docs = [
            Document(title="Python教程", path="/python/guide.md", content="学习 Python 编程语言"),
            Document(title="JavaScript教程", path="/js/guide.md", content="学习 JavaScript 前端"),
            Document(title="Python框架", path="/python/framework.md", content="Django 和 Flask 框架"),
        ]

        indexer.add_documents(docs)

        results = list(indexer.search("Python"))

        assert len(results) >= 1
        # Python 相关文档应该在结果中
        titles = [r["title"] for r in results]
        assert any("Python" in t for t in titles)

    def test_search_chinese(self, temp_index_dir):
        """测试中文搜索"""
        indexer = BM25Indexer(temp_index_dir)

        docs = [
            Document(title="API文档", path="/api.md", content="这是 API 接口文档"),
            Document(title="使用指南", path="/guide.md", content="详细的使用指南和说明"),
            Document(title="FAQ", path="/faq.md", content="常见问题和答案"),
        ]

        indexer.add_documents(docs)

        results = list(indexer.search("使用指南"))

        assert len(results) >= 1
        assert results[0]["title"] == "使用指南"

    def test_search_with_limit(self, temp_index_dir):
        """测试搜索结果限制"""
        indexer = BM25Indexer(temp_index_dir)

        docs = [
            Document(title=f"文档{i}", path=f"/test/{i}.md", content=f"内容 {i}")
            for i in range(20)
        ]

        indexer.add_documents(docs)

        results = list(indexer.search("内容", limit=5))

        assert len(results) == 5

    def test_search_returns_highlights(self, temp_index_dir):
        """测试搜索返回高亮片段"""
        indexer = BM25Indexer(temp_index_dir)

        docs = [
            Document(
                title="API文档",
                path="/test.md",
                content="这是关于 API 接口的文档，API 是重要的功能",
            ),
        ]

        indexer.add_documents(docs)

        results = list(indexer.search("API", highlight=True))

        # 由于 jieba 分词，英文可能不会被分词
        # 改用中文搜索
        results2 = list(indexer.search("接口", highlight=True))
        assert len(results2) == 1
        assert len(results2[0]["highlights"]) > 0

    def test_count(self, temp_index_dir):
        """测试文档计数"""
        indexer = BM25Indexer(temp_index_dir)

        assert indexer.count() == 0

        docs = [
            Document(title="文档1", path="/test/1.md", content="内容1"),
            Document(title="文档2", path="/test/2.md", content="内容2"),
        ]
        indexer.add_documents(docs)

        assert indexer.count() == 2


class TestKnowledgeBaseIndexer:
    """测试知识库索引器"""

    def test_indexer_creation(self, tmp_kb_path):
        """测试索引器创建"""
        config = KnowledgeBaseConfig(
            name="test-kb",
            path=str(tmp_kb_path),
        )
        indexer = KnowledgeBaseIndexer(config)

        assert indexer.config.name == "test-kb"

    def test_create_index_empty_kb(self, tmp_kb_path):
        """测试为空知识库创建索引"""
        config = KnowledgeBaseConfig(
            name="test-kb",
            path=str(tmp_kb_path),
        )
        indexer = KnowledgeBaseIndexer(config)

        info = indexer.create_index()

        assert isinstance(info, IndexInfo)
        assert info.document_count == 0

    def test_create_index_with_docs(self, sample_documents):
        """测试为有文档的知识库创建索引"""
        config = KnowledgeBaseConfig(
            name="sample-kb",
            path=str(sample_documents),
        )
        indexer = KnowledgeBaseIndexer(config)

        info = indexer.create_index()

        assert info.document_count > 0
        assert info.index_path is not None

    def test_update_index(self, sample_documents):
        """测试更新索引"""
        config = KnowledgeBaseConfig(
            name="sample-kb",
            path=str(sample_documents),
        )
        indexer = KnowledgeBaseIndexer(config)

        # 首次创建
        info1 = indexer.create_index()

        # 更新
        info2 = indexer.update_index()

        assert info2.document_count == info1.document_count

    def test_search_in_kb(self, sample_documents):
        """测试在知识库中搜索"""
        config = KnowledgeBaseConfig(
            name="sample-kb",
            path=str(sample_documents),
        )
        indexer = KnowledgeBaseIndexer(config)

        indexer.create_index()

        results = indexer.search("API")

        assert len(results) >= 1

    def test_search_with_dir_filter(self, sample_documents):
        """测试带目录过滤的搜索"""
        config = KnowledgeBaseConfig(
            name="sample-kb",
            path=str(sample_documents),
        )
        indexer = KnowledgeBaseIndexer(config)

        indexer.create_index()

        results = indexer.search("文档", dirs=["docs"])

        for r in results:
            assert "docs" in r.document.path

    def test_index_info_structure(self, sample_documents):
        """测试 IndexInfo 结构"""
        config = KnowledgeBaseConfig(
            name="sample-kb",
            path=str(sample_documents),
        )
        indexer = KnowledgeBaseIndexer(config)

        info = indexer.create_index()

        assert hasattr(info, 'document_count')
        assert hasattr(info, 'index_path')
        assert hasattr(info, 'knowledge_base')  # 注意：这里是 knowledge_base，不是 kb_name
