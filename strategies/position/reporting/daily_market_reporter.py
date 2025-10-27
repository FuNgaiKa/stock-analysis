#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日市场报告生成器
Daily Market Reporter

综合所有分析器,生成每日市场总结报告:
- 三大市场概览(美股/港股/A股)
- 核心技术指标
- 资金流向分析
- 市场情绪评估
- 估值水平
- 交易建议

作者: Claude Code
日期: 2025-10-12
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategies.position.market_analyzers.us_market_analyzer import USMarketAnalyzer
from strategies.position.market_analyzers.hk_market_analyzer import HKMarketAnalyzer
from strategies.position.market_analyzers.cn_market_analyzer import CNMarketAnalyzer
from strategies.position.analyzers.market_specific.margin_trading_analyzer import MarginTradingAnalyzer
from strategies.position.analyzers.market_specific.hk_connect_analyzer import HKConnectAnalyzer
from strategies.position.analyzers.market_structure.market_breadth_analyzer import MarketBreadthAnalyzer

logger = logging.getLogger(__name__)


class DailyMarketReporter:
    """
    每日市场报告生成器

    整合三大市场分析器和专项分析器,生成综合报告
    """

    def __init__(self):
        """初始化分析器"""
        logger.info("初始化每日市场报告生成器...")

        # 三大市场分析器
        self.us_analyzer = USMarketAnalyzer()
        self.hk_analyzer = HKMarketAnalyzer()
        self.cn_analyzer = CNMarketAnalyzer()

        # A股特色分析器
        self.margin_analyzer = MarginTradingAnalyzer()
        self.hk_connect_analyzer = HKConnectAnalyzer()
        self.breadth_analyzer = MarketBreadthAnalyzer()

        logger.info("每日市场报告生成器初始化完成")

    def _analyze_us_market(self) -> Dict:
        """分析美股市场"""
        try:
            logger.info("分析美股市场...")

            # 分析纳斯达克和标普500 (使用指数代码,不是ticker符号)
            nasdaq_result = self.us_analyzer.analyze_single_index('NASDAQ')
            sp500_result = self.us_analyzer.analyze_single_index('SPX')

            return {
                'nasdaq': {
                    'close': nasdaq_result.get('current_price', 0),
                    'change_pct': nasdaq_result.get('current_change_pct', 0),
                    'technical': {},
                    'signals': {}
                },
                'sp500': {
                    'close': sp500_result.get('current_price', 0),
                    'change_pct': sp500_result.get('current_change_pct', 0),
                    'technical': {},
                    'signals': {}
                }
            }
        except Exception as e:
            logger.error(f"美股市场分析失败: {str(e)}")
            return {}

    def _analyze_hk_market(self) -> Dict:
        """分析港股市场"""
        try:
            logger.info("分析港股市场...")

            # 分析恒生指数 (使用指数代码)
            hsi_result = self.hk_analyzer.analyze_single_index('HSI')

            # 南向资金分析
            south_capital = self.hk_connect_analyzer.comprehensive_analysis(direction='south')

            return {
                'hsi': {
                    'close': hsi_result.get('current_price', 0),
                    'change_pct': hsi_result.get('current_change_pct', 0),
                    'technical': {},
                    'signals': {}
                },
                'south_capital': south_capital.get('sentiment_analysis', {})
            }
        except Exception as e:
            logger.error(f"港股市场分析失败: {str(e)}")
            return {}

    def _analyze_cn_market(self) -> Dict:
        """分析A股市场"""
        try:
            logger.info("分析A股市场...")

            # 分析上证指数和深证成指 (使用指数代码)
            sse_result = self.cn_analyzer.analyze_single_index('SSE')
            szse_result = self.cn_analyzer.analyze_single_index('SZSE')

            # 北向资金分析
            north_capital = self.hk_connect_analyzer.comprehensive_analysis(direction='north')

            # 融资融券分析
            margin_trading = self.margin_analyzer.comprehensive_analysis(market='sse')

            # 市场宽度分析
            market_breadth = self.breadth_analyzer.comprehensive_analysis()

            return {
                'sse': {
                    'close': sse_result.get('current_price', 0),
                    'change_pct': sse_result.get('current_change_pct', 0),
                    'technical': {},
                    'signals': {}
                },
                'szse': {
                    'close': szse_result.get('current_price', 0),
                    'change_pct': szse_result.get('current_change_pct', 0),
                    'technical': {}
                },
                'north_capital': north_capital.get('sentiment_analysis', {}),
                'margin_trading': margin_trading.get('sentiment_analysis', {}),
                'market_breadth': market_breadth.get('strength_analysis', {})
            }
        except Exception as e:
            logger.error(f"A股市场分析失败: {str(e)}")
            return {}

    def _calculate_composite_score(self, report: Dict) -> float:
        """
        计算综合评分(0-10分)

        Args:
            report: 完整报告数据

        Returns:
            综合评分
        """
        score = 5.0  # 基础分
        signals_count = {'bullish': 0, 'bearish': 0, 'neutral': 0}

        try:
            # A股技术信号权重最高
            cn_data = report.get('cn_market', {})
            if cn_data:
                sse_data = cn_data.get('sse', {})
                signals = sse_data.get('signals', {})

                # MACD信号
                if signals.get('macd') == 'bullish':
                    score += 0.5
                    signals_count['bullish'] += 1
                elif signals.get('macd') == 'bearish':
                    score -= 0.5
                    signals_count['bearish'] += 1

                # RSI信号
                rsi = sse_data.get('technical', {}).get('rsi')
                if rsi:
                    if rsi > 70:
                        score -= 0.3
                        signals_count['bearish'] += 1
                    elif rsi < 30:
                        score += 0.3
                        signals_count['bullish'] += 1

                # KDJ信号
                kdj_k = sse_data.get('technical', {}).get('kdj_k', 50)
                kdj_d = sse_data.get('technical', {}).get('kdj_d', 50)
                if kdj_k > kdj_d and kdj_k < 80:
                    score += 0.4
                    signals_count['bullish'] += 1
                elif kdj_k < kdj_d and kdj_k > 20:
                    score -= 0.4
                    signals_count['bearish'] += 1

                # 北向资金
                north_sentiment = cn_data.get('north_capital', {})
                north_score = north_sentiment.get('sentiment_score', 50)
                if north_score > 70:
                    score += 0.8
                    signals_count['bullish'] += 1
                elif north_score < 30:
                    score -= 0.8
                    signals_count['bearish'] += 1

                # 融资融券
                margin_sentiment = cn_data.get('margin_trading', {})
                margin_score = margin_sentiment.get('sentiment_score', 50)
                if margin_score > 65:
                    score += 0.5
                    signals_count['bullish'] += 1
                elif margin_score < 35:
                    score -= 0.5
                    signals_count['bearish'] += 1

                # 市场宽度
                breadth_strength = cn_data.get('market_breadth', {})
                breadth_score = breadth_strength.get('strength_score', 50)
                if breadth_score > 70:
                    score += 0.8
                    signals_count['bullish'] += 1
                elif breadth_score < 30:
                    score -= 0.8
                    signals_count['bearish'] += 1

            # 限制分数范围
            score = max(0, min(10, score))

        except Exception as e:
            logger.error(f"计算综合评分失败: {str(e)}")

        return score, signals_count

    def _generate_trade_suggestion(self, score: float, signals_count: Dict, report: Dict) -> Dict:
        """
        生成交易建议

        Args:
            score: 综合评分
            signals_count: 信号统计
            report: 完整报告

        Returns:
            交易建议字典
        """
        bullish_signals = []
        bearish_signals = []

        try:
            cn_data = report.get('cn_market', {})
            if cn_data:
                sse_data = cn_data.get('sse', {})
                technical = sse_data.get('technical', {})

                # 多头信号
                if technical.get('kdj_k', 0) > technical.get('kdj_d', 0):
                    bullish_signals.append('KDJ金叉')

                if cn_data.get('north_capital', {}).get('sentiment_score', 0) > 70:
                    bullish_signals.append('北向资金大幅流入')

                if cn_data.get('market_breadth', {}).get('strength_score', 0) > 70:
                    bullish_signals.append('市场宽度强劲')

                # 空头信号
                if technical.get('rsi', 50) > 70:
                    bearish_signals.append('RSI超买')

                if cn_data.get('margin_trading', {}).get('sentiment_score', 0) < 35:
                    bearish_signals.append('融资情绪低迷')

            # 根据评分生成建议
            if score >= 7.5:
                direction = '强烈看多'
                position = 0.8
                suggestion = '趋势向上,建议加大仓位至80%'
                strategy = '逢低买入,持有优质标的'
            elif score >= 6.5:
                direction = '看多'
                position = 0.7
                suggestion = '市场偏强,建议仓位70%'
                strategy = '持有为主,适当加仓'
            elif score >= 5.5:
                direction = '偏多'
                position = 0.5
                suggestion = '中性偏多,建议仓位50%'
                strategy = '保持观望,等待更明确信号'
            elif score >= 4.5:
                direction = '中性'
                position = 0.3
                suggestion = '方向不明,建议降低仓位至30%'
                strategy = '谨慎操作,控制风险'
            elif score >= 3.5:
                direction = '偏空'
                position = 0.2
                suggestion = '市场偏弱,建议仓位20%'
                strategy = '减仓为主,保留核心仓位'
            else:
                direction = '看空'
                position = 0.1
                suggestion = '趋势向下,建议降低仓位至10%'
                strategy = '空仓观望,等待趋势反转'

            # 支撑压力位(使用上证指数)
            sse_close = cn_data.get('sse', {}).get('close', 0)
            support_level = sse_close * 0.98
            resistance_level = sse_close * 1.02

            return {
                'direction': direction,
                'position': position,
                'suggestion': suggestion,
                'strategy': strategy,
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals,
                'support_level': round(support_level, 2),
                'resistance_level': round(resistance_level, 2)
            }

        except Exception as e:
            logger.error(f"生成交易建议失败: {str(e)}")
            return {
                'direction': '中性',
                'position': 0.5,
                'suggestion': '数据不足,建议谨慎操作',
                'strategy': '等待更多信号',
                'bullish_signals': [],
                'bearish_signals': [],
                'support_level': 0,
                'resistance_level': 0
            }

    def generate_daily_report(self) -> Dict:
        """
        生成每日市场报告

        Returns:
            完整的市场报告数据
        """
        try:
            logger.info("开始生成每日市场报告...")

            report = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now(),
                'us_market': self._analyze_us_market(),
                'hk_market': self._analyze_hk_market(),
                'cn_market': self._analyze_cn_market()
            }

            # 计算综合评分
            score, signals_count = self._calculate_composite_score(report)
            report['composite_score'] = score
            report['signals_count'] = signals_count

            # 生成交易建议
            report['trade_suggestion'] = self._generate_trade_suggestion(score, signals_count, report)

            logger.info("每日市场报告生成完成")
            return report

        except Exception as e:
            logger.error(f"生成每日市场报告失败: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now()
            }

    def format_text_report(self, report: Dict) -> str:
        """
        格式化为文本报告

        Args:
            report: 报告数据

        Returns:
            格式化的文本
        """
        if 'error' in report:
            return f"生成报告失败: {report['error']}"

        lines = []
        lines.append("=" * 70)
        lines.append(f"📊 每日市场总结 - {report['date']}")
        lines.append("=" * 70)

        # 三大市场概览
        lines.append("\n🌍 三大市场概览")
        lines.append("-" * 70)

        # 美股
        us_data = report.get('us_market', {})
        if us_data:
            nasdaq = us_data.get('nasdaq', {})
            sp500 = us_data.get('sp500', {})
            lines.append(f"📈 美股 (昨夜收盘)")
            lines.append(f"  纳斯达克: {nasdaq.get('close', 0):.2f} ({nasdaq.get('change_pct', 0):+.2f}%)")
            lines.append(f"  标普500: {sp500.get('close', 0):.2f} ({sp500.get('change_pct', 0):+.2f}%)")

        # 港股
        hk_data = report.get('hk_market', {})
        if hk_data:
            hsi = hk_data.get('hsi', {})
            south = hk_data.get('south_capital', {})
            lines.append(f"\n🇭🇰 港股 (今日收盘)")
            lines.append(f"  恒生指数: {hsi.get('close', 0):.2f} ({hsi.get('change_pct', 0):+.2f}%)")
            if south:
                lines.append(f"  南向资金: {south.get('sentiment', '未知')} ({south.get('sentiment_score', 0)}/100)")

        # A股
        cn_data = report.get('cn_market', {})
        if cn_data:
            sse = cn_data.get('sse', {})
            szse = cn_data.get('szse', {})
            north = cn_data.get('north_capital', {})
            lines.append(f"\n🇨🇳 A股 (今日收盘)")
            lines.append(f"  上证指数: {sse.get('close', 0):.2f} ({sse.get('change_pct', 0):+.2f}%)")
            lines.append(f"  深证成指: {szse.get('close', 0):.2f} ({szse.get('change_pct', 0):+.2f}%)")
            if north:
                lines.append(f"  北向资金: {north.get('sentiment', '未知')} ({north.get('sentiment_score', 0)}/100)")

        # 核心指标
        lines.append("\n" + "=" * 70)
        lines.append("📊 核心指标快照")
        lines.append("-" * 70)

        if cn_data:
            sse_tech = sse.get('technical', {})
            lines.append(f"✅ 技术信号 (上证指数)")
            lines.append(f"  MACD: {sse.get('signals', {}).get('macd', '未知')}")
            lines.append(f"  RSI(14): {sse_tech.get('rsi', 0):.1f}")
            lines.append(f"  KDJ: K={sse_tech.get('kdj_k', 0):.1f} D={sse_tech.get('kdj_d', 0):.1f}")

            margin = cn_data.get('margin_trading', {})
            if margin:
                lines.append(f"\n💰 资金面")
                lines.append(f"  融资余额: {margin.get('sentiment', '未知')}")

            breadth = cn_data.get('market_breadth', {})
            if breadth:
                lines.append(f"  市场宽度: {breadth.get('strength', '未知')} ({breadth.get('strength_score', 0)}/100)")

        # 交易建议
        lines.append("\n" + "=" * 70)
        lines.append("🎯 今日交易建议")
        lines.append("-" * 70)
        suggestion = report.get('trade_suggestion', {})
        lines.append(f"综合评分: {report.get('composite_score', 5):.1f}/10 ({suggestion.get('direction', '中性')})")
        lines.append(f"\n{suggestion.get('suggestion', '')}")
        lines.append(f"操作策略: {suggestion.get('strategy', '')}")
        lines.append(f"建议仓位: {suggestion.get('position', 0)*100:.0f}%")

        bullish = suggestion.get('bullish_signals', [])
        if bullish:
            lines.append(f"\n✅ 看多信号 ({len(bullish)}个)")
            for signal in bullish:
                lines.append(f"  • {signal}")

        bearish = suggestion.get('bearish_signals', [])
        if bearish:
            lines.append(f"\n⚠️ 风险提示 ({len(bearish)}个)")
            for signal in bearish:
                lines.append(f"  • {signal}")

        if suggestion.get('support_level', 0) > 0:
            lines.append(f"\n关键点位:")
            lines.append(f"  支撑位: {suggestion.get('support_level', 0):.2f}")
            lines.append(f"  压力位: {suggestion.get('resistance_level', 0):.2f}")

        lines.append("\n" + "=" * 70)
        lines.append("由 Claude Code 量化分析系统生成")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)

        return '\n'.join(lines)


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("测试每日市场报告生成器...\n")

    reporter = DailyMarketReporter()
    report = reporter.generate_daily_report()

    text_report = reporter.format_text_report(report)
    print(text_report)

    print("\n✅ 测试完成")
