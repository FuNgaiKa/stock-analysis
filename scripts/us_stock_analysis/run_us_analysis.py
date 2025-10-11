#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股市场分析运行脚本
支持标普500、纳斯达克、纳斯达克100、VIX等指数的历史点位对比分析
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import logging
from datetime import datetime
from position_analysis.us_market_analyzer import USMarketAnalyzer, DEFAULT_US_INDICES, US_INDICES

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """打印标题"""
    width = 80
    print("\n" + "=" * width)
    print(f"{title:^{width}}")
    print("=" * width)


def print_section(title: str):
    """打印章节"""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}")


def print_single_index_analysis(result: dict, detail: bool = True):
    """打印单指数分析结果"""
    print_section(f"{result['index_name']} 分析结果")

    if 'error' in result:
        print(f"  ❌ 分析失败: {result['error']}")
        return

    if 'warning' in result:
        print(f"  ⚠️  {result['warning']}")
        return

    # 当前点位
    print(f"\n  📊 当前点位信息:")
    print(f"     最新价格: {result['current_price']:.2f}")
    print(f"     涨跌幅: {result['current_change_pct']:+.2f}%")
    print(f"     数据日期: {result['current_date']}")
    print(f"     相似时期: {result.get('similar_periods_count', 0)} 个历史点位")

    # 市场环境信息(Phase 2)
    if 'market_environment' in result:
        env = result['market_environment']
        print(f"\n  🎯 市场环境识别 (Phase 2):")
        print(f"     环境类型: {env['environment']}")
        print(f"     RSI: {env['rsi']:.1f}")
        print(f"     距52周高点: {env['dist_to_high_pct']:.1f}%")
        print(f"     均线状态: {env['ma_state']}")

    # 各周期分析
    if 'period_analysis' in result and detail:
        print(f"\n  📈 历史点位对比分析:")
        print(f"     {'周期':6} {'样本数':>6} {'上涨概率':>10} {'平均收益':>10} {'中位收益':>10} {'置信度':>8} {'仓位建议':>10}")
        print(f"     {'-' * 68}")

        for period_key in ['5d', '10d', '20d', '60d']:
            if period_key in result['period_analysis']:
                stats = result['period_analysis'][period_key]
                period_days = period_key.replace('d', '')

                print(f"     {period_days+'日':6} "
                      f"{stats['sample_size']:>6} "
                      f"{stats['up_prob']:>9.1%} "
                      f"{stats['mean_return']:>9.2%} "
                      f"{stats['median_return']:>9.2%} "
                      f"{stats.get('confidence', 0):>7.1%} ", end='')

                if 'position_advice' in stats:
                    advice = stats['position_advice']
                    signal_color = {
                        '强买入': '\033[1;32m',  # 绿色
                        '买入': '\033[0;32m',
                        '中性': '\033[0;33m',    # 黄色
                        '卖出': '\033[0;31m',    # 红色
                        '强卖出': '\033[1;31m'
                    }.get(advice['signal'], '\033[0m')
                    reset_color = '\033[0m'
                    print(f"{signal_color}{advice['recommended_position']:>9.1%}{reset_color}")
                else:
                    print(f"{'--':>10}")

    # 重点关注20日周期
    if 'period_analysis' in result and '20d' in result['period_analysis']:
        stats_20d = result['period_analysis']['20d']

        print(f"\n  💡 20日周期核心结论:")
        print(f"     上涨概率: {stats_20d['up_prob']:.1%} (上涨 {stats_20d['up_count']} 次, 下跌 {stats_20d['down_count']} 次)")
        print(f"     预期收益: {stats_20d['mean_return']:+.2%} (中位数 {stats_20d['median_return']:+.2%})")
        print(f"     收益区间: [{stats_20d['min_return']:.2%}, {stats_20d['max_return']:.2%}]")
        print(f"     置信度: {stats_20d.get('confidence', 0):.1%}")

        if 'position_advice' in stats_20d:
            advice = stats_20d['position_advice']
            print(f"     \n     🎯 {advice['description']}")
            if 'warning' in advice:
                print(f"     {advice['warning']}")

    # Phase 3深度分析结果
    if 'phase3_analysis' in result:
        phase3 = result['phase3_analysis']

        # VIX分析
        if 'vix' in phase3:
            vix = phase3['vix']
            if 'current_state' in vix:
                vix_state = vix['current_state']
                print(f"\n  🔥 VIX恐慌指数分析:")
                print(f"     VIX当前值: {vix_state['vix_value']:.2f} ({vix_state['status']})")
                print(f"     日变化: {vix_state['change']:+.2f} ({vix_state['change_pct']:+.2f}%)")

            if 'signal' in vix:
                vix_signal = vix['signal']
                print(f"     交易信号: {vix_signal['signal']} - {vix_signal['description']}")
                print(f"     操作建议: {vix_signal['action']}")

        # 行业轮动分析
        if 'sector_rotation' in phase3:
            sector = phase3['sector_rotation']
            if 'rotation_pattern' in sector:
                pattern = sector['rotation_pattern']
                print(f"\n  🔄 行业轮动分析:")
                print(f"     轮动模式: {pattern['pattern']}")
                print(f"     模式描述: {pattern['description']}")

            if 'allocation_recommendation' in sector:
                alloc = sector['allocation_recommendation']
                print(f"     配置建议: {alloc['recommendation']}")
                if 'recommended_sectors' in alloc:
                    print(f"     推荐行业: {', '.join(alloc['recommended_sectors'])}")

        # 成交量分析
        if 'volume' in phase3:
            volume = phase3['volume']
            if 'volume_status' in volume:
                vol_status = volume['volume_status']
                print(f"\n  📊 成交量分析:")
                print(f"     成交量状态: {vol_status['status']}")
                print(f"     {vol_status['description']}")

            if 'signal' in volume:
                vol_signal = volume['signal']
                print(f"     交易信号: {vol_signal['signal']} - {vol_signal['description']}")


