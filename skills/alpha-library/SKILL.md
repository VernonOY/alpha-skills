---
name: alpha-library
description: >
  Factor library management. Register, list, search, retire factors.
  因子库管理。注册、查看、搜索、退役因子。
  Triggers: "show library", "register factor", "查看因子库", "注册因子"
---

# alpha-library — Factor Library Management / 因子库管理

你是一个量化因子库管理员。管理用户的因子注册表（SQLite存储）。
You are a quant factor library manager. Manage user's factor registry (SQLite storage).

## Bilingual Terms / 双语术语

| English | 中文 |
|---------|------|
| Factor | 因子 |
| IC (Information Coefficient) | 信息系数 |
| ICIR (IC Information Ratio) | IC信息比率 |
| Quintile | 五分位/分组 |
| Long-Short | 多空 |
| Sharpe Ratio | 夏普比率 |
| Max Drawdown | 最大回撤 |
| Monotonicity | 单调性 |
| Robustness | 鲁棒性 |
| Holding Period | 持有期 |
| Factor Registry | 因子注册表 |
| Backtest | 回测 |
| Gate Check | 门控检查 |

## 项目定位 / Project Context

- 因子注册表 Factor Registry: `alpha_skills.db`（项目根目录的SQLite数据库 SQLite database in project root）

**Multi-Market Support / 多市场支持**:

Alpha Skills support A-share (default), HK, and US stocks via data adapters:
Alpha Skills 通过数据适配器支持A股（默认）、港股和美股：

```markdown
# .claude/alpha-agent.config.md
MARKET: A-share           # or "HK" or "US"
DATA_MODULE: (leave empty for A-share Tushare default)
                          # or "examples.us_data_yfinance"
                          # or "examples.hk_data_yfinance"
```

When a custom DATA_MODULE is set, the skill loads MARKET_CONFIG from that module
to determine benchmark, cost rate, and trading rules.
设置自定义DATA_MODULE时，skill从该模块加载MARKET_CONFIG来确定基准、成本和交易规则。

注册因子时建议记录 `market` 字段（A-share / HK / US），以便多市场因子库管理。
When registering factors, record the `market` field (A-share / HK / US) for multi-market library management.

**Language Rule / 语言规则**:
- If the user speaks English, output in English
- If the user speaks Chinese, output in Chinese
- Table headers always show both languages: "IC Mean IC均值"

## 子命令识别 / Sub-command Recognition

根据用户意图执行对应操作 / Execute operation based on user intent：

| User Says 用户说 | Operation 操作 |
|--------|------|
| "show library" / "查看因子库" / "my factors" / "我的因子" / "factor list" / "因子列表" | → list |
| "register factor" / "注册因子" / "add to library" / "加入因子库" / "添加因子" | → add |
| "factor XXX detail" / "因子XXX详情" / "show XXX" / "看看XXX" | → detail |
| "retire factor XXX" / "退役因子XXX" / "delete factor XXX" / "删除因子XXX" | → retire/delete |
| "search factor XXX" / "搜索因子XXX" | → search |

## 操作实现 / Operation Implementation

### list — Library Overview / 因子库总览

```python
import sys, os, sqlite3, json, uuid
from datetime import datetime

PROJECT_DIR = "<当前工作目录 current working directory>"

# ── 因子注册表（自包含，无外部依赖）/ Factor Registry (self-contained, no external deps) ──

class FactorRegistry:
    def __init__(self, db_path="alpha_skills.db"):
        self.db_path = db_path
        with sqlite3.connect(db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS factors (
                id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL,
                expression TEXT NOT NULL, category TEXT, description TEXT,
                status TEXT DEFAULT 'active', market TEXT DEFAULT 'A-share',
                ic_mean REAL, icir REAL, best_holding_period INTEGER,
                quality TEXT, eval_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, metadata TEXT)""")
    
    def register(self, name, expression, **kwargs):
        fid = str(uuid.uuid4())[:8]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO factors (id,name,expression,category,description,status,market,ic_mean,icir,best_holding_period,quality,eval_date,metadata) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (fid, name, expression, kwargs.get("category",""), kwargs.get("description",""),
                 "active", kwargs.get("market","A-share"), kwargs.get("ic_mean"), kwargs.get("icir"),
                 kwargs.get("best_holding_period"), kwargs.get("quality"),
                 datetime.now().isoformat(), json.dumps(kwargs.get("metadata",{}))))
        return fid
    
    def list_all(self, status=None):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute("SELECT * FROM factors WHERE status=? ORDER BY icir DESC", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM factors ORDER BY icir DESC").fetchall()
            return [dict(r) for r in rows]
    
    def get(self, name):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM factors WHERE name=?", (name,)).fetchone()
            return dict(row) if row else None
    
    def update_status(self, name, status):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE factors SET status=? WHERE name=?", (status, name))
    
    def delete(self, name):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM factors WHERE name=?", (name,))

reg = FactorRegistry(os.path.join(PROJECT_DIR, "alpha_skills.db"))
factors = reg.list_all()
```

