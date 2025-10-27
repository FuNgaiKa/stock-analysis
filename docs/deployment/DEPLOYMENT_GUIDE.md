# 📦 部署指南 - 美股分析系统

本项目是**Python数据分析工具**,不是Web应用。提供3种免费部署方案。

---

## 🌟 方案1: GitHub Actions自动化 (强烈推荐!)

**优点**: 完全免费、全自动、无需服务器
**适合**: 定期分析 + 邮件报告

### 1.1 快速开始(3步完成)

#### Step 1: 启用GitHub Actions

文件已创建: `.github/workflows/us_market_analysis.yml`

#### Step 2: 配置邮件通知(可选)

如果需要邮件发送分析报告:

1. **获取Gmail应用密码**
   - 访问 https://myaccount.google.com/apppasswords
   - 生成应用专用密码

2. **配置GitHub Secrets**
   ```
   GitHub仓库 → Settings → Secrets and variables → Actions → New repository secret

   添加3个secrets:
   - MAIL_USERNAME: 你的Gmail地址
   - MAIL_PASSWORD: Gmail应用密码
   - MAIL_TO: 收件人邮箱(可以是你自己)
   ```

#### Step 3: 提交代码并推送

```bash
git add .github/workflows/us_market_analysis.yml
git commit -m "chore: 添加GitHub Actions自动分析"
git push
```

### 1.2 验证配置

1. 访问 `https://github.com/你的用户名/stock-analysis/actions`
2. 点击 "美股市场分析定时任务"
3. 点击右上角 "Run workflow" 手动触发测试

### 1.3 运行时间

- **自动运行**: 每天美股收盘后2小时 (UTC 22:00)
  - 北京时间: 次日 06:00
  - 美东时间: 18:00
- **手动触发**: 随时在Actions页面手动运行

### 1.4 查看报告

**方式1: 下载Artifacts**
```
Actions → 选择运行记录 → Artifacts → 下载报告
```

**方式2: 邮件接收**(需配置邮件)
```
报告自动发送到你的邮箱
```

**方式3: GitHub查看**(如果启用了提交报告)
```
reports/us_market/report_20251012.txt
```

### 1.5 GitHub Actions配置详解

```yaml
# 定时任务
schedule:
  - cron: '0 22 * * 1-5'  # 周一到周五 UTC 22:00

# 分析命令
python scripts/us_stock_analysis/run_us_analysis.py \
  --indices SPX NASDAQ NDX \  # 分析的指数
  --phase3 \                   # 使用Phase 3深度分析
  --detail                     # 显示详细信息
```

### 1.6 自定义配置

**修改运行时间**:
```yaml
# 改为每天UTC 14:00 (北京时间22:00)
- cron: '0 14 * * 1-5'
```

**修改分析指数**:
```yaml
# 只分析标普500
--indices SPX

# 分析所有指数
--indices SPX NASDAQ NDX VIX DJI RUT
```

**修改分析模式**:
```yaml
# Phase 1 基础分析
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX

# Phase 2 增强分析
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX --phase2

# Phase 3 深度分析(完整)
python scripts/us_stock_analysis/run_us_analysis.py --indices SPX --phase3
```

### 1.7 GitHub Actions限额

- **免费额度**: 每月2000分钟
- **单次运行**: 约3-5分钟
- **每月可运行**: 约400-600次
- **每天运行1次**: 完全够用!

---

## 🖥️ 方案2: 本地运行 + 定时任务

**优点**: 最简单、无需配置
**适合**: 个人使用、电脑常开

### 2.1 macOS/Linux - crontab

```bash
# 编辑定时任务
crontab -e

# 添加以下行(每天18:00运行)
0 18 * * 1-5 cd /Users/russ/PycharmProjects/stock-analysis && /usr/bin/python3 scripts/us_stock_analysis/run_us_analysis.py --indices SPX --phase3 > /tmp/us_analysis.log 2>&1
```

