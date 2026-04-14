# Factor Taxonomy
# 因子分类学

> Complete classification of alpha factors with economic intuition, implementation patterns, and market-specific behavior.
> 完整的alpha因子分类，包含经济直觉、实现模式和市场特性。

---

## 1. Momentum / 动量因子

### Economic Intuition / 经济直觉
- **Behavioral**: investors underreact to new information → prices trend
- **Structural**: positive-feedback trading, herding, institutional slow rebalancing
- Winner stocks continue to win for 3-12 months (Jegadeesh & Titman, 1993)

### Variants / 变体

| Factor | Expression | Typical IC | Best for |
|--------|-----------|-----------|----------|
| Raw momentum (20d) | `close.pct_change(20)` | 0.01~0.03 | Short-term |
| Skip-1-month momentum | `close.shift(21).pct_change(240)` | 0.02~0.04 | Classic 12-1 |
| Residual momentum | Regression residual after removing market/industry | 0.02~0.05 | Pure alpha |
| Volume-weighted momentum | `(ret * volume).sum() / volume.sum()` | 0.01~0.03 | Conviction-weighted |
| Risk-adjusted momentum | `momentum / volatility` | 0.03~0.05 | Sharpe of price trend |

### Market-Specific Behavior / 市场特性
- **US**: classic momentum works well at 6-12 month horizons
- **A-share**: momentum is WEAK or REVERSED — short-term reversal dominates
  - IC often negative for 20-60 day momentum
  - Market structure (retail-dominated, T+1, price limits) creates mean-reversion
- **HK**: mixed — momentum in large caps, reversal in small caps

### Known Risks / 已知风险
- Momentum crashes: sharp reversals during market stress (2009 March)
- Crowding: most traded anomaly, alpha has decayed significantly since 2000s
- High turnover: 50-100% monthly, expensive to implement

---

## 2. Mean Reversion / Reversal / 反转因子

### Economic Intuition / 经济直觉
- **Behavioral**: overreaction to short-term news → prices revert
- **Structural**: market-maker inventory management, contrarian institutions
- Short-term (1-5 day) reversal is one of the strongest anomalies globally

### Variants / 变体

| Factor | Expression | Typical IC | Best for |
|--------|-----------|-----------|----------|
| Short-term reversal (5d) | `-close.pct_change(5)` | 0.03~0.06 | Intraweek |
| Medium reversal (20d) | `-close.pct_change(20)` | 0.01~0.03 | Monthly |
| RSI contrarian | `-(RSI - 50)` | 0.02~0.04 | Overbought/oversold |
| Bollinger reversion | `-(close - MA) / std` | 0.02~0.04 | Volatility-adjusted |
| Max drawdown reversion | `-(1 - close / close.rolling(20).max())` | 0.03~0.05 | Drawdown recovery |

