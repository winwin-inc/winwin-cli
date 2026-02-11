"""测试 web-search 命令"""

import pytest
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from winwin_cli.web_search.cli import web_search
from winwin_cli.web_search.providers import (
    SearchResult,
    FetchResult,
    DuckDuckGoProvider,
    TavilyProvider,
    MarkItDownProvider,
    PROVIDERS,
    get_provider,
)


# ==================== 测试 Provider 层 ====================

class TestSearchResult:
    """测试 SearchResult 数据类"""

    def test_to_dict(self):
        result = SearchResult(title="标题", url="https://example.com", snippet="摘要")
        d = result.to_dict()
        assert d["title"] == "标题"
        assert d["url"] == "https://example.com"
        assert d["snippet"] == "摘要"


class TestGetProvider:
    """测试 get_provider 工厂函数"""

    def test_get_duckduckgo(self):
        provider = get_provider("duckduckgo")
        assert isinstance(provider, DuckDuckGoProvider)

    def test_get_tavily(self):
        provider = get_provider("tavily", api_key="test-key")
        assert isinstance(provider, TavilyProvider)
        assert provider.api_key == "test-key"

    def test_invalid_provider(self):
        with pytest.raises(ValueError, match="不支持的搜索引擎"):
            get_provider("不存在的引擎")


class TestDuckDuckGoProvider:
    """测试 DuckDuckGo 搜索后端"""

    @patch("ddgs.DDGS")
    def test_search_returns_results(self, mock_ddgs_cls):
        # 模拟 ddgs 返回结果
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "结果1", "href": "https://example.com/1", "body": "摘要1"},
            {"title": "结果2", "href": "https://example.com/2", "body": "摘要2"},
        ]
        mock_ddgs_cls.return_value = mock_ddgs

        provider = DuckDuckGoProvider()
        results = provider.search("测试查询", limit=2)

        assert len(results) == 2
        assert results[0].title == "结果1"
        assert results[0].url == "https://example.com/1"
        assert results[0].snippet == "摘要1"


class TestTavilyProvider:
    """测试 Tavily 搜索后端"""

    def test_missing_api_key(self):
        """未提供 API Key 时应报错"""
        provider = TavilyProvider()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API Key"):
                provider.search("测试")


# ==================== 测试 CLI 层 ====================

