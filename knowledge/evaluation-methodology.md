# Factor Evaluation Methodology
# 因子评估方法论

> Reference guide for institutional-grade factor evaluation.
> 机构级因子评估参考指南。

---

## 1. Information Coefficient (IC) / 信息系数

### Definition / 定义
IC measures the cross-sectional rank correlation between factor values at time t and forward stock returns from t+1 to t+N.

IC = Spearman_rank_correlation(factor_t, return_{t+1:t+N})

### Interpretation / 解读

| IC Mean | Interpretation |
|---------|---------------|
| > 0.05 | Very strong signal — rare, check for data errors or look-ahead bias |
| 0.03 ~ 0.05 | Strong signal — publishable alpha |
| 0.02 ~ 0.03 | Moderate — useful in combination |
| 0.01 ~ 0.02 | Weak but potentially useful with low correlation to existing factors |
| < 0.01 | Noise — not worth pursuing |

### IC vs Rank IC
- **Pearson IC**: sensitive to outliers, measures linear relationship
- **Spearman IC (Rank IC)**: robust to outliers, measures monotonic relationship
- **Always use Rank IC** for factor evaluation — Pearson IC inflates significance for factors with extreme tails

### IC Stability Metrics
- **ICIR (IC Information Ratio)** = IC_mean / IC_std
  - The single most important metric for factor quality
  - ICIR > 0.5 → strong factor
  - ICIR > 0.3 → moderate factor
  - Analogous to Sharpe ratio but for information rather than returns
- **IC Hit Rate** = % of periods where IC > 0
  - > 55% for a long factor, < 45% for a short factor = meaningful directionality
- **IC Autocorrelation** = correlation between IC_t and IC_{t+1}
  - High autocorrelation → stable, predictable factor
  - Low or negative → noisy, regime-dependent

### IC Decay Analysis / IC衰减分析
- Compute IC at multiple forward horizons: 1d, 2d, 3d, 5d, 10d, 20d, 40d, 60d
- **Half-life**: the horizon at which IC drops to 50% of its peak
  - Short half-life (< 5d) → short-term alpha, high turnover required
  - Long half-life (> 20d) → stable alpha, suitable for lower-frequency strategies
- IC decay curve shape:
  - Monotonically decreasing → clean signal with clear optimal horizon
  - Hump-shaped (peaks at 5-10d) → factor needs time to realize but eventually decays
  - Flat → either very persistent alpha or just noise

---

## 2. Quintile Stratification / 分组分层

### Methodology / 方法
1. At each rebalance date, rank all stocks by factor value
2. Split into N groups (typically 5 = quintiles)
3. Compute equal-weight return for each group over the holding period
4. Accumulate over time → quintile cumulative return curves

### What to Look For / 关注要点

**Monotonicity / 单调性**
- Ideal: G1 < G2 < G3 < G4 < G5 (or reverse for inverse factors)
- Test: Spearman correlation between group rank and cumulative return
  - p-value < 0.05 → statistically significant monotonicity
- **Non-monotonic patterns**:
  - G1 and G5 both outperform middle → U-shaped, factor captures extremes not direction
  - G5 outperforms G1 but G2 > G3 → noisy middle, signal only at tails
  - Only G5 works, G1-G4 similar → factor is a tail screener, not a ranker

**Spread / 多空价差**
- Long-Short return = G5 - G1 (top minus bottom)
- Long-Short Sharpe = annualized L/S return / annualized L/S volatility
  - > 1.0 → excellent standalone factor
  - > 0.5 → useful in combination
  - < 0.3 → weak
- **Caveat**: L/S Sharpe can be inflated by daily rebalancing. Always report the rebalancing frequency.

**Turnover / 换手率**
- Factor turnover = % of stocks changing in top/bottom quintile each period
- High turnover (> 50% per period) → signal is noisy, transaction costs will eat alpha
- Low turnover (< 20%) → stable signal, practical for real portfolios
- **Turnover-adjusted ICIR**: multiply ICIR by (1 - turnover × cost_per_unit) for realistic assessment

---

## 3. Robustness Testing / 鲁棒性检验

### Parameter Sensitivity / 参数敏感性
- Perturb each parameter by ±10%, ±20%, ±30%
- Re-run evaluation at each perturbation
- **Pass**: ICIR changes by < 30% across all perturbations
- **Fail**: factor is parameter-fragile, likely overfitted to specific window size

