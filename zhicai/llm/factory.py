# -*- coding: utf-8 -*-
"""LLM 工厂：根据环境变量构建 LangChain 封装或离线 Mock。"""

from __future__ import annotations

import os

from .base import LLM
from .mock_llm import MockLLM


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def build_llm(use_mock: bool | None = None) -> LLM:
    """构建 LLM。未配置 `QWEN_BASE_URL` 时自动回退到 MockLLM（离线）。"""
    base_url = _env("QWEN_BASE_URL")
    if use_mock is None:
        use_mock = not base_url
    if use_mock:
        return MockLLM()
    return build_langchain_llm()


def build_langchain_llm() -> LLM:
    """通过 LangChain `ChatOpenAI` 构建 Qwen3（Ollama / vLLM 的 OpenAI 兼容接口）。"""
    from langchain_openai import ChatOpenAI

    from .langchain_llm import LangChainLLM

    base_url = _env("QWEN_BASE_URL", "http://localhost:11434/v1")
    api_key = _env("QWEN_API_KEY", "EMPTY")
    model_name = _env("QWEN_MODEL", "qwen3:8b")
    temperature = float(_env("QWEN_TEMPERATURE", "0") or "0")

    model = ChatOpenAI(base_url=base_url, api_key=api_key, model=model_name, temperature=temperature)

    vl_model_name = _env("QWEN_VL_MODEL")
    vision_model = None
    if vl_model_name:
        vision_model = ChatOpenAI(
            base_url=base_url, api_key=api_key, model=vl_model_name, temperature=temperature
        )
    return LangChainLLM(model, vision_model=vision_model)
