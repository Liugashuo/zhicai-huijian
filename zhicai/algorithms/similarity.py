# -*- coding: utf-8 -*-
"""关键词相似度算法：Jaccard + Bigram。

分词策略：
- 英文：完整单词
- 数字：数值
- 中文：单字 + 二元组(bigram)
"""

from __future__ import annotations

import re

_EN_RE = re.compile(r"[a-z]+")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def tokenize(text: str) -> set[str]:
    s = (text or "").lower()
    tokens: set[str] = set()
    tokens.update(_EN_RE.findall(s))
    tokens.update(_NUM_RE.findall(s))
    cjk = _CJK_RE.findall(s)
    tokens.update(cjk)
    for i in range(len(cjk) - 1):
        tokens.add(cjk[i] + cjk[i + 1])
    return tokens


def jaccard_similarity(a: str, b: str) -> float:
    A = tokenize(a)
    B = tokenize(b)
    if not A and not B:
        return 1.0
    union = A | B
    if not union:
        return 0.0
    return len(A & B) / len(union)
