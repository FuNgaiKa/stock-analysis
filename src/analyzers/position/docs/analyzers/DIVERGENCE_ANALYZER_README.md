# 背离分析器 (Divergence Analyzer)

## 📖 概述

背离分析器是一个专业的技术分析工具，用于检测股票/指数中的价格与技术指标背离现象。支持**A股、H股、美股**三大市场。

### 背离原理

- **顶背离**: 价格创新高，指标未创新高 → 上涨动能衰竭，警惕回调
- **底背离**: 价格创新低，指标未创新低 → 下跌动能衰竭，可能反弹

## 🚀 功能特性

### 1. 量价背离检测
分析价格与成交量的背离情况：
- **顶背离**: 价格创新高，成交量萎缩
- **底背离**: 价格创新低，成交量放大

### 2. MACD背驰检测
检测价格与MACD指标的背离：
- **顶背驰**: 价格创新高，MACD柱状图/DIF未创新高
- **底背驰**: 价格创新低，MACD柱状图/DIF未创新低

### 3. RSI背离检测
识别价格与RSI指标的背离：
- **顶背离**: 价格创新高，RSI未创新高
- **底背离**: 价格创新低，RSI未创新低

### 4. 综合分析
整合所有背离信号，给出综合评估和操作建议。

## 💻 使用方法

### 基础用法

```python
from divergence_analyzer import DivergenceAnalyzer, normalize_dataframe_columns
from data_sources.us_stock_source import USStockDataSource

# 1. 获取数据
source = USStockDataSource()
df = source.get_us_index_daily('SPX', period='6mo')
df = normalize_dataframe_columns(df)  # 标准化列名

# 2. 创建分析器
analyzer = DivergenceAnalyzer(
    peak_valley_window=5,      # 峰谷识别窗口
    lookback_period=60,        # 回看周期
    min_peak_distance=5        # 相邻峰谷最小间隔
)

# 3. 执行综合分析
result = analyzer.comprehensive_analysis(df, symbol='S&P 500', market='US')

# 4. 查看结果
if result['has_any_divergence']:
    print(f"检测到 {len(result['summary'])} 个背离信号")
    for signal in result['summary']:
        print(f"{signal['type']}: {signal['description']}")
else:
    print("无明显背离")
```

### A股市场示例

```python
from data_sources.us_stock_source import USStockDataSource

source = USStockDataSource()
df = source.get_us_index_daily('SSE', period='6mo')  # 上证指数
df = normalize_dataframe_columns(df)

analyzer = DivergenceAnalyzer()
result = analyzer.comprehensive_analysis(df, symbol='上证指数', market='CN')
```

### H股市场示例

```python
from data_sources.hkstock_source import HKStockDataSource

source = HKStockDataSource()
df = source.get_hk_index_daily('HSI')  # 恒生指数
df = normalize_dataframe_columns(df)

analyzer = DivergenceAnalyzer()
result = analyzer.comprehensive_analysis(df, symbol='恒生指数', market='HK')
```

### 单独检测某类背离

```python
# 只检测量价背离
volume_result = analyzer.detect_volume_price_divergence(df)

# 只检测MACD背驰
macd_result = analyzer.detect_macd_divergence(df)

# 只检测RSI背离
rsi_result = analyzer.detect_rsi_divergence(df)
```

## 📊 返回结果格式

### 综合分析结果

```python
{
    'symbol': '股票代码',
    'market': 'CN/HK/US',
    'timestamp': '2025-10-14 12:00:00',
    'has_any_divergence': True,
    'summary': [
        {
            'type': 'MACD背驰',
            'direction': '顶背驰',
            'strength': 90,           # 强度评分 0-100
            'confidence': '高',       # 置信度: 高/中/低
            'description': 'MACD顶背驰: 价格上涨3.5%，MACD动能衰减'
        }
    ],
    'overall_assessment': {
        'signal': '看跌',
        'strength': 90,
        'total_signals': 1,
        'bearish_signals': 1,
        'bullish_signals': 0,
        'advice': '多个顶背离信号出现，上涨动能衰竭，建议谨慎或减仓'
    }
}
```

## 🔧 参数说明

### DivergenceAnalyzer 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| peak_valley_window | int | 5 | 峰谷识别窗口大小 |
| lookback_period | int | 60 | 背离检测回看周期 |
| min_peak_distance | int | 5 | 相邻峰谷最小间隔 |