### Market-Specific / 市场特性
- **A-share**: VERY STRONG — the dominant alpha source in Chinese equities
  - T+1 rule amplifies overreaction (can't exit same day)
  - ±10% price limits create pent-up demand/supply
  - IC for 5-day reversal: 0.04-0.08 in A-shares vs 0.01-0.03 in US
- **US**: weaker, mostly at 1-5 day horizon
- **HK**: moderate, similar to US

### Known Risks / 已知风险
- Very high turnover (weekly rebalance required)
- Catches falling knives — need stop-loss
- Decays with longer holding periods

---

## 3. Volatility / 波动率因子

### Economic Intuition / 经济直觉
- **Low-volatility anomaly**: low-vol stocks outperform high-vol on risk-adjusted basis
- **Behavioral**: investors overpay for "lottery" high-vol stocks
- **Structural**: institutional leverage constraints → preference for inherently volatile stocks
- Documented by Baker, Bradley & Wurgler (2011), Ang et al. (2006)

### Variants / 变体

| Factor | Expression | Typical IC |
|--------|-----------|-----------|
| Realized volatility | `-(ret.rolling(20).std())` | 0.03~0.06 |
| Downside volatility | `-(ret.clip(upper=0).rolling(20).std())` | 0.03~0.06 |
| Idiosyncratic volatility | `-(residual_vol after market regression)` | 0.04~0.07 |
| ATR ratio | `-(ATR / close)` | 0.03~0.06 |
| High-low range | `-((high-low)/close).rolling(20).mean()` | 0.03~0.05 |
| Beta (inverse) | `-beta_to_market` | 0.02~0.04 |

### Market-Specific / 市场特性
- **A-share**: strong low-vol effect, especially in bear markets
- **US**: documented for decades, partially eroded by crowding (low-vol ETFs)
- **Global**: one of the most robust anomalies across markets

### Known Risks / 已知风险
- Low-vol factor is inherently defensive — underperforms in strong bull markets
- Crowded since the launch of low-vol ETFs (SPLV, USMV)
- Can become concentrated in utilities/staples (sector bet in disguise)

---

## 4. Value / 估值因子

### Economic Intuition / 经济直觉
- **Fundamental**: cheap stocks offer higher expected returns as compensation for risk
- **Behavioral**: investors overweight growth stories, underweight boring cheap stocks
- One of the Fama-French factors (HML — High Minus Low book-to-market)

### Variants / 变体

| Factor | Expression | Typical IC |
|--------|-----------|-----------|
| Book-to-Price (1/PB) | `-pb` (negated, lower PB = better) | 0.01~0.03 |
| Earnings Yield (1/PE) | `-pe_ttm` | 0.01~0.02 |
| Dividend Yield | `dv_ttm` | 0.01~0.02 |
| FCF Yield | `fcf / market_cap` | 0.02~0.03 |
| EBITDA/EV | `ebitda / enterprise_value` | 0.02~0.04 |
| PEG (inverse) | `-pe / earnings_growth` | 0.01~0.02 |
| Composite value | `rank(1/PE) + rank(1/PB) + rank(DY)` | 0.02~0.03 |

### Market-Specific / 市场特性
- **A-share**: PB works better than PE (many companies manipulate earnings)
  - Value has been weak since 2016 (growth/tech dominance)
  - Dividend yield is meaningful due to large SOE universe
- **US**: classic HML factor, struggled 2017-2020, recovered 2021+
- **HK**: strong PB effect due to deep value in property/banking stocks

### Known Risks / 已知风险
- Value traps: cheap stocks that get cheaper (for good fundamental reasons)
- Regime-dependent: value underperformed for a decade (2010-2020)
- Needs fundamental quality filter to avoid distressed companies

---

## 5. Quality / 质量因子

### Economic Intuition / 经济直觉
- **Fundamental**: high-quality companies compound value more reliably
- **Behavioral**: market underprices stable, boring quality — focuses on exciting growth stories
- Quality as a factor: Asness, Frazzini & Pedersen (2013)

### Variants / 变体

| Factor | Expression | Typical IC |
|--------|-----------|-----------|
| ROE | `roe` (from financial statements) | 0.01~0.02 |
| ROA | `roa` | 0.01~0.02 |
| Gross Margin | `gross_margin` | 0.01~0.02 |
| Earnings Stability | `-std(earnings_growth, 8q)` | 0.01~0.03 |
| Accruals | `-(total_accruals / total_assets)` | 0.02~0.03 |
| Composite quality | `rank(ROE) + rank(margin) + rank(stability)` | 0.02~0.03 |

### Market-Specific / 市场特性
- **A-share**: quality IC is low but stable, works best as a filter (not a ranker)
  - Financial data quality issues: earnings manipulation common
  - Use ann_date alignment to avoid look-ahead bias
- **US**: moderate effect, enhanced when combined with value
- **Global**: defensive factor, outperforms in downturns

---

## 6. Volume / Liquidity / 成交量/流动性因子

### Economic Intuition / 经济直觉
- **Illiquidity premium**: less-traded stocks earn higher returns (compensation for liquidity risk)
- **Attention**: low-turnover stocks are neglected → mispriced → alpha opportunity
- Amihud (2002) illiquidity factor

### Variants / 变体

| Factor | Expression | Typical IC |
|--------|-----------|-----------|
| Low turnover | `-(turnover_rate.rolling(20).mean())` | 0.04~0.08 |
| Abnormal turnover | `-(short_turnover / long_turnover - 1)` | 0.03~0.06 |
| Amihud illiquidity | `abs(ret) / volume` | 0.03~0.05 |
| Volume trend | `volume.rolling(5).mean() / volume.rolling(60).mean()` | 0.02~0.04 |
| Price-Volume divergence | `-(ret.rolling(20).corr(vol_ret))` | 0.04~0.07 |

### Market-Specific / 市场特性
- **A-share**: EXTREMELY STRONG — low turnover is the #2 alpha source after reversal
  - Retail-dominated market: high turnover = retail speculation = negative alpha
  - IC for low turnover factor: 0.05-0.09, ICIR > 0.5
- **US**: moderate illiquidity premium, mostly in small caps
- **HK**: moderate, concentrated in small caps

### Known Risks / 已知风险
- Low-liquidity stocks are hard to trade (market impact, slippage)
- Factor alpha may not be capturable at scale
- Need minimum liquidity filters to avoid untradeable names

---

## 7. Price-Volume Interaction / 量价交互因子

### Economic Intuition / 经济直觉
- Price and volume carry different information
- Divergence between price trend and volume trend = potential reversal signal
- Volume precedes price (market microstructure theory)

### Variants / 变体

| Factor | Expression | Typical IC |
|--------|-----------|-----------|
| PV divergence | `-(ret.corr(vol_ret, 20))` | 0.04~0.07 |
| VWAP deviation | `-(close / vwap - 1)` | 0.02~0.04 |
| Volume-price trend | `corr(cumsum(ret), cumsum(vol_ret), 20)` | 0.02~0.05 |
| OBV slope | `OBV.rolling(20).apply(linregress_slope)` | 0.02~0.04 |

### Market-Specific / 市场特性
- **A-share**: PV divergence is the STRONGEST single factor (ICIR > 0.6)
  - Economic story: when price rises but volume declines, smart money is exiting
  - Retail investors chase price; institutions watch volume
- **US**: moderate, best at daily frequency
- **HK**: moderate

---

## 8. Technical / 技术面因子

### Variants / 变体

| Factor | Expression | Typical IC |
|--------|-----------|-----------|
| RSI contrarian | `-(RSI_14 - 50)` | 0.02~0.04 |
| MACD histogram | `(DIF - DEA) / close` | 0.01~0.03 |
| Bollinger position | `-((close-lower)/(upper-lower)*2-1)` | 0.02~0.04 |
| MA crossover | `MA5 / MA20 - 1` | 0.01~0.02 |

### Market-Specific / 市场特性
- **A-share**: moderate, technical factors work because retail traders use them (self-fulfilling)
- **US**: weak as standalone factors, slightly useful as timing signals
- Generally: technical factors are proxies for momentum or reversal

---

## 9. Fundamental Growth / 成长因子

### Variants / 变体

| Factor | Expression | Typical IC |
|--------|-----------|-----------|
| Earnings growth YoY | `netprofit_yoy` | 0.01~0.02 |
| Revenue growth YoY | `revenue_yoy` | 0.01~0.02 |
| Earnings acceleration | `this_quarter_growth - last_quarter_growth` | 0.01~0.02 |
| SUE (Standardized Unexpected Earnings) | `(actual - consensus) / std` | 0.03~0.05 |

### Market-Specific / 市场特性
- **A-share**: weak as ranking factors, strong as filters (require growth > 0)
- **US**: earnings surprise (SUE) is the strongest fundamental factor
- Growth factors need careful look-ahead bias prevention (use ann_date!)

---

## Factor Combination Principles / 因子组合原则

1. **Low correlation is key**: combining two IC=0.03 factors with corr=0.2 >> one IC=0.05 factor
2. **Rank-weighted combination**: `composite = w1*rank(f1) + w2*rank(f2) + ...`
3. **ICIR-weighted is optimal**: weight by ICIR if you have a track record
4. **Category diversification**: include at least one factor from each of momentum/value/quality/volume
5. **Watch for hidden correlations**: low-vol and quality are often highly correlated (~0.5)
6. **Incremental IC test**: after adding factor N, does the combined IC improve by > 5%? If not, it's redundant
