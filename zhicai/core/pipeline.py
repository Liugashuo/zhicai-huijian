# -*- coding: utf-8 -*-
"""Pipeline：编排 Agent，统一收口状态变更，保证单向数据流。"""

from __future__ import annotations

from typing import Iterable

from .agent import BaseAgent
from .state import StateManager
from .task_result import TaskResult, TaskStatus


class Pipeline:
    def __init__(self, state: StateManager | None = None) -> None:
        self.state = state or StateManager()

    def execute(self, agents: Iterable[BaseAgent], stop_on_error: bool = True) -> list[TaskResult]:
        results: list[TaskResult] = []
        for agent in agents:
            result = self._run_agent(agent)
            results.append(result)
            if stop_on_error and not result.is_ok:
                break
        return results

    def _run_agent(self, agent: BaseAgent) -> TaskResult:
        self.state.record(TaskResult(agent.name, status=TaskStatus.RUNNING))
        try:
            result = agent.run(self.state)
        except Exception as exc:  # noqa: BLE001 - 兜底，避免单个 Agent 拖垮整条流水线
            result = TaskResult.fail(agent.name, f"{type(exc).__name__}: {exc}")
        else:
            if result.is_ok and agent.state_key is not None:
                self.state.set(agent.state_key, result.data)
        self.state.record(result)
        return result
