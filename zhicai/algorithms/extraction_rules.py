# -*- coding: utf-8 -*-
"""确定性兜底解析器：识别「数量+单位+单价+小计」并做「小计≈单价×数量」反向校验。"""

from __future__ import annotations

import re
from typing import Any

_UNITS = "台|个|套|件|项|米|箱|支|张|本|卷|吨|把|块|根|条|人|天|次|月|年|kg|KG|台套|台/套|册|批"
_LINE_RE = re.compile(
    r"(?P<name>[^\d\n]{2,}?)\s*"
    r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>%s)"
    r"(?:[^\d\n]{0,4}?(?P<unit_price>\d+(?:\.\d+)?))?"
    r"(?:[^\d\n]{0,4}?(?P<subtotal>\d+(?:\.\d+)?))?"
    % _UNITS
)


def parse_line_items(text: str, tolerance: float = 0.02) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        m = _LINE_RE.search(line)
        if not m:
            continue
        qty = float(m.group("qty"))
        unit_price_raw = m.group("unit_price")
        subtotal_raw = m.group("subtotal")
        if unit_price_raw is None or subtotal_raw is None:
            continue
        unit_price = float(unit_price_raw)
        subtotal = float(subtotal_raw)
        item = {
            "name": m.group("name").strip(),
            "quantity": qty,
            "unit": m.group("unit"),
            "unit_price": unit_price,
            "subtotal": subtotal,
            "trap": False,
        }
        if qty > 1 and subtotal and abs(subtotal - unit_price) <= tolerance * max(unit_price, 1):
            item["trap"] = True
            item["subtotal"] = round(qty * unit_price, 2)
        expected = round(qty * unit_price, 2)
        item["verified"] = abs(subtotal - expected) <= tolerance * max(expected, 1) or item["trap"]
        items.append(item)
    return items
