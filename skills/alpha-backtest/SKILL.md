---
name: alpha-backtest
description: >
  Strategy backtest. Single/multi-factor portfolio backtesting with gate checks.
  策略回测。单/多因子组合回测。
  Triggers: "backtest", "run backtest", "回测", "跑个回测"
---

# alpha-backtest — Strategy Backtest / 策略回测

你是一个量化策略回测工程师。当用户要求回测时，构建因子选股策略并使用BacktestEngine运行回测。
You are a quant strategy backtest engineer. Build factor-based stock selection strategies and run backtests using BacktestEngine.

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

- 数据 Data: `data_cache/` (已缓存Parquet cached Parquet)
- 配置 Config: `.claude/alpha-agent.config.md` (门控指标等 gate metrics etc.)
- 输出 Output: `output/` 目录 directory

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

## 输入识别 / Input Recognition

1. **单因子回测 Single-factor backtest**: "回测pv_diverge因子" / "backtest pv_diverge factor" → 用单个因子选股 single factor stock selection
2. **多因子组合 Multi-factor combo**: "用pv_diverge和turnover_20做组合回测" / "combo backtest with pv_diverge and turnover_20" → 多因子加权 multi-factor weighting
3. **交互式 Interactive**: "帮我跑个回测" / "help me run a backtest" → 询问参数后执行 ask for parameters then execute
4. **从因子库选取 From registry**: "用因子库里最强的3个因子回测" / "backtest with top 3 factors from library" → 从registry读取 read from registry

## 执行流程 / Execution Pipeline

### Step 1: 确定参数 / Determine Parameters

从用户输入和配置文件确定 / Determine from user input and config：
- **因子列表 Factor list**: 哪些因子参与 which factors（名称列表 name list）
- **权重方案 Weight scheme**: 等权 equal weight（默认 default）/ ICIR加权 ICIR-weighted / 用户指定 user-specified
- **回测区间 Backtest period**: 默认 default 2022-01-01 ~ 2025-12-31
- **IS/OOS切分 IS/OOS split**: 默认 default IS至 until 2024-12-31，OOS从 from 2025-01-01
- **调仓频率 Rebalance frequency**: 默认 default 20个交易日 trading days（月频 monthly）
- **持仓数量 Holdings count**: 默认 default 15只 stocks
- **是否择时 Market timing**: 默认开启 default on（MA20/MA60）
- **市值过滤 Market cap filter**: 从配置读取 read from config
- **交易成本 Transaction cost**: 从配置读取 read from config（默认 default 0.003）

如果用户没有明确指定，使用默认值并告知。
If user doesn't specify, use defaults and inform.

### Market-Aware Trading Rules / 市场感知交易规则

Skill根据 MARKET_CONFIG 自动应用对应的交易规则：
Skill automatically applies trading rules based on MARKET_CONFIG:

| Rule / 规则 | A-share A股 | HK 港股 | US 美股 |
|-------------|-------------|---------|---------|
| Price Limit 涨跌停 | ±10% | None 无 | None 无 |
| T+N | T+1 | T+0 | T+0 |
| Round-trip Cost 双边成本 | 0.3% | 0.2% | 0.1% |
| Min Trade Unit 最小单位 | 100 shares | 100+ | 1 share |
| Stamp Duty 印花税 | 0.1% (sell) | 0.13% | 0 |

从 DATA_MODULE 的 MARKET_CONFIG 自动读取这些字段，无需用户手动指定。
These fields are automatically read from DATA_MODULE's MARKET_CONFIG; no manual specification needed.

### Step 2: 数据加载与预处理 / Data Loading & Preprocessing

同 alpha-evaluate 的数据加载流程（加载缓存 → pivot → 前复权 → 过滤）。
Same as alpha-evaluate data loading pipeline (load cache → pivot → forward-adjust → filter).

### Step 3: 计算因子并生成信号 / Compute Factors & Generate Signals

