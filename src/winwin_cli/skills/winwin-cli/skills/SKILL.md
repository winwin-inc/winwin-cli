---
name: winwin-cli-skills
description: "⚡ 技能管理 - 列出、安装 Claude Code 技能。AI 友好，非交互式安装。"
version: 1.0.0
priority: 1
---

# winwin-cli skills

技能管理工具。

## 子命令

| 命令 | 说明 |
|------|------|
| `list` | 列出所有已注册的技能 |
| `register` | 注册本地技能 |
| `unregister` | 取消注册技能 |
| `info` | 查看技能详情 |
| `install` | 安装技能 |

## 命令

### list

```bash
winwin-cli skills list [--json]
```

- `--json`：JSON 格式输出（AI 推荐）

### register

```bash
winwin-cli skills register <path> [--name <name>]
```

注册本地技能目录。支持单个技能或技能集合（包含多个子技能）。

- `<path>`：技能目录路径
- `--name`：自定义技能名称

### unregister

```bash
winwin-cli skills unregister <skill-name>
```

从注册表中移除指定技能。

### info

```bash
winwin-cli skills info <skill-name>
```

### install

```bash
winwin-cli skills install <skill-name> [path] --platform <platform>
```

- `path`：安装路径（默认当前目录）
- `--platform`：目标平台（claude-code、opencode）

## AI 调用

```bash
# 列出技能
winwin-cli skills list --json

# 安装技能
winwin-cli skills install git-workflow /path/to/project --platform claude-code
```

## 安装位置

- Claude Code：`<path>/.claude/plugins/skills/`
- OpenCode：`<path>/.opencode/skills/`
