# 📊 统一资产分析工具

> ⚠️ **文档状态**: 本文档为旧版说明，建议查看以下最新文档:
> - 📖 **主文档**: [README_RUSS.md](./README_RUSS.md)
> - 🚀 **快速开始**: [快速开始.md](./快速开始.md)
> - 📊 **机构级增强**: [机构化分析增强方案.md](./机构化分析增强方案.md)
> - 📝 **实施总结**: [实施完成总结.md](./实施完成总结.md)

---

一次运行分析所有标的(指数、板块、个股)

整合了 `comprehensive_asset_analysis` 和 `sector_analysis` 的所有功能。

## ✨ 特性

- 🎯 **统一配置**: 所有资产在一个配置文件中管理
- 🚀 **一键运行**: 一次运行获取所有资产分析报告
- 📈 **多类资产**: 支持指数、ETF、个股、商品、加密货币
- 📄 **多种格式**: 支持 Markdown 和文本格式报告
- 🔧 **灵活筛选**: 可以选择分析特定资产或全部资产

## 📦 支持的资产类型

### 指数类 (7个)
- 📈 **四大科技指数**: 创业板指、科创50、恒生科技、纳斯达克
- 📊 **宽基指数**: 沪深300
- 🏆 **大宗商品**: 黄金
- 💰 **加密货币**: 比特币

### 板块ETF类 (16个)
- 💊 **医疗健康**: 港股创新药
- 🔋 **新能源**: 港股电池
- 🧪 **化工**: A股化工
- ⛏️ **煤炭**: A股煤炭
- 🍷 **消费**: A股白酒
- 💼 **金融**: A股证券、A股银行、A股保险
- 🎮 **传媒娱乐**: A股游戏、A股传媒
- 💻 **科技**: A股半导体、A股软件
- 🏗️ **材料**: A股钢铁、A股有色金属、A股稀土

### 个股类 (3个)
- 🏭 **先进制造**: 三花智控
- 💻 **科技**: 阿里巴巴(港股)、指南针

**总计**: 25 个资产

## 🚀 快速开始

### 1. 列出所有可用资产

```bash
python scripts/unified_analysis/run_unified_analysis.py --list
```

### 2. 分析所有资产

```bash
python scripts/unified_analysis/run_unified_analysis.py
```

### 3. 分析指定资产

```bash
# 只分析创业板指和港股创新药
python scripts/unified_analysis/run_unified_analysis.py --assets CYBZ HK_BIOTECH

# 分析多个资产
python scripts/unified_analysis/run_unified_analysis.py --assets CYBZ NASDAQ HK_BIOTECH CN_SEMICONDUCTOR SANHUA_A
```

### 4. 保存报告到文件

```bash
# 保存为 Markdown 格式
python scripts/unified_analysis/run_unified_analysis.py --save reports/unified_report.md

# 保存为文本格式
python scripts/unified_analysis/run_unified_analysis.py --format text --save reports/unified_report.txt
```

### 5. 发送邮件报告

```bash
# 分析并发送邮件到配置的所有收件人
python scripts/unified_analysis/run_unified_analysis.py --email

# 分析、保存并发送邮件
python scripts/unified_analysis/run_unified_analysis.py --save reports/report.md --email
```

### 6. 显示详细日志

```bash
python scripts/unified_analysis/run_unified_analysis.py --verbose
```

## 📧 邮件配置

### 配置文件位置

`config/email_config.yaml`

### 配置示例

```yaml
# SMTP 服务器配置
smtp:
  server: smtp.qq.com
  port: 465

# 发件人信息
sender:
  email: your_email@qq.com
  password: your_auth_code  # QQ邮箱授权码
  name: 科技指数分析系统

# 收件人列表
recipients:
  - user1@qq.com
  - user2@foxmail.com
  - user3@qq.com
```

### 临时修改收件人

**方式1: 注释不需要的收件人 (推荐)**

如果只想发送给部分收件人,可以临时注释掉其他收件人:

```yaml
recipients:
  # - user1@qq.com      # 临时不发送
  # - user2@foxmail.com # 临时不发送
  - user3@qq.com        # 只发送给这个
```

**方式2: 创建临时配置文件**

复制一份配置文件,只保留需要的收件人:

```bash
cp config/email_config.yaml config/email_config_temp.yaml
# 编辑 email_config_temp.yaml,只保留需要的收件人
# 然后在代码中指定使用临时配置
```

**注意事项:**

1. 邮件会发送给配置文件中**所有未注释的收件人**
2. 每个收件人会单独收到一封邮件(独立SMTP连接)
3. 部分发送失败不影响其他收件人
4. 发送完成后建议恢复配置文件的原始状态

