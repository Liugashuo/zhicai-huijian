# -*- coding: utf-8 -*-
"""ReportLab 风险研判报告输出。"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _find_cjk_font() -> str | None:
    for name in ("msyh.ttc", "msyh.ttf", "simhei.ttf", "simsun.ttc"):
        p = Path(r"C:\Windows\Fonts") / name
        if p.exists():
            return str(p)
    return None


def render_report_pdf(report: dict[str, Any], output_path: str) -> str:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font = _find_cjk_font()
    font_name = "Helvetica"
    if font:
        pdfmetrics.registerFont(TTFont("CJK", font))
        font_name = "CJK"

    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleCJK", parent=styles["Title"], fontName=font_name)
    body = ParagraphStyle("BodyCJK", parent=styles["BodyText"], fontName=font_name, leading=16)
    heading = ParagraphStyle("HeadingCJK", parent=styles["Heading2"], fontName=font_name)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    story = [
        Paragraph("智采慧鉴 · 综合风险研判报告", title),
        Spacer(1, 6 * mm),
        Paragraph(f"综合风险评分：{report.get('score', 0)} / 100", heading),
        Paragraph(report.get("summary", "") or "", body),
        Spacer(1, 6 * mm),
        Paragraph("价格偏离分析", heading),
    ]

    rows = [["品名", "报价单价", "市场基准价", "偏离率", "风险分级"]]
    for p in report.get("price_rows", []) or []:
        rate = p.get("deviation_rate")
        rate_s = f"{rate * 100:.1f}%" if rate is not None else "-"
        market = p.get("market_avg")
        rows.append(
            [
                p.get("name", ""),
                str(p.get("bid_price", "-")),
                str(market) if market is not None else "无可比数据",
                rate_s,
                p.get("grade", ""),
            ]
        )
    story.append(
        Table(
            rows,
            style=TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ]
            ),
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("合规问题清单", heading))

    findings = report.get("findings", []) or []
    if not findings:
        story.append(Paragraph("未发现明显合规风险。", body))
    else:
        for f in findings:
            story.append(
                Paragraph(
                    f"[{f.get('severity', '')}] {f.get('dimension_name', '')} · {f.get('category', '')}："
                    f"{f.get('matched_text', '')}",
                    body,
                )
            )
            if f.get("suggestion"):
                story.append(Paragraph("建议：" + f["suggestion"], body))

    doc.build(story)
    return str(output_path)
