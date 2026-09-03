# -*- coding: utf-8 -*-
"""LLM 领域接口。

按《技术方案与算法说明》的「AI/Python 分治」原则：
- LLM 只负责感知、识别与判断；
- Python 负责流程编排、确定性算法与反爬。
所有语义判断统一经由本接口，LangChain 负责底层大模型 API 的封装与调用。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLM(ABC):
    """文本 + 视觉大模型领域接口（Qwen 文本模型 / Qwen-VL 视觉模型）。

    实现：LangChainLLM，通过 LangChain（ChatOpenAI）调用 Qwen 的 OpenAI 兼容接口。
    """

    # ---- 任务一 · 寻源 ----
    @abstractmethod
    def classify_product(self, name: str) -> dict[str, Any]:
        """品类识别 / 参数提取 / 检索关键词生成。"""

    @abstractmethod
    def decide_browser_action(
        self, context: dict[str, Any], screenshots: list[Any] | None = None
    ) -> dict[str, Any]:
        """VLM 浏览器决策：截图 + 上下文 -> 结构化动作 JSON。"""

    @abstractmethod
    def assess_quality(self, metrics: dict[str, Any]) -> str:
        """基准价数据质量的定性评估。"""

    # ---- 任务二 · 研判 ----
    @abstractmethod
    def extract_metadata(self, text: str) -> dict[str, Any]:
        """招标元数据提取。"""

    @abstractmethod
    def extract_items(self, text: str) -> list[dict[str, Any]]:
        """产品条目提取。"""

    @abstractmethod
    def extract_sections(self, text: str) -> list[dict[str, Any]]:
        """章节结构提取。"""

    @abstractmethod
    def review_compliance(self, chunk: str, dimension: str) -> list[dict[str, Any]]:
        """单维度合规语义审查。"""

    @abstractmethod
    def summarize(self, payload: dict[str, Any]) -> str:
        """综合研判总结。"""
