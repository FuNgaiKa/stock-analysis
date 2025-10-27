#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
压力测试模块
Stress Tester

模拟历史危机场景,评估组合抗压能力
"""

from typing import Dict, List
from ..utils.config_loader import get_historical_crises


class StressTester:
    """压力测试器"""

    def __init__(self):
        """初始化压力测试器"""
        self.historical_crises = get_historical_crises()

    def run_stress_test(
        self,
        positions: List[Dict],
        total_value: float
    ) -> Dict:
        """
        运行压力测试

        Args:
            positions: 持仓列表
            total_value: 总市值

        Returns:
            压力测试结果
        """
        if not positions or total_value == 0:
            return {'tests': [], 'summary': {}}

        # 计算当前现金比例
        cash_ratio = 1.0 - sum(p.get('position_ratio', 0) for p in positions)

        test_results = []

        for crisis in self.historical_crises:
            crisis_name = crisis['name']
            market_drop = crisis['market_drop']

            # 估算组合在该危机下的损失
            # 简化假设: 组合损失 = 市场下跌 × 组合Beta
            # Beta估算: 科技股1.2, 价值股0.8, 混合1.0
            portfolio_beta = self._estimate_portfolio_beta(positions)

            # 组合预计下跌
            portfolio_drop = market_drop * portfolio_beta

            # 当前组合损失
            current_loss_pct = portfolio_drop
            current_loss_value = total_value * abs(current_loss_pct)

            # 调整后组合 (假设仓位降低10%, 现金增加10%)
            adjusted_positions_ratio = 0.90  # 90%仓位
            adjusted_cash_ratio = 0.10

            adjusted_portfolio_drop = market_drop * portfolio_beta * (adjusted_positions_ratio / (1 - cash_ratio))
            adjusted_loss_pct = adjusted_portfolio_drop
            adjusted_loss_value = total_value * abs(adjusted_loss_pct)

            # 现金缓冲是否足够
            cash_value = total_value * cash_ratio
            can_handle = cash_value >= current_loss_value * 0.5  # 现金能覆盖一半损失

            test_results.append({
                'crisis_name': crisis_name,
                'market_drop_pct': market_drop,
                'portfolio_beta': portfolio_beta,
                'current_loss_pct': current_loss_pct,
                'current_loss_value': current_loss_value,
                'adjusted_loss_pct': adjusted_loss_pct,
                'adjusted_loss_value': adjusted_loss_value,
                'cash_buffer': cash_value,
                'can_handle': can_handle
            })

        # 汇总
        avg_loss = sum(t['current_loss_pct'] for t in test_results) / len(test_results) if test_results else 0
        max_loss = min(t['current_loss_pct'] for t in test_results) if test_results else 0

        summary = {
            'average_loss_pct': avg_loss,
            'max_loss_pct': max_loss,
            'tests_passed': sum(1 for t in test_results if t['can_handle']),
            'tests_total': len(test_results),
            'current_cash_pct': cash_ratio,
            'recommended_cash_pct': 0.10
        }

        return {
            'tests': test_results,
            'summary': summary
        }

    def _estimate_portfolio_beta(self, positions: List[Dict]) -> float:
        """
        估算组合Beta

        Args:
            positions: 持仓列表

        Returns:
            组合Beta
        """
        total_beta = 0.0
        total_weight = 0.0

        for pos in positions:
            asset_name = pos.get('asset_name', '')
            ratio = pos.get('position_ratio', 0)

            # 根据资产类型估算Beta
            if any(kw in asset_name for kw in ['科技', '创业', '科创', '恒科']):
                beta = 1.3  # 科技股高Beta
            elif any(kw in asset_name for kw in ['银行', '保险', '白酒']):
                beta = 0.8  # 防守股低Beta
            elif any(kw in asset_name for kw in ['煤炭', '化工', '钢铁']):
                beta = 1.1  # 周期股中等偏高
            else:
                beta = 1.0  # 市场平均

            total_beta += beta * ratio
            total_weight += ratio

        return total_beta / total_weight if total_weight > 0 else 1.0

    def format_stress_test_report(self, test_result: Dict) -> str:
        """
        格式化压力测试报告

        Args:
            test_result: 测试结果

        Returns:
            Markdown格式报告
        """
        lines = []
        lines.append("### 💣 压力测试 (历史危机模拟)")
        lines.append("")
        lines.append("模拟历史危机对当前持仓的冲击:")
        lines.append("")

        # 表格
        lines.append("| 危机事件 | 市场跌幅 | 当前组合预计损失 | 调整后损失 | 现金缓冲 |")
        lines.append("|---------|---------|----------------|-----------|---------|")

        tests = test_result.get('tests', [])
        for test in tests:
            crisis_name = test['crisis_name']
            market_drop = test['market_drop_pct'] * 100
            current_loss_pct = abs(test['current_loss_pct']) * 100
            current_loss_value = test['current_loss_value']
            adjusted_loss_pct = abs(test['adjusted_loss_pct']) * 100
            adjusted_loss_value = test['adjusted_loss_value']
            can_handle = test['can_handle']

            handle_emoji = "✅ 可应对" if can_handle else "⚠️ 压力大"

            lines.append(
                f"| {crisis_name} | {market_drop:.0f}% | "
                f"-¥{current_loss_value/10000:.1f}万 ({current_loss_pct:.0f}%) | "
                f"-¥{adjusted_loss_value/10000:.1f}万 ({adjusted_loss_pct:.0f}%) | "
                f"{handle_emoji} |"
            )

        lines.append("")

        # 汇总结论
        summary = test_result.get('summary', {})
        current_cash_pct = summary.get('current_cash_pct', 0) * 100
        recommended_cash_pct = summary.get('recommended_cash_pct', 0) * 100
        tests_passed = summary.get('tests_passed', 0)
        tests_total = summary.get('tests_total', 0)

        lines.append("🎯 **压力测试结论**:")
        lines.append("")

        if current_cash_pct < recommended_cash_pct:
            lines.append(
                f"- 🚨 **现金不足**: 当前现金{current_cash_pct:.1f}%不足以应对历史级别危机"
            )
            lines.append(
                f"- 💡 **建议**: 补充现金至{recommended_cash_pct:.0f}%,增强抗风险能力"
            )
        else:
            lines.append(f"- ✅ **现金充足**: 当前现金{current_cash_pct:.1f}%可应对大部分危机")

        lines.append(f"- 📊 **通过测试**: {tests_passed}/{tests_total}个历史危机场景")

        lines.append("")

        return '\n'.join(lines)


if __name__ == '__main__':
    # 测试压力测试
    tester = StressTester()

    positions = [
        {'asset_name': '恒生科技ETF', 'position_ratio': 0.28, 'current_value': 144200},
        {'asset_name': '证券ETF', 'position_ratio': 0.23, 'current_value': 118450},
        {'asset_name': '白酒ETF', 'position_ratio': 0.22, 'current_value': 113300},
    ]
    total_value = 515000

    result = tester.run_stress_test(positions, total_value)
    report = tester.format_stress_test_report(result)

    print(report)
