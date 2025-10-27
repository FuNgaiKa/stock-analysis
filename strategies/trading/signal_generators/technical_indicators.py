#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标计算模块
实现MACD、RSI、KDJ、MA等经典技术指标
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""

    def __init__(self):
        """初始化技术指标计算器"""
        self.indicators_cache = {}

    @staticmethod
    def calculate_ma(df: pd.DataFrame, periods: list = [5, 10, 20, 60]) -> pd.DataFrame:
        """
        计算移动平均线 (Moving Average)

        Args:
            df: 包含'close'列的DataFrame
            periods: MA周期列表，如[5, 10, 20, 60]

        Returns:
            添加了MA列的DataFrame
        """
        df = df.copy()

        for period in periods:
            df[f'ma{period}'] = df['close'].rolling(window=period).mean()

        return df

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> pd.DataFrame:
        """
        计算MACD指标 (Moving Average Convergence Divergence)

        Args:
            df: 包含'close'列的DataFrame
            fast_period: 快线周期，默认12
            slow_period: 慢线周期，默认26
            signal_period: 信号线周期，默认9

        Returns:
            添加了MACD、Signal、Histogram列的DataFrame
        """
        df = df.copy()

        # 计算快线和慢线的EMA
        exp1 = df['close'].ewm(span=fast_period, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow_period, adjust=False).mean()

        # MACD线 = 快线 - 慢线
        df['macd'] = exp1 - exp2

        # 信号线(DEA) = MACD的9日EMA
        df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()

        # MACD柱状图 = MACD - 信号线
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        return df

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算RSI指标 (Relative Strength Index)

        Args:
            df: 包含'close'列的DataFrame
            period: RSI周期，默认14

        Returns:
            添加了RSI列的DataFrame
        """
        df = df.copy()

        # 计算价格变化
        delta = df['close'].diff()

        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 计算平均涨幅和跌幅
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # 计算RS和RSI
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))

        return df

    @staticmethod
    def calculate_kdj(
        df: pd.DataFrame,
        n: int = 9,
        m1: int = 3,
        m2: int = 3
    ) -> pd.DataFrame:
        """
        计算KDJ指标 (Stochastic Oscillator)

        Args:
            df: 包含'high', 'low', 'close'列的DataFrame
            n: RSV周期，默认9
            m1: K值平滑周期，默认3
            m2: D值平滑周期，默认3

        Returns:
            添加了K、D、J列的DataFrame
        """
        df = df.copy()

        # 计算RSV (未成熟随机值)
        low_n = df['low'].rolling(window=n).min()
        high_n = df['high'].rolling(window=n).max()

        df['rsv'] = (df['close'] - low_n) / (high_n - low_n) * 100

        # 计算K值 (RSV的m1日移动平均)
        df['kdj_k'] = df['rsv'].ewm(span=m1, adjust=False).mean()

        # 计算D值 (K值的m2日移动平均)
        df['kdj_d'] = df['kdj_k'].ewm(span=m2, adjust=False).mean()

        # 计算J值 (3K - 2D)
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']

        # 清理中间变量
        df = df.drop(columns=['rsv'])

        return df

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        num_std: float = 2.0
    ) -> pd.DataFrame:
        """
        计算布林带指标 (Bollinger Bands)

        Args:
            df: 包含'close'列的DataFrame
            period: 周期，默认20
            num_std: 标准差倍数，默认2

        Returns:
            添加了BOLL_UPPER、BOLL_MID、BOLL_LOWER列的DataFrame
        """
        df = df.copy()

        # 中轨 = 20日移动平均
        df['boll_mid'] = df['close'].rolling(window=period).mean()

        # 标准差
        std = df['close'].rolling(window=period).std()

        # 上轨 = 中轨 + 2倍标准差
        df['boll_upper'] = df['boll_mid'] + (std * num_std)

        # 下轨 = 中轨 - 2倍标准差
        df['boll_lower'] = df['boll_mid'] - (std * num_std)

        return df

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算ATR指标 (Average True Range) - 用于风险管理

        Args:
            df: 包含'high', 'low', 'close'列的DataFrame
            period: 周期，默认14

        Returns:
            添加了ATR列的DataFrame
        """
        df = df.copy()

        # 计算真实波幅
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # 计算ATR (真实波幅的移动平均)
        df['atr'] = true_range.rolling(window=period).mean()

        return df

    @staticmethod
    def calculate_dmi_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算DMI/ADX指标 (Directional Movement Index / Average Directional Index)

        用于判断趋势强度，适合趋势跟踪策略

        Args:
            df: 包含'high', 'low', 'close'列的DataFrame
            period: 周期，默认14

        Returns:
            添加了+di, -di, adx列的DataFrame
        """
        from .dmi_adx import calculate_dmi_adx_simple
        return calculate_dmi_adx_simple(df, period)

    def calculate_all_indicators(
        self,
        df: pd.DataFrame,
        ma_periods: list = [5, 10, 20, 60],
        include_boll: bool = True,
        include_atr: bool = True,
        include_dmi_adx: bool = True
    ) -> pd.DataFrame:
        """
        一次性计算所有技术指标

        Args:
            df: 股票数据DataFrame，需包含['open', 'high', 'low', 'close', 'volume']
            ma_periods: MA周期列表
            include_boll: 是否包含布林带
            include_atr: 是否包含ATR
            include_dmi_adx: 是否包含DMI/ADX (趋势强度指标)

        Returns:
            添加了所有指标的DataFrame
        """
        logger.info("开始计算技术指标...")

        # 确保数据按日期排序
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)

        # 计算各项指标
        df = self.calculate_ma(df, periods=ma_periods)
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df)
        df = self.calculate_kdj(df)

        if include_boll:
            df = self.calculate_bollinger_bands(df)

        if include_atr:
            df = self.calculate_atr(df)

        if include_dmi_adx:
            df = self.calculate_dmi_adx(df)

        logger.info(f"技术指标计算完成，共 {len(df)} 条数据")

        return df

    @staticmethod
    def identify_ma_pattern(df: pd.DataFrame, index: int = -1) -> Dict:
        """
        识别均线排列形态

        Args:
            df: 包含MA指标的DataFrame
            index: 要分析的行索引，默认-1(最新)

        Returns:
            {
                'pattern': '多头排列' / '空头排列' / '均线粘合',
                'price_position': '价格位于均线上方' / '价格位于均线下方',
                'strength': 0-10的强度评分
            }
        """
        if index < 0:
            index = len(df) + index

        row = df.iloc[index]

        # 获取价格和各周期均线
        price = row['close']
        ma5 = row.get('ma5', None)
        ma10 = row.get('ma10', None)
        ma20 = row.get('ma20', None)
        ma60 = row.get('ma60', None)

        mas = [ma for ma in [ma5, ma10, ma20, ma60] if ma is not None]

        if len(mas) < 2:
            return {'pattern': '数据不足', 'price_position': '未知', 'strength': 0}

        # 判断均线排列
        is_bullish = all(mas[i] > mas[i+1] for i in range(len(mas)-1))
        is_bearish = all(mas[i] < mas[i+1] for i in range(len(mas)-1))

        if is_bullish:
            pattern = '完美多头排列' if price > mas[0] else '多头排列(价格回调)'
            strength = 8 if price > mas[0] else 6
        elif is_bearish:
            pattern = '完美空头排列' if price < mas[0] else '空头排列(价格反弹)'
            strength = 2 if price < mas[0] else 4
        else:
            pattern = '均线粘合/交叉'
            strength = 5

        price_position = '价格位于均线上方' if price > mas[0] else '价格位于均线下方'

        return {
            'pattern': pattern,
            'price_position': price_position,
            'strength': strength
        }

    @staticmethod
    def identify_macd_signal(df: pd.DataFrame, index: int = -1) -> Dict:
        """
        识别MACD信号

        Args:
            df: 包含MACD指标的DataFrame
            index: 要分析的行索引

        Returns:
            {
                'signal': '金叉' / '死叉' / '多头' / '空头',
                'position': '零轴上方' / '零轴下方',
                'histogram_trend': '扩大' / '缩小',
                'strength': 0-10的强度评分
            }
        """
        if index < 0:
            index = len(df) + index

        if index < 1:
            return {'signal': '数据不足', 'position': '未知', 'histogram_trend': '未知', 'strength': 0}

        current = df.iloc[index]
        previous = df.iloc[index-1]

        # MACD信号判断
        current_hist = current['macd_histogram']
        prev_hist = previous['macd_histogram']

        if current_hist > 0 and prev_hist <= 0:
            signal = '金叉'
            strength = 9
        elif current_hist < 0 and prev_hist >= 0:
            signal = '死叉'
            strength = 1
        elif current_hist > 0:
            signal = '多头'
            strength = 7
        else:
            signal = '空头'
            strength = 3

        # 零轴位置
        position = '零轴上方' if current['macd'] > 0 else '零轴下方'

        # 柱状图趋势
        histogram_trend = '扩大' if abs(current_hist) > abs(prev_hist) else '缩小'

        return {
            'signal': signal,
            'position': position,
            'histogram_trend': histogram_trend,
            'strength': strength
        }

    @staticmethod
    def identify_rsi_signal(df: pd.DataFrame, index: int = -1) -> Dict:
        """
        识别RSI信号

        Args:
            df: 包含RSI指标的DataFrame
            index: 要分析的行索引

        Returns:
            {
                'signal': '超买' / '超卖' / '中性',
                'value': RSI值,
                'trend': '上升' / '下降',
                'strength': 0-10的强度评分
            }
        """
        if index < 0:
            index = len(df) + index

        if index < 1:
            return {'signal': '数据不足', 'value': 0, 'trend': '未知', 'strength': 0}

        current_rsi = df.iloc[index]['rsi']
        prev_rsi = df.iloc[index-1]['rsi']

        # RSI信号判断
        if current_rsi > 70:
            signal = '超买'
            strength = 2
        elif current_rsi < 30:
            signal = '超卖'
            strength = 8
        elif current_rsi > 50:
            signal = '中性偏多'
            strength = 6
        else:
            signal = '中性偏空'
            strength = 4

        # 趋势
        trend = '上升' if current_rsi > prev_rsi else '下降'

        return {
            'signal': signal,
            'value': float(current_rsi),
            'trend': trend,
            'strength': strength
        }

    @staticmethod
    def identify_kdj_signal(df: pd.DataFrame, index: int = -1) -> Dict:
        """
        识别KDJ信号

        Args:
            df: 包含KDJ指标的DataFrame
            index: 要分析的行索引

        Returns:
            {
                'signal': '金叉' / '死叉' / '超买' / '超卖',
                'k': K值,
                'd': D值,
                'j': J值,
                'strength': 0-10的强度评分
            }
        """
        if index < 0:
            index = len(df) + index

        if index < 1:
            return {'signal': '数据不足', 'k': 0, 'd': 0, 'j': 0, 'strength': 0}

        current = df.iloc[index]
        previous = df.iloc[index-1]

        k = current['kdj_k']
        d = current['kdj_d']
        j = current['kdj_j']

        prev_k = previous['kdj_k']
        prev_d = previous['kdj_d']

        # KDJ信号判断
        if k > d and prev_k <= prev_d and k < 50:
            signal = '低位金叉'
            strength = 9
        elif k < d and prev_k >= prev_d and k > 50:
            signal = '高位死叉'
            strength = 1
        elif j > 100:
            signal = '超买'
            strength = 2
        elif j < 0:
            signal = '超卖'
            strength = 8
        elif k > d:
            signal = '多头'
            strength = 7
        else:
            signal = '空头'
            strength = 3

        return {
            'signal': signal,
            'k': float(k),
            'd': float(d),
            'j': float(j),
            'strength': strength
        }

    @staticmethod
    def identify_dmi_adx_signal(df: pd.DataFrame, index: int = -1) -> Dict:
        """
        识别DMI/ADX趋势强度信号

        Args:
            df: 包含DMI/ADX指标的DataFrame
            index: 要分析的行索引

        Returns:
            {
                'trend_strength': 'very_strong'/'strong'/'medium'/'weak',
                'trend_direction': 'bullish'/'bearish'/'neutral',
                'adx': ADX值,
                '+di': +DI值,
                '-di': -DI值,
                'signal': 描述信号,
                'recommendation': 操作建议,
                'strength': 0-10评分
            }
        """
        from .dmi_adx import DMI_ADX_Calculator
        calculator = DMI_ADX_Calculator()
        return calculator.identify_trend_strength(df, index)


if __name__ == '__main__':
    # 测试代码
    import akshare as ak

    # 获取测试数据
    print("获取测试数据...")
    df = ak.stock_zh_index_daily(symbol='sh000001')
    df = df.tail(100)  # 最近100天

    # 计算指标
    print("\n计算技术指标...")
    calculator = TechnicalIndicators()
    df = calculator.calculate_all_indicators(df)

    # 显示最新指标
    print("\n=== 最新技术指标 ===")
    latest = df.iloc[-1]
    print(f"日期: {latest.get('date', 'N/A')}")
    print(f"收盘价: {latest['close']:.2f}")
    print(f"\nMA指标:")
    print(f"  MA5: {latest.get('ma5', 0):.2f}")
    print(f"  MA10: {latest.get('ma10', 0):.2f}")
    print(f"  MA20: {latest.get('ma20', 0):.2f}")
    print(f"  MA60: {latest.get('ma60', 0):.2f}")

    print(f"\nMACD指标:")
    print(f"  MACD: {latest['macd']:.4f}")
    print(f"  Signal: {latest['macd_signal']:.4f}")
    print(f"  Histogram: {latest['macd_histogram']:.4f}")

    print(f"\nRSI指标:")
    print(f"  RSI(14): {latest['rsi']:.2f}")

    print(f"\nKDJ指标:")
    print(f"  K: {latest['kdj_k']:.2f}")
    print(f"  D: {latest['kdj_d']:.2f}")
    print(f"  J: {latest['kdj_j']:.2f}")

    # 识别信号
    print("\n=== 信号识别 ===")
    ma_signal = calculator.identify_ma_pattern(df)
    print(f"均线形态: {ma_signal['pattern']} (强度: {ma_signal['strength']}/10)")

    macd_signal = calculator.identify_macd_signal(df)
    print(f"MACD信号: {macd_signal['signal']} - {macd_signal['position']} - 柱状图{macd_signal['histogram_trend']}")

    rsi_signal = calculator.identify_rsi_signal(df)
    print(f"RSI信号: {rsi_signal['signal']} (值: {rsi_signal['value']:.2f}, 趋势: {rsi_signal['trend']})")

    kdj_signal = calculator.identify_kdj_signal(df)
    print(f"KDJ信号: {kdj_signal['signal']} (K: {kdj_signal['k']:.2f}, D: {kdj_signal['d']:.2f}, J: {kdj_signal['j']:.2f})")
