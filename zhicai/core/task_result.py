# -*- coding: utf-8 -*-
"""结构化任务结果：Executor -> TaskResult -> Pipeline -> StateManager 单向数据流。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class TaskResult:
    agent: str
    status: TaskStatus = TaskStatus.SUCCESS
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, agent: str, data: Any = None, **metadata: Any) -> "TaskResult":
        return cls(agent=agent, status=TaskStatus.SUCCESS, data=data, metadata=metadata)

    @classmethod
    def fail(cls, agent: str, error: str, **metadata: Any) -> "TaskResult":
        return cls(agent=agent, status=TaskStatus.FAILED, error=error, metadata=metadata)

    @property
    def is_ok(self) -> bool:
        return self.status is TaskStatus.SUCCESS

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }
