# 快速参考指南 - 投资分析系统

## 核心概念速记

### 系统三层架构
```
Layer 1: 数据采集 (Data Sources)
         ↓
Layer 2: 多维分析 (11 Dimensions)
         ├─ 历史点位 (Historical Position)
         ├─ 技术面 (Technical)
         ├─ 资金面 (Capital Flow)
         └─ ... (更多维度)
         ↓
Layer 3: 投资决策 (Investment Judgment)
         ├─ 方向判断 (Direction)
         ├─ 仓位建议 (Position)
         ├─ 操作策略 (Strategies)
         └─ 持有建议 (Hold Suggestion)
```

---

## 快速判断规则表

### Rule 1: 方向判断 (Direction)
```
条件                           判断          仓位
────────────────────────────────────────────────
up_prob ≥ 70% & risk < 0.3    强烈看多✅✅  70-80%
up_prob ≥ 60% & risk < 0.5    看多✅       60-70%
up_prob ≥ 50% & risk < 0.6    中性偏多⚖️  50-60%
up_prob < 40% | risk > 0.7    看空🔴      20-30%
其他                          中性⚖️      40-50%
```

### Rule 2: 风险评分 (Risk Score)
```
风险因子              权重    触发条件
──────────────────────────────────────
下跌概率风险          30%    下跌概率>60%→+0.2
MACD顶背离           15%    检测到顶背离→+0.15
RSI超买风险           10%    RSI>80→+0.1, >70→+0.05
MA20偏离              10%    |偏离|>15%→+0.1
资金面风险            20%    流出>40%→+0.1

风险等级: <0.3低 | 0.3-0.5中 | 0.5-0.7高 | ≥0.7极高
```

### Rule 3: 持有建议 (Hold Suggestion)
```
优先级高→低

1. 看空+低风险+非避险资产 → "✅ 低风险,可以持有" ⭐ 特殊逻辑
2. 高风险 → "⚠️ 高风险,强烈建议减仓"
3. 低风险 → "✅ 低风险,可以持有"
4. 高上涨概率 → "历史概率支持,可以配置"
5. 其他 → 根据技术面补充

避险资产特殊提示: "💰 避险资产,关注地缘政治"
加密资产特殊提示: "₿ 波动较大,控制仓位"
```

---

## 关键指标对照表

| 指标 | 极端 | 严重 | 正常 | 轻微 |
|------|------|------|------|------|
| 上涨概率 | >75% | 60-75% | 40-60% | <25% |
| 风险评分 | ≥0.7 | 0.5-0.7 | 0.3-0.5 | <0.3 |
| RSI | >80 | 70-80 | 30-70 | <30 |
| MACD | 强死叉 | 死叉 | 持平 | 金叉 |
| MA偏离 | >20% | 15-20% | <10% | <5% |

---

## 数据字段映射

### 历史分析 (historical_analysis)
```
{
  'current_price': 当前价格,
  'current_date': 数据日期,
  'current_change_pct': 今日涨跌%,
  'similar_periods_count': 相似点位数,
  '20d': {
    'up_prob': 20日上涨概率,
    'mean_return': 平均预期收益,
    'median_return': 中位数收益,
    'confidence': 置信度 (0-1)
  },
  '60d': { ... }  # 60日数据
}
```

### 风险评估 (risk_assessment)
```
{
  'risk_score': 综合风险评分 (0-1),
  'risk_level': 风险等级 (低/中/高/极高),
  'risk_factors': [风险因素列表]
}
```

### 综合判断 (comprehensive_judgment)
```
{
  'direction': 方向 (强烈看多/看多/中性/看空),
  'recommended_position': 建议仓位 (xx-xx%),
  'strategies': [操作策略列表],
  'combo_strategy_match': {组合策略匹配度}
}
```

---

## 常见场景应答

### Scenario 1: 看多但风险高
```
症状: up_prob > 60% but risk_score > 0.5
原因: 可能是MACD顶背离或RSI超买
建议: 
  1. 选择低风险的个股参与(而不是指数)
  2. 等待回调到MA20以下再介入
  3. 控制仓位在建议的50-60%以内
```

