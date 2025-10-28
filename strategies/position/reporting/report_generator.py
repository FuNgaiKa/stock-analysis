#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成器 - 命令行文本 + HTML可视化
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TextReportGenerator:
    """命令行文本报告生成器"""

    @staticmethod
    def generate_header(title: str = "市场历史点位对比分析报告") -> str:
        """生成报告头部"""
        line = "=" * 80
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""
{line}
{title:^80}
分析时间: {timestamp:^80}
{line}
"""

    @staticmethod
    def generate_current_positions_section(positions: Dict) -> str:
        """生成当前点位部分"""
        section = "\n[当前市场点位]\n"

        for code, info in positions.items():
            section += f"  {info['name']:8s}: {info['price']:8.2f}  (数据日期: {info['date']})\n"

        return section

    @staticmethod
    def generate_single_index_analysis(
        index_name: str,
        current_price: float,
        similar_count: int,
        year_distribution: Dict,
        prob_stats: Dict,
        periods: List[int] = [5, 10, 20, 60]
    ) -> str:
        """生成单指数分析部分"""
        section = f"\n【{index_name} - {current_price:.2f}】\n"
        section += f"历史相似点位出现: {similar_count} 次"

        if year_distribution:
            years = ', '.join([f"{year}年({count}次)" for year, count in year_distribution.items()])
            section += f" (分布在 {years})\n"
        else:
            section += "\n"

        # 各周期概率统计
        for period in periods:
            if f'period_{period}d' in prob_stats:
                stats = prob_stats[f'period_{period}d']
                section += f"\n  未来{period}日涨跌概率:\n"
                section += f"    上涨概率: {stats['up_prob']:5.1%} ({stats['up_count']}次)\n"
                section += f"    下跌概率: {stats['down_prob']:5.1%} ({stats['down_count']}次)\n"
                section += f"    平均收益: {stats['mean_return']:+6.2%}\n"
                section += f"    收益中位数: {stats['median_return']:+6.2%}\n"

                # 置信度星级
                confidence = stats.get('confidence', 0)
                stars = TextReportGenerator._get_confidence_stars(confidence)
                warning = " ⚠️ 样本量偏少" if stats['sample_size'] < 10 else ""
                section += f"    置信度: {stars} ({confidence:.0%}){warning}\n"

        return section

    @staticmethod
    def generate_multi_index_analysis(
        match_count: int,
        matched_periods: pd.DataFrame,
        multi_prob_stats: Dict
    ) -> str:
        """生成多指数联合分析部分"""
        section = "\n[多指数联合分析]\n\n"

        if match_count == 0:
            section += "  未找到多个指数同时处于相似点位的历史时期\n"
            return section

        section += f"找到 {match_count} 个历史时期，多个指数同时处于相似点位:\n"

        # 显示前10个匹配时期
        for i, (idx, row) in enumerate(matched_periods.head(10).iterrows(), 1):
            date_str = row['date'].strftime('%Y-%m-%d')
            section += f"  {i}. {date_str} (匹配{row['match_count']}个指数)\n"

        if len(matched_periods) > 10:
            section += f"  ... (还有{len(matched_periods)-10}个时期)\n"

        # 多指数匹配后的概率
        if multi_prob_stats:
            section += f"\n多指数联合匹配后的未来20日走势:\n"
            section += f"  上涨概率: {multi_prob_stats['up_prob']:.1%}\n"
            section += f"  下跌概率: {multi_prob_stats['down_prob']:.1%}\n"
            section += f"  平均收益: {multi_prob_stats['mean_return']:+.2%}\n"

            confidence = multi_prob_stats.get('confidence', 0)
            stars = TextReportGenerator._get_confidence_stars(confidence)
            section += f"  置信度: {stars} (多维度匹配)\n"

        return section

    @staticmethod
    def generate_position_advice(
        signal: str,
        recommended_position: float,
        description: str,
        stop_loss: Dict = None
    ) -> str:
        """生成仓位建议部分"""
        section = "\n[仓位管理建议]\n\n"
        section += f"交易信号: {signal}\n"
        section += f"建议仓位: {recommended_position*100:.0f}%\n"
        section += f"策略说明: {description}\n"

        if stop_loss:
            section += f"\n止损止盈参考:\n"
            section += f"  止损位: {stop_loss['stop_loss_price']:.2f} ({stop_loss['stop_loss_pct']:+.1%})\n"
            section += f"  止盈位: {stop_loss['take_profit_price']:.2f} ({stop_loss['take_profit_pct']:+.1%})\n"
            section += f"  盈亏比: {stop_loss['risk_reward_ratio']:.2f}\n"

        return section

    @staticmethod
    def generate_conclusion(
        direction: str,
        confidence: float,
        reasons: List[str],
        suggestions: Dict[str, str]
    ) -> str:
        """生成综合结论部分"""
        section = "\n[综合结论]\n\n"
        section += f"方向判断: {direction} (置信度 {confidence:.0%})\n\n"

        section += "主要依据:\n"
        for i, reason in enumerate(reasons, 1):
            section += f"  {i}. {reason}\n"

        section += "\n操作建议:\n"
        for period, suggestion in suggestions.items():
            section += f"  {period}: {suggestion}\n"

        section += "\n风险提示:\n"
        section += "  该分析基于历史统计，历史表现不代表未来结果。\n"
        section += "  请结合基本面、政策面等因素综合判断，控制风险。\n"

        return section

    @staticmethod
    def generate_footer() -> str:
        """生成报告尾部"""
        return "\n" + "=" * 80 + "\n"

    @staticmethod
    def _get_confidence_stars(confidence: float) -> str:
        """根据置信度返回星级"""
        if confidence >= 0.8:
            return "★★★★★"
        elif confidence >= 0.6:
            return "★★★★☆"
        elif confidence >= 0.4:
            return "★★★☆☆"
        elif confidence >= 0.2:
            return "★★☆☆☆"
        else:
            return "★☆☆☆☆"

    @staticmethod
    def get_year_distribution(dates: pd.DatetimeIndex) -> Dict[int, int]:
        """统计年份分布"""
        years = dates.year
        year_counts = years.value_counts().to_dict()
        return dict(sorted(year_counts.items()))


class HTMLReportGenerator:
    """HTML可视化报告生成器"""

    @staticmethod
    def generate_html_report(
        title: str,
        sections: Dict[str, str],
        charts: Dict[str, str] = None
    ) -> str:
        """
        生成完整的HTML报告

        Args:
            title: 报告标题
            sections: 各部分内容字典
            charts: 图表HTML字典 (plotly/echarts)

        Returns:
            完整的HTML字符串
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {HTMLReportGenerator._get_css_styles()}
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p class="timestamp">生成时间: {timestamp}</p>
        </header>

        <main>
