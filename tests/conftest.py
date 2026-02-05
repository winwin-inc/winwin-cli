"""测试配置文件"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def tmp_kb_path(tmp_path):
    """创建临时知识库路径"""
    kb_path = tmp_path / "test-knowledge-base"
    kb_path.mkdir()
    docs_dir = kb_path / "docs"
    docs_dir.mkdir()
    return kb_path


@pytest.fixture
def sample_documents(tmp_path):
    """创建示例文档"""
    kb_path = tmp_path / "sample-kb"
    kb_path.mkdir()
    docs_dir = kb_path / "docs"
    docs_dir.mkdir()

    documents = [
        ("api.md", "# API 文档\n\n介绍如何使用 API 接口。"),
        ("guide.md", "# 使用指南\n\n详细的使用说明。"),
        ("faq.md", "# 常见问题\n\nFAQ 内容。"),
    ]

    for filename, content in documents:
        (docs_dir / filename).write_text(content, encoding="utf-8")

    return kb_path


@pytest.fixture
def sample_config(tmp_path):
    """创建示例配置文件"""
    config_content = """
knowledge_bases:
  - name: test-kb
    path: /path/to/test-kb
    description: 测试知识库
    enabled: true
    extensions:
      - .md
      - .txt
"""
    config_file = tmp_path / "knowledge-bases.yaml"
    config_file.write_text(config_content, encoding="utf-8")
    return config_file
