# -*- coding: utf-8 -*-
"""任务二 Stage 4.3：证据溯源存储（EvidenceStore）。"""

from __future__ import annotations

from typing import Any

from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult


class EvidenceStoreAgent(BaseAgent):
    name = "EvidenceStore"
    state_key = "evidence"

    def run(self, state: StateManager) -> TaskResult:
        document = state.require("document")
        chunks: list[dict[str, Any]] = []
        by_id: dict[str, dict[str, Any]] = {}
        for idx, c in enumerate(document.get("chunks", []), start=1):
            page = c.get("page_num") or 1
            chunk_id = f"bid_p{page}_c{idx}"
            record = {**c, "chunk_id": chunk_id}
            chunks.append(record)
            by_id[chunk_id] = record
        return TaskResult.ok(self.name, {"chunks": chunks, "by_id": by_id})
