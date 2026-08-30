# -*- coding: utf-8 -*-
"""任务二 Stage 4.6：六维度合规风险 AI 审查（ComplianceAgent）。"""

from __future__ import annotations

import re
from typing import Any

from ..config.compliance_rules import DIMENSIONS, DIMENSION_NAMES, RULES
from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult

_SEVERITY_WEIGHT = {"high": 15, "medium": 8, "low": 4}


def _snippet(text: str, start: int, end: int, radius: int = 40) -> str:
    lo = max(0, start - radius)
    hi = min(len(text), end + radius)
    return text[lo:hi].strip()


class ComplianceAgent(BaseAgent):
    name = "ComplianceAgent"
    state_key = "compliance"

    def run(self, state: StateManager) -> TaskResult:
        evidence = state.require("evidence")
        chunks = list(evidence.get("chunks", []))
        findings: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        for chunk in chunks:
            title = chunk.get("section_title") or ""
            content = chunk.get("content", "")
            full = (f"{title}\n{content}").strip()
            for rule in RULES:
                for pattern in rule["patterns"]:
                    m = re.search(pattern, full)
                    if not m:
                        continue
                    key = (chunk["chunk_id"], rule["id"])
                    if key in seen:
                        continue
                    seen.add(key)
                    findings.append(
                        {
                            "chunk_id": chunk["chunk_id"],
                            "section_title": chunk.get("section_title"),
                            "rule_id": rule["id"],
                            "dimension": rule["dimension"],
                            "dimension_name": DIMENSION_NAMES[rule["dimension"]],
                            "category": rule["category"],
                            "severity": rule["severity"],
                            "matched_text": m.group(0),
                            "context": _snippet(full, m.start(), m.end()),
                            "description": rule["description"],
                            "suggestion": rule["suggestion"],
                        }
                    )
                    break

        # LLM 语义层（MockLLM 返回空，真实模型在此补充语义级发现）。
        if self.llm is not None:
            for chunk in chunks:
                title = chunk.get("section_title") or ""
                full = (f"{title}\n{chunk.get('content', '')}").strip()
                for dim in DIMENSIONS:
                    for f in self.llm.review_compliance(full, dim["key"]):
                        key = (chunk["chunk_id"], f.get("rule_id", dim["key"]))
                        if key in seen:
                            continue
                        seen.add(key)
                        findings.append({**f, "chunk_id": chunk["chunk_id"], "dimension": dim["key"]})

        score = min(100, sum(_SEVERITY_WEIGHT.get(f["severity"], 4) for f in findings))
        return TaskResult.ok(self.name, {"findings": findings, "score": score})
