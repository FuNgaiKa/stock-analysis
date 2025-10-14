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
        print(f"    - KDJ K: {hsi['kdj_k']:.2f}")
        print(f"    - KDJ D: {hsi['kdj_d']:.2f}")
        print(f"    - KDJ J: {hsi['kdj_j']:.2f}")
        print(f"    - KDJ 信号: {hsi['kdj_signal']}")
        print(f"    - DMI+: {hsi['dmi_plus']:.2f}")
        print(f"    - DMI-: {hsi['dmi_minus']:.2f}")
        print(f"    - ADX: {hsi['adx']:.2f}")
        print(f"    - DMI 信号: {hsi['dmi_signal']}")
        print(f"    - MACD DIF: {hsi['macd_dif']:.2f}")
        print(f"    - MACD DEA: {hsi['macd_dea']:.2f}")
        print(f"    - MACD 柱: {hsi['macd_hist']:.2f}")
        print(f"    - MACD 信号: {hsi['macd_signal']}")
        print(f"  布林带:")
        print(f"    - 上轨: {hsi['bb_upper']:.2f}")
        print(f"    - 中轨: {hsi['bb_middle']:.2f}")
        print(f"    - 下轨: {hsi['bb_lower']:.2f}")
        print(f"    - 带宽: {hsi['bb_width']:.2f}%")
        print(f"    - 位置: {hsi['bb_signal']}")
        print(f"  波动与成交量:")
        print(f"    - ATR: {hsi['atr']:.2f} ({hsi['atr_pct']:.2f}%)")
        print(f"    - 量比: {hsi['volume_ratio']:.2f}")
        print(f"    - 量价背离: {hsi['volume_divergence']}")
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
        print(f"  技术指标:")
        print(f"    - RSI: {tech['rsi']:.2f}")
        print(f"    - KDJ 信号: {tech['kdj_signal']} (K:{tech['kdj_k']:.1f} D:{tech['kdj_d']:.1f} J:{tech['kdj_j']:.1f})")
        print(f"    - DMI 信号: {tech['dmi_signal']} (ADX:{tech['adx']:.1f})")
        print(f"    - MACD 信号: {tech['macd_signal']}")
        print(f"    - 布林带位置: {tech['bb_signal']}")
        print(f"    - 量比: {tech['volume_ratio']:.2f}")
        print(f"    - 量价背离: {tech['volume_divergence']}")
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
            kdj_k = result['hsi_analysis'].get('kdj_k', 50)
            kdj_d = result['hsi_analysis'].get('kdj_d', 50)
            kdj_j = result['hsi_analysis'].get('kdj_j', 50)
            kdj_signal = result['hsi_analysis'].get('kdj_signal', '')
            adx = result['hsi_analysis'].get('adx', 0)
            dmi_signal = result['hsi_analysis'].get('dmi_signal', '')
            macd_signal = result['hsi_analysis'].get('macd_signal', '')
            bb_signal = result['hsi_analysis'].get('bb_signal', '')
            volume_divergence = result['hsi_analysis'].get('volume_divergence', '')
            volume_ratio = result['hsi_analysis'].get('volume_ratio', 1.0)

            if rsi > 70:
                print(f"    - 恒指RSI达{rsi:.1f}，市场可能短期超买")
            elif rsi < 30:
                print(f"    - 恒指RSI仅{rsi:.1f}，市场可能短期超卖，关注反弹机会")

            # KDJ 风险提示
            if kdj_k > 80 and kdj_d > 80:
                print(f"    - KDJ高位超买 (K:{kdj_k:.1f} D:{kdj_d:.1f})，警惕短期回调")
            elif kdj_k < 20 and kdj_d < 20:
                print(f"    - KDJ低位超卖 (K:{kdj_k:.1f} D:{kdj_d:.1f})，关注反弹机会")
            elif "高位死叉" in kdj_signal:
                print(f"    - KDJ高位死叉，短期见顶信号")
            elif "低位金叉" in kdj_signal:
                print(f"    - KDJ低位金叉，底部反转信号")

            if kdj_j > 100:
                print(f"    - KDJ的J值达{kdj_j:.1f}，严重超买，警惕快速回调")
            elif kdj_j < 0:
                print(f"    - KDJ的J值仅{kdj_j:.1f}，严重超卖，可能出现反弹")

            # DMI/ADX 风险提示
            if adx > 50:
                print(f"    - ADX达{adx:.1f}，趋势极强，顺势操作")
            elif adx > 25:
                print(f"    - ADX达{adx:.1f}，趋势明确 ({dmi_signal})")
            elif adx < 20:
                print(f"    - ADX仅{adx:.1f}，市场无明显趋势，震荡市操作")

            if macd_signal == "死叉":
                print(f"    - MACD出现死叉信号，注意短期回调风险")
            elif macd_signal == "金叉":
                print(f"    - MACD出现金叉信号，可关注上涨机会")

            if bb_signal == "突破上轨":
                print(f"    - 价格突破布林带上轨，短期超买，警惕回调")
            elif bb_signal == "突破下轨":
                print(f"    - 价格突破布林带下轨，短期超卖，关注反弹")
            elif bb_signal == "接近下轨":
                print(f"    - 价格接近布林带下轨，可能存在支撑")

            if volume_divergence == "顶背离":
                print(f"    - 出现量价顶背离，价格创新高但成交量未跟上，警惕见顶")
            elif volume_divergence == "底背离":
                print(f"    - 出现量价底背离，可能是见底信号")

            if volume_ratio > 2.0:
                print(f"    - 量比达{volume_ratio:.1f}，成交量异常放大，关注市场变化")
            elif volume_ratio < 0.5:
                print(f"    - 量比仅{volume_ratio:.1f}，成交清淡，警惕流动性风险")

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
