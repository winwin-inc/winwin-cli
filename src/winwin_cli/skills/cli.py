"""Skills CLI command - Manage and install skills."""

import os
import sys
import subprocess
import click
import yaml
from pathlib import Path
from typing import Optional, List


@click.group()
def skills():
    """技能管理命令 - 安装和管理 Claude Code 技能"""
    pass


@skills.command()
@click.argument("skill_name", required=False)
@click.argument("path", required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "--platform",
    type=click.Choice(["claude-code", "opencode"], case_sensitive=False),
    help="目标平台",
)
def install(skill_name: Optional[str], path: Optional[str], platform: Optional[str]):
    """安装技能到指定位置

    用法：
        winwin-cli skills install                           # 交互式选择，安装到当前目录
        winwin-cli skills install git-workflow              # 安装到当前目录
        winwin-cli skills install git-workflow ./my-project  # 安装到指定目录
        winwin-cli skills install git-workflow --platform claude-code
    """
    try:
        # 确定技能源目录（项目根目录的 skills/）
        project_root = Path(__file__).parent.parent.parent.parent
        skills_base_dir = project_root / "skills"

        if not skills_base_dir.exists():
            click.echo(f"错误: 技能目录不存在: {skills_base_dir}", err=True)
            sys.exit(1)

        # 确定安装路径（path 参数或当前目录）
        install_path = Path(path) if path else Path.cwd()

        # 如果没有指定技能名称，显示列表供选择
        if not skill_name:
            available_skills = _list_available_skills(skills_base_dir)
            if not available_skills:
                click.echo("未找到可用技能", err=True)
                sys.exit(1)

            click.echo("\n可用的技能：")
            for idx, skill in enumerate(available_skills, 1):
                click.echo(f"  {idx}. {skill['name']} - {skill.get('description', '无描述')}")

            # 让用户选择
            choice = click.prompt("\n选择要安装的技能（输入序号）", type=int)
            if choice < 1 or choice > len(available_skills):
                click.echo("无效的选择", err=True)
                sys.exit(1)

            skill_name = available_skills[choice - 1]["name"]
            click.echo(f"\n已选择: {skill_name}")

        # 加载技能信息
        skill_path = skills_base_dir / skill_name
        if not skill_path.exists():
            click.echo(f"错误: 技能不存在: {skill_name}", err=True)
            sys.exit(1)

        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            click.echo(f"错误: 技能文件不存在: {skill_file}", err=True)
            sys.exit(1)

        # 解析技能元数据
        skill_metadata = _parse_skill_metadata(skill_file)

        # 如果没有指定平台，交互式选择
        if not platform:
            click.echo("\n选择目标平台：")
            click.echo("  1. claude-code")
            click.echo("  2. opencode")

            platform_choice = click.prompt("\n选择平台（输入序号）", type=int)
            platform = "claude-code" if platform_choice == 1 else "opencode"

        # 执行安装
        _install_skill(skill_path, skill_name, install_path, platform, skill_metadata)

        click.echo(f"\n✅ 技能 '{skill_name}' 安装成功！")
        click.echo(f"   平台: {platform}")
        click.echo(f"   路径: {install_path}")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@skills.command()
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="以 JSON 格式输出（用于 AI 调用）",
)
def list(output_json: bool):
    """列出所有可用的技能"""
    try:
        # 技能源目录（项目根目录的 skills/）
        project_root = Path(__file__).parent.parent.parent.parent
        skills_base_dir = project_root / "skills"

        if not skills_base_dir.exists():
            click.echo(f"错误: 技能目录不存在: {skills_base_dir}", err=True)
            sys.exit(1)

        available_skills = _list_available_skills(skills_base_dir)

        if output_json:
            import json
            click.echo(json.dumps(available_skills, ensure_ascii=False, indent=2))
        else:
            if not available_skills:
                click.echo("未找到可用技能")
            else:
                click.echo(f"\n找到 {len(available_skills)} 个技能：\n")
                for skill in available_skills:
                    click.echo(f"📦 {skill['name']}")
                    click.echo(f"   描述: {skill.get('description', '无描述')}")
                    click.echo(f"   版本: {skill.get('version', 'N/A')}")
                    click.echo(f"   作者: {skill.get('author', 'N/A')}")
                    click.echo(f"   路径: {skill['path']}")
                    click.echo()

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@skills.command()
@click.argument("skill_name")
def info(skill_name: str):
    """显示技能详细信息"""
    try:
        # 技能源目录（项目根目录的 skills/）
        project_root = Path(__file__).parent.parent.parent.parent
        skills_base_dir = project_root / "skills"

        skill_path = skills_base_dir / skill_name
        if not skill_path.exists():
            click.echo(f"错误: 技能不存在: {skill_name}", err=True)
            sys.exit(1)

        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            click.echo(f"错误: 技能文件不存在: {skill_file}", err=True)
            sys.exit(1)

        # 解析技能元数据
        metadata = _parse_skill_metadata(skill_file)

        # 显示信息
        click.echo(f"\n📦 技能: {metadata.get('name', skill_name)}")
        click.echo(f"{'='*50}")
        click.echo(f"描述: {metadata.get('description', '无描述')}")
        click.echo(f"版本: {metadata.get('version', 'N/A')}")
        click.echo(f"作者: {metadata.get('author', 'N/A')}")
        click.echo(f"路径: {skill_path}")

        # 显示支持的文件
        click.echo(f"\n包含的文件:")
        for item in skill_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(skill_path)
                click.echo(f"  - {rel_path}")

        click.echo()

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


