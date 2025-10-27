#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
归因分析模块
Attribution Analyzer

解释健康度评分的扣分来源
"""

from typing import Dict, List


class AttributionAnalyzer:
    """归因分析器"""

    def analyze_health_attribution(
        self,
        health_result: Dict
    ) -> Dict:
        """
        分析健康度归因

        Args:
            health_result: 健康检查结果

        Returns:
            归因分析结果
        """
        base_score = 100.0
        deductions = []

        checks = health_result.get('checks', {})

        # 总仓位检查
        total_position_check = checks.get('total_position', {})
        if not total_position_check.get('passed', True):
            penalty = total_position_check.get('penalty', 0)
            if penalty > 0:
                deductions.append({
                    'item': '总仓位超标',
                    'penalty': penalty,
                    'reason': total_position_check.get('message', '')
                })

        # 现金储备检查
        cash_check = checks.get('cash_reserve', {})
        if not cash_check.get('passed', True):
            penalty = cash_check.get('penalty', 0)
            if penalty > 0:
                deductions.append({
                    'item': '现金储备不足',
                    'penalty': penalty,
                    'reason': cash_check.get('message', '')
                })

        # 单一标的检查
        single_pos_check = checks.get('single_positions', {})
        if not single_pos_check.get('passed', True):
            penalty = single_pos_check.get('penalty', 0)
            if penalty > 0:
                deductions.append({
                    'item': '单一标的超配',
                    'penalty': penalty,
                    'reason': f"有{len(single_pos_check.get('overweight_assets', []))}个标的超配"
                })

        # 标的数量检查
        asset_count_check = checks.get('asset_count', {})
        if not asset_count_check.get('passed', True):
            penalty = asset_count_check.get('penalty', 0)
            if penalty > 0:
                deductions.append({
                    'item': '标的数量不合理',
                    'penalty': penalty,
                    'reason': asset_count_check.get('message', '')
                })

        # 计算最终得分
        final_score = base_score - sum(d['penalty'] for d in deductions)

        return {
            'base_score': base_score,
            'deductions': deductions,
            'final_score': final_score,
            'total_penalty': sum(d['penalty'] for d in deductions)
        }

    def format_attribution_report(self, attribution: Dict) -> str:
        """格式化归因分析报告"""
        lines = []
        lines.append("### 🔍 健康度归因分析")
        lines.append("")
        lines.append(f"**基准分**: {attribution['base_score']:.0f}分")
        lines.append("")

        if attribution['deductions']:
            lines.append("**扣分明细**:")
            lines.append("")
            for deduction in attribution['deductions']:
                item = deduction['item']
                penalty = deduction['penalty']
                reason = deduction['reason']
                lines.append(f"- {item}: **-{penalty:.0f}分**")
                lines.append(f"  - 原因: {reason}")

            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("")

        final_score = attribution['final_score']
        lines.append(f"**最终得分**: **{final_score:.0f}分**")

        # 评级
        if final_score >= 90:
            level = "🟢 优秀"
        elif final_score >= 70:
            level = "🟡 良好"
        elif final_score >= 50:
            level = "🟠 警告"
        else:
            level = "🔴 危险"

        lines.append(f"**健康等级**: {level}")
        lines.append("")

        return '\n'.join(lines)


if __name__ == '__main__':
    # 测试归因分析
    analyzer = AttributionAnalyzer()

    # 模拟健康检查结果
    health_result = {
        'health_score': 45.0,
        'checks': {
            'total_position': {
                'passed': False,
                'penalty': 15.0,
                'message': '总仓位93%超标'
            },
            'cash_reserve': {
                'passed': False,
                'penalty': 15.0,
                'message': '现金7%不足'
            },
            'single_positions': {
                'passed': False,
                'penalty': 15.0,
                'overweight_assets': [{'name': '恒科'}, {'name': '证券'}]
            },
            'asset_count': {
                'passed': False,
                'penalty': 10.0,
                'message': '持仓9只偏多'
            }
        }
    }

    attribution = analyzer.analyze_health_attribution(health_result)
    report = analyzer.format_attribution_report(attribution)

    print(report)
