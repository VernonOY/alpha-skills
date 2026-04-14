# Risk Management & Common Pitfalls in Quantitative Research
# 量化研究中的风险管理与常见陷阱

> This document catalogs the mistakes that separate amateur backtests from
> production-grade alpha research. Every item here has cost real money.

---

## Table of Contents

1. [Look-Ahead Bias (前视偏差)](#1-look-ahead-bias-前视偏差)
2. [Survivorship Bias (幸存者偏差)](#2-survivorship-bias-幸存者偏差)
3. [Overfitting & Data Snooping (过拟合与数据窥探)](#3-overfitting--data-snooping-过拟合与数据窥探)
4. [Transaction Cost Blindness (交易成本盲区)](#4-transaction-cost-blindness-交易成本盲区)
5. [Selection Bias & Publication Bias (选择偏差与发表偏差)](#5-selection-bias--publication-bias-选择偏差与发表偏差)
6. [Multiple Testing Correction (多重测试校正)](#6-multiple-testing-correction-多重测试校正)
7. [Backtest Pitfall Checklist (回测陷阱清单)](#7-backtest-pitfall-checklist-回测陷阱清单)
8. [Factor Decay (因子衰减)](#8-factor-decay-因子衰减)
9. [Live vs. Backtest Gap (实盘与回测差距)](#9-live-vs-backtest-gap-实盘与回测差距)

---

## 1. Look-Ahead Bias (前视偏差)

Look-ahead bias occurs when information that was **not available at the time
of the trading decision** leaks into the backtest. It is the single most
common cause of unreplicable backtest results.

### 10 Common Forms and Detection Methods

| # | Form | Example | Detection |
|---|------|---------|-----------|
| 1 | **Point-in-time violation on financial data (财务数据时间点错误)** | Using Q1 earnings filed on April 28 in a March 31 portfolio. A-share companies have up to 4 months to file annual reports. | Compare your signal date against the actual filing date (`公告日期`), not the reporting period end date (`报告期`). Build a PIT (point-in-time) database keyed on announcement date. |
| 2 | **Index constituent look-ahead (指数成分股前视)** | Using today's CSI 300 list to filter the universe in 2018. Constituents change quarterly. | Archive monthly constituent snapshots. Never use a single "current" list. |
| 3 | **Adjusted-price leakage (复权价格泄漏)** | Back-adjusted prices for splits/dividends use future adjustment factors. Using "forward-adjusted" prices means the most recent bar is correct but historical bars shift with every new corporate action. | Use **backward-adjusted** (后复权) prices for return calculation, or raw prices + separate adjustment factor table. Re-adjust from raw prices at each simulation date. |
| 4 | **Macro data revision (宏观数据修订)** | Using revised GDP figures that differ from the initial release. China's NBS routinely revises GDP, PMI, and industrial production by 0.1–0.5pp. | Source "first-release" (初值) vintages. FRED-MD and CEIC provide vintage data. |
| 5 | **Derived analytics computed on full sample (全样本衍生分析)** | Standardizing a factor using the full-sample mean and standard deviation, or fitting PCA on the entire time series. | Use **expanding-window** or **rolling-window** standardization. Never `z = (x - x.mean()) / x.std()` on the whole DataFrame at once. |
| 6 | **End-of-day price at signal time (收盘价作为信号时刻价格)** | Generating a signal at 14:50 but using the 15:00 close price that incorporates the closing auction. | If the signal is intraday, use the price at or before the signal timestamp. If using close-to-close returns, trade at the **next** open or VWAP. |
| 7 | **Settlement / ex-date confusion (结算日/除权日混淆)** | Dividends: the ex-date (除权日) and the record date (股权登记日) differ. Using returns that already strip out the dividend before the ex-date. | Align cash flow timing: dividend accrues on ex-date, not declaration date. |
| 8 | **Corporate event timing (公司事件时间)** | Using M&A, share buyback, or equity issuance data before the public announcement. Wind and CSMAR sometimes key on "event date" vs "announcement date". | Always key on the **first public disclosure date** (首次公告日). |
| 9 | **Analyst estimate vintage (分析师预测版本)** | Using "consensus EPS" that includes estimates submitted after portfolio formation. | Use only estimates with a timestamp ≤ signal date. I/B/E/S detail files provide individual estimate dates. |
| 10 | **Alternative data alignment (另类数据对齐)** | Satellite imagery processed on day T may reflect conditions on day T−3 due to cloud cover and processing lag. Sentiment scores from social media may be timestamped at publication but reflect after-hours information. | Map each alternative data source's **observation date**, **processing date**, and **availability date**. Use the availability date as the earliest valid signal date. Add a safety buffer (1–2 days). |

### Systematic Detection Strategy

```python
# Pseudo-code: detect look-ahead in factor values
# If future information leaks, factor values at time t will correlate
# with future returns more than they should after controlling for
# known predictability.

# Test 1: Check if factor values change when you re-run with a PIT database
factor_pit = compute_factor(pit_database, date=t)
factor_naive = compute_factor(current_database, date=t)
drift = (factor_pit - factor_naive).abs().mean()
# drift should be ~0. If drift > 0.01 * factor_std, you have look-ahead.

# Test 2: Verify no future returns in the factor
for lag in [-5, -4, -3, -2, -1]:  # negative = future
    ic = rank_ic(factor[t], returns[t + lag])
    # IC with future returns should be ~0. If |IC| > 0.03, investigate.
```

---

## 2. Survivorship Bias (幸存者偏差)

Survivorship bias inflates backtest returns because delisted stocks
(typically poor performers) are excluded from the historical universe.

### Quantified Impact by Market

| Market | Bias Source | Estimated Annual Return Inflation |
|--------|-----------|----------------------------------|
| **A-shares (A股)** | Delisting is rare (~30–50 per year out of 5000+); bias is smaller than US but growing. ST/\*ST stocks that eventually delist have extreme negative returns (−30% to −80%). | +0.5% to +1.5% per year on equal-weighted strategies |
| **Hong Kong (港股)** | Higher delisting rate; many small caps delist via privatization, voluntary withdrawal, or forced cancellation. Penny stocks (仙股) frequently delist. | +1.0% to +3.0% per year for small-cap strategies |
| **US Equities** | ~8% of listed companies delist annually. Delisted stocks average −40% in the 12 months before delisting (Shumway, 1997). | +1.0% to +2.5% per year on equal-weighted strategies; ~0.3% on cap-weighted |

### How to Handle Survivorship Bias

1. **Use a survivorship-bias-free database**: Wind (万得) point-in-time universe, CRSP (includes delisting returns), CSMAR (with delisted stocks flagged).

2. **Include delisting returns**: When a stock delists, assign a terminal return:
   - Merger/acquisition: use the acquisition price.
   - Forced delisting / bankruptcy: use the last traded price, then assume −100% or use the OTC recovery rate (typically 5–15 cents on the dollar for US; near zero for A-shares).
   - Voluntary privatization (HK): use the offer price.

3. **Reconstruct the historical universe at each rebalance date**: The stock universe at time *t* should be exactly the stocks that were tradeable on date *t*, including those that subsequently delisted.

4. **Test sensitivity**: Run the strategy with and without delisted stocks. If the Sharpe ratio drops by more than 0.2, the strategy may be exploiting survivorship bias.

### A-Share Specific: ST and Delisting (ST与退市)

China's ST system provides early warning:
- **ST** (Special Treatment): operating losses for 2 consecutive years → price limit narrows to ±5%
- **\*ST**: risk of delisting → price limit ±5%
- **Delisting consolidation period (退市整理期)**: 30 trading days, ±10% limit, then move to the OTC board (老三板/新三板)

For factor research, recommended handling:
- Exclude ST/\*ST stocks from the tradeable universe at each rebalance (most institutional strategies do this).
- If studying distress factors, keep them but use a separate analysis.

---

## 3. Overfitting & Data Snooping (过拟合与数据窥探)

### What Is Overfitting?

Overfitting occurs when a model or strategy captures noise rather than signal
in historical data, resulting in poor out-of-sample performance. In
quantitative finance, the most dangerous form is **researcher degrees of
freedom (研究者自由度)**: the ability to make hundreds of small decisions
(parameter choices, universe filters, rebalance dates) that collectively
"tune" the result to look good.

### How to Diagnose Overfitting

| Diagnostic | Method | Red Flag |
|-----------|--------|----------|
| **In-sample vs. out-of-sample Sharpe gap** | Split data 60/40 temporally. | OOS Sharpe < 50% of IS Sharpe |
| **Parameter sensitivity (参数敏感性)** | Vary each parameter ±20%. | Performance changes > 30% |
| **Strategy complexity vs. improvement** | Count free parameters. | Sharpe improves < 0.05 per added parameter |
| **Turnover check** | Unusually high turnover suggests fitting to short-term noise. | Monthly turnover > 100% for a "monthly" strategy |
| **Performance by sub-period** | Split in-sample into 3 sub-periods. | Sharpe varies > 2× across sub-periods |
| **Bootstrap reality check** | White's (2000) or Hansen's (2005) SPA test. | p-value > 0.10 |

### The Probability of Overfitting

From López de Prado (2018), the **Probability of Backtest Overfitting (PBO)** framework:

Given *N* backtested strategy configurations:
- With N = 100 trials and true Sharpe = 0, the expected maximum in-sample Sharpe ≈ 3.3
- With N = 1,000 trials: expected max IS Sharpe ≈ 4.0
- With N = 10,000 trials: expected max IS Sharpe ≈ 4.5

**Rule of thumb**: If you tried K configurations and report only the best one, your effective significance level is not 5% but approximately `1 - (1 - 0.05)^K`. With K = 50 trials, the probability of at least one false discovery at 5% level is 92%.

### Prevention Strategies

1. **Pre-registration (预注册)**: Write down the hypothesis, universe, parameters, and evaluation criteria **before** looking at any results. This is the single most effective defense.

2. **Combinatorially Symmetric Cross-Validation (CSCV)**: López de Prado's method partitions the backtest into S sub-periods and evaluates all `C(S, S/2)` train/test splits to estimate PBO.

3. **Embargo periods**: When using walk-forward or cross-validation, add an embargo (gap) between training and test periods to prevent autocorrelation leakage. Typical embargo: 5–20 trading days for daily strategies.

4. **Economic rationale first**: If you cannot write a 1-paragraph explanation of **why** a factor should work (behavioral, structural, or risk-based), discard it regardless of statistical significance.

5. **Deflated Sharpe Ratio**: Adjust the observed Sharpe ratio for the number of trials, skewness, and kurtosis:

```
SR* = (SR_observed - SR_benchmark) / sqrt((1 - γ₃·SR + ((γ₄-1)/4)·SR²) / T)
```

where γ₃ = skewness, γ₄ = kurtosis, T = number of observations.

6. **Minimum Backtest Length (MBL)**: The minimum number of years needed to statistically distinguish a strategy's Sharpe from zero:

```
MBL ≈ (1 + (γ₄ - 1)/4 · SR² - γ₃ · SR)  × (z_α / SR)²  years
```

For SR = 0.5, MBL ≈ 16 years at 95% confidence. For SR = 1.0, MBL ≈ 4 years.

---

## 4. Transaction Cost Blindness (交易成本盲区)

A strategy that looks profitable before costs is worthless if costs consume
the edge. This is especially dangerous for high-turnover, small-cap, or
short-selling strategies.

### Realistic Transaction Cost Models by Market

#### A-Shares (A股)

| Cost Component | Buy | Sell | Notes |
|---------------|-----|------|-------|
| Broker commission (佣金) | 0.02%–0.03% | 0.02%–0.03% | Institutional rate; retail may be 0.03%–0.05%. Minimum ¥5 per trade for retail. |
| Stamp tax (印花税) | 0 | 0.05% | Reduced from 0.1% to 0.05% in Aug 2023. Sell-side only. |
| Transfer fee (过户费) | 0.001% | 0.001% | Both exchanges (previously Shanghai only). |
| Slippage (滑点) | 0.05%–0.20% | 0.05%–0.20% | Depends on liquidity, order size, and urgency. Small/mid cap: 0.10%–0.30%. |
| Market impact (冲击成本) | 0.05%–0.50% | 0.05%–0.50% | Function of ADV participation rate. |
| **Total one-way (typical)** | **0.10%–0.30%** | **0.12%–0.35%** | |
| **Total round-trip** | | | **0.22%–0.65%** |

#### Hong Kong (港股)

| Cost Component | Buy | Sell | Notes |
|---------------|-----|------|-------|
| Broker commission | 0.03%–0.10% | 0.03%–0.10% | Varies widely; online brokers may offer 0.03%. |
| Stamp duty (印花税) | 0.13% | 0.13% | Both sides. Raised from 0.10% to 0.13% in Aug 2021. |
| Transaction levy (交易征费) | 0.00565% | 0.00565% | SFC levy. |
| Trading fee (交易费) | 0.00050% | 0.00050% | HKEX fee. |
| CCASS settlement (中央结算) | 0.002%–0.005% | 0.002%–0.005% | Min HK$2, max HK$100. |
| Slippage | 0.05%–0.30% | 0.05%–0.30% | Wider spreads than A-shares for most stocks. |
| **Total round-trip** | | | **0.40%–1.00%** |

#### US Equities (美股)

| Cost Component | Buy | Sell | Notes |
|---------------|-----|------|-------|
| Broker commission | $0–$0.005/share | $0–$0.005/share | Zero-commission for retail; institutional: $0.001–$0.005/share. |
| SEC fee | 0 | $27.80 per $1M | Sell-side only. Adjusted periodically. |
| TAF fee | $0.000166/share | $0.000166/share | Max $8.30 per trade. |
| Exchange fees/rebates | −$0.002 to +$0.003/share | −$0.002 to +$0.003/share | Maker-taker model; varies by venue. |
| Slippage | 0.01%–0.10% | 0.01%–0.10% | Highly liquid large caps: 0.01%; small caps: 0.10%+. |
| **Total round-trip** | | | **0.02%–0.25%** (large cap: ~0.05%) |

### Market Impact Models

**Square-Root Model** (Almgren et al., 2005): The most widely used model for estimating market impact.

```
Impact = σ × k × sqrt(Q / V)
```

Where:
- σ = daily volatility
- k = constant (typically 0.5–1.5, calibrated to market)
- Q = order quantity (shares)
- V = average daily volume (shares)
- Q/V = participation rate (参与率)

**Practical thresholds**:
- Participation rate < 5%: minimal impact
- 5%–10%: moderate impact (~10–30 bps for A-shares)
- 10%–25%: significant impact, consider splitting across days
- \>25%: dangerous; may not be executable at reasonable cost

### Cost-Aware Strategy Design

1. **Pre-cost hurdle**: Require gross alpha > 2× estimated round-trip cost × annual turnover.
2. **Net-of-cost IC**: Compute IC on net returns (after subtracting estimated trade cost from each rebalance).
3. **Capacity estimation**: `Capacity ≈ k × ADV_median / participation_rate_max`. If strategy capacity < target AUM, rethink the universe or turnover.

---

## 5. Selection Bias & Publication Bias (选择偏差与发表偏差)

### The Problem

Researchers (including you) naturally:
- Report the best-performing variant of a strategy
- Choose the evaluation window that looks best
- Stop testing a strategy when results are bad (and continue when good)
- Publish factors that "work" and file away those that don't

This creates a systematic upward bias in reported performance.

### Quantified Impact

Harvey, Liu, and Zhu (2016) — "... and the Cross-Section of Expected Returns":
- Over 300 factors have been published in top finance journals.
- The required t-statistic for a "new" factor should be **3.0**, not the traditional 2.0, to account for the collective data mining across the profession.
- Many published factors fail to replicate out-of-sample. McLean and Pontiff (2016) found that post-publication, factor returns decline by 32% on average, and 58% after accounting for statistical bias.

### Mitigation

1. **Report all tested variants**: Include a table of all parameter combinations and factor definitions you tried, not just the winner.

2. **Pre-specify the evaluation protocol**: Fix the metric (IC, Sharpe, quintile spread), the evaluation period, and the benchmark before running any test.

3. **Out-of-sample mandate**: Reserve at least 20% of the most recent data as a strict holdout. Never look at it until the final evaluation.

4. **Cross-market validation (跨市场验证)**: If a factor works in A-shares, test it in HK and US (or at least in a different A-share sub-period). Genuine risk premia should exist across markets; data-mined artifacts typically don't.

5. **Decay analysis**: Track factor performance in rolling 1-year windows. A genuine factor may weaken but should not suddenly disappear at a specific date that coincides with a parameter choice boundary.

---

## 6. Multiple Testing Correction (多重测试校正)

When you test multiple hypotheses, the probability of finding at least one
false positive increases dramatically.

### Methods

#### Bonferroni Correction (邦费罗尼校正)

The simplest and most conservative method.

- Adjusted significance level: `α* = α / m` where m = number of tests.
- If you test 100 factors at α = 5%, the corrected threshold is α* = 0.05%.
- Equivalent t-stat threshold: from ~2.0 to ~3.9.

**Pros**: Simple, no assumptions about test dependence.
**Cons**: Very conservative. With m = 100, many true factors will be missed (high Type II error / 第二类错误).

#### Holm-Bonferroni (Step-Down)

Less conservative than Bonferroni while still controlling FWER.

1. Sort p-values: p₁ ≤ p₂ ≤ ... ≤ pₘ
2. Find the smallest k where pₖ > α / (m - k + 1)
3. Reject H₁, ..., Hₖ₋₁

#### Benjamini-Hochberg FDR (BH-FDR, 假发现率控制)

Controls the **False Discovery Rate** (the expected proportion of false
discoveries among all discoveries) rather than the Family-Wise Error Rate.

1. Sort p-values: p₍₁₎ ≤ p₍₂₎ ≤ ... ≤ p₍ₘ₎
2. Find the largest k where p₍ₖ₎ ≤ (k/m) × q, where q is the desired FDR level (e.g., 0.05).
3. Reject all hypotheses H₍₁₎, ..., H₍ₖ₎.

**This is the recommended default for factor research.** It balances discovery power with false positive control.

```python
from scipy import stats
import numpy as np

def bh_fdr(p_values, q=0.05):
    """Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: array of raw p-values from factor tests
        q: desired FDR level (default 5%)
    
    Returns:
        rejected: boolean array, True = significant after correction
        adjusted_p: adjusted p-values
    """
    m = len(p_values)
    sorted_idx = np.argsort(p_values)
    sorted_p = p_values[sorted_idx]
    
    # BH critical values
    bh_critical = np.arange(1, m + 1) / m * q
    
    # Find the largest k where p_(k) <= (k/m) * q
    candidates = np.where(sorted_p <= bh_critical)[0]
    if len(candidates) == 0:
        return np.zeros(m, dtype=bool), np.ones(m)
    
    k_max = candidates[-1]
    
    rejected = np.zeros(m, dtype=bool)
    rejected[sorted_idx[:k_max + 1]] = True
    
    # Adjusted p-values (Benjamini-Hochberg)
    adjusted_p = np.minimum(1, sorted_p * m / np.arange(1, m + 1))
    # Enforce monotonicity
    for i in range(m - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])
    
    result_p = np.empty(m)
    result_p[sorted_idx] = adjusted_p
    
    return rejected, result_p
```

#### Storey's q-value (Storey q值)

An improvement over BH that estimates the proportion of true nulls (π₀) from the data, giving higher power.

#### Practical Recommendation

| Scenario | Method | Rationale |
|----------|--------|-----------|
| Testing a single pre-specified factor | No correction needed | One test, one hypothesis. |
| Testing 5–10 related factors (e.g., variants of momentum) | Holm-Bonferroni | Small m, want strict FWER control. |
| Screening 50–200 candidate factors | BH-FDR at q = 5% | Good balance of power and control. |
| Mining 1,000+ factors (automated alpha mining) | BH-FDR at q = 1% or Storey q-value | High m requires strict control; consider PBO as well. |

### The Harvey-Liu-Zhu (HLZ) Framework

For the cross-section of expected returns, Harvey et al. (2016) propose:

- Required t-stat ≈ 3.0 for single-sorted factors (accounting for ~300 published factors)
- This corresponds to a Bonferroni-adjusted p-value of ~0.003
- For factors based on accounting data: t > 2.78
- For factors based on market data: t > 3.39 (more tests have been run)

---

## 7. Backtest Pitfall Checklist (回测陷阱清单)

Use this checklist before trusting any backtest result. A single "Yes" answer
is a potential invalidation.

### Data Issues (数据问题)

| # | Pitfall | Check |
|---|---------|-------|
| 1 | **Survivorship bias in universe** — Are delisted stocks included? | Verify delisted stocks appear in the historical universe. Count them per year. |
| 2 | **Look-ahead in financial data** — Are financials aligned to announcement dates? | Compare signal dates against filing dates for a sample of 20 stocks. |
| 3 | **Price adjustment errors** — Are splits, dividends, and rights issues correctly handled? | Check 5 known corporate actions manually. Verify adjusted prices match a reference source. |
| 4 | **Missing data handling** — How are NaN/missing values treated? | Forward-filling is OK for prices (up to a limit); filling with zero for returns is dangerous. Check how many NaNs exist per factor per date. |
| 5 | **Data vendor errors** — Are there outliers from bad data? | Screen for returns > ±50% in a single day, prices of 0 or negative, and volume spikes > 50× median. |

### Signal Construction (信号构建)

| # | Pitfall | Check |
|---|---------|-------|
| 6 | **Full-sample normalization** — Is the factor standardized using future data? | Ensure all transformations (z-score, rank, winsorize) use only data available at signal time. |
| 7 | **Indicator parameter snooping** — Were parameters optimized on the test period? | Document all parameter choices. Run sensitivity analysis ±20%. |
| 8 | **Regime-specific factor** — Does the factor only work in one market regime? | Test in bull, bear, and sideways sub-periods separately. |

### Execution (执行)

| # | Pitfall | Check |
|---|---------|-------|
| 9 | **Unrealistic execution prices** — Can you actually trade at the backtest price? | Use next-day open or VWAP, not same-day close. For A-shares, remember the close is determined by a call auction. |
| 10 | **Zero transaction costs** — Were costs ignored or underestimated? | Apply realistic costs (see Section 4). Compare gross and net Sharpe. |
| 11 | **Unlimited short-selling** — Does the strategy require shorting stocks that cannot be shorted? | For A-shares: only ~1,800 stocks are on the margin trading list (融资融券标的). For HK: check the designated short-selling list. |
| 12 | **No liquidity filter** — Are illiquid stocks included? | Require minimum ADV (e.g., ¥10M for A-shares, HK$5M for HK, $1M for US). Exclude stocks in the bottom 10% of liquidity. |
| 13 | **Ignoring limit-up/limit-down (涨跌停)** — Does the backtest trade at limit prices? | For A-shares: if a stock hits ±10% (±20% for ChiNext/STAR), it may be untradeable. Exclude stocks at limit from the rebalance. |

### Statistical (统计)

| # | Pitfall | Check |
|---|---------|-------|
| 14 | **Insufficient history** — Is the backtest too short? | Use the MBL formula. For SR = 1.0, need ≥ 4 years; for SR = 0.5, need ≥ 16 years. |
| 15 | **Single-period evaluation** — Was performance evaluated in only one window? | Use rolling-window Sharpe ratios (e.g., 1-year rolling) and examine the distribution. |
| 16 | **Ignoring drawdown duration** — Was max drawdown reported without recovery time? | Report max drawdown, drawdown duration, and Calmar ratio. A 20% drawdown lasting 2 years is very different from one lasting 2 months. |
| 17 | **Cherry-picked benchmark** — Was the benchmark chosen to make the strategy look good? | Use the most relevant market index (CSI 300 for large cap A, CSI 500 for mid cap, HSI for HK, S&P 500 for US large). |
| 18 | **Ignoring tail risk** — Are returns normally distributed? | Report skewness, kurtosis, and worst 5 daily/monthly returns. Many strategies have negative skew (赚小亏大). |

### Structural (结构)

| # | Pitfall | Check |
|---|---------|-------|
| 19 | **Capacity ignorance** — Can the strategy absorb meaningful capital? | Estimate capacity. If ADV participation > 10%, the strategy may not scale. |
| 20 | **Correlated signals** — Is the "new" factor just a repackaging of known factors? | Regress against Fama-French factors + momentum. If alpha disappears, the factor is redundant. |

---

## 8. Factor Decay (因子衰减)

Factor decay (因子衰减/alpha衰减) is the reduction in a factor's predictive
power over time. It is not optional to monitor — every factor will eventually
decay.

### Common Causes

| Cause | Mechanism | Time Scale |
|-------|-----------|------------|
| **Crowding (拥挤交易)** | Too many investors trade the same signal, compressing the spread between long and short portfolios. | Months to years after publication/adoption. |
| **Market microstructure changes** | Tick size reduction, HFT proliferation, exchange reforms change the environment the factor relied on. | Event-driven, can be abrupt. |
| **Regulatory changes (监管变化)** | New rules (e.g., A-share short-selling expansion, HK stamp duty change, US Reg NMS) alter the playing field. | Event-driven. |
| **Data availability (数据普及)** | Alternative data that was once exclusive becomes widely available (e.g., satellite data, web scraping). | 1–3 years after data vendor launches. |
| **Structural economic shifts** | The risk premium or behavioral bias that the factor exploits diminishes (e.g., improved corporate governance reduces the value premium). | Decades. |
| **Regime change** | A factor designed for one market regime (e.g., low interest rates) loses effectiveness when the regime shifts. | Varies. |

### Detection Methods

1. **Rolling IC / ICIR**: Compute IC in 12-month rolling windows. A sustained decline below |IC| < 0.02 for 6+ months is a warning.

2. **Cumulative IC curve**: Plot the cumulative sum of daily/monthly IC. A flattening or reversal indicates decay.

3. **Quintile spread time series**: Track the long-short return spread monthly. Use a structural break test (Chow test, CUSUM) to detect regime changes.

4. **Factor return half-life**: Fit an exponential decay model to the post-signal cumulative return. If the half-life shortens over time, the factor is decaying.

5. **Crowding indicators**:
   - Short interest concentration on the short leg
   - Correlation increase among factor-aligned stocks
   - Factor valuation spread compression (for value-type factors)
   - AUM tracking the factor via ETFs or smart beta products

6. **Out-of-sample monitoring**: Compare the most recent 12 months' IC/Sharpe to the long-run average. Use a one-sided test: is recent performance significantly **below** the historical mean?

### Response to Decay

| Decay Level | Signal | Action |
|-------------|--------|--------|
| **Minor**: IC dropped 20% from peak | Rolling 12M IC still above threshold | Monitor. No action. |
| **Moderate**: IC dropped 50%; ICIR < 1.5 | Rolling IC near zero for 3+ months | Reduce weight in multi-factor model. Investigate cause. |
| **Severe**: IC negative; quintile spread inverted | Factor is broken | Remove from production. Investigate if this is temporary (regime-driven) or permanent (structural). |

---

## 9. Live vs. Backtest Gap (实盘与回测差距)

### Sources of Gap

| Source | Typical Magnitude | Direction |
|--------|-------------------|-----------|
| **Transaction costs** | 50–200 bps/year | Hurts live |
| **Slippage and market impact** | 20–100 bps/year | Hurts live |
| **Execution delay (执行延迟)** | 10–50 bps/year | Hurts live (signal stale by execution time) |
| **Data timing differences** | 10–30 bps/year | Can go either way |
| **Look-ahead bias in backtest** | 50–300 bps/year | Inflates backtest |
| **Fill rate < 100%** | 10–50 bps/year | Hurts live (limit orders may not fill; limit-up/down stocks not tradeable) |
| **Cash drag (现金拖累)** | 5–20 bps/year | Hurts live (uninvested cash) |
| **Corporate action handling** | 5–20 bps/year | Can go either way |
| **Short borrow cost** | 50–400 bps/year for hard-to-borrow | Hurts live (backtest often ignores borrow cost) |
| **Total typical gap** | **150–600 bps/year** | **Live underperforms backtest** |

### Minimizing the Gap

1. **Use realistic execution assumptions in backtest**:
   - Trade at T+1 open or VWAP, not T close.
   - Apply the full cost model from Section 4.
   - Implement a fill probability model: if a stock hits limit-up, assume 0% fill on buys.

2. **Paper trading (模拟盘) validation**:
   - Run the strategy live with no real capital for at least 3–6 months.
   - Compare paper trading results to concurrent backtest predictions.
   - The gap in this period is your best estimate of the structural gap.

3. **Implementation shortfall analysis**:
   - Track every trade: target price (from signal), decision price (when order sent), execution price (actual fill).
   - Decompose: `Shortfall = (execution price - target price) = delay cost + market impact + timing cost`.

4. **Gradual capital deployment**:
   - Start at 10–20% of target AUM.
   - Scale up over 3–6 months as the live-backtest gap is understood.
   - Budget for the gap: if backtest Sharpe is 2.0 and expected gap is 30%, target live Sharpe of 1.4.

5. **A-share specific considerations**:
   - T+1 settlement means you cannot sell stocks bought today. The backtest must enforce this.
   - Closing auction (收盘集合竞价) determines the close price. If your signal uses the close, you must submit orders during the auction (14:57–15:00), which has limited liquidity.
   - Order size limits: single order ≤ 100 lots (10,000 shares) on some brokers; split large orders.

---

## Appendix: Quick Reference Card

### Red Flags in a Backtest Report (回测报告危险信号)

- [ ] Sharpe > 3.0 with daily rebalancing → almost certainly overfitted
- [ ] No transaction costs mentioned → results are meaningless
- [ ] Backtest starts at a convenient date → may be cherry-picked
- [ ] Only one evaluation metric reported → hiding weaknesses
- [ ] No drawdown analysis → ignoring tail risk
- [ ] "Proprietary data" without description → unverifiable
- [ ] Factor works only in small caps → may be illiquidity premium, not alpha
- [ ] No comparison to known factors → may be redundant
- [ ] Parameter values are "round numbers" (5, 10, 20) but not explained → likely tuned

### The 5-Minute Sniff Test

Before spending hours on a factor, ask:

1. **Why does this work?** (Economic rationale — 经济逻辑)
2. **Is this already known?** (Literature search — 文献检索)
3. **Can I trade this?** (Liquidity, costs, short constraints — 可交易性)
4. **Is the data clean?** (PIT, survivorship-free — 数据质量)
5. **How many things did I try to find this?** (Multiple testing — 多重测试)

If any answer is unsatisfactory, stop. Don't waste time on detailed backtesting.
