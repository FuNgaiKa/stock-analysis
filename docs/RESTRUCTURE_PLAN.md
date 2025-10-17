# 项目目录重构方案

## 当前问题

1. **重复目录**：
   - `position_analysis/` (根目录) 和 `scripts/position_analysis/` 重复
   - `trading_strategies/` (根目录) 和 `scripts/trading_strategies/` 重复

2. **scripts目录混乱**：
   - 包含14个子文件夹，缺少清晰分类
   - 混合了核心模块和独立脚本

3. **不明确的目录**：
   - `stock/` - 用途不清
   - `joinquant/` - 看起来是特定平台代码

## 建议的新结构

```
stock-analysis/
├── src/                                    # 核心源代码（可复用模块）
│   ├── analyzers/                          # 分析器模块
│   │   ├── position/                       # 持仓分析
│   │   │   ├── core/                       # 核心逻辑 (from position_analysis/core)
│   │   │   ├── analyzers/                  # 分析器 (from position_analysis/analyzers)
│   │   │   ├── monitoring/                 # 监控 (from position_analysis/monitoring)
│   │   │   └── reporting/                  # 报告 (from position_analysis/reporting)
│   │   ├── market/                         # 市场分析
│   │   │   ├── indices/                    # 指数分析 (from scripts/tech_indices_analysis)
│   │   │   ├── heat/                       # 市场热度 (from scripts/market_heat)
│   │   │   └── indicators/                 # 技术指标 (from scripts/market_indicators)
│   │   ├── sector/                         # 板块分析
│   │   │   └── analysis.py                 # (from scripts/sector_analysis)
│   │   ├── macro/                          # 宏观分析
│   │   │   ├── fed_cycles/                 # 美联储周期 (from scripts/fed_rate_cut_analysis)
│   │   │   └── leverage/                   # 杠杆管理 (from scripts/leverage_management)
│   │   ├── stock_specific/                 # 特定市场股票分析
│   │   │   ├── us/                         # 美股 (from scripts/us_stock_analysis)
│   │   │   └── hk/                         # 港股 (from scripts/hk_stock_analysis)
│   │   └── comprehensive/                  # 综合分析
│   │       ├── unified/                    # 统一分析 (from scripts/unified_analysis)
│   │       └── asset/                      # 资产分析 (from scripts/comprehensive_asset_analysis)
│   ├── strategies/                         # 交易策略模块
│   │   ├── signal_generators/              # 信号生成器 (from trading_strategies/signal_generators)
│   │   ├── backtesting/                    # 回测系统 (from trading_strategies/backtesting)
│   │   ├── examples/                       # 策略示例 (from trading_strategies/examples)
│   │   └── utils/                          # 工具函数 (from trading_strategies/utils)
│   ├── data_sources/                       # 数据源（保持不变）
│   └── utils/                              # 通用工具函数
├── scripts/                                # 独立可执行脚本
│   ├── run_analysis.py                     # 运行各种分析的入口
│   ├── run_backtest.py                     # 运行回测
│   └── tools/                              # 工具脚本
├── reports/                                # 分析报告输出
├── config/                                 # 配置文件
├── docs/                                   # 文档
│   ├── guides/                             # 使用指南
│   └── examples/                           # 示例
├── tests/                                  # 测试
├── frontend/                               # 前端（保持不变）
├── api/                                    # API（保持不变）
├── logs/                                   # 日志
└── [deprecated]/                           # 待废弃代码
    ├── stock/                              # 老的stock文件夹
    ├── joinquant/                          # joinquant代码
    └── compound_interest/                  # 复利计算

```

## 迁移映射表

| 当前路径 | 新路径 | 说明 |
|---------|--------|------|
| `position_analysis/` | `src/analyzers/position/` | 持仓分析核心模块 |
| `trading_strategies/` | `src/strategies/` | 交易策略核心模块 |
| `scripts/position_analysis/` | **删除** | 与根目录重复 |
| `scripts/trading_strategies/` | **删除** | 与根目录重复 |
| `scripts/fed_rate_cut_analysis/` | `src/analyzers/macro/fed_cycles/` | 美联储周期分析 |
| `scripts/market_heat/` | `src/analyzers/market/heat/` | 市场热度 |
| `scripts/market_indicators/` | `src/analyzers/market/indicators/` | 技术指标 |
| `scripts/tech_indices_analysis/` | `src/analyzers/market/indices/` | 指数分析 |
| `scripts/sector_analysis/` | `src/analyzers/sector/` | 板块分析 |
| `scripts/unified_analysis/` | `src/analyzers/comprehensive/unified/` | 统一分析 |
| `scripts/comprehensive_asset_analysis/` | `src/analyzers/comprehensive/asset/` | 资产分析 |
| `scripts/us_stock_analysis/` | `src/analyzers/stock_specific/us/` | 美股分析 |
| `scripts/hk_stock_analysis/` | `src/analyzers/stock_specific/hk/` | 港股分析 |
| `scripts/leverage_management/` | `src/analyzers/macro/leverage/` | 杠杆管理 |
| `stock/` | `[deprecated]/stock/` | 待确认是否需要 |
| `joinquant/` | `[deprecated]/joinquant/` | 特定平台代码 |
| `compound_interest/` | `[deprecated]/compound_interest/` | 独立工具 |

## 迁移步骤

### 阶段1: 创建新结构 ✓
1. 创建 `src/` 主目录
2. 创建子目录结构

### 阶段2: 迁移核心模块
1. 迁移 `position_analysis/` → `src/analyzers/position/`
2. 迁移 `trading_strategies/` → `src/strategies/`
3. 删除重复的 `scripts/position_analysis/` 和 `scripts/trading_strategies/`

### 阶段3: 重组scripts内容
1. 迁移各个分析脚本到对应的 `src/analyzers/` 子目录
2. 保留真正的独立脚本在 `scripts/`
3. 创建统一的运行入口脚本

### 阶段4: 更新import路径
1. 全局搜索并替换import路径
2. 更新配置文件中的路径

### 阶段5: 测试验证
1. 运行测试套件
2. 验证关键功能
3. 更新文档

### 阶段6: 清理
1. 移动废弃代码到 `[deprecated]/`
2. 更新README
3. 提交代码

## 优势

1. **清晰的模块化**：
   - `src/` 包含可复用的核心模块
   - `scripts/` 只包含独立运行脚本

2. **更好的组织**：
   - 按功能分类（市场分析、持仓分析、策略等）
   - 减少目录深度和复杂性

3. **易于维护**：
   - 消除重复目录
   - 明确的职责划分

4. **更好的可扩展性**：
   - 新功能容易找到归属
   - 符合Python项目最佳实践

## 需要确认

1. `stock/` 文件夹的用途？是否还在使用？
2. `joinquant/` 是否还需要？
3. `compound_interest/` 是否应该保留为独立工具？
4. 是否需要保留 `scripts/` 下的某些特定脚本？

## 风险和注意事项

1. **Import路径变更**：需要全局更新
2. **现有脚本兼容性**：可能需要创建软链接或兼容层
3. **文档更新**：需要同步更新所有文档
4. **团队协作**：需要通知团队成员新的目录结构

## 建议

**我建议分阶段进行**，先征得你的同意后，我会：
1. 创建新的目录结构
2. 逐步迁移模块（每次迁移一个大模块并测试）
3. 最后清理和文档更新

**你希望我现在开始执行吗？还是需要调整方案？**
