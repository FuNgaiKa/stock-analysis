# 使用说明

## 快速开始

### 最简单的方式
```bash
python quick_start.py
```
这将自动使用多数据源进行市场分析，给出火热程度评分和仓位建议。

## 三种启动方式

### 1. quick_start.py - 快速启动脚本（推荐新手）

**默认模式** - 自动选择最佳数据源：
```bash
python quick_start.py
```

**交互模式** - 手动选择数据源：
```bash
python quick_start.py --interactive
```

输出示例：
```
============================================================
A股市场火热程度快速分析
============================================================

[核心指标]
  火热程度评分: 0.191
  风险等级: 极低风险
  仓位建议: 可考虑满仓操作，但需关注基本面

[市场概况]
  上证指数涨跌幅: 0.52%
  涨停股票: 0 只
  跌停股票: 0 只
```

---

### 2. main.py - 完整主程序（推荐日常使用）

```bash
python main.py
```

功能菜单：
```
1. A股市场分析 (推荐)
2. 复合收益计算
3. 退出
```

包含：
- 市场火热程度分析
- 智能仓位建议
- 复合收益计算器

---

### 3. stock/stock.py - 命令行工具（推荐高级用户）

**交互式选择数据源：**
```bash
python stock/stock.py --interactive
```

会显示数据源菜单：
```
1. efinance (东方财富) - 实时数据，响应快速 (~1-2s)
2. baostock (证券宝) - 历史数据完整 (~5-10s)
3. akshare - 全市场数据 (~30-60s)
4. 腾讯财经 - 快速指数查询 (~0.2s)
5. 多源自动切换 - 智能选择最佳数据源
```

**其他模式：**
```bash
python stock/stock.py              # 多数据源自动切换
python stock/stock.py --test       # 测试模式（使用模拟数据）
python stock/stock.py --single     # 单一数据源模式
```

---

## 数据源说明

### 推荐数据源

| 数据源 | 速度 | 特点 | 适用场景 |
|--------|------|------|----------|
| **efinance** | ⚡⚡⚡ (1-2s) | 实时行情，涨跌停数据 | 实时监控 |
| **baostock** | ⚡⚡ (5-10s) | 历史完整，无需注册 | 历史回测 |
| **腾讯财经** | ⚡⚡⚡ (0.2s) | 三大指数，极速响应 | 快速查看 |
| **akshare** | ⚡ (30-60s) | 全市场覆盖 | 全面分析 |

### 自动切换逻辑
系统会按以下顺序尝试数据源：
1. efinance (首选) → 2. baostock (备用) → 3. 腾讯财经 → 4. 其他

如果一个数据源失败，会自动切换到下一个，确保分析成功。

---

## 编程接口

### 基础使用
```python
from stock.stock import AStockHeatAnalyzer

# 使用默认多数据源
analyzer = AStockHeatAnalyzer()
result = analyzer.analyze_market_heat()

print(f"火热程度: {result['heat_score']:.3f}")
print(f"风险等级: {result['risk_level']}")
print(f"仓位建议: {result['position_suggestion']}")
```

### 指定数据源
```python
# 使用 efinance (快速实时)
analyzer = AStockHeatAnalyzer(data_source='efinance')
result = analyzer.analyze_market_heat()

# 使用 baostock (历史完整)
analyzer = AStockHeatAnalyzer(data_source='baostock')
result = analyzer.analyze_market_heat()
```

### 场景化选择
```python
from stock.data_source_selector import DataSourceSelector

selector = DataSourceSelector()

# 实时监控场景
source = selector.get_quick_recommendation('realtime')
analyzer = AStockHeatAnalyzer(data_source=source)

# 历史回测场景
source = selector.get_quick_recommendation('backtest')
analyzer = AStockHeatAnalyzer(data_source=source)
```

---

## 输出说明

### 火热程度评分 (0-1)
- **0.8+**: 极高风险，建议减仓至3-4成
- **0.6-0.8**: 高风险，建议减仓至5-6成
- **0.4-0.6**: 中等风险，保持6-7成仓位
- **0.2-0.4**: 低风险，可适度加仓至7-8成
- **0-0.2**: 极低风险，可考虑满仓

### 核心指标
- **成交量比率**: 市场活跃度指标
- **价格动量**: 指数涨跌趋势
- **市场广度**: 个股表现分布
- **波动率**: 市场风险水平
- **情绪指标**: 涨跌停情绪

---

## 常见问题

### Q1: 数据获取失败怎么办？
A: 系统会自动尝试多个数据源。如果全部失败，请：
1. 检查网络连接
2. 尝试使用测试模式：`python stock/stock.py --test`
3. 手动指定其他数据源

### Q2: 如何提高分析速度？
A:
- 使用腾讯财经（0.2秒）：仅三大指数
- 使用 efinance（1-2秒）：完整实时数据
- 避免使用 akshare（30-60秒）：全市场扫描

### Q3: 可以自定义权重吗？
A: 可以修改 `stock/stock.py` 中的权重配置：
```python
self.weights = {
    "volume_ratio": 0.25,      # 成交量比率
    "price_momentum": 0.20,     # 价格动量
    "market_breadth": 0.20,     # 市场广度
    "volatility": 0.15,         # 波动率
    "sentiment": 0.20,          # 情绪指标
}
```

---

## 测试

### 测试所有数据源
```bash
python stock/test_integration.py
```

### 测试单个数据源
```bash
# 测试 baostock
python stock/baostock_source.py

# 测试 efinance
python stock/efinance_source.py

# 测试数据源选择器
python stock/data_source_selector.py
```

---

## 更多信息

详细文档请参考 [README.md](README.md)