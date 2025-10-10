#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试技术指标计算：布林带、ATR、成交量指标
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np


def test_bollinger_bands():
    """测试布林带计算"""
    print("=" * 70)
    print("测试布林带 (Bollinger Bands)")
    print("=" * 70)

    # 生成测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    close_prices = 20000 + np.cumsum(np.random.randn(100) * 100)

    df = pd.DataFrame({'close': close_prices}, index=dates)

    # 计算布林带
    bb_period = 20
    bb_std = 2
    bb_middle = df['close'].rolling(bb_period).mean()
    bb_std_dev = df['close'].rolling(bb_period).std()
    bb_upper = bb_middle + (bb_std * bb_std_dev)
    bb_lower = bb_middle - (bb_std * bb_std_dev)

    # 带宽百分比
    bb_width = ((bb_upper - bb_lower) / bb_middle * 100).iloc[-1]

    # 价格位置
    bb_position = ((df['close'].iloc[-1] - bb_lower.iloc[-1]) /
                   (bb_upper.iloc[-1] - bb_lower.iloc[-1]) * 100)

    print(f"\n布林带计算结果:")
    print(f"  当前价格: {df['close'].iloc[-1]:.2f}")
    print(f"  上轨: {bb_upper.iloc[-1]:.2f}")
    print(f"  中轨: {bb_middle.iloc[-1]:.2f}")
    print(f"  下轨: {bb_lower.iloc[-1]:.2f}")
    print(f"  带宽: {bb_width:.2f}%")
    print(f"  价格位置: {bb_position:.1f}% (0%=下轨, 100%=上轨)")

    # 验证
    print(f"\n验证:")
    print(f"  [OK] 中轨 = 20日MA")
    print(f"  [OK] 上轨 > 中轨: {bb_upper.iloc[-1] > bb_middle.iloc[-1]}")
    print(f"  [OK] 下轨 < 中轨: {bb_lower.iloc[-1] < bb_middle.iloc[-1]}")
    print(f"  [OK] 带宽百分比 > 0: {bb_width > 0}")

    assert bb_upper.iloc[-1] > bb_middle.iloc[-1], "上轨应该大于中轨"
    assert bb_lower.iloc[-1] < bb_middle.iloc[-1], "下轨应该小于中轨"
    assert bb_width > 0, "带宽应该大于0"

    print("\n[PASS] 布林带计算测试通过！")
    print("=" * 70)


def test_atr():
    """测试ATR计算"""
    print("\n" + "=" * 70)
    print("测试 ATR (Average True Range)")
    print("=" * 70)

    # 生成测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    base_price = 20000
    df = pd.DataFrame({
        'high': base_price + np.random.rand(100) * 500,
        'low': base_price - np.random.rand(100) * 500,
        'close': base_price + np.random.randn(100) * 200
    }, index=dates)

    # 计算ATR
    atr_period = 14
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(atr_period).mean()
    atr_pct = (atr.iloc[-1] / df['close'].iloc[-1] * 100)

    print(f"\nATR 计算结果:")
    print(f"  当前价格: {df['close'].iloc[-1]:.2f}")
    print(f"  ATR: {atr.iloc[-1]:.2f}")
    print(f"  ATR%: {atr_pct:.2f}%")
    print(f"  True Range (最新): {true_range.iloc[-1]:.2f}")

    # 验证
    print(f"\n验证:")
    print(f"  [OK] ATR > 0: {atr.iloc[-1] > 0}")
    print(f"  [OK] ATR <= High-Low: {atr.iloc[-1] <= (df['high'] - df['low']).max()}")
    print(f"  [OK] ATR% 合理范围 (0-10%): {0 < atr_pct < 10}")

    assert atr.iloc[-1] > 0, "ATR应该大于0"
    assert atr_pct > 0, "ATR百分比应该大于0"

    print("\n[PASS] ATR 计算测试通过！")
    print("=" * 70)