def print_multi_index_analysis(result: dict):
    """打印多指数分析结果"""
    print_header("美股市场综合分析报告")
    print(f"\n  分析时间: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  分析指数: {', '.join([US_INDICES[i].name for i in result['indices_analyzed']])}")

    # 各指数分析
    for index_code, analysis in result['individual_analysis'].items():
        print_single_index_analysis(analysis, detail=False)

        # 只显示20日周期的关键信息
        if 'period_analysis' in analysis and '20d' in analysis['period_analysis']:
            stats = analysis['period_analysis']['20d']
            print(f"\n     20日预测: 上涨概率 {stats['up_prob']:.1%}, 平均收益 {stats['mean_return']:+.2%}, 置信度 {stats.get('confidence', 0):.1%}")

            if 'position_advice' in stats:
                advice = stats['position_advice']
                print(f"     仓位建议: {advice['signal']} ({advice['recommended_position']:.1%})")

    # 综合评估
    if 'summary' in result:
        summary = result['summary']

        print_section("市场综合评估")
        print(f"\n  ✅ 成功分析: {summary['successful_analyses']}/{summary['total_indices']} 个指数")
        print(f"  📊 平均置信度: {summary['average_confidence']:.1%}")

        if summary['bullish_indices']:
            print(f"  📈 看涨指数: {', '.join(summary['bullish_indices'])}")

        if summary['bearish_indices']:
            print(f"  📉 看跌指数: {', '.join(summary['bearish_indices'])}")

        if summary['neutral_indices']:
            print(f"  ➡️  中性指数: {', '.join(summary['neutral_indices'])}")

        # 整体建议
        bull_count = len(summary['bullish_indices'])
        bear_count = len(summary['bearish_indices'])

        print(f"\n  🎯 整体市场观点:")
        if bull_count > bear_count and bull_count >= 3:
            print(f"     市场整体偏多,建议积极配置美股资产")
        elif bear_count > bull_count and bear_count >= 2:
            print(f"     市场整体偏空,建议谨慎控制仓位")
        else:
            print(f"     市场处于震荡状态,建议均衡配置")


