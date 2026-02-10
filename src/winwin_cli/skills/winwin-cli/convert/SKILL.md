---
name: winwin-cli-convert
description: "⚡ 文档转换 - PDF/Office/图片/音频/视频 转 Markdown。AI 友好，支持批量转换。"
version: 1.0.0
priority: 1
---

# winwin-cli convert

文档转换工具。

## 支持格式

| 类别 | 格式 |
|------|------|
| Office | .docx, .doc, .pptx, .xlsx, .xls |
| PDF | .pdf |
| 图片（OCR） | .jpg, .jpeg, .png, .gif, .bmp, .webp |
| 音频 | .wav, .mp3, .m4a |
| 视频 | .mp4, .avi, .mov, .mkv |
| 文本 | .html, .htm, .csv, .json, .xml |

## 命令

```bash
winwin-cli convert <input> [-o <output>] [--ext <ext>] [--overwrite]
```

| 参数 | 简写 | 说明 |
|------|------|------|
| `input` | - | 输入文件或目录（必需） |
| `--output` | `-o` | 输出路径 |
| `--ext` | `-e` | 按扩展名过滤 |
| `--overwrite` | `-f` | 覆盖已存在文件 |

## 示例

```bash
# 单文件转换
winwin-cli convert document.docx -o output.md

# 批量转换
winwin-cli convert ./docs -o ./markdown --ext .pdf --ext .docx

# 覆盖模式
winwin-cli convert ./docs --overwrite

# OCR 图片
winwin-cli convert ./images --ext .png --ext .jpg
```

## AI 调用

```bash
winwin-cli convert /path/to/file.ext -o /path/to/output.md
```
