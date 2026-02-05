# winwin-cli

CLI 封装工具，专为 AI 使用设计。

## 功能

### kb-search - 知识库检索工具

快速搜索你的文档，支持基于 BM25 的全文检索。

**特性：**
- 支持多种文档格式（Markdown、HTML、PDF、Office 文档等）
- 基于 BM25 算法的全文检索
- 自动文档索引和更新
- 中文分词支持（jieba）
- 多知识库管理
- JSON 输出格式，便于 AI 解析

**安装：**
```bash
# 使用 uvx 直接运行（无需安装）
uvx winwin-cli kb-search --help

# 或使用 uv pip 安装
uv pip install winwin-cli
winwin-cli kb-search --help
```

**快速开始：**
```bash
# 添加文档到知识库
winwin-cli kb-search add my-kb ./docs

# 搜索文档
winwin-cli kb-search search my-kb "查询关键词"

# 列出所有知识库
winwin-cli kb-search list
```

### convert - 文档转换工具

将各种格式的文档转换为 Markdown 或纯文本。

**支持格式：**
- Markdown (.md, .markdown)
- HTML (.html, .htm)
- PDF (.pdf)
- Word 文档 (.docx, .doc)
- PowerPoint (.pptx, .ppt)
- Excel (.xlsx, .xls)
- 纯文本 (.txt)

**使用方法：**
```bash
# 转换单个文件
winwin-cli convert document.docx output.md

# 转换为纯文本
winwin-cli convert document.pdf --format text
```

## 开发

**环境设置：**
```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate
```

**运行测试：**
```bash
uv pytest
```

**构建：**
```bash
uv build
```

## 项目结构

```
winwin-cli/
├── src/winwin_cli/       # 源代码
│   ├── cli.py           # 主入口
│   ├── convert.py       # 文档转换模块
│   └── kb_search/       # 知识库检索模块
│       ├── cli.py       # kb-search 命令行
│       ├── config.py    # 配置管理
│       ├── indexer.py   # 文档索引
│       ├── search.py    # 搜索引擎
│       ├── models.py    # 数据模型
│       └── commands/    # 子命令
├── tests/               # 测试文件
├── docs/                # 文档
└── pyproject.toml       # 项目配置
```

## 许可证

MIT License
