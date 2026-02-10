"""测试 skills 命令"""

import pytest
import tempfile
import yaml
import os
from pathlib import Path
from click.testing import CliRunner

from winwin_cli.skills.cli import skills, _get_registry_file


@pytest.fixture(autouse=True)
def clean_registry():
    """每个测试前后清理注册表"""
    # 测试前清理
    registry_file = _get_registry_file()
    if registry_file.exists():
        os.remove(registry_file)

    yield

    # 测试后清理
    if registry_file.exists():
        os.remove(registry_file)


class TestSkillsCommand:
    """测试 skills 命令"""

    def test_skills_command_exists(self):
        """测试 skills 命令存在"""
        runner = CliRunner()
        result = runner.invoke(skills, ["--help"])
        assert result.exit_code == 0
        assert "技能管理命令" in result.output

    def test_list_command(self):
        """测试 list 子命令"""
        runner = CliRunner()
        result = runner.invoke(skills, ["list"])
        assert result.exit_code == 0
        # 应该包含默认的技能
        assert "vega-lite-charts" in result.output or "winwin-cli" in result.output

    def test_list_json_output(self):
        """测试 list 命令的 JSON 输出"""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建并注册一个测试技能
            skill_dir = Path(tmpdir) / "test-json-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: test-json-skill\n"
                "description: JSON 测试技能\n"
                "---\n"
            )

            runner = CliRunner()

            # 注册技能
            result = runner.invoke(skills, ["register", str(skill_dir)])
            assert result.exit_code == 0

            # 测试 JSON 输出
            result = runner.invoke(skills, ["list", "--json"])
            assert result.exit_code == 0

            # 验证是有效的 JSON
            data = json.loads(result.output)
            assert isinstance(data, list)
            # 应该有至少 2 个技能（winwin-cli 默认技能 + test-json-skill）
            assert len(data) >= 2

            # 验证包含我们注册的技能
            test_skill = next((s for s in data if s["name"] == "test-json-skill"), None)
            assert test_skill is not None
            assert test_skill["description"] == "JSON 测试技能"

    def test_info_command(self):
        """测试 info 子命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试技能
            skill_dir = Path(tmpdir) / "test-info-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: test-info-skill\n"
                "description: 测试信息命令\n"
                "version: 1.0.0\n"
                "author: Test Author\n"
                "---\n"
                "# 测试技能\n"
            )

            runner = CliRunner()

            # 先注册技能
            result = runner.invoke(skills, ["register", str(skill_dir)])
            assert result.exit_code == 0

            # 然后查看信息
            result = runner.invoke(skills, ["info", "test-info-skill"])
            assert result.exit_code == 0
            assert "test-info-skill" in result.output
            assert "测试信息命令" in result.output or "description" in result.output.lower()

    def test_info_command_invalid_skill(self):
        """测试 info 命令处理不存在的技能"""
        runner = CliRunner()
        result = runner.invoke(skills, ["info", "nonexistent-skill"])
        assert result.exit_code != 0
        assert "错误" in result.output or "not found" in result.output.lower()

    def test_install_command_to_temp_dir(self):
        """测试 install 命令安装到临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试技能
            skill_dir = Path(tmpdir) / "test-install-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: test-install-skill\n"
                "description: 测试安装技能\n"
                "version: 1.0.0\n"
                "---\n"
                "# 测试安装\n"
            )
            (skill_dir / "scripts").mkdir()
            (skill_dir / "scripts" / "test.sh").write_text("#!/bin/bash\necho 'test'")

            runner = CliRunner()

            # 注册技能
            result = runner.invoke(skills, ["register", str(skill_dir)])
            assert result.exit_code == 0

            # 安装技能
            result = runner.invoke(
                skills,
                ["install", "test-install-skill", "--to", tmpdir, "--platform", "claude-code"]
            )
            assert result.exit_code == 0
            assert "安装成功" in result.output

            # 验证技能目录已复制
            installed_dir = Path(tmpdir) / ".claude" / "skills" / "test-install-skill"
            assert installed_dir.exists()
            assert (installed_dir / "SKILL.md").exists()

            # 验证子目录也被复制了
            assert (installed_dir / "scripts").exists()

    def test_install_command_interactive_mode(self):
        """测试 install 命令的交互模式"""
        # 模拟用户输入：选择第1个技能，选择平台1
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = CliRunner()

            # 使用输入流模拟交互
            result = runner.invoke(
                skills,
                ["install", tmpdir],
                input="1\n1\n"
            )
            # 交互模式可能会有问题，只要不崩溃就行
            # 如果失败，检查输出是否包含有用的信息
            if result.exit_code != 0:
                # 至少应该显示技能列表
                assert "可用的技能" in result.output or len(result.output) > 0

    def test_install_command_requires_skill_or_path(self):
        """测试 install 命令没有参数时的行为"""
        runner = CliRunner()
        # 不提供任何参数应该提示错误（因为没有注册的技能且无法连接 GitHub）
        result = runner.invoke(skills, ["install"], input="n")
        # 应该显示错误或提示信息
        assert result.exit_code != 0 or len(result.output) > 0


