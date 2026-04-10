---
name: alpha-evaluate
description: >
  Factor evaluation. Multi-level evaluation pipeline (IC/ICIR/quintile/robustness).
  因子评估。多级评估管线（IC/ICIR/分层/多空/鲁棒性）。
  Triggers: "evaluate factor", "test factor", "评估因子", "测试因子"
---

# alpha-evaluate — Factor Evaluation / 因子评估

你是一个专业量化分析师。当用户要求评估一个因子时，按照以下流程执行。
You are a professional quant analyst. Follow the pipeline below when evaluating a factor.

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

项目目录在用户的当前工作目录，其中：
Project directory is the user's current working directory, containing:
- `data_cache/` — 本地缓存的行情数据 Local cached market data（Parquet格式 format）
- `output/` — 报告输出目录 Report output directory
- `.claude/alpha-agent.config.md` — 用户自定义评估参数 User-defined evaluation parameters

**数据来源 / Data Source**：技能支持任何数据源。优先检查用户配置中的 DATA_SOURCE 字段：
The skill supports any data source. Check user config DATA_SOURCE field first:
- `tushare` (默认 default) — 使用Tushare Pro API拉取A股数据 / Fetch A-share data via Tushare Pro API
- `csv` — 从用户指定目录读取CSV/Parquet文件 / Read CSV/Parquet from user-specified directory
- `custom` — 用户提供自定义数据加载函数 / User-provided custom data loader

如果用户已在项目中定义了自己的数据加载模块（如 `my_data.py`），优先使用用户的模块。
If the user has defined a custom data module (e.g., `my_data.py`), use it first.
检查方式：查看配置文件中是否有 `DATA_MODULE` 字段指定了自定义模块路径。
Check: look for `DATA_MODULE` field in config file for custom module path.

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

用户可能以以下方式提供因子 / Users may provide factors in these ways：

1. **内置因子名称 Built-in name**: "评估reversal_5因子" / "evaluate reversal_5 factor"
2. **Python表达式 Python expression**: "评估 -close.pct_change(5) 这个因子" / "evaluate -close.pct_change(5)"
3. **自然语言描述 Natural language**: "评估一个5日反转因子" / "evaluate a 5-day reversal factor" → 你理解后映射到内置因子或生成代码
4. **FEL表达式 FEL expression**: "评估 ts_corr(close, volume, 20) * -1"（如项目已实现FEL解析器 if FEL parser is implemented）

## 执行流程 / Execution Pipeline

### Step 0 (Optional): Static Code Check / 静态代码检查

If the factor is provided as **a source file or a Python expression longer than one line**, offer to run `qtype` as a pre-flight check to catch look-ahead bias and time-leak bugs. `qtype` is an independent tool — check if it is installed:

如果用户提供的是**源文件或多行 Python 表达式**，建议先跑一遍 `qtype` 预检查，捕捉前视偏差和时间泄漏bug。`qtype` 是独立工具，先检查是否已安装：

```bash
which qtype || pip show qtype
```

If installed and the factor is a file:
如果已安装且因子是文件：

```bash
qtype check <path_to_factor.py>
```

**Rules / 规则**:
- QT001 look-ahead-bias: `.shift(N)` with negative literal
- QT002 future-function: calls to `lead`, `look_forward`, `peek_future`, etc.
- QT003 survival-bias: universe builder missing ST / suspended / delisted filters
- QT004 alignment-error: `.merge()` without explicit join keys
- QT005 return-offset: `pct_change()` assigned to `forward_*` / `next_*` / `target`

**Behavior / 行为**:
- If qtype finds **errors** (QT001/QT002): stop evaluation and show the bug. Evaluating a factor with look-ahead bias produces fake alpha.
- If qtype finds **warnings** (QT003/QT004/QT005): show them to the user and ask whether to proceed.
- If qtype is **not installed**: skip this step silently. Do not block evaluation. Optionally mention qtype once: "Tip: install qtype to catch time-leak bugs automatically — `pip install qtype`."
- If the factor is a **built-in factor name** (e.g., `pv_diverge`): skip this step entirely, built-ins are already verified.

