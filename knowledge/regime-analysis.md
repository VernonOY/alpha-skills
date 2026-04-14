# Market Regime Analysis & Factor Adaptation
# 市场环境分析与因子适配

> How to identify market regimes, understand their impact on factor performance, and adapt factor strategies accordingly.
> 如何识别市场环境、理解环境对因子的影响、以及相应调整策略。

---

## 1. Regime Definitions / 环境定义

### Trend Regimes / 趋势环境

| Regime | Definition | Detection Method |
|--------|-----------|-----------------|
| **Bull 牛市** | MA20 > MA60, broad market rising > 20% from trough | MA crossover + drawdown < 10% from peak |
| **Bear 熊市** | MA20 < MA60, broad market falling > 20% from peak | MA crossover + drawdown > 20% |
| **Sideways 震荡** | No clear trend, range-bound ±10% | Low slope of MA60, ADX < 20 |
| **Recovery 修复** | Turning from bear to bull, first 3 months post-trough | MA20 crossing above MA60 after bear |
| **Distribution 派发** | Late bull, narrowing breadth, momentum divergence | Breadth declining while index rising |

### Volatility Regimes / 波动率环境

| Regime | Detection |
|--------|-----------|
| **Low-Vol 低波** | 20d realized vol < 25th percentile of 2-year history |
| **Normal-Vol 常态** | 25th-75th percentile |
| **High-Vol 高波** | > 75th percentile |
| **Crisis 危机** | > 95th percentile, or VIX > 30 (US), or implied vol spike |

### Style Regimes / 风格环境

| Regime | Detection |
|--------|-----------|
| **Value leadership 价值占优** | Value index outperforming Growth index over trailing 60d |
| **Growth leadership 成长占优** | Growth index outperforming Value index |
| **Small-cap leadership 小盘占优** | Small-cap index outperforming large-cap |
| **Large-cap leadership 大盘占优** | Opposite |

---

## 2. Quantitative Regime Detection / 量化环境识别

### Method A: Moving Average Crossover / 均线交叉

```python
def detect_trend_regime(benchmark_close, fast=20, slow=60):
    ma_fast = benchmark_close.rolling(fast).mean()
    ma_slow = benchmark_close.rolling(slow).mean()
    ratio = (ma_fast - ma_slow) / ma_slow
    
    regime = pd.Series("sideways", index=benchmark_close.index)
    regime[ratio > 0.03] = "bull"
    regime[ratio < -0.03] = "bear"
    return regime
```

Pros: simple, interpretable. Cons: lagging, frequent false signals in choppy markets.

### Method B: Volatility Percentile / 波动率百分位

```python
def detect_vol_regime(returns, window=20, lookback=504):
    vol = returns.rolling(window).std() * np.sqrt(252)
    pct = vol.rolling(lookback).rank(pct=True)
    
    regime = pd.Series("normal", index=returns.index)
    regime[pct < 0.25] = "low_vol"
    regime[pct > 0.75] = "high_vol"
    regime[pct > 0.95] = "crisis"
    return regime
```

### Method C: Market Breadth / 市场宽度

```python
def market_breadth(close_matrix):
    # % of stocks above their 20-day MA
    ma20 = close_matrix.rolling(20).mean()
    above = (close_matrix > ma20).mean(axis=1)
    # above > 0.7 = broad rally (bull)
    # above < 0.3 = broad decline (bear)
    return above
```

### Method D: Hidden Markov Model / 隐马尔可夫模型

More sophisticated — fits 2-3 hidden states (bull/bear/sideways) to return data using HMM. Requires `hmmlearn` library. Better at detecting regime transitions but prone to overfitting with too many states.

### Recommended: Composite Regime Score / 推荐：复合环境评分

Combine multiple signals for robustness:

```python
def composite_regime(benchmark_close, returns, close_matrix):
    trend = detect_trend_regime(benchmark_close)    # MA-based
    vol = detect_vol_regime(returns)                 # Vol-based
    breadth = market_breadth(close_matrix)           # Breadth-based
    
    # Map to numeric scores
    trend_score = trend.map({"bull": 1, "sideways": 0, "bear": -1})
    vol_score = vol.map({"low_vol": 0.5, "normal": 0, "high_vol": -0.5, "crisis": -1})
    breadth_score = (breadth - 0.5) * 2  # normalize to [-1, 1]
    
    composite = (trend_score + vol_score + breadth_score) / 3
    # composite > 0.3 → favorable, < -0.3 → adverse
    return composite
```