"""

        # 添加各个部分
        for section_title, content in sections.items():
            html += f"""
            <section>
                <h2>{section_title}</h2>
                <div class="content">
                    {content}
                </div>
            </section>
"""

        # 添加图表
        if charts:
            html += """
            <section>
                <h2>可视化分析</h2>
"""
            for chart_title, chart_html in charts.items():
                html += f"""
                <div class="chart-container">
                    <h3>{chart_title}</h3>
                    {chart_html}
                </div>
"""
            html += """
            </section>
"""

        html += """
        </main>

        <footer>
            <p>⚠️ 风险提示：该分析基于历史统计，不构成投资建议。投资有风险，决策需谨慎。</p>
        </footer>
    </div>
</body>
</html>
"""
        return html

    @staticmethod
    def _get_css_styles() -> str:
        """获取CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        .timestamp {
            opacity: 0.9;
            font-size: 0.9em;
        }

        section {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        section h2 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }

        section h3 {
            color: #555;
            margin: 15px 0 10px 0;
        }

        .content {
            line-height: 1.8;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }

        table th, table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        table th {
            background-color: #667eea;
            color: white;
            font-weight: bold;
        }

        table tr:hover {
            background-color: #f5f5f5;
        }

        .metric {
            display: inline-block;
            margin: 10px 15px 10px 0;
            padding: 10px 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }

        .metric-label {
            font-size: 0.9em;
            color: #666;
        }

        .metric-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }

        .positive {
            color: #28a745;
        }

        .negative {
            color: #dc3545;
        }

        .neutral {
            color: #6c757d;
        }

        .chart-container {
            margin: 20px 0;
        }

        .signal-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }

        .signal-strong-buy {
            background-color: #28a745;
            color: white;
        }

        .signal-buy {
            background-color: #5cb85c;
            color: white;
        }

        .signal-neutral {
            background-color: #6c757d;
            color: white;
        }

        .signal-sell {
            background-color: #f0ad4e;
            color: white;
        }

        .signal-strong-sell {
            background-color: #dc3545;
            color: white;
        }

        footer {
            text-align: center;
            padding: 20px;
            color: #666;
            background: white;
            border-radius: 8px;
            margin-top: 20px;
        }

        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }

            header h1 {
                font-size: 1.5em;
            }

            section {
                padding: 15px;
            }
        }
        """

    @staticmethod
    def create_metrics_html(metrics: Dict[str, any]) -> str:
        """创建指标卡片HTML"""
        html = '<div class="metrics-container">'

        for label, value in metrics.items():
            # 判断正负
            value_class = ""
            if isinstance(value, (int, float)):
                if value > 0:
                    value_class = "positive"
                elif value < 0:
                    value_class = "negative"
                else:
                    value_class = "neutral"

                # 格式化
                if abs(value) < 1:
                    value_str = f"{value:.2%}"
                else:
                    value_str = f"{value:.2f}"
            else:
                value_str = str(value)

            html += f"""
            <div class="metric">
                <div class="metric-label">{label}</div>
                <div class="metric-value {value_class}">{value_str}</div>
            </div>
            """

        html += '</div>'
        return html

    @staticmethod
    def create_table_html(df: pd.DataFrame, max_rows: int = 20) -> str:
        """将DataFrame转换为HTML表格"""
        if len(df) > max_rows:
            df_display = df.head(max_rows)
            footer_note = f"<p><em>（仅显示前{max_rows}条，共{len(df)}条数据）</em></p>"
        else:
            df_display = df
            footer_note = ""

        html = df_display.to_html(
            classes='data-table',
            index=False,
            float_format=lambda x: f'{x:.2%}' if abs(x) < 1 else f'{x:.2f}'
        )

        return html + footer_note


class MarkdownReportGenerator:
    """Markdown格式报告生成器"""

    @staticmethod
    def generate_header(title: str = "市场历史点位对比分析报告") -> str:
        """生成报告头部"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""# 📊 {title}

