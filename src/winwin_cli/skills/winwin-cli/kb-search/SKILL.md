---
name: winwin-cli-kb-search
description: "⚡ 知识库检索 - 本地文档语义搜索、多知识库管理。JSON 输出，AI 友好。"
version: 1.0.0
priority: 1
---

# winwin-cli kb-search

知识库检索工具。

## 子命令

| 命令 | 说明 |
|------|------|
| `add` | 添加知识库 |
| `remove` | 移除知识库 |
| `enable` | 启用知识库 |
| `disable` | 禁用知识库 |
| `index` | 构建索引 |
| `search` | 搜索知识库 |
| `list` | 列出知识库 |
| `status` | 查看状态 |
| `info` | 显示系统信息

## 命令

### add

```bash
winwin-cli kb-search add <path> --name <name>
```

### index

```bash
winwin-cli kb-search index [<name>]
```

### search

```bash
winwin-cli kb-search search <query> [--kb <name>] [--json] [--limit <n>] [--content]
```

- `--kb`：指定知识库
- `--json`：JSON 输出（AI 推荐）
- `--limit`：最大结果数（默认 10）
- `--content`：返回完整内容

### list

```bash
winwin-cli kb-search list
```

### remove/enable/disable

```bash
winwin-cli kb-search remove <name>
winwin-cli kb-search enable <name>
winwin-cli kb-search disable <name>
```

### status

```bash
winwin-cli kb-search status [--json]
```

显示知识库统计信息（总数、启用/禁用数量、文档总数、索引状态）。

### info

```bash
winwin-cli kb-search info
```

显示知识库检索工具的版本和配置信息。

## 示例

```bash
# 添加并索引
winwin-cli kb-search add ./docs --name my-docs
winwin-cli kb-search index my-docs

# 搜索
winwin-cli kb-search search "API" --json --limit 5
winwin-cli kb-search search "API" --kb my-docs --json --content

# 管理
winwin-cli kb-search list
winwin-cli kb-search disable old-docs
winwin-cli kb-search remove temp-docs
```

## AI 调用

```bash
# Python 调用示例
result = subprocess.run([
    "winwin-cli", "kb-search", "search", "query",
    "--json", "--limit", "5"
], capture_output=True, text=True)
```
