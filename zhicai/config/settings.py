# -*- coding: utf-8 -*-
"""运行配置：从 .env 读取路径、模型与浏览器配置。"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "output"
DEFAULT_DB = OUTPUT_DIR / "benchmarks.sqlite"


def _load_dotenv(path: Path | None = None) -> None:
    env_path = path or (ROOT / ".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

QWEN_BASE_URL = os.environ.get(
    "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
QWEN_API_KEY = os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY", "")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen-plus")
QWEN_VL_MODEL = os.environ.get("QWEN_VL_MODEL", "qwen3-vl-plus")
QWEN_TEMPERATURE = float(os.environ.get("QWEN_TEMPERATURE", "0") or "0")

EDGE_PATH = os.environ.get(
    "EDGE_PATH", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)
BROWSER_HEADLESS = os.environ.get("BROWSER_HEADLESS", "false").lower() in ("1", "true", "yes")
COMPLIANCE_LLM_REVIEW = os.environ.get("COMPLIANCE_LLM_REVIEW", "false").lower() in ("1", "true", "yes")
