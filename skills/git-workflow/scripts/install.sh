#!/bin/bash
# Git Workflow 技能安装脚本
# 用法: ./install.sh <技能目录路径>

set -e

SKILL_DIR="${1:-.}"
INSTALL_DIR=".claude/plugins/skills"

echo "🚀 Installing Git Workflow skill..."
echo "   技能目录: $SKILL_DIR"

# 创建 .claude 目录（如果不存在）
mkdir -p "$INSTALL_DIR"

# 复制技能文件
cp "$SKILL_DIR/SKILL.md" "$INSTALL_DIR/git-workflow.md"

echo "✅ Git Workflow skill installed successfully!"
echo ""
echo "Usage:"
echo "  - When committing code, I'll check commit message format"
echo "  - When creating branches, I'll suggest proper naming"
echo "  - When preparing PRs, I'll review the checklist"
