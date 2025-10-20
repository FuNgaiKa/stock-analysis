# 🌟 金融工具平台 - 全市场量化分析系统

一个功能完善的**现代化Web平台** + **Python量化工具集**，支持**美股、港股、A股**三大市场，提供历史点位分析、VIX恐慌指数、行业轮动、策略回测、市场火热度分析等多维度量化分析功能。

## 🎨 **Web平台** (最新 v3.2)

现代化的Vue 3前端 + FastAPI后端，提供直观的可视化界面，支持三大市场实时分析。

### 🌐 快速访问
- **前端地址**: http://localhost:3000
- **API文档**: http://localhost:8000/docs

### 🛠️ Web平台技术栈

#### 前端技术栈
- **Vue 3.3.4** - 渐进式JavaScript框架，Composition API
- **TypeScript 5.2.2** - 类型安全的JavaScript超集
- **Element Plus 2.3.12** - 基于Vue 3的组件库
- **ECharts 5.4.3** - 数据可视化图表库
- **Vue Router 4.2.4** - 官方路由管理器
- **Pinia 2.1.6** - Vue 3状态管理
- **Vue I18n 9.4.1** - 国际化支持
- **Axios 1.5.0** - HTTP客户端
- **Vite 4.4.9** - 快速构建工具

#### 后端技术栈
- **FastAPI** - 现代高性能Python Web框架
- **Uvicorn** - ASGI服务器
- **Pydantic** - 数据验证和设置管理
- **yfinance** - 美股/港股/A股数据源（Yahoo Finance）
- **pandas & numpy** - 数据分析和计算
- **TA-Lib** - 技术指标计算

#### 数据源技术
- **yfinance** - 全球市场实时/历史数据（美股/港股/A股）
- **efinance** - 东方财富数据源（A股实时数据）
- **baostock** - 证券宝数据源（A股历史数据）
- **akshare** - 开源金融数据接口（A股全市场）
- **RESTful API** - 统一的API接口设计

### ✨ 核心功能

#### 🇺🇸 美股市场分析
- **指数分析** - 标普500/纳斯达克/道琼斯等主要指数历史点位对比
- **VIX恐慌指数** - 实时监控市场恐慌情绪，VIX分位数分析
- **行业轮动** - 11个行业ETF(XLK/XLF/XLE等)相对强度雷达图
- **历史回测** - 四指标共振策略回测，支持SPY/QQQ等ETF

#### 🇭🇰 港股市场分析
- **恒生指数** (HSI) - 香港主板蓝筹指数
- **国企指数** (HSCEI) - H股国企成份股指数
- **恒生科技指数** (HSTECH) - 科技股指数
- **市场热度分析** - 火热程度评分、风险等级、仓位建议
- **关键指标监控** - 5大核心指标实时追踪
- **智能操作建议** - 基于多维度分析的投资建议

#### 🇨🇳 A股市场分析
- **上证指数** (SSE) / **深证成指** (SZSE) / **创业板指** (CYBZ)
- **沪深300** (HS300) / **中证500** (ZZ500)
- 全面支持A股主要指数分析

#### 💰 复合收益计算器
- **复利计算** - 支持年化收益率、投资年限配置
- **定投功能** - 按月定投模拟分析
- **可视化展示** - 收益构成饼图、增长趋势折线图
- **年度明细** - 逐年收益和累计收益统计
- **快速预设** - 保守型/平衡型/进取型/高风险四种模式

### 📊 主要页面

| 页面 | 功能 | 访问路径 |
|------|------|----------|
| 市场概览 | 美股/港股/A股三大市场实时数据 | /market-overview |
| 指数分析 | 历史点位相似度分析，涨跌概率预测 | /index-analysis |
| VIX恐慌指数 | VIX历史走势、分位数、相关性分析 | /vix-analysis |
| 行业轮动 | 11个行业ETF雷达图、排名、轮动模式 | /sector-rotation |
| 历史回测 | 策略回测、权益曲线、性能指标 | /backtest |
| 历史点位对比 | 多指数历史点位对比分析，Phase 2/3深度分析 | /position-analysis |
| 港股市场分析 | 港股三大指数、市场热度、操作建议 | /hk-stock-analysis |
| 复合收益计算器 | 复利计算、定投分析、年度明细 | /compound-calculator |
| 使用文档 | 完整的功能说明和FAQ | /docs |

