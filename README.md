# 股票市场综合分析系统

一个功能完善的股票市场分析工具集，集成多数据源架构，提供A股/港股市场分析、历史点位对比、估值分析、均线偏离度监控等多维度量化分析功能。

## 🎯 项目特色

### 🥇 多数据源智能架构
- **efinance (东方财富)**（推荐）- 免费实时，响应速度快
- **baostock (证券宝)**（推荐）- 免费开源，历史数据完整
- **腾讯财经**（备用）- 0.2秒快速指数数据
- **akshare** - 免费稳定，完整市场数据
- **Ashare**（备用）- 轻量级价格数据
- **新浪财经** - 传统稳定接口
- **yfinance** - 国际市场支持
- **自动故障切换** - 确保数据获取成功率

### 📊 核心功能

#### 🔥 A股市场火热程度分析
- ✅ **市场火热程度量化分析** - 综合多维指标
- ✅ **智能仓位建议** - 基于风险评估
- ✅ **实时涨跌停监控** - 涨停/跌停实时统计
- ✅ **5434只股票** 全市场覆盖
- ✅ **网络重试机制** - 3次重试 + 指数退避
- ✅ **智能缓存** - 5分钟缓存提升性能

#### 📈 历史点位对比分析系统
- ✅ **智能市场状态诊断** (Phase 3.1) - 12维度自动识别牛市/熊市/震荡市
- ✅ **九维度指标体系** (Phase 2) - 估值/资金/情绪/宽度/技术/波动率全面分析
- ✅ **历史相似点位查找** - 基于价格、成交量等多因子匹配
- ✅ **概率统计预测** - 5/10/20/60日涨跌概率和平均收益率
- ✅ **置信度评估** - 样本量/一致性/时间分散度综合评分
- ✅ **仓位管理建议** - Kelly公式优化的量化仓位策略
- ✅ **支持多标的** - 指数/ETF/个股全支持

#### 🌏 港股市场分析
- ✅ **港股指数分析** - 恒生指数/恒生科技/恒生国企
- ✅ **技术指标分析** - KDJ/DMI/MACD/RSI/布林带/ATR/均线等
- ✅ **南向资金监控** - 沪港通/深港通资金流向
- ✅ **AH股溢价分析** - 180+AH股溢价率监控
- ✅ **市场广度分析** - 涨跌家数统计和状态判断
- ✅ **综合评分系统** - 多维度评分和投资建议

#### 💰 估值分析系统
- ✅ **估值指标计算** - PE/PB历史分位数
- ✅ **历史估值对比** - 当前估值在历史中的位置
- ✅ **估值匹配分析** - 基于估值水平的历史点位查找
- ✅ **多维度估值** - 支持主要指数的估值分析

#### ⚠️ 均线偏离度监控系统
- ✅ **11个指数监控** - 9个A股指数 + 2个港股指数
- ✅ **三级预警机制** - 20%/30%/40%偏离阈值
- ✅ **历史回测分析** - 偏离后5/10/20/60日收益率统计
- ✅ **邮件自动通知** - HTML格式彩色预警邮件
- ✅ **失败自动重试** - 最多3次重试确保数据获取
- ✅ **定时任务支持** - 本地cron或云端GitHub Actions
- ✅ **GitHub Actions集成** - 无需服务器的自动化监控

## 📈 项目结构

