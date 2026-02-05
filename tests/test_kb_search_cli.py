"""测试 CLI 模块（简化版）"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

from winwin_cli.kb_search.cli import kb_search, search, list_kb, index, add, remove, enable, disable


class TestKbSearchCLI:
    """测试 kb-search CLI"""

    def test_cli_group_exists(self):
        """测试 CLI 组存在"""
        runner = CliRunner()
        result = runner.invoke(kb_search, ["--help"])

        assert result.exit_code == 0
        assert "知识库检索工具" in result.output

    def test_cli_subcommands(self):
        """测试 CLI 子命令"""
        runner = CliRunner()
        result = runner.invoke(kb_search, ["--help"])

        assert result.exit_code == 0
        assert "search" in result.output
        assert "list" in result.output
        assert "index" in result.output
        assert "add" in result.output
        assert "remove" in result.output


class TestSearchCommand:
    """测试 search 命令"""

    @patch("winwin_cli.kb_search.commands.search.load_global_config")
    @patch("winwin_cli.kb_search.commands.search.SearchEngine")
    def test_search_basic(self, mock_engine_class, mock_config):
        """测试基本搜索"""
        mock_config.return_value = []
        mock_engine = MagicMock()
        mock_engine.execute.return_value = {
            "format": "text",
            "output": "找到 1 个结果",
        }
        mock_engine_class.return_value = mock_engine

        runner = CliRunner()
        result = runner.invoke(search, ["测试"])

        assert result.exit_code == 0
        assert "找到" in result.output

    @patch("winwin_cli.kb_search.commands.search.load_global_config")
    @patch("winwin_cli.kb_search.commands.search.SearchEngine")
    def test_search_json_output(self, mock_engine_class, mock_config):
        """测试 JSON 格式输出"""
        mock_config.return_value = []
        mock_engine = MagicMock()
        mock_engine.execute.return_value = {
            "format": "json",
            "query": "API",
            "total_results": 1,
            "results": [],
        }
        mock_engine_class.return_value = mock_engine

        runner = CliRunner()
        result = runner.invoke(search, ["API", "--json"])

        assert result.exit_code == 0


class TestListKbCommand:
    """测试 list 命令"""

    @patch("winwin_cli.kb_search.commands.list.load_global_config")
    def test_list_empty(self, mock_config):
        """测试空列表"""
        mock_config.return_value = []

        runner = CliRunner()
        result = runner.invoke(list_kb, [])

        assert result.exit_code == 0
        assert "未配置" in result.output

    @patch("winwin_cli.kb_search.commands.list.load_global_config")
    def test_list_with_knowledge_bases(self, mock_config):
        """测试列出知识库"""
        from winwin_cli.kb_search.models import KnowledgeBaseConfig

        mock_config.return_value = [
            KnowledgeBaseConfig(
                name="test-kb",
                path="/test/path",
                enabled=True,
            )
        ]

        runner = CliRunner()
        result = runner.invoke(list_kb, [])

        assert result.exit_code == 0
        assert "test-kb" in result.output

    @patch("winwin_cli.kb_search.commands.list.load_global_config")
    def test_list_json_output(self, mock_config):
        """测试 JSON 输出"""
        mock_config.return_value = []

        runner = CliRunner()
        result = runner.invoke(list_kb, ["--json"])

        assert result.exit_code == 0
        assert "knowledge_bases" in result.output


class TestIndexCommand:
    """测试 index 命令"""

    @patch("winwin_cli.kb_search.commands.index.load_global_config")
    def test_index_requires_kb_or_all(self, mock_config):
        """测试索引需要知识库或全部"""
        mock_config.return_value = []

        runner = CliRunner()
        result = runner.invoke(index, [])

        assert result.exit_code == 1
        assert "未配置" in result.output


class TestAddCommand:
    """测试 add 命令"""

    def test_add_requires_name_and_path(self):
        """测试需要名称和路径"""
        runner = CliRunner()
        result = runner.invoke(add, [])

        assert result.exit_code == 2

    @patch("winwin_cli.kb_search.commands.add.KnowledgeBaseLoader")
    def test_add_success(self, mock_loader_class):
        """测试添加成功"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_loader = MagicMock()
            mock_loader.load.return_value = []
            mock_loader_class.return_value = mock_loader

            runner = CliRunner()
            result = runner.invoke(add, ["test-kb", tmpdir])

            assert result.exit_code == 0
            assert "添加知识库" in result.output


class TestRemoveCommand:
    """测试 remove 命令"""

    def test_remove_success(self):
        """测试移除成功"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 先添加
            loader = __import__("winwin_cli.kb_search.config", fromlist=["KnowledgeBaseLoader"]).KnowledgeBaseLoader()
            config_model = __import__("winwin_cli.kb_search.models", fromlist=["KnowledgeBaseConfig"]).KnowledgeBaseConfig

            kb_path = Path(tmpdir) / "docs"
            kb_path.mkdir()

            configs = [config_model(name="test-kb", path=str(kb_path))]
            loader.save(configs)

            # 再移除
            runner = CliRunner()
            result = runner.invoke(remove, ["test-kb"])

            assert result.exit_code == 0
            assert "移除" in result.output

    def test_remove_nonexistent(self):
        """测试移除不存在的知识库"""
        runner = CliRunner()
        result = runner.invoke(remove, ["nonexistent"])

        assert result.exit_code == 1


class TestEnableCommand:
    """测试 enable 命令"""

    def test_enable_success(self):
        """测试启用成功"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 先添加并禁用
            loader = __import__("winwin_cli.kb_search.config", fromlist=["KnowledgeBaseLoader"]).KnowledgeBaseLoader()
            config_model = __import__("winwin_cli.kb_search.models", fromlist=["KnowledgeBaseConfig"]).KnowledgeBaseConfig

            kb_path = Path(tmpdir) / "docs"
            kb_path.mkdir()

            configs = [config_model(name="test-kb", path=str(kb_path), enabled=False)]
            loader.save(configs)

            # 再启用
            runner = CliRunner()
            result = runner.invoke(enable, ["test-kb"])

            assert result.exit_code == 0
            assert "启用" in result.output


class TestDisableCommand:
    """测试 disable 命令"""

    def test_disable_success(self):
        """测试禁用成功"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 先添加
            loader = __import__("winwin_cli.kb_search.config", fromlist=["KnowledgeBaseLoader"]).KnowledgeBaseLoader()
            config_model = __import__("winwin_cli.kb_search.models", fromlist=["KnowledgeBaseConfig"]).KnowledgeBaseConfig

            kb_path = Path(tmpdir) / "docs"
            kb_path.mkdir()

            configs = [config_model(name="test-kb", path=str(kb_path), enabled=True)]
            loader.save(configs)

            # 再禁用
            runner = CliRunner()
            result = runner.invoke(disable, ["test-kb"])

            assert result.exit_code == 0
            assert "禁用" in result.output
