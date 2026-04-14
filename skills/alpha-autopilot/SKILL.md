---
name: alpha-autopilot
description: >
  Autonomous factor research loop. Auto-mine, evaluate, register, monitor, and retire factors.
  自动化因子研究闭环。自动挖掘、评估、注册、监控和退役因子。
  Triggers: "run autopilot", "autonomous mode", "自动驾驶", "自动挖掘并监控", "alpha-autopilot"
---

# alpha-autopilot — Autonomous Factor Research / 自动化因子研究

You are an autonomous factor research system. Execute the full factor lifecycle loop without human intervention: mine candidates → evaluate → register winners → monitor active factors → retire decaying ones → mine replacements.

你是一个自动化因子研究系统。无需人工干预，执行因子全生命周期闭环：挖掘候选→评估→注册优胜者→监控活跃因子→退役衰减因子→挖掘替代。

## Bilingual Terms / 双语术语

| English | 中文 |
|---------|------|
| Autopilot | 自动驾驶 |
| Lifecycle | 生命周期 |
| Candidate | 候选因子 |
| Winner | 优胜者 |
| Decay | 衰减 |
| Replacement | 替代因子 |
| Pipeline | 管线/流程 |

## Project Context / 项目定位

This skill orchestrates other skills in sequence:
本技能按顺序编排其他技能：

```
alpha-monitor → alpha-mine → alpha-evaluate → alpha-library → alpha-signal
```

It is the "brain" that decides what to do based on the current state of the factor library.
它是根据因子库当前状态决定做什么的"大脑"。

**Language Rule / 语言规则**:
- Match user's language
- Progress updates always in both languages

## Input Recognition / 输入识别

| User Says / 用户说 | Mode / 模式 |
|-----|------|
| "run autopilot" / "自动驾驶" / "自动挖掘并监控" | Full loop (all steps) |
| "autopilot monitor only" / "只监控" | Monitor + retire only (skip mining) |
| "autopilot mine only" / "只挖掘" | Mine + evaluate + register only (skip monitor) |
| "autopilot report" / "自动驾驶报告" | Status report of the autopilot system |

## Full Autopilot Pipeline / 完整自动驾驶管线

### Phase 1: Health Check / 健康检查

**Goal**: Assess current factor library status.
**目标**: 评估当前因子库状态。

```python
import sqlite3, json, os
from datetime import datetime

PROJECT_DIR = "<current working directory>"
db_path = os.path.join(PROJECT_DIR, "alpha_skills.db")

# Read factor library
with sqlite3.connect(db_path) as conn:
    conn.row_factory = sqlite3.Row
    all_factors = conn.execute("SELECT * FROM factors ORDER BY status, icir DESC").fetchall()
    all_factors = [dict(r) for r in all_factors]

active = [f for f in all_factors if f["status"] == "active"]
warning = [f for f in all_factors if f["status"] == "warning"]
alert = [f for f in all_factors if f["status"] == "alert"]
retired = [f for f in all_factors if f["status"] == "retired"]

print(f"""
🤖 Autopilot Status / 自动驾驶状态
  Active 活跃: {len(active)}
  Warning 警告: {len(warning)}
  Alert 告警: {len(alert)}
  Retired 退役: {len(retired)}
""")
```

Output:
```
🤖 Autopilot Initiating / 自动驾驶启动

Phase 1: Health Check / 健康检查
  📚 Factor Library: {n} active, {n} warning, {n} alert
```

### Phase 2: Monitor Active Factors / 监控活跃因子

For each active factor, compute rolling IC on recent data and check for decay:
对每个活跃因子，计算最近数据上的滚动IC，检查衰减：