```
stock-analysis/
├── stock/                                  # A股市场火热程度分析
│   ├── stock.py                           # 🎯 主分析器
│   ├── enhanced_data_sources.py           # 多数据源管理器
│   ├── akshare_optimized.py               # akshare优化数据源
│   ├── tencent_source.py                  # 腾讯财经数据源
│   └── ...                                # 其他数据源
│
├── position_analysis/                      # 历史点位对比分析系统
│   ├── historical_position_analyzer.py    # 核心分析器
│   ├── market_state_detector.py           # 市场状态检测器 (Phase 3.1)
│   ├── enhanced_data_provider.py          # 九维度数据提供器 (Phase 2)
│   ├── valuation_analyzer.py              # 估值分析器
│   ├── hk_market_analyzer.py              # 港股市场分析器
│   ├── ma_deviation_monitor.py            # 均线偏离度监控器
│   ├── email_notifier.py                  # 邮件通知模块
│   ├── report_generator.py                # 报告生成器
│   ├── chart_generator.py                 # 图表生成器
│   └── README.md                          # 详细文档
│
├── data_sources/                           # 数据源模块
│   └── hkstock_source.py                  # 港股数据源
│
├── scripts/                                # 运行脚本
│   ├── position_analysis/
│   │   └── run_ma_deviation_monitor.py    # 均线偏离度监控脚本
│   └── hk_stock_analysis/
│       └── run_hk_analysis.py             # 港股分析脚本
│
├── .github/workflows/                      # GitHub Actions 配置
│   └── ma_deviation_monitor.yml           # 自动监控工作流
│
├── docs/                                   # 文档目录
│   ├── 均线偏离度监控系统.md               # 监控系统说明
│   ├── GitHub_Actions配置指南.md          # Actions 配置指南
│   ├── 定时任务配置指南.md                # 本地定时任务配置
│   ├── HK_STOCK_README.md                 # 港股模块文档
│   ├── VALUATION_ANALYSIS_GUIDE.md        # 估值分析指南
│   └── ...                                # 其他设计文档
│
├── run_position_analysis.py               # Phase 1: 基础历史点位分析
├── run_enhanced_analysis.py               # Phase 1.5: 增强因子分析
├── run_phase2_analysis.py                 # Phase 2: 九维度分析
├── run_phase3_state_detection.py          # Phase 3.1: 市场状态诊断
│
├── compound_interest/                      # 复合收益计算
├── requirements.txt                       # 项目依赖
├── email_config.yaml.template             # 邮件配置模板
└── README.md                              # 项目文档
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

#### 方式1: A股市场火热程度分析
```bash
# 快速分析（自动选择最佳数据源）
python quick_start.py

# 交互式选择数据源
python quick_start.py --interactive

# 命令行模式
python stock/stock.py --interactive
```

#### 方式2: 历史点位对比分析
```bash
# Phase 3.1: 市场状态智能诊断（最新推荐⭐）
python run_phase3_state_detection.py
python run_phase3_state_detection.py --index sh000001  # 指定指数
python run_phase3_state_detection.py --detail          # 详细12维度分析

# Phase 2: 九维度市场分析
python run_phase2_analysis.py
python run_phase2_analysis.py --index sz399006

# Phase 1.5: 增强因子分析（支持ETF/个股）
python run_enhanced_analysis.py --code 512690   # 酒ETF
python run_enhanced_analysis.py --code 002050   # 三花智控
python run_enhanced_analysis.py --list          # 查看支持的标的

# Phase 1: 基础历史点位分析
python run_position_analysis.py
```

#### 方式3: 港股市场分析
```bash
# 港股综合分析
python scripts/hk_stock_analysis/run_hk_analysis.py

# 或通过主程序选择
python main.py  # 选择 "2. 港股市场分析"
```

#### 方式4: 均线偏离度监控
```bash
# 控制台输出监控结果
python scripts/position_analysis/run_ma_deviation_monitor.py

# 发送邮件通知（需先配置 email_config.yaml）
python scripts/position_analysis/run_ma_deviation_monitor.py --email

# 静默模式（仅发邮件，不输出到控制台）
python scripts/position_analysis/run_ma_deviation_monitor.py --email --quiet

# 自定义重试次数
python scripts/position_analysis/run_ma_deviation_monitor.py --email --retry 5
```

#### 方式5: 完整主程序
```bash
# 运行主程序（包含所有功能菜单）
python main.py
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
| 数据源 | 响应时间 | 数据量 | 稳定性 | 费用 | 推荐场景 |
|--------|----------|--------|--------|------|----------|
| **efinance** | ~1-2s | 实时+历史 | ⭐⭐⭐⭐ | 免费 | 实时行情监控 |
| **baostock** | ~5-10s | 全市场 | ⭐⭐⭐⭐ | 免费 | 历史数据回测 |
| **腾讯财经** | 0.2s | 3大指数 | ⭐⭐⭐⭐⭐ | 免费 | 快速指数查询 |
| **akshare** | ~30-60s | 5000+股票 | ⭐⭐⭐⭐⭐ | 免费 | 全市场分析 |
| **Ashare** | 0.7s | 价格数据 | ⭐⭐⭐⭐ | 免费 | 轻量级场景 |
| **tushare** | 需积分 | 专业数据 | ⭐⭐⭐⭐⭐ | 积分制 | 专业量化 |

### 量化指标体系
- **成交量比率** (25%) - 市场活跃度
- **价格动量** (20%) - 指数涨跌趋势
- **市场广度** (20%) - 个股表现分布
- **波动率** (15%) - 市场风险水平
- **情绪指标** (20%) - 涨跌停情绪

## 📋 数据源配置

