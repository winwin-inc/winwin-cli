"""知识库检索工具 - markitdown 封装模块"""

import subprocess
from pathlib import Path
from typing import Optional


def run_markitdown(
    input_path: str,
    output_path: Optional[str] = None,
    format: str = "md",
) -> str:
    """使用 markitdown 进行文档转换

    优先使用已安装的 markitdown 包，如果不可用则回退到 uvx

    Args:
        input_path: 输入文件或目录路径
        output_path: 输出文件路径，如果为 None 则自动生成
        format: 目标格式 (注意：markitdown 默认只输出 markdown)

    Returns:
        输出文件路径

    Raises:
        FileNotFoundError: markitdown 未安装
        subprocess.CalledProcessError: 转换失败
    """
    # 优先尝试使用 Python 包
    try:
        from markitdown import convert

        if output_path:
            convert(input_path, output_path)
            return output_path
        else:
            # 如果没有指定输出路径，生成默认路径
            input_path_obj = Path(input_path)
            output_path = str(input_path_obj.with_suffix(".md"))
            convert(input_path, output_path)
            return output_path
    except ImportError:
        # 回退到 uvx
        cmd = ["uvx", "markitdown", input_path]

        if output_path:
            cmd.extend(["--output", output_path])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        if output_path:
            return output_path

        # 尝试从输出中提取文件路径
        output = result.stdout.strip()
        if output:
            return output

        # 默认输出路径
        input_path_obj = Path(input_path)
        return str(input_path_obj.with_suffix(".md"))


def convert_markdown(
    input_path: str,
    output_path: Optional[str] = None,
    format: str = "md",
) -> str:
    """转换 Markdown 文档

    Args:
        input_path: 输入文件或目录路径
        output_path: 输出文件路径
        format: 目标格式

    Returns:
        输出文件路径

    Raises:
        FileNotFoundError: 输入文件不存在
        ValueError: 不支持的目标格式
    """
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        raise FileNotFoundError(f"输入路径不存在: {input_path}")

    valid_formats = ["md", "pdf", "docx", "html", "xml"]
    if format not in valid_formats:
        raise ValueError(f"不支持的格式: {format}，可选格式: {valid_formats}")

    if not output_path:
        output_path = str(input_path_obj.with_suffix(f".{format}"))

    return run_markitdown(input_path, output_path, format)