- 如果 qtype 发现**错误**（QT001/QT002）：停止评估并展示bug。带前视偏差的因子会产出虚假 alpha。
- 如果发现**警告**（QT003/QT004/QT005）：展示给用户并询问是否继续。
- 如果 qtype **未安装**：静默跳过，不要阻塞流程。可以提一句建议："提示：安装 qtype 可自动捕捉时间泄漏bug — `pip install qtype`。"
- 如果因子是**内置因子名**（如 `pv_diverge`）：跳过此步，内置因子已验证。

### Step 1: 读取用户配置 / Read User Config

```python
# 读取 .claude/alpha-agent.config.md 中的评估参数
# Read evaluation parameters from .claude/alpha-agent.config.md
# 如果文件不存在，使用默认值 / If file not found, use defaults
```

默认值 Defaults：
- 持有期 Holding periods: [5, 10, 20]
- IC快筛阈值 IC quick-filter threshold: 0.02
- Strong ICIR: 0.5
- Moderate ICIR: 0.3

### Step 1.5: 确定市场 / Determine Market

从配置读取 `MARKET` 字段（默认 "A-share"）：
Read `MARKET` field from config (default "A-share"):

- **A-share (A股)**: 默认Tushare数据源，data_cache/ 目录
- **US (美股)**: DATA_MODULE=examples.us_data_yfinance
- **HK (港股)**: DATA_MODULE=examples.hk_data_yfinance
- **Custom**: 用户自定义模块 / user custom module

如果配置了 DATA_MODULE，加载该模块并读取其 MARKET_CONFIG：
If DATA_MODULE is configured, load module and read MARKET_CONFIG:

```python
import importlib
if config.get("DATA_MODULE"):
    data_mod = importlib.import_module(config["DATA_MODULE"])
    market_config = data_mod.MARKET_CONFIG
    cost_rate = market_config["cost_rate"]
    benchmark_symbol = market_config["benchmark"]
    price_limit = market_config.get("price_limit")  # None表示无涨跌停
```

### Step 2: 加载数据 / Load Data

首先检查用户是否有自定义数据加载方式（配置中 DATA_MODULE 或 DATA_SOURCE 字段）。
First check if user has a custom data loader (DATA_MODULE or DATA_SOURCE in config).

**方式A: 用户自定义数据模块 / Method A: User Custom Data Module**（优先 Priority）

如果配置了 `DATA_MODULE: my_data`，则 / If `DATA_MODULE: my_data` is configured：
```python
import importlib
data_mod = importlib.import_module("my_data")
# 用户模块需提供以下函数（返回DataFrame）：
# User module must provide these functions (returning DataFrame):
# data_mod.load_prices(start, end) → DataFrame with columns: ts_code, trade_date, open, high, low, close, vol, amount
# data_mod.load_adj_factor(start, end) → DataFrame with columns: ts_code, trade_date, adj_factor
# data_mod.load_daily_basic(start, end) → DataFrame with columns: ts_code, trade_date, pe_ttm, pb, turnover_rate_f, ...
# data_mod.load_financial(start, end) → DataFrame with columns: ts_code, ann_date, end_date, roe, roa, ...
```

**方式B: CSV/Parquet本地文件 / Method B: Local CSV/Parquet Files**

如果配置了 `DATA_SOURCE: csv` 和 `DATA_DIR: /path/to/data`，则从指定目录读取文件：
If `DATA_SOURCE: csv` and `DATA_DIR: /path/to/data` are configured, read from specified directory:
```python
DATA_DIR = config.get("DATA_DIR", "data")
daily_prices = pd.read_parquet(os.path.join(DATA_DIR, "daily_prices.parquet"))
# 或 / or pd.read_csv(os.path.join(DATA_DIR, "daily_prices.csv"))
```

**方式C: Tushare缓存 / Method C: Tushare Cache**（默认 Default）

```python
import sys, os, glob, warnings
warnings.filterwarnings("ignore")
PROJECT_DIR = "<用户当前工作目录的绝对路径 / absolute path to user's cwd>"
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

**数据格式约定 / Data Format Convention**（无论哪种方式，最终数据需符合 regardless of method）：
- `daily_prices`: 必须含 must contain ts_code, trade_date, open, high, low, close, vol, amount
- `adj_factor`: 必须含 must contain ts_code, trade_date, adj_factor
- `trade_date` 格式 format: YYYYMMDD 字符串或可解析日期 string or parseable date

### Step 3: 数据预处理 / Data Preprocessing（前复权+过滤 Forward-adjust + Filter）

```python
# 过滤股票池 / Filter stock pool
valid_codes = set(stock_pool["ts_code"].tolist()) if not stock_pool.empty else set(daily_prices["ts_code"].unique())
dp = daily_prices[daily_prices["ts_code"].isin(valid_codes)].copy()
dp["trade_date"] = pd.to_datetime(dp["trade_date"], format="%Y%m%d")

