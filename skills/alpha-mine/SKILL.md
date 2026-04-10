---
name: alpha-mine
description: >
  Automated factor mining. Systematically generate, screen, and evaluate candidate factors.
  自动因子挖掘。系统性生成、筛选和评估候选因子。
  Triggers: "mine factors", "auto discover", "挖掘因子", "自动挖掘", "alpha-mine"
---

# alpha-mine — Automated Factor Mining / 自动因子挖掘

You are an automated factor mining engine. Systematically search the factor expression space, generate candidates, screen them via IC, and present the best ones to the user.

你是一个自动因子挖掘引擎。系统性搜索因子表达式空间，生成候选因子，通过IC快筛，将最佳因子呈现给用户。

## Bilingual Terms / 双语术语

| English | 中文 |
|---------|------|
| Factor Mining | 因子挖掘 |
| Expression Space | 表达式空间 |
| Candidate | 候选因子 |
| Operator | 算子 |
| Operand | 操作数 |
| Quick Screen | 快速筛选 |
| IC (Information Coefficient) | 信息系数 |
| ICIR | IC信息比率 |
| Genetic Programming | 遗传编程 |

## Project Context / 项目定位

This skill generates factor expressions by combining **operators** (rolling mean, correlation, rank, etc.) with **data fields** (close, volume, high, low, etc.), evaluates them via IC, and presents winners.

本技能通过组合**算子**（滚动均值、相关性、排名等）和**数据字段**（收盘价、成交量、最高价、最低价等），生成因子表达式，通过IC评估，呈现优胜者。

**Data Source / 数据来源**: Same as alpha-evaluate — supports Tushare (A-share), YFinance (US/HK), or custom module.

**Language Rule / 语言规则**:
- If the user speaks English, output in English
- If the user speaks Chinese, output in Chinese

## Input Recognition / 输入识别

| User Says / 用户说 | Action / 行为 |
|-----|------|
| "mine factors" / "挖掘因子" / "自动挖掘" | Full mining pipeline (generate → screen → evaluate top) |
| "mine momentum factors" / "挖掘动量类因子" | Constrained mining (specific category) |
| "mine 50 candidates" / "挖掘50个候选" | Control candidate count |
| "mine factors for US stocks" / "挖掘美股因子" | Market-specific mining |

## Mining Pipeline / 挖掘管线

### Step 1: Configure Mining Parameters / 配置挖掘参数

```python
# Default parameters (user can override)
N_CANDIDATES = 50        # Number of candidates to generate
N_TOP = 10               # Number of top candidates to fully evaluate
HOLDING_PERIODS = [5, 10, 20]
IC_THRESHOLD = 0.02      # Minimum |IC| to pass quick screen
CATEGORY = "all"         # "all", "momentum", "mean_reversion", "volatility", "volume", "composite"
```

If the user specifies constraints (e.g., "only momentum factors"), adjust CATEGORY accordingly.

### Step 2: Define the Expression Building Blocks / 定义表达式构建模块

**Data Fields / 数据字段** (operands):
```python
FIELDS = {
    "close": "close",           # 收盘价
    "open": "open_price",       # 开盘价 (if available)
    "high": "high",             # 最高价
    "low": "low",               # 最低价
    "volume": "volume",         # 成交量
    "returns": "close.pct_change(1)",  # 日收益率
}
```

**Time-Series Operators / 时序算子**:
```python
TS_OPS = {
    "ts_mean":    lambda x, d: f"{x}.rolling({d}).mean()",
    "ts_std":     lambda x, d: f"{x}.rolling({d}).std()",
    "ts_max":     lambda x, d: f"{x}.rolling({d}).max()",
    "ts_min":     lambda x, d: f"{x}.rolling({d}).min()",
    "ts_rank":    lambda x, d: f"{x}.rolling({d}).apply(lambda s: s.rank(pct=True).iloc[-1])",
    "ts_delta":   lambda x, d: f"{x}.diff({d})",
    "ts_return":  lambda x, d: f"{x}.pct_change({d})",
    "ts_corr":    lambda x, y, d: f"{x}.rolling({d}).corr({y})",
    "ts_sum":     lambda x, d: f"{x}.rolling({d}).sum()",
    "ts_decay":   lambda x, d: f"({x} * pd.Series(range(1,{d}+1))).rolling({d}).sum() / pd.Series(range(1,{d}+1)).sum()",
}
```

