#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态仓位管理器

智能化仓位调整,包括:
1. 凯利公式最优仓位
2. 波动率目标仓位
3. 市场环境自动识别
4. 风险平价仓位
5. 动态再平衡建议
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


# Kelly公式(内联,避免外部依赖)
def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    Kelly公式: f* = (p × b - q) / b

    Args:
        win_rate: 胜率 (0-1)
        avg_win: 平均盈利 (例如 0.05 表示5%)
        avg_loss: 平均亏损 (例如 0.03 表示3%, 传入正数)

    Returns:
        最优仓位比例 (0-1)
    """
    if avg_loss <= 0:
        return 0.0

    p = win_rate  # 胜率
    q = 1 - win_rate  # 败率
    b = avg_win / avg_loss  # 赔率 (盈亏比)

    # Kelly公式
    kelly = (p * b - q) / b

    return max(0.0, kelly)


class DynamicPositionManager:
    """动态仓位管理器 - 智能化仓位调整"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化动态仓位管理器

        Args:
            config: 配置字典,包含:
                - min_position: 最小仓位 (默认0.50)
                - max_position: 最大仓位 (默认0.90)
                - kelly_fraction: Kelly公式折扣系数 (默认0.25, 即1/4 Kelly)
                - target_volatility: 目标波动率 (默认0.15, 即15%)
                - rebalance_threshold: 再平衡阈值 (默认0.05, 即5%)
        """
        if config is None:
            config = {}

        self.min_position = config.get('min_position', 0.50)
        self.max_position = config.get('max_position', 0.90)
        self.kelly_fraction = config.get('kelly_fraction', 0.25)
        self.target_volatility = config.get('target_volatility', 0.15)
        self.rebalance_threshold = config.get('rebalance_threshold', 0.05)

    # ==================== 凯利公式仓位 ====================

    def calculate_kelly_position(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        use_fraction: bool = True
    ) -> Dict:
        """
        计算凯利公式最优仓位

        Kelly公式: f* = (p × b - q) / b
        其中: p=胜率, q=败率, b=盈亏比

        Args:
            win_rate: 胜率 (0-1)
            avg_win: 平均盈利率
            avg_loss: 平均亏损率(传入正数)
            use_fraction: 是否使用Kelly折扣(推荐True)

        Returns:
            Kelly仓位建议
        """
        # 调用现有的Kelly公式
        kelly_position = kelly_criterion(win_rate, avg_win, avg_loss)

        if use_fraction:
            kelly_position = kelly_position * self.kelly_fraction

        # 限制在合理范围
        kelly_position = max(0.0, min(kelly_position, self.max_position - self.min_position))

        # 实际建议仓位 = 最小仓位 + Kelly额外仓位
        actual_position = self.min_position + kelly_position

        return {
            'kelly_position': kelly_position,
            'kelly_position_pct': f"{kelly_position * 100:.1f}%",
            'suggested_position': actual_position,
            'suggested_position_pct': f"{actual_position * 100:.1f}%",
            'win_rate': win_rate,
            'avg_win_pct': f"{avg_win * 100:.1f}%",
            'avg_loss_pct': f"{avg_loss * 100:.1f}%",
            'profit_factor': (win_rate * avg_win) / ((1 - win_rate) * avg_loss) if avg_loss > 0 else 0,
            'kelly_fraction_used': self.kelly_fraction,
            'rationale': f"基于Kelly公式({self.kelly_fraction*100:.0f}% Kelly),考虑胜率{win_rate*100:.1f}%和盈亏比{avg_win/avg_loss:.2f}"
        }

    # ==================== 波动率目标仓位 ====================

    def calculate_volatility_target_position(
        self,
        current_volatility: float,
        target_volatility: Optional[float] = None
    ) -> Dict:
        """
        基于波动率目标调整仓位

        核心思想: 波动率高时降低仓位,波动率低时提高仓位
        目标仓位 = 基础仓位 × (目标波动率 / 当前波动率)

        Args:
            current_volatility: 当前年化波动率
            target_volatility: 目标年化波动率,不提供则使用配置值

        Returns:
            波动率目标仓位建议
        """
        if target_volatility is None:
            target_volatility = self.target_volatility

        if current_volatility <= 0:
            return {
                'suggested_position': self.max_position,
                'suggested_position_pct': f"{self.max_position * 100:.1f}%",
                'volatility_adjustment': 1.0,
                'rationale': '波动率数据异常,建议最大仓位'
            }

        # 波动率调整系数
        vol_adjustment = target_volatility / current_volatility

        # 调整后的仓位 (以最大仓位为基准)
        adjusted_position = self.max_position * vol_adjustment

        # 限制在合理范围
        adjusted_position = max(self.min_position, min(adjusted_position, self.max_position))

        # 判断调整方向
        if vol_adjustment > 1.1:
            direction = "提高仓位"
            reason = f"当前波动率{current_volatility*100:.1f}%低于目标{target_volatility*100:.1f}%"
        elif vol_adjustment < 0.9:
            direction = "降低仓位"
            reason = f"当前波动率{current_volatility*100:.1f}%高于目标{target_volatility*100:.1f}%"
        else:
            direction = "维持仓位"
            reason = "当前波动率接近目标"

        return {
            'suggested_position': adjusted_position,
            'suggested_position_pct': f"{adjusted_position * 100:.1f}%",
            'current_volatility': current_volatility,
            'current_volatility_pct': f"{current_volatility * 100:.1f}%",
            'target_volatility': target_volatility,
            'target_volatility_pct': f"{target_volatility * 100:.1f}%",
            'volatility_adjustment': vol_adjustment,
            'direction': direction,
            'rationale': reason
        }

    # ==================== 市场环境识别 ====================

    def detect_market_regime(self, market_data: Dict) -> Dict:
        """
        自动检测市场环境 (牛市/熊市/震荡)

        使用多个指标综合判断:
        1. MA均线系统 (20日/60日/120日)
        2. 市场宽度 (上涨股票占比)
        3. 趋势强度 (ADX)
        4. RSI
        5. 恐慌指数

        Args:
            market_data: 市场数据字典,包含:
                - current_price: 当前价格
                - ma20: 20日均线
                - ma60: 60日均线
                - ma120: 120日均线
                - advancing_stocks_pct: 上涨股票占比 (可选)
                - rsi: RSI指标 (可选)
                - vix: 恐慌指数 (可选)

        Returns:
            市场环境判断结果
        """
        current_price = market_data.get('current_price', 0)
        ma20 = market_data.get('ma20', current_price)
        ma60 = market_data.get('ma60', current_price)
        ma120 = market_data.get('ma120', current_price)

        scores = {'bull': 0, 'bear': 0, 'sideways': 0}

        # 1. MA均线系统判断
        if current_price > ma20 > ma60 > ma120:
            scores['bull'] += 3  # 多头排列
        elif current_price < ma20 < ma60 < ma120:
            scores['bear'] += 3  # 空头排列
        else:
            scores['sideways'] += 2  # 交叉状态

        # 2. 与MA的偏离度
        if ma20 > 0:
            deviation_20 = (current_price - ma20) / ma20
            if deviation_20 > 0.05:  # 上涨趋势
                scores['bull'] += 1
            elif deviation_20 < -0.05:  # 下跌趋势
                scores['bear'] += 1
            else:
                scores['sideways'] += 1

        # 3. 市场宽度
        advancing_pct = market_data.get('advancing_stocks_pct', None)
        if advancing_pct is not None:
            if advancing_pct > 0.6:
                scores['bull'] += 2
            elif advancing_pct < 0.4:
                scores['bear'] += 2
            else:
                scores['sideways'] += 1

        # 4. RSI指标
        rsi = market_data.get('rsi', None)
        if rsi is not None:
            if rsi > 60:
                scores['bull'] += 1
            elif rsi < 40:
                scores['bear'] += 1
            else:
                scores['sideways'] += 1

        # 5. 恐慌指数
        vix = market_data.get('vix', None)
        if vix is not None:
            if vix < 15:  # 低恐慌
                scores['bull'] += 1
            elif vix > 25:  # 高恐慌
                scores['bear'] += 2
            else:
                scores['sideways'] += 1

        # 判断市场环境
        max_score = max(scores.values())
        if scores['bull'] == max_score:
            regime = 'bull'
            regime_name = '牛市上升期'
            confidence = scores['bull'] / sum(scores.values())
        elif scores['bear'] == max_score:
            regime = 'bear'
            regime_name = '熊市下跌期'
            confidence = scores['bear'] / sum(scores.values())
        else:
            regime = 'sideways'
            regime_name = '震荡整理期'
            confidence = scores['sideways'] / sum(scores.values())

        return {
            'regime': regime,
            'regime_name': regime_name,
            'confidence': confidence,
            'confidence_pct': f"{confidence * 100:.1f}%",
            'scores': scores,
            'indicators': {
                'ma_alignment': '多头排列' if current_price > ma20 > ma60 > ma120 else
                               '空头排列' if current_price < ma20 < ma60 < ma120 else '交叉',
                'advancing_stocks': f"{advancing_pct*100:.1f}%" if advancing_pct else 'N/A',
                'rsi': rsi if rsi else 'N/A',
                'vix': vix if vix else 'N/A'
            }
        }

    def suggest_position_by_regime(self, regime: str, custom_rules: Optional[Dict] = None) -> Dict:
        """
        根据市场环境建议仓位

        Args:
            regime: 市场环境 ('bull', 'bear', 'sideways')
            custom_rules: 自定义规则,覆盖默认设置

        Returns:
            仓位建议
        """
        # 默认规则
        default_rules = {
            'bull': {
                'position_range': (0.70, 0.90),
                'rationale': '牛市上升期,可以较高仓位(7-9成)'
            },
            'bear': {
                'position_range': (0.30, 0.50),
                'rationale': '熊市下跌期,控制仓位(3-5成),保留现金'
            },
            'sideways': {
                'position_range': (0.50, 0.70),
                'rationale': '震荡期,中等仓位(5-7成),灵活调整'
            }
        }

        rules = custom_rules if custom_rules else default_rules

        if regime not in rules:
            regime = 'sideways'  # 默认震荡

        rule = rules[regime]
        pos_min, pos_max = rule['position_range']
        suggested_position = (pos_min + pos_max) / 2  # 取中间值

        return {
            'regime': regime,
            'suggested_position': suggested_position,
            'suggested_position_pct': f"{suggested_position * 100:.1f}%",
            'position_range_min': pos_min,
            'position_range_max': pos_max,
            'position_range_text': f"{pos_min*100:.0f}%-{pos_max*100:.0f}%",
            'rationale': rule['rationale']
        }

    # ==================== 风险平价仓位 ====================

    def calculate_risk_parity_positions(
        self,
        assets: List[Dict],
        target_risk_contribution: Optional[float] = None
    ) -> Dict:
        """
        计算风险平价仓位

        核心思想: 让每个资产贡献相同的风险(波动率)

        Args:
            assets: 资产列表,每个包含:
                - asset_name: 资产名称
                - volatility: 年化波动率
                - current_weight: 当前权重(可选)
            target_risk_contribution: 目标风险贡献,默认平均分配

        Returns:
            风险平价仓位建议
        """
        if not assets:
            return {'error': '资产列表为空'}

        n_assets = len(assets)
        if target_risk_contribution is None:
            target_risk_contribution = 1.0 / n_assets

        # 计算逆波动率权重
        total_inv_vol = sum(1.0 / asset['volatility'] for asset in assets if asset['volatility'] > 0)

        risk_parity_weights = []
        for asset in assets:
            if asset['volatility'] > 0:
                weight = (1.0 / asset['volatility']) / total_inv_vol
            else:
                weight = 0.0

            risk_parity_weights.append({
                'asset_name': asset['asset_name'],
                'current_weight': asset.get('current_weight', 0),
                'current_weight_pct': f"{asset.get('current_weight', 0) * 100:.1f}%",
                'risk_parity_weight': weight,
                'risk_parity_weight_pct': f"{weight * 100:.1f}%",
                'volatility': asset['volatility'],
                'volatility_pct': f"{asset['volatility'] * 100:.1f}%",
                'adjustment_needed': abs(weight - asset.get('current_weight', 0)) > self.rebalance_threshold
            })

        return {
            'risk_parity_weights': risk_parity_weights,
            'rebalance_needed': any(w['adjustment_needed'] for w in risk_parity_weights),
            'rationale': '风险平价配置,让每个资产贡献相同的风险'
        }

    # ==================== 再平衡检查 ====================

    def check_rebalance_need(
        self,
        current_positions: List[Dict],
        target_positions: List[Dict]
    ) -> Dict:
        """
        检查是否需要再平衡

        Args:
            current_positions: 当前持仓,包含:
                - asset_name: 资产名称
                - weight: 当前权重
            target_positions: 目标持仓,包含:
                - asset_name: 资产名称
                - weight: 目标权重

        Returns:
            再平衡建议
        """
        # 构建字典方便查找
        current_dict = {p['asset_name']: p['weight'] for p in current_positions}
        target_dict = {p['asset_name']: p['weight'] for p in target_positions}

        all_assets = set(current_dict.keys()) | set(target_dict.keys())

        rebalance_actions = []
        max_deviation = 0

        for asset in all_assets:
            current_weight = current_dict.get(asset, 0)
            target_weight = target_dict.get(asset, 0)
            deviation = abs(current_weight - target_weight)

            if deviation > max_deviation:
                max_deviation = deviation

            if deviation > self.rebalance_threshold:
                if target_weight > current_weight:
                    action = f"加仓{(target_weight - current_weight)*100:.1f}%"
                elif target_weight < current_weight:
                    action = f"减仓{(current_weight - target_weight)*100:.1f}%"
                else:
                    action = "持有"

                rebalance_actions.append({
                    'asset_name': asset,
                    'current_weight_pct': f"{current_weight * 100:.1f}%",
                    'target_weight_pct': f"{target_weight * 100:.1f}%",
                    'deviation_pct': f"{deviation * 100:.1f}%",
                    'action': action
                })

        needs_rebalance = len(rebalance_actions) > 0

        return {
            'needs_rebalance': needs_rebalance,
            'max_deviation': max_deviation,
            'max_deviation_pct': f"{max_deviation * 100:.1f}%",
            'rebalance_threshold_pct': f"{self.rebalance_threshold * 100:.1f}%",
            'actions_count': len(rebalance_actions),
            'actions': rebalance_actions,
            'suggestion': '建议执行再平衡' if needs_rebalance else '当前仓位合理,无需再平衡'
        }

    # ==================== 综合仓位建议 ====================

    def generate_comprehensive_position_advice(
        self,
        market_data: Dict,
        trading_stats: Optional[Dict] = None,
        current_volatility: Optional[float] = None
    ) -> Dict:
        """
        综合各种方法,生成最终仓位建议

        Args:
            market_data: 市场数据(用于环境识别)
            trading_stats: 交易统计(用于Kelly公式),包含:
                - win_rate: 胜率
                - avg_win: 平均盈利
                - avg_loss: 平均亏损
            current_volatility: 当前波动率(用于波动率目标)

        Returns:
            综合仓位建议
        """
        advice = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'methods': {}
        }

        # 1. 市场环境判断
        regime_result = self.detect_market_regime(market_data)
        regime_position = self.suggest_position_by_regime(regime_result['regime'])

        advice['methods']['market_regime'] = {
            'regime': regime_result['regime_name'],
            'confidence': regime_result['confidence_pct'],
            'suggested_position': regime_position['suggested_position'],
            'suggested_position_pct': regime_position['suggested_position_pct'],
            'weight': 0.4  # 市场环境权重40%
        }

        # 2. Kelly公式(如果有交易统计)
        if trading_stats and all(k in trading_stats for k in ['win_rate', 'avg_win', 'avg_loss']):
            kelly_result = self.calculate_kelly_position(
                trading_stats['win_rate'],
                trading_stats['avg_win'],
                trading_stats['avg_loss']
            )
            advice['methods']['kelly'] = {
                'suggested_position': kelly_result['suggested_position'],
                'suggested_position_pct': kelly_result['suggested_position_pct'],
                'profit_factor': kelly_result['profit_factor'],
                'weight': 0.3  # Kelly权重30%
            }

        # 3. 波动率目标(如果有波动率数据)
        if current_volatility is not None:
            vol_result = self.calculate_volatility_target_position(current_volatility)
            advice['methods']['volatility_target'] = {
                'suggested_position': vol_result['suggested_position'],
                'suggested_position_pct': vol_result['suggested_position_pct'],
                'volatility_adjustment': vol_result['volatility_adjustment'],
                'weight': 0.3  # 波动率权重30%
            }

        # 4. 计算加权平均仓位
        total_weight = sum(method['weight'] for method in advice['methods'].values())
        weighted_position = sum(
            method['suggested_position'] * method['weight']
            for method in advice['methods'].values()
        ) / total_weight

        # 限制在合理范围
        weighted_position = max(self.min_position, min(weighted_position, self.max_position))

        advice['final_recommendation'] = {
            'suggested_position': weighted_position,
            'suggested_position_pct': f"{weighted_position * 100:.1f}%",
            'position_range_min': self.min_position,
            'position_range_max': self.max_position,
            'rationale': self._generate_position_rationale(advice['methods'], regime_result)
        }

        return advice

    def _generate_position_rationale(self, methods: Dict, regime_result: Dict) -> str:
        """生成仓位建议理由"""
        rationale_parts = []

        # 市场环境
        regime_name = regime_result['regime_name']
        confidence = regime_result['confidence_pct']
        rationale_parts.append(f"市场处于{regime_name}(置信度{confidence})")

        # Kelly公式
        if 'kelly' in methods:
            pf = methods['kelly'].get('profit_factor', 0)
            rationale_parts.append(f"策略盈亏比{pf:.2f}")

        # 波动率
        if 'volatility_target' in methods:
            vol_adj = methods['volatility_target'].get('volatility_adjustment', 1.0)
            if vol_adj > 1.1:
                rationale_parts.append("当前波动率较低")
            elif vol_adj < 0.9:
                rationale_parts.append("当前波动率较高")

        return ", ".join(rationale_parts)


# 示例用法
if __name__ == "__main__":
    # 创建动态仓位管理器
    manager = DynamicPositionManager()

    # 示例1: 市场环境识别
    market_data = {
        'current_price': 3000,
        'ma20': 2950,
        'ma60': 2900,
        'ma120': 2850,
        'advancing_stocks_pct': 0.65,
        'rsi': 62,
        'vix': 18
    }

    regime = manager.detect_market_regime(market_data)
    print("市场环境:", regime['regime_name'])
    print("置信度:", regime['confidence_pct'])
    print()

    # 示例2: 综合仓位建议
    trading_stats = {
        'win_rate': 0.55,
        'avg_win': 0.08,
        'avg_loss': 0.05
    }

    advice = manager.generate_comprehensive_position_advice(
        market_data=market_data,
        trading_stats=trading_stats,
        current_volatility=0.25
    )

    print("综合仓位建议:", advice['final_recommendation']['suggested_position_pct'])
    print("理由:", advice['final_recommendation']['rationale'])