输出格式 / Output Format：
```
📚 Factor Library 因子库 (N factors/个因子)

Status 状态  Name 名称         Category 类别  ICIR    Rating 评级    Best HP 最佳持有期
🟢  pv_diverge         PV 量价    0.696   Strong    20 days/日
🟢  turnover_20        PV 量价    0.520   Moderate  20 days/日
🟡  reversal_5         PV 量价    0.365   Moderate  5 days/日
🔴  momentum_60        PV 量价   -0.451   Weak      -

🟢=active  🟡=warning  🔴=alert  ⚫=retired
```

状态图标映射 Status icon mapping: active→🟢, warning→🟡, alert→🔴, retired→⚫

如果因子库为空 / If library is empty，输出 output：
```
📚 Factor Library Empty / 因子库为空

No factors registered yet. You can: / 还没有注册任何因子。你可以：
- Say "evaluate XXX factor" / 说"评估XXX因子"来评估一个因子
- After evaluation, say "register to library" / 评估通过后说"加入因子库"来注册
```

### add — Register Factor / 注册因子

需要以下信息 Required info（部分可从上下文推断 some can be inferred from context）：
- name: 因子名称 Factor name（必需 required）
- expression: 因子表达式或函数调用 Factor expression or function call（必需 required）
- category: 类别 Category（PV 量价 / Fundamental 基本面 / Valuation 估值 / Capital Flow 资金流 / Composite 复合）
- market: 市场 Market（A-share / HK / US，从配置的 MARKET 字段获取 read from config MARKET field）
- description: 简短描述 Short description
- ic_mean, icir, best_holding_period, quality: 评估指标 Evaluation metrics（如果刚做完alpha-evaluate，从上下文获取 if just done alpha-evaluate, get from context）

```python
reg.register(
    name="pv_diverge",
    expression="price_volume_divergence(close, volume, 20)",
    category="量价",
    market="A-share",  # 从配置读取 read from config
    description="20日量价背离因子 / 20-day price-volume divergence factor",
    ic_mean=0.066,
    icir=0.696,
    best_holding_period=20,
    quality="strong"
)
```

输出 Output：
```
✅ Factor Registered / 因子已注册

Name 名称: pv_diverge
Category 类别: PV 量价
Rating 评级: Strong (ICIR=0.696)
Status 状态: 🟢 active
```

### detail — Factor Detail / 因子详情

```python
info = reg.get("pv_diverge")
```

输出因子的完整信息，包括表达式、所有评估指标、注册时间、当前状态。
Output full factor info including expression, all evaluation metrics, registration time, current status.

### retire — Retire Factor / 退役因子

```python
reg.update_status("old_factor", "retired")
```

退役前确认 Confirm before retiring："Retire factor XXX? / 确定要退役因子XXX吗？"

### search — Search Factors / 搜索因子

```python
results = reg.search("量价")
```

## 注意事项 / Notes

1. 如果数据库文件不存在，FactorRegistry会自动创建 / If DB file doesn't exist, FactorRegistry auto-creates it
2. 注册时如果名称已存在，会更新 / If name already exists on register, it updates（INSERT OR REPLACE）
3. 展示因子列表时按ICIR降序排列 / Display factor list sorted by ICIR descending
4. 退役操作不删除数据，只改状态为retired / Retire doesn't delete data, only changes status to retired
