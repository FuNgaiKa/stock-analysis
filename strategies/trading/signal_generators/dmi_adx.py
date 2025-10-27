#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMI/ADX 趋势强度指标
Directional Movement Index (DMI) + Average Directional Index (ADX)

用途:
- 判断市场是否处于趋势状态
- 评估趋势的强度
- 适合趋势跟踪策略

指标说明:
- +DI (Positive Directional Indicator): 上升动向指标
- -DI (Negative Directional Indicator): 下降动向指标
- ADX (Average Directional Index): 平均趋势指标
  * ADX > 25: 强趋势
  * ADX < 20: 弱趋势/震荡市
  * ADX > 50: 极强趋势

作者: Claude Code
日期: 2025-10-12
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class DMI_ADX_Calculator:
    """
    DMI/ADX 指标计算器

    趋势跟踪的核心指标，用于判断:
    1. 市场是否处于趋势
    2. 趋势的强度
    3. 趋势的方向
    """

    def __init__(self, period: int = 14):
        """
        初始化

        Args:
            period: 计算周期，默认14
        """
        self.period = period

    def calculate_dmi_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算完整的 DMI/ADX 指标

        Args:
            df: 包含 'high', 'low', 'close' 列的DataFrame

        Returns:
            添加了 +DI, -DI, ADX 列的DataFrame
        """
        df = df.copy()

        # Step 1: 计算 True Range (TR)
        df['tr'] = self._calculate_true_range(df)

        # Step 2: 计算 Directional Movement (+DM, -DM)
        df['+dm'], df['-dm'] = self._calculate_directional_movement(df)

        # Step 3: 平滑 TR, +DM, -DM (使用 Wilder's Smoothing)
        df['tr_smooth'] = self._wilders_smoothing(df['tr'], self.period)
        df['+dm_smooth'] = self._wilders_smoothing(df['+dm'], self.period)
        df['-dm_smooth'] = self._wilders_smoothing(df['-dm'], self.period)

        # Step 4: 计算 +DI 和 -DI
        df['+di'] = 100 * df['+dm_smooth'] / df['tr_smooth']
        df['-di'] = 100 * df['-dm_smooth'] / df['tr_smooth']

        # Step 5: 计算 DX (Directional Index)
        df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])

        # Step 6: 计算 ADX (DX 的平滑)
        df['adx'] = self._wilders_smoothing(df['dx'], self.period)

        # 清理中间变量
        df = df.drop(columns=['tr', '+dm', '-dm', 'tr_smooth',
                              '+dm_smooth', '-dm_smooth', 'dx'])

        return df

    def _calculate_true_range(self, df: pd.DataFrame) -> pd.Series:
        """
        计算真实波幅 (True Range)

        TR = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )
        """
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr

    def _calculate_directional_movement(
        self,
        df: pd.DataFrame
    ) -> Tuple[pd.Series, pd.Series]:
        """
        计算方向性移动 (+DM, -DM)

        +DM = current_high - previous_high (if > 0 and > -DM, else 0)
        -DM = previous_low - current_low (if > 0 and > +DM, else 0)
        """
        high_diff = df['high'] - df['high'].shift(1)
        low_diff = df['low'].shift(1) - df['low']

        # 初始化
        plus_dm = pd.Series(0, index=df.index, dtype=float)
        minus_dm = pd.Series(0, index=df.index, dtype=float)

        # +DM: 上升动向大于下降动向时
        plus_dm[high_diff > low_diff] = high_diff[high_diff > low_diff]
        plus_dm[plus_dm < 0] = 0

        # -DM: 下降动向大于上升动向时
        minus_dm[low_diff > high_diff] = low_diff[low_diff > high_diff]
        minus_dm[minus_dm < 0] = 0

        return plus_dm, minus_dm

    def _wilders_smoothing(self, series: pd.Series, period: int) -> pd.Series:
        """
        Wilder's Smoothing (类似EMA，但更平滑)

        First value = SUM(first n values) / n
        Subsequent values = (Previous smoothed value * (n-1) + Current value) / n
        """
        smoothed = pd.Series(index=series.index, dtype=float)

        # 第一个值：简单平均
        smoothed.iloc[period-1] = series.iloc[:period].sum() / period

        # 后续值：递推平滑
        for i in range(period, len(series)):
            smoothed.iloc[i] = (
                smoothed.iloc[i-1] * (period - 1) + series.iloc[i]
            ) / period

        return smoothed

    def identify_trend_strength(
        self,
        df: pd.DataFrame,
        index: int = -1
    ) -> Dict:
        """
        识别趋势强度和信号

        Args:
            df: 包含 DMI/ADX 指标的DataFrame
            index: 要分析的行索引，默认-1(最新)

        Returns:
            {
                'trend_strength': 'strong'/'medium'/'weak'/'no_trend',
                'trend_direction': 'bullish'/'bearish'/'neutral',
                'adx': ADX值,
                '+di': +DI值,
                '-di': -DI值,
                'signal': '强势上升趋势'/'弱趋势震荡'等,
                'recommendation': '持有多头'/'观望'等,
                'score': 0-10评分
            }
        """
        if index < 0:
            index = len(df) + index

        if index < 1 or 'adx' not in df.columns:
            return {
                'trend_strength': 'unknown',
                'trend_direction': 'unknown',
                'signal': '数据不足',
                'score': 0
            }

        row = df.iloc[index]
        prev_row = df.iloc[index - 1]

        adx = row['adx']
        plus_di = row['+di']
        minus_di = row['-di']

        # 1. 判断趋势强度
        if adx > 50:
            trend_strength = 'very_strong'
            strength_score = 10
        elif adx > 25:
            trend_strength = 'strong'
            strength_score = 8
        elif adx > 20:
            trend_strength = 'medium'
            strength_score = 6
        else:
            trend_strength = 'weak'
            strength_score = 3

        # 2. 判断趋势方向
        if plus_di > minus_di:
            if plus_di - minus_di > 10:
                trend_direction = 'strong_bullish'
                direction_desc = '强势上涨'
            else:
                trend_direction = 'bullish'
                direction_desc = '上涨'
        elif minus_di > plus_di:
            if minus_di - plus_di > 10:
                trend_direction = 'strong_bearish'
                direction_desc = '强势下跌'
            else:
                trend_direction = 'bearish'
                direction_desc = '下跌'
        else:
            trend_direction = 'neutral'
            direction_desc = '中性'

        # 3. 综合信号
        if trend_strength == 'very_strong' or trend_strength == 'strong':
            if trend_direction in ['strong_bullish', 'bullish']:
                signal = f'⬆️ {direction_desc}趋势（ADX={adx:.1f}）'
                recommendation = '✅ 持有多头/顺势做多'
                score = 9
            elif trend_direction in ['strong_bearish', 'bearish']:
                signal = f'⬇️ {direction_desc}趋势（ADX={adx:.1f}）'
                recommendation = '❌ 持有空头/顺势做空'
                score = 2
            else:
                signal = f'➡️ 趋势不明确（ADX={adx:.1f}）'
                recommendation = '⚠️ 观望'
                score = 5
        else:
            signal = f'📊 震荡市/弱趋势（ADX={adx:.1f}）'
            recommendation = '⚠️ 不适合趋势跟踪，等待突破'
            score = 5

        # 4. 检查趋势转折信号
        adx_rising = adx > prev_row['adx']
        di_cross = False

        # DI交叉检测
        if (plus_di > minus_di and prev_row['+di'] <= prev_row['-di']):
            di_cross = True
            cross_direction = 'golden'  # 金叉
        elif (plus_di < minus_di and prev_row['+di'] >= prev_row['-di']):
            di_cross = True
            cross_direction = 'death'   # 死叉

        alerts = []
        if di_cross:
            if cross_direction == 'golden' and adx > 20:
                alerts.append('🔔 +DI上穿-DI，可能启动上升趋势')
                score = min(score + 1, 10)
            elif cross_direction == 'death' and adx > 20:
                alerts.append('🔔 -DI上穿+DI，可能启动下跌趋势')
                score = max(score - 1, 0)

        if adx_rising and adx > 25:
            alerts.append('📈 ADX上升，趋势强化')
        elif not adx_rising and adx < 20:
            alerts.append('📉 ADX下降，趋势减弱')

        return {
            'trend_strength': trend_strength,
            'trend_direction': trend_direction,
            'adx': float(adx),
            '+di': float(plus_di),
            '-di': float(minus_di),
            'signal': signal,
            'recommendation': recommendation,
            'alerts': alerts,
            'score': score
        }

    def calculate_all_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为整个DataFrame计算DMI/ADX并生成信号

        Args:
            df: 包含OHLC数据的DataFrame

        Returns:
            添加了DMI/ADX指标和信号的DataFrame
        """
        # 计算指标
        df = self.calculate_dmi_adx(df)

        # 为每一行生成信号
        signals = []
        for i in range(len(df)):
            if i < self.period:
                signals.append(None)
            else:
                signal = self.identify_trend_strength(df, i)
                signals.append(signal)

        df['dmi_adx_signal'] = signals

        return df