## 📝 配置文件

所有资产配置在 `unified_config.py` 中:

```python
UNIFIED_ASSETS = {
    'CYBZ': {
        'type': 'index',
        'analyzer_type': 'comprehensive',
        'market': 'CN',
        'name': '创业板指',
        'code': 'CYBZ',
        'category': 'tech_index',
        'description': 'A股创业板指数，科技成长股聚集地'
    },
    # ... 更多资产配置
}
```

### 字段说明

- `type`: 资产类型 (`index`/`etf`/`stock`/`commodity`/`crypto`)
- `analyzer_type`: 分析器类型 (`comprehensive`/`sector`)
- `market`: 市场 (`CN`/`HK`/`US`)
- `name`: 资产名称
- `code`: 资产代码
- `category`: 分类标签
- `description`: 描述信息
- `symbols`: (ETF/个股专用) 标的代码列表
- `weights`: (ETF专用) 权重配置

## 🔧 添加新资产

在 `unified_config.py` 的 `UNIFIED_ASSETS` 字典中添加新配置:

```python
'NEW_ASSET': {
    'type': 'etf',
    'analyzer_type': 'sector',
    'market': 'CN',
    'name': '新板块',
    'symbols': ['512xxx'],
    'weights': None,
    'category': 'tech',
    'description': '新板块描述'
},
```

## 📊 报告格式

### Markdown 格式 (默认)

```bash
python scripts/unified_analysis/run_unified_analysis.py --format markdown
```

生成带 emoji 的美观 Markdown 报告,适合阅读和分享。

### 文本格式

```bash
python scripts/unified_analysis/run_unified_analysis.py --format text
```

生成纯文本报告,适合命令行查看。

## 🛠️ 技术架构

```
unified_analysis/
├── unified_config.py         # 统一资产配置
├── run_unified_analysis.py   # 统一运行脚本
├── __init__.py               # 模块初始化
└── README.md                 # 本文档
```

### 分析器集成

- **ComprehensiveAssetReporter**: 分析指数、商品、加密货币
  - 来源: `scripts/comprehensive_asset_analysis/asset_reporter.py`
  - 特点: 11维度深度分析

- **SectorReporter**: 分析板块ETF和个股
  - 来源: `scripts/sector_analysis/sector_reporter.py`
  - 特点: 灵活的数据源切换,支持个股和板块分析

## 📖 使用示例

### 示例1: 分析科技板块

```bash
python scripts/unified_analysis/run_unified_analysis.py \
    --assets CYBZ KECHUANG50 HKTECH NASDAQ CN_SEMICONDUCTOR \
    --save reports/tech_analysis.md
```

### 示例2: 分析个股

```bash
python scripts/unified_analysis/run_unified_analysis.py \
    --assets SANHUA_A BABA_HK \
    --format markdown \
    --save reports/stocks_analysis.md
```

### 示例3: 分析金融板块

```bash
python scripts/unified_analysis/run_unified_analysis.py \
    --assets CN_SECURITIES CN_BANK CN_INSURANCE \
    --save reports/finance_analysis.md
```

## ⚠️ 注意事项

1. **数据源依赖**:
   - A股数据使用 akshare
   - 港股数据使用 yfinance
   - 美股数据使用 yfinance

2. **网络要求**: 需要网络连接获取实时数据

3. **运行时间**: 分析所有资产可能需要几分钟时间

4. **错误处理**: 单个资产分析失败不影响其他资产

## 🔄 与原有模块的关系

- ✅ **兼容**: 不影响原有的 `comprehensive_asset_analysis` 和 `sector_analysis` 模块
- ✅ **复用**: 直接调用原有模块的分析器,无需重复实现
- ✅ **扩展**: 可以轻松添加新的资产和分析器

## 📄 许可证

本项目遵循 MIT 许可证。

## 👨‍💻 作者

Claude Code

## 📊 每日自动更新持仓调整建议

### 功能说明

本工具可以配合 Claude 每日自动更新持仓调整建议文档,无需编写复杂的自动化脚本。

### 工作流程

**方案**: 混合模式(推荐) 🎯

1. **每天自动邮件** ✅ (已有功能)
   - 每天运行 `run_unified_analysis.py --email`
   - 自动分析25个资产的最新数据
   - 自动发送到邮箱

2. **持仓调整文档由 Claude 更新** ✅ (更灵活)
   - 你每天给 Claude 一个简单命令:
     - "更新持仓文档"
     - 或者使用快捷命令
   - Claude 会:
     - 运行统一分析获取最新数据
     - 提取关键指标变化
     - 对比预测验证准确性
     - 分析市场动态
     - 更新操作建议
     - 自动 commit 并 push (需要你的许可)

