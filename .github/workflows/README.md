# GitHub Actions 自动化配置说明

## 📋 功能说明

`daily_tech_analysis.yml` 工作流实现：
- ⏰ **每天定时执行**: 北京时间15:00 (UTC 07:00)
- 📊 **分析四大科技指数**: 创业板/科创50/恒生科技/纳斯达克
- 📧 **自动发送邮件**: 发送HTML格式分析报告
- 🔧 **手动触发**: 支持在GitHub网页手动运行

---

## 🔐 配置GitHub Secrets（必须）

您需要在GitHub仓库中配置以下3个Secrets：

### 步骤1: 进入仓库设置

1. 打开您的GitHub仓库: https://github.com/FuNgaiKa/stock-analysis
2. 点击 **Settings** (设置)
3. 左侧菜单找到 **Secrets and variables** → **Actions**
4. 点击 **New repository secret** (新建仓库密钥)

### 步骤2: 添加3个Secrets

#### Secret 1: `SENDER_EMAIL`
- **Name**: `SENDER_EMAIL`
- **Value**: 您的QQ邮箱地址
- **示例**: `123456789@qq.com`

#### Secret 2: `EMAIL_PASSWORD`
- **Name**: `EMAIL_PASSWORD`
- **Value**: QQ邮箱授权码（16位，不是登录密码！）
- **示例**: `abcdwxyzefgh1234`

**如何获取QQ邮箱授权码**:
1. 访问 https://mail.qq.com
2. 登录 → 设置 → 账户
3. 找到 **POP3/IMAP/SMTP服务**
4. 开启服务 → 生成授权码
5. 发送短信 → 复制授权码

#### Secret 3: `RECIPIENT_EMAIL`
- **Name**: `RECIPIENT_EMAIL`
- **Value**: 收件人邮箱
- **示例**: `1264947688@qq.com`

### 步骤3: 验证配置

配置完成后，您应该看到3个Secrets：

```
SENDER_EMAIL         Updated X minutes ago
EMAIL_PASSWORD       Updated X minutes ago
RECIPIENT_EMAIL      Updated X minutes ago
```

---

## 🚀 启用工作流

### 方式1: 自动触发

配置好Secrets后，工作流会自动在每天北京时间15:00执行。

**执行逻辑**:
```
UTC 07:00 (每天)
↓
北京时间 15:00
↓
GitHub Actions 自动运行
↓
分析四大科技指数
↓
发送邮件到 RECIPIENT_EMAIL
```

### 方式2: 手动触发

您也可以随时手动运行：

1. 进入仓库页面
2. 点击 **Actions** 标签
3. 左侧选择 **四大科技指数每日分析**
4. 右侧点击 **Run workflow** → **Run workflow**

---

## 📊 查看执行结果

### 查看运行记录

1. 进入 **Actions** 标签
2. 查看最近的运行记录
3. 点击任意记录查看详细日志

### 查看分析日志

每次运行会保存日志文件，保留7天：

1. 点击运行记录
2. 向下滚动到 **Artifacts** 部分
3. 下载 **analysis-log** 查看详细日志

---

## ⏰ 修改执行时间

编辑 `.github/workflows/daily_tech_analysis.yml` 第6行：

```yaml
# 当前: 每天 UTC 07:00 (北京时间 15:00)
- cron: '0 7 * * *'

# 改为北京时间 22:00 (UTC 14:00)
- cron: '0 14 * * *'

# 改为每天两次: 15:00 和 22:00
- cron: '0 7 * * *'
- cron: '0 14 * * *'
```

**Cron表达式说明**:
```
* * * * *
│ │ │ │ │
│ │ │ │ └─ 星期 (0-6, 0=周日)
│ │ │ └─── 月份 (1-12)
│ │ └───── 日期 (1-31)
│ └─────── 小时 (0-23, UTC时间)
└───────── 分钟 (0-59)
```

**常用时间**:
- `0 7 * * *` → UTC 07:00 = 北京时间 15:00
- `0 14 * * *` → UTC 14:00 = 北京时间 22:00
- `0 23 * * *` → UTC 23:00 = 北京时间 07:00
- `0 7 * * 1-5` → 仅工作日执行

