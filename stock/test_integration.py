#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 测试所有新集成的数据源
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_efinance():
    """测试 efinance 数据源"""
    print("\n" + "=" * 60)
    print("测试 efinance 数据源")
    print("=" * 60)

    try:
        from efinance_source import EfinanceDataSource
        source = EfinanceDataSource()
        data = source.get_realtime_data()

        if data:
            print("[OK] efinance 数据源正常")
            print(f"  数据时间: {data.get('timestamp')}")
            if data.get('sz_index') is not None and not data['sz_index'].empty:
                print(f"  上证指数: 获取成功")
        else:
            print("[FAIL] efinance 数据获取失败")
    except Exception as e:
        print(f"[ERROR] efinance 测试失败: {str(e)}")


def test_baostock():
    """测试 baostock 数据源"""
    print("\n" + "=" * 60)
    print("测试 baostock 数据源")
    print("=" * 60)

    try:
        from baostock_source import BaostockDataSource
        source = BaostockDataSource()
        data = source.get_market_data()

        if data:
            print("[OK] baostock 数据源正常")
            if data.get('sz_index') is not None and not data['sz_index'].empty:
                print(f"  上证指数: {data['sz_index']['收盘'].iloc[0]:.2f}")
        else:
            print("[FAIL] baostock 数据获取失败")
    except Exception as e:
        print(f"[ERROR] baostock 测试失败: {str(e)}")


def test_multi_source():
    """测试多数据源管理器"""
    print("\n" + "=" * 60)
    print("测试多数据源管理器")
    print("=" * 60)

    try:
        from enhanced_data_sources import MultiSourceDataProvider
        provider = MultiSourceDataProvider()
        data = provider.get_market_data()

        if data:
            print("[OK] 多数据源管理器正常")
            print(f"  数据时间: {data.get('timestamp')}")
            if data.get('sz_index') is not None and not data['sz_index'].empty:
                print(f"  上证指数数据: 已获取")
        else:
            print("[FAIL] 多数据源获取失败")
    except Exception as e:
        print(f"[ERROR] 多数据源测试失败: {str(e)}")


def test_analyzer():
    """测试分析器集成"""
    print("\n" + "=" * 60)
    print("测试分析器集成")
    print("=" * 60)

    try:
        from stock import AStockHeatAnalyzer

        # 测试使用 baostock
        print("\n使用 baostock 数据源...")
        analyzer = AStockHeatAnalyzer(data_source='baostock')
        result = analyzer.analyze_market_heat()

        if result:
            print("[OK] 分析器集成正常")
            print(f"  火热程度: {result['heat_score']:.3f}")
            print(f"  风险等级: {result['risk_level']}")
        else:
            print("[FAIL] 分析失败")
    except Exception as e:
        print(f"[ERROR] 分析器测试失败: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("数据源集成测试")
    print("=" * 60)

    # 运行所有测试
    test_efinance()
    test_baostock()
    test_multi_source()
    test_analyzer()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)