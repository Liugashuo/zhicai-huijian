# -*- coding: utf-8 -*-
"""StateManager：所有状态变更统一收口，Executor 不碰状态、Planner 只读状态。"""

from __future__ import annotations

from typing import Any

from .task_result import TaskResult


class StateManager:
    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self._state: dict[str, Any] = dict(initial or {})
        self._results: list[TaskResult] = []

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def update(self, mapping: dict[str, Any]) -> None:
        self._state.update(mapping)

    def require(self, key: str) -> Any:
        if key not in self._state:
            raise KeyError(f"StateManager 缺少必要状态: {key!r}")
        return self._state[key]

    def record(self, result: TaskResult) -> None:
        self._results.append(result)

    def results(self, agent: str | None = None) -> list[TaskResult]:
        if agent is None:
            return list(self._results)
        return [r for r in self._results if r.agent == agent]

    def last_result(self, agent: str) -> TaskResult | None:
        for r in reversed(self._results):
            if r.agent == agent:
                return r
        return None

    def snapshot(self) -> dict[str, Any]:
        return {"state": dict(self._state), "results": [r.to_dict() for r in self._results]}
