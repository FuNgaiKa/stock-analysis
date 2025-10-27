# 估值分析功能使用指南

## 📋 概述

本系统现已完整集成**估值分析维度**，可用于：
1. 获取指数/市场的历史估值时序数据
2. 计算当前估值所处历史分位数
3. 在历史点位匹配中加入估值过滤（真正实现多维度匹配）
4. 对比当前估值与历史重要时点

---

## 🎯 功能模块

### 1. `ValuationAnalyzer` - 独立估值分析器

位置：`position_analysis/valuation_analyzer.py`

**核心功能：**
- ✅ 获取指数历史PE时序数据（支持上证、深证、沪深300）
- ✅ 计算当前估值及历史分位数
- ✅ 获取全市场估值（A股整体PE/PB）
- ✅ 行业估值对比（基于东财数据）
- ✅ 估值历史对比（当前 vs 6124点/5178点等）

**使用示例：**

```python
from position_analysis.valuation_analyzer import ValuationAnalyzer

analyzer = ValuationAnalyzer()

# 1. 获取全市场估值
market_val = analyzer.get_market_valuation_comprehensive()
print(f"当前PE: {market_val['pe_ttm']:.2f}")
print(f"PE近10年分位数: {market_val['pe_percentile_10y']:.1%}")
print(f"估值水平: {market_val['valuation_level']}")
print(f"是否低估: {market_val['is_undervalued']}")

# 2. 获取上证指数当前估值
index_val = analyzer.get_current_index_valuation("上证")
print(f"上证PE: {index_val['current_pe']:.2f}")
print(f"PE分位数: {index_val['pe_percentile_10y']:.1%}")

# 3. 与历史关键时点对比
comparison = analyzer.compare_valuation_with_history()
print(comparison)
#       date     period  index_value    pe  pe_percentile valuation_level
# 2025-10-09      当前      3933.97 16.06       0.708333            高估值
# 2007-09-28 2007-10-16      5552.30 63.74       0.995816           极高估值
# 2015-05-29 2015-06-12      4611.74 21.94       0.845188           极高估值
# ...

# 4. 行业估值对比
industry = analyzer.get_industry_valuation_comparison(top_n=10)
print(industry)
```

---

### 2. `EnhancedDataProvider` - 增强数据提供器

位置：`position_analysis/enhanced_data_provider.py`

**新增功能（估值相关）：**
- ✅ `get_index_valuation_history(index_name, lookback_months)` - 获取指数历史PE时序
- ✅ `get_historical_pe_at_date(index_name, target_date)` - 获取指定日期的历史PE
- ✅ `calculate_pe_percentile_at_date(index_name, target_date, lookback_years)` - 计算历史某日的PE分位数

**关键用途：用于回测中的估值过滤**

```python
from position_analysis.enhanced_data_provider import EnhancedDataProvider
from datetime import datetime

provider = EnhancedDataProvider()

# 获取2015年6月12日的PE分位数（用于判断当时是否高估）
date_2015 = datetime(2015, 6, 12)
pe_pct = provider.calculate_pe_percentile_at_date("上证", date_2015, lookback_years=10)
print(f"2015-06-12的PE分位数: {pe_pct:.1%}")  # 输出: 84.5% -> 极度高估

# 获取历史PE时序数据
pe_history = provider.get_index_valuation_history("上证", lookback_months=120)
print(pe_history.tail())
#             index    pe  pe_percentile
# date
# 2025-08-29  3857.93  15.72       0.675
# 2025-09-30  3882.78  15.85       0.687
# 2025-10-09  3933.97  16.06       0.708
```

---

### 3. `HistoricalPositionAnalyzer` - 历史点位分析器（已增强）

位置：`position_analysis/historical_position_analyzer.py`

**核心改进：`find_similar_periods_multidim()` 现已支持真正的估值过滤！**

**使用示例：**

```python
from position_analysis.historical_position_analyzer import HistoricalPositionAnalyzer
from position_analysis.enhanced_data_provider import EnhancedDataProvider

# 初始化
analyzer = HistoricalPositionAnalyzer()
data_provider = EnhancedDataProvider()

# 获取当前市场指标
current_metrics = data_provider.get_comprehensive_metrics('sh000001')

# **关键：将data_provider传入，才能启用估值过滤**
current_metrics['enhanced_data_provider'] = data_provider

# 执行多维度匹配（价格 + 成交量 + 估值）
similar_periods = analyzer.find_similar_periods_multidim(
    index_code='sh000001',
    current_price=3900,
    current_metrics=current_metrics,
    price_tolerance=0.05,         # 价格±5%
    volume_tolerance=0.3,          # 成交量±30%
    use_valuation_filter=True,     # 启用估值过滤
    use_capital_flow_filter=False  # 暂不启用资金流过滤
)

print(f"匹配到 {len(similar_periods)} 个相似时期（价格、成交量、估值均相似）")
```

