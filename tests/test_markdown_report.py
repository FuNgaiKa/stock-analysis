#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Markdown报告生成
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from strategies.position.reporting.report_generator import MarkdownReportGenerator
from datetime import datetime

def test_markdown_report():
    """测试Markdown报告生成"""

    md_gen = MarkdownReportGenerator()

    # 测试数据
    positions = {
        'sh000001': {'name': '上证指数', 'price': 3882.77, 'date': '2025-09-30'},
        'sh000300': {'name': '沪深300', 'price': 4521.33, 'date': '2025-09-30'},
    }

    prob_stats = {
        'period_20d': {
            'up_prob': 0.65,
            'down_prob': 0.35,
            'up_count': 26,
            'down_count': 14,
            'mean_return': 0.032,
            'median_return': 0.018,
            'sample_size': 40,
            'confidence': 0.72
        }
    }

    # 生成完整报告
    full_report = ""

    # 1. 头部
    full_report += md_gen.generate_header("市场历史点位对比分析报告")

    # 2. 当前点位
    full_report += "\n\n" + md_gen.generate_current_positions_section(positions)

    # 3. 单指数分析
    full_report += "\n\n" + md_gen.generate_single_index_analysis(
        '上证指数',
        3882.77,
        48,
        {2007: 12, 2015: 7, 2025: 27},
        prob_stats,
        [20]
    )

    # 4. 仓位建议
    full_report += "\n\n" + md_gen.generate_position_advice(
        "看多",
        0.6,
        "历史数据显示上涨概率较高，建议适度增加仓位",
        {
            'stop_loss_price': 3700,
            'stop_loss_pct': -0.05,
            'take_profit_price': 4100,
            'take_profit_pct': 0.06,
            'risk_reward_ratio': 1.2
        }
    )

    # 5. 综合结论
    full_report += "\n\n" + md_gen.generate_conclusion(
        "看多",
        0.75,
        [
            "历史相似点位样本共 120 个",
            "历史数据显示，相似点位后上涨概率较高(65.0%)",
            "多指数联合匹配找到 35 个时期"
        ],
        {
            "短期(5-10日)": "可适度参与，关注放量突破",
            "中期(20-60日)": "持有为主，逢低加仓"
        }
    )

    # 6. 尾部
    full_report += "\n\n" + md_gen.generate_footer()

    # 保存到文件
    output_path = project_root / "reports" / "test_markdown_report.md"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_report)

    print(f"Success! Markdown report saved to: {output_path}")
    print(f"Report length: {len(full_report)} characters")
    return output_path


if __name__ == '__main__':
    output_path = test_markdown_report()
    print("Test completed!")
