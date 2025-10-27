#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背离分析器测试脚本
测试A股、H股、美股的背离检测功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import logging
from divergence_analyzer import DivergenceAnalyzer, normalize_dataframe_columns

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_cn_market():
    """测试A股市场"""
    print("\n" + "=" * 80)
    print("测试 1: A股市场背离分析 (上证指数)")
    print("=" * 80)

    try:
        from src.data_sources.us_stock_source import USStockDataSource

        # 使用yfinance获取上证指数数据
        source = USStockDataSource()
        df = source.get_us_index_daily('SSE', period='6mo')  # 上证指数

        if df.empty:
            print("[ERROR] 数据获取失败")
            return

        # 标准化列名
        df = normalize_dataframe_columns(df)

        print(f"[OK] 数据获取成功: {len(df)} 条记录")
        print(f"  日期范围: {df.index[0].date()} 至 {df.index[-1].date()}")
        print(f"  最新收盘: {df['close'].iloc[-1]:.2f}")

        # 创建分析器
        analyzer = DivergenceAnalyzer(
            peak_valley_window=5,
            lookback_period=100,
            min_peak_distance=5
        )

        # 综合分析
        result = analyzer.comprehensive_analysis(df, symbol='上证指数', market='CN')

        # 打印结果
        print_analysis_result(result)

    except Exception as e:
        logger.error(f"A股市场测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_hk_market():
    """测试H股市场"""
    print("\n" + "=" * 80)
    print("测试 2: H股市场背离分析 (恒生指数)")
    print("=" * 80)

    try:
        from src.data_sources.hkstock_source import HKStockDataSource

        source = HKStockDataSource()
        df = source.get_hk_index_daily('HSI')

        if df.empty:
            print("[ERROR] 数据获取失败")
            return

        # 标准化列名
        df = normalize_dataframe_columns(df)

        print(f"[OK] 数据获取成功: {len(df)} 条记录")
        print(f"  日期范围: {df.index[0].date()} 至 {df.index[-1].date()}")
        print(f"  最新收盘: {df['close'].iloc[-1]:.2f}")

        # 创建分析器
        analyzer = DivergenceAnalyzer(
            peak_valley_window=5,
            lookback_period=100,
            min_peak_distance=5
        )

        # 综合分析
        result = analyzer.comprehensive_analysis(df, symbol='恒生指数', market='HK')

        # 打印结果
        print_analysis_result(result)

    except Exception as e:
        logger.error(f"H股市场测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_us_market():
    """测试美股市场"""
    print("\n" + "=" * 80)
    print("测试 3: 美股市场背离分析 (标普500)")
    print("=" * 80)

    try:
        from src.data_sources.us_stock_source import USStockDataSource

        source = USStockDataSource()
        df = source.get_us_index_daily('SPX', period='6mo')

        if df.empty:
            print("[ERROR] 数据获取失败")
            return

        # 标准化列名
        df = normalize_dataframe_columns(df)

        print(f"[OK] 数据获取成功: {len(df)} 条记录")
        print(f"  日期范围: {df.index[0].date()} 至 {df.index[-1].date()}")
        print(f"  最新收盘: {df['close'].iloc[-1]:.2f}")

        # 创建分析器
        analyzer = DivergenceAnalyzer(
            peak_valley_window=5,
            lookback_period=100,
            min_peak_distance=5
        )

        # 综合分析
        result = analyzer.comprehensive_analysis(df, symbol='S&P 500', market='US')

        # 打印结果
        print_analysis_result(result)

    except Exception as e:
        logger.error(f"美股市场测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_individual_divergence_types():
    """测试单独的背离类型"""
    print("\n" + "=" * 80)
    print("测试 4: 单独测试各类背离检测")
    print("=" * 80)

    try:
        from src.data_sources.us_stock_source import USStockDataSource

        source = USStockDataSource()
        df = source.get_us_index_daily('SPX', period='6mo')
        df = normalize_dataframe_columns(df)

        if df.empty:
            print("[ERROR] 数据获取失败")
            return

        analyzer = DivergenceAnalyzer()

        # 1. 量价背离
        print("\n[1] 量价背离检测:")
        vol_result = analyzer.detect_volume_price_divergence(df)
        if vol_result.get('has_divergence'):
            for signal in vol_result['signals']:
                print(f"  [+] {signal.description}")
                print(f"    强度: {signal.strength}/100 | 置信度: {signal.confidence}")
        else:
            print("  - 无量价背离")

        # 2. MACD背驰
        print("\n[2] MACD背驰检测:")
        macd_result = analyzer.detect_macd_divergence(df)
        if macd_result.get('has_divergence'):
            for signal in macd_result['signals']:
                print(f"  [+] {signal.description}")
                print(f"    强度: {signal.strength}/100 | 置信度: {signal.confidence}")
        else:
            print("  - 无MACD背驰")

        # 3. RSI背离
        print("\n[3] RSI背离检测:")
        rsi_result = analyzer.detect_rsi_divergence(df)
        if rsi_result.get('has_divergence'):
            for signal in rsi_result['signals']:
                print(f"  [+] {signal.description}")
                print(f"    强度: {signal.strength}/100 | 置信度: {signal.confidence}")
        else:
            print("  - 无RSI背离")

    except Exception as e:
        logger.error(f"单独测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


def print_analysis_result(result: dict):
    """打印分析结果"""
    print(f"\n[综合分析结果]")
    print(f"  标的: {result['symbol']}")
    print(f"  市场: {result['market']}")
    print(f"  时间: {result['timestamp']}")

    if result['has_any_divergence']:
        print(f"\n[检测到背离信号]")

        # 打印所有信号
        for i, signal in enumerate(result['summary'], 1):
            confidence_icon = '[高]' if signal['confidence'] == '高' else '[中]' if signal['confidence'] == '中' else '[低]'
            print(f"\n  {i}. {confidence_icon} {signal['type']} - {signal['direction']}")
            print(f"     强度: {signal['strength']}/100")
            print(f"     置信度: {signal['confidence']}")
            print(f"     描述: {signal['description']}")

        # 打印综合评估
        if 'overall_assessment' in result:
            assessment = result['overall_assessment']
            print(f"\n[综合评估]")
            print(f"  信号: {assessment['signal']}")
            if 'strength' in assessment:
                print(f"  平均强度: {assessment['strength']}/100")
            print(f"  信号数量: {assessment.get('total_signals', 0)}")
            print(f"    - 看跌信号: {assessment.get('bearish_signals', 0)}")
            print(f"    - 看涨信号: {assessment.get('bullish_signals', 0)}")
            print(f"  建议: {assessment['advice']}")
    else:
        print(f"\n[OK] {result['overall_assessment']['advice']}")


def main():
    """主测试函数"""
    print("=" * 80)
    print("背离分析器测试套件")
    print("=" * 80)

    # 测试各个市场
    test_us_market()      # 美股
    test_cn_market()      # A股
    test_hk_market()      # H股

    # 单独测试各类背离
    test_individual_divergence_types()

    print("\n" + "=" * 80)
    print("[OK] 所有测试完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
