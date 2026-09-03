# -*- coding: utf-8 -*-
"""LLM 工厂：构建真实 Qwen 的 LangChain 封装（生产环境，无 Mock 回退）。"""

from __future__ import annotations

from ..config.settings import (
    QWEN_API_KEY,
    QWEN_BASE_URL,
    QWEN_MODEL,
    QWEN_TEMPERATURE,
    QWEN_VL_MODEL,
)
from .base import LLM


def build_llm() -> LLM:
    """构建真实 Qwen LLM。未配置 API Key 时直接抛错，不静默降级。"""
    if not QWEN_API_KEY:
        raise RuntimeError("未配置 QWEN_API_KEY（请在项目根目录 .env 中设置）")
    return build_langchain_llm()


def build_langchain_llm() -> LLM:
    """通过 LangChain `ChatOpenAI` 调用 Qwen 的 OpenAI 兼容接口。"""
    from langchain_openai import ChatOpenAI

    from .langchain_llm import LangChainLLM

    model = ChatOpenAI(
        base_url=QWEN_BASE_URL,
        api_key=QWEN_API_KEY,
        model=QWEN_MODEL,
        temperature=QWEN_TEMPERATURE,
    )
    vision_model = None
    if QWEN_VL_MODEL:
        vision_model = ChatOpenAI(
            base_url=QWEN_BASE_URL,
            api_key=QWEN_API_KEY,
            model=QWEN_VL_MODEL,
            temperature=QWEN_TEMPERATURE,
        )
    return LangChainLLM(model, vision_model=vision_model)
