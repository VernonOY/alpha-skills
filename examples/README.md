# Data Adapters 数据适配器

Ready-to-use data adapters for different markets. Just set `DATA_MODULE` in your config.

开箱即用的市场数据适配器。只需在配置中设置 `DATA_MODULE` 即可。

## Available Adapters 可用适配器

| Market 市场 | File 文件 | Data Source 数据源 | Cost 成本 | Benchmark 基准 |
|-------------|-----------|-------------------|-----------|----------------|
| **A-share 中国A股** | Default (Tushare) | Tushare Pro API | 0.3% | 000300.SH |
| **US 美股** | `us_data_yfinance.py` | Yahoo Finance | 0.1% | ^GSPC |
| **HK 港股** | `hk_data_yfinance.py` | Yahoo Finance | 0.2% | ^HSI |

## Quick Setup 快速配置

### US Stocks 美股

```bash
pip install yfinance
```

In `.claude/alpha-agent.config.md`:
```markdown
MARKET: US
DATA_MODULE: examples.us_data_yfinance
```

### HK Stocks 港股

```bash
pip install yfinance
```

In `.claude/alpha-agent.config.md`:
```markdown
MARKET: HK
DATA_MODULE: examples.hk_data_yfinance
```

### A-Share A股 (Default 默认)

Install tushare and configure token. No `DATA_MODULE` needed.
安装tushare并配置token，无需设置 `DATA_MODULE`。

```bash
pip install tushare
```

## Writing Your Own Adapter 编写自定义适配器

Create a Python module with these functions (all returning pandas DataFrames):

创建一个Python模块，实现以下函数（全部返回pandas DataFrame）：

```python
MARKET_CONFIG = {
    "market": "YourMarket",
    "currency": "USD",
    "benchmark": "INDEX_SYMBOL",
    "cost_rate": 0.001,
    "price_limit": None,      # or 0.1 for markets with price limits
    "min_trade_unit": 1,
    "t_plus": 0,
}

def load_prices(start_date, end_date, ts_code_list=None): ...
def load_adj_factor(start_date, end_date, ts_code_list=None): ...
def load_daily_basic(start_date, end_date, ts_code_list=None): ...
def load_financial(start_date, end_date, ts_code_list=None): ...
def load_index(ts_code, start_date, end_date): ...
def load_stock_pool(date): ...
def load_trade_cal(start_date, end_date): ...
```

See `us_data_yfinance.py` or `hk_data_yfinance.py` for reference implementations.

参考 `us_data_yfinance.py` 或 `hk_data_yfinance.py` 的实现。
