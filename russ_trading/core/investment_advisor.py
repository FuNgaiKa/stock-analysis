#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资建议生成器
Investment Advisor

根据技术分析结果生成具体的投资建议和操作指导

Author: Claude Code
Date: 2025-11-03
"""

from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class InvestmentAdvisor:
    """投资建议生成器"""

    def __init__(self):
        """初始化建议生成器"""
        self.rating_weights = {
            'technical_position': 0.3,  # 技术位置权重
            'recent_performance': 0.25,  # 近期表现权重
            'volume_ratio': 0.2,  # 成交量权重
            'momentum': 0.15,  # 动量指标权重
            'risk_level': 0.1  # 风险水平权重
        }

    def generate_asset_advice(self, asset_data: Dict) -> Dict[str, Any]:
        """
        为单个资产生成投资建议

        Args:
            asset_data: 资产分析数据

        Returns:
            投资建议字典
        """
        try:
            # 提取关键数据
            asset_name = asset_data.get('name', '未知资产')
            asset_key = asset_data.get('key', '')

            # 技术指标
            technical_analysis = asset_data.get('technical_analysis', {})
            current_price = technical_analysis.get('current_price', 0)
            change_pct = technical_analysis.get('change_pct', 0)

            # 位置分析
            position_analysis = asset_data.get('position_analysis', {})
            position_level = position_analysis.get('position_level', '未知')
            position_pct = position_analysis.get('position_pct', 0)
            ma20_position_pct = position_analysis.get('ma20_position_pct', 0)

            # 量价分析
            volume_analysis = asset_data.get('volume_analysis', {})
            volume_ratio = volume_analysis.get('volume_ratio_20d', 1.0)

            # 历史表现
            historical_analysis = asset_data.get('historical_analysis', {})
            d20_performance = historical_analysis.get('d20', {}).get('total_return', 0)

            # 综合判断
            overall_judgment = asset_data.get('overall_judgment', {})
            judgment = overall_judgment.get('judgment', '中性')
            confidence = overall_judgment.get('confidence', 50)

            # 计算评分
            score = self._calculate_score(
                position_pct, change_pct, volume_ratio,
                d20_performance, judgment, confidence
            )

            # 生成建议
            advice = self._generate_advice(
                asset_name, asset_key, score, judgment,
                current_price, position_level, volume_ratio, change_pct
            )

            return advice

        except Exception as e:
            logger.error(f"生成投资建议失败: {e}")
            return self._get_default_advice()

    def _calculate_score(self, position_pct: float, change_pct: float,
                        volume_ratio: float, d20_performance: float,
                        judgment: str, confidence: float) -> float:
        """
        计算综合评分

        Args:
            position_pct: 位置百分比
            change_pct: 涨跌幅
            volume_ratio: 成交量比
            d20_performance: 20日表现
            judgment: 综合判断
            confidence: 置信度

        Returns:
            综合评分 (0-100)
        """
        score = 50  # 基础分

        # 技术位置评分
        if position_pct >= 70:
            score += 20
        elif position_pct >= 50:
            score += 10
        elif position_pct >= 30:
            score += 5
        else:
            score -= 10

        # 近期表现评分
        if change_pct > 3:
            score += 15
        elif change_pct > 1:
            score += 8
        elif change_pct > 0:
            score += 3
        elif change_pct > -2:
            score -= 5
        else:
            score -= 15

        # 成交量评分
        if volume_ratio > 2:
            score += 15
        elif volume_ratio > 1.5:
            score += 10
        elif volume_ratio > 1:
            score += 5
        else:
            score -= 5

        # 动量评分
        if d20_performance > 5:
            score += 10
        elif d20_performance > 0:
            score += 5
        elif d20_performance > -5:
            score -= 5
        else:
            score -= 10

        # 综合判断评分
        judgment_scores = {
            '强烈看好': 20, '看好': 10, '中性偏强': 5,
            '中性': 0, '中性偏弱': -5, '看淡': -10, '强烈看淡': -20
        }
        score += judgment_scores.get(judgment, 0)

        # 置信度调整
        confidence_factor = confidence / 50
        score = 50 + (score - 50) * confidence_factor

        return max(0, min(100, score))

    def _generate_advice(self, asset_name: str, asset_key: str, score: float,
                        judgment: str, current_price: float,
                        position_level: str, volume_ratio: float,
                        change_pct: float) -> Dict[str, Any]:
        """
        生成具体建议

        Args:
            asset_name: 资产名称
            asset_key: 资产代码
            score: 综合评分
            judgment: 综合判断
            current_price: 当前价格
            position_level: 位置水平
            volume_ratio: 成交量比
            change_pct: 涨跌幅

        Returns:
            建议字典
        """
        # 确定建议等级
        if score >= 80:
            level = "强烈建议参与"
            stars = "⭐⭐⭐"
            action = "立即参与"
            position_suggestion = "可重仓配置"
        elif score >= 65:
            level = "谨慎参与"
            stars = "⭐⭐"
            action = "可轻仓参与"
            position_suggestion = "建议小仓位"
        elif score >= 45:
            level = "观望"
            stars = "⭐"
            action = "保持观望"
            position_suggestion = "等待更好时机"
        else:
            level = "暂不建议参与"
            stars = "❌"
            action = "建议等待"
            position_suggestion = "规避当前风险"

        # 生成具体建议
        advice_text = self._generate_specific_advice(
            score, judgment, position_level, volume_ratio, change_pct
        )

        # 生成目标价位（如果适用）
        target_price = ""
        if score >= 65 and current_price > 0:
            if asset_key == 'HK_BIOTECH':
                target_price = "目标1.42-1.48"
            elif asset_key == 'NASDAQ':
                target_price = "关注科技股反弹"
            elif asset_key == 'GOLD':
                target_price = "分批建仓，对冲配置"

        return {
            'asset_name': asset_name,
            'asset_key': asset_key,
            'level': level,
            'stars': stars,
            'score': round(score, 1),
            'current_state': judgment,
            'technical_position': position_level,
            'recent_performance': f"{change_pct:+.2f}%",
            'volume_active': "成交活跃" if volume_ratio > 1.2 else "成交温和",
            'rating': f"{'⭐' * min(5, int(score/20))}{'☆' * (5 - min(5, int(score/20)))}",
            'action': action,
            'target_price': target_price,
            'position_suggestion': position_suggestion,
            'advice_text': advice_text
        }

    def _generate_specific_advice(self, score: float, judgment: str,
                                 position_level: str, volume_ratio: float,
                                 change_pct: float) -> str:
        """生成具体建议文本"""
        if score >= 80:
            return f"技术面强劲，{position_level}，成交量配合良好，建议立即参与"
        elif score >= 65:
            return f"整体趋势向好，可谨慎参与，注意控制仓位"
        elif score >= 45:
            return f"方向不明朗，建议等待更明确的信号"
        else:
            return f"技术面偏弱，建议等待更好的时机"

    def _get_default_advice(self) -> Dict[str, Any]:
        """获取默认建议"""
        return {
            'asset_name': '未知资产',
            'asset_key': '',
            'level': '暂不建议参与',
            'stars': '❌',
            'score': 0,
            'current_state': '数据不足',
            'technical_position': '未知',
            'recent_performance': '0.00%',
            'volume_active': '无数据',
            'rating': '☆☆☆☆☆',
            'action': '建议等待',
            'target_price': '',
            'position_suggestion': '需要更多分析',
            'advice_text': '数据不足，无法生成有效建议'
        }

    def generate_portfolio_advice(self, assets_advice: List[Dict]) -> Dict[str, Any]:
        """
        生成投资组合建议

        Args:
            assets_advice: 资产建议列表

        Returns:
            投资组合建议
        """
        # 筛选不同等级的资产
        strong_buy = [a for a in assets_advice if a['score'] >= 80]
        moderate_buy = [a for a in assets_advice if 65 <= a['score'] < 80]
        hold = [a for a in assets_advice if 45 <= a['score'] < 65]
        avoid = [a for a in assets_advice if a['score'] < 45]

        # 生成优先级排序
        priority_list = strong_buy + moderate_buy + hold + avoid

        # 生成仓位配置建议
        aggressive_allocation = self._generate_allocation_plan(strong_buy, moderate_buy, 'aggressive')
        conservative_allocation = self._generate_allocation_plan(strong_buy, moderate_buy, 'conservative')

        # 生成关键时点
        key_events = self._generate_key_events(strong_buy + moderate_buy)

        return {
            'summary': f"共分析{len(assets_advice)}个资产，强烈推荐{len(strong_buy)}个，谨慎参与{len(moderate_buy)}个",
            'strong_recommendations': strong_buy[:3],  # 前3个最强推荐
            'priority_ranking': priority_list[:10],  # 前10个优先级
            'allocation_suggestions': {
                'aggressive': aggressive_allocation,
                'conservative': conservative_allocation
            },
            'key_events': key_events,
            'risk_warning': self._generate_risk_warning(len(avoid), len(assets_advice))
        }

    def _generate_allocation_plan(self, strong_buy: List[Dict],
                                 moderate_buy: List[Dict],
                                 strategy: str) -> Dict[str, Any]:
        """生成仓位配置计划"""
        if strategy == 'aggressive':
            total_allocation = 70
            strong_weight = 0.6
            moderate_weight = 0.4
        else:
            total_allocation = 50
            strong_weight = 0.7
            moderate_weight = 0.3

        allocation = {}

        # 分配强烈推荐标的
        if strong_buy:
            strong_each = (total_allocation * strong_weight) / len(strong_buy)
            for asset in strong_buy:
                allocation[asset['asset_name']] = f"{strong_each:.0f}%"

        # 分配谨慎推荐标的
        if moderate_buy:
            moderate_each = (total_allocation * moderate_weight) / len(moderate_buy)
            for asset in moderate_buy:
                allocation[asset['asset_name']] = f"{moderate_each:.0f}%"

        return allocation

    def _generate_key_events(self, recommended_assets: List[Dict]) -> List[str]:
        """生成关键时点"""
        events = []

        for asset in recommended_assets[:5]:  # 前5个推荐资产
            if asset['asset_key'] == 'HK_BIOTECH':
                events.append("本周: 重点关注港股创新药突破1.40")
            elif asset['asset_key'] == 'CYBZ':
                events.append("本周: 关注创业板指能否企稳3000点")
            elif asset['asset_key'] == 'GOLD':
                events.append("月内: 关注美联储政策对黄金影响")

        return events if events else ["关注市场整体趋势变化"]

    def _generate_risk_warning(self, avoid_count: int, total_count: int) -> str:
        """生成风险提示"""
        risk_ratio = avoid_count / total_count if total_count > 0 else 0

        if risk_ratio > 0.5:
            return "市场整体风险较高，建议严格控制仓位，保持充足现金"
        elif risk_ratio > 0.3:
            return "部分标的估值偏高，建议精选个股，分散投资"
        else:
            return "市场机会与风险并存，建议均衡配置，动态调整"