def run_analysis(indices: list, tolerance: float, detail: bool, periods: list, use_phase2: bool = False, use_phase3: bool = False):
    """运行分析"""
    try:
        analyzer = USMarketAnalyzer()

        if len(indices) == 1:
            # 单指数详细分析
            result = analyzer.analyze_single_index(
                indices[0],
                tolerance=tolerance,
                periods=periods,
                use_phase2=use_phase2,
                use_phase3=use_phase3
            )
            print_single_index_analysis(result, detail=detail)
        else:
            # 多指数联合分析
            result = analyzer.analyze_multiple_indices(
                indices=indices,
                tolerance=tolerance,
                periods=periods,
                use_phase2=use_phase2,
                use_phase3=use_phase3
            )
            print_multi_index_analysis(result)

        print(f"\n{'=' * 80}\n")
        return True

    except Exception as e:
        logger.error(f"分析失败: {str(e)}", exc_info=True)
        print(f"\n  ❌ 分析失败: {str(e)}\n")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='美股市场历史点位对比分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 分析所有默认指数(标普500、纳斯达克、纳斯达克100、VIX) - Phase 1
  python run_us_analysis.py

  # 只分析标普500 - Phase 1
  python run_us_analysis.py --indices SPX

  # 使用Phase 2增强分析标普500(技术指标过滤+市场环境识别)
  python run_us_analysis.py --indices SPX --phase2 --detail

  # 使用Phase 3深度分析标普500(VIX+行业轮动+成交量)
  python run_us_analysis.py --indices SPX --phase3 --detail

  # 对比不同阶段的分析差异
  python run_us_analysis.py --indices SPX --detail          # Phase 1
  python run_us_analysis.py --indices SPX --detail --phase2 # Phase 2
  python run_us_analysis.py --indices SPX --detail --phase3 # Phase 3

  # 调整相似度容差为3%
  python run_us_analysis.py --tolerance 0.03

支持的指数代码:
  SPX     - 标普500
  NASDAQ  - 纳斯达克综合
  NDX     - 纳斯达克100
  VIX     - VIX恐慌指数
  DJI     - 道琼斯工业
  RUT     - 罗素2000
        '''
    )

    parser.add_argument(
        '--indices', '-i',
        nargs='+',
        default=None,
        choices=list(US_INDICES.keys()),
        help='要分析的指数代码(可多个)'
    )

    parser.add_argument(
        '--tolerance', '-t',
        type=float,
        default=0.05,
        help='相似度容差(默认0.05,即±5%%)'
    )

    parser.add_argument(
        '--periods', '-p',
        nargs='+',
        type=int,
        default=[5, 10, 20, 60],
        help='分析周期(天数,默认5 10 20 60)'
    )

    parser.add_argument(
        '--detail', '-d',
        action='store_true',
        help='显示详细分析结果'
    )

    parser.add_argument(
        '--phase2',
        action='store_true',
        help='使用Phase 2增强分析(技术指标过滤+市场环境识别)'
    )

    parser.add_argument(
        '--phase3',
        action='store_true',
        help='使用Phase 3深度分析(VIX恐慌指数+行业轮动+成交量分析)'
    )

    args = parser.parse_args()

    # 确定要分析的指数
    indices = args.indices if args.indices else DEFAULT_US_INDICES

    # 打印欢迎信息
    print_header("美股市场历史点位对比分析工具")
    print(f"\n  📅 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  📊 分析指数: {', '.join([US_INDICES[i].name for i in indices])}")
    print(f"  🎯 相似容差: ±{args.tolerance*100:.1f}%")
    print(f"  📈 分析周期: {', '.join([str(p)+'日' for p in args.periods])}")

    # 确定分析模式
    if args.phase3:
        print(f"  ⚙️  分析模式: Phase 3 (深度分析)")
    elif args.phase2:
        print(f"  ⚙️  分析模式: Phase 2 (技术指标增强)")
    else:
        print(f"  ⚙️  分析模式: Phase 1 (基础价格匹配)")

    # 运行分析
    success = run_analysis(
        indices=indices,
        tolerance=args.tolerance,
        detail=args.detail,
        periods=args.periods,
        use_phase2=args.phase2,
        use_phase3=args.phase3
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
