# 🚀 快速开始指南

**3分钟完成部署!无需前端、服务器、域名**

---

## 📋 你需要什么?

- ✅ GitHub账号
- ✅ Gmail邮箱(用于接收报告)
- ✅ 5分钟时间

**不需要**:
- ❌ 服务器
- ❌ 前端技术(Vue/React)
- ❌ Cloudflare/域名
- ❌ 复杂配置

---

## ⚡ 3步部署

### Step 1: 配置Gmail应用密码(2分钟)

1. 访问 https://myaccount.google.com/apppasswords
2. 登录你的Gmail
3. 选择"其他(自定义名称)" → 输入"股票分析"
4. 点击"生成"
5. **复制16位密码**(格式: xxxx xxxx xxxx xxxx)

> 💡 如果没有这个选项,需要先开启2步验证

### Step 2: 配置GitHub Secrets(1分钟)

1. 访问你的GitHub仓库: `https://github.com/你的用户名/stock-analysis`
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`,添加以下3个:

```
Name: MAIL_USERNAME
Secret: 你的Gmail地址 (例如: your_email@gmail.com)

Name: MAIL_PASSWORD
Secret: 刚才生成的16位密码 (例如: abcd efgh ijkl mnop)

Name: MAIL_TO
Secret: 接收报告的邮箱 (可以填你自己的Gmail)
```

### Step 3: 推送代码并测试(1分钟)

```bash
# 提交部署配置
git add .
git commit -m "chore: 添加GitHub Actions自动部署"
git push

# 查看Actions状态
# 访问: https://github.com/你的用户名/stock-analysis/actions
```

手动触发测试:
1. 点击 "美股市场分析定时任务"
2. 点击右上角 "Run workflow" → "Run workflow"
3. 等待3-5分钟
4. 查看你的邮箱,应该收到分析报告!

---

## ✅ 完成!

现在系统会:
- ⏰ **每天自动运行**: 美股收盘后2小时
  - UTC 22:00 = 北京时间次日06:00 = 美东18:00
- 📧 **自动发邮件**: 分析报告直接到你邮箱
- 💾 **自动保存**: GitHub上保存90天历史报告

---

## 📊 查看报告的3种方式

### 方式1: 邮箱接收(推荐)
打开Gmail → 查收"美股分析报告"

### 方式2: GitHub下载
1. 访问 `https://github.com/你的用户名/stock-analysis/actions`
2. 点击最近的运行记录
3. 滚动到底部 "Artifacts"
4. 下载 `us-market-analysis-xxx`

### 方式3: GitHub仓库查看(如果启用)
查看 `reports/us_market/` 目录

---

## 🎯 本地运行(可选)

不想等自动运行?可以立即本地测试:

```bash
# 进入项目目录
cd /Users/russ/PycharmProjects/stock-analysis

# Phase 1 基础分析
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX

# Phase 2 增强分析
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX --phase2

# Phase 3 深度分析(完整)
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX --phase3

# 多指数联合分析
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX NASDAQ NDX --phase3
```

---

## ⚙️ 自定义配置(可选)

### 修改运行时间

编辑 `.github/workflows/us_market_analysis.yml`:

```yaml
schedule:
  # 改为每天北京时间22:00 (UTC 14:00)
  - cron: '0 14 * * 1-5'

  # 或每周一次(周五收盘后)
  - cron: '0 22 * * 5'
```

### 修改分析指数

```yaml
python scripts/us_stock_analysis/run_us_analysis.py \
  --indices SPX NASDAQ NDX VIX DJI RUT \  # 添加更多指数
  --phase3 \
  --detail
```

### 修改相似度容差

```yaml
python scripts/us_stock_analysis/run_us_analysis.py \
  --indices SPX \
  --tolerance 0.03 \  # 改为±3%
  --phase3
```

---

## 📱 报告示例

邮件内容示例:

```
============================================================
                    美股市场综合分析报告
============================================================

分析时间: 2025-10-12 18:00:00
分析指数: 标普500, 纳斯达克综合, 纳斯达克100

────────────────────────────────────────────────────────────
  标普500 分析结果
────────────────────────────────────────────────────────────

📊 当前点位信息:
   最新价格: 6552.45
   涨跌幅: +0.52%
   数据日期: 2025-10-11
   相似时期: 23 个历史点位

🎯 市场环境识别 (Phase 2):
   环境类型: 牛市顶部
   RSI: 72.3
   距52周高点: -0.8%
   均线状态: 多头排列

💡 20日周期核心结论:
   上涨概率: 60.9% (上涨 14 次, 下跌 9 次)
   预期收益: +1.25% (中位数 +0.82%)
   收益区间: [-8.45%, +12.36%]
   置信度: 75.2%

   🎯 谨慎观望:建议轻仓观望(52%左右)
   ⚠️ 当前处于牛市顶部,建议谨慎,降低仓位

🔥 VIX恐慌指数分析:
   VIX当前值: 16.25 (正常区间)
   日变化: -0.35 (-2.11%)
   交易信号: 正常 - VIX在正常区间下沿(15-20)
   操作建议: 正常操作,可适度乐观

🔄 行业轮动分析:
   轮动模式: 进攻模式
   模式描述: 科技/金融/可选消费领涨,市场风险偏好高
   配置建议: 加配科技/金融,适度配置防守
   推荐行业: 科技, 金融, 可选消费

📊 成交量分析:
   成交量状态: 温和放量
   成交量是均量的1.2倍
   交易信号: 中性偏多 - 成交量配合尚可
```

---

## ❓ 常见问题

### Q: GitHub Actions免费吗?
**A**: 是的!免费账号每月2000分钟,本项目每次约3分钟,每天运行完全够用。

### Q: 为什么需要Gmail应用密码?
**A**: 为了安全!不能直接使用Gmail密码,必须用应用专用密码。

### Q: 可以用QQ邮箱/163邮箱吗?
**A**: 可以,但配置更复杂。Gmail最简单。

### Q: 报告会保存多久?
**A**: GitHub Artifacts保存90天,邮箱永久保存。

### Q: 可以修改报告格式吗?
**A**: 可以!修改 `scripts/us_stock_analysis/run_us_analysis.py` 的输出部分。

### Q: 运行失败了怎么办?
**A**:
1. 检查GitHub Secrets是否配置正确
2. 查看Actions运行日志
3. 提Issue: https://github.com/你的用户名/stock-analysis/issues

### Q: 需要Cloudflare吗?
**A**: **不需要!** 这是命令行工具,不是Web应用。

---

## 🎯 总结

**最适合后端开发者的方案**:
- ✅ 无需前端
- ✅ 无需服务器
- ✅ 完全免费
- ✅ 全自动运行
- ✅ 5分钟部署

**GitHub Actions = 你的免费服务器!**

---

## 📚 相关文档

- [完整部署指南](DEPLOYMENT_GUIDE.md) - 所有部署方案详解
- [美股分析系统文档](US_STOCK_README.md) - 系统使用说明
- [Phase 3完成总结](../scripts/us_stock_analysis/PHASE3_COMPLETION_SUMMARY.md) - 功能详解

---

**开始享受自动化分析吧!** 🚀

有问题随时提Issue或联系我!