### 强度评分规则

- **80-100分**: 强背离，高度可靠
- **60-80分**: 中等背离，值得关注
- **0-60分**: 弱背离，仅供参考

### 置信度说明

- **高**: 价格与指标变化方向完全相反
- **中**: 价格与指标变化幅度差异明显
- **低**: 背离信号较弱

## 🎯 实战案例

### 案例1: 标普500顶背驰

```python
# 测试结果显示:
# - 类型: MACD顶背驰
# - 强度: 90/100
# - 置信度: 高
# - 描述: 价格上涨3.5%，MACD动能衰减
# - 建议: 上涨动能衰竭，建议谨慎或减仓
```

**分析**:
- 价格创出新高，但MACD柱状图未能创新高
- 说明上涨动能减弱，短期可能面临回调
- 建议: 获利了结或减仓观望

### 案例2: 量价底背离

```python
# 假设检测到:
# - 类型: 量价底背离
# - 强度: 75/100
# - 置信度: 中
# - 描述: 价格下跌5%，成交量反增20%
```

**分析**:
- 价格创新低，但成交量反而放大
- 说明抛压逐渐减小，可能形成底部
- 建议: 关注企稳信号，考虑分批建仓

## 📁 文件结构

```
position_analysis/analyzers/
├── divergence_analyzer.py          # 主分析器模块
├── test_divergence.py              # 完整测试套件
├── simple_test.py                  # 快速测试脚本
└── DIVERGENCE_ANALYZER_README.md   # 本文档
```

## 🔍 技术细节

### 峰谷识别算法

使用滑动窗口法识别局部极值点：
- 峰值: 窗口内的最高点
- 谷值: 窗口内的最低点
- 保证相邻极值点有足够间隔，避免噪音

### 背离判断逻辑

1. **价格对比**: 比较相邻两个峰/谷的价格
2. **指标对比**: 比较对应时间点的指标值
3. **方向判断**: 价格和指标变化方向是否一致
4. **强度计算**: 根据变化幅度差异评分

### 数据适配器

`normalize_dataframe_columns()` 函数自动适配不同市场的数据格式：
- A股: 中文列名 → 英文小写
- H股: 中文列名 → 英文小写
- 美股: 首字母大写 → 英文小写

## ⚠️ 注意事项

1. **数据要求**:
   - 至少需要60天历史数据
   - 必须包含OHLCV数据
   - 日期需为DatetimeIndex

2. **信号使用**:
   - 背离信号不是买卖点，需结合其他分析
   - 强度>=80的信号更可靠
   - 建议多周期验证

3. **假信号过滤**:
   - 设置合理的峰谷识别窗口
   - 增加最小峰谷间隔
   - 结合趋势和位置判断

4. **市场差异**:
   - 不同市场的背离有效性可能不同
   - A股波动较大，建议提高阈值
   - 美股相对平稳，背离信号更可靠

## 🚀 快速测试

运行简单测试验证功能：

```bash
cd position_analysis/analyzers
python simple_test.py
```

运行完整测试套件（A股/H股/美股）：

```bash
python test_divergence.py
```

## 📈 性能优化

- 使用缓存避免重复计算
- 只分析必要的回看周期
- 并行处理多只股票

## 🤝 集成指南

### 集成到现有分析框架

```python
# 在 position_analysis 中使用
from analyzers.divergence_analyzer import DivergenceAnalyzer

class MarketAnalyzer:
    def __init__(self):
        self.divergence_analyzer = DivergenceAnalyzer()

    def analyze_market(self, df):
        # 添加背离分析
        divergence_result = self.divergence_analyzer.comprehensive_analysis(df)
        return divergence_result
```

### 添加到日报系统

```python
# 在 daily_market_reporter.py 中
from analyzers.divergence_analyzer import DivergenceAnalyzer

def generate_report(index_code):
    analyzer = DivergenceAnalyzer()
    result = analyzer.comprehensive_analysis(df, symbol=index_code)

    if result['has_any_divergence']:
        # 添加到报告中
        report += format_divergence_report(result)
```

## 📞 问题反馈

如有问题或建议，请通过以下方式反馈：
- 提交 Issue
- 查看测试代码了解更多用法
- 参考源码注释

---

**作者**: Claude Code
**创建日期**: 2025-10-14
**版本**: 1.0.0
**适用市场**: A股、H股、美股
