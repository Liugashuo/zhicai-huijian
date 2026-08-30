# 智采慧鉴

采购供应链招投标信息异常识别与价格合理性智能研判系统（多智能体实现）。

本仓库依据《智采慧鉴_技术方案与算法说明》落地一套可离线运行、可测试的多智能体框架，遵循
「AI 负责感知与判断、Python 负责流程与确定性算法」的分层解耦原则。

## 系统结构

```
Executor -> TaskResult -> Pipeline -> StateManager
```

所有 Agent 通过结构化 `TaskResult` 单向传递数据，状态变更由 `Pipeline` 统一收口。
每个 Agent 职责单一、不直接修改流程状态，支持独立单元测试。

### 任务一 · 自主寻源 Agent

| Agent | 职责 |
| --- | --- |
| ProductAnalysisAgent | 品类识别、参数提取、寻源策略生成 |
| BrowserAgent | VLM 自主浏览器 Agent（感知-决策-执行-反馈闭环，7 类原子动作） |
| DataCleaningAgent | IQR 去极值 + 三级去重 + 来源标记 |
| BenchmarkAgent | 基准价测算 + AI 定性评估 |

### 任务二 · 六阶段研判流水线

`PDFParser -> EvidenceStore -> Extraction -> Price -> Compliance -> Report`

| Agent | 职责 |
| --- | --- |
| PDFParserAgent | PDF 解析与中文标题分块 |
| EvidenceStoreAgent | 分块唯一 ID 与证据溯源索引 |
| ExtractionAgent | 元数据/产品条目/章节结构三轮结构化提取 + 确定性兜底 |
| PriceAgent | 三级匹配 + 价格偏离度量化 + 不平衡报价识别 |
| ComplianceAgent | 6 维度合规规则引擎 + 可选 LLM 语义审查 |
| ReportAgent | 综合评分与 Markdown/PDF 报告生成 |

## 核心算法

- Jaccard + Bigram 关键词相似度（`algorithms/similarity.py`）
- IQR 四分位距去极值与基准价测算（`algorithms/iqr.py`）
- 截断 JSON 自修复（`algorithms/json_repair.py`）
- 价格偏离度与分级（`algorithms/deviation.py`）
- 「数量+单位+单价+小计」确定性兜底解析与反向校验（`algorithms/extraction_rules.py`）

## 运行

```bash
pip install -r requirements.txt
python run_demo.py
```

运行后生成：

- `output/report.md`：研判报告（Markdown）
- `output/report.pdf`：研判报告（ReportLab PDF）
- `output/benchmarks.sqlite`：比价基准库

Web 界面：

```bash
streamlit run app.py
```

## 测试

```bash
python -m unittest discover -s tests -v
```

## LLM 可替换

默认使用 `MockLLM` 保证离线运行与可复现测试。接入真实 Qwen3（Ollama / vLLM）时：

```python
from zhicai.core.llm import OpenAICompatibleLLM
llm = OpenAICompatibleLLM(base_url="http://localhost:11434/v1", model="qwen3:8b")
```

所有语义判断都经由 `LLMProvider` 抽象，Python 确定性算法负责流程与反爬/兜底，规避纯 LLM
方案的不确定性。
