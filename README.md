# 智采慧鉴

采购供应链招投标信息异常识别与价格合理性智能研判系统（生产级实现）。

系统以 **LangChain** 统一封装并调用 **Qwen**（阿里云 DashScope OpenAI 兼容接口），Python
负责流程编排与确定性算法；浏览器自动化使用 **Playwright 驱动本机 Edge（CDP）**，前端使用
**Streamlit**，数据落 **SQLite**，报告输出 **ReportLab PDF**。

## 系统结构

```
Streamlit Web (app.py)
   ├── Tab1 自主寻源（真实浏览器 + VLM 决策闭环）
   └── Tab2 风险研判（六阶段流水线）
              │
              ▼
SQLite 比价基准库 (products / price_benchmarks)
```

编排遵循 `Executor -> TaskResult -> Pipeline -> StateManager` 单向数据流，所有状态变更由
`Pipeline` 统一收口。

### 任务一 · 自主寻源

`ProductAnalysisAgent -> BrowserAgent -> DataCleaningAgent -> BenchmarkAgent`

- Qwen-VL 视觉大模型驱动的浏览器 Agent：`截图感知 -> 上下文推理 -> 动作执行 -> 反馈更新`；
- 7 类原子动作：`scroll / click_product / extract_products / extract_detail / go_back / wait / done`；
- VLM/DOM 双通道融合（DOM 优先、VLM 补充、价格交叉验证）；
- IQR 去极值 + 三级去重 + 基准价测算 + AI 定性评估。

### 任务二 · 六阶段风险研判

`PDFParser -> EvidenceStore -> MarkdownParser -> PriceAgent -> ComplianceAgent -> ReportAgent`

- PDFParser：PyMuPDF 逐页提取 + 中文标题分块；
- EvidenceStore：分块唯一 ID（`bid_p{page}_c{idx}`）与证据溯源索引；
- MarkdownParser：元数据 / 产品条目 / 章节结构三轮 LLM 结构化提取 + 确定性兜底；
- PriceAgent：三级匹配（LIKE -> Jaccard -> unknown）+ 价格偏离度量化 + 不平衡报价识别；
- ComplianceAgent：6 维度规则引擎（确定性）+ 可选 LLM 语义审查（可并行）；
- ReportAgent：综合评分与 Markdown / ReportLab PDF 报告。

## 快速开始

```bash
pip install -r requirements.txt
```

在项目根目录创建 `.env`（参考 `.env.example`）：

```bash
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
QWEN_VL_MODEL=qwen3-vl-plus
QWEN_TEMPERATURE=0
```

启动 Web 前端：

```bash
streamlit run app.py
```

命令行演示（真实 Qwen 风险研判；加 `--sourcing 商品名` 可跑真实浏览器寻源）：

```bash
python run_demo.py
```

## 环境变量

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `QWEN_API_KEY` | Qwen（DashScope）API Key | 空 |
| `QWEN_BASE_URL` | OpenAI 兼容接口地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `QWEN_MODEL` | 文本模型 | `qwen-plus` |
| `QWEN_VL_MODEL` | 视觉模型 | `qwen3-vl-plus` |
| `QWEN_TEMPERATURE` | 采样温度 | `0` |
| `BROWSER_HEADLESS` | 浏览器是否无头运行 | `false` |
| `COMPLIANCE_LLM_REVIEW` | 是否启用合规 LLM 语义审查（开启时并行） | `false` |

## 关键算法

- Jaccard + Bigram 关键词相似度（`algorithms/similarity.py`）
- IQR 四分位距去极值与基准价测算（`algorithms/iqr.py`）
- 截断 JSON 自修复（`algorithms/json_repair.py`）
- 价格偏离度与分级（`algorithms/deviation.py`）
- 「数量+单位+单价+小计」确定性兜底解析与反向校验（`algorithms/extraction_rules.py`）

## 测试

```bash
python -m unittest discover -s tests -v
```

> 说明：`.env` 含 API Key，已加入 `.gitignore`，不会被提交。
