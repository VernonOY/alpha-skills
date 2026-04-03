---
name: alpha-evaluate
description: >
  因子评估skill。评估一个因子的有效性（IC/ICIR/分层/多空/鲁棒性）。
  触发词："评估因子"、"测试因子"、"这个因子怎么样"、"alpha-evaluate"。
  当用户提供因子名称或Python表达式时，自动运行4级评估管线并输出报告。
---

# alpha-evaluate — 因子评估

你是一个专业量化分析师。当用户要求评估一个因子时，按照以下流程执行。

## 项目定位

项目目录在用户的当前工作目录，其中：
- `data_cache/` — 本地缓存的行情数据（Parquet格式）
- `output/` — 报告输出目录
- `.claude/alpha-agent.config.md` — 用户自定义评估参数

**数据来源**：技能支持任何数据源。优先检查用户配置中的 DATA_SOURCE 字段：
- `tushare` (默认) — 使用Tushare Pro API拉取A股数据
- `csv` — 从用户指定目录读取CSV/Parquet文件
- `custom` — 用户提供自定义数据加载函数

如果用户已在项目中定义了自己的数据加载模块（如 `my_data.py`），优先使用用户的模块。
检查方式：查看配置文件中是否有 `DATA_MODULE` 字段指定了自定义模块路径。

## 输入识别

用户可能以以下方式提供因子：

1. **内置因子名称**: "评估reversal_5因子"、"测试pv_diverge"
2. **Python表达式**: "评估 -close.pct_change(5) 这个因子"
3. **自然语言描述**: "评估一个5日反转因子" → 你理解后映射到内置因子或生成代码
4. **FEL表达式**: "评估 ts_corr(close, volume, 20) * -1"（如项目已实现FEL解析器）

## 执行流程

### Step 1: 读取用户配置

```python
# 读取 .claude/alpha-agent.config.md 中的评估参数
# 如果文件不存在，使用默认值
```

默认值：
- 持有期: [5, 10, 20]
- IC快筛阈值: 0.02
- Strong ICIR: 0.5
- Moderate ICIR: 0.3

### Step 2: 加载数据

首先检查用户是否有自定义数据加载方式（配置中 DATA_MODULE 或 DATA_SOURCE 字段）。

**方式A: 用户自定义数据模块**（优先）

如果配置了 `DATA_MODULE: my_data`，则：
```python
import importlib
data_mod = importlib.import_module("my_data")
# 用户模块需提供以下函数（返回DataFrame）：
# data_mod.load_prices(start, end) → DataFrame with columns: ts_code, trade_date, open, high, low, close, vol, amount
# data_mod.load_adj_factor(start, end) → DataFrame with columns: ts_code, trade_date, adj_factor
# data_mod.load_daily_basic(start, end) → DataFrame with columns: ts_code, trade_date, pe_ttm, pb, turnover_rate_f, ...
# data_mod.load_financial(start, end) → DataFrame with columns: ts_code, ann_date, end_date, roe, roa, ...
```

**方式B: CSV/Parquet本地文件**

如果配置了 `DATA_SOURCE: csv` 和 `DATA_DIR: /path/to/data`，则从指定目录读取文件：
```python
DATA_DIR = config.get("DATA_DIR", "data")
daily_prices = pd.read_parquet(os.path.join(DATA_DIR, "daily_prices.parquet"))
# 或 pd.read_csv(os.path.join(DATA_DIR, "daily_prices.csv"))
```

**方式C: Tushare缓存**（默认）

