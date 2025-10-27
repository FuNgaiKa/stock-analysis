# 回测框架使用指南

## 📊 回测框架概述

回测框架可以验证四指标共振策略在历史数据上的表现，提供详细的性能指标和交易明细。

## 🚀 快速开始

### 方式1: 自动测试 (最简单)

```bash
python test_backtest.py
```

自动回测上证指数500天数据，输出完整性能报告。

### 方式2: 交互式回测

```bash
python run_backtest.py
```

选择回测模式:
- **模式1**: 单个回测 - 自定义所有参数
- **模式2**: 快速回测 - 上证指数500天
- **模式3**: 批量回测 - 对比3个主要指数

### 方式3: Python API

```python
from trading_strategies.signal_generators.technical_indicators import TechnicalIndicators
from trading_strategies.signal_generators.resonance_signals import ResonanceSignalGenerator
from trading_strategies.backtesting.backtest_engine import BacktestEngine
from trading_strategies.backtesting.performance_metrics import PerformanceMetrics
import akshare as ak

# 1. 获取数据
df = ak.stock_zh_index_daily(symbol='sh000001')
df = df.tail(500).set_index('date')

# 2. 计算指标
calculator = TechnicalIndicators()
df = calculator.calculate_all_indicators(df)

# 3. 运行回测
generator = ResonanceSignalGenerator()
engine = BacktestEngine(
    initial_capital=100000,  # 10万初始资金
    commission=0.0003,        # 0.03%手续费
    stop_loss=0.08,          # 8%止损
    take_profit=0.15          # 15%止盈
)

result = engine.run_backtest_with_strategy(df, generator)

# 4. 计算性能
metrics = PerformanceMetrics()
performance = metrics.generate_performance_report(
    returns=result['daily_returns'],
    trades=result['trades'],
    initial_capital=100000
)

# 5. 打印报告
metrics.print_performance_report(performance, "我的策略")
```

## 📋 性能指标说明

### 收益指标
- **总收益率**: 策略期间的累计收益
- **年化收益率**: 换算成年化的收益率
- **期末资金**: 回测结束时的总资金
- **盈亏金额**: 实际盈亏金额

### 风险指标
- **年化波动率**: 收益率的标准差(年化)
- **最大回撤**: 从最高点到最低点的最大跌幅
- **回撤持续**: 最大回撤持续的天数
- **恢复时间**: 从最大回撤恢复到前高的天数

### 风险调整收益
- **夏普比率**: (年化收益 - 无风险利率) / 年化波动率
  - > 1.0: 优秀
  - 0.5-1.0: 良好
  - < 0.5: 一般
- **卡玛比率**: 年化收益 / |最大回撤|
  - > 1.0: 优秀
  - 0.5-1.0: 良好

### 交易指标
- **总交易次数**: 完整买卖的次数
- **胜率**: 盈利交易占比
- **平均盈利/亏损**: 盈利和亏损交易的平均收益率
- **盈亏比**: 总盈利 / 总亏损
  - > 2.0: 优秀
  - 1.5-2.0: 良好
  - < 1.5: 一般

## 📊 回测结果示例

### 上证指数 500天回测

```
【收益指标】
  总收益率:    14.99%
  年化收益率:   7.29%
  期末资金:      114,990 元
  盈亏金额:       14,990 元

【风险指标】
  年化波动率:  12.28%
  最大回撤:    16.03%

【风险调整收益】
  夏普比率:     0.35
  卡玛比率:     0.45

【交易指标】
  总交易次数:     11
  胜率:        36.36%
  盈亏比:       1.53
```

**分析**:
- ✅ 年化收益7.29%，跑赢3%无风险利率
- ⚠️ 最大回撤16%，需要承受一定风险
- ⚠️ 胜率36%偏低，但盈亏比1.53补偿
- 💡 典型的"低胜率高盈亏比"策略

## 🎯 优化建议

### 提高胜率
1. **调整共振阈值**: 买入评分从70提高到75
2. **增加过滤条件**: 只在趋势向上时交易
3. **优化参数**: 调整MACD/RSI/KDJ参数

### 降低回撤
1. **收紧止损**: 从8%降到5-6%
2. **分批建仓**: 不要一次性满仓
3. **趋势过滤**: 只在MA多头排列时交易

### 提高盈亏比
1. **放宽止盈**: 从15%提高到20%
2. **移动止损**: 盈利后移动止损保护利润
3. **金字塔加仓**: 盈利后小幅加仓

## 🛠️ 参数配置

### 回测参数

```python
engine = BacktestEngine(
    initial_capital=100000,   # 初始资金
    commission=0.0003,        # 手续费率(双边)
    slippage=0.0001,          # 滑点
    stop_loss=0.08,           # 止损比例
    take_profit=0.15,         # 止盈比例
)
```

### 信号参数

可在`technical_indicators.py`中调整:

```python
# MACD参数
calculate_macd(fast_period=12, slow_period=26, signal_period=9)

# RSI参数
calculate_rsi(period=14)

# KDJ参数
calculate_kdj(n=9, m1=3, m2=3)

# MA周期
calculate_ma(periods=[5, 10, 20, 60])
```

## 📈 可视化图表

### 生成回测图表

```python
# 在回测后调用
engine.plot_results(df, save_path='my_backtest.png')
```

生成3张图:
1. **组合价值曲线** - 资金增长情况
2. **价格与交易点** - 买卖点标注
3. **累计收益率** - 收益率走势

## ⚠️ 注意事项

### 过拟合风险
- 不要过度优化参数以适应历史数据
- 样本外测试：留一部分数据不参与优化
- 参数稳定性：小幅调整参数不应导致结果剧变

### 交易成本
- 实盘手续费可能高于0.03%
- 滑点在大单或波动大时更明显
- 考虑印花税(卖出时0.1%)

### 市场环境
- 牛市/熊市/震荡市表现可能不同
- 分别测试不同市场环境
- 策略可能更适合某种市场

## 🔄 批量回测

### 对比不同标的

```bash
python run_backtest.py
# 选择模式3
```

输出对比表:
```
code       name      total_return  annual_return  sharpe  max_dd   win_rate
sh000001   上证指数    14.99%        7.29%         0.35    -16.03%  36.36%
sz399006   创业板指    22.15%        10.82%        0.52    -18.52%  42.86%
sh000300   沪深300     18.45%        9.01%         0.44    -15.21%  38.89%
```

### 对比不同参数

```python
# 测试不同止损
for stop_loss in [0.05, 0.08, 0.10, 0.12]:
    engine = BacktestEngine(stop_loss=stop_loss, ...)
    result = engine.run_backtest_with_strategy(df, generator)
    # 记录结果
```

## 📚 进阶功能

### 滚动回测

测试策略在不同时间段的稳定性:

```python
window = 252  # 一年
step = 63     # 一个季度

for i in range(0, len(df) - window, step):
    df_window = df.iloc[i:i+window]
    # 运行回测
    # 记录结果
```

### 蒙特卡洛模拟

测试策略的鲁棒性:

```python
for _ in range(1000):
    # 随机打乱交易顺序
    shuffled_trades = np.random.permutation(trades)
    # 计算性能
    # 记录分布
```

## 💡 最佳实践

1. **先测试后实盘**: 充分回测验证策略
2. **保守参数**: 实盘参数比回测更保守
3. **小资金试错**: 先用小资金验证
4. **记录交易**: 实盘记录与回测对比
5. **定期复盘**: 每月/季度复盘策略表现

---

**Made with ❤️ by Claude & Russ**
