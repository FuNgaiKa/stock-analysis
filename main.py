#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票分析项目主入口文件
提供股票分析和复合收益计算功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock.enhanced_stock_analyzer import EnhancedStockAnalyzer
from compound_interest.compound_calculator import CompoundCalculator


def demo_stock_analysis():
    """演示股票分析功能"""
    print("=== 股票分析演示 ===")
    try:
        analyzer = EnhancedStockAnalyzer()
        # 分析平安银行
        analyzer.analyze_stock("000001", period="6m")
        print("股票分析完成！")
    except Exception as e:
        print(f"股票分析出错: {e}")


def demo_compound_calculator():
    """演示复合收益计算"""
    print("\n=== 复合收益计算演示 ===")
    try:
        calculator = CompoundCalculator()

        # 示例：本金10万，年化收益率8%，投资10年
        principal = 100000
        annual_rate = 0.08
        years = 10

        result = calculator.calculate(principal, annual_rate, years)
        print(f"本金: {principal:,.0f}元")
        print(f"年化收益率: {annual_rate:.1%}")
        print(f"投资年限: {years}年")
        print(f"最终收益: {result:,.0f}元")
        print(f"总收益: {result - principal:,.0f}元")

    except Exception as e:
        print(f"复合收益计算出错: {e}")


def main():
    """主函数"""
    print("欢迎使用股票分析项目！")
    print("此项目包含股票分析和复合收益计算功能")

    while True:
        print("\n请选择功能:")
        print("1. 股票分析演示")
        print("2. 复合收益计算演示")
        print("3. 退出")

        choice = input("请输入选择 (1-3): ").strip()

        if choice == '1':
            demo_stock_analysis()
        elif choice == '2':
            demo_compound_calculator()
        elif choice == '3':
            print("谢谢使用！")
            break
        else:
            print("无效选择，请重新输入")


if __name__ == '__main__':
    main()
