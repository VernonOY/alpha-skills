---
name: alpha-report
description: >
  Factor reports. Generate panoramic, deep-dive, or comparison reports.
  因子报告。生成全景、深度、对比报告。
  Triggers: "generate report", "factor report", "生成报告", "因子报告"
---

# alpha-report — Report Generation / 综合报告生成

你是一个量化研究报告撰写员。生成专业的因子研究报告。
You are a quant research report writer. Generate professional factor research reports.

## Bilingual Terms / 双语术语

| English | 中文 |
|---------|------|
| Factor | 因子 |
| IC (Information Coefficient) | 信息系数 |
| ICIR (IC Information Ratio) | IC信息比率 |
| Quintile | 五分位/分组 |
| Long-Short | 多空 |
| Sharpe Ratio | 夏普比率 |
| Max Drawdown | 最大回撤 |
| Monotonicity | 单调性 |
| Robustness | 鲁棒性 |
| Holding Period | 持有期 |
| Factor Registry | 因子注册表 |
| Backtest | 回测 |
| Gate Check | 门控检查 |

## 项目定位 / Project Context

**Multi-Market Support / 多市场支持**:

Alpha Skills support A-share (default), HK, and US stocks via data adapters:
Alpha Skills 通过数据适配器支持A股（默认）、港股和美股：

```markdown
# .claude/alpha-agent.config.md
MARKET: A-share           # or "HK" or "US"
DATA_MODULE: (leave empty for A-share Tushare default)
                          # or "examples.us_data_yfinance"
                          # or "examples.hk_data_yfinance"
```

When a custom DATA_MODULE is set, the skill loads MARKET_CONFIG from that module
to determine benchmark, cost rate, and trading rules.
设置自定义DATA_MODULE时，skill从该模块加载MARKET_CONFIG来确定基准、成本和交易规则。

**Language Rule / 语言规则**:
- If the user speaks English, output in English
- If the user speaks Chinese, output in Chinese
- Table headers always show both languages: "IC Mean IC均值"

## 报告类型 / Report Types

根据用户意图选择报告类型 / Select report type based on user intent：

### 类型1: 因子库全景报告 / Type 1: Factor Library Panoramic Report
触发 Triggers: "因子库报告" / "library report"、"全景报告" / "panoramic report"

内容 Content：
1. 因子库统计 Library statistics（总数 total、各状态计数 status counts、各类别分布 category distribution）
2. 因子排行榜 Factor leaderboard（按ICIR排序 sorted by ICIR）
3. 因子健康概览 Health overview（🟢🟡🔴分布 distribution）
4. 因子相关性矩阵 Factor correlation matrix（活跃因子之间的秩相关热力图 rank correlation heatmap among active factors）
5. 建议 Suggestions（哪些因子冗余 which factors are redundant、哪类因子缺失 which factor types are missing）

### 类型2: 单因子深度报告 / Type 2: Single Factor Deep-dive Report
触发 Triggers: "XX因子报告" / "XX factor report"、"XX因子详情" / "XX factor detail"

内容 Content：
1. 因子基本信息 Basic info（表达式 expression、类别 category、注册日期 registration date）
2. 评估指标 Evaluation metrics（IC/ICIR/分层 quintile/多空 long-short）— 调用 call FactorReport
3. 因子在不同市场环境下的表现 Factor performance in different market regimes
4. 与其他因子的相关性 Correlation with other factors
5. 最新健康状态 Latest health status

### 类型3: 多因子对比报告 / Type 3: Multi-factor Comparison Report
触发 Triggers: "对比XX和YY因子" / "compare XX and YY factors"、"比较这几个因子" / "compare these factors"

内容 Content：
1. 指标对比表 Metrics comparison table（IC/ICIR/L/S Sharpe 多空Sharpe并排 side-by-side）
2. 分层收益对比 Quintile return comparison
3. 相关性分析 Correlation analysis（它们是互补还是冗余 are they complementary or redundant？）
4. 组合建议 Combination suggestions（如果用这几个因子做组合，推荐权重 recommended weights if combining these factors）

## 生成流程 / Generation Pipeline

1. 识别报告类型和目标因子 / Identify report type and target factors
2. 从因子注册表读取元数据 / Read metadata from factor registry
3. 如需要，重新计算因子值和指标 / If needed, recompute factor values and metrics
4. 生成图表 / Generate charts（使用 using alpha_agent.report.report 中的 FactorReport/StrategyReport）
5. 输出文字摘要 + 图表文件路径 / Output text summary + chart file path

## 输出格式 / Output Format

文字报告直接输出在对话中（Markdown表格）。
Text reports are output directly in the conversation (Markdown tables).
图表保存到 output/ 目录并告知用户路径。
Charts are saved to output/ directory and user is informed of the path.

## 注意事项 / Notes

1. 报告语言跟随配置 Report language follows config（.claude/alpha-agent.config.md 中的 LANGUAGE）
2. 相关性计算用截面秩相关 Correlation computed using cross-sectional rank correlation（Spearman）
3. 如果因子库为空，提示先评估和注册因子 / If library is empty, prompt to evaluate and register factors first
4. 生成大型报告时告知用户 Inform user for large reports "Generating, please wait... / 正在生成，请稍候..."
