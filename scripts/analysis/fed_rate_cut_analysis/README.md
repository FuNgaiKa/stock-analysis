# 美联储降息周期市场分析系统 (增强版)

## 📋 功能简介

本模块专门分析美联储历史降息周期下,A股、美股、港股三大市场的表现,为投资决策提供历史数据支持。

### 核心功能

- ✅ **历史降息周期数据** - 覆盖2000年至今4个降息周期
- ✅ **三大市场对比** - 美股/A股/港股主要指数表现
- ✅ **关键指标分析** - 总收益率、年化收益率、最大回撤、最大涨幅、波动率、夏普比率
- ✅ **分阶段分析** - 降息前90天/降息周期中/降息后180天/完整周期
- ✅ **周期类型对比** - 预防式降息 vs 纾困式降息
- ✅ **多周期自由对比** - 🆕 支持选择任意多个降息周期进行对比分析
- ✅ **特朗普执政期分析** - 🆕 分析特朗普第一/第二任期的市场表现
- ✅ **A股历史牛市分析** - 🆕 深度分析2007/2015/2021三次牛市
- ✅ **详细报告输出** - 文本格式报告,便于查看和分享

## 📊 历史降息周期

### 2000年以来的4个降息周期

| 周期 | 时间范围 | 利率变化 | 类型 | 经济背景 |
|------|----------|----------|------|----------|
| 2001年互联网泡沫 | 2001-01-03 ~ 2003-06-25 | 6.5% → 1.0% | 纾困式 | 互联网泡沫破裂,911事件 |
| 2007-2008年金融危机 | 2007-09-18 ~ 2008-12-16 | 5.25% → 0.25% | 纾困式 | 次贷危机,雷曼破产 |
| 2019年预防式降息 | 2019-08-01 ~ 2020-03-16 | 2.25% → 0.25% | 预防式 | 贸易摩擦,后期疫情 |
| 2024年软着陆降息 | 2024-09-19 ~ 至今 | 5.5% → 4.5% | 预防式 | 通胀回落,软着陆 |

## 🎯 支持的市场指数

### 美股指数
- 标普500 (^GSPC)
- 纳斯达克 (^IXIC)
- 道琼斯 (^DJI)

### A股指数
- 上证指数 (000001.SS)
- 深证成指 (399001.SZ)
- 创业板指 (399006.SZ)
- 沪深300 (000300.SS)

### 港股指数
- 恒生指数 (^HSI)
- 恒生国企 (^HSCE)
- 恒生科技 (HSTECH.HK)

## 🚀 快速开始

### 1. 环境准备

确保已安装必要的依赖:

```bash
pip install yfinance pandas numpy
```

### 2. 基础使用 (原版功能)

#### 分析所有降息周期(推荐)

```bash
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode all
```

这将分析所有4个降息周期,输出完整的对比报告。

#### 分析当前降息周期(2024年)

```bash
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode current
```

快速查看当前降息周期的市场表现。

#### 对比最近两个周期(2019 vs 2024)

```bash
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode compare
```

重点对比2019预防式降息和2024软着陆降息的市场表现差异。

#### 分析指定周期

```bash
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode single --cycle "2019年预防式降息"
```

### 3. 市场选择

可以通过 `--market` 参数选择特定市场:

```bash
# 仅分析美股
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode all --market us

# 仅分析A股
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode all --market cn

# 仅分析港股
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode all --market hk

# 分析所有市场(默认)
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode all --market all
```

### 4. 🆕 增强功能使用 (run_enhanced_analysis.py)

#### 4.1 多周期自由对比

选择任意多个降息周期进行对比分析:

```bash
# 对比2019和2024两次预防式降息
python scripts/fed_rate_cut_analysis/run_enhanced_analysis.py --mode multi --cycles "2019年预防式降息" "2024年软着陆降息"

# 对比2001和2007两次纾困式降息
python scripts/fed_rate_cut_analysis/run_enhanced_analysis.py --mode multi --cycles "2001年互联网泡沫" "2007-2008年金融危机" --market us

# 对比所有4个降息周期
python scripts/fed_rate_cut_analysis/run_enhanced_analysis.py --mode multi --cycles "2001年互联网泡沫" "2007-2008年金融危机" "2019年预防式降息" "2024年软着陆降息"
```