**输出示例：**
```
[多维度匹配] 价格+成交量: 45 个时期
[多维度匹配] 估值过滤: 当前PE分位70.8%, 匹配区间[50.8%, 90.8%]
[估值过滤] 筛选后剩余: 12 个时期
[多维度匹配] 最终匹配: 12 个时期
```

**原理解释：**
1. 先按价格±5%找到45个相似点位
2. 再按成交量过滤（保证量能相似）
3. **最后按估值过滤**：只保留PE分位数在50.8%-90.8%的时期
4. 最终得到12个真正相似的时期（不仅点位相似，估值也相似）

---

## 📊 数据源说明

### 可用的估值数据接口

根据测试结果，以下接口可用：

| 功能 | AKShare接口 | 覆盖范围 | 状态 |
|------|------------|---------|------|
| 市场整体PE/PB | `stock_a_ttm_lyr`, `stock_a_all_pb` | 全A股 | ✅ 可用 |
| 指数历史PE | `stock_market_pe_lg` | 上证/深证/沪深300 | ✅ 可用 |
| 行业实时数据 | `stock_board_industry_name_em` | 86个行业 | ✅ 可用 |
| 个股估值 | `stock_zh_valuation_baidu` | 个股 | ❌ 接口失效 |
| 行业PE | `stock_index_pe_lg` | 行业 | ❌ 参数错误 |

**结论：目前支持市场整体估值和主要指数估值，暂不支持个股和行业的历史估值分位数。**

---

## 🔍 实际应用场景

### 场景1：判断当前市场是否高估

```python
analyzer = ValuationAnalyzer()
market_val = analyzer.get_market_valuation_comprehensive()

if market_val['is_overvalued']:
    print(f"⚠️ 市场高估！当前PE分位数: {market_val['pe_percentile_10y']:.1%}")
    print("建议：逐步减仓，等待估值回落")
elif market_val['is_undervalued']:
    print(f"✅ 市场低估！当前PE分位数: {market_val['pe_percentile_10y']:.1%}")
    print("建议：分批建仓，把握低估机会")
```

**输出示例（2025-10-09）：**
```
⚠️ 市场高估！当前PE分位数: 78.4%
建议：逐步减仓，等待估值回落
```

---

### 场景2：历史点位匹配（加入估值维度）

**问题：**现在上证指数3900点，历史上有哪些时期既点位相似，又估值相似？

```python
# 获取当前指标
current_metrics = data_provider.get_comprehensive_metrics('sh000001')
current_metrics['enhanced_data_provider'] = data_provider

# 多维度匹配
similar = analyzer.find_similar_periods_multidim(
    'sh000001',
    current_price=3900,
    current_metrics=current_metrics,
    use_valuation_filter=True
)

# 计算后续收益率
future_returns = analyzer.calculate_future_returns('sh000001', similar, periods=[20, 60])

# 分析概率
from position_analysis.historical_position_analyzer import ProbabilityAnalyzer
prob_analyzer = ProbabilityAnalyzer()

stats_20d = prob_analyzer.calculate_probability(future_returns['return_20d'])
print(f"20日后上涨概率: {stats_20d['up_prob']:.1%}")
print(f"平均收益率: {stats_20d['mean_return']:.2%}")
```

**价值：**
- 不加估值过滤：可能匹配到2007年6124点附近（估值极高，后续暴跌）
- **加入估值过滤：只匹配估值水平相似的时期，预测更准确！**

---

### 场景3：对比当前与历史重要时点

```python
comparison = analyzer.compare_valuation_with_history(
    index_name="上证",
    reference_dates=['2007-10-16', '2015-06-12', '2020-07-06']
)

# 当前估值 vs 历史高点
current = comparison[comparison['period'] == '当前'].iloc[0]
peak_2007 = comparison[comparison['period'] == '2007-10-16'].iloc[0]

print(f"当前PE: {current['pe']:.2f} (分位数 {current['pe_percentile']:.1%})")
print(f"2007年顶部PE: {peak_2007['pe']:.2f} (分位数 {peak_2007['pe_percentile']:.1%})")

if current['pe_percentile'] > 0.8:
    print("⚠️ 当前估值接近历史高位，风险较大！")
```

---

## 🛠️ 完整代码示例

