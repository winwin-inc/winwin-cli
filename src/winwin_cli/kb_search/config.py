"""知识库检索工具 - 配置加载模块"""

import os
from pathlib import Path
from typing import List, Optional
import yaml

from winwin_cli.kb_search.models import KnowledgeBaseConfig


class KnowledgeBaseLoader:
    """知识库配置加载器"""

    DEFAULT_CONFIG_FILENAME = "knowledge-bases.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """初始化加载器

        Args:
            config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        self.config_path = config_path

    def load(self) -> List[KnowledgeBaseConfig]:
        """加载知识库配置

        Returns:
            知识库配置列表

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置文件格式错误
        """
        path = self._find_config_file()
        if not path:
            return []

        return self._parse_config(path)

    def _find_config_file(self) -> Optional[Path]:
        """查找配置文件"""
        if self.config_path:
            path = Path(self.config_path)
            if path.exists():
                return path
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        # 查找默认配置文件
        default_paths = [
            Path.cwd() / self.DEFAULT_CONFIG_FILENAME,
            Path.home() / ".config" / "winwin-cli" / self.DEFAULT_CONFIG_FILENAME,
        ]

        for path in default_paths:
            if path.exists():
                return path

        return None

    def _parse_config(self, path: Path) -> List[KnowledgeBaseConfig]:
        """解析配置文件

        Args:
            path: 配置文件路径

        Returns:
            知识库配置列表

        Raises:
            ValueError: 配置文件格式错误
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 解析错误: {e}")

        if not isinstance(data, dict):
            raise ValueError("配置文件必须是 YAML 对象")

        if "knowledge_bases" not in data:
            raise ValueError("配置文件必须包含 knowledge_bases 键")

        knowledge_bases = data.get("knowledge_bases", [])
        if not isinstance(knowledge_bases, list):
            raise ValueError("knowledge_bases 必须是列表")

        configs = []
        for i, kb_data in enumerate(knowledge_bases):
            try:
                config = KnowledgeBaseConfig(**kb_data)
                configs.append(config)
            except Exception as e:
                raise ValueError(f"知识库配置 #{i+1} 错误: {e}")

        return configs

    def save(self, configs: List[KnowledgeBaseConfig]):
        """保存知识库配置

        Args:
            configs: 知识库配置列表

        Raises:
            ValueError: 保存失败
        """
        path = self._find_config_file()
        if not path:
            # 如果没有配置文件，创建默认位置
            path = Path.cwd() / self.DEFAULT_CONFIG_FILENAME

        data = {
            "knowledge_bases": [
                {
                    "name": c.name,
                    "path": c.path,
                    "description": c.description,
                    "enabled": c.enabled,
                    "index_path": c.index_path,
                    "extensions": c.extensions,
                }
                for c in configs
            ]
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            raise ValueError(f"保存配置失败: {e}")


def load_global_config() -> List[KnowledgeBaseConfig]:
    """加载全局知识库配置

    优先级：
    1. 环境变量 WINWIN_KB_CONFIG 指定的文件
    2. 当前目录的 knowledge-bases.yaml
    3. ~/.config/winwin-cli/knowledge-bases.yaml

    Returns:
        知识库配置列表
    """
    config_path = os.environ.get("WINWIN_KB_CONFIG")
    loader = KnowledgeBaseLoader(config_path)
    return loader.load()
