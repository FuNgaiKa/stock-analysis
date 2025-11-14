#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VaR和风险预算分配单元测试
不依赖pytest,直接运行测试
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from russ_trading.managers.dynamic_position_manager import DynamicPositionManager


def test_var_calculation():
    """测试VaR计算"""
    print("\n" + "="*60)
    print("测试1: VaR计算")
    print("="*60)

    manager = DynamicPositionManager()

    # 测试用例1: 100万市值, 2%日波动率, 95%置信度
    var = manager.calculate_var(
        current_value=1_000_000,
        daily_volatility=0.02,
        confidence_level=0.95
    )

    print(f"市值: 100万")
    print(f"日波动率: 2%")
    print(f"置信度: 95%")
    print(f"1日VaR: {var:,.2f}元")

    # 验证VaR在合理范围
    # VaR = 1000000 * 1.645 * 0.02 ≈ 32,900元
    expected_var = 1_000_000 * 1.645 * 0.02
    assert abs(var - expected_var) < 1000, f"VaR应接近{expected_var:.0f}元,实际{var:.0f}元"

    print("✅ VaR计算测试通过!")
    return True


def test_var_different_confidence_levels():
    """测试不同置信度的VaR"""
    print("\n" + "="*60)
    print("测试2: 不同置信度的VaR")
    print("="*60)

    manager = DynamicPositionManager()

    current_value = 1_000_000
    daily_volatility = 0.02

    # 测试不同置信度
    confidence_levels = [0.90, 0.95, 0.99]

    for cl in confidence_levels:
        var = manager.calculate_var(
            current_value=current_value,
            daily_volatility=daily_volatility,
            confidence_level=cl
        )

        print(f"置信度{cl*100}%: VaR = {var:,.2f}元")

    # 验证: 置信度越高,VaR越大
    var_90 = manager.calculate_var(current_value, daily_volatility, 0.90)
    var_95 = manager.calculate_var(current_value, daily_volatility, 0.95)
    var_99 = manager.calculate_var(current_value, daily_volatility, 0.99)

    assert var_90 < var_95 < var_99, "置信度越高,VaR应该越大"

    print("✅ 不同置信度VaR测试通过!")
    return True


def test_risk_budget_over_budget():
    """测试超预算情况的风险分配"""
    print("\n" + "="*60)
    print("测试3: 超预算情况 - 需要缩减仓位")
    print("="*60)

    manager = DynamicPositionManager()

    # 模拟持仓: 总资金50万,当前仓位50万(满仓)
    positions = [
        {
            'symbol': '510300.SS',
            'asset_name': '证券ETF',
            'current_value': 200_000,  # 20万
            'current_ratio': 0.40,     # 40%
            'daily_volatility': 0.025  # 2.5%日波动率
        },
        {
            'symbol': '159915.SZ',
            'asset_name': '创业板ETF',
            'current_value': 150_000,  # 15万
            'current_ratio': 0.30,     # 30%
            'daily_volatility': 0.030  # 3%日波动率
        },
        {
            'symbol': '513050.SS',
            'asset_name': '中概互联',
            'current_value': 150_000,  # 15万
            'current_ratio': 0.30,     # 30%
            'daily_volatility': 0.035  # 3.5%日波动率
        }
    ]

    # 设置较小的风险预算,触发超预算
    total_capital = 500_000
    risk_budget = 20_000  # 风险预算仅2万 (总资金的4%)

    result = manager.allocate_by_risk_budget(
        positions=positions,
        total_capital=total_capital,
        risk_budget=risk_budget,
        confidence_level=0.95
    )

    print(f"\n风险预算配置:")
    print(f"总资金: {total_capital:,}元")
    print(f"风险预算: {risk_budget:,}元 ({risk_budget/total_capital*100:.1f}%)")
    print(f"当前总VaR: {result['total_var']:,.2f}元")
    print(f"VaR利用率: {result['var_utilization']*100:.1f}%")
    print(f"是否超预算: {'是' if result['over_budget'] else '否'}")

    print(f"\n仓位调整建议:")
    print(f"{'标的':<12} {'当前仓位':<8} {'建议仓位':<8} {'调整幅度':<10} VaR占比")
    print("-" * 60)

    for s in result['suggestions']:
        print(f"{s['asset_name']:<10} {s['current_ratio']*100:>6.1f}% "
              f"{s['suggested_ratio']*100:>6.1f}% {s['adjustment']*100:>8.1f}% "
              f"{s['var_contribution']*100:>6.1f}%")

    # 验证
    assert result['over_budget'], "当前VaR应该超预算"
    assert result['total_var'] > risk_budget, "总VaR应该大于风险预算"

    # 验证所有建议仓位都小于当前仓位
    for s in result['suggestions']:
        assert s['suggested_ratio'] < s['current_ratio'], \
            f"{s['asset_name']}建议仓位应小于当前仓位"

    print("\n✅ 超预算风险分配测试通过!")
    return True


