#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本 - 带数据源选择
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stock.stock import AStockHeatAnalyzer
from stock.data_source_selector import DataSourceSelector


def quick_analysis():
    """快速分析 - 使用默认多数据源"""
    print("=" * 60)
    print("A股市场火热程度快速分析")
    print("=" * 60)

    print("\n正在启动分析器（使用多数据源自动切换）...")
    analyzer = AStockHeatAnalyzer()

    print("正在分析市场数据...\n")
    result = analyzer.analyze_market_heat()

    if result:
        print("=" * 60)
        print(f"分析时间: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print(f"\n[核心指标]")
        print(f"  火热程度评分: {result['heat_score']:.3f}")
        print(f"  风险等级: {result['risk_level']}")
        print(f"  仓位建议: {result['position_suggestion']}")

        print(f"\n[市场概况]")
        print(f"  上证指数涨跌幅: {result['market_data_summary']['sz_index_change']}")
        print(f"  涨停股票: {result['market_data_summary']['limit_up_count']} 只")
        print(f"  跌停股票: {result['market_data_summary']['limit_down_count']} 只")

        print(f"\n[详细指标]")
        print(f"  成交量比率: {result['indicators']['volume_ratio']:.2f}")
        print(f"  价格动量: {result['indicators']['price_momentum']:.4f}")
        print(f"  市场广度: {result['indicators']['market_breadth']:.4f}")
        print(f"  波动率: {result['indicators']['volatility']:.4f}")
        print(f"  情绪指标: {result['indicators']['sentiment']:.4f}")
        print("=" * 60)
    else:
        print("\n[错误] 分析失败，请检查网络连接或数据源")


def interactive_analysis():
    """交互式分析 - 让用户选择数据源"""
    print("=" * 60)
    print("A股市场火热程度分析 - 交互模式")
    print("=" * 60)

    selector = DataSourceSelector()
    source_code = selector.select_source()

    print(f"\n正在启动分析器（数据源: {source_code}）...")
    analyzer = AStockHeatAnalyzer(data_source=source_code)

    print("正在分析市场数据...\n")
    result = analyzer.analyze_market_heat()

    if result:
        print("=" * 60)
        print(f"分析时间: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"数据源: {source_code}")
        print("=" * 60)
        print(f"\n火热程度评分: {result['heat_score']:.3f}")
        print(f"风险等级: {result['risk_level']}")
        print(f"仓位建议: {result['position_suggestion']}")
        print("=" * 60)
    else:
        print("\n[错误] 分析失败")


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_analysis()
    else:
        quick_analysis()


if __name__ == "__main__":
    main()