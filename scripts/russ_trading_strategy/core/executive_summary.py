#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行摘要生成器
Executive Summary Generator

生成报告的核心结论,方便快速决策
"""

from typing import Dict, List


class ExecutiveSummaryGenerator:
    """执行摘要生成器"""

    def generate_summary(
        self,
        health_result: Dict,
        action_items: Dict,
        risk_analysis: Dict = None
    ) -> str:
        """
        生成执行摘要

        Args:
            health_result: 健康检查结果
            action_items: 操作建议
            risk_analysis: 风险分析结果

        Returns:
            Markdown格式的执行摘要
        """
        lines = []
        lines.append("## 📋 执行摘要 (一分钟速览)")
        lines.append("")

        # 核心结论
        lines.append("### 🎯 核心结论")
        lines.append("")

        health_score = health_result.get('health_score', 0)
        health_level = health_result.get('health_level', 'unknown')

        # 健康度评估
        if health_level == 'danger':
            emoji = "❌"
            status = "危险"
            action = "需立即调整"
        elif health_level == 'warning':
            emoji = "⚠️"
            status = "警告"
            action = "建议尽快调整"
        elif health_level == 'good':
            emoji = "✅"
            status = "良好"
            action = "保持当前策略"
        else:
            emoji = "🟢"
            status = "优秀"
            action = "继续保持"

        lines.append(f"- {emoji} **持仓健康度**: {health_score:.0f}分({status}) - {action}")

        # 紧急操作
        priority_1 = action_items.get('priority_1', [])
        if priority_1:
            # 提取关键操作
            urgent_actions = self._extract_urgent_actions(priority_1)
            if urgent_actions:
                urgent_summary = "、".join(urgent_actions[:3])  # 最多3个
                lines.append(f"- 🚨 **紧急操作**: {urgent_summary}")
        else:
            lines.append("- ✅ **紧急操作**: 无需立即调整")

        # 执行时间
        lines.append("- ⏰ **执行时间**: 今晚设置,明天执行")

        lines.append("")

        # 预期收益
        lines.append("### 💰 调整预期")
        lines.append("")

        expected_results = action_items.get('expected_results', '')
        if expected_results:
            # 提取关键信息
            if "降低" in expected_results and "波动率" in expected_results:
                # 简单提取,实际应该解析
                lines.append("- **调整后**: 降低组合风险,提升稳健性")
            else:
                lines.append("- **调整后**: 优化持仓结构,控制风险")

            if "不调整" in expected_results:
                lines.append("- **不调整**: 持续面临风险,建议执行调整")
        else:
            lines.append("- 当前持仓合理,保持现有配置")

        lines.append("")

        # Top 3 行动项
        checklist = action_items.get('checklist', [])
        if checklist:
            lines.append("### ⚡ Top 3 行动项")
            lines.append("")
            # 提取前3个checkbox
            top_actions = [item for item in checklist if item.startswith('- [ ] 🔥')][:3]
            if not top_actions:
                top_actions = checklist[:3]

            for i, action in enumerate(top_actions, 1):
                # 去掉checkbox格式
                clean_action = action.replace('- [ ]', f'{i}.').strip()
                lines.append(clean_action)

            lines.append("")

        # 风险提示
        if risk_analysis:
            cash_ratio = risk_analysis.get('cash_ratio', 0)
            min_required = risk_analysis.get('min_required', 0.10)
            if cash_ratio < min_required:
                lines.append("### ⚠️ 风险提示")
                lines.append("")
                lines.append(f"- 现金储备{cash_ratio*100:.1f}%低于{min_required*100:.0f}%安全线")
                lines.append("- 建议优先补充现金,应对黑天鹅事件")
                lines.append("")

        lines.append("---")
        lines.append("")

        return '\n'.join(lines)

    def _extract_urgent_actions(self, priority_1_items: List[str]) -> List[str]:
        """
        从优先级1条目中提取紧急操作

        Args:
            priority_1_items: 优先级1条目列表

        Returns:
            紧急操作摘要列表
        """
        actions = []

        for item in priority_1_items:
            # 查找包含"减仓"、"补充"等关键词的行
            if '减仓' in item and '%' in item:
                # 提取资产名称和百分比
                if '**' in item:
                    # 格式: **1. 恒生科技ETF立即减仓8%**
                    parts = item.split('**')
                    if len(parts) >= 2:
                        text = parts[1]
                        if '减仓' in text:
                            # 提取 "恒生科技ETF减仓8%"
                            asset_and_pct = text.split('立即')[0].strip() if '立即' in text else text
                            actions.append(asset_and_pct.replace('.', '').strip())

            elif '补充现金' in item and '%' in item:
                if '**' in item:
                    parts = item.split('**')
                    if len(parts) >= 2:
                        text = parts[1]
                        if '补充现金' in text:
                            actions.append("补充现金至10%")

        return actions


if __name__ == '__main__':
    # 测试执行摘要
    generator = ExecutiveSummaryGenerator()

    health_result = {
        'health_score': 45.0,
        'health_level': 'danger'
    }

    action_items = {
        'priority_1': [
            "**1. 恒生科技ETF立即减仓8%** 🔥🔥🔥",
            "**2. 证券ETF立即减仓3%** 🔥🔥🔥",
            "**3. 补充现金至10%** 🔥🔥"
        ],
        'checklist': [
            "- [ ] 🔥 **恒生科技ETF减仓8%** (当前28% → 目标20%)",
            "- [ ] 🔥 **证券ETF减仓3%** (当前23% → 目标20%)",
            "- [ ] 💰 **补充现金至10%** (当前7.0% → 缺口3.0%)"
        ],
        'expected_results': "降低波动率3.9%,如果不调整则风险扩大"
    }

    summary = generator.generate_summary(health_result, action_items)
    print(summary)