### 🚀 启动Web平台

```bash
# 1. 安装依赖
pip install fastapi uvicorn pydantic yfinance -q
cd frontend && npm install

# 2. 启动后端API (终端1)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 3. 启动前端服务 (终端2)
cd frontend && npm run dev

# 4. 浏览器访问
open http://localhost:3000
```

### 🎯 Web平台特色

- ✅ **现代化UI设计** - 参考TradingView/PackyCode的专业设计风格
- ✅ **蓝紫渐变主题** - 优雅的配色方案，支持暗黑模式
- ✅ **响应式布局** - 完美适配桌面和移动端
- ✅ **ECharts可视化** - 雷达图、柱状图、折线图等丰富图表
- ✅ **实时数据更新** - 基于yfinance的实时行情数据
- ✅ **多市场支持** - 美股/港股/A股一站式分析
- ✅ **RESTful API** - 完整的API文档和Swagger UI

---

## 🐍 **Python量化工具集**

强大的命令行工具集，适合量化研究和自动化监控。

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
├── 🌐 Web平台 (v3.2)
│   ├── api/                               # FastAPI后端
│   │   └── main.py                        # API主程序
│   │       ├── 美股API - /api/indices, /api/vix, /api/sectors
│   │       ├── 港股API - /api/hk/indices, /api/hk/current-positions
│   │       ├── A股API - /api/cn/indices, /api/cn/current-positions
│   │       └── 回测API - /api/backtest/run
│   │
│   └── frontend/                          # Vue 3前端(保持独立)
│       ├── src/views/                     # 页面组件
│       ├── src/components/                # UI组件
│       └── package.json                   # 前端依赖
│
├── 🐍 Python量化核心库
│   ├── src/                               # 核心代码库(新架构) 📦
│   │   ├── analyzers/                     # 分析器模块
│   │   │   ├── comprehensive/             # 综合分析
│   │   │   ├── position/                  # 持仓分析
│   │   │   ├── sector/                    # 板块分析
│   │   │   └── macro/                     # 宏观分析
│   │   ├── strategies/                    # 策略模块
│   │   └── utils/                         # 工具函数
│   │
│   ├── position_analysis/                 # 历史点位对比分析系统
│   │   ├── market_analyzers/              # 市场分析器
│   │   │   ├── us_market_analyzer.py      # 美股 ⭐
│   │   │   ├── hk_market_analyzer.py      # 港股 ⭐
│   │   │   └── cn_market_analyzer.py      # A股 ⭐
│   │   ├── analyzers/                     # 专业分析器(20+个)
│   │   │   ├── technical_analysis/        # 技术分析
│   │   │   │   └── divergence_analyzer.py # 背离分析 🆕
│   │   │   ├── market_indicators/         # 市场指标
│   │   │   │   ├── vix_analyzer.py        # VIX恐慌指数
│   │   │   │   └── cn_volatility_index.py # A股波动率
│   │   │   ├── market_specific/           # 市场特性
│   │   │   │   ├── ah_premium_analyzer.py # AH溢价
│   │   │   │   └── hk_connect_analyzer.py # 港股通
│   │   │   └── valuation/                 # 估值分析
│   │   ├── core/                          # 核心引擎
│   │   └── README.md                      # 详细文档
│   │
│   ├── data_sources/                      # 数据源模块
│   │   ├── us_stock_source.py             # 美股(yfinance)
│   │   ├── hkstock_source.py              # 港股
│   │   └── akshare_optimized.py           # A股(akshare)
│   │
│   └── trading_strategies/                # 交易策略
│       ├── backtesting/                   # 回测引擎
│       └── signal_generators/             # 信号生成器
│
├── 📜 运行脚本
│   └── scripts/                           # 可执行脚本
│       ├── unified_analysis/              # 🆕⭐ 统一分析工具
│       │   ├── run_unified_analysis.py    # 25个资产统一分析
│       │   ├── unified_email_notifier.py  # 邮件通知
│       │   ├── unified_config.py          # 资产配置
│       │   └── README.md                  # 每日更新工作流程
│       │
│       ├── comprehensive_asset_analysis/  # 综合资产分析
│       ├── sector_analysis/               # 板块分析
│       ├── tech_indices_analysis/         # 科技指数分析
│       ├── fed_rate_cut_analysis/         # 美联储降息周期
│       ├── position_analysis/             # 持仓分析脚本
│       ├── hk_stock_analysis/             # 港股分析
│       ├── us_stock_analysis/             # 美股分析
│       └── run_daily_report.py            # 每日报告生成
│
├── 📊 报告和文档
│   ├── reports/                           # 分析报告 📂
│   │   ├── README.md                      # 报告目录说明 🆕
│   │   ├── daily/                         # 每日报告 🆕
│   │   │   └── 2025-10/                   # 按月分类
│   │   │       ├── unified_analysis_*.md  # 统一分析报告
│   │   │       └── 持仓调整建议_*.md       # 持仓建议
│   │   ├── analysis/                      # 专项分析 🆕
│   │   │   ├── bull_markets/              # 牛市分析
│   │   │   └── 其他专项分析
│   │   └── archive/                       # 历史归档 🆕
│   │
│   └── docs/                              # 项目文档
│       ├── 均线偏离度监控系统.md
│       ├── GitHub_Actions配置指南.md
│       ├── HK_STOCK_README.md
│       └── ...
│
├── 🧪 测试和示例
│   ├── tests/                             # 测试文件 📦
│   │   ├── test_*.py                      # 单元测试
│   │   └── scripts/                       # 脚本测试 🆕
│   │       ├── test_data_sources.py
│   │       └── test_phase2_comparison.py
│   │
│   └── examples/                          # 示例代码 🆕
│       └── demo_us_stock_phase2.py
│
├── 🗂️ 配置和其他
│   ├── config/                            # 配置文件
│   │   └── email_config.yaml              # 邮件配置
│   ├── _deprecated/                       # 废弃代码(保留)
│   ├── .github/workflows/                 # CI/CD
│   ├── main.py                            # 主程序入口
│   ├── requirements.txt                   # Python依赖
│   └── README.md                          # 本文档
```

**🆕 最新更新(2025-10-20)**:
- ✅ **reports目录重构** - daily/analysis/archive三级分类
- ✅ **测试文件整理** - 统一到tests目录
- ✅ **示例代码分离** - examples目录独立管理
- ✅ **unified_analysis** - 25个资产一键分析+每日自动更新

**📂 目录说明**:
- `src/` - 新架构核心库,逐步整合
- `position_analysis/` - 成熟的分析系统
- `scripts/` - 可执行脚本,按功能分类
- `reports/` - 分析报告,按时间和类型归档
- `tests/` - 所有测试文件集中管理

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

#### 方式5: 综合资产分析 🆕⭐
```bash
# 分析7大资产(四大科技指数+沪深300+黄金+比特币) - 11维度分析
python scripts/comprehensive_asset_analysis/run_asset_analysis.py

