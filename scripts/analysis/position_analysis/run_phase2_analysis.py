#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 九维度市场分析 - Demo脚本
展示完整的9维度指标分析和多维度匹配

Usage:
    python run_phase2_analysis.py
    python run_phase2_analysis.py --index sh000001
    python run_phase2_analysis.py --index sz399006 --detail
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from strategies.position.core.enhanced_data_provider import EnhancedDataProvider
from strategies.position.core.historical_position_analyzer import (
    HistoricalPositionAnalyzer,
    ProbabilityAnalyzer,
    PositionManager,
    SUPPORTED_INDICES
)


def print_section_header(title: str, char: str = "="):
    """打印章节标题"""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")


def print_metric(label: str, value: str, indent: int = 2):
    """打印指标"""
    print(f"{' ' * indent}{label}: {value}")


def analyze_nine_dimensions(index_code: str = 'sh000001', show_detail: bool = False):
    """
    执行九维度分析

    Args:
        index_code: 指数代码
        show_detail: 是否显示详细信息
    """
    print_section_header(f"Phase 2 九维度市场分析 - {SUPPORTED_INDICES[index_code].name}")

    # 初始化
    provider = EnhancedDataProvider()
    analyzer = HistoricalPositionAnalyzer()
    prob_analyzer = ProbabilityAnalyzer()
    position_manager = PositionManager()

    # 获取当前点位
    positions = analyzer.get_current_positions()
    if index_code not in positions:
        print(f"❌ 无法获取 {index_code} 数据")
        return

    current_price = positions[index_code]['price']
    current_date = positions[index_code]['date']

    print(f"📅 分析日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 当前点位: {SUPPORTED_INDICES[index_code].name} {current_price:.2f} ({current_date})")

    # ========== 1. 获取九维度指标 ==========
    print_section_header("一、九维度市场扫描", "-")

    print("⏳ 正在获取市场数据...\n")
    metrics = provider.get_comprehensive_metrics(index_code)

    # 1. 估值维度
    print("【维度1: 估值】")
    val_metrics = metrics.get('valuation_metrics', {})
    if val_metrics:
        pe_pct = val_metrics.get('pe_percentile_10y', 0) * 100
        pb_pct = val_metrics.get('pb_percentile_10y', 0) * 100
        val_level = val_metrics.get('valuation_level', 'N/A')

        # 判断信号
        avg_pct = (pe_pct + pb_pct) / 2
        if avg_pct < 30:
            signal = "✅ 买入区域"
        elif avg_pct < 50:
            signal = "🟢 可配置区域"
        elif avg_pct < 70:
            signal = "🟡 中性区域"
        else:
            signal = "⚠️  高估区域"

        print_metric(f"PE分位(10年)", f"{pe_pct:.1f}%")
        print_metric(f"PB分位(10年)", f"{pb_pct:.1f}%")
        print_metric(f"估值水平", f"{val_level} → {signal}")
    else:
        print_metric("状态", "数据获取失败")

    # 2. 资金维度
    print("\n【维度2: 北向资金】")
    cap_metrics = metrics.get('capital_flow_metrics', {})
    if cap_metrics:
        today_flow = cap_metrics.get('today_net_inflow', 0)
        flow_5d = cap_metrics.get('cumulative_5d', 0)
        flow_status = cap_metrics.get('flow_status', 'N/A')

        # 判断信号
        if flow_5d > 200:
            signal = "✅ 大幅流入"
        elif flow_5d > 50:
            signal = "🟢 持续流入"
        elif flow_5d > -50:
            signal = "🟡 中性"
        else:
            signal = "⚠️  持续流出"

        print_metric(f"当日净流入", f"{today_flow:.1f}亿")
        print_metric(f"5日累计", f"{flow_5d:.1f}亿")
        print_metric(f"资金状态", f"{flow_status} → {signal}")
    else:
        print_metric("状态", "数据获取失败")

    # 3. 情绪维度
    print("\n【维度3: 市场情绪】")
    sent_metrics = metrics.get('sentiment_metrics', {})
    if sent_metrics:
        limit_up = sent_metrics.get('limit_up_count', 0)
        limit_down = sent_metrics.get('limit_down_count', 0)
        sent_level = sent_metrics.get('sentiment_level', 'N/A')

        # 判断信号
        if limit_up > 100:
            signal = "⚠️  过度狂热"
        elif limit_up > 50:
            signal = "🟡 情绪高涨"
        elif limit_down > 50:
            signal = "✅ 恐慌杀跌"
        else:
            signal = "🟢 情绪平稳"

        print_metric(f"涨停数", f"{limit_up}只")
        print_metric(f"跌停数", f"{limit_down}只")
        print_metric(f"情绪水平", f"{sent_level} → {signal}")
    else:
        print_metric("状态", "数据获取失败")

    # 4. 市场宽度
    print("\n【维度4: 市场宽度】")
    breadth_metrics = metrics.get('market_breadth_metrics', {})
    if breadth_metrics:
        up_count = breadth_metrics.get('up_count', 0)
        up_ratio = breadth_metrics.get('up_ratio', 0) * 100
        breadth_level = breadth_metrics.get('breadth_level', 'N/A')

        # 判断信号
        if up_ratio > 70:
            signal = "✅ 普涨行情"
        elif up_ratio > 50:
            signal = "🟢 多数上涨"
        elif up_ratio > 30:
            signal = "🟡 涨跌平衡"
        else:
            signal = "⚠️  普跌行情"

        print_metric(f"上涨家数", f"{up_count}只 ({up_ratio:.1f}%)")
        print_metric(f"市场宽度", f"{breadth_level} → {signal}")
    else:
        print_metric("状态", "数据获取失败")

    # 5. 技术指标
    print("\n【维度5: 技术指标】")
    tech_metrics = metrics.get('technical_indicators', {})
    if tech_metrics:
        macd = tech_metrics.get('macd', 0)
        macd_signal = tech_metrics.get('macd_signal', 'N/A')
        rsi = tech_metrics.get('rsi', 50)
        rsi_signal = tech_metrics.get('rsi_signal', 'N/A')

        # 判断信号
        if macd_signal == '金叉' and rsi < 50:
            signal = "✅ 底部金叉"
        elif macd_signal == '金叉':
            signal = "🟢 多头趋势"
        elif macd_signal == '死叉':
            signal = "⚠️  空头趋势"
        else:
            signal = "🟡 震荡整理"

        print_metric(f"MACD", f"{macd:.2f} ({macd_signal})")
        print_metric(f"RSI", f"{rsi:.1f} ({rsi_signal})")
        print_metric(f"技术信号", signal)
    else:
        print_metric("状态", "数据获取失败")

    # 6. 波动率
    print("\n【维度6: 波动率】")
    vol_metrics = metrics.get('volatility_metrics', {})
    if vol_metrics:
        current_vol = vol_metrics.get('current_volatility', 0) * 100
        vol_pct = vol_metrics.get('volatility_percentile', 0) * 100
        vol_level = vol_metrics.get('volatility_level', 'N/A')

        # 判断信号
        if vol_pct < 20:
            signal = "🟢 低波动 (适合持仓)"
        elif vol_pct < 60:
            signal = "🟡 正常波动"
        else:
            signal = "⚠️  高波动 (谨慎)"

        print_metric(f"当前波动率", f"{current_vol:.2f}% (年化)")
        print_metric(f"波动率分位", f"{vol_pct:.1f}%")
        print_metric(f"波动水平", f"{vol_level} → {signal}")
    else:
        print_metric("状态", "数据获取失败")

    # 7. 成交量
    print("\n【维度7: 成交量】")
    volume_metrics = metrics.get('volume_metrics', {})
    if volume_metrics:
        volume_ratio = volume_metrics.get('volume_ratio', 1)
        volume_status = volume_metrics.get('volume_status', 'N/A')

        # 判断信号
        if volume_ratio > 2:
            signal = "✅ 放量突破"
        elif volume_ratio > 1.5:
            signal = "🟢 温和放量"
        elif volume_ratio < 0.8:
            signal = "⚠️  缩量"
        else:
            signal = "🟡 正常水平"

        print_metric(f"量比", f"{volume_ratio:.2f}")
        print_metric(f"成交量状态", f"{volume_status} → {signal}")
    else:
        print_metric("状态", "数据获取失败")

    # 8. 量价背离
    print("\n【维度8: 量价关系】")
    div_metrics = metrics.get('divergence_metrics', {})
    if div_metrics:
        has_div = div_metrics.get('has_divergence', False)
        div_type = div_metrics.get('divergence_type', None)

        if has_div and div_type == '顶背离':
            signal = "⚠️  顶背离 (见顶信号)"
        elif has_div and div_type == '底背离':
            signal = "✅ 底背离 (见底信号)"
        else:
            signal = "🟢 量价配合"

        print_metric(f"背离检测", signal)
    else:
        print_metric("状态", "数据获取失败")

    # 9. 宏观环境
    print("\n【维度9: 宏观环境】")
    macro_metrics = metrics.get('macro_metrics', {})
    if macro_metrics:
        bond_yield = macro_metrics.get('bond_yield_10y', 0)

        # 判断信号
        if bond_yield < 2.0:
            signal = "✅ 低利率 (利好股市)"
        elif bond_yield < 3.0:
            signal = "🟢 中性利率"
        else:
            signal = "⚠️  高利率 (利空股市)"

        print_metric(f"10年期国债", f"{bond_yield:.2f}% → {signal}")
    else:
        print_metric("状态", "数据获取失败")

    # ========== 2. 综合诊断 ==========
    print_section_header("二、综合市场诊断", "-")

    # 计算信号得分
    signals = []

    # 估值 (40%权重)
    if val_metrics:
        avg_pct = (val_metrics.get('pe_percentile_10y', 0.5) + val_metrics.get('pb_percentile_10y', 0.5)) / 2
        if avg_pct < 0.3:
            signals.append(('估值', 1.0, 0.4))
        elif avg_pct < 0.5:
            signals.append(('估值', 0.7, 0.4))
        elif avg_pct < 0.7:
            signals.append(('估值', 0.3, 0.4))
        else:
            signals.append(('估值', -0.3, 0.4))

    # 资金 (20%权重)
    if cap_metrics:
        flow_5d = cap_metrics.get('cumulative_5d', 0)
        if flow_5d > 200:
            signals.append(('资金', 1.0, 0.2))
        elif flow_5d > 50:
            signals.append(('资金', 0.7, 0.2))
        elif flow_5d > -50:
            signals.append(('资金', 0.0, 0.2))
        else:
            signals.append(('资金', -0.5, 0.2))

    # 情绪 (15%权重) - 反向指标
    if sent_metrics:
        limit_up = sent_metrics.get('limit_up_count', 0)
        if limit_up > 100:
            signals.append(('情绪', -0.5, 0.15))  # 过热反而不好
        elif limit_up < 20:
            signals.append(('情绪', 0.8, 0.15))  # 冷清是机会
        else:
            signals.append(('情绪', 0.3, 0.15))

    # 其他维度(合计25%权重)
    if tech_metrics and tech_metrics.get('macd_signal') == '金叉':
        signals.append(('技术', 0.6, 0.1))
    elif tech_metrics and tech_metrics.get('macd_signal') == '死叉':
        signals.append(('技术', -0.4, 0.1))

    if vol_metrics and vol_metrics.get('volatility_percentile', 0.5) < 0.3:
        signals.append(('波动', 0.5, 0.05))

    # 计算综合得分 (-1 到 +1)
    if signals:
        weighted_score = sum(score * weight for _, score, weight in signals)
        total_weight = sum(weight for _, _, weight in signals)
        final_score = weighted_score / total_weight if total_weight > 0 else 0
    else:
        final_score = 0

    print("📊 信号汇总:\n")
    for name, score, weight in signals:
        emoji = "✅" if score > 0.5 else "⚠️ " if score < 0 else "🟡"
        print(f"  {emoji} {name}: {score:+.1f} (权重{weight:.0%})")

    print(f"\n🎯 综合评分: {final_score:+.2f} / 1.00")

    # 给出建议
    if final_score > 0.5:
        suggestion = "✅ 强烈买入信号"
        position_advice = "建议仓位: 70-80%"
    elif final_score > 0.2:
        suggestion = "🟢 买入信号"
        position_advice = "建议仓位: 60-70%"
    elif final_score > -0.2:
        suggestion = "🟡 中性观望"
        position_advice = "建议仓位: 40-50%"
    elif final_score > -0.5:
        suggestion = "⚠️  卖出信号"
        position_advice = "建议仓位: 30-40%"
    else:
        suggestion = "🔴 强烈卖出信号"
        position_advice = "建议仓位: 20-30%"

    print(f"\n{suggestion}")
    print(f"{position_advice}")

    # ========== 3. 多维度历史匹配 (如果需要详细分析) ==========
    if show_detail:
        print_section_header("三、多维度历史匹配分析", "-")

        print("⏳ 正在进行多维度历史匹配...\n")

        try:
            # 使用新的多维度匹配算法
            similar = analyzer.find_similar_periods_multidim(
                index_code,
                current_price,
                current_metrics=metrics,
                price_tolerance=0.05,
                volume_tolerance=0.3,
                use_valuation_filter=False,  # 暂时关闭(需要历史估值数据)
                use_capital_flow_filter=False  # 暂时关闭(需要历史资金数据)
            )

            if len(similar) > 0:
                print(f"✅ 找到 {len(similar)} 个历史相似时期\n")

                # 计算未来收益
                future_returns = analyzer.calculate_future_returns(
                    index_code,
                    similar,
                    periods=[5, 10, 20, 60]
                )

                # 统计20日后概率
                prob_stats = prob_analyzer.calculate_probability(future_returns['return_20d'])

                print("📈 未来20日走势概率预测:")
                print_metric("上涨概率", f"{prob_stats['up_prob']:.1%}")
                print_metric("下跌概率", f"{prob_stats['down_prob']:.1%}")
                print_metric("平均收益", f"{prob_stats['mean_return']:+.2%}")
                print_metric("中位收益", f"{prob_stats['median_return']:+.2%}")
                print_metric("样本数量", f"{prob_stats['sample_size']}个")
            else:
                print("⚠️  未找到足够的历史相似时期")

        except Exception as e:
            print(f"❌ 多维度匹配失败: {str(e)}")

    # ========== 结束 ==========
    print_section_header("分析完成", "=")
    print(f"💡 提示: 添加 --detail 参数可查看历史匹配详情")
    print(f"💡 提示: 使用 --index <代码> 可分析其他指数\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 2 九维度市场分析')
    parser.add_argument('--index', '-i', default='sh000001', help='指数代码 (默认: sh000001)')
    parser.add_argument('--detail', '-d', action='store_true', help='显示详细的历史匹配分析')

    args = parser.parse_args()

    # 检查指数代码是否支持
    if args.index not in SUPPORTED_INDICES:
        print(f"❌ 不支持的指数代码: {args.index}")
        print(f"\n支持的指数:")
        for code, config in SUPPORTED_INDICES.items():
            print(f"  {code}: {config.name}")
        return 1

    try:
        analyze_nine_dimensions(args.index, args.detail)
        return 0
    except Exception as e:
        print(f"\n❌ 分析过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
