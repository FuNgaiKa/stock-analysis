# GitHub Actions 自动监控配置指南

本文档介绍如何使用 GitHub Actions 实现每日自动监控，无需本地电脑开机。

## 📋 前提条件

- ✅ 代码已推送到 GitHub（private 仓库也可以）
- ✅ 有 QQ 邮箱或其他邮箱的授权码

## 🚀 配置步骤

### 第一步：配置 GitHub Secrets

在你的 GitHub 仓库页面：

1. 点击 **Settings** (设置)
2. 左侧菜单找到 **Secrets and variables** → **Actions**
3. 点击 **New repository secret** 按钮

依次添加以下 6 个 Secrets：

| Secret 名称 | 值 | 说明 |
|------------|-----|------|
| `SMTP_SERVER` | `smtp.qq.com` | SMTP 服务器地址 |
| `SMTP_PORT` | `465` | SMTP 端口 |
| `SENDER_EMAIL` | `1264947688@qq.com` | 你的发件邮箱 |
| `SENDER_PASSWORD` | `swdfhpryoztsgfei` | 邮箱授权码 |
| `SENDER_NAME` | `股票监控系统` | 发件人名称 |
| `RECIPIENT_EMAIL` | `1264947688@qq.com` | 收件邮箱 |

**添加方法**：
1. 点击 **New repository secret**
2. **Name**: 输入 Secret 名称（如 `SMTP_SERVER`）
3. **Secret**: 输入对应的值（如 `smtp.qq.com`）
4. 点击 **Add secret**
5. 重复以上步骤，添加全部 6 个 Secrets

### 第二步：提交代码到 GitHub

```bash
# 添加 GitHub Actions 配置文件
git add .github/workflows/ma_deviation_monitor.yml

# 提交
git commit -m "feat: 添加 GitHub Actions 自动监控配置"

# 推送到 GitHub
git push
```

### 第三步：启用 GitHub Actions

1. 进入你的 GitHub 仓库页面
2. 点击顶部的 **Actions** 标签
3. 如果看到提示需要启用 Actions，点击 **I understand my workflows, go ahead and enable them**

### 第四步：手动测试运行

首次配置建议手动测试：

1. 进入 **Actions** 标签
2. 左侧选择 **均线偏离度监控** 工作流
3. 点击右上角 **Run workflow** 下拉菜单
4. 点击绿色的 **Run workflow** 按钮

等待 1-2 分钟，查看运行结果：
- ✅ 绿色对勾：运行成功，检查邮箱是否收到邮件
- ❌ 红色叉：运行失败，点击查看日志

## 📅 自动执行时间

配置完成后，系统会在以下时间自动运行：

- **每周一到周五** 下午 **15:10** (北京时间)
- A股收盘后 10 分钟，确保数据已更新

**为什么是这个时间？**
- A股收盘时间：15:00
- 留 10 分钟给数据源更新数据
- 确保监控的是当天收盘数据

## 🔍 查看运行历史

1. 进入 **Actions** 标签
2. 左侧选择 **均线偏离度监控**
3. 查看历史运行记录
4. 点击任意一次运行，可以查看详细日志

## ⚙️ 高级配置

### 修改执行时间

编辑 `.github/workflows/ma_deviation_monitor.yml`：

```yaml
on:
  schedule:
    # 修改这里的时间
    # 格式: 'MM HH * * 1-5'
    # MM: 分钟 (0-59)
    # HH: 小时 (0-23, UTC时间，需要减8小时)

    # 示例：
    # 北京时间 15:10 = UTC 07:10
    - cron: '10 7 * * 1-5'

    # 北京时间 16:10 (港股收盘后) = UTC 08:10
    # - cron: '10 8 * * 1-5'
```

**时区转换**：
- GitHub Actions 使用 UTC 时间
- 北京时间 = UTC + 8
- 例：北京时间 15:00 → UTC 07:00

### 同时监控A股和港股收盘

```yaml
on:
  schedule:
    # A股收盘后 (15:10)
    - cron: '10 7 * * 1-5'
    # 港股收盘后 (16:10)
    - cron: '10 8 * * 1-5'
```

### 增加重试次数

修改配置文件中的 `--retry` 参数：

```yaml
- name: 运行监控并发送邮件
  run: |
    python scripts/position_analysis/run_ma_deviation_monitor.py --email --quiet --retry 5
```

### 添加多个收件人

修改 Secret `RECIPIENT_EMAIL`：

```yaml
# 在 GitHub Secrets 中，RECIPIENT_EMAIL 填写：
1264947688@qq.com,another@example.com
```

或者直接修改 workflow 配置：

```yaml
- name: 创建邮箱配置文件
  run: |
    cat > email_config.yaml << EOF
    smtp:
      server: ${{ secrets.SMTP_SERVER }}
      port: ${{ secrets.SMTP_PORT }}

    sender:
      email: ${{ secrets.SENDER_EMAIL }}
      password: ${{ secrets.SENDER_PASSWORD }}
      name: ${{ secrets.SENDER_NAME }}

    recipients:
      - ${{ secrets.RECIPIENT_EMAIL }}
      - user2@example.com
      - user3@example.com

    send_no_alert_email: false
    EOF
```

## 🛠️ 故障排查

### 问题1：没有收到邮件

**检查步骤**：
1. 进入 **Actions** 查看运行是否成功（绿色对勾）
2. 点击运行记录，查看 **运行监控并发送邮件** 步骤的日志
3. 查找 `✅ 预警邮件发送成功` 或错误信息

**常见原因**：
- Secrets 配置错误（邮箱授权码不正确）
- 邮箱服务商限制（QQ邮箱每天发送限制）
- 今日无预警且未开启 `send_no_alert_email`

