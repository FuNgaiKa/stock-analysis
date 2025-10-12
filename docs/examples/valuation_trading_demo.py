#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实战演示：基于估值分析的量化交易决策

场景：
假设今天是2025-10-10，你有100万资金，想投资上证指数ETF（如510300）
问题：
1. 现在市场贵不贵？该不该买？
2. 如果买，应该买多少仓位？
3. 预期未来20天/60天的收益如何？
4. 止损止盈位应该设在哪里？
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入模块，避免__init__.py中的plotly依赖
import importlib.util

# 手动加载模块
def load_module(module_path):
    spec = importlib.util.spec_from_file_location("temp_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

val_module = load_module(os.path.join(base_path, 'position_analysis', 'valuation_analyzer.py'))
ValuationAnalyzer = val_module.ValuationAnalyzer

data_module = load_module(os.path.join(base_path, 'position_analysis', 'enhanced_data_provider.py'))
EnhancedDataProvider = data_module.EnhancedDataProvider

hist_module = load_module(os.path.join(base_path, 'position_analysis', 'historical_position_analyzer.py'))
HistoricalPositionAnalyzer = hist_module.HistoricalPositionAnalyzer
ProbabilityAnalyzer = hist_module.ProbabilityAnalyzer
PositionManager = hist_module.PositionManager


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def step1_check_valuation():
    """步骤1：检查当前估值水平"""
    print_section("步骤1：检查当前估值水平（回答：现在贵不贵？）")

    val_analyzer = ValuationAnalyzer()

    # 1.1 全市场估值
    print("\n[1.1] 全市场估值（A股整体）")
    market_val = val_analyzer.get_market_valuation_comprehensive()

    print(f"  PE TTM: {market_val['pe_ttm']:.2f}")
    print(f"  PE近10年分位数: {market_val['pe_percentile_10y']:.1%}")
    print(f"  PB: {market_val['pb']:.2f}")
    print(f"  PB近10年分位数: {market_val['pb_percentile_10y']:.1%}")
    print(f"  估值水平: {market_val['valuation_level']}")

    # 判断
    if market_val['is_overvalued']:
        print(f"\n  [!] 结论: 市场目前处于高估区域！")
        print(f"      PE分位数{market_val['pe_percentile_10y']:.1%} > 70%，建议谨慎")
        valuation_signal = "高估-谨慎"
    elif market_val['is_undervalued']:
        print(f"\n  [OK] 结论: 市场目前处于低估区域！")
        print(f"       PE分位数{market_val['pe_percentile_10y']:.1%} < 30%，可以考虑建仓")
        valuation_signal = "低估-机会"
    else:
        print(f"\n  [INFO] 结论: 市场估值合理")
        print(f"         PE分位数{market_val['pe_percentile_10y']:.1%}在30%-70%区间")
        valuation_signal = "合理-观望"

    # 1.2 上证指数估值
    print("\n[1.2] 上证指数估值")
    index_val = val_analyzer.get_current_index_valuation("上证")

    print(f"  当前点位: {index_val.get('data_date', 'N/A')}")
    print(f"  当前PE: {index_val['current_pe']:.2f}")
    print(f"  PE近10年分位数: {index_val['pe_percentile_10y']:.1%}")
    print(f"  估值水平: {index_val['valuation_level']}")

    # 1.3 与历史关键时点对比
    print("\n[1.3] 与历史重要时点对比")
    comparison = val_analyzer.compare_valuation_with_history()

    # 显示关键时点
    print("\n  时间          点位      PE    PE分位数  估值水平")
    print("  " + "-" * 60)
    for _, row in comparison.head(5).iterrows():
        period = row['period'].ljust(12)
        index_val_str = f"{row['index_value']:.2f}".rjust(8)
        pe = f"{row['pe']:.2f}".rjust(6)
        pct = f"{row['pe_percentile']:.1%}".rjust(8)
        level = row['valuation_level']
        print(f"  {period} {index_val_str}  {pe}  {pct}  {level}")

    return {
        'market_val': market_val,
        'index_val': index_val,
        'valuation_signal': valuation_signal
    }


def step2_find_similar_periods(valuation_signal):
    """步骤2：找到历史相似时期（加入估值过滤）"""
    print_section("步骤2：找历史相似时期（价格+成交量+估值三重过滤）")

    pos_analyzer = HistoricalPositionAnalyzer()
    data_provider = EnhancedDataProvider()

    # 2.1 获取当前市场指标
    print("\n[2.1] 获取当前市场综合指标...")
    current_metrics = data_provider.get_comprehensive_metrics('sh000001')

    # 关键：传入data_provider，启用估值过滤
    current_metrics['enhanced_data_provider'] = data_provider

    print(f"  [OK]成交量状态: {current_metrics['volume_metrics'].get('volume_status', 'N/A')}")
    print(f"  [OK]市场情绪: {current_metrics['sentiment_metrics'].get('sentiment_level', 'N/A')}")
    print(f"  [OK]估值水平: {current_metrics['valuation_metrics'].get('valuation_level', 'N/A')}")

    # 2.2 多维度匹配（价格+成交量+估值）
    print("\n[2.2] 执行多维度历史匹配...")

    similar = pos_analyzer.find_similar_periods_multidim(
        index_code='sh000001',
        current_metrics=current_metrics,
        price_tolerance=0.05,         # 价格±5%
        volume_tolerance=0.3,          # 成交量±30%
        use_valuation_filter=True,     # 启用估值过滤！
        use_capital_flow_filter=False  # 资金流向暂不启用
    )

    if len(similar) == 0:
        print("\n  [WARN]未找到符合条件的历史时期（可能估值过滤太严格）")
        return None

    print(f"\n  [OK]找到 {len(similar)} 个真正相似的历史时期")
    print(f"    （这些时期不仅点位相似，估值水平也相似）")

    # 显示部分匹配的日期
    print("\n  示例匹配日期:")
    for i, date in enumerate(similar.index[:5]):
        print(f"    - {date.strftime('%Y-%m-%d')}: 收盘{similar.loc[date, 'close']:.2f}")

    return {
        'similar_periods': similar,
        'pos_analyzer': pos_analyzer
    }


def step3_calculate_probability(similar_data):
    """步骤3：计算未来收益概率"""
    print_section("步骤3：基于历史相似时期，预测未来收益")

    if similar_data is None:
        print("\n  [WARN]跳过（无相似时期）")
        return None

    similar = similar_data['similar_periods']
    pos_analyzer = similar_data['pos_analyzer']

    # 3.1 计算未来收益率
    print("\n[3.1] 计算这些相似时期的后续表现...")
    future_returns = pos_analyzer.calculate_future_returns(
        'sh000001',
        similar,
        periods=[5, 10, 20, 60]
    )

    print(f"  [OK]成功计算 {len(future_returns)} 个样本的后续收益")

    # 3.2 统计分析
    print("\n[3.2] 统计分析结果:")
    prob_analyzer = ProbabilityAnalyzer()

    periods_to_analyze = [
        (5, "5日后（1周）"),
        (20, "20日后（1月）"),
        (60, "60日后（3月）")
    ]

    results = {}

    for period, desc in periods_to_analyze:
        stats = prob_analyzer.calculate_probability(future_returns[f'return_{period}d'])
        results[period] = stats

        print(f"\n  {desc}:")
        print(f"    样本数: {stats['sample_size']}")
        print(f"    上涨概率: {stats['up_prob']:.1%}  (上涨{stats['up_count']}次)")
        print(f"    下跌概率: {stats['down_prob']:.1%}  (下跌{stats['down_count']}次)")
        print(f"    平均收益率: {stats['mean_return']:.2%}")
        print(f"    中位数收益率: {stats['median_return']:.2%}")
        print(f"    最大涨幅: {stats['max_return']:.2%}")
        print(f"    最大跌幅: {stats['min_return']:.2%}")

        # 置信度
        confidence = prob_analyzer.calculate_confidence(
            stats['sample_size'],
            max(stats['up_prob'], stats['down_prob'])
        )
        print(f"    置信度: {confidence:.1%}")

        # 判断
        if stats['up_prob'] > 0.65 and confidence > 0.7:
            signal = "[UP] 大概率上涨"
        elif stats['down_prob'] > 0.65 and confidence > 0.7:
            signal = "[DOWN] 大概率下跌"
        else:
            signal = "[NEUTRAL] 方向不明确"

        print(f"    信号: {signal}")

    return results


def step4_position_recommendation(probability_results, valuation_signal):
    """步骤4：仓位建议和风险管理"""
    print_section("步骤4：给出具体交易建议（仓位+止损止盈）")

    if probability_results is None:
        print("\n  [WARN]跳过（无概率数据）")
        return

    # 4.1 基于20日概率计算仓位
    print("\n[4.1] 仓位建议（基于20日预期）")

    stats_20d = probability_results[20]

    position_manager = PositionManager()
    position_advice = position_manager.calculate_position_advice(
        up_prob=stats_20d['up_prob'],
        confidence=0.75,  # 简化，实际应动态计算
        mean_return=stats_20d['mean_return'],
        std=stats_20d['std']
    )

    print(f"  信号: {position_advice['signal']}")
    print(f"  建议仓位: {position_advice['recommended_position']*100:.0f}%")
    print(f"  说明: {position_advice['description']}")

    # 4.2 结合估值调整仓位
    print("\n[4.2] 估值修正后的最终仓位")

    base_position = position_advice['recommended_position']

    if valuation_signal == "高估-谨慎":
        final_position = base_position * 0.6  # 高估时降低仓位
        print(f"  当前估值偏高，仓位下调至: {final_position*100:.0f}%")
        print(f"  理由: 估值处于高位，即使概率看好，也要控制风险")
    elif valuation_signal == "低估-机会":
        final_position = min(0.9, base_position * 1.2)  # 低估时提高仓位
        print(f"  当前估值偏低，仓位上调至: {final_position*100:.0f}%")
        print(f"  理由: 估值安全垫较厚，可以适当加大仓位")
    else:
        final_position = base_position
        print(f"  估值合理，维持建议仓位: {final_position*100:.0f}%")

    # 4.3 止损止盈位
    print("\n[4.3] 风险管理：止损止盈位")

    current_price = 3900  # 假设当前点位

    stop_loss_take_profit = position_manager.calculate_stop_loss_take_profit(
        current_price=current_price,
        max_loss_percentile=stats_20d['percentile_25'],  # 25%分位数作为止损
        avg_gain_percentile=stats_20d['percentile_75']   # 75%分位数作为止盈
    )

    print(f"  止损位: {stop_loss_take_profit['stop_loss_price']:.0f} ({stop_loss_take_profit['stop_loss_pct']:.1%})")
    print(f"  止盈位: {stop_loss_take_profit['take_profit_price']:.0f} ({stop_loss_take_profit['take_profit_pct']:.1%})")
    print(f"  盈亏比: {stop_loss_take_profit['risk_reward_ratio']:.2f}")

    # 4.4 实际交易计划
    print("\n[4.4] 具体交易计划（假设100万资金）")

    capital = 1_000_000
    invest_amount = capital * final_position

    print(f"\n  总资金: {capital:,.0f} 元")
    print(f"  建议投资: {invest_amount:,.0f} 元 ({final_position*100:.0f}%)")
    print(f"  保留现金: {capital - invest_amount:,.0f} 元")

    print(f"\n  买入价格: {current_price:.0f} 点附近")
    print(f"  止损价格: {stop_loss_take_profit['stop_loss_price']:.0f} 点")
    print(f"  止盈价格: {stop_loss_take_profit['take_profit_price']:.0f} 点")

    # 预期收益
    expected_profit = invest_amount * stats_20d['mean_return']
    max_profit = invest_amount * stats_20d['percentile_75']
    max_loss = invest_amount * stats_20d['percentile_25']

    print(f"\n  预期收益（20日）: {expected_profit:,.0f} 元 ({stats_20d['mean_return']:.1%})")
    print(f"  最佳情况: +{max_profit:,.0f} 元")
    print(f"  最差情况: {max_loss:,.0f} 元")

    # 4.5 风险提示
    print("\n[4.5] 风险提示")
    print(f"  • 历史相似不代表未来相同，请谨慎决策")
    print(f"  • 当前估值水平: {valuation_signal}")
    print(f"  • 建议分批建仓，不要一次性买入")
    print(f"  • 严格执行止损，保护本金")


def step5_summary():
    """步骤5：决策总结"""
    print_section("步骤5：决策总结")

    print("""
  综合分析流程:

  1. ✓ 估值检查 → 判断市场是否高估/低估
  2. ✓ 历史匹配 → 找到估值+点位+成交量都相似的时期
  3. ✓ 概率分析 → 统计这些相似时期的后续表现
  4. ✓ 仓位管理 → 基于概率+估值给出具体建议
  5. ✓ 风险管理 → 设置止损止盈位

  核心优势:

  • 不是盲目根据"点位"判断，而是加入"估值"维度
  • 3000点在估值30%和70%分位时，结果完全不同
  • 历史匹配更精准，预测更可靠

  投资建议:

  • 低估值（PE<30%） + 上涨概率>65% → 重仓买入
  • 高估值（PE>70%） + 下跌概率>65% → 清仓观望
  • 估值合理 + 方向不明 → 半仓持有，等待明确信号
    """)


def main():
    """主函数：完整交易决策流程"""

    print("\n" + "=" * 80)
    print("  基于估值分析的量化交易决策系统")
    print("  实战演示：如何用估值功能做交易决策")
    print("=" * 80)

    try:
        # 步骤1：检查估值
        valuation_data = step1_check_valuation()

        # 步骤2：找相似时期
        similar_data = step2_find_similar_periods(valuation_data['valuation_signal'])

        # 步骤3：计算概率
        probability_results = step3_calculate_probability(similar_data)

        # 步骤4：仓位建议
        step4_position_recommendation(probability_results, valuation_data['valuation_signal'])

        # 步骤5：总结
        step5_summary()

        print("\n" + "=" * 80)
        print("  分析完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR]错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
