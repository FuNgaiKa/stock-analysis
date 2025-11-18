# GitHub Workflow 持仓配置说明

## 📋 问题背景

GitHub workflow生成的市场洞察报告之前缺失持仓分析章节,原因是:
1. 持仓数据文件 `data/positions_*.json` 在 `.gitignore` 中被排除(隐私保护)
2. GitHub Actions运行时,仓库中没有实际持仓数据
3. 本地代码存在排序bug,可能读到错误的持仓文件

## ✅ 修复内容

### 1. 修复排序Bug
**位置**: `russ_trading/runners/run_unified_analysis.py:1408-1412`

**修复前** (错误):
```python
# 按字典序排序,可能读到 positions_test.json 而非最新文件
position_files = sorted(glob.glob(str(positions_dir / 'positions_*.json')), reverse=True)
```

**修复后** (正确):
```python
# 按修改时间排序,确保读取最新持仓文件
position_files = sorted(
    glob.glob(str(positions_dir / 'positions_*.json')),
    key=os.path.getmtime,  # 按修改时间排序
    reverse=True  # 最新的在前
)
```

### 2. 支持环境变量读取
**位置**: `russ_trading/runners/run_unified_analysis.py:1379-1403`

新增持仓数据读取优先级:
1. **环境变量 `POSITIONS_DATA`** (GitHub Secret) - 优先
2. **本地最新文件** `data/positions_YYYYMMDD.json` - 降级
3. **示例文件** `data/positions_example.json` - 保底(如需要)

### 3. 修改GitHub Workflow配置
**位置**: `.github/workflows/daily_market_report.yml:36-37`

新增环境变量:
```yaml
env:
  POSITIONS_DATA: ${{ secrets.POSITIONS_DATA }}  # 从GitHub Secret读取
```

---

## 🔧 GitHub Secret 配置方法

### 步骤1: 准备持仓数据JSON

复制你最新的持仓文件内容,例如 `data/positions_20251112.json`:

```json
[
  {
    "asset_name": "恒生科技ETF",
    "asset_code": "513180",
    "asset_key": "513180",
    "position_ratio": 0.28,
    "current_value": 144200
  },
  {
    "asset_name": "证券ETF",
    "asset_code": "512880",
    "asset_key": "512880",
    "position_ratio": 0.23,
    "current_value": 118450
  }
]
```

### 步骤2: 在GitHub仓库中配置Secret

1. 打开你的GitHub仓库: `https://github.com/<你的用户名>/stock-analysis`
2. 点击 **Settings** (设置)
3. 左侧菜单选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. 填写:
   - **Name**: `POSITIONS_DATA`
   - **Secret**: 粘贴上面的JSON内容(整个数组,包括方括号)
6. 点击 **Add secret** 保存

### 步骤3: 更新Secret (当持仓变化时)

每次调仓后,如果想更新GitHub workflow的持仓数据:
1. 打开 **Settings** → **Secrets and variables** → **Actions**
2. 找到 `POSITIONS_DATA`,点击 **Update**
3. 粘贴新的JSON内容
4. 保存

**建议更新频率**: 每周/每月调仓后更新一次即可

---

## 🧪 测试方法

### 本地测试 (读取本地文件)
```bash
# 应该读取 data/positions_20251112.json (最新的)
python -m russ_trading.runners.run_unified_analysis --verbose
```

**预期日志**:
```
成功读取 8 个持仓 (来源: positions_20251112.json)
✅ 将使用持仓数据生成报告, 共 8 个持仓
```

### GitHub Workflow测试 (读取Secret)

**方式1: 手动触发workflow**
1. GitHub仓库 → **Actions** 标签
2. 选择 **Daily Market Report**
3. 点击 **Run workflow** → **Run workflow**

**方式2: 检查定时任务日志**
- 等待北京时间 16:10 自动运行
- 查看 **Actions** → 最新运行记录

**预期日志**:
```
✅ 从环境变量 POSITIONS_DATA 读取持仓数据
成功读取 8 个持仓 (来源: 环境变量)
✅ 将使用持仓数据生成报告, 共 8 个持仓
```

---

## 📊 运行逻辑对比

| 环境 | POSITIONS_DATA | 本地文件 | 读取结果 |
|------|---------------|---------|---------|
| **本地** | ❌ 未配置 | ✅ 有最新文件 | 读取 `positions_20251112.json` |
| **GitHub** (未配置Secret) | ❌ 未配置 | ❌ 无文件 | ⚠️ 无持仓数据,报告缺失持仓章节 |
| **GitHub** (已配置Secret) | ✅ 已配置 | ❌ 无文件 | 读取环境变量 `POSITIONS_DATA` |

---

## ⚠️ 注意事项

### 1. 隐私保护
- ✅ `data/positions_*.json` 依然不提交到git (`.gitignore`保护)
- ✅ GitHub Secret是加密存储,不会在日志中明文显示
- ⚠️ 报告中的持仓分析会包含仓位百分比和市值,注意邮件接收人范围

### 2. 数据同步
- **本地**: 自动读取最新 `positions_YYYYMMDD.json`
- **GitHub**: 需要手动更新Secret `POSITIONS_DATA`
- **建议**: 每周调仓后同时更新本地文件和GitHub Secret

### 3. 可选配置
如果你不想在GitHub workflow的邮件报告中包含持仓分析:
- 不配置 `POSITIONS_DATA` Secret即可
- 邮件将只包含市场分析,不包含持仓章节

---

## 🔍 故障排查

### 问题1: 本地报告读到旧的持仓文件
**症状**: 日志显示读取了 `positions_test.json` 或很旧的文件

**原因**: 旧版本代码的排序bug

**解决**:
1. 确认已更新到最新代码 (包含 `key=os.path.getmtime`)
2. 删除 `positions_test.json` 等测试文件

### 问题2: GitHub workflow报告没有持仓分析
**症状**: 邮件报告缺少"我的持仓分析"章节

**原因**:
- 未配置 `POSITIONS_DATA` Secret
- Secret内容格式错误

**解决**:
1. 检查GitHub仓库 Settings → Secrets 中是否有 `POSITIONS_DATA`
2. 检查Secret内容是否为有效JSON数组
3. 查看workflow运行日志,搜索 "持仓" 关键词

### 问题3: GitHub workflow读取Secret失败
**症状**: 日志显示 "解析环境变量 POSITIONS_DATA 失败"

**原因**: Secret内容不是有效的JSON格式

**解决**:
1. 复制你的 `positions_YYYYMMDD.json` 文件内容
2. 使用JSON验证工具检查格式: https://jsonlint.com/
3. 确保Secret中粘贴的是完整JSON数组 (包括 `[` 和 `]`)

---

## 📝 总结

修复后的持仓读取逻辑:
1. ✅ **本地**: 按修改时间自动读取最新持仓文件
2. ✅ **GitHub**: 从Secret读取,或降级到本地文件(如果存在)
3. ✅ **隐私**: 实际持仓不提交git,通过Secret安全传递
4. ✅ **灵活**: 可选择是否在GitHub workflow报告中包含持仓

---

**文档创建时间**: 2025-11-18
**相关文件**:
- `russ_trading/runners/run_unified_analysis.py`
- `.github/workflows/daily_market_report.yml`