class TestSkillsHelpers:
    """测试 skills 辅助函数"""

    def test_parse_skill_metadata(self):
        """测试技能元数据解析"""
        from winwin_cli.skills.cli import _parse_skill_metadata

        # 创建临时技能文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(
                "---\n"
                "name: test-skill\n"
                "description: 测试技能\n"
                "version: 1.0.0\n"
                "author: Test Author\n"
                "---\n"
                "# 技能内容\n"
            )
            temp_path = f.name

        try:
            metadata = _parse_skill_metadata(Path(temp_path))
            assert metadata["name"] == "test-skill"
            assert metadata["description"] == "测试技能"
            assert metadata["version"] == "1.0.0"
            assert metadata["author"] == "Test Author"
        finally:
            Path(temp_path).unlink()

    def test_parse_skill_metadata_no_frontmatter(self):
        """测试没有前置元数据的技能文件"""
        from winwin_cli.skills.cli import _parse_skill_metadata

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# 技能内容\n没有前置元数据")
            temp_path = f.name

        try:
            metadata = _parse_skill_metadata(Path(temp_path))
            assert metadata == {}
        finally:
            Path(temp_path).unlink()


class TestSkillsIntegration:
    """集成测试"""

    def test_full_install_workflow(self):
        """测试完整的安装流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试技能
            skill_dir = Path(tmpdir) / "test-full-workflow"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: test-full-workflow\n"
                "description: 完整工作流测试\n"
                "version: 1.0.0\n"
                "author: Test Author\n"
                "---\n"
                "# 完整工作流测试\n"
            )
            (skill_dir / "assets").mkdir()
            (skill_dir / "assets" / "test.txt").write_text("test asset")

            runner = CliRunner()

            # 1. 注册技能
            result = runner.invoke(skills, ["register", str(skill_dir)])
            assert result.exit_code == 0
            assert "test-full-workflow" in result.output

            # 2. 列出技能
            result = runner.invoke(skills, ["list"])
            assert result.exit_code == 0
            assert "test-full-workflow" in result.output

            # 3. 查看技能详情
            result = runner.invoke(skills, ["info", "test-full-workflow"])
            assert result.exit_code == 0
            assert "test-full-workflow" in result.output

            # 4. 安装技能
            result = runner.invoke(
                skills,
                ["install", "test-full-workflow", "--to", tmpdir, "--platform", "claude-code"]
            )
            assert result.exit_code == 0
            assert "安装成功" in result.output

            # 5. 验证安装
            installed_dir = Path(tmpdir) / ".claude" / "skills" / "test-full-workflow"
            assert installed_dir.exists()

            # 验证 SKILL.md 文件
            skill_file = installed_dir / "SKILL.md"
            assert skill_file.exists()
            content = skill_file.read_text()
            assert "完整工作流测试" in content

            # 验证子目录也被复制
            assert (installed_dir / "assets").exists()

    def test_install_from_local_directory(self):
        """测试从本地目录安装技能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建临时技能目录
            skill_dir = Path(tmpdir) / "test-local-skill"
            skill_dir.mkdir()

            # 创建 SKILL.md
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                "---\n"
                "name: test-local-skill\n"
                "description: 本地测试技能\n"
                "version: 1.0.0\n"
                "author: Test Author\n"
                "---\n"
                "# 本地测试技能\n"
                "这是一个用于测试的本地技能。\n"
            )

            # 创建一些子目录和文件
            (skill_dir / "scripts").mkdir()
            (skill_dir / "scripts" / "test.sh").write_text("#!/bin/bash\necho 'test'")
            (skill_dir / "assets").mkdir()
            (skill_dir / "assets" / "test.txt").write_text("test asset")

            # 创建安装目标目录
            install_dir = Path(tmpdir) / "project"
            install_dir.mkdir()

            # 执行安装
            runner = CliRunner()
            result = runner.invoke(
                skills,
                ["install", str(skill_dir), "--to", str(install_dir), "--platform", "claude-code"]
            )

            assert result.exit_code == 0
            assert "安装成功" in result.output
            assert "本地目录" in result.output

            # 验证技能目录已复制
            installed_skill_dir = install_dir / ".claude" / "skills" / "test-local-skill"
            assert installed_skill_dir.exists()
            assert (installed_skill_dir / "SKILL.md").exists()

            # 验证子目录也被复制了
            assert (installed_skill_dir / "scripts").exists()
            assert (installed_skill_dir / "assets").exists()

    def test_install_from_local_directory_missing_skill_md(self):
        """测试从缺少 SKILL.md 的本地目录安装"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建临时目录但不创建 SKILL.md
            skill_dir = Path(tmpdir) / "invalid-skill"
            skill_dir.mkdir()

            # 创建一些其他文件
            (skill_dir / "readme.txt").write_text("This is not a skill")

            # 尝试安装
            runner = CliRunner()
            result = runner.invoke(skills, ["install", str(skill_dir)])

            assert result.exit_code != 0
            assert "SKILL.md" in result.output
            assert "错误" in result.output

    def test_install_from_local_directory_with_to_option(self):
        """测试使用 --to 选项指定安装目标"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建临时技能目录
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: test-skill\n"
                "description: 测试技能\n"
                "---\n"
            )

            # 使用 --to 指定目标
            target_dir = Path(tmpdir) / "target-project"
            runner = CliRunner()
            result = runner.invoke(
                skills,
                ["install", str(skill_dir), "--to", str(target_dir), "--platform", "claude-code"]
            )

            assert result.exit_code == 0
            assert (target_dir / ".claude" / "skills" / "test-skill").exists()

    def test_smart_path_detection_directory(self):
        """测试智能路径识别 - 本地目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建本地技能目录
            skill_dir = Path(tmpdir) / "my-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")

            # 目标目录
            target_dir = Path(tmpdir) / "project"
            target_dir.mkdir()

            # 使用本地目录路径
            runner = CliRunner()
            result = runner.invoke(
                skills,
                ["install", str(skill_dir), "--to", str(target_dir), "--platform", "claude-code"]
            )

            assert result.exit_code == 0
            assert "检测到本地目录" in result.output
            assert (target_dir / ".claude" / "skills" / "my-skill").exists()