---

## 3. Factor Performance by Regime / 各因子的环境表现

### Trend Regime Impact / 趋势环境影响

| Factor | Bull 牛市 | Bear 熊市 | Sideways 震荡 |
|--------|----------|----------|-------------|
| **Momentum 动量** | ✅ Strong | ❌ Crashes | ⚠️ Noisy |
| **Reversal 反转** | ⚠️ Weak | ✅ Strong | ✅ Strong |
| **Low Volatility 低波动** | ⚠️ Underperforms | ✅ Defensive | ✅ Steady |
| **Value 价值** | ⚠️ Lags growth | ✅ Relative safety | ✅ Moderate |
| **Quality 质量** | ⚠️ Boring | ✅ Flight to quality | ✅ Steady |
| **Low Turnover 低换手** | ✅ Works | ✅ Works | ✅ Most stable |
| **PV Divergence 量价背离** | ✅ Works | ✅ Works | ✅ Works (most regime-robust) |

### Volatility Regime Impact / 波动率环境影响

| Factor | Low Vol 低波 | Normal 常态 | High Vol 高波 | Crisis 危机 |
|--------|-------------|------------|-------------|-----------|
| **Reversal** | ⚠️ Weak signals | ✅ Good | ✅ Strong | ✅ Very strong |
| **Momentum** | ✅ Trends clean | ✅ Good | ❌ Whipsaws | ❌ Crashes |
| **Low Vol** | ⚠️ No spread | ✅ Good | ✅ Outperforms | ✅ Best performer |
| **Value** | ⚠️ Slow | ✅ Moderate | ⚠️ Value traps | ❌ Forced selling |

### A-share Specific Regimes / A股特有环境

| Period | Regime | Best Factors | Worst Factors |
|--------|--------|-------------|---------------|
| 2014-2015 H1 | Leverage Bull 杠杆牛 | Momentum, Small-cap, High-beta | Low-vol, Value |
| 2015 H2 | Crash 股灾 | Reversal (post-crash), Low-vol | Momentum, Leverage |
| 2016-2017 | Blue-chip Rally 蓝筹行情 | Value, Quality, Large-cap | Small-cap, Growth |
| 2018 | Trade War Bear 贸易战熊市 | Low-vol, Reversal | Momentum, Growth |
| 2019-2021 H1 | Structure Bull 结构牛 | Growth, Quality, Momentum | Value (deep) |
| 2021 H2-2024 H1 | Bear/Sideways 熊市震荡 | Reversal, Low-turnover, PV-diverge | Momentum, Growth, Small-cap |
| 2024 H2-2025 | Recovery 修复 | Value, Low-vol, Quality | Extreme reversal |

---

## 4. Regime-Adaptive Strategy / 环境自适应策略

### Approach A: Regime-Conditional Factor Weights / 条件因子权重

```python
def adaptive_weights(regime, base_weights):
    """Adjust factor weights based on current regime"""
    adjustments = {
        "bull":     {"momentum": 1.5, "reversal": 0.5, "low_vol": 0.5, "value": 0.7},
        "bear":     {"momentum": 0.3, "reversal": 1.5, "low_vol": 1.5, "value": 1.0},
        "sideways": {"momentum": 0.5, "reversal": 1.2, "low_vol": 1.0, "value": 1.0},
    }
    
    adj = adjustments.get(regime, {})
    new_weights = {f: w * adj.get(f, 1.0) for f, w in base_weights.items()}
    total = sum(new_weights.values())
    return {f: w / total for f, w in new_weights.items()}
```

### Approach B: Regime-Based Position Sizing / 环境仓位管理

```python
def position_size(regime, vol_regime):
    """Determine overall position size based on regime"""
    if regime == "bear" and vol_regime == "crisis":
        return 0.0   # fully out
    elif regime == "bear":
        return 0.3   # defensive
    elif vol_regime == "high_vol":
        return 0.5   # reduced
    elif regime == "bull" and vol_regime == "low_vol":
        return 1.0   # full
    else:
        return 0.7   # normal
```

### Approach C: Regime-Switching Model / 环境切换模型

More sophisticated: maintain separate factor portfolios for each regime, switch between them based on detected regime. Risk: transition detection lag + whipsaws during uncertain periods.

---

## 5. Regime Transition Detection / 环境转换检测

### Leading Indicators / 领先指标