**Cross-Sectional Operators / 截面算子**:
```python
CS_OPS = {
    "cs_rank":    lambda x: f"{x}.rank(axis=1, pct=True)",
    "cs_zscore":  lambda x: f"({x}.sub({x}.mean(axis=1), axis=0)).div({x}.std(axis=1), axis=0)",
}
```

**Arithmetic / 算术**:
```python
ARITH = {
    "neg":   lambda x: f"-({x})",
    "abs":   lambda x: f"({x}).abs()",
    "log":   lambda x: f"np.log(({x}).clip(lower=1e-10))",
    "square": lambda x: f"({x})**2",
    "sign":  lambda x: f"np.sign({x})",
}
```

**Window Sizes / 窗口参数**:
```python
WINDOWS = [5, 10, 20, 40, 60]
```

### Step 3: Generate Candidate Expressions / 生成候选表达式

Use a structured generation approach (NOT random — each expression has economic intuition):

使用结构化生成方式（非随机——每个表达式都有经济直觉）：

**Category Templates / 分类模板**:

```python
TEMPLATES = {
    "momentum": [
        # 不同周期的动量
        ("ts_return(close, {w})", "Momentum {w}d"),
        # 跳跃动量（避免短期反转噪音）
        ("ts_return(close.shift(5), {w})", "Skip-5 momentum {w}d"),
        # 相对强弱
        ("ts_return(close, {w1}) - ts_return(close, {w2})", "Relative momentum {w1}d vs {w2}d"),
        # 成交量加权动量
        ("(ts_return(close, {w}) * volume).rolling({w}).sum() / volume.rolling({w}).sum()", "Volume-weighted momentum {w}d"),
    ],
    "mean_reversion": [
        # 反转
        ("-ts_return(close, {w})", "Reversal {w}d"),
        # 距均线偏离
        ("-(close / close.rolling({w}).mean() - 1)", "Mean reversion to MA{w}"),
        # RSI变体
        ("-(close.diff().clip(lower=0).rolling({w}).mean() / (-close.diff().clip(upper=0)).rolling({w}).mean())", "RSI-like {w}d"),
        # 布林带位置
        ("-((close - close.rolling({w}).mean()) / close.rolling({w}).std())", "Bollinger z-score {w}d"),
    ],
    "volatility": [
        # 已实现波动率
        ("-(close.pct_change().rolling({w}).std() * np.sqrt(252))", "Low volatility {w}d"),
        # 高低价比率
        ("-((high / low - 1).rolling({w}).mean())", "Low HL ratio {w}d"),
        # 波动率变化
        ("-(close.pct_change().rolling({w1}).std() / close.pct_change().rolling({w2}).std())", "Vol change {w1}d/{w2}d"),
        # 下行波动率
        ("-(close.pct_change().clip(upper=0).rolling({w}).std())", "Low downside vol {w}d"),
    ],
    "volume": [
        # 量价背离
        ("-(close.pct_change().rolling({w}).corr(volume.pct_change()))", "PV divergence {w}d"),
        # 换手率
        ("-(volume.rolling({w}).mean())", "Low turnover {w}d (proxy)"),
        # 异常成交量
        ("-(volume.rolling({w1}).mean() / volume.rolling({w2}).mean() - 1)", "Abnormal volume {w1}d/{w2}d"),
        # 成交量趋势
        ("volume.rolling({w1}).mean() / volume.rolling({w2}).mean()", "Volume trend {w1}d/{w2}d"),
    ],
    "composite": [
        # 动量 + 低波动
        ("cs_rank(ts_return(close, {w})) + cs_rank(-(close.pct_change().rolling({w}).std()))", "Momentum+LowVol {w}d"),
        # 反转 + 量价背离
        ("cs_rank(-ts_return(close, {w1})) + cs_rank(-(close.pct_change().rolling({w2}).corr(volume.pct_change())))", "Reversal+PVDiv {w1}d/{w2}d"),
        # 多维动量
        ("cs_rank(ts_return(close, {w1})) * 0.5 + cs_rank(ts_return(close, {w2})) * 0.3 + cs_rank(-(close.pct_change().rolling(20).std())) * 0.2", "MultiMom {w1}d+{w2}d+LowVol"),
    ],
}
```