**生成时间**: {timestamp}

---
"""

    @staticmethod
    def generate_current_positions_section(positions: Dict) -> str:
        """生成当前点位部分"""
        section = "## 💼 当前市场点位\n\n"
        section += "| 指数名称 | 当前价格 | 数据日期 |\n"
        section += "|---------|---------|----------|\n"

        for code, info in positions.items():
            section += f"| **{info['name']}** | {info['price']:.2f} | {info['date']} |\n"

        return section

    @staticmethod
    def generate_single_index_analysis(
        index_name: str,
        current_price: float,
        similar_count: int,
        year_distribution: Dict,
        prob_stats: Dict,
        periods: List[int] = [5, 10, 20, 60]
    ) -> str:
        """生成单指数分析部分"""
        section = f"\n## 📈 {index_name} - {current_price:.2f}\n\n"
        section += f"历史相似点位出现: **{similar_count}** 次"

        if year_distribution:
            years = ', '.join([f"{year}年({count}次)" for year, count in year_distribution.items()])
            section += f" (分布在 {years})\n\n"
        else:
            section += "\n\n"

        # 各周期概率统计
        for period in periods:
            if f'period_{period}d' in prob_stats:
                stats = prob_stats[f'period_{period}d']

                # 根据概率选择emoji
                up_emoji = "📈" if stats['up_prob'] > 0.5 else "📉"

                section += f"### 🎯 未来{period}日涨跌概率\n\n"
                section += "| 指标 | 数值 |\n"
                section += "|------|------|\n"
                section += f"| **上涨概率** | {up_emoji} {stats['up_prob']:.1%} ({stats['up_count']}次) |\n"
                section += f"| **下跌概率** | {stats['down_prob']:.1%} ({stats['down_count']}次) |\n"
                section += f"| **平均收益** | {stats['mean_return']:+.2%} |\n"
                section += f"| **收益中位数** | {stats['median_return']:+.2%} |\n"

                # 置信度
                confidence = stats.get('confidence', 0)
                stars = MarkdownReportGenerator._get_confidence_stars(confidence)
                warning = " ⚠️ 样本量偏少" if stats['sample_size'] < 10 else ""
                section += f"| **置信度** | {stars} ({confidence:.0%}){warning} |\n\n"

        return section

    @staticmethod
    def generate_multi_index_analysis(
        match_count: int,
        matched_periods: pd.DataFrame,
        multi_prob_stats: Dict
    ) -> str:
        """生成多指数联合分析部分"""
        section = "\n## 🔍 多指数联合分析\n\n"

        if match_count == 0:
            section += "未找到多个指数同时处于相似点位的历史时期\n\n"
            return section

        section += f"找到 **{match_count}** 个历史时期，多个指数同时处于相似点位:\n\n"

        # 显示前10个匹配时期
        section += "| 序号 | 日期 | 匹配指数数量 |\n"
        section += "|------|------|-------------|\n"

        for i, (idx, row) in enumerate(matched_periods.head(10).iterrows(), 1):
            date_str = row['date'].strftime('%Y-%m-%d')
            section += f"| {i} | {date_str} | {row['match_count']}个 |\n"

        if len(matched_periods) > 10:
            section += f"\n*... (还有{len(matched_periods)-10}个时期)*\n"

        # 多指数匹配后的概率
        if multi_prob_stats:
            up_emoji = "📈" if multi_prob_stats['up_prob'] > 0.5 else "📉"

            section += f"\n### 🎲 多指数联合匹配后的未来20日走势\n\n"
            section += "| 指标 | 数值 |\n"
            section += "|------|------|\n"
            section += f"| **上涨概率** | {up_emoji} {multi_prob_stats['up_prob']:.1%} |\n"
            section += f"| **下跌概率** | {multi_prob_stats['down_prob']:.1%} |\n"
            section += f"| **平均收益** | {multi_prob_stats['mean_return']:+.2%} |\n"

            confidence = multi_prob_stats.get('confidence', 0)
            stars = MarkdownReportGenerator._get_confidence_stars(confidence)
            section += f"| **置信度** | {stars} (多维度匹配) |\n\n"

        return section

    @staticmethod
    def generate_position_advice(
        signal: str,
        recommended_position: float,
        description: str,
        stop_loss: Dict = None
    ) -> str:
        """生成仓位建议部分"""
        section = "\n## 💡 仓位管理建议\n\n"

        # 根据信号选择emoji
        signal_emoji = {
            "强烈看多": "🟢",
            "看多": "🟢",
            "中性": "🟡",
            "看空": "🔴",
            "强烈看空": "🔴"
        }
        emoji = signal_emoji.get(signal, "🔵")

        section += "| 项目 | 内容 |\n"
        section += "|------|------|\n"
        section += f"| **交易信号** | {emoji} {signal} |\n"
        section += f"| **建议仓位** | {recommended_position*100:.0f}% |\n"
        section += f"| **策略说明** | {description} |\n"

        if stop_loss:
            section += "\n### 🎯 止损止盈参考\n\n"
            section += "| 项目 | 价格 | 幅度 |\n"
            section += "|------|------|------|\n"
            section += f"| **止损位** | {stop_loss['stop_loss_price']:.2f} | {stop_loss['stop_loss_pct']:+.1%} |\n"
            section += f"| **止盈位** | {stop_loss['take_profit_price']:.2f} | {stop_loss['take_profit_pct']:+.1%} |\n"
            section += f"| **盈亏比** | {stop_loss['risk_reward_ratio']:.2f} | - |\n"

        return section

    @staticmethod
    def generate_conclusion(
        direction: str,
        confidence: float,
        reasons: List[str],
        suggestions: Dict[str, str]
    ) -> str:
        """生成综合结论部分"""
        # 根据方向选择emoji
        direction_emoji = "📈" if "看多" in direction or "上涨" in direction else "📉" if "看空" in direction or "下跌" in direction else "➡️"

        section = f"\n## 🎯 综合结论\n\n"
        section += f"### {direction_emoji} 方向判断: {direction}\n\n"
        section += f"**置信度**: {MarkdownReportGenerator._get_confidence_stars(confidence)} ({confidence:.0%})\n\n"

        section += "### 📋 主要依据\n\n"
        for i, reason in enumerate(reasons, 1):
            section += f"{i}. {reason}\n"

        section += "\n### 💼 操作建议\n\n"
        for period, suggestion in suggestions.items():
            section += f"- **{period}**: {suggestion}\n"

        section += "\n### ⚠️ 风险提示\n\n"
        section += "- 该分析基于历史统计，历史表现不代表未来结果\n"
        section += "- 请结合基本面、政策面等因素综合判断，控制风险\n"
        section += "- 投资有风险，入市需谨慎\n"

        return section

    @staticmethod
    def generate_footer() -> str:
        """生成报告尾部"""
        return "\n---\n\n*报告结束*\n"

    @staticmethod
    def _get_confidence_stars(confidence: float) -> str:
        """根据置信度返回星级"""
        if confidence >= 0.8:
            return "⭐⭐⭐⭐⭐"
        elif confidence >= 0.6:
            return "⭐⭐⭐⭐"
        elif confidence >= 0.4:
            return "⭐⭐⭐"
        elif confidence >= 0.2:
            return "⭐⭐"
        else:
            return "⭐"

    @staticmethod
    def get_year_distribution(dates: pd.DatetimeIndex) -> Dict[int, int]:
        """统计年份分布"""
        years = dates.year
        year_counts = years.value_counts().to_dict()
        return dict(sorted(year_counts.items()))

    @staticmethod
    def generate_valuation_section(valuation_data: Dict) -> str:
        """
        生成估值分析部分

        Args:
            valuation_data: 估值分析数据字典

        Returns:
            Markdown格式的估值分析部分
        """
        if not valuation_data or 'error' in valuation_data:
            return "\n### 💰 估值分析\n\n暂无估值数据\n\n"

        section = "\n### 💰 估值分析 (PE/PB分位数)\n\n"

        # 基本信息
        section += f"**{valuation_data.get('index_name', 'N/A')}** | 日期: {valuation_data.get('date', 'N/A')}\n\n"

        # 当前估值
        current_pe = valuation_data.get('current_pe', 0)
        current_pb = valuation_data.get('current_pb', 0)

        section += "| 指标 | 当前值 |\n"
        section += "|------|--------|\n"
        section += f"| **当前PE** | {current_pe:.2f} |\n"
        if current_pb:
            section += f"| **当前PB** | {current_pb:.2f} |\n"
        section += "\n"

        # PE历史分位数
        pe_percentiles = valuation_data.get('pe_percentiles', {})
        if pe_percentiles:
            section += "#### 📊 PE历史分位数\n\n"
            section += "| 周期 | 分位数 | 估值水平 | 历史均值 | 历史中位数 |\n"
            section += "|------|--------|----------|----------|------------|\n"

            for period, data in pe_percentiles.items():
                percentile = data['percentile']
                level = data['level']
                mean = data['mean']
                median = data['median']
                section += f"| {period} | {percentile:.1f}% | {level} | {mean:.2f} | {median:.2f} |\n"
            section += "\n"

        # 估值水平综合判断
        val_level = valuation_data.get('valuation_level', {})
        if val_level:
            emoji = val_level.get('emoji', '')
            level = val_level.get('level', '')
            signal = val_level.get('signal', '')
            description = val_level.get('description', '')

            section += f"#### {emoji} 估值水平综合判断\n\n"
            section += f"- **估值水平**: {level}\n"
            section += f"- **操作信号**: {signal}\n"
            section += f"- **说明**: {description}\n\n"

        return section

    @staticmethod
    def generate_breadth_section(breadth_data: Dict) -> str:
        """
        生成市场宽度分析部分

        Args:
            breadth_data: 市场宽度数据字典

        Returns:
            Markdown格式的市场宽度分析部分
        """
        if not breadth_data or 'error' in breadth_data:
            return "\n### 📊 市场宽度分析\n\n暂无市场宽度数据\n\n"

        section = "\n### 📊 市场宽度分析 (新高新低指标)\n\n"

        metrics = breadth_data.get('metrics', {})
        strength = breadth_data.get('strength_analysis', {})

        if not metrics:
            return section + "暂无数据\n\n"

        # 基本指标
        section += f"**日期**: {metrics.get('latest_date', 'N/A')} | **指数**: {metrics.get('index_close', 0):.2f}\n\n"

        section += "#### 📈 新高新低统计\n\n"
        section += "| 周期 | 新高个股数 | 新低个股数 | 新高新低比率 |\n"
        section += "|------|------------|------------|-------------|\n"

        high20 = metrics.get('high20', 0)
        low20 = metrics.get('low20', 0)
        ratio20 = metrics.get('ratio20', 0)
        high60 = metrics.get('high60', 0)
        low60 = metrics.get('low60', 0)
        ratio60 = metrics.get('ratio60', 0)
        high120 = metrics.get('high120', 0)
        low120 = metrics.get('low120', 0)
        ratio120 = metrics.get('ratio120', 0)

        section += f"| 20日 | {high20}只 | {low20}只 | {ratio20:.2f} |\n"
        section += f"| 60日 | {high60}只 | {low60}只 | {ratio60:.2f} |\n"
        section += f"| 120日 | {high120}只 | {low120}只 | {ratio120:.2f} |\n"
        section += f"| **平均** | - | - | **{metrics.get('avg_ratio', 0):.2f}** |\n\n"

        # 市场宽度评分
        breadth_score = metrics.get('breadth_score', 50)
        trend = metrics.get('trend', '中性')

        section += "#### 💯 市场宽度评分\n\n"
        section += f"- **宽度得分**: {breadth_score}/100\n"
        section += f"- **市场趋势**: {trend}\n\n"

        # 市场强度分析
        if strength:
            section += "#### 💪 市场内部强度\n\n"
            section += f"- **强度**: {strength.get('strength', 'N/A')}\n"
            section += f"- **评分**: {strength.get('strength_score', 0)}/100\n"
            section += f"- **信号**: {strength.get('signal', 'N/A')}\n\n"

            reasoning = strength.get('reasoning', [])
            if reasoning:
                section += "**分析理由**:\n"
                for reason in reasoning:
                    section += f"- {reason}\n"
                section += "\n"

        return section

    @staticmethod
    def generate_margin_section(margin_data: Dict) -> str:
        """
        生成融资融券分析部分

        Args:
            margin_data: 融资融券数据字典

        Returns:
            Markdown格式的融资融券分析部分
        """
        if not margin_data or 'error' in margin_data:
            return "\n### 💳 融资融券分析\n\n暂无融资融券数据\n\n"

        section = "\n### 💳 融资融券分析 (散户杠杆情绪)\n\n"

        market = margin_data.get('market', 'N/A')
        metrics = margin_data.get('metrics', {})
        sentiment = margin_data.get('sentiment_analysis', {})

        if not metrics:
            return section + "暂无数据\n\n"

        # 基本信息
        section += f"**市场**: {market} | **日期**: {metrics.get('latest_date', 'N/A')}\n\n"

        # 融资融券余额
        section += "#### 💰 融资融券余额\n\n"

        margin_balance = metrics.get('latest_margin_balance', 0)
        short_balance = metrics.get('latest_short_balance', 0)
        total_balance = metrics.get('latest_total_balance', 0)
        leverage = metrics.get('leverage_ratio', 0)

        section += "| 指标 | 金额 |\n"
        section += "|------|------|\n"
        section += f"| **融资余额** | {margin_balance/1e12:.2f} 万亿 |\n"
        section += f"| **融券余额** | {short_balance/1e12:.2f} 万亿 |\n"
        section += f"| **总余额** | {total_balance/1e12:.2f} 万亿 |\n"
        section += f"| **杠杆率** | {leverage:.1f} 倍 |\n\n"

        # 变化趋势
        section += "#### 📈 变化趋势\n\n"

        change_1d = metrics.get('margin_change_pct_1d', 0)
        change_5d = metrics.get('margin_change_pct_5d', 0)
        change_20d = metrics.get('margin_change_pct_20d', 0)
        percentile = metrics.get('percentile_252d', 50)
        trend = metrics.get('trend', '震荡')

        section += "| 周期 | 变化率 |\n"
        section += "|------|--------|\n"
        section += f"| **单日** | {change_1d:+.2f}% |\n"
        section += f"| **5日** | {change_5d:+.2f}% |\n"
        section += f"| **20日** | {change_20d:+.2f}% |\n"
        section += f"| **历史分位** | {percentile:.1f}% |\n"
        section += f"| **趋势** | {trend} |\n\n"

        # 市场情绪
        if sentiment:
            section += "#### 😊 市场情绪判断\n\n"

            sentiment_level = sentiment.get('sentiment', 'N/A')
            sentiment_score = sentiment.get('sentiment_score', 50)
            signal = sentiment.get('signal', 'N/A')

            section += f"- **情绪**: {sentiment_level}\n"
            section += f"- **评分**: {sentiment_score}/100\n"
            section += f"- **信号**: {signal}\n\n"

            reasoning = sentiment.get('reasoning', [])
            if reasoning:
                section += "**判断理由**:\n"
                for reason in reasoning:
                    section += f"- {reason}\n"
                section += "\n"

        return section


if __name__ == '__main__':
    # 测试文本报告
    text_gen = TextReportGenerator()

    print(text_gen.generate_header())

    positions = {
        'sh000001': {'name': '上证指数', 'price': 3882.77, 'date': '2025-09-30'},
        'sh000300': {'name': '沪深300', 'price': 4521.33, 'date': '2025-09-30'},
    }

    print(text_gen.generate_current_positions_section(positions))

    prob_stats = {
        'period_20d': {
            'up_prob': 0.65,
            'down_prob': 0.35,
            'up_count': 26,
            'down_count': 14,
            'mean_return': 0.032,
            'median_return': 0.018,
            'sample_size': 40,
            'confidence': 0.72
        }
    }

    print(text_gen.generate_single_index_analysis(
        '上证指数',
        3882.77,
        48,
        {2007: 12, 2015: 7, 2025: 27},
        prob_stats,
        [20]
    ))
