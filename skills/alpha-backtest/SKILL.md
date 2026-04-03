---
name: alpha-backtest
description: >
  策略回测skill。用一个或多个因子构建选股策略并回测。
  触发词："回测"、"跑个回测"、"用XX因子回测"、"多因子组合"、"alpha-backtest"。
---

# alpha-backtest — 策略回测

你是一个量化策略回测工程师。当用户要求回测时，构建因子选股策略并使用BacktestEngine运行回测。

## 项目定位

- Python包: `alpha_agent/` (backtest/engine.py, backtest/result.py, factors/builtin.py等)
- 数据: `data_cache/` (已缓存Parquet)
- 配置: `.claude/alpha-agent.config.md` (门控指标等)
- 输出: `output/` 目录

## 输入识别

1. **单因子回测**: "回测pv_diverge因子" → 用单个因子选股
2. **多因子组合**: "用pv_diverge和turnover_20做组合回测" → 多因子加权
3. **交互式**: "帮我跑个回测" → 询问参数后执行
4. **从因子库选取**: "用因子库里最强的3个因子回测" → 从registry读取

## 执行流程

### Step 1: 确定参数

从用户输入和配置文件确定：
- **因子列表**: 哪些因子参与（名称列表）
- **权重方案**: 等权（默认）/ ICIR加权 / 用户指定
- **回测区间**: 默认 2022-01-01 ~ 2025-12-31
- **IS/OOS切分**: 默认 IS至2024-12-31，OOS从2025-01-01
- **调仓频率**: 默认20个交易日（月频）
- **持仓数量**: 默认15只
- **是否择时**: 默认开启（MA20/MA60）
- **市值过滤**: 从配置读取
- **交易成本**: 从配置读取（默认0.003）

如果用户没有明确指定，使用默认值并告知。

### Step 2: 数据加载与预处理

同 alpha-evaluate 的数据加载流程（加载缓存 → pivot → 前复权 → 过滤）。

### Step 3: 计算因子并生成信号

```python
from alpha_agent.factors.builtin import <因子函数>
from alpha_agent.factors.preprocessing import standardize

# 计算各因子
factor_dfs = {}
for name in factor_names:
    factor_dfs[name] = standardize(<对应因子函数>(...))

# 复合得分
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

# 择时信号（可选）
if use_timing:
    benchmark_close = ...  # 沪深300
    ma_fast = benchmark_close.rolling(20).mean()
    ma_slow = benchmark_close.rolling(60).mean()
    ratio = (ma_fast - ma_slow) / ma_slow
    # ratio > 0.02 满仓, -0.02~0.02 半仓, < -0.02 空仓

# 生成调仓信号
trading_days = close.index
mask = (trading_days >= start_date) & (trading_days <= end_date)
bt_days = trading_days[mask]
rebal_dates = bt_days[::rebal_freq]

signals = {}
for date in rebal_dates:
    if use_timing and ratio.get(date, 0) < -0.02:
        continue  # 空仓
    
    scores = composite.loc[date].dropna()
    # 过滤涨停（收益率>9.5%不可买入）
    daily_ret = close.pct_change()
    if date in daily_ret.index:
        limit_up = daily_ret.loc[date] > 0.095
        scores = scores[~scores.index.isin(limit_up[limit_up].index)]
    
    n = n_stocks if (not use_timing or ratio.get(date, 0) > 0.02) else n_stocks // 2
    top = scores.nlargest(n)
    # 按得分加权
    w = top / top.sum()
    signals[date] = w.to_dict()
```

### Step 4: 运行回测

```python
from alpha_agent.backtest.engine import BacktestEngine

# 基准
idx = index_data.copy()
idx["trade_date"] = pd.to_datetime(idx["trade_date"], format="%Y%m%d")
benchmark = idx.set_index("trade_date")["close"].sort_index()

engine = BacktestEngine(close, benchmark, cost_rate=cost_rate, risk_free=risk_free)
result = engine.run(signals)
```

### Step 5: 门控检查

```python
# 从配置读取门控阈值
gate = result.gate_check()
pref = result.preferred_check()
metrics = result.metrics()
```

### Step 6: IS/OOS对比

分别在IS和OOS区间运行回测，计算Sharpe衰减：
```python
is_signals = {d: s for d, s in signals.items() if d <= is_end}
oos_signals = {d: s for d, s in signals.items() if d >= oos_start}

is_result = engine.run(is_signals)
oos_result = engine.run(oos_signals)

from alpha_agent.backtest.result import BacktestResult
decay = BacktestResult.oos_sharpe_decay(is_result, oos_result)
```

### Step 7: 生成报告

```python
from alpha_agent.report.report import StrategyReport

report = StrategyReport(result, strategy_name="MultiFactorStrategy")
report.generate_full_report(save_path=os.path.join(OUTPUT_DIR, "backtest_report.png"))
```

### Step 8: 输出结果

```
📈 回测结果: <策略名称>

因子: <因子1>×权重 + <因子2>×权重 + ...
区间: YYYY-MM-DD ~ YYYY-MM-DD | 调仓: N日 | 持仓: N只

           IS期间      OOS期间     全区间
年化收益    xx.xx%      xx.xx%     xx.xx%
Sharpe     x.xxx       x.xxx      x.xxx
MaxDD      -xx.xx%     -xx.xx%    -xx.xx%
PF         x.xxx       x.xxx      x.xxx
月度胜率    xx.x%       xx.x%      xx.x%
Calmar     x.xxx       x.xxx      x.xxx

Sharpe衰减: xx.x% (IS→OOS)

门控检查:
  ✓/✗ Sharpe ≥ 1.0      → x.xxx
  ✓/✗ MaxDD ≥ -25%      → -xx.xx%
  ✓/✗ PF ≥ 1.0          → x.xxx
  ✓/✗ 月度胜率 ≥ 55%    → xx.x%
  ✓/✗ 最大连续亏损月 ≤ 4 → N个月

报告图表: output/backtest_report.png
```

## 注意事项

1. 多因子权重归一化：确保权重之和=1.0
2. 择时逻辑：空仓日不生成信号，BacktestEngine在无信号期间保持现金
3. 涨停过滤：A股涨幅>9.5%的股票无法买入
4. 如果因子需要daily_basic或fina数据但缺失，提示用户
5. 回测时间较长时告知用户"正在回测，预计1-2分钟..."
6. 门控阈值从 .claude/alpha-agent.config.md 读取
