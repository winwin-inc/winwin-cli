# Skills 目录

此目录包含可安装的技能定义，用于 winwin-cli 的 skills 命令。

## 目录结构

```
skills/
├── git-workflow/              # Git 工作流技能
│   ├── SKILL.md              # 技能定义文件（必需）
│   ├── scripts/              # 可执行脚本
│   │   └── install.sh        # 安装脚本（可选）
│   ├── references/           # 参考文档（可选）
│   └── assets/               # 资源文件（可选）
│       └── pr-template.md    # PR 模板
└── code-review/              # 代码审查技能
    ├── SKILL.md
    ├── scripts/
    ├── references/
    └── assets/
        └── checklist.md
```

## 技能定义格式

每个技能是一个独立目录，必须包含 `SKILL.md` 文件：

### SKILL.md 结构

```markdown
---
name: skill-name              # 必需：技能名称
description: 技能描述          # 必需：简短描述
version: 1.0.0               # 可选：版本号
author: 作者名                # 可选：作者
---

# 技能标题

详细的技能说明、使用场景和示例...
```

**必需字段**：
- `name`: 技能名称（用于命令行引用）
- `description`: 技能描述（显示在列表中）

**可选字段**：
- `version`: 版本号
- `author`: 作者信息
- 其他自定义元数据

**Markdown 内容**：
- YAML 前置元数据后是技能的具体内容
- 包含使用场景、示例对话、配置选项等

### 可选目录

- **scripts/**: 安装脚本和其他辅助脚本
  - `install.sh`: 安装时自动执行的脚本
- **references/**: 相关文档和参考资料
- **assets/**: 模板、配置文件等资源

## 使用方法

### 列出所有可用技能

```bash
winwin-cli skills list
```

### 查看技能详情

```bash
winwin-cli skills info git-workflow
```

### 安装技能

**交互式安装**（推荐新手）：
```bash
# 默认安装到当前目录
winwin-cli skills install

# 安装到指定路径
winwin-cli skills install /path/to/project
```

**直接安装**（推荐熟练用户）：
```bash
# 安装到当前目录
winwin-cli skills install git-workflow

# 安装到指定目录
winwin-cli skills install git-workflow /path/to/project

# 指定平台
winwin-cli skills install git-workflow --platform claude-code
```

### JSON 输出（用于 AI 调用）

```bash
winwin-cli skills list --json
```

输出示例：
```json
[
  {
    "name": "git-workflow",
    "description": "Git 工作流助手",
    "version": "1.0.0",
    "author": "winwin-cli",
    "path": "/path/to/skills/git-workflow"
  }
]
```

## 支持的平台

### Claude Code
- **状态**: ✅ 完整支持
- **安装路径**: `.claude/plugins/skills/`
- **说明**: 技能文件会被复制到项目的 `.claude/plugins/skills/` 目录
- **自动执行**: 如果技能包含 `scripts/install.sh`，会自动执行

| 平台 | 状态 | 安装路径 |
|------|------|----------|
| Claude Code | ✅ 完整支持 | `.claude/plugins/skills/` |
| OpenCode | ⚠️ 基础支持 | `.opencode/skills/` |

## 创建新技能

### 1. 创建技能目录

```bash
mkdir -p skills/my-skill/{scripts,references,assets}
```

### 2. 创建 SKILL.md

```markdown
---
name: my-skill
description: 我的自定义技能
version: 1.0.0
author: Your Name
---

# 技能标题

技能描述和使用说明...
```

### 3. （可选）添加安装脚本

创建 `scripts/install.sh`：

```bash
#!/bin/bash
# 接收技能目录路径作为第一个参数
SKILL_DIR="${1:-.}"

# 你的安装逻辑
echo "Installing my skill..."
```

注意：
- 脚本会接收技能目录路径作为第一个参数
- 脚本在目标安装目录的上下文中执行

### 4. 测试技能

```bash
# 列出技能（应该包含你的新技能）
winwin-cli skills list

# 查看详情
winwin-cli skills info my-skill

# 测试安装
cd /tmp/test-install
winwin-cli skills install my-skill
```

## 技能最佳实践

### 1. 命名规范
- 使用小写字母和连字符：`git-workflow`
- 避免使用特殊字符和空格
- 名称应该具有描述性

### 2. 元数据
- 描述应该简洁明了（不超过 50 字）
- 包含版本号便于更新管理
- 添加作者信息用于识别

### 3. 内容组织
- 使用清晰的章节结构
- 提供具体的使用示例
- 包含常见场景的对话示例
- 说明配置选项和环境要求

### 4. 资源管理
- `assets/` 存放可复用的模板和配置
- `references/` 存放参考文档和链接
- `scripts/` 存放自动化脚本

## 示例技能

### git-workflow
Git 工作流助手，帮助你：
- 遵循约定式提交规范
- 使用正确的分支命名
- 创建规范的 Pull Request

### code-review
代码审查助手，提供：
- 代码质量检查
- 安全性审查
- 性能优化建议
- 错误处理检查

## 故障排除

### 技能未显示在列表中
- 检查 `SKILL.md` 文件是否存在
- 验证 YAML 前置元数据格式正确
- 确认 `name` 和 `description` 字段存在

### 安装失败
- 检查目标路径的写入权限
- 验证平台名称拼写正确
- 查看 `scripts/install.sh` 是否有执行权限

### 技能未生效
- Claude Code: 检查 `.claude/plugins/skills/` 目录
- 确认技能文件格式正确
- 查看平台日志了解错误信息

## 进阶用法

### 自定义技能目录

```bash
winwin-cli skills list --skills-dir /path/to/custom/skills
winwin-cli skills install my-skill --skills-dir /path/to/custom/skills
```

### 批量安装脚本

```bash
#!/bin/bash
for skill in git-workflow code-review; do
  winwin-cli skills install "$skill" --platform claude-code
done
```

### 集成到 CI/CD

```yaml
# .github/workflows/setup.yml
- name: Install Claude Code Skills
  run: |
    winwin-cli skills install git-workflow --platform claude-code
    winwin-cli skills install code-review --platform claude-code
```

## 贡献

欢迎创建和分享新的技能！贡献指南：

1. Fork 项目
2. 在 `skills/` 目录创建新技能
3. 确保遵循技能定义格式
4. 添加示例和文档
5. 提交 Pull Request

## 许可

根据项目许可证共享技能。
