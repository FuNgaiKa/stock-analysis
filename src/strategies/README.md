# 四指标共振买卖点策略

基于 **MACD + RSI + KDJ + MA** 的四指标共振交易系统，自动识别股票/ETF的最佳买卖点，并提供完整的回测框架验证策略表现。

## 🎯 核心优势

- **四指标共振** - 多维度验证，提高信号可靠性
- **量化评分** - 0-100分评分系统，一目了然
- **智能判断** - 自动区分强买入/买入/观望/卖出/强卖出
- **实时分析** - 支持股票、ETF、指数
- **完整回测** - 历史数据验证，计算胜率/盈亏比/夏普比率等
- **性能优化** - 止损止盈、仓位管理、交易成本模拟

## 📊 策略口诀

> **"先定方向(MACD)，再选时机(KDJ/RSI)，始终管风险(ATR)"**

## 🚀 快速开始

### 方式1: 交互式分析 (推荐)

```bash
python trading_strategies/examples/quick_resonance_demo.py
```

选择模式:
- **模式1**: 单只分析 - 输入任意股票/ETF/指数代码
- **模式2**: 批量分析 - 分析预设的6只标的
- **模式3**: 快速分析 - 直接分析上证指数

### 方式2: 命令行直接分析

```bash
# 分析上证指数
python -c "from trading_strategies.examples.quick_resonance_demo import analyze_stock; analyze_stock('sh000001', '上证指数')"

# 分析酒ETF
python -c "from trading_strategies.examples.quick_resonance_demo import analyze_stock; analyze_stock('512690', '酒ETF')"

# 分析贵州茅台
python -c "from trading_strategies.examples.quick_resonance_demo import analyze_stock; analyze_stock('600519', '贵州茅台')"
```

### 方式3: Python API调用

```python
from trading_strategies.signal_generators.technical_indicators import TechnicalIndicators
from trading_strategies.signal_generators.resonance_signals import ResonanceSignalGenerator
import akshare as ak

# 1. 获取数据
df = ak.stock_zh_index_daily(symbol='sh000001')
df = df.tail(100)

# 2. 计算技术指标
calculator = TechnicalIndicators()
df = calculator.calculate_all_indicators(df)

# 3. 生成交易信号
generator = ResonanceSignalGenerator()
signal = generator.generate_trading_signal(df)

# 4. 查看结果
generator.print_signal_report(signal, "上证指数")

# 或者直接使用返回值
print(f"信号: {signal['action']}")
print(f"置信度: {signal['confidence']}")
print(f"建议: {signal['suggestion']}")
```

## 📈 信号说明

### 买入信号 (四指标共振)

当以下条件同时满足时，产生强买入信号:

1. ✅ **MA (均线)**: 股价突破5日/10日均线，呈多头排列
2. ✅ **MACD**: 零轴下方金叉，红柱扩大
3. ✅ **KDJ**: 低位金叉，J线突破向上
4. ✅ **RSI**: 从超卖区(<30)反弹，突破50确认

**评分规则**:
- **85-100分** + 3个以上共振 → `STRONG_BUY` 强烈买入
- **70-85分** + 2个以上共振 → `BUY` 买入
- **55-70分** → `WEAK_BUY` 弱买入
- **<55分** → `NEUTRAL` 观望

### 卖出信号 (四指标共振)

当以下条件同时满足时，产生强卖出信号:

1. ✅ **MA (均线)**: 股价跌破5日/10日均线，呈空头排列
2. ✅ **MACD**: 零轴上方死叉，绿柱扩大
3. ✅ **KDJ**: 高位死叉，J线向下
4. ✅ **RSI**: 进入超买区(>70)后回落，跌破50确认

## 📋 输出示例

```
======================================================================
📊 上证指数 - 四指标共振交易信号报告
======================================================================

【交易信号】🟢🟢 BUY
【置信度】⭐⭐⭐⭐ (72%)

【评分对比】
  买入评分: 72.5/100 (共振: 3/4)
  卖出评分: 38.2/100 (共振: 1/4)

【操作建议】
  买入信号(评分72.5/100)，多个指标支持，可以适度买入，建议仓位40-60%

【详细理由】
  ✅ MA: 多头排列(价格回调)
  ✅ MACD: 金叉 - 零轴下方 (强势信号)
  ✅ KDJ: 低位金叉 (K:45.2, D:38.6)
  ⚠️  RSI: 中性偏多 (58.3)

======================================================================
```

## 🧩 项目结构

