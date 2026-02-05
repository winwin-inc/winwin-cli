#!/bin/bash
# 快速发布脚本

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "用法: ./scripts/release.sh <version>"
    echo "示例: ./scripts/release.sh v0.1.0"
    exit 1
fi

# 检查版本号格式
if [[ ! $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "错误: 版本号格式应为 v0.1.0"
    exit 1
fi

# 提取版本号（不含 v）
VERSION_NUMBER=${VERSION#v}

echo "🚀 开始发布 winwin-cli $VERSION"

# 1. 更新 pyproject.toml
echo "📝 更新版本号到 $VERSION_NUMBER"
sed -i.bak "s/^version = \".*\"/version = \"$VERSION_NUMBER\"/" pyproject.toml
rm -f pyproject.toml.bak

# 2. 运行测试
echo "🧪 运行测试..."
uv pytest

# 3. 构建包
echo "📦 构建包..."
uv build

# 4. 检查包
echo "🔍 检查包..."
twine check dist/*

# 5. 提交更改
echo "💾 提交版本更新..."
git add pyproject.toml
git commit -m "🔖 chore: bump version to $VERSION_NUMBER"

# 6. 创建标签
echo "🏷️  创建标签 $VERSION"
git tag -a "$VERSION" -m "Release $VERSION"

# 7. 询问是否推送
echo ""
echo "准备发布 $VERSION"
echo "文件："
ls -lh dist/
echo ""
read -p "是否推送到 GitHub 并发布到 PyPI？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⬆️  推送到 GitHub..."
    git push
    git push origin "$VERSION"

    echo "✅ GitHub Actions 将自动发布到 PyPI"
    echo "📊 查看进度: https://github.com/你的用户名/winwin-cli/actions"
else
    echo "❌ 取消发布"
    echo "提示: 手动推送使用: git push && git push origin $VERSION"
fi
