"""知识库检索工具 - 数据模型"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from pathlib import Path


class KnowledgeBaseConfig(BaseModel):
    """知识库配置模型"""

    name: str = Field(..., min_length=1, description="知识库名称")
    path: str = Field(..., min_length=1, description="知识库根目录路径")
    description: Optional[str] = Field(None, description="知识库描述")
    enabled: bool = Field(True, description="是否启用该知识库")
    index_path: Optional[str] = Field(None, description="索引文件路径")
    extensions: List[str] = Field(
        default_factory=lambda: [
            # 文本格式（直接读取）
            ".md", ".txt", ".html", ".htm", ".csv", ".json", ".xml",
            # Office 文档（markitdown 转换）
            ".docx", ".doc", ".pptx", ".xlsx", ".xls",
            # PDF（markitdown 转换）
            ".pdf",
            # 图片（markitdown + OCR）
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
            # 音频（markitdown + 语音转录）
            ".wav", ".mp3", ".m4a",
            # 视频（markitdown）
            ".mp4", ".avi", ".mov", ".mkv",
            # 压缩包
            ".zip",
        ],
        description="包含的文件扩展名"
    )

    @field_validator("path")
    @classmethod
    def path_must_be_absolute(cls, v: str) -> str:
        """验证路径是否为绝对路径"""
        if not Path(v).is_absolute():
            raise ValueError("知识库路径必须为绝对路径")
        return v

    @property
    def exists(self) -> bool:
        """检查知识库目录是否存在"""
        return Path(self.path).exists()


class Document(BaseModel):
    """文档模型"""

    path: str = Field(..., description="文档路径")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    metadata: Optional[dict] = Field(default_factory=dict, description="文档元数据")


class SearchResult(BaseModel):
    """搜索结果模型"""

    document: Document = Field(..., description="匹配的文档")
    score: float = Field(..., ge=0.0, description="匹配分数")
    highlights: List[str] = Field(default_factory=list, description="高亮片段")


class SearchRequest(BaseModel):
    """搜索请求模型"""

    query: str = Field(..., min_length=1, description="搜索查询")
    knowledge_bases: Optional[List[str]] = Field(None, description="要搜索的知识库列表")
    dirs: Optional[List[str]] = Field(None, description="要搜索的子目录列表（相对路径）")
    max_results: int = Field(10, ge=1, le=100, description="最大返回结果数")
    threshold: float = Field(0.1, ge=0.0, le=1.0, description="最低匹配分数阈值")
    format: str = Field("text", pattern="^(text|json)$", description="输出格式")
    highlight: bool = Field(True, description="是否返回高亮片段")
    with_content: bool = Field(False, description="是否返回文档完整内容")


class IndexInfo(BaseModel):
    """索引信息模型"""

    knowledge_base: str = Field(..., description="知识库名称")
    document_count: int = Field(0, ge=0, description="索引文档数")
    index_path: str = Field(..., description="索引路径")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
