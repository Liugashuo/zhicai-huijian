# -*- coding: utf-8 -*-
"""截断 JSON 自修复算法：基于栈匹配补齐未闭合的字符串/数组/对象。"""

from __future__ import annotations

import json
import re
from typing import Any


def _find_json_start(text: str) -> int:
    for i, ch in enumerate(text):
        if ch in "{[":
            return i
    return -1


def repair_json(text: str) -> str:
    text = (text or "").strip()
    start = _find_json_start(text)
    if start < 0:
        return "{}"
    text = text[start:]

    out: list[str] = []
    stack: list[str] = []
    in_string = False
    escaped = False
    for ch in text:
        out.append(ch)
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]":
            if stack and stack[-1] == ch:
                stack.pop()

    if in_string:
        out.append('"')
    while stack:
        out.append(stack.pop())
    return "".join(out)


def extract_json(text: str) -> Any:
    text = (text or "").strip()
    for candidate in (text, repair_json(text)):
        try:
            return json.loads(candidate)
        except Exception:  # noqa: BLE001
            continue
    m = re.search(r"[\{\[].*[\}\]]", text, re.DOTALL)
    if m:
        try:
            return json.loads(repair_json(m.group(0)))
        except Exception:  # noqa: BLE001
            pass
    return {}
