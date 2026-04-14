# Portfolio Construction: From Factors to Tradeable Portfolios
# 组合构建：从因子到可交易组合

> This document covers the complete methodology of translating factor signals
> into implementable portfolios, including weighting, constraints,
> optimization, risk attribution, and market-specific considerations.

---

## Table of Contents

1. [Weighting Schemes (权重方案)](#1-weighting-schemes-权重方案)
2. [Portfolio Constraints (组合约束)](#2-portfolio-constraints-组合约束)
3. [Transaction Cost Optimization (交易成本优化)](#3-transaction-cost-optimization-交易成本优化)
4. [Risk Attribution (风险归因)](#4-risk-attribution-风险归因)
5. [Rebalancing Frequency (调仓频率)](#5-rebalancing-frequency-调仓频率)
6. [Multi-Factor Weight Optimization (多因子权重优化)](#6-multi-factor-weight-optimization-多因子权重优化)
7. [Market-Specific Construction (各市场组合构建差异)](#7-market-specific-construction-各市场组合构建差异)

---

## 1. Weighting Schemes (权重方案)

### Comparison of Common Weighting Methods

| Method | Formula | Pros | Cons | Best For |
|--------|---------|------|------|----------|
| **Equal Weight (等权)** | w_i = 1/N | Simple; diversified across names; tilts toward small caps | High turnover from rebalancing; may overweight illiquid stocks; implicit small-cap bet | Factor research / paper portfolios; strategies where you want maximum factor exposure |
| **Market-Cap Weight (市值加权)** | w_i = MCap_i / ΣMCap | Low turnover; reflects investability; benchmark-aware | Concentrated in mega-caps; dilutes factor exposure; momentum-chasing | Tracking-error-constrained strategies; large AUM funds |
| **Factor-Score Weight (因子得分加权)** | w_i = score_i / Σ|score_i| | Proportional to conviction; stronger factor tilt | Sensitive to outliers; can concentrate in few stocks | Single-factor demonstration portfolios |
| **ICIR Weight (ICIR加权)** | w_factor_j = ICIR_j / Σ ICIR_j | Allocates more to predictive factors; adapts over time | Look-ahead risk if ICIR estimated on future data; needs rolling estimation | Multi-factor combination |
| **Minimum Variance (最小方差)** | min w'Σw s.t. Σw = 1 | Lowest portfolio volatility; robust to expected return estimation error | Concentrates in low-vol stocks; ignores expected returns; sensitive to covariance estimation | Risk-focused mandates; defensive portfolios |
| **Risk Parity (风险平价)** | RC_i = w_i × (Σw)_i / w'Σw = 1/N for all i | Equal risk contribution from each asset/factor; well-diversified risk budget | Ignores expected returns; requires leverage for competitive returns; complex optimization | Multi-asset allocation; factor allocation |
| **Mean-Variance Optimization (均值方差优化)** | max w'μ - (λ/2)w'Σw | Theoretically optimal; considers both return and risk | Extremely sensitive to expected return estimates ("error maximizer"); concentrates positions; requires robust inputs | Only with strong conviction on expected returns; always use with constraints and shrinkage |

### Detailed Method Notes

#### Equal Weight (等权)

```python
def equal_weight(signal: pd.Series, top_n: int = 100) -> pd.Series:
    """Select top N stocks by factor score, assign equal weight."""
    selected = signal.nlargest(top_n).index
    weights = pd.Series(1.0 / top_n, index=selected)
    return weights
```

- **Small-cap tilt**: Equal weighting overweights small stocks relative to cap-weighted. This can artificially inflate returns in backtests because small-cap premium is well-documented.
- **Mitigation**: Report both equal-weight and cap-weight results. If the factor only works in equal-weight, it may be a disguised small-cap bet.

#### Market-Cap Weight (市值加权)

```python
def cap_weight(signal: pd.Series, market_cap: pd.Series, top_n: int = 100) -> pd.Series:
    """Select top N stocks, weight by market cap."""
    selected = signal.nlargest(top_n).index
    caps = market_cap.loc[selected]
    weights = caps / caps.sum()
    return weights
```

- **Square-root cap weight**: A compromise between equal and cap weight. `w_i ∝ sqrt(MCap_i)`. Reduces mega-cap concentration while maintaining some size awareness.

#### Minimum Variance (最小方差)

The optimization problem:

```
minimize    w' Σ w
subject to  1' w = 1
            w ≥ 0  (long-only)
```

**Practical issues**:
- Covariance estimation: With N = 500 stocks and 250 trading days, the sample covariance matrix is singular. Solutions:
  - **Shrinkage** (Ledoit-Wolf): `Σ_shrunk = δ·F + (1-δ)·S` where F is a structured target (e.g., single-factor model) and S is the sample covariance.
  - **Factor model covariance**: Use Barra-style factor model to estimate Σ = BFB' + D, where B = factor loadings, F = factor covariance, D = diagonal specific risk.
  - **Sparse estimation**: Graphical Lasso for high-dimensional settings.
- The resulting portfolio will concentrate in low-volatility, low-beta stocks. This is a known factor tilt (低波动异象), not pure "risk minimization."

#### Risk Parity (风险平价)

Each position contributes equally to total portfolio risk:

```
Risk Contribution_i = w_i × (Σw)_i
Target: RC_i = Total Risk / N  for all i
```

This is a system of N nonlinear equations solved iteratively. For the special case of uncorrelated assets, risk parity reduces to inverse-volatility weighting: `w_i ∝ 1/σ_i`.

```python
def risk_parity_weights(cov_matrix: np.ndarray, tol: float = 1e-8, max_iter: int = 1000) -> np.ndarray:
    """Compute risk parity weights using the CCD algorithm (Griveau-Billion et al.)."""
    n = cov_matrix.shape[0]
    w = np.ones(n) / n  # initial equal weights
    
    for iteration in range(max_iter):
        for i in range(n):
            # Marginal risk contribution of asset i
            sigma_p = np.sqrt(w @ cov_matrix @ w)
            mrc_i = (cov_matrix @ w)[i] / sigma_p
            # Target risk contribution
            target_rc = sigma_p / n
            # Update weight
            w_new_i = target_rc / mrc_i
            w[i] = w_new_i
        
        # Normalize
        w = w / w.sum()
        
        # Check convergence
        sigma_p = np.sqrt(w @ cov_matrix @ w)
        rc = w * (cov_matrix @ w) / sigma_p
        if np.max(np.abs(rc - sigma_p / n)) < tol:
            break
    
    return w
```

#### Mean-Variance Optimization (均值方差优化)

```
maximize    w' μ  -  (λ/2) w' Σ w
subject to  1' w = 1
            w ≥ 0
            |w - w_bench| ≤ tracking_error_budget
```

**Critical**: Never use MVO with raw expected return estimates. Always:
1. **Shrink expected returns**: Use Black-Litterman or James-Stein shrinkage.
2. **Add regularization**: L1 (sparse) or L2 (ridge) penalty on weights.
3. **Use resampled efficiency** (Michaud): Generate many bootstrap samples, optimize each, average the weights.
4. **Constrain heavily**: Position limits, sector limits, turnover limits all help prevent extreme solutions.

---

## 2. Portfolio Constraints (组合约束)

### Standard Constraint Types

#### Industry / Sector Exposure Limits (行业暴露限制)

Purpose: Prevent the portfolio from taking unintended industry bets that could dominate factor returns.

| Constraint Type | Specification | Typical Value |
|----------------|---------------|---------------|
| **Absolute sector weight** | w_sector ≤ upper_bound | Each sector ≤ 15–25% |
| **Relative to benchmark** | \|w_sector - w_bench_sector\| ≤ δ | δ = 3–5% for low TE; 8–15% for higher TE |
| **Industry neutrality (行业中性)** | w_sector = w_bench_sector (exact) | Used in pure alpha strategies |

Industry classification systems:
- **A-shares**: CITIC (中信) 29/30 industries or Shenwan (申万) 31 industries. CITIC is standard for institutional quant.
- **HK / US**: GICS (Global Industry Classification Standard), 11 sectors / 24 industry groups / 69 industries / 158 sub-industries.

```python
# Example: CITIC industry neutral constraint
def industry_neutral_weights(signal, industry_map, benchmark_weights):
    """Adjust weights to match benchmark industry distribution."""
    result = pd.Series(0.0, index=signal.index)
    
    for ind in industry_map.unique():
        ind_mask = industry_map == ind
        bench_ind_weight = benchmark_weights[ind_mask].sum()
        
        # Within each industry, allocate proportional to signal
        ind_signal = signal[ind_mask]
        if ind_signal.sum() > 0:
            ind_weights = ind_signal / ind_signal.sum() * bench_ind_weight
        else:
            ind_weights = benchmark_weights[ind_mask]
        
        result[ind_mask] = ind_weights
    
    return result
```

#### Individual Stock Limits (个股上限)

| Constraint | Typical Range | Rationale |
|-----------|---------------|-----------|
| Maximum weight per stock | 2–5% (long-only); 1–3% (long-short) | Diversification; limit idiosyncratic risk |
| Minimum weight per stock | 0% (long-only); can be negative for L/S | Avoid tiny positions that aren't worth trading |
| Maximum ADV participation | 5–10% of 20-day ADV | Ensures executability |
| Minimum market cap | Top 70–80% of total market cap | Excludes micro-caps |

#### Turnover Limits (换手率上限)

| Constraint | Specification | Typical Value |
|-----------|---------------|---------------|
| One-way turnover per rebalance | Σ\|w_new - w_old\| / 2 | 10–30% for monthly; 5–15% for weekly |
| Annual turnover budget | 12 × monthly turnover | 100–400% (aggressive); 50–150% (moderate) |
| Turnover penalty in objective | Add λ_to × Σ\|w_new - w_old\| to cost function | λ_to calibrated to half-spread cost |

#### Number of Holdings (持仓数量)

| Strategy Type | Typical Holdings | Rationale |
|--------------|-----------------|-----------|
| Concentrated alpha | 30–50 | Maximum factor exposure; high idiosyncratic risk |
| Diversified factor | 100–200 | Good diversification; moderate factor dilution |
| Broad quant | 300–500 | Low idiosyncratic risk; factor exposure diluted |
| Index-enhanced (指数增强) | 200–500 | Close to benchmark; low tracking error |

**Practical guidance**: For A-share quant funds, 100–300 holdings is typical. Below 50 creates high volatility; above 500 starts to look like the index.

### Factor Exposure Constraints (因子暴露约束)

Beyond industry neutrality, control exposure to known risk factors:

```
|β_portfolio_factor - β_benchmark_factor| ≤ tolerance
```

Common factor exposures to constrain:
- **Size (市值)**: Prevent unintended small/large cap tilt
- **Beta (贝塔)**: Keep portfolio beta near 1.0 (or target level)
- **Value (价值)**: Prevent extreme value/growth tilt
- **Momentum (动量)**: Prevent unintended momentum exposure
- **Volatility (波动率)**: Prevent low-vol concentration from optimization

Tolerances typically: 0.1–0.3 standard deviations from benchmark.

---

## 3. Transaction Cost Optimization (交易成本优化)

### Turnover Control Methods

#### Method 1: Buffer Zone / No-Trade Region (缓冲区域)

The simplest and most effective method for reducing unnecessary turnover.

**Concept**: Only trade when the signal crosses a threshold. Stocks near the buy/sell boundary are kept to avoid round-trip costs on marginal positions.

```python
def buffer_zone_rebalance(
    current_holdings: set,
    signal: pd.Series,
    top_n: int = 100,
    buffer_n: int = 20  # buffer zone: rank top_n+buffer_n to retain
) -> set:
    """
    Rebalance with a buffer zone to reduce turnover.
    
    - New stocks enter only if ranked in top_n.
    - Existing stocks are sold only if ranked below top_n + buffer_n.
    """
    ranked = signal.rank(ascending=False)
    
    new_holdings = set()
    for stock in ranked.index:
        rank = ranked[stock]
        if rank <= top_n:
            # Definitely in
            new_holdings.add(stock)
        elif rank <= top_n + buffer_n and stock in current_holdings:
            # In buffer zone and currently held: keep
            new_holdings.add(stock)
    
    return new_holdings
```

**Typical buffer size**: 10–30% of portfolio size (e.g., top 100 + buffer of 20).

**Turnover reduction**: Typically 30–50% reduction in turnover with minimal impact on factor exposure.

#### Method 2: Proportional Trading (比例交易)

Instead of trading to the full target weight instantly, trade a fraction:

```
w_trade = w_current + λ × (w_target - w_current)
```

Where λ ∈ (0, 1] is the trading speed. Lower λ = slower adjustment = less turnover but slower signal capture.

**Typical values**: λ = 0.3–0.5 for daily signals; λ = 1.0 for monthly signals (full rebalance).

**Tradeoff**: This introduces signal lag. The optimal λ balances:
- Cost of delayed execution (signal decay) against
- Cost of immediate execution (market impact + commissions)

Grinold & Kahn formula for optimal trading rate:

```
λ* = 1 - exp(-2 × sqrt(cost_per_unit_traded / signal_variance))
```

#### Method 3: Turnover Penalty in Optimization (优化中的换手率惩罚)

Add a turnover cost to the objective function:

```
maximize    w' α  -  (λ_risk/2) w' Σ w  -  λ_cost × Σ c_i |w_i - w_i_old|
```

Where c_i is the estimated one-way trading cost for stock i.

This makes the optimizer internalize costs and naturally trade less in
expensive-to-trade stocks.

#### Method 4: Trade Scheduling (交易排程)

For large orders, split execution across multiple days or use TWAP/VWAP algorithms:

```python
def optimal_trade_schedule(
    target_shares: int,
    adv: int,
    urgency: float = 0.5,  # 0 = patient, 1 = urgent
    days: int = 5
) -> list:
    """
    Almgren-Chriss optimal execution schedule.
    Balances market impact (trade fast) vs. timing risk (trade slow).
    """
    participation_rate = target_shares / (adv * days)
    
    if participation_rate < 0.05:
        # Small order: execute immediately
        return [target_shares]
    
    # Simple linear schedule (full Almgren-Chriss uses exponential)
    kappa = urgency * 2  # risk aversion parameter
    schedule = []
    remaining = target_shares
    for day in range(days):
        # Front-load if urgent, spread evenly if patient
        frac = (1 + kappa * (days - day - 1)) / sum(1 + kappa * (days - j - 1) for j in range(days))
        trade = int(remaining * frac)
        schedule.append(trade)
        remaining -= trade
    
    schedule[-1] += remaining  # remainder
    return schedule
```

### Cost-Aware Signal Weighting

Instead of equal-weighting factor signals, weight by expected **net alpha** (alpha minus estimated trading cost):

```
net_alpha_i = gross_alpha_i - cost_i × expected_turnover_i
```

This naturally downweights stocks where the factor signal is strong but
trading costs would consume the edge (e.g., illiquid small caps).

---

## 4. Risk Attribution (风险归因)

### Factor-Based Risk Decomposition (因子风险分解)

Using a multi-factor risk model (e.g., Barra CNE6, Axioma), decompose
portfolio risk into:

```
Total Risk² = Factor Risk² + Specific Risk²

Factor Risk² = w' B F B' w
Specific Risk² = w' D w

where:
  w = portfolio weight vector (active weights if relative to benchmark)
  B = N × K factor loading matrix
  F = K × K factor covariance matrix
  D = N × N diagonal specific variance matrix
```

### Risk Attribution Table

| Component | Formula | Interpretation |
|-----------|---------|----------------|
| **Total active risk (跟踪误差)** | TE = sqrt(w_active' Σ w_active) | Annual tracking error vs. benchmark |
| **Factor contribution to risk** | For factor j: RC_j = w' B_j × Σ_row_j × B' w / TE² | % of TE explained by factor j |
| **Industry contribution** | Same as factor, using industry dummy loadings | % of TE from industry bets |
| **Stock-specific contribution** | Σ w_i² × σ_specific_i² / TE² | % of TE from idiosyncratic risk |
| **Marginal contribution to risk (MCTR)** | MCTR_i = (Σ w)_i / sqrt(w' Σ w) | How much adding $1 to stock i changes portfolio risk |

### Performance Attribution (业绩归因)

#### Brinson Attribution (Brinson归因)

For sector-level attribution relative to a benchmark:

```
Allocation Effect  = Σ_s (w_p_s - w_b_s) × (r_b_s - r_b)
Selection Effect   = Σ_s w_b_s × (r_p_s - r_b_s)
Interaction Effect = Σ_s (w_p_s - w_b_s) × (r_p_s - r_b_s)
Total Active Return = Allocation + Selection + Interaction
```

Where:
- w_p_s = portfolio weight in sector s
- w_b_s = benchmark weight in sector s
- r_p_s = portfolio return in sector s
- r_b_s = benchmark return in sector s
- r_b = total benchmark return

#### Factor-Based Performance Attribution

```
Active Return = Σ_j (β_p_j - β_b_j) × f_j  +  Σ_i w_active_i × ε_i

                ←── Factor return ──→          ←── Specific return ──→
```

**Practical output table**:

| Factor | Active Exposure | Factor Return | Contribution |
|--------|----------------|---------------|--------------|
| Size | −0.15 | +2.3% | −0.35% |
| Value | +0.42 | +1.8% | +0.76% |
| Momentum | +0.28 | −0.5% | −0.14% |
| Industry (Finance) | +3.2% | +4.1% | +0.13% |
| Specific | — | — | +1.85% |
| **Total Active** | | | **+2.25%** |

The goal is to have most of the active return coming from **intended factor
exposures** and **specific return** (stock selection), not from unintended
bets.

---

## 5. Rebalancing Frequency (调仓频率)

### Tradeoffs by Frequency

| Frequency | Pros | Cons | Best For |
|-----------|------|------|----------|
| **Daily (日频)** | Maximum signal freshness; captures short-term alpha | Very high turnover and costs; requires robust execution infrastructure; A-share T+1 limits flexibility | HFT-adjacent strategies; very short-term reversal or intraday signals |
| **Weekly (周频)** | Good signal freshness; moderate turnover | Higher costs than monthly; still substantial infrastructure needs | Short-term momentum; event-driven factors; sentiment factors |
| **Monthly (月频)** | Low turnover; simple execution; aligns with most fundamental data release cycles | Signal decay for fast factors; misses intra-month opportunities | Fundamental factors (value, quality, growth); most institutional factor strategies |
| **Quarterly (季频)** | Very low turnover; minimal costs | Significant signal staleness; large tracking error to ideal portfolio | Highly stable factors (deep value); capacity-constrained strategies |

### Optimal Frequency Selection

The optimal rebalance frequency depends on:

1. **Signal half-life (信号半衰期)**: How quickly the factor's predictive power decays after formation.
   - Measure: compute IC at lag 1, 2, 3, ..., 20 days. The lag where IC drops to 50% of peak IC is the half-life.
   - If half-life < 5 days → daily or weekly rebalance
   - If half-life 5–20 days → weekly
   - If half-life 20–60 days → monthly
   - If half-life > 60 days → monthly or quarterly

2. **Round-trip cost**: Higher costs → less frequent rebalancing.

3. **Implementation capacity**: Frequent rebalancing requires automated execution, real-time data, and operational readiness.

### Staggered Rebalancing (错峰调仓)

Instead of rebalancing the entire portfolio on one day (which creates concentrated market impact and timing risk), split the portfolio into sub-portfolios:

```python
def staggered_rebalance(
    portfolio_value: float,
    n_tranches: int = 5,  # 5 tranches for weekly stagger within monthly cycle
    rebalance_day: int = 0  # 0 = Monday
) -> dict:
    """
    Split portfolio into n_tranches, each rebalanced on a different day.
    
    Benefits:
    - Reduces market impact by spreading trades
    - Reduces timing risk (not all eggs on one rebalance date)
    - Smooths turnover over time
    
    Cost:
    - Slightly stale signals for later tranches
    - More complex tracking and reconciliation
    """
    tranche_value = portfolio_value / n_tranches
    schedule = {}
    for i in range(n_tranches):
        schedule[f"tranche_{i}"] = {
            "value": tranche_value,
            "rebalance_day": (rebalance_day + i) % 5  # Mon-Fri
        }
    return schedule
```

**Academic support**: Israelov and Katz (2023) show that staggering reduces implementation shortfall by 15–25% for typical factor portfolios.

### Calendar Effects (日历效应)

Certain rebalance dates interact with market anomalies:

| Effect | Description | Recommendation |
|--------|-------------|----------------|
| **Month-end rebalancing clustering** | Many funds rebalance on the last trading day → increased market impact | Rebalance on T−2 or T+2 relative to month-end |
| **Index rebalance dates** | CSI 300/500 rebalances in June and December → large flows | Avoid trading constituent changes on announcement day; front-run or delay |
| **Earnings season** | Most A-share companies report in April (annual), August (semi-annual) | Fundamental factor signals are freshest right after reporting season |
| **Window dressing (粉饰橱窗)** | Funds buy winners and sell losers at quarter-end for reporting | May temporarily distort momentum/reversal signals at quarter-end |

---

## 6. Multi-Factor Weight Optimization (多因子权重优化)

### Methods for Combining Multiple Factors

#### Method 1: Simple Composite (简单合成)

```python
def simple_composite(factor_scores: pd.DataFrame, weights: dict) -> pd.Series:
    """
    Weighted sum of z-scored factors.
    
    factor_scores: DataFrame with columns = factor names, index = stocks
    weights: dict of {factor_name: weight}
    """
    # Cross-sectional z-score each factor
    z_scores = factor_scores.apply(lambda x: (x - x.mean()) / x.std())
    
    # Weighted sum
    composite = sum(z_scores[f] * w for f, w in weights.items())
    
    return composite
```

**Common weight choices**:
- Equal weight: w_j = 1/K for all factors
- IC-based: w_j = IC_j (use rolling 12-month IC)
- ICIR-based: w_j = ICIR_j (IC / IC_std)
- IR-based: w_j = IR_j (information ratio of factor long-short portfolio)

#### Method 2: Sequential Sorting (序贯排序)

Sort first by Factor 1, then within each group by Factor 2, etc.

**Problem**: Order of sorting matters; first factor gets disproportionate influence. Not recommended except for simple demonstration.

#### Method 3: Conditional / Dependent Sorting (条件排序)

Within each quantile of Factor 1, sort by Factor 2. Creates a 2D grid. Can extend to 3D but becomes impractical beyond that.

**Use case**: Examining interaction effects between factors (e.g., "Does momentum work differently within value vs. growth stocks?").

#### Method 4: Cross-Sectional Regression (截面回归)

Fama-MacBeth style:

```
r_{i,t+1} = α_t + β_1 × f_{1,i,t} + β_2 × f_{2,i,t} + ... + ε_{i,t+1}
```

Run this cross-sectional regression at each time t. The time series of β coefficients gives factor risk premiums and their significance.

For portfolio construction, use the predicted return from the regression as the composite signal.

#### Method 5: Machine Learning (机器学习)

| Method | Strengths | Risks | Recommended Use |
|--------|-----------|-------|-----------------|
| **LASSO / Ridge regression** | Feature selection; handles multicollinearity; interpretable | Sensitive to regularization parameter; linear model | First ML method to try; use as baseline |
| **Random Forest / Gradient Boosting** | Captures nonlinear interactions; robust to outliers | Easy to overfit; non-interpretable; computationally expensive | When there's strong evidence of nonlinear factor interactions |
| **Neural Networks** | Maximum flexibility; can model complex patterns | Very high overfitting risk; black box; needs large data | Only with very large sample (10+ years, 3000+ stocks); always validate OOS |

**Critical warning**: ML methods require extreme discipline in cross-validation. Use purged k-fold CV with embargo (López de Prado, 2018) to prevent data leakage.

#### Method 6: Bayesian Shrinkage (贝叶斯收缩)

Combine prior beliefs about factor premiums with observed data:

```
w_posterior = (1/(σ²_prior) × w_prior + T/(σ²_data) × w_data) / (1/(σ²_prior) + T/(σ²_data))
```

**Practical approach**: Start with equal factor weights as the prior. As you accumulate out-of-sample data, let the posterior gradually adjust. This prevents wild swings in factor weights from period to period.

### Dynamic Factor Timing (动态因子择时)

Adjust factor weights based on current market conditions:

| Indicator | Factor Weight Adjustment | Evidence Strength |
|-----------|------------------------|-------------------|
| **Volatility regime** | ↓ Momentum, ↑ Quality in high-vol | Moderate (Daniel & Moskowitz, 2016) |
| **Credit spread** | ↑ Value when spread is wide (distress recovery) | Moderate |
| **Sentiment** | ↓ Growth, ↑ Value when sentiment is extreme | Moderate (Baker & Wurgler, 2006) |
| **Factor valuation** | ↑ Factor when its long-short valuation spread is extreme | Moderate (Arnott et al., 2019) |
| **Factor momentum** | ↑ Factor that has performed well recently | Strong (Ehsani & Linnainmaa, 2022) |

**Caution**: Factor timing is notoriously difficult. Most academic studies find modest improvement at best. Use with small allocation (e.g., 70% static + 30% dynamic).

---

## 7. Market-Specific Construction (各市场组合构建差异)

### A-Shares (A股)

#### Key Constraints

| Dimension | Constraint | Rationale |
|-----------|-----------|-----------|
| **Short selling (做空)** | Very limited. Only ~1,800 stocks on margin trading list. Securities lending (融券) is expensive and limited in supply. Stock index futures have position limits and basis risk. | Long-only strategies dominate. Long-short strategies must use index futures or limited stock shorting. |
| **T+1 settlement** | Cannot sell stocks bought today. | Daily rebalancing is constrained. Must plan buys 1 day ahead. Intraday reversal strategies are not possible with spot equities. |
| **Price limits (涨跌停)** | Main board: ±10%. ChiNext (创业板) / STAR (科创板): ±20%. ST stocks: ±5%. | Stocks hitting limits cannot be traded. Must exclude from rebalance or model fill probability. |
| **Minimum lot size** | 100 shares (1手). STAR Market allows 200-share minimum. | For small accounts, position sizing is quantized. May not be able to hold exactly the target weight. |
| **ST stock exclusion** | Most institutional mandates exclude ST/\*ST stocks. | Remove from universe at each rebalance. |
| **IPO exclusion** | New stocks exhibit extreme volatility in first N days. | Exclude stocks listed < 60–120 trading days. |
| **Suspension (停牌)** | Stocks can be suspended for days/weeks/months. | Must handle in portfolio: (1) cannot exit, weight drifts; (2) cannot enter. Use "tradeable universe" filter daily. |

#### Typical A-Share Factor Portfolio

```
Universe:        CSI All-Share (中证全指) ex ST, ex suspended, ex IPO < 60 days
Holdings:        100–300 stocks
Weighting:       Market-cap weighted or square-root cap weighted
Industry:        CITIC 1st level, neutral to CSI 500 or CSI 800
Size:            Neutral to benchmark ± 0.2 std
Rebalance:       Monthly (last trading day of month)
Turnover target: 15–25% one-way monthly
Cost budget:     0.25% round-trip per rebalance
Long-only:       Yes (or long + index futures hedge)
```

### Hong Kong (港股)

#### Key Constraints

| Dimension | Constraint | Rationale |
|-----------|-----------|-----------|
| **Short selling** | Available for designated securities (~900 stocks). Must borrow shares first. Uptick rule applies. | Long-short possible but universe is limited. |
| **No price limits** | Stocks can move ±100% in a day. Penny stocks (仙股) are especially volatile. | Need careful risk management. Wider stop-losses. |
| **T+0 settlement** | Can day-trade. Settlement is T+2. | More flexible than A-shares for short-term strategies. |
| **Board lots** | Vary by stock. Some large-cap: 100 shares. Some small-cap: 1,000 or 10,000 shares. | Check lot size; may be large in dollar terms for penny stocks. |
| **Stamp duty** | 0.13% both sides. Significant cost. | Reduces feasible turnover. Monthly rebalancing is typical. |
| **Low liquidity for many stocks** | Only ~200–300 stocks have ADV > HK$50M. Many small caps trade < HK$1M/day. | Liquidity filter is essential. Universe typically limited to HSI or HSCI constituents. |
| **Penny stock risk** | Stocks < HK$1 are common; susceptible to manipulation, share consolidation, and sudden delisting. | Exclude stocks below HK$1 (or HK$2 to be safe). |

#### Typical HK Factor Portfolio

```
Universe:        Hang Seng Composite Index (恒生综合指数) or top 500 by liquidity
                 Exclude price < HK$1, ADV < HK$10M
Holdings:        50–150 stocks
Weighting:       Cap-weighted or factor-score weighted
Industry:        GICS sector neutral to HSCI
Rebalance:       Monthly
Turnover target: 10–20% one-way monthly (higher cost → lower turnover)
Cost budget:     0.50% round-trip per rebalance
Long-short:      Possible with designated securities list; use H-share index futures for broad hedge
```

### US Equities (美股)

#### Key Constraints

| Dimension | Constraint | Rationale |
|-----------|-----------|-----------|
| **Short selling** | Widely available. Most stocks can be borrowed. Hard-to-borrow (HTB) names have elevated borrow costs (1–50% annualized). | Long-short strategies are standard. Monitor borrow availability and cost. |
| **T+0 (pattern day trader rules)** | Accounts < $25K have PDT restrictions. Institutional accounts: no restriction. | Not a practical constraint for institutional strategies. |
| **No price limits** | Market-wide circuit breakers at 7%, 13%, 20% (S&P 500 level). Individual stock halts via LULD (Limit Up-Limit Down). | Stocks can gap ±30%+ on earnings. Need tail risk management. |
| **Reg NMS** | Best execution requirement. Orders must be routed to the best available price across all venues. | Dark pools, internalization, and routing matter for execution quality. |
| **Decimalization** | Tick size = $0.01 for stocks > $1. SEC's tick size pilot (2016–2018) tested $0.05 ticks for small caps. | Very tight spreads for large caps; slightly wider for small caps. |
| **Tax considerations** | Wash sale rule: cannot claim a tax loss if you rebuy within 30 days. Long-term vs. short-term capital gains rates differ significantly. | Tax-loss harvesting is a strategy in itself. Holding period matters. |

#### Typical US Factor Portfolio

```
Universe:        Russell 1000 or S&P 500 (large cap); Russell 2000 (small cap)
                 Exclude ADC < $1M, price < $5
Holdings:        100–500 stocks (long); 100–500 (short) for L/S
Weighting:       Cap-weighted (long); factor-score weighted (L/S)
Industry:        GICS sector neutral to benchmark
Rebalance:       Monthly or weekly (low cost environment allows higher frequency)
Turnover target: 20–40% one-way monthly (long-only); 30–60% (L/S)
Cost budget:     0.05% round-trip per rebalance (large cap); 0.15% (small cap)
Long-short:      Standard. Typical gross exposure 150–200%. Net exposure 0–30%.
```

### Cross-Market Comparison Summary (跨市场对比总结)

| Dimension | A-Shares | Hong Kong | US |
|-----------|----------|-----------|-----|
| **Dominant strategy** | Long-only + futures hedge | Long-only or long-short | Long-short |
| **Typical turnover** | 15–25% monthly | 10–20% monthly | 20–40% monthly |
| **Cost per round-trip** | 0.22–0.65% | 0.40–1.00% | 0.02–0.25% |
| **Short selling ease** | Very difficult | Limited | Easy |
| **Price limits** | Yes (±10/20%) | No | Circuit breakers only |
| **Settlement** | T+1 | T+0 (settle T+2) | T+0 (settle T+1) |
| **Liquidity depth** | Good for top 2000 | Good for top 300 | Excellent for top 3000 |
| **Industry neutrality basis** | CITIC / Shenwan | GICS | GICS |
| **Risk model** | Barra CNE6 or custom | Barra GEM / APT | Barra USE4 / Axioma |
| **Capacity (typical factor strategy)** | ¥1–10B | HK$0.5–3B | $1–10B+ |

---

## Appendix: Portfolio Construction Workflow Checklist

### Step-by-Step Process

```
1. Define Universe (定义股票池)
   ├── Market and exchange filter
   ├── Liquidity filter (ADV, market cap)
   ├── Exclude: ST, suspended, IPO < 60d, penny stocks
   └── Verify point-in-time universe

2. Generate Factor Signals (生成因子信号)
   ├── Compute raw factor values (PIT data only)
   ├── Cross-sectional standardization (z-score or rank)
   ├── Winsorize outliers (±3σ or ±5 MAD)
   ├── Handle missing values (drop or fill within reason)
   └── Combine factors (composite score)

3. Construct Target Portfolio (构建目标组合)
   ├── Select weighting scheme
   ├── Apply constraints (industry, size, position limits)
   ├── Optimize (if using MVO, risk parity, etc.)
   └── Output: target weight vector

4. Generate Trades (生成交易)
   ├── Compare target vs. current portfolio
   ├── Apply turnover limits / buffer zone
   ├── Filter untradeable stocks (limit-up/down, suspended)
   ├── Estimate trade costs per stock
   └── Output: trade list with estimated costs

5. Execute (执行)
   ├── Split large orders (VWAP, TWAP, or IS algorithm)
   ├── Monitor fills and slippage
   └── Record implementation shortfall

6. Monitor and Attribute (监控与归因)
   ├── Daily P&L attribution (factor + specific)
   ├── Risk exposure monitoring
   ├── Turnover tracking vs. budget
   └── Factor decay detection
```
