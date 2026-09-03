# -*- coding: utf-8 -*-
"""智采慧鉴 · 生产级 Web 前端（Streamlit）。"""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path

import pandas as pd
import streamlit as st

from zhicai.config.settings import QWEN_MODEL, QWEN_VL_MODEL
from zhicai.db.benchmark_store import BenchmarkStore
from zhicai.llm import build_llm
from zhicai.pipeline import RiskPipeline, SourcingPipeline
from zhicai.reporting import render_report_pdf

DB_PATH = "output/benchmarks.sqlite"

st.set_page_config(page_title="智采慧鉴", page_icon="🔎", layout="wide")


@st.cache_resource
def get_llm():
    return build_llm()


with st.sidebar:
    st.header("运行配置")
    st.metric("文本模型", QWEN_MODEL)
    st.metric("视觉模型", QWEN_VL_MODEL)
    try:
        get_llm()
        st.success("Qwen API 已就绪")
    except Exception as exc:  # noqa: BLE001
        st.error(f"LLM 未就绪：{exc}")
    st.divider()
    if st.button("退出应用"):
        st.stop()
    st.caption("退出只停止当前页面脚本；完全关闭服务请关闭启动它的终端窗口，或按 Ctrl+C。")


if "stop_event" not in st.session_state:
    st.session_state.stop_event = None
if "sourcing_running" not in st.session_state:
    st.session_state.sourcing_running = False
if "sourcing_result" not in st.session_state:
    st.session_state.sourcing_result = None
if "sourcing_error" not in st.session_state:
    st.session_state.sourcing_error = None


def _run_sourcing(name: str, target: int, stop_event: threading.Event) -> None:
    try:
        store = BenchmarkStore(DB_PATH)
        try:
            out = SourcingPipeline(get_llm(), store=store).run(
                name, target_count=target, stop_event=stop_event
            )
        finally:
            store.close()
        st.session_state.sourcing_result = out
    except Exception as exc:  # noqa: BLE001
        st.session_state.sourcing_error = str(exc)
    finally:
        st.session_state.sourcing_running = False


tab1, tab2, tab3 = st.tabs(["自主寻源", "风险研判", "数据看板"])

with tab1:
    st.subheader("任务一 · 自主寻源")
    name = st.text_input("商品名称", value="台式计算机")
    target = st.slider("采集目标数量", 1, 20, 5)
    c1, c2 = st.columns(2)
    if c1.button("开始寻源", type="primary", disabled=st.session_state.sourcing_running):
        st.session_state.sourcing_running = True
        st.session_state.sourcing_result = None
        st.session_state.sourcing_error = None
        st.session_state.stop_event = threading.Event()
        threading.Thread(
            target=_run_sourcing,
            args=(name, target, st.session_state.stop_event),
            daemon=True,
        ).start()
    if c2.button("停止任务 / 退出浏览器", disabled=not st.session_state.sourcing_running):
        if st.session_state.stop_event is not None:
            st.session_state.stop_event.set()

    @st.fragment(run_every="1s")
    def _show_sourcing_status():
        if st.session_state.sourcing_error:
            st.error(st.session_state.sourcing_error)
        elif st.session_state.sourcing_running:
            st.info("采集中，可点击「停止任务 / 退出浏览器」中断…")
        elif st.session_state.sourcing_result is not None:
            out = st.session_state.sourcing_result
            benchmark = out["state"].get("benchmark", {})
            st.json(benchmark.get("metrics", {}))
            st.info(benchmark.get("ai_assessment", ""))
            items = out["state"].get("sourced_items", {}).get("items", [])
            if items:
                st.dataframe(items)

    _show_sourcing_status()


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
                store = BenchmarkStore(DB_PATH)
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


with tab3:
    st.subheader("比价基准库 · 数据看板")
    store = BenchmarkStore(DB_PATH)
    try:
        products = store.all_products()
        benchmarks = store.all_benchmarks()
        if not benchmarks:
            st.info("暂无行情数据。可先运行「自主寻源」，或执行 scripts/seed_benchmarks.py 写入样例数据。")
        else:
            df = pd.DataFrame(benchmarks)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("商品数", len(products))
            c2.metric("行情条数", len(df))
            c3.metric("平均价格", f"{df['price'].mean():.2f}")
            c4.metric("价格中位数", f"{df['price'].median():.2f}")

            st.markdown("#### 各商品平均价格")
            st.bar_chart(df.groupby("name")["price"].mean().sort_values())

            st.markdown("#### 价格分布")
            hist = pd.cut(df["price"], bins=10).value_counts().sort_index()
            st.bar_chart(
                pd.DataFrame({"数量": hist.values}, index=[str(i) for i in hist.index])
            )

            st.markdown("#### 平台行情分布")
            st.bar_chart(df["platform"].value_counts())

            st.markdown("#### 行情明细")
            st.dataframe(df, use_container_width=True)
    finally:
        store.close()
