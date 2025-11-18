#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场标的洞察报告邮件发送模块
Market Targets Insight Email Notifier
"""

import smtplib
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Dict
from datetime import datetime
import logging
from pathlib import Path


class UnifiedEmailNotifier:
    """市场标的洞察报告邮件通知器"""

    def __init__(self, config_path: str = None):
        """
        初始化邮件通知器

        Args:
            config_path: 配置文件路径,默认为项目根目录的 config/email_config.yaml
        """
        # 先初始化logger
        self.logger = logging.getLogger(__name__)

        if config_path is None:
            # __file__ = .../stock-analysis/russ_trading/notifiers/unified_email_notifier.py
            # parent = .../stock-analysis/russ_trading/notifiers
            # parent.parent = .../stock-analysis/russ_trading
            # parent.parent.parent = .../stock-analysis (项目根目录)
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / 'config' / 'email_config.yaml'

        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Path) -> Dict:
        """加载邮箱配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            self.logger.error(f"配置文件未找到: {config_path}")
            self.logger.info("请参考 config/email_config.yaml.template 创建配置文件")
            raise
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            raise

    def _filter_email_report(self, markdown_content: str, report: Dict) -> str:
        """
        精简邮件报告 - 只保留看多/强烈看多/中性偏多标的的详细分析

        参考: scripts/filter_report_targets.py

        Args:
            markdown_content: 完整的Markdown报告
            report: 报告数据字典

        Returns:
            精简后的Markdown报告
        """
        import re

        # 从 report 数据中动态提取看多标的
        KEEP_TARGETS = set()
        assets_data = report.get('assets', {})

        for asset_key, asset_data in assets_data.items():
            if 'error' in asset_data:
                continue

            judgment = asset_data.get('comprehensive_judgment', {})
            direction = judgment.get('direction', '')

            # 只保留看多/强烈看多/中性偏多
            if any(x in direction for x in ['强烈看多', '看多', '中性偏多']):
                asset_name = asset_data.get('asset_name', '')
                if asset_name:
                    KEEP_TARGETS.add(asset_name)

        self.logger.info(f"📋 需要保留的标的: {', '.join(sorted(KEEP_TARGETS))} (共{len(KEEP_TARGETS)}个)")

        lines = markdown_content.split('\n')

        # 1. 找到详细分析的起始位置
        detail_start = None
        for i, line in enumerate(lines):
            # 支持一级标题或二级标题
            if ("综合资产分析报告" in line or
                "## 📈 详细资产分析" in line or
                line.strip() == "## 四大科技指数" or
                "# 综合资产分析报告" in line):
                detail_start = i
                break

        if detail_start is None:
            # 未找到详细分析章节,返回原内容
            self.logger.warning("⚠️ 未找到详细分析章节,保留完整报告")
            return markdown_content

        # 2. 找到详细分析的结束位置
        detail_end = None
        for i in range(detail_start, len(lines)):
            if ("## 📖 【投资纪律】" in lines[i] or
                "## 📊 投资纪律" in lines[i] or
                lines[i].strip() == "## 投资纪律"):
                detail_end = i
                break

        if detail_end is None:
            detail_end = len(lines)

        self.logger.info(f"📍 详细分析部分: 第{detail_start+1}行 到 第{detail_end}行")

        # 3. 处理详细分析部分 - 只保留指定标的
        detail_lines = lines[detail_start:detail_end]
        filtered_detail = []

        in_target_section = False
        current_target = None

        for i, line in enumerate(detail_lines):
            # 检测标的章节 (## CATEGORY: 标的名称 或 ### 标的名称)
            is_target_header = False
            if line.startswith("## ") and ":" in line:
                # ## CHEMICAL: A股化工 格式
                is_target_header = True
                target_name = line.split(":", 1)[1].strip() if ":" in line else line.replace("##", "").strip()
            elif line.startswith("### ") and not any(x in line for x in [
                "📈", "💰", "⚠️", "🎯", "📝", "📉", "💎", "📋",
                "✅", "⚖️", "⚪", "🔴", "当前", "综合", "历史", "技术",
                "资金", "风险", "成交", "恐慌", "筹码"
            ]):
                # ### 标的名称 格式
                is_target_header = True
                target_name = line.replace("###", "").strip()

            if is_target_header:
                # 这是一个标的章节
                target_base = target_name.split("(")[0].strip()

                # 检查是否需要保留
                should_keep = any(keep in target_name or keep in target_base for keep in KEEP_TARGETS)

                if should_keep:
                    current_target = target_name
                    in_target_section = True
                    filtered_detail.append(line)
                    self.logger.info(f"  ✅ 保留: {target_name}")
                else:
                    current_target = target_name
                    in_target_section = False
                    self.logger.info(f"  🗑️  删除: {target_name}")

            # 检测一级章节 (#), 表示新的大章节
            elif line.startswith("# ") and not line.startswith("##"):
                in_target_section = False
                filtered_detail.append(line)

            # 如果在保留的标的章节中,保留所有内容
            elif in_target_section:
                filtered_detail.append(line)
            # 非标的章节的内容也保留(如分析说明、表格等)
            elif not is_target_header:
                filtered_detail.append(line)

        # 4. 修改章节标题
        for i, line in enumerate(filtered_detail):
            if ("详细资产分析" in line or
                "综合资产分析报告" in line or
                line.strip() == "## 四大科技指数"):
                # 将一级标题改为二级标题
                if line.startswith("# "):
                    filtered_detail[i] = "## 📈 看多标的详细分析 (精简版)"
                else:
                    filtered_detail[i] = "## 📈 看多标的详细分析 (精简版)"
                filtered_detail.insert(i+1, "")
                filtered_detail.insert(i+2, "**说明**: 仅保留看多/强烈看多/中性偏多标的的详细分析,其他标的已省略。如需查看完整报告,请访问本地生成的Markdown文件。")
                filtered_detail.insert(i+3, "")
                break

        # 5. 重新组合内容
        result_lines = lines[:detail_start] + filtered_detail + lines[detail_end:]
        result_content = '\n'.join(result_lines)

        # 统计信息
        original_lines = len(lines)
        filtered_lines = len(result_lines)
        saved_lines = original_lines - filtered_lines
        saved_pct = saved_lines / original_lines * 100 if original_lines > 0 else 0

        self.logger.info(f"📊 报告精简统计: 原始{original_lines}行 → 精简后{filtered_lines}行, 减少{saved_lines}行 ({saved_pct:.1f}%)")

        return result_content

    def _markdown_to_html(self, markdown_text: str) -> str:
        """
        将Markdown转换为带样式的HTML邮件

        Args:
            markdown_text: Markdown格式文本

        Returns:
            HTML格式邮件内容
        """
        try:
            import markdown
        except ImportError:
            self.logger.error("❌ 缺少markdown库,请安装: pip install markdown")
            # 降级为简单的纯文本转HTML
            return f"<html><body><pre>{markdown_text}</pre></body></html>"

        # Markdown → HTML
        html_body = markdown.markdown(
            markdown_text,
            extensions=[
                'tables',           # 支持表格
                'fenced_code',      # 支持代码块
                'nl2br',            # 换行转<br>
                'sane_lists'        # 更好的列表支持
            ]
        )

        # 包裹邮件样式
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* 基础样式 */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Arial, "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}

        /* 内容容器 */
        .email-content {{
            max-width: 900px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        /* 标题样式 */
        h1 {{
            color: #1a1a1a;
            font-size: 28px;
            margin-bottom: 10px;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}

        h2 {{
            color: #2c3e50;
            font-size: 22px;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #4CAF50;
            padding-left: 12px;
        }}

        h3 {{
            color: #34495e;
            font-size: 18px;
            margin-top: 20px;
            margin-bottom: 10px;
        }}

        /* 表格样式 */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        th {{
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #45a049;
        }}

        td {{
            padding: 10px 8px;
            border: 1px solid #ddd;
        }}

        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}

        tr:hover {{
            background-color: #f1f1f1;
        }}

        /* 列表样式 */
        ul, ol {{
            margin: 10px 0;
            padding-left: 25px;
        }}

        li {{
            margin: 5px 0;
        }}

        /* 代码样式 */
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', Consolas, monospace;
            font-size: 0.9em;
            color: #e83e8c;
        }}

        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border: 1px solid #ddd;
        }}

        pre code {{
            background-color: transparent;
            padding: 0;
            color: #333;
        }}

        /* 分隔线 */
        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}

        /* 强调文本 */
        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}

        em {{
            color: #7f8c8d;
        }}

        /* 链接样式 */
        a {{
            color: #4CAF50;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        /* 引用块 */
        blockquote {{
            border-left: 4px solid #4CAF50;
            padding-left: 15px;
            margin: 15px 0;
            color: #555;
            font-style: italic;
            background-color: #f9f9f9;
            padding: 10px 15px;
            border-radius: 0 5px 5px 0;
        }}

        /* 页脚 */
        .email-footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}

        /* 移动端适配 */
        @media only screen and (max-width: 600px) {{
            body {{
                padding: 10px;
            }}

            .email-content {{
                padding: 15px;
            }}

            h1 {{
                font-size: 24px;
            }}

            h2 {{
                font-size: 20px;
            }}

            h3 {{
                font-size: 16px;
            }}

            table {{
                font-size: 14px;
            }}

            th, td {{
                padding: 8px 4px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-content">
        {html_body}

        <div class="email-footer">
            <p>🤖 Claude Code 量化分析系统 | 自动生成</p>
            <p style="font-size: 12px; color: #bbb;">
                本报告由AI驱动的量化分析系统自动生成,仅供参考,不构成投资建议
            </p>
        </div>
    </div>
</body>
</html>
    """

        return html

    def send_unified_report(self, report: Dict, markdown_content: str) -> bool:
        """
        发送市场标的洞察报告邮件

        Args:
            report: 报告数据字典
            markdown_content: Markdown格式报告(完整内容)

        Returns:
            是否发送成功
        """
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))

        # 1. 精简报告内容 (只保留看多标的)
        filtered_markdown = self._filter_email_report(markdown_content, report)

        # 2. Markdown转HTML
        html_content = self._markdown_to_html(filtered_markdown)

        # 3. 计算整体趋势 (用于邮件主题)
        assets_data = report.get('assets', {})
        bullish_count = 0
        bearish_count = 0
        total_count = 0

        for asset_data in assets_data.values():
            if 'error' in asset_data:
                continue
            total_count += 1
            judgment = asset_data.get('comprehensive_judgment', {})
            direction = judgment.get('direction', '')
            if '看多' in direction:
                bullish_count += 1
            elif '看空' in direction:
                bearish_count += 1

        # 4. 确定邮件主题
        if bullish_count >= total_count * 0.6:
            subject = f"📈 【偏多】市场洞察报告 - {bullish_count}个看多"
        elif bearish_count >= total_count * 0.6:
            subject = f"📉 【偏空】市场洞察报告 - {bearish_count}个看空"
        else:
            subject = f"➡️ 【中性】市场洞察报告 - 多空分化"

        subject += f" ({total_count}个标的, {date})"

        # 5. 从配置文件获取收件人列表
        recipients = self.config.get('recipients', ['your_email@example.com'])

        # 6. 发送邮件 - 给每个收件人单独发送一封
        success_count = 0
        failed_recipients = []

        for recipient in recipients:
            try:
                # 每个收件人建立独立的SMTP连接
                smtp = smtplib.SMTP_SSL(
                    self.config['smtp']['server'],
                    self.config['smtp']['port']
                )
                smtp.login(
                    self.config['sender']['email'],
                    self.config['sender']['password']
                )

                # 创建邮件
                message = MIMEMultipart('alternative')
                message['From'] = self.config['sender']['email']
                message['To'] = recipient
                message['Subject'] = Header(subject, 'utf-8')
                message['X-Priority'] = '3'

                # 添加纯文本版本(简要摘要,用于不支持HTML的邮件客户端)
                text_summary = f"""
市场洞察报告 ({date})

本次分析了 {total_count} 个标的:
- 看多: {bullish_count} 个
- 看空: {bearish_count} 个
- 中性: {total_count - bullish_count - bearish_count} 个

请使用支持HTML的邮件客户端查看完整报告。

---
🤖 Claude Code 量化分析系统
            """
                text_part = MIMEText(text_summary.strip(), 'plain', 'utf-8')

                # 添加HTML版本(完整报告)
                html_part = MIMEText(html_content, 'html', 'utf-8')

                # 先添加纯文本,再添加HTML(邮件客户端优先显示HTML)
                message.attach(text_part)
                message.attach(html_part)

                # 发送给当前收件人
                smtp.sendmail(
                    self.config['sender']['email'],
                    [recipient],
                    message.as_string()
                )

                smtp.quit()
                success_count += 1
                self.logger.info(f"✅ 邮件发送成功: {recipient}")

            except Exception as e:
                failed_recipients.append(recipient)
                self.logger.error(f"❌ 发送到 {recipient} 失败: {str(e)}")
                try:
                    smtp.quit()
                except:
                    pass

        # 7. 汇总结果
        if success_count == len(recipients):
            self.logger.info(f"🎉 所有邮件发送成功(共{success_count}个收件人): {subject}")
            return True
        elif success_count > 0:
            self.logger.warning(f"⚠️ 部分邮件发送成功({success_count}/{len(recipients)}),失败的收件人: {', '.join(failed_recipients)}")
            return True
        else:
            self.logger.error(f"❌ 所有邮件发送失败")
            return False

    def _format_html_content(self, report: Dict) -> str:
        """格式化HTML邮件内容,对齐markdown报告格式"""
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))
        assets_data = report.get('assets', {})

        # 计算整体趋势
        bullish_count = 0
        bearish_count = 0
        total_count = 0

        for asset_data in assets_data.values():
            if 'error' in asset_data:
                continue
            total_count += 1
            judgment = asset_data.get('comprehensive_judgment', {})
            direction = judgment.get('direction', '')
            if '看多' in direction:
                bullish_count += 1
            elif '看空' in direction:
                bearish_count += 1

        # 选择颜色
        if bullish_count >= total_count * 0.6:
            header_color = "#28a745"  # 绿色
            trend_icon = "📈"
            trend_text = "偏多"
        elif bearish_count >= total_count * 0.6:
            header_color = "#dc3545"  # 红色
            trend_icon = "📉"
            trend_text = "偏空"
        else:
            header_color = "#6c757d"  # 灰色
            trend_icon = "➡️"
            trend_text = "中性"

        html = f"""
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: Arial, 'Microsoft YaHei', sans-serif;
        line-height: 1.6;
        margin: 0;
        padding: 0;
        background-color: #f5f5f5;
    }}
    .container {{
        max-width: 1000px;
        margin: 20px auto;
        background-color: white;
    }}
    .header {{
        background: linear-gradient(135deg, {header_color} 0%, {header_color}cc 100%);
        color: white;
        padding: 30px 20px;
        text-align: center;
    }}
    .header h1 {{
        margin: 0;
        font-size: 28px;
    }}
    .header .subtitle {{
        font-size: 16px;
        margin-top: 10px;
        opacity: 0.9;
    }}
    .overview {{
        background-color: #f8f9fa;
        padding: 20px 25px;
        border-bottom: 2px solid #dee2e6;
    }}
    .overview h2 {{
        font-size: 20px;
        color: {header_color};
        margin: 0 0 15px 0;
    }}
    .overview-stats {{
        display: flex;
        gap: 30px;
        font-size: 14px;
    }}
    .stat-item {{
        color: #495057;
    }}
    .stat-item strong {{
        color: #212529;
    }}
    .summary-table {{
        padding: 25px;
        background-color: white;
    }}
    .summary-table h2 {{
        font-size: 20px;
        color: {header_color};
        margin: 0 0 15px 0;
        border-left: 4px solid {header_color};
        padding-left: 12px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        margin-top: 15px;
    }}
    th {{
        background-color: {header_color};
        color: white;
        padding: 12px 8px;
        text-align: left;
        font-weight: 600;
    }}
    td {{
        padding: 10px 8px;
        border-bottom: 1px solid #e9ecef;
    }}
    tr:hover {{
        background-color: #f8f9fa;
    }}
    .positive {{ color: #28a745; font-weight: bold; }}
    .negative {{ color: #dc3545; font-weight: bold; }}
    .section {{
        padding: 25px;
        border-bottom: 1px solid #e0e0e0;
    }}
    .section-title {{
        font-size: 20px;
        font-weight: bold;
        color: #333;
        margin-bottom: 20px;
        border-left: 4px solid {header_color};
        padding-left: 12px;
    }}
    .subsection-title {{
        font-size: 16px;
        font-weight: bold;
        color: {header_color};
        margin: 15px 0 10px 0;
    }}
    .info-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin: 10px 0;
    }}
    .info-item {{
        font-size: 14px;
        color: #495057;
    }}
    .info-item strong {{
        color: #212529;
    }}
    .strategies {{
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 12px 15px;
        margin: 10px 0;
        border-radius: 4px;
    }}
    .strategies ul {{
        margin: 5px 0;
        padding-left: 20px;
    }}
    .strategies li {{
        margin: 3px 0;
    }}
    .tech-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        margin: 10px 0;
    }}
    .tech-item {{
        font-size: 13px;
        padding: 8px;
        background-color: #f8f9fa;
        border-radius: 4px;
        text-align: center;
    }}
    .footer {{
        background-color: #343a40;
        color: white;
        padding: 20px;
        text-align: center;
        font-size: 12px;
    }}
    .risk-low {{ color: #28a745; }}
    .risk-medium {{ color: #ffc107; }}
    .risk-high {{ color: #dc3545; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>{trend_icon} 市场标的洞察报告</h1>
        <div class="subtitle">指数 + 板块 + 个股 全面分析</div>
        <div class="subtitle">整体趋势: {trend_text} | 分析标的: {total_count}个 | {date}</div>
    </div>

    <div class="overview">
        <h2>📋 分析概览</h2>
        <div class="overview-stats">
            <div class="stat-item"><strong>总资产数:</strong> {total_count}</div>
            <div class="stat-item"><strong>成功分析:</strong> {len([d for d in assets_data.values() if 'error' not in d])}</div>
            <div class="stat-item"><strong>看多:</strong> <span class="positive">{bullish_count}</span></div>
            <div class="stat-item"><strong>看空:</strong> <span class="negative">{bearish_count}</span></div>
        </div>
    </div>

    <div class="summary-table">
        <h2>📊 标的汇总</h2>
        {self._generate_summary_table_html(report)}
    </div>
"""

        # 按类别渲染资产详情
        html += self._render_assets_by_category(assets_data)

        html += f"""
    <div class="footer">
        <p>📊 Claude Code 量化分析系统 | 市场标的洞察专项分析</p>
        <p>分析维度: 11大维度全面覆盖</p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>本邮件由系统自动生成,请勿直接回复</p>
    </div>
</div>
</body>
</html>
"""
        return html

    def _generate_summary_table_html(self, report: Dict) -> str:
        """生成汇总表格HTML"""
        assets_data = report.get('assets', {})

        rows = []
        for asset_key, data in assets_data.items():
            if 'error' in data:
                continue

            # 获取资产名称
            asset_name = data.get('asset_name') or data.get('sector_name', asset_key)

            # 获取历史分析数据
            hist = data.get('historical_analysis', {})
            current_price = hist.get('current_price', 0)
            change_pct = hist.get('current_change_pct', 0)
            change_class = 'positive' if change_pct >= 0 else 'negative'
            change_emoji = "📈" if change_pct >= 0 else "📉"

            # 综合判断
            judgment = data.get('comprehensive_judgment', {})
            direction = judgment.get('direction', 'N/A')
            position = judgment.get('recommended_position', 'N/A')

            # 20日上涨概率
            stats_20d = hist.get('20d', {})
            up_prob_20d = stats_20d.get('up_prob', 0)
            prob_class = 'positive' if up_prob_20d > 0.5 else 'negative'

            # 风险等级
            risk = data.get('risk_assessment', {})
            risk_level = risk.get('risk_level', 'N/A')
            if '低风险' in risk_level or '低风险🟢' in risk_level:
                risk_class = 'risk-low'
                risk_emoji = '✅'
            elif '中风险' in risk_level:
                risk_class = 'risk-medium'
                risk_emoji = '⚠️'
            else:
                risk_class = 'risk-high'
                risk_emoji = '🔴'

            # 持有建议 - 从 strategies 中提取包含"持有"的建议
            strategies = judgment.get('strategies', [])
            hold_suggestion = '-'
            for strategy in strategies:
                # 匹配包含"持有"关键词的建议
                if '持有' in strategy:
                    hold_suggestion = strategy
                    break

            rows.append(f"""
            <tr>
                <td><strong>{asset_name}</strong></td>
                <td>{current_price:.2f}</td>
                <td class="{change_class}">{change_pct:+.2f}% {change_emoji}</td>
                <td>{direction}</td>
                <td>{position}</td>
                <td class="{prob_class}">{up_prob_20d:.1%}</td>
                <td class="{risk_class}">{risk_emoji} {risk_level}</td>
                <td>{hold_suggestion}</td>
            </tr>
            """)

        table_html = f"""
        <table>
            <thead>
                <tr>
                    <th>标的名称</th>
                    <th>当前价格</th>
                    <th>涨跌幅</th>
                    <th>方向判断</th>
                    <th>建议仓位</th>
                    <th>20日上涨概率</th>
                    <th>风险等级</th>
                    <th>持有建议</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
        return table_html

    def _render_assets_by_category(self, assets_data: Dict) -> str:
        """按类别渲染资产详情"""
        from russ_trading.config.unified_config import UNIFIED_ASSETS

        # 按类别分组
        categories = {}
        for asset_key, data in assets_data.items():
            if 'error' in data:
                continue

            config = UNIFIED_ASSETS.get(asset_key, {})
            category = config.get('category', 'other')

            if category not in categories:
                categories[category] = []
            categories[category].append((asset_key, data, config))

        html_parts = []

        # 类别名称映射
        category_names = {
            'tech_index': '🚀 四大科技指数',
            'broad_index': '📊 宽基指数',
            'commodity': '💰 大宗商品',
            'crypto': '₿ 加密货币',
            'healthcare': '🏥 医疗健康',
            'energy': '🔋 能源电池',
            'chemical': '🧪 化工',
            'coal': '⛏️ 煤炭',
            'consumer': '🍷 消费',
            'finance': '💼 金融',
            'media': '🎮 传媒游戏',
            'tech': '💻 科技',
            'materials': '🏭 原材料',
            'manufacturing': '🏗️ 制造业'
        }

        for category, assets in categories.items():
            category_name = category_names.get(category, category.upper())

            html_parts.append(f"""
    <div class="section">
        <div class="section-title">{category_name}</div>
""")

            for asset_key, data, config in assets:
                html_parts.append(self._render_single_asset(asset_key, data, config))

            html_parts.append("    </div>")

        return '\n'.join(html_parts)

    def _render_single_asset(self, asset_key: str, data: Dict, config: Dict) -> str:
        """渲染单个资产详情"""
        asset_name = data.get('asset_name') or data.get('sector_name', config.get('name', asset_key))

        html = f"""
        <div style="background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #dee2e6;">
            <h3 style="margin: 0 0 15px 0; color: #495057; font-size: 18px;">{asset_name}</h3>
"""

        # 1. 当前点位
        hist = data.get('historical_analysis', {})
        if hist and 'current_price' in hist:
            current_price = hist.get('current_price', 0)
            change_pct = hist.get('current_change_pct', 0)
            change_class = 'positive' if change_pct >= 0 else 'negative'
            change_emoji = "📈" if change_pct >= 0 else "📉"

            html += f"""
            <div class="subsection-title">📍 当前点位</div>
            <div class="info-grid">
                <div class="info-item"><strong>最新价格:</strong> {current_price:.2f}</div>
                <div class="info-item"><strong>涨跌幅:</strong> <span class="{change_class}">{change_pct:+.2f}% {change_emoji}</span></div>
            </div>
"""

        # 2. 综合判断
        judgment = data.get('comprehensive_judgment', {})
        if judgment:
            direction = judgment.get('direction', 'N/A')
            position = judgment.get('recommended_position', 'N/A')
            strategies = judgment.get('strategies', [])

            html += f"""
            <div class="subsection-title">💡 综合判断</div>
            <div class="info-grid">
                <div class="info-item"><strong>方向判断:</strong> {direction}</div>
                <div class="info-item"><strong>建议仓位:</strong> {position}</div>
            </div>
"""

            if strategies:
                html += """
            <div class="strategies">
                <strong>操作策略:</strong>
                <ul>
"""
                for strategy in strategies[:5]:  # 最多显示5条
                    html += f"                    <li>{strategy}</li>\n"
                html += """
                </ul>
            </div>
"""

        # 3. 历史点位分析
        if hist and '20d' in hist:
            stats_20d = hist.get('20d', {})
            up_prob = stats_20d.get('up_prob', 0)
            mean_return = stats_20d.get('mean_return', 0)
            prob_class = 'positive' if up_prob > 0.5 else 'negative'
            return_class = 'positive' if mean_return > 0 else 'negative'

            html += f"""
            <div class="subsection-title">📈 历史点位分析</div>
            <div class="info-grid">
                <div class="info-item"><strong>相似点位:</strong> {hist.get('similar_periods_count', 0)} 个</div>
                <div class="info-item"><strong>20日上涨概率:</strong> <span class="{prob_class}">{up_prob:.1%}</span></div>
                <div class="info-item"><strong>平均收益:</strong> <span class="{return_class}">{mean_return:+.2%}</span></div>
                <div class="info-item"><strong>置信度:</strong> {stats_20d.get('confidence', 0):.1%}</div>
            </div>
"""

        # 4. 技术面分析
        tech = data.get('technical_analysis', {})
        if tech and 'error' not in tech:
            tech_items = []

            if 'macd' in tech:
                macd_status = '✅ 金叉' if tech['macd']['status'] == 'golden_cross' else '🔴 死叉'
                tech_items.append(f"<div class='tech-item'><strong>MACD</strong><br>{macd_status}</div>")

            if 'rsi' in tech:
                rsi_val = tech['rsi']['value']
                rsi_status = {'overbought': '⚠️ 超买', 'oversold': '✅ 超卖', 'normal': '😊 正常'}.get(tech['rsi']['status'], '')
                tech_items.append(f"<div class='tech-item'><strong>RSI</strong><br>{rsi_val:.1f}<br>{rsi_status}</div>")

            if 'kdj' in tech:
                kdj = tech['kdj']
                kdj_signal = '✅' if kdj['signal'] == 'golden_cross' else '🔴'
                tech_items.append(f"<div class='tech-item'><strong>KDJ</strong><br>K={kdj['k']:.1f}<br>{kdj_signal}</div>")

            if 'boll' in tech:
                boll = tech['boll']
                boll_pos = boll['position'] * 100
                tech_items.append(f"<div class='tech-item'><strong>布林带</strong><br>{boll_pos:.0f}%</div>")

            if 'dmi_adx' in tech:
                dmi = tech['dmi_adx']
                direction_emoji = '📈' if dmi['direction'] == 'bullish' else '📉'
                tech_items.append(f"<div class='tech-item'><strong>ADX</strong><br>{dmi['adx']:.1f}<br>{direction_emoji}</div>")

            if tech_items:
                html += f"""
            <div class="subsection-title">🔧 技术面分析</div>
            <div class="tech-grid">
                {''.join(tech_items)}
            </div>
"""

        # 5. 风险评估
        risk = data.get('risk_assessment', {})
        if risk:
            risk_score = risk.get('risk_score', 0)
            risk_level = risk.get('risk_level', 'N/A')
            risk_factors = risk.get('risk_factors', [])

            if '低风险' in risk_level or '低风险🟢' in risk_level:
                risk_class = 'risk-low'
                risk_emoji = '✅'
            elif '中风险' in risk_level:
                risk_class = 'risk-medium'
                risk_emoji = '⚠️'
            else:
                risk_class = 'risk-high'
                risk_emoji = '🔴'

            html += f"""
            <div class="subsection-title">⚠️ 风险评估</div>
            <div class="info-item">
                <strong>综合风险:</strong> {risk_score:.2f}
                <span class="{risk_class}">{risk_emoji} {risk_level}</span>
            </div>
"""

            if risk_factors:
                html += "            <div class='info-item' style='margin-top: 5px;'><strong>风险因素:</strong> "
                html += ", ".join(risk_factors[:3])  # 最多显示3条
                html += "</div>\n"

        html += "        </div>\n"
        return html


    def send_position_report(self, report_data: Dict, text_content: str, date: str) -> bool:
        """
        发送持仓调整报告邮件

        Args:
            report_data: 报告元数据字典
            text_content: Markdown格式报告内容
            date: 报告日期

        Returns:
            是否发送成功
        """
        # 构建邮件主题
        subject = f"📊 持仓调整建议报告 v2.0 - {date}"

        # 构建HTML邮件内容
        html_content = self._format_position_report_html(text_content, date)

        # 从配置文件获取收件人列表
        recipients = self.config.get('recipients', ['your_email@example.com'])

        # 发送邮件 - 给每个收件人单独发送一封
        success_count = 0
        failed_recipients = []

        for recipient in recipients:
            try:
                # 每个收件人建立独立的SMTP连接
                smtp = smtplib.SMTP_SSL(
                    self.config['smtp']['server'],
                    self.config['smtp']['port']
                )
                smtp.login(
                    self.config['sender']['email'],
                    self.config['sender']['password']
                )

                # 创建邮件
                message = MIMEMultipart('alternative')
                message['From'] = self.config['sender']['email']
                message['To'] = recipient
                message['Subject'] = Header(subject, 'utf-8')
                message['X-Priority'] = '3'

                # 添加纯文本和HTML版本
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                html_part = MIMEText(html_content, 'html', 'utf-8')
                message.attach(text_part)
                message.attach(html_part)

                # 发送给当前收件人
                smtp.sendmail(
                    self.config['sender']['email'],
                    [recipient],
                    message.as_string()
                )

                smtp.quit()
                success_count += 1
                self.logger.info(f"✅ 邮件发送成功: {recipient}")

            except Exception as e:
                failed_recipients.append(recipient)
                self.logger.error(f"❌ 发送到 {recipient} 失败: {str(e)}")
                try:
                    smtp.quit()
                except:
                    pass

        # 汇总结果
        if success_count == len(recipients):
            self.logger.info(f"🎉 所有邮件发送成功(共{success_count}个收件人): {subject}")
            return True
        elif success_count > 0:
            self.logger.warning(f"⚠️ 部分邮件发送成功({success_count}/{len(recipients)}),失败的收件人: {', '.join(failed_recipients)}")
            return True
        else:
            self.logger.error(f"❌ 所有邮件发送失败")
            return False

    def _format_position_report_html(self, markdown_content: str, date: str) -> str:
        """
        将Markdown持仓报告转换为HTML邮件格式

        Args:
            markdown_content: Markdown格式报告
            date: 报告日期

        Returns:
            HTML格式邮件内容
        """
        # 简单的Markdown转HTML（保留关键格式）
        html_body = markdown_content.replace('\n', '<br>\n')
        html_body = html_body.replace('###', '<h3>').replace('##', '<h2>').replace('#', '<h1>')
        html_body = html_body.replace('**', '<strong>').replace('*', '<em>')

        # 构建完整HTML
        html = f"""
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: Arial, 'Microsoft YaHei', sans-serif;
        line-height: 1.6;
        margin: 0;
        padding: 0;
        background-color: #f5f5f5;
    }}
    .container {{
        max-width: 1000px;
        margin: 20px auto;
        background-color: white;
    }}
    .header {{
        background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
        color: white;
        padding: 30px 20px;
        text-align: center;
    }}
    .header h1 {{
        margin: 0;
        font-size: 28px;
    }}
    .header .subtitle {{
        font-size: 16px;
        margin-top: 10px;
        opacity: 0.9;
    }}
    .content {{
        padding: 30px;
    }}
    .content h2 {{
        color: #4ECDC4;
        border-left: 4px solid #4ECDC4;
        padding-left: 12px;
        margin-top: 30px;
    }}
    .content h3 {{
        color: #44A08D;
        margin-top: 20px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 13px;
    }}
    th {{
        background-color: #4ECDC4;
        color: white;
        padding: 12px 8px;
        text-align: left;
        font-weight: 600;
    }}
    td {{
        padding: 10px 8px;
        border-bottom: 1px solid #e9ecef;
    }}
    tr:hover {{
        background-color: #f8f9fa;
    }}
    .positive {{ color: #28a745; font-weight: bold; }}
    .negative {{ color: #dc3545; font-weight: bold; }}
    .footer {{
        background-color: #343a40;
        color: white;
        padding: 20px;
        text-align: center;
        font-size: 12px;
    }}
    pre {{
        background-color: #f8f9fa;
        padding: 15px;
        border-left: 4px solid #4ECDC4;
        overflow-x: auto;
        font-family: 'Courier New', monospace;
        font-size: 12px;
    }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📊 持仓调整建议报告 v2.0</h1>
        <div class="subtitle">机构级量化分析 | 持仓健康诊断 + 风险优化策略</div>
        <div class="subtitle">{date}</div>
    </div>

    <div class="content">
        {html_body}
    </div>

    <div class="footer">
        <p>📊 Claude Code 量化分析系统 | Russ个人持仓策略 v2.0</p>
        <p>分析维度: 执行摘要 | 量化指标 | 归因分析 | 压力测试 | 情景分析</p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>本邮件由系统自动生成,请勿直接回复</p>
    </div>
</div>
</body>
</html>
"""
        return html


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("测试邮件发送模块...")
    print("注意: 需要先配置 config/email_config.yaml")
