# Alpha Skills

**Quantitative factor research skills for AI coding assistants.**

A collection of structured skill definitions that turn any LLM-powered coding assistant into a quantitative factor research workstation. Supports Claude Code, Cursor, Windsurf, Continue, and any AI coding tool that accepts system prompts.

> 一套量化因子研究技能集，将任何AI编程助手变成专业的因子研究工作站。

![Alpha Skills Demo](assets/demo.png)

---

## What are Alpha Skills?

Alpha Skills are **structured instruction files** (Markdown) that teach AI coding assistants how to perform professional quantitative factor research. Each skill defines:

- **When to activate** — trigger phrases in natural language
- **What to do** — step-by-step research methodology
- **How to compute** — Python code patterns for factor calculation, evaluation, and backtesting
- **How to present** — standardized output formats for results

The AI reads these instructions and executes the research workflow — loading data, computing factors, running statistical tests, generating reports — all through natural conversation.

## Skills

| Skill | Description | Trigger Examples |
|-------|-------------|-----------------|
| **alpha-discover** | Design factors from natural language | "帮我找一个量价背离因子" / "design a momentum factor" |
| **alpha-evaluate** | Multi-level factor evaluation (IC/ICIR/quintile) | "评估reversal_5因子" / "evaluate this factor" |
| **alpha-library** | Factor registry with lifecycle management | "查看因子库" / "register this factor" |
| **alpha-backtest** | Single/multi-factor portfolio backtesting | "回测" / "backtest with these factors" |
| **alpha-monitor** | Monitor active factors for IC decay | "检查因子健康" / "factor health check" |
| **alpha-report** | Generate comprehensive analysis reports | "生成报告" / "factor report" |

## Quick Start

### 1. Clone

```bash
git clone https://github.com/VernonOY/alpha-skills.git
```

### 2. Install Skills

**Cursor / Windsurf**: Copy `skills/alpha-*/SKILL.md` content into `.cursorrules` or `.windsurfrules`

**Other AI coding tools**: Include SKILL.md content as system prompt or rules file

### 3. Configure

