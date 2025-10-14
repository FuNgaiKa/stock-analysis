#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3.1 市场状态检测 - Demo脚本
基于12维度评分模型,自动诊断当前市场状态
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from position_analysis.core.enhanced_data_provider import EnhancedDataProvider
from position_analysis.core.market_state_detector import MarketStateDetector
import akshare as ak
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    """打印小节标题"""
    print(f"\n【{title}】")


def diagnose_market_state(index_code: str = 'sh000001', show_detail: bool = False):
    """
    市场状态诊断主函数

    Args:
        index_code: 指数代码
        show_detail: 是否显示详细的维度分析
    """
    print_header("Phase 3.1 市场状态智能诊断")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"分析标的: {index_code}")

    # 1. 初始化数据提供器和检测器
    provider = EnhancedDataProvider()
    detector = MarketStateDetector()

    # 2. 获取价格数据
    print("\n正在获取市场数据...")
    try:
        df_price = ak.stock_zh_index_daily(symbol=index_code)
        df_price['date'] = pd.to_datetime(df_price['date'])
        df_price = df_price.set_index('date').sort_index()
        current_price = df_price['close'].iloc[-1]
        print(f"✓ 当前价格: {current_price:.2f}")
    except Exception as e:
        print(f"✗ 获取价格数据失败: {str(e)}")
        return

    # 3. 获取各维度指标
    print("\n正在获取12维度指标...")

    # 3.1 均线数据
    print("  [1/12] 趋势(均线)...", end='')
    ma_metrics = provider.get_moving_averages(index_code)
    print("✓" if ma_metrics else "✗")

    # 3.2 估值指标
    print("  [2/12] 估值...", end='')
    valuation_metrics = provider.get_valuation_metrics()
    print("✓" if valuation_metrics else "✗")

    # 3.3 北向资金
    print("  [3/12] 北向资金...", end='')
    capital_flow_metrics = provider.get_north_capital_flow()
    print("✓" if capital_flow_metrics else "✗")

    # 3.4 市场情绪
    print("  [4/12] 市场情绪...", end='')
    sentiment_metrics = provider.get_market_sentiment()
    print("✓" if sentiment_metrics else "✓" if sentiment_metrics else "✗")

    # 3.5 市场宽度
    print("  [5/12] 市场宽度...", end='')
    breadth_metrics = provider.get_market_breadth_metrics()
    print("✓" if breadth_metrics else "✗")

    # 3.6 融资融券
    print("  [6/12] 融资融券...", end='')
    margin_metrics = provider.get_margin_trading_metrics()
    print("✓" if margin_metrics else "⚠")  # 这个接口可能经常失败

    # 3.7 主力资金
    print("  [7/12] 主力资金...", end='')
    main_fund_metrics = provider.get_main_fund_flow(index_code)
    print("✓" if main_fund_metrics else "⚠")

    # 3.8 龙虎榜
    print("  [8/12] 龙虎榜...", end='')
    lhb_metrics = provider.get_dragon_tiger_list_metrics()
    print("✓" if lhb_metrics else "⚠")

    # 3.9 波动率
    print("  [9/12] 波动率...", end='')
    volatility_metrics = provider.get_volatility_metrics(index_code)
    print("✓" if volatility_metrics else "✗")

    # 3.10 成交量
    print(" [10/12] 成交量...", end='')
    volume_metrics = provider.get_volume_metrics(index_code)
    print("✓" if volume_metrics else "✗")

    # 3.11 技术指标
    print(" [11/12] 技术指标...", end='')
    technical_metrics = provider.get_technical_indicators(index_code)
    print("✓" if technical_metrics else "✗")

    # 3.12 涨跌幅(已在price_data中)
    print(" [12/12] 涨跌幅...✓")

    # 4. 执行市场状态检测
    print("\n正在分析市场状态...")
    result = detector.detect_market_state(
        ma_metrics=ma_metrics,
        price_data=df_price,
        valuation_metrics=valuation_metrics,
        capital_flow_metrics=capital_flow_metrics,
        sentiment_metrics=sentiment_metrics,
        breadth_metrics=breadth_metrics,
        margin_metrics=margin_metrics,
        main_fund_metrics=main_fund_metrics,
        lhb_metrics=lhb_metrics,
        volatility_metrics=volatility_metrics,
        volume_metrics=volume_metrics,
        technical_metrics=technical_metrics
    )

    if not result:
        print("✗ 市场状态分析失败")
        return

    # 5. 输出诊断结果
    print_section("市场状态诊断")
    print(f"  当前状态: {result['state']} (置信度 {result['confidence']*100:.0f}%)")
    print(f"  状态描述: {result['state_description']}")
    print(f"  综合评分: {result['overall_score']:+.2f} / 1.00")

    # 6. 关键信号
    if result.get('key_signals'):
        print_section("关键信号")
        for i, signal in enumerate(result['key_signals'], 1):
            print(f"    ✅ {signal}")

    # 7. 风险警告
    if result.get('risk_alerts'):
        print_section("风险警告")
        for i, alert in enumerate(result['risk_alerts'], 1):
            print(f"    ⚠️  {alert}")

    # 8. 仓位建议
    position_rec = detector.get_position_recommendation(
        result['state'],
        result['overall_score'],
        result['confidence']
    )

    print_section("操作建议")
    print(f"  建议仓位: {position_rec['position_center']*100:.0f}% " +
          f"({position_rec['position_min']*100:.0f}%-{position_rec['position_max']*100:.0f}%)")
    print(f"  操作策略: {position_rec['strategy']}")
    print(f"  具体行动: {position_rec['action']}")

    # 9. 详细维度分析 (可选)
    if show_detail:
        print_section("12维度详细分析")
        dimension_names = {
            'trend': '1. 趋势(均线)',
            'price_change': '2. 涨跌幅',
            'valuation': '3. 估值',
            'capital_flow': '4. 北向资金',
            'sentiment': '5. 市场情绪',
            'breadth': '6. 市场宽度',
            'leverage': '7. 融资融券',
            'main_fund': '8. 主力资金',
            'institution': '9. 机构行为',
            'volatility': '10. 波动率',
            'volume': '11. 成交量',
            'technical': '12. 技术形态'
        }

        for dim_key, dim_name in dimension_names.items():
            score = result['dimension_scores'].get(dim_key, 0)
            weight = detector.dimension_weights.get(dim_key, 0)

            # 可视化得分条
            bar_length = int(abs(score) * 20)
            if score > 0:
                bar = '█' * bar_length + '░' * (20 - bar_length)
                color = '🟢' if score > 0.5 else '🟡'
            else:
                bar = '░' * (20 - bar_length) + '█' * bar_length
                color = '🔴' if score < -0.5 else '🟡'

            print(f"  {dim_name:15} {color} [{bar}] {score:+.2f} (权重{weight*100:.0f}%)")

        # 显示具体指标值
        print_section("具体指标数据")

        if ma_metrics:
            print(f"  均线排列: {ma_metrics.get('ma_arrangement', 'N/A')}")
            print(f"    MA20: {ma_metrics.get('ma20', 0):.2f}")
            print(f"    MA60: {ma_metrics.get('ma60', 0):.2f}")
            print(f"    MA120: {ma_metrics.get('ma120', 0):.2f}")

        if valuation_metrics:
            print(f"  估值水平: {valuation_metrics.get('valuation_level', 'N/A')}")
            print(f"    PE分位: {valuation_metrics.get('pe_percentile_10y', 0)*100:.1f}%")
            print(f"    PB分位: {valuation_metrics.get('pb_percentile_10y', 0)*100:.1f}%")

        if capital_flow_metrics:
            print(f"  北向资金: {capital_flow_metrics.get('flow_status', 'N/A')}")
            print(f"    今日流入: {capital_flow_metrics.get('today_net_inflow', 0):.1f}亿")
            print(f"    5日累计: {capital_flow_metrics.get('cumulative_5d', 0):.1f}亿")

        if sentiment_metrics:
            print(f"  市场情绪: {sentiment_metrics.get('sentiment_level', 'N/A')}")
            print(f"    涨停: {sentiment_metrics.get('limit_up_count', 0)}只")
            print(f"    跌停: {sentiment_metrics.get('limit_down_count', 0)}只")

        if breadth_metrics:
            print(f"  市场宽度: {breadth_metrics.get('breadth_level', 'N/A')}")
            print(f"    上涨比例: {breadth_metrics.get('up_ratio', 0)*100:.1f}%")

        if margin_metrics:
            print(f"  融资融券: {margin_metrics.get('leverage_level', 'N/A')}")
            print(f"    融资余额: {margin_metrics.get('margin_balance', 0):.0f}亿")
            print(f"    变化率: {margin_metrics.get('margin_balance_pct_change', 0):+.2f}%")

        if main_fund_metrics:
            print(f"  主力资金: {main_fund_metrics.get('fund_flow_status', 'N/A')}")
            print(f"    今日流入: {main_fund_metrics.get('today_main_inflow', 0):.1f}亿")
            print(f"    5日累计: {main_fund_metrics.get('cumulative_5d', 0):.1f}亿")

        if volatility_metrics:
            print(f"  波动率: {volatility_metrics.get('volatility_level', 'N/A')}")
            print(f"    当前波动: {volatility_metrics.get('current_volatility', 0)*100:.1f}%")
            print(f"    历史分位: {volatility_metrics.get('volatility_percentile', 0)*100:.1f}%")

        if volume_metrics:
            print(f"  成交量: {volume_metrics.get('volume_status', 'N/A')}")
            print(f"    量比: {volume_metrics.get('volume_ratio', 0):.2f}")

        if technical_metrics:
            print(f"  技术形态:")
            print(f"    MACD: {technical_metrics.get('macd_signal', 'N/A')}")
            print(f"    RSI: {technical_metrics.get('rsi', 0):.1f} ({technical_metrics.get('rsi_signal', 'N/A')})")

    # 10. 结论
    print_section("综合结论")

    if result['overall_score'] > 0.3:
        conclusion = "市场整体偏多,建议保持积极态度"
        emoji = "📈"
    elif result['overall_score'] < -0.3:
        conclusion = "市场整体偏空,建议保持谨慎"
        emoji = "📉"
    else:
        conclusion = "市场处于平衡状态,建议观望为主"
        emoji = "➡️"

    print(f"  {emoji} {conclusion}")
    print(f"  置信度: {'★' * int(result['confidence'] * 5)}{'☆' * (5 - int(result['confidence'] * 5))} " +
          f"({result['confidence']*100:.0f}%)")

    print("\n" + "=" * 80)
    print("⚠️  风险提示: 本分析仅供参考,不构成投资建议。投资有风险,决策需谨慎。")
    print("=" * 80 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 3.1 市场状态智能诊断')
    parser.add_argument(
        '--index',
        '-i',
        type=str,
        default='sh000001',
        help='指数代码 (默认: sh000001 上证指数)'
    )
    parser.add_argument(
        '--detail',
        '-d',
        action='store_true',
        help='显示详细的维度分析'
    )

    args = parser.parse_args()

    try:
        diagnose_market_state(args.index, args.detail)
    except KeyboardInterrupt:
        print("\n\n用户中断执行")
    except Exception as e:
        print(f"\n执行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
