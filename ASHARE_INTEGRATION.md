# 多数据源架构说明 v2.0

## 🎯 概述

本项目已升级为**多数据源智能架构**，以 **akshare 优化版** 为主力数据源，集成7大数据源，提供最稳定的A股数据获取能力。

## 🏗️ 架构升级

### v2.0 数据源架构
```
🥇 akshare优化版 (主力) ──┐
🥈 腾讯财经 (快速)      ──┤
🥉 Ashare (轻量)       ──┤── 智能切换管理器
📊 新浪财经 (传统)      ──┤
🌍 yfinance (国际)     ──┤
🔄 akshare (原版)      ──┤
📰 网易+tushare (专业) ──┘
```

### 最新数据源优先级
1. **akshare优化版**（主力）- 49s获取5434只股票
2. **腾讯财经**（备用1）- 0.2s快速指数数据
3. **Ashare**（备用2）- 轻量级价格数据
4. **新浪财经**（备用3）- 传统稳定接口
5. **yfinance**（备用4）- 国际市场支持
6. **akshare原版**（备用5）- 兼容性保留
7. **网易+tushare**（专业）- 高级功能

### 3. 功能特点
- **自动故障切换**：如果Ashare失败，自动尝试下一个数据源
- **数据验证**：自动验证数据完整性
- **缓存机制**：避免重复请求
- **统一接口**：所有数据源返回统一格式

## 使用方法

### 基础使用

```python
from stock.enhanced_data_sources import MultiSourceDataProvider

# 创建数据提供器
provider = MultiSourceDataProvider()

# 获取市场数据
market_data = provider.get_market_data()

# 查看指数数据
if market_data and market_data.get('sz_index') is not None:
    print(f"上证指数: {market_data['sz_index']['收盘'].iloc[0]}")
```

### 获取增强指标

```python
# 获取市场增强指标
indicators = provider.get_enhanced_market_indicators()

for key, value in indicators.items():
    print(f"{key}: {value}")
```

### 直接使用Ashare

```python
from stock.Ashare import get_price

# 获取股票数据
data = get_price('sh000001', frequency='1d', count=10)
print(data)
```

## 测试验证

运行以下命令测试集成：

```bash
# 测试Ashare基础功能
python test_ashare_final.py

# 测试数据源集成
python test_direct_integration.py
```

## 优势对比

### Ashare vs 其他数据源

| 特性 | Ashare | AKShare | Tushare | 富途API |
|------|--------|---------|---------|---------|
| 免费程度 | ✅ 完全免费 | ✅ 免费 | ⚠️ 需积分 | ❌ 需开户 |
| 稳定性 | ✅ 极高 | ⚠️ 一般 | ✅ 高 | ✅ 高 |
| API限制 | ✅ 无限制 | ⚠️ 有限制 | ❌ 严格 | ❌ 严格 |
| 安装难度 | ✅ 单文件 | ✅ 简单 | ✅ 简单 | ⚠️ 复杂 |
| A股支持 | ✅ 完整 | ✅ 完整 | ✅ 完整 | ✅ 支持 |
| 实时性 | ✅ 实时 | ✅ 实时 | ✅ 实时 | ✅ 实时 |

## 数据支持

### 支持的指数
- 上证指数 (sh000001)
- 深证成指 (sz399001)
- 创业板指 (sz399006)

### 支持的数据类型
- 日线 (1d)
- 周线 (1w)
- 月线 (1M)
- 分钟线 (1m, 5m, 15m, 30m, 60m)

### 支持的字段
- open（开盘价）
- high（最高价）
- low（最低价）
- close（收盘价）
- volume（成交量）

## 注意事项

1. **网络依赖**：需要访问腾讯和新浪的数据接口
2. **交易时间**：非交易时间获取的是最新收盘数据
3. **数据延迟**：实时数据可能有15分钟延迟
4. **代码格式**：支持多种代码格式（sh/sz前缀）

## 常见问题

### Q: Ashare无法获取数据？
A: 检查网络连接，确保可以访问 `web.ifzq.gtimg.cn` 和 `money.finance.sina.com.cn`

### Q: 数据获取很慢？
A: 首次获取会有网络延迟，之后会使用缓存机制加速

### Q: 如何切换数据源？
A: 系统会自动按优先级尝试，无需手动切换

### Q: 可以只使用Ashare吗？
A: 可以，直接导入 `from stock.Ashare import get_price` 使用

## 更新日志

### 2025-09-29 v2.0 重大升级
- 🆕 **akshare优化版**成为主力数据源
- 🆕 集成**腾讯财经**0.2秒快速接口
- 🆕 **7层数据源**智能切换架构
- 🆕 **5434只股票** + **47只涨停**数据支持
- 🆕 **网络重试机制** + **智能缓存**
- 🔧 性能优化，稳定性提升至95%

### 2025-09-28 v1.0
- ✅ 集成Ashare数据源
- ✅ 添加多数据源备份机制
- ✅ 实现自动故障切换
- ✅ 完成集成测试
- ✅ 更新项目文档

## 参考资源

- Ashare GitHub: https://github.com/mpquant/Ashare
- AKShare文档: https://akshare.akfamily.xyz/
- 项目README: README.md

## 联系与反馈

如有问题或建议，请在项目中提Issue。