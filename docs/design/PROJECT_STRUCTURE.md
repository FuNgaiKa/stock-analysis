# 📁 项目结构说明

> **更新时间**: 2025-10-12
> **版本**: v3.2

---

## 🌳 目录树

```
stock-analysis/
├── 📱 前端 (Vue 3 + TypeScript)
│   └── frontend/                       # Web平台前端
│       ├── src/
│       │   ├── views/                  # 页面组件
│       │   ├── components/             # 可复用组件
│       │   ├── assets/                 # 静态资源
│       │   └── router/                 # 路由配置
│       └── package.json
│
├── 🔧 后端 (FastAPI)
│   └── api/
│       └── main.py                     # API主程序
│
├── 🐍 核心模块
│   ├── stock/                          # A股市场热度分析
│   │   ├── stock.py                    # 主分析器
│   │   ├── enhanced_data_sources.py    # 多数据源管理
│   │   └── ...                         # 其他数据源
│   │
│   ├── position_analysis/              # 历史点位对比分析
│   │   ├── us_market_analyzer.py       # 美股分析器
│   │   ├── hk_market_analyzer.py       # 港股分析器
│   │   ├── cn_market_analyzer.py       # A股分析器
│   │   ├── historical_position_analyzer.py  # 核心分析器
│   │   ├── market_state_detector.py    # 市场状态检测
│   │   ├── enhanced_data_provider.py   # 九维度数据
│   │   ├── ma_deviation_monitor.py     # 均线偏离度监控
│   │   ├── email_notifier.py           # 邮件通知
│   │   ├── report_generator.py         # 报告生成
│   │   ├── chart_generator.py          # 图表生成
│   │   └── analyzers/                  # 专业分析器
│   │       ├── alpha101_factors.py     # Alpha101因子
│   │       ├── vix_analyzer.py         # VIX分析
│   │       ├── sector_analyzer.py      # 行业轮动
│   │       ├── volume_analyzer.py      # 成交量分析
│   │       ├── slope_analyzer.py       # 斜率分析
│   │       ├── microstructure_analyzer.py  # 微观结构
│   │       ├── correlation_analyzer.py # 相关性分析
│   │       ├── support_resistance.py   # 支撑压力位
│   │       ├── sentiment_index.py      # 情绪指标
│   │       └── historical_matcher.py   # 历史匹配
│   │
│   ├── trading_strategies/             # 交易策略模块
│   │   ├── backtesting/                # 回测引擎
│   │   │   ├── backtest_engine.py      # 回测引擎
│   │   │   └── performance_metrics.py  # 性能指标
│   │   └── signal_generators/          # 信号生成器
│   │       ├── resonance_signals.py    # 四指标共振
│   │       ├── sr_breakout_strategy.py # 支撑压力位突破
│   │       └── technical_indicators.py # 技术指标
│   │
│   ├── data_sources/                   # 数据源模块
│   │   ├── us_stock_source.py          # 美股数据源
│   │   ├── hkstock_source.py           # 港股数据源
│   │   ├── akshare_optimized.py        # A股数据源
│   │   └── tushare_source.py           # Tushare数据源
│   │
│   └── compound_interest/              # 复合收益计算
│       └── compound_calculator.py      # 计算器
│
├── 📜 脚本
│   └── scripts/
│       ├── cli.py                      # 命令行主程序 ⭐
│       ├── position_analysis/          # 点位分析脚本
│       │   ├── run_position_analysis.py
│       │   ├── run_enhanced_analysis.py
│       │   ├── run_phase2_analysis.py
│       │   ├── run_phase3_state_detection.py
│       │   └── run_ma_deviation_monitor.py
│       ├── hk_stock_analysis/          # 港股分析脚本
│       │   └── run_hk_analysis.py
│       ├── us_stock_analysis/          # 美股分析脚本
│       │   └── run_us_analysis.py
│       ├── trading_strategies/         # 策略脚本
│       │   ├── run_resonance_strategy.py
│       │   └── run_backtest.py
│       ├── market_indicators/          # 指标脚本
│       │   ├── run_vix_analysis.py
│       │   └── china_vix_equivalent.py
│       ├── market_heat/                # 市场热度脚本
│       │   └── quick_start.py
│       └── leverage_management/        # 仓位管理脚本
│           └── kelly_calculator.py
│
├── 📚 文档
│   └── docs/
│       ├── guides/                     # 使用指南 🆕
│       ├── design/                     # 设计文档 🆕
│       ├── api/                        # API文档 🆕
│       ├── analyzers/                  # 分析器文档 🆕
│       ├── phase_reports/              # 阶段报告 🆕
│       ├── frontend/                   # 前端文档 🆕
│       ├── examples/                   # 示例代码 🆕
│       ├── IMPLEMENTATION_ROADMAP.md   # 实施路线图 🆕
│       ├── PROJECT_STRUCTURE.md        # 本文档 🆕
│       ├── README.md                   # 主文档
│       ├── QUICK_START.md              # 快速开始
│       ├── DEPLOYMENT_GUIDE.md         # 部署指南
│       ├── VALUATION_ANALYSIS_GUIDE.md # 估值分析
│       ├── HK_STOCK_README.md          # 港股模块
│       ├── US_STOCK_README.md          # 美股模块
│       ├── WEB_PLATFORM_DESIGN.md      # Web平台设计
│       ├── GitHub_Actions配置指南.md    # Actions配置
│       ├── 定时任务配置指南.md          # 定时任务
│       ├── 均线偏离度监控系统.md        # 均线监控
│       ├── 市场热度量化指标设计.md      # 热度指标
│       ├── 量化策略增强方案_顶级机构指标.md  # 策略增强
│       └── ...                         # 其他文档
│
├── 🧪 测试
│   └── tests/
│       ├── test_integration.py         # 集成测试
│       ├── test_backtest.py            # 回测测试
│       ├── test_technical_indicators.py # 指标测试
│       └── ...                         # 其他测试
│
├── ⚙️ 配置文件
│   ├── main.py                         # 兼容性入口（调用scripts/cli.py）
│   ├── requirements.txt                # Python依赖
│   ├── email_config.yaml.template      # 邮件配置模板
│   └── .gitignore                      # Git忽略规则
│
├── 🤖 自动化
│   └── .github/workflows/
│       └── ma_deviation_monitor.yml    # 均线监控Action
│
└── 📊 输出 (git忽略)
    ├── reports/                        # 分析报告 (统一目录)
    └── logs/                           # 运行日志
```

