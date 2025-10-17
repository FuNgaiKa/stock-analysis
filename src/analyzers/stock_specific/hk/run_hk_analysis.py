#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场分析脚本
提供港股综合分析功能的命令行入口
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from position_analysis.market_analyzers.hk_market_analyzer import HKMarketAnalyzer
import logging


def format_analysis_report(result: dict) -> None:
    """
    格式化输出分析报告

    Args:
        result: 分析结果字典
    """
    print("\n" + "=" * 70)
    print("港股市场历史点位对比分析报告")
    print(f"分析时间: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"指数名称: {result['index_name']}")
    print("=" * 70)

    # 检查错误
    if 'error' in result:
        print(f"\n  ✗ 分析失败: {result['error']}")
        return

    if 'warning' in result:
        print(f"\n  ⚠️  {result['warning']}")
        return

    # 1. 当前点位信息
    print(f"\n【当前市场点位】")
    print(f"  最新价格: {result['current_price']:.2f}")
    print(f"  涨跌幅: {result['current_change_pct']:+.2f}%")
    print(f"  数据日期: {result['current_date']}")
    print(f"  相似时期: {result['similar_periods_count']} 个历史点位")

    # 2. 历史点位分析
    if 'period_analysis' in result:
        print(f"\n【历史点位对比分析】")

        for period_key in ['5d', '10d', '20d', '60d']:
            if period_key not in result['period_analysis']:
                continue

            stats = result['period_analysis'][period_key]
            period_days = period_key.replace('d', '')

            print(f"\n  未来{period_days}日涨跌概率:")
            print(f"    上涨概率: {stats['up_prob']:.1%} ({stats['up_count']}次)")
            print(f"    下跌概率: {stats['down_prob']:.1%} ({stats['down_count']}次)")
            print(f"    平均收益: {stats['mean_return']:+.2%}")
            print(f"    收益中位数: {stats['median_return']:+.2%}")
            print(f"    收益区间: [{stats['min_return']:.2%}, {stats['max_return']:.2%}]")
            print(f"    置信度: {stats.get('confidence', 0):.1%}")

            if 'position_advice' in stats:
                advice = stats['position_advice']
                print(f"    仓位建议: {advice['description']}")

    # 3. Phase 3 深度分析
    if 'phase3_analysis' in result:
        phase3 = result['phase3_analysis']

        # AH溢价
        if 'ah_premium' in phase3:
            print(f"\n【AH股溢价分析】")
            ah = phase3['ah_premium']
            if 'median_premium' in ah:
                print(f"  平均溢价率: {ah['avg_premium']:.2f}%")
                print(f"  中位溢价率: {ah['median_premium']:.2f}%")
                print(f"  溢价水平: {ah['level']}")
            else:
                print(f"  溢价水平: {ah.get('level', '数据不足')}")

        # 南向资金
        if 'southbound_funds' in phase3:
            print(f"\n【南向资金流向】")
            flow = phase3['southbound_funds']
            if 'recent_5d_flow' in flow:
                print(f"  近5日累计: {flow['recent_5d_flow']:.2f} 亿元")
                print(f"  流向状态: {flow['status']}")

    # 4. 综合建议
    print(f"\n【投资建议】")
    if 'period_analysis' in result and '20d' in result['period_analysis']:
        stats = result['period_analysis']['20d']
        up_prob = stats['up_prob']

        if up_prob >= 0.7:
            suggestion = "历史数据显示该点位后续上涨概率较高，可考虑积极配置"
        elif up_prob >= 0.5:
            suggestion = "历史数据显示该点位后续涨跌概率相当，建议观望为主"
        else:
            suggestion = "历史数据显示该点位后续下跌概率较高，建议谨慎操作"

        print(f"  {suggestion}")
        print(f"\n  风险提示:")
        print(f"    - 历史表现不代表未来结果，请结合基本面和政策面综合判断")
        print(f"    - 建议关注南向资金流向和AH溢价变化")

    print("\n" + "=" * 70)


def main():
    """主函数"""
    print("=" * 70)
    print("港股市场分析工具")
    print("=" * 70)

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 创建分析器
    analyzer = HKMarketAnalyzer()

    # 执行分析 - 默认分析恒生指数
    print("\n正在分析港股市场数据，请稍候...")
    result = analyzer.analyze_single_index('HSI', tolerance=0.05)

    # 输出报告
    format_analysis_report(result)

    print("\n分析完成！")


if __name__ == "__main__":
    main()