Create a config file with your data source and evaluation preferences (see [Configuration](#configuration)).

### 4. Use

Tell your AI assistant: "评估pv_diverge因子" or "evaluate the reversal factor" — it handles the rest.

## Requirements

```bash
pip install pandas numpy scipy matplotlib pyarrow
# For A-share data via Tushare:
pip install tushare
```

## Multi-Market Support 多市场支持

Alpha Skills work out-of-the-box with **A-share, HK, and US** stocks:

| Market 市场 | Adapter 适配器 | Data Source 数据源 | Setup 配置 |
|-------------|----------------|-------------------|------------|
| **A-share 中国A股** | Default | [Tushare Pro](https://tushare.pro) | `pip install tushare` |
| **HK 港股** | `examples/hk_data_yfinance.py` | Yahoo Finance | `pip install yfinance` |
| **US 美股** | `examples/us_data_yfinance.py` | Yahoo Finance | `pip install yfinance` |

Just set `MARKET` and `DATA_MODULE` in your config:

```markdown
# US stocks
MARKET: US
DATA_MODULE: examples.us_data_yfinance

# HK stocks
MARKET: HK
DATA_MODULE: examples.hk_data_yfinance

# A-share (default, no DATA_MODULE needed)
MARKET: A-share
```

The skills automatically adapt trading rules per market:

| Rule 规则 | A-share | HK | US |
|-----------|---------|-----|-----|
| Price Limit 涨跌停 | ±10% | None 无 | None 无 |
| T+N | T+1 | T+0 | T+0 |
| Round-trip Cost 双边成本 | 0.3% | 0.2% | 0.1% |

## Custom Data Sources 自定义数据源

Need a different data source (AkShare, Bloomberg, Binance, etc.)? Write your own adapter — see [`examples/README.md`](examples/README.md) for the interface spec.

需要其他数据源（AkShare、Bloomberg、币安等）？编写自己的适配器 — 接口规范见 [`examples/README.md`](examples/README.md)。

### Using Your Own Data API

Create a Python module (e.g., `my_data.py`) that provides these functions:

```python
def load_prices(start_date, end_date):
    """Return DataFrame: ts_code, trade_date, open, high, low, close, vol, amount"""
    ...

def load_adj_factor(start_date, end_date):
    """Return DataFrame: ts_code, trade_date, adj_factor"""
    ...

def load_daily_basic(start_date, end_date):
    """Return DataFrame: ts_code, trade_date, pe_ttm, pb, turnover_rate_f, ..."""
    ...

def load_financial(start_date, end_date):
    """Return DataFrame: ts_code, ann_date, end_date, roe, roa, ..."""
    ...
```

Then set `DATA_MODULE: my_data` in your config. The skills will automatically use your module.

## Supported Platforms

| Platform | Method | Status |
|----------|--------|--------|
| AI coding assistants | Copy SKILL.md to system prompt or rules file | Tested |
| Cursor | `.cursorrules` | Compatible |
| Windsurf | `.windsurfrules` | Compatible |
| Continue | config system prompt | Compatible |
| ChatGPT | paste as instructions | Compatible |
| Local models | system prompt | Depends on model capability |

## Research Workflow

```
Discover → Evaluate → Register → Monitor → Backtest → Report
```

### Optional: Static Code Analysis 可选：静态代码检查

Before running `alpha-evaluate` on a hand-written factor, you can pipe the code through [**qtype**](https://github.com/VernonOY/qtype) to catch common time-leak bugs:

在运行 `alpha-evaluate` 之前，你可以用 [**qtype**](https://github.com/VernonOY/qtype) 扫描手写因子代码，捕捉常见的时间泄漏bug：

```bash
pip install qtype
qtype check my_factor.py
```

qtype is a standalone AST-based linter that detects look-ahead bias (`shift(-1)`), future functions, survival bias (missing ST filters), alignment errors, and return-offset bugs. It is not a dependency of Alpha Skills — just a recommended pre-flight check for any quant code.

qtype 是一个独立的 AST 静态分析器，不是 Alpha Skills 的依赖，但推荐在任何量化代码评估前先跑一遍。

### Evaluation Pipeline

| Level | What | Time |
|-------|------|------|
| L0 | Syntax validation | instant |
| L1 | Quick IC screen (sampled) | <30s |
| L2 | Full test (IC/ICIR/quintile/long-short) | 1-3min |
| L3 | Robustness (parameter perturbation, rolling window) | 5-15min |

### Configurable Criteria

Users customize evaluation thresholds via config file:

```markdown
GATE_SHARPE: 1.0
GATE_MAX_DRAWDOWN: -0.25
GATE_PROFIT_FACTOR: 1.0
EVAL_ICIR_STRONG: 0.5
COST_RATE: 0.003
```

## Built-in Factors (25+)

**Price-Volume**: momentum · reversal · volatility · pv_diverge · rsi · macd · bollinger · atr_ratio · turnover · abnormal_turnover

**Fundamental**: roe · roa · gross_margin · net_profit_growth · revenue_growth

**Valuation**: pe_ttm · pb · ps_ttm · dividend_yield · peg

**Composite**: quality_score · value_score · growth_momentum

## Roadmap

- [x] 6 core research skills (discover / evaluate / library / backtest / monitor / report)
- [x] A-share, HK, and US market support (out-of-the-box)
- [x] Market-aware trading rules (price limits, T+N, costs)
- [x] Configurable evaluation criteria & gate checks
- [x] Custom data source support (CSV / Parquet / custom Python module)
- [x] Multi-platform compatibility (Cursor, Windsurf, Continue, ChatGPT, local models)
- [x] Optional integration with [qtype](https://github.com/VernonOY/qtype) for static code checks
- [ ] Automated factor mining skill (genetic programming)
- [ ] Portfolio construction skill (factor → tradeable portfolio)
- [ ] Market regime detection & factor-regime mapping
- [ ] Factor crowding detection
- [ ] English-first skill variants
- [ ] Web UI dashboard (standalone application)

## Recommended Companion Tools 推荐配套工具

These are independent tools that pair well with Alpha Skills — not dependencies:

这些是与 Alpha Skills 搭配使用的独立工具，不是依赖项：

- **[qtype](https://github.com/VernonOY/qtype)** — Static analyzer for quant code. Run it on your factor files to catch look-ahead bias, future functions, survival bias, alignment errors, and return-offset bugs before wasting compute on a fake-alpha backtest.

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

## Contributing

PRs welcome! You can:
- Add new skills for different research workflows
- Adapt existing skills for other markets (US, HK, crypto)
- Add support for new data providers (Yahoo Finance, AkShare, Binance, etc.)
- Improve evaluation methodology
- Translate skills to other languages
