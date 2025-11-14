#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史点位对比分析 - 主程序入口
整合所有功能模块，生成完整分析报告
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategies.position.core.historical_position_analyzer import (
    HistoricalPositionAnalyzer,
    ProbabilityAnalyzer,
    PositionManager,
    SUPPORTED_INDICES
)
from strategies.position.reporting.report_generator import TextReportGenerator, HTMLReportGenerator, MarkdownReportGenerator
from strategies.position.reporting.chart_generator import ChartGenerator

# 配置日志
# 确保日志目录存在
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/position_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PositionAnalysisEngine:
    """历史点位对比分析引擎"""

    def __init__(self, indices: List[str] = None):
        """
        初始化分析引擎

        Args:
            indices: 要分析的指数代码列表，None表示分析所有支持的指数
        """
        self.analyzer = HistoricalPositionAnalyzer()
        self.prob_analyzer = ProbabilityAnalyzer()
        self.position_manager = PositionManager()
        self.text_reporter = TextReportGenerator()
        self.html_reporter = HTMLReportGenerator()
        self.markdown_reporter = MarkdownReportGenerator()
        self.chart_gen = ChartGenerator()

        # 要分析的指数
        if indices is None:
            self.indices = list(SUPPORTED_INDICES.keys())
        else:
            self.indices = [idx for idx in indices if idx in SUPPORTED_INDICES]

        logger.info(f"分析引擎初始化完成，待分析指数: {', '.join(self.indices)}")

    def run_full_analysis(
        self,
        tolerance: float = 0.05,
        periods: List[int] = [5, 10, 20, 60],
        output_format: str = "markdown",
        output_dir: str = "reports"
    ) -> Dict:
        """
        执行完整分析流程

        Args:
            tolerance: 相似度容差
            periods: 分析周期
            output_format: 报告输出格式 ("text", "html", "markdown")
            output_dir: 报告输出目录

        Returns:
            分析结果字典
        """
        logger.info("=" * 80)
        logger.info("开始执行历史点位对比分析")
        logger.info("=" * 80)

        # 1. 获取当前点位
        logger.info("\n[步骤1] 获取当前市场点位...")
        positions = self.analyzer.get_current_positions()

        if not positions:
            logger.error("无法获取当前点位数据，分析终止")
            return {}

        # 2. 单指数分析
        logger.info("\n[步骤2] 执行单指数历史对比分析...")
        single_index_results = {}

        for index_code in self.indices:
            if index_code not in positions:
                continue

            logger.info(f"\n分析 {SUPPORTED_INDICES[index_code].name}...")

            try:
                result = self._analyze_single_index(
                    index_code,
                    positions[index_code]['price'],
                    tolerance,
                    periods
                )
                single_index_results[index_code] = result
            except Exception as e:
                logger.error(f"分析 {index_code} 失败: {str(e)}")
                continue

        # 3. 多指数联合分析
        logger.info("\n[步骤3] 执行多指数联合匹配分析...")
        multi_index_result = self._analyze_multi_index(
            positions,
            tolerance,
            periods
        )

        # 4. 生成综合结论
        logger.info("\n[步骤4] 生成综合分析结论...")
        conclusion = self._generate_conclusion(
            single_index_results,
            multi_index_result
        )

        # 5. 输出报告
        logger.info("\n[步骤5] 生成分析报告...")

        # 根据格式生成报告
        if output_format == "text":
            # 文本报告
            text_report = self._generate_text_report(
                positions,
                single_index_results,
                multi_index_result,
                conclusion
            )
            print("\n" + text_report)

        elif output_format == "html":
            # HTML报告
            html_report = self._generate_html_report(
                positions,
                single_index_results,
                multi_index_result,
                conclusion,
                periods
            )

            # 保存HTML
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = os.path.join(output_dir, f"position_analysis_{timestamp}.html")

            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_report)

            logger.info(f"HTML报告已保存: {html_path}")

        elif output_format == "markdown":
            # Markdown报告
            markdown_report = self._generate_markdown_report(
                positions,
                single_index_results,
                multi_index_result,
                conclusion
            )

            # 保存Markdown
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            md_path = os.path.join(output_dir, f"position_analysis_{timestamp}.md")

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_report)

            logger.info(f"Markdown报告已保存: {md_path}")

        else:
            logger.warning(f"不支持的输出格式: {output_format}，使用文本格式")
            text_report = self._generate_text_report(
                positions,
                single_index_results,
                multi_index_result,
                conclusion
            )
            print("\n" + text_report)

        logger.info("\n" + "=" * 80)
        logger.info("分析完成!")
        logger.info("=" * 80)

        return {
            'positions': positions,
            'single_index_results': single_index_results,
            'multi_index_result': multi_index_result,
            'conclusion': conclusion
        }

    def _analyze_single_index(
        self,
        index_code: str,
        current_price: float,
        tolerance: float,
        periods: List[int]
    ) -> Dict:
        """单指数分析"""

        # 查找相似时期
        similar_periods = self.analyzer.find_similar_periods(
            index_code,
            current_price,
            tolerance
        )

        if len(similar_periods) == 0:
            return {
                'similar_count': 0,
                'warning': '未找到历史相似点位'
            }

        # 计算未来收益率
        future_returns = self.analyzer.calculate_future_returns(
            index_code,
            similar_periods,
            periods
        )

        # 概率统计
        prob_stats = {}
        for period in periods:
            returns_col = f'return_{period}d'
            if returns_col in future_returns.columns:
                stats = self.prob_analyzer.calculate_probability(
                    future_returns[returns_col]
                )

                # 计算置信度
                time_diversity = self._calculate_time_diversity(similar_periods.index)
                confidence = self.prob_analyzer.calculate_confidence(
                    stats['sample_size'],
                    max(stats['up_prob'], stats['down_prob']),
                    time_diversity
                )
                stats['confidence'] = confidence

                prob_stats[f'period_{period}d'] = stats

        # 年份分布
        year_distribution = self.text_reporter.get_year_distribution(similar_periods.index)

        return {
            'similar_count': len(similar_periods),
            'similar_periods': similar_periods,
            'future_returns': future_returns,
            'prob_stats': prob_stats,
            'year_distribution': year_distribution
        }

    def _analyze_multi_index(
        self,
        positions: Dict,
        tolerance: float,
        periods: List[int]
    ) -> Dict:
        """多指数联合分析"""

        # 多指数匹配
        matched = self.analyzer.find_multi_index_match(
            positions,
            tolerance,
            min_match_count=len(positions) // 2  # 至少匹配一半
        )

        if len(matched) == 0:
            return {
                'match_count': 0,
                'warning': '未找到多指数联合匹配时期'
            }

        # 这里简化：使用第一个指数的数据来计算多指数匹配后的概率
        # 实际可以更复杂，例如计算所有匹配时期在各指数上的平均表现
        first_index = list(positions.keys())[0]

        try:
            # 获取匹配时期的未来收益率
            df = self.analyzer.get_index_data(first_index)

            multi_returns = []
            for _, row in matched.iterrows():
                date = row['date']
                if date in df.index:
                    # 计算20日后收益率
                    future_data = df[df.index > date]
                    if len(future_data) >= 20:
                        future_price = future_data['close'].iloc[19]
                        current_price = df.loc[date, 'close']
                        ret = (future_price - current_price) / current_price
                        multi_returns.append(ret)

            multi_returns = pd.Series(multi_returns)
            multi_prob_stats = self.prob_analyzer.calculate_probability(multi_returns)

            # 置信度
            time_diversity = self._calculate_time_diversity(pd.DatetimeIndex(matched['date']))
            confidence = self.prob_analyzer.calculate_confidence(
                len(multi_returns),
                max(multi_prob_stats['up_prob'], multi_prob_stats['down_prob']),
                time_diversity
            )
            multi_prob_stats['confidence'] = confidence

        except Exception as e:
            logger.warning(f"多指数概率计算失败: {str(e)}")
            multi_prob_stats = {}

        return {
            'match_count': len(matched),
            'matched_periods': matched,
            'prob_stats': multi_prob_stats
        }

    def _generate_conclusion(
        self,
        single_results: Dict,
        multi_result: Dict
    ) -> Dict:
        """生成综合结论"""

        # 汇总各指数20日概率
        up_probs = []
        confidences = []

        for index_code, result in single_results.items():
            if 'prob_stats' in result and 'period_20d' in result['prob_stats']:
                stats = result['prob_stats']['period_20d']
                up_probs.append(stats['up_prob'])
                confidences.append(stats['confidence'])

        if len(up_probs) == 0:
            return {
                'direction': '数据不足',
                'confidence': 0,
                'reasons': ['样本数据不足，无法给出结论'],
                'suggestions': {}
            }

        # 综合判断
        avg_up_prob = np.mean(up_probs)
        avg_confidence = np.mean(confidences)

        # 加入多指数结果
        if multi_result.get('prob_stats'):
            multi_up_prob = multi_result['prob_stats']['up_prob']
            multi_confidence = multi_result['prob_stats']['confidence']

            # 加权平均（多指数匹配权重更高）
            final_up_prob = 0.4 * avg_up_prob + 0.6 * multi_up_prob
            final_confidence = 0.4 * avg_confidence + 0.6 * multi_confidence
        else:
            final_up_prob = avg_up_prob
            final_confidence = avg_confidence

        # 方向判断
        if final_up_prob >= 0.65:
            direction = "看多"
        elif final_up_prob <= 0.35:
            direction = "看空"
        else:
            direction = "中性偏震荡"

        # 生成理由
        reasons = self._generate_reasons(single_results, multi_result, final_up_prob)

        # 生成建议
        suggestions = self._generate_suggestions(final_up_prob, final_confidence)

        # 仓位建议
        position_advice = self.position_manager.calculate_position_advice(
            final_up_prob,
            final_confidence,
            avg_up_prob - 0.5,  # 简化：用概率差值作为期望收益
            0.1  # 简化：固定标准差
        )

        return {
            'direction': direction,
            'confidence': final_confidence,
            'up_probability': final_up_prob,
            'reasons': reasons,
            'suggestions': suggestions,
            'position_advice': position_advice
        }

    def _generate_text_report(
        self,
        positions: Dict,
        single_results: Dict,
        multi_result: Dict,
        conclusion: Dict
    ) -> str:
        """生成文本报告"""

        report = self.text_reporter.generate_header()

        # 当前点位
        report += self.text_reporter.generate_current_positions_section(positions)

        # 单指数分析
        report += "\n[单指数历史对比分析]\n"
        for index_code, result in single_results.items():
            if 'warning' in result:
                continue

            report += self.text_reporter.generate_single_index_analysis(
                SUPPORTED_INDICES[index_code].name,
                positions[index_code]['price'],
                result['similar_count'],
                result.get('year_distribution', {}),
                result.get('prob_stats', {})
            )

        # Phase 3.3: 机构级核心指标
        phase3_data = None
        for index_code, result in single_results.items():
            if 'phase3_analysis' in result:
                phase3_data = result['phase3_analysis']
                break

        if phase3_data:
            report += "\n\n" + "=" * 80 + "\n"
            report += "[机构级核心指标]\n"
            report += "=" * 80 + "\n"

            # 估值分析
            if 'valuation' in phase3_data:
                val_data = phase3_data['valuation']
                report += f"\n【估值分析 - {val_data.get('index_name', 'N/A')}】\n"
                report += f"日期: {val_data.get('date', 'N/A')}\n"
                report += f"当前PE: {val_data.get('current_pe', 0):.2f}\n"

                if val_data.get('current_pb'):
                    report += f"当前PB: {val_data.get('current_pb', 0):.2f}\n"

                pe_percentiles = val_data.get('pe_percentiles', {})
                if pe_percentiles:
                    report += "\nPE历史分位数:\n"
                    for period, data in pe_percentiles.items():
                        report += f"  {period}: {data['percentile']:.1f}% ({data['level']})\n"

                val_level = val_data.get('valuation_level', {})
                if val_level:
                    report += f"\n估值判断: {val_level.get('emoji', '')} {val_level.get('level', '')} - {val_level.get('signal', '')}\n"
                    report += f"说明: {val_level.get('description', '')}\n"

            # 市场宽度分析
            if 'market_breadth' in phase3_data:
                breadth_data = phase3_data['market_breadth']
                metrics = breadth_data.get('metrics', {})

                if metrics:
                    report += f"\n【市场宽度分析】\n"
                    report += f"日期: {metrics.get('latest_date', 'N/A')}\n"
                    report += f"20日新高: {metrics.get('high20', 0)}只 | 新低: {metrics.get('low20', 0)}只 | 比率: {metrics.get('ratio20', 0):.2f}\n"
                    report += f"60日新高: {metrics.get('high60', 0)}只 | 新低: {metrics.get('low60', 0)}只 | 比率: {metrics.get('ratio60', 0):.2f}\n"
                    report += f"宽度得分: {metrics.get('breadth_score', 0)}/100 | 趋势: {metrics.get('trend', 'N/A')}\n"

                    strength = breadth_data.get('strength_analysis', {})
                    if strength:
                        report += f"市场强度: {strength.get('strength', 'N/A')} ({strength.get('strength_score', 0)}/100) - {strength.get('signal', 'N/A')}\n"

            # 融资融券分析
            if 'margin_trading' in phase3_data:
                margin_data = phase3_data['margin_trading']
                metrics = margin_data.get('metrics', {})

                if metrics:
                    report += f"\n【融资融券分析】\n"
                    report += f"市场: {margin_data.get('market', 'N/A')} | 日期: {metrics.get('latest_date', 'N/A')}\n"
                    report += f"融资余额: {metrics.get('latest_margin_balance', 0)/1e12:.2f} 万亿\n"
                    report += f"杠杆率: {metrics.get('leverage_ratio', 0):.1f} 倍\n"
                    report += f"单日变化: {metrics.get('margin_change_pct_1d', 0):+.2f}%\n"
                    report += f"历史分位: {metrics.get('percentile_252d', 0):.1f}%\n"

                    sentiment = margin_data.get('sentiment_analysis', {})
                    if sentiment:
                        report += f"市场情绪: {sentiment.get('sentiment', 'N/A')} ({sentiment.get('sentiment_score', 0)}/100) - {sentiment.get('signal', 'N/A')}\n"

        # 多指数分析
        report += self.text_reporter.generate_multi_index_analysis(
            multi_result.get('match_count', 0),
            multi_result.get('matched_periods', pd.DataFrame()),
            multi_result.get('prob_stats', {})
        )

        # 仓位建议
        if 'position_advice' in conclusion:
            advice = conclusion['position_advice']
            report += self.text_reporter.generate_position_advice(
                advice['signal'],
                advice['recommended_position'],
                advice['description']
            )

        # 综合结论
        report += self.text_reporter.generate_conclusion(
            conclusion['direction'],
            conclusion['confidence'],
            conclusion['reasons'],
            conclusion['suggestions']
        )

        report += self.text_reporter.generate_footer()

        return report

    def _generate_html_report(
        self,
        positions: Dict,
        single_results: Dict,
        multi_result: Dict,
        conclusion: Dict,
        periods: List[int]
    ) -> str:
        """生成HTML报告"""

        sections = {}
        charts = {}

        # 当前点位部分
        positions_html = "<div class='metrics-container'>"
        for code, info in positions.items():
            positions_html += f"""
            <div class="metric">
                <div class="metric-label">{info['name']}</div>
                <div class="metric-value">{info['price']:.2f}</div>
                <div style="font-size:0.8em;color:#666;">{info['date']}</div>
            </div>
            """
        positions_html += "</div>"
        sections['当前市场点位'] = positions_html

        # 单指数分析
        for index_code, result in single_results.items():
            if 'prob_stats' not in result:
                continue

            # 概率图表 - 传入指数名称以生成唯一div_id
            prob_chart = self.chart_gen.create_probability_chart(
                result['prob_stats'],
                periods,
                index_name=SUPPORTED_INDICES[index_code].name
            )
            charts[f"{SUPPORTED_INDICES[index_code].name} - 涨跌概率"] = prob_chart

        # Phase 3.3: 机构级核心指标
        phase3_data = None
        for index_code, result in single_results.items():
            if 'phase3_analysis' in result:
                phase3_data = result['phase3_analysis']
                break

        if phase3_data:
            # 估值分析
            if 'valuation' in phase3_data:
                val_data = phase3_data['valuation']
                val_html = f"<p><strong>{val_data.get('index_name', 'N/A')}</strong> ({val_data.get('date', 'N/A')})</p>"
                val_html += "<table>"
                val_html += "<tr><th>指标</th><th>当前值</th><th>5年分位数</th><th>估值水平</th></tr>"

                pe = val_data.get('current_pe', 0)
                pe_pct = val_data.get('pe_percentiles', {}).get('5年', {})
                percentile = pe_pct.get('percentile', 0) if pe_pct else 0
                level = pe_pct.get('level', 'N/A') if pe_pct else 'N/A'

                val_html += f"<tr><td>PE</td><td>{pe:.2f}</td><td>{percentile:.1f}%</td><td>{level}</td></tr>"

                if val_data.get('current_pb'):
                    pb = val_data.get('current_pb', 0)
                    val_html += f"<tr><td>PB</td><td>{pb:.2f}</td><td>-</td><td>-</td></tr>"

                val_html += "</table>"

                val_level = val_data.get('valuation_level', {})
                if val_level:
                    val_html += f"<p><strong>估值判断:</strong> {val_level.get('emoji', '')} {val_level.get('level', '')} - {val_level.get('signal', '')}</p>"
                    val_html += f"<p>{val_level.get('description', '')}</p>"

                sections['估值分析'] = val_html

            # 市场宽度分析
            if 'market_breadth' in phase3_data:
                breadth_data = phase3_data['market_breadth']
                metrics = breadth_data.get('metrics', {})

                if metrics:
                    breadth_html = f"<p>日期: {metrics.get('latest_date', 'N/A')}</p>"
                    breadth_html += "<table>"
                    breadth_html += "<tr><th>周期</th><th>新高</th><th>新低</th><th>比率</th></tr>"
                    breadth_html += f"<tr><td>20日</td><td>{metrics.get('high20', 0)}</td><td>{metrics.get('low20', 0)}</td><td>{metrics.get('ratio20', 0):.2f}</td></tr>"
                    breadth_html += f"<tr><td>60日</td><td>{metrics.get('high60', 0)}</td><td>{metrics.get('low60', 0)}</td><td>{metrics.get('ratio60', 0):.2f}</td></tr>"
                    breadth_html += "</table>"
                    breadth_html += f"<p><strong>宽度得分:</strong> {metrics.get('breadth_score', 0)}/100 | <strong>趋势:</strong> {metrics.get('trend', 'N/A')}</p>"

                    strength = breadth_data.get('strength_analysis', {})
                    if strength:
                        breadth_html += f"<p><strong>市场强度:</strong> {strength.get('strength', 'N/A')} ({strength.get('strength_score', 0)}/100) - {strength.get('signal', 'N/A')}</p>"

                    sections['市场宽度'] = breadth_html

            # 融资融券分析
            if 'margin_trading' in phase3_data:
                margin_data = phase3_data['margin_trading']
                metrics = margin_data.get('metrics', {})

                if metrics:
                    margin_html = f"<p>市场: {margin_data.get('market', 'N/A')} | 日期: {metrics.get('latest_date', 'N/A')}</p>"
                    margin_html += "<table>"
                    margin_html += "<tr><th>指标</th><th>金额/比率</th></tr>"
                    margin_html += f"<tr><td>融资余额</td><td>{metrics.get('latest_margin_balance', 0)/1e12:.2f} 万亿</td></tr>"
                    margin_html += f"<tr><td>杠杆率</td><td>{metrics.get('leverage_ratio', 0):.1f} 倍</td></tr>"
                    margin_html += f"<tr><td>单日变化</td><td>{metrics.get('margin_change_pct_1d', 0):+.2f}%</td></tr>"
                    margin_html += f"<tr><td>历史分位</td><td>{metrics.get('percentile_252d', 0):.1f}%</td></tr>"
                    margin_html += "</table>"

                    sentiment = margin_data.get('sentiment_analysis', {})
                    if sentiment:
                        margin_html += f"<p><strong>市场情绪:</strong> {sentiment.get('sentiment', 'N/A')} ({sentiment.get('sentiment_score', 0)}/100) - {sentiment.get('signal', 'N/A')}</p>"

                    sections['融资融券'] = margin_html

        # 置信度仪表盘
        if conclusion.get('confidence'):
            confidence_chart = self.chart_gen.create_confidence_gauge(
                conclusion['confidence']
            )
            charts['综合置信度'] = confidence_chart

        # 综合结论
        conclusion_html = f"""
        <div class="signal-badge signal-{conclusion['direction'].lower()}">
            {conclusion['direction']} (置信度 {conclusion['confidence']:.0%})
        </div>
        <h3>主要依据:</h3>
        <ul>
        """
        for reason in conclusion['reasons']:
            conclusion_html += f"<li>{reason}</li>"
        conclusion_html += "</ul>"

        sections['综合结论'] = conclusion_html

        # 生成完整HTML
        html = self.html_reporter.generate_html_report(
            "市场历史点位对比分析报告",
            sections,
            charts
        )

        return html

    def _generate_markdown_report(
        self,
        positions: Dict,
        single_results: Dict,
        multi_result: Dict,
        conclusion: Dict
    ) -> str:
        """生成Markdown报告"""

        report = self.markdown_reporter.generate_header()

        # 当前点位
        report += self.markdown_reporter.generate_current_positions_section(positions)

        # 单指数分析
        report += "\n\n"
        for index_code, result in single_results.items():
            if 'warning' in result:
                continue

            report += self.markdown_reporter.generate_single_index_analysis(
                SUPPORTED_INDICES[index_code].name,
                positions[index_code]['price'],
                result['similar_count'],
                result.get('year_distribution', {}),
                result.get('prob_stats', {})
            )

        # Phase 3.3: 机构级核心指标 (P0优先级)
        # 注意：估值、市场宽度、融资融券是全市场级别的，不针对单个指数
        # 取第一个有效结果的phase3_analysis
        phase3_data = None
        for index_code, result in single_results.items():
            if 'phase3_analysis' in result:
                phase3_data = result['phase3_analysis']
                break

        if phase3_data:
            report += "\n\n## 🏛️ 机构级核心指标\n\n"

            # 1. 估值分析
            if 'valuation' in phase3_data:
                report += self.markdown_reporter.generate_valuation_section(
                    phase3_data['valuation']
                )

            # 2. 市场宽度分析
            if 'market_breadth' in phase3_data:
                report += self.markdown_reporter.generate_breadth_section(
                    phase3_data['market_breadth']
                )

            # 3. 融资融券分析
            if 'margin_trading' in phase3_data:
                report += self.markdown_reporter.generate_margin_section(
                    phase3_data['margin_trading']
                )

        # 多指数分析
        report += self.markdown_reporter.generate_multi_index_analysis(
            multi_result.get('match_count', 0),
            multi_result.get('matched_periods', pd.DataFrame()),
            multi_result.get('prob_stats', {})
        )

        # 仓位建议
        if 'position_advice' in conclusion:
            advice = conclusion['position_advice']
            report += self.markdown_reporter.generate_position_advice(
                advice['signal'],
                advice['recommended_position'],
                advice['description']
            )

        # 综合结论
        report += self.markdown_reporter.generate_conclusion(
            conclusion['direction'],
            conclusion['confidence'],
            conclusion['reasons'],
            conclusion['suggestions']
        )

        report += self.markdown_reporter.generate_footer()

        return report

    @staticmethod
    def _calculate_time_diversity(dates: pd.DatetimeIndex) -> float:
        """计算时间分散度"""
        if len(dates) == 0:
            return 0

        years = dates.year.unique()
        # 分散在3个以上年份认为分散度高
        diversity = min(1.0, len(years) / 3)
        return diversity

    @staticmethod
    def _generate_reasons(single_results: Dict, multi_result: Dict, up_prob: float) -> List[str]:
        """生成理由列表"""
        reasons = []

        # 样本量
        total_samples = sum([r.get('similar_count', 0) for r in single_results.values()])
        reasons.append(f"历史相似点位样本共 {total_samples} 个")

        # 概率
        if up_prob >= 0.65:
            reasons.append(f"历史数据显示，相似点位后上涨概率较高({up_prob:.1%})")
        elif up_prob <= 0.35:
            reasons.append(f"历史数据显示，相似点位后下跌概率较高({1-up_prob:.1%})")
        else:
            reasons.append(f"历史数据显示，相似点位后涨跌概率相当(上涨{up_prob:.1%})")

        # 多指数匹配
        if multi_result.get('match_count', 0) > 0:
            reasons.append(f"多指数联合匹配找到 {multi_result['match_count']} 个时期")

        return reasons

    @staticmethod
    def _generate_suggestions(up_prob: float, confidence: float) -> Dict[str, str]:
        """生成操作建议"""
        suggestions = {}

        if up_prob >= 0.7 and confidence >= 0.7:
            suggestions['短期(5-10日)'] = "可适度参与，关注放量突破"
            suggestions['中期(20-60日)'] = "持有为主，逢低加仓"
        elif up_prob <= 0.3 and confidence >= 0.7:
            suggestions['短期(5-10日)'] = "谨慎为主，逢高减仓"
            suggestions['中期(20-60日)'] = "降低仓位，等待企稳信号"
        else:
            suggestions['短期(5-10日)'] = "震荡为主，不追高不杀跌"
            suggestions['中期(20-60日)'] = "保持中性仓位，等待方向明确"

        return suggestions


