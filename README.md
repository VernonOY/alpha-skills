# Alpha Skills

**Quantitative factor research skills for AI coding assistants.**

A collection of structured skill definitions that turn any LLM-powered coding assistant into a quantitative factor research workstation. Supports Claude Code, Cursor, Windsurf, Continue, and any AI coding tool that accepts system prompts.

> 一套量化因子研究技能集，将任何AI编程助手变成专业的因子研究工作站。

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

## Data Sources

Alpha Skills support **any data source**. Configure via `DATA_SOURCE` in your config file:

| Source | Config | Description |
|--------|--------|-------------|
| **Tushare** | `DATA_SOURCE: tushare` | A-share data via [Tushare Pro](https://tushare.pro) (default) |
| **CSV/Parquet** | `DATA_SOURCE: csv` + `DATA_DIR: /path` | Read from local files |
| **Custom module** | `DATA_MODULE: my_data` | Your own Python data loader |

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
- [x] A-share market support (Tushare)
- [x] Configurable evaluation criteria & gate checks
- [x] Custom data source support (CSV / Parquet / custom Python module)
- [x] Multi-platform compatibility (Cursor, Windsurf, Continue, ChatGPT, local models)
- [ ] US/HK market skill variants
- [ ] Automated factor mining skill (genetic programming)
- [ ] Portfolio construction skill (factor → tradeable portfolio)
- [ ] Market regime detection & factor-regime mapping
- [ ] Factor crowding detection
- [ ] Data quality dashboard & look-ahead bias detector
- [ ] English-first skill variants
- [ ] Web UI dashboard (standalone application)

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

## Contributing

PRs welcome! You can:
- Add new skills for different research workflows
- Adapt existing skills for other markets (US, HK, crypto)
- Add support for new data providers (Yahoo Finance, AkShare, Binance, etc.)
- Improve evaluation methodology
- Translate skills to other languages