```python
import sys, os, glob, warnings
warnings.filterwarnings("ignore")
PROJECT_DIR = "<用户当前工作目录的绝对路径>"
sys.path.insert(0, PROJECT_DIR)

import pandas as pd
import numpy as np
CACHE_DIR = os.path.join(PROJECT_DIR, "data_cache")

def load_and_merge(prefix):
    files = sorted(glob.glob(os.path.join(CACHE_DIR, f"{prefix}_*.parquet")))
    frames = [pd.read_parquet(f) for f in files if os.path.getsize(f) > 100]
    return pd.concat(frames, ignore_index=True).drop_duplicates() if frames else pd.DataFrame()

daily_prices = load_and_merge("get_daily_prices")
adj_factor = load_and_merge("get_adj_factor")
daily_basic = load_and_merge("get_daily_basic")
fina = load_and_merge("get_financial_data")
stock_pool = load_and_merge("get_stock_pool")
index_data = load_and_merge("get_index_daily")
```

**数据格式约定**（无论哪种方式，最终数据需符合）：
- `daily_prices`: 必须含 ts_code, trade_date, open, high, low, close, vol, amount
- `adj_factor`: 必须含 ts_code, trade_date, adj_factor
- `trade_date` 格式: YYYYMMDD 字符串或可解析日期

### Step 3: 数据预处理（前复权+过滤）

```python
# 过滤股票池
valid_codes = set(stock_pool["ts_code"].tolist()) if not stock_pool.empty else set(daily_prices["ts_code"].unique())
dp = daily_prices[daily_prices["ts_code"].isin(valid_codes)].copy()
dp["trade_date"] = pd.to_datetime(dp["trade_date"], format="%Y%m%d")

# Pivot成宽表
close_raw = dp.pivot_table(index="trade_date", columns="ts_code", values="close").sort_index()
volume = dp.pivot_table(index="trade_date", columns="ts_code", values="vol").fillna(0)
high_raw = dp.pivot_table(index="trade_date", columns="ts_code", values="high")
low_raw = dp.pivot_table(index="trade_date", columns="ts_code", values="low")

# 前复权
if not adj_factor.empty:
    af = adj_factor[adj_factor["ts_code"].isin(valid_codes)].copy()
    af["trade_date"] = pd.to_datetime(af["trade_date"], format="%Y%m%d")
    adj_pivot = af.pivot_table(index="trade_date", columns="ts_code", values="adj_factor").sort_index()
    common_dates = close_raw.index.intersection(adj_pivot.index)
    common_stocks = close_raw.columns.intersection(adj_pivot.columns)
    close_raw = close_raw.loc[common_dates, common_stocks]
    adj_pivot = adj_pivot.loc[common_dates, common_stocks]
    high_raw = high_raw.reindex(index=common_dates, columns=common_stocks)
    low_raw = low_raw.reindex(index=common_dates, columns=common_stocks)
    volume = volume.reindex(index=common_dates, columns=common_stocks)
    adj_ratio = adj_pivot / adj_pivot.iloc[-1]
    close = (close_raw * adj_ratio).ffill(limit=5)
    high = high_raw * adj_ratio
    low = low_raw * adj_ratio
else:
    close = close_raw.ffill(limit=5)
    high = high_raw
    low = low_raw

# 过滤稀疏股票
min_count = int(len(close) * 0.4)
valid_stocks = close.columns[close.notna().sum() >= min_count]
close = close[valid_stocks]
```

### Step 4: 计算因子

根据用户输入的因子类型调用对应函数：

```python
from alpha_agent.factors.builtin import <对应因子函数>
from alpha_agent.factors.preprocessing import standardize

factor_values = <因子函数>(close, ...)  # 根据因子类型调用
factor_values = standardize(factor_values)  # 截面标准化
```

