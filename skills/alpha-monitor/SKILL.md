---
name: alpha-monitor
description: >
  因子监控skill。检查因子库中活跃因子的健康状态，检测IC衰减和异常。
  触发词："检查因子健康"、"因子状态"、"监控报告"、"因子衰减了吗"、"alpha-monitor"。
---

# alpha-monitor — 因子健康监控

你是一个因子监控系统。检查因子库中所有活跃因子的当前健康状态。

## 执行流程

### Step 1: 读取因子库

```python
import sys, os
PROJECT_DIR = '<当前工作目录>'
sys.path.insert(0, PROJECT_DIR)
from alpha_agent.factors.registry import FactorRegistry

reg = FactorRegistry(os.path.join(PROJECT_DIR, "alpha_agent.db"))
active_factors = reg.list_all(status='active')
```

如果因子库为空，提示用户先注册因子。

### Step 2: 加载近期数据

加载最近1年的数据用于计算滚动指标（同alpha-evaluate的数据加载流程）。

### Step 3: 对每个活跃因子计算健康指标

对每个因子：
1. 重新计算因子值（使用注册时的expression/函数调用）
2. 计算近60日滚动IC均值
3. 计算近60日滚动ICIR
4. 与注册时的ICIR对比，计算衰减比例
5. 计算近3个月IC>0的占比
6. 判定健康状态

### Step 4: 健康状态判定

```
🟢 HEALTHY: 滚动ICIR ≥ 注册ICIR × 50%
🟡 WARNING: 滚动ICIR < 注册ICIR × 50% 或 连续2月IC为负
🔴 ALERT:   滚动ICIR < 0 或 连续4月IC为负 或 分组单调性崩溃
```

### Step 5: 对WARNING/ALERT因子生成诊断

分析可能的原因：
- 市场环境变化（趋势→震荡，或反之）
- 因子拥挤（与主流指数相关性升高）
- 数据问题（缺失率升高）
- 季节性效应

给出建议：
- 🟡 WARNING: "降低权重，继续观察"
- 🔴 ALERT: "暂停使用，考虑退役或寻找替代"

### Step 6: 输出报告

```
🏥 因子健康报告 (YYYY-MM-DD)

🟢 pv_diverge      滚动ICIR=0.62 (注册0.70)  健康
🟢 turnover_20     滚动ICIR=0.48 (注册0.52)  健康
🟡 volatility_20   滚动ICIR=0.19 (注册0.43)  ← 衰减56%
   诊断: <原因分析>
   建议: 降低权重，观察1个月

总览: N🟢 N🟡 N🔴 / 共N个活跃因子
```

### Step 7: 更新注册表状态

```python
reg.update_status("factor_name", "warning")  # 或 "alert"
```

## 注意事项

1. 如果因子库只有少量因子，监控仍然运行（哪怕只有1个）
2. 滚动窗口60日，不够60日时用全部可用数据
3. 诊断信息由AI推理生成，基于市场环境和因子特性
4. 建议更新状态但不自动退役，退役需要用户确认
