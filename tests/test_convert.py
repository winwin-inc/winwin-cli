"""测试 convert 命令"""

import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner

from winwin_cli.convert import convert


class TestConvertCommand:
    """测试 convert 命令"""

    def test_convert_command_exists(self):
        """测试 convert 命令存在"""
        runner = CliRunner()
        result = runner.invoke(convert, ["--help"])
        assert result.exit_code == 0
        assert "转换文档为 Markdown" in result.output

    def test_convert_requires_input_path(self):
        """测试转换命令需要输入路径"""
        runner = CliRunner()
        result = runner.invoke(convert, [])
        assert result.exit_code != 0

    def test_convert_single_html_file(self):
        """测试转换单个 HTML 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试 HTML 文件
            html_file = Path(tmpdir) / "test.html"
            html_file.write_text("<h1>标题</h1><p>内容</p>")

            runner = CliRunner()
            result = runner.invoke(convert, [str(html_file)])

            assert result.exit_code == 0
            assert "转换成功" in result.output

            # 验证输出文件
            md_file = html_file.with_suffix(".md")
            assert md_file.exists()
            content = md_file.read_text()
            assert "标题" in content
            assert "内容" in content

    def test_convert_with_output_directory(self):
        """测试指定输出目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()

            # 创建测试文件
            html_file = input_dir / "test.html"
            html_file.write_text("<p>测试</p>")

            runner = CliRunner()
            result = runner.invoke(convert, [str(input_dir), "-o", str(output_dir)])

            assert result.exit_code == 0
            assert (output_dir / "test.md").exists()

    def test_convert_directory(self):
        """测试转换整个目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "docs"
            input_dir.mkdir()

            # 创建多个测试文件
            (input_dir / "file1.html").write_text("<h1>文件1</h1>")
            (input_dir / "file2.html").write_text("<h1>文件2</h1>")
            (input_dir / "file3.html").write_text("<h1>文件3</h1>")

            runner = CliRunner()
            result = runner.invoke(convert, [str(input_dir)])

            assert result.exit_code == 0
            assert "成功: 3 个文件" in result.output

            # 验证所有文件都被转换
            assert (input_dir / "file1.md").exists()
            assert (input_dir / "file2.md").exists()
            assert (input_dir / "file3.md").exists()

    def test_convert_with_extension_filter(self):
        """测试扩展名过滤"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "docs"
            input_dir.mkdir()

            # 创建不同格式的文件
            (input_dir / "file1.html").write_text("<p>HTML</p>")
            (input_dir / "file2.txt").write_text("Text")
            (input_dir / "file3.html").write_text("<p>Another HTML</p>")

            runner = CliRunner()
            result = runner.invoke(convert, [str(input_dir), "--ext", ".html"])

            assert result.exit_code == 0
            # 应该只转换 2 个 HTML 文件，不包含 txt
            assert "成功: 2 个文件" in result.output

    def test_convert_skip_existing_files(self):
        """测试跳过已存在的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            md_file = Path(tmpdir) / "test.md"

            # 创建 HTML 文件和已存在的 MD 文件
            html_file.write_text("<p>HTML</p>")
            md_file.write_text("Existing MD")

            runner = CliRunner()
            result = runner.invoke(convert, [str(html_file)])

            assert result.exit_code == 0
            assert "跳过" in result.output or "成功: 0 个文件" in result.output

            # 验证原 MD 文件未被覆盖
            assert md_file.read_text() == "Existing MD"

    def test_convert_overwrite_existing_files(self):
        """测试覆盖已存在的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "test.html"
            md_file = Path(tmpdir) / "test.md"

            # 创建 HTML 文件和已存在的 MD 文件
            html_file.write_text("<p>New HTML</p>")
            md_file.write_text("Old MD")

            runner = CliRunner()
            result = runner.invoke(convert, [str(html_file), "--overwrite"])

            assert result.exit_code == 0
            assert "转换成功" in result.output

            # 验证 MD 文件被覆盖
            content = md_file.read_text()
            assert "New HTML" in content or "HTML" in content
            assert "Old MD" not in content

    def test_convert_with_multiple_extensions(self):
        """测试多个扩展名过滤"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "docs"
            input_dir.mkdir()

            # 创建不同格式的文件
            (input_dir / "file1.html").write_text("<p>HTML1</p>")
            (input_dir / "file2.csv").write_text("data1,data2")
            (input_dir / "file3.html").write_text("<p>HTML2</p>")
            (input_dir / "file4.json").write_text("{}")

            runner = CliRunner()
            result = runner.invoke(convert, [str(input_dir), "-e", ".html", "-e", ".csv"])

            assert result.exit_code == 0
            # 应该转换 3 个文件（2个HTML + 1个CSV）
            assert "成功: 3 个文件" in result.output

    def test_convert_nonexistent_path(self):
        """测试转换不存在的路径"""
        runner = CliRunner()
        result = runner.invoke(convert, ["/nonexistent/path"])

        assert result.exit_code != 0

    def test_convert_preserves_directory_structure(self):
        """测试保持目录结构"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"

            # 创建嵌套目录结构
            (input_dir / "sub1").mkdir(parents=True)
            (input_dir / "sub2").mkdir(parents=True)

            (input_dir / "sub1" / "file1.html").write_text("<p>File 1</p>")
            (input_dir / "sub2" / "file2.html").write_text("<p>File 2</p>")

            runner = CliRunner()
            result = runner.invoke(convert, [str(input_dir), "-o", str(output_dir)])

            assert result.exit_code == 0
            # 验证目录结构被保留
            assert (output_dir / "sub1" / "file1.md").exists()
            assert (output_dir / "sub2" / "file2.md").exists()
