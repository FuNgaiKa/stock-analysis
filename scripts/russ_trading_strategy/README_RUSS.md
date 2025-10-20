# 📊 Russ个人交易策略系统

> **专属个人投资策略管理系统** - 整合仓位管理、收益追踪、潜在空间评估和月度计划生成

---

## 🎯 系统概述

这是一个完整的个人投资策略管理系统,基于你的投资理念设计:

### 核心策略原则
- **仓位管理**: 滚动保持5-9成,留至少1成应对黑天鹅
- **标的选择**: 集中投资3-5只,单一标的≤20%
- **投资节奏**: 长线底仓 + 波段加减仓
- **收益目标**: 年化15%,穿越牛熊

### 收益目标

**长期目标**: 年化15%,穿越牛熊

**短期目标**(到2026年底,按优先级排序):
1. 🥇 资金达到100万 (最优先)
2. 🥈 跑赢沪深300 (次优先,从2025.1.1起计算)
3. 🥉 资金翻倍/100%涨幅 (第三优先)

---

## 📦 模块功能

### 1. 持仓健康度检查 (`position_health_checker.py`)
**功能**:检查持仓是否符合策略规则

**检查项**:
- ✅ 总仓位是否在5-9成区间
- ✅ 现金预留是否≥10%
- ✅ 单一标的是否≤20%
- ✅ 标的数量是否为3-5只

**输出**:
- 健康评分(0-100分)
- 健康等级(优秀/良好/警告/危险)
- 具体警告信息和优化建议

---

### 2. 收益追踪对比 (`performance_tracker.py`)
**功能**:追踪投资收益并与基准对比

**追踪指标**:
- 总收益率和年化收益率
- 与沪深300对比(超额收益)
- 阶段性目标进度(50万→60万→70万→100万)
- 翻倍目标进度(100%涨幅)
- 三大目标达成情况

**输出**:
- 收益概况表
- 基准对比表
- 阶段目标完成度
- 优化建议

---

### 3. 潜在空间评估 (`potential_analyzer.py`)
**功能**:基于历史牛市数据评估上涨潜力

**历史数据库**:
- 沪深300: 历史涨幅1.69-4.82倍
- 创业板: 历史涨幅1.97-3.33倍
- 科创50: 历史涨幅1.7-2.5倍

**评估场景**:
- 保守场景:基于历史最低涨幅
- 平均场景:基于历史平均涨幅
- 乐观场景:基于历史最高涨幅

**输出**:
- 各场景目标点位和上涨空间
- 风险收益比评估
- 投资价值判断
- 资产对比排名

---

### 4. 月度计划生成器 (`monthly_plan_generator.py`)
**功能**:生成月度投资计划

**输入数据**:
- 大盘数据(市场走势、技术面、资金面)
- 博主观点(雪球、公众号等)
- 机构数据(券商研报、基金持仓)
- 当前持仓情况

**输出内容**:
- 市场评估和综合判断
- 仓位调整策略
- 资产配置建议
- 具体行动清单(按优先级)
- 风险提示和投资机会
- 月度目标和复盘清单

---

## 🚀 快速开始

### 基础用法

```bash
# 进入目录
cd /Users/russ/PycharmProjects/stock-analysis/scripts/russ_trading_strategy

# 查看帮助
python russ_strategy_runner.py --help
```

---

## 📖 使用示例

### 示例1: 生成完整策略报告

```bash
python russ_strategy_runner.py \
    --full-report \
    --positions data/positions.json \
    --capital 550000 \
    --hs300 4538 \
    --save reports/russ_strategy_20251020.md
```

**positions.json 示例**:
```json
[
    {
        "asset_name": "证券ETF",
        "asset_key": "CN_SECURITIES",
        "position_ratio": 0.40,
        "current_value": 200000
    },
    {
        "asset_name": "恒生科技",
        "asset_key": "HKTECH",
        "position_ratio": 0.30,
        "current_value": 150000
    },
    {
        "asset_name": "煤炭ETF",
        "asset_key": "CN_COAL",
        "position_ratio": 0.15,
        "current_value": 75000
    },
    {
        "asset_name": "白酒ETF",
        "asset_key": "CN_LIQUOR",
        "position_ratio": 0.08,
        "current_value": 40000
    }
]
```