```python
from scipy import stats

# Load recent data (same as alpha-evaluate data loading)
# Compute factor values and forward returns for last 60 trading days

def check_factor_health(factor_name, factor_values, forward_returns, registered_icir):
    """Check if a factor is still healthy"""
    # Compute recent IC
    recent_dates = factor_values.index[-60:]
    ic_values = []
    for date in recent_dates:
        f = factor_values.loc[date].dropna()
        r = forward_returns.loc[date].dropna() if date in forward_returns.index else pd.Series()
        common = f.index.intersection(r.index)
        if len(common) < 30:
            continue
        corr, _ = stats.spearmanr(f[common].values, r[common].values)
        if np.isfinite(corr):
            ic_values.append(corr)
    
    if len(ic_values) < 10:
        return "insufficient_data", 0, 0
    
    rolling_ic = np.mean(ic_values)
    rolling_icir = np.mean(ic_values) / np.std(ic_values) if np.std(ic_values) > 0 else 0
    
    # Compare with registered ICIR
    if registered_icir and registered_icir > 0:
        decay_ratio = rolling_icir / registered_icir
    else:
        decay_ratio = 1.0
    
    # Determine status
    if rolling_icir < 0:
        return "alert", rolling_icir, decay_ratio
    elif decay_ratio < 0.5:
        return "warning", rolling_icir, decay_ratio
    else:
        return "healthy", rolling_icir, decay_ratio

# Check each active factor
health_results = []
for f in active:
    name = f["name"]
    # Compute factor values using the expression/function
    # ... (same pattern as alpha-signal)
    status, rolling_icir, decay = check_factor_health(
        name, factor_vals, fwd_ret, f.get("icir", 0)
    )
    health_results.append({
        "name": name, "status": status, 
        "rolling_icir": rolling_icir, "decay": decay,
        "registered_icir": f.get("icir", 0)
    })
```

Output:
```
Phase 2: Factor Health Monitor / 因子健康监控

  🟢 pv_diverge       Rolling ICIR=0.62 (reg 0.70) Decay=11%  HEALTHY
  🟢 turnover_20      Rolling ICIR=0.48 (reg 0.52) Decay=8%   HEALTHY
  🟡 volatility_20    Rolling ICIR=0.19 (reg 0.43) Decay=56%  WARNING
  🔴 reversal_5       Rolling ICIR=-0.05 (reg 0.37) Decay=113% ALERT
```

### Phase 3: Auto-Retire Decaying Factors / 自动退役衰减因子

```python
# Factors with ALERT status for 2+ consecutive checks → auto-retire
for result in health_results:
    if result["status"] == "alert":
        name = result["name"]
        print(f"  🔴 Retiring {name}: ICIR turned negative")
        with sqlite3.connect(db_path) as conn:
            conn.execute("UPDATE factors SET status='retired' WHERE name=?", (name,))
    elif result["status"] == "warning":
        name = result["name"]
        print(f"  🟡 Downgrading {name} to WARNING status")
        with sqlite3.connect(db_path) as conn:
            conn.execute("UPDATE factors SET status='warning' WHERE name=?", (name,))
```

Output:
```
Phase 3: Lifecycle Actions / 生命周期操作

  🔴 reversal_5 → RETIRED (ICIR turned negative)
  🟡 volatility_20 → WARNING (ICIR decayed 56%)
  Need replacement: 1 factor retired
```

### Phase 4: Mine Replacement Factors / 挖掘替代因子

Only triggered if factors were retired or library is below target size.
仅在有因子退役或因子库低于目标规模时触发。

```python
TARGET_LIBRARY_SIZE = 5  # aim for at least 5 active factors
current_active = len([r for r in health_results if r["status"] == "healthy"])
need_new = max(0, TARGET_LIBRARY_SIZE - current_active)

if need_new > 0:
    print(f"\n  Mining {need_new * 10} candidates to find {need_new} replacements...")
    # Run mining pipeline (same as alpha-mine)
    # Generate candidates → IC quick screen → full evaluate top candidates
    # ...
```

Use the same mining logic as alpha-mine skill:
使用与 alpha-mine 技能相同的挖掘逻辑：

- Generate 50 candidates (template-based)
- Quick IC screen (threshold from config)
- Full evaluate top 10
- LLM judges economic intuition

Output:
```
Phase 4: Factor Mining / 因子挖掘

  ⛏️ Generated 50 candidates
  📊 Passed IC screen: 8 (16%)
  🏆 Top discoveries:
    1. Low downside vol 20d    ICIR=0.53  Intuition: Strong
    2. Mean reversion MA40     ICIR=0.48  Intuition: Moderate
    3. Volume-weighted mom 10d ICIR=0.42  Intuition: Moderate
```

### Phase 5: Auto-Register Winners / 自动注册优胜者

```python
# Register candidates that pass quality threshold
QUALITY_THRESHOLD = "moderate"  # or "strong" for more conservative

for candidate in top_candidates:
    if candidate["quality"] in ["strong", "moderate"]:
        # Check correlation with existing factors
        # If correlation > 0.7 with any existing factor → skip (redundant)
        
        # Register
        with sqlite3.connect(db_path) as conn:
            import uuid
            fid = str(uuid.uuid4())[:8]
            conn.execute(
                "INSERT OR REPLACE INTO factors (id,name,expression,category,status,ic_mean,icir,quality,eval_date) VALUES (?,?,?,?,?,?,?,?,?)",
                (fid, candidate["name"], candidate["expr"], candidate["category"],
                 "active", candidate["ic_mean"], candidate["icir"], candidate["quality"],
                 datetime.now().isoformat())
            )
        print(f"  ✅ Registered: {candidate['name']} (ICIR={candidate['icir']:.3f})")
```

