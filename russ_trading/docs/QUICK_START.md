# 📖 每日报告生成 - 快速开始指南

> 最简单的命令，快速生成你的每日报告

---

## 🎯 每日两个报告

### 报告1: 持仓调整建议（Ultra Aggressive版）
- **内容**：市场状态、持仓健康度、收益追踪、操作建议
- **输出**：Markdown文档（不发邮件）
- **位置**：`reports/daily/YYYY-MM/持仓调整建议_YYYYMMDD_增强版.md`

### 报告2: 市场标的洞察（25个资产分析）
- **内容**：25个资产的11维度技术分析和风险评估
- **输出**：发送邮件 + Markdown文档
- **位置**：`reports/daily/YYYY-MM/unified_analysis_YYYYMMDD.md`

---

## ⚡ 最简单的命令（推荐）

> ⚠️ **v4.0重要变更**: 必须使用 `-m` 模块方式运行，不再支持直接执行脚本

### 方式1: 从项目根目录运行（推荐）

```bash
# 进入项目根目录
cd /Users/russ/PycharmProjects/stock-analysis

# 生成报告1：持仓调整建议
python -m russ_trading.generators.daily_position_report_generator --auto-update

# 生成报告2：市场标的洞察（发送邮件）
python -m russ_trading.runners.run_unified_analysis --email
```

### ~~方式2: 从russ_trading目录运行~~ (已弃用)

**v4.0后不再支持**，请使用方式1

---

## 🤖 对Claude说什么

### 生成两个报告（最常用）

**直接对Claude说**：
```
帮我生成今天的两个报告
```

或者更详细：
```
帮我运行每日报告：
1. 持仓调整建议（--auto-update）
2. 市场标的洞察（--email）
```

### 只生成持仓调整建议

```
生成持仓调整建议报告
```

### 只生成市场标的洞察

```
生成市场标的洞察报告并发送邮件
```

---

## 📋 命令参数说明

### 报告1: daily_position_report_generator.py

| 参数 | 说明 | 示例 |
|------|------|------|
| `--auto-update` | 自动获取最新市场数据 | **推荐每次使用** |
| `--date` | 指定日期 | `--date 2025-10-29` |
| `--positions` | 指定持仓文件 | `--positions data/positions_20251029.json` |
| 无参数 | 使用默认配置生成报告 | |

### 报告2: run_unified_analysis.py

| 参数 | 说明 | 示例 |
|------|------|------|
| `--email` | 生成报告并发送邮件 | **推荐每次使用** |
| `--save` | 保存到指定文件 | `--save reports/test.md` |
| `--assets` | 分析指定资产 | `--assets CYBZ HKTECH` |

---

## 📁 文件位置说明

### 输入文件（你需要准备）

```
data/
├── positions_20251029.json      # 你的最新持仓（必须）
└── positions_example.json       # 示例文件（不要修改）
```

**持仓文件命名规则**：`positions_YYYYMMDD.json`

### 输出文件（自动生成）

```
reports/
└── daily/
    └── 2025-10/                          # 按月份分组
        ├── 持仓调整建议_20251029_增强版.md   # 报告1
        └── unified_analysis_20251029.md     # 报告2
```

---

## ⚙️ 首次使用配置

### 1. 确认持仓文件存在

```bash
# 检查最新的持仓文件
ls data/positions_*.json

# 如果没有，复制示例文件并修改
cp data/positions_example.json data/positions_20251029.json
# 然后编辑 positions_20251029.json，填入你的实际持仓
```

### 2. 确认邮箱配置（报告2需要）

```bash
# 检查邮箱配置文件是否存在
ls config/email_config.yaml

# 如果没有，复制模板并配置
cp config/email_config.example.yaml config/email_config.yaml
# 然后编辑 email_config.yaml，填入你的邮箱信息
```

### 3. 安装依赖（首次运行前）

```bash
pip install -r requirements.txt
```

---

## ❓ 常见问题

### Q1: 找不到持仓文件？

**错误信息**：`WARNING - 未找到持仓文件,使用默认持仓`

**解决方法**：
```bash
# 检查data目录下是否有positions_*.json文件
ls data/positions_*.json

# 如果没有，创建一个
cp data/positions_example.json data/positions_20251029.json
```

### Q2: 邮件发送失败？

**错误信息**：`ERROR - 邮件发送失败`

**解决方法**：
1. 检查邮箱配置文件：`config/email_config.yaml`
2. 确认QQ邮箱授权码是否正确
3. 检查网络连接

### Q3: 市场数据获取失败？

**错误信息**：`WARNING - 获取沪深300失败`

**解决方法**：
1. 检查网络连接
2. 等待几分钟后重试（API限流）
3. 系统会自动切换备用数据源

### Q4: 报告在哪里？

**位置**：
- 报告1：`reports/daily/2025-10/持仓调整建议_YYYYMMDD_增强版.md`
- 报告2：发送到邮箱 + `reports/daily/2025-10/unified_analysis_YYYYMMDD.md`

---

## 🔥 快速参考卡片

**保存这个到你的笔记里**：

```bash
# ===== 每日必做 =====
cd C:\Users\russell.fu\PycharmProjects\stock-analysis

# 1. 生成持仓调整建议
python russ_trading/daily_position_report_generator.py --auto-update

# 2. 生成市场标的洞察（发送邮件）
python russ_trading/run_unified_analysis.py --email

# ===== 对Claude说 =====
"帮我生成今天的两个报告"
```

---

## 📞 需要帮助？

### 对Claude说：

```
# 生成报告
"帮我生成今天的两个报告"

# 检查配置
"检查一下我的持仓文件和邮箱配置"

# 查看报告
"打开今天的持仓调整建议报告"

# 问题排查
"报告生成失败了，帮我看看是什么问题"
```

---

**最后更新**: 2025-10-29
**文档维护**: Claude Code
