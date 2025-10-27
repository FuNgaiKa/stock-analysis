#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""演示背离分析器的完整输出"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from divergence_analyzer import DivergenceAnalyzer, normalize_dataframe_columns
from src.data_sources.us_stock_source import USStockDataSource
from src.data_sources.hkstock_source import HKStockDataSource
import json

def print_divider(title=""):
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)

def test_spx():
    """测试标普500"""
    print_divider("测试案例 1: 标普500指数 (SPX)")

    source = USStockDataSource()
    df = source.get_us_index_daily('SPX', period='6mo')
    df = normalize_dataframe_columns(df)

    print(f"\n[数据信息]")
    print(f"  代码: SPX (标普500)")
    print(f"  数据条数: {len(df)}")
    print(f"  日期范围: {df.index[0].date()} 至 {df.index[-1].date()}")
    print(f"  最新价格: {df['close'].iloc[-1]:.2f}")
    print(f"  期间涨跌: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:+.2f}%")

    analyzer = DivergenceAnalyzer(
        peak_valley_window=5,
        lookback_period=100,
        min_peak_distance=5
    )

    result = analyzer.comprehensive_analysis(df, symbol='S&P 500', market='US')

    print(f"\n[背离检测结果]")
    print(f"  发现背离: {'是' if result['has_any_divergence'] else '否'}")

    if result['has_any_divergence']:
        print(f"  信号总数: {len(result['summary'])}")

        for i, signal in enumerate(result['summary'], 1):
            print(f"\n  --- 信号 {i} ---")
            print(f"  类型: {signal['type']}")
            print(f"  方向: {signal['direction']}")
            print(f"  强度: {signal['strength']}/100")
            print(f"  置信度: {signal['confidence']}")
            print(f"  描述: {signal['description']}")

        if 'overall_assessment' in result:
            ass = result['overall_assessment']
            print(f"\n[综合评估]")
            print(f"  信号: {ass['signal']}")
            if 'strength' in ass:
                print(f"  平均强度: {ass['strength']}/100")
            print(f"  看跌信号: {ass.get('bearish_signals', 0)}")
            print(f"  看涨信号: {ass.get('bullish_signals', 0)}")
            print(f"  操作建议: {ass['advice']}")
    else:
        print(f"  评估: {result['overall_assessment']['advice']}")

    # 显示详细的背离点位
    if result['has_any_divergence']:
        print(f"\n[背离点位详情]")
        for detail_type in ['volume_price', 'macd', 'rsi']:
            detail = result['details'].get(detail_type, {})
            if detail.get('has_divergence'):
                print(f"\n  {detail_type.upper()} 背离:")
                for signal in detail['signals']:
                    print(f"    价格点位: {signal.price_points}")
                    print(f"    指标点位: {signal.indicator_points}")

def test_sse():
    """测试上证指数"""
    print_divider("测试案例 2: 上证指数 (SSE)")

    source = USStockDataSource()
    df = source.get_us_index_daily('SSE', period='6mo')
    df = normalize_dataframe_columns(df)

    print(f"\n[数据信息]")
    print(f"  代码: SSE (上证指数)")
    print(f"  数据条数: {len(df)}")
    print(f"  日期范围: {df.index[0].date()} 至 {df.index[-1].date()}")
    print(f"  最新价格: {df['close'].iloc[-1]:.2f}")
    print(f"  期间涨跌: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:+.2f}%")

    analyzer = DivergenceAnalyzer()
    result = analyzer.comprehensive_analysis(df, symbol='上证指数', market='CN')

    print(f"\n[背离检测结果]")
    print(f"  发现背离: {'是' if result['has_any_divergence'] else '否'}")

    if result['has_any_divergence']:
        print(f"  信号总数: {len(result['summary'])}")
        for i, signal in enumerate(result['summary'], 1):
            print(f"\n  --- 信号 {i} ---")
            print(f"  {signal['type']} - {signal['direction']}")
            print(f"  强度: {signal['strength']}/100 | 置信度: {signal['confidence']}")
            print(f"  {signal['description']}")

        if 'overall_assessment' in result:
            ass = result['overall_assessment']
            print(f"\n[综合评估]")
            print(f"  {ass['signal']} - {ass['advice']}")
    else:
        print(f"  评估: {result['overall_assessment']['advice']}")

def test_hsi():
    """测试恒生指数"""
    print_divider("测试案例 3: 恒生指数 (HSI)")

    try:
        source = HKStockDataSource()
        df = source.get_hk_index_daily('HSI')
        df = normalize_dataframe_columns(df)

        # 只取最近6个月
        df = df.tail(120)

        print(f"\n[数据信息]")
        print(f"  代码: HSI (恒生指数)")
        print(f"  数据条数: {len(df)}")
        print(f"  日期范围: {df.index[0].date()} 至 {df.index[-1].date()}")
        print(f"  最新价格: {df['close'].iloc[-1]:.2f}")
        print(f"  期间涨跌: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:+.2f}%")

        analyzer = DivergenceAnalyzer()
        result = analyzer.comprehensive_analysis(df, symbol='恒生指数', market='HK')

        print(f"\n[背离检测结果]")
        print(f"  发现背离: {'是' if result['has_any_divergence'] else '否'}")

        if result['has_any_divergence']:
            print(f"  信号总数: {len(result['summary'])}")
            for i, signal in enumerate(result['summary'], 1):
                print(f"\n  --- 信号 {i} ---")
                print(f"  {signal['type']} - {signal['direction']}")
                print(f"  强度: {signal['strength']}/100 | 置信度: {signal['confidence']}")
                print(f"  {signal['description']}")

            if 'overall_assessment' in result:
                ass = result['overall_assessment']
                print(f"\n[综合评估]")
                print(f"  {ass['signal']} - {ass['advice']}")
        else:
            print(f"  评估: {result['overall_assessment']['advice']}")

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {str(e)}")

def main():
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  背离分析器 - 完整演示输出".center(66) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)

    # 测试三个市场
    test_spx()
    test_sse()
    test_hsi()

    print_divider("测试完成")
    print("\n提示: 详细文档请参考 DIVERGENCE_ANALYZER_README.md\n")

if __name__ == '__main__':
    main()
