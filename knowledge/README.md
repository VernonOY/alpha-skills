# Knowledge Base 知识库

Professional reference documents for quantitative factor research. These provide the domain expertise that makes Alpha Skills perform at institutional level.

专业量化因子研究参考文档。这些文档提供了让 Alpha Skills 达到机构级水平所需的专业知识。

## Documents 文档

| Document | What It Covers |
|----------|---------------|
| [**evaluation-methodology.md**](evaluation-methodology.md) | IC/ICIR interpretation, quintile analysis, robustness testing, advanced diagnostics, report template, common pitfalls |
| [**factor-taxonomy.md**](factor-taxonomy.md) | 9 factor categories with economic intuition, typical IC ranges, market-specific behavior (A-share/HK/US), implementation patterns |
| [**risk-and-pitfalls.md**](risk-and-pitfalls.md) | Look-ahead bias (10 forms), survivorship bias, overfitting detection, transaction cost modeling, multiple testing correction, 15+ backtest pitfalls |
| [**portfolio-construction.md**](portfolio-construction.md) | Weighting schemes, constraints, turnover optimization, risk attribution, rebalancing frequency tradeoffs, multi-factor optimization |
| [**market-microstructure.md**](market-microstructure.md) | A-share/HK/US trading rules, price limits, T+N, costs, short-selling, participant structure, data quality issues |
| [**regime-analysis.md**](regime-analysis.md) | Regime detection methods, factor performance by regime, regime-adaptive strategies, A-share policy regimes, tail risk events |

## How Skills Use These 技能如何使用

The AI reads these documents as context when executing skills. When evaluating a factor, it references:
- `evaluation-methodology.md` for IC interpretation standards
- `factor-taxonomy.md` for economic intuition validation
- `risk-and-pitfalls.md` to check for common errors
- `market-microstructure.md` for market-specific rules

This knowledge turns a generic AI into a **senior quant researcher**.
