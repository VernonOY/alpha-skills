"""
US Stock Data Adapter using YFinance
=====================================

A drop-in data adapter for the alpha-agent skills, providing US equity data
via the yfinance package. The function signatures and DataFrame schemas mirror
those of the Tushare-based loader so that skills can switch markets seamlessly.

Usage
-----
1. Install yfinance:
       pip install yfinance pyarrow

2. In `.claude/alpha-agent.config.md` (or equivalent) set:
       DATA_MODULE: examples.us_data_yfinance
       MARKET: US

3. Then in skills:
       import importlib
       data_mod = importlib.import_module("examples.us_data_yfinance")
       prices = data_mod.load_prices("20240101", "20240131")

Date format
-----------
All dates use the Tushare convention `YYYYMMDD` (string). Internally we convert
to `YYYY-MM-DD` for yfinance and convert results back.

Caching
-------
Results are cached locally as parquet files in `../data_cache_us/` so that
expensive network calls are not repeated. Delete the cache directory to refresh.
"""

from __future__ import annotations

import hashlib
import os
from typing import List, Optional

import pandas as pd

try:
    import yfinance as yf
except ImportError as exc:  # pragma: no cover - import-time guard
    raise ImportError(
        "yfinance is required for examples.us_data_yfinance. "
        "Install it with: pip install yfinance"
    ) from exc


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data_cache_us"
)
os.makedirs(CACHE_DIR, exist_ok=True)


# S&P 500 Top ~120 by market cap (hard-coded to avoid web-scrape dependency).
# Note: yfinance uses '-' for class shares (e.g. BRK-B), not '.'.
SP500_TICKERS: List[str] = [
    # Technology
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "META", "AVGO", "ORCL", "ADBE",
    "CRM", "AMD", "INTC", "CSCO", "ACN", "QCOM", "TXN", "IBM", "INTU", "NOW",
    "AMAT", "MU", "LRCX", "KLAC", "PANW", "SNPS", "CDNS", "ADI", "MRVL",
    # Communication / Media
    "DIS", "NFLX", "CMCSA", "TMUS", "VZ", "T", "CHTR",
    # Consumer Discretionary
    "AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TGT", "TJX", "BKNG",
    "ABNB", "MAR", "GM", "F", "LULU",
    # Consumer Staples
    "WMT", "COST", "PG", "KO", "PEP", "PM", "MO", "MDLZ", "CL", "KMB",
    # Financials
    "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "AXP", "BLK", "C",
    "SCHW", "SPGI", "CB", "PGR", "MMC", "ICE", "CME", "USB", "PNC",
    # Health Care
    "UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY",
    "AMGN", "GILD", "CVS", "MDT", "ISRG", "ELV", "REGN", "VRTX", "SYK", "ZTS",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "PSX", "MPC", "VLO", "OXY", "KMI",
    # Industrials
    "CAT", "BA", "GE", "HON", "UPS", "RTX", "LMT", "DE", "MMM", "UNP",
    "ETN", "ADP", "NOC", "GD", "FDX", "CSX", "NSC", "EMR",
    # Materials / Real Estate / Utilities
    "LIN", "SHW", "FCX", "NEM", "ECL", "PLD", "AMT", "EQIX", "CCI", "PSA",
    "NEE", "DUK", "SO", "D", "AEP",
]

# Deduplicate while preserving order
SP500_TICKERS = list(dict.fromkeys(SP500_TICKERS))


MARKET_CONFIG = {
    "market": "US",
    "currency": "USD",
    "benchmark": "^GSPC",
    "cost_rate": 0.001,        # ~10bps round-trip
    "price_limit": None,       # no daily limit in US
    "tax_sell": 0,
    "min_trade_unit": 1,       # 1-share lot
    "t_plus": 0,               # T+0 same-day settlement (intraday)
    "trade_calendar_source": "NYSE",
}


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _cache_key(name: str, **kwargs) -> str:
    """Build a deterministic cache filename from function name + kwargs."""
    payload = name + repr(sorted(kwargs.items()))
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()[:12]
    return f"{name}_{digest}.parquet"


def _load_cache(name: str, **kwargs) -> Optional[pd.DataFrame]:
    path = os.path.join(CACHE_DIR, _cache_key(name, **kwargs))
    if os.path.exists(path):
        try:
            return pd.read_parquet(path)
        except Exception:
            # Corrupted cache file -- ignore and refetch.
            return None
    return None


def _save_cache(name: str, df: Optional[pd.DataFrame], **kwargs) -> None:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, _cache_key(name, **kwargs))
    try:
        df.to_parquet(path)
    except Exception:
        # Cache failure should not break the data path.
        pass


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _to_yf_date(date_str: str) -> str:
    """Convert 'YYYYMMDD' -> 'YYYY-MM-DD' for yfinance."""
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"