# 发送邮件报告
python scripts/comprehensive_asset_analysis/run_asset_analysis.py --email

# 保存为Markdown格式
python scripts/comprehensive_asset_analysis/run_asset_analysis.py --format markdown --save reports/assets.md
```

**分析对象:**
- 🇨🇳 创业板指/科创50/沪深300
- 🇭🇰 恒生科技
- 🇺🇸 纳斯达克
- 💰 黄金
- ₿ 比特币

**分析维度(11维度):**
- 历史点位、技术面、资金面、估值、市场情绪、风险评估、综合判断
- 成交量分析、支撑压力位、市场宽度、恐慌指数(VIX/CNVI/HKVI)

**详见**: [scripts/comprehensive_asset_analysis/README.md](scripts/comprehensive_asset_analysis/README.md)

#### 方式6: 四大科技指数分析 🆕⭐
```bash
# 专注分析四大科技指数(创业板指/科创50/恒生科技/纳斯达克) - 7维度分析
python scripts/tech_indices_analysis/run_tech_comprehensive_analysis.py

# 发送邮件报告
python scripts/tech_indices_analysis/run_tech_comprehensive_analysis.py --email
```

**分析维度(7维度):**
- 历史点位、技术面、资金面、估值、市场情绪、风险评估、综合判断

**详见**: [scripts/tech_indices_analysis/README.md](scripts/tech_indices_analysis/README.md)

#### 方式7: 每日市场推送
```bash
# 生成每日市场报告(控制台输出)
python scripts/run_daily_report.py

