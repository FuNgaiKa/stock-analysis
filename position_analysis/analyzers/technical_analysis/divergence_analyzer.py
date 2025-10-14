#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背离分析器 (Divergence Analyzer)
支持量价背离、MACD背驰、RSI背离等多种背离检测
适用于A股、H股、美股市场

背离原理:
- 顶背离: 价格创新高，指标未创新高 → 上涨动能衰竭，警惕回调
- 底背离: 价格创新低，指标未创新低 → 下跌动能衰竭，可能反弹

作者: Claude Code
日期: 2025-10-14
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DivergenceSignal:
    """背离信号数据类"""
    divergence_type: str  # 'bullish'(底背离) or 'bearish'(顶背离)
    indicator_name: str   # 'volume', 'macd', 'rsi'
    strength: int         # 强度评分 0-100
    price_points: List[Tuple[str, float]]  # [(日期, 价格), ...]
    indicator_points: List[Tuple[str, float]]  # [(日期, 指标值), ...]
    description: str      # 描述信息
    confidence: str       # '高', '中', '低'


class DivergenceAnalyzer:
    """
    背离分析器

    功能:
    1. 量价背离检测
    2. MACD背驰检测
    3. RSI背离检测
    4. 综合背离分析
    """

    def __init__(
        self,
        peak_valley_window: int = 5,
        lookback_period: int = 60,
        min_peak_distance: int = 5
    ):
        """
        初始化背离分析器

        Args:
            peak_valley_window: 峰谷识别窗口，默认5天
            lookback_period: 背离检测周期，默认60天
            min_peak_distance: 相邻峰谷最小间隔，默认5天
        """
        self.peak_valley_window = peak_valley_window
        self.lookback_period = lookback_period
        self.min_peak_distance = min_peak_distance
        logger.info("背离分析器初始化完成")

    def _find_peaks_valleys(
        self,
        series: pd.Series,
        window: int = None
    ) -> Tuple[List[int], List[int]]:
        """
        识别序列中的峰和谷

        Args:
            series: 数据序列
            window: 识别窗口大小

        Returns:
            (peaks, valleys) - 峰和谷的索引列表
        """
        if window is None:
            window = self.peak_valley_window

        peaks = []
        valleys = []

        for i in range(window, len(series) - window):
            # 检查是否为峰值
            is_peak = True
            is_valley = True

            for j in range(1, window + 1):
                if series.iloc[i] <= series.iloc[i - j] or series.iloc[i] <= series.iloc[i + j]:
                    is_peak = False
                if series.iloc[i] >= series.iloc[i - j] or series.iloc[i] >= series.iloc[i + j]:
                    is_valley = False

            if is_peak:
                # 确保与上一个峰值有足够距离
                if not peaks or (i - peaks[-1]) >= self.min_peak_distance:
                    peaks.append(i)

            if is_valley:
                # 确保与上一个谷值有足够距离
                if not valleys or (i - valleys[-1]) >= self.min_peak_distance:
                    valleys.append(i)

        return peaks, valleys

    def _calculate_divergence_strength(
        self,
        price_change_pct: float,
        indicator_change_pct: float,
        divergence_type: str
    ) -> int:
        """
        计算背离强度评分

        Args:
            price_change_pct: 价格变化百分比
            indicator_change_pct: 指标变化百分比
            divergence_type: 'bullish' or 'bearish'

        Returns:
            评分 0-100
        """
        # 背离幅度: 价格和指标变化方向相反的程度
        if divergence_type == 'bearish':
            # 顶背离: 价格上涨，指标下跌或涨幅小
            divergence_magnitude = abs(price_change_pct - indicator_change_pct)
        else:
            # 底背离: 价格下跌，指标上涨或跌幅小
            divergence_magnitude = abs(price_change_pct - indicator_change_pct)

        # 基础分数: 背离幅度越大，分数越高
        base_score = min(divergence_magnitude * 2, 70)

        # 方向一致性加分
        if divergence_type == 'bearish':
            if price_change_pct > 0 and indicator_change_pct < 0:
                base_score += 20  # 价格上涨但指标下跌，强背离
            elif price_change_pct > 0 and indicator_change_pct < price_change_pct * 0.5:
                base_score += 10  # 指标涨幅明显小于价格
        else:
            if price_change_pct < 0 and indicator_change_pct > 0:
                base_score += 20  # 价格下跌但指标上涨，强背离
            elif price_change_pct < 0 and abs(indicator_change_pct) < abs(price_change_pct) * 0.5:
                base_score += 10  # 指标跌幅明显小于价格

        return int(min(base_score, 100))

    def detect_volume_price_divergence(
        self,
        df: pd.DataFrame,
        price_col: str = 'close',
        volume_col: str = 'volume'
    ) -> Dict:
        """
        检测量价背离

        Args:
            df: OHLCV数据
            price_col: 价格列名
            volume_col: 成交量列名

        Returns:
            量价背离分析结果
        """
        if df.empty or len(df) < self.lookback_period:
            return {'error': '数据不足'}

        try:
            # 只取最近的数据
            df_recent = df.tail(self.lookback_period).copy()

            # 识别价格和成交量的峰谷
            price_peaks, price_valleys = self._find_peaks_valleys(df_recent[price_col])
            volume_peaks, volume_valleys = self._find_peaks_valleys(df_recent[volume_col])

            result = {
                'has_divergence': False,
                'signals': []
            }

            # 检测顶背离 (价格新高，成交量未创新高)
            if len(price_peaks) >= 2:
                # 取最近两个价格高点
                recent_price_peaks = price_peaks[-2:]
                peak1_idx, peak2_idx = recent_price_peaks

                price1 = df_recent[price_col].iloc[peak1_idx]
                price2 = df_recent[price_col].iloc[peak2_idx]

                # 价格创新高
                if price2 > price1:
                    # 找到对应时间段的成交量高点
                    vol_peaks_in_range = [p for p in volume_peaks if peak1_idx <= p <= peak2_idx]

                    if vol_peaks_in_range:
                        # 比较成交量
                        vol1 = df_recent[volume_col].iloc[peak1_idx]
                        vol2_idx = vol_peaks_in_range[-1]
                        vol2 = df_recent[volume_col].iloc[vol2_idx]

                        if vol2 < vol1 * 0.9:  # 成交量明显萎缩
                            price_change_pct = (price2 - price1) / price1 * 100
                            vol_change_pct = (vol2 - vol1) / vol1 * 100

                            strength = self._calculate_divergence_strength(
                                price_change_pct, vol_change_pct, 'bearish'
                            )

                            signal = DivergenceSignal(
                                divergence_type='bearish',
                                indicator_name='volume',
                                strength=strength,
                                price_points=[
                                    (df_recent.index[peak1_idx].strftime('%Y-%m-%d'), float(price1)),
                                    (df_recent.index[peak2_idx].strftime('%Y-%m-%d'), float(price2))
                                ],
                                indicator_points=[
                                    (df_recent.index[peak1_idx].strftime('%Y-%m-%d'), float(vol1)),
                                    (df_recent.index[vol2_idx].strftime('%Y-%m-%d'), float(vol2))
                                ],
                                description=f'量价顶背离: 价格上涨{price_change_pct:.1f}%，成交量下降{abs(vol_change_pct):.1f}%',
                                confidence='高' if strength >= 80 else '中' if strength >= 60 else '低'
                            )

                            result['has_divergence'] = True
                            result['signals'].append(signal)

            # 检测底背离 (价格新低，成交量未创新低)
            if len(price_valleys) >= 2:
                # 取最近两个价格低点
                recent_price_valleys = price_valleys[-2:]
                valley1_idx, valley2_idx = recent_price_valleys

                price1 = df_recent[price_col].iloc[valley1_idx]
                price2 = df_recent[price_col].iloc[valley2_idx]

                # 价格创新低
                if price2 < price1:
                    # 找到对应时间段的成交量低点
                    vol_valleys_in_range = [v for v in volume_valleys if valley1_idx <= v <= valley2_idx]

                    if vol_valleys_in_range:
                        # 比较成交量
                        vol1 = df_recent[volume_col].iloc[valley1_idx]
                        vol2_idx = vol_valleys_in_range[-1]
                        vol2 = df_recent[volume_col].iloc[vol2_idx]

                        if vol2 > vol1 * 1.1:  # 成交量反而放大
                            price_change_pct = (price2 - price1) / price1 * 100
                            vol_change_pct = (vol2 - vol1) / vol1 * 100

                            strength = self._calculate_divergence_strength(
                                price_change_pct, vol_change_pct, 'bullish'
                            )

                            signal = DivergenceSignal(
                                divergence_type='bullish',
                                indicator_name='volume',
                                strength=strength,
                                price_points=[
                                    (df_recent.index[valley1_idx].strftime('%Y-%m-%d'), float(price1)),
                                    (df_recent.index[valley2_idx].strftime('%Y-%m-%d'), float(price2))
                                ],
                                indicator_points=[
                                    (df_recent.index[valley1_idx].strftime('%Y-%m-%d'), float(vol1)),
                                    (df_recent.index[vol2_idx].strftime('%Y-%m-%d'), float(vol2))
                                ],
                                description=f'量价底背离: 价格下跌{abs(price_change_pct):.1f}%，成交量反增{vol_change_pct:.1f}%',
                                confidence='高' if strength >= 80 else '中' if strength >= 60 else '低'
                            )

                            result['has_divergence'] = True
                            result['signals'].append(signal)

            return result

        except Exception as e:
            logger.error(f"量价背离检测失败: {str(e)}")
            return {'error': str(e)}

    def detect_macd_divergence(
        self,
        df: pd.DataFrame,
        price_col: str = 'close',
        use_histogram: bool = True
    ) -> Dict:
        """
        检测MACD背驰

        Args:
            df: OHLCV数据
            price_col: 价格列名
            use_histogram: 是否使用MACD柱状图（True）还是DIF线（False）

        Returns:
            MACD背驰分析结果
        """
        if df.empty or len(df) < self.lookback_period:
            return {'error': '数据不足'}

        try:
            df_recent = df.tail(self.lookback_period).copy()

            # 计算MACD
            if 'macd_histogram' not in df_recent.columns or 'macd' not in df_recent.columns:
                from trading_strategies.signal_generators.technical_indicators import TechnicalIndicators
                calc = TechnicalIndicators()
                df_recent = calc.calculate_macd(df_recent)

            # 选择使用柱状图还是DIF线
            macd_col = 'macd_histogram' if use_histogram else 'macd'

            # 识别价格和MACD的峰谷
            price_peaks, price_valleys = self._find_peaks_valleys(df_recent[price_col])
            macd_peaks, macd_valleys = self._find_peaks_valleys(df_recent[macd_col])

            result = {
                'has_divergence': False,
                'signals': []
            }

            # 检测顶背驰
            if len(price_peaks) >= 2 and len(macd_peaks) >= 2:
                price_peak1_idx, price_peak2_idx = price_peaks[-2:]

                price1 = df_recent[price_col].iloc[price_peak1_idx]
                price2 = df_recent[price_col].iloc[price_peak2_idx]

                # 价格创新高
                if price2 > price1:
                    # 找到对应的MACD高点
                    macd_peaks_in_range = [p for p in macd_peaks if price_peak1_idx - 10 <= p <= price_peak2_idx + 10]

                    if len(macd_peaks_in_range) >= 2:
                        macd_peak1_idx = macd_peaks_in_range[-2]
                        macd_peak2_idx = macd_peaks_in_range[-1]

                        macd1 = df_recent[macd_col].iloc[macd_peak1_idx]
                        macd2 = df_recent[macd_col].iloc[macd_peak2_idx]

                        # MACD未创新高
                        if macd2 < macd1 * 0.9:
                            price_change_pct = (price2 - price1) / price1 * 100
                            macd_change_pct = (macd2 - macd1) / abs(macd1) * 100 if macd1 != 0 else 0

                            strength = self._calculate_divergence_strength(
                                price_change_pct, macd_change_pct, 'bearish'
                            )

                            signal = DivergenceSignal(
                                divergence_type='bearish',
                                indicator_name='macd',
                                strength=strength,
                                price_points=[
                                    (df_recent.index[price_peak1_idx].strftime('%Y-%m-%d'), float(price1)),
                                    (df_recent.index[price_peak2_idx].strftime('%Y-%m-%d'), float(price2))
                                ],
                                indicator_points=[
                                    (df_recent.index[macd_peak1_idx].strftime('%Y-%m-%d'), float(macd1)),
                                    (df_recent.index[macd_peak2_idx].strftime('%Y-%m-%d'), float(macd2))
                                ],
                                description=f'MACD顶背驰: 价格上涨{price_change_pct:.1f}%，MACD动能衰减',
                                confidence='高' if strength >= 80 else '中' if strength >= 60 else '低'
                            )

                            result['has_divergence'] = True
                            result['signals'].append(signal)

            # 检测底背驰
            if len(price_valleys) >= 2 and len(macd_valleys) >= 2:
                price_valley1_idx, price_valley2_idx = price_valleys[-2:]

                price1 = df_recent[price_col].iloc[price_valley1_idx]
                price2 = df_recent[price_col].iloc[price_valley2_idx]

                # 价格创新低
                if price2 < price1:
                    # 找到对应的MACD低点
                    macd_valleys_in_range = [v for v in macd_valleys if price_valley1_idx - 10 <= v <= price_valley2_idx + 10]

                    if len(macd_valleys_in_range) >= 2:
                        macd_valley1_idx = macd_valleys_in_range[-2]
                        macd_valley2_idx = macd_valleys_in_range[-1]

                        macd1 = df_recent[macd_col].iloc[macd_valley1_idx]
                        macd2 = df_recent[macd_col].iloc[macd_valley2_idx]

                        # MACD未创新低（绝对值变小）
                        if abs(macd2) < abs(macd1) * 0.9:
                            price_change_pct = (price2 - price1) / price1 * 100
                            macd_change_pct = (macd2 - macd1) / abs(macd1) * 100 if macd1 != 0 else 0

                            strength = self._calculate_divergence_strength(
                                price_change_pct, macd_change_pct, 'bullish'
                            )

                            signal = DivergenceSignal(
                                divergence_type='bullish',
                                indicator_name='macd',
                                strength=strength,
                                price_points=[
                                    (df_recent.index[price_valley1_idx].strftime('%Y-%m-%d'), float(price1)),
                                    (df_recent.index[price_valley2_idx].strftime('%Y-%m-%d'), float(price2))
                                ],
                                indicator_points=[
                                    (df_recent.index[macd_valley1_idx].strftime('%Y-%m-%d'), float(macd1)),
                                    (df_recent.index[macd_valley2_idx].strftime('%Y-%m-%d'), float(macd2))
                                ],
                                description=f'MACD底背驰: 价格下跌{abs(price_change_pct):.1f}%，MACD下跌动能减弱',
                                confidence='高' if strength >= 80 else '中' if strength >= 60 else '低'
                            )

                            result['has_divergence'] = True
                            result['signals'].append(signal)

            return result

        except Exception as e:
            logger.error(f"MACD背驰检测失败: {str(e)}")
            return {'error': str(e)}

    def detect_rsi_divergence(
        self,
        df: pd.DataFrame,
        price_col: str = 'close',
        rsi_period: int = 14
    ) -> Dict:
        """
        检测RSI背离

        Args:
            df: OHLCV数据
            price_col: 价格列名
            rsi_period: RSI周期

        Returns:
            RSI背离分析结果
        """
        if df.empty or len(df) < self.lookback_period:
            return {'error': '数据不足'}

        try:
            df_recent = df.tail(self.lookback_period).copy()

            # 计算RSI
            if 'rsi' not in df_recent.columns:
                from trading_strategies.signal_generators.technical_indicators import TechnicalIndicators
                calc = TechnicalIndicators()
                df_recent = calc.calculate_rsi(df_recent, period=rsi_period)

            # 识别价格和RSI的峰谷
            price_peaks, price_valleys = self._find_peaks_valleys(df_recent[price_col])
            rsi_peaks, rsi_valleys = self._find_peaks_valleys(df_recent['rsi'])

            result = {
                'has_divergence': False,
                'signals': []
            }

            # 检测顶背离
            if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
                price_peak1_idx, price_peak2_idx = price_peaks[-2:]

                price1 = df_recent[price_col].iloc[price_peak1_idx]
                price2 = df_recent[price_col].iloc[price_peak2_idx]

                # 价格创新高
                if price2 > price1:
                    # 找到对应的RSI高点
                    rsi_peaks_in_range = [p for p in rsi_peaks if price_peak1_idx - 10 <= p <= price_peak2_idx + 10]

                    if len(rsi_peaks_in_range) >= 2:
                        rsi_peak1_idx = rsi_peaks_in_range[-2]
                        rsi_peak2_idx = rsi_peaks_in_range[-1]

                        rsi1 = df_recent['rsi'].iloc[rsi_peak1_idx]
                        rsi2 = df_recent['rsi'].iloc[rsi_peak2_idx]

                        # RSI未创新高
                        if rsi2 < rsi1 - 3:  # RSI下降超过3个点
                            price_change_pct = (price2 - price1) / price1 * 100
                            rsi_change = rsi2 - rsi1

                            strength = self._calculate_divergence_strength(
                                price_change_pct, rsi_change, 'bearish'
                            )

                            signal = DivergenceSignal(
                                divergence_type='bearish',
                                indicator_name='rsi',
                                strength=strength,
                                price_points=[
                                    (df_recent.index[price_peak1_idx].strftime('%Y-%m-%d'), float(price1)),
                                    (df_recent.index[price_peak2_idx].strftime('%Y-%m-%d'), float(price2))
                                ],
                                indicator_points=[
                                    (df_recent.index[rsi_peak1_idx].strftime('%Y-%m-%d'), float(rsi1)),
                                    (df_recent.index[rsi_peak2_idx].strftime('%Y-%m-%d'), float(rsi2))
                                ],
                                description=f'RSI顶背离: 价格上涨{price_change_pct:.1f}%，RSI从{rsi1:.1f}降至{rsi2:.1f}',
                                confidence='高' if strength >= 80 else '中' if strength >= 60 else '低'
                            )

                            result['has_divergence'] = True
                            result['signals'].append(signal)

            # 检测底背离
            if len(price_valleys) >= 2 and len(rsi_valleys) >= 2:
                price_valley1_idx, price_valley2_idx = price_valleys[-2:]

                price1 = df_recent[price_col].iloc[price_valley1_idx]
                price2 = df_recent[price_col].iloc[price_valley2_idx]

                # 价格创新低
                if price2 < price1:
                    # 找到对应的RSI低点
                    rsi_valleys_in_range = [v for v in rsi_valleys if price_valley1_idx - 10 <= v <= price_valley2_idx + 10]

                    if len(rsi_valleys_in_range) >= 2:
                        rsi_valley1_idx = rsi_valleys_in_range[-2]
                        rsi_valley2_idx = rsi_valleys_in_range[-1]

                        rsi1 = df_recent['rsi'].iloc[rsi_valley1_idx]
                        rsi2 = df_recent['rsi'].iloc[rsi_valley2_idx]

                        # RSI未创新低
                        if rsi2 > rsi1 + 3:  # RSI上升超过3个点
                            price_change_pct = (price2 - price1) / price1 * 100
                            rsi_change = rsi2 - rsi1

                            strength = self._calculate_divergence_strength(
                                price_change_pct, rsi_change, 'bullish'
                            )

                            signal = DivergenceSignal(
                                divergence_type='bullish',
                                indicator_name='rsi',
                                strength=strength,
                                price_points=[
                                    (df_recent.index[price_valley1_idx].strftime('%Y-%m-%d'), float(price1)),
                                    (df_recent.index[price_valley2_idx].strftime('%Y-%m-%d'), float(price2))
                                ],
                                indicator_points=[
                                    (df_recent.index[rsi_valley1_idx].strftime('%Y-%m-%d'), float(rsi1)),
                                    (df_recent.index[rsi_valley2_idx].strftime('%Y-%m-%d'), float(rsi2))
                                ],
                                description=f'RSI底背离: 价格下跌{abs(price_change_pct):.1f}%，RSI从{rsi1:.1f}升至{rsi2:.1f}',
                                confidence='高' if strength >= 80 else '中' if strength >= 60 else '低'
                            )

                            result['has_divergence'] = True
                            result['signals'].append(signal)

            return result

        except Exception as e:
            logger.error(f"RSI背离检测失败: {str(e)}")
            return {'error': str(e)}

    def comprehensive_analysis(
        self,
        df: pd.DataFrame,
        symbol: str = "",
        market: str = "CN"
    ) -> Dict:
        """
        综合背离分析

        Args:
            df: OHLCV数据（已标准化为小写列名）
            symbol: 股票/指数代码
            market: 市场标识 ('CN', 'HK', 'US')

        Returns:
            综合分析结果
        """
        logger.info(f"开始综合背离分析: {symbol} ({market})")

        result = {
            'symbol': symbol,
            'market': market,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'has_any_divergence': False,
            'summary': [],
            'details': {}
        }

        # 1. 量价背离检测
        volume_div = self.detect_volume_price_divergence(df)
        result['details']['volume_price'] = volume_div

        if volume_div.get('has_divergence'):
            result['has_any_divergence'] = True
            for signal in volume_div['signals']:
                result['summary'].append({
                    'type': '量价背离',
                    'direction': '顶背离' if signal.divergence_type == 'bearish' else '底背离',
                    'strength': signal.strength,
                    'confidence': signal.confidence,
                    'description': signal.description
                })

        # 2. MACD背驰检测
        macd_div = self.detect_macd_divergence(df)
        result['details']['macd'] = macd_div

        if macd_div.get('has_divergence'):
            result['has_any_divergence'] = True
            for signal in macd_div['signals']:
                result['summary'].append({
                    'type': 'MACD背驰',
                    'direction': '顶背驰' if signal.divergence_type == 'bearish' else '底背驰',
                    'strength': signal.strength,
                    'confidence': signal.confidence,
                    'description': signal.description
                })

        # 3. RSI背离检测
        rsi_div = self.detect_rsi_divergence(df)
        result['details']['rsi'] = rsi_div

        if rsi_div.get('has_divergence'):
            result['has_any_divergence'] = True
            for signal in rsi_div['signals']:
                result['summary'].append({
                    'type': 'RSI背离',
                    'direction': '顶背离' if signal.divergence_type == 'bearish' else '底背离',
                    'strength': signal.strength,
                    'confidence': signal.confidence,
                    'description': signal.description
                })

        # 4. 综合评估
        if result['has_any_divergence']:
            # 统计背离信号
            bearish_count = sum(1 for s in result['summary'] if s['direction'] in ['顶背离', '顶背驰'])
            bullish_count = sum(1 for s in result['summary'] if s['direction'] in ['底背离', '底背驰'])

            avg_strength = sum(s['strength'] for s in result['summary']) / len(result['summary'])

            if bearish_count > bullish_count:
                overall = '看跌'
                advice = '多个顶背离信号出现，上涨动能衰竭，建议谨慎或减仓'
            elif bullish_count > bearish_count:
                overall = '看涨'
                advice = '多个底背离信号出现，下跌动能衰竭，可能迎来反弹'
            else:
                overall = '中性'
                advice = '背离信号冲突，建议继续观察'

            result['overall_assessment'] = {
                'signal': overall,
                'strength': int(avg_strength),
                'total_signals': len(result['summary']),
                'bearish_signals': bearish_count,
                'bullish_signals': bullish_count,
                'advice': advice
            }
        else:
            result['overall_assessment'] = {
                'signal': '无明显背离',
                'advice': '暂无背离信号，价格与技术指标配合良好'
            }

        logger.info(f"{symbol} 综合背离分析完成")
        return result


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    标准化DataFrame列名为小写
    适配不同市场的数据格式
    """
    df = df.copy()

    # 常见列名映射
    column_mapping = {
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume',
        'latest': 'close'
    }

    # 重命名列
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})

    return df


if __name__ == '__main__':
    """测试代码"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("背离分析器测试")
    print("=" * 80)

    # 测试用例在后续添加
    print("\n✅ 背离分析器模块加载成功")
    print("支持的功能:")
    print("  1. 量价背离检测")
    print("  2. MACD背驰检测")
    print("  3. RSI背离检测")
    print("  4. 综合背离分析")
    print("\n适用市场: A股、H股、美股")
