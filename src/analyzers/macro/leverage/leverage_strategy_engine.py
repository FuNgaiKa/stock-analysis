#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
杠杆策略引擎 - 集成版
整合市场分析、Kelly公式、仓位管理，输出完整的杠杆策略建议

基于docs/guides/杠杆与风险管理指南.md的理念设计
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analyzers.position.core.market_state_detector import MarketStateDetector
from src.analyzers.position.core.valuation_analyzer import ValuationAnalyzer
from src.analyzers.position.core.enhanced_data_provider import EnhancedDataProvider
from src.analyzers.position.analyzers.market_structure.sentiment_index import MarketSentimentIndex
from src.analyzers.macro.leverage.kelly_calculator import (
    kelly_criterion,
    calculate_leverage_recommendations,
    simulate_growth_rate
)
import akshare as ak

logger = logging.getLogger(__name__)


class LeverageStrategyEngine:
    """
    杠杆策略引擎

    核心功能:
    1. 五维度市场评分 (从13维度聚合)
    2. Kelly公式杠杆计算
    3. 市场环境识别
    4. 综合杠杆建议
    5. 实战操作指导
    """

    def __init__(self):
        """初始化引擎"""
        self.market_detector = MarketStateDetector()
        self.valuation_analyzer = ValuationAnalyzer()
        self.sentiment_analyzer = MarketSentimentIndex()
        self.data_provider = EnhancedDataProvider()

        logger.info("杠杆策略引擎初始化完成")

    # ==================== 五维度评分系统 ====================

    def calculate_five_dimensions_score(
        self,
        market_state_result: Dict,
        sentiment_result: Dict = None
    ) -> Dict:
        """
        将13维度评分聚合为5大维度

        五维度映射:
        1. 估值维度: valuation
        2. 政策维度: capital_flow (北向资金作为政策宽松的代理指标)
        3. 情绪维度: sentiment, breadth, leverage
        4. 技术维度: trend, price_change, technical, slope
        5. 资金维度: main_fund, institution, volume

        Args:
            market_state_result: MarketStateDetector的输出
            sentiment_result: MarketSentimentIndex的输出(可选)

        Returns:
            {
                'valuation': {'score': 0.6, 'level': '低估', 'description': '...'},
                'policy': {...},
                'sentiment': {...},
                'technical': {...},
                'capital': {...},
                'overall_score': 0.55,
                'overall_rating': '偏多'
            }
        """
        dimension_scores = market_state_result.get('dimension_scores', {})

        # 1. 估值维度
        valuation_score = dimension_scores.get('valuation', 0)
        valuation = self._interpret_dimension(
            valuation_score,
            dim_name='估值',
            positive_desc='低估，安全边际高',
            negative_desc='高估，泡沫风险',
            threshold_high=0.5,
            threshold_low=-0.5
        )

        # 2. 政策维度 (用北向资金 + 融资融券作为代理)
        policy_score = (
            dimension_scores.get('capital_flow', 0) * 0.6 +
            dimension_scores.get('leverage', 0) * 0.4
        )
        policy = self._interpret_dimension(
            policy_score,
            dim_name='政策',
            positive_desc='政策宽松，资金充裕',
            negative_desc='政策收紧，资金撤离',
            threshold_high=0.4,
            threshold_low=-0.4
        )

        # 3. 情绪维度
        sentiment_score = (
            dimension_scores.get('sentiment', 0) * 0.4 +
            dimension_scores.get('breadth', 0) * 0.3 +
            dimension_scores.get('leverage', 0) * 0.3
        )

        # 如果有外部情绪数据，整合进来
        if sentiment_result:
            external_sentiment = (sentiment_result.get('sentiment_score', 50) - 50) / 50
            sentiment_score = sentiment_score * 0.7 + external_sentiment * 0.3

        sentiment = self._interpret_dimension(
            sentiment_score,
            dim_name='情绪',
            positive_desc='市场情绪乐观，参与度高',
            negative_desc='市场情绪低迷，恐慌抛售',
            threshold_high=0.6,
            threshold_low=-0.6,
            warning_high='情绪过热，警惕回调',
            warning_threshold_high=0.8
        )

        # 4. 技术维度
        technical_score = (
            dimension_scores.get('trend', 0) * 0.35 +
            dimension_scores.get('price_change', 0) * 0.25 +
            dimension_scores.get('technical', 0) * 0.20 +
            dimension_scores.get('slope', 0) * 0.20
        )
        technical = self._interpret_dimension(
            technical_score,
            dim_name='技术',
            positive_desc='趋势强劲，技术形态良好',
            negative_desc='趋势破位，技术形态恶化',
            threshold_high=0.5,
            threshold_low=-0.5
        )

        # 5. 资金维度
        capital_score = (
            dimension_scores.get('main_fund', 0) * 0.4 +
            dimension_scores.get('institution', 0) * 0.3 +
            dimension_scores.get('volume', 0) * 0.3
        )
        capital = self._interpret_dimension(
            capital_score,
            dim_name='资金',
            positive_desc='主力资金流入，机构加仓',
            negative_desc='主力资金流出，机构减仓',
            threshold_high=0.4,
            threshold_low=-0.4
        )

        # 综合评分 (五维度加权平均)
        weights = {
            'valuation': 0.25,   # 估值最重要
            'policy': 0.20,      # 政策次之
            'sentiment': 0.15,   # 情绪
            'technical': 0.20,   # 技术
            'capital': 0.20      # 资金
        }

        overall_score = (
            valuation_score * weights['valuation'] +
            policy_score * weights['policy'] +
            sentiment_score * weights['sentiment'] +
            technical_score * weights['technical'] +
            capital_score * weights['capital']
        )

        # 评级
        if overall_score > 0.6:
            overall_rating = '极度看多'
            rating_emoji = '🔥🔥🔥'
        elif overall_score > 0.3:
            overall_rating = '偏多'
            rating_emoji = '📈'
        elif overall_score > -0.3:
            overall_rating = '中性'
            rating_emoji = '😐'
        elif overall_score > -0.6:
            overall_rating = '偏空'
            rating_emoji = '📉'
        else:
            overall_rating = '极度看空'
            rating_emoji = '💀'

        return {
            'valuation': valuation,
            'policy': policy,
            'sentiment': sentiment,
            'technical': technical,
            'capital': capital,
            'overall_score': float(overall_score),
            'overall_rating': overall_rating,
            'rating_emoji': rating_emoji,
            'weights': weights,
            'timestamp': datetime.now()
        }

    def _interpret_dimension(
        self,
        score: float,
        dim_name: str,
        positive_desc: str,
        negative_desc: str,
        threshold_high: float = 0.5,
        threshold_low: float = -0.5,
        warning_high: str = None,
        warning_threshold_high: float = 0.8
    ) -> Dict:
        """解释单个维度得分"""

        # 评级
        if score > warning_threshold_high and warning_high:
            level = '警告'
            description = warning_high
            emoji = '⚠️'
        elif score > threshold_high:
            level = '优秀'
            description = positive_desc
            emoji = '✅'
        elif score > 0:
            level = '良好'
            description = positive_desc
            emoji = '👍'
        elif score > threshold_low:
            level = '一般'
            description = '中性偏弱'
            emoji = '😐'
        elif score > -warning_threshold_high:
            level = '较差'
            description = negative_desc
            emoji = '👎'
        else:
            level = '极差'
            description = negative_desc
            emoji = '❌'

        return {
            'dimension': dim_name,
            'score': float(score),
            'level': level,
            'description': description,
            'emoji': emoji
        }

    # ==================== Kelly公式集成 ====================

    def calculate_kelly_based_leverage(
        self,
        five_dimensions_score: Dict,
        market_state: str,
        historical_win_rate: float = None,
        historical_avg_win: float = None,
        historical_avg_loss: float = None
    ) -> Dict:
        """
        基于五维度评分和Kelly公式计算杠杆建议

        核心逻辑:
        1. 如果有历史胜率数据，直接使用Kelly公式
        2. 如果没有，根据五维度评分推算胜率和盈亏比
        3. 结合市场状态调整杠杆上限

        Args:
            five_dimensions_score: 五维度评分结果
            market_state: 市场状态 ('牛市初期', '牛市中期', ...)
            historical_win_rate: 历史胜率(可选)
            historical_avg_win: 历史平均盈利(可选)
            historical_avg_loss: 历史平均亏损(可选)

        Returns:
            Kelly杠杆建议 + 调整后的实战建议
        """
        overall_score = five_dimensions_score['overall_score']

        # 1. 推算胜率和盈亏比 (如果没有历史数据)
        if historical_win_rate is None:
            # 根据五维度评分推算胜率
            # 综合得分 0.6 → 胜率 65%, 综合得分 -0.6 → 胜率 35%
            estimated_win_rate = 0.5 + overall_score * 0.25
            estimated_win_rate = max(0.3, min(0.7, estimated_win_rate))
        else:
            estimated_win_rate = historical_win_rate

        if historical_avg_win is None:
            # 根据市场状态推算盈亏比
            if '牛市' in market_state:
                estimated_avg_win = 0.08  # 牛市平均盈利8%
                estimated_avg_loss = 0.04  # 牛市平均亏损4%
            elif '熊市' in market_state:
                estimated_avg_win = 0.05  # 熊市平均盈利5%
                estimated_avg_loss = 0.06  # 熊市平均亏损6%
            else:
                estimated_avg_win = 0.06  # 震荡市平均盈利6%
                estimated_avg_loss = 0.05  # 震荡市平均亏损5%
        else:
            estimated_avg_win = historical_avg_win
            estimated_avg_loss = historical_avg_loss

        # 2. 计算Kelly杠杆
        kelly_result = calculate_leverage_recommendations(
            estimated_win_rate,
            estimated_avg_win,
            estimated_avg_loss
        )

        # 3. 市场状态调整
        # 在不同市场状态下，应用不同的Kelly折扣系数
        state_kelly_multiplier = {
            '牛市初期': 1.0,      # 底部启动，可以Full Kelly
            '牛市中期': 0.5,      # 主升浪，Half Kelly
            '牛市末期': 0.0,      # 顶部风险，不加杠杆
            '上行震荡': 0.25,     # Quarter Kelly
            '横盘震荡': 0.0,      # 不加杠杆
            '下行震荡': 0.0,      # 不加杠杆
            '熊市中期': 0.0,      # 不加杠杆
            '熊市末期': 0.5       # 底部区域，可以Half Kelly
        }

        multiplier = state_kelly_multiplier.get(market_state, 0.25)

        # 4. 情绪过热惩罚
        sentiment_score = five_dimensions_score['sentiment']['score']
        if sentiment_score > 0.8:
            # 情绪过热，杠杆打折
            multiplier *= 0.5

        # 5. 计算最终建议杠杆
        base_kelly = kelly_result['full_kelly']
        adjusted_kelly = base_kelly * multiplier
        recommended_leverage = 1.0 + adjusted_kelly

        # 限制在合理范围 (1.0-2.0)
        recommended_leverage = max(1.0, min(2.0, recommended_leverage))

        return {
            'estimated_win_rate': float(estimated_win_rate),
            'estimated_avg_win': float(estimated_avg_win),
            'estimated_avg_loss': float(estimated_avg_loss),
            'full_kelly': float(base_kelly),
            'kelly_multiplier': float(multiplier),
            'kelly_multiplier_reason': self._get_multiplier_reason(market_state, sentiment_score),
            'recommended_kelly_position': float(adjusted_kelly),
            'recommended_leverage': float(recommended_leverage),
            'kelly_raw_result': kelly_result
        }

    def _get_multiplier_reason(self, market_state: str, sentiment_score: float) -> str:
        """解释Kelly折扣系数的原因"""
        reasons = []

        if '牛市初期' in market_state:
            reasons.append('牛市初期，底部启动，可以Full Kelly')
        elif '牛市中期' in market_state:
            reasons.append('牛市中期，使用Half Kelly控制风险')
        elif '牛市末期' in market_state:
            reasons.append('牛市末期，风险极高，不建议加杠杆')
        elif '熊市末期' in market_state:
            reasons.append('熊市末期，底部区域，可适度加杠杆')
        elif '熊市' in market_state:
            reasons.append('熊市中，不建议加杠杆')
        else:
            reasons.append('震荡市，谨慎使用Quarter Kelly')

        if sentiment_score > 0.8:
            reasons.append('市场情绪过热，杠杆打折50%')

        return '；'.join(reasons)

    # ==================== 综合杠杆策略 ====================

    def generate_comprehensive_leverage_strategy(
        self,
        index_code: str = 'sh000001',
        index_name: str = '上证指数',
        historical_win_rate: float = None,
        historical_avg_win: float = None,
        historical_avg_loss: float = None,
        include_detailed_analysis: bool = True
    ) -> Dict:
        """
        生成完整的杠杆策略报告

        包含:
        1. 五维度市场评分
        2. Kelly公式杠杆建议
        3. 市场状态判断
        4. 综合杠杆建议
        5. 实战操作指导

        Returns:
            完整的策略报告字典
        """
        logger.info(f"开始生成{index_name}的杠杆策略...")

        report = {
            'index_code': index_code,
            'index_name': index_name,
            'generated_at': datetime.now(),
            'analysis_sections': {}
        }

        try:
            # 1. 获取真实市场状态（自动降级到模拟数据）
            real_market_state = self._fetch_real_market_state(index_code)

            # 2. 五维度评分
            five_dimensions = self.calculate_five_dimensions_score(real_market_state)
            report['analysis_sections']['five_dimensions'] = five_dimensions

            # 3. Kelly杠杆计算
            market_state = real_market_state['state']
            kelly_leverage = self.calculate_kelly_based_leverage(
                five_dimensions,
                market_state,
                historical_win_rate,
                historical_avg_win,
                historical_avg_loss
            )
            report['analysis_sections']['kelly_leverage'] = kelly_leverage

            # 4. 市场状态
            report['analysis_sections']['market_state'] = {
                'state': market_state,
                'state_description': real_market_state['state_description'],
                'confidence': real_market_state['confidence']
            }

            # 5. 综合建议
            comprehensive_advice = self._generate_comprehensive_advice(
                five_dimensions,
                kelly_leverage,
                market_state
            )
            report['analysis_sections']['comprehensive_advice'] = comprehensive_advice

            # 6. 实战指导
            if include_detailed_analysis:
                practical_guide = self._generate_practical_guide(
                    five_dimensions,
                    kelly_leverage,
                    market_state
                )
                report['analysis_sections']['practical_guide'] = practical_guide

            logger.info("杠杆策略生成完成")
            return report

        except Exception as e:
            logger.error(f"生成杠杆策略失败: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return report

    def _fetch_real_market_state(self, index_code: str) -> Dict:
        """
        获取真实市场状态数据

        Args:
            index_code: 指数代码，如 'sh000001'

        Returns:
            市场状态字典，格式与 MarketStateDetector.detect_market_state() 输出一致
        """
        try:
            logger.info(f"正在获取 {index_code} 的真实市场数据...")

            # 1. 获取价格数据
            df_price = ak.stock_zh_index_daily(symbol=index_code)
            df_price['date'] = pd.to_datetime(df_price['date'])
            df_price = df_price.set_index('date').sort_index()

            # 2. 获取各维度指标（参考 run_phase3_state_detection.py）
            ma_metrics = self.data_provider.get_moving_averages(index_code)
            valuation_metrics = self.data_provider.get_valuation_metrics()
            capital_flow_metrics = self.data_provider.get_north_capital_flow()
            sentiment_metrics = self.data_provider.get_market_sentiment()
            breadth_metrics = self.data_provider.get_market_breadth_metrics()
            margin_metrics = self.data_provider.get_margin_trading_metrics()
            main_fund_metrics = self.data_provider.get_main_fund_flow(index_code)
            lhb_metrics = self.data_provider.get_dragon_tiger_list_metrics()
            volatility_metrics = self.data_provider.get_volatility_metrics(index_code)
            volume_metrics = self.data_provider.get_volume_metrics(index_code)
            technical_metrics = self.data_provider.get_technical_indicators(index_code)

            # 3. 调用市场状态检测器
            result = self.market_detector.detect_market_state(
                ma_metrics=ma_metrics,
                price_data=df_price,
                valuation_metrics=valuation_metrics,
                capital_flow_metrics=capital_flow_metrics,
                sentiment_metrics=sentiment_metrics,
                breadth_metrics=breadth_metrics,
                margin_metrics=margin_metrics,
                main_fund_metrics=main_fund_metrics,
                lhb_metrics=lhb_metrics,
                volatility_metrics=volatility_metrics,
                volume_metrics=volume_metrics,
                technical_metrics=technical_metrics
            )

            logger.info(f"真实市场数据获取成功: {result.get('state', 'Unknown')}")
            return result

        except Exception as e:
            logger.error(f"获取真实市场数据失败: {str(e)}")
            logger.warning("降级使用模拟数据")
            return self._get_mock_market_state()

    def _get_mock_market_state(self) -> Dict:
        """获取模拟市场状态数据 (用于演示或降级)"""
        return {
            'state': '上行震荡',
            'state_description': '震荡向上，多头占优',
            'confidence': 0.72,
            'overall_score': 0.35,
            'dimension_scores': {
                'trend': 0.5,
                'price_change': 0.3,
                'valuation': 0.4,     # 估值合理
                'capital_flow': 0.2,  # 北向资金小幅流入
                'sentiment': 0.3,     # 情绪正常偏乐观
                'breadth': 0.4,
                'leverage': 0.1,
                'main_fund': 0.3,
                'institution': 0.2,
                'volatility': 0.1,
                'volume': 0.2,
                'technical': 0.4,
                'slope': 0.3
            }
        }

    def _generate_comprehensive_advice(
        self,
        five_dimensions: Dict,
        kelly_leverage: Dict,
        market_state: str
    ) -> Dict:
        """生成综合建议"""

        overall_score = five_dimensions['overall_score']
        recommended_leverage = kelly_leverage['recommended_leverage']

        # 判断操作方向
        if overall_score > 0.5:
            direction = '积极做多'
            direction_emoji = '🚀'
        elif overall_score > 0.2:
            direction = '偏多，标准配置'
            direction_emoji = '📈'
        elif overall_score > -0.2:
            direction = '中性，观望为主'
            direction_emoji = '😐'
        elif overall_score > -0.5:
            direction = '偏空，降低仓位'
            direction_emoji = '📉'
        else:
            direction = '空仓观望'
            direction_emoji = '💀'

        # 杠杆建议
        if recommended_leverage <= 1.0:
            leverage_advice = f'不建议加杠杆 (杠杆={recommended_leverage:.2f}x)'
            leverage_explanation = '当前市场环境不适合加杠杆，保持满仓或降低仓位'
        elif recommended_leverage <= 1.2:
            leverage_advice = f'可适度加杠杆 (杠杆={recommended_leverage:.2f}x)'
            leverage_explanation = '市场环境一般，可小幅加杠杆，但需严格止损'
        elif recommended_leverage <= 1.5:
            leverage_advice = f'建议加杠杆 (杠杆={recommended_leverage:.2f}x)'
            leverage_explanation = '市场环境较好，可以适度加杠杆'
        else:
            leverage_advice = f'可大胆加杠杆 (杠杆={recommended_leverage:.2f}x)'
            leverage_explanation = '市场环境极佳，可以大胆加杠杆，但仍需注意风险控制'

        # 风险提示
        warnings = []
        if five_dimensions['sentiment']['score'] > 0.7:
            warnings.append('⚠️ 市场情绪过热，警惕回调风险')
        if five_dimensions['valuation']['score'] < -0.5:
            warnings.append('⚠️ 估值过高，泡沫风险')
        if market_state in ['牛市末期', '熊市中期']:
            warnings.append('⚠️ 市场处于不利阶段，建议降低杠杆')

        return {
            'direction': direction,
            'direction_emoji': direction_emoji,
            'overall_score': float(overall_score),
            'leverage_advice': leverage_advice,
            'leverage_explanation': leverage_explanation,
            'recommended_leverage': float(recommended_leverage),
            'warnings': warnings,
            'key_factors': self._extract_key_factors(five_dimensions)
        }

    def _extract_key_factors(self, five_dimensions: Dict) -> List[str]:
        """提取关键因素"""
        factors = []

        for dim_name in ['valuation', 'policy', 'sentiment', 'technical', 'capital']:
            dim_data = five_dimensions[dim_name]
            if dim_data['score'] > 0.4:
                factors.append(f"{dim_data['emoji']} {dim_data['dimension']}: {dim_data['description']}")
            elif dim_data['score'] < -0.4:
                factors.append(f"{dim_data['emoji']} {dim_data['dimension']}: {dim_data['description']}")

        return factors[:5]  # 最多5个

    def _generate_practical_guide(
        self,
        five_dimensions: Dict,
        kelly_leverage: Dict,
        market_state: str
    ) -> Dict:
        """生成实战操作指导"""

        recommended_leverage = kelly_leverage['recommended_leverage']

        # 建仓策略
        if recommended_leverage >= 1.3:
            entry_strategy = '分3批建仓：第一批50%，第二批30%，第三批20%'
            entry_timing = '第一批立即建仓，后续批次等待回调5%时加仓'
        elif recommended_leverage >= 1.1:
            entry_strategy = '分2批建仓：第一批60%，第二批40%'
            entry_timing = '第一批立即建仓，第二批等待确认趋势后加仓'
        else:
            entry_strategy = '一次性建仓'
            entry_timing = '等待明确信号后再建仓'

        # 止损策略
        if '牛市' in market_state:
            stop_loss = '止损位：-8%（牛市容忍度高）'
        elif '熊市' in market_state:
            stop_loss = '止损位：-5%（熊市严格止损）'
        else:
            stop_loss = '止损位：-6%（震荡市中等止损）'

        # 止盈策略
        if recommended_leverage >= 1.5:
            take_profit = '分批止盈：+15%减仓1/3，+25%减仓1/3，+35%全部清仓'
        elif recommended_leverage >= 1.2:
            take_profit = '分批止盈：+20%减仓1/2，+35%全部清仓'
        else:
            take_profit = '长期持有，根据市场状态变化调整'

        # 加仓条件
        add_conditions = []
        if five_dimensions['technical']['score'] > 0.3:
            add_conditions.append('突破关键压力位时加仓')
        if five_dimensions['valuation']['score'] > 0.4:
            add_conditions.append('估值回落至安全区域时加仓')
        if five_dimensions['sentiment']['score'] < 0:
            add_conditions.append('市场恐慌性下跌时逢低加仓')

        # 减仓条件
        reduce_conditions = []
        if five_dimensions['sentiment']['score'] > 0.7:
            reduce_conditions.append('市场情绪过热时减仓')
        if five_dimensions['technical']['score'] < -0.3:
            reduce_conditions.append('技术形态破位时减仓')
        if five_dimensions['valuation']['score'] < -0.5:
            reduce_conditions.append('估值过高时减仓')

        return {
            'entry_strategy': entry_strategy,
            'entry_timing': entry_timing,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'add_conditions': add_conditions if add_conditions else ['无明确加仓信号'],
            'reduce_conditions': reduce_conditions if reduce_conditions else ['无明确减仓信号'],
            'position_management': f'建议仓位: {recommended_leverage*100-100:.0f}% 杠杆'
        }

    # ==================== 报告输出 ====================

    def print_strategy_report(self, report: Dict):
        """打印策略报告 (控制台输出)"""

        print("\n" + "=" * 80)
        print(f"  杠杆策略分析报告 - {report['index_name']}")
        print(f"  生成时间: {report['generated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # 1. 市场状态
        if 'market_state' in report['analysis_sections']:
            market_state = report['analysis_sections']['market_state']
            print(f"\n【市场状态】")
            print(f"  状态: {market_state['state']} ({market_state['state_description']})")
            print(f"  置信度: {market_state['confidence']:.1%}")

        # 2. 五维度评分
        if 'five_dimensions' in report['analysis_sections']:
            five_dim = report['analysis_sections']['five_dimensions']
            print(f"\n【五维度评分】")
            print(f"  综合评分: {five_dim['overall_score']:.2f} {five_dim['rating_emoji']} ({five_dim['overall_rating']})")
            print(f"\n  各维度详情:")
            for dim_name in ['valuation', 'policy', 'sentiment', 'technical', 'capital']:
                dim = five_dim[dim_name]
                print(f"    {dim['emoji']} {dim['dimension']}: {dim['score']:+.2f} ({dim['level']}) - {dim['description']}")

        # 3. Kelly杠杆建议
        if 'kelly_leverage' in report['analysis_sections']:
            kelly = report['analysis_sections']['kelly_leverage']
            print(f"\n【Kelly公式分析】")
            print(f"  估算胜率: {kelly['estimated_win_rate']:.1%}")
            print(f"  估算盈亏比: {kelly['estimated_avg_win']:.1%} / {kelly['estimated_avg_loss']:.1%}")
            print(f"  Full Kelly: {kelly['full_kelly']:.2%}")
            print(f"  Kelly折扣系数: {kelly['kelly_multiplier']:.2f}x ({kelly['kelly_multiplier_reason']})")
            print(f"  推荐Kelly仓位: {kelly['recommended_kelly_position']:.2%}")

        # 4. 综合建议
        if 'comprehensive_advice' in report['analysis_sections']:
            advice = report['analysis_sections']['comprehensive_advice']
            print(f"\n【综合建议】")
            print(f"  操作方向: {advice['direction_emoji']} {advice['direction']}")
            print(f"  杠杆建议: {advice['leverage_advice']}")
            print(f"  说明: {advice['leverage_explanation']}")

            if advice['warnings']:
                print(f"\n  ⚠️ 风险警告:")
                for warning in advice['warnings']:
                    print(f"    {warning}")

            print(f"\n  关键因素:")
            for factor in advice['key_factors']:
                print(f"    {factor}")

        # 5. 实战指导
        if 'practical_guide' in report['analysis_sections']:
            guide = report['analysis_sections']['practical_guide']
            print(f"\n【实战操作指导】")
            print(f"  建仓策略: {guide['entry_strategy']}")
            print(f"  建仓时机: {guide['entry_timing']}")
            print(f"  止损策略: {guide['stop_loss']}")
            print(f"  止盈策略: {guide['take_profit']}")

            print(f"\n  加仓条件:")
            for cond in guide['add_conditions']:
                print(f"    • {cond}")

            print(f"\n  减仓条件:")
            for cond in guide['reduce_conditions']:
                print(f"    • {cond}")

        print("\n" + "=" * 80)
        print("  报告结束")
        print("=" * 80 + "\n")


# ==================== 主程序 ====================

def main():
    """主函数 - 演示用法"""

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║          杠杆策略引擎 - Leverage Strategy Engine              ║
    ║                  整合 Kelly + 五维度评分                       ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    # 创建引擎
    engine = LeverageStrategyEngine()

    # 生成策略报告
    report = engine.generate_comprehensive_leverage_strategy(
        index_code='sh000001',
        index_name='上证指数',
        historical_win_rate=0.55,  # 可选：如果有历史数据
        historical_avg_win=0.08,
        historical_avg_loss=0.05,
        include_detailed_analysis=True
    )

    # 打印报告
    engine.print_strategy_report(report)

    print("\n💡 提示:")
    print("  - 当前使用模拟数据演示框架")
    print("  - 实际使用时需要接入真实市场数据")
    print("  - 可通过 MarketStateDetector 获取完整的市场分析")


if __name__ == '__main__':
    main()