#### 4.2 特朗普执政期分析

分析特朗普第一任期(2017-2021)和第二任期(2025至今)的市场表现:

```bash
# 分析美股在特朗普执政期的表现
python scripts/fed_rate_cut_analysis/run_enhanced_analysis.py --mode trump --market us

# 分析三大市场在特朗普执政期的表现
python scripts/fed_rate_cut_analysis/run_enhanced_analysis.py --mode trump --market all
```

**关键发现:**
- 第一任期(2017-2021): 标普500 +67.26%, 纳斯达克 +137.56%
- 贸易战、税改、疫情等因素交织,但整体科技股表现突出

#### 4.3 A股历史牛市分析

深度分析A股三次重要牛市:

```bash
# 分析A股历史牛市(2007/2015/2021)
python scripts/fed_rate_cut_analysis/run_enhanced_analysis.py --mode bull
```

**三次牛市对比:**

| 牛市 | 时间 | 上证指数涨幅 | 特点 |
|------|------|--------------|------|
| 2007年大牛市 | 2006-01 ~ 2007-10 | +410.61% | 股权分置改革,疯狂牛市 |
| 2015年杠杆牛市 | 2014-07 ~ 2015-06 | +149.79% | 融资融券+场外配资 |
| 2021年结构性牛市 | 2020-07 ~ 2021-02 | +20.79% | 机构抱团,核心资产 |

## 📈 输出指标说明

| 指标 | 含义 | 计算方法 |
|------|------|----------|
| **总收益率(%)** | 周期内总涨跌幅 | (期末价格 - 期初价格) / 期初价格 × 100 |
| **最大回撤(%)** | 从高点回落的最大幅度 | 最大 ((当前价 - 累计最高价) / 累计最高价) × 100 |
| **最大涨幅(%)** | 从低点反弹的最大幅度 | 最大 ((当前价 - 累计最低价) / 累计最低价) × 100 |
| **年化波动率(%)** | 价格波动程度(风险指标) | 日收益率标准差 × √252 × 100 |
| **夏普比率** | 风险调整后收益 | (年化收益率 - 无风险利率) / 年化波动率 |
| **胜率(%)** | 上涨交易日占比 | 上涨天数 / 总交易天数 × 100 |

## 📂 报告输出

运行后会在 `scripts/fed_rate_cut_analysis/reports/` 目录下生成详细报告:

```
reports/
└── fed_cycle_analysis_all_20241017_143022.txt  # 分析报告
```

报告内容包括:
1. 各降息周期的详细信息
2. 各指数在不同阶段的表现对比
3. 最佳表现排名(按总收益率)

## 💡 使用场景

### 场景1: 了解当前降息周期的历史规律

```bash
# 查看2024年降息周期与历史的对比
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode compare --market all
```

**适用于**: 想了解当前市场在历史降息周期中的位置,判断后续走势。

### 场景2: 研究预防式降息的市场特征

对比2019年和2024年两次预防式降息,找出共同规律。

**发现**: 预防式降息周期中,科技股(纳斯达克)和港股表现通常优于传统指数。

### 场景3: 评估不同市场的降息敏感度

```bash
# 分析美股表现
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode all --market us

# 对比A股表现
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode all --market cn
```

**发现**: 港股对美联储降息最敏感,A股具有一定独立性。

## 🔍 关键发现(基于历史数据)

### 1. 降息类型很重要

- **预防式降息**(1995-1996, 2019, 2024): 股市通常表现较好
- **纾困式降息**(2001, 2007-2008): 伴随经济衰退,股市大概率下跌

### 2. 市场敏感度差异

- **港股**: 对美联储降息反应最积极,弹性最大
- **美股**: 科技成长股(纳斯达克)在降息周期中表现突出
- **A股**: 具有独立性,关键看国内政策和基本面

### 3. 阶段性表现

