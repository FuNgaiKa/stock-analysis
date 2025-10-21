#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情景分析模块
Scenario Analyzer

提供乐观/中性/悲观三种情景下的组合表现预测
"""

from typing import Dict, List
from ..utils.config_loader import get_scenario_config


class ScenarioAnalyzer:
    """情景分析器"""

    def __init__(self):
        """初始化情景分析器"""
        self.scenario_config = get_scenario_config()

    def analyze_scenarios(
        self,
        positions: List[Dict],
        total_value: float,
        time_horizon_days: int = 30
    ) -> Dict:
        """
        情景分析

        Args:
            positions: 当前持仓
            total_value: 总市值
            time_horizon_days: 时间跨度(天)

        Returns:
            情景分析结果
        """
        scenarios = []

        for scenario_name in ['optimistic', 'neutral', 'pessimistic']:
            scenario_cfg = self.scenario_config[scenario_name]

            probability = scenario_cfg['probability']
            market_return = scenario_cfg['market_return']
            name = scenario_cfg['name']
            emoji = scenario_cfg['emoji']

            # 估算组合收益 (简化: 组合收益 ≈ 市场收益 × Beta)
            portfolio_beta = self._estimate_beta(positions)
            portfolio_return = market_return * portfolio_beta

            # 计算期望市值
            expected_value = total_value * (1 + portfolio_return)
            gain_loss = expected_value - total_value

            # 估算最大回撤 (简化)
            if market_return < 0:
                max_drawdown = market_return * portfolio_beta * 1.2  # 下跌时放大20%
            else:
                max_drawdown = market_return * 0.3  # 上涨时也可能有回撤

            scenarios.append({
                'name': name,
                'emoji': emoji,
                'probability': probability,
                'market_return': market_return,
                'portfolio_return': portfolio_return,
                'expected_value': expected_value,
                'gain_loss': gain_loss,
                'max_drawdown': max_drawdown
            })

        # 计算期望收益
        expected_return = sum(s['probability'] * s['portfolio_return'] for s in scenarios)
        expected_value = total_value * (1 + expected_return)

        return {
            'scenarios': scenarios,
            'expected_return': expected_return,
            'expected_value': expected_value,
            'time_horizon_days': time_horizon_days
        }

    def _estimate_beta(self, positions: List[Dict]) -> float:
        """估算组合Beta"""
        total_beta = 0.0
        total_weight = 0.0

        for pos in positions:
            asset_name = pos.get('asset_name', '')
            ratio = pos.get('position_ratio', 0)

            # 估算Beta
            if any(kw in asset_name for kw in ['科技', '创业', '科创', '恒科']):
                beta = 1.2
            elif any(kw in asset_name for kw in ['白酒', '消费']):
                beta = 0.9
            elif any(kw in asset_name for kw in ['煤炭', '化工']):
                beta = 1.1
            else:
                beta = 1.0

            total_beta += beta * ratio
            total_weight += ratio

        return total_beta / total_weight if total_weight > 0 else 1.0

    def format_scenario_report(self, analysis: Dict) -> str:
        """格式化情景分析报告"""
        lines = []
        lines.append("### 📊 情景分析 (未来1个月)")
        lines.append("")
        lines.append("| 情景 | 概率 | 市场环境 | 组合收益 | 期望市值 | 最大回撤 |")
        lines.append("|------|------|---------|---------|---------|---------|")

        for s in analysis['scenarios']:
            name = f"{s['emoji']} {s['name']}"
            prob = f"{s['probability']*100:.0f}%"
            market_desc = "牛市延续" if s['market_return'] > 0.10 else ("震荡整理" if s['market_return'] > 0 else "调整10%")
            portfolio_return = f"{s['portfolio_return']*100:+.1f}%"
            expected_value = f"¥{s['expected_value']/10000:.1f}万"
            max_dd = f"{s['max_drawdown']*100:.1f}%"

            lines.append(f"| {name} | {prob} | {market_desc} | {portfolio_return} | {expected_value} | {max_dd} |")

        lines.append("")
        lines.append("**期望收益**:")
        lines.append("")
        expected_return = analysis['expected_return']
        expected_value = analysis['expected_value']
        lines.append(f"- 综合概率加权后,期望收益为 **{expected_return*100:+.1f}%**")
        lines.append(f"- 期望市值: ¥{expected_value/10000:.1f}万")
        lines.append("")

        return '\n'.join(lines)


if __name__ == '__main__':
    analyzer = ScenarioAnalyzer()

    positions = [
        {'asset_name': '恒生科技ETF', 'position_ratio': 0.28},
        {'asset_name': '证券ETF', 'position_ratio': 0.23},
    ]

    result = analyzer.analyze_scenarios(positions, 500000)
    report = analyzer.format_scenario_report(result)
    print(report)
