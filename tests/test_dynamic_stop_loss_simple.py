#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态止损功能简单测试
不依赖pytest,直接运行测试
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from russ_trading.managers.risk_manager import RiskManager


def test_atr_calculation():
    """测试ATR计算"""
    print("\n" + "="*60)
    print("测试1: ATR计算")
    print("="*60)

    rm = RiskManager()

    # 模拟价格数据
    prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106]
    highs = [101, 103, 102, 104, 103, 105, 104, 106, 105, 107]
    lows = [99, 101, 100, 102, 101, 103, 102, 104, 103, 105]

    atr = rm.calculate_atr(prices, highs, lows, period=5)

    print(f"价格序列: {prices[-5:]}")
    print(f"计算ATR: {atr:.4f}")

    assert atr > 0, "ATR应该大于0"
    assert 1 < atr < 3, f"ATR值{atr}不在预期范围内(1-3)"

    print("✅ ATR计算测试通过!")
    return True


def test_low_volatility_stop_loss():
    """测试低波动标的的动态止损"""
    print("\n" + "="*60)
    print("测试2: 低波动标的动态止损")
    print("="*60)

    rm = RiskManager()

    # 创建低波动价格数据 (极低波动,ATR < 1.5%)
    np.random.seed(42)
    prices = 100 + np.random.normal(0, 0.3, 30)  # 降低波动
    highs = prices * (1 + np.random.uniform(0.002, 0.005, 30))  # 减小振幅
    lows = prices * (1 - np.random.uniform(0.002, 0.005, 30))

    df = pd.DataFrame({
        'Close': prices,
        'High': highs,
        'Low': lows
    })

    result = rm.calculate_dynamic_stop_loss(
        symbol='TEST_LOW',
        current_price=101,
        entry_price=100,
        price_data=df
    )

    print(f"标的: {result['symbol']}")
    print(f"ATR: {result['atr']:.2f} ({result['atr_pct']*100:.2f}%)")
    print(f"波动率等级: {result['volatility_level']}")
    print(f"固定止损: {result['fixed_stop_loss']*100:.0f}%")
    print(f"动态止损: {result['dynamic_stop_loss']*100:.0f}%")
    print(f"建议: {result['recommendation']}")

    assert result['volatility_level'] == '低', f"应该识别为低波动,实际为{result['volatility_level']}"
    assert result['dynamic_stop_loss'] > -0.15, "低波动应该收紧止损"

    print("✅ 低波动动态止损测试通过!")
    return True


def test_high_volatility_stop_loss():
    """测试高波动标的的动态止损"""
    print("\n" + "="*60)
    print("测试3: 高波动标的动态止损")
    print("="*60)

    rm = RiskManager()

    # 创建高波动价格数据
    np.random.seed(42)
    prices = 100 + np.random.normal(0, 4, 30)
    highs = prices * (1 + np.random.uniform(0.005, 0.015, 30))
    lows = prices * (1 - np.random.uniform(0.005, 0.015, 30))

    df = pd.DataFrame({
        'Close': prices,
        'High': highs,
        'Low': lows
    })

    result = rm.calculate_dynamic_stop_loss(
        symbol='TEST_HIGH',
        current_price=101,
        entry_price=100,
        price_data=df
    )

    print(f"标的: {result['symbol']}")
    print(f"ATR: {result['atr']:.2f} ({result['atr_pct']*100:.2f}%)")
    print(f"波动率等级: {result['volatility_level']}")
    print(f"固定止损: {result['fixed_stop_loss']*100:.0f}%")
    print(f"动态止损: {result['dynamic_stop_loss']*100:.0f}%")
    print(f"建议: {result['recommendation']}")

    assert result['volatility_level'] == '高', f"应该识别为高波动,实际为{result['volatility_level']}"
    assert result['dynamic_stop_loss'] < -0.15, "高波动应该放宽止损"

    print("✅ 高波动动态止损测试通过!")
    return True


