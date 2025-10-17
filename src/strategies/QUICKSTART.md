# 四指标共振策略 - 快速指引

## 🎯 这是什么？

基于 **MACD + RSI + KDJ + MA** 的四指标共振交易系统,可以:
- ✅ 自动分析股票/ETF/指数的买卖点
- ✅ 提供0-100分的量化评分
- ✅ 历史回测验证策略表现

## 🚀 立即开始

### 1. 分析买卖点 (实时)

```bash
# 快速分析上证指数
python test_resonance.py

# 交互式分析(可选择任意标的)
python run_resonance_strategy.py
```

### 2. 历史回测 (验证策略)

```bash
# 快速回测
python test_backtest.py

# 交互式回测(自定义参数)
python run_backtest.py
```

## 📊 输出示例

### 实时信号
```
【交易信号】🟢🟢 BUY
【置信度】⭐⭐⭐⭐ (72%)
【操作建议】买入信号，建议仓位40-60%
```

### 回测结果
```
【收益指标】
  总收益率:    14.99%
  年化收益率:   7.29%

【交易指标】
  胜率:        36.36%
  盈亏比:       1.53
  夏普比率:     0.35
```

## 📁 文件说明

### 快速启动脚本
- `test_resonance.py` - 测试实时分析 (3只标的)
- `test_backtest.py` - 测试回测框架 (上证500天)
- `run_resonance_strategy.py` - 交互式实时分析
- `run_backtest.py` - 交互式回测

### 核心模块
- `trading_strategies/` - 策略核心代码
  - `signal_generators/` - 信号生成器
  - `backtesting/` - 回测框架
  - `examples/` - 示例代码

### 文档
- `trading_strategies/README.md` - 详细使用文档
- `trading_strategies/BACKTEST_GUIDE.md` - 回测指南

## 💡 快速示例

### Python API
```python
from trading_strategies.signal_generators.technical_indicators import TechnicalIndicators
from trading_strategies.signal_generators.resonance_signals import ResonanceSignalGenerator
import akshare as ak

# 获取数据
df = ak.stock_zh_index_daily(symbol='sh000001').tail(100)

# 计算指标 + 生成信号
calculator = TechnicalIndicators()
df = calculator.calculate_all_indicators(df)

generator = ResonanceSignalGenerator()
signal = generator.generate_trading_signal(df)

# 查看结果
print(f"信号: {signal['action']}")  # BUY/SELL/HOLD
print(f"评分: {signal['buy_score']}/100")
print(f"建议: {signal['suggestion']}")
```

## 📚 更多资源

- [完整文档](./trading_strategies/README.md)
- [回测指南](./trading_strategies/BACKTEST_GUIDE.md)
- 技术支持: 欢迎提交Issue

## ⚠️ 风险提示

- 策略仅供学习研究，不构成投资建议
- 历史表现不代表未来收益
- 投资有风险，决策需谨慎

---

**Made with ❤️ by Claude & Russ**
