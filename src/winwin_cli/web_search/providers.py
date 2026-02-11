"""搜索引擎后端 Provider 实现"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Optional
from winwin_cli.kb_search.markitdown import run_markitdown


@dataclass
class SearchResult:
    """搜索结果数据类"""
    title: str
    url: str
    snippet: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FetchResult:
    """网页爬取结果数据类"""
    url: str
    content: str  # Markdown 格式内容
    title: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class BaseProvider(ABC):
    """搜索引擎后端基类"""

    name: str = ""
    description: str = ""
    requires_api_key: bool = False

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        """执行搜索"""
        ...

    def fetch(self, url: str) -> FetchResult:
        """从 URL 爬取内容

        Args:
            url: 网页地址

        Returns:
            爬取结果
        """
        raise NotImplementedError(f"Provider {self.name} 不支持网页爬取功能。")


class DuckDuckGoProvider(BaseProvider):
    """DuckDuckGo 搜索引擎（使用 ddgs 包，免 Key）"""

    name = "duckduckgo"
    description = "DuckDuckGo 搜索（使用 ddgs 包，免 Key）"
    requires_api_key = False

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        """使用 ddgs 搜索

        Args:
            query: 搜索关键词
            limit: 返回结果数量

        Returns:
            搜索结果列表
        """
        try:
            from ddgs import DDGS
        except ImportError:
            raise ImportError(
                "未安装 ddgs 库。\n"
                "请运行: uv pip install ddgs"
            )

        results = []
        try:
            with DDGS() as ddgs:
                ddgs_results = ddgs.text(query, max_results=limit)
                if ddgs_results:
                    for r in ddgs_results:
                        results.append(SearchResult(
                            title=r.get("title", ""),
                            url=r.get("href", ""),
                            snippet=r.get("body", ""),
                        ))
        except Exception as e:
            # 如果是网络问题，抛出更清晰的错误
            msg = str(e).lower()
            if any(k in msg for k in ["proxy", "timeout", "connection", "http", "status code 403"]):
                raise RuntimeError(f"DuckDuckGo 网络请求失败，请检查网络（可能需要代理）。详细错误: {e}")
            raise e
            
        if not results:
            # 如果没有抛出异常但结果为空，通常是 DDG 屏蔽或地区不可达
            pass
            
        return results


class TavilyProvider(BaseProvider):
    """Tavily 搜索引擎（需要 API Key，专为 AI 设计）"""

    name = "tavily"
    description = "Tavily AI 搜索（需要 API Key，免费额度 1000 次/月）"
    requires_api_key = True

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        """使用 Tavily 搜索"""
        import os

        api_key = self.api_key or os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError(
                "Tavily 搜索需要 API Key。\n"
                "获取免费 API Key: https://app.tavily.com"
            )

        try:
            from tavily import TavilyClient
        except ImportError:
            raise ImportError("未安装 tavily-python 库。")

        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=limit)

        results = []
        for r in response.get("results", []):
            results.append(SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
            ))
        return results

    def fetch(self, url: str) -> FetchResult:
        """使用 Tavily 提取内容"""
        import os
        api_key = self.api_key or os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("Tavily 提取需要 API Key。")

        try:
            from tavily import TavilyClient
        except ImportError:
            raise ImportError("未安装 tavily-python 库。")

        client = TavilyClient(api_key=api_key)
        try:
            # 优先使用 extract API (如果客户端支持)
            if hasattr(client, 'extract'):
                response = client.extract(urls=[url])
                result = response.get("results", [{}])[0]
                return FetchResult(
                    url=url,
                    content=result.get("raw_content", result.get("content", "")),
                    title=result.get("title")
                )
            else:
                # 降级使用 search 包含内容
                response = client.search(query=url, search_depth="advanced", include_raw_content=True)
                for r in response.get("results", []):
                    if r.get("url") == url:
                        return FetchResult(url=url, content=r.get("raw_content", ""), title=r.get("title"))
                raise ValueError("Tavily 未能提取到该内容")
        except Exception as e:
            raise RuntimeError(f"Tavily 提取失败: {e}")


class MarkItDownProvider(BaseProvider):
    """使用 MarkItDown 进行通用网页爬取"""

    name = "markitdown"
    description = "使用本地 MarkItDown 引擎进行网页爬取"
    requires_api_key = False

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        raise NotImplementedError("MarkItDown 不支持搜索功能。")

    def fetch(self, url: str) -> FetchResult:
        try:
            import tempfile
            import os
            from pathlib import Path

            with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                run_markitdown(url, tmp_path, "md")
                content = Path(tmp_path).read_text(encoding="utf-8")
                return FetchResult(url=url, content=content)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            error_msg = str(e)
            if "Could not convert" in error_msg:
                error_msg = f"{error_msg} (提示: 可能是由于网站 WAF 拦截、需要登录或暂不支持该格式)"
            raise RuntimeError(f"MarkItDown 爬取失败: {error_msg}")


# 可用的后端引擎注册表
PROVIDERS = {
    "duckduckgo": DuckDuckGoProvider,
    "tavily": TavilyProvider,
    "markitdown": MarkItDownProvider,
}

DEFAULT_PROVIDER = "duckduckgo"
DEFAULT_FETCH_PROVIDER = "markitdown"


def get_provider(name: str, api_key: Optional[str] = None) -> BaseProvider:
    """获取搜索引擎实例

    Args:
        name: 搜索引擎名称
        api_key: API Key（可选）

    Returns:
        搜索引擎实例

    Raises:
        ValueError: 不支持的搜索引擎
    """
    provider_cls = PROVIDERS.get(name)
    if not provider_cls:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"不支持的搜索引擎: {name}。可用: {available}")

    if provider_cls.requires_api_key:
        return provider_cls(api_key=api_key)
    return provider_cls()