# Pivot成宽表 / Pivot to wide format
close_raw = dp.pivot_table(index="trade_date", columns="ts_code", values="close").sort_index()
volume = dp.pivot_table(index="trade_date", columns="ts_code", values="vol").fillna(0)
high_raw = dp.pivot_table(index="trade_date", columns="ts_code", values="high")
low_raw = dp.pivot_table(index="trade_date", columns="ts_code", values="low")

# 前复权 / Forward adjustment
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

# 过滤稀疏股票 / Filter sparse stocks
min_count = int(len(close) * 0.4)
valid_stocks = close.columns[close.notna().sum() >= min_count]
close = close[valid_stocks]
```

### Step 4: 计算因子 / Compute Factor

根据用户输入的因子类型调用对应函数 / Call corresponding function based on user input：

```python
import pandas as pd
import numpy as np

# ── 因子计算函数（自包含，无外部依赖）/ Factor functions (self-contained, no external deps) ──

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

def macd_divergence(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    return (dif - dea) / close

def bollinger_position(close, period=20, std_mult=2):
    ma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = ma + std_mult * std
    lower = ma - std_mult * std
    band_width = (upper - lower).replace(0, np.nan)
    return -((close - lower) / band_width * 2 - 1)

def atr_ratio(high, low, close, period=14):
    prev_close = close.shift(1)
    tr = pd.DataFrame(
        np.maximum(np.maximum((high-low).values, (high-prev_close).abs().values), (low-prev_close).abs().values),
        index=close.index, columns=close.columns
    )
    atr = tr.rolling(period).mean()
    return -(atr / close.replace(0, np.nan))

def turnover_rate(daily_basic_df, period=20):
    df = daily_basic_df[["ts_code","trade_date","turnover_rate_f"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    pivot = df.pivot_table(index="trade_date", columns="ts_code", values="turnover_rate_f")
    return -pivot.rolling(period).mean()

def abnormal_turnover(daily_basic_df, period_short=5, period_long=60):
    df = daily_basic_df[["ts_code","trade_date","turnover_rate_f"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    pivot = df.pivot_table(index="trade_date", columns="ts_code", values="turnover_rate_f")
    return -(pivot.rolling(period_short).mean() / pivot.rolling(period_long).mean() - 1)

def pe_ttm(daily_basic_df):
    df = daily_basic_df[["ts_code","trade_date","pe_ttm"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    pivot = df.pivot_table(index="trade_date", columns="ts_code", values="pe_ttm")
    return -pivot.where(pivot > 0)

def pb(daily_basic_df):
    df = daily_basic_df[["ts_code","trade_date","pb"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    pivot = df.pivot_table(index="trade_date", columns="ts_code", values="pb")
    return -pivot.where(pivot > 0)

def dividend_yield(daily_basic_df):
    df = daily_basic_df[["ts_code","trade_date","dv_ttm"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    return df.pivot_table(index="trade_date", columns="ts_code", values="dv_ttm")

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

# ── 计算因子 / Compute factor ──
factor_values = <因子函数>(close, ...)  # 根据因子类型调用 call by factor type
factor_values = standardize(factor_values)  # 截面标准化 cross-sectional standardize
```

**按上述模式现场编写更多因子 / Write more factors following the pattern above**：
对于内置因子映射表中未在上面提供完整实现的因子（如 roe, roa, gross_margin, net_profit_growth 等基本面因子），
AI应参考已有因子的实现模式，使用 pandas pivot + rolling 等操作现场编写代码。
For built-in factors not fully implemented above (e.g., roe, roa, gross_margin, net_profit_growth),
the AI should write code on-the-fly following the same pattern using pandas pivot + rolling operations.

**内置因子映射表 / Built-in Factor Mapping**（用户说因子名时参考 reference when user mentions factor name）：
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

### Step 5: 运行评估 / Run Evaluation

```python
from scipy import stats

def compute_forward_returns(close, periods=5, shift_days=1):
    future_close = close.shift(-shift_days - periods + 1)
    entry_close = close.shift(-shift_days + 1)
    return future_close / entry_close.replace(0, np.nan) - 1.0

def calc_ic_series(factor_values, forward_returns):
    """计算每期截面IC（Spearman秩相关） / Compute per-period cross-sectional IC (Spearman rank corr)"""
    ic_values, ic_dates = [], []
    common_dates = factor_values.index.intersection(forward_returns.index)
    common_stocks = factor_values.columns.intersection(forward_returns.columns)
    for date in common_dates:
        f = factor_values.loc[date, common_stocks].dropna()
        r = forward_returns.loc[date, common_stocks].dropna()
        common = f.index.intersection(r.index)
        if len(common) < 5:
            continue
        fv, rv = f[common].values, r[common].values
        valid = np.isfinite(fv) & np.isfinite(rv)
        if valid.sum() < 5:
            continue
        corr, _ = stats.spearmanr(fv[valid], rv[valid])
        if np.isfinite(corr):
            ic_values.append(corr)
            ic_dates.append(date)
    return pd.Series(ic_values, index=pd.DatetimeIndex(ic_dates), name="IC")

def calc_group_returns(factor_values, forward_returns, n_groups=5):
    """分层回测 / Quintile stratification backtest"""
    group_data = {f"G{i+1}": [] for i in range(n_groups)}
    valid_dates = []
    common_dates = factor_values.index.intersection(forward_returns.index)
    common_stocks = factor_values.columns.intersection(forward_returns.columns)
    for date in common_dates:
        f = factor_values.loc[date, common_stocks].dropna()
        r = forward_returns.loc[date, common_stocks].dropna()
        common = f.index.intersection(r.index)
        if len(common) < n_groups:
            continue
        f, r = f[common], r[common]
        valid = np.isfinite(f) & np.isfinite(r)
        f, r = f[valid], r[valid]
        if len(f) < n_groups:
            continue
        try:
            labels = pd.qcut(f.rank(method="first"), n_groups, labels=False)
        except ValueError:
            continue
        valid_dates.append(date)
        for g in range(n_groups):
            mask = labels == g
            group_data[f"G{g+1}"].append(r[mask].mean() if mask.sum() > 0 else np.nan)
    return pd.DataFrame(group_data, index=pd.DatetimeIndex(valid_dates))

# ── 运行评估 / Run evaluation ──
results = {}
for hp in holding_periods:  # [5, 10, 20]
    fwd_ret = compute_forward_returns(close, periods=hp)
    # 对齐 / Align
    cd = factor_values.index.intersection(fwd_ret.index)
    cs = factor_values.columns.intersection(fwd_ret.columns)
    fv = factor_values.loc[cd, cs]
    fr = fwd_ret.loc[cd, cs]
    ic_series = calc_ic_series(fv, fr)
    group_ret = calc_group_returns(fv, fr, n_groups=5)
    ic_mean = ic_series.mean()
    icir = ic_series.mean() / ic_series.std() if ic_series.std() > 0 else 0
    ic_pos_ratio = (ic_series > 0).mean()
    # 多空收益 / Long-short returns
    ls_ret = group_ret["G5"] - group_ret["G1"]
    ls_cum = (1 + ls_ret).cumprod()
    ls_sharpe = ls_ret.mean() / ls_ret.std() * np.sqrt(252 / hp) if ls_ret.std() > 0 else 0
    ls_maxdd = ((ls_cum - ls_cum.cummax()) / ls_cum.cummax()).min()
    # 单调性 / Monotonicity
    group_means = [group_ret[f"G{g+1}"].mean() for g in range(5)]
    mono_corr, mono_p = stats.spearmanr(range(5), group_means)
    results[hp] = {
        "ic_mean": ic_mean, "icir": icir, "ic_pos_ratio": ic_pos_ratio,
        "ls_sharpe": ls_sharpe, "ls_maxdd": ls_maxdd,
        "monotonic": abs(mono_corr) > 0.8 and mono_p < 0.1,
        "mono_corr": mono_corr, "mono_p": mono_p,
        "ic_series": ic_series, "group_ret": group_ret,
    }
```

### Step 6: 生成报告 / Generate Report

```python
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

best_hp = max(results, key=lambda hp: abs(results[hp]["icir"]))
best = results[best_hp]

# 用matplotlib生成4子图报告 / Generate 4-subplot report with matplotlib:
# 子图1 Subplot1: IC时序图 IC time series (bar chart, color by positive/negative)
# 子图2 Subplot2: 累计IC Cumulative IC (line chart)
# 子图3 Subplot3: 分组累计收益 Quintile cumulative returns (5 lines, G1~G5)
# 子图4 Subplot4: 多空净值 Long-short NAV (line chart with drawdown shading)
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle(f"Factor Report: {factor_name} (HP={best_hp}d)")

# Plot IC series, cumulative IC, group returns, long-short NAV
# ... (AI writes the specific plotting code based on results dict)

plt.tight_layout()
save_path = os.path.join(OUTPUT_DIR, f"eval_{factor_name}.png")
fig.savefig(save_path, dpi=150, bbox_inches="tight")
plt.close()
```

### Step 7: 输出结果 / Output Results

向用户展示如下格式的结果（使用表格）/ Present results in this format (using tables)：

```
📊 Factor Evaluation Report / 因子评估报告: <factor_name>

Expression 表达式: <factor expression or function call>

┌──────────────────────────────┬─────────────┬──────────────┬──────────────┐
│ Metric 指标                  │ 5-day 5日   │ 10-day 10日  │ 20-day 20日  │
├──────────────────────────────┼─────────────┼──────────────┼──────────────┤
│ IC Mean IC均值               │ x.xxx       │ x.xxx        │ x.xxx        │
│ ICIR                         │ x.xxx       │ x.xxx        │ x.xxx        │
│ IC>0 Ratio IC>0占比          │ xx.x%       │ xx.x%        │ xx.x%        │
│ L/S Sharpe 多空Sharpe        │ x.xx        │ x.xx         │ x.xx         │
│ L/S MaxDD 多空MaxDD          │ -xx.x%      │ -xx.x%       │ -xx.x%       │
│ Quintile Mono 分组单调       │  ✓/✗        │  ✓/✗         │  ✓/✗         │
└──────────────────────────────┴─────────────┴──────────────┴──────────────┘

Rating 评级: ⭐ Strong / ● Moderate / · Weak
Best Holding Period 最佳持有期: xx days/日
Quintile Monotonicity 分组单调性: Spearman=x.xx, p=x.xx

Report chart saved / 报告图表已保存: output/eval_<name>.png
```

评级标准 Rating Criteria（从配置读取 read from config）：
- **Strong**: |ICIR| >= 0.5 且 and 分组单调 quintile monotonic 且 and |L/S Sharpe 多空Sharpe| > 1
- **Moderate**: |ICIR| >= 0.3 或 or |L/S Sharpe 多空Sharpe| > 0.5
- **Weak**: 以上均不满足 none of the above

### Step 8: 后续建议 / Follow-up Suggestions

评估完成后询问用户 / After evaluation, ask the user：
- "Register to factor library? / 是否加入因子库？"（→ 触发 trigger alpha-library add）
- "Run robustness test? / 是否需要鲁棒性检验？"（→ 运行 run Level 3）
- "Run backtest? / 是否回测？"（→ 触发 trigger alpha-backtest）

## 注意事项 / Notes

1. 所有Python代码用 `/opt/anaconda3/bin/python` 执行 / All Python code runs with `/opt/anaconda3/bin/python`
2. 数据量大时预处理可能需要30秒+ / Preprocessing may take 30s+ with large data，告知用户 inform user "Loading data... / 正在加载数据..."
3. 如果用户没有配置文件，使用默认参数并告知 / If no config file, use defaults and inform user
4. 错误处理 Error handling：数据加载失败时给出明确提示 give clear message on data load failure（如 e.g. "Missing daily_basic data, cannot compute turnover factor / 缺少daily_basic数据，无法计算换手率因子"）
5. 因子值中的NaN是正常的 NaN in factor values is normal（停牌/新股 suspended/new stocks），不要过滤掉整行 do not filter entire rows
