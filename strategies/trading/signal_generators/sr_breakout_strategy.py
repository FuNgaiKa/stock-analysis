#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支撑/压力位突破策略
基于动态计算的支撑和压力位进行交易
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SRBreakoutStrategy:
    """支撑/压力位突破策略"""

    def __init__(
        self,
        lookback_period: int = 60,
        breakout_threshold: float = 0.01,  # 1%突破确认
        volume_threshold: float = 1.2,      # 1.2倍平均成交量
    ):
        """
        初始化策略参数

        Args:
            lookback_period: 支撑/压力位计算回溯周期
            breakout_threshold: 突破确认阈值(百分比)
            volume_threshold: 成交量确认倍数
        """
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold
        self.volume_threshold = volume_threshold

    def calculate_support_resistance(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        计算动态支撑和压力位

        Args:
            df: 价格数据

        Returns:
            (support, resistance) 支撑位和压力位
        """
        if len(df) < self.lookback_period:
            return None, None

        # 最近N天的高低点
        recent_data = df.tail(self.lookback_period)
        highs = recent_data['high'].values
        lows = recent_data['low'].values

        # 找局部高点和低点
        local_highs = []
        local_lows = []

        window = 5
        for i in range(window, len(recent_data) - window):
            # 局部高点
            if highs[i] == max(highs[i-window:i+window+1]):
                local_highs.append(highs[i])
            # 局部低点
            if lows[i] == min(lows[i-window:i+window+1]):
                local_lows.append(lows[i])

        if not local_highs or not local_lows:
            return None, None

        # 当前价格
        current_price = df['close'].iloc[-1]

        # 找最近的压力位(高于当前价)
        resistance_levels = [h for h in local_highs if h > current_price]
        resistance = min(resistance_levels) if resistance_levels else max(local_highs)

        # 找最近的支撑位(低于当前价)
        support_levels = [l for l in local_lows if l < current_price]
        support = max(support_levels) if support_levels else min(local_lows)

        return support, resistance

    def calculate_average_volume(self, df: pd.DataFrame, period: int = 20) -> float:
        """计算平均成交量"""
        if len(df) < period:
            return df['volume'].mean()
        return df['volume'].tail(period).mean()

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成交易信号

        策略逻辑:
        1. 突破压力位+成交量放大 -> 买入
        2. 跌破支撑位+成交量放大 -> 卖出
        3. 价格在支撑/压力位之间 -> 观望

        Args:
            df: 包含OHLCV的DataFrame

        Returns:
            signals: 信号序列 (1=买入, -1=卖出, 0=观望)
        """
        signals = pd.Series(index=df.index, data=0, dtype=int)

        if len(df) < self.lookback_period + 20:
            logger.warning("数据不足,无法生成信号")
            return signals

        for i in range(self.lookback_period + 20, len(df)):
            # 获取历史数据
            hist_df = df.iloc[:i+1]

            # 计算支撑/压力位
            support, resistance = self.calculate_support_resistance(hist_df)

            if support is None or resistance is None:
                continue

            # 当前价格和成交量
            current_price = hist_df['close'].iloc[-1]
            prev_price = hist_df['close'].iloc[-2]
            current_volume = hist_df['volume'].iloc[-1]
            avg_volume = self.calculate_average_volume(hist_df)

            # 判断突破
            # 买入信号: 突破压力位
            if prev_price <= resistance and current_price > resistance * (1 + self.breakout_threshold):
                if current_volume > avg_volume * self.volume_threshold:
                    signals.iloc[i] = 1
                    logger.debug(f"买入信号: 突破压力位 {resistance:.2f}, 当前价 {current_price:.2f}")

            # 卖出信号: 跌破支撑位
            elif prev_price >= support and current_price < support * (1 - self.breakout_threshold):
                if current_volume > avg_volume * self.volume_threshold:
                    signals.iloc[i] = -1
                    logger.debug(f"卖出信号: 跌破支撑位 {support:.2f}, 当前价 {current_price:.2f}")

        return signals

    def get_strategy_info(self) -> Dict:
        """获取策略信息"""
        return {
            'name': '支撑/压力位突破策略',
            'description': '基于动态支撑和压力位进行突破交易',
            'parameters': {
                'lookback_period': self.lookback_period,
                'breakout_threshold': f'{self.breakout_threshold * 100:.1f}%',
                'volume_threshold': f'{self.volume_threshold:.1f}x',
            },
            'logic': [
                '1. 动态计算支撑/压力位(基于局部高低点)',
                '2. 突破压力位+放量 -> 买入',
                '3. 跌破支撑位+放量 -> 卖出',
                '4. 需要1%的突破确认',
                '5. 需要1.2倍以上成交量确认'
            ]
        }


if __name__ == '__main__':
    # 测试策略
    import yfinance as yf

    logging.basicConfig(level=logging.INFO)

    print("="*70)
    print("支撑/压力位突破策略测试")
    print("="*70)

    # 获取测试数据
    symbol = 'SPY'
    ticker = yf.Ticker(symbol)
    df = ticker.history(period='1y')

    # 重命名列
    df = df.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })

    # 创建策略
    strategy = SRBreakoutStrategy(
        lookback_period=60,
        breakout_threshold=0.01,
        volume_threshold=1.2
    )

    # 生成信号
    print(f"\n测试标的: {symbol}")
    print(f"数据范围: {df.index[0].date()} 至 {df.index[-1].date()}")
    print(f"数据点数: {len(df)}")

    signals = strategy.generate_signals(df)

    # 统计信号
    buy_signals = (signals == 1).sum()
    sell_signals = (signals == -1).sum()

    print(f"\n信号统计:")
    print(f"  买入信号: {buy_signals} 次")
    print(f"  卖出信号: {sell_signals} 次")

    # 显示最近5个信号
    signal_dates = signals[signals != 0]
    if len(signal_dates) > 0:
        print(f"\n最近5个信号:")
        for date, signal in signal_dates.tail(5).items():
            signal_type = "买入" if signal == 1 else "卖出"
            price = df.loc[date, 'close']
            print(f"  {date.date()}: {signal_type} @ ${price:.2f}")

    # 策略信息
    print(f"\n策略配置:")
    info = strategy.get_strategy_info()
    print(f"  名称: {info['name']}")
    print(f"  参数: {info['parameters']}")

    print("\n" + "="*70)