- **降息前90天**: 市场预期反应,提前定价
- **降息周期中**: 流动性改善,风险偏好提升
- **降息后180天**: 经济基本面主导,关键看是否软着陆

## 📊 技术实现

### 模块结构

```
fed_rate_cut_analysis/
├── cycle_data_provider.py       # 降息周期数据定义
├── special_period_provider.py   # 🆕 特殊时期数据(特朗普执政期/A股牛市)
├── fed_cycle_analyzer.py        # 核心分析引擎
├── special_period_analyzer.py   # 🆕 特殊时期分析引擎
├── run_fed_analysis.py          # 原版执行入口
├── run_enhanced_analysis.py     # 🆕 增强版执行入口
├── README.md                    # 使用文档
└── reports/                     # 输出报告目录
```

### 数据源

- **yfinance**: 获取美股、港股、A股历史行情数据
- **pandas**: 数据处理和指标计算
- **numpy**: 统计计算

### 分析流程

1. 定义降息周期时间范围
2. 获取各市场指数的历史数据
3. 计算各阶段的关键指标
4. 生成对比分析报告
5. 输出最佳表现排名

## 🔧 高级用法

### 自定义分析周期

如需添加新的降息周期,编辑 `cycle_data_provider.py`:

```python
RateCutCycle(
    name="自定义周期名称",
    start_date="YYYY-MM-DD",
    end_date="YYYY-MM-DD",
    start_rate=X.X,
    end_rate=Y.Y,
    total_cuts=N,
    background="经济背景描述",
    cycle_type="预防式/纾困式"
)
```

### 添加新的市场指数

在 `cycle_data_provider.py` 的 `_define_indices()` 方法中添加:

```python
"cn": {
    "000905.SS": "中证500",  # 添加新指数
    ...
}
```

## ⚠️ 注意事项

1. **数据可用性**: 部分历史周期的A股数据可能不完整,这是数据源限制
2. **网络依赖**: 首次运行需要下载历史数据,请保持网络连接
3. **2024周期**: 当前周期尚未结束,后续数据会持续更新
4. **免责声明**: 历史数据仅供参考,不构成投资建议

## 📞 技术支持

如遇到问题,请检查:

1. yfinance库是否正常工作: `pip install --upgrade yfinance`
2. 网络连接是否正常
3. 指数代码是否正确(不同市场代码格式不同)

## 🔄 更新日志

### v2.0 (2025-10-17) 🆕
- ✅ 支持选择多个降息周期进行自由对比
- ✅ 添加特朗普执政期分析(第一/第二任期)
- ✅ 添加A股历史牛市分析(2007/2015/2021)
- ✅ 新增年化收益率指标
- ✅ 优化报告格式和可读性

### v1.0 (2025-10-17)
- ✅ 基础降息周期分析功能
- ✅ 4个历史周期数据
- ✅ 三大市场对比
- ✅ 分阶段分析

## 🔄 未来计划

- [ ] 支持HTML可视化报告
- [ ] 添加行业轮动分析
- [ ] 集成邮件推送功能
- [ ] 支持更多技术指标
- [ ] 添加Web界面集成
- [ ] 添加更多政治周期分析(拜登/奥巴马等)

## 📚 使用示例汇总

```bash
# 1. 基础降息周期分析
python scripts/fed_rate_cut_analysis/run_fed_analysis.py --mode all

# 2. 对比多个降息周期
python scripts/fed_rate_cut_analysis/run_enhanced_analysis.py --mode multi --cycles "2019年预防式降息" "2024年软着陆降息"

# 3. 分析特朗普执政期
python scripts/fed_rate_cut_analysis/run_enhanced_analysis.py --mode trump --market us

# 4. 分析A股历史牛市
python scripts/fed_rate_cut_analysis/run_enhanced_analysis.py --mode bull

# 5. 对比所有纾困式降息
python scripts/fed_rate_cut_analysis/run_enhanced_analysis.py --mode multi --cycles "2001年互联网泡沫" "2007-2008年金融危机" --market us
```

---

**让历史数据指导投资决策!** 📈
