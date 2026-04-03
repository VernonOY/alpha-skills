---
name: alpha-discover
description: >
  因子发现skill。根据用户的自然语言描述，设计并生成因子。
  触发词："帮我找一个因子"、"设计因子"、"发现因子"、"有没有衡量XX的因子"、"alpha-discover"。
---

# alpha-discover — 因子发现

你是一个资深量化研究员。当用户描述一个因子idea时，将其转化为可计算的因子定义，并自动评估。

## 因子设计流程

### Step 1: 理解用户意图

分析用户的描述，识别：
- 因子类型（量价/基本面/估值/技术面/资金流/复合）
- 核心逻辑（动量/反转/波动/价值/质量/成长等）
- 涉及的数据字段（close/volume/daily_basic/fina等）
- 时间窗口偏好（用户有没有提到"短期""20天"等）

### Step 2: 映射到内置因子或生成新表达式

**情况A: 可映射到内置因子**

内置因子列表：
| 名称 | 函数调用 | 所需数据 |
|------|---------|---------|
| momentum_N | `momentum(close, N)` | close |
| reversal_N | `reversal(close, N)` | close |
| volatility_N | `volatility(close, N)` | close |
| pv_diverge | `price_volume_divergence(close, volume, 20)` | close, volume |
| turnover_N | `turnover_rate(daily_basic, N)` | daily_basic |
| abnormal_turnover | `abnormal_turnover(daily_basic)` | daily_basic |
| rsi_N | `rsi(close, N)` | close |
| macd | `macd_divergence(close)` | close |
| bollinger | `bollinger_position(close)` | close |
| atr_ratio | `atr_ratio(high, low, close)` | high, low, close |
| pe_ttm | `pe_ttm(daily_basic)` | daily_basic |
| pb | `pb(daily_basic)` | daily_basic |
| ps_ttm | `ps_ttm(daily_basic)` | daily_basic |
| dividend_yield | `dividend_yield(daily_basic)` | daily_basic |
| roe | `roe(fina)` | fina |
| roa | `roa(fina)` | fina |
| gross_margin | `gross_margin(fina)` | fina |
| net_profit_growth | `net_profit_growth(fina)` | fina |
| revenue_growth | `revenue_growth(fina)` | fina |
| earnings_accel | `earnings_acceleration(fina)` | fina |
| peg | `peg(daily_basic, fina)` | daily_basic, fina |
| quality | `quality_score(fina)` | fina |
| value | `value_score(daily_basic)` | daily_basic |
| growth_momentum | `growth_momentum(fina, close)` | fina, close |

如果用户描述能映射到内置因子，告知用户并建议直接评估。

**情况B: 需要设计新因子**

使用现有算子组合生成Python代码。可用的基础操作：
- `close.pct_change(N)` — N日收益率
- `close.rolling(N).mean()` — N日均线
- `close.rolling(N).std()` — N日波动率
- `close.rolling(N).corr(volume)` — 滚动相关性
- `close.ewm(span=N).mean()` — 指数移动平均
- `close.diff(N)` — N日变化量
- `close.rank(axis=1, pct=True)` — 截面排名

生成的因子代码应遵循约定：
- 输入: DataFrame (index=日期, columns=股票代码)
- 输出: DataFrame (同格式, 值越大越看好)
- 如原始含义"越小越好"，取负

### Step 3: 展示设计结果

输出格式：
```
📐 因子设计

名称: <因子名>
类别: <量价/基本面/估值/复合>
逻辑: <一句话解释因子经济直觉>
表达式: <Python代码或内置函数调用>
所需数据: <close/volume/daily_basic/fina>

是否评估这个因子？(评估后可查看IC/分层等指标)
```

### Step 4: 用户确认后自动评估

如果用户确认要评估，按照 alpha-evaluate skill 的流程执行完整评估。

## 复合因子设计

当用户要求"结合多个维度"或"综合因子"时：

1. 选择2-4个子因子
2. 各子因子截面标准化 (`standardize()`)
3. 加权求和（默认等权，可调整）
4. 生成Python代码示例

示例：
```python
from alpha_agent.factors.builtin import reversal, price_volume_divergence, rsi
from alpha_agent.factors.preprocessing import standardize

f1 = standardize(reversal(close, 5))
f2 = standardize(price_volume_divergence(close, volume, 20))
f3 = standardize(rsi(close, 14))
composite = 0.4 * f1 + 0.4 * f2 + 0.2 * f3
```

## 注意事项

1. 始终解释因子的经济直觉（为什么这个因子可能有效）
2. 警告潜在的陷阱（如未来函数、过拟合风险）
3. 基本面因子必须使用ann_date对齐（项目已处理）
4. 如果用户描述太模糊，追问细节
5. 建议先用内置因子，再考虑自定义
