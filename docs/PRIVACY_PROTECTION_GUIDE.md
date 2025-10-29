# 🔒 隐私保护与配置化指南

## 📋 问题说明

原项目中存在以下隐私泄露风险：

1. **硬编码的个人财务目标**
   - 代码中硬编码了具体金额（50万、100万等）
   - 报告中显示实际仓位和投资策略

2. **已提交的敏感报告**
   - `reports/daily/` 下的每日报告包含真实持仓建议
   - `reports/monthly/` 下的月度计划包含具体目标

## ✅ 解决方案

### 核心思路：配置化 + 脱敏显示

1. **所有敏感数据从配置文件读取**
2. **支持两种显示模式**：
   - 私有模式：显示具体金额
   - 公开模式：只显示百分比和进度

3. **配置文件不提交到 Git**

---

## 🚀 快速开始

### 步骤1：创建你的私有配置

```bash
# 复制配置模板
cp config/investment_goals.yaml.example config/investment_goals.yaml

# 编辑配置（填入你的真实数据）
# Windows: notepad config/investment_goals.yaml
# macOS/Linux: vim config/investment_goals.yaml
```

**如果是公开仓库，使用脱敏版本：**
```bash
cp config/investment_goals_privacy.yaml.example config/investment_goals.yaml
```

### 步骤2：配置隐私保护选项

编辑 `config/investment_goals.yaml`：

```yaml
# 私有使用（本地）
show_absolute_amounts: true   # 显示具体金额
show_target_amounts: true     # 显示目标金额

# 公开分享（GitHub）
show_absolute_amounts: false  # 只显示百分比
show_target_amounts: false    # 用别名代替金额
```

### 步骤3：验证配置

```bash
# 测试配置加载
python russ_trading/config/investment_config.py
```

输出示例：
```
==================================================
投资目标配置测试
==================================================
初始资金: 500000.0
阶段目标: [500000, 750000, 1000000]
最终目标: 1000000.0
目标年化收益: 60.0%
基准日期: 2025-01-01
沪深300基准: 3145.0
显示具体金额: False
显示目标金额: False

金额格式化测试:
  初始资金: 初始资金
  当前进度: 目标进度30%
  最终目标: 最终目标
==================================================
```

---

## 📝 配置文件说明

### 完整配置项

```yaml
# ================================
# 资金目标配置
# ================================

initial_capital: 500000        # 初始资金
current_capital: null          # 当前资金（null=自动计算）
stage_targets:                 # 阶段性目标
  - 500000
  - 750000
  - 1000000
final_target: 1000000          # 最终目标

# ================================
# 收益率目标
# ================================

target_annual_return: 0.60     # 目标年化收益率（60%）
target_total_return: 1.0       # 目标总收益率（100%=翻倍）

# ================================
# 基准配置
# ================================

base_date: "2025-01-01"        # 基准日期
hs300_base: 3145.0             # 沪深300基准点位
cybz_base: 2060.0              # 创业板指基准点位
kechuang50_base: 955.0         # 科创50基准点位

# ================================
# 隐私保护配置
# ================================

show_absolute_amounts: false   # 是否显示具体金额
show_target_amounts: false     # 是否显示目标金额
stage_names:                   # 阶段名称（代替金额）
  - "初始阶段"
  - "中期目标"
  - "最终目标"
```

---

## 🔧 代码迁移指南

### 旧代码（硬编码）

```python
# ❌ 旧方式：硬编码
initial_capital = 500000
stage_targets = [500000, 600000, 700000, 1000000]
final_target = 1000000
```

### 新代码（配置化）

```python
# ✅ 新方式：从配置读取
from russ_trading.config.investment_config import get_investment_config

config = get_investment_config()

initial_capital = config.initial_capital
stage_targets = config.stage_targets
final_target = config.final_target

# 格式化显示（自动脱敏）
print(f"当前资金: {config.format_amount(current_capital)}")
print(f"目标: {config.format_target_description(final_target, 2)}")
```

### 显示效果对比

**私有模式** (`show_absolute_amounts: true`):
```
当前资金: ¥51.5万
还需: ¥48.5万
目标: ¥100万
```

**公开模式** (`show_absolute_amounts: false`):
```
当前资金: 目标进度51.5%
还需: 48.5%
目标: 最终目标
```

---

## 🛡️ 已提交文件的清理

如果你之前已经将敏感报告提交到了 Git，需要从历史中清除：

### ⚠️ 警告：此操作会改写 Git 历史

