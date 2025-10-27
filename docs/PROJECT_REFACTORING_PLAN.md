# 项目结构重构方案

> 目标：简化根目录结构，整合策略代码，提升项目可维护性

## 📊 当前问题

### 根目录文件夹过多（26个）
```
├── position_analysis/          # 历史点位分析
├── russ_trading_strategy/      # Russ策略系统
├── trading_strategies/         # 交易策略
├── scripts/                    # 脚本（内部又有很多子文件夹）
├── frontend/                   # 前端
├── api/                        # API
├── src/                        # 源代码
├── data_sources/               # 数据源
├── ... 还有18个其他文件夹
```

### 策略代码分散
- **历史点位分析** → `position_analysis/`
- **Russ持仓策略** → `russ_trading_strategy/`
- **交易策略** → `trading_strategies/`
- **杠杆策略** → `scripts/leverage_management/`
- **各种分析脚本** → `scripts/xxx_analysis/`

---

## 🎯 重构方案

### 方案概览

```
stock-analysis/
├── russ_trading/               # ⭐ Russ策略系统（独立在根目录，最显眼）
│   ├── daily_position_report_generator.py
│   ├── daily_position_report_generator_v2.py
│   ├── dynamic_position_manager.py
│   ├── risk_manager.py
│   ├── performance_tracker.py
│   ├── core/                   # 核心模块
│   ├── formatters/             # 格式化工具
│   ├── utils/                  # 工具函数
│   └── README.md
│
├── src/                        # 核心代码库（保持）
│   ├── analyzers/              # 各种分析器
│   ├── strategies/             # 策略模块
│   ├── data_sources/           # 数据源（整合原data_sources/）
│   └── utils/                  # 工具函数
│
├── strategies/                 # 🆕 其他策略中心
│   ├── leverage/               # 杠杆策略（原scripts/leverage_management/）
│   ├── position/               # 历史点位分析（原position_analysis/）
│   │   ├── core/
│   │   ├── analyzers/
│   │   └── reporting/
│   ├── trading/                # 交易策略（原trading_strategies/）
│   └── README.md               # 策略中心说明
│
├── scripts/                    # 🆕 统一CLI脚本
│   ├── analysis/               # 分析类脚本
│   │   ├── run_position_analysis.py
│   │   ├── run_sector_analysis.py
│   │   └── run_comprehensive_analysis.py
│   ├── leverage/               # 杠杆策略CLI
│   │   └── run_leverage_strategy.py
│   ├── russ_trading/           # Russ策略CLI
│   │   └── run_daily_report.py
│   ├── monitoring/             # 监控类脚本
│   │   └── run_ma_deviation_monitor.py
│   └── utils/                  # 工具脚本
│       └── create_test_cache.py
│
├── web/                        # 🆕 Web平台（整合前端+API）
│   ├── frontend/               # 前端代码（原frontend/）
│   │   ├── src/
│   │   ├── package.json
│   │   └── README.md
│   └── api/                    # API后端（原api/）
│       └── main.py
│
├── data/                       # 数据文件（保持）
├── config/                     # 配置文件（保持）
├── docs/                       # 文档（保持）
├── reports/                    # 报告（保持）
├── logs/                       # 日志（保持）
├── tests/                      # 测试（保持）
├── examples/                   # 示例（保持）
│
├── _deprecated/                # 废弃代码（保持）
├── .github/                    # CI/CD（保持）
├── main.py                     # 主程序入口（保持）
├── requirements.txt            # 依赖（保持）
└── README.md                   # 项目说明（保持）
```

---

## 📦 重构细节

### 1️⃣ 整合策略代码

#### Russ策略系统（独立保留在根目录）
```bash
# Russ策略系统保持在根目录，只需重命名
mv russ_trading_strategy russ_trading
```

#### 其他策略 → `strategies/`
```bash
# 创建策略中心
mkdir -p strategies/position
mkdir -p strategies/leverage
mkdir -p strategies/trading

# 移动文件
# 历史点位分析
mv position_analysis/* strategies/position/

# 杠杆策略
mv scripts/leverage_management strategies/leverage

# 交易策略
mv trading_strategies/* strategies/trading/
```

### 2️⃣ 整合CLI脚本 → `scripts/`

