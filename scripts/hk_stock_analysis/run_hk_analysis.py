#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场分析脚本
提供港股综合分析功能的命令行入口
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from position_analysis.hk_market_analyzer import HKMarketAnalyzer
import logging


def format_analysis_report(result: dict) -> None:
    """
    格式化输出分析报告

    Args:
        result: 分析结果字典
    """
    print("\n" + "=" * 70)
    print("港股市场综合分析报告")
    print(f"分析时间: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. 恒生指数
    print("\n【恒生指数】")
    if 'hsi_analysis' in result and 'error' not in result['hsi_analysis']:
        hsi = result['hsi_analysis']
        print(f"  最新点位: {hsi['latest_price']:.2f}")
        print(f"  涨跌幅: {hsi['change_pct']:+.2f}% ({hsi['change']:+.2f}点)")
        print(f"  趋势状态: {hsi['trend']}")
        print(f"  技术指标:")
        print(f"    - MA20: {hsi['ma20']:.2f}")
        print(f"    - MA60: {hsi['ma60']:.2f}")
        print(f"    - MA120: {hsi['ma120']:.2f}")
        print(f"    - RSI: {hsi['rsi']:.2f}")
        print(f"  52周表现:")
        print(f"    - 52周最高: {hsi['high_52w']:.2f} (距离: {hsi['dist_to_high_pct']:+.2f}%)")
        print(f"    - 52周最低: {hsi['low_52w']:.2f} (距离: {hsi['dist_to_low_pct']:+.2f}%)")
        print(f"  年化波动率: {hsi['volatility']:.2%}")
    else:
        print("  数据获取失败")

    # 2. 恒生科技指数
    print("\n【恒生科技指数】")
    if 'hstech_analysis' in result and 'error' not in result['hstech_analysis']:
        tech = result['hstech_analysis']
        print(f"  最新点位: {tech['latest_price']:.2f}")
        print(f"  涨跌幅: {tech['change_pct']:+.2f}% ({tech['change']:+.2f}点)")
        print(f"  趋势状态: {tech['trend']}")
        print(f"  RSI: {tech['rsi']:.2f}")
    else:
        print("  数据获取失败")

    # 3. 南向资金
    print("\n【南向资金流向】")
    if 'capital_flow' in result and 'error' not in result['capital_flow']:
        flow = result['capital_flow']
        print(f"  近3日累计: {flow['recent_3d_flow']:.2f} 亿元")
        print(f"  近5日累计: {flow['recent_5d_flow']:.2f} 亿元")
        print(f"  总计流向: {flow['total_flow']:.2f} 亿元")
        print(f"  日均流向: {flow['avg_daily_flow']:.2f} 亿元")
        print(f"  流向状态: {flow['status']}")
        print(f"  净流入天数: {flow['positive_days']}/{flow['data_days']} 天")
    else:
        print("  数据获取失败")

    # 4. AH股溢价
    print("\n【AH股溢价分析】")
    if 'ah_premium' in result and 'error' not in result['ah_premium']:
        ah = result['ah_premium']
        print(f"  AH股对数: {ah['total_stocks']} 只")
        if 'median_premium' in ah:
            print(f"  平均溢价率: {ah['avg_premium']:.2f}%")
            print(f"  中位溢价率: {ah['median_premium']:.2f}%")
            print(f"  溢价率区间: {ah['min_premium']:.2f}% ~ {ah['max_premium']:.2f}%")
            print(f"  高溢价股票: {ah['high_premium_count']} 只 (>30%)")
            print(f"  H股溢价股票: {ah['negative_premium_count']} 只")
            print(f"  溢价水平: {ah['level']}")
        else:
            print(f"  溢价水平: {ah['level']}")
    else:
        print("  数据获取失败")

    # 5. 市场广度
    print("\n【市场广度】")
    if 'market_breadth' in result and 'error' not in result['market_breadth']:
        breadth = result['market_breadth']
        print(f"  总股票数: {breadth['total_stocks']} 只")
        print(f"  上涨: {breadth['up_count']} 只 ({breadth['up_ratio']:.1%})")
        print(f"  下跌: {breadth['down_count']} 只")
        print(f"  平盘: {breadth['flat_count']} 只")
        print(f"  涨幅>3%: {breadth['up_3pct_count']} 只")
        print(f"  涨幅>5%: {breadth['up_5pct_count']} 只")
        print(f"  跌幅>3%: {breadth['down_3pct_count']} 只")
        print(f"  跌幅>5%: {breadth['down_5pct_count']} 只")
        print(f"  市场状态: {breadth['status']}")
    else:
        print("  数据获取失败")

    # 6. 综合评分
    print("\n【综合评分】")
    if 'comprehensive_score' in result:
        comp = result['comprehensive_score']
        print(f"  综合得分: {comp['score']:.2f}/1.00")
        print(f"  市场评级: {comp['rating']}")
        print(f"  评分因子:")
        for factor in comp['factors']:
            print(f"    - {factor}")
    else:
        print("  评分计算失败")

    # 7. 投资建议
    print("\n【投资建议】")
    if 'comprehensive_score' in result:
        score = result['comprehensive_score']['score']
        rating = result['comprehensive_score']['rating']

        if score >= 0.7:
            suggestion = "市场处于强势状态，可考虑积极配置。建议关注南向资金持续流入的优质标的。"
        elif score >= 0.5:
            suggestion = "市场中性偏强，可适当参与。建议关注恒生科技等成长板块机会。"
        elif score >= 0.3:
            suggestion = "市场偏弱，建议保持谨慎。可关注防御性板块或等待更好时机。"
        else:
            suggestion = "市场较弱，建议降低仓位。等待市场企稳信号后再考虑配置。"

        print(f"  {suggestion}")

        # 风险提示
        print(f"\n  风险提示:")
        if 'hsi_analysis' in result and 'error' not in result['hsi_analysis']:
            rsi = result['hsi_analysis'].get('rsi', 50)
            if rsi > 70:
                print(f"    - 恒指RSI达{rsi:.1f}，市场可能短期超买")
            elif rsi < 30:
                print(f"    - 恒指RSI仅{rsi:.1f}，市场可能短期超卖，关注反弹机会")

        if 'ah_premium' in result and 'median_premium' in result['ah_premium']:
            premium = result['ah_premium']['median_premium']
            if premium > 130:
                print(f"    - AH溢价率达{premium:.1f}%，A股相对港股估值较高")

    print("\n" + "=" * 70)


def main():
    """主函数"""
    print("=" * 70)
    print("港股市场分析工具")
    print("=" * 70)

    # 配置日志
    logging.basicConfig(
        level=logging.WARNING,  # 只显示警告和错误
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 创建分析器
    analyzer = HKMarketAnalyzer()

    # 执行综合分析
    print("\n正在分析港股市场数据，请稍候...")
    result = analyzer.comprehensive_analysis()

    # 输出报告
    format_analysis_report(result)

    print("\n分析完成！")


if __name__ == "__main__":
    main()
