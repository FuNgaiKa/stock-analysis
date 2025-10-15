#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合资产分析报告邮件发送模块
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


class AssetEmailNotifier:
    """综合资产报告邮件通知器"""

    def __init__(self, config_path: str = None):
        """
        初始化邮件通知器

        Args:
            config_path: 配置文件路径,默认为项目根目录的 config/email_config.yaml
        """
        if config_path is None:
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

    def send_asset_report(self, report: Dict, text_content: str) -> bool:
        """
        发送综合资产分析报告邮件

        Args:
            report: 报告数据字典
            text_content: 文本格式报告

        Returns:
            是否发送成功
        """
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))

        # 计算整体趋势
        assets_data = report.get('assets', {})
        bullish_count = 0
        bearish_count = 0

        for asset_data in assets_data.values():
            judgment = asset_data.get('comprehensive_judgment', {})
            direction = judgment.get('direction', '')
            if '看多' in direction:
                bullish_count += 1
            elif '看空' in direction:
                bearish_count += 1

        # 确定邮件主题
        if bullish_count >= 5:
            subject = f"📈 【偏多】综合资产分析 - {bullish_count}个看多"
        elif bearish_count >= 5:
            subject = f"📉 【偏空】综合资产分析 - {bearish_count}个看空"
        else:
            subject = f"➡️ 【中性】综合资产分析 - 多空分化"

        subject += f" ({date})"

        # 构建HTML邮件内容
        html_content = self._format_html_content(report)

        # 创建邮件
        message = MIMEMultipart('alternative')
        message['From'] = self.config['sender']['email']

        # 固定收件人为 1264947688@qq.com
        recipient = '1264947688@qq.com'
        message['To'] = recipient
        message['Subject'] = Header(subject, 'utf-8')
        message['X-Priority'] = '3'

        # 添加纯文本和HTML版本
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
                [recipient],
                message.as_string()
            )
            smtp.quit()

            self.logger.info(f"邮件发送成功: {subject}")
            return True

        except Exception as e:
            self.logger.error(f"邮件发送失败: {str(e)}")
            return False

    def _format_html_content(self, report: Dict) -> str:
        """格式化HTML邮件内容"""
        date = report.get('date', datetime.now().strftime('%Y-%m-%d'))
        assets_data = report.get('assets', {})

        # 计算整体趋势
        bullish_count = 0
        for asset_data in assets_data.values():
            judgment = asset_data.get('comprehensive_judgment', {})
            direction = judgment.get('direction', '')
            if '看多' in direction:
                bullish_count += 1

        # 选择颜色
        if bullish_count >= 5:
            header_color = "#28a745"  # 绿色
            trend_icon = "📈"
            trend_text = "偏多"
        elif bullish_count <= 2:
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
        max-width: 900px;
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
        font-size: 26px;
    }}
    .header .subtitle {{
        font-size: 16px;
        margin-top: 10px;
        opacity: 0.9;
    }}
    .category-section {{
        background-color: #f8f9fa;
        padding: 15px 25px;
        border-top: 3px solid {header_color};
        margin: 0;
    }}
    .category-title {{
        font-size: 18px;
        font-weight: bold;
        color: {header_color};
        margin: 0;
    }}
    .section {{
        padding: 25px;
        border-bottom: 1px solid #e0e0e0;
    }}
    .section:last-child {{
        border-bottom: none;
    }}
    .section-title {{
        font-size: 20px;
        font-weight: bold;
        color: #333;
        margin-bottom: 20px;
        border-left: 4px solid {header_color};
        padding-left: 12px;
    }}
    .asset-card {{
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }}
    .asset-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #dee2e6;
    }}
    .asset-name {{
        font-size: 18px;
        font-weight: bold;
        color: #333;
    }}
    .asset-type {{
        font-size: 12px;
        color: #6c757d;
        background-color: #e9ecef;
        padding: 3px 10px;
        border-radius: 12px;
    }}
    .asset-price {{
        font-size: 20px;
        font-weight: bold;
    }}
    .positive {{ color: #28a745; }}
    .negative {{ color: #dc3545; }}
    .info-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin: 15px 0;
    }}
    .info-item {{
        background-color: white;
        padding: 12px;
        border-radius: 5px;
        border-left: 3px solid {header_color};
    }}
    .info-label {{
        font-size: 12px;
        color: #6c757d;
        margin-bottom: 5px;
    }}
    .info-value {{
        font-size: 16px;
        font-weight: bold;
        color: #333;
    }}
    .judgment-box {{
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }}
    .risk-box {{
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }}
    .low-risk {{
        background-color: #d4edda;
        border-left-color: #28a745;
    }}
    .strategy-list {{
        margin: 10px 0;
    }}
    .strategy-item {{
        padding: 8px 0;
        padding-left: 20px;
        border-left: 2px solid #dee2e6;
        margin-left: 10px;
    }}
    .combo-match {{
        background-color: #e7f3ff;
        padding: 12px;
        border-radius: 5px;
        margin: 10px 0;
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
        <h1>{trend_icon} 综合资产分析报告</h1>
        <div class="subtitle">四大科技指数 + 沪深300 + 黄金 + 比特币</div>
        <div class="subtitle">整体趋势: {trend_text} | {date}</div>
    </div>
"""

        # 按类别分组资产
        categories = {
            'tech_index': ('🚀 四大科技指数', []),
            'broad_index': ('📊 宽基指数', []),
            'commodity': ('💰 大宗商品', []),
            'crypto': ('₿ 加密货币', [])
        }

        for asset_key, asset_data in assets_data.items():
            if 'error' in asset_data:
                continue
            category = asset_data.get('category', '')
            if category in categories:
                categories[category][1].append((asset_key, asset_data))

        # 渲染每个类别
        for category_key, (category_name, assets) in categories.items():
            if not assets:
                continue

            html += f"""
    <div class="category-section">
        <div class="category-title">{category_name}</div>
    </div>
"""

            for asset_key, data in assets:
                asset_name = data['asset_name']
                asset_type = data['asset_type']
                hist = data.get('historical_analysis', {})
                tech = data.get('technical_analysis', {})
                risk = data.get('risk_assessment', {})
                judgment = data.get('comprehensive_judgment', {})

                # 价格变化颜色
                price_change = hist.get('current_change_pct', 0)
                price_color = 'positive' if price_change > 0 else 'negative'

                # 风险等级样式
                risk_score = risk.get('risk_score', 0.5)
                risk_box_class = 'low-risk' if risk_score < 0.3 else 'risk-box'

                html += f"""
    <div class="section">
        <div class="section-title">
            {asset_name}
            <span class="asset-type">{asset_type}</span>
        </div>

        <div class="asset-card">
            <div class="asset-header">
                <div class="asset-name">当前点位</div>
                <div class="asset-price {price_color}">
                    {hist.get('current_price', 0):.2f} ({price_change:+.2f}%)
                </div>
            </div>

            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">20日上涨概率</div>
                    <div class="info-value {'positive' if hist.get('20d', {}).get('up_prob', 0) > 0.5 else 'negative'}">
                        {hist.get('20d', {}).get('up_prob', 0):.1%}
                    </div>
                </div>
                <div class="info-item">
                    <div class="info-label">平均收益</div>
                    <div class="info-value {'positive' if hist.get('20d', {}).get('mean_return', 0) > 0 else 'negative'}">
                        {hist.get('20d', {}).get('mean_return', 0):+.2%}
                    </div>
                </div>
                <div class="info-item">
                    <div class="info-label">RSI指标</div>
                    <div class="info-value">{tech.get('rsi', {}).get('value', 0):.1f}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">MACD状态</div>
                    <div class="info-value">
                        {'金叉✅' if tech.get('macd', {}).get('status') == 'golden_cross' else '死叉🔴'}
                    </div>
                </div>
            </div>

            <div class="{risk_box_class}">
                <strong>风险评估:</strong> {risk.get('risk_level', '未知')} (评分: {risk_score:.2f})
                {f"<div style='margin-top: 8px;'>主要风险因素:</div>" if risk.get('risk_factors') else ''}
                {''.join([f"<div style='margin-left: 15px;'>• {factor}</div>" for factor in risk.get('risk_factors', [])[:3]])}
            </div>

            <div class="judgment-box">
                <strong>综合判断:</strong> {judgment.get('direction', '未知')}<br>
                <strong>建议仓位:</strong> {judgment.get('recommended_position', '50%')}
            </div>

            {f'''
            <div class="strategy-list">
                <strong>操作策略:</strong>
                {''.join([f"<div class='strategy-item'>• {s}</div>" for s in judgment.get('strategies', [])])}
            </div>
            ''' if judgment.get('strategies') else ''}

            {self._format_combo_strategies_html(judgment.get('combo_strategy_match', {}))}
        </div>
    </div>
"""

        html += f"""
    <div class="footer">
        <p>📊 Claude Code 量化分析系统 | 综合资产专项分析</p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>本邮件由系统自动生成,请勿直接回复</p>
    </div>
</div>
</body>
</html>
"""
        return html

    def _format_combo_strategies_html(self, combo: Dict) -> str:
        """格式化组合策略匹配HTML"""
        if not combo:
            return ''

        html_parts = []

        # 牛市确认组合
        bull = combo.get('bull_confirmation', {})
        if bull.get('matched', 0) >= 3:
            emoji = '✅✅' if bull['matched'] >= 4 else '✅'
            html_parts.append(f"""
                <div class="combo-match">
                    <strong>{emoji} 牛市确认组合: {bull['matched']}/{bull['total']}项</strong>
                    {''.join([f"<div style='margin-left: 15px; margin-top: 5px;'>✓ {cond}</div>" for cond in bull.get('conditions', [])])}
                </div>
            """)

        # 熊市确认组合
        bear = combo.get('bear_confirmation', {})
        if bear.get('matched', 0) >= 2:
            emoji = '🔴' if bear['matched'] >= 3 else '⚠️'
            html_parts.append(f"""
                <div class="risk-box">
                    <strong>{emoji} 熊市确认组合: {bear['matched']}/{bear['total']}项</strong>
                    {''.join([f"<div style='margin-left: 15px; margin-top: 5px;'>✗ {cond}</div>" for cond in bear.get('conditions', [])])}
                </div>
            """)

        # 抄底组合
        bottom = combo.get('bottom_fishing', {})
        if bottom.get('matched', 0) >= 2:
            html_parts.append(f"""
                <div class="combo-match">
                    <strong>💎 抄底组合: {bottom['matched']}/{bottom['total']}项</strong>
                </div>
            """)

        # 逃顶组合
        escape = combo.get('top_escape', {})
        if escape.get('matched', 0) >= 2:
            html_parts.append(f"""
                <div class="risk-box">
                    <strong>🚨 逃顶组合: {escape['matched']}/{escape['total']}项</strong>
                </div>
            """)

        return ''.join(html_parts)


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("测试邮件发送模块...")
    print("注意: 需要先配置 config/email_config.yaml")
