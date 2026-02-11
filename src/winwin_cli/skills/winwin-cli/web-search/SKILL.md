---
name: web-search
description: "🌐 网络搜索与网页抓取 - 支持 DuckDuckGo 和 Tavily 搜索引擎。支持将网页内容抓取并转换为 Markdown 格式。"
---

# web-search

网络搜索与网页抓取功能。

## 主要命令

### 1. search - 搜索互联网
```bash
winwin-cli web-search search <query> [OPTIONS]
```
- `--limit` : 结果数量 (默认 5)
- `--provider` : 引擎 (duckduckgo, tavily)
- `--json` : 输出 JSON 格式 (AI 必备)

### 2. fetch - 抓取网页并转为 Markdown
```bash
winwin-cli web-search fetch <URL> [OPTIONS]
```
- `--provider` : 引擎 (markitdown, tavily)
- `-o, --output` : 保存到文件
- `--json` : 输出 JSON

### 3. providers - 列出可用引擎
```bash
winwin-cli web-search providers
```

## 触发场景

- 当用户要求搜索互联网信息时
- 当用户要求总结某个网页内容或抓取 URL 时
- 当需要实时新闻或最新技术文档时