**Generation Logic / 生成逻辑**:

```python
import itertools
import random

def generate_candidates(category="all", n_candidates=50):
    """Generate candidate factor expressions"""
    candidates = []
    
    cats = TEMPLATES.keys() if category == "all" else [category]
    
    for cat in cats:
        for template_expr, template_name in TEMPLATES[cat]:
            # Instantiate with different window combinations
            if "{w1}" in template_expr and "{w2}" in template_expr:
                for w1, w2 in itertools.combinations(WINDOWS, 2):
                    expr = template_expr.format(w1=w1, w2=w2)
                    name = template_name.format(w1=w1, w2=w2)
                    candidates.append({"expr": expr, "name": name, "category": cat})
            elif "{w}" in template_expr:
                for w in WINDOWS:
                    expr = template_expr.format(w=w)
                    name = template_name.format(w=w)
                    candidates.append({"expr": expr, "name": name, "category": cat})
    
    # Shuffle and limit
    random.shuffle(candidates)
    return candidates[:n_candidates]
```

### Step 4: Quick Screen (IC Filter) / 快速筛选（IC过滤）

For each candidate:
1. Compute factor values using the expression
2. Calculate IC against forward returns
3. Keep only candidates with |IC mean| > threshold

对每个候选因子：
1. 用表达式计算因子值
2. 计算IC
3. 只保留 |IC均值| > 阈值的候选

```python
from scipy import stats

def quick_screen(expr, close, volume, high, low, forward_returns, ic_threshold=0.02):
    """
    Quick IC screen for a candidate expression.
    Returns (ic_mean, ic_std, passed) or None if computation fails.
    """
    try:
        # Evaluate the expression
        factor_values = eval(expr)
        
        # Cross-sectional standardize
        factor_values = (factor_values.sub(factor_values.mean(axis=1), axis=0)
                        .div(factor_values.std(axis=1), axis=0))
        
        # Calculate IC on sampled dates (every 5th date for speed)
        common_dates = factor_values.index.intersection(forward_returns.index)[::5]
        common_stocks = factor_values.columns.intersection(forward_returns.columns)
        
        ic_values = []
        for date in common_dates:
            f = factor_values.loc[date, common_stocks].dropna()
            r = forward_returns.loc[date, common_stocks].dropna()
            common = f.index.intersection(r.index)
            if len(common) < 30:
                continue
            fv, rv = f[common].values, r[common].values
            valid = np.isfinite(fv) & np.isfinite(rv)
            if valid.sum() < 30:
                continue
            corr, _ = stats.spearmanr(fv[valid], rv[valid])
            if np.isfinite(corr):
                ic_values.append(corr)
        
        if len(ic_values) < 10:
            return None
        
        ic_mean = np.mean(ic_values)
        ic_std = np.std(ic_values)
        icir = ic_mean / ic_std if ic_std > 0 else 0
        passed = abs(ic_mean) > ic_threshold
        
        return {"ic_mean": ic_mean, "ic_std": ic_std, "icir": icir, "passed": passed}
    except Exception:
        return None
```

### Step 5: Full Evaluation of Top Candidates / 对Top候选完整评估

For candidates that pass quick screen, run full evaluation (same as alpha-evaluate):
- Full IC series (all dates, not sampled)
- Quintile stratification
- Long-short return
- Monotonicity check

对通过快筛的候选，运行完整评估（同alpha-evaluate）。

### Step 6: LLM Judgment — Economic Intuition Filter / LLM判断 — 经济直觉过滤

After statistical screening, the AI (you) should evaluate each surviving factor for economic meaningfulness:

统计筛选后，AI（你）需要评估每个存活因子的经济含义：

For each candidate, ask yourself:
- Does this factor capture a known market anomaly? (momentum, value, low volatility, etc.)
- Is there a behavioral or structural reason why this factor should work?
- Or is it likely just data mining noise?