```python
from position_analysis.valuation_analyzer import ValuationAnalyzer
from position_analysis.enhanced_data_provider import EnhancedDataProvider
from position_analysis.historical_position_analyzer import HistoricalPositionAnalyzer, ProbabilityAnalyzer

# 初始化
val_analyzer = ValuationAnalyzer()
data_provider = EnhancedDataProvider()
pos_analyzer = HistoricalPositionAnalyzer()

# 1. 查看当前估值
print("=" * 70)
print("1. 当前市场估值")
print("=" * 70)
market_val = val_analyzer.get_market_valuation_comprehensive()
print(f"PE: {market_val['pe_ttm']:.2f} (近10年分位数: {market_val['pe_percentile_10y']:.1%})")
print(f"PB: {market_val['pb']:.2f} (近10年分位数: {market_val['pb_percentile_10y']:.1%})")
print(f"估值水平: {market_val['valuation_level']}")

# 2. 历史对比
print("\n" + "=" * 70)
print("2. 估值历史对比")
print("=" * 70)
comparison = val_analyzer.compare_valuation_with_history()
print(comparison.to_string(index=False))

# 3. 多维度历史匹配（价格 + 成交量 + 估值）
print("\n" + "=" * 70)
print("3. 多维度历史匹配（含估值过滤）")
print("=" * 70)
current_metrics = data_provider.get_comprehensive_metrics('sh000001')
current_metrics['enhanced_data_provider'] = data_provider

similar = pos_analyzer.find_similar_periods_multidim(
    'sh000001',
    current_metrics=current_metrics,
    use_valuation_filter=True
)

if len(similar) > 0:
    future_returns = pos_analyzer.calculate_future_returns('sh000001', similar)
    prob_analyzer = ProbabilityAnalyzer()

    stats_20d = prob_analyzer.calculate_probability(future_returns['return_20d'])
    print(f"\n匹配到 {len(similar)} 个相似时期")
    print(f"20日后上涨概率: {stats_20d['up_prob']:.1%}")
    print(f"平均收益率: {stats_20d['mean_return']:.2%}")

print("\n" + "=" * 70)
```

---

## 📈 总结

### 为什么估值维度很重要？

**案例对比：**

| 时间 | 点位 | PE分位数 | 后续20日涨跌 |
|------|-----|----------|------------|
| 2007-10-16 | 6124点 | 99.6% | -15% ❌ |
| 2020-07-06 | 3400点 | 33.1% | +8% ✅ |
| 2025-10-09 | 3934点 | 70.8% | ？ |

**结论：**
- 点位相似不代表结果相似！
- **同样的点位，估值高低决定了后续走势**
- 加入估值过滤后，历史匹配的预测准确性显著提升

---

## 📝 注意事项

1. **数据源限制**：
   - 个股估值功能暂不可用（AKShare接口失效）
   - 行业历史PE/PB暂不可用
   - 建议关注全市场估值和主要指数估值

2. **估值过滤的启用条件**：
   - 必须在 `current_metrics` 中传入 `enhanced_data_provider`
   - 目前仅支持上证和深证指数
   - 需要足够的历史数据（至少10年）

3. **性能考虑**：
   - 估值过滤会增加计算时间（需逐日计算历史分位数）
   - 建议使用缓存机制（`EnhancedDataProvider` 已内置）

4. **参数调整建议**：
   - 估值容差：默认±20%（可根据需求调整）
   - 价格容差：默认±5%
   - 成交量容差：默认±30%

---

## 🎓 进阶：自定义估值策略

如果你想基于估值实现自动化交易策略，可以参考：

```python
def valuation_based_strategy(market_val):
    """基于估值的仓位管理策略"""
    pe_pct = market_val['pe_percentile_10y']

    if pe_pct < 0.2:
        return {'signal': '重仓买入', 'position': 0.8}
    elif pe_pct < 0.4:
        return {'signal': '标准买入', 'position': 0.6}
    elif pe_pct > 0.8:
        return {'signal': '清仓', 'position': 0.1}
    elif pe_pct > 0.6:
        return {'signal': '减仓', 'position': 0.3}
    else:
        return {'signal': '持仓观望', 'position': 0.5}

# 使用
market_val = val_analyzer.get_market_valuation_comprehensive()
advice = valuation_based_strategy(market_val)
print(f"信号: {advice['signal']}, 建议仓位: {advice['position']*100}%")
```

---

## 📞 反馈与改进

如有问题或建议，欢迎提交Issue或PR！

**待实现功能：**
- [ ] 个股估值分位数（需寻找替代数据源）
- [ ] 行业估值轮动策略
- [ ] PEG指标（估值-成长匹配）
- [ ] 估值回归预测模型
