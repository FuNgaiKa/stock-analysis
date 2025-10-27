# 美股市场历史点位对比分析系统

基于历史数据统计的美股市场择时工具,支持标普500、纳斯达克、纳斯达克100、VIX恐慌指数等核心指数的分析。

## 🎯 核心功能

### Phase 1: 基础价格匹配 (已实现)

- ✅ **历史点位对比** - 查找历史相似点位,统计后续涨跌概率
- ✅ **概率统计分析** - 计算5日/10日/20日/60日上涨概率和预期收益
- ✅ **仓位管理建议** - 基于Kelly公式的智能仓位计算
- ✅ **多指数联合分析** - 四大核心指数综合研判
- ✅ **置信度评估** - 样本量和一致性加权的置信度打分

### Phase 2: 技术指标增强 (已实现) 🆕

- ✅ **技术指标过滤** - RSI/均线/52周位置三重过滤,提高匹配精度
- ✅ **市场环境识别** - 自动识别牛市顶部/熊市底部等5种市场状态
- ✅ **智能仓位调整** - 基于市场环境动态调整仓位建议
- ✅ **高位风险警示** - 在牛市顶部降低仓位,避免追高被套
- ✅ **底部机会提示** - 在熊市底部提示抄底机会

> 📖 **详细说明**: 参考 [`docs/US_STOCK_PHASE2.md`](US_STOCK_PHASE2.md) 了解Phase 2的完整功能和使用方法

### 支持的指数

| 指数代码 | 指数名称 | yfinance代码 | 说明 |
|---------|---------|-------------|------|
| **SPX** | 标普500 | ^GSPC | 美股大盘核心指标 |
| **NASDAQ** | 纳斯达克综合 | ^IXIC | 科技股为主 |
| **NDX** | 纳斯达克100 | ^NDX | 科技巨头 |
| **VIX** | VIX恐慌指数 | ^VIX | 市场情绪指标 |
| DJI | 道琼斯工业 | ^DJI | 传统蓝筹股 |
| RUT | 罗素2000 | ^RUT | 小盘股指数 |

## 📦 安装依赖

```bash
# 安装yfinance数据源
pip install yfinance

# 或安装所有项目依赖
pip install -r requirements.txt
```

## 🚀 快速开始

### 方式1: 主程序菜单(推荐)

```bash
# 运行主程序,选择"2.美股市场"
python position_analysis/main.py
```

### 方式2: 独立脚本

```bash
# Phase 1: 基础分析(默认)
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX --detail

# Phase 2: 技术指标增强分析 🆕
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX --detail --phase2

# 分析多个指数
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX NASDAQ NDX

# 调整相似度容差为3%
python scripts/us_stock_analysis/run_us_analysis.py --tolerance 0.03
```

## 📊 使用示例

### 示例1: 标普500单指数分析

```bash
$ python scripts/us_stock_analysis/run_us_analysis.py --indices SPX --detail

================================================================================
                          美股市场历史点位对比分析工具
================================================================================

  📅 分析时间: 2025-10-12 00:25:20
  📊 分析指数: 标普500
  🎯 相似容差: ±5.0%
  📈 分析周期: 5日, 10日, 20日, 60日

────────────────────────────────────────────────────────────────────────────────
  标普500 分析结果
────────────────────────────────────────────────────────────────────────────────

  📊 当前点位信息:
     最新价格: 6552.51
     涨跌幅: -2.71%
     数据日期: 2025-10-10
     相似时期: 66 个历史点位

  📈 历史点位对比分析:
     周期        样本数       上涨概率       平均收益       中位收益      置信度       仓位建议
     --------------------------------------------------------------------
     5日         66     72.7%     0.54%     0.63%   77.6%     75.5%
     10日        61     88.5%     1.14%     1.21%   89.8%     86.0%
     20日        51     96.1%     2.26%     2.24%   94.3%     86.0%
     60日        11    100.0%     6.96%     7.22%   57.3%     65.0%

  💡 20日周期核心结论:
     上涨概率: 96.1% (上涨 49 次, 下跌 2 次)
     预期收益: +2.26% (中位数 +2.24%)
     收益区间: [-0.66%, 4.62%]
     置信度: 94.3%

     🎯 强买入:建议重仓配置(86%左右)
```

### 示例2: 四大指数综合分析