```bash
# 备份当前仓库
cp -r ../stock-analysis ../stock-analysis.backup

# 方案1：使用 git-filter-repo（推荐）
pip install git-filter-repo

git filter-repo --path reports/daily/ --invert-paths
git filter-repo --path reports/monthly/ --invert-paths
git filter-repo --path reports/archive/russ_*.md --invert-paths

# 方案2：使用 filter-branch（适用于 Windows）
bash scripts/cleanup_sensitive_reports.sh

# 强制推送到远程（⚠️ 谨慎操作）
git push origin --force --all
```

### 更安全的方案：重新开始

如果报告不重要，可以考虑：

```bash
# 1. 删除所有报告文件
rm -rf reports/daily/2025*
rm -rf reports/monthly/*
rm -rf reports/archive/russ_*

# 2. 提交删除记录
git add -A
git commit -m "chore: 移除包含敏感信息的历史报告"
git push origin main
```

---

## 📋 完整的 .gitignore 配置

确保以下文件不会被提交：

```gitignore
# 敏感配置文件
config/email_config.yaml
config/investment_goals.yaml
!config/*.example.yaml

# 持仓数据
data/positions_*.json
!data/positions_example.json

# 个人报告（包含真实数据）
reports/daily/
reports/archive/
reports/temp/

# 但允许示例和README
!reports/README.md
!reports/example/

# 环境变量
.env
!.env.example
```

---

## ✅ 最佳实践

### 1. 本地开发（显示真实数据）

```yaml
# config/investment_goals.yaml（不提交）
show_absolute_amounts: true
show_target_amounts: true
initial_capital: 515000  # 你的真实数据
```

### 2. 公开仓库（脱敏显示）

```yaml
# config/investment_goals.yaml（不提交）
show_absolute_amounts: false
show_target_amounts: false
initial_capital: 500000  # 示例数据
```

### 3. 多人协作

每个人维护自己的 `config/investment_goals.yaml`：

```bash
# 团队成员A
initial_capital: 300000
final_target: 600000

# 团队成员B
initial_capital: 800000
final_target: 1500000
```

### 4. CI/CD 环境

使用环境变量或 GitHub Secrets：

```yaml
# .github/workflows/daily_report.yml
env:
  INITIAL_CAPITAL: ${{ secrets.INITIAL_CAPITAL }}
  FINAL_TARGET: ${{ secrets.FINAL_TARGET }}
```

---

## 🔍 验证隐私保护

### 检查是否有敏感信息泄露

```bash
# 1. 检查 Git 跟踪的文件
git ls-files | grep -E "(config|data|reports)"

# 2. 搜索代码中的硬编码金额
grep -r "515000\|51\.5万\|100万" --include="*.py" russ_trading/

# 3. 检查报告文件
git status reports/

# 4. 查看最近的提交
git log --oneline -10
```

### 期望结果

- ✅ `config/investment_goals.yaml` 不在 Git 跟踪中
- ✅ `reports/daily/` 目录为空或不提交
- ✅ 代码中无硬编码金额
- ✅ 最近提交无敏感信息

---

## 📞 问题排查

### Q1: 配置文件不存在，程序报错？

**A**: 程序会自动使用默认配置（示例值），不会报错。但建议创建配置文件：

```bash
cp config/investment_goals.yaml.example config/investment_goals.yaml
```

### Q2: 如何在报告中显示真实金额？

**A**: 修改配置文件：

```yaml
show_absolute_amounts: true
show_target_amounts: true
```

### Q3: 如何完全隐藏目标金额？

**A**: 使用阶段名称代替：

```yaml
show_target_amounts: false
stage_names:
  - "启动阶段"
  - "成长阶段"
  - "成熟阶段"
```

### Q4: 已经提交的报告如何处理？

**A**: 有三种方案：

1. **从 Git 历史清除**（推荐，但会改写历史）
2. **删除文件并提交**（历史仍可见）
3. **私有化仓库**（最简单）

---

## 📚 相关文档

- [配置文件示例](../config/investment_goals.yaml.example)
- [脱敏配置示例](../config/investment_goals_privacy.yaml.example)
- [代码示例](../russ_trading/config/investment_config.py)
- [环境变量配置](.env.example)

---

## 🎯 总结

通过配置化和脱敏显示，你可以：

1. ✅ **保护隐私** - 敏感数据不提交到 Git
2. ✅ **灵活切换** - 本地显示真实数据，公开分享时自动脱敏
3. ✅ **团队协作** - 每个人使用自己的配置
4. ✅ **易于维护** - 修改目标无需改代码

**建议配置**：

- 个人项目：`show_absolute_amounts: true`（本地）
- 公开项目：`show_absolute_amounts: false`（GitHub）
- 商业项目：使用环境变量 + CI/CD Secrets
