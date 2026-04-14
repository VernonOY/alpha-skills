---
name: alpha-signal
description: >
  Daily trading signal generator. Compute factor scores on latest data and output target portfolio.
  每日交易信号生成器。基于最新数据计算因子得分，输出目标持仓。
  Triggers: "generate signals", "today's trades", "生成信号", "今日信号", "alpha-signal"
---

# alpha-signal — Daily Signal Generator / 每日信号生成

You are a portfolio signal generator. Read active factors from the library, compute scores on latest data, and output today's target portfolio.

你是一个组合信号生成器。从因子库读取活跃因子，在最新数据上计算得分，输出今日目标持仓。

## Bilingual Terms / 双语术语

| English | 中文 |
|---------|------|
| Signal | 信号 |
| Target Portfolio | 目标持仓 |
| Rebalance | 调仓 |
| Holdings | 持仓 |
| Weight | 权重 |
| Turnover | 换手率 |

## Project Context / 项目定位

- Factor Registry: `alpha_skills.db` (SQLite in project root)
- Signal History: `signals/` directory (auto-created)
- Config: `.claude/alpha-agent.config.md`

**Language Rule / 语言规则**:
- If the user speaks English, output in English
- If the user speaks Chinese, output in Chinese

## Execution Pipeline / 执行流程

### Step 1: Read Factor Library / 读取因子库

```python
import sqlite3, json, os
from datetime import datetime

PROJECT_DIR = "<current working directory>"
db_path = os.path.join(PROJECT_DIR, "alpha_skills.db")

with sqlite3.connect(db_path) as conn:
    conn.row_factory = sqlite3.Row
    active_factors = conn.execute(
        "SELECT * FROM factors WHERE status='active' ORDER BY icir DESC"
    ).fetchall()
    active_factors = [dict(r) for r in active_factors]

if not active_factors:
    print("No active factors in library. Run alpha-evaluate and alpha-library first.")
    # Stop here
```

If the library is empty, tell the user to evaluate and register factors first.
如果因子库为空，提示用户先评估并注册因子。

### Step 2: Load Latest Data / 加载最新数据

Same data loading pattern as alpha-evaluate (support Tushare cache, YFinance, or custom module).
数据加载方式同 alpha-evaluate。

Key difference: for signal generation, we need the **most recent dates** only.
关键区别：信号生成只需要**最近的日期数据**。

```python
# After loading and preprocessing close, volume, daily_basic, etc.
# Filter to recent data for efficiency
recent_start = close.index[-252]  # last 1 year for factor computation windows
close_recent = close.loc[recent_start:]
volume_recent = volume.loc[recent_start:]
# ... same for other data
```

### Step 3: Compute Factor Scores / 计算因子得分

For each active factor, compute its value on the latest date:

对每个活跃因子，计算其在最新日期上的值：

```python
import pandas as pd
import numpy as np

# Factor computation functions (self-contained, same as alpha-evaluate)
def momentum(close, period=20):
    return close.pct_change(period)

def reversal(close, period=5):
    return -close.pct_change(period)

def volatility(close, period=20):
    return -(close.pct_change().rolling(period).std() * np.sqrt(252))

def price_volume_divergence(close, volume, period=20):
    price_ret = close.pct_change()
    vol_ret = volume.pct_change()
    result = pd.DataFrame(index=close.index, columns=close.columns, dtype=float)
    for col in close.columns:
        if col in volume.columns:
            result[col] = price_ret[col].rolling(period).corr(vol_ret[col])
    return -result

def turnover_rate(daily_basic_df, period=20):
    df = daily_basic_df[["ts_code","trade_date","turnover_rate_f"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    pivot = df.pivot_table(index="trade_date", columns="ts_code", values="turnover_rate_f")
    return -pivot.rolling(period).mean()

# ... other factor functions as needed (see alpha-evaluate for full list)

def winsorize_mad(df, n=5):
    median = df.median(axis=1)
    mad = df.sub(median, axis=0).abs().median(axis=1)
    return df.clip(median - n*1.4826*mad, median + n*1.4826*mad, axis=0)

def standardize(df):
    df = winsorize_mad(df)
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)

# Map factor names to computation functions
FACTOR_MAP = {
    "momentum_20": lambda: momentum(close_recent, 20),
    "reversal_5": lambda: reversal(close_recent, 5),
    "reversal_10": lambda: reversal(close_recent, 10),
    "volatility_20": lambda: volatility(close_recent, 20),
    "pv_diverge": lambda: price_volume_divergence(close_recent, volume_recent, 20),
    "turnover_20": lambda: turnover_rate(daily_basic_recent, 20),
    # ... AI should map factor names from registry to computation functions
    # ... using the expression field from the registry record
}

# Compute all active factors
factor_scores = {}
for f in active_factors:
    name = f["name"]
    if name in FACTOR_MAP:
        try:
            vals = standardize(FACTOR_MAP[name]())
            factor_scores[name] = vals
        except Exception as e:
            print(f"Warning: failed to compute {name}: {e}")
```

### Step 4: Composite Score & Stock Selection / 复合得分与选股

