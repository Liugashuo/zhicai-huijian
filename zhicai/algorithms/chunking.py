# -*- coding: utf-8 -*-
"""PDF 智能分块：中文标题模式优先，无标题时定长分块（200 字符重叠）。"""

from __future__ import annotations

import re
from typing import Any

_CN_HEADING_RE = re.compile(
    r"^\s*(第[一二三四五六七八九十百\d]+[章节部分]|[一二三四五六七八九十]+、|（[一二三四五六七八九十]+）)\s*\S*"
)
_NUM_HEADING_RE = re.compile(r"^\s*\d+(?:\.\d+)*[、.．]\s*[^：:，,；;。]{1,24}\s*$")


def _is_heading(line: str) -> bool:
    return bool(_CN_HEADING_RE.match(line) or _NUM_HEADING_RE.match(line))


def split_by_headings(text: str) -> list[dict[str, Any]]:
    lines = (text or "").splitlines()
    sections: list[dict[str, Any]] = []
    current_title = ""
    buf: list[str] = []

    def flush() -> None:
        if buf:
            sections.append({"title": current_title, "content": "\n".join(buf)})
        buf.clear()

    for line in lines:
        if _is_heading(line):
            flush()
            current_title = line.strip()
        else:
            buf.append(line)
    flush()
    return sections


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    step = max(chunk_size - overlap, 1)
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += step
    return chunks