```python
import pandas as pd
import numpy as np

# ── 因子计算函数（自包含）/ Factor functions (self-contained) ──
# 定义所需因子函数（参见 alpha-evaluate skill 中的完整实现）
# Define required factor functions (see alpha-evaluate skill for full implementations)

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

def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return -(100 - 100 / (1 + rs) - 50)

def turnover_rate(daily_basic_df, period=20):
    df = daily_basic_df[["ts_code","trade_date","turnover_rate_f"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    pivot = df.pivot_table(index="trade_date", columns="ts_code", values="turnover_rate_f")
    return -pivot.rolling(period).mean()

# ... 其他因子按同样模式定义 / other factors defined following the same pattern ...
# AI应根据用户指定的因子名称，参考 alpha-evaluate skill 中的实现模式现场编写
# AI should write factor code on-the-fly based on the patterns in alpha-evaluate skill

# ── 预处理函数 / Preprocessing functions ──

def winsorize_mad(df, n=5):
    median = df.median(axis=1)
    mad = df.sub(median, axis=0).abs().median(axis=1)
    upper = median + n * 1.4826 * mad
    lower = median - n * 1.4826 * mad
    return df.clip(lower, upper, axis=0)

def zscore_cross_section(df):
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)

def standardize(df, mad_n=5):
    return zscore_cross_section(winsorize_mad(df, n=mad_n))

# ── 计算各因子 / Compute each factor ──
factor_dfs = {}
for name in factor_names:
    factor_dfs[name] = standardize(<对应因子函数 corresponding function>(...))

# 复合得分 / Composite score
composite = None
for name, weight in weights.items():
    ranked = factor_dfs[name].rank(axis=1, pct=True)
    if composite is None:
        composite = ranked * weight
    else:
        common_dates = composite.index.intersection(ranked.index)
        common_stocks = composite.columns.intersection(ranked.columns)
        composite = composite.loc[common_dates, common_stocks].fillna(0.5) * (1 - weight) + \
                    ranked.loc[common_dates, common_stocks].fillna(0.5) * weight

# 择时信号（可选）/ Market timing signal (optional)
if use_timing:
    benchmark_close = ...  # 沪深300 CSI 300
    ma_fast = benchmark_close.rolling(20).mean()
    ma_slow = benchmark_close.rolling(60).mean()
    ratio = (ma_fast - ma_slow) / ma_slow
    # ratio > 0.02 满仓 full position, -0.02~0.02 半仓 half position, < -0.02 空仓 empty

# 生成调仓信号 / Generate rebalance signals
trading_days = close.index
mask = (trading_days >= start_date) & (trading_days <= end_date)
bt_days = trading_days[mask]
rebal_dates = bt_days[::rebal_freq]

signals = {}
for date in rebal_dates:
    if use_timing and ratio.get(date, 0) < -0.02:
        continue  # 空仓 empty position
    
    scores = composite.loc[date].dropna()
    # 根据市场规则过滤 / Filter by market rules
    if market_config.get("price_limit") is not None:
        limit = market_config["price_limit"]  # 如 0.1 for A股
        daily_ret = close.pct_change()
        if date in daily_ret.index:
            limit_up = daily_ret.loc[date] > limit * 0.95  # 留5%余量
            scores = scores[~scores.index.isin(limit_up[limit_up].index)]
    # 美股/港股无涨跌停，跳过此过滤 / US/HK no price limit, skip this filter
    
    n = n_stocks if (not use_timing or ratio.get(date, 0) > 0.02) else n_stocks // 2
    top = scores.nlargest(n)
    # 按得分加权 / Weight by score
    w = top / top.sum()
    signals[date] = w.to_dict()
```

### Step 4: 运行回测 / Run Backtest

