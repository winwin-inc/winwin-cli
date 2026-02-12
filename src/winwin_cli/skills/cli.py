"""Skills CLI command - Manage and install skills."""

import os
import sys
import subprocess
import tempfile
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import click
import yaml
import requests
from pathlib import Path
from typing import Optional, List, Tuple, Dict


# ==================== 注册表管理 ====================

def _get_registry_file() -> Path:
    """获取注册表文件路径"""
    config_dir = Path.home() / ".winwin-cli"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "registered-skills.yaml"


def _get_default_skill_path() -> Path:
    """获取默认技能（winwin-cli）的路径"""
    # 获取当前文件的目录
    current_dir = Path(__file__).parent
    # 默认技能位于 src/winwin_cli/skills/winwin-cli/
    return current_dir / "winwin-cli"


def _ensure_default_skills():
    """确保默认技能已注册（不调用 _load_registry 以避免递归）"""
    registry_file = _get_registry_file()

    # 读取现有注册表
    if registry_file.exists():
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                registry = yaml.safe_load(f) or {"skills": []}
        except Exception:
            registry = {"skills": []}
    else:
        registry = {"skills": []}

    # 检查 winwin-cli 技能是否已注册
    winwin_skill = None
    for skill in registry.get("skills", []):
        if skill.get("name") == "winwin-cli":
            winwin_skill = skill
            break

    if winwin_skill:
        # 检查路径是否仍然有效
        skill_path = Path(winwin_skill["path"])
        if skill_path.exists() and (skill_path / "SKILL.md").exists():
            return  # 已注册且路径有效
        else:
            # 路径无效，需要更新
            registry["skills"] = [s for s in registry.get("skills", []) if s.get("name") != "winwin-cli"]

    # 注册默认的 winwin-cli 技能
    default_skill_path = _get_default_skill_path()
    if default_skill_path.exists() and (default_skill_path / "SKILL.md").exists():
        skill_file = default_skill_path / "SKILL.md"
        metadata = _parse_skill_metadata(skill_file)

        registry["skills"].append({
            "name": "winwin-cli",
            "path": str(default_skill_path.absolute()),
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "source": "builtin",
            "description": "内置默认技能"
        })

        # 保存注册表
        try:
            with open(registry_file, "w", encoding="utf-8") as f:
                yaml.dump(registry, f, allow_unicode=True, default_flow_style=False)
        except Exception:
            # 静默失败，避免在初始化时报错
            pass


def _load_registry() -> Dict:
    """加载注册表"""
    registry_file = _get_registry_file()

    # 如果不存在，尝试初始化默认技能
    if not registry_file.exists():
        _ensure_default_skills()

    # 再次检查是否存在
    if registry_file.exists():
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                registry = yaml.safe_load(f) or {"skills": []}
                # 再次确保至少有基本结构
                if not isinstance(registry, dict):
                    registry = {"skills": []}
                if "skills" not in registry:
                    registry["skills"] = []

                # 始终确保默认技能已注册（包括注册表已存在但缺少默认技能的情况）
                _ensure_default_skills()
                # 重新读取以获取更新后的注册表
                with open(registry_file, "r", encoding="utf-8") as f:
                    registry = yaml.safe_load(f) or {"skills": []}

                return registry
        except Exception as e:
            click.echo(f"警告: 无法加载注册表: {e}", err=True)
            return {"skills": []}

    # 如果还是不存在（可能因为权限问题或内置技能目录缺失），返回空结构而不是递归
    return {"skills": []}


