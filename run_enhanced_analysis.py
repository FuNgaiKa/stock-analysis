#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史点位对比分析 - 增强版主程序 (Phase 1.5)
新增：成交量匹配、市场情绪、量价背离等增强指标
"""

import sys
import os
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from position_analysis.historical_position_analyzer import (
    HistoricalPositionAnalyzer,
    ProbabilityAnalyzer,
    PositionManager,
    SUPPORTED_INDICES
)
from position_analysis.enhanced_data_provider import EnhancedDataProvider
from position_analysis.report_generator import TextReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(target_code: str = None):
    """增强版主函数

    Args:
        target_code: 指定要分析的标的代码（指数/ETF/个股），如不指定则使用默认
    """
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║       历史点位对比分析系统 - Phase 1.5 增强版                 ║
    ║         Enhanced Historical Position Analyzer                 ║
    ║                                                                ║
    ║  新增功能：                                                    ║
    ║  ✓ 成交量匹配分析                                             ║
    ║  ✓ 市场情绪指标                                               ║
    ║  ✓ 量价背离检测                                               ║
    ║  ✓ 分层概率统计（放量/缩量）                                  ║
    ║  ✓ 支持指数/ETF/个股分析                                      ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    # 初始化
    analyzer = HistoricalPositionAnalyzer()
    enhanced_provider = EnhancedDataProvider()
    prob_analyzer = ProbabilityAnalyzer()
    text_reporter = TextReportGenerator()

    # 获取当前点位
    logger.info("=" * 80)
    logger.info("步骤1: 获取当前市场点位...")
    logger.info("=" * 80)

    positions = analyzer.get_current_positions()
    if not positions:
        logger.error("无法获取当前点位数据")
        return 1

    # 选择主要分析标的（支持命令行参数或交互选择）
    if target_code and target_code in SUPPORTED_INDICES:
        main_index = target_code
    else:
        # 默认使用科创50，或者可以改成交互选择
        main_index = 'sh000688'  # 科创50

    if main_index not in positions:
        logger.error(f"无法获取 {main_index} 的数据，使用上证指数")
        main_index = 'sh000001'

    index_name = SUPPORTED_INDICES[main_index].name
    target_type = SUPPORTED_INDICES[main_index].type
    current_price = positions[main_index]['price']

    print(f"\n当前{index_name} ({target_type}): {current_price:.2f}")

    # 获取增强指标
    logger.info("\n" + "=" * 80)
    logger.info(f"步骤2: 获取{index_name}的增强指标...")
    logger.info("=" * 80)

    enhanced_metrics = enhanced_provider.get_comprehensive_metrics(main_index)

    volume_metrics = enhanced_metrics['volume_metrics']
    sentiment_metrics = enhanced_metrics['sentiment_metrics']
    divergence_metrics = enhanced_metrics['divergence_metrics']

    print(f"\n=== 当前市场状态 ===")
    print(f"成交量状态: {volume_metrics.get('volume_status', 'N/A')}")
    print(f"  当前成交量: {volume_metrics.get('current_volume', 0) / 1e8:.1f}亿")
    print(f"  量比: {volume_metrics.get('volume_ratio', 0):.2f}")
    print(f"  历史分位数: {volume_metrics.get('volume_percentile', 0):.1%}")

    print(f"\n市场情绪: {sentiment_metrics.get('sentiment_level', 'N/A')}")
    print(f"  涨停: {sentiment_metrics.get('limit_up_count', 0)}只")
    print(f"  跌停: {sentiment_metrics.get('limit_down_count', 0)}只")
    print(f"  情绪得分: {sentiment_metrics.get('sentiment_score', 0):.3f}")

    if divergence_metrics.get('has_divergence'):
        print(f"\n⚠️  检测到{divergence_metrics.get('divergence_type')}")
        print(f"  背离强度: {divergence_metrics.get('divergence_score', 0):.1%}")

    # 基础匹配 vs 增强匹配对比
    logger.info("\n" + "=" * 80)
    logger.info("步骤3: 历史点位匹配对比...")
    logger.info("=" * 80)

    # 基础匹配（仅价格）
    print(f"\n【基础匹配】仅价格相似（±5%）")
    similar_basic = analyzer.find_similar_periods(main_index, current_price, 0.05)
    future_returns_basic = analyzer.calculate_future_returns(main_index, similar_basic, [20])
    stats_basic = prob_analyzer.calculate_probability(future_returns_basic['return_20d'])

    print(f"  样本数: {len(similar_basic)}")
    print(f"  20日上涨概率: {stats_basic['up_prob']:.1%}")
    print(f"  平均收益: {stats_basic['mean_return']:+.2%}")

    # 增强匹配（价格+成交量）
    print(f"\n【增强匹配】价格+成交量双重过滤")
    current_volume = volume_metrics.get('current_volume')
    similar_enhanced = analyzer.find_similar_periods_enhanced(
        main_index,
        current_price,
        current_volume,
        price_tolerance=0.05,
        volume_tolerance=0.3,
        use_volume_filter=True
    )

    if len(similar_enhanced) > 0:
        future_returns_enhanced = analyzer.calculate_future_returns(
            main_index, similar_enhanced, [20]
        )
        stats_enhanced = prob_analyzer.calculate_probability(future_returns_enhanced['return_20d'])

        print(f"  样本数: {len(similar_enhanced)}")
        print(f"  20日上涨概率: {stats_enhanced['up_prob']:.1%}")
        print(f"  平均收益: {stats_enhanced['mean_return']:+.2%}")

        # 对比分析
        prob_diff = stats_enhanced['up_prob'] - stats_basic['up_prob']
        print(f"\n💡 增强匹配使概率调整: {prob_diff:+.1%}")
        if abs(prob_diff) > 0.1:
            direction = "更乐观" if prob_diff > 0 else "更谨慎"
            print(f"   结论: 加入成交量因子后，预测{direction}")
    else:
        print("  ⚠️ 增强匹配样本不足（<5个），建议降低容差或使用基础匹配")

    # 量价分层分析
    logger.info("\n" + "=" * 80)
    logger.info("步骤4: 量价配合分层分析...")
    logger.info("=" * 80)

    print(f"\n【分层概率统计】")

    # 计算历史各时期的量比
    df = analyzer.get_index_data(main_index)
    df['volume_ma20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma20']

    # 放量时期
    similar_high_vol = similar_basic[
        similar_basic.index.isin(
            df[df['volume_ratio'] > 1.5].index
        )
    ]
    if len(similar_high_vol) >= 5:
        returns_high_vol = analyzer.calculate_future_returns(
            main_index, similar_high_vol, [20]
        )
        stats_high_vol = prob_analyzer.calculate_probability(returns_high_vol['return_20d'])
        print(f"\n放量突破（量比>1.5）:")
        print(f"  样本数: {len(similar_high_vol)}")
        print(f"  20日上涨概率: {stats_high_vol['up_prob']:.1%}")
        print(f"  平均收益: {stats_high_vol['mean_return']:+.2%}")

    # 缩量时期
    similar_low_vol = similar_basic[
        similar_basic.index.isin(
            df[df['volume_ratio'] < 0.8].index
        )
    ]
    if len(similar_low_vol) >= 5:
        returns_low_vol = analyzer.calculate_future_returns(
            main_index, similar_low_vol, [20]
        )
        stats_low_vol = prob_analyzer.calculate_probability(returns_low_vol['return_20d'])
        print(f"\n缩量上涨（量比<0.8）:")
        print(f"  样本数: {len(similar_low_vol)}")
        print(f"  20日上涨概率: {stats_low_vol['up_prob']:.1%}")
        print(f"  平均收益: {stats_low_vol['mean_return']:+.2%}")

    # 综合建议
    logger.info("\n" + "=" * 80)
    logger.info("步骤5: 生成综合建议...")
    logger.info("=" * 80)

    # 使用增强匹配的结果（如果可用）
    if len(similar_enhanced) >= 10:
        final_up_prob = stats_enhanced['up_prob']
        final_mean_return = stats_enhanced['mean_return']
        match_type = "增强匹配"
    else:
        final_up_prob = stats_basic['up_prob']
        final_mean_return = stats_basic['mean_return']
        match_type = "基础匹配"

    # 情绪调整
    sentiment_score = sentiment_metrics.get('sentiment_score', 0)
    if sentiment_score > 0.02:  # 情绪高涨
        sentiment_adj = 0.05
    elif sentiment_score < -0.02:  # 情绪低迷
        sentiment_adj = -0.05
    else:
        sentiment_adj = 0

    adjusted_prob = min(0.95, max(0.05, final_up_prob + sentiment_adj))

    print(f"\n=== 综合结论 ===")
    print(f"匹配方式: {match_type}")
    print(f"基础概率: {final_up_prob:.1%}")
    if sentiment_adj != 0:
        print(f"情绪调整: {sentiment_adj:+.1%}")
        print(f"调整后概率: {adjusted_prob:.1%}")

    # 仓位建议
    position_mgr = PositionManager()
    advice = position_mgr.calculate_position_advice(
        adjusted_prob,
        0.75,  # 置信度
        final_mean_return,
        0.05
    )

    print(f"\n交易信号: {advice['signal']}")
    print(f"建议仓位: {advice['recommended_position']*100:.0f}%")
    print(f"策略说明: {advice['description']}")

    # 风险提示
    print(f"\n⚠️  风险提示:")
    if volume_metrics.get('volume_status') == '严重缩量':
        print("  - 当前成交量严重萎缩，警惕虚假突破")
    if divergence_metrics.get('divergence_type') == '顶背离':
        print("  - 检测到量价顶背离，注意回调风险")
    if sentiment_metrics.get('limit_up_count', 0) > 100:
        print("  - 涨停潮出现，市场情绪过热，警惕回调")

    logger.info("\n" + "=" * 80)
    logger.info("分析完成!")
    logger.info("=" * 80)

    return 0


if __name__ == '__main__':
    # 支持命令行参数指定标的
    import argparse
    parser = argparse.ArgumentParser(description='历史点位对比分析')
    parser.add_argument('--code', '-c', type=str, help='标的代码（指数/ETF/个股）',
                        choices=list(SUPPORTED_INDICES.keys()))
    parser.add_argument('--list', '-l', action='store_true', help='列出所有支持的标的')

    args = parser.parse_args()

    if args.list:
        print("\n支持的标的列表：")
        print("=" * 70)
        print(f"{'代码':<12} {'名称':<15} {'类型':<10}")
        print("-" * 70)
        for code, config in SUPPORTED_INDICES.items():
            type_name = {'index': '指数', 'etf': 'ETF', 'stock': '个股'}.get(config.type, config.type)
            print(f"{code:<12} {config.name:<15} {type_name:<10}")
        print("=" * 70)
        sys.exit(0)

    sys.exit(main(target_code=args.code))
