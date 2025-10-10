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
            project_root = Path(__file__).parent.parent
            config_path = project_root / 'email_config.yaml'

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
            self.logger.info("请参考 email_config.yaml.template 创建配置文件")
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
        message['To'] = ', '.join(self.config['recipients'])
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
                self.config['recipients'],
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
        message['To'] = ', '.join(self.config['recipients'])
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
                self.config['recipients'],
                message.as_string()
            )
            smtp.quit()

            self.logger.info(f"邮件发送成功: {subject}")
            return True

        except Exception as e:
            self.logger.error(f"邮件发送失败: {str(e)}")
            return False

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
