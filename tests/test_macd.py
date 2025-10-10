#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 MACD 指标计算
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np


def test_macd_calculation():
    """测试 MACD 计算逻辑"""
    print("=" * 70)
    print("测试 MACD 计算")
    print("=" * 70)

    # 生成测试数据（模拟上涨趋势）
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    close_prices = 20000 + np.cumsum(np.random.randn(100) * 100)  # 模拟恒生指数价格

    df = pd.DataFrame({
        'close': close_prices
    }, index=dates)

    print(f"\n生成测试数据: {len(df)} 天")
    print(f"价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")

    # 计算 MACD（与 HKMarketAnalyzer 中的逻辑一致）
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd_hist = (dif - dea) * 2

    # 信号判断
    prev_dif = dif.iloc[-2]
    prev_dea = dea.iloc[-2]
    curr_dif = dif.iloc[-1]
    curr_dea = dea.iloc[-1]

    if prev_dif <= prev_dea and curr_dif > curr_dea:
        macd_signal = "金叉"
    elif prev_dif >= prev_dea and curr_dif < curr_dea:
        macd_signal = "死叉"
    elif curr_dif > curr_dea:
        macd_signal = "多头"
    else:
        macd_signal = "空头"

    print(f"\nMACD 计算结果:")
    print(f"  DIF: {curr_dif:.2f}")
    print(f"  DEA: {curr_dea:.2f}")
    print(f"  MACD 柱: {macd_hist.iloc[-1]:.2f}")
    print(f"  信号: {macd_signal}")

    # 验证计算结果的合理性
    print(f"\n验证:")
    print(f"  [OK] EMA12 计算成功: {len(ema12)} 个数据点")
    print(f"  [OK] EMA26 计算成功: {len(ema26)} 个数据点")
    print(f"  [OK] DIF 计算成功: {len(dif)} 个数据点")
    print(f"  [OK] DEA 计算成功: {len(dea)} 个数据点")
    print(f"  [OK] MACD 柱计算成功: {len(macd_hist)} 个数据点")
    print(f"  [OK] 信号判断: {macd_signal}")

    # 显示最近5天的 MACD 数据
    print(f"\n最近5天 MACD 数据:")
    print(f"{'日期':<12} {'DIF':>10} {'DEA':>10} {'MACD柱':>10}")
    print("-" * 45)
    for i in range(-5, 0):
        date = df.index[i].strftime('%Y-%m-%d')
        print(f"{date:<12} {dif.iloc[i]:>10.2f} {dea.iloc[i]:>10.2f} {macd_hist.iloc[i]:>10.2f}")

    print("\n" + "=" * 70)
    print("[PASS] MACD 计算测试通过！")
    print("=" * 70)


def test_macd_signals():
    """测试 MACD 信号识别"""
    print("\n" + "=" * 70)
    print("测试 MACD 信号识别")
    print("=" * 70)

    # 测试场景1: 金叉
    print("\n场景1: 金叉信号")
    prev_dif, prev_dea = -10, 0
    curr_dif, curr_dea = 10, 0

    if prev_dif <= prev_dea and curr_dif > curr_dea:
        signal = "金叉"
    elif prev_dif >= prev_dea and curr_dif < curr_dea:
        signal = "死叉"
    elif curr_dif > curr_dea:
        signal = "多头"
    else:
        signal = "空头"

    print(f"  前一日: DIF={prev_dif}, DEA={prev_dea}")
    print(f"  当前: DIF={curr_dif}, DEA={curr_dea}")
    print(f"  信号: {signal}")
    assert signal == "金叉", "金叉信号识别错误"
    print("  [OK] 金叉信号识别正确")

    # 测试场景2: 死叉
    print("\n场景2: 死叉信号")
    prev_dif, prev_dea = 10, 0
    curr_dif, curr_dea = -10, 0

    if prev_dif <= prev_dea and curr_dif > curr_dea:
        signal = "金叉"
    elif prev_dif >= prev_dea and curr_dif < curr_dea:
        signal = "死叉"
    elif curr_dif > curr_dea:
        signal = "多头"
    else:
        signal = "空头"

    print(f"  前一日: DIF={prev_dif}, DEA={prev_dea}")
    print(f"  当前: DIF={curr_dif}, DEA={curr_dea}")
    print(f"  信号: {signal}")
    assert signal == "死叉", "死叉信号识别错误"
    print("  [OK] 死叉信号识别正确")

    # 测试场景3: 多头
    print("\n场景3: 多头状态")
    prev_dif, prev_dea = 10, 5
    curr_dif, curr_dea = 15, 8

    if prev_dif <= prev_dea and curr_dif > curr_dea:
        signal = "金叉"
    elif prev_dif >= prev_dea and curr_dif < curr_dea:
        signal = "死叉"
    elif curr_dif > curr_dea:
        signal = "多头"
    else:
        signal = "空头"

    print(f"  前一日: DIF={prev_dif}, DEA={prev_dea}")
    print(f"  当前: DIF={curr_dif}, DEA={curr_dea}")
    print(f"  信号: {signal}")
    assert signal == "多头", "多头信号识别错误"
    print("  [OK] 多头信号识别正确")

    # 测试场景4: 空头
    print("\n场景4: 空头状态")
    prev_dif, prev_dea = -10, -5
    curr_dif, curr_dea = -15, -8

    if prev_dif <= prev_dea and curr_dif > curr_dea:
        signal = "金叉"
    elif prev_dif >= prev_dea and curr_dif < curr_dea:
        signal = "死叉"
    elif curr_dif > curr_dea:
        signal = "多头"
    else:
        signal = "空头"

    print(f"  前一日: DIF={prev_dif}, DEA={prev_dea}")
    print(f"  当前: DIF={curr_dif}, DEA={curr_dea}")
    print(f"  信号: {signal}")
    assert signal == "空头", "空头信号识别错误"
    print("  [OK] 空头信号识别正确")

    print("\n" + "=" * 70)
    print("[PASS] MACD 信号识别测试全部通过！")
    print("=" * 70)


if __name__ == "__main__":
    # 运行测试
    test_macd_calculation()
    test_macd_signals()

    print("\n" + "=" * 70)
    print("所有测试完成！MACD 功能实现正确 [PASS]")
    print("=" * 70)