class TestWebSearchCommand:
    """测试 web-search CLI 命令"""

    def test_command_exists(self):
        """测试 web-search 命令存在"""
        runner = CliRunner()
        result = runner.invoke(web_search, ["--help"])
        assert result.exit_code == 0
        assert "网络搜索" in result.output

    def test_search_subcommand_help(self):
        """测试 search 子命令帮助"""
        runner = CliRunner()
        result = runner.invoke(web_search, ["search", "--help"])
        assert result.exit_code == 0
        assert "搜索互联网内容" in result.output

    def test_providers_subcommand(self):
        """测试 providers 子命令"""
        runner = CliRunner()
        result = runner.invoke(web_search, ["providers"])
        assert result.exit_code == 0
        assert "duckduckgo" in result.output
        assert "tavily" in result.output

    def test_providers_json_output(self):
        """测试 providers JSON 输出"""
        runner = CliRunner()
        result = runner.invoke(web_search, ["providers", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 3
        names = [p["name"] for p in data]
        assert "duckduckgo" in names
        assert "tavily" in names
        assert "markitdown" in names

    @patch("winwin_cli.web_search.cli.get_provider")
    def test_search_text_output(self, mock_get_provider):
        """测试搜索文本格式输出"""
        mock_provider = MagicMock()
        mock_provider.name = "duckduckgo"
        mock_provider.search.return_value = [
            SearchResult(title="测试结果", url="https://example.com", snippet="这是摘要"),
        ]
        mock_get_provider.return_value = mock_provider

        runner = CliRunner()
        result = runner.invoke(web_search, ["search", "测试"])
        assert result.exit_code == 0
        assert "测试结果" in result.output
        assert "https://example.com" in result.output

    @patch("winwin_cli.web_search.cli.get_provider")
    def test_search_json_output(self, mock_get_provider):
        """测试搜索 JSON 格式输出"""
        mock_provider = MagicMock()
        mock_provider.name = "duckduckgo"
        mock_provider.search.return_value = [
            SearchResult(title="结果A", url="https://a.com", snippet="摘要A"),
            SearchResult(title="结果B", url="https://b.com", snippet="摘要B"),
        ]
        mock_get_provider.return_value = mock_provider

        runner = CliRunner()
        result = runner.invoke(web_search, ["search", "测试", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2
        assert data[0]["title"] == "结果A"

    @patch("winwin_cli.web_search.cli.get_provider")
    def test_search_limit_option(self, mock_get_provider):
        """测试 --limit 参数传递"""
        mock_provider = MagicMock()
        mock_provider.name = "duckduckgo"
        mock_provider.search.return_value = []
        mock_get_provider.return_value = mock_provider

        runner = CliRunner()
        result = runner.invoke(web_search, ["search", "测试", "--limit", "10"])
        assert result.exit_code == 0
        mock_provider.search.assert_called_once_with("测试", limit=10)

    @patch("winwin_cli.web_search.cli.get_provider")
    def test_search_no_results(self, mock_get_provider):
        """测试无搜索结果"""
        mock_provider = MagicMock()
        mock_provider.name = "duckduckgo"
        mock_provider.search.return_value = []
        mock_get_provider.return_value = mock_provider

        runner = CliRunner()
        result = runner.invoke(web_search, ["search", "xxxnotfoundxxx"])
        assert result.exit_code == 0
        assert "未找到" in result.output

    def test_search_requires_query(self):
        """测试 search 命令需要 query 参数"""
        runner = CliRunner()
        result = runner.invoke(web_search, ["search"])
        assert result.exit_code != 0


# ==================== 测试 Fetch 相关 ====================

class TestFetchResult:
    """测试 FetchResult 数据类"""

    def test_to_dict(self):
        result = FetchResult(url="https://a.com", content="# Hello", title="Title")
        d = result.to_dict()
        assert d["url"] == "https://a.com"
        assert d["content"] == "# Hello"
        assert d["title"] == "Title"


class TestMarkItDownProvider:
    """测试 MarkItDown 爬取后端"""

    @patch("winwin_cli.web_search.providers.run_markitdown")
    @patch("pathlib.Path.read_text")
    def test_fetch_success(self, mock_read_text, mock_run_mid):
        # 模拟 run_markitdown
        mock_read_text.return_value = "# Web Content"
        provider = MarkItDownProvider()
        result = provider.fetch("https://example.com")
        
        assert result.url == "https://example.com"
        assert result.content == "# Web Content"
        mock_run_mid.assert_called_once()

    def test_search_not_implemented(self):
        provider = MarkItDownProvider()
        with pytest.raises(NotImplementedError):
            provider.search("test")


class TestWebSearchFetchCommand:
    """测试 web-search fetch CLI 命令"""

    @patch("winwin_cli.web_search.cli.get_provider")
    def test_fetch_text_output(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.name = "markitdown"
        mock_provider.fetch.return_value = FetchResult(url="https://a.com", content="Markdown Content")
        mock_get_provider.return_value = mock_provider

        runner = CliRunner()
        result = runner.invoke(web_search, ["fetch", "https://a.com"])
        
        assert result.exit_code == 0
        assert "Markdown Content" in result.output

    @patch("winwin_cli.web_search.cli.get_provider")
    def test_fetch_json_output(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.name = "markitdown"
        mock_provider.fetch.return_value = FetchResult(url="https://a.com", content="MD", title="T")
        mock_get_provider.return_value = mock_provider

        runner = CliRunner()
        result = runner.invoke(web_search, ["fetch", "https://a.com", "--json"])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["url"] == "https://a.com"
        assert data["content"] == "MD"
