# -*- coding: utf-8 -*-
"""LLM 统一封装层（生产环境，仅真实 Qwen）。"""

from .base import LLM
from .factory import build_llm, build_langchain_llm

__all__ = ["LLM", "LangChainLLM", "build_llm", "build_langchain_llm"]


def __getattr__(name: str):
    if name == "LangChainLLM":
        from .langchain_llm import LangChainLLM

        return LangChainLLM
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
