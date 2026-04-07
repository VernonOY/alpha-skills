---
name: alpha-monitor
description: >
  Factor monitoring. Check active factors for IC decay and health issues.
  因子监控。检查活跃因子的IC衰减和健康状态。
  Triggers: "health check", "monitor", "检查因子健康", "因子状态"
---

# alpha-monitor — Factor Health Monitoring / 因子健康监控

你是一个因子监控系统。检查因子库中所有活跃因子的当前健康状态。
You are a factor monitoring system. Check health status of all active factors in the library.

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

## 执行流程 / Execution Pipeline

### Step 1: 读取因子库 / Read Factor Library

```python
import sys, os
PROJECT_DIR = '<当前工作目录 current working directory>'
sys.path.insert(0, PROJECT_DIR)
from alpha_agent.factors.registry import FactorRegistry

reg = FactorRegistry(os.path.join(PROJECT_DIR, "alpha_agent.db"))
active_factors = reg.list_all(status='active')
```

如果因子库为空，提示用户先注册因子。
If library is empty, prompt user to register factors first.

### Step 2: 加载近期数据 / Load Recent Data

加载最近1年的数据用于计算滚动指标（同alpha-evaluate的数据加载流程）。
Load last 1 year of data for rolling metrics (same as alpha-evaluate data loading pipeline).

### Step 3: 对每个活跃因子计算健康指标 / Compute Health Metrics for Each Active Factor

对每个因子 / For each factor：
1. 重新计算因子值 Recompute factor values（使用注册时的expression/函数调用 using registered expression/function call）
2. 计算近60日滚动IC均值 Compute 60-day rolling IC mean
3. 计算近60日滚动ICIR Compute 60-day rolling ICIR
4. 与注册时的ICIR对比，计算衰减比例 Compare with registered ICIR, compute decay ratio
5. 计算近3个月IC>0的占比 Compute IC>0 ratio for last 3 months
6. 判定健康状态 Determine health status

### Step 4: 健康状态判定 / Health Status Determination

```
🟢 HEALTHY: Rolling ICIR 滚动ICIR ≥ Registered ICIR 注册ICIR × 50%
🟡 WARNING: Rolling ICIR 滚动ICIR < Registered ICIR 注册ICIR × 50% or 或 2 consecutive months IC negative 连续2月IC为负
🔴 ALERT:   Rolling ICIR 滚动ICIR < 0 or 或 4 consecutive months IC negative 连续4月IC为负 or 或 quintile monotonicity collapse 分组单调性崩溃
```

### Step 5: 对WARNING/ALERT因子生成诊断 / Generate Diagnosis for WARNING/ALERT Factors

分析可能的原因 Analyze possible causes：
- 市场环境变化 Market regime change（趋势→震荡 trending→range-bound，或反之 or vice versa）
- 因子拥挤 Factor crowding（与主流指数相关性升高 increased correlation with major indices）
- 数据问题 Data issues（缺失率升高 higher missing rate）
- 季节性效应 Seasonal effects

给出建议 Provide suggestions：
- 🟡 WARNING: "Reduce weight, continue monitoring / 降低权重，继续观察"
- 🔴 ALERT: "Suspend usage, consider retiring or finding replacement / 暂停使用，考虑退役或寻找替代"

### Step 6: 输出报告 / Output Report

```
🏥 Factor Health Report / 因子健康报告 (YYYY-MM-DD)

🟢 pv_diverge      Rolling ICIR 滚动ICIR=0.62 (Registered 注册 0.70)  Healthy 健康
🟢 turnover_20     Rolling ICIR 滚动ICIR=0.48 (Registered 注册 0.52)  Healthy 健康
🟡 volatility_20   Rolling ICIR 滚动ICIR=0.19 (Registered 注册 0.43)  ← Decay 衰减 56%
   Diagnosis 诊断: <cause analysis 原因分析>
   Suggestion 建议: Reduce weight, observe 1 month / 降低权重，观察1个月

Summary 总览: N🟢 N🟡 N🔴 / Total 共 N active factors 个活跃因子
```

### Step 7: 更新注册表状态 / Update Registry Status

```python
reg.update_status("factor_name", "warning")  # or 或 "alert"
```

## 注意事项 / Notes

1. 如果因子库只有少量因子，监控仍然运行（哪怕只有1个）/ Monitoring still runs even with just 1 factor
2. 滚动窗口60日，不够60日时用全部可用数据 / Rolling window 60 days, use all available data if less than 60 days
3. 诊断信息由AI推理生成，基于市场环境和因子特性 / Diagnosis is AI-generated based on market environment and factor characteristics
4. 建议更新状态但不自动退役，退役需要用户确认 / Suggest status update but no auto-retire, retirement needs user confirmation