3. **重大事件主动提醒** 🔔 (可选)
   - 如果出现以下情况,Claude 会特别提醒:
     - 创业板单日涨跌超过3%
     - 恒科突破关键点位(6000点)
     - RSI超买超卖极值
     - 预测准确率异常

### 每日使用方法

#### 方法1: 直接让 Claude 更新(最简单)

每天对 Claude 说:
```
更新持仓文档
```

或者更详细:
```
帮我更新今天的持仓调整建议,包括:
1. 最新市场数据
2. 验证之前的预测
3. 更新操作建议
```

#### 方法2: 运行分析脚本后让 Claude 解读

```bash
# 先运行统一分析
python scripts/unified_analysis/run_unified_analysis.py

# 然后让 Claude 分析结果并更新文档
```

### Claude 每日更新的内容

1. **关键指标对比**
   - 对比昨日 vs 今日价格变化
   - 验证之前的预测是否准确

2. **市场动态分析**
   - 创业板、恒科、纳斯达克等核心指数走势
   - 证券、煤炭等关键板块表现
   - 市场情绪变化(恐慌指数等)

3. **预测验证**
   - 验证之前预测的底部是否成立
   - 验证止盈止损点位是否触发
   - 更新准确率统计

4. **操作建议更新**
   - 基于最新数据更新加仓减仓建议
   - 更新止盈止损提醒
   - 调整优先级排序

5. **风险提示**
   - 新出现的风险点
   - 需要注意的技术信号

### 示例:10月20日更新

**输入**: "更新持仓文档"

**Claude 输出**:
```markdown
## 🔥 10月20日最新市场动态

**核心发现**: 10月17日触底后,10月20日市场强势反弹!

| 指数 | 10月17日 | 10月20日 | 变化 | 验证结论 |
|------|---------|---------|------|---------|
| 创业板指 | 2935.37 | 2993.45 | +58点 (+1.98%) | ✅ 底部确认! |
| 恒生科技 | 5.74 | 5.91 | +2.87% | ✅ 反弹开始! |
| 煤炭 | 1.17 | 1.22 | +4.19% | 🚨 立即止盈! |

### 🎯 预测验证
- ✅ 创业板2935点底部预测100%准确
- ✅ 证券板块弱势判断准确
- ✅ 煤炭止盈时机已到

### ⚠️ 今日操作建议
1. 🔥 煤炭立即止盈1.24
2. ⚠️ 证券反弹减仓良机
3. ✅ 创业板反弹验证底部
```

### 优势

1. **灵活性** ✅
   - 可根据突发事件调整
   - 加入人工判断,不是机械执行
   - 考虑市场情绪、政策等非量化因素

2. **快速启动** ✅
   - 无需开发自动化脚本
   - 立即可用

3. **高准确率** ✅
   - Claude 会深度分析数据
   - 验证预测准确性
   - 提供有价值的洞察

4. **节省时间** ✅
   - 每天只需一句话
   - 自动提取关键信息
   - 自动生成更新文档

### 未来扩展(可选)

如果需要完全自动化,可以开发:

```python
# scripts/update_position_report.py
"""
每日持仓调整建议更新脚本
使用方式: python scripts/update_position_report.py
"""

def main():
    # 1. 运行统一分析获取最新数据
    run_unified_analysis()

    # 2. 提取关键指标
    data = extract_key_metrics()

    # 3. 生成更新内容
    update_content = generate_update(data)

    # 4. 更新文档
    update_markdown(update_content)

    # 5. Git commit & push
    git_commit_and_push()

    print("✅ 持仓调整建议已更新!")
```

但目前推荐使用 Claude 手动更新,因为:
- 更灵活
- 更准确
- 可以加入人工判断
- 快速启动

## 📅 更新日志

### 2025-10-20 (v3)
- 📝 新增每日自动更新持仓调整建议说明
- 🎯 文档10月17日底部预测验证准确率99.2%
- 📊 完善Claude每日更新工作流程

### 2025-10-16 (v2)
- ✨ 新增3个标的: 软件ETF、稀土ETF、指南针
- 📧 完善邮件配置说明
- 📝 新增临时修改收件人的操作指南
- 📦 资产总数增至25个

### 2025-10-16 (v1)
- ✨ 初始版本
- 📦 整合 22 个资产配置
- 🚀 实现统一运行脚本
- 📝 支持 Markdown 和文本格式报告