def _from_ts_date(ts) -> str:
    """Convert pandas Timestamp -> 'YYYYMMDD' string."""
    return pd.Timestamp(ts).strftime("%Y%m%d")


def _resolve_tickers(ts_code_list: Optional[List[str]]) -> List[str]:
    if ts_code_list is None or len(ts_code_list) == 0:
        return list(SP500_TICKERS)
    return list(ts_code_list)


def _download(tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
    """Wrap yf.download to always return a (field, ticker) MultiIndex frame.

    yfinance returns a single-level column DataFrame when only one ticker is
    requested; we normalise that to a MultiIndex grouped by ticker so the
    downstream parsing is uniform.
    """
    start = _to_yf_date(start_date)
    end = _to_yf_date(end_date)

    data = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=False,
        progress=False,
        threads=True,
        group_by="ticker",
    )

    if data is None or data.empty:
        return pd.DataFrame()

    # Single-ticker case: columns are flat (Open, High, ...). Promote to
    # MultiIndex (ticker, field) so the rest of the code is uniform.
    if not isinstance(data.columns, pd.MultiIndex):
        only = tickers[0] if len(tickers) == 1 else "TICKER"
        data.columns = pd.MultiIndex.from_product([[only], data.columns])
    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_stock_pool(date: str) -> pd.DataFrame:
    """Return the S&P 500-style stock pool.

    yfinance does not expose a historical constituency feed, so we return the
    static `SP500_TICKERS` list. Columns mirror the Tushare schema:
    `ts_code, symbol, name, list_date`.
    """
    cached = _load_cache("stock_pool", date=date)
    if cached is not None:
        return cached

    rows = []
    for tk in SP500_TICKERS:
        rows.append(
            {
                "ts_code": tk,
                "symbol": tk,
                "name": tk,        # full name lookup is per-ticker (slow); skipped
                "list_date": "",  # unknown without per-ticker info() call
            }
        )
    result = pd.DataFrame(rows)
    _save_cache("stock_pool", result, date=date)
    return result