#### 重新组织scripts
```bash
# 创建新的scripts结构
mkdir -p scripts/analysis
mkdir -p scripts/leverage
mkdir -p scripts/russ_trading
mkdir -p scripts/monitoring
mkdir -p scripts/utils

# 移动分析类脚本
mv scripts/comprehensive_asset_analysis/* scripts/analysis/
mv scripts/sector_analysis/* scripts/analysis/
mv scripts/tech_indices_analysis/* scripts/analysis/
mv scripts/us_stock_analysis/* scripts/analysis/
mv scripts/hk_stock_analysis/* scripts/analysis/
mv scripts/position_analysis/* scripts/analysis/
mv scripts/fed_rate_cut_analysis/* scripts/analysis/

# 杠杆策略CLI
mv strategies/leverage/run_leverage_strategy.py scripts/leverage/

# Russ策略CLI
mv strategies/russ_trading/run_unified_analysis.py scripts/russ_trading/
cp scripts/run_daily_report.py scripts/russ_trading/

# 监控类脚本
mv scripts/market_heat/* scripts/monitoring/
mv scripts/market_indicators/* scripts/monitoring/

# 工具脚本
mv scripts/create_*.py scripts/utils/
mv scripts/get_realtime_sectors.py scripts/utils/
```

### 3️⃣ 整合Web平台 → `web/`

```bash
# 创建web目录
mkdir -p web

# 移动前端和API
mv frontend web/
mv api web/
```

### 4️⃣ 整合数据源 → `src/data_sources/`

```bash
# 移动数据源到src下
mv data_sources/* src/data_sources/
rmdir data_sources
```

---

## 🔧 重构后的结构对比

### 根目录文件夹：26个 → 12个

**重构前（26个）**:
```
position_analysis, russ_trading_strategy, trading_strategies,
scripts, frontend, api, src, data_sources, docs, reports,
logs, tests, examples, config, data, _deprecated, .github,
... 等26个
```

**重构后（12个）**:
```
russ_trading/  - ⭐ Russ策略系统（独立）
strategies/    - 其他策略（leverage/position/trading）
scripts/       - 所有CLI
web/           - 前端+API
src/           - 核心代码
data/          - 数据
config/        - 配置
docs/          - 文档
reports/       - 报告
logs/          - 日志
tests/         - 测试
examples/      - 示例
```

---

## ✅ 优势

### 1. **清晰的模块划分**
- `russ_trading/` - ⭐ Russ策略系统（最常用，独立显眼）
- `strategies/` - 其他策略实现（业务逻辑）
- `src/` - 核心库代码（不直接运行）
- `scripts/` - CLI入口（用户交互）
- `web/` - Web界面（可视化）

### 2. **Russ策略系统独立**
- 独立在根目录，最显眼的位置
- 不与其他策略混淆
- 快速访问和开发

### 3. **其他策略集中**
- 其他策略在 `strategies/` 下
- 按功能分类：leverage、position、trading

### 4. **简化根目录**
- 从26个文件夹减少到12个
- 更容易导航和理解项目结构

### 5. **统一CLI入口**
- 所有可执行脚本在 `scripts/` 下
- 按功能分类：analysis、leverage、monitoring等

---

## 📝 需要更新的内容

### 1. **Import路径调整**

#### Russ策略系统（路径不变，只是重命名）
```python
# 旧路径
from russ_trading_strategy.xxx import yyy

# 新路径
from russ_trading.xxx import yyy
```

#### 其他策略
```python
# 旧路径
from position_analysis.core.xxx import yyy

# 新路径
from strategies.position.core.xxx import yyy
```

#### 数据源
```python
# 旧路径
from data_sources.xxx import yyy

# 新路径
from src.data_sources.xxx import yyy
```

### 2. **文档更新**

- `README.md` - 更新项目结构图
- `docs/PROJECT_STRUCTURE.md` - 更新结构说明
- 各策略的README - 更新路径说明

### 3. **GitHub Actions**

更新 `.github/workflows/` 中的脚本路径：
```yaml
# 旧路径
python scripts/leverage_management/run_leverage_strategy.py

# 新路径
python scripts/leverage/run_leverage_strategy.py
```

---

## 🚀 执行步骤

### Phase 1: 创建新结构（不破坏旧代码）
1. 创建 `strategies/`、`web/` 新目录
2. 复制文件到新位置
3. 测试新路径是否可用

### Phase 2: 更新Import路径
1. 批量更新import语句
2. 运行测试，确保无错误

### Phase 3: 清理旧文件
1. 删除旧的文件夹
2. 更新文档
3. 提交Git

---

## ⚠️ 风险控制

1. **先复制，后删除** - 确保不丢失代码
2. **分阶段执行** - 每个Phase都测试通过后再进行下一个
3. **Git分支** - 在新分支上进行重构，测试通过后再合并
4. **保留备份** - 重构前完整备份项目

---

## 📅 执行计划

### 建议执行时间
- **Phase 1**: 30分钟（创建新结构+复制文件）
- **Phase 2**: 1小时（更新import路径+测试）
- **Phase 3**: 20分钟（清理+文档）

**总计**: 约2小时

---

**最后更新**: 2025-10-27
**方案版本**: v1.0
**维护者**: Russ Investment Research Team
