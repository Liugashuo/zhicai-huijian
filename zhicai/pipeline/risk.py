# -*- coding: utf-8 -*-
"""任务二 · 六阶段研判流水线。

PDFParser -> EvidenceStore -> MarkdownParser -> PriceAgent -> ComplianceAgent -> ReportAgent
"""

from __future__ import annotations

from typing import Any

from ..agents import (
    ComplianceAgent,
    EvidenceStoreAgent,
    MarkdownParserAgent,
    PDFParserAgent,
    PriceAgent,
    ReportAgent,
)
from ..core.pipeline import Pipeline
from ..core.state import StateManager
from ..db.benchmark_store import BenchmarkStore
from ..llm import LLM


class RiskPipeline:
    def __init__(self, llm: LLM | None = None, store: BenchmarkStore | None = None) -> None:
        self.llm = llm
        self.store = store

    def run(self, document_path: str) -> dict[str, Any]:
        state = StateManager()
        state.set("document_path", document_path)
        agents = [
            PDFParserAgent(self.llm),
            EvidenceStoreAgent(self.llm),
            MarkdownParserAgent(self.llm),
            PriceAgent(self.llm, store=self.store),
            ComplianceAgent(self.llm),
            ReportAgent(self.llm),
        ]
        results = Pipeline(state).execute(agents)
        return {"state": state, "results": results, "report": state.get("report")}