def run_a_stock_analysis():
    """运行A股市场分析"""
    # 创建分析引擎（包含科创50）
    # 默认分析A股主要指数（恒生科技数据源不稳定，暂时注释）
    indices_to_analyze = [
        'sh000001',  # 上证指数
        'sh000300',  # 沪深300
        'sz399006',  # 创业板指
        'sh000688',  # 科创50
        # 'hk_hstech'  # 恒生科技（数据源不稳定，需要时手动启用）
    ]

    engine = PositionAnalysisEngine(
        indices=indices_to_analyze
    )

    # 执行分析
    try:
        results = engine.run_full_analysis(
            tolerance=0.05,
            periods=[5, 10, 20, 60],
            output_format='markdown',
            output_dir='reports'
        )

        print("\n✓ 分析完成！报告已生成。")
        return 0

    except Exception as e:
        logger.error(f"分析过程出错: {str(e)}", exc_info=True)
        print(f"\n✗ 分析失败: {str(e)}")
        return 1


def run_us_stock_analysis():
    """运行美股市场分析"""
    # 导入美股分析脚本
    scripts_dir = project_root / 'scripts' / 'us_stock_analysis'
    sys.path.insert(0, str(scripts_dir))

    try:
        from run_us_analysis import run_analysis, DEFAULT_US_INDICES

        print("\n开始美股市场分析...")
        success = run_analysis(
            indices=DEFAULT_US_INDICES,
            tolerance=0.05,
            detail=True,
            periods=[5, 10, 20, 60]
        )

        return 0 if success else 1

    except Exception as e:
        logger.error(f"美股分析失败: {str(e)}", exc_info=True)
        print(f"\n✗ 美股分析失败: {str(e)}")
        return 1


def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║          历史点位对比分析系统 - Phase 1                       ║
    ║                  Historical Position Analyzer                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    print("\n请选择要分析的市场:")
    print("  1. A股市场 (上证、沪深300、创业板、科创50)")
    print("  2. 美股市场 (标普500、纳斯达克、纳斯达克100、VIX)")
    print("  3. 港股市场 (恒生指数、恒生科技)")
    print("  0. 退出")

    choice = input("\n请输入选项 (0-3): ").strip()

    if choice == '1':
        print("\n" + "=" * 70)
        print("  A股市场分析")
        print("=" * 70)
        return run_a_stock_analysis()

    elif choice == '2':
        print("\n" + "=" * 70)
        print("  美股市场分析")
        print("=" * 70)
        return run_us_stock_analysis()

    elif choice == '3':
        print("\n  ⚠️  港股分析功能正在开发中...")
        return 0

    elif choice == '0':
        print("\n  退出程序。")
        return 0

    else:
        print("\n  ✗ 无效的选项，请重新运行程序。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