### Time-Period Stability / 时间稳定性
- Split sample in half (first half vs second half)
- Compute ICIR for each half
- **Pass**: ratio of min(ICIR)/max(ICIR) > 0.5
- **Fail**: factor is regime-dependent or sample-period-specific
- Also test: rolling 3-year windows, report worst window ICIR

### Start-Date Sensitivity / 起始日敏感性
- Run evaluation starting from 5 different dates (e.g., Jan, Apr, Jul, Oct + random)
- **Pass**: ICIR standard deviation across runs < 0.3
- **Fail**: results depend on starting point → unstable

### Best-Month Removal / 剔除最佳月份
- Remove top 5 performing months from the long-short return series
- **Pass**: remaining return is still positive
- **Fail**: factor's entire alpha comes from a few outlier months → fragile

### Out-of-Sample Decay / 样本外衰减
- IS (in-sample): period used for factor design
- OOS (out-of-sample): holdout period, never seen during design
- Sharpe decay = (IS_Sharpe - OOS_Sharpe) / IS_Sharpe
  - < 20% → excellent generalization
  - 20-40% → acceptable
  - > 40% → likely overfitted
  - Negative (OOS > IS) → rare but possible, often indicates regime shift in factor's favor

---

## 4. Advanced Diagnostics / 高级诊断

### Industry Neutralization / 行业中性化
- Compute IC after regressing out industry dummies from factor values
- If IC drops to ~0 → factor is just an industry bet (e.g., "buy tech" disguised as a factor)
- Neutral IC should retain at least 50% of raw IC to be considered a true stock-level alpha

### Size Neutralization / 市值中性化
- Same as above but regress out log(market_cap)
- Small-cap bias is the most common false alpha source
- If factor only works in small caps → it may be capturing illiquidity premium, not alpha

### Factor Crowding / 因子拥挤
- Compute rolling correlation between your factor's L/S return and public factor indices
- ETF proxies: low-vol ETF, value ETF, momentum ETF
- Correlation > 0.7 → your factor is crowded, alpha will decay as capital enters
- Monitor trend: rising correlation = increasing crowding risk

### Regime Dependency / 环境依赖
- Tag each month with market regime (bull/bear/sideways, high-vol/low-vol)
- Compute IC separately per regime
- Report: "Factor works in bull markets (IC=0.05) but fails in bear markets (IC=-0.01)"
- This information is critical for portfolio construction and risk management

### Transaction Cost Analysis / 交易成本分析
- Compute "implementable ICIR" = ICIR after deducting estimated transaction costs
- Cost model: turnover × cost_per_unit
- If implementable ICIR < 0.2 → factor is not tradeable despite good raw statistics
- Different markets have very different cost structures (A-share 0.3%, US 0.1%)

---

## 5. Evaluation Report Template / 评估报告模板

A complete factor evaluation report should include:

1. **Factor Definition** — expression, economic intuition, data requirements
2. **IC Analysis** — mean, std, ICIR, hit rate, IC time series plot
3. **IC Decay** — decay curve across holding periods, half-life
4. **Quintile Returns** — cumulative return curves, monotonicity test
5. **Long-Short Performance** — NAV, Sharpe, MaxDD, Calmar
6. **Robustness** — parameter sensitivity, time stability, start-date sensitivity
7. **Neutralization** — industry-neutral IC, size-neutral IC
8. **Correlation with Library** — redundancy check against existing factors
9. **Turnover & Cost** — estimated implementable return
10. **Verdict** — Strong / Moderate / Weak, with clear reasoning

---

## 6. Common Pitfalls / 常见陷阱

### Look-Ahead Bias / 前视偏差
- Using data that wasn't available at factor computation time
- Most common: using financial report data on `end_date` instead of `ann_date`
- Also: using adjusted prices computed with future information
- **Detection**: run `qtype check` or manually inspect all `.shift()` calls

### Survivorship Bias / 幸存者偏差
- Only testing on stocks that exist today, ignoring delisted stocks
- Inflates factor returns by 1-3% annually depending on market
- **Fix**: include all stocks that were tradeable at each historical date

### Data Snooping / 数据窥探
- Testing hundreds of factor variants and reporting only the best one
- Multiple testing correction: if you tested N factors, the significance threshold should be α/N (Bonferroni)
- **Guard**: report how many factors were screened to find each "significant" one

### Overfitting Signals
- Factor only works in a specific time period
- Factor breaks when parameters change by 10%
- Factor has no economic intuition
- Factor's L/S return comes from < 5 outlier months
- Factor's turnover is so high that costs exceed alpha