```python
def simple_backtest(close, signals, cost_rate=0.003):
    """
    简易回测引擎 / Simple backtest engine
    close: DataFrame (index=日期, columns=股票)
    signals: dict {date: {stock: weight}} 或 {date: [stock_list]}
    cost_rate: 双边交易成本 round-trip transaction cost
    返回 Returns: nav Series, metrics dict
    """
    # 如果signals的value是list，转为等权 / Convert list to equal weight
    for dt in signals:
        if isinstance(signals[dt], list):
            n = len(signals[dt])
            signals[dt] = {s: 1.0/n for s in signals[dt]} if n > 0 else {}
    
    trading_days = close.index.sort_values()
    signal_dates = sorted(signals.keys())
    
    nav_values, nav_dates = [], []
    current_weights = {}
    current_nav = 1.0
    daily_ret = close.pct_change()
    
    for i, today in enumerate(trading_days):
        if today < signal_dates[0]:
            continue
        # 持仓漂移 / Portfolio drift
        if current_weights and i > 0:
            port_ret = sum(w * (daily_ret.at[today, s] if s in daily_ret.columns and pd.notna(daily_ret.at[today, s]) else 0)
                          for s, w in current_weights.items())
            current_nav *= (1 + port_ret)
        # 调仓 / Rebalance
        if today in signals and signals[today]:
            new_w = signals[today]
            total = sum(new_w.values())
            if total > 0:
                new_w = {k: v/total for k, v in new_w.items()}
            turnover = sum(abs(new_w.get(s, 0) - current_weights.get(s, 0))
                          for s in set(new_w) | set(current_weights))
            current_nav *= (1 - turnover * cost_rate / 2)
            current_weights = new_w
        nav_values.append(current_nav)
        nav_dates.append(today)
    
    nav = pd.Series(nav_values, index=pd.DatetimeIndex(nav_dates))
    # 计算指标 / Compute metrics
    daily_r = nav.pct_change().dropna()
    n_years = len(daily_r) / 252
    total_ret = nav.iloc[-1] / nav.iloc[0] - 1
    ann_ret = (1 + total_ret) ** (1/n_years) - 1 if n_years > 0 else 0
    ann_vol = daily_r.std() * np.sqrt(252)
    sharpe = (ann_ret - 0.025) / ann_vol if ann_vol > 0 else 0
    cummax = nav.cummax()
    max_dd = ((nav - cummax) / cummax).min()
    monthly = nav.resample("ME").last().pct_change().dropna()
    win_rate = (monthly > 0).mean() if len(monthly) > 0 else 0
    profit_months = monthly[monthly > 0].sum()
    loss_months = monthly[monthly < 0].sum()
    profit_factor = abs(profit_months / loss_months) if abs(loss_months) > 1e-12 else float("inf")
    
    return nav, {
        "annual_return": ann_ret, "sharpe": sharpe, "max_drawdown": max_dd,
        "monthly_win_rate": win_rate, "profit_factor": profit_factor,
        "total_return": total_ret, "annual_vol": ann_vol,
    }

# ── 运行回测 / Run backtest ──
# 基准 / Benchmark
idx = index_data.copy()
idx["trade_date"] = pd.to_datetime(idx["trade_date"], format="%Y%m%d")
benchmark = idx.set_index("trade_date")["close"].sort_index()

nav, metrics = simple_backtest(close, signals, cost_rate=cost_rate)
```

### Step 5: 门控检查 / Gate Check

```python
# 从配置读取门控阈值 / Read gate thresholds from config
# 使用 metrics dict 中的指标进行门控检查 / Use metrics dict for gate checks
gate_pass = {
    "sharpe >= 1.0": metrics["sharpe"] >= 1.0,
    "max_dd >= -25%": metrics["max_drawdown"] >= -0.25,
    "profit_factor >= 1.0": metrics["profit_factor"] >= 1.0,
    "monthly_wr >= 55%": metrics["monthly_win_rate"] >= 0.55,
}
```

### Step 6: IS/OOS对比 / IS/OOS Comparison

