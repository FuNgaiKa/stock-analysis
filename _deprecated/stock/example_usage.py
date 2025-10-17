#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用示例 - 演示如何使用不同的数据源
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock import AStockHeatAnalyzer


def example_1_default_multi_source():
    """示例1: 使用默认多数据源模式"""
    print("\n" + "=" * 60)
    print("示例1: 默认多数据源模式")
    print("=" * 60)

    analyzer = AStockHeatAnalyzer()
    result = analyzer.analyze_market_heat()

    if result:
        print(f"✓ 分析成功")
        print(f"  火热程度: {result['heat_score']:.3f}")
        print(f"  风险等级: {result['risk_level']}")
    else:
        print("✗ 分析失败")


def example_2_efinance():
    """示例2: 使用 efinance 数据源"""
    print("\n" + "=" * 60)
    print("示例2: 使用 efinance (东方财富) 数据源")
    print("=" * 60)

    analyzer = AStockHeatAnalyzer(data_source='efinance')
    result = analyzer.analyze_market_heat()

    if result:
        print(f"✓ 分析成功 (efinance)")
        print(f"  涨停数: {result['market_data_summary']['limit_up_count']}")
        print(f"  跌停数: {result['market_data_summary']['limit_down_count']}")
    else:
        print("✗ 分析失败")


def example_3_baostock():
    """示例3: 使用 baostock 数据源"""
    print("\n" + "=" * 60)
    print("示例3: 使用 baostock (证券宝) 数据源")
    print("=" * 60)

    analyzer = AStockHeatAnalyzer(data_source='baostock')
    result = analyzer.analyze_market_heat()

    if result:
        print(f"✓ 分析成功 (baostock)")
        print(f"  上证指数涨跌幅: {result['market_data_summary']['sz_index_change']}")
    else:
        print("✗ 分析失败")


def example_4_interactive():
    """示例4: 交互式选择数据源"""
    print("\n" + "=" * 60)
    print("示例4: 交互式选择数据源")
    print("=" * 60)

    from data_source_selector import DataSourceSelector

    selector = DataSourceSelector()
    source_code = selector.select_source()

    analyzer = AStockHeatAnalyzer(data_source=source_code)
    result = analyzer.analyze_market_heat()

    if result:
        print(f"✓ 分析成功")
        print(f"  数据源: {source_code}")
        print(f"  火热程度: {result['heat_score']:.3f}")
    else:
        print("✗ 分析失败")


def example_5_quick_recommendation():
    """示例5: 根据场景快速选择数据源"""
    print("\n" + "=" * 60)
    print("示例5: 根据场景快速选择数据源")
    print("=" * 60)

    from data_source_selector import DataSourceSelector

    selector = DataSourceSelector()

    # 场景: 实时监控
    print("\n场景: 实时监控")
    source = selector.get_quick_recommendation('realtime')
    print(f"推荐数据源: {source}")
    analyzer = AStockHeatAnalyzer(data_source=source)
    # result = analyzer.analyze_market_heat()

    # 场景: 历史回测
    print("\n场景: 历史回测")
    source = selector.get_quick_recommendation('backtest')
    print(f"推荐数据源: {source}")

    # 场景: 全市场分析
    print("\n场景: 全市场分析")
    source = selector.get_quick_recommendation('analysis')
    print(f"推荐数据源: {source}")


if __name__ == "__main__":
    print("=" * 60)
    print("数据源使用示例")
    print("=" * 60)

    # 运行示例
    try:
        # 示例1: 默认多数据源
        # example_1_default_multi_source()

        # 示例2: efinance
        # example_2_efinance()

        # 示例3: baostock
        # example_3_baostock()

        # 示例4: 交互式选择（需要用户输入）
        # example_4_interactive()

        # 示例5: 场景推荐
        example_5_quick_recommendation()

        print("\n" + "=" * 60)
        print("所有示例完成")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()