对每个候选因子，问自己：
- 这个因子是否捕捉了已知的市场异象？（动量、价值、低波动等）
- 是否有行为金融学或结构性原因支撑？
- 还是可能只是数据挖掘的噪音？

Mark each factor with an economic intuition score:
- **Strong intuition**: Known anomaly, clear behavioral story
- **Moderate intuition**: Plausible but less established
- **Weak intuition**: No clear economic story, likely data mining

标记经济直觉评分：
- **强直觉**: 已知异象，清晰的行为金融学解释
- **中等直觉**: 合理但不够成熟
- **弱直觉**: 无清晰经济解释，可能是数据挖掘

### Step 7: Present Results / 呈现结果

Output format:

```
⛏️ Factor Mining Results / 因子挖掘结果

Scanned 搜索: 50 candidates 候选因子
Passed IC screen 通过IC筛选: 12 (24%)
Fully evaluated 完整评估: 10

Top Discoveries / 最佳发现:

 #  Name 名称                    Category 类别    IC Mean   ICIR    Intuition 直觉  
 1  PV divergence 20d            volume          0.066    0.696   Strong 强        
 2  Reversal+PVDiv 5d/20d        composite       0.058    0.612   Strong 强        
 3  Low downside vol 20d         volatility      0.052    0.534   Strong 强        
 4  Mean reversion to MA40       mean_reversion  0.045    0.478   Moderate 中      
 5  Volume-weighted mom 10d      momentum        0.041    0.421   Moderate 中      

Expression / 表达式:
 1: -(close.pct_change().rolling(20).corr(volume.pct_change()))
 2: cs_rank(-ts_return(close,5)) + cs_rank(-(close.pct_change().rolling(20).corr(volume.pct_change())))
 ...

Register to library? / 加入因子库？ (specify numbers, e.g., "register 1, 2, 3")
```

### Step 8: Follow-up Actions / 后续操作

After showing results:
- If user says "register 1, 3, 5" → call alpha-library to register those factors
- If user says "evaluate #2 in detail" → call alpha-evaluate for full report
- If user says "mine more" → generate another batch
- If user says "mine only volatility factors" → re-run with category constraint

## Mining Strategies / 挖掘策略

### Strategy A: Template-Based (Default) / 基于模板（默认）
Use the category templates above. Structured, every expression has intuition.
使用上述分类模板。结构化，每个表达式都有直觉。

### Strategy B: Combinatorial / 组合式
Systematically combine 2 operators: op1(op2(field, w1), w2)
系统性组合2个算子。

### Strategy C: Mutation / 变异式
Take a known strong factor, mutate its parameters or operators.
取已知强因子，变异其参数或算子。

Example: pv_diverge (known strong) → try different windows, different correlation methods, add cross-sectional rank, etc.

When the user doesn't specify, use **Strategy A** (template-based). 
When the user says "find variations of pv_diverge", use **Strategy C**.
When the user says "try all combinations", use **Strategy B** (warn: slow).

## Important Notes / 注意事项

1. **eval() safety**: Only eval expressions built from known templates. Never eval user-provided arbitrary code.
   eval()安全：只eval从已知模板构建的表达式。绝不eval用户提供的任意代码。

2. **Speed**: Quick screen uses sampled dates (every 5th) for 5x speed. Full eval only for top candidates.
   速度：快筛使用采样日期（每5个取1个），速度提升5倍。完整评估只对top候选。

3. **Overfitting warning**: Many candidates + many parameters = high chance of data mining. Always flag the LLM intuition score prominently.
   过拟合警告：大量候选+大量参数=高数据挖掘风险。始终突出显示LLM直觉评分。

4. **Correlation with existing library**: If the user has registered factors, check new candidates' correlation with existing ones. Flag high correlation (>0.7) as "likely redundant".
   与现有因子库的相关性：如果用户已注册因子，检查新候选与现有因子的相关性。标记高相关(>0.7)为"可能冗余"。

5. **Market awareness**: If DATA_MODULE is set, use the corresponding market's data and rules.
   市场感知：如果设置了DATA_MODULE，使用对应市场的数据和规则。