---

### 示例2: 持仓健康度检查

```bash
python russ_strategy_runner.py \
    --health-check \
    --positions data/positions.json
```

**输出示例**:
```markdown
## 📊 持仓健康度检查

**检查时间**: 2025-10-20 22:50

### 🟢 健康评分: 85.0分 (良好)

### 持仓概况

- **总仓位**: 93.0%
- **现金预留**: 7.0%
- **标的数量**: 4只

### 检查结果

- 🚨 总仓位93.0%偏高,超过最高建议90%
- ⚠️ 现金预留7.0%不足,低于最低要求10%
- ⚠️ 证券ETF仓位40.0%超过20%限制
- ✅ 持仓标的数量4只在合理区间(3-5只)

### 💡 优化建议

- 建议减仓至90%以下
- 建议保留至少10%现金应对黑天鹅事件
- 建议将单一标的仓位控制在20%以内
  - 证券ETF: 建议减仓20.0%
```

---

### 示例3: 收益追踪对比

```bash
python russ_strategy_runner.py \
    --performance \
    --capital 550000 \
    --hs300 4538
```

**输出示例**:
```markdown
## 📈 收益追踪对比

**追踪日期**: 2025-10-20
**基准日期**: 2025-01-01 (已运行293天/0.8年)

### 收益概况

- **初始资金**: ¥500,000
- **当前资金**: ¥550,000
- **总收益率**: 10.00%
- **年化收益率**: 12.82%
- **目标年化**: 15%

### 📊 基准对比(沪深300)

| 指标 | 我的收益 | 沪深300 | 超额收益 |
|------|---------|---------|---------|
| 总收益率 | 10.00% | 44.32% | -34.32% |

⚠️ **落后沪深300约34.32%**

### 🎯 三大目标达成情况

#### ✅ 目标1: 资金达到100万
- 当前进度: 55.0%
- 还需: ¥450,000 (45.0万)

#### ❌ 目标2: 跑赢沪深300
- 落后幅度: -34.32%

#### 🔄 目标3: 资金翻倍(100%涨幅)
- 当前进度: 55.0%
- 翻倍目标: ¥1,000,000
- 还需: ¥450,000 (45.0万)
```

---

### 示例4: 潜在空间评估

```bash
python russ_strategy_runner.py \
    --potential \
    --assets CYBZ,HS300,KECHUANG50 \
    --prices '{"CYBZ": 2993, "HS300": 4538, "KECHUANG50": 1368}'
```

**输出示例**:
```markdown
## 🚀 潜在空间对比评估

**分析日期**: 2025-10-20
**场景**: average (平均场景)

### 📊 上涨空间排名

| 排名 | 指数 | 当前点位 | 目标点位 | 上涨空间 |
|------|------|---------|---------|---------|
| 🥇 | 创业板指 | 2993 | 7932 | **165.1%** |
| 🥈 | 沪深300 | 4538 | 13750 | **203.0%** |
| 🥉 | 科创50 | 1368 | 2326 | **70.0%** |

### 📈 各指数详细分析

#### 创业板指
- **当前点位**: 2993
- **相对年初**: +45.29%
- **目标点位**: 7932
- **上涨空间**: 165.1%
- **建议**: ✅ 创业板具备翻倍潜力,适合作为核心配置

#### 沪深300
- **当前点位**: 4538
- **相对年初**: +44.32%
- **目标点位**: 13750
- **上涨空间**: 203.0%
- **建议**: 💡 沪深300作为大盘基准,适合作为底仓配置
```

---

### 示例5: 生成月度计划

首先准备市场数据文件 `market_data.json`:

```json
{
    "market_sentiment": "bullish",
    "trend": "uptrend",
    "fear_greed_index": 65,
    "indices": {
        "HS300": {
            "name": "沪深300",
            "current": 4538,
            "change_pct": "+0.53%",
            "judgment": "企稳"
        },
        "CYBZ": {
            "name": "创业板指",
            "current": 2993,
            "change_pct": "+1.98%",
            "judgment": "底部反弹,可加仓"
        },
        "KECHUANG50": {
            "name": "科创50",
            "current": 1368,
            "change_pct": "+0.35%",
            "judgment": "震荡"
        }
    }
}
```

