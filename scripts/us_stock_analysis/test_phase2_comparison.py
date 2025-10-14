#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 vs Phase 2 对比测试脚本
测试技术指标增强匹配的效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from position_analysis.market_analyzers.us_market_analyzer import USMarketAnalyzer
from datetime import datetime


def print_header(title: str):
    """打印标题"""
    print(f"\n{'='*80}")
    print(f"{title:^80}")
    print(f"{'='*80}\n")


def print_comparison(phase1_result: dict, phase2_result: dict, index_name: str):
    """对比显示Phase 1和Phase 2的结果"""

    print_header(f"{index_name} - Phase 1 vs Phase 2 对比分析")

    # 当前点位信息
    print(f"📊 当前点位信息:")
    print(f"   最新价格: {phase1_result['current_price']:.2f}")
    print(f"   涨跌幅: {phase1_result['current_change_pct']:+.2f}%")
    print(f"   数据日期: {phase1_result['current_date']}")

    # Phase 2市场环境
    if 'market_environment' in phase2_result:
        env = phase2_result['market_environment']
        print(f"\n🎯 市场环境识别: {env['environment']}")
        print(f"   RSI: {env['rsi']:.1f}")
        print(f"   距52周高点: {env['dist_to_high_pct']:.1f}%")
        print(f"   均线状态: {env['ma_state']}")

    # 相似期数量对比
    print(f"\n🔍 相似历史期数对比:")
    print(f"   Phase 1 (仅价格匹配): {phase1_result.get('similar_periods_count', 0)} 个")
    print(f"   Phase 2 (技术指标过滤): {phase2_result.get('similar_periods_count', 0)} 个")

    reduction = phase1_result.get('similar_periods_count', 0) - phase2_result.get('similar_periods_count', 0)
    if phase1_result.get('similar_periods_count', 0) > 0:
        reduction_pct = reduction / phase1_result.get('similar_periods_count', 1) * 100
        print(f"   过滤掉: {reduction} 个 ({reduction_pct:.1f}%)")

    # 20日周期详细对比
    if '20d' in phase1_result.get('period_analysis', {}) and '20d' in phase2_result.get('period_analysis', {}):
        stats_p1 = phase1_result['period_analysis']['20d']
        stats_p2 = phase2_result['period_analysis']['20d']

        print(f"\n📈 20日周期核心指标对比:")
        print(f"\n   {'指标':<20} {'Phase 1':>15} {'Phase 2':>15} {'变化':>15}")
        print(f"   {'-'*70}")

        # 上涨概率
        prob_diff = stats_p2['up_prob'] - stats_p1['up_prob']
        print(f"   {'上涨概率':<20} {stats_p1['up_prob']:>14.1%} {stats_p2['up_prob']:>14.1%} {prob_diff:>+14.1%}")

        # 平均收益
        return_diff = stats_p2['mean_return'] - stats_p1['mean_return']
        print(f"   {'平均收益':<20} {stats_p1['mean_return']:>+14.2%} {stats_p2['mean_return']:>+14.2%} {return_diff:>+14.2%}")

        # 中位收益
        median_diff = stats_p2['median_return'] - stats_p1['median_return']
        print(f"   {'中位收益':<20} {stats_p1['median_return']:>+14.2%} {stats_p2['median_return']:>+14.2%} {median_diff:>+14.2%}")

        # 置信度
        conf_diff = stats_p2.get('confidence', 0) - stats_p1.get('confidence', 0)
        print(f"   {'置信度':<20} {stats_p1.get('confidence', 0):>14.1%} {stats_p2.get('confidence', 0):>14.1%} {conf_diff:>+14.1%}")

        # 仓位建议对比
        if 'position_advice' in stats_p1 and 'position_advice' in stats_p2:
            advice_p1 = stats_p1['position_advice']
            advice_p2 = stats_p2['position_advice']

            print(f"\n💡 仓位建议对比:")
            print(f"   Phase 1: {advice_p1['signal']} (推荐仓位 {advice_p1['recommended_position']:.1%})")
            print(f"   Phase 2: {advice_p2['signal']} (推荐仓位 {advice_p2['recommended_position']:.1%})")

            if 'warning' in advice_p2:
                print(f"   ⚠️  {advice_p2['warning']}")

            pos_diff = advice_p2['recommended_position'] - advice_p1['recommended_position']
            print(f"   仓位变化: {pos_diff:+.1%}")

    print(f"\n{'='*80}\n")


def main():
    """主测试函数"""
    print_header("Phase 1 vs Phase 2 增强分析对比测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试目的: 验证技术指标过滤是否能更准确识别市场高位风险\n")

    # 创建分析器
    analyzer = USMarketAnalyzer()

    # 测试指数列表
    test_indices = ['SPX', 'NASDAQ', 'NDX']

    for index_code in test_indices:
        try:
            print(f"\n正在分析 {index_code}...")

            # Phase 1分析 (仅价格匹配)
            result_p1 = analyzer.analyze_single_index(
                index_code=index_code,
                tolerance=0.05,
                periods=[5, 10, 20, 60],
                use_phase2=False
            )

            # Phase 2分析 (技术指标增强)
            result_p2 = analyzer.analyze_single_index(
                index_code=index_code,
                tolerance=0.05,
                periods=[5, 10, 20, 60],
                use_phase2=True
            )

            # 对比显示
            if 'error' not in result_p1 and 'error' not in result_p2:
                print_comparison(result_p1, result_p2, result_p1['index_name'])
            else:
                print(f"❌ {index_code} 分析失败")
                if 'error' in result_p1:
                    print(f"   Phase 1 错误: {result_p1['error']}")
                if 'error' in result_p2:
                    print(f"   Phase 2 错误: {result_p2['error']}")

        except Exception as e:
            print(f"❌ {index_code} 分析异常: {str(e)}")
            import traceback
            traceback.print_exc()

    # 总结
    print_header("测试总结")
    print("✅ Phase 2增强分析主要改进:")
    print("   1. 技术指标过滤: 确保历史匹配点位与当前技术状态相似")
    print("   2. 市场环境识别: 识别牛市顶部/底部等关键位置")
    print("   3. 高位风险警示: 在牛市顶部降低仓位建议")
    print("   4. 更准确的概率: 通过过滤不相似的历史点位,提高预测准确性")
    print("\n预期效果:")
    print("   - 相似期数量减少 (过滤掉技术状态不匹配的点位)")
    print("   - 上涨概率更保守 (剔除了不同市场环境的误导性数据)")
    print("   - 仓位建议更谨慎 (在高位市场降低推荐仓位)")
    print("   - 增加风险警示 (明确提示当前市场环境)")


if __name__ == "__main__":
    main()
