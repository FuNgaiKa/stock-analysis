# Position Analysis 使用场景指南

> 📖 根据你的分析需求,快速找到对应的策略和工具
> 🎯 实战导向,场景化说明

---

## 🎯 快速导航

| 你想分析什么? | 跳转到 |
|-------------|--------|
| 技术面(MACD/KDJ/RSI等) | [场景1: 技术面分析](#场景1-技术面分析) |
| 资金面(北向/南向/融资融券) | [场景2: 资金面分析](#场景2-资金面分析) |
| 估值(PE/PB贵不贵) | [场景3: 估值分析](#场景3-估值分析) |
| 情绪(市场火不火) | [场景4: 市场情绪分析](#场景4-市场情绪分析) |
| 风险(会不会见顶) | [场景5: 风险检测](#场景5-风险检测) |
| 历史相似点位 | [场景6: 历史点位对比](#场景6-历史点位对比) |
| 综合判断(所有维度) | [场景7: 综合分析](#场景7-综合分析-推荐) |

---

## 场景1: 技术面分析

### 📌 **你想知道**:
- MACD是金叉还是死叉?
- RSI是超买还是超卖?
- KDJ信号怎么样?
- 均线是多头还是空头排列?
- 有没有技术背离?

### 🔧 **使用工具**:

#### **方法1: 使用背离分析器(推荐)**
```python
from position_analysis.analyzers.technical_analysis.divergence_analyzer import DivergenceAnalyzer, normalize_dataframe_columns
from position_analysis.core.historical_position_analyzer import HistoricalPositionAnalyzer

# 获取数据
analyzer = HistoricalPositionAnalyzer()
df = analyzer.get_index_data('sz399006')  # 创业板指
df = normalize_dataframe_columns(df)

# 技术背离分析
div_analyzer = DivergenceAnalyzer(lookback_period=60)
result = div_analyzer.comprehensive_analysis(df, symbol='创业板指', market='CN')

# 查看结果
if result['has_any_divergence']:
    for signal in result['summary']:
        print(f"{signal['type']} - {signal['direction']}")
        print(f"强度: {signal['strength']}/100")
        print(f"描述: {signal['description']}")
```

#### **方法2: 使用市场分析器(一站式)**
```bash
# A股技术面分析
python -c "
from position_analysis.market_analyzers.cn_market_analyzer import CNMarketAnalyzer
analyzer = CNMarketAnalyzer()
result = analyzer.analyze_single_index('sz399006', tolerance=0.05)
print('技术背离:', result.get('technical_divergence', '无'))
"
```

### 📊 **查看哪些指标**:
| 指标 | 位置 | 含义 |
|------|------|------|
| MACD背离 | `result['details']['macd']` | 顶背离→见顶 / 底背离→见底 |
| RSI背离 | `result['details']['rsi']` | 价格新高但RSI不创新高→动能衰竭 |
| 量价背离 | `result['details']['volume_price']` | 价格涨但量缩→上涨乏力 |

### 🎯 **实战案例**:
```
问题: 创业板指数MACD出现顶背离了吗?
操作: 运行上面代码
结果:
  - 有背离 → "MACD顶背驰,强度90/100,高置信度"
  - 无背离 → "暂无背离信号,价格与技术指标配合良好"

判断:
  - MACD顶背离 → 上涨动能衰竭,建议减仓
  - 无背离 → 技术面健康,可继续持有
```

---

## 场景2: 资金面分析

### 📌 **你想知道**:
- **A股**: 北向资金在买还是卖?
- **A股**: 融资资金是流入还是流出?
- **港股**: 南向资金(内地资金)在买港股吗?
- 主力资金在进还是出?

### 🔧 **使用工具**:

#### **A股 - 北向资金**
```python
from position_analysis.analyzers.market_specific.cn_stock_indicators import CNStockIndicators

cn_indicators = CNStockIndicators()

# 北向资金
north_flow = cn_indicators.get_north_flow()
print(f"今日北向资金: {north_flow['today_flow']:.2f}亿")
print(f"近5日累计: {north_flow['recent_5d_flow']:.2f}亿")
print(f"状态: {north_flow['status']}")  # 持续流入/流出/震荡
```

**判断逻辑**:
```
北向资金连续5日净流入 > 50亿 → 外资看好,中期看多
北向资金连续5日净流出 > 50亿 → 外资撤退,需要警惕
单日流入 > 100亿 → 强烈看多信号
单日流出 > 100亿 → 强烈看空信号
```

#### **A股 - 融资融券**
```python
from position_analysis.analyzers.market_specific.margin_trading_analyzer import MarginTradingAnalyzer

margin_analyzer = MarginTradingAnalyzer()

# 融资融券数据
margin_data = margin_analyzer.get_margin_data('sh000001')  # 上证指数
print(f"融资余额: {margin_data['margin_balance']:.2f}亿")
print(f"融资买入额: {margin_data['margin_buy']:.2f}亿")
print(f"趋势: {margin_data['trend']}")  # 上升/下降
```

**判断逻辑**:
```
融资余额快速上升(单周+5%) → 散户加杠杆,情绪亢奋,警惕过热
融资余额持续下降 → 杠杆资金撤退,市场转冷
融资买入占比 > 10% → 杠杆率高,风险大
```

#### **港股 - 南向资金**
```python
from position_analysis.analyzers.market_specific.southbound_funds_analyzer import SouthboundFundsAnalyzer

sb_analyzer = SouthboundFundsAnalyzer()

# 南向资金流向
sb_flow = sb_analyzer.analyze_southbound_funds()
print(f"近5日流向: {sb_flow['recent_5d_flow']:.2f}亿")
print(f"状态: {sb_flow['status']}")
```

**判断逻辑**:
```
南向资金连续流入 → 内地资金看好港股,港股中期看涨
南向资金连续流出 → 内地资金撤离,港股承压
```

### 🎯 **实战案例**:
```
问题: 现在是否适合买A股?资金面怎么样?
操作:
  1. 查北向资金 → 近5日净流入200亿
  2. 查融资余额 → 稳定在1.8万亿,未快速上升

判断:
  ✅ 北向资金大幅流入 → 外资看好
  ✅ 融资余额稳定 → 没有过度加杠杆
  → 资金面支持,可以买入
```

---

## 场景3: 估值分析

### 📌 **你想知道**:
- 现在A股/港股/美股贵不贵?
- PE/PB在历史什么位置?
- 是高估还是低估?

### 🔧 **使用工具**:

#### **方法1: 使用估值分析器**
```python
from position_analysis.core.valuation_analyzer import ValuationAnalyzer

val_analyzer = ValuationAnalyzer()

# A股估值
valuation = val_analyzer.get_valuation_data('sh000001')  # 上证指数
print(f"PE: {valuation['pe']:.2f}")
print(f"PE分位数: {valuation['pe_percentile']:.1f}%")
print(f"PB: {valuation['pb']:.2f}")
print(f"PB分位数: {valuation['pb_percentile']:.1f}%")
print(f"估值水平: {valuation['level']}")
```

#### **方法2: 用市场综合分析器(更快)**
```bash
# A股估值快速查看
python position_analysis/main.py  # 选择1(A股)
# 报告中会显示估值分位数
```

### 📊 **估值判断标准**:

| PE分位数 | 估值水平 | 操作建议 |
|---------|---------|---------|
| < 20% | 低估 | ✅ 积极买入区域 |
| 20-40% | 合理偏低 | ✅ 可以买入 |
| 40-60% | 合理 | ⚖️ 正常持有 |
| 60-80% | 合理偏高 | ⚠️ 谨慎,逢高减仓 |
| 80-90% | 高估 | 🔴 建议减仓 |
| > 90% | 严重高估 | 🔴 强烈建议减仓 |

**PB判断类似,但更保守**:
- PB < 1.0 → 破净,可能是底部区域(需结合行业)

### 🎯 **实战案例**:
```
问题: 上证指数现在3800点,贵不贵?能买吗?
操作: 查看估值分位数
结果:
  PE分位数: 78%
  PB分位数: 75%

判断:
  ⚠️ PE/PB都在70-80%区间 → 合理偏高
  → 不是最佳买点,但也不是特别贵
  → 建议: 轻仓或等回调
```

---

## 场景4: 市场情绪分析

### 📌 **你想知道**:
- 市场现在火不火?
- 是疯狂还是冷清?
- 有没有过热风险?

### 🔧 **使用工具**:

```python
from position_analysis.analyzers.market_specific.cn_stock_indicators import CNStockIndicators

cn_indicators = CNStockIndicators()

# 市场情绪数据
sentiment = cn_indicators.get_market_sentiment()
print(f"涨停家数: {sentiment['limit_up_count']}只")
print(f"跌停家数: {sentiment['limit_down_count']}只")
print(f"新高家数: {sentiment['new_high_count']}只")
print(f"情绪状态: {sentiment['status']}")
```

### 📊 **情绪判断标准**:

| 涨停数 | 市场状态 | 风险提示 |
|-------|---------|---------|
| > 150只/日 | 🔥 情绪癫狂 | 🔴 极度过热,高风险 |
| 100-150只 | 📈 情绪高涨 | ⚠️ 过热,注意风险 |
| 50-100只 | 😊 情绪良好 | ✅ 健康上涨 |
| 20-50只 | 😐 情绪平淡 | ⚖️ 正常 |
| < 20只 | 😔 情绪低迷 | ✅ 可能是机会 |

**特殊情况**:
```
跌停数 > 100只/日 → 恐慌性下跌,可能是抄底机会
涨停数 > 200只 + 跌停数 < 10只 → 单边上涨,极度过热
```

### 🎯 **实战案例**:
```
问题: 最近A股涨得很猛,还能追吗?
操作: 查看市场情绪
结果:
  涨停家数: 180只/日
  连续3天 > 150只

判断:
  🔴 情绪已经癫狂 → 散户全面入场
  → 通常是阶段性顶部信号
  → 建议: 不追高,逢高减仓
```

---

## 场景5: 风险检测

### 📌 **你想知道**:
- 会不会马上见顶?
- 有没有暴跌风险?
- 什么时候该跑?

### 🔧 **使用工具**:

#### **A股牛市顶部检测**
```python
from position_analysis.analyzers.risk_detection.bull_market_top_detector import BullMarketTopDetector

top_detector = BullMarketTopDetector()

# 检测见顶风险
risk = top_detector.detect_top_risk()
print(f"综合风险评分: {risk['overall_risk']:.2f}")  # 0-1之间
print(f"风险等级: {risk['risk_level']}")  # 低/中/高/极高
print(f"风险因素:")
for factor in risk['risk_factors']:
    print(f"  - {factor}")
```

#### **美股见顶检测**
```python
from position_analysis.analyzers.risk_detection.us_market_top_detector import USMarketTopDetector

us_top = USMarketTopDetector()
us_risk = us_top.detect_top_risk()
print(f"美股见顶风险: {us_risk['overall_risk']:.2f}")
```

#### **港股见顶检测**
```python
from position_analysis.analyzers.risk_detection.hk_market_top_detector import HKMarketTopDetector

hk_top = HKMarketTopDetector()
hk_risk = hk_top.detect_top_risk()
print(f"港股见顶风险: {hk_risk['overall_risk']:.2f}")
```

### 📊 **风险评分解读**:

| 风险评分 | 风险等级 | 操作建议 |
|---------|---------|---------|
| < 0.3 | 🟢 低风险 | ✅ 安全,可持有 |
| 0.3-0.5 | 🟡 中风险 | ⚠️ 注意,设止损 |
| 0.5-0.7 | 🟠 高风险 | 🔴 减仓,保留核心仓位 |
| > 0.7 | 🔴 极高风险 | 🔴 强烈建议大幅减仓 |

### 🎯 **实战案例**:
```
问题: A股涨了一波,现在是不是要见顶了?
操作: 运行牛市顶部检测
结果:
  综合风险评分: 0.75
  风险等级: 极高
  风险因素:
    - 估值分位数90% (历史高位)
    - 日均成交额2.5万亿 (是平时2倍)
    - 涨停数连续5日>150只 (情绪癫狂)
    - MACD顶背离 (技术见顶)
    - 北向资金转为流出 (聪明钱撤退)

判断:
  🔴 5项风险因素全部满足 → 牛市顶部特征明显
  → 强烈建议: 大幅减仓至30%以下,保留核心资产
```

---

## 场景6: 历史点位对比

### 📌 **你想知道**:
- 现在这个点位历史上出现过吗?
- 历史上这个点位后来怎么走的?
- 上涨概率多少?平均涨多少?

### 🔧 **使用工具**:

```python
from position_analysis.core.historical_position_analyzer import HistoricalPositionAnalyzer

analyzer = HistoricalPositionAnalyzer()

# 分析上证指数
index_code = 'sh000001'
df = analyzer.get_index_data(index_code)
current_price = df['close'].iloc[-1]

# 查找相似点位
similar = analyzer.find_similar_periods(index_code, current_price, tolerance=0.05)
print(f"历史相似点位: {len(similar)}个")

# 计算未来收益
future_returns = analyzer.calculate_future_returns(index_code, similar, [5, 10, 20, 60])

# 20日后统计
ret_20d = future_returns['return_20d'].dropna()
up_count = (ret_20d > 0).sum()
total = len(ret_20d)
print(f"20日上涨概率: {up_count/total:.1%} ({up_count}次/{total}次)")
print(f"平均收益: {ret_20d.mean():.2%}")
print(f"中位数收益: {ret_20d.median():.2%}")
```

### 🎯 **实战案例**:
```
问题: 上证指数3850点,历史上这个位置后来怎么走?
操作: 运行历史点位对比
结果:
  历史相似点位: 127个
  年份分布: 2007年42次, 2015年41次, 2025年30次

  20日后:
    上涨概率: 51% (56次/110次)
    下跌概率: 49% (54次/110次)
    平均收益: +0.5%
    中位数: +0.1%

判断:
  ⚖️ 涨跌概率接近 → 方向不明确
  💡 注意2007和2015都是牛市高点年份
  → 建议: 中性观望,不追高
```

---

## 场景7: 综合分析 (推荐⭐⭐⭐)

### 📌 **你想要**:
一次性看完所有维度:
- 历史概率
- 技术面
- 资金面
- 估值
- 情绪
- 风险

### 🔧 **最简单的方法**:

#### **A股综合分析**
```bash
# 方式1: 命令行快速分析
python position_analysis/main.py
# 选择 1 (A股市场)

# 方式2: Python脚本
python -c "
from position_analysis.market_analyzers.cn_market_analyzer import CNMarketAnalyzer
analyzer = CNMarketAnalyzer()
result = analyzer.analyze_single_index('sh000001', tolerance=0.05)
print('已生成完整报告')
"
```

#### **美股综合分析**
```bash
python scripts/us_stock_analysis/run_us_analysis.py
```

#### **港股综合分析**
```bash
python scripts/hk_stock_analysis/run_hk_analysis.py
```

### 📊 **报告包含内容**:

```
═══════════════════════════════════════════════════
          完整分析报告 (示例)
═══════════════════════════════════════════════════

【当前点位】
  上证指数: 3850.00
  日期: 2025-10-15

【历史点位分析】 ← 场景6
  相似点位: 127个
  20日上涨概率: 51%
  平均收益: +0.5%
  置信度: 71%

【技术面分析】 ← 场景1
  MACD: 金叉
  RSI: 65 (偏超买但未过热)
  KDJ: K线在70附近
  背离: 无明显背离

【资金面分析】 ← 场景2
  北向资金: 近5日净流入150亿 ✅
  融资余额: 1.78万亿 (稳定)
  主力资金: 净流入

【估值分析】 ← 场景3
  PE分位数: 75% ⚠️ 偏高
  PB分位数: 72% ⚠️ 偏高
  估值水平: 合理偏高

【市场情绪】 ← 场景4
  涨停家数: 88只
  市场状态: 情绪良好
  过热程度: 中等

【风险评估】 ← 场景5
  综合风险: 0.45 (中风险)
  见顶风险: 中等
  主要风险: 估值偏高

【综合判断】
  方向: 中性偏多
  建议仓位: 50-60%
  操作策略:
    - 估值偏高,不追高
    - 资金面支持,可持有
    - 技术面健康,设好止损
    - 等回调3-5%后加仓
```

### 🎯 **实战案例**:
```
问题: 我想全面了解现在A股能不能买?
操作: 运行综合分析
时间: 3分钟
结果: 一份完整报告,包含上面所有7个维度

判断流程:
  1. 先看风险评估 → 中风险,可控
  2. 再看估值 → 偏高,不是最佳买点
  3. 看资金面 → 北向流入,支持
  4. 看技术面 → 健康,无背离
  5. 看情绪 → 良好,未过热
  6. 看历史概率 → 中性,涨跌概率相当

最终决策:
  ⚖️ 综合判断: 可以轻仓参与(30-40%)
  💡 最佳策略: 等待回调3-5%后加仓至50-60%
  🎯 止损位: 3700点
```

---

## 🎓 进阶组合策略

### 策略1: 牛市确认组合
```
1. 历史概率 > 60% 上涨 ✅
2. 估值 < 60分位 ✅
3. 北向资金连续流入 ✅
4. MACD金叉 ✅
5. 风险评分 < 0.4 ✅

→ 5项全满足 → 确认牛市,可重仓(70-80%)
```

### 策略2: 熊市确认组合
```
1. 历史概率 < 40% 上涨 🔴
2. 估值 > 80分位 🔴
3. 北向资金持续流出 🔴
4. MACD死叉或顶背离 🔴
5. 风险评分 > 0.6 🔴

→ 满足3项以上 → 熊市特征,建议减仓至20-30%
```

### 策略3: 抄底组合
```
1. 估值 < 30分位 ✅ (便宜)
2. 市场情绪低迷(涨停<20只) ✅ (恐慌)
3. RSI < 30 ✅ (超卖)
4. 北向资金开始流入 ✅ (聪明钱进场)

→ 满足3项 → 可能是底部,可分批建仓
```

### 策略4: 逃顶组合
```
1. 估值 > 85分位 🔴
2. 涨停数 > 150只连续3天 🔴
3. MACD顶背离 🔴
4. 成交额暴增(>平时2倍) 🔴
5. 北向资金转为流出 🔴
6. 风险评分 > 0.7 🔴

→ 满足4项以上 → 牛市顶部,强烈建议减仓
```

---

## 📱 快速查询表

| 我想... | 用什么工具 | 查什么指标 | 多久更新 |
|--------|-----------|-----------|---------|
| 看MACD | 背离分析器 | MACD金叉/死叉/背离 | 每日 |
| 看北向资金 | CN指标分析器 | 流入/流出/趋势 | 每日 |
| 看估值 | 估值分析器 | PE/PB分位数 | 每日 |
| 看情绪 | CN指标分析器 | 涨停数/新高数 | 每日 |
| 看风险 | 风险检测器 | 综合风险评分 | 每日 |
| 看历史 | 历史点位分析器 | 未来概率统计 | 实时 |
| 看全部 | 市场综合分析器 | 完整报告 | 每日 |

---

## 💡 最佳实践建议

### 1️⃣ **日常使用流程**
```
早上: 运行综合分析 → 查看整体状况
重点看:
  - 风险评分(是否>0.6)
  - 北向资金(是否流出)
  - 估值分位数(是否>85%)

发现异常 → 深入分析对应维度
```

### 2️⃣ **买入决策流程**
```
1. 先看风险评分 → 如果>0.6,放弃
2. 再看估值 → 如果>80%,等回调
3. 看资金面 → 北向流入才考虑
4. 看技术面 → 无背离才安全
5. 看历史概率 → 参考预期收益

→ 都满足 → 可以买入
```

### 3️⃣ **卖出决策流程**
```
1. 先看风险评分 → 如果>0.7,立即减仓
2. 看技术背离 → 顶背离出现,减仓
3. 看资金面 → 北向连续流出,减仓
4. 看情绪 → 涨停>150只连续3天,减仓

→ 满足任一条 → 考虑减仓
→ 满足2条以上 → 强烈建议减仓
```

---

**Made with ❤️ by Claude Code & Russ**
