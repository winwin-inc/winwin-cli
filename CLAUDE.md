# CLAUDE.md

本文档为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目用途

这是一个 CLI 封装工具项目，专为 AI 使用设计。它封装命令行工具，通过 `uvx` 实现无需安装即可运行。

## 常用命令

### 开发环境搭建
```bash
# 安装 uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖并进入虚拟环境
uv sync

# 激活虚拟环境
source .venv/bin/activate
```

### 构建与分发
```bash
# 构建分发包
uv build

# 发布到 PyPI（需要凭据）
uv publish
```

### 安装使用
```bash
# 无需安装，直接运行
uvx winwin-cli <command>

# 或安装后运行
uv pip install winwin-cli
winwin-cli <command>
```

### 测试
```bash
# 运行所有测试
uv pytest

# 运行指定测试
uv pytest tests/test_cli.py
```

## 项目架构

使用标准 Python CLI 工具结构（uv 管理）：
- `src/` - 源代码主目录
- `pyproject.toml` - 项目配置
- `.venv/` - 虚拟环境
- `tests/` - 单元测试目录

## CLI 工具设计规范

封装 CLI 工具时：
- `pyproject.toml` 中配置 `[project.scripts]` 入口点
- 使用 Click 或 Typer 进行命令行解析
- 为 AI 提供清晰的 JSON 输出格式
- 所有命令支持 `--help` 参数
- 确保非交互模式，便于 AI 自动化调用
