# A股市场火热程度分析器

一个专业的A股市场分析工具，集成多数据源架构，提供实时市场火热程度分析和智能仓位建议。

## 🎯 项目特色

### 🥇 多数据源智能架构
- **akshare 优化版**（主力）- 免费稳定，完整市场数据
- **腾讯财经**（备用）- 0.2秒快速指数数据
- **Ashare**（备用）- 轻量级价格数据
- **新浪财经** - 传统稳定接口
- **yfinance** - 国际市场支持
- **自动故障切换** - 确保数据获取成功率

### 📊 核心功能
- ✅ **市场火热程度量化分析** - 综合多维指标
- ✅ **智能仓位建议** - 基于风险评估
- ✅ **实时涨跌停监控** - 47只涨停 + 33只跌停
- ✅ **5434只股票** 全市场覆盖
- ✅ **网络重试机制** - 3次重试 + 指数退避
- ✅ **智能缓存** - 5分钟缓存提升性能

## 📈 项目结构

```
stock-analysis/
├── stock/                          # 核心分析模块
│   ├── stock.py                   # 🎯 主分析器 (升级版)
│   ├── akshare_optimized.py       # 🥇 akshare优化数据源
│   ├── tencent_source.py          # 🥈 腾讯财经数据源
│   ├── tushare_source.py          # 🥉 tushare专业数据源
│   ├── enhanced_data_sources.py   # 多数据源管理器
│   ├── enhanced_stock_analyzer.py # 技术分析增强版
│   ├── Ashare.py                  # 轻量级数据源
│   └── joinquant.py              # 聚宽数据源
├── compound_interest/             # 复合收益计算
├── requirements.txt              # 项目依赖
└── README.md                    # 项目文档
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 安装TA-Lib (macOS)
brew install ta-lib
```

### 2. 立即运行
```bash
# 🥇 推荐：多数据源模式 (akshare优化版主导)
python stock/stock.py

# 🧪 演示模式：查看完整功能
python stock/stock.py --test

# 🔧 单数据源模式：使用原版akshare
python stock/stock.py --single
```

### 3. 运行结果示例
```
============================================================
A股市场火热程度分析报告
分析时间: 2025-09-29 00:55:48
============================================================
综合火热程度评分: 0.185
风险等级: 极低风险
仓位建议: 可考虑满仓操作，但需关注基本面

指标详情:
- 成交量比率: 1.00
- 价格动量: 0.0000
- 市场广度: 0.0000
- 波动率: 0.0200
- 情绪指标: 0.0000

市场概况:
- 上证指数涨跌幅: -0.65%
- 涨停股票数: 47
- 跌停股票数: 33
============================================================
```

## 🛠️ 核心技术

### 数据源性能对比
| 数据源 | 响应时间 | 数据量 | 稳定性 | 费用 |
|--------|----------|--------|--------|------|
| **akshare优化版** | 49s | 5434只股票 | ⭐⭐⭐⭐⭐ | 免费 |
| **腾讯财经** | 0.2s | 3大指数 | ⭐⭐⭐⭐⭐ | 免费 |
| **Ashare** | 0.7s | 价格数据 | ⭐⭐⭐⭐ | 免费 |
| **tushare** | 需积分 | 专业数据 | ⭐⭐⭐⭐⭐ | 积分制 |

### 量化指标体系
- **成交量比率** (25%) - 市场活跃度
- **价格动量** (20%) - 指数涨跌趋势
- **市场广度** (20%) - 个股表现分布
- **波动率** (15%) - 市场风险水平
- **情绪指标** (20%) - 涨跌停情绪

## 📋 数据源配置

### 免费数据源 (无需配置)
- ✅ **akshare** - 完全免费，5434只股票数据
- ✅ **腾讯财经** - 实时指数，响应极快
- ✅ **新浪财经** - 传统稳定接口

### 可选专业数据源
```python
# tushare 配置 (可选)
import tushare as ts
ts.set_token('your_token_here')  # 注册获取: https://tushare.pro
```

## 💡 使用示例

### 基础分析
```python
from stock.stock import AStockHeatAnalyzer

# 创建分析器
analyzer = AStockHeatAnalyzer()

# 执行分析
result = analyzer.analyze_market_heat()
print(f"火热程度: {result['heat_score']:.3f}")
print(f"风险等级: {result['risk_level']}")
```

### 多数据源测试
```python
from stock.enhanced_data_sources import MultiSourceDataProvider

# 测试所有数据源
provider = MultiSourceDataProvider()
data = provider.get_market_data()

# 查看数据源使用情况
print("成功获取数据，来源：第一优先级数据源")
```

### 单独测试数据源
```python
# 测试腾讯财经
from stock.tencent_source import TencentDataSource
tencent = TencentDataSource()
data = tencent.get_market_summary()

# 测试akshare优化版
from stock.akshare_optimized import OptimizedAkshareSource
akshare = OptimizedAkshareSource()
market_data = akshare.get_market_data()
```

## ⚡ 性能优化

### 缓存机制
- 5分钟数据缓存
- 减少重复请求
- 提升响应速度

### 网络优化
- 3次重试机制
- 指数退避延时
- 请求间隔控制

### 容错设计
- 多数据源备份
- 自动故障切换
- 优雅降级处理

## 🔧 故障排除

### 常见问题

**Q: TA-Lib安装失败？**
```bash
# macOS
brew install ta-lib
pip install TA-Lib

# Ubuntu
sudo apt-get install libta-lib0-dev
pip install TA-Lib
```

**Q: 网络连接失败？**
- 检查网络环境
- 使用测试模式：`python stock/stock.py --test`
- 程序会自动切换数据源

**Q: 数据获取慢？**
- 首次运行需要49秒获取完整数据
- 后续使用缓存，响应更快
- 可使用腾讯数据源获取指数（0.2秒）

## 📊 升级日志

### v2.0 (2025-09-29) - 重大升级
- 🆕 **akshare优化版**成为主数据源
- 🆕 集成**腾讯财经**高速接口
- 🆕 **多数据源智能切换**架构
- 🆕 **网络重试机制** + **智能缓存**
- 🆕 支持 **5434只股票** + **47只涨停** 数据
- 🔧 优化性能，提升稳定性

### v1.0 - 基础版本
- ✅ 基础市场分析功能
- ✅ 单一akshare数据源
- ✅ 火热程度量化模型

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发建议
- 新增数据源请在 `enhanced_data_sources.py` 中扩展
- 优化性能请关注缓存和网络重试机制
- 添加测试用例确保稳定性

## ⚖️ 免责声明

本项目仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。

## 📞 技术支持

- **akshare 文档**: https://akshare.akfamily.xyz/
- **tushare 文档**: https://tushare.pro/document/2
- **项目问题**: 欢迎提交 GitHub Issues

---

**🎯 让数据驱动投资决策！** 🚀