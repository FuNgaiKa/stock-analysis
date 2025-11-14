# GitHub Workflow 每日邮件配置指南

## 功能说明

每天**北京时间15:10**(A股收盘后10分钟)自动:
1. 生成市场洞察报告 (25个标的的完整分析)
2. 发送到你的邮箱

---

## 配置步骤

### 1. 设置GitHub Secrets

在你的GitHub仓库中配置以下Secrets:

**Settings → Secrets and variables → Actions → New repository secret**

| Secret名称 | 说明 | 示例值 |
|-----------|------|--------|
| `SMTP_SERVER` | SMTP服务器地址 | `smtp.qq.com` (QQ邮箱)<br>`smtp.gmail.com` (Gmail) |
| `SMTP_PORT` | SMTP端口 | `465` (SSL)<br>`587` (TLS) |
| `SENDER_EMAIL` | 发件人邮箱 | `your_email@qq.com` |
| `SENDER_PASSWORD` | 邮箱授权码(非登录密码!) | QQ邮箱需在设置中生成授权码 |
| `RECIPIENT_EMAILS` | 收件人邮箱(多个用逗号分隔) | `your_email@qq.com,another@gmail.com` |

---

### 2. 获取QQ邮箱授权码(推荐)

1. 登录QQ邮箱 → 设置 → 账户
2. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
3. 开启"POP3/SMTP服务"
4. 点击"生成授权码"
5. 将生成的**授权码**作为 `SENDER_PASSWORD`

**注意**: 
- ❌ 不是你的QQ密码!
- ✅ 是QQ邮箱生成的授权码(16位字符)

---

### 3. 配置示例

#### QQ邮箱配置
```yaml
SMTP_SERVER: smtp.qq.com
SMTP_PORT: 465
SENDER_EMAIL: your_qq_number@qq.com
SENDER_PASSWORD: abcdefghijklmnop  # 授权码,非QQ密码
RECIPIENT_EMAILS: your_qq_number@qq.com
```

#### Gmail配置
```yaml
SMTP_SERVER: smtp.gmail.com
SMTP_PORT: 587
SENDER_EMAIL: your_email@gmail.com
SENDER_PASSWORD: your_app_password  # Gmail应用专用密码
RECIPIENT_EMAILS: your_email@gmail.com
```

#### 163邮箱配置
```yaml
SMTP_SERVER: smtp.163.com
SMTP_PORT: 465
SENDER_EMAIL: your_email@163.com
SENDER_PASSWORD: your_auth_code  # 163邮箱授权码
RECIPIENT_EMAILS: your_email@163.com
```

---

## 运行时间

**Cron表达式**: `10 7 * * 1-5`

| 字段 | 值 | 说明 |
|------|-----|------|
| 分钟 | 10 | 第10分钟 |
| 小时 | 7 | UTC 07:00 = 北京时间 15:00 |
| 日 | * | 每天 |
| 月 | * | 每月 |
| 星期 | 1-5 | 周一到周五(工作日) |

**实际运行时间**: 北京时间 15:10 (工作日)

---

## 手动触发

不想等到15:10?可以手动触发:

1. 进入GitHub仓库
2. **Actions** → **Daily Market Report**
3. 点击 **Run workflow** → **Run workflow**

立即生成并发送报告!

---

## 发送内容

邮件包含:
- **主题**: `市场洞察报告 - YYYY-MM-DD`
- **正文**: 完整的Markdown格式报告
- **附件**: 无(直接嵌入正文)

报告内容:
- ✅ 今日市场大盘分析
- ✅ 我的持仓分析
- ✅ 持仓综合评价 (9维度)
- ✅ 标的汇总 (25个标的)
- ✅ 机构级核心指标
- ✅ 14个看多标的详细分析 (经过精简)

---

## 常见问题

### Q1: 为什么收不到邮件?

**检查清单**:
1. ✅ GitHub Secrets配置正确?
2. ✅ `SENDER_PASSWORD` 是授权码,不是登录密码?
3. ✅ SMTP服务器和端口正确?
4. ✅ 发件人邮箱开启了SMTP服务?
5. ✅ 检查垃圾邮件箱

**调试方法**:
- Actions页面查看workflow运行日志
- 如果失败,会上传日志artifact

---

### Q2: 能改成每天早上发送吗?

可以!修改 `.github/workflows/daily_market_report.yml`:

```yaml
on:
  schedule:
    # 北京时间 08:00 = UTC 00:00
    - cron: '0 0 * * 1-5'
```

**注意**: 早上发送的是**前一日收盘数据**

---

### Q3: 能发送到多个邮箱吗?

可以!在 `RECIPIENT_EMAILS` 中用逗号分隔:

```
your_email@qq.com,partner@gmail.com,team@163.com
```

---

### Q4: 如何暂停自动发送?

**方法1**: 禁用workflow
- Actions → Daily Market Report → ⋯ → Disable workflow

**方法2**: 删除schedule触发器
- 删除 `daily_market_report.yml` 中的 `schedule` 部分
- 保留 `workflow_dispatch` 可手动触发

---

### Q5: 能自定义邮件标题吗?

可以!修改 `russ_trading/runners/run_unified_analysis.py` 中的邮件发送逻辑。

---

## 安全建议

### 1. 使用独立的发件邮箱 ✅
- 不要用个人主力邮箱
- 创建一个专门用于自动化的邮箱

### 2. 定期更换授权码 ✅
- 每3-6个月更换一次
- 在GitHub Secrets中更新

### 3. 限制收件人 ✅
- 只发给你自己或信任的人
- 报告包含你的持仓信息,注意隐私

### 4. 监控workflow运行 ✅
- 定期检查Actions运行状态
- 如果连续失败,及时排查

---

## 高级配置

### 添加持仓综合评价(已集成)

报告已包含:
- 📊 九维度评分
- 🚨 三大核心问题
- 📋 本周操作清单(T0/T1/T2)
- 📊 执行后预期效果

### 精简报告(已实现)

默认只发送14个看多标的的详细分析:
- 强烈看多(5个)
- 看多(3个)
- 中性偏多(6个)

如需完整版(25个标的),修改运行命令:
```bash
# 不使用过滤脚本,直接发送完整报告
python -m russ_trading.runners.run_unified_analysis --email
```

---

## 文件位置

- **Workflow配置**: `.github/workflows/daily_market_report.yml`
- **报告生成器**: `russ_trading/runners/run_unified_analysis.py`
- **邮件配置**: `config/email_config.yaml` (GitHub Actions自动生成)
- **过滤脚本**: `scripts/filter_report_targets_v2.py` (可选)

---

## 总结

**配置步骤**:
1. ✅ 在GitHub Secrets中配置5个变量
2. ✅ 获取邮箱授权码(非登录密码)
3. ✅ 提交并推送 `.github/workflows/daily_market_report.yml`
4. ✅ 等待北京时间15:10自动运行,或手动触发测试

**下次改进**:
- ⏳ 可选: 添加周报自动发送
- ⏳ 可选: 邮件HTML格式美化
- ⏳ 可选: 添加图表附件

**状态**: ✅ 配置完成,立即可用!
