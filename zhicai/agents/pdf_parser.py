# -*- coding: utf-8 -*-
"""任务二 Stage 4.2：PDF 智能解析与分块。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..algorithms.chunking import chunk_text, split_by_headings
from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult


def _read_text(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        import pdfplumber

        with pdfplumber.open(str(p)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    return p.read_text(encoding="utf-8")


class PDFParserAgent(BaseAgent):
    name = "PDFParserAgent"
    state_key = "document"

    def run(self, state: StateManager) -> TaskResult:
        path = state.require("document_path")
        text = _read_text(path)
        sections = split_by_headings(text)
        if sections and any(s["content"].strip() for s in sections):
            chunks = [
                {"section_title": s["title"], "content": s["content"], "page_num": None, "source": path}
                for s in sections
                if s["content"].strip()
            ]
        else:
            chunks = [
                {"section_title": None, "content": c, "page_num": None, "source": path}
                for c in chunk_text(text)
            ]
        return TaskResult.ok(self.name, {"text": text, "chunks": chunks, "path": path})