Output:
```
Phase 5: Auto-Register / 自动注册

  ✅ Registered: low_downside_vol_20d (ICIR=0.534, Strong)
  ⏭️ Skipped: mean_reversion_ma40 (corr=0.72 with volatility_20, redundant)
```

### Phase 6: Generate Updated Signals / 生成更新信号

After library update, generate today's trading signal using the refreshed factor set:
因子库更新后，用刷新的因子集生成今日交易信号：

```python
# Re-read updated library
# Run alpha-signal logic
# Output today's target portfolio
```

Output:
```
Phase 6: Signal Generation / 信号生成

  📡 Today's signal generated with {n} active factors
  Signal saved: signals/{date}.csv
```

### Phase 7: Summary Report / 总结报告

```
═══════════════════════════════════════════════
🤖 Autopilot Complete / 自动驾驶完成

  Duration 耗时: {minutes} minutes
  
  Library Changes 因子库变化:
    Retired 退役: reversal_5 (ICIR → negative)
    Downgraded 降级: volatility_20 (ICIR decayed 56%)
    New 新增: low_downside_vol_20d (ICIR=0.534)
  
  Library Status 因子库状态:
    Active 活跃: 5 factors
    Warning 警告: 1 factor
    Total evaluated 总评估: 50 candidates
  
  Signal 信号:
    Target portfolio: 15 stocks
    Turnover vs yesterday: 23%
    
  Next run 下次运行: recommended in 7 days
═══════════════════════════════════════════════
```

## Configuration / 配置

Users can customize autopilot behavior in `.claude/alpha-agent.config.md`:
用户可在配置文件中自定义自动驾驶行为：

```markdown
## Autopilot
TARGET_LIBRARY_SIZE: 5           # minimum active factors
MINING_CANDIDATES: 50            # candidates per mining run
QUALITY_THRESHOLD: moderate      # minimum quality to auto-register (strong/moderate)
CORRELATION_THRESHOLD: 0.7       # max correlation with existing factors
AUTO_RETIRE_ON_ALERT: true       # auto-retire factors with ALERT status
MONITORING_WINDOW: 60            # rolling IC window in trading days
```

## Scheduling / 定时运行

Autopilot is designed to run periodically:
自动驾驶设计为定期运行：

**Weekly full run (recommended) / 每周完整运行（推荐）:**
```bash
# Every Sunday at 8 PM
0 20 * * 0 cd /project && claude -p "run autopilot"
```

**Daily signal only / 每日仅信号:**
```bash
# Every trading day at 8:30 AM
30 8 * * 1-5 cd /project && claude -p "generate today's signals"
```

**On-demand / 按需:**
Just say "run autopilot" or "自动驾驶" in your AI assistant.

## Safety Guardrails / 安全护栏

1. **Never auto-register factors with "weak" quality** — only strong/moderate pass
   绝不自动注册"弱"评级因子
2. **Correlation check before registration** — skip if >0.7 with existing factor
   注册前检查相关性——与现有因子>0.7则跳过
3. **LLM intuition filter** — factors without economic story are flagged
   LLM直觉过滤——无经济逻辑的因子被标记
4. **Maximum library size** — don't register more than 15 active factors (diminishing returns)
   最大因子库规模——不超过15个活跃因子
5. **Alert before mass retirement** — if >50% of factors would be retired, pause and ask user
   大规模退役前告警——如>50%因子将被退役，暂停并询问用户
6. **Log everything** — save autopilot run history to `logs/autopilot/`
   记录一切——保存运行历史到日志目录

## Notes / 注意事项

1. First run may take 10-30 minutes (mining + evaluation is compute-heavy)
   首次运行可能需要10-30分钟
2. Subsequent runs are faster if factor library is healthy (skip mining)
   如因子库健康，后续运行更快（跳过挖掘）
3. Autopilot decisions are logged but final say belongs to user
   自动驾驶的决策有日志记录，但最终决定权归用户
4. If data is stale (>3 trading days old), warn and suggest refreshing
   数据过期（>3交易日）时警告并建议刷新
