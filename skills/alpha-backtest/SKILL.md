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

- Python包 Package: `alpha_agent/` (backtest/engine.py, backtest/result.py, factors/builtin.py等)
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
from alpha_agent.factors.builtin import <因子函数 factor functions>
from alpha_agent.factors.preprocessing import standardize

# 计算各因子 / Compute each factor
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
from alpha_agent.backtest.engine import BacktestEngine

# 基准 / Benchmark
idx = index_data.copy()
idx["trade_date"] = pd.to_datetime(idx["trade_date"], format="%Y%m%d")
benchmark = idx.set_index("trade_date")["close"].sort_index()

engine = BacktestEngine(close, benchmark, cost_rate=cost_rate, risk_free=risk_free)
result = engine.run(signals)
```

### Step 5: 门控检查 / Gate Check

```python
# 从配置读取门控阈值 / Read gate thresholds from config
gate = result.gate_check()
pref = result.preferred_check()
metrics = result.metrics()
```

### Step 6: IS/OOS对比 / IS/OOS Comparison

分别在IS和OOS区间运行回测，计算Sharpe衰减 / Run backtest on IS and OOS separately, compute Sharpe decay：
```python
is_signals = {d: s for d, s in signals.items() if d <= is_end}
oos_signals = {d: s for d, s in signals.items() if d >= oos_start}

is_result = engine.run(is_signals)
oos_result = engine.run(oos_signals)

from alpha_agent.backtest.result import BacktestResult
decay = BacktestResult.oos_sharpe_decay(is_result, oos_result)
```

### Step 7: 生成报告 / Generate Report

```python
from alpha_agent.report.report import StrategyReport

report = StrategyReport(result, strategy_name="MultiFactorStrategy")
report.generate_full_report(save_path=os.path.join(OUTPUT_DIR, "backtest_report.png"))
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