def _list_available_skills(skills_dir: Path) -> List[dict]:
    """扫描技能目录，返回可用技能列表"""
    skills = []

    for item in skills_dir.iterdir():
        if not item.is_dir():
            continue

        skill_file = item / "SKILL.md"
        if not skill_file.exists():
            continue

        # 解析元数据
        metadata = _parse_skill_metadata(skill_file)

        skills.append({
            "name": metadata.get("name", item.name),
            "description": metadata.get("description", "无描述"),
            "version": metadata.get("version", "N/A"),
            "author": metadata.get("author", "N/A"),
            "path": str(item),
        })

    return sorted(skills, key=lambda x: x["name"])


def _parse_skill_metadata(skill_file: Path) -> dict:
    """解析 SKILL.md 文件中的 YAML 前置元数据"""
    try:
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取 YAML 前置元数据（在 --- 之间）
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                return yaml.safe_load(yaml_content) or {}

        return {}
    except Exception as e:
        click.echo(f"警告: 无法解析技能元数据: {e}", err=True)
        return {}


def _install_skill(skill_path: Path, skill_name: str, install_path: Path, platform: str, metadata: dict):
    """执行技能安装"""
    if platform == "claude-code":
        _install_for_claude_code(skill_path, skill_name, install_path, metadata)
    elif platform == "opencode":
        _install_for_opencode(skill_path, skill_name, install_path, metadata)
    else:
        click.echo(f"错误: 不支持的平台: {platform}", err=True)
        sys.exit(1)


def _install_for_claude_code(skill_path: Path, skill_name: str, install_path: Path, metadata: dict):
    """安装到 Claude Code"""
    # 创建 .claude 目录结构
    claude_dir = install_path / ".claude" / "plugins" / "skills"
    claude_dir.mkdir(parents=True, exist_ok=True)

    # 复制 SKILL.md
    import shutil
    skill_file = skill_path / "SKILL.md"
    dest_file = claude_dir / f"{skill_name}.md"
    shutil.copy2(skill_file, dest_file)

    click.echo(f"✓ 已复制技能文件到: {dest_file}")

    # 如果有 install.sh 脚本，执行它（使用安全的 subprocess）
    install_script = skill_path / "scripts" / "install.sh"
    if install_script.exists():
        click.echo(f"✓ 执行安装脚本...")
        # 传递技能目录路径作为参数
        subprocess.run(["bash", str(install_script), str(skill_path)], cwd=install_path, check=True)


def _install_for_opencode(skill_path: Path, skill_name: str, install_path: Path, metadata: dict):
    """安装到 OpenCode（待实现）"""
    click.echo(f"警告: OpenCode 平台支持尚未实现", err=True)
    click.echo(f"提示: 你可以手动复制技能文件到合适位置", err=True)

    # 创建示例目录结构
    opencode_dir = install_path / ".opencode" / "skills"
    opencode_dir.mkdir(parents=True, exist_ok=True)

    # 复制技能文件
    import shutil
    skill_file = skill_path / "SKILL.md"
    dest_file = opencode_dir / f"{skill_name}.md"
    shutil.copy2(skill_file, dest_file)

    click.echo(f"✓ 已复制技能文件到: {dest_file}")
    click.echo(f"  (平台适配需要进一步配置)")


__all__ = ["skills"]