---

## 📂 核心目录说明

### 1. `frontend/` - Web平台前端

**技术栈**: Vue 3 + TypeScript + Element Plus + ECharts

**核心页面**:
- `MarketOverview.vue` - 市场概览
- `IndexAnalysis.vue` - 指数分析
- `VixAnalysis.vue` - VIX恐慌指数
- `SectorRotation.vue` - 行业轮动
- `Backtest.vue` - 历史回测
- `PositionAnalysis.vue` - 历史点位对比
- `HKStockAnalysis.vue` - 港股分析
- `CompoundCalculator.vue` - 复合收益计算器

**访问地址**: http://localhost:3000

---

### 2. `api/` - FastAPI后端

**API文档**: http://localhost:8000/docs

**核心接口**:
- `/api/indices` - 指数数据
- `/api/vix` - VIX指数
- `/api/sectors` - 行业轮动
- `/api/backtest/run` - 回测执行
- `/api/hk/*` - 港股接口
- `/api/cn/*` - A股接口

---

### 3. `stock/` - A股市场热度分析

**核心文件**:
- `stock.py` - 市场热度分析器
- `enhanced_data_sources.py` - 多数据源管理器

**支持的数据源**:
- efinance (东方财富) - 实时数据
- baostock (证券宝) - 历史数据
- akshare - 全市场数据
- 腾讯财经 - 快速指数
- Ashare - 轻量级

**功能**:
- 综合火热程度评分
- 智能仓位建议
- 涨跌停监控
- 5434只股票全市场覆盖

---

### 4. `position_analysis/` - 历史点位对比分析

**三市场分析器**:
- `us_market_analyzer.py` - 美股（标普500/纳斯达克/道琼斯）
- `hk_market_analyzer.py` - 港股（恒生指数/恒生科技/恒生国企）
- `cn_market_analyzer.py` - A股（上证/深证/创业板/沪深300/中证500）

**核心功能**:
- Phase 1: 历史点位匹配
- Phase 1.5: 成交量维度
- Phase 2: 九维度指标体系
- Phase 3: 市场状态诊断