### 问题2：Actions 运行失败

1. 点击失败的运行记录
2. 展开红色的步骤
3. 查看错误日志

**常见错误**：
- `secrets.SMTP_SERVER not found` → Secrets 未配置
- `ModuleNotFoundError` → 依赖安装失败（检查 requirements.txt）
- `Connection refused` → 网络问题或 SMTP 服务器不可达

### 问题3：时间不对

GitHub Actions 使用 UTC 时间，需要手动转换：
- 北京时间 15:10 → cron: `'10 7 * * 1-5'`
- 北京时间 16:10 → cron: `'10 8 * * 1-5'`

## 💰 费用说明

GitHub Actions 对 private 仓库的免费额度：

- **免费额度**：每月 2000 分钟
- **本监控消耗**：每次约 1-2 分钟
- **每月执行次数**：约 20 次 (每月工作日)
- **实际消耗**：约 40 分钟/月

**结论**：完全在免费额度内，无需付费！

## 🔒 安全说明

### Secrets 安全性

- ✅ Secrets 在 GitHub 中加密存储
- ✅ 日志中不会显示 Secrets 内容
- ✅ 只有仓库管理员可以查看/修改 Secrets
- ⚠️ 建议定期更换邮箱授权码

### 私有仓库优势

- ✅ 代码不公开
- ✅ 配置不公开
- ✅ 只有你能看到 Actions 运行记录

## 📊 运行示例

成功运行的日志示例：

```
Run python scripts/position_analysis/run_ma_deviation_monitor.py --email --quiet --retry 5
INFO:__main__:开始监控 (第 1/3 次尝试)
INFO:position_analysis.ma_deviation_monitor:均线偏离度监控器初始化完成
INFO:position_analysis.ma_deviation_monitor:获取 上证指数 历史数据...
INFO:position_analysis.ma_deviation_monitor:上证指数 数据获取成功: 8497 条
...
INFO:__main__:发送预警邮件: 5 个信号
INFO:position_analysis.email_notifier:邮件发送成功
INFO:__main__:✅ 预警邮件发送成功
```

## 🎯 最佳实践

1. **首次配置后立即手动测试**，确保能收到邮件
2. **定期检查 Actions 运行记录**，确保没有失败
3. **每3-6个月更换邮箱授权码**，保障安全
4. **关注邮件内容**，及时调整投资策略

## 📚 相关文档

- [GitHub Actions 官方文档](https://docs.github.com/en/actions)
- [定时任务配置指南](./定时任务配置指南.md) - 本地 cron 方案
- [均线偏离度监控系统](./均线偏离度监控系统.md) - 系统说明

## ❓ 常见问题

### 执行时间相关

**Q: 会自动执行吗？几点执行？**
A: 会！每周一到周五下午 **15:10**（北京时间）自动执行。

**Q: 执行时间准确吗？**
A: GitHub Actions 调度可能有 **5-15分钟延迟**。设置15:10可能15:15-15:25才执行，但对股票监控来说完全够用。

**Q: 周末会执行吗？**
A: 不会，配置中使用 `1-5` 限定为周一到周五。

**Q: 国庆/春节等假期会执行吗？**
A: 会执行，因为 GitHub Actions 无法识别中国法定假期。但因为是假期，数据源不会更新，获取的还是最后一个交易日的数据。不影响使用。

**Q: 可以改成其他时间吗？**
A: 可以！修改 `.github/workflows/ma_deviation_monitor.yml` 中的 cron 表达式。

**Q: 可以一天执行两次吗（A股+港股收盘后各一次）？**
A: 可以！添加两个 cron 时间：
```yaml
schedule:
  - cron: '10 7 * * 1-5'  # 15:10 A股收盘后
  - cron: '10 8 * * 1-5'  # 16:10 港股收盘后
```

### 操作相关

**Q: 可以暂停吗？**
A: 可以，进入 Actions → 选择工作流 → 右上角 `...` → Disable workflow

**Q: 可以立即手动执行一次吗？**
A: 可以，进入 Actions → 选择工作流 → Run workflow

**Q: 如何查看运行历史？**
A: 进入仓库的 Actions 标签，选择"均线偏离度监控"工作流，查看历史记录。

### 技术细节

**Q: cron 表达式是什么意思？**
A: cron 是 Linux 定时任务的标准格式：
```
'10 7 * * 1-5'
 │  │ │ │ │
 │  │ │ │ └─ 周一到周五 (1=周一, 5=周五)
 │  │ │ └─── 每月
 │  │ └───── 每日
 │  └─────── 7点 (UTC时间)
 └────────── 10分
```

**Q: 为什么 cron 是 7 点，实际是 15:10？**
A: GitHub Actions 使用 **UTC 时间**（世界标准时间），北京时间 = UTC + 8 小时。
- UTC 07:10 = 北京时间 15:10

**Q: 虚拟机运行完会保留数据吗？**
A: 不会。每次运行都是全新的 Ubuntu 虚拟机，运行完立即销毁。数据每次都重新下载。

**Q: 为什么要安装 TA-Lib C 库？**
A: TA-Lib 是技术分析库，Python 包依赖于 C 库。Ubuntu 上需要先编译安装 C 库，才能安装 Python 包。

## ✅ 配置检查清单

配置完成后，请确认：

- [ ] 6 个 Secrets 已全部添加
- [ ] GitHub Actions 已启用
- [ ] 手动运行测试成功
- [ ] 收到测试邮件
- [ ] 检查邮件内容格式正常
- [ ] 了解每天执行时间 (15:10)
- [ ] 知道如何查看运行历史

全部完成后，系统将自动运行，无需干预！