# 生成并发送邮件
python scripts/run_daily_report.py --email

# 保存报告到文件
python scripts/run_daily_report.py --save reports/daily_report.txt

# 详细日志模式
python scripts/run_daily_report.py --email --verbose
```

**邮件报告包含:**
- 三大市场概览(美股/港股/A股)
- A股核心指标(北向资金/融资情绪/市场宽度)
- 综合评分(0-10分)
- 交易建议(方向/仓位/策略)
- 看多看空信号

**GitHub Actions自动推送:**
- 每个工作日 15:10 自动执行
- 详见: [每日市场推送配置指南](docs/DAILY_REPORT_SETUP.md)

#### 方式8: 完整主程序
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

### v4.3 (2025-10-14) - 🔥 背离分析器 **[最新]**
- 🆕 **背离分析器** - 支持A股/H股/美股三大市场
  - 量价背离检测(顶背离/底背离)
  - MACD背驰检测(柱状图/DIF线)
  - RSI背离检测
  - 自动峰谷识别算法
  - 背离强度评分系统(0-100)
  - 置信度分级(高/中/低)
  - 综合分析+操作建议

### v4.0 (2025-10-12) - 🚀 量化分析系统全面升级
#### 核心新功能
- 🆕 **DMI/ADX趋势强度指标** - 识别强趋势(>25)和弱趋势(<20)
- 🆕 **KDJ超买超卖指标** - 精准的短期交易信号
- 🆕 **专业K线图组件** - ECharts candlestick + 技术指标子图(KDJ/DMI/MACD)
- 🆕 **融资融券深度分析** - A股特色杠杆情绪指标
- 🆕 **A股特色指标** - 量比(成交量/5日均量)、换手率、MACD能量
- 🆕 **港股通持股分析** - 北向/南向资金流向监控
- 🆕 **财务数据分析器** - ROE/营收增长率/三维评分系统
- 🆕 **市场宽度分析器** - 新高新低指数(20/60/120日)
- 🆕 **📧 每日市场推送系统** - 自动生成HTML邮件+GitHub Actions定时任务

#### 技术指标升级
- **趋势类**: MA均线 → +DMI/ADX趋势强度
- **震荡类**: RSI/布林带 → +KDJ超买超卖
- **A股特色**: 基础量价 → +量比/换手率/MACD能量
- **资金流向**: 基础分析 → +融资融券/港股通深度分析
- **市场宽度**: 涨跌家数 → +新高新低指数/内部强度

#### 每日市场推送系统 🎯
- **自动报告生成** - 集成三大市场+专项分析器
- **智能评分系统** - 0-10分综合评估
- **HTML邮件模板** - 响应式设计,美观易读
- **GitHub Actions** - 工作日15:10自动推送
- **交易建议生成** - 仓位/策略/信号智能推荐

#### 性能提升
- 新增约8000行代码
- 12个新功能模块
- 技术指标从8个增至12个
- 系统能力提升300%

### v3.2 (2025-10-11) - 前端功能完善
- 🆕 **复合收益计算器** - 复利计算、定投分析、可视化展示
- 🆕 **港股市场分析页面** - 港股三大指数、市场热度分析、智能建议
- 🆕 **历史点位对比页面** - 多指数分析、Phase 2/3深度分析集成
- ✨ **前端功能对齐** - 与main.py命令行工具功能完全一致
- 📱 **响应式优化** - 更好的移动端适配体验

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
- [背离分析器使用文档](position_analysis/analyzers/DIVERGENCE_ANALYZER_README.md) - 量价背离/MACD背驰/RSI背离完整指南 🆕
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