**内置因子映射表**（用户说因子名时参考）：
- momentum_20 → `momentum(close, 20)`
- reversal_5 → `reversal(close, 5)`
- volatility_20 → `volatility(close, 20)`
- pv_diverge → `price_volume_divergence(close, volume, 20)`
- turnover_20 → `turnover_rate(daily_basic, 20)`
- abnormal_turnover → `abnormal_turnover(daily_basic)`
- rsi_14 → `rsi(close, 14)`
- macd → `macd_divergence(close)`
- bollinger → `bollinger_position(close)`
- atr_ratio → `atr_ratio(high, low, close)`
- pe_ttm → `pe_ttm(daily_basic)`
- pb → `pb(daily_basic)`
- ps_ttm → `ps_ttm(daily_basic)`
- dividend_yield → `dividend_yield(daily_basic)`
- roe → `roe(fina)`
- roa → `roa(fina)`
- gross_margin → `gross_margin(fina)`
- net_profit_growth / np_growth → `net_profit_growth(fina)`
- revenue_growth / rev_growth → `revenue_growth(fina)`
- quality → `quality_score(fina)`
- value → `value_score(daily_basic)`
- peg → `peg(daily_basic, fina)`

### Step 5: 运行评估

```python
from alpha_agent.evaluation.metrics import compute_forward_returns
from alpha_agent.evaluation.evaluator import FactorTester

results = {}
for hp in holding_periods:  # [5, 10, 20]
    fwd_ret = compute_forward_returns(close, periods=hp)
    # 对齐
    cd = factor_values.index.intersection(fwd_ret.index)
    cs = factor_values.columns.intersection(fwd_ret.columns)
    tester = FactorTester(factor_values.loc[cd, cs], fwd_ret.loc[cd, cs], n_groups=5)
    s = tester.summary()
    results[hp] = s
```

### Step 6: 生成报告

```python
from alpha_agent.report.report import FactorReport

# 用ICIR最高的持有期生成详细报告
best_hp = max(results, key=lambda hp: abs(results[hp]["ic_stats"]["icir"]))
best_tester = ...  # 重新创建对应tester
report = FactorReport(best_tester, factor_name=f"{factor_name}_hp{best_hp}")
report.generate_full_report(save_path=os.path.join(OUTPUT_DIR, f"eval_{factor_name}.png"))
```

### Step 7: 输出结果

向用户展示如下格式的结果（使用表格）：

```
📊 因子评估报告: <因子名>

表达式: <因子表达式或函数调用>

┌────────────┬────────┬────────┬────────┐
│ 持有期     │  5日   │  10日  │  20日  │
├────────────┼────────┼────────┼────────┤
│ IC均值     │ x.xxx  │ x.xxx  │ x.xxx  │
│ ICIR       │ x.xxx  │ x.xxx  │ x.xxx  │
│ IC>0占比   │ xx.x%  │ xx.x%  │ xx.x%  │
│ 多空Sharpe │ x.xx   │ x.xx   │ x.xx   │
│ 多空MaxDD  │ -xx.x% │ -xx.x% │ -xx.x% │
│ 分组单调   │  ✓/✗   │  ✓/✗   │  ✓/✗   │
└────────────┴────────┴────────┴────────┘

评级: ⭐ Strong / ● Moderate / · Weak
最佳持有期: xx日
分组单调性: Spearman=x.xx, p=x.xx

报告图表已保存: output/eval_<name>.png
```

评级标准（从配置读取）：
- **Strong**: |ICIR| ≥ 0.5 且 分组单调 且 |多空Sharpe| > 1
- **Moderate**: |ICIR| ≥ 0.3 或 |多空Sharpe| > 0.5
- **Weak**: 以上均不满足

### Step 8: 后续建议

评估完成后询问用户：
- "是否加入因子库？"（→ 触发 alpha-library add）
- "是否需要鲁棒性检验？"（→ 运行Level 3）
- "是否回测？"（→ 触发 alpha-backtest）

## 注意事项

1. 所有Python代码用 `/opt/anaconda3/bin/python` 执行
2. 数据量大时预处理可能需要30秒+，告知用户"正在加载数据..."
3. 如果用户没有配置文件，使用默认参数并告知
4. 错误处理：数据加载失败时给出明确提示（如"缺少daily_basic数据，无法计算换手率因子"）
5. 因子值中的NaN是正常的（停牌/新股），不要过滤掉整行