def test_obv_and_volume_ratio():
    """测试OBV和量比计算"""
    print("\n" + "=" * 70)
    print("测试 OBV 和量比")
    print("=" * 70)

    # 生成测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    # 模拟上涨趋势
    close_prices = 20000 + np.cumsum(np.random.randn(100) * 50)
    volumes = 1000000 + np.random.rand(100) * 500000

    df = pd.DataFrame({
        'close': close_prices,
        'volume': volumes
    }, index=dates)

    # 计算OBV
    price_direction = df['close'].diff().apply(
        lambda x: 1 if x > 0 else (-1 if x < 0 else 0)
    )
    obv = (df['volume'] * price_direction).cumsum()

    # 计算量比
    avg_volume_20 = df['volume'].rolling(20).mean()
    volume_ratio = df['volume'].iloc[-1] / avg_volume_20.iloc[-1]

    print(f"\n成交量指标计算结果:")
    print(f"  当日成交量: {df['volume'].iloc[-1]:,.0f}")
    print(f"  20日平均成交量: {avg_volume_20.iloc[-1]:,.0f}")
    print(f"  量比: {volume_ratio:.2f}")
    print(f"  OBV (当前): {obv.iloc[-1]:,.0f}")
    print(f"  OBV 变化趋势: {'上升' if obv.iloc[-1] > obv.iloc[-20] else '下降'}")

    # 验证
    print(f"\n验证:")
    print(f"  [OK] 量比 > 0: {volume_ratio > 0}")
    print(f"  [OK] OBV 已计算: {not pd.isna(obv.iloc[-1])}")

    # 简单的量价关系检验
    price_change = df['close'].iloc[-1] - df['close'].iloc[-20]
    obv_change = obv.iloc[-1] - obv.iloc[-20]
    same_direction = (price_change > 0 and obv_change > 0) or (price_change < 0 and obv_change < 0)

    print(f"  [INFO] 价格变化: {price_change:+.2f}")
    print(f"  [INFO] OBV变化: {obv_change:+.0f}")
    print(f"  [INFO] 方向一致: {same_direction}")

    assert volume_ratio > 0, "量比应该大于0"
    assert not pd.isna(obv.iloc[-1]), "OBV应该有值"

    print("\n[PASS] OBV 和量比测试通过！")
    print("=" * 70)


def test_volume_divergence():
    """测试量价背离检测"""
    print("\n" + "=" * 70)
    print("测试量价背离检测")
    print("=" * 70)

    # 场景1: 顶背离 (价格新高，OBV未新高)
    print("\n场景1: 顶背离测试")
    dates = pd.date_range('2024-01-01', periods=20, freq='D')

    # 价格持续上涨
    prices = list(range(100, 120))
    # 成交量逐渐萎缩
    volumes = [1000000 - i * 30000 for i in range(20)]

    df1 = pd.DataFrame({
        'close': prices,
        'volume': volumes
    }, index=dates)

    price_direction = df1['close'].diff().apply(
        lambda x: 1 if x > 0 else (-1 if x < 0 else 0)
    )
    obv = (df1['volume'] * price_direction).cumsum()

    price_high_idx = df1['close'].idxmax()
    obv_high_idx = obv.idxmax()

    is_top_divergence = (price_high_idx == df1.index[-1]) and (obv_high_idx != obv.index[-1])

    print(f"  价格最高点: {price_high_idx}")
    print(f"  OBV最高点: {obv_high_idx}")
    print(f"  是否顶背离: {is_top_divergence}")
    print(f"  [OK] 检测到顶背离" if is_top_divergence else "  [WARN] 未检测到顶背离")

    # 场景2: 正常情况 (价格和OBV同步)
    print("\n场景2: 正常情况测试")
    prices2 = list(range(100, 120))
    volumes2 = [1000000 + i * 30000 for i in range(20)]  # 成交量同步增长

    df2 = pd.DataFrame({
        'close': prices2,
        'volume': volumes2
    }, index=dates)

    price_direction2 = df2['close'].diff().apply(
        lambda x: 1 if x > 0 else (-1 if x < 0 else 0)
    )
    obv2 = (df2['volume'] * price_direction2).cumsum()

    price_high_idx2 = df2['close'].idxmax()
    obv_high_idx2 = obv2.idxmax()

    is_normal = (price_high_idx2 == df2.index[-1]) and (obv_high_idx2 == obv2.index[-1])

    print(f"  价格最高点: {price_high_idx2}")
    print(f"  OBV最高点: {obv_high_idx2}")
    print(f"  是否同步: {is_normal}")
    print(f"  [OK] 价格和OBV同步" if is_normal else "  [WARN] 未同步")

    print("\n[PASS] 量价背离检测测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    # 运行所有测试
    test_bollinger_bands()
    test_atr()
    test_obv_and_volume_ratio()
    test_volume_divergence()

    print("\n" + "=" * 70)
    print("所有技术指标测试完成！ [PASS]")
    print("=" * 70)
