#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用示例 - 历史点位对比分析系统
"""

from strategies.position import PositionAnalysisEngine

# ============================================================
# 示例1: 快速分析（默认参数）
# ============================================================
def example_quick_analysis():
    """快速分析示例"""
    print("=== 示例1: 快速分析 ===\n")

    engine = PositionAnalysisEngine()
    results = engine.run_full_analysis()

    print("\n✓ 分析完成！")
    print(f"分析了 {len(results['positions'])} 个指数")
    print(f"生成的报告保存在 reports/ 目录")


# ============================================================
# 示例2: 自定义指数和参数
# ============================================================
def example_custom_analysis():
    """自定义分析示例"""
    print("\n=== 示例2: 自定义分析 ===\n")

    # 只分析上证指数和沪深300
    engine = PositionAnalysisEngine(
        indices=['sh000001', 'sh000300']
    )

    results = engine.run_full_analysis(
        tolerance=0.03,           # 收紧到±3%
        periods=[10, 20, 60],     # 只看10/20/60日
        output_html=True,
        output_dir='my_reports'
    )

    print("\n✓ 自定义分析完成！")


# ============================================================
# 示例3: 单指数深度分析
# ============================================================
def example_single_index():
    """单指数深度分析"""
    print("\n=== 示例3: 单指数深度分析 ===\n")

    from strategies.position import HistoricalPositionAnalyzer, ProbabilityAnalyzer

    analyzer = HistoricalPositionAnalyzer()
    prob_analyzer = ProbabilityAnalyzer()

    # 获取上证指数当前点位
    positions = analyzer.get_current_positions()
    sh_price = positions['sh000001']['price']

    print(f"上证指数当前点位: {sh_price:.2f}")

    # 查找历史相似点位
    similar = analyzer.find_similar_periods('sh000001', sh_price, tolerance=0.05)
    print(f"找到 {len(similar)} 个历史相似点位")

    # 计算未来收益率
    future_returns = analyzer.calculate_future_returns('sh000001', similar, periods=[20])
    print(f"未来20日收益率样本数: {len(future_returns)}")

    # 概率统计
    stats = prob_analyzer.calculate_probability(future_returns['return_20d'])
    print(f"\n未来20日统计:")
    print(f"  上涨概率: {stats['up_prob']:.1%}")
    print(f"  平均收益: {stats['mean_return']:+.2%}")
    print(f"  收益中位数: {stats['median_return']:+.2%}")
    print(f"  样本量: {stats['sample_size']}")


# ============================================================
# 示例4: 仓位管理计算
# ============================================================
def example_position_management():
    """仓位管理示例"""
    print("\n=== 示例4: 仓位管理计算 ===\n")

    from strategies.position import PositionManager

    manager = PositionManager()

    # 假设统计结果：上涨概率65%，置信度75%
    advice = manager.calculate_position_advice(
        up_prob=0.65,
        confidence=0.75,
        mean_return=0.03,  # 3%平均收益
        std=0.05           # 5%标准差
    )

    print(f"交易信号: {advice['signal']}")
    print(f"建议仓位: {advice['recommended_position']*100:.0f}%")
    print(f"说明: {advice['description']}")

    # 止损止盈计算
    current_price = 3882.78
    stop_loss_info = manager.calculate_stop_loss_take_profit(
        current_price=current_price,
        max_loss_percentile=-0.05,  # 历史最大回撤5%
        avg_gain_percentile=0.08     # 历史平均盈利8%
    )

    print(f"\n止损止盈建议:")
    print(f"  止损位: {stop_loss_info['stop_loss_price']:.2f} ({stop_loss_info['stop_loss_pct']:+.1%})")
    print(f"  止盈位: {stop_loss_info['take_profit_price']:.2f} ({stop_loss_info['take_profit_pct']:+.1%})")
    print(f"  盈亏比: {stop_loss_info['risk_reward_ratio']:.2f}")


# ============================================================
# 示例5: 访问详细结果数据
# ============================================================
def example_access_results():
    """访问详细结果数据"""
    print("\n=== 示例5: 访问详细结果 ===\n")

    engine = PositionAnalysisEngine(indices=['sh000001'])

    results = engine.run_full_analysis(
        tolerance=0.05,
        periods=[20],
        output_html=False  # 不生成HTML
    )

    # 访问各部分数据
    positions = results['positions']
    single_results = results['single_index_results']
    conclusion = results['conclusion']

    print("当前点位:")
    for code, info in positions.items():
        print(f"  {info['name']}: {info['price']:.2f}")

    print("\n单指数分析结果:")
    for code, result in single_results.items():
        if 'prob_stats' in result:
            stats_20d = result['prob_stats'].get('period_20d', {})
            print(f"  {positions[code]['name']}:")
            print(f"    样本数: {result['similar_count']}")
            print(f"    20日上涨概率: {stats_20d.get('up_prob', 0):.1%}")
            print(f"    年份分布: {result.get('year_distribution', {})}")

    print(f"\n综合结论:")
    print(f"  方向: {conclusion['direction']}")
    print(f"  置信度: {conclusion['confidence']:.0%}")
    print(f"  建议仓位: {conclusion['position_advice']['recommended_position']*100:.0f}%")


if __name__ == '__main__':
    # 运行所有示例
    examples = [
        # example_quick_analysis,           # 完整分析，较慢
        example_custom_analysis,
        example_single_index,
        example_position_management,
        example_access_results,
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{'='*60}")
        example()
        print(f"{'='*60}")

    print("\n所有示例运行完成！")