| Indicator | What It Signals | Lead Time |
|-----------|----------------|-----------|
| Yield curve inversion | Recession → bear market | 6-18 months (US) |
| Credit spreads widening | Risk-off → bear | 1-3 months |
| Market breadth divergence | Bull exhaustion → correction | 1-2 months |
| Volume climax | Capitulation → bottom | Days to weeks |
| VIX term structure inversion | Short-term fear spike | Days |
| PBOC rate cuts (A-share) | Policy easing → potential bottom | 1-3 months |
| Margin debt decline (A-share) | Deleverage risk | Concurrent |

### Transition Signals / 转换信号

**Bear → Bull transition（熊转牛）:**
- MA20 crosses above MA60 (confirmed)
- Market breadth > 0.6 sustained for 10+ days
- Volume expanding on up days
- Value factors stop bleeding

**Bull → Bear transition（牛转熊）:**
- MA20 crosses below MA60 (confirmed)
- Market breadth < 0.4 sustained
- New highs decreasing while index still near peak (divergence)
- Defensive factors (low-vol, quality) start outperforming

---

## 6. A-share Policy Regimes / A股政策环境

### Unique to A-share Market / A股特有

| Policy Event | Impact on Factors | Duration |
|-------------|------------------|----------|
| **PBOC easing 央行放水** | Positive for small-cap, growth, momentum | Months |
| **PBOC tightening 央行收紧** | Positive for value, quality, large-cap | Months |
| **National Team intervention 国家队入场** | Crushes short-term reversal (artificial floor) | Weeks |
| **IPO pace change IPO节奏变化** | Affects small-cap/new-stock factors | Months |
| **Stamp duty change 印花税调整** | Immediate volume/turnover factor impact | Permanent |
| **Short-selling restriction 限制做空** | Amplifies overvaluation, hurts value factors | Duration of restriction |
| **Margin call cascade 融资盘爆仓** | Extreme reversal opportunities | Days to weeks |

### How to Incorporate / 如何整合

Policy regime analysis cannot be fully automated — it requires judgment. The AI should:
1. Note when policy events coincide with factor performance changes
2. Flag known policy-sensitive periods in evaluation reports
3. Exclude policy-distorted periods from robustness tests (optional)
4. Adjust position sizing during known policy transition periods

---

## 7. Tail Risk Events / 尾部风险事件

### Historical Factor Crashes / 历史因子崩溃事件

| Event | Date | Most Affected Factor | IC Drop |
|-------|------|---------------------|---------|
| Quant Quake (US) | Aug 2007 | Momentum, Value | IC → -0.15 |
| GFC (Global) | 2008-2009 | Value, Momentum | Months of negative IC |
| A-share Crash 股灾 | Jun-Aug 2015 | All factors (liquidity freeze) | IC meaningless |
| A-share Crash 2.0 | Jan 2016 | Circuit breaker killed all signals | N/A |
| COVID Crash | Mar 2020 | Momentum reversed, low-vol outperformed | 2-3 weeks recovery |
| A-share Tech Crackdown | Jul 2021 | Growth, Momentum crashed | Months |
| SVB Crisis (US) | Mar 2023 | Value (bank exposure) | Weeks |

### Lessons / 教训

1. **Diversify across factor types** — no single factor survives all crises
2. **Position sizing > factor selection** during crises — reduce exposure first
3. **Reversal factors recover fastest** post-crisis — mean-reversion accelerates
4. **Momentum is the most fragile** factor during regime transitions
5. **Low-volatility is the best defensive** factor across all crises
6. **Factor correlations spike during crises** — diversification benefit disappears when you need it most

---

## 8. Practical Regime-Aware Workflow / 实用环境感知工作流

### For Factor Evaluation / 用于因子评估

1. Tag each date in your evaluation period with its regime
2. Report IC/ICIR separately per regime
3. Flag factors that only work in one regime as "regime-dependent"
4. Require positive IC in at least 2 out of 3 trend regimes for "robust" rating

### For Portfolio Construction / 用于组合构建

1. Detect current regime (composite method)
2. Adjust factor weights using regime-conditional table
3. Adjust position size using vol-regime
4. Monitor for regime transition signals
5. Re-evaluate factor weights quarterly or when regime changes

### For Factor Monitoring / 用于因子监控

1. When a factor's rolling IC drops, first check: did the regime change?
2. If IC dropped but regime didn't change → factor may be decaying
3. If IC dropped and regime changed → factor may recover when regime reverts
4. Include regime context in all monitoring alerts
