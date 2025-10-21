#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表生成器
Chart Generator

生成ASCII格式的图表,用于Markdown报告
"""

from typing import Dict, List
import math


class ChartGenerator:
    """ASCII图表生成器"""

    def generate_position_bar_chart(
        self,
        positions: List[Dict],
        max_width: int = 50
    ) -> str:
        """
        生成持仓结构条形图 (ASCII)

        Args:
            positions: 持仓列表
            max_width: 最大宽度

        Returns:
            ASCII条形图
        """
        lines = []
        lines.append("### 📊 持仓结构分布")
        lines.append("")
        lines.append("```")

        # 按仓位排序
        sorted_positions = sorted(
            positions,
            key=lambda x: x.get('position_ratio', 0),
            reverse=True
        )

        # 找出最大仓位
        max_ratio = max(p.get('position_ratio', 0) for p in sorted_positions) if sorted_positions else 0

        for pos in sorted_positions:
            asset_name = pos.get('asset_name', 'Unknown')
            ratio = pos.get('position_ratio', 0)
            pct = ratio * 100

            # 计算条形长度
            if max_ratio > 0:
                bar_length = int((ratio / max_ratio) * max_width)
            else:
                bar_length = 0

            # 生成条形
            bar = "█" * bar_length

            # 格式化输出
            lines.append(f"{asset_name:15s} [{pct:5.1f}%] {bar}")

        lines.append("```")
        lines.append("")

        # 集中度分析
        if len(sorted_positions) >= 3:
            top3_ratio = sum(p.get('position_ratio', 0) for p in sorted_positions[:3])
            lines.append(f"**集中度**: 前3大持仓占比 {top3_ratio*100:.1f}%")

            if top3_ratio > 0.70:
                lines.append("- ⚠️ 高集中度,分散风险建议")
            elif top3_ratio > 0.50:
                lines.append("- ✅ 中等集中度,较为合理")
            else:
                lines.append("- 📊 低集中度,过度分散")

        lines.append("")

        return '\n'.join(lines)

    def generate_correlation_heatmap(
        self,
        correlation_matrix: Dict[str, Dict[str, float]]
    ) -> str:
        """
        生成相关性热力图 (ASCII)

        Args:
            correlation_matrix: 相关性矩阵 {资产1: {资产2: 相关系数}}

        Returns:
            ASCII热力图
        """
        if not correlation_matrix:
            return ""

        lines = []
        lines.append("### 🔗 相关性矩阵")
        lines.append("")

        # 获取资产列表
        assets = list(correlation_matrix.keys())

        # 生成表格
        # 表头
        header = "| " + " | ".join([""] + [a[:4] for a in assets]) + " |"
        separator = "|" + "|".join(["---"] * (len(assets) + 1)) + "|"

        lines.append(header)
        lines.append(separator)

        # 数据行
        for asset1 in assets:
            row_data = [asset1[:4]]
            for asset2 in assets:
                corr = correlation_matrix.get(asset1, {}).get(asset2, 0)
                # 格式化相关系数
                row_data.append(f"{corr:.2f}")

            line = "| " + " | ".join(row_data) + " |"
            lines.append(line)

        lines.append("")

        # 相关性分析
        lines.append("**相关性分析**:")
        lines.append("")

        # 找出高相关对
        high_corr_pairs = []
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                if i < j:  # 避免重复
                    corr = correlation_matrix.get(asset1, {}).get(asset2, 0)
                    if abs(corr) > 0.75:
                        high_corr_pairs.append((asset1, asset2, corr))

        if high_corr_pairs:
            lines.append("高度相关标的 (|相关系数| > 0.75):")
            for asset1, asset2, corr in high_corr_pairs:
                emoji = "⚠️" if corr > 0 else "ℹ️"
                corr_type = "正相关" if corr > 0 else "负相关"
                lines.append(f"- {emoji} {asset1} ↔ {asset2}: {corr:.2f} ({corr_type})")

            lines.append("")
            lines.append("💡 **建议**: 高度相关的标的分散效果有限,考虑调整配置")
        else:
            lines.append("- ✅ 各标的相关性适中,分散效果良好")

        lines.append("")

        return '\n'.join(lines)

    def generate_risk_return_scatter(
        self,
        assets_data: List[Dict]
    ) -> str:
        """
        生成风险-收益散点图 (ASCII)

        Args:
            assets_data: [{name, return, risk}]

        Returns:
            ASCII散点图描述
        """
        if not assets_data:
            return ""

        lines = []
        lines.append("### 🎯 风险-收益分布")
        lines.append("")
        lines.append("```")
        lines.append("                高收益")
        lines.append("                  ↑")

        # 简单分象限
        for asset in assets_data:
            name = asset.get('name', '')
            ret = asset.get('return', 0)
            risk = asset.get('risk', 0)

            # 判断象限
            if ret > 0.10 and risk > 0.30:
                pos = "右上 (高风险高收益)"
                emoji = "●"
            elif ret > 0.10 and risk <= 0.30:
                pos = "左上 (低风险高收益)"
                emoji = "★"
            elif ret <= 0.10 and risk > 0.30:
                pos = "右下 (高风险低收益)"
                emoji = "▼"
            else:
                pos = "左下 (低风险低收益)"
                emoji = "○"

            lines.append(f"   {name:10s} {emoji}  [{pos}]")

        lines.append("─────────────────┼─────────────→ 高风险")
        lines.append("                  ↓")
        lines.append("                低收益")
        lines.append("```")
        lines.append("")

        lines.append("**图例**:")
        lines.append("- ★ 最优区域 (低风险高收益)")
        lines.append("- ● 进攻区域 (高风险高收益)")
        lines.append("- ○ 防守区域 (低风险低收益)")
        lines.append("- ▼ 劣势区域 (高风险低收益,应避免)")
        lines.append("")

        return '\n'.join(lines)

    def generate_waterfall_chart(
        self,
        base_value: float,
        changes: List[Dict]  # [{label, value}]
    ) -> str:
        """
        生成瀑布图 (ASCII) - 用于归因分析

        Args:
            base_value: 基准值
            changes: 变化列表

        Returns:
            ASCII瀑布图
        """
        lines = []
        lines.append("```")

        current_value = base_value
        lines.append(f"基准分: {base_value:.0f}  ████████████")

        for change in changes:
            label = change.get('label', '')
            value = change.get('value', 0)

            current_value += value

            # 生成条形
            bar_length = abs(int(value / 2))  # 简化比例
            if value < 0:
                bar = "▼" * bar_length
                sign = "-"
            else:
                bar = "▲" * bar_length
                sign = "+"

            lines.append(f"{label:15s} {sign}{abs(value):.0f}  {bar}")

        lines.append(f"{'─' * 40}")
        lines.append(f"最终得分: {current_value:.0f}")
        lines.append("```")
        lines.append("")

        return '\n'.join(lines)


if __name__ == '__main__':
    # 测试图表生成
    generator = ChartGenerator()

    print("=== 测试持仓条形图 ===")
    positions = [
        {'asset_name': '恒生科技ETF', 'position_ratio': 0.28},
        {'asset_name': '证券ETF', 'position_ratio': 0.23},
        {'asset_name': '白酒ETF', 'position_ratio': 0.22},
        {'asset_name': '化工ETF', 'position_ratio': 0.07},
    ]
    chart = generator.generate_position_bar_chart(positions)
    print(chart)

    print("\n=== 测试瀑布图 ===")
    changes = [
        {'label': '仓位超标', 'value': -15},
        {'label': '现金不足', 'value': -15},
        {'label': '标的过多', 'value': -10},
    ]
    waterfall = generator.generate_waterfall_chart(100, changes)
    print(waterfall)