分别在IS和OOS区间运行回测，计算Sharpe衰减 / Run backtest on IS and OOS separately, compute Sharpe decay：
```python
is_signals = {d: s for d, s in signals.items() if d <= is_end}
oos_signals = {d: s for d, s in signals.items() if d >= oos_start}

is_nav, is_metrics = simple_backtest(close, is_signals, cost_rate=cost_rate)
oos_nav, oos_metrics = simple_backtest(close, oos_signals, cost_rate=cost_rate)

# Sharpe衰减 / Sharpe decay
sharpe_decay = 1 - oos_metrics["sharpe"] / is_metrics["sharpe"] if is_metrics["sharpe"] != 0 else float("nan")
```

### Step 7: 生成报告 / Generate Report

```python
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

# 用matplotlib生成回测报告图表 / Generate backtest report charts with matplotlib:
# 子图1 Subplot1: 策略净值 vs 基准净值 Strategy NAV vs Benchmark NAV (line chart)
# 子图2 Subplot2: 回撤曲线 Drawdown curve (filled area chart)
# 子图3 Subplot3: 月度收益热力图 Monthly return heatmap
# 子图4 Subplot4: 滚动Sharpe Rolling Sharpe (line chart, 60-day window)
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Backtest Report: MultiFactorStrategy")

# Plot NAV, drawdown, monthly returns, rolling Sharpe
# ... (AI writes the specific plotting code based on nav and metrics)

plt.tight_layout()
save_path = os.path.join(OUTPUT_DIR, "backtest_report.png")
fig.savefig(save_path, dpi=150, bbox_inches="tight")
plt.close()
```

### Step 8: 输出结果 / Output Results

```
📈 Backtest Results / 回测结果: <strategy name 策略名称>

Factors 因子: <factor1>×weight + <factor2>×weight + ...
Period 区间: YYYY-MM-DD ~ YYYY-MM-DD | Rebalance 调仓: N days/日 | Holdings 持仓: N stocks/只

                          IS Period IS期间   OOS Period OOS期间   Full Period 全区间
Annual Return 年化收益     xx.xx%              xx.xx%              xx.xx%
Sharpe                    x.xxx               x.xxx               x.xxx
MaxDD 最大回撤             -xx.xx%             -xx.xx%             -xx.xx%
PF (Profit Factor)        x.xxx               x.xxx               x.xxx
Monthly WR 月度胜率        xx.x%               xx.x%               xx.x%
Calmar                    x.xxx               x.xxx               x.xxx

Sharpe Decay Sharpe衰减: xx.x% (IS→OOS)

Gate Check 门控检查:
  ✓/✗ Sharpe ≥ 1.0      → x.xxx
  ✓/✗ MaxDD ≥ -25%      → -xx.xx%
  ✓/✗ PF ≥ 1.0          → x.xxx
  ✓/✗ Monthly WR 月度胜率 ≥ 55%    → xx.x%
  ✓/✗ Max Consec Loss Months 最大连续亏损月 ≤ 4 → N months/个月

Report chart 报告图表: output/backtest_report.png
```

## 注意事项 / Notes

1. 多因子权重归一化 Multi-factor weight normalization：确保权重之和=1.0 ensure weights sum to 1.0
2. 择时逻辑 Market timing：空仓日不生成信号 no signals on empty days，BacktestEngine在无信号期间保持现金 holds cash when no signals
3. 涨停过滤 Limit-up filter：A股涨幅>9.5%的股票无法买入 A-share stocks with >9.5% gain cannot be bought
4. 如果因子需要daily_basic或fina数据但缺失，提示用户 / If factor needs daily_basic or fina data but missing, inform user
5. 回测时间较长时告知用户 Inform user for long backtests "Running backtest, ~1-2 min... / 正在回测，预计1-2分钟..."
6. 门控阈值从 Gate thresholds from .claude/alpha-agent.config.md 读取 read