### 免费数据源 (无需配置)
- ✅ **baostock (证券宝)** - 完全免费，无需注册，历史数据完整
- ✅ **efinance (东方财富)** - 完全免费，实时行情，响应快速
- ✅ **akshare** - 完全免费，5434只股票数据
- ✅ **腾讯财经** - 实时指数，响应极快
- ✅ **新浪财经** - 传统稳定接口

### 可选专业数据源
```python
# tushare 配置 (可选)
import tushare as ts
ts.set_token('your_token_here')  # 注册获取: https://tushare.pro
```

## 📧 均线偏离度监控邮件配置

### 快速配置

1. **复制邮箱配置模板**:
```bash
cp email_config.yaml.template email_config.yaml
```

2. **填写邮箱信息**:
```yaml
smtp:
  server: smtp.qq.com      # SMTP服务器
  port: 465                # SMTP端口

sender:
  email: your_email@qq.com        # 发件邮箱
  password: your_app_password     # 邮箱授权码（不是登录密码！）
  name: 股票监控系统

recipients:
  - your_email@qq.com             # 收件人
```

**获取邮箱授权码**:
- **QQ邮箱**: 邮箱设置 → 账户 → POP3/IMAP/SMTP → 生成授权码
- **163邮箱**: 邮箱设置 → POP3/SMTP/IMAP → 开启服务并获取授权码

3. **测试邮件发送**:
```bash
python scripts/position_analysis/run_ma_deviation_monitor.py --email
```

### 定时任务配置

#### 方案一: GitHub Actions（推荐 - 无需服务器）

详见: [docs/GitHub_Actions配置指南.md](docs/GitHub_Actions配置指南.md)

- ✅ 完全免费（private仓库也支持）
- ✅ 每周一到周五 15:10 自动执行
- ✅ 自动发送邮件通知
- ✅ 无需本地电脑开机

#### 方案二: 本地定时任务（cron/launchd）

详见: [docs/定时任务配置指南.md](docs/定时任务配置指南.md)

**macOS/Linux 快速配置**:
```bash
# 1. 创建监控脚本
mkdir -p ~/bin
cat > ~/bin/stock_monitor.sh << 'EOF'
#!/bin/bash
cd /path/to/stock-analysis
python3 scripts/position_analysis/run_ma_deviation_monitor.py --email --quiet
EOF
chmod +x ~/bin/stock_monitor.sh

# 2. 配置 cron (每天15:10执行)
crontab -e
# 添加: 10 15 * * 1-5 /Users/your_name/bin/stock_monitor.sh
```

## 💡 使用示例

### 交互式选择数据源
```bash
# 运行时交互式选择数据源
python stock/stock.py --interactive
```

运行后会显示数据源选择菜单：
```
请选择数据源：
======================================================================

1. efinance (东方财富)
   实时数据，响应快速 (~1-2s)
   推荐场景: 实时监控

2. baostock (证券宝)
   历史数据完整 (~5-10s)
   推荐场景: 历史回测

3. akshare
   全市场数据 (~30-60s)
   推荐场景: 全市场分析

4. 腾讯财经
   快速指数查询 (~0.2s)
   推荐场景: 快速查看

5. 多源自动切换
   智能选择最佳数据源
   推荐场景: 日常使用
```

### 基础分析
```python
from stock.stock import AStockHeatAnalyzer

# 使用默认多数据源
analyzer = AStockHeatAnalyzer()
result = analyzer.analyze_market_heat()

# 指定数据源 - efinance (快速实时)
analyzer = AStockHeatAnalyzer(data_source='efinance')
result = analyzer.analyze_market_heat()

# 指定数据源 - baostock (历史完整)
analyzer = AStockHeatAnalyzer(data_source='baostock')
result = analyzer.analyze_market_heat()

print(f"火热程度: {result['heat_score']:.3f}")
print(f"风险等级: {result['risk_level']}")
```

