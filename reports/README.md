# 📊 报告目录说明

本目录存放各类分析报告,按照类型和时间进行分类管理。

## 📁 目录结构

```
reports/
├── daily/              # 每日报告
│   ├── 2024/           # 按年份分类
│   │   └── 10/         # 按月份分类
│   └── 2025/
│       └── 10/
│           ├── unified_analysis_20251016.md
│           ├── unified_analysis_20251017.md
│           ├── 持仓调整建议_20251020.md
│           └── 持仓调整建议_20251021_v2.md
│
├── analysis/           # 专项分析报告
│   ├── bull_markets/   # 牛市分析
│   │   ├── cn_bull_markets_analysis_*.md
│   │   └── cn_bull_drawdown_*.md
│   ├── drawdown/       # 回撤分析
│   │   └── 创业板科创50回撤分析_20251019.md
│   └── sector/         # 行业分析
│
├── backtest/           # 回测报告
│
├── archive/            # 历史归档
│   ├── comprehensive_asset_*.md
│   ├── test_*.md
│   ├── 升级总结报告.md
│   └── russ_strategy_full_report.md
│
├── charts/             # 图表存储
│
└── temp/               # 临时文件和测试文件
    ├── *.txt           # 各类测试数据
    ├── *test*.md       # 测试报告
    └── position_analysis_*.html
```

## 📋 报告类型说明

### 1. 每日报告 (daily/)

**统一分析报告**:
- 文件命名: `unified_analysis_YYYYMMDD.md`
- 内容: 25个资产(指数、板块、个股)的11维度分析
- 频率: 每日更新
- 脚本: `scripts/unified_analysis/run_unified_analysis.py`

**持仓调整建议**:
- 文件命名: `持仓调整建议_YYYYMMDD.md` 或 `持仓调整建议_YYYYMMDD_更新说明.md`
- 内容: 基于最新数据的持仓调整建议,包括预测验证、操作建议等
- 频率: 根据市场变化更新
- 生成方式: Claude每日更新(使用命令: "更新持仓文档")

### 2. 专项分析报告 (analysis/)

**牛市分析** (bull_markets/):
- 中国A股牛市周期分析
- 牛市回撤分析
- 历史牛市对比研究

**回撤分析** (drawdown/):
- 创业板科创50回撤分析
- 各类资产回撤研究

**行业分析** (sector/):
- 板块轮动分析
- 行业深度研究

### 3. 历史归档 (archive/)

存放以下类型的报告:
- 超过1个月的旧报告
- 测试报告
- 已废弃的报告格式
- 临时性分析报告

## 🔄 报告更新流程

### 每日自动报告

**方式1: 自动邮件**
```bash
# 运行统一分析并发送邮件
python scripts/unified_analysis/run_unified_analysis.py --email
```

**方式2: 生成本地报告**
```bash
# 生成Markdown报告
python scripts/unified_analysis/run_unified_analysis.py --save reports/daily/2025-10/unified_analysis_$(date +%Y%m%d).md
```

### 持仓调整建议更新

**推荐方式: 让 Claude 更新**

每天对 Claude 说:
```
更新持仓文档
```

Claude 会自动:
1. 运行统一分析获取最新数据
2. 对比关键指标变化
3. 验证之前的预测准确性
4. 更新操作建议
5. 生成新版本文档

详见: `scripts/unified_analysis/README.md` 的"每日自动更新持仓调整建议"章节

## 📊 报告内容说明

### 统一分析报告包含

1. **分析概览**: 总资产数、成功分析数、失败数
2. **标的汇总表**: 25个资产的核心指标一览
3. **详细分析**:
   - 四大科技指数(创业板指、科创50、恒生科技、纳斯达克)
   - 宽基指数(沪深300)
   - 大宗商品(黄金、比特币)
   - 16个板块ETF
   - 3个个股

4. **分析维度**(11维):
   - 历史点位分析
   - 技术面分析
   - 资金面分析
   - 估值分析(A股专属)
   - 情绪分析
   - 风险评估
   - 综合判断
   - 成交量分析
   - 支撑压力位
   - 市场宽度
   - 恐慌指数

### 持仓调整建议包含

1. **最新市场动态**: 关键指标变化
2. **预测验证**: 对比之前的预测和实际走势
3. **操作建议**: 加仓、减仓、止盈、止损等
4. **风险提示**: 需要注意的风险点
5. **执行清单**: 具体的操作步骤

## 🗄️ 归档规则

**自动归档**(建议每月执行):
- 将超过1个月的每日报告移至 `archive/`
- 保留最近30天的报告在 `daily/` 目录

**手动归档**:
- 测试报告
- 临时性分析
- 已废弃的报告格式

## ⚠️ 注意事项

1. **文件命名规范**:
   - 每日报告: 使用日期格式 `YYYYMMDD`
   - 专项报告: 使用描述性名称 + 日期
   - 避免使用空格,使用下划线或中文

2. **Git管理**:
   - 每日报告建议commit
   - 过旧的归档报告可以考虑从Git中删除(保留在本地)

3. **邮件报告**:
   - 邮件配置文件: `config/email_config.yaml`
   - 详见: `scripts/unified_analysis/README.md`

## 📝 更新日志

### 2025-10-21
- 优化目录结构,daily按年/月两级分类
- 新增 drawdown/、sector/、backtest/、temp/ 子目录
- 移动所有临时和测试文件到 temp/
- 移动回撤分析文件到 analysis/drawdown/
- 更新 README.md 说明文档

### 2025-10-20
- 创建reports目录结构说明
- 整理现有报告文件,按类型和日期分类
- 新增 daily/、analysis/、archive/ 子目录
- 移动21个报告文件到对应目录

---

**生成时间**: 2025-10-21
**维护者**: Claude Code