```bash
$ python scripts/us_stock_analysis/run_us_analysis.py

# 输出综合市场评估:
# ✅ 成功分析: 4/4 个指数
# 📊 平均置信度: 84.7%
# 📈 看涨指数: 标普500, 纳斯达克综合, 纳斯达克100
# ➡️  中性指数: VIX恐慌指数
#
# 🎯 整体市场观点:
#    市场整体偏多,建议积极配置美股资产
```

## 📖 核心逻辑说明

### 1. 历史点位匹配

在近5年历史数据中,查找与当前点位相似的时期(默认容差±5%):

```python
当前标普500: 6552.51
相似区间: [6224.88, 6880.14]
找到66个历史点位
```

### 2. 未来收益率统计

计算这66个相似点位之后的涨跌情况:

```python
20日后统计:
- 上涨49次,下跌2次 → 上涨概率96.1%
- 平均收益+2.26%,中位数+2.24%
- 最好涨4.62%,最差跌0.66%
```

### 3. 置信度评估

综合考虑样本量和结果一致性:

```python
置信度 = 0.6 × 样本量得分 + 0.4 × 一致性得分
       = 0.6 × sigmoid(51-20)/10 + 0.4 × (0.961-0.5)/0.5
       = 94.3%
```

### 4. 仓位建议

基于Kelly公式和风险管理:

```python
基础仓位(概率): 96.1% > 75% → 0.8
Kelly调整(期望): 0.5 × (收益/方差)
最终仓位 = 0.7 × 基础 + 0.3 × Kelly = 86%
```

## 📚 数据源说明

### yfinance

- **优势**: 完全免费,无API限制,数据质量高
- **数据覆盖**: 美股所有指数,历史数据完整
- **更新频率**: 每日收盘后更新
- **延迟**: 主要指数实时,部分个股延迟15分钟
- **稳定性**: 基于Yahoo Finance公开API,长期稳定

### 数据质量验证

```python
# 5年历史数据测试结果(2020-2025):
标普500:      1255条记录,无缺失 ✓
纳斯达克综合: 1255条记录,无缺失 ✓
纳斯达克100:  1255条记录,无缺失 ✓
VIX恐慌指数:  1255条记录,无缺失 ✓
```

## ⚙️ 参数配置

### 命令行参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--indices` | `-i` | `['SPX', 'NASDAQ', 'NDX', 'VIX']` | 要分析的指数代码 |
| `--tolerance` | `-t` | `0.05` | 相似度容差(±5%) |
| `--periods` | `-p` | `[5, 10, 20, 60]` | 分析周期(天数) |
| `--detail` | `-d` | `False` | 显示详细分析结果 |
| `--phase2` | - | `False` | 🆕 使用Phase 2技术指标增强分析 |

### 使用示例

```bash
# 分析多个指数
python run_us_analysis.py --indices SPX NASDAQ VIX

# 调整容差为3%
python run_us_analysis.py --tolerance 0.03

# 自定义分析周期
python run_us_analysis.py --periods 10 20 30 90

# 详细模式
python run_us_analysis.py --detail
```

## 🔧 代码集成

### 在Python代码中使用

```python
from position_analysis.us_market_analyzer import USMarketAnalyzer

# 创建分析器
analyzer = USMarketAnalyzer()

# Phase 1: 基础分析
result_p1 = analyzer.analyze_single_index('SPX', tolerance=0.05, use_phase2=False)

# Phase 2: 技术指标增强分析 🆕
result_p2 = analyzer.analyze_single_index('SPX', tolerance=0.05, use_phase2=True)

# 查看Phase 2市场环境识别
if 'market_environment' in result_p2:
    env = result_p2['market_environment']
    print(f"市场环境: {env['environment']}")
    print(f"RSI: {env['rsi']:.1f}")
    print(f"距52周高点: {env['dist_to_high_pct']:.1f}%")
    print(f"均线状态: {env['ma_state']}")

# 查看分析结果
stats = result_p2['period_analysis']['20d']
print(f"上涨概率: {stats['up_prob']:.1%}")
print(f"平均收益: {stats['mean_return']:.2%}")

# 查看仓位建议(Phase 2会考虑市场环境调整)
advice = stats['position_advice']
print(f"推荐仓位: {advice['recommended_position']:.1%}")
print(f"操作信号: {advice['signal']}")
if 'warning' in advice:
    print(f"风险警示: {advice['warning']}")
```

## 📈 实战建议

### 1. 如何使用分析结果?