**专业分析器** (`analyzers/`):
- Alpha101因子
- VIX恐慌指数
- 行业轮动
- 微观结构
- 支撑压力位
- 情绪指标

---

### 5. `trading_strategies/` - 交易策略

**回测引擎** (`backtesting/`):
- 性能指标计算（夏普率、最大回撤、胜率）
- 权益曲线绘制
- 交易记录统计

**信号生成器** (`signal_generators/`):
- 四指标共振策略
- 支撑压力位突破策略
- 技术指标计算（MACD/RSI/KDJ/布林带/ATR）

---

### 6. `scripts/` - 运行脚本

**主程序**:
- `cli.py` - 命令行界面主程序（原main.py）

**分类脚本**:
- `position_analysis/` - 点位分析相关
- `hk_stock_analysis/` - 港股分析相关
- `us_stock_analysis/` - 美股分析相关
- `trading_strategies/` - 策略相关
- `market_indicators/` - 指标相关

**运行方式**:
```bash
# 方式1: 根目录兼容入口
python main.py

# 方式2: 直接运行CLI
python scripts/cli.py

# 方式3: 运行特定脚本
python scripts/position_analysis/run_phase3_state_detection.py
```

---

### 7. `docs/` - 文档中心

**新增分类**:
- `guides/` - 用户使用指南
- `design/` - 技术设计文档
- `api/` - API接口文档
- `analyzers/` - 分析器说明
- `phase_reports/` - 阶段开发报告
- `frontend/` - 前端实现文档
- `examples/` - 示例代码

**重点文档**:
- `IMPLEMENTATION_ROADMAP.md` - 完整实施路线图
- `PROJECT_STRUCTURE.md` - 本文档
- `README.md` - 项目主文档

---

### 8. `tests/` - 测试套件

**测试类型**:
- 单元测试 - 各模块功能测试
- 集成测试 - 数据源集成测试
- 回测测试 - 策略回测验证

---

## 🔄 项目结构变更记录

### v3.2 (2025-10-12) - 结构优化

**变更内容**:
1. ✅ `main.py` 移动到 `scripts/cli.py`，根目录保留兼容性入口
2. ✅ `examples/` 移动到 `docs/examples/`
3. ✅ 删除 `position_analysis/reports/`，统一使用根目录 `reports/`
4. ✅ `reports/` 和 `logs/` 加入 `.gitignore`
5. ✅ `docs/` 创建子目录分类结构
6. ✅ 创建 `IMPLEMENTATION_ROADMAP.md` 路线图
7. ✅ 创建 `PROJECT_STRUCTURE.md` 结构说明

**优势**:
- 📂 更清晰的目录层次
- 📝 更好的文档组织
- 🔧 更规范的脚本管理
- 🎯 更易于维护和扩展

---

## 🚀 快速导航

### 我想...

**运行Web平台**:
```bash
# 后端
uvicorn api.main:app --reload

# 前端
cd frontend && npm run dev
```

**运行命令行工具**:
```bash
python main.py
# 或
python scripts/cli.py
```

**运行特定分析**:
```bash
# 市场状态诊断
python scripts/position_analysis/run_phase3_state_detection.py

# 均线偏离度监控（带邮件）
python scripts/position_analysis/run_ma_deviation_monitor.py --email

# 四指标共振回测
python scripts/trading_strategies/run_backtest.py
```

**查看文档**:
- 功能介绍 → `README.md`
- 快速开始 → `docs/QUICK_START.md`
- 部署指南 → `docs/DEPLOYMENT_GUIDE.md`
- 实施路线图 → `docs/IMPLEMENTATION_ROADMAP.md`

---

## 📞 维护说明

### 添加新模块

1. **新增分析器** → `position_analysis/analyzers/`
2. **新增策略** → `trading_strategies/signal_generators/`
3. **新增脚本** → `scripts/相应分类目录/`
4. **新增文档** → `docs/相应分类目录/`

### 命名规范

**Python模块**:
- 分析器: `*_analyzer.py`
- 策略: `*_strategy.py`
- 脚本: `run_*.py`

**文档**:
- 指南: `*_GUIDE.md`
- 设计: `*_DESIGN.md`
- 报告: `*_SUMMARY.md` 或 `*_REPORT.md`

---

**Made with ❤️ by Claude Code**
最后更新: 2025-10-12