def test_risk_budget_under_budget():
    """测试未超预算情况的风险分配"""
    print("\n" + "="*60)
    print("测试4: 未超预算情况 - 可适当加仓")
    print("="*60)

    manager = DynamicPositionManager()

    # 模拟持仓: 总资金50万,当前仓位25万(半仓)
    positions = [
        {
            'symbol': '510300.SS',
            'asset_name': '证券ETF',
            'current_value': 125_000,  # 12.5万
            'current_ratio': 0.25,     # 25%
            'daily_volatility': 0.020  # 2%日波动率
        },
        {
            'symbol': '159915.SZ',
            'asset_name': '创业板ETF',
            'current_value': 125_000,  # 12.5万
            'current_ratio': 0.25,     # 25%
            'daily_volatility': 0.025  # 2.5%日波动率
        }
    ]

    # 设置较大的风险预算,未超预算
    total_capital = 500_000
    risk_budget = 50_000  # 风险预算5万 (总资金的10%)

    result = manager.allocate_by_risk_budget(
        positions=positions,
        total_capital=total_capital,
        risk_budget=risk_budget,
        confidence_level=0.95
    )

    print(f"\n风险预算配置:")
    print(f"总资金: {total_capital:,}元")
    print(f"风险预算: {risk_budget:,}元 ({risk_budget/total_capital*100:.1f}%)")
    print(f"当前总VaR: {result['total_var']:,.2f}元")
    print(f"VaR利用率: {result['var_utilization']*100:.1f}%")
    print(f"是否超预算: {'是' if result['over_budget'] else '否'}")

    print(f"\n仓位调整建议:")
    print(f"{'标的':<12} {'当前仓位':<8} {'建议仓位':<8} {'调整幅度':<10} VaR占比")
    print("-" * 60)

    for s in result['suggestions']:
        print(f"{s['asset_name']:<10} {s['current_ratio']*100:>6.1f}% "
              f"{s['suggested_ratio']*100:>6.1f}% {s['adjustment']*100:>8.1f}% "
              f"{s['var_contribution']*100:>6.1f}%")

    # 验证
    assert not result['over_budget'], "当前VaR不应该超预算"
    assert result['total_var'] < risk_budget, "总VaR应该小于风险预算"

    print("\n✅ 未超预算风险分配测试通过!")
    return True


def test_risk_budget_balanced():
    """测试风险预算刚好平衡的情况"""
    print("\n" + "="*60)
    print("测试5: 风险预算平衡情况")
    print("="*60)

    manager = DynamicPositionManager()

    # 先计算一组持仓的VaR
    positions = [
        {
            'symbol': '510300.SS',
            'asset_name': '证券ETF',
            'current_value': 200_000,
            'current_ratio': 0.40,
            'daily_volatility': 0.020
        },
        {
            'symbol': '159915.SZ',
            'asset_name': '创业板ETF',
            'current_value': 150_000,
            'current_ratio': 0.30,
            'daily_volatility': 0.025
        }
    ]

    total_capital = 500_000

    # 第一次计算,获取当前VaR
    result1 = manager.allocate_by_risk_budget(
        positions=positions,
        total_capital=total_capital,
        risk_budget=100_000,  # 先用一个大的预算
        confidence_level=0.95
    )

    current_var = result1['total_var']

    # 第二次计算,用当前VaR作为风险预算
    result2 = manager.allocate_by_risk_budget(
        positions=positions,
        total_capital=total_capital,
        risk_budget=current_var,  # 刚好等于当前VaR
        confidence_level=0.95
    )

    print(f"\n风险预算配置:")
    print(f"当前总VaR: {result2['total_var']:,.2f}元")
    print(f"风险预算: {result2['risk_budget']:,.2f}元")
    print(f"VaR利用率: {result2['var_utilization']*100:.1f}%")

    # 验证VaR利用率接近100%
    assert 0.99 < result2['var_utilization'] < 1.01, \
        f"VaR利用率应接近100%,实际{result2['var_utilization']*100:.1f}%"

    # 验证不应该触发超预算
    assert not result2['over_budget'], "刚好平衡时不应该超预算"

    print("\n✅ 风险预算平衡测试通过!")
    return True


def test_var_with_holding_days():
    """测试多日持有期的VaR"""
    print("\n" + "="*60)
    print("测试6: 多日持有期VaR")
    print("="*60)

    manager = DynamicPositionManager()

    current_value = 1_000_000
    daily_volatility = 0.02

    # 测试不同持有天数
    holding_days_list = [1, 5, 10, 20]

    print(f"市值: {current_value:,}元")
    print(f"日波动率: {daily_volatility*100}%")
    print(f"置信度: 95%\n")

    for days in holding_days_list:
        var = manager.calculate_var(
            current_value=current_value,
            daily_volatility=daily_volatility,
            confidence_level=0.95,
            holding_days=days
        )

        print(f"{days}日VaR: {var:,.2f}元")

    # 验证: 持有天数越长,VaR越大
    var_1d = manager.calculate_var(current_value, daily_volatility, 0.95, 1)
    var_10d = manager.calculate_var(current_value, daily_volatility, 0.95, 10)

    # VaR应该 ∝ sqrt(天数), 即10日VaR ≈ 1日VaR * sqrt(10)
    expected_ratio = (10 ** 0.5)
    actual_ratio = var_10d / var_1d

    assert abs(actual_ratio - expected_ratio) < 0.01, \
        f"10日VaR应约为1日VaR的{expected_ratio:.2f}倍,实际{actual_ratio:.2f}倍"

    print("\n✅ 多日持有期VaR测试通过!")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀"*30)
    print("VaR和风险预算分配测试套件")
    print("🚀"*30)

    tests = [
        test_var_calculation,
        test_var_different_confidence_levels,
        test_risk_budget_over_budget,
        test_risk_budget_under_budget,
        test_risk_budget_balanced,
        test_var_with_holding_days
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
        print("\n🎉 所有测试通过! VaR和风险预算分配功能运行正常!")
        return True
    else:
        print(f"\n⚠️  有{failed}个测试失败,请检查代码")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
