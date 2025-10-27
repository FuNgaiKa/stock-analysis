# 📊 每日市场报告配置指南

> 自动生成并发送每日市场总结邮件

---

## 🎯 功能说明

每日市场报告系统会在 **A股收盘后(15:10)** 自动:
1. 分析三大市场(美股/港股/A股)
2. 综合评估技术指标、资金流向、市场情绪
3. 计算综合评分(0-10分)
4. 生成交易建议
5. 通过邮件发送HTML格式报告

---

## 📧 邮件内容预览

### 邮件主题
```
📈 【偏多】每日市场总结 - 综合评分7.2/10 (2025-10-12)
```

### 邮件内容
- **三大市场概览**: 纳斯达克、标普500、恒生指数、上证指数、深证成指
- **A股核心指标**: 北向资金、融资情绪、市场宽度
- **交易建议**: 综合评分、操作策略、建议仓位
- **看多/看空信号**: 关键信号提示
- **支撑/压力位**: 关键技术点位

---

## 🔧 本地配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置邮箱

创建 `email_config.yaml`:

```yaml
smtp:
  server: smtp.qq.com       # QQ邮箱
  port: 465                 # SSL端口

sender:
  email: your_email@qq.com
  password: your_auth_code  # QQ邮箱授权码

recipients:
  - recipient1@example.com
  - recipient2@example.com

send_no_alert_email: false
```

**获取QQ邮箱授权码**:
1. 登录QQ邮箱网页版
2. 设置 → 账户 → POP3/SMTP服务
3. 开启服务并生成授权码
4. 使用授权码(不是QQ密码)

### 3. 本地测试

```bash
# 仅生成报告(不发送邮件)
python scripts/run_daily_report.py

# 生成并发送邮件
python scripts/run_daily_report.py --email

# 保存到文件
python scripts/run_daily_report.py --save reports/daily_report.txt

# 详细日志
python scripts/run_daily_report.py --email --verbose
```

---

## ☁️ GitHub Actions配置

### 1. 设置Secrets

在GitHub仓库 `Settings → Secrets and variables → Actions` 中添加:

| Secret Name | 说明 | 示例 |
|-------------|------|------|
| `SMTP_SERVER` | SMTP服务器 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP端口 | `465` |
| `SENDER_EMAIL` | 发件人邮箱 | `your_email@qq.com` |
| `SENDER_PASSWORD` | 邮箱授权码 | `xxxxxxxxxxxxxx` |
| `RECIPIENT_EMAILS` | 收件人邮箱 | `recipient@example.com` |

### 2. 工作流配置

文件: `.github/workflows/daily_market_report.yml`

**触发时间**:
- **自动**: 每个工作日 15:10(北京时间)
- **手动**: GitHub Actions页面手动触发

**执行流程**:
1. 拉取最新代码
2. 安装Python依赖
3. 创建临时邮箱配置
4. 生成并发送报告
5. 清理配置文件
6. 失败时上传日志

### 3. 手动触发

GitHub网页 → Actions → Daily Market Report → Run workflow

---

## 📊 报告数据来源

### 美股数据
- **纳斯达克指数**: ^IXIC
- **标普500指数**: ^GSPC
- **数据源**: yfinance

### 港股数据
- **恒生指数**: ^HSI
- **南向资金**: AKShare
- **数据源**: yfinance + AKShare

### A股数据
- **上证指数**: 000001.SS
- **深证成指**: 399001.SZ
- **北向资金**: AKShare (沪深股通)
- **融资融券**: AKShare (上交所)
- **市场宽度**: AKShare (新高新低统计)
- **数据源**: yfinance + AKShare

---

## 🎨 报告评分逻辑

### 综合评分(0-10分)

基础分: 5.0

**加分项**:
- MACD金叉: +0.5
- RSI < 30(超卖): +0.3
- KDJ金叉且K < 80: +0.4
- 北向资金流入(得分>70): +0.8
- 融资情绪乐观(得分>65): +0.5
- 市场宽度强劲(得分>70): +0.8

**减分项**:
- MACD死叉: -0.5
- RSI > 70(超买): -0.3
- KDJ死叉且K > 20: -0.4
- 北向资金流出(得分<30): -0.8
- 融资情绪低迷(得分<35): -0.5
- 市场宽度疲弱(得分<30): -0.8

### 评分对应建议

| 评分 | 趋势 | 建议仓位 | 操作策略 |
|------|------|----------|----------|
| 7.5+ | 强烈看多 | 80% | 逢低买入,持有优质标的 |
| 6.5-7.5 | 看多 | 70% | 持有为主,适当加仓 |
| 5.5-6.5 | 偏多 | 50% | 保持观望,等待更明确信号 |
| 4.5-5.5 | 中性 | 30% | 谨慎操作,控制风险 |
| 3.5-4.5 | 偏空 | 20% | 减仓为主,保留核心仓位 |
| <3.5 | 看空 | 10% | 空仓观望,等待趋势反转 |

---

## 🔍 故障排查

### 问题1: 邮件发送失败

**可能原因**:
- 邮箱授权码错误
- SMTP服务器/端口配置错误
- 网络连接问题
- 邮箱安全策略限制

**解决方法**:
```bash
# 测试SMTP连接
python -c "
import smtplib
smtp = smtplib.SMTP_SSL('smtp.qq.com', 465)
smtp.login('your_email@qq.com', 'your_auth_code')
print('连接成功')
smtp.quit()
"
```

### 问题2: 数据获取失败

**可能原因**:
- API限流
- 网络不稳定
- 数据源维护

**解决方法**:
- 检查日志确认具体错误
- 等待几分钟后重试
- 使用 `--verbose` 查看详细日志

### 问题3: GitHub Actions失败

**排查步骤**:
1. 检查Actions日志
2. 验证Secrets配置正确
3. 手动触发测试
4. 下载失败日志分析

---

## 📝 自定义配置

### 修改推送时间

编辑 `.github/workflows/daily_market_report.yml`:

```yaml
schedule:
  # 修改cron表达式
  # 格式: 分 时 日 月 周
  - cron: '10 7 * * 1-5'  # UTC 07:10 = 北京时间 15:10
```

### 修改评分逻辑

编辑 `position_analysis/daily_market_reporter.py`:

```python
def _calculate_composite_score(self, report: Dict) -> float:
    # 修改权重和阈值
    score = 5.0  # 基础分
    # ... 自定义逻辑
```

### 修改邮件模板

编辑 `position_analysis/email_notifier.py`:

```python
def _format_daily_report_html(self, report: Dict) -> str:
    # 修改HTML模板和样式
    # ... 自定义布局
```

---

## 📚 相关文档

- [GitHub Actions配置指南](./GitHub_Actions配置指南.md)
- [实施路线图](./IMPLEMENTATION_ROADMAP.md)
- [实施进度报告](./IMPLEMENTATION_PROGRESS_2025-10-12.md)

---

## ⚠️ 注意事项

1. **数据延迟**: 数据源可能有5-15分钟延迟
2. **API限制**: 频繁调用可能触发限流
3. **市场休市**: 休市日不会收到报告
4. **邮件安全**: 不要在代码中硬编码密码
5. **时区转换**: GitHub Actions使用UTC时间

---

## 🎁 最佳实践

1. **测试先行**: 先在本地测试成功再配置Actions
2. **日志保留**: 定期检查日志,发现问题及时处理
3. **备份配置**: 保留配置文件备份
4. **版本控制**: 使用git管理配置变更
5. **安全第一**: 使用Secrets管理敏感信息

---

**Made with ❤️ by Claude Code**
生成时间: 2025-10-12
版本: 1.0
