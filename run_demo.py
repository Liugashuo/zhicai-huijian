# -*- coding: utf-8 -*-
"""生产演示：真实 Qwen 六阶段风险研判，可选用真实浏览器自主寻源。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from zhicai.config.settings import DEFAULT_DB, OUTPUT_DIR
from zhicai.db.benchmark_store import BenchmarkStore
from zhicai.llm import build_llm
from zhicai.pipeline import RiskPipeline, SourcingPipeline
from zhicai.reporting import render_report_pdf

ROOT = Path(__file__).resolve().parent

MARKET_SEED = {
    "台式计算机": [4200, 4300, 4400, 4500, 4600],
    "键鼠套装": [80, 90, 100, 110],
    "打印机": [1500, 1600, 1700, 1800],
    "网络线缆": [20, 22, 24, 26],
}


def seed_store(store: BenchmarkStore) -> None:
    for name, prices in MARKET_SEED.items():
        pid = store.upsert_product(name, category="电子", platform="京东")
        for price in prices:
            store.add_benchmark(pid, price, platform="京东", source_channel="DOM")


def make_sample_pdf(txt_path: Path, pdf_path: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    font = None
    for name in ("msyh.ttc", "msyh.ttf", "simhei.ttf", "simsun.ttc"):
        p = Path(r"C:\Windows\Fonts") / name
        if p.exists():
            font = str(p)
            break
    font_name = "Helvetica"
    if font:
        pdfmetrics.registerFont(TTFont("CJK", font))
        font_name = "CJK"

    style = ParagraphStyle("cjk", fontName=font_name, fontSize=11, leading=17)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    story = [
        Paragraph(line.replace(" ", "&nbsp;") if line.strip() else "&nbsp;", style)
        for line in txt_path.read_text(encoding="utf-8").splitlines()
    ]
    story.insert(0, Spacer(1, 6))
    doc.build(story)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    ap = argparse.ArgumentParser(description="智采慧鉴生产演示")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--bid", default=str(ROOT / "examples" / "sample_bid.txt"))
    ap.add_argument("--sourcing", default=None, help="商品名，运行真实浏览器自主寻源")
    args = ap.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    store = BenchmarkStore(args.db)
    seed_store(store)
    llm = build_llm()

    if args.sourcing:
        print("=" * 60)
        print("任务一 · 自主寻源（真实浏览器）")
        out = SourcingPipeline(llm, store=store).run(args.sourcing, target_count=5)
        benchmark = out["state"].get("benchmark", {})
        print("采集条目:", len(out["state"].get("sourced_items", {}).get("items", [])))
        print("基准价指标:", benchmark.get("metrics"))
        print("AI 定性评估:", benchmark.get("ai_assessment"))

    print("=" * 60)
    print("任务二 · 六阶段风险研判（真实 Qwen）")
    pdf_path = OUTPUT_DIR / "sample_bid.pdf"
    make_sample_pdf(Path(args.bid), pdf_path)
    risk = RiskPipeline(llm, store=store).run(str(pdf_path))
    report = risk["report"]
    print("综合风险评分:", report["score"])
    print("合规问题数:", len(report["findings"]))
    print("价格分析项:", len(report["price_rows"]))

    md_path = OUTPUT_DIR / "report.md"
    md_path.write_text(report["markdown"], encoding="utf-8")
    report_pdf = render_report_pdf(report, str(OUTPUT_DIR / "report.pdf"))

    print("报告已生成:")
    print("  Markdown:", md_path)
    print("  PDF     :", report_pdf)
    print("  基准库  :", args.db)
    store.close()


if __name__ == "__main__":
    main()
