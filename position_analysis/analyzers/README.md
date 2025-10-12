# 📊 专业分析器模块

> 量化分析的核心工具集

---

## 📁 模块概览

本目录包含16个专业级分析器,涵盖从技术指标到基本面分析的完整量化体系。

### 🔥 核心分析器

#### 1️⃣ 因子分析
- **alpha101_factors.py** - WorldQuant Alpha101因子库
  - 101个经典量化因子
  - 技术、动量、反转等多维度
  - 适用于因子挖掘和策略开发

#### 2️⃣ 市场微观结构
- **microstructure_analyzer.py** - 微观结构分析器
  - 买卖价差分析
  - 订单流分析
  - 流动性评估
  - 高频交易信号

- **slope_analyzer.py** - 趋势斜率分析器
  - 均线斜率计算
  - 趋势强度评估
  - 动态趋势跟踪

#### 3️⃣ 技术分析
- **vix_analyzer.py** - VIX恐慌指数分析器
  - VIX历史走势
  - 分位数分析
  - 恐慌/贪婪情绪判断
  - 与指数相关性分析

- **support_resistance.py** - 支撑压力位分析器
  - 关键价位识别
  - 突破概率统计
  - 回测验证

- **correlation_analyzer.py** - 相关性分析器
  - 指数相关性矩阵
  - 相关系数计算
  - 板块联动分析

#### 4️⃣ 成交量分析
- **volume_analyzer.py** - 成交量分析器
  - 量价关系分析
  - 量比计算
  - 放量/缩量判断
  - 成交量背离检测

#### 5️⃣ 行业与板块
- **sector_analyzer.py** - 行业轮动分析器
  - 11个行业ETF监控
  - 相对强度排名
  - 轮动模式识别
  - 行业配置建议

#### 6️⃣ 历史匹配
- **historical_matcher.py** - 历史相似点位匹配器
  - 形态识别
  - 相似度计算
  - 统计预测

---

## 🇨🇳 A股特色分析器

### 资金流向
- **margin_trading_analyzer.py** - 融资融券分析器 ⭐
  - 融资余额/融券余额
  - 融资买入额占比
  - 杠杆资金情绪
  - 市场情绪温度计

- **hk_connect_analyzer.py** - 港股通/沪深股通分析器 ⭐
  - 北向资金流向(聪明钱)
  - 南向资金流向
  - 累计净买入
  - 外资持股变化

- **cn_stock_indicators.py** - A股特色指标 ⭐
  - 量比(成交量/5日均量)
  - 换手率
  - MACD能量
  - 市场活跃度

### 基本面分析
- **financial_analyzer.py** - 财务数据分析器 ⭐
  - ROE(净资产收益率)
  - 营收增长率
  - 利润增长率
  - 财务质量评分
  - 成长性/盈利性/稳定性三维评分

### 市场宽度
- **market_breadth_analyzer.py** - 市场宽度分析器 ⭐
  - 新高新低指数(20/60/120日)
  - 涨跌家数统计
  - 内部强度指标
  - 市场参与度评估

### 情绪指标
- **sentiment_index.py** - 情绪指标分析器
  - 涨停/跌停统计
  - 市场情绪温度
  - 极端情绪预警
  - 反转信号识别

---

## 🚀 使用示例

### 1. VIX恐慌指数分析
```python
from position_analysis.analyzers.vix_analyzer import VIXAnalyzer

analyzer = VIXAnalyzer()
result = analyzer.analyze_current_vix()

print(f"当前VIX: {result['current_vix']:.2f}")
print(f"历史分位数: {result['percentile']:.1f}%")
print(f"市场情绪: {result['sentiment']}")
```

### 2. 融资融券分析
```python
from position_analysis.analyzers.margin_trading_analyzer import MarginTradingAnalyzer

analyzer = MarginTradingAnalyzer()
result = analyzer.analyze_margin_trading()

print(f"融资余额: {result['margin_balance']:.2f}亿")
print(f"融资买入占比: {result['margin_buy_ratio']:.2f}%")
print(f"市场情绪: {result['sentiment']}")
```