```
trading_strategies/
├── signal_generators/          # 信号生成器
│   ├── technical_indicators.py # 技术指标计算 (MACD/RSI/KDJ/MA)
│   └── resonance_signals.py    # 四指标共振信号生成
│
├── backtesting/                # 回测框架 ✅
│   ├── backtest_engine.py      # 回测引擎
│   └── performance_metrics.py  # 性能评估
│
├── examples/                   # 示例程序
│   └── quick_resonance_demo.py # 快速启动示例
│
├── README.md                   # 使用文档
└── BACKTEST_GUIDE.md          # 回测指南 ✅
```

## 🔧 技术指标详解

### MACD (Moving Average Convergence Divergence)
- **参数**: 快线12, 慢线26, 信号线9
- **作用**: 判断趋势方向和动量
- **关键**: 零轴下方金叉最强，零轴上方死叉最危险

### RSI (Relative Strength Index)
- **参数**: 14日
- **作用**: 判断超买超卖
- **关键**: <30超卖，>70超买，50是多空分界

### KDJ (Stochastic Oscillator)
- **参数**: N=9, M1=3, M2=3
- **作用**: 精确择时
- **关键**: K/D低位金叉买入，高位死叉卖出

### MA (Moving Average)
- **参数**: 5日、10日、20日、60日
- **作用**: 判断趋势强度
- **关键**: 多头排列看多，空头排列看空

## ⚙️ 参数配置

所有指标参数可在代码中自定义:

```python
# 自定义MA周期
df = calculator.calculate_ma(df, periods=[5, 10, 20, 60, 120])

# 自定义MACD参数
df = calculator.calculate_macd(df, fast_period=12, slow_period=26, signal_period=9)

# 自定义RSI周期
df = calculator.calculate_rsi(df, period=14)

# 自定义KDJ参数
df = calculator.calculate_kdj(df, n=9, m1=3, m2=3)
```

## 📊 支持的标的类型

- **指数**: sh000001 (上证), sz399006 (创业板), sh000300 (沪深300)
- **ETF**: 512690 (酒ETF), 512880 (证券ETF), 159870 (化工ETF)
- **股票**: 600519 (贵州茅台), 000858 (五粮液) 等6位代码

## ⚠️ 风险提示

1. 技术指标有滞后性，仅供参考
2. 四指标共振提高准确率，但不保证100%正确
3. 建议结合基本面、资金面、政策面综合判断
4. 严格止损，单笔风险控制在2-3%以内
5. 投资有风险，决策需谨慎

## 🚀 快速回测

### 自动回测测试

```bash
python test_backtest.py
```

### 交互式回测

```bash
python run_backtest.py
```

选择:
1. 单个回测 - 自定义参数
2. 快速回测 - 上证指数500天
3. 批量回测 - 对比多个指数

### 回测结果示例

```
【收益指标】
  总收益率:    14.99%
  年化收益率:   7.29%
  最大回撤:    16.03%

【交易指标】
  总交易次数:     11
  胜率:        36.36%
  盈亏比:       1.53
  夏普比率:     0.35
```

详见 [回测指南](./BACKTEST_GUIDE.md)

---

## 🛣️ 开发路线图

### ✅ Phase 1 - 已完成
- [x] 技术指标计算模块
- [x] 四指标共振信号生成器
- [x] 交互式分析工具
- [x] 批量分析功能

### ✅ Phase 2 - 已完成
- [x] 回测框架引擎
- [x] 性能评估模块
- [x] 胜率/盈亏比/夏普比率统计
- [x] 止损止盈机制
- [x] 可视化图表

### 📅 Phase 3 - 计划中
- [ ] 参数优化工具
- [ ] 滚动回测
- [ ] 蒙特卡洛模拟
- [ ] 网格交易策略
- [ ] 动量反转策略
- [ ] 多因子选股模型
- [ ] 机器学习信号优化

## 💡 使用技巧

1. **批量筛选**: 使用批量分析模式快速筛选买入机会
2. **趋势确认**: 重点关注共振数≥3的信号
3. **分批建仓**: 强买入信号出现后，分2-3次建仓
4. **止损设置**: 买入后设置5-8%的止损位
5. **止盈策略**: 卖出信号出现或盈利15%+分批止盈

## 📖 学习资源

- [MACD指标详解](https://www.investopedia.com/terms/m/macd.asp)
- [RSI指标使用](https://www.investopedia.com/terms/r/rsi.asp)
- [KDJ实战技巧](https://www.investopedia.com/terms/s/stochasticoscillator.asp)

## 🤝 贡献

欢迎提交Issue和PR！

---

**Made with ❤️ by Claude & Russ**
