# 增强版A股市场火热程度分析器

## 概述
增强版分析器在原有基础上进行了全面升级，提供更精准的市场分析和更稳定的数据获取能力。

## 主要改进

### 1. 多数据源支持
- **AKShare** - 主要数据源
- **新浪财经** - 实时指数数据备份
- **网易财经** - 历史数据备份  
- **Yahoo Finance** - 国际化数据源
- **Tushare** - 专业金融数据(需配置)

### 2. 增强指标体系
原有5个指标扩展为6个维度：
- **成交量指标** (20%) - 基础比率+相对强弱+量价关系
- **价格动量** (18%) - 多指数加权动量
- **市场广度** (22%) - 涨跌停比例+多空力量+市场参与度
- **技术指标** (15%) - RSI+MACD+布林带
- **情绪指标** (15%) - 增强版情绪分析+极端程度
- **资金流向** (10%) - 资金流向评估

### 3. 新增功能
- **风险因子分析** - 识别具体风险点
- **策略建议** - 个性化操作建议
- **市场极端度** - 识别异常市场状态
- **多空比率** - 精确的市场情绪量化

## 安装依赖

```bash
pip install -r requirements_enhanced.txt
```

注意：TA-Lib需要单独安装：
```bash
# Windows
pip install TA-Lib

# macOS  
brew install ta-lib
pip install TA-Lib

# Linux
sudo apt-get install libta-lib-dev
pip install TA-Lib
```

## 使用方法

### 基础使用
```python
from enhanced_stock_analyzer import EnhancedAStockAnalyzer

# 初始化分析器
analyzer = EnhancedAStockAnalyzer()

# 分析今日市场
result = analyzer.analyze_enhanced_market_heat()

if result:
    print(f"火热程度: {result['heat_score']:.3f}")
    print(f"风险评估: {result['risk_assessment']['level']}")
    print(f"仓位建议: {result['position_advice']['position']}")
```

### 历史分析
```python
# 分析指定日期
result = analyzer.analyze_enhanced_market_heat('20231201')
```

### 对比演示
```python
# 运行对比演示
python comparison_demo.py
```

## 数据源配置

### 1. Tushare配置（可选）
```python
# 在enhanced_data_sources.py中配置
import tushare as ts
ts.set_token('your_token_here')
```

### 2. 代理配置（如需要）
```python
# 在requests调用中添加代理
proxies = {
    'http': 'http://proxy:port',
    'https': 'https://proxy:port'
}
```

## 输出示例

```
=== 增强版A股市场火热程度分析 ===

综合火热程度评分: 0.652
风险评估: 高风险
仓位建议: 建议减仓至40-50%

详细指标:
- volume_indicators: 0.720
- price_momentum: 0.340
- market_breadth: 0.580
- technical_indicators: 0.850
- sentiment_indicators: 0.410
- fund_flow: 0.290

市场摘要:
- 涨停股票: 45
- 跌停股票: 12
- 市场参与度: 0.570
- 多空比率: 0.789

风险因子: 技术指标过热, 成交量异常放大
策略建议: 关注技术指标背离
```

## 性能对比

| 特性 | 原版 | 增强版 | 改进 |
|------|------|--------|------|
| 分析维度 | 5个 | 6个 | +1 |
| 数据源 | 1个 | 5个 | +4 |
| 技术指标 | 无 | RSI/MACD/布林带 | +3 |
| 风险评估 | 基础 | 多因子分析 | ✓ |
| 策略建议 | 简单 | 个性化 | ✓ |

## 常见问题

### Q: 数据获取失败怎么办？
A: 增强版会自动尝试多个数据源，通常能保证至少一个数据源可用。

### Q: 技术指标需要多少历史数据？
A: RSI需要14天，MACD需要26天，系统会自动处理数据不足的情况。

### Q: 如何提高分析准确性？  
A: 建议结合基本面分析，技术指标仅作为辅助参考。

## 文件说明

- `enhanced_stock_analyzer.py` - 增强版主分析器
- `enhanced_data_sources.py` - 多数据源管理器  
- `comparison_demo.py` - 对比演示脚本
- `requirements_enhanced.txt` - 依赖项清单

## 注意事项

1. **数据源限制** - 免费数据源可能有频率限制
2. **网络依赖** - 需要稳定的网络连接
3. **计算资源** - 技术指标计算需要一定CPU资源
4. **法律合规** - 请遵守各数据源的使用条款

## 更新日志

### v2.0 (当前版本)
- ✨ 多数据源支持
- ✨ 技术指标集成
- ✨ 增强风险评估
- 🐛 修复数据获取稳定性问题

### v1.0 (原版)
- 基础市场火热程度分析
- 单一数据源(AKShare)