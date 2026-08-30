# 智采慧鉴

采购供应链招投标信息异常识别与价格合理性智能研判系统（赛题十四 · 行业应用赛道）。

本仓库依据《智采慧鉴_技术方案与算法说明》落地，采用「大模型自主决策 + 全链路证据可溯源」的
核心范式。系统以 **LangChain** 统一封装并调用 Qwen3 系列模型，Python 负责流程编排与确定性算法，
二者通过结构化 `TaskResult` 单向数据流耦合。

## 技术栈

| 类别 | 技术/工具 | 用途 |
| --- | --- | --- |
| 前端界面 | Streamlit | Web 统一交互层 |
| 视觉大模型 | Qwen3-VL-32B / Qwen3-VL-8B | 浏览器 Agent 决策中枢、详情页识别 |
| 文本大模型 | Qwen3-8B | 寻源分析、数据评估、合规审查、综合评分 |
| LLM 框架 | LangChain | 大模型统一调用与封装（ChatOpenAI 对接 OpenAI 兼容接口） |
| 浏览器自动化 | browser-use (CDP) | 拟人化浏览器操作 |
| PDF 解析 | PyMuPDF | 招标文件文本提取 |
| 报告生成 | ReportLab | 风险研判报告输出 |
| 数据库 | SQLite | 比价基准库存储与查询 |
| 开发语言 | Python | 全栈开发 |

## 系统结构

```
Streamlit Web (app.py)
   ├── Tab1 自主寻源引擎
   └── Tab2 风险研判引擎
              │
              ▼
SQLite 比价基准库 (products / price_benchmarks)
```

编排遵循 `Executor -> TaskResult -> Pipeline -> StateManager` 单向数据流，所有状态变更由
`Pipeline` 统一收口；每个 Agent 职责单一、不直接修改流程状态，支持独立单元测试。

### 任务一 · 自主寻源引擎

`ProductAnalysisAgent -> BrowserAgent -> DataCleaningAgent -> BenchmarkAgent`

- Qwen3-VL 视觉大模型驱动的自主浏览器 Agent：`截图感知 -> 上下文推理 -> 动作执行 -> 反馈更新` 闭环；
- 7 类原子动作：`scroll / click_product / extract_products / extract_detail / go_back / wait / done`；
- VLM/DOM 双通道融合提取（DOM 优先、VLM 补充，价格交叉验证）；
- IQR 去极值 + 三级强去重 + 来源标记 + 基准价测算 + AI 定性评估。

### 任务二 · 六阶段研判流水线

`PDFParser -> EvidenceStore -> MarkdownParser -> PriceAgent -> ComplianceAgent -> ReportAgent`

| 阶段 | 说明 |
| --- | --- |
| PDFParser | PyMuPDF 逐页提取 + 中文标题分块 |
| EvidenceStore | 分块唯一 ID（`bid_p{page}_c{idx}`）与证据溯源索引 |
| MarkdownParser | 元数据/产品条目/章节结构三轮 LLM 结构化提取 + 确定性兜底 |
| PriceAgent | 三级匹配 + 价格偏离度量化 + 不平衡报价识别 |
| ComplianceAgent | 6 维度 81 项合规规则引擎 + LLM 语义审查 |
| ReportAgent | 综合评分与 Markdown/ReportLab PDF 报告 |

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

## 接入真实 Qwen3（LangChain 统一封装）

系统通过 LangChain 的 `ChatOpenAI` 调用 Qwen3 的 OpenAI 兼容接口（Ollama / vLLM），用环境变量配置：

```bash
QWEN_BASE_URL=http://localhost:11434/v1
QWEN_API_KEY=EMPTY
QWEN_MODEL=qwen3:8b
QWEN_VL_MODEL=qwen3-vl:8b
```

```python
from zhicai.llm import build_llm

llm = build_llm()  # 读取环境变量，构建 LangChainLLM
```

未配置 `QWEN_BASE_URL` 时，`build_llm()` 自动回退到 `MockLLM`，保证离线可运行、测试可复现。
所有语义判断都经由 `zhicai.llm.LLM` 抽象，可在任意 LangChain `BaseChatModel` 之间平滑切换。

## 真实浏览器自动化（browser-use）

离线演示使用 `MockBrowserDriver`。接入真实浏览器时安装 `browser-use`，并以 CDP 连接已启动的
浏览器实例，将 `BrowserUseDriver` 注入 `SourcingPipeline`。拟人化反检测策略（贝塞尔曲线鼠标轨迹、
分段随机滚动、随机延迟、多标签页管理）在 `zhicai/agents/browser_driver.py` 中实现。

## 测试

```bash
python -m unittest discover -s tests -v
```
