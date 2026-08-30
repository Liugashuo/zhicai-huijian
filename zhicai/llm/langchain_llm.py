# -*- coding: utf-8 -*-
"""LangChain 统一 LLM 封装。

使用 LangChain 的 `ChatOpenAI` 调用 Qwen3（Ollama / vLLM 的 OpenAI 兼容接口）：
- `ChatPromptTemplate` 构造消息；
- 文本类任务输出 JSON 文本，并用「截断 JSON 自修复」兜底；
- 视觉决策走多模态消息（截图以 data URL 传入 Qwen3-VL）。
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from ..algorithms.json_repair import extract_json
from .base import LLM


_PRODUCT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "你是政府采购寻源分析专家。仅输出 JSON，不要输出多余文字。"),
        (
            "human",
            '对商品进行分类并提取检索关键词：{name}\n'
            '返回 JSON：{{"category": "电子/办公/通用物资/工程服务", "keywords": ["..."], "reasoning": "..."}}',
        ),
    ]
)

_BROWSER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "你是电商商品采集的视觉决策 Agent。仅输出 JSON，不要输出多余文字。"),
        (
            "human",
            '当前上下文：{context}\n'
            '输出下一步动作 JSON：{{"action": "scroll/click_product/extract_products/extract_detail/go_back/wait/done", "index": 0, "reason": "..."}}',
        ),
    ]
)

_METADATA_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "你是招投标信息抽取专家。仅输出 JSON，不要输出多余文字。"),
        (
            "human",
            '提取招标元数据：{text}\n'
            '返回 JSON：{{"项目名称": "", "项目编号": "", "采购人": "", "预算总额": "", "资质要求": "", "技术参数": ""}}',
        ),
    ]
)

_ITEMS_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "你是报价单解析专家。仅输出 JSON 数组，不要输出多余文字。"),
        (
            "human",
            '提取报价条目（品名、规格、数量、单位、预算价、报价）：{text}\n'
            '返回 JSON 数组：[{{"name": "", "spec": "", "quantity": 0, "unit": "", "budget_price": 0, "quote_price": 0}}]',
        ),
    ]
)

_SECTIONS_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "你是文档结构解析专家。仅输出 JSON 数组，不要输出多余文字。"),
        (
            "human",
            '提取章节标题与内容摘要：{text}\n'
            '返回 JSON 数组：[{{"title": "", "summary": ""}}]',
        ),
    ]
)

_ASSESS_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "你是数据质量评估专家。用简短中文给出结论。"),
        ("human", "基于基准价指标评估数据质量：{metrics}"),
    ]
)

_COMPLIANCE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "你是政府采购合规审查专家。仅输出 JSON 数组，未发现问题输出 []。"),
        (
            "human",
            '对以下文本做「{dimension}」维度合规审查，仅输出违规项：\n{chunk}\n'
            '返回 JSON 数组：[{{"rule_id": "", "category": "", "severity": "high/medium/low", "matched_text": "", "description": "", "suggestion": ""}}]',
        ),
    ]
)

_SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "你是采购风险研判总结专家。用简短中文给出综合结论与建议。"),
        ("human", "基于研判结果给出总结：{payload}"),
    ]
)


class LangChainLLM(LLM):
    """通过 LangChain BaseChatModel 调用 Qwen3（文本 + 可选视觉模型）。"""

    def __init__(self, model: BaseChatModel, vision_model: BaseChatModel | None = None) -> None:
        self.model = model
        self.vision_model = vision_model

    def _invoke(self, prompt: ChatPromptTemplate, **variables: Any) -> str:
        messages = prompt.invoke(variables).to_messages()
        resp = self.model.invoke(messages)
        return str(resp.content) if resp.content else ""

    def _invoke_json(self, prompt: ChatPromptTemplate, **variables: Any) -> Any:
        return extract_json(self._invoke(prompt, **variables))

    def classify_product(self, name: str) -> dict[str, Any]:
        return self._invoke_json(_PRODUCT_PROMPT, name=name)

    def decide_browser_action(
        self, context: dict[str, Any], screenshots: list[Any] | None = None
    ) -> dict[str, Any]:
        if self.vision_model is not None and screenshots:
            return self._invoke_vision(context, screenshots)
        return self._invoke_json(_BROWSER_PROMPT, context=json.dumps(context, ensure_ascii=False))

    def _invoke_vision(self, context: dict[str, Any], screenshots: list[Any]) -> dict[str, Any]:
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    "你是电商商品采集的视觉决策 Agent。基于截图与上下文，输出下一步动作 JSON。\n"
                    f"上下文：{json.dumps(context, ensure_ascii=False)}\n"
                    '输出 JSON：{"action": "scroll/click_product/extract_products/extract_detail/go_back/wait/done", "index": 0, "reason": "..."}'
                ),
            }
        ]
        for shot in screenshots[-3:]:
            content.append({"type": "image_url", "image_url": {"url": shot}})
        resp = self.vision_model.invoke([HumanMessage(content=content)])
        return extract_json(str(resp.content or ""))

    def assess_quality(self, metrics: dict[str, Any]) -> str:
        return self._invoke(_ASSESS_PROMPT, metrics=json.dumps(metrics, ensure_ascii=False)).strip()

    def extract_metadata(self, text: str) -> dict[str, Any]:
        return self._invoke_json(_METADATA_PROMPT, text=text[:5000])

    def extract_items(self, text: str) -> list[dict[str, Any]]:
        return self._invoke_json(_ITEMS_PROMPT, text=text)

    def extract_sections(self, text: str) -> list[dict[str, Any]]:
        return self._invoke_json(_SECTIONS_PROMPT, text=text[:6000])

    def review_compliance(self, chunk: str, dimension: str) -> list[dict[str, Any]]:
        return self._invoke_json(_COMPLIANCE_PROMPT, chunk=chunk, dimension=dimension)

    def summarize(self, payload: dict[str, Any]) -> str:
        return self._invoke(_SUMMARY_PROMPT, payload=json.dumps(payload, ensure_ascii=False)).strip()
