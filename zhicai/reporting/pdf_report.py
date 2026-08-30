# -*- coding: utf-8 -*-
"""ReportLab 综合研判报告 PDF 输出。"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _find_cjk_font() -> str | None:
    for name in ("msyh.ttc", "msyh.ttf", "simhei.ttf", "simsun.ttc", "simsunb.ttf"):
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

    font_path = _find_cjk_font()
    font_name = "Helvetica"
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("CJK", font_path))
            font_name = "CJK"
        except Exception:  # noqa: BLE001
            font_name = "Helvetica"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCJK", parent=styles["Title"], fontName=font_name)
    body_style = ParagraphStyle("BodyCJK", parent=styles["BodyText"], fontName=font_name, leading=16)
    heading_style = ParagraphStyle("HeadingCJK", parent=styles["Heading2"], fontName=font_name)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    story = [
        Paragraph("智采慧鉴 · 综合风险研判报告", title_style),
        Spacer(1, 6 * mm),
        Paragraph(f"综合风险评分：{report.get('score', 0)} / 100", heading_style),
        Spacer(1, 3 * mm),
        Paragraph(report.get("summary", ""), body_style),
        Spacer(1, 5 * mm),
    ]

    price_rows = report.get("price_rows", []) or []
    if price_rows:
        story.append(Paragraph("价格偏离分析", heading_style))
        data = [["品名", "报价单价", "市场基准价", "偏离率", "风险分级"]]
        for p in price_rows:
            rate = p.get("deviation_rate")
            rate_str = f"{rate * 100:.1f}%" if rate is not None else "-"
            data.append([
                p.get("name", ""),
                str(p.get("bid_price", "-")),
                str(p.get("market_avg", "-")) if p.get("market_avg") is not None else "无可比数据",
                rate_str,
                p.get("grade", ""),
            ])
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 5 * mm))

    findings = report.get("findings", []) or []
    story.append(Paragraph("合规问题清单", heading_style))
    if not findings:
        story.append(Paragraph("未发现明显合规风险。", body_style))
    else:
        for f in findings:
            story.append(Paragraph(
                f"[{f.get('dimension_name', '')}] {f.get('matched_text', '')} —— {f.get('suggestion', '')}",
                body_style,
            ))

    doc.build(story)
    return str(output)
