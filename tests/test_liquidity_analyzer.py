#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流动性分析器单元测试
不依赖pytest,直接运行测试
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from russ_trading.analyzers.liquidity_analyzer import LiquidityAnalyzer


def test_high_liquidity_asset():
    """测试高流动性资产"""
    print("\n" + "="*60)
    print("测试1: 高流动性资产 (大盘ETF)")
    print("="*60)

    analyzer = LiquidityAnalyzer()

    # 创建高流动性数据
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    data = pd.DataFrame({
        'Close': np.random.uniform(5, 6, 30),
        'Volume': np.random.uniform(5_000_000_000, 10_000_000_000, 30),  # 50-100亿股
        'High': np.random.uniform(5, 6, 30),
        'Low': np.random.uniform(5, 6, 30)
    }, index=dates)

    result = analyzer.analyze_liquidity(
        symbol='TEST_HIGH',
        price_data=data,
        position_value=1_000_000  # 100万持仓
    )

    print(f"标的: {result['symbol']}")
    print(f"日均成交额: ¥{result['avg_amount']/100000000:.2f}亿")
    print(f"流动性评分: {result['liquidity_score']}分")
    print(f"流动性等级: {result['liquidity_level']}")
    print(f"平仓天数: {result['sell_days_needed']}天")

    # 验证
    assert result['liquidity_score'] >= 80, f"高流动性评分应≥80,实际{result['liquidity_score']}"
    assert result['liquidity_level'] == '优秀', f"高流动性等级应为'优秀',实际{result['liquidity_level']}"
    assert result['warning'] is None, "高流动性不应有预警"
    assert result['sell_days_needed'] <= 2, f"高流动性平仓天数应≤2天,实际{result['sell_days_needed']}"

    print("✅ 高流动性资产测试通过!")
    return True


def test_low_liquidity_asset():
    """测试低流动性资产"""
    print("\n" + "="*60)
    print("测试2: 低流动性资产 (小盘股)")
    print("="*60)

    analyzer = LiquidityAnalyzer()

    # 创建低流动性数据
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    data = pd.DataFrame({
        'Close': np.random.uniform(10, 12, 30),
        'Volume': np.random.uniform(100_000, 500_000, 30),  # 10-50万股
        'High': np.random.uniform(10, 12, 30),
        'Low': np.random.uniform(10, 12, 30)
    }, index=dates)

    result = analyzer.analyze_liquidity(
        symbol='TEST_LOW',
        price_data=data,
        position_value=100_000  # 10万持仓
    )

    print(f"标的: {result['symbol']}")
    print(f"日均成交额: ¥{result['avg_amount']/10000:.1f}万")
    print(f"流动性评分: {result['liquidity_score']}分")
    print(f"流动性等级: {result['liquidity_level']}")
    print(f"平仓天数: {result['sell_days_needed']}天")

    if result['warning']:
        print(f"预警: {result['warning']}")

    # 验证
    assert result['liquidity_score'] < 40, f"低流动性评分应<40,实际{result['liquidity_score']}"
    assert result['liquidity_level'] in ['一般', '不足'], f"低流动性等级应为'一般'或'不足',实际{result['liquidity_level']}"
    assert result['warning'] is not None, "低流动性应有预警"
    assert '流动性' in result['warning'], "预警信息应包含'流动性'"

    print("✅ 低流动性资产测试通过!")
    return True


def test_medium_liquidity_asset():
    """测试中等流动性资产"""
    print("\n" + "="*60)
    print("测试3: 中等流动性资产")
    print("="*60)

    analyzer = LiquidityAnalyzer()

    # 创建中等流动性数据
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    data = pd.DataFrame({
        'Close': np.random.uniform(20, 25, 30),
        'Volume': np.random.uniform(5_000_000, 10_000_000, 30),  # 500-1000万股
        'High': np.random.uniform(20, 25, 30),
        'Low': np.random.uniform(20, 25, 30)
    }, index=dates)

    result = analyzer.analyze_liquidity(
        symbol='TEST_MEDIUM',
        price_data=data,
        position_value=200_000  # 20万持仓
    )

    print(f"标的: {result['symbol']}")
    print(f"日均成交额: ¥{result['avg_amount']/100000000:.2f}亿")
    print(f"流动性评分: {result['liquidity_score']}分")
    print(f"流动性等级: {result['liquidity_level']}")
    print(f"平仓天数: {result['sell_days_needed']}天")

    # 验证
    assert 40 <= result['liquidity_score'] < 80, f"中等流动性评分应在40-80之间,实际{result['liquidity_score']}"
    assert result['liquidity_level'] in ['良好', '一般'], f"中等流动性等级应为'良好'或'一般',实际{result['liquidity_level']}"

    print("✅ 中等流动性资产测试通过!")
    return True


