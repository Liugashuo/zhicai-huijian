# -*- coding: utf-8 -*-
"""Streamlit Web 统一交互层：Tab1 自主寻源 / Tab2 风险研判。"""

from __future__ import annotations

import tempfile

import streamlit as st

from zhicai.core.llm import MockLLM
from zhicai.db.benchmark_store import BenchmarkStore
from zhicai.pipeline import RiskPipeline, SourcingPipeline

st.set_page_config(page_title="智采慧鉴", layout="wide")
llm = MockLLM()

tab1, tab2 = st.tabs(["自主寻源", "风险研判"])

with tab1:
    st.header("任务一 · 自主寻源")
    name = st.text_input("商品名称", value="台式计算机")
    target = st.slider("采集目标数量", 1, 20, 5)
    if st.button("开始寻源"):
        store = BenchmarkStore("output/benchmarks.sqlite")
        out = SourcingPipeline(llm, store=store).run(name, target_count=target, dataset=[])
        metrics = out["state"].get("benchmark", {}).get("metrics", {})
        st.json(metrics)
        st.write(out["state"].get("benchmark", {}).get("ai_assessment", ""))
        store.close()

with tab2:
    st.header("任务二 · 六阶段风险研判")
    uploaded = st.file_uploader("上传招标文件 (PDF/TXT)", type=["pdf", "txt"])
    if uploaded is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded.name.rsplit(".", 1)[-1]) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name
        store = BenchmarkStore("output/benchmarks.sqlite")
        out = RiskPipeline(llm, store=store).run(tmp_path)
        report = out["report"]
        st.metric("综合风险评分", f"{report['score']} / 100")
        st.markdown(report["markdown"])
        store.close()