```python
# Weight by ICIR (from registry)
weights = {}
total_icir = sum(abs(f["icir"] or 0) for f in active_factors if f["name"] in factor_scores)
for f in active_factors:
    name = f["name"]
    if name in factor_scores and total_icir > 0:
        weights[name] = abs(f["icir"] or 0) / total_icir

# Composite score on latest date
latest_date = close_recent.index[-1]
composite = None
for name, w in weights.items():
    if latest_date not in factor_scores[name].index:
        continue
    row = factor_scores[name].loc[latest_date].rank(pct=True).fillna(0.5)
    if composite is None:
        composite = row * w
    else:
        common = composite.index.intersection(row.index)
        composite = composite.reindex(common) * (1 - w) + row.reindex(common) * w

if composite is None:
    print("Error: no factor scores available for latest date")
    # Stop here

# Read config for stock count, filters
n_stocks = 15  # default, read from config if available

# Filter: remove NaN, suspended stocks
composite = composite.dropna()

# Filter: market cap and liquidity (if daily_basic available)
# ... apply MIN_MARKET_CAP, MIN_DAILY_AMOUNT from config

# Filter: limit-up stocks cannot be bought (A-share)
# Check market config for price_limit
daily_ret = close_recent.pct_change()
if latest_date in daily_ret.index:
    market_config = {}  # load from DATA_MODULE if available
    price_limit = market_config.get("price_limit", 0.1)
    if price_limit is not None:
        limit_up = daily_ret.loc[latest_date] > price_limit * 0.95
        composite = composite[~composite.index.isin(limit_up[limit_up].index)]

# Select top N
top_stocks = composite.nlargest(n_stocks)

# Normalize weights (ICIR-weighted based on factor scores)
target_weights = top_stocks / top_stocks.sum()
```

### Step 5: Compare with Previous Holdings / 与前日持仓对比

```python
signals_dir = os.path.join(PROJECT_DIR, "signals")
os.makedirs(signals_dir, exist_ok=True)

# Load yesterday's signal (if exists)
import glob
prev_files = sorted(glob.glob(os.path.join(signals_dir, "*.csv")))
prev_holdings = {}
if prev_files:
    prev_df = pd.read_csv(prev_files[-1])
    prev_holdings = dict(zip(prev_df["stock"], prev_df["weight"]))

# Calculate turnover
all_stocks = set(target_weights.index) | set(prev_holdings.keys())
turnover = sum(abs(target_weights.get(s, 0) - prev_holdings.get(s, 0)) for s in all_stocks)

# Identify buys and sells
new_buys = set(target_weights.index) - set(prev_holdings.keys())
sells = set(prev_holdings.keys()) - set(target_weights.index)
holds = set(target_weights.index) & set(prev_holdings.keys())
```

### Step 6: Save Signal & Output / 保存信号并输出

```python
# Save to CSV
date_str = latest_date.strftime("%Y-%m-%d")
signal_df = pd.DataFrame({
    "stock": target_weights.index,
    "weight": target_weights.values,
    "score": top_stocks.values,
})
signal_path = os.path.join(signals_dir, f"{date_str}.csv")
signal_df.to_csv(signal_path, index=False)
```

Output format:

```
📡 Daily Signal / 每日信号 — {date}

Active Factors 活跃因子 ({n} total):
  pv_diverge (ICIR=0.70, weight=40%)
  turnover_20 (ICIR=0.52, weight=30%)
  volatility_20 (ICIR=0.43, weight=30%)

Target Portfolio 目标持仓 ({n_stocks} stocks):

  Stock 股票     Weight 权重    Score 得分    Action 操作
  000001.SZ      8.2%          0.92        HOLD 持有
  600519.SH      7.5%          0.89        NEW BUY 新买入
  300750.SZ      7.1%          0.87        NEW BUY 新买入
  ...

Summary 摘要:
  New Buys 新买入: {n} stocks
  Sells 卖出: {n} stocks
  Holds 持有: {n} stocks
  Turnover 换手率: {turnover:.1%}
  Estimated Cost 预估成本: {turnover * cost_rate / 2:.2%}

Signal saved 信号已保存: signals/{date}.csv
```

### Step 7: Performance Tracking (if history exists) / 绩效追踪

If there are previous signals, compute realized performance:

如果有历史信号，计算已实现绩效：

```python
if len(prev_files) >= 5:
    # Load last 5 signals, compute daily return of each signal's portfolio
    # Compare with benchmark
    # Output: "Last 5 signals: avg return X%, benchmark Y%, excess Z%"
    ...
```

## Signal History Format / 信号历史格式

Each daily signal is saved as `signals/YYYY-MM-DD.csv`:

```csv
stock,weight,score
000001.SZ,0.082,0.92
600519.SH,0.075,0.89
300750.SZ,0.071,0.87
...
```

## Integration Options / 集成选项

The signal output is a standard CSV. Users can:
信号输出为标准CSV，用户可以：

1. **Manual execution 手动执行**: Read the signal, place orders yourself
2. **Script execution 脚本执行**: Write a script to read CSV and call broker API
3. **Webhook 推送**: Add a webhook call at the end to push signal to Slack/WeChat/email
4. **Scheduled 定时运行**: Use cron or Claude Code's schedule skill:
   ```bash
   # Run daily at 8:30 AM before market open
   30 8 * * 1-5 cd /project && claude -p "generate today's signals"
   ```

## Notes / 注意事项

1. Signal generation should run BEFORE market open (before 9:30 AM for A-share)
   信号生成应在开盘前运行
2. If factor library is empty, prompt user to evaluate and register factors first
   因子库为空时提示用户先评估注册因子
3. If no new data available (weekend/holiday), skip and notify
   无新数据时（周末/假日）跳过并通知
4. Always show turnover and estimated cost — high turnover = high cost
   始终显示换手率和预估成本
5. Save every signal to signals/ for future performance tracking
   保存每个信号用于未来绩效追踪
