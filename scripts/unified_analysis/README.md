# 📊 统一资产分析工具

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

## 📅 更新日志

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