**高置信度(>80%)**:
- 上涨概率>70% → 积极配置,建议仓位60-80%
- 下跌概率>70% → 谨慎防守,建议仓位20-40%

**中等置信度(60-80%)**:
- 作为参考,结合其他指标决策
- 建议仓位40-60%

**低置信度(<60%)**:
- 样本不足,谨慎决策
- 建议中性仓位50%

### 2. VIX指数特殊说明

VIX是市场恐慌指数,与股指呈**负相关**:
- VIX高(>25)且看跌 → 股市可能反弹
- VIX低(<15)且看涨 → 股市可能调整
- VIX中位(15-25) → 市场情绪正常

### 3. 多指数联合研判

**三大指数同向**:
- 标普500、纳斯达克、纳斯达克100均看多 → 强烈看多信号
- 三者均看空 → 强烈看空信号

**指数分歧**:
- 标普看多,纳斯达克看空 → 结构性分化,谨慎
- 结合VIX判断市场情绪

## ⚠️ 风险提示

1. **历史不代表未来** - 分析基于历史统计,不保证未来表现
2. **样本量要求** - 样本少于20个时,置信度较低,谨慎参考
3. **黑天鹅事件** - 无法预测突发事件(如战争、疫情、金融危机)
4. **数据延迟** - yfinance部分数据有15分钟延迟
5. **模型局限** - 仅考虑价格因素,未考虑基本面、政策面

## 🛠️ 故障排查

### 常见问题

**Q1: 提示"数据获取失败"?**
```bash
# 检查网络连接
ping finance.yahoo.com

# 检查yfinance版本
pip show yfinance  # 推荐版本>=0.2.0

# 重新安装
pip install --upgrade yfinance
```

**Q2: 分析速度慢?**
```bash
# yfinance首次获取数据较慢(需下载5-10年历史数据)
# 后续会使用缓存,速度较快

# 如果持续慢,检查网络:
curl -I https://query1.finance.yahoo.com
```

**Q3: 某个指数分析失败?**
```bash
# 跳过该指数,单独测试
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX

# 查看详细错误日志
python scripts/us_stock_analysis/run_us_analysis.py --indices VIX 2>&1 | tee debug.log
```

## 🚧 后续规划

### ✅ Phase 2: 技术指标增强 (已完成 ✨)

- [x] 技术指标集成(RSI/均线/52周位置)
- [x] 市场环境识别(牛市顶部/熊市底部等5种状态)
- [x] 智能仓位调整(基于市场环境动态调整)
- [x] 高位风险警示功能
- [x] 完整测试和文档

> 📖 详细文档: [`docs/US_STOCK_PHASE2.md`](US_STOCK_PHASE2.md)
> 📊 完成总结: [`scripts/us_stock_analysis/PHASE2_COMPLETION_SUMMARY.md`](../scripts/us_stock_analysis/PHASE2_COMPLETION_SUMMARY.md)

**Phase 2核心价值**:
- 🎯 **更准确**: 三重技术指标过滤,只匹配技术状态相似的历史点位
- 🔍 **更智能**: 自动识别市场环境(牛市顶部/熊市底部等5种状态)
- 🛡️ **更安全**: 在高位自动降低仓位建议,避免追高被套
- 💡 **更实用**: 提供风险警示,帮助投资者做出理性决策

**使用示例**:
```bash
# Phase 2增强分析
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX --detail --phase2

# 查看Phase 2改进效果演示
python scripts/us_stock_analysis/demo_phase2_improvement.py
```

### Phase 3: 多维度深度分析 (规划中)

- [ ] VIX深度分析(分位数/历史相关性)
- [ ] 市场宽度分析(涨跌家数统计)
- [ ] 行业轮动分析(11大行业ETF)
- [ ] MACD/布林带等更多技术指标

### Phase 4: 智能诊断 (规划中)

- [ ] 12维度评分模型
- [ ] 牛熊市周期自动识别
- [ ] 中美市场联动分析
- [ ] 美联储政策监控

## 📞 技术支持

- **项目地址**: https://github.com/your-repo/stock-analysis
- **问题反馈**: 提交Issue或Pull Request
- **设计文档**: 参考 `docs/US_STOCK_DESIGN.md`

## 📄 许可证

本项目仅供学习研究使用,不构成投资建议。

---

**Created by Claude Code** 🤖

*Let data drive investment decisions!* 📈
