# -*- coding: utf-8 -*-
"""智采慧鉴 · 生产级 Web 前端（Streamlit）。"""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from zhicai.config.settings import QWEN_MODEL, QWEN_VL_MODEL
from zhicai.db.benchmark_store import BenchmarkStore
from zhicai.llm import build_llm
from zhicai.pipeline import RiskPipeline, SourcingPipeline
from zhicai.reporting import render_report_pdf

st.set_page_config(page_title="智采慧鉴", page_icon="🔎", layout="wide")


@st.cache_resource
def get_llm():
    return build_llm()


def run_sourcing(name: str, target: int):
    store = BenchmarkStore("output/benchmarks.sqlite")
    try:
        out = SourcingPipeline(get_llm(), store=store).run(name, target_count=target)
        return out
    finally:
        store.close()


st.title("智采慧鉴")
st.caption("采购供应链招投标信息异常识别与价格合理性智能研判系统")

with st.sidebar:
    st.header("运行配置")
    st.metric("文本模型", QWEN_MODEL)
    st.metric("视觉模型", QWEN_VL_MODEL)
    try:
        get_llm()
        st.success("Qwen API 已就绪")
    except Exception as exc:  # noqa: BLE001
        st.error(f"LLM 未就绪：{exc}")

tab1, tab2 = st.tabs(["自主寻源", "风险研判"])

with tab1:
    st.subheader("任务一 · 自主寻源")
    name = st.text_input("商品名称", value="台式计算机")
    target = st.slider("采集目标数量", 1, 20, 5)
    if st.button("开始寻源", type="primary"):
        with st.spinner("浏览器采集中…"):
            try:
                out = run_sourcing(name, target)
            except Exception as exc:  # noqa: BLE001
                st.error(f"寻源失败：{exc}")
            else:
                benchmark = out["state"].get("benchmark", {})
                st.json(benchmark.get("metrics", {}))
                st.info(benchmark.get("ai_assessment", ""))
                items = out["state"].get("sourced_items", {}).get("items", [])
                if items:
                    st.dataframe(items)

with tab2:
    st.subheader("任务二 · 六阶段风险研判")
    uploaded = st.file_uploader("上传招标文件 (PDF/TXT)", type=["pdf", "txt"])
    if uploaded is not None:
        suffix = "." + uploaded.name.rsplit(".", 1)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name

        if st.button("开始研判", type="primary"):
            with st.spinner("研判中…"):
                store = BenchmarkStore("output/benchmarks.sqlite")
                try:
                    out = RiskPipeline(get_llm(), store=store).run(tmp_path)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"研判失败：{exc}")
                else:
                    report = out["report"]
                    c1, c2, c3 = st.columns(3)
                    c1.metric("综合风险评分", f"{report['score']} / 100")
                    c2.metric("合规问题数", len(report.get("findings", [])))
                    c3.metric("价格分析项", len(report.get("price_rows", [])))
                    st.markdown(report["summary"])

                    st.markdown("#### 价格偏离分析")
                    st.dataframe(report.get("price_rows", []))

                    st.markdown("#### 合规问题清单")
                    st.dataframe(report.get("findings", []))

                    st.download_button(
                        "下载 Markdown 报告",
                        data=report["markdown"].encode("utf-8"),
                        file_name="report.md",
                        mime="text/markdown",
                    )
                    pdf_path = render_report_pdf(report, str(Path("output") / "report.pdf"))
                    with open(pdf_path, "rb") as fh:
                        st.download_button(
                            "下载 PDF 报告",
                            data=fh.read(),
                            file_name="report.pdf",
                            mime="application/pdf",
                        )
                finally:
                    store.close()
