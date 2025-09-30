#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票分析项目主入口文件
提供股票分析和复合收益计算功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock.stock import AStockHeatAnalyzer
from compound_interest.compound_calculator import CompoundCalculator


def demo_stock_analysis():
    """演示股票分析功能"""
    print("=== A股市场火热程度分析 ===")
    try:
        # 直接显示数据源选择菜单
        print("\n请选择数据源:")
        from stock.data_source_selector import DataSourceSelector
        selector = DataSourceSelector()

        # 显示菜单并选择
        source_code = selector.select_source()

        print(f"\n正在启动分析器（数据源: {source_code}）...")
        analyzer = AStockHeatAnalyzer(data_source=source_code)

        # 执行市场分析
        print("\n正在分析市场数据...\n")
        result = analyzer.analyze_market_heat()

        if result:
            print("\n" + "=" * 60)
            print("分析结果")
            print("=" * 60)
            print(f"分析时间: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"数据源: {source_code}")
            print(f"火热程度评分: {result['heat_score']:.3f}")
            print(f"风险等级: {result['risk_level']}")
            print(f"仓位建议: {result['position_suggestion']}")
            print("\n详细指标:")
            print(f"  - 成交量比率: {result['indicators']['volume_ratio']:.2f}")
            print(f"  - 价格动量: {result['indicators']['price_momentum']:.4f}")
            print(f"  - 市场广度: {result['indicators']['market_breadth']:.4f}")
            print(f"  - 波动率: {result['indicators']['volatility']:.4f}")
            print(f"  - 情绪指标: {result['indicators']['sentiment']:.4f}")

            # 显示市场概况
            summary = result.get('market_data_summary', {})
            if summary:
                print("\n市场概况:")
                print(f"  - 上证指数涨跌幅: {summary.get('sz_index_change', 'N/A')}")
                print(f"  - 涨停股票: {summary.get('limit_up_count', 0)} 只")
                print(f"  - 跌停股票: {summary.get('limit_down_count', 0)} 只")
            print("=" * 60)
        else:
            print("\n[错误] 分析失败，请检查网络连接")
            print("提示：可以尝试选择其他数据源")

    except Exception as e:
        print(f"股票分析出错: {e}")
        import traceback
        traceback.print_exc()


def demo_compound_calculator():
    """演示复合收益计算"""
    print("\n=== 复合收益计算演示 ===")
    try:
        calculator = CompoundCalculator()

        # 让用户输入参数
        print("\n请输入计算参数:")

        # 本金
        while True:
            try:
                principal_input = input("本金（元，默认100000）: ").strip()
                principal = float(principal_input) if principal_input else 100000
                if principal <= 0:
                    print("本金必须大于0，请重新输入")
                    continue
                break
            except ValueError:
                print("输入无效，请输入数字")

        # 年化收益率
        while True:
            try:
                rate_input = input("年化收益率（%，默认8）: ").strip()
                if rate_input:
                    annual_rate = float(rate_input) / 100
                else:
                    annual_rate = 0.08
                break
            except ValueError:
                print("输入无效，请输入数字")

        # 投资年限
        while True:
            try:
                years_input = input("投资年限（年，默认10）: ").strip()
                years = int(years_input) if years_input else 10
                if years <= 0:
                    print("年限必须大于0，请重新输入")
                    continue
                break
            except ValueError:
                print("输入无效，请输入整数")

        # 计算
        result = calculator.calculate(principal, annual_rate, years)

        # 显示结果
        print("\n" + "=" * 60)
        print("复合收益计算结果")
        print("=" * 60)
        print(f"本金: {principal:,.0f} 元")
        print(f"年化收益率: {annual_rate:.1%}")
        print(f"投资年限: {years} 年")
        print("-" * 60)
        print(f"最终金额: {result:,.0f} 元")
        print(f"总收益: {result - principal:,.0f} 元")
        print(f"收益率: {(result - principal) / principal:.1%}")
        print("=" * 60)

    except Exception as e:
        print(f"复合收益计算出错: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("=" * 60)
    print("欢迎使用 A股量化分析系统！")
    print("=" * 60)
    print("此项目包含以下功能:")
    print("  - A股市场火热程度分析")
    print("  - 智能仓位建议")
    print("  - 多数据源支持 (efinance, baostock, akshare 等)")
    print("  - 复合收益计算")

    while True:
        print("\n请选择功能:")
        print("1. A股市场分析 (推荐)")
        print("2. 复合收益计算")
        print("3. 退出")

        choice = input("\n请输入选择 (1-3): ").strip()

        if choice == '1':
            demo_stock_analysis()
        elif choice == '2':
            demo_compound_calculator()
        elif choice == '3':
            print("\n谢谢使用！")
            break
        else:
            print("无效选择，请重新输入")


if __name__ == '__main__':
    main()
