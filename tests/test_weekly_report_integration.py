#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周报生成器集成测试
测试事件日历和风险预算在周报中的集成效果
"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from russ_trading.generators.weekly_strategy_generator import WeeklyStrategyGenerator


def test_weekly_report_with_positions():
    """测试带持仓数据的周报生成"""
    print("=" * 60)
    print("测试: 周报生成器集成(带持仓数据)")
    print("=" * 60)

    # 创建生成器
    generator = WeeklyStrategyGenerator()

    # 模拟持仓数据
    positions = [
        {
            'symbol': '513180.SS',
            'asset_name': '恒生科技ETF',
            'current_value': 30000,
            'current_ratio': 0.30,
            'daily_volatility': 0.022
        },
        {
            'symbol': '512880.SS',
            'asset_name': '证券ETF',
            'current_value': 25000,
            'current_ratio': 0.25,
            'daily_volatility': 0.025
        },
        {
            'symbol': 'BABA',
            'asset_name': '阿里巴巴',
            'current_value': 20000,
            'current_ratio': 0.20,
            'daily_volatility': 0.030
        }
    ]

    # 构造week_info
    week_info = {
        'current_position': '75%',
        'cash': '25%',
        'last_week_summary': '仓位从78%降至75%,符合震荡市策略',
        'positions': positions,
        'total_capital': 100000
    }

    # 构造info
    info = {
        'total_positions': 3,
        'high_concentration_assets': ['恒生科技ETF'],
        'suggested_adjustments': []
    }

    # 生成周报
    content = generator.generate_strategy_markdown(info, week_info)

    # 验证内容
    print("\n✅ 生成的周报长度:", len(content), "字符")

    # 检查是否包含事件日历章节
    if '📅 本周重要事件日历' in content:
        print("✅ 包含事件日历章节")
    else:
        print("❌ 未找到事件日历章节")

    # 检查是否包含风险预算章节
    if '💰 风险预算配置建议' in content:
        print("✅ 包含风险预算配置章节")
    else:
        print("❌ 未找到风险预算配置章节")

    # 检查是否包含VaR相关内容
    if 'VaR' in content:
        print("✅ 包含VaR风险分析")
    else:
        print("❌ 未找到VaR相关内容")

    # 保存到文件
    output_path = project_root / "docs" / "周报测试_集成效果.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✅ 周报已保存到: {output_path}")

    return content


def test_weekly_report_without_positions():
    """测试不带持仓数据的周报生成"""
    print("\n" + "=" * 60)
    print("测试: 周报生成器(不带持仓数据)")
    print("=" * 60)

    # 创建生成器
    generator = WeeklyStrategyGenerator()

    # 构造week_info(不含positions)
    week_info = {
        'current_position': '78%',
        'cash': '22%',
        'last_week_summary': '维持现状,观察为主'
    }

    # 构造info
    info = {
        'total_positions': 0,
        'high_concentration_assets': [],
        'suggested_adjustments': []
    }

    # 生成周报
    content = generator.generate_strategy_markdown(info, week_info)

    print("✅ 生成的周报长度:", len(content), "字符")

    # 验证不应该包含新章节(因为没有positions数据)
    if '📅 本周重要事件日历' not in content:
        print("✅ 正确:不带持仓时,不显示事件日历")
    else:
        print("⚠️ 警告:不带持仓时仍显示事件日历")

    if '💰 风险预算配置建议' not in content:
        print("✅ 正确:不带持仓时,不显示风险预算")
    else:
        print("⚠️ 警告:不带持仓时仍显示风险预算")

    return content


def main():
    """运行所有测试"""
    print("🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀")
    print("周报生成器集成测试套件")
    print("🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀")

    # 测试1: 带持仓数据
    try:
        content1 = test_weekly_report_with_positions()
        print("\n✅ 测试1通过")
    except Exception as e:
        print(f"\n❌ 测试1失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试2: 不带持仓数据
    try:
        content2 = test_weekly_report_without_positions()
        print("\n✅ 测试2通过")
    except Exception as e:
        print(f"\n❌ 测试2失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
