# 📖 每日报告生成 - 快速开始指南

> 最简单的命令，快速生成你的每日报告

**更新说明(2025-11-18)**: 持仓调整建议已整合到市场洞察报告中,现在只需运行一个命令!

---

## 🎯 每日报告(整合版)

### 市场洞察报告(整合持仓调整建议)
- **内容**：
  - 📊 持仓分析章节(持仓概况+调整建议+风险预警)
  - 🌍 5阶段市场状态识别
  - 📈 25个资产11维度分析(看多/看空标的筛选)
  - 💰 综合投资建议
- **输出**：发送邮件 + Markdown文档
- **位置**：`reports/daily/YYYY-MM/市场洞察报告_YYYYMMDD.md`

---

## ⚡ 最简单的命令（推荐）

> ⚠️ **v4.0重要变更**: 必须使用 `-m` 模块方式运行，不再支持直接执行脚本
> ✨ **v4.1整合更新**: 持仓调整已整合到市场洞察报告中,只需一个命令!

### 从项目根目录运行（推荐）

```bash
# 进入项目根目录
cd C:\Users\russell.fu\PycharmProjects\stock-analysis

# 生成市场洞察报告(已整合持仓调整建议)并发送邮件
python -m russ_trading.runners.run_unified_analysis --email

# 或者仅生成不发邮件
python -m russ_trading.runners.run_unified_analysis
```

---

## 🤖 对Claude说什么

### 生成市场洞察报告（最常用）

**直接对Claude说**：
```
帮我生成今天的市场洞察报告
```

或者更详细：
```
帮我运行市场洞察报告,整合持仓调整建议,发送邮件
```

或者简洁版:
```
生成报告
```

---

## 📋 命令参数说明

### run_unified_analysis.py (市场洞察报告)

| 参数 | 说明 | 示例 |
|------|------|------|
| `--email` | 生成报告并发送邮件 | **推荐每次使用** |
| `--save` | 保存到指定文件 | `--save reports/test.md` |
| `--assets` | 分析指定资产 | `--assets CYBZ HKTECH` |
| 无参数 | 仅生成报告不发邮件 | - |

**说明**: 报告已自动整合持仓调整建议章节,无需单独运行持仓调整命令

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
    └── 2025-11/                          # 按月份分组
        └── 市场洞察报告_20251118.md         # 整合版报告(含持仓调整建议)
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
- 发送到邮箱(--email参数)
- 本地文件: `reports/daily/2025-11/市场洞察报告_YYYYMMDD.md`

---

## 🔥 快速参考卡片

**保存这个到你的笔记里**：

```bash
# ===== 每日必做 =====
cd C:\Users\russell.fu\PycharmProjects\stock-analysis

# 生成市场洞察报告(整合持仓调整建议)并发送邮件
python -m russ_trading.runners.run_unified_analysis --email

# ===== 对Claude说 =====
"帮我生成今天的市场洞察报告"
# 或简洁版
"生成报告"
```

---

## 📞 需要帮助？

### 对Claude说：

```
# 生成报告
"帮我生成今天的市场洞察报告"
"生成报告"

# 检查配置
"检查一下我的持仓文件和邮箱配置"

# 查看报告
"打开今天的市场洞察报告"

# 问题排查
"报告生成失败了，帮我看看是什么问题"
```

---

**最后更新**: 2025-11-18
**文档维护**: Claude Code
**版本**: v4.1 (整合版)
