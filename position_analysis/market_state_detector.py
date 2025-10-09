#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场状态检测器 - Phase 3.1
基于12维度评分模型,自动识别市场所处阶段
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class MarketStateDetector:
    """市场状态检测器"""

    def __init__(self):
        """初始化"""
        self.dimension_weights = {
            'trend': 0.15,          # 1. 趋势 (均线排列)
            'price_change': 0.10,   # 2. 涨跌幅
            'valuation': 0.12,      # 3. 估值
            'capital_flow': 0.10,   # 4. 北向资金
            'sentiment': 0.08,      # 5. 情绪
            'breadth': 0.08,        # 6. 市场宽度
            'leverage': 0.08,       # 7. 融资融券
            'main_fund': 0.10,      # 8. 主力资金
            'institution': 0.05,    # 9. 机构行为
            'volatility': 0.05,     # 10. 波动率
            'volume': 0.05,         # 11. 成交量
            'technical': 0.04       # 12. 技术形态
        }

        logger.info("市场状态检测器初始化完成")

    def detect_market_state(
        self,
        ma_metrics: Dict,
        price_data: pd.DataFrame,
        valuation_metrics: Dict,
        capital_flow_metrics: Dict,
        sentiment_metrics: Dict,
        breadth_metrics: Dict,
        margin_metrics: Dict,
        main_fund_metrics: Dict,
        lhb_metrics: Dict,
        volatility_metrics: Dict,
        volume_metrics: Dict,
        technical_metrics: Dict
    ) -> Dict:
        """
        检测市场状态

        Returns:
            {
                'state': '牛市中期',
                'confidence': 0.85,
                'overall_score': 0.65,
                'dimension_scores': {...},
                'key_signals': ['主力持续流入', '估值合理偏低'],
                'risk_alerts': ['融资余额过高', '情绪过热']
            }
        """
        try:
            # 1. 计算12个维度的得分
            dimension_scores = {}

            # 1.1 趋势得分 (均线排列)
            dimension_scores['trend'] = self._score_trend(ma_metrics)

            # 1.2 涨跌幅得分
            dimension_scores['price_change'] = self._score_price_change(price_data)

            # 1.3 估值得分
            dimension_scores['valuation'] = self._score_valuation(valuation_metrics)

            # 1.4 资金流向得分 (北向资金)
            dimension_scores['capital_flow'] = self._score_capital_flow(capital_flow_metrics)

            # 1.5 情绪得分
            dimension_scores['sentiment'] = self._score_sentiment(sentiment_metrics)

            # 1.6 市场宽度得分
            dimension_scores['breadth'] = self._score_breadth(breadth_metrics)

            # 1.7 杠杆得分 (融资融券)
            dimension_scores['leverage'] = self._score_leverage(margin_metrics)

            # 1.8 主力资金得分
            dimension_scores['main_fund'] = self._score_main_fund(main_fund_metrics)

            # 1.9 机构行为得分
            dimension_scores['institution'] = self._score_institution(lhb_metrics)

            # 1.10 波动率得分
            dimension_scores['volatility'] = self._score_volatility(volatility_metrics)

            # 1.11 成交量得分
            dimension_scores['volume'] = self._score_volume(volume_metrics)

            # 1.12 技术形态得分
            dimension_scores['technical'] = self._score_technical(technical_metrics)

            # 2. 加权综合评分 (-1到+1, 负数看空, 正数看多)
            overall_score = sum(
                dimension_scores[dim] * self.dimension_weights[dim]
                for dim in self.dimension_weights.keys()
                if dim in dimension_scores
            )

            # 3. 状态映射
            state, state_description = self._map_score_to_state(overall_score, dimension_scores)

            # 4. 计算置信度
            confidence = self._calculate_confidence(dimension_scores)

            # 5. 提取关键信号
            key_signals = self._extract_key_signals(dimension_scores)

            # 6. 提取风险警告
            risk_alerts = self._extract_risk_alerts(dimension_scores)

            return {
                'state': state,
                'state_description': state_description,
                'confidence': float(confidence),
                'overall_score': float(overall_score),
                'dimension_scores': {k: float(v) for k, v in dimension_scores.items()},
                'key_signals': key_signals,
                'risk_alerts': risk_alerts
            }

        except Exception as e:
            logger.error(f"市场状态检测失败: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return {}

    def _score_trend(self, ma_metrics: Dict) -> float:
        """
        趋势得分 (基于均线排列)

        Returns:
            -1到+1, -1极度空头, +1极度多头
        """
        if not ma_metrics:
            return 0.0

        ma_arrangement = ma_metrics.get('ma_arrangement', '')
        trend_strength = ma_metrics.get('trend_strength', 0)

        # 基础得分
        if '完美多头' in ma_arrangement:
            base_score = 1.0
        elif '多头' in ma_arrangement:
            base_score = 0.6
        elif '完美空头' in ma_arrangement:
            base_score = -1.0
        elif '空头' in ma_arrangement:
            base_score = -0.6
        else:  # 粘合/交叉
            base_score = 0.0

        # 趋势强度调整
        strength_adjustment = min(0.3, trend_strength / 10 * 0.3)

        return max(-1, min(1, base_score + (strength_adjustment if base_score > 0 else -strength_adjustment)))

    def _score_price_change(self, price_data: pd.DataFrame) -> float:
        """
        涨跌幅得分

        Returns:
            -1到+1
        """
        if price_data is None or len(price_data) == 0:
            return 0.0

        try:
            # 计算近20日和60日涨跌幅
            current_price = price_data['close'].iloc[-1]
            price_20d_ago = price_data['close'].iloc[-20] if len(price_data) >= 20 else price_data['close'].iloc[0]
            price_60d_ago = price_data['close'].iloc[-60] if len(price_data) >= 60 else price_data['close'].iloc[0]

            change_20d = (current_price - price_20d_ago) / price_20d_ago
            change_60d = (current_price - price_60d_ago) / price_60d_ago

            # 综合评分 (20日权重0.6, 60日权重0.4)
            score = change_20d * 0.6 + change_60d * 0.4

            # 标准化到-1到+1 (±30%为极值)
            normalized_score = max(-1, min(1, score / 0.3))

            return normalized_score

        except Exception as e:
            logger.warning(f"计算涨跌幅得分失败: {str(e)}")
            return 0.0

    def _score_valuation(self, valuation_metrics: Dict) -> float:
        """
        估值得分

        Returns:
            -1到+1, -1极度高估, +1极度低估
        """
        if not valuation_metrics:
            return 0.0

        pe_pct = valuation_metrics.get('pe_percentile_10y', 0.5)
        pb_pct = valuation_metrics.get('pb_percentile_10y', 0.5)

        avg_pct = (pe_pct + pb_pct) / 2

        # 估值分位数越高,得分越低
        # 20%分位 → +0.8, 50%分位 → 0, 80%分位 → -0.8
        score = (0.5 - avg_pct) * 2

        return max(-1, min(1, score))

    def _score_capital_flow(self, capital_flow_metrics: Dict) -> float:
        """
        北向资金得分

        Returns:
            -1到+1
        """
        if not capital_flow_metrics:
            return 0.0

        cumulative_5d = capital_flow_metrics.get('cumulative_5d', 0)
        cumulative_20d = capital_flow_metrics.get('cumulative_20d', 0)

        # 5日流入权重0.6, 20日流入权重0.4
        score = (cumulative_5d / 500 * 0.6 + cumulative_20d / 1500 * 0.4)

        return max(-1, min(1, score))

    def _score_sentiment(self, sentiment_metrics: Dict) -> float:
        """
        情绪得分

        Returns:
            -1到+1
        """
        if not sentiment_metrics:
            return 0.0

        limit_up = sentiment_metrics.get('limit_up_count', 0)
        limit_down = sentiment_metrics.get('limit_down_count', 0)

        # 涨停多为正, 跌停多为负
        score = (limit_up - limit_down) / 100

        return max(-1, min(1, score))

    def _score_breadth(self, breadth_metrics: Dict) -> float:
        """
        市场宽度得分

        Returns:
            -1到+1
        """
        if not breadth_metrics:
            return 0.0

        up_ratio = breadth_metrics.get('up_ratio', 0.5)

        # 上涨比例 → 得分
        # 80%+ → +1, 50% → 0, 20%- → -1
        score = (up_ratio - 0.5) * 2

        return max(-1, min(1, score))

    def _score_leverage(self, margin_metrics: Dict) -> float:
        """
        杠杆得分 (融资融券)

        Returns:
            -1到+1, 杠杆快速上升偏正(但有风险), 下降偏负
        """
        if not margin_metrics:
            return 0.0

        margin_pct_change = margin_metrics.get('margin_balance_pct_change', 0)

        # 融资余额变化 → 得分
        # +3%以上 → +0.8 (但有过热风险)
        # -3%以下 → -0.8
        score = margin_pct_change / 3 * 0.8

        return max(-1, min(1, score))

    def _score_main_fund(self, main_fund_metrics: Dict) -> float:
        """
        主力资金得分

        Returns:
            -1到+1
        """
        if not main_fund_metrics:
            return 0.0

        today_inflow = main_fund_metrics.get('today_main_inflow', 0)
        cumulative_5d = main_fund_metrics.get('cumulative_5d', 0)

        # 当日权重0.4, 5日权重0.6
        score = (today_inflow / 200 * 0.4 + cumulative_5d / 500 * 0.6)

        return max(-1, min(1, score))

    def _score_institution(self, lhb_metrics: Dict) -> float:
        """
        机构行为得分

        Returns:
            -1到+1
        """
        if not lhb_metrics:
            return 0.0

        inst_buy = lhb_metrics.get('institution_buy_count', 0)
        inst_sell = lhb_metrics.get('institution_sell_count', 0)
        inst_net_buy = lhb_metrics.get('institution_net_buy', 0)

        # 机构净买入 → 得分
        if inst_buy + inst_sell > 0:
            ratio_score = (inst_buy - inst_sell) / (inst_buy + inst_sell)
        else:
            ratio_score = 0

        amount_score = inst_net_buy / 50

        # 综合得分
        score = ratio_score * 0.5 + amount_score * 0.5

        return max(-1, min(1, score))

    def _score_volatility(self, volatility_metrics: Dict) -> float:
        """
        波动率得分

        Returns:
            -1到+1, 极低波动偏正(稳健), 极高波动偏负(风险)
        """
        if not volatility_metrics:
            return 0.0

        vol_percentile = volatility_metrics.get('volatility_percentile', 0.5)

        # 波动率分位数越低,得分越高
        # 20%分位 → +0.6, 80%分位 → -0.6
        score = (0.5 - vol_percentile) * 1.2

        return max(-1, min(1, score))

    def _score_volume(self, volume_metrics: Dict) -> float:
        """
        成交量得分

        Returns:
            -1到+1
        """
        if not volume_metrics:
            return 0.0

        volume_ratio = volume_metrics.get('volume_ratio', 1.0)
        volume_percentile = volume_metrics.get('volume_percentile', 0.5)

        # 量比 → 得分
        # 量比>2 → +0.8, 量比<0.5 → -0.5
        if volume_ratio > 1.5:
            score = min(0.8, (volume_ratio - 1) * 0.5)
        elif volume_ratio < 0.8:
            score = max(-0.5, (volume_ratio - 1) * 0.5)
        else:
            score = 0

        return max(-1, min(1, score))

    def _score_technical(self, technical_metrics: Dict) -> float:
        """
        技术形态得分

        Returns:
            -1到+1
        """
        if not technical_metrics:
            return 0.0

        macd_signal = technical_metrics.get('macd_signal', '中性')
        rsi_signal = technical_metrics.get('rsi_signal', '中性')
        rsi_value = technical_metrics.get('rsi', 50)

        # MACD得分
        if macd_signal == '金叉':
            macd_score = 0.8
        elif macd_signal == '多头':
            macd_score = 0.5
        elif macd_signal == '死叉':
            macd_score = -0.8
        elif macd_signal == '空头':
            macd_score = -0.5
        else:
            macd_score = 0

        # RSI得分
        if rsi_signal == '超买':
            rsi_score = -0.3  # 超买有回调风险
        elif rsi_signal == '超卖':
            rsi_score = 0.5   # 超卖有反弹机会
        else:
            # 中性区间,根据数值判断
            rsi_score = (rsi_value - 50) / 50 * 0.3

        # 综合得分
        score = macd_score * 0.7 + rsi_score * 0.3

        return max(-1, min(1, score))

    def _map_score_to_state(self, score: float, dimension_scores: Dict) -> Tuple[str, str]:
        """
        将综合得分映射到市场状态

        Returns:
            (状态简称, 状态详细描述)
        """
        # 获取趋势和估值得分辅助判断
        trend_score = dimension_scores.get('trend', 0)
        valuation_score = dimension_scores.get('valuation', 0)

        if score > 0.6:
            if valuation_score > 0.3:
                return "牛市初期", "底部启动,估值合理,趋势向上"
            else:
                return "牛市中期", "主升浪,趋势强劲"
        elif score > 0.3:
            return "上行震荡", "震荡向上,多头占优"
        elif score > -0.3:
            return "横盘震荡", "多空平衡,方向不明"
        elif score > -0.6:
            return "下行震荡", "震荡向下,空头占优"
        else:
            if valuation_score < -0.3:
                return "熊市末期", "估值过高,趋势下行"
            else:
                return "熊市中期", "持续阴跌,趋势疲弱"

    def _calculate_confidence(self, dimension_scores: Dict) -> float:
        """
        计算置信度

        基于维度得分的一致性
        """
        scores = list(dimension_scores.values())

        if len(scores) == 0:
            return 0.0

        # 计算得分的标准差
        std = np.std(scores)

        # 标准差越小,一致性越高,置信度越高
        # std=0 → confidence=1.0, std=1 → confidence=0.3
        confidence = max(0.3, 1.0 - std * 0.7)

        return confidence

    def _extract_key_signals(self, dimension_scores: Dict) -> List[str]:
        """
        提取关键信号(得分>0.5的维度)
        """
        signals = []

        signal_map = {
            'trend': '趋势强劲向上',
            'price_change': '价格持续上涨',
            'valuation': '估值合理偏低',
            'capital_flow': '北向资金流入',
            'sentiment': '市场情绪积极',
            'breadth': '普涨行情',
            'leverage': '杠杆资金活跃',
            'main_fund': '主力持续流入',
            'institution': '机构积极买入',
            'volatility': '波动率稳定',
            'volume': '成交量放大',
            'technical': '技术形态良好'
        }

        for dim, score in dimension_scores.items():
            if score > 0.5 and dim in signal_map:
                signals.append(signal_map[dim])

        return signals[:5]  # 最多返回5个

    def _extract_risk_alerts(self, dimension_scores: Dict) -> List[str]:
        """
        提取风险警告(得分<-0.5或特定维度得分过高)
        """
        alerts = []

        # 负面信号
        negative_map = {
            'trend': '趋势转弱',
            'price_change': '价格持续下跌',
            'valuation': '估值过高',
            'capital_flow': '北向资金流出',
            'sentiment': '市场情绪低迷',
            'breadth': '普跌行情',
            'leverage': '杠杆资金撤离',
            'main_fund': '主力持续流出',
            'institution': '机构抛售',
            'volatility': '波动率异常',
            'volume': '成交量萎缩',
            'technical': '技术形态破位'
        }

        for dim, score in dimension_scores.items():
            if score < -0.5 and dim in negative_map:
                alerts.append(negative_map[dim])

        # 特殊风险: 情绪过热
        if dimension_scores.get('sentiment', 0) > 0.8:
            alerts.append('情绪过热,警惕回调')

        # 特殊风险: 杠杆过高
        if dimension_scores.get('leverage', 0) > 0.8:
            alerts.append('融资余额快速上升,杠杆风险')

        return alerts[:5]  # 最多返回5个

    def get_position_recommendation(self, state: str, overall_score: float, confidence: float) -> Dict:
        """
        根据市场状态给出仓位建议

        Returns:
            {
                'position_min': 0.7,
                'position_max': 0.8,
                'position_center': 0.75,
                'strategy': '持股为主',
                'action': '逢低加仓'
            }
        """
        # 基础仓位映射
        state_position_map = {
            '牛市初期': (0.75, 0.85, '积极做多', '分批建仓'),
            '牛市中期': (0.65, 0.75, '持股为主', '逢低加仓'),
            '牛市末期': (0.25, 0.35, '逐步减仓', '落袋为安'),
            '上行震荡': (0.55, 0.65, '标准配置', '高抛低吸'),
            '横盘震荡': (0.45, 0.55, '观望为主', '等待方向'),
            '下行震荡': (0.30, 0.40, '轻仓观望', '严格止损'),
            '熊市中期': (0.15, 0.25, '空仓为主', '等待企稳'),
            '熊市末期': (0.35, 0.45, '分批建仓', '价值布局')
        }

        base_pos_min, base_pos_max, strategy, action = state_position_map.get(
            state, (0.45, 0.55, '标准配置', '谨慎操作')
        )

        # 根据置信度微调
        confidence_adjustment = (confidence - 0.7) * 0.1

        pos_min = max(0.1, min(0.9, base_pos_min + confidence_adjustment))
        pos_max = max(0.1, min(0.9, base_pos_max + confidence_adjustment))
        pos_center = (pos_min + pos_max) / 2

        return {
            'position_min': float(pos_min),
            'position_max': float(pos_max),
            'position_center': float(pos_center),
            'strategy': strategy,
            'action': action
        }


if __name__ == '__main__':
    # 简单测试
    detector = MarketStateDetector()
    print("市场状态检测器已初始化")
    print(f"维度权重: {detector.dimension_weights}")
