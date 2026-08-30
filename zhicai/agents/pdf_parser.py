# -*- coding: utf-8 -*-
"""任务二 Stage 4.2：PDF 智能解析与分块（PyMuPDF 逐页提取）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..algorithms.chunking import chunk_text, split_by_headings
from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult


def _read_pages(path: str) -> list[tuple[int, str]]:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        import pymupdf

        doc = pymupdf.open(str(p))
        try:
            return [(i + 1, page.get_text() or "") for i, page in enumerate(doc)]
        finally:
            doc.close()
    return [(1, p.read_text(encoding="utf-8"))]


class PDFParserAgent(BaseAgent):
    name = "PDFParser"
    state_key = "document"

    def run(self, state: StateManager) -> TaskResult:
        path = state.require("document_path")
        pages = _read_pages(path)
        chunks: list[dict[str, Any]] = []

        for page_num, text in pages:
            sections = split_by_headings(text)
            if sections and any(s["content"].strip() for s in sections):
                for s in sections:
                    if s["content"].strip():
                        chunks.append(
                            {"section_title": s["title"], "content": s["content"], "page_num": page_num, "source": path}
                        )
            else:
                for c in chunk_text(text):
                    chunks.append({"section_title": None, "content": c, "page_num": page_num, "source": path})

        full_text = "\n".join(t for _, t in pages)
        return TaskResult.ok(self.name, {"text": full_text, "chunks": chunks, "path": path})