def load_prices(
    start_date: str,
    end_date: str,
    ts_code_list: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Daily OHLCV bars for US equities.

    Returns columns: ts_code, trade_date, open, high, low, close, vol, amount.
    `vol` is in shares, `amount` is approximated as close * volume (USD).
    """
    tickers = _resolve_tickers(ts_code_list)

    cached = _load_cache(
        "prices", start=start_date, end=end_date, codes=tuple(tickers)
    )
    if cached is not None:
        return cached

    data = _download(tickers, start_date, end_date)
    if data.empty:
        return pd.DataFrame(
            columns=["ts_code", "trade_date", "open", "high", "low",
                     "close", "vol", "amount"]
        )

    available_tickers = list(data.columns.get_level_values(0).unique())

    records = []
    for ticker in tickers:
        if ticker not in available_tickers:
            continue
        df = data[ticker].dropna(subset=["Close"])
        if df.empty:
            continue
        for ts, row in df.iterrows():
            close = row.get("Close", 0) or 0
            volume = row.get("Volume", 0) or 0
            records.append(
                {
                    "ts_code": ticker,
                    "trade_date": _from_ts_date(ts),
                    "open": row.get("Open", 0),
                    "high": row.get("High", 0),
                    "low": row.get("Low", 0),
                    "close": close,
                    "vol": volume,
                    "amount": float(close) * float(volume),
                }
            )

    result = pd.DataFrame(records)
    _save_cache(
        "prices", result, start=start_date, end=end_date, codes=tuple(tickers)
    )
    return result


def load_adj_factor(
    start_date: str,
    end_date: str,
    ts_code_list: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Adjustment factor = Adj Close / Close (forward-adjusted ratio).

    Returns columns: ts_code, trade_date, adj_factor.
    """
    tickers = _resolve_tickers(ts_code_list)

    cached = _load_cache(
        "adj_factor", start=start_date, end=end_date, codes=tuple(tickers)
    )
    if cached is not None:
        return cached

    data = _download(tickers, start_date, end_date)
    if data.empty:
        return pd.DataFrame(columns=["ts_code", "trade_date", "adj_factor"])

    available_tickers = list(data.columns.get_level_values(0).unique())

    records = []
    for ticker in tickers:
        if ticker not in available_tickers:
            continue
        df = data[ticker].dropna(subset=["Close"]).copy()
        if df.empty or "Adj Close" not in df.columns:
            continue
        df["adj_factor"] = df["Adj Close"] / df["Close"]
        for ts, row in df.iterrows():
            adj = row.get("adj_factor")
            if pd.isna(adj):
                continue
            records.append(
                {
                    "ts_code": ticker,
                    "trade_date": _from_ts_date(ts),
                    "adj_factor": float(adj),
                }
            )

    result = pd.DataFrame(records)
    _save_cache(
        "adj_factor", result, start=start_date, end=end_date, codes=tuple(tickers)
    )
    return result


def load_daily_basic(
    start_date: str,
    end_date: str,
    ts_code_list: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Per-day fundamental snapshot.

    yfinance only exposes the *latest* PE/PB/market cap via `Ticker.info`,
    so we broadcast that snapshot across every trading day in the requested
    window. This is a known limitation of YFinance vs. Tushare.

    Returns columns: ts_code, trade_date, pe_ttm, pb, turnover_rate_f,
    circ_mv, total_mv.
    """
    tickers = _resolve_tickers(ts_code_list)

    cached = _load_cache(
        "daily_basic", start=start_date, end=end_date, codes=tuple(tickers)
    )
    if cached is not None:
        return cached

    # Get the trading day axis from the benchmark.
    cal = load_trade_cal(start_date, end_date)
    if cal.empty:
        return pd.DataFrame(
            columns=["ts_code", "trade_date", "pe_ttm", "pb",
                     "turnover_rate_f", "circ_mv", "total_mv"]
        )
    trade_dates = cal["cal_date"].tolist()

    records = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info or {}
        except Exception:
            info = {}

        pe_ttm = info.get("trailingPE")
        pb = info.get("priceToBook")
        # YFinance gives floats already; we keep None where unavailable.
        total_mv = info.get("marketCap")
        # YFinance has no public circulating-only mcap; reuse marketCap.
        circ_mv = info.get("marketCap")
        # No turnover field; set to NaN so factor code can mask it.
        turnover_rate_f = None

        for d in trade_dates:
            records.append(
                {
                    "ts_code": ticker,
                    "trade_date": d,
                    "pe_ttm": pe_ttm,
                    "pb": pb,
                    "turnover_rate_f": turnover_rate_f,
                    "circ_mv": circ_mv,
                    "total_mv": total_mv,
                }
            )

    result = pd.DataFrame(records)
    _save_cache(
        "daily_basic", result, start=start_date, end=end_date, codes=tuple(tickers)
    )
    return result


def load_financial(
    start_date: str,
    end_date: str,
    ts_code_list: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Quarterly / annual financials per ticker.

    Pulled from `Ticker.financials`, `Ticker.balance_sheet`, `Ticker.cashflow`.
    Reports are filtered so that `end_date` lies within the requested window.

    Returns columns: ts_code, ann_date, end_date, roe, roa,
    grossprofit_margin, netprofit_yoy, or_yoy.
    """
    tickers = _resolve_tickers(ts_code_list)

    cached = _load_cache(
        "financial", start=start_date, end=end_date, codes=tuple(tickers)
    )
    if cached is not None:
        return cached

    start_ts = pd.Timestamp(_to_yf_date(start_date))
    end_ts = pd.Timestamp(_to_yf_date(end_date))

    records = []
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            inc = t.financials       # columns are period end dates
            bs = t.balance_sheet
        except Exception:
            continue

        if inc is None or inc.empty:
            continue

        def _row(df, *labels):
            """Return the first matching row label as a Series, or None."""
            if df is None or df.empty:
                return None
            for lbl in labels:
                if lbl in df.index:
                    return df.loc[lbl]
            return None

        net_income = _row(inc, "Net Income", "NetIncome")
        revenue = _row(inc, "Total Revenue", "TotalRevenue")
        gross = _row(inc, "Gross Profit", "GrossProfit")
        equity = _row(bs, "Total Stockholder Equity",
                      "Stockholders Equity", "TotalStockholderEquity")
        total_assets = _row(bs, "Total Assets", "TotalAssets")

        if net_income is None or revenue is None:
            continue

        # Sort columns ascending so YoY math is correct.
        periods = sorted(net_income.index)
        prev_ni = None
        prev_rev = None
        for end in periods:
            end_ts_p = pd.Timestamp(end)
            if not (start_ts <= end_ts_p <= end_ts):
                # Track YoY history but skip emit if outside window.
                prev_ni = net_income.get(end, prev_ni)
                prev_rev = revenue.get(end, prev_rev)
                continue

            ni = float(net_income.get(end)) if pd.notna(
                net_income.get(end)) else None
            rev = float(revenue.get(end)) if pd.notna(
                revenue.get(end)) else None
            gp = float(gross.get(end)) if (
                gross is not None and pd.notna(gross.get(end))
            ) else None
            eq = float(equity.get(end)) if (
                equity is not None and pd.notna(equity.get(end))
            ) else None
            ta = float(total_assets.get(end)) if (
                total_assets is not None and pd.notna(total_assets.get(end))
            ) else None

            roe = (ni / eq) if (ni is not None and eq) else None
            roa = (ni / ta) if (ni is not None and ta) else None
            gpm = (gp / rev) if (gp is not None and rev) else None
            ni_yoy = (
                (ni - prev_ni) / abs(prev_ni)
                if (ni is not None and prev_ni)
                else None
            )
            or_yoy = (
                (rev - prev_rev) / abs(prev_rev)
                if (rev is not None and prev_rev)
                else None
            )

            records.append(
                {
                    "ts_code": ticker,
                    "ann_date": _from_ts_date(end_ts_p),
                    "end_date": _from_ts_date(end_ts_p),
                    "roe": roe,
                    "roa": roa,
                    "grossprofit_margin": gpm,
                    "netprofit_yoy": ni_yoy,
                    "or_yoy": or_yoy,
                }
            )

            prev_ni = ni if ni is not None else prev_ni
            prev_rev = rev if rev is not None else prev_rev

    result = pd.DataFrame(records)
    _save_cache(
        "financial", result, start=start_date, end=end_date, codes=tuple(tickers)
    )
    return result


def load_index(ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Index OHLCV. `ts_code` is a yfinance index symbol like '^GSPC' or 'SPY'.

    Returns columns: ts_code, trade_date, close, open, high, low, vol.
    """
    cached = _load_cache(
        "index", code=ts_code, start=start_date, end=end_date
    )
    if cached is not None:
        return cached

    data = _download([ts_code], start_date, end_date)
    if data.empty:
        return pd.DataFrame(
            columns=["ts_code", "trade_date", "close", "open", "high", "low", "vol"]
        )

    # _download already wraps in a MultiIndex grouped by ticker.
    available = list(data.columns.get_level_values(0).unique())
    if ts_code not in available:
        # Single-ticker special case: _download labelled it ts_code already
        ts_code_local = available[0]
    else:
        ts_code_local = ts_code

    df = data[ts_code_local].dropna(subset=["Close"])
    records = []
    for ts, row in df.iterrows():
        records.append(
            {
                "ts_code": ts_code,
                "trade_date": _from_ts_date(ts),
                "close": row.get("Close", 0),
                "open": row.get("Open", 0),
                "high": row.get("High", 0),
                "low": row.get("Low", 0),
                "vol": row.get("Volume", 0),
            }
        )

    result = pd.DataFrame(records)
    _save_cache("index", result, code=ts_code, start=start_date, end=end_date)
    return result


def load_trade_cal(start_date: str, end_date: str) -> pd.DataFrame:
    """Inferred NYSE trading calendar.

    yfinance does not expose an exchange calendar directly, so we derive the
    list of open days from the S&P 500 (`^GSPC`) bar timestamps. Days that
    appear in the index series are flagged `is_open=1`, otherwise `0`.

    Returns columns: cal_date, is_open.
    """
    cached = _load_cache("trade_cal", start=start_date, end=end_date)
    if cached is not None:
        return cached

    idx = load_index("^GSPC", start_date, end_date)
    if idx.empty:
        return pd.DataFrame(columns=["cal_date", "is_open"])

    open_days = set(idx["trade_date"].astype(str).tolist())

    start_ts = pd.Timestamp(_to_yf_date(start_date))
    end_ts = pd.Timestamp(_to_yf_date(end_date))
    all_days = pd.date_range(start_ts, end_ts, freq="D")

    rows = []
    for d in all_days:
        cal_date = d.strftime("%Y%m%d")
        rows.append(
            {"cal_date": cal_date, "is_open": 1 if cal_date in open_days else 0}
        )

    result = pd.DataFrame(rows)
    _save_cache("trade_cal", result, start=start_date, end=end_date)
    return result


# ---------------------------------------------------------------------------
# Self-test (no network) -- run with: python examples/us_data_yfinance.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    print("US data adapter loaded.")
    print(f"  market         : {MARKET_CONFIG['market']}")
    print(f"  benchmark      : {MARKET_CONFIG['benchmark']}")
    print(f"  pool size      : {len(SP500_TICKERS)} tickers")
    print(f"  cache dir      : {CACHE_DIR}")
    print("Public functions:")
    for fn in (
        load_prices, load_adj_factor, load_daily_basic, load_financial,
        load_index, load_stock_pool, load_trade_cal,
    ):
        print(f"  - {fn.__name__}")