### Scenario 2: 看空但需要持有
```
症状: direction='看空' but risk_score < 0.3
原因: 避险资产(黄金)或概率35-40%的中性资产
建议:
  1. 这是正常的,风险低的资产可以继续持有
  2. 减少仓位到20-30%左右
  3. 关注转折信号(RSI从超卖反弹)
```

### Scenario 3: 中性但样本不足
```
症状: confidence < 0.3
原因: 相似点位<10个,置信度低
建议:
  1. 参考技术面和基本面作为辅助
  2. 选择中性仓位(40-50%)观望
  3. 等待样本增加(数据越多越可靠)
```

---

## 投资决策流程图

```
开始报告
  ↓
查看汇总表格 ← 快速扫描全局
  ↓ 锁定目标资产
查看该资产详情
  ├─ 方向判断 + 建议仓位 ← 核心决策
  ├─ 风险等级 ← 风险评估
  └─ 持有建议 ← 快速建议
  ↓
深入分析(如需要)
  ├─ 历史点位概率 ← 胜率
  ├─ 技术指标 ← 时机
  ├─ 操作策略 ← 细节
  └─ 风险因素 ← 止损
  ↓
确认决策并执行
  ├─ 买入: 按建议仓位分批介入
  ├─ 持有: 监控风险因素变化
  └─ 止损: 遵守风险等级约束
```

---

## 数据刷新与更新

| 频率 | 组件 | 更新延迟 |
|------|------|---------|
| 日更 | 历史点位、技术指标、资金面 | T+1 |
| 周更 | 汇总报告、投资建议 | T+2 |
| 实时 | 当前价格、涨跌幅 | 实时 |
| 按需 | 宏观环境、特殊指标 | 变化时 |

---

## 常见误区与纠正

| 误区 | 影响 | 纠正方法 |
|------|------|---------|
| 只看上涨概率忽视风险 | 高风险操作 | 必须同时查看risk_score |
| 看空就全部卖出 | 错过避险机会 | 看风险等级,低风险可持有 |
| 中性仓位40-50% | 过于保守 | 根据方向调整到20-80% |
| 单个技术指标决策 | 容易踩坑 | 必须多因子确认 |
| 忽视置信度 | 虚假信号 | 置信度<50%的信号参考即可 |

---

## 文件路径快速查询

| 文件 | 路径 | 功能 |
|------|------|------|
| 统一分析 | scripts/unified_analysis/run_unified_analysis.py | 全量分析 |
| 资产配置 | scripts/unified_analysis/unified_config.py | 资产定义 |
| 综合分析 | scripts/comprehensive_asset_analysis/asset_reporter.py | 指数分析 |
| 板块分析 | scripts/sector_analysis/sector_reporter.py | 板块分析 |
| 位置分析 | position_analysis/main.py | 点位分析 |

---

## 命令速查

### 生成统一报告
```bash
# Markdown格式
python scripts/unified_analysis/run_unified_analysis.py --format markdown

# 保存到文件
python scripts/unified_analysis/run_unified_analysis.py --save report.md

# 发送邮件
python scripts/unified_analysis/run_unified_analysis.py --email

# 仅分析某些资产
python scripts/unified_analysis/run_unified_analysis.py --assets CYBZ HS300 HK_BIOTECH

# 列出所有资产
python scripts/unified_analysis/run_unified_analysis.py --list
```

### 生成板块报告
```bash
python scripts/sector_analysis/run_sector_analysis.py --email
```

### 生成历史点位报告
```bash
python position_analysis/main.py
```

---

## 风险免责声明

本系统分析仅供参考，不构成投资建议。使用者需了解：

1. **历史不等于未来**: 历史点位分析基于历史数据，市场环境变化时失效
2. **黑天鹅事件**: 系统不能预测突发事件（政策、地震、战争等）
3. **流动性风险**: 某些资产(加密、小盘股)流动性可能不足
4. **宏观风险**: 不包含宏观经济周期变化的影响
5. **杠杆风险**: 任何杠杆操作都会放大收益和亏损

**投资有风险，入市需谨慎！**

---

**最后更新**: 2025-10-20  
**版本**: 1.0  
**维护**: Claude Code
