# -*- coding: utf-8 -*-
"""运行配置：路径与模型相关环境变量名。"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "output"
DEFAULT_DB = OUTPUT_DIR / "benchmarks.sqlite"

QWEN_BASE_URL = os.environ.get("QWEN_BASE_URL", "http://localhost:11434/v1")
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "EMPTY")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen3:8b")
QWEN_VL_MODEL = os.environ.get("QWEN_VL_MODEL", "")
