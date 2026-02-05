"""文档转换模块 - 将各种格式转换为 Markdown"""

import sys
from pathlib import Path
from typing import Optional, List

import click

from winwin_cli.kb_search.markitdown import run_markitdown


@click.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="输出目录或文件路径（默认：与输入文件同目录）",
)
@click.option(
    "--ext",
    "-e",
    multiple=True,
    help="文件扩展名过滤（可多次使用，如：--ext .docx --ext .pdf）",
)
@click.option(
    "--overwrite",
    "-f",
    is_flag=True,
    help="覆盖已存在的 Markdown 文件",
)
def convert(input_path: str, output: Optional[str], ext: tuple, overwrite: bool):
    """转换文档为 Markdown 格式

    支持的输入格式：
    - Office: .docx, .doc, .pptx, .xlsx, .xls
    - PDF: .pdf
    - 图片（OCR）: .jpg, .jpeg, .png, .gif, .bmp, .webp
    - 音频（语音转录）: .wav, .mp3, .m4a
    - 视频: .mp4, .avi, .mov, .mkv
    - 文本: .html, .htm, .csv, .json, .xml

    用例：
        # 转换单个文件
        winwin-cli convert document.docx

        # 转换目录中的所有文件
        winwin-cli convert ./docs

        # 转换并指定输出目录
        winwin-cli convert ./docs -o ./markdown

        # 只转换特定格式
        winwin-cli convert ./docs --ext .pdf --ext .docx

        # 覆盖已存在的 Markdown 文件
        winwin-cli convert ./docs --overwrite
    """
    from tqdm import tqdm

    input_path_obj = Path(input_path)

    # 判断是文件还是目录
    if input_path_obj.is_file():
        # 转换单个文件
        _convert_single_file(input_path_obj, output, overwrite)
    else:
        # 转换目录
        _convert_directory(input_path_obj, output, ext, overwrite)


def _convert_single_file(
    input_file: Path,
    output_path: Optional[str],
    overwrite: bool,
):
    """转换单个文件

    Args:
        input_file: 输入文件路径
        output_path: 输出路径（可选）
        overwrite: 是否覆盖已存在的文件
    """
    # 确定输出路径
    if output_path:
        output_path_obj = Path(output_path)
        if output_path_obj.is_dir():
            # 如果是目录，文件名保持不变，扩展名改为 .md
            output_file = output_path_obj / f"{input_file.stem}.md"
        else:
            # 如果是文件路径，直接使用
            output_file = output_path_obj
    else:
        # 默认保存在同一目录
        output_file = input_file.with_suffix(".md")

    # 检查是否已存在
    if output_file.exists() and not overwrite:
        click.echo(f"⚠ 跳过（已存在）: {output_file}")
        return

    try:
        click.echo(f"正在转换: {input_file.name}")
        run_markitdown(str(input_file), str(output_file), "md")
        click.echo(f"✓ 转换成功: {output_file}")
    except Exception as e:
        click.echo(f"✗ 转换失败: {input_file.name} - {e}", err=True)
        sys.exit(1)


def _convert_directory(
    input_dir: Path,
    output_path: Optional[str],
    extensions: tuple,
    overwrite: bool,
):
    """转换目录中的所有文件

    Args:
        input_dir: 输入目录路径
        output_path: 输出目录路径（可选）
        extensions: 文件扩展名过滤
        overwrite: 是否覆盖已存在的文件
    """
    from tqdm import tqdm

    # 支持的格式列表
    supported_extensions = {
        # Office 文档
        ".docx", ".doc", ".pptx", ".xlsx", ".xls",
        # PDF
        ".pdf",
        # 图片
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
        # 音频
        ".wav", ".mp3", ".m4a",
        # 视频
        ".mp4", ".avi", ".mov", ".mkv",
        # 文本格式
        ".html", ".htm", ".csv", ".json", ".xml",
    }

    # 确定输出目录
    if output_path:
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = input_dir

    # 收集要转换的文件
    files_to_convert = []
    for ext in supported_extensions:
        if extensions and ext not in extensions:
            # 如果指定了扩展名过滤，跳过不在列表中的
            continue
        for file_path in input_dir.rglob(f"*{ext}"):
            if file_path.is_file():
                files_to_convert.append(file_path)

    if not files_to_convert:
        click.echo("未找到可转换的文件")
        return

    click.echo(f"\n找到 {len(files_to_convert)} 个文件")

    # 统计
    success_count = 0
    skip_count = 0
    error_count = 0

    # 转换文件（显示进度条）
    for input_file in tqdm(files_to_convert, desc="  转换进度", unit="文件"):
        # 计算相对路径
        try:
            relative_path = input_file.relative_to(input_dir)
        except ValueError:
            # 文件不在 input_dir 下，使用文件名
            relative_path = input_file.name

        output_file = output_dir / relative_path.with_suffix(".md")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 检查是否已存在
        if output_file.exists() and not overwrite:
            skip_count += 1
            continue

        try:
            run_markitdown(str(input_file), str(output_file), "md")
            success_count += 1
        except Exception:
            error_count += 1

    # 显示结果
    click.echo(f"\n转换完成:")
    click.echo(f"  ✓ 成功: {success_count} 个文件")
    if skip_count > 0:
        click.echo(f"  ⊘ 跳过: {skip_count} 个文件（已存在）")
    if error_count > 0:
        click.echo(f"  ✗ 失败: {error_count} 个文件")
        sys.exit(1)
