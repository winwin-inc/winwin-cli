"""知识库检索工具 - 索引构建模块

使用 jieba 中文分词 + rank-bm25 排序算法
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Dict, Any

import click
import jieba
from rank_bm25 import BM25Okapi

from winwin_cli.kb_search.models import (
    KnowledgeBaseConfig,
    IndexInfo,
    Document,
    SearchResult,
)


class BM25Indexer:
    """基于 jieba 分词 + BM25 排序的全文索引器"""

    def __init__(self, index_dir: str):
        """初始化索引器

        Args:
            index_dir: 索引目录路径
        """
        self.index_dir = Path(index_dir)
        self.corpus_file = self.index_dir / "corpus.json"
        self._load_index()

    def _load_index(self):
        """加载或初始化索引"""
        self.index_dir.mkdir(parents=True, exist_ok=True)

        if self.corpus_file.exists():
            with open(self.corpus_file, "r", encoding="utf-8") as f:
                self.corpus = json.load(f)
            # 重新构建 BM25 模型
            self._build_bm25()
        else:
            self.corpus = []
            self.bm25 = None

    def _tokenize(self, text: str) -> List[str]:
        """使用 jieba 分词

        Args:
            text: 文本内容

        Returns:
            分词后的词列表
        """
        return list(jieba.cut(text))

    def _build_bm25(self):
        """构建 BM25 索引"""
        if not self.corpus:
            self.bm25 = None
            return
        # 对所有文档内容进行分词
        tokenized_corpus = [self._tokenize(doc["content"]) for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def add_document(self, path: str, title: str, content: str):
        """添加文档到索引

        Args:
            path: 文档路径
            title: 文档标题
            content: 文档内容
        """
        # 检查是否已存在
        for i, doc in enumerate(self.corpus):
            if doc["path"] == path:
                self.corpus[i] = {
                    "path": path,
                    "title": title,
                    "content": content,
                }
                self._save_index()
                return

        self.corpus.append({
            "path": path,
            "title": title,
            "content": content,
        })
        self._save_index()

    def add_documents(self, documents: List[Document]):
        """批量添加文档

        Args:
            documents: 文档列表
        """
        from tqdm import tqdm

        for doc in tqdm(documents, desc="  构建索引", unit="文档"):
            self.add_document(doc.path, doc.title, doc.content)

    def _save_index(self):
        """保存索引到磁盘"""
        with open(self.corpus_file, "w", encoding="utf-8") as f:
            json.dump(self.corpus, f, ensure_ascii=False)
        self._build_bm25()

    def search(
        self,
        query: str,
        limit: int = 10,
        highlight: bool = False,
        dirs: Optional[List[str]] = None,
        with_content: bool = False,
    ) -> Iterator[Dict[str, Any]]:
        """搜索索引

        Args:
            query: 搜索查询
            limit: 最大返回结果数
            highlight: 是否返回高亮片段
            dirs: 过滤的目录列表（相对路径），只搜索这些目录下的文档
            with_content: 是否返回文档完整内容

        Yields:
            搜索结果字典
        """
        if not query or not self.bm25:
            return

        # 对查询进行分词
        tokenized_query = self._tokenize(query)

        # BM25 搜索
        scores = self.bm25.get_scores(tokenized_query)

        # 过滤和排序
        filtered = []
        for i, score in enumerate(scores):
            # BM25 对小语料库可能返回负分，但相对分数仍有参考价值
            # 只在分数为 NaN 时跳过
            if score != score:  # NaN 检查
                continue

            doc = self.corpus[i]

            # 目录过滤
            if dirs:
                matched = False
                for d in dirs:
                    # 检查文档路径是否在指定目录内
                    if d in doc["path"]:
                        matched = True
                        break
                if not matched:
                    continue

            filtered.append((i, score))

        # 按分数排序
        filtered.sort(key=lambda x: x[1], reverse=True)

        # 获取 top-N 结果
        for i, score in filtered[:limit]:
            doc = self.corpus[i]
            result = {
                "path": doc["path"],
                "title": doc["title"],
                "score": float(score),
            }
            if with_content:
                result["content"] = doc["content"]
            if highlight:
                result["highlights"] = self._get_highlights(tokenized_query, doc["content"])
            yield result

    def _get_highlights(self, query_terms: List[str], content: str) -> List[str]:
        """获取高亮片段

        Args:
            query_terms: 查询词列表
            content: 文档内容

        Returns:
            高亮片段列表
        """
        if not query_terms:
            return []

        # 查找包含查询词的片段
        highlights = []
        content_lower = content.lower()
        query_lower = [t.lower() for t in query_terms]

        # 高亮：找到包含查询词的位置，返回更长的上下文
        for term in query_lower:
            if term in content_lower:
                idx = content_lower.find(term)
                # 增加上下文范围：从前后 30 字符增加到 100 字符
                start = max(0, idx - 100)
                end = min(len(content), idx + len(term) + 100)
                snippet = content[start:end]
                highlights.append(snippet)
                # 增加片段数量：从 2 个增加到 3 个
                if len(highlights) >= 3:
                    break

        return highlights

    def delete_document(self, path: str):
        """从索引中删除文档

        Args:
            path: 文档路径
        """
        self.corpus = [doc for doc in self.corpus if doc["path"] != path]
        self._save_index()

    def clear(self):
        """清空索引"""
        self.corpus = []
        self.bm25 = None
        if self.corpus_file.exists():
            self.corpus_file.unlink()

    def count(self) -> int:
        """返回索引文档数"""
        return len(self.corpus)


class KnowledgeBaseIndexer:
    """知识库索引管理器"""

    # 可以直接读取的文本格式
    TEXT_EXTENSIONS = {
        ".md", ".txt", ".html", ".htm", ".csv", ".json", ".xml"
    }

    # 需要 markitdown 转换的格式
    CONVERT_EXTENSIONS = {
        # Office 文档
        ".docx", ".doc", ".pptx", ".xlsx", ".xls",
        # PDF
        ".pdf",
        # 图片（需要 OCR）
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
        # 音频（语音转录）
        ".wav", ".mp3", ".m4a",
        # 视频
        ".mp4", ".avi", ".mov", ".mkv",
        # 压缩包
        ".zip",
    }

    def __init__(self, config: KnowledgeBaseConfig):
        """初始化索引管理器

        Args:
            config: 知识库配置
        """
        self.config = config
        self.docs_dir = Path(config.path) / "docs"
        self.index_dir = self._get_index_dir()

    def _get_index_dir(self) -> Path:
        """获取索引目录"""
        if self.config.index_path:
            return Path(self.config.index_path)
        return Path(self.config.path) / ".winwin-index"

    def _discover_documents(self) -> List[Document]:
        """发现知识库中的文档

        同时在 {kb_path}/docs/ 和 {kb_path}/ 目录中搜索

        Returns:
            文档列表
        """
        from tqdm import tqdm

        search_dirs = []

        # 先搜索 docs/ 子目录
        if self.docs_dir.exists():
            search_dirs.append(self.docs_dir)

        # 如果 docs/ 不存在或为空，也搜索根目录
        kb_path = Path(self.config.path)
        if kb_path.exists():
            search_dirs.append(kb_path)

        if not search_dirs:
            return []

        # 先收集所有文件路径
        all_files = []
        seen_paths = set()  # 用于去重

        for search_dir in search_dirs:
            for ext in self.config.extensions:
                for md_file in search_dir.rglob(f"*{ext}"):
                    if md_file.is_file() and str(md_file) not in seen_paths:
                        seen_paths.add(str(md_file))
                        all_files.append(md_file)

        # 使用进度条加载文档
        documents = []
        for md_file in tqdm(all_files, desc="  发现文档", unit="文件"):
            doc = self._load_document(md_file)
            if doc:
                documents.append(doc)

        return documents

    def _load_document(self, path: Path) -> Optional[Document]:
        """加载单个文档

        对于文本格式（.md, .txt 等），直接读取
        对于其他格式（.docx, .pdf 等），使用 markitdown 转换后索引

        Args:
            path: 文档路径

        Returns:
            Document 对象，失败时返回 None
        """
        try:
            ext = path.suffix.lower()

            # 文本格式：直接读取
            if ext in self.TEXT_EXTENSIONS:
                content = path.read_text(encoding="utf-8")
                title = self._extract_title(content, path.stem)
                return Document(
                    path=str(path),
                    title=title,
                    content=content,
                    metadata={
                        "extension": path.suffix,
                        "modified": str(path.stat().st_mtime),
                        "converted": False,
                    },
                )

            # 其他格式：使用 markitdown 转换
            elif ext in self.CONVERT_EXTENSIONS:
                markdown_content = self._convert_document(path)
                if markdown_content:
                    title = self._extract_title(markdown_content, path.stem)
                    return Document(
                        path=str(path),
                        title=title,
                        content=markdown_content,
                        metadata={
                            "extension": path.suffix,
                            "modified": str(path.stat().st_mtime),
                            "converted": True,
                        },
                    )

            return None

        except Exception:
            return None

    def _extract_title(self, content: str, default: str) -> str:
        """从内容中提取标题

        Args:
            content: 文档内容
            default: 默认标题

        Returns:
            标题字符串
        """
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return default

    def _convert_document(self, path: Path) -> Optional[str]:
        """转换文档为 Markdown（使用 markitdown）

        支持所有 markitdown 能转换的格式：
        - Office 文档: .docx, .doc, .pptx, .xlsx, .xls
        - PDF: .pdf
        - 图片（OCR）: .jpg, .jpeg, .png, .gif, .bmp, .webp
        - 音频（语音转录）: .wav, .mp3, .m4a
        - 视频: .mp4, .avi, .mov, .mkv
        - 压缩包: .zip

        Args:
            path: 源文档路径

        Returns:
            转换后的 Markdown 内容，失败返回 None
        """
        from winwin_cli.kb_search.markitdown import run_markitdown
        import tempfile

        ext = path.suffix.lower()

        # 只转换支持的格式
        if ext not in self.CONVERT_EXTENSIONS:
            return None

        try:
            # 使用临时文件存储转换结果
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # 调用 markitdown 转换到临时文件
            run_markitdown(str(path), tmp_path, "md")

            # 读取转换后的内容
            content = Path(tmp_path).read_text(encoding="utf-8")

            # 清理临时文件
            Path(tmp_path).unlink(missing_ok=True)

            return content

        except Exception:
            # 清理临时文件（如果存在）
            if 'tmp_path' in locals():
                Path(tmp_path).unlink(missing_ok=True)
            return None

    def create_index(self) -> IndexInfo:
        """创建知识库索引

        自动将所有支持格式的文档转换为 Markdown 后索引（包括 docx/pdf/pptx/xlsx/图片/音频/视频等）

        Returns:
            索引信息
        """
        click.echo(f"\n正在构建知识库索引: {self.config.name}")

        self.index_dir.mkdir(parents=True, exist_ok=True)
        indexer = BM25Indexer(str(self.index_dir))

        # 先清空旧索引，确保只保留当前存在的文档
        indexer.clear()

        # 发现并加载所有文档（转换在加载时按需进行，会显示进度条）
        documents = self._discover_documents()
        indexer.add_documents(documents)  # 也会显示进度条

        now = datetime.now().isoformat()
        click.echo(f"✓ 索引构建完成: {len(documents)} 个文档\n")

        return IndexInfo(
            knowledge_base=self.config.name,
            document_count=len(documents),
            index_path=str(self.index_dir),
            created_at=now,
            updated_at=None,
        )

    def update_index(self) -> IndexInfo:
        """更新知识库索引

        Returns:
            索引信息
        """
        return self.create_index()

    def get_index_info(self) -> Optional[IndexInfo]:
        """获取索引信息

        Returns:
            索引信息，如果索引不存在返回 None
        """
        if not self.index_dir.exists():
            return None

        indexer = BM25Indexer(str(self.index_dir))
        doc_count = indexer.count()

        now = datetime.now().isoformat()
        return IndexInfo(
            knowledge_base=self.config.name,
            document_count=doc_count,
            index_path=str(self.index_dir),
            created_at=now,
            updated_at=now,
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        highlight: bool = False,
        dirs: Optional[List[str]] = None,
        with_content: bool = False,
    ) -> List[SearchResult]:
        """搜索知识库

        Args:
            query: 搜索查询
            limit: 最大返回结果数
            highlight: 是否返回高亮片段
            dirs: 过滤的目录列表
            with_content: 是否返回文档完整内容

        Returns:
            搜索结果列表
        """
        indexer = BM25Indexer(str(self.index_dir))
        results = []

        for hit in indexer.search(query, limit=limit, highlight=highlight, dirs=dirs, with_content=with_content):
            doc = Document(
                path=hit["path"],
                title=hit["title"],
                content=hit.get("content", ""),
            )
            results.append(
                SearchResult(
                    document=doc,
                    score=hit["score"],
                    highlights=hit.get("highlights", []),
                )
            )

        return results