### 3. 市场宽度分析
```python
from position_analysis.analyzers.market_breadth_analyzer import MarketBreadthAnalyzer

analyzer = MarketBreadthAnalyzer()
result = analyzer.analyze_market_breadth()

print(f"20日新高新低指数: {result['nh_nl_20d']:.2f}")
print(f"市场宽度评分: {result['breadth_score']:.1f}/100")
print(f"市场状态: {result['market_state']}")
```

### 4. 财务数据分析
```python
from position_analysis.analyzers.financial_analyzer import FinancialAnalyzer

analyzer = FinancialAnalyzer()
result = analyzer.analyze_stock_fundamentals('000001')

print(f"ROE: {result['roe']:.2f}%")
print(f"营收增长率: {result['revenue_growth']:.2f}%")
print(f"综合评分: {result['total_score']:.1f}/100")
```

### 5. 斜率分析
```python
from position_analysis.analyzers.slope_analyzer import SlopeAnalyzer

analyzer = SlopeAnalyzer()
result = analyzer.analyze_trend_slope('sh000001')

print(f"MA20斜率: {result['ma20_slope']:.4f}")
print(f"趋势强度: {result['trend_strength']}")
print(f"趋势方向: {result['trend_direction']}")
```

---

## 📊 数据来源

| 分析器 | 主要数据源 | 覆盖范围 |
|--------|-----------|---------|
| VIX分析器 | yfinance | 美股VIX指数 |
| 融资融券 | AKShare | A股两融数据 |
| 港股通 | AKShare | 沪深港通数据 |
| 财务数据 | AKShare | A股财报数据 |
| 市场宽度 | AKShare | A股全市场 |
| 技术指标 | yfinance/AKShare | 全球市场 |

---

## 🎯 适用场景

### 短线交易
- VIX恐慌指数 → 超买超卖判断
- 市场宽度 → 普涨普跌识别
- 情绪指标 → 极端情绪反转

### 中线趋势
- 斜率分析 → 趋势强度确认
- 融资融券 → 杠杆资金方向
- 港股通 → 外资配置意图

### 长线价值
- 财务分析 → 基本面质量
- 相关性分析 → 组合优化
- Alpha101因子 → 量化选股

---

## 🔧 技术架构

### 设计原则
1. **模块化设计** - 每个分析器独立运行
2. **统一接口** - 标准化输入输出格式
3. **数据缓存** - 避免重复请求
4. **异常处理** - 优雅的错误处理

### 性能优化
- 多数据源备份
- 请求重试机制
- 5分钟数据缓存
- 异步并发支持

---

## 📚 相关文档

- [项目主文档](../../README.md)
- [历史点位分析系统](../README.md)
- [每日市场推送](../../docs/DAILY_REPORT_SETUP.md)
- [实施路线图](../../docs/IMPLEMENTATION_ROADMAP.md)

---

## 🛠️ 维护与扩展

### 添加新分析器
1. 继承基础分析器类
2. 实现 `analyze()` 方法
3. 遵循统一的返回格式
4. 添加单元测试
5. 更新本文档

### 数据源切换
编辑对应分析器文件,修改数据获取逻辑:
```python
# 示例: 切换数据源
def get_data(self):
    try:
        # 主数据源
        data = primary_source.fetch()
    except:
        # 备用数据源
        data = backup_source.fetch()
    return data
```

---

## ⚠️ 注意事项

1. **数据延迟**: 部分数据源有5-15分钟延迟
2. **API限制**: 避免频繁请求,建议使用缓存
3. **数据质量**: 交叉验证多个数据源
4. **时区问题**: 注意美股/港股/A股时区差异

---

## 🎖️ 版本历史

- **v4.0** (2025-10-12) - 新增6个A股特色分析器
- **v3.0** (2025-10-10) - 新增斜率和微观结构分析器
- **v2.0** (2025-10-09) - 新增VIX和行业轮动分析器
- **v1.0** (2025-10-02) - 初始版本

---

**Made with ❤️ by Claude Code**
最后更新: 2025-10-12