### 2.2 Windows - 任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器: 每天 18:00
4. 操作: 启动程序
   - 程序: `python`
   - 参数: `scripts/us_stock_analysis/run_us_analysis.py --indices SPX --phase3`
   - 起始位置: `C:\path\to\stock-analysis`

### 2.3 Python脚本定时运行

创建 `auto_run.py`:

```python
import schedule
import time
import subprocess

def run_analysis():
    print(f"开始分析: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    subprocess.run([
        'python',
        'scripts/us_stock_analysis/run_us_analysis.py',
        '--indices', 'SPX', 'NASDAQ', 'NDX',
        '--phase3'
    ])

# 每天18:00运行
schedule.every().day.at("18:00").do(run_analysis)

print("定时任务已启动...")
while True:
    schedule.run_pending()
    time.sleep(60)
```

运行:
```bash
pip install schedule
python auto_run.py
```

---

## 🌐 方案3: Streamlit Cloud部署Web界面

**优点**: 有Web界面、随时访问
**缺点**: 需要改造代码、交互式使用

### 3.1 创建Streamlit应用

创建 `streamlit_app.py`:

```python
import streamlit as st
import sys
sys.path.append('.')

from position_analysis.us_market_analyzer import USMarketAnalyzer, US_INDICES

st.set_page_config(page_title="美股市场分析", page_icon="📊", layout="wide")

st.title("📊 美股市场分析系统")

# 侧边栏配置
st.sidebar.header("分析配置")
indices = st.sidebar.multiselect(
    "选择指数",
    options=list(US_INDICES.keys()),
    default=['SPX', 'NASDAQ', 'NDX']
)

phase = st.sidebar.radio(
    "分析模式",
    options=['Phase 1', 'Phase 2', 'Phase 3'],
    index=2
)

tolerance = st.sidebar.slider(
    "相似度容差(%)",
    min_value=1.0,
    max_value=10.0,
    value=5.0,
    step=0.5
) / 100

# 运行分析
if st.sidebar.button("🚀 开始分析", type="primary"):
    with st.spinner("分析中..."):
        analyzer = USMarketAnalyzer()

        use_phase2 = phase in ['Phase 2', 'Phase 3']
        use_phase3 = phase == 'Phase 3'

        result = analyzer.analyze_multiple_indices(
            indices=indices,
            tolerance=tolerance,
            use_phase2=use_phase2,
            use_phase3=use_phase3
        )

        # 显示结果
        st.success("✅ 分析完成!")

        for idx_code, analysis in result['individual_analysis'].items():
            st.subheader(f"{analysis['index_name']}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("当前价格", f"{analysis['current_price']:.2f}")
            with col2:
                st.metric("涨跌幅", f"{analysis['current_change_pct']:+.2f}%")
            with col3:
                st.metric("相似时期", f"{analysis.get('similar_periods_count', 0)}个")

            # 20日分析
            if 'period_analysis' in analysis and '20d' in analysis['period_analysis']:
                stats = analysis['period_analysis']['20d']

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("上涨概率", f"{stats['up_prob']:.1%}")
                with col2:
                    st.metric("平均收益", f"{stats['mean_return']:+.2%}")
                with col3:
                    st.metric("置信度", f"{stats.get('confidence', 0):.1%}")
                with col4:
                    if 'position_advice' in stats:
                        st.metric("建议仓位",
                                f"{stats['position_advice']['recommended_position']:.1%}")

st.sidebar.markdown("---")
st.sidebar.info("""
**使用说明**:
1. 选择要分析的指数
2. 选择分析模式
3. 点击"开始分析"
4. 查看分析结果
""")
```

### 3.2 部署到Streamlit Cloud

1. **创建requirements.txt**:
```txt
pandas>=2.0.0
numpy>=1.24.0
yfinance>=0.2.28
streamlit>=1.28.0
```

2. **推送代码到GitHub**:
```bash
git add streamlit_app.py requirements.txt
git commit -m "feat: 添加Streamlit Web界面"
git push
```

3. **部署**:
   - 访问 https://share.streamlit.io/
   - 用GitHub登录
   - New app → 选择你的仓库
   - Main file path: `streamlit_app.py`
   - 点击Deploy