def test_stop_loss_trigger():
    """测试止损触发"""
    print("\n" + "="*60)
    print("测试4: 止损触发逻辑")
    print("="*60)

    rm = RiskManager()

    # 创建低波动数据,使止损线更紧
    np.random.seed(42)
    prices = 100 + np.random.normal(0, 0.3, 30)  # 低波动
    highs = prices * 1.005
    lows = prices * 0.995

    df = pd.DataFrame({
        'Close': prices,
        'High': highs,
        'Low': lows
    })

    # 当前价格大幅低于买入价
    result = rm.calculate_dynamic_stop_loss(
        symbol='TEST_TRIGGER',
        current_price=92,  # 跌了8%
        entry_price=100,
        price_data=df
    )

    print(f"买入价: {result['entry_price']:.2f}")
    print(f"当前价: {result['current_price']:.2f}")
    print(f"当前亏损: {result['current_loss']*100:.1f}%")
    print(f"动态止损线: {result['dynamic_stop_loss']*100:.1f}%")
    print(f"止损价: {result['stop_loss_price']:.2f}")
    print(f"是否触发: {result['is_triggered']}")
    print(f"建议: {result['recommendation']}")

    # 低波动情况下,止损线应该在-5%附近,当前亏损-8%应该触发
    assert result['is_triggered'], f"亏损{result['current_loss']*100:.1f}%超过止损线{result['dynamic_stop_loss']*100:.1f}%应该触发"
    assert '触发止损' in result['recommendation'], "建议中应该包含'触发止损'"

    print("✅ 止损触发测试通过!")
    return True


def test_real_world_scenario():
    """测试真实场景"""
    print("\n" + "="*60)
    print("测试5: 真实场景综合测试")
    print("="*60)

    rm = RiskManager()

    # 模拟一个上升趋势带波动的价格序列
    np.random.seed(123)
    base_prices = np.linspace(100, 110, 30)
    noise = np.random.normal(0, 1.5, 30)
    prices = base_prices + noise

    df = pd.DataFrame({
        'Close': prices,
        'High': prices * 1.01,
        'Low': prices * 0.99
    })

    result = rm.calculate_dynamic_stop_loss(
        symbol='510300.SS',  # 证券ETF
        current_price=108,
        entry_price=100,
        price_data=df
    )

    print(f"\n真实场景 - 证券ETF")
    print(f"标的: {result['symbol']}")
    print(f"买入价: {result['entry_price']:.2f}元")
    print(f"当前价: {result['current_price']:.2f}元")
    print(f"当前盈亏: {result['current_loss']*100:+.1f}%")
    print(f"\nATR分析:")
    print(f"  ATR: {result['atr']:.2f}元 ({result['atr_pct']*100:.2f}%)")
    print(f"  波动率等级: {result['volatility_level']} {result.get('volatility_color', '')}")
    print(f"  止损倍数: {result['stop_loss_multiplier']}倍ATR")
    print(f"\n止损建议:")
    print(f"  固定止损: {result['fixed_stop_loss']*100:.0f}%")
    print(f"  动态止损: {result['dynamic_stop_loss']*100:.0f}%")
    print(f"  止损价: {result['stop_loss_price']:.2f}元")
    print(f"  是否触发: {'是' if result['is_triggered'] else '否'}")
    print(f"\n💡 {result['recommendation']}")
    print(f"📌 {result['reason']}")

    # 验证所有关键字段存在
    required_fields = [
        'symbol', 'atr', 'atr_pct', 'volatility_level',
        'dynamic_stop_loss', 'stop_loss_price', 'current_loss',
        'is_triggered', 'recommendation', 'reason'
    ]

    for field in required_fields:
        assert field in result, f"缺少必需字段: {field}"

    assert not result['is_triggered'], "盈利8%不应该触发止损"

    print("\n✅ 真实场景测试通过!")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀"*30)
    print("动态止损功能测试套件")
    print("🚀"*30)

    tests = [
        test_atr_calculation,
        test_low_volatility_stop_loss,
        test_high_volatility_stop_loss,
        test_stop_loss_trigger,
        test_real_world_scenario
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
        print("\n🎉 所有测试通过! 动态止损功能运行正常!")
        return True
    else:
        print(f"\n⚠️  有{failed}个测试失败,请检查代码")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