运行命令:

```bash
python russ_strategy_runner.py \
    --monthly-plan \
    --month 2025-11 \
    --market-data data/market_data.json \
    --positions data/positions.json \
    --save reports/monthly_plan_2025-11.md
```

**输出包含**:
- 📊 市场评估(情绪、趋势、综合判断)
- 🎯 仓位策略(当前仓位、目标区间、调整建议)
- 💼 资产配置建议(推荐配置、建议减仓)
- ✅ 本月行动清单(按优先级分类)
- ⚠️ 风险提示
- 💡 投资机会
- 🎯 月度目标(收益目标、操作目标、纪律目标)
- 📋 月末复盘清单

---

## 🛠️ 配置说明

系统使用默认配置,也可以通过修改代码自定义:

```python
config = {
    'strategy': {
        'min_position': 0.50,           # 最小仓位50%
        'max_position': 0.90,           # 最大仓位90%
        'max_single_position': 0.20,    # 单一标的最大20%
        'black_swan_reserve': 0.10,     # 黑天鹅预留10%
        'min_assets': 3,                # 最少3只
        'max_assets': 5,                # 最多5只
        'target_annual_return': 0.15,   # 年化15%
        'risk_preference': 'moderate'   # 风险偏好
    },
    'targets': {
        'stage_targets': [500000, 600000, 700000, 1000000],  # 阶段目标
        'base_date': '2025-01-01',                           # 基准日期
        'initial_capital': 500000,                           # 初始资金
        'target_annual_return': 0.15                         # 年化15%
    },
    'benchmarks': {
        'hs300_base': 3145.0,      # 沪深300基准点位(2025.1.1)
        'cybz_base': 2060.0,       # 创业板基准点位
        'kechuang50_base': 955.0   # 科创50基准点位
    }
}
```

---

## 📁 目录结构

```
russ_trading_strategy/
├── README_RUSS.md                  # 本文档
├── russ_strategy_runner.py         # 主程序入口 ⭐
├── position_health_checker.py      # 持仓健康度检查
├── performance_tracker.py          # 收益追踪对比
├── potential_analyzer.py           # 潜在空间评估
├── monthly_plan_generator.py       # 月度计划生成器
├── unified_config.py               # 统一资产配置
├── run_unified_analysis.py         # 统一资产分析(原有)
└── unified_email_notifier.py       # 邮件通知器(原有)
```

---

## 🎓 使用流程建议

### 每日流程
1. **早盘前**: 查看隔夜市场动态
2. **盘中**: 观察持仓走势,记录重要信号
3. **收盘后**:
   - 运行 `--health-check` 检查持仓健康度
   - 运行 `--performance` 追踪收益情况
   - 更新持仓调整建议文档

### 每周流程
1. **周末**:
   - 运行 `--potential` 评估各指数潜在空间
   - 复盘本周操作,检查是否符合策略
   - 调整下周操作计划

### 每月流程
1. **月初**:
   - 运行 `--monthly-plan` 生成本月计划
   - 制定本月仓位调整和资产配置方案
2. **月末**:
   - 运行 `--full-report` 生成完整报告
   - 复盘本月执行情况
   - 评估目标达成度

---

## 💡 进阶技巧

### 1. 批量生成报告

创建shell脚本 `generate_reports.sh`:

```bash
#!/bin/bash

DATE=$(date +%Y%m%d)
REPORT_DIR="reports/$DATE"
mkdir -p $REPORT_DIR

# 健康度检查
python russ_strategy_runner.py \
    --health-check \
    --positions data/positions.json \
    --save "$REPORT_DIR/health_check.md"

# 收益追踪
python russ_strategy_runner.py \
    --performance \
    --capital 550000 \
    --hs300 4538 \
    --save "$REPORT_DIR/performance.md"

# 完整报告
python russ_strategy_runner.py \
    --full-report \
    --positions data/positions.json \
    --capital 550000 \
    --hs300 4538 \
    --save "$REPORT_DIR/full_report.md"

echo "报告生成完成: $REPORT_DIR"
```

