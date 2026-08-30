# -*- coding: utf-8 -*-
"""LLM 统一封装层。

- `LLM`：领域接口，所有语义判断统一经由该接口；
- `LangChainLLM`：通过 LangChain（ChatOpenAI）调用 Qwen3 的 OpenAI 兼容接口；
- `MockLLM`：确定性实现，离线可运行、测试可复现；
- `build_llm`：按环境变量构建真实 LangChainLLM 或回退 MockLLM。
"""

from .base import LLM
from .factory import build_llm, build_langchain_llm
from .mock_llm import MockLLM

__all__ = ["LLM", "LangChainLLM", "MockLLM", "build_llm", "build_langchain_llm"]


def __getattr__(name: str):
    if name == "LangChainLLM":
        from .langchain_llm import LangChainLLM

        return LangChainLLM
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