def test_sell_days_calculation():
    """测试平仓天数计算"""
    print("\n" + "="*60)
    print("测试4: 平仓天数计算")
    print("="*60)

    analyzer = LiquidityAnalyzer()

    # 创建数据
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    data = pd.DataFrame({
        'Close': [100.0] * 30,
        'Volume': [1_000_000] * 30,  # 100万股/天
        'High': [101.0] * 30,
        'Low': [99.0] * 30
    }, index=dates)

    # 日均成交额 = 100万股 * 100元 = 1亿元
    # 每天可卖10% = 1000万元
    # 持仓5000万,需要5天

    result = analyzer.analyze_liquidity(
        symbol='TEST_SELL_DAYS',
        price_data=data,
        position_value=50_000_000  # 5000万持仓
    )

    print(f"标的: {result['symbol']}")
    print(f"日均成交额: ¥{result['avg_amount']/100000000:.2f}亿")
    print(f"持仓市值: ¥{50_000_000/100000000:.2f}亿")
    print(f"平仓天数: {result['sell_days_needed']}天")
    print(f"计算说明: 每天可卖日均成交额的10%,即{result['avg_amount']*0.1/10000:.1f}万元")

    # 验证: 5000万 / (1亿 * 10%) = 5天
    expected_days = 5
    assert result['sell_days_needed'] == expected_days, \
        f"平仓天数应为{expected_days}天,实际{result['sell_days_needed']}"

    print("✅ 平仓天数计算测试通过!")
    return True


def test_error_handling():
    """测试错误处理"""
    print("\n" + "="*60)
    print("测试5: 错误处理")
    print("="*60)

    analyzer = LiquidityAnalyzer()

    # 测试空数据
    print("\n5.1 空数据测试")
    result = analyzer.analyze_liquidity(
        symbol='TEST_EMPTY',
        price_data=pd.DataFrame(),
        position_value=0
    )

    assert 'error' in result, "空数据应返回错误"
    assert result['liquidity_score'] == 0, "错误情况评分应为0"
    print(f"错误信息: {result['error']}")
    print("✅ 空数据处理正确")

    # 测试缺少列
    print("\n5.2 缺少列测试")
    data = pd.DataFrame({
        'Close': [100, 101, 102]
        # 缺少 Volume 列
    })

    result = analyzer.analyze_liquidity(
        symbol='TEST_MISSING_COL',
        price_data=data,
        position_value=0
    )

    assert 'error' in result, "缺少列应返回错误"
    assert '缺少必需列' in result['error'], "错误信息应说明缺少列"
    print(f"错误信息: {result['error']}")
    print("✅ 缺少列处理正确")

    print("\n✅ 错误处理测试通过!")
    return True


def test_liquidity_score_components():
    """测试流动性评分组成"""
    print("\n" + "="*60)
    print("测试6: 流动性评分组成")
    print("="*60)

    analyzer = LiquidityAnalyzer()

    # 测试不同成交额档次的评分
    test_cases = [
        {'amount': 6_000_000_000, 'expected_min': 80, 'desc': '超大盘 (>=50亿)'},
        {'amount': 1_500_000_000, 'expected_min': 60, 'desc': '大盘 (>=10亿)'},
        {'amount': 150_000_000, 'expected_min': 50, 'desc': '中盘 (>=1亿)'},
        {'amount': 15_000_000, 'expected_min': 30, 'desc': '小盘 (>=1000万)'},
        {'amount': 5_000_000, 'expected_min': 10, 'desc': '微盘 (<1000万)'}
    ]

    for case in test_cases:
        # 创建对应成交额的数据
        avg_price = 100
        avg_volume = case['amount'] / avg_price

        dates = pd.date_range(end=datetime.now(), periods=20, freq='D')
        data = pd.DataFrame({
            'Close': [avg_price] * 20,
            'Volume': [avg_volume] * 20,
            'High': [avg_price * 1.01] * 20,
            'Low': [avg_price * 0.99] * 20
        }, index=dates)

        result = analyzer.analyze_liquidity(
            symbol=f'TEST_{case["desc"]}',
            price_data=data,
            position_value=0
        )

        print(f"\n{case['desc']}")
        print(f"  日均成交额: ¥{result['avg_amount']/100000000:.2f}亿")
        print(f"  流动性评分: {result['liquidity_score']}分")
        print(f"  流动性等级: {result['liquidity_level']}")

        assert result['liquidity_score'] >= case['expected_min'], \
            f"{case['desc']}评分应≥{case['expected_min']},实际{result['liquidity_score']}"

    print("\n✅ 流动性评分组成测试通过!")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀"*30)
    print("流动性分析器测试套件")
    print("🚀"*30)

    tests = [
        test_high_liquidity_asset,
        test_low_liquidity_asset,
        test_medium_liquidity_asset,
        test_sell_days_calculation,
        test_error_handling,
        test_liquidity_score_components
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ 测试出错: {test.__name__}")
            print(f"   异常: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"测试汇总: 通过{passed}个, 失败{failed}个")
    print("="*60)

    if failed == 0:
        print("\n🎉 所有测试通过! 流动性分析器运行正常!")
        return True
    else:
        print(f"\n⚠️  有{failed}个测试失败,请检查代码")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
