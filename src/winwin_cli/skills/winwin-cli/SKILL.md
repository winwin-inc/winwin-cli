---
name: winwin-cli
description: "⚡ AI 工具集 - 文档转换(PDF/Office/图片/音频转Markdown)、网络搜索与网页抓取、知识库检索、技能管理。AI 友好，非交互式调用。"
version: 1.1.0
priority: 1
---

# winwin-cli

AI 友好的命令行工具集。

## 子技能

| 子技能 | 说明 | 触发场景 |
|--------|------|---------|
| web-search | 网络搜索与抓取 | 在线搜索公开信息、抓取网页正文 |
| convert | 文档转换 | 转换文档、OCR、提取文本 |
| kb-search | 知识库检索 | 搜索本地知识库、语义检索 |
| skills | 技能管理 | 安装技能、管理本地技能 |

## 路由规则

1. **明确功能** → 直接使用对应子技能
2. **未指定功能** → 按关键词选择：
   - 搜索/网络搜索/爬虫/抓取/web-search/fetch → web-search
   - 转换/convert/pdf/docx/OCR → convert
   - 搜索/kb-search/知识库 → kb-search
   - 技能/skills/install → skills
3. **模糊不清** → 询问用户

## 子技能文档

每个子技能都有独立的文档：

| 子技能 | SKILL.md | examples.json |
|--------|----------|---------------|
| web-search | `web-search/SKILL.md` | `web-search/examples.json` |
| convert | `convert/SKILL.md` | `convert/examples.json` |
| kb-search | `kb-search/SKILL.md` | `kb-search/examples.json` |
| skills | `skills/SKILL.md` | `skills/examples.json` |

**详细用法和示例请参考各子技能文件**。

## 常用命令

```bash
# 网络搜索与抓取
winwin-cli web-search search "AI 最新进展" --json
winwin-cli web-search fetch https://example.com

# 文档转换
winwin-cli convert ./docs -o ./markdown --ext .pdf

# 知识库搜索
winwin-cli kb-search add ./docs --name my-docs
winwin-cli kb-search index my-docs
winwin-cli kb-search search "API" --json --limit 5

# 技能管理
winwin-cli skills list --json
winwin-cli skills install <name> --platform claude-code
```

## 输出建议

- **AI 调用**：使用 `--json` 获取结构化输出
- **错误处理**：检查命令退出码