4. **访问应用**:
```
https://你的用户名-stock-analysis.streamlit.app/
```

### 3.3 Streamlit优缺点

**优点**:
- ✅ 完全免费
- ✅ 有Web界面,随时访问
- ✅ 支持交互式配置

**缺点**:
- ❌ 不是自动运行(需要手动点击)
- ❌ 共享资源,可能较慢
- ❌ 休眠后首次加载慢

---

## 📊 方案对比总结

| 方案 | 成本 | 自动化 | 易用性 | 推荐度 |
|------|------|--------|--------|--------|
| **GitHub Actions** | 免费 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **本地定时任务** | 免费 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Streamlit Cloud** | 免费 | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

---

## 🎯 推荐选择

### 场景1: 定期自动分析 + 邮件报告
**推荐**: GitHub Actions
**原因**: 全自动、免费、无需服务器

### 场景2: 个人使用、电脑常开
**推荐**: 本地定时任务
**原因**: 最简单、最快

### 场景3: 想要Web界面
**推荐**: Streamlit Cloud
**原因**: 有界面、随时访问

---

## 🚀 快速开始(推荐GitHub Actions)

```bash
# 1. 确保代码已推送
git add .
git commit -m "feat: 添加自动部署配置"
git push

# 2. 配置GitHub Secrets(如需邮件)
# GitHub → Settings → Secrets → New secret
# - MAIL_USERNAME
# - MAIL_PASSWORD
# - MAIL_TO

# 3. 手动触发测试
# GitHub → Actions → 美股市场分析定时任务 → Run workflow

# 4. 完成! 每天自动运行
```

---

## 🔧 高级配置

### 多时段运行

```yaml
schedule:
  # 美股开盘前
  - cron: '30 13 * * 1-5'  # UTC 13:30 = 美东 09:30
  # 美股收盘后
  - cron: '0 22 * * 1-5'   # UTC 22:00 = 美东 18:00
```

### 生成HTML报告

修改workflow:
```yaml
- name: 生成HTML报告
  run: |
    python -c "
    from position_analysis.us_market_analyzer import USMarketAnalyzer
    import json
    analyzer = USMarketAnalyzer()
    result = analyzer.analyze_multiple_indices(
        indices=['SPX', 'NASDAQ', 'NDX'],
        use_phase3=True
    )
    # 生成HTML
    with open('report.html', 'w') as f:
        f.write('<html>...')  # 使用你的HTML模板
    "
```

### 发送到Discord/Slack

使用webhook:
```yaml
- name: 发送Discord通知
  run: |
    curl -H "Content-Type: application/json" \
      -d '{"content":"美股分析完成!"}' \
      ${{ secrets.DISCORD_WEBHOOK_URL }}
```

---

## ❓ 常见问题

### Q1: GitHub Actions会消耗我的配额吗?
A: 免费账号有2000分钟/月,本项目单次约3分钟,每天运行完全够用。

### Q2: yfinance会被限流吗?
A: GitHub Actions的IP每次都不同,基本不会被限流。

### Q3: 如何查看历史报告?
A: Actions → Artifacts,保留90天。

### Q4: 可以同时用多种方案吗?
A: 可以!比如GitHub Actions定期运行+本地手动运行。

### Q5: 需要Cloudflare吗?
A: **不需要**!Cloudflare是用于Web应用的,你的项目是命令行工具。

---

## 📝 总结

**最简单免费方案**: GitHub Actions ⭐⭐⭐⭐⭐

3步完成:
1. ✅ 文件已创建 `.github/workflows/us_market_analysis.yml`
2. ✅ `git push` 推送代码
3. ✅ GitHub Actions自动运行

**无需**:
- ❌ 服务器
- ❌ Cloudflare
- ❌ 域名
- ❌ 复杂配置

**完全免费 + 全自动!** 🎉

---

需要帮助? 提Issue: https://github.com/你的用户名/stock-analysis/issues