---

## 🔧 故障排查

### 问题1: 工作流未执行

**可能原因**:
- Secrets未配置或配置错误
- 工作流文件语法错误
- GitHub Actions权限未开启

**解决方法**:
1. 检查Secrets是否正确配置
2. 进入 **Actions** → **四大科技指数每日分析** → 查看错误信息
3. Settings → Actions → General → Workflow permissions → 选择 "Read and write permissions"

### 问题2: 邮件发送失败

**可能原因**:
- QQ邮箱授权码错误
- QQ邮箱未开启SMTP服务
- 授权码包含空格

**解决方法**:
1. 重新生成QQ邮箱授权码
2. 确保授权码没有空格
3. 检查 `EMAIL_PASSWORD` Secret是否正确

### 问题3: 依赖安装失败

**可能原因**:
- requirements.txt缺失或版本冲突

**解决方法**:
在项目根目录创建 `requirements.txt`:

```txt
yfinance>=0.2.28
pandas>=2.0.0
numpy>=1.24.0
akshare>=1.11.0
pyyaml>=6.0
tqdm>=4.65.0
```

### 问题4: 数据获取超时

**可能原因**:
- GitHub Actions服务器网络限制
- 数据源API限流

**解决方法**:
- 工作流会自动重试3次
- 如果持续失败，可以手动触发重新运行

---

## 📈 执行流程说明

```
1. 检出代码
   ↓
2. 设置Python 3.10环境
   ↓
3. 安装依赖包
   (yfinance, pandas, numpy, akshare, pyyaml, tqdm)
   ↓
4. 创建邮箱配置文件
   (使用Secrets中的配置)
   ↓
5. 运行分析脚本
   run_tech_comprehensive_analysis.py --email
   ↓
6. 分析四大科技指数
   - 创业板指
   - 科创50
   - 恒生科技
   - 纳斯达克
   ↓
7. 发送邮件报告
   (HTML格式，包含7大维度分析)
   ↓
8. 上传日志文件
   (保留7天)
```

---

## 💡 优化建议

### 1. 添加失败通知

在工作流失败时发送通知邮件：

```yaml
- name: 发送失败通知
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.qq.com
    server_port: 465
    username: ${{ secrets.SENDER_EMAIL }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: ⚠️ 四大科技指数分析失败
    to: ${{ secrets.RECIPIENT_EMAIL }}
    from: ${{ secrets.SENDER_EMAIL }}
    body: 分析任务执行失败，请查看GitHub Actions日志
```

### 2. 缓存依赖加速

工作流已启用pip缓存（`cache: 'pip'`），首次运行后会缓存依赖，加快后续运行速度。

### 3. 定时任务最佳实践

- ✅ 避开整点（如15:00改为15:05），减少GitHub Actions拥堵
- ✅ 避免周末执行（美股休市）: `0 7 * * 1-5`
- ✅ 多时间段执行（如15:00和22:00）获取更新数据

---

## 🎯 快速开始检查清单

- [ ] 已在GitHub仓库中配置3个Secrets
  - [ ] `SENDER_EMAIL`
  - [ ] `EMAIL_PASSWORD`
  - [ ] `RECIPIENT_EMAIL`
- [ ] 已推送 `.github/workflows/daily_tech_analysis.yml` 到仓库
- [ ] 已手动触发测试运行一次
- [ ] 已收到测试邮件
- [ ] ✅ 完成！等待每天定时执行

---

## 📧 预期邮件效果

您将每天收到：

**邮件主题**:
```
📈 【偏多】四大科技指数分析 - 3个看多 (2025-10-15)
```

**邮件内容**:
- 📊 四大指数卡片式展示
- 📈 20日上涨概率 + 平均收益
- 🎯 MACD/RSI技术指标
- 🔴 风险评估高亮
- ✅ 组合策略匹配
- 💡 操作建议

---

**配置完成后，您就可以每天自动收到科技指数分析报告了！** 🎉

有任何问题随时查看 **Actions** 标签中的运行日志。
