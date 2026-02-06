---
name: git-workflow
description: Git 工作流助手 - 规范化 Git 提交、分支管理和代码审查流程
version: 1.0.0
author: winwin-cli
---

# Git 工作流助手

此技能帮助你遵循最佳实践进行 Git 操作，包括提交信息规范、分支管理和代码审查流程。

## 主要功能

### 1. 提交信息规范

遵循约定式提交（Conventional Commits）格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型（type）**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具链相关

**示例**：
```
feat(auth): add OAuth2 login support

Implement OAuth2 authentication with Google and GitHub providers.
Includes token refresh logic and error handling.

Closes #123
```

### 2. 分支管理策略

使用 Git Flow 或 GitHub Flow：

**主分支**：
- `main`: 生产环境代码
- `develop`: 开发分支（Git Flow）

**支持分支**：
- `feature/*`: 新功能开发
- `bugfix/*`: Bug 修复
- `hotfix/*`: 紧急修复
- `release/*`: 发布准备

**命名规范**：
```
feature/user-authentication
bugfix/login-validation-error
hotfix/security-patch-2025
release/v1.2.0
```

### 3. 代码审查检查清单

在创建 PR 前检查：
- [ ] 代码符合项目风格指南
- [ ] 所有测试通过
- [ ] 添加/更新了相关文档
- [ ] 提交信息清晰明确
- [ ] 没有调试代码或注释掉的代码
- [ ] 敏感信息已移除
- [ ] 适当的错误处理
- [ ] 性能影响已评估

### 4. 常用命令

**初始化工作流**：
```bash
git workflow init
```

**创建功能分支**：
```bash
git workflow feature user-auth
```

**提交并推送**：
```bash
git workflow commit "feat(auth): add user authentication"
git workflow push
```

**创建 PR 模板**：
```bash
git workflow pr
```

## 使用场景

当用户执行以下操作时，主动应用此技能：

1. **创建提交时**：检查提交信息格式，提供改进建议
2. **创建分支时**：建议合适的分支名称和类型
3. **准备 PR 时**：检查代码质量和审查清单
4. **合并代码时**：确保分支策略正确执行

## 示例对话

**用户**：帮我提交这些代码

**助手**：我注意到你修改了登录模块。根据约定式提交规范，建议使用以下提交信息：

```
feat(login): add remember me functionality

- Add checkbox for persistent session
- Store token in localStorage with 7-day expiry
- Implement auto-login on page reload

Refs: #456
```

是否使用此提交信息？或者你想修改？

**用户**：创建新分支

**助手**：你想要创建什么类型的分支？

- `feature` - 新功能开发
- `bugfix` - Bug 修复
- `hotfix` - 紧急生产修复
- `release` - 发布准备

请提供分支类型和简短描述，例如：`feature add-payment-gateway`

## 配置选项

项目根目录可创建 `.git-workflow.yaml` 配置文件：

```yaml
# 分支策略
branch_strategy: github-flow  # github-flow | git-flow

# 提交信息规范
commit_convention: conventional  # conventional | custom

# 强制检查
enforce_checks:
  test_required: true
  review_required: true
  docs_required: false

# PR 模板
pr_template: .github/PULL_REQUEST_TEMPLATE.md
```
