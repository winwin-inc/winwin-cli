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

### skills - 技能管理命令

安装和管理 Claude Code 等平台的技能。

**特性：**
- 交互式技能安装
- 支持多平台（Claude Code、OpenCode）
- 自动解析技能元数据
- JSON 输出格式，便于 AI 调用
- 自定义安装路径

**使用方法：**
```bash
# 列出所有可用技能
winwin-cli skills list

# 查看技能详情
winwin-cli skills info git-workflow

# 交互式安装（推荐）
winwin-cli skills install

# 安装到当前目录
winwin-cli skills install git-workflow

# 安装到指定目录
winwin-cli skills install git-workflow /path/to/project

# 指定平台
winwin-cli skills install git-workflow --platform claude-code

# JSON 格式输出（AI 调用）
winwin-cli skills list --json
```

**包含的技能：**
- `git-workflow` - Git 工作流助手（提交规范、分支管理、PR 检查）
- `code-review` - 代码审查助手（质量、安全、性能检查）

更多技能参见 [skills/README.md](skills/README.md)

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
│   ├── skills/          # 技能管理模块
│   │   ├── cli.py       # skills 命令行
│   │   └── __init__.py
│   └── kb_search/       # 知识库检索模块
│       ├── cli.py       # kb-search 命令行
│       ├── config.py    # 配置管理
│       ├── indexer.py   # 文档索引
│       ├── search.py    # 搜索引擎
│       ├── models.py    # 数据模型
│       └── commands/    # 子命令
├── skills/              # 技能定义目录
│   ├── git-workflow/    # Git 工作流技能
│   ├── code-review/     # 代码审查技能
│   └── README.md        # 技能文档
├── tests/               # 测试文件
├── docs/                # 文档
└── pyproject.toml       # 项目配置
```

## 许可证

MIT License
