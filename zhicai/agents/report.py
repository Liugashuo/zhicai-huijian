# -*- coding: utf-8 -*-
"""任务二 Stage 4.7：综合研判报告生成（ReportAgent）。"""

from __future__ import annotations

from typing import Any

from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult


class ReportAgent(BaseAgent):
    name = "ReportAgent"
    state_key = "report"

    def run(self, state: StateManager) -> TaskResult:
        extraction = state.get("extraction", {})
        metadata = extraction.get("metadata", {})
        items = extraction.get("items", [])
        price_analysis = state.get("price_analysis", []) or []
        compliance = state.get("compliance", {}) or {}
        findings = compliance.get("findings", []) or []

        price_score = self._price_score(price_analysis)
        compliance_score = int(compliance.get("score", 0))
        total = min(100, price_score + compliance_score)

        payload = {"score": total, "price_analysis": price_analysis, "findings": findings}
        summary = self.llm.summarize(payload) if self.llm else ""
        markdown = self._build_markdown(metadata, items, price_analysis, findings, total, summary)

        return TaskResult.ok(
            self.name,
            {
                "markdown": markdown,
                "score": total,
                "price_score": price_score,
                "compliance_score": compliance_score,
                "summary": summary,
                "metadata": metadata,
                "price_rows": price_analysis,
                "findings": findings,
            },
        )

    @staticmethod
    def _price_score(price_analysis: list[dict[str, Any]]) -> int:
        high = sum(1 for p in price_analysis if p.get("grade") == "high")
        medium = sum(1 for p in price_analysis if p.get("grade") == "medium")
        return min(50, high * 15 + medium * 8)

    def _build_markdown(self, metadata, items, price_analysis, findings, total, summary) -> str:
        lines = ["# 智采慧鉴 · 综合风险研判报告", ""]
        lines.append("## 一、项目概要")
        for k, v in metadata.items():
            lines.append(f"- **{k}**：{v or '未识别'}")
        lines.append(f"- **解析报价条目数**：{len(items)}")
        lines.append("")
        lines.append(f"## 二、综合风险评分：{total} / 100")
        lines.append(f"> {summary}")
        lines.append("")
        lines.append("## 三、价格偏离分析")
        lines.append("| 品名 | 报价单价 | 市场基准价 | 偏离率 | 风险分级 | 备注 |")
        lines.append("| --- | ---: | ---: | ---: | --- | --- |")
        for p in price_analysis:
            rate = p.get("deviation_rate")
            rate_str = f"{rate * 100:.1f}%" if rate is not None else "-"
            lines.append(
                f"| {p.get('name','')} | {p.get('bid_price','-')} | "
                f"{p.get('market_avg','-') if p.get('market_avg') is not None else '无可比数据'} | "
                f"{rate_str} | {p.get('grade','')} | {p.get('note','')} |"
            )
        lines.append("")
        lines.append("## 四、合规问题清单")
        if not findings:
            lines.append("未发现明显合规风险。")
        else:
            lines.append("| 维度 | 类别 | 严重度 | 命中原文 | 建议 |")
            lines.append("| --- | --- | --- | --- | --- |")
            for f in findings:
                text = f.get("matched_text", "").replace("|", "/")
                lines.append(
                    f"| {f.get('dimension_name','')} | {f.get('category','')} | {f.get('severity','')} | "
                    f"{text} | {f.get('suggestion','')} |"
                )
        lines.append("")
        lines.append("## 五、证据溯源附录")
        cited: set[str] = set()
        for f in findings:
            cid = f.get("chunk_id", "")
            if cid in cited:
                continue
            cited.add(cid)
            lines.append(f"- [{cid}] `{f.get('context','').replace(chr(10), ' ')[:120]}`")
        lines.append("")
        lines.append("---")
        lines.append("*本报告由智采慧鉴多智能体流水线自动生成，所有结论均带 chunk_id 可反查原文。*")
        return "\n".join(lines)
