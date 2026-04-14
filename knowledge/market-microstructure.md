# Market Microstructure: Trading Rules and Their Impact on Factor Research
# 市场微观结构：交易规则及其对因子研究的影响

> Understanding the plumbing of each market is essential for realistic backtesting
> and live strategy implementation. This document covers the trading mechanics
> of A-shares, Hong Kong, and US equities, with specific attention to how these
> mechanics affect quantitative factor research.

---

## Table of Contents

1. [Trading System Comparison (交易制度对比)](#1-trading-system-comparison-交易制度对比)
2. [Price Limits and Their Impact (涨跌停板的影响)](#2-price-limits-and-their-impact-涨跌停板的影响)
3. [T+1 vs T+0: Impact on Short-Term Factors (T+1与T+0对短期因子的影响)](#3-t1-vs-t0-impact-on-short-term-factors)
4. [Transaction Costs: Accurate Numbers and Modeling (交易成本建模)](#4-transaction-costs-accurate-numbers-and-modeling-交易成本建模)
5. [Short Selling and Margin Trading (融资融券与做空限制)](#5-short-selling-and-margin-trading-融资融券与做空限制)
6. [Delisting and ST System (退市与ST制度)](#6-delisting-and-st-system-退市与st制度)
7. [IPO Effects on Factors (新股对因子的影响)](#7-ipo-effects-on-factors-新股对因子的影响)
8. [Auction Mechanisms (集合竞价与连续竞价)](#8-auction-mechanisms-集合竞价与连续竞价)
9. [Market Participant Structure (市场参与者结构)](#9-market-participant-structure-市场参与者结构)
10. [Data Quality Issues (数据质量问题)](#10-data-quality-issues-数据质量问题)

---

## 1. Trading System Comparison (交易制度对比)

### Comprehensive Comparison Table

| Feature | A-Shares (A股) | Hong Kong (港股) | US Equities (美股) |
|---------|----------------|-----------------|-------------------|
| **Exchanges** | Shanghai (SSE, 上交所), Shenzhen (SZSE, 深交所), Beijing (BSE, 北交所) | Hong Kong Exchanges (HKEX, 港交所) | NYSE, NASDAQ, CBOE, IEX, + ~13 other exchanges and ~30 dark pools |
| **Trading hours** | 09:30–11:30, 13:00–15:00 (4 hours) | 09:30–12:00, 13:00–16:00 (5.5 hours) | 09:30–16:00 ET (6.5 hours); pre-market 04:00–09:30; after-hours 16:00–20:00 |
| **Pre-open auction** | 09:15–09:25 (open auction); 09:25–09:30 (order acceptance, no cancellation) | 09:00–09:30 (pre-opening session); random close between 09:22–09:30 | Varies by exchange; NYSE has opening auction starting 06:30 |
| **Closing auction** | 14:57–15:00 (closing call auction, SSE & SZSE) | 16:00–16:08 (closing auction session); random close 16:08–16:10 | NYSE has closing auction (MOC/LOC orders, cutoff 15:50); NASDAQ has closing cross |
| **Settlement cycle** | T+1 (cannot sell shares bought today) | T+0 trading; T+2 settlement | T+0 trading; T+1 settlement (changed from T+2 in May 2024) |
| **Price limits (涨跌停)** | Main board: ±10%; ChiNext/STAR: ±20%; ST: ±5%; IPO first day: ±44% (main board) or no limit (ChiNext/STAR for first 5 days) | None (but has volatility control mechanism VCM for HSI/HSCEI constituents: 5-minute cooling off if ±10% from last close) | No price limits; market-wide circuit breakers at S&P 500 ±7%, ±13%, ±20%; individual stock LULD bands (±5–20% depending on tier) |
| **Tick size (最小报价单位)** | ¥0.01 | HK$0.01–HK$0.50 depending on price level (9 spread groups) | $0.01 for stocks > $1.00; $0.0001 for stocks < $1.00 |
| **Board lot (最小交易单位)** | 100 shares (1手); STAR allows 200 shares minimum | Varies by stock: 100, 200, 400, 500, 1000, 2000, etc. Odd lot trading available but at wider spreads | 1 share (no lot size requirement); round lots of 100 shares for market-making purposes |
| **Order types** | Limit, market (limited availability), IOC | Limit, enhanced limit, special limit, market, at-auction, at-auction limit | Limit, market, stop, stop-limit, MOC, LOC, IOC, FOK, midpoint peg, and many more |
| **Short selling (卖空)** | Limited to margin trading list (~1,800 stocks); securities lending through brokers and CSFC | Designated securities only (~900 stocks); uptick rule applies; naked short selling prohibited | Generally available for most stocks; Reg SHO locate requirement; no uptick rule since 2007 (reinstated as alternative uptick rule in 2010) |
| **Margin trading (融资融券)** | Available for approved stocks; maintenance margin 130%; max leverage ~2× | Initial margin 25–50% depending on stock; maintenance margin 25%; max leverage ~4× for blue chips | Initial margin 50% (Reg T); maintenance margin 25% (FINRA); portfolio margin allows 6–7× for diversified portfolios |
| **Currency** | RMB (CNY) | HKD (pegged to USD; some stocks trade in RMB/CNH) | USD |
| **Index futures** | IF (CSI 300), IH (SSE 50), IC (CSI 500), IM (CSI 1000) | HSI futures, HSCEI futures, Hang Seng Tech futures | S&P 500 (ES), NASDAQ 100 (NQ), Russell 2000 (RTY), Dow (YM), single stock futures (limited) |
| **Options** | SSE 50 ETF options, CSI 300 ETF options, CSI 300 index options, CSI 1000 index options; individual stock options starting in 2024 | Index options (HSI, HSCEI); stock options for ~100 stocks | Extensive: index options, ETF options, individual stock options for ~5000 stocks; weekly/monthly/quarterly/LEAPS |
| **Market maker (做市商)** | No formal market maker system for main board; STAR/ChiNext have competitive market maker system | Designated market makers for some stocks; but most liquidity from limit order book | NYSE DMMs (Designated Market Makers); NASDAQ market makers; competing market makers across venues |

---

## 2. Price Limits and Their Impact (涨跌停板的影响)

### A-Share Price Limit Rules (A股涨跌停规则)

| Board | Up Limit | Down Limit | IPO First Day | IPO First 5 Days |
|-------|----------|------------|---------------|------------------|
| Main Board (主板) | +10% | −10% | +44% / −36% | Normal ±10% from day 2 |
| ChiNext (创业板) | +20% | −20% | No limit | No limit |
| STAR Market (科创板) | +20% | −20% | No limit | No limit |
| ST / \*ST | +5% | −5% | +5% / −5% | +5% / −5% |
| BSE (北交所) | +30% | −30% | No limit for first day | Normal ±30% from day 2 |

Note: Limit prices are calculated based on the previous closing price, rounded to ¥0.01.

### Impact on Factor Research

#### Problem 1: Untradeable Returns (不可交易的收益)

When a stock hits limit-up (涨停), buy orders cannot be filled because there are no sellers. When a stock hits limit-down (跌停), sell orders cannot be filled.

**Impact on backtest**: If the backtest assumes you can buy a stock at limit-up price, the backtest return is upward-biased because in reality you couldn't buy it.

**Solution**:
```python
def is_at_limit(close, prev_close, limit_pct=0.10, tolerance=0.001):
    """Check if a stock is at its price limit."""
    up_limit = prev_close * (1 + limit_pct)
    down_limit = prev_close * (1 - limit_pct)
    
    at_limit_up = abs(close - up_limit) / prev_close < tolerance
    at_limit_down = abs(close - down_limit) / prev_close < tolerance
    
    return at_limit_up, at_limit_down

# In backtest: exclude stocks at limit from rebalancing
tradeable = ~at_limit_up & ~at_limit_down
# Also check: if high == low == limit price, definitely untradeable
one_price_day = (high == low)  # strong signal of limit lock
```

#### Problem 2: Truncated Return Distribution (截断的收益分布)

Price limits create censored returns: you never observe what the "true" return would have been beyond ±10%.

**Impact on factors**:
- **Volatility factors**: Underestimate true volatility for stocks that frequently hit limits.
- **Momentum factors**: Returns are artificially bounded; extreme momentum is unobservable.
- **Reversal factors**: Limit-down stocks may continue falling the next day (serial limit-down, 连续跌停); the reversal signal is delayed.

**Quantified effect**: Kim and Rhee (1997) find that A-share stocks hitting limits show continuation the next day in ~60% of cases (vs. 50% random), suggesting the limit prevented price discovery.

#### Problem 3: Magnet Effect (磁吸效应)

Prices tend to accelerate toward the limit as they approach it, because traders rush to trade before the stock becomes untradeable.

**Impact**: Intraday momentum strategies may capture artificial momentum near limits.

#### Problem 4: Asymmetric Information (信息不对称)

Limit-up stocks often have queues of unfilled buy orders. The queue position contains information: stocks with larger unfilled buy queues at limit-up tend to continue rising.

**Factor idea**: `Unfilled volume at limit / ADV` as a short-term signal. But this requires order book data.

### Recommended Handling in Backtest

```python
class LimitPriceHandler:
    """Handle price limits in A-share backtest."""
    
    def __init__(self, limit_map: dict):
        """
        limit_map: {board_type: limit_pct}
        e.g., {'main': 0.10, 'chinext': 0.20, 'star': 0.20, 'st': 0.05}
        """
        self.limit_map = limit_map
    
    def filter_tradeable(self, close, prev_close, board_type, high, low):
        """
        Returns boolean mask: True = tradeable.
        
        Rules:
        1. If close == limit_up and high == low: locked limit-up, cannot buy
        2. If close == limit_down and high == low: locked limit-down, cannot sell
        3. If close == limit_up but high > low: touched limit but traded, partially tradeable
        """
        limit_pct = self.limit_map.get(board_type, 0.10)
        up_limit = np.round(prev_close * (1 + limit_pct), 2)
        down_limit = np.round(prev_close * (1 - limit_pct), 2)
        
        locked_up = (close >= up_limit) & (high == low)
        locked_down = (close <= down_limit) & (high == low)
        
        # Can buy if not locked limit-up
        can_buy = ~locked_up
        # Can sell if not locked limit-down
        can_sell = ~locked_down
        
        return can_buy, can_sell
```

---

## 3. T+1 vs T+0: Impact on Short-Term Factors

### T+1 Constraints in A-Shares

The T+1 rule means shares purchased today cannot be sold until the next trading day. This has profound implications:

#### Impact 1: Intraday Reversal Strategies Are Impossible

In US/HK markets, intraday mean reversion (buy dips, sell rallies within the same day) is a major source of HFT alpha. In A-shares, this is not possible with spot equities.

**Workaround**: Use ETFs that allow T+0 trading (e.g., certain cross-border ETFs, money market ETFs). Some quant funds use "revolving position" (底仓轮动): maintain a base position and trade around it, but this requires double capital.

#### Impact 2: Overnight Risk Is Mandatory

Any position taken today must be held overnight. This means:
- Overnight gap risk cannot be avoided
- Factors that predict intraday returns are less useful because you bear overnight noise
- The information ratio of short-term signals is reduced because overnight volatility adds noise

**Quantified impact**: Overnight return volatility in A-shares is approximately 60% of total daily volatility (vs. ~30% for US large caps), making the T+1 penalty particularly severe.

#### Impact 3: Short-Term Momentum/Reversal Factor Design

- **1-day reversal** (classic: buy yesterday's losers, sell yesterday's winners) works differently under T+1:
  - You buy at today's open and must hold until tomorrow's open at minimum.
  - The effective holding period is 1 day, not intraday.
  - This is more of a 2-day return pattern than a true reversal.

- **Intraday factors** (e.g., volume profile, intraday momentum) can inform next-day signals but cannot be directly traded intraday.

#### Impact 4: Execution Timing Matters More

Under T+1, if you make a wrong buy decision in the morning, you cannot cut the loss until tomorrow. This amplifies the cost of signal errors.

**Best practice**: For short-term strategies in A-shares, prefer to generate signals at or after the close, then execute the next morning. This avoids forced overnight holds on stale signals.

### T+0 Markets (HK and US)

In T+0 markets, short-term factor strategies benefit from:
- Ability to cut losses intraday
- Intraday mean reversion strategies
- Pairs trading with same-day entry and exit
- Scalping around factor signals

However, T+0 also means:
- Pattern day trader (PDT) rules in US for accounts < $25K
- Higher operational complexity
- More susceptible to HFT competition on short-term signals

---

## 4. Transaction Costs: Accurate Numbers and Modeling (交易成本建模)

### A-Shares (A股) — Detailed Cost Breakdown

| Component | Rate | Applied To | Notes |
|-----------|------|-----------|-------|
| **Stamp duty (印花税)** | 0.05% | Sell side only | Reduced from 0.1% in Aug 2023. Applies to turnover amount. |
| **Broker commission (佣金)** | 0.02%–0.03% (institutional) | Both sides | Minimum ¥5 per trade for retail accounts. Institutional: negotiable, often 0.015%–0.025%. Includes exchange fees. |
| **Transfer fee (过户费)** | 0.001% | Both sides | Charged by CSDC (中国结算). Unified for SSE and SZSE since 2022. |
| **Exchange levy (经手费)** | 0.00341% (SSE) / 0.00341% (SZSE) | Both sides | Included in broker commission for most accounts. |
| **CSRC levy (证管费)** | 0.002% | Both sides | Regulatory fee, included in broker commission. |

**Total explicit cost (one-way)**:
- Buy: 0.02%–0.03% (commission) + 0.001% (transfer) ≈ **0.021%–0.031%**
- Sell: 0.02%–0.03% (commission) + 0.001% (transfer) + 0.05% (stamp) ≈ **0.071%–0.081%**
- **Round-trip explicit: ~0.09%–0.11%**

**Implicit costs (slippage + market impact)**:
- Large caps (沪深300): 0.03%–0.10% per side
- Mid caps (中证500): 0.05%–0.20% per side
- Small caps (中证1000/2000): 0.10%–0.50% per side

### Hong Kong (港股) — Detailed Cost Breakdown

| Component | Rate | Applied To | Notes |
|-----------|------|-----------|-------|
| **Stamp duty (印花税)** | 0.13% | Both sides | Increased from 0.10% in Aug 2021. Rounded up to nearest HK$1. |
| **SFC transaction levy (证监会交易征费)** | 0.00565% | Both sides | Securities and Futures Commission levy. |
| **HKEX trading fee (交易费)** | 0.00050% | Both sides | Stock Exchange fee. |
| **AFRC transaction levy** | 0.00015% | Both sides | Accounting and Financial Reporting Council levy (effective Oct 2022). |
| **CCASS settlement fee (中央结算费)** | 0.002%–0.005% | Both sides | Min HK$2, max HK$100 per side per stock. |
| **Broker commission** | 0.03%–0.10% | Both sides | Online brokers (e.g., Futu, Tiger): 0.03%. Full-service: 0.10%+. Min HK$0–HK$100 depending on broker. |

**Total explicit cost (one-way)**:
- Per side: 0.13% (stamp) + 0.03%–0.10% (commission) + ~0.01% (levies) ≈ **0.17%–0.24%**
- **Round-trip explicit: ~0.34%–0.48%**

**Implicit costs**: Generally wider than A-shares due to lower liquidity.
- Blue chips (HSI constituents): 0.05%–0.15% per side
- Mid caps: 0.10%–0.40% per side
- Small caps: 0.30%–1.00%+ per side

### US Equities (美股) — Detailed Cost Breakdown

| Component | Rate | Applied To | Notes |
|-----------|------|-----------|-------|
| **SEC fee** | $27.80 per $1M (as of 2024, adjusted annually) | Sell side only | ~0.00278% |
| **TAF fee (FINRA)** | $0.000166 per share | Both sides | Max $8.30 per trade. ~0.001% for a $10 stock. |
| **Exchange fees / rebates** | −$0.0035 to +$0.0030 per share | Depends on order type and venue | Maker-taker model: limit orders adding liquidity receive rebates; market orders removing liquidity pay fees. Inverted venues (IEX, EDGA) pay for adding. |
| **Broker commission** | $0 (retail) to $0.005/share (institutional) | Both sides | Zero-commission for retail (PFOF model). DMA/institutional: $0.001–$0.005/share. |

**Total explicit cost (one-way)**:
- Retail: ~$0 + SEC/TAF ≈ **~0.003%** per side
- Institutional DMA: $0.002/share + SEC/TAF ≈ **0.01%–0.03%** per side
- **Round-trip explicit: ~0.01%–0.06%**

**Implicit costs**:
- Mega caps (top 50): 0.01%–0.03% per side (extremely tight spreads)
- Large caps (S&P 500): 0.02%–0.05% per side
- Mid caps (S&P 400): 0.05%–0.15% per side
- Small caps (Russell 2000): 0.10%–0.30% per side
- Micro caps: 0.30%–1.00%+ per side

### Market Impact Model (冲击成本模型)

The industry standard is the **square-root model**:

```
Temporary Impact = η × σ_daily × (Q / ADV)^0.5
Permanent Impact = γ × σ_daily × (Q / ADV)^0.5

Total Impact = Temporary + Permanent

Where:
  η = temporary impact coefficient (typically 0.1–0.5)
  γ = permanent impact coefficient (typically 0.05–0.2)
  σ_daily = daily return volatility
  Q = order size (shares or dollars)
  ADV = average daily volume (20-day)
  Q/ADV = participation rate (参与率)
```

**Calibrated parameters by market**:

| Market | η (temporary) | γ (permanent) | Data Source |
|--------|--------------|---------------|-------------|
| A-shares (large cap) | 0.20–0.35 | 0.05–0.15 | Empirical estimates from institutional brokers |
| A-shares (mid/small cap) | 0.35–0.60 | 0.10–0.25 | Higher due to lower liquidity |
| HK (blue chip) | 0.25–0.40 | 0.08–0.18 | Similar to A-share large cap |
| HK (mid/small cap) | 0.50–1.00 | 0.15–0.35 | Very wide spreads |
| US (large cap) | 0.10–0.25 | 0.03–0.10 | Well-calibrated (Almgren et al., 2005) |
| US (small cap) | 0.30–0.50 | 0.10–0.20 | |

### Practical Cost Function for Backtesting

```python
def estimate_trade_cost(
    trade_value: float,
    adv_value: float,
    daily_vol: float,
    market: str = 'a_shares',
    side: str = 'buy'
) -> float:
    """
    Estimate total one-way trading cost including explicit and implicit costs.
    
    Returns: cost as a fraction of trade value (e.g., 0.003 = 30 bps)
    """
    participation = abs(trade_value) / adv_value if adv_value > 0 else 1.0
    
    # Explicit costs
    if market == 'a_shares':
        commission = 0.00025  # 2.5 bps
        stamp = 0.0005 if side == 'sell' else 0.0
        transfer = 0.00001
        explicit = commission + stamp + transfer
        eta = 0.30
    elif market == 'hk':
        commission = 0.0005  # 5 bps
        stamp = 0.0013  # both sides
        levies = 0.0001
        explicit = commission + stamp + levies
        eta = 0.35
    elif market == 'us':
        commission = 0.0002  # 2 bps (institutional)
        sec_taf = 0.00003 if side == 'sell' else 0.00001
        explicit = commission + sec_taf
        eta = 0.20
    else:
        raise ValueError(f"Unknown market: {market}")
    
    # Implicit cost: square-root model
    implicit = eta * daily_vol * (participation ** 0.5)
    
    # Half-spread cost
    half_spread = daily_vol * 0.1  # rough approximation
    
    total = explicit + implicit + half_spread
    return total
```

---

## 5. Short Selling and Margin Trading (融资融券与做空限制)

### A-Shares (A股)

#### Securities Lending (融券卖出)

- **Eligible stocks**: ~1,800 stocks on the margin trading list (融资融券标的), which includes most large and mid-cap stocks (roughly CSI 800 constituents + some others).
- **Lending source**: Brokers lend from their proprietary inventory or borrow from institutional holders (insurance companies, mutual funds) via the CSFC (中国证券金融公司).
- **Cost**: Lending rate ranges from 1.5% to 10%+ annualized, depending on supply/demand. Hard-to-borrow stocks can be 8–18%.
- **Supply**: Very limited. Total securities lending balance is typically < ¥100B (vs. ¥1.5T+ for margin lending). Many stocks have zero available inventory.
- **Restrictions**: 
  - Cannot short a stock on its first day of being added to the margin trading list.
  - There were temporary bans on strategic short selling (融券做空) in late 2023 and restrictions on intraday selling of borrowed shares.
  - The regulatory environment for short selling in A-shares is uncertain and can change rapidly.

#### Impact on Factor Research

- **Long-short strategies are severely constrained**: Most academic long-short factor studies cannot be implemented in A-shares. The short leg is often not executable.
- **Short-leg alpha is theoretical**: When you see a factor's long-short return, the short-leg contribution may not be capturable.
- **Alternative short implementation**: Use stock index futures (IF, IC, IH, IM) to hedge market beta. This gives a market-neutral portfolio but does not capture the pure short-side factor alpha.
- **Recommendation**: Always report long-only returns separately from long-short. In A-shares, the long-only version is what matters for practical investing.

### Hong Kong (港股)

#### Designated Short Selling

- **Eligible securities**: ~900 stocks on the designated securities list (designated short selling securities list), updated by HKEX periodically.
- **Uptick rule**: Can only short at a price ≥ the best current ask price.
- **Naked short selling**: Prohibited. Must pre-borrow shares.
- **Lending**: Available through brokers and prime brokers. More liquid than A-shares but still limited for mid/small caps.
- **Cost**: 0.5%–5% annualized for blue chips; 5%–15% for small/mid caps; some stocks are unborrowed.

#### Impact

- Long-short strategies are feasible for large caps but constrained for the broader market.
- The short-side alpha is partially capturable.
- Southbound investors (内地投资者 via Stock Connect) **cannot** short sell HK stocks.

### US Equities (美股)

#### Short Selling Mechanics

- **Locate requirement** (Reg SHO): Before short selling, the broker must locate shares to borrow. For easy-to-borrow (ETB) stocks (~85% of stocks), this is automatic. For hard-to-borrow (HTB), the locate may be refused or very expensive.
- **Alternative uptick rule** (Rule 201): If a stock drops ≥ 10% from previous close, short selling is restricted to prices above the best bid for the rest of the day and the next day.
- **Cost**: 0.25%–1% annualized for ETB stocks; 1%–50%+ for HTB stocks. Some heavily shorted stocks can have borrow costs > 100% annualized during short squeezes.
- **Availability**: Generally excellent. The US has a deep securities lending market.

#### Impact

- Long-short factor strategies are standard and well-supported.
- Short-side alpha is largely capturable, but monitor borrow costs and availability.
- Short squeezes (e.g., GME in Jan 2021) are tail risks for short portfolios.

### Comparison Summary

| Feature | A-Shares | Hong Kong | US |
|---------|----------|-----------|-----|
| Eligible universe for shorting | ~1,800 / 5,000+ (36%) | ~900 / 2,600+ (35%) | ~4,000 / 5,000+ (80%+) |
| Supply availability | Very limited | Moderate | Abundant |
| Typical borrow cost (blue chip) | 2%–5% | 0.5%–2% | 0.25%–1% |
| Regulatory risk | High (rules change frequently) | Moderate | Low (well-established rules) |
| Short-side factor alpha capturable? | Mostly not | Partially | Mostly yes |

---

## 6. Delisting and ST System (退市与ST制度)

### A-Share Delisting (A股退市)

#### Delisting Criteria (退市条件)

Since the 2020 delisting reform, A-shares have four categories of delisting:

| Category | Trigger | Process |
|----------|---------|---------|
| **Financial (财务类)** | Net income negative + revenue < ¥100M for 2 consecutive years; net assets negative; auditor issues adverse opinion or disclaimer | Warning (\*ST) → delisting consolidation period (30 days) → OTC transfer |
| **Trading (交易类)** | Stock price < ¥1 for 20 consecutive days; market cap < ¥300M for 20 consecutive days; shareholder count < required minimum | Direct delisting after confirmation |
| **Regulatory (规范类)** | Material information disclosure violation; refusal to disclose required reports; half of directors cannot certify report accuracy | Warning → correction period → delisting if not rectified |
| **Major illegality (重大违法类)** | Fraudulent IPO; fraudulent secondary offering; material financial fraud | Mandatory delisting |

#### ST / \*ST System

| Status | Meaning | Price Limit | Trading | Duration |
|--------|---------|-------------|---------|----------|
| **ST** (Special Treatment) | Warning of financial issues | ±5% | Normal | Until issues resolved |
| **\*ST** | Delisting risk warning | ±5% | Normal | If not resolved → delist |
| **Delisting consolidation (退市整理期)** | Final trading period before removal | ±10% | 30 trading days, stock code prefixed with "退" | Fixed 30 days |

#### Impact on Factor Research

1. **Universe construction**: Most strategies exclude ST/\*ST stocks. You must apply this filter at each historical date using point-in-time data. If you use a current ST list, you introduce look-ahead bias.

2. **Return handling for delisted stocks**: 
   - During the delisting consolidation period, returns are often extreme (−30% to −80% cumulative).
   - After delisting, assign −100% return or use OTC transfer value (usually near zero).
   - Many databases simply drop delisted stocks, creating survivorship bias.

3. **Value trap (价值陷阱)**: Low P/E or P/B stocks that are cheap because they are heading toward delisting. The value factor can accidentally pick up these stocks.
   - **Mitigation**: Combine value factors with quality factors (ROE, operating cash flow) to filter out distressed companies.

4. **"Shell value" (壳价值)**: Historically, A-share listed company status had value because of the difficulty of IPO approval (核准制). Distressed companies were often acquired for their listing status (借壳上市). This created a floor under small-cap stock prices, distorting the size factor. Since the IPO registration system (注册制) was fully implemented in 2023, shell value has diminished significantly.

### Hong Kong Delisting

- Delisting is more common than A-shares. HKEX can delist stocks that have been suspended for 18+ consecutive months (Main Board) or 12 months (GEM).
- Privatization: Companies can voluntarily delist via buyout (offer price typically at a premium).
- Long suspension: Many HK stocks are suspended for extended periods awaiting restructuring. These frozen positions are a practical risk.

### US Delisting

- NYSE/NASDAQ have quantitative standards: minimum share price ($1), minimum market cap, minimum shareholders, minimum equity.
- Stocks that fall below standards receive notice and have a cure period (typically 6 months).
- Delisted stocks move to OTC markets (Pink Sheets, OTC Bulletin Board) where liquidity is very thin.
- CRSP database includes delisting returns, which is critical for survivorship-bias-free research.

---

## 7. IPO Effects on Factors (新股对因子的影响)

### A-Share IPO Characteristics

| Feature | Main Board | ChiNext (创业板) | STAR (科创板) |
|---------|-----------|-----------------|--------------|
| **Price limit on Day 1** | +44% / −36% | No limit | No limit |
| **Price limit Days 2–5** | ±10% | No limit | No limit |
| **After Day 5** | ±10% | ±20% | ±20% |
| **Subscription method** | Lottery (打新, online/offline) | Same | Same |
| **Typical Day 1 return** | +44% (often limit-up) | +50% to +300% | +50% to +200% |
| **Post-IPO volatility** | Very high for 1–3 months | Very high for 1–3 months | Very high for 1–3 months |
| **Lock-up period (锁定期)** | Insiders: 12–36 months | Same | Same |

### How IPOs Contaminate Factors

1. **Extreme returns distort momentum**: IPO stocks in ChiNext/STAR can return +200% in 5 days. If included in momentum calculations, they create extreme outliers that dominate the factor.

2. **Lack of history distorts fundamental factors**: New stocks have only 1–2 quarters of public financial data. Factors that use trailing 12-month earnings or multi-year averages cannot be computed.

3. **Abnormal volatility**: IPO stocks have 2–5× the volatility of seasoned stocks in the first 60 days. Volatility factors will be dominated by IPO names.

4. **Abnormal volume**: IPO stocks often have huge initial volume (from lottery winners selling) followed by volume decline. Volume-based factors are distorted.

5. **Lock-up expiry effects (解禁效应)**: When insider lock-up periods expire, there is selling pressure. This creates a predictable negative return around the lock-up expiry date, which can be a factor in itself but contaminates other factors.

### Recommended IPO Handling

```python
# Standard IPO exclusion
IPO_EXCLUSION_DAYS = {
    'conservative': 120,  # 6 months (recommended for most factor research)
    'moderate': 60,       # ~3 months
    'aggressive': 20,     # ~1 month (minimum for ChiNext/STAR)
}

def filter_ipo(listing_date: pd.Series, current_date: pd.Timestamp, 
               min_days: int = 120) -> pd.Series:
    """Return boolean mask: True = stock has been listed long enough."""
    days_listed = (current_date - listing_date).dt.days
    return days_listed >= min_days
```

**Lock-up expiry factor**:
```python
def lockup_expiry_factor(lockup_dates: pd.Series, current_date: pd.Timestamp,
                         window: int = 30) -> pd.Series:
    """
    Flag stocks approaching lock-up expiry.
    Stocks within `window` trading days of lock-up expiry tend to underperform.
    """
    days_to_expiry = (lockup_dates - current_date).dt.days
    approaching = (days_to_expiry >= 0) & (days_to_expiry <= window)
    return approaching.astype(float) * -1  # negative signal
```

---

## 8. Auction Mechanisms (集合竞价与连续竞价)

### Opening Auction (开盘集合竞价)

#### A-Shares

| Phase | Time | Rules |
|-------|------|-------|
| **Order acceptance (接受委托)** | 09:15–09:20 | Orders accepted; cancellations allowed |
| **Order matching (撮合阶段)** | 09:20–09:25 | Orders accepted; cancellations NOT allowed |
| **Order acceptance only** | 09:25–09:30 | Orders accepted, stored; no matching; no cancellation. These orders enter the continuous trading session. |

**Opening price determination**: The price at which the maximum volume can be traded. If multiple prices qualify, the one closest to the previous close is chosen.

#### Hong Kong

| Phase | Time | Rules |
|-------|------|-------|
| **Order input** | 09:00–09:15 | At-auction limit orders accepted |
| **No cancellation** | 09:15–09:20 | No new at-auction orders; no cancellations |
| **Random matching** | 09:20–09:22 (or random end before 09:30) | Price determination and matching; random close to prevent manipulation |
| **Blocking period** | Until 09:30 | Transition to continuous trading |

#### US (NYSE)

| Phase | Time | Rules |
|-------|------|-------|
| **Pre-opening** | 06:30–09:28 | Market-on-open (MOO) and limit-on-open (LOO) orders accepted |
| **Opening auction** | 09:28–09:35 (or later) | DMM facilitates opening; opening price determined by auction |

### Closing Auction (收盘集合竞价)

#### A-Shares

**Both SSE and SZSE adopted a closing call auction in 2018.** Time: 14:57–15:00.

- During this period, orders are accepted but not matched until 15:00.
- No cancellations during 14:57–15:00.
- The closing price is determined by the auction, not the last traded price.

**Impact on factor research**:
- The **closing price** is the auction price, which may differ from the last continuous trading price.
- Strategies that use close prices are effectively using auction prices.
- If your signal generates at 14:55 and you want to trade at the close, you must submit orders into the closing auction.
- The closing auction has lower liquidity than continuous trading, so large orders may get partial fills or suffer impact.
- Approximately 5–10% of daily volume occurs in the closing auction.

#### Hong Kong

Closing Auction Session (CAS): 16:00–16:08 (random close 16:08–16:10).
- Only at-auction and at-auction limit orders.
- Closing price = auction price.
- ~7–10% of daily volume.

#### US

- **NYSE**: D-Order and MOC/LOC orders determine the closing price. ~10–15% of NYSE-listed volume occurs at the close.
- **NASDAQ**: Closing Cross. ~10% of volume.
- The 15:50 MOC/LOC cutoff creates a rush of order submission, increasing volatility in the last 10 minutes.

### Impact on Factor Signals

| Issue | Explanation | Recommendation |
|-------|-------------|----------------|
| **Close price ≠ continuous trading price** | If your signal uses close-to-close returns, the close is an auction price that may not be continuously tradeable. | If trading at close, use the auction. If trading during continuous hours, use VWAP instead. |
| **Opening auction gap** | The opening price can gap significantly from the previous close, especially after overnight news. | Use open-to-close returns for intraday factors, close-to-close for daily factors. Separate overnight and intraday returns for analysis. |
| **Auction manipulation** | Closing auctions can be manipulated by large orders placed at 14:59 (A-shares) or 16:07 (HK). | Use VWAP(14:00–14:57) as an alternative to close price for factor calculation. |
| **Volume at auction** | Auction volume is lumpy and does not represent continuous demand. | Exclude auction volume when computing intraday volume profiles or VWAP calculations. |

---

## 9. Market Participant Structure (市场参与者结构)

### A-Shares (A股)

| Participant | % of Free-Float Holdings | % of Trading Volume | Characteristics |
|-------------|--------------------------|--------------------|-|
| **Retail investors (散户)** | ~25–30% | ~55–65% | Short holding periods; trend-following; sentiment-driven; herd behavior (羊群效应). Account for most of trading but a declining share of holdings. |
| **Mutual funds (公募基金)** | ~8–10% | ~10–15% | Benchmark-constrained; quarterly reporting drives herding and window-dressing; growing share. |
| **Private funds (私募基金)** | ~5–8% | ~10–15% | More flexible; includes quant funds (量化私募) that are a significant and growing force, estimated ~¥1.5T AUM. |
| **Insurance & pension (保险/养老金)** | ~5–8% | ~2–5% | Long-term; value-oriented; low turnover. |
| **Foreign (外资/北向资金)** | ~3–5% | ~5–10% | Via Stock Connect (QFII is smaller). Tend to be fundamental/value-oriented. Flow data (北向资金流) is closely watched as a sentiment indicator. |
| **National Team (国家队)** | ~5–8% (varies) | Irregular | Central Huijin, SAFE, social security funds. Active mainly during market stress. |
| **Corporate insiders** | ~30–40% (but mostly locked) | ~1–2% | Subject to lock-up and pre-announcement trading windows. |

#### Impact on Factor Effectiveness

1. **High retail participation → Stronger behavioral factors**: Sentiment, lottery-demand, attention, and anchoring factors work better in A-shares than in institutional-dominated markets. The "overreaction followed by reversal" pattern is more pronounced.

2. **Herding → Momentum works but is unstable**: Retail herding creates momentum, but rapid sentiment shifts cause sharp reversals. Short-term momentum (1–4 weeks) works; 12-month momentum is weak in A-shares (unlike US).

3. **Analyst herding (分析师羊群效应)**: A-share analysts tend to issue optimistic recommendations (90%+ are "buy" or "overweight"). Downgrades are rare and informationally valuable.

4. **Quant crowding**: The rapid growth of quant private funds (量化私募) in 2019–2023 has led to factor crowding. Small-cap, reversal, and volume factors have become more competitive. Some quant funds reported significantly lower returns in 2023–2024 as crowding intensified.

5. **Northbound flow as a factor**: Net northbound flow (via Stock Connect) for individual stocks is a useful short-term signal. Stocks with large northbound inflows tend to outperform over the next 1–5 days.

### Hong Kong (港股)

| Participant | % of Trading Value | Characteristics |
|-------------|-------------------|-----------------|
| **Mainland investors (内地投资者)** | ~25–30% (via Southbound Connect) | Growing rapidly; tend to buy large H-share discounts; sentiment-driven flow |
| **Foreign institutional** | ~30–40% | Global fund managers; fundamental/value-oriented; hedge funds |
| **Local retail** | ~10–15% | Declining share; less influential |
| **Local institutional** | ~15–20% | Insurance, MPF (pension) |
| **Market makers / proprietary** | ~5–10% | Provide liquidity |

**Impact**: HK is more institutionally driven → fundamental factors (value, quality, earnings revision) tend to work better and more stably. However, the growing Southbound flow introduces more speculative activity, especially in H-shares with large A/H discounts.

### US Equities (美股)

| Participant | Characteristics |
|-------------|-----------------|
| **Institutional investors** | Dominate both holdings (~80%) and volume (~85%). Includes mutual funds, ETFs, pension funds, insurance, endowments, hedge funds. |
| **Retail investors** | ~15–20% of volume (increased post-2020 via Robinhood/zero-commission). Concentrated in tech, meme stocks, options. |
| **HFT / market makers** | ~50% of total equity volume. Provide liquidity; extract small edge from market microstructure. |
| **Quant funds** | Significant presence (Renaissance, Two Sigma, Citadel, DE Shaw, etc.). Highly competitive; factors decay faster. |

**Impact**: High institutional participation → traditional factors like value and quality work but are competitive and lower-alpha. HFT dominance means short-term microstructure alpha is very hard to capture. Factor crowding is most severe in US equities due to the concentration of quant AUM.

### Participant Structure Effects on Specific Factors

| Factor | A-Shares | Hong Kong | US |
|--------|----------|-----------|-----|
| **Value (B/P, E/P)** | Works but plagued by value traps; weaker due to retail speculation | Works well; mean-reversion channel | Classic risk premium; crowded; weak post-2010 |
| **Momentum (12-1 month)** | Weak or negative; dominated by reversal | Moderate effectiveness | Strong historically; crowded post-publication |
| **Short-term reversal (1-week)** | Strong (retail overreaction) | Moderate | Moderate (less retail activity) |
| **Size (small cap premium)** | Strong historically; declining with quant crowding | Weak (penny stock risk) | Weak after adjusting for quality |
| **Quality (ROE, margins)** | Increasingly effective as institutional share grows | Strong | Strong and stable |
| **Sentiment / attention** | Very strong (retail-driven) | Moderate | Moderate (but growing with retail surge post-2020) |
| **Analyst revision** | Strong (information asymmetry is high) | Strong | Moderate (well-arbitraged) |

---

## 10. Data Quality Issues (数据质量问题)

### A-Shares (A股)

| Issue | Description | Impact | Handling |
|-------|-------------|--------|----------|
| **Financial data timing (财务数据时间)** | Companies file reports up to 4 months after period end. Many databases key on reporting period, not filing date. | Look-ahead bias if not using PIT data. | Use 公告日期 (announcement date) as the availability date. Build or use a PIT database. Wind PIT function: `w.wsd(..., "rptDate=xxxx")`. |
| **Price adjustment (复权处理)** | Forward-adjusted prices change when new corporate actions occur, altering historical values. Different data sources use slightly different adjustment methods. | Return calculation errors; inconsistency across data sources. | Use backward-adjustment (后复权) or raw prices with a separate adjustment factor table. Recompute returns from raw data. |
| **Industry classification changes (行业分类变更)** | CITIC and Shenwan periodically reclassify stocks. A stock may change industry classification over its lifetime. | If using current classification for historical analysis, industry neutralization is wrong. | Use point-in-time industry classification. |
| **Index constituent history (指数成分股历史)** | CSI index constituents change semi-annually. Many databases only provide current constituents. | Survivorship bias in universe construction. | Source historical constituent lists. Wind: `w.wset("indexconstituent", date=xxxx)`. |
| **Suspension handling (停牌处理)** | Suspended stocks have no price or volume data. Some databases forward-fill prices; others leave NaN. | If forward-filled, returns appear zero during suspension. After resumption, the stock may gap significantly. | Exclude suspended stocks from the tradeable universe. Do not compute returns during suspension. Handle the resumption gap carefully. |
| **Rights issue / placement (配股/增发)** | These events dilute existing shareholders. Databases may not correctly adjust the share count or price. | Incorrect market cap calculation; wrong per-share metrics. | Verify share count changes around corporate actions. Cross-reference multiple sources. |
| **XBRL vs. reported financials** | Some databases auto-extract financials from XBRL filings, which may contain errors or use different line items than the human-readable report. | Incorrect financial ratios. | Spot-check extracted data against actual reports for a sample of companies each period. |
| **Duplicate tickers** | When a company is restructured (借壳上市), the same ticker may represent a completely different company. | Historical data before and after restructuring should not be treated as the same company. | Flag restructuring events and treat pre/post as separate entities for factor calculation. |

### Hong Kong (港股)

| Issue | Description | Handling |
|-------|-------------|---------|
| **Multi-currency quotation** | Some stocks trade in HKD and RMB (dual counter). Price data must specify currency. | Use a consistent currency. Convert at the prevailing exchange rate if mixing. |
| **Share consolidation (合股) / share subdivision (拆股)** | Very common for HK stocks, especially small caps. 10:1 consolidation can make a HK$0.10 stock become HK$1.00. | Verify adjusted prices around these events. Database may miss some actions. |
| **Lot size changes** | HK stocks change lot sizes occasionally. Historical lot sizes may not be available. | Use current lot size as approximation, or source historical lot sizes from HKEX announcements. |
| **Incomplete coverage** | Some data vendors cover only a subset of HK stocks (e.g., only HSCI constituents). Small cap / GEM data may be patchy. | Verify coverage against HKEX official listed companies. |
| **Accounting standards** | HK-listed companies use HKFRS/IFRS, but mainland companies listed in HK may report slightly differently. Pre-2005, HK GAAP differed from IFRS. | Use standardized financial metrics from a reputable data source. |
| **Dual-listed companies** | A/H shares (same company listed in both markets). Price levels differ (A-H premium). Financial data should be shared. | Use the same financial data for both listings; track A-H premium as a potential factor. |

### US Equities (美股)

| Issue | Description | Handling |
|-------|-------------|---------|
| **CRSP/Compustat merge** | Linking price data (CRSP) with fundamental data (Compustat) requires the CRSP/Compustat merged dataset (CCM). Incorrect linking leads to wrong fundamentals for a given stock. | Use the official CRSP-Compustat link table (GVKEY-PERMNO-PERMCO). Verify with manual checks. |
| **Delisting returns** | CRSP includes delisting returns, but some are estimated. Ignoring delisting returns inflates strategy returns by ~1–2% annually. | Always include CRSP delisting returns. For missing delisting returns, use Shumway (1997) estimates: −30% for NYSE/AMEX, −55% for NASDAQ. |
| **Restatements (重述)** | US companies occasionally restate prior financials. Compustat may update historical records retroactively. | Use Compustat Snapshot (point-in-time) or I/B/E/S Actuals for PIT financial data. |
| **Ticker changes** | US companies frequently change tickers (e.g., after M&A, rebranding). PERMNO (from CRSP) is the stable identifier, not the ticker. | Use PERMNO or CUSIP as the primary identifier. Never link data using tickers alone. |
| **ADR vs. ordinary shares** | Many foreign companies trade as ADRs in the US. These are not the same as the ordinary shares and may have different share counts, corporate actions, and trading hours. | Exclude ADRs from domestic US factor studies, or handle them separately. |
| **Penny stock data quality** | Stocks < $1 have very noisy data: wide bid-ask spreads, low volume, potential for stale quotes. | Exclude stocks with price < $5 (conservative) or < $1 (minimum). |
| **Ex-date vs. pay-date for dividends** | The ex-date (when price adjusts) and pay-date (when cash is received) differ by weeks. | Use ex-date for price adjustment and return calculation. |

### General Data Quality Best Practices (通用数据质量建议)

1. **Cross-validate across multiple sources**: Compare returns, factor values, and universe counts across at least two data vendors. Discrepancies indicate data issues.

2. **Run sanity checks at every step**:
   ```python
   def data_sanity_check(df: pd.DataFrame):
       checks = {
           'missing_rate': df.isnull().mean(),
           'zero_rate': (df == 0).mean(),
           'inf_rate': np.isinf(df.select_dtypes(include=[np.number])).mean(),
           'duplicate_index': df.index.duplicated().sum(),
           'extreme_values': (df.select_dtypes(include=[np.number]).abs() > 
                             df.select_dtypes(include=[np.number]).abs().quantile(0.999) * 10).mean(),
       }
       for check, result in checks.items():
           if isinstance(result, pd.Series):
               bad_cols = result[result > 0.01].index.tolist()
               if bad_cols:
                   print(f"WARNING [{check}]: {bad_cols}")
           elif result > 0:
               print(f"WARNING [{check}]: {result}")
   ```

3. **Maintain a data issue log**: Every time you discover a data error, log it with the date, source, stock, and nature of the error. Over time, this becomes an invaluable reference.

4. **Version your data**: Snapshot and version your cleaned datasets. When you discover and fix data issues, you can re-run analyses on corrected data and compare.

5. **Point-in-time is non-negotiable**: For any data that is subject to revision or delayed publication (financials, macro data, analyst estimates), you must use point-in-time data. This is the single most impactful data quality practice.

---

## Appendix: Market Calendar Reference (交易日历)

### Trading Days per Year

| Market | Typical Trading Days/Year | Major Closures |
|--------|--------------------------|----------------|
| **A-Shares** | ~242 | Chinese New Year (~7 days), National Day (~7 days), other public holidays |
| **Hong Kong** | ~248 | Chinese New Year (~3 days), Christmas, other HK public holidays |
| **US** | ~252 | New Year, MLK Day, Presidents Day, Good Friday, Memorial Day, Independence Day, Labor Day, Thanksgiving, Christmas |

### Key Calendar Events for Factor Research

| Event | Timing | Impact |
|-------|--------|--------|
| **A-share annual report season** | January–April (deadline: April 30) | Fundamental factor signals refresh; earnings surprise factors are most active |
| **A-share semi-annual report season** | July–August (deadline: August 31) | Mid-year update to fundamental factors |
| **A-share quarterly reports** | Q1: April 30; Q3: October 31 | Lighter reporting requirements |
| **CSI index rebalance** | June and December (effective 2nd Friday) | Large index fund flows; front-running and reversal opportunities |
| **MSCI rebalance** | February, May, August, November | Foreign fund flows into/out of A-shares and HK |
| **US earnings season** | Jan-Feb (Q4), Apr-May (Q1), Jul-Aug (Q2), Oct-Nov (Q3) | Earnings surprise, post-earnings drift (PEAD) |
| **Triple/Quadruple witching (US)** | 3rd Friday of March, June, September, December | Options and futures expiry; increased volume and volatility |
