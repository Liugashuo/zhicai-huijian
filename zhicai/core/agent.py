# -*- coding: utf-8 -*-
"""Agent 基类：每个 Agent 只依赖 LLM 推理，不直接修改流程状态。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .llm import LLMProvider
from .state import StateManager
from .task_result import TaskResult


class BaseAgent(ABC):
    name: str = "agent"
    state_key: str | None = None

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm

    @abstractmethod
    def run(self, state: StateManager) -> TaskResult:
        """执行 Agent 逻辑并返回结构化 TaskResult。"""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