def calculate_dmi_adx_simple(
    df: pd.DataFrame,
    period: int = 14
) -> pd.DataFrame:
    """
    简化的DMI/ADX计算函数（方便快速调用）

    Args:
        df: 包含'high', 'low', 'close'的DataFrame
        period: 周期，默认14

    Returns:
        添加了+di, -di, adx列的DataFrame
    """
    calculator = DMI_ADX_Calculator(period=period)
    return calculator.calculate_dmi_adx(df)


if __name__ == '__main__':
    """测试代码"""
    import yfinance as yf
    from datetime import datetime, timedelta

    print("=" * 80)
    print("DMI/ADX 趋势强度指标测试")
    print("=" * 80)

    # 测试纳斯达克指数
    print("\n📊 测试标的: 纳斯达克综合指数 (^IXIC)")
    print("-" * 80)

    # 获取数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6个月数据

    df = yf.download('^IXIC', start=start_date, end=end_date, progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1)

    df.columns = [c.lower() for c in df.columns]

    # 计算DMI/ADX
    calculator = DMI_ADX_Calculator(period=14)
    df = calculator.calculate_dmi_adx(df)

    # 获取最新信号
    signal = calculator.identify_trend_strength(df)

    print("\n📈 最新DMI/ADX指标:")
    print(f"  ADX: {signal['adx']:.2f}")
    print(f"  +DI: {signal['+di']:.2f}")
    print(f"  -DI: {signal['-di']:.2f}")

    print(f"\n🎯 趋势分析:")
    print(f"  趋势强度: {signal['trend_strength']}")
    print(f"  趋势方向: {signal['trend_direction']}")
    print(f"  信号: {signal['signal']}")
    print(f"  建议: {signal['recommendation']}")
    print(f"  评分: {signal['score']}/10")

    if signal.get('alerts'):
        print(f"\n⚠️ 重要提示:")
        for alert in signal['alerts']:
            print(f"  {alert}")

    # 显示最近5日数据
    print("\n📊 最近5日DMI/ADX数据:")
    print("-" * 80)
    recent = df[['close', '+di', '-di', 'adx']].tail(5)
    print(recent.to_string())

    print("\n" + "=" * 80)
    print("✅ DMI/ADX指标测试完成")
    print("=" * 80)