def _save_registry(registry: Dict):
    """保存注册表"""
    registry_file = _get_registry_file()
    try:
        with open(registry_file, "w", encoding="utf-8") as f:
            yaml.dump(registry, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        click.echo(f"错误: 无法保存注册表: {e}", err=True)
        sys.exit(1)


def _find_registered_skill(skill_name: str) -> Optional[Dict]:
    """从注册表中查找技能"""
    registry = _load_registry()
    for skill in registry.get("skills", []):
        if skill.get("name") == skill_name:
            return skill
    return None


def _list_registered_skills() -> List[Dict]:
    """列出所有已注册的技能（自动刷新元数据）"""
    registry = _load_registry()
    skills = registry.get("skills", [])

    # 自动刷新每个技能的元数据
    updated_skills = []
    needs_save = False

    for skill in skills:
        skill_path = Path(skill.get("path", ""))

        # 检查路径是否仍然有效
        if skill_path.exists() and (skill_path / "SKILL.md").exists():
            # 重新解析元数据
            skill_file = skill_path / "SKILL.md"
            metadata = _parse_skill_metadata(skill_file)

            # 如果元数据有变化，更新注册表
            if metadata and metadata != skill.get("metadata", {}):
                skill["metadata"] = metadata
                needs_save = True

            updated_skills.append(skill)
        else:
            # 路径无效，保留原记录但可能标记为无效
            updated_skills.append(skill)

    # 如果有更新，保存注册表
    if needs_save:
        registry["skills"] = updated_skills
        try:
            registry_file = _get_registry_file()
            with open(registry_file, "w", encoding="utf-8") as f:
                yaml.dump(registry, f, allow_unicode=True, default_flow_style=False)
        except Exception:
            # 静默失败，避免影响列表显示
            pass

    return updated_skills


def _get_cache_dir() -> Path:
    """获取技能缓存目录"""
    config_dir = Path.home() / ".winwin-cli"
    config_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = config_dir / "skills-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _download_and_register_github_skill(github_url: str, ref: str = "main", repo: Optional[str] = None) -> str:
    """从 GitHub URL 下载技能并注册到本地缓存

    Args:
        github_url: GitHub 技能目录 URL
        ref: Git 分支或标签（默认: main）
        repo: 覆盖默认的 GitHub 仓库（格式: owner/repo）

    Returns:
        注册的技能名称
    """
    click.echo(f"📥 正在从 GitHub 下载技能...")
    click.echo(f"   URL: {github_url}")
    if repo:
        click.echo(f"   仓库: {repo}")
    if ref != "main":
        click.echo(f"   分支: {ref}")

    # 下载技能到临时目录
    skill_temp_dir = _resolve_and_download_skill(github_url, ref, repo)
    if not skill_temp_dir:
        click.echo(f"❌ 错误: 下载技能失败", err=True)
        sys.exit(1)

    try:
        # 获取技能名称
        skill_name = _get_skill_name(skill_temp_dir)

        # 验证 SKILL.md
        skill_file = skill_temp_dir / "SKILL.md"
        if not skill_file.exists():
            click.echo(f"❌ 错误: 下载的内容不是有效的技能（缺少 SKILL.md）", err=True)
            sys.exit(1)

        # 解析元数据
        metadata = _parse_skill_metadata(skill_file)

        # 复制到缓存目录
        cache_dir = _get_cache_dir()
        cached_skill_dir = cache_dir / skill_name

        # 如果已存在，先删除
        if cached_skill_dir.exists():
            shutil.rmtree(cached_skill_dir)

        # 复制到缓存
        shutil.copytree(skill_temp_dir, cached_skill_dir)

        click.echo(f"   ✓ 已缓存到: {cached_skill_dir}")

        # 检查是否已注册
        existing = _find_registered_skill(skill_name)
        if existing and existing.get("path") != str(cached_skill_dir):
            click.echo(f"⚠️  技能 '{skill_name}' 已注册，更新为缓存路径")

        # 注册到注册表
        registry = _load_registry()
        registry["skills"] = [s for s in registry.get("skills", []) if s.get("name") != skill_name]
        registry["skills"].append({
            "name": skill_name,
            "path": str(cached_skill_dir),
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "source": "github",
            "source_url": github_url
        })
        _save_registry(registry)

        click.echo(f"   ✓ 已注册到本地: {skill_name}")

        return skill_name

    finally:
        # 清理临时目录
        if skill_temp_dir and skill_temp_dir.exists():
            shutil.rmtree(skill_temp_dir, ignore_errors=True)


@click.group()
def skills():
    """技能管理命令 - 安装和管理 Claude Code 技能"""
    pass


def _scan_skills_in_directory(root_dir: Path) -> List[Path]:
    """扫描目录中的所有技能（包含 SKILL.md 的子目录）

    Args:
        root_dir: 根目录

    Returns:
        包含 SKILL.md 的目录列表
    """
    skill_dirs = []

    # 如果根目录直接包含 SKILL.md，则它本身就是一个技能
    if (root_dir / "SKILL.md").exists():
        return [root_dir]

    # 否则扫描子目录
    for item in root_dir.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            skill_dirs.append(item)

    return sorted(skill_dirs)


@skills.command()
@click.argument("skill_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "--name",
    help="自定义技能名称（默认从 SKILL.md 读取）",
)
def register(skill_path: str, name: Optional[str]):
    """注册本地技能到 winwin-cli

    用法：
        winwin-cli skills register /path/to/skill
        winwin-cli skills register /path/to/skills-collection  # 批量注册子目录中的所有技能
        winwin-cli skills register /path/to/skill --name my-custom-name
    """
    try:
        skill_dir = Path(skill_path)

        # 扫描技能目录
        skill_dirs = _scan_skills_in_directory(skill_dir)

        if not skill_dirs:
            click.echo(f"❌ 错误: 目录中未找到任何技能", err=True)
            click.echo(f"   目录: {skill_dir}", err=True)
            click.echo(f"\n要求:", err=True)
            click.echo(f"  - 单个技能: 目录必须包含 SKILL.md", err=True)
            click.echo(f"  - 技能集合: 子目录中需包含 SKILL.md", err=True)
            sys.exit(1)

        # 如果找到多个技能，显示批量注册信息
        if len(skill_dirs) > 1:
            click.echo(f"📂 发现 {len(skill_dirs)} 个技能目录：")
            for sd in skill_dirs:
                click.echo(f"   - {sd.name}")
            click.echo()

        # 批量注册
        success_count = 0
        failed_count = 0

        for current_skill_dir in skill_dirs:
            try:
                # 验证 SKILL.md 存在
                skill_file = current_skill_dir / "SKILL.md"
                if not skill_file.exists():
                    click.echo(f"⚠️  跳过 {current_skill_dir.name}: 缺少 SKILL.md", err=True)
                    failed_count += 1
                    continue

                # 解析元数据
                metadata = _parse_skill_metadata(skill_file)

                # 确定技能名称
                if len(skill_dirs) == 1 and name:
                    # 单个注册且指定了名称
                    skill_name = name
                elif metadata.get("name"):
                    # 从 SKILL.md 读取名称
                    skill_name = metadata["name"]
                else:
                    # 使用目录名
                    skill_name = current_skill_dir.name

                # 检查是否已注册
                existing = _find_registered_skill(skill_name)
                if existing:
                    click.echo(f"⚠️  技能 '{skill_name}' 已经注册", err=True)
                    click.echo(f"   旧路径: {existing.get('path')}", err=True)
                    click.echo(f"   新路径: {current_skill_dir}", err=True)

                    if not click.confirm(f"\n是否更新 '{skill_name}' 的注册路径？"):
                        click.echo(f"   ⊗ 跳过: {skill_name}", err=True)
                        failed_count += 1
                        continue

                # 加载注册表
                registry = _load_registry()

                # 移除旧的注册（如果存在）
                registry["skills"] = [s for s in registry.get("skills", []) if s.get("name") != skill_name]

                # 添加新注册
                registry["skills"].append({
                    "name": skill_name,
                    "path": str(current_skill_dir.absolute()),
                    "registered_at": datetime.now().isoformat(),
                    "metadata": metadata or {}
                })

                # 保存注册表
                _save_registry(registry)

                click.echo(f"✅ 注册 '{skill_name}'")
                success_count += 1

            except Exception as e:
                click.echo(f"❌ 注册失败: {current_skill_dir.name} - {e}", err=True)
                failed_count += 1

        # 显示总结
        click.echo(f"\n{'='*60}")
        if success_count > 0:
            click.echo(f"✅ 成功注册 {success_count} 个技能")
        if failed_count > 0:
            click.echo(f"⚠️  失败 {failed_count} 个技能", err=True)

        if len(skill_dirs) == 1:
            # 单个技能注册，显示详细信息
            skill_dir = skill_dirs[0]
            skill_file = skill_dir / "SKILL.md"
            metadata = _parse_skill_metadata(skill_file)

            click.echo(f"   路径: {skill_dir}")
            if metadata.get("description"):
                click.echo(f"   描述: {metadata.get('description')}")
            if metadata.get("version"):
                click.echo(f"   版本: {metadata.get('version')}")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@skills.command()
@click.argument("skill_name")
def unregister(skill_name: str):
    """取消注册技能

    用法：
        winwin-cli skills unregister skill-name
    """
    try:
        # 查找技能
        registry = _load_registry()
        skills_list = registry.get("skills", [])

        # 查找并移除
        found = False
        new_skills = []
        for skill in skills_list:
            if skill.get("name") == skill_name:
                found = True
                click.echo(f"取消注册技能: {skill_name}")
                click.echo(f"   路径: {skill.get('path')}")
            else:
                new_skills.append(skill)

        if not found:
            click.echo(f"❌ 错误: 未找到注册的技能 '{skill_name}'", err=True)
            click.echo(f"\n已注册的技能:", err=True)
            for skill in skills_list:
                click.echo(f"  - {skill.get('name')}", err=True)
            sys.exit(1)

        # 保存更新后的注册表
        registry["skills"] = new_skills
        _save_registry(registry)

        click.echo(f"✅ 技能 '{skill_name}' 已取消注册")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@skills.command()
@click.argument("skill_spec", required=False)
@click.argument("path", required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "--to", "target_path",
    type=click.Path(file_okay=False, dir_okay=True),
    help="安装目标目录",
)
@click.option(
    "--platform",
    type=click.Choice(["claude-code", "opencode"], case_sensitive=False),
    help="目标平台",
)
@click.option(
    "--branch", "ref",
    default="main",
    help="Git 分支或标签（默认: main）",
)
@click.option(
    "--repo",
    help="覆盖默认的 GitHub 仓库（格式: owner/repo）",
)
def install(skill_spec: Optional[str], path: Optional[str], target_path: Optional[str], platform: Optional[str], ref: str, repo: Optional[str]):
    """安装技能

    工作流程：
        1. 技能名称 → 从注册表查找 → 安装
        2. 本地目录 → 注册 → 安装
        3. 无参数 → 交互式从注册表选择

    用法：
        winwin-cli skills install                      # 交互式选择已注册的技能
        winwin-cli skills install skill-name          # 从注册表安装指定技能
        winwin-cli skills install /path/to/local/skill # 从本地目录注册并安装
        winwin-cli skills install skill-name --to /target  # 指定安装目标
    """
    try:
        # 确定安装路径（优先使用 --to，其次是 path，最后是当前目录）
        if target_path:
            install_path = Path(target_path)
            # 如果 --to 指定的目录不存在，创建它
            install_path.mkdir(parents=True, exist_ok=True)
        elif path:
            install_path = Path(path)
        else:
            install_path = Path.cwd()

        # 如果没有指定技能，从注册表显示列表供选择
        if not skill_spec:
            skill_spec = _interactive_select_from_registry()
            if not skill_spec:
                click.echo("未选择技能", err=True)
                sys.exit(1)

        # 智能识别 skill_spec 类型
        # 1. GitHub URL
        if skill_spec.startswith("https://") or skill_spec.startswith("http://"):
            # 下载并注册到本地缓存
            skill_name = _download_and_register_github_skill(skill_spec, ref, repo)

            # 从注册表查找并安装
            registered_skill = _find_registered_skill(skill_name)
            if not registered_skill:
                click.echo(f"❌ 错误: 注册失败", err=True)
                sys.exit(1)

            skill_dir = Path(registered_skill["path"])
            metadata = registered_skill.get("metadata", {})

            # 如果没有指定平台，交互式选择
            if not platform:
                click.echo("\n选择目标平台：")
                click.echo("  1. claude-code")
                click.echo("  2. opencode")
                platform_choice = click.prompt("\n选择平台（输入序号）", type=int)
                platform = "claude-code" if platform_choice == 1 else "opencode"

            click.echo(f"\n📦 正在安装...")
            _install_from_local_directory(skill_dir, install_path, platform)

            dest_skill_dir = install_path / ".claude" / "skills" / skill_name if platform == "claude-code" else install_path / ".opencode" / "skills" / skill_name

            click.echo(f"\n✅ 技能 '{skill_name}' 安装成功！")
            click.echo(f"   来源: GitHub（已缓存到本地）")
            click.echo(f"   平台: {platform}")
            click.echo(f"   目标: {install_path}")
            click.echo(f"   技能路径: {dest_skill_dir}")

            if metadata.get("description"):
                click.echo(f"\n📋 {metadata.get('description')}")
            if metadata.get("version"):
                click.echo(f"   版本: {metadata.get('version')}")

            return

        # 2. 本地目录
        elif Path(skill_spec).is_dir():
            click.echo(f"🔍 检测到本地目录: {skill_spec}")
            skill_dir = Path(skill_spec)

            # 验证 SKILL.md
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                click.echo(f"   ✗ 缺少 SKILL.md", err=True)
                click.echo(f"❌ 错误: 目录中未找到 SKILL.md", err=True)
                click.echo(f"   目录: {skill_dir}", err=True)
                click.echo(f"   要求: 技能目录必须包含 SKILL.md 文件", err=True)

                # 列出目录内容，帮助调试
                try:
                    contents = list(skill_dir.iterdir())[:5]
                    if contents:
                        click.echo(f"   目录内容: {', '.join([p.name for p in contents])}", err=True)
                except Exception:
                    pass

                sys.exit(1)

            click.echo(f"   ✓ 找到 SKILL.md")

            # 解析元数据
            metadata = _parse_skill_metadata(skill_file)
            skill_name = _get_skill_name(skill_dir)

            if metadata.get("name"):
                click.echo(f"   ✓ 技能名称: {metadata['name']}")
            if metadata.get("version"):
                click.echo(f"   ✓ 版本: {metadata['version']}")

            # 注册到本地（如果尚未注册）
            click.echo(f"\n📋 正在注册技能...")
            existing = _find_registered_skill(skill_name)
            if existing:
                if existing.get("path") != str(skill_dir.absolute()):
                    click.echo(f"⚠️  技能 '{skill_name}' 已注册，但路径不同")
                    click.echo(f"   旧路径: {existing.get('path')}")
                    click.echo(f"   新路径: {skill_dir}")
                    if not click.confirm(f"\n是否更新注册路径？"):
                        # 使用现有注册路径
                        skill_dir = Path(existing["path"])
                        click.echo(f"   使用已注册的路径")
                else:
                    click.echo(f"   ✓ 技能已注册")
            else:
                # 添加到注册表
                registry = _load_registry()
                registry["skills"].append({
                    "name": skill_name,
                    "path": str(skill_dir.absolute()),
                    "registered_at": datetime.now().isoformat(),
                    "metadata": metadata or {},
                    "source": "local"
                })
                _save_registry(registry)
                click.echo(f"   ✓ 已注册: {skill_name}")

            # 如果没有指定平台，交互式选择
            if not platform:
                click.echo("\n选择目标平台：")
                click.echo("  1. claude-code")
                click.echo("  2. opencode")
                platform_choice = click.prompt("\n选择平台（输入序号）", type=int)
                platform = "claude-code" if platform_choice == 1 else "opencode"

            # 从注册的路径安装
            click.echo(f"\n📦 正在安装...")
            _install_from_local_directory(skill_dir, install_path, platform)

            dest_skill_dir = install_path / ".claude" / "skills" / skill_name if platform == "claude-code" else install_path / ".opencode" / "skills" / skill_name

            click.echo(f"\n✅ 技能 '{skill_name}' 安装成功！")
            click.echo(f"   来源: 本地目录（已注册）")
            click.echo(f"   平台: {platform}")
            click.echo(f"   目标: {install_path}")
            click.echo(f"   技能路径: {dest_skill_dir}")

            if metadata.get("description"):
                click.echo(f"\n📋 {metadata.get('description')}")
            if metadata.get("version"):
                click.echo(f"   版本: {metadata.get('version')}")

            return

        # 3. 技能名称（优先从注册表查找）
        else:
            # 先尝试从注册表查找
            if skill_spec and "/" not in skill_spec and not skill_spec.startswith("https://"):
                registered_skill = _find_registered_skill(skill_spec)
                if registered_skill:
                    # 从注册表安装
                    click.echo(f"📋 从注册表找到技能: {skill_spec}")
                    skill_dir = Path(registered_skill["path"])

                    if not skill_dir.exists():
                        click.echo(f"❌ 错误: 注册的技能路径不存在: {skill_dir}", err=True)
                        click.echo(f"提示: 请使用 'winwin-cli skills unregister {skill_spec}' 取消注册", err=True)
                        click.echo(f"      然后使用 'winwin-cli skills register /new/path' 重新注册", err=True)
                        sys.exit(1)

                    # 验证 SKILL.md
                    skill_file = skill_dir / "SKILL.md"
                    if not skill_file.exists():
                        click.echo(f"❌ 错误: 技能目录中未找到 SKILL.md: {skill_dir}", err=True)
                        sys.exit(1)

                    # 解析元数据显示
                    metadata = _parse_skill_metadata(skill_file)
                    if metadata.get("name"):
                        click.echo(f"   ✓ 技能名称: {metadata['name']}")
                    if metadata.get("version"):
                        click.echo(f"   ✓ 版本: {metadata['version']}")

                    # 如果没有指定平台，交互式选择
                    if not platform:
                        click.echo("\n选择目标平台：")
                        click.echo("  1. claude-code")
                        click.echo("  2. opencode")
                        platform_choice = click.prompt("\n选择平台（输入序号）", type=int)
                        platform = "claude-code" if platform_choice == 1 else "opencode"

                    click.echo(f"\n📦 正在从注册表安装...")
                    _install_from_local_directory(skill_dir, install_path, platform)

                    # 获取技能名称用于显示
                    skill_name = _get_skill_name(skill_dir)
                    dest_skill_dir = install_path / ".claude" / "skills" / skill_name if platform == "claude-code" else install_path / ".opencode" / "skills" / skill_name

                    click.echo(f"\n✅ 技能 '{skill_name}' 安装成功！")
                    click.echo(f"   来源: 注册表")
                    click.echo(f"   平台: {platform}")
                    click.echo(f"   目标: {install_path}")
                    click.echo(f"   技能路径: {dest_skill_dir}")

                    if metadata.get("description"):
                        click.echo(f"\n📋 {metadata.get('description')}")
                    if metadata.get("version"):
                        click.echo(f"   版本: {metadata.get('version')}")

                    return

            # 注册表找不到该技能
            click.echo(f"❌ 错误: 注册表中未找到技能 '{skill_spec}'", err=True)
            click.echo(f"\n提示:", err=True)
            click.echo(f"  1. 使用 'winwin-cli skills list' 查看已注册的技能", err=True)
            click.echo(f"  2. 使用 'winwin-cli skills register /path/to/skill' 注册本地技能", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@skills.command("list")
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="以 JSON 格式输出（用于 AI 调用）",
)
def list_cmd(output_json: bool):
    """列出所有已注册的技能"""
    try:
        # 从注册表获取技能列表
        registered_skills = _list_registered_skills()

        if not registered_skills:
            if output_json:
                # JSON 模式：返回空数组
                import json
                click.echo(json.dumps([], ensure_ascii=False))
            else:
                # 文本模式：显示提示信息
                click.echo("未找到已注册的技能")
                click.echo("\n提示: 使用 'winwin-cli skills register /path/to/skill' 注册技能")
            return

        if output_json:
            import json
            # 简化输出，只保留需要的字段
            output_skills = []
            for skill in registered_skills:
                output_skills.append({
                    "name": skill.get("name"),
                    "path": skill.get("path"),
                    "description": skill.get("metadata", {}).get("description", "无描述"),
                    "version": skill.get("metadata", {}).get("version", "N/A"),
                    "author": skill.get("metadata", {}).get("author", "N/A"),
                    "registered_at": skill.get("registered_at")
                })
            click.echo(json.dumps(output_skills, ensure_ascii=False, indent=2))
        else:
            click.echo(f"\n找到 {len(registered_skills)} 个已注册的技能：\n")
            for skill in registered_skills:
                skill_name = skill.get("name")
                metadata = skill.get("metadata", {})

                click.echo(f"📦 {skill_name}")
                click.echo(f"   路径: {skill.get('path')}")
                click.echo(f"   安装: winwin-cli skills install {skill_name}")
                click.echo(f"   描述: {metadata.get('description', '无描述')}")
                click.echo(f"   版本: {metadata.get('version', 'N/A')}")
                click.echo(f"   作者: {metadata.get('author', 'N/A')}")
                click.echo(f"   注册时间: {skill.get('registered_at', 'N/A')}")
                click.echo()

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@skills.command()
@click.argument("skill_spec")
@click.option(
    "--repo",
    help="指定 GitHub 仓库（格式: owner/repo）",
)
@click.option(
    "--branch", "ref",
    default="main",
    help="Git 分支或标签（默认: main）",
)
def info(skill_spec: str, repo: Optional[str], ref: str):
    """显示技能详细信息（优先从注册表查找）

    技能规格格式:
    - skill-name (从注册表查找)
    - /path/to/local/skill (本地路径)
    - https://github.com/... (GitHub URL)
    """
    try:
        skill_dir = None
        source = None

        # 1. GitHub URL
        if skill_spec.startswith("https://") or skill_spec.startswith("http://"):
            # 下载并注册到本地缓存
            skill_name = _download_and_register_github_skill(skill_spec, ref, repo)
            registered_skill = _find_registered_skill(skill_name)
            if registered_skill:
                skill_dir = Path(registered_skill["path"])
                source = "GitHub (已缓存)"

        # 2. 本地目录
        elif Path(skill_spec).is_dir():
            skill_dir = Path(skill_spec)
            source = "本地目录"

        # 3. 技能名称（从注册表查找）
        elif "/" not in skill_spec:
            registered_skill = _find_registered_skill(skill_spec)
            if registered_skill:
                skill_dir = Path(registered_skill["path"])
                source = f"注册表 ({registered_skill.get('source', 'local')})"
            else:
                click.echo(f"❌ 错误: 注册表中未找到技能 '{skill_spec}'", err=True)
                click.echo(f"\n提示:", err=True)
                click.echo(f"  1. 使用 'winwin-cli skills list' 查看已注册的技能", err=True)
                click.echo(f"  2. 使用 'winwin-cli skills register /path/to/skill' 注册本地技能", err=True)
                sys.exit(1)
        else:
            click.echo(f"❌ 错误: 不支持的技能规格 '{skill_spec}'", err=True)
            click.echo(f"\n支持的格式:", err=True)
            click.echo(f"  - 技能名称: my-skill", err=True)
            click.echo(f"  - 本地路径: /path/to/skill", err=True)
            click.echo(f"  - GitHub URL: https://github.com/...", err=True)
            sys.exit(1)

        if not skill_dir:
            click.echo(f"❌ 错误: 无法找到技能", err=True)
            sys.exit(1)

        # 验证技能目录
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            click.echo(f"❌ 错误: 技能目录中未找到 SKILL.md: {skill_dir}", err=True)
            sys.exit(1)

        # 获取技能名称
        skill_name = _get_skill_name(skill_dir)

        # 解析技能元数据
        metadata = _parse_skill_metadata(skill_file)

        # 显示信息
        click.echo(f"\n📦 技能: {metadata.get('name', skill_name)}")
        click.echo(f"{'='*50}")
        click.echo(f"来源: {source}")
        click.echo(f"路径: {skill_dir}")
        click.echo(f"描述: {metadata.get('description', '无描述')}")
        click.echo(f"版本: {metadata.get('version', 'N/A')}")
        click.echo(f"作者: {metadata.get('author', 'N/A')}")

        # 显示支持的文件
        click.echo(f"\n包含的文件:")
        for item in sorted(skill_dir.rglob("*")):
            if item.is_file():
                rel_path = item.relative_to(skill_dir)
                click.echo(f"  - {rel_path}")

        click.echo()

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _find_skill_by_name(skill_name: str, ref: str, repo_override: Optional[str]) -> Optional[str]:
    """在所有分类中查找指定名称的技能

    返回完整的技能规格 (如: category/skill-name)
    """
    try:
        default_repo = repo_override or _get_default_skills_repo()
        all_skills = _list_github_skills(default_repo, ref)

        # 查找匹配的技能
        for skill in all_skills:
            if skill.get("name") == skill_name:
                category = skill.get("category", "")
                if category:
                    return f"{default_repo}/{category}/{skill_name}"
                else:
                    return f"{default_repo}/{skill_name}"

        # 如果没有找到精确匹配，尝试模糊匹配
        for skill in all_skills:
            if skill_name.lower() in skill.get("name", "").lower():
                category = skill.get("category", "")
                if category:
                    return f"{default_repo}/{category}/{skill['name']}"
                else:
                    return f"{default_repo}/{skill['name']}"

        return None

    except Exception as e:
        click.echo(f"查找技能失败: {e}", err=True)
        return None


def _get_default_skills_repo() -> str:
    """获取默认的技能仓库"""
    # 可以从环境变量或配置文件读取
    # 例如: export WINWIN_SKILLS_REPO="owner/skills-repo"
    return os.environ.get("WINWIN_SKILLS_REPO", "heibaibufen/winwin-skills")


def _interactive_select_from_registry() -> Optional[str]:
    """从注册表交互式选择技能"""
    try:
        registered_skills = _list_registered_skills()

        if not registered_skills:
            click.echo("未找到已注册的技能", err=True)
            click.echo("\n提示:", err=True)
            click.echo("  1. 使用 'winwin-cli skills register /path/to/skill' 注册技能", err=True)
            click.echo("  2. 或直接指定路径: winwin-cli skills install /path/to/skill", err=True)
            return None

        click.echo("\n已注册的技能：")
        for idx, skill in enumerate(registered_skills, 1):
            skill_name = skill.get("name")
            metadata = skill.get("metadata", {})
            description = metadata.get("description", "无描述")
            click.echo(f"  {idx}. {skill_name} - {description}")

        # 让用户选择
        choice = click.prompt("\n选择要安装的技能（输入序号）", type=int)
        if choice < 1 or choice > len(registered_skills):
            click.echo("无效的选择", err=True)
            return None

        selected_skill = registered_skills[choice - 1]
        skill_name = selected_skill.get("name")
        click.echo(f"\n已选择: {skill_name}")

        return skill_name

    except Exception as e:
        click.echo(f"选择技能失败: {e}", err=True)
        return None


def _interactive_select_skill(repo_override: Optional[str]) -> Optional[str]:
    """交互式选择技能"""
    try:
        default_repo = repo_override or _get_default_skills_repo()
        click.echo(f"正在从仓库获取技能列表: {default_repo}")

        available_skills = _list_github_skills(default_repo, "main")

        if not available_skills:
            click.echo("未找到可用技能", err=True)
            return None

        click.echo("\n可用的技能：")
        for idx, skill in enumerate(available_skills, 1):
            click.echo(f"  {idx}. {skill['name']} - {skill.get('description', '无描述')}")

        # 让用户选择
        choice = click.prompt("\n选择要安装的技能（输入序号）", type=int)
        if choice < 1 or choice > len(available_skills):
            click.echo("无效的选择", err=True)
            return None

        skill_name = available_skills[choice - 1]["name"]
        category = available_skills[choice - 1].get("category", "")
        click.echo(f"\n已选择: {skill_name}")

        # 构建技能规格（包含分类）
        if category:
            return f"{default_repo}/{category}/{skill_name}"
        else:
            return f"{default_repo}/{skill_name}"

    except Exception as e:
        click.echo(f"获取技能列表失败: {e}", err=True)
        return None


def _resolve_and_download_skill(skill_spec: str, ref: str, repo_override: Optional[str]) -> Optional[Path]:
    """解析技能规格并下载到临时目录

    支持的格式:
    - https://github.com/owner/repo/tree/main/category/skill-name
    - https://github.com/owner/repo/tree/branch/category/skill-name
    - owner/repo/category/skill-name
    - owner/repo/skill-name
    - skill-name (使用默认仓库)
    """
    temp_dir = None

    try:
        # 解析 GitHub URL
        if skill_spec.startswith("https://github.com/"):
            # 从 URL 解析
            parts = skill_spec.replace("https://github.com/", "").split("/tree/")
            repo_path = parts[0]

            if len(parts) > 1:
                ref = parts[1].split("/")[0]  # 获取分支名
                skill_name = "/".join(parts[1].split("/")[1:])  # 获取技能路径
            else:
                skill_name = repo_path.split("/")[-1]
                repo_path = "/".join(repo_path.split("/")[:-1])

            owner, repo = repo_path.split("/")
            skill_path = skill_name

        elif "/" in skill_spec:
            # owner/repo/skill-name 或 owner/repo 格式
            parts = skill_spec.split("/")
            if len(parts) >= 3:
                owner, repo = parts[0], parts[1]
                skill_path = "/".join(parts[2:])
            else:
                # 使用提供的 repo 或默认仓库
                if repo_override:
                    owner, repo = repo_override.split("/")
                    skill_path = skill_spec
                else:
                    default_repo = _get_default_skills_repo()
                    owner, repo = default_repo.split("/")
                    skill_path = skill_spec
        else:
            # 仅技能名称，使用默认仓库
            default_repo = repo_override or _get_default_skills_repo()
            owner, repo = default_repo.split("/")
            skill_path = skill_spec

        click.echo(f"正在下载技能: {owner}/{repo}/{skill_path} (ref: {ref})")

        # 下载技能
        temp_dir = _download_skill_from_github(owner, repo, skill_path, ref)
        return temp_dir

    except Exception as e:
        click.echo(f"下载技能失败: {e}", err=True)
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        return None


def _download_skill_from_github(owner: str, repo: str, skill_path: str, ref: str = "main") -> Optional[Path]:
    """从 GitHub 下载技能目录到临时目录（使用并发下载加速）

    使用 GitHub API 获取目录内容并使用并发下载
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="winwin_skill_"))

    try:
        # 首先收集所有需要下载的文件
        files_to_download = []

        def _collect_files(api_url: str, local_dir: Path):
            """递归收集所有文件"""
            response = requests.get(api_url, params={"ref": ref}, timeout=30)
            response.raise_for_status()

            items = response.json()

            if not isinstance(items, list):
                items = [items]

            for item in items:
                if item.get("type") == "file":
                    download_url = item.get("download_url")
                    if download_url:
                        file_path = local_dir / item["name"]
                        files_to_download.append((download_url, file_path, item.get("path", item["name"])))

                elif item.get("type") == "dir":
                    sub_dir = local_dir / item["name"]
                    _collect_files(item["url"], sub_dir)

        # 收集所有文件
        api_base = f"https://api.github.com/repos/{owner}/{repo}/contents/{skill_path}"
        click.echo(f"正在分析技能目录结构...")
        _collect_files(api_base, temp_dir)

        if not files_to_download:
            click.echo(f"错误: 未找到任何文件", err=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None

        # 使用并发下载
        click.echo(f"正在下载 {len(files_to_download)} 个文件...")

        def _download_file(args: Tuple[str, Path, str]) -> Tuple[bool, str]:
            """下载单个文件"""
            download_url, file_path, display_path = args
            try:
                response = requests.get(download_url, timeout=30)
                response.raise_for_status()

                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, "wb") as f:
                    f.write(response.content)

                return (True, display_path)
            except Exception as e:
                return (False, f"{display_path}: {e}")

        # 使用线程池并发下载（最多 10 个并发）
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(_download_file, args): args for args in files_to_download}

            completed = 0
            failed = 0

            for future in as_completed(futures):
                completed += 1
                success, result = future.result()

                if success:
                    # 每下载 10% 显示一次进度
                    if completed % max(1, len(files_to_download) // 10) == 0 or completed == len(files_to_download):
                        click.echo(f"  进度: {completed}/{len(files_to_download)} 文件已完成")
                else:
                    failed += 1
                    click.echo(f"  ✗ 下载失败: {result}", err=True)

        if failed > 0:
            click.echo(f"警告: {failed} 个文件下载失败", err=True)

        # 验证 SKILL.md 是否存在
        skill_md = temp_dir / "SKILL.md"
        if not skill_md.exists():
            click.echo(f"警告: 下载的目录中未找到 SKILL.md", err=True)

        return temp_dir

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        click.echo(f"从 GitHub 下载失败: {e}", err=True)
        return None


def _get_skill_name(skill_dir: Path) -> str:
    """从 SKILL.md 或目录名获取技能名称"""
    skill_file = skill_dir / "SKILL.md"

    if skill_file.exists():
        metadata = _parse_skill_metadata(skill_file)
        if metadata.get("name"):
            return metadata["name"]

    # 如果元数据中没有名称，使用目录名
    return skill_dir.name


def _list_github_skills(repo: str, ref: str = "main") -> List[dict]:
    """从 GitHub 仓库列出所有技能

    扫描仓库根目录的分类子目录，在每个分类下查找包含 SKILL.md 的技能目录
    结构: repo/category/skill-name/
    """
    try:
        owner, repo_name = repo.split("/")

        # 获取仓库根目录内容
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/"
        response = requests.get(api_url, params={"ref": ref}, timeout=30)
        response.raise_for_status()

        categories = response.json()

        # 检查返回的数据格式
        if not isinstance(categories, list):
            click.echo(f"警告: GitHub API 返回了意外的数据格式", err=True)
            if isinstance(categories, dict):
                # 可能是错误信息
                if "message" in categories:
                    click.echo(f"错误信息: {categories.get('message')}", err=True)
                if "documentation_url" in categories:
                    click.echo(f"文档: {categories.get('documentation_url')}", err=True)
            return []

        skills = []

        # 遍历每个分类目录
        for category in categories:
            if not isinstance(category, dict):
                continue

            if category.get("type") == "dir":
                category_name = category["name"]
                category_url = f"{api_url}{category_name}"

                try:
                    # 获取分类目录下的内容
                    cat_response = requests.get(category_url, params={"ref": ref}, timeout=30)
                    cat_response.raise_for_status()
                    items = cat_response.json()

                    if not isinstance(items, list):
                        continue

                    # 在分类目录下查找技能
                    for item in items:
                        if not isinstance(item, dict):
                            continue

                        if item.get("type") == "dir":
                            # 检查是否包含 SKILL.md
                            skill_api_url = f"{category_url}/{item['name']}"
                            try:
                                skill_response = requests.get(skill_api_url, params={"ref": ref}, timeout=30)
                                skill_response.raise_for_status()
                                skill_items = skill_response.json()

                                if isinstance(skill_items, list) and any(i.get("name") == "SKILL.md" for i in skill_items if isinstance(i, dict)):
                                    # 下载 SKILL.md 获取元数据
                                    skill_md_url = f"{skill_api_url}/SKILL.md"
                                    md_response = requests.get(skill_md_url, params={"ref": ref}, timeout=30)

                                    metadata = {}
                                    if md_response.status_code == 200:
                                        try:
                                            md_content = md_response.json()
                                            if isinstance(md_content, dict) and md_content.get("encoding") == "base64":
                                                import base64
                                                content = base64.b64decode(md_content["content"]).decode("utf-8")
                                                # 解析 YAML 前置元数据
                                                metadata = _parse_skill_metadata_from_content(content)
                                        except Exception as e:
                                            click.echo(f"警告: 解析 {category_name}/{item['name']} 的元数据失败: {e}", err=True)

                                    skills.append({
                                        "name": metadata.get("name", item["name"]),
                                        "description": metadata.get("description", "无描述"),
                                        "version": metadata.get("version", "N/A"),
                                        "author": metadata.get("author", "N/A"),
                                        "category": category_name,
                                        "path": f"{repo}/{category_name}/{item['name']}",
                                    })

                            except requests.exceptions.RequestException as e:
                                click.echo(f"警告: 获取技能 {category_name}/{item['name']} 信息失败: {e}", err=True)
                                continue

                except requests.exceptions.RequestException as e:
                    click.echo(f"警告: 获取分类 {category_name} 的内容失败: {e}", err=True)
                    continue

        return sorted(skills, key=lambda x: (x.get("category", ""), x["name"]))

    except requests.exceptions.RequestException as e:
        click.echo(f"从 GitHub 获取技能列表失败: {e}", err=True)
        return []
    except Exception as e:
        click.echo(f"从 GitHub 获取技能列表失败: {e}", err=True)
        import traceback
        traceback.print_exc()
        return []


def _parse_skill_metadata_from_content(content: str) -> dict:
    """从 SKILL.md 内容解析 YAML 前置元数据"""
    try:
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                return yaml.safe_load(yaml_content) or {}

        return {}
    except Exception as e:
        return {}


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
    import shutil

    # 创建 .claude/skills 目录结构
    claude_skills_dir = install_path / ".claude" / "skills"
    claude_skills_dir.mkdir(parents=True, exist_ok=True)

    # 复制整个技能目录
    dest_skill_dir = claude_skills_dir / skill_name
    if dest_skill_dir.exists():
        shutil.rmtree(dest_skill_dir)

    shutil.copytree(skill_path, dest_skill_dir)
    click.echo(f"✓ 已复制技能目录到: {dest_skill_dir}")

    # 不再需要单独执行 install.sh，因为整个目录已经复制了
    # 保留这个逻辑以向后兼容
    install_script = skill_path / "scripts" / "install.sh"
    if install_script.exists():
        click.echo(f"✓ 检测到安装脚本（已随目录复制）")
        # 不执行脚本，因为整个目录已经复制完成
        # 如果需要执行，可以取消下面的注释
        # subprocess.run(["bash", str(install_script), str(skill_path)], cwd=install_path, check=True)


def _install_for_opencode(skill_path: Path, skill_name: str, install_path: Path, metadata: dict):
    """安装到 OpenCode（待实现）"""
    import shutil

    click.echo(f"警告: OpenCode 平台支持尚未完全实现", err=True)
    click.echo(f"提示: 复制技能文件，但可能需要手动配置", err=True)

    # 创建示例目录结构
    opencode_skills_dir = install_path / ".opencode" / "skills"
    opencode_skills_dir.mkdir(parents=True, exist_ok=True)

    # 复制整个技能目录
    dest_skill_dir = opencode_skills_dir / skill_name
    if dest_skill_dir.exists():
        shutil.rmtree(dest_skill_dir)

    shutil.copytree(skill_path, dest_skill_dir)

    click.echo(f"✓ 已复制技能目录到: {dest_skill_dir}")
    click.echo(f"  (平台适配需要进一步配置)")


def _install_from_local_directory(skill_dir: Path, install_path: Path, platform: str):
    """从本地目录安装技能

    Args:
        skill_dir: 本地技能目录（必须包含 SKILL.md）
        install_path: 安装目标路径
        platform: 目标平台（claude-code 或 opencode）
    """
    # 验证 SKILL.md 存在
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        click.echo(f"❌ 错误: 目录中未找到 SKILL.md", err=True)
        click.echo(f"   目录: {skill_dir}", err=True)
        click.echo(f"   要求: 技能目录必须包含 SKILL.md 文件", err=True)

        # 列出目录内容，帮助调试
        try:
            contents = list(skill_dir.iterdir())[:5]
            if contents:
                click.echo(f"   目录内容: {', '.join([p.name for p in contents])}", err=True)
        except Exception:
            pass

        sys.exit(1)

    # 获取技能名称
    skill_name = _get_skill_name(skill_dir)

    # 解析元数据
    metadata = _parse_skill_metadata(skill_file)

    # 执行安装（复用现有逻辑）
    _install_skill(skill_dir, skill_name, install_path, platform, metadata)


__all__ = ["skills"]