### 2. 结合现有的unified_analysis

```bash
# 先运行资产分析
python run_unified_analysis.py --assets CYBZ HKTECH CN_COAL CN_LIQUOR

# 再运行策略报告
python russ_strategy_runner.py --full-report --positions data/positions.json
```

### 3. 定时任务

使用crontab设置定时任务:

```bash
# 每个交易日收盘后19:00运行
0 19 * * 1-5 cd /Users/russ/PycharmProjects/stock-analysis/scripts/russ_trading_strategy && ./generate_reports.sh
```

---

## 📊 与其他工具整合

### 与持仓调整建议文档整合

在每日持仓更新文档中嵌入策略模块结果:

```markdown
# 持仓调整建议_20251020

## 📊 持仓健康度检查
[嵌入 health_check 输出]

## 📈 收益追踪对比
[嵌入 performance 输出]

## 🚀 潜在空间评估
[嵌入 potential 输出]

## 操作建议
...
```

### Python脚本调用

```python
from russ_trading_strategy.russ_strategy_runner import RussStrategyRunner

# 创建运行器
runner = RussStrategyRunner()

# 持仓数据
positions = [...]

# 运行健康检查
health_report = runner.run_health_check(positions)

# 运行收益追踪
perf_report = runner.run_performance_tracking(550000, 4538)

# 组合输出
with open('daily_report.md', 'w') as f:
    f.write(health_report)
    f.write("\n\n")
    f.write(perf_report)
```

---

## 🐛 故障排查

### 问题1: 找不到模块

**错误**: `ModuleNotFoundError: No module named 'russ_trading_strategy'`

**解决**:
```bash
cd /Users/russ/PycharmProjects/stock-analysis/scripts
python russ_trading_strategy/russ_strategy_runner.py --help
```

### 问题2: JSON格式错误

**错误**: `JSONDecodeError: Expecting value`

**解决**: 检查JSON文件格式是否正确,使用在线工具验证: https://jsonlint.com/

### 问题3: 权限不足

**错误**: `PermissionError: [Errno 13] Permission denied`

**解决**:
```bash
chmod +x russ_strategy_runner.py
chmod +x generate_reports.sh
```

---

## 📞 维护说明

### 更新基准数据

如果需要更新基准点位(如新一年开始):

```python
# 在 russ_strategy_runner.py 的 _load_default_config() 中修改:
'benchmarks': {
    'hs300_base': 3145.0,      # 更新为新基准点位
    'cybz_base': 2060.0,
    'kechuang50_base': 955.0
}

'targets': {
    'base_date': '2025-01-01',  # 更新为新基准日期
    'initial_capital': 500000    # 更新为新起始资金
}
```

### 添加新的历史牛市数据

在 `potential_analyzer.py` 的 `HISTORICAL_BULL_DATA` 中添加:

```python
'CYBZ': {
    'bull_markets': [
        {'year': '2015', 'low': 1200, 'high': 4000, 'multiple': 3.33},
        {'year': '2021', 'low': 1817, 'high': 3576, 'multiple': 1.97},
        {'year': '2025', 'low': 2060, 'high': ???, 'multiple': ???}  # 新增
    ]
}
```

---

## 📝 免责声明

本系统基于历史数据和技术分析,仅供个人参考和学习使用,不构成任何投资建议。

**投资有风险,入市需谨慎。**

所有投资决策应基于个人独立判断,本系统开发者不对任何投资损失承担责任。

---

## 🎉 总结

这个系统整合了你的投资策略核心原则,提供了:

✅ **系统化**: 完整的策略执行和监控体系
✅ **自动化**: 一键生成各类报告
✅ **数据驱动**: 基于历史数据和实时数据决策
✅ **纪律性**: 强制执行仓位管理和风险控制规则

坚持使用这个系统,配合每日/每周/每月复盘,相信能帮助你实现:
- 📈 **长期目标**: 年化15%
- 💰 **短期目标**(到2026年底,按优先级):
  1. 100万资金 (最优先)
  2. 跑赢沪深300 (次优先)
  3. 资金翻倍 (第三优先)

**记住**: 系统只是工具,最重要的是执行纪律! 💪

---

**Happy Trading! 🎯**