### 场景化使用
```python
from stock.data_source_selector import DataSourceSelector

selector = DataSourceSelector()

# 实时监控场景
source = selector.get_quick_recommendation('realtime')  # 返回 'efinance'
analyzer = AStockHeatAnalyzer(data_source=source)

# 历史回测场景
source = selector.get_quick_recommendation('backtest')  # 返回 'baostock'
analyzer = AStockHeatAnalyzer(data_source=source)

# 全市场分析场景
source = selector.get_quick_recommendation('analysis')  # 返回 'akshare'
analyzer = AStockHeatAnalyzer(data_source=source)
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
# 测试 baostock
from stock.baostock_source import BaostockDataSource
baostock = BaostockDataSource()
data = baostock.get_market_data()

# 测试 efinance
from stock.efinance_source import EfinanceDataSource
efinance = EfinanceDataSource()
data = efinance.get_realtime_data()

# 测试腾讯财经
from stock.tencent_source import TencentDataSource
tencent = TencentDataSource()
data = tencent.get_market_summary()
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

## 📊 版本历史

### v3.1 (2025-10-11) - 监控与自动化
- 🆕 **均线偏离度监控系统** - 11个指数三级预警机制
- 🆕 **邮件自动通知** - HTML格式彩色预警邮件
- 🆕 **历史回测数据** - 偏离后5/10/20/60日收益率统计
- 🆕 **GitHub Actions集成** - 云端自动化监控
- 🆕 **定时任务支持** - 本地cron和launchd配置
- 🆕 **失败自动重试** - 确保数据获取成功率

### v3.0 (2025-10-10) - 市场状态智能诊断
- 🆕 **Phase 3.1市场状态检测** - 12维度智能识别牛市/熊市/震荡市
- 🆕 **智能评分模型** - 综合12个维度加权评分
- 🆕 **关键信号提取** - 自动识别看多/看空信号和风险预警
- 🆕 **动态仓位建议** - 根据市场状态自适应调整
- 🆕 **新增数据维度** - 均线、融资融券、主力资金、龙虎榜

### v2.5 (2025-10-09) - 九维度指标体系
- 🆕 **Phase 2九维度分析** - 达到专业投资者水平
- 🆕 **估值指标** - PE/PB历史分位数
- 🆕 **北向资金流向** - 追踪外资(聪明钱)动向
- 🆕 **市场宽度指标** - 判断普涨/普跌/结构性行情
- 🆕 **技术指标** - MACD/RSI趋势确认
- 🆕 **波动率指标** - 风险水平量化
- 🆕 **综合评分系统** - 多维度加权评分

### v2.0 (2025-10-06) - 港股分析与增强
- 🆕 **港股市场分析模块** - 恒生指数/恒生科技/恒生国企
- 🆕 **技术指标分析** - KDJ/DMI/MACD/RSI/布林带/ATR
- 🆕 **南向资金监控** - 沪港通/深港通资金流向
- 🆕 **AH股溢价分析** - 180+AH股溢价率监控
- 🆕 **历史点位对比 Phase 1.5** - 成交量维度、ETF/个股支持
- 🆕 **估值分析系统** - PE/PB历史估值对比

### v1.5 (2025-10-02) - 历史点位对比
- 🆕 **历史点位对比分析系统** (Phase 1)
- 🆕 **概率统计模型** - 5/10/20/60日涨跌概率
- 🆕 **置信度评估** - 样本量/一致性/时间分散度
- 🆕 **仓位管理建议** - Kelly公式优化
- 🆕 **HTML可视化报告** - 交互式图表

### v1.0 (2025-09-29) - 基础版本
- ✅ **A股市场火热程度分析**
- ✅ **多数据源智能架构** - efinance/baostock/akshare等
- ✅ **网络重试机制** + **智能缓存**
- ✅ 支持 **5434只股票** 全市场覆盖

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

## 📚 相关文档

### 核心功能文档
- [历史点位对比分析系统 README](position_analysis/README.md) - Phase 1/2/3完整文档
- [港股分析模块使用指南](docs/HK_STOCK_README.md) - 港股数据源和分析器说明
- [估值分析指南](docs/VALUATION_ANALYSIS_GUIDE.md) - 估值分析使用方法
- [均线偏离度监控系统](docs/均线偏离度监控系统.md) - 监控系统完整说明

### 配置指南
- [GitHub Actions配置指南](docs/GitHub_Actions配置指南.md) - 云端自动化监控配置
- [定时任务配置指南](docs/定时任务配置指南.md) - 本地定时任务配置
- [市场热度量化指标设计](docs/市场热度量化指标设计.md) - 火热程度算法说明

### 技术文档
- [港股实现总结](docs/HK_STOCK_IMPLEMENTATION_SUMMARY.md) - 港股模块技术实现
- [历史点位对比功能设计](docs/历史点位对比分析功能设计.md) - 设计思路和算法
- [Phase 2 Summary](position_analysis/PHASE2_SUMMARY.md) - 九维度指标体系
- [Phase 3 Design](position_analysis/PHASE3_DESIGN.md) - 市场状态诊断设计

---

**🎯 让数据驱动投资决策！** 🚀