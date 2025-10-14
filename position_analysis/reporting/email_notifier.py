#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件通知模块
用于发送均线偏离度监控预警邮件
"""

import smtplib
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Dict, List, Optional
from datetime import datetime
import logging
from pathlib import Path


class EmailNotifier:
    """邮件通知器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化邮件通知器

        Args:
            config_path: 配置文件路径,默认为项目根目录的 email_config.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / 'config' / 'email_config.yaml'

        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)

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

    def send_alert_email(
        self,
        alert_report: str,
        alert_count: int,
        has_level3: bool = False,
        has_level2: bool = False
    ) -> bool:
        """
        发送预警邮件

        Args:
            alert_report: 预警报告文本
            alert_count: 预警数量
            has_level3: 是否有三级预警
            has_level2: 是否有二级预警

        Returns:
            是否发送成功
        """
        # 确定邮件主题优先级
        if has_level3:
            subject = f"💥 【三级预警】均线偏离度预警 - {alert_count}个信号"
            priority = "1"  # 最高优先级
        elif has_level2:
            subject = f"🚨 【二级预警】均线偏离度预警 - {alert_count}个信号"
            priority = "2"
        else:
            subject = f"⚠️ 【一级预警】均线偏离度预警 - {alert_count}个信号"
            priority = "3"

        subject += f" ({datetime.now().strftime('%Y-%m-%d')})"

        # 构建HTML邮件内容
        html_content = self._format_html_content(alert_report, alert_count, has_level3, has_level2)

        # 创建邮件
        message = MIMEMultipart('alternative')
        # QQ邮箱要求From必须是有效的邮箱地址格式
        message['From'] = self.config['sender']['email']
        # 过滤None值
        recipients = [r for r in self.config['recipients'] if r is not None and r.strip()]
        message['To'] = ', '.join(recipients)
        message['Subject'] = Header(subject, 'utf-8')
        message['X-Priority'] = priority

        # 添加纯文本和HTML版本
        text_part = MIMEText(alert_report, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(text_part)
        message.attach(html_part)

        # 发送邮件
        try:
            smtp = smtplib.SMTP_SSL(
                self.config['smtp']['server'],
                self.config['smtp']['port']
            )
            smtp.login(
                self.config['sender']['email'],
                self.config['sender']['password']
            )
            smtp.sendmail(
                self.config['sender']['email'],
                recipients,
                message.as_string()
            )
            smtp.quit()

            self.logger.info(f"邮件发送成功: {subject}")
            return True

        except Exception as e:
            self.logger.error(f"邮件发送失败: {str(e)}")
            return False

    def send_no_alert_email(self) -> bool:
        """
        发送无预警邮件(可选)

        Returns:
            是否发送成功
        """
        if not self.config.get('send_no_alert_email', False):
            return True  # 配置为不发送,返回成功

        subject = f"✅ 均线偏离度监控 - 无预警 ({datetime.now().strftime('%Y-%m-%d')})"

        content = f"""
均线偏离度监控报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

今日所有监控指数均未触发预警阈值。

监控指数:
  A股: 上证指数、沪深300、创业板指、科创50、深证成指
       中小板指、上证50、中证500、中证1000
  港股: 恒生指数、恒生科技

预警阈值:
  一级预警: >20%
  二级预警: >30%
  三级预警: >40%

市场运行平稳,继续保持观察。
"""

        html_content = f"""
<html>
<head>
<style>
    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
    .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
    .content {{ padding: 20px; }}
    .footer {{ background-color: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #6c757d; }}
</style>
</head>
<body>
<div class="header">
    <h2>✅ 均线偏离度监控 - 无预警</h2>
    <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
<div class="content">
    <p>今日所有监控指数均未触发预警阈值。</p>
    <p>市场运行平稳,继续保持观察。</p>
</div>
<div class="footer">
    <p>均线偏离度监控系统 | 自动发送</p>
</div>
</body>
</html>
"""

        message = MIMEMultipart('alternative')
        # QQ邮箱要求From必须是有效的邮箱地址格式
        message['From'] = self.config['sender']['email']
        # 过滤None值
        recipients = [r for r in self.config['recipients'] if r is not None and r.strip()]
        message['To'] = ', '.join(recipients)
        message['Subject'] = Header(subject, 'utf-8')

        text_part = MIMEText(content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(text_part)
        message.attach(html_part)

        try:
            smtp = smtplib.SMTP_SSL(
                self.config['smtp']['server'],
                self.config['smtp']['port']
            )
            smtp.login(
                self.config['sender']['email'],
                self.config['sender']['password']
            )
            smtp.sendmail(
                self.config['sender']['email'],
                recipients,
                message.as_string()
            )
            smtp.quit()

            self.logger.info(f"邮件发送成功: {subject}")
            return True

        except Exception as e:
            self.logger.error(f"邮件发送失败: {str(e)}")
            return False

    def send_daily_report(self, report: Dict) -> bool:
        """
        发送每日市场总结邮件

        Args:
            report: 每日报告数据字典

        Returns:
            是否发送成功
        """
        score = report.get('composite_score', 5)
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))

        # 根据评分选择标题和颜色
        if score >= 7:
            subject = f"📈 【偏多】每日市场总结 - 综合评分{score:.1f}/10"
            priority = "2"
        elif score >= 5.5:
            subject = f"➡️ 【中性】每日市场总结 - 综合评分{score:.1f}/10"
            priority = "3"
        else:
            subject = f"📉 【偏空】每日市场总结 - 综合评分{score:.1f}/10"
            priority = "3"

        subject += f" ({date})"

        # 构建HTML邮件内容
        html_content = self._format_daily_report_html(report)

        # 创建邮件
        message = MIMEMultipart('alternative')
        message['From'] = self.config['sender']['email']
        # 过滤None值
        recipients = [r for r in self.config['recipients'] if r is not None and r.strip()]
        message['To'] = ', '.join(recipients)
        message['Subject'] = Header(subject, 'utf-8')
        message['X-Priority'] = priority

        # 添加纯文本版本(简化)
        from position_analysis.reporting.daily_market_reporter import DailyMarketReporter
        reporter = DailyMarketReporter.__new__(DailyMarketReporter)  # 不初始化分析器
        text_content = reporter.format_text_report(report)

        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(text_part)
        message.attach(html_part)

        # 发送邮件
        try:
            smtp = smtplib.SMTP_SSL(
                self.config['smtp']['server'],
                self.config['smtp']['port']
            )
            smtp.login(
                self.config['sender']['email'],
                self.config['sender']['password']
            )
            smtp.sendmail(
                self.config['sender']['email'],
                recipients,
                message.as_string()
            )
            smtp.quit()

            self.logger.info(f"每日报告邮件发送成功: {subject}")
            return True

        except Exception as e:
            self.logger.error(f"每日报告邮件发送失败: {str(e)}")
            return False

    def _format_daily_report_html(self, report: Dict) -> str:
        """格式化每日报告HTML内容"""
        score = report.get('composite_score', 5)
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))

        # 根据评分选择颜色
        if score >= 7:
            header_color = "#28a745"  # 绿色
            score_icon = "📈"
            trend_text = "偏多"
        elif score >= 5.5:
            header_color = "#6c757d"  # 灰色
            score_icon = "➡️"
            trend_text = "中性"
        else:
            header_color = "#dc3545"  # 红色
            score_icon = "📉"
            trend_text = "偏空"

        # 提取数据
        cn_data = report.get('cn_market', {})
        us_data = report.get('us_market', {})
        hk_data = report.get('hk_market', {})
        suggestion = report.get('trade_suggestion', {})

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
        max-width: 800px;
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
        font-size: 24px;
    }}
    .header .score {{
        font-size: 36px;
        font-weight: bold;
        margin: 10px 0;
    }}
    .section {{
        padding: 20px;
        border-bottom: 1px solid #e0e0e0;
    }}
    .section:last-child {{
        border-bottom: none;
    }}
    .section-title {{
        font-size: 18px;
        font-weight: bold;
        color: #333;
        margin-bottom: 15px;
        border-left: 4px solid {header_color};
        padding-left: 10px;
    }}
    .market-grid {{
        display: table;
        width: 100%;
        margin: 10px 0;
    }}
    .market-row {{
        display: table-row;
    }}
    .market-cell {{
        display: table-cell;
        padding: 10px;
        border-bottom: 1px solid #f0f0f0;
    }}
    .market-name {{
        font-weight: bold;
        width: 25%;
    }}
    .market-value {{
        text-align: right;
        width: 25%;
    }}
    .positive {{ color: #28a745; }}
    .negative {{ color: #dc3545; }}
    .indicator-box {{
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }}
    .indicator-item {{
        margin: 8px 0;
        padding-left: 20px;
    }}
    .suggestion-box {{
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
    }}
    .signal-list {{
        margin: 10px 0;
    }}
    .signal-item {{
        padding: 5px 0;
        padding-left: 20px;
    }}
    .footer {{
        background-color: #343a40;
        color: white;
        padding: 20px;
        text-align: center;
        font-size: 12px;
    }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>{score_icon} 每日市场总结</h1>
        <div class="score">{score:.1f} / 10</div>
        <p>市场趋势: {trend_text} | {date}</p>
    </div>

    <div class="section">
        <div class="section-title">🌍 三大市场概览</div>
        <div class="market-grid">
            <div class="market-row">
                <div class="market-cell market-name">📈 美股-纳斯达克</div>
                <div class="market-cell market-value">{us_data.get('nasdaq', {}).get('close', 0):.2f}</div>
                <div class="market-cell market-value {'positive' if us_data.get('nasdaq', {}).get('change_pct', 0) > 0 else 'negative'}">
                    {us_data.get('nasdaq', {}).get('change_pct', 0):+.2f}%
                </div>
            </div>
            <div class="market-row">
                <div class="market-cell market-name">📈 美股-标普500</div>
                <div class="market-cell market-value">{us_data.get('sp500', {}).get('close', 0):.2f}</div>
                <div class="market-cell market-value {'positive' if us_data.get('sp500', {}).get('change_pct', 0) > 0 else 'negative'}">
                    {us_data.get('sp500', {}).get('change_pct', 0):+.2f}%
                </div>
            </div>
            <div class="market-row">
                <div class="market-cell market-name">🇭🇰 港股-恒生指数</div>
                <div class="market-cell market-value">{hk_data.get('hsi', {}).get('close', 0):.2f}</div>
                <div class="market-cell market-value {'positive' if hk_data.get('hsi', {}).get('change_pct', 0) > 0 else 'negative'}">
                    {hk_data.get('hsi', {}).get('change_pct', 0):+.2f}%
                </div>
            </div>
            <div class="market-row">
                <div class="market-cell market-name">🇨🇳 A股-上证指数</div>
                <div class="market-cell market-value">{cn_data.get('sse', {}).get('close', 0):.2f}</div>
                <div class="market-cell market-value {'positive' if cn_data.get('sse', {}).get('change_pct', 0) > 0 else 'negative'}">
                    {cn_data.get('sse', {}).get('change_pct', 0):+.2f}%
                </div>
            </div>
            <div class="market-row">
                <div class="market-cell market-name">🇨🇳 A股-深证成指</div>
                <div class="market-cell market-value">{cn_data.get('szse', {}).get('close', 0):.2f}</div>
                <div class="market-cell market-value {'positive' if cn_data.get('szse', {}).get('change_pct', 0) > 0 else 'negative'}">
                    {cn_data.get('szse', {}).get('change_pct', 0):+.2f}%
                </div>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">📊 A股核心指标</div>
        <div class="indicator-box">
            <div class="indicator-item">✅ 北向资金: {cn_data.get('north_capital', {}).get('sentiment', '未知')} ({cn_data.get('north_capital', {}).get('sentiment_score', 0)}/100)</div>
            <div class="indicator-item">💰 融资情绪: {cn_data.get('margin_trading', {}).get('sentiment', '未知')} ({cn_data.get('margin_trading', {}).get('sentiment_score', 0)}/100)</div>
            <div class="indicator-item">📈 市场宽度: {cn_data.get('market_breadth', {}).get('strength', '未知')} ({cn_data.get('market_breadth', {}).get('strength_score', 0)}/100)</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">🎯 交易建议</div>
        <div class="suggestion-box">
            <p><strong>方向:</strong> {suggestion.get('direction', '中性')}</p>
            <p><strong>建议:</strong> {suggestion.get('suggestion', '数据不足')}</p>
            <p><strong>策略:</strong> {suggestion.get('strategy', '谨慎操作')}</p>
            <p><strong>建议仓位:</strong> {suggestion.get('position', 0.5)*100:.0f}%</p>
        </div>

        {f'''
        <div class="signal-list">
            <strong>✅ 看多信号 ({len(suggestion.get('bullish_signals', []))}个):</strong>
            {''.join([f'<div class="signal-item">• {s}</div>' for s in suggestion.get('bullish_signals', []) if s is not None])}
        </div>
        ''' if suggestion.get('bullish_signals') else ''}

        {f'''
        <div class="signal-list">
            <strong>⚠️ 风险提示 ({len(suggestion.get('bearish_signals', []))}个):</strong>
            {''.join([f'<div class="signal-item">• {s}</div>' for s in suggestion.get('bearish_signals', []) if s is not None])}
        </div>
        ''' if suggestion.get('bearish_signals') else ''}

        {f'''
        <div class="indicator-box">
            <div><strong>关键点位:</strong></div>
            <div class="indicator-item">支撑位: {suggestion.get('support_level', 0):.2f}</div>
            <div class="indicator-item">压力位: {suggestion.get('resistance_level', 0):.2f}</div>
        </div>
        ''' if suggestion.get('support_level', 0) > 0 else ''}
    </div>

    <div class="footer">
        <p>📊 Claude Code 量化分析系统 | 每日市场推送</p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>本邮件由系统自动生成,请勿直接回复</p>
    </div>
</div>
</body>
</html>
"""
        return html

    def _format_html_content(
        self,
        alert_report: str,
        alert_count: int,
        has_level3: bool,
        has_level2: bool
    ) -> str:
        """格式化HTML邮件内容"""

        # 根据预警级别选择颜色
        if has_level3:
            header_color = "#dc3545"  # 红色
            alert_icon = "💥"
            alert_level = "三级预警"
        elif has_level2:
            header_color = "#fd7e14"  # 橙色
            alert_icon = "🚨"
            alert_level = "二级预警"
        else:
            header_color = "#ffc107"  # 黄色
            alert_icon = "⚠️"
            alert_level = "一级预警"

        # 转义HTML并保留格式
        report_html = alert_report.replace('\n', '<br>').replace(' ', '&nbsp;')

        html = f"""
<html>
<head>
<style>
    body {{
        font-family: Arial, sans-serif;
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }}
    .header {{
        background-color: {header_color};
        color: white;
        padding: 20px;
        text-align: center;
    }}
    .content {{
        padding: 20px;
        background-color: #f8f9fa;
    }}
    .alert-box {{
        background-color: white;
        border-left: 4px solid {header_color};
        padding: 15px;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
        font-size: 13px;
    }}
    .footer {{
        background-color: #343a40;
        color: white;
        padding: 15px;
        text-align: center;
        font-size: 12px;
    }}
    .warning {{
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }}
</style>
</head>
<body>
<div class="header">
    <h2>{alert_icon} {alert_level} - 均线偏离度监控</h2>
    <p>检测到 {alert_count} 个预警信号</p>
    <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
<div class="content">
    <div class="warning">
        <strong>⚠️ 温馨提示:</strong>
        <ul>
            <li>偏离度仅为参考指标,需结合估值、资金流向等多维度判断</li>
            <li>向上大幅偏离(>30%)往往伴随短期回调风险</li>
            <li>向下大幅偏离(>30%)可能存在超跌反弹机会</li>
        </ul>
    </div>
    <div class="alert-box">
{report_html}
    </div>
</div>
<div class="footer">
    <p>均线偏离度监控系统 | 自动发送</p>
    <p>本邮件由系统自动生成,请勿直接回复</p>
</div>
</body>
</html>
"""
        return html
