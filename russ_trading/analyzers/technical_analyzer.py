#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标分析模块
Technical Analyzer Module

提供量价关系、MACD背离、RSI等技术指标分析

作者: Claude Code
日期: 2025-10-21
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """技术指标分析器"""

    def __init__(self):
        """初始化技术分析器"""
        pass

    def calculate_macd(self, df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
        """
        计算MACD指标

        Args:
            df: 数据DataFrame,需包含'收盘'列
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            包含MACD, Signal, Histogram的DataFrame
        """
        try:
            close = df['收盘']

            # 计算EMA
            ema_fast = close.ewm(span=fast, adjust=False).mean()
            ema_slow = close.ewm(span=slow, adjust=False).mean()

            # MACD线 = 快线 - 慢线
            macd_line = ema_fast - ema_slow

            # 信号线 = MACD的9日EMA
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()

            # 柱状图 = MACD - 信号线
            histogram = macd_line - signal_line

            df['MACD'] = macd_line
            df['Signal'] = signal_line
            df['Histogram'] = histogram

            return df
        except Exception as e:
            logger.error(f"计算MACD失败: {e}")
            return df

    def calculate_rsi(self, df: pd.DataFrame, period=14) -> pd.DataFrame:
        """
        计算RSI指标

        Args:
            df: 数据DataFrame,需包含'收盘'列
            period: RSI周期

        Returns:
            包含RSI的DataFrame
        """
        try:
            close = df['收盘']

            # 计算价格变化
            delta = close.diff()

            # 分离上涨和下跌
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            # 计算RS和RSI
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            df['RSI'] = rsi

            return df
        except Exception as e:
            logger.error(f"计算RSI失败: {e}")
            return df

    def detect_macd_divergence(self, df: pd.DataFrame, window=20) -> Dict:
        """
        检测MACD背离

        Args:
            df: 包含价格和MACD的DataFrame
            window: 检测窗口

        Returns:
            背离信息字典
        """
        try:
            if len(df) < window:
                return {'has_divergence': False}

            recent = df.tail(window)
            close = recent['收盘']
            macd = recent['MACD']

            # 检测顶背离:价格新高,MACD不创新高
            price_high_idx = close.idxmax()
            macd_high_idx = macd.idxmax()

            price_high = close.max()
            macd_high = macd.max()

            # 检测底背离:价格新低,MACD不创新低
            price_low_idx = close.idxmin()
            macd_low_idx = macd.idxmin()

            price_low = close.min()
            macd_low = macd.min()

            # 判断顶背离
            top_divergence = False
            if price_high_idx != macd_high_idx:
                # 价格在后期创新高,但MACD在前期
                if price_high_idx > macd_high_idx:
                    top_divergence = True

            # 判断底背离
            bottom_divergence = False
            if price_low_idx != macd_low_idx:
                # 价格在后期创新低,但MACD在前期
                if price_low_idx > macd_low_idx:
                    bottom_divergence = True

            return {
                'has_divergence': top_divergence or bottom_divergence,
                'top_divergence': top_divergence,
                'bottom_divergence': bottom_divergence,
                'signal': '看跌' if top_divergence else ('看涨' if bottom_divergence else '无明显信号')
            }
        except Exception as e:
            logger.error(f"检测MACD背离失败: {e}")
            return {'has_divergence': False}

    def analyze_volume_price(self, df: pd.DataFrame, window=5) -> Dict:
        """
        分析量价关系

        Args:
            df: 包含价格和成交量的DataFrame
            window: 分析窗口

        Returns:
            量价关系分析结果
        """
        try:
            if len(df) < window:
                return {'status': '数据不足'}

            recent = df.tail(window)

            # 获取最新数据
            latest = recent.iloc[-1]
            prev = recent.iloc[-2]

            price_change = latest['收盘'] - prev['收盘']
            volume_change = latest['成交量'] - prev['成交量']

            # 计算平均成交量
            avg_volume = recent['成交量'].mean()
            volume_ratio = latest['成交量'] / avg_volume if avg_volume > 0 else 1

            # 量价关系判断
            if price_change > 0:
                if volume_ratio > 1.2:  # 成交量放大20%
                    pattern = '放量上涨'
                    signal = '多头强势,上涨动能足'
                    emoji = '📈🔊'
                elif volume_ratio < 0.8:  # 成交量缩小20%
                    pattern = '缩量上涨'
                    signal = '上涨乏力,需警惕'
                    emoji = '📈🔉'
                else:
                    pattern = '温和上涨'
                    signal = '正常上涨'
                    emoji = '📈'
            elif price_change < 0:
                if volume_ratio > 1.2:
                    pattern = '放量下跌'
                    signal = '空头强势,杀跌明显'
                    emoji = '📉🔊'
                elif volume_ratio < 0.8:
                    pattern = '缩量下跌'
                    signal = '抛压减轻,可能企稳'
                    emoji = '📉🔉'
                else:
                    pattern = '温和下跌'
                    signal = '正常回调'
                    emoji = '📉'
            else:
                pattern = '横盘整理'
                signal = '等待方向'
                emoji = '➡️'

            return {
                'pattern': pattern,
                'signal': signal,
                'emoji': emoji,
                'volume_ratio': volume_ratio,
                'price_change_pct': (price_change / prev['收盘'] * 100) if prev['收盘'] > 0 else 0
            }
        except Exception as e:
            logger.error(f"分析量价关系失败: {e}")
            return {'status': '分析失败'}

    def analyze_index(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        综合分析指数技术指标

        Args:
            symbol: 指数代码
            df: 历史数据DataFrame

        Returns:
            综合技术分析结果
        """
        try:
            if df.empty or len(df) < 30:
                return {
                    'symbol': symbol,
                    'status': '数据不足',
                    'has_data': False
                }

            # 计算技术指标
            df = self.calculate_macd(df)
            df = self.calculate_rsi(df)

            # 获取最新值
            latest = df.iloc[-1]

            # MACD分析
            macd_value = latest.get('MACD', 0)
            signal_value = latest.get('Signal', 0)
            histogram = latest.get('Histogram', 0)

            macd_signal = '多头' if histogram > 0 else '空头'

            # RSI分析
            rsi_value = latest.get('RSI', 50)
            if rsi_value > 70:
                rsi_signal = '超买'
                rsi_emoji = '⚠️'
            elif rsi_value < 30:
                rsi_signal = '超卖'
                rsi_emoji = '✅'
            else:
                rsi_signal = '正常'
                rsi_emoji = '➡️'

            # MACD背离检测
            divergence = self.detect_macd_divergence(df)

            # 量价关系
            volume_price = self.analyze_volume_price(df)

            return {
                'symbol': symbol,
                'has_data': True,
                'macd': {
                    'value': float(macd_value),
                    'signal': float(signal_value),
                    'histogram': float(histogram),
                    'trend': macd_signal
                },
                'rsi': {
                    'value': float(rsi_value),
                    'signal': rsi_signal,
                    'emoji': rsi_emoji
                },
                'divergence': divergence,
                'volume_price': volume_price,
                'latest_price': float(latest['收盘']),
                'latest_date': str(latest['日期']) if '日期' in latest else 'Unknown'
            }
        except Exception as e:
            logger.error(f"综合分析指数{symbol}失败: {e}")
            return {
                'symbol': symbol,
                'status': f'分析失败: {e}',
                'has_data': False
            }

    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
        """
        计算移动平均线

        Args:
            df: 数据DataFrame,需包含'收盘'列
            periods: MA周期列表

        Returns:
            包含MA的DataFrame
        """
        try:
            for period in periods:
                df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
            return df
        except Exception as e:
            logger.error(f"计算MA失败: {e}")
            return df

    def calculate_atr(self, df: pd.DataFrame, period=14) -> pd.DataFrame:
        """
        计算ATR (Average True Range) 真实波动幅度

        Args:
            df: 数据DataFrame,需包含'最高','最低','收盘'列
            period: ATR周期

        Returns:
            包含ATR的DataFrame
        """
        try:
            high = df['最高']
            low = df['最低']
            close = df['收盘']
            prev_close = close.shift(1)

            # 计算真实波动范围
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)

            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # 计算ATR
            atr = tr.rolling(window=period).mean()
            df['ATR'] = atr

            return df
        except Exception as e:
            logger.error(f"计算ATR失败: {e}")
            return df

    def calculate_volume_ratio(self, df: pd.DataFrame, period=5) -> pd.DataFrame:
        """
        计算量比

        Args:
            df: 数据DataFrame,需包含'成交量'列
            period: 平均成交量周期

        Returns:
            包含量比的DataFrame
        """
        try:
            avg_volume = df['成交量'].rolling(window=period).mean()
            df['量比'] = df['成交量'] / avg_volume
            return df
        except Exception as e:
            logger.error(f"计算量比失败: {e}")
            return df

    def calculate_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算VWAP (Volume Weighted Average Price) 成交量加权平均价

        Args:
            df: 数据DataFrame,需包含'最高','最低','收盘','成交量'列

        Returns:
            包含VWAP的DataFrame
        """
        try:
            typical_price = (df['最高'] + df['最低'] + df['收盘']) / 3
            df['VWAP'] = (typical_price * df['成交量']).cumsum() / df['成交量'].cumsum()
            return df
        except Exception as e:
            logger.error(f"计算VWAP失败: {e}")
            return df

    def detect_volume_price_divergence(self, df: pd.DataFrame, window=20) -> Dict:
        """
        检测量价背离

        Args:
            df: 包含价格和成交量的DataFrame
            window: 检测窗口

        Returns:
            量价背离信息字典
        """
        try:
            if len(df) < window:
                return {'has_divergence': False}

            recent = df.tail(window)
            close = recent['收盘']
            volume = recent['成交量']

            # 检测价格和成交量的趋势
            price_trend = close.iloc[-1] - close.iloc[0]
            volume_trend = volume.iloc[-1] - volume.iloc[0]

            # 顶背离:价格上涨但成交量下降
            top_divergence = False
            if price_trend > 0 and volume_trend < 0:
                # 进一步确认:检查最近几天的趋势
                recent_price_up = close.iloc[-5:].mean() > close.iloc[:5].mean()
                recent_volume_down = volume.iloc[-5:].mean() < volume.iloc[:5].mean()
                if recent_price_up and recent_volume_down:
                    top_divergence = True

            # 底背离:价格下跌但成交量上升(可能是恐慌性抛售)
            bottom_divergence = False
            if price_trend < 0 and volume_trend > 0:
                recent_price_down = close.iloc[-5:].mean() < close.iloc[:5].mean()
                recent_volume_up = volume.iloc[-5:].mean() > volume.iloc[:5].mean()
                if recent_price_down and recent_volume_up:
                    bottom_divergence = True

            return {
                'has_divergence': top_divergence or bottom_divergence,
                'top_divergence': top_divergence,
                'bottom_divergence': bottom_divergence,
                'signal': '看跌(量价背离)' if top_divergence else ('看涨(放量杀跌)' if bottom_divergence else '无量价背离')
            }
        except Exception as e:
            logger.error(f"检测量价背离失败: {e}")
            return {'has_divergence': False}

    def get_enhanced_signals(self, df: pd.DataFrame) -> Dict:
        """
        获取增强型技术信号 (机构级7指标)

        Args:
            df: 历史数据DataFrame

        Returns:
            包含所有新增指标的字典
        """
        try:
            if df.empty or len(df) < 60:
                return {'status': '数据不足', 'has_data': False}

            # 计算所有新指标
            df = self.calculate_rsi(df)
            df = self.calculate_ma(df, [5, 10, 20, 60])
            df = self.calculate_atr(df)
            df = self.calculate_volume_ratio(df)
            df = self.calculate_vwap(df)

            latest = df.iloc[-1]
            current_price = latest['收盘']

            # 1. RSI信号
            rsi_value = latest.get('RSI', 50)
            if rsi_value > 70:
                rsi_signal = '超买'
                rsi_emoji = '⚠️'
            elif rsi_value < 30:
                rsi_signal = '超卖'
                rsi_emoji = '✅'
            else:
                rsi_signal = '正常'
                rsi_emoji = '➡️'

            # 2. 量比信号
            volume_ratio = latest.get('量比', 1.0)
            if volume_ratio > 2.0:
                vol_signal = '放量'
                vol_emoji = '🔊'
            elif volume_ratio < 0.5:
                vol_signal = '缩量'
                vol_emoji = '🔉'
            else:
                vol_signal = '正常'
                vol_emoji = '➡️'

            # 3. 均线系统
            ma20 = latest.get('MA20', current_price)
            ma60 = latest.get('MA60', current_price)
            ma_deviation_20 = ((current_price - ma20) / ma20 * 100) if ma20 > 0 else 0
            ma_deviation_60 = ((current_price - ma60) / ma60 * 100) if ma60 > 0 else 0

            if current_price > ma20 > ma60:
                ma_signal = '多头排列'
                ma_emoji = '✅'
            elif current_price < ma20 < ma60:
                ma_signal = '空头排列'
                ma_emoji = '⚠️'
            else:
                ma_signal = '震荡'
                ma_emoji = '➡️'

            # 4. ATR止损位
            atr_value = latest.get('ATR', 0)
            stop_loss = current_price - 2 * atr_value
            take_profit = current_price + 3 * atr_value

            # 5. VWAP信号
            vwap = latest.get('VWAP', current_price)
            vwap_diff = ((current_price - vwap) / vwap * 100) if vwap > 0 else 0

            if current_price > vwap:
                vwap_signal = '强势(价格>VWAP)'
                vwap_emoji = '✅'
            else:
                vwap_signal = '弱势(价格<VWAP)'
                vwap_emoji = '⚠️'

            # 6. 量价背离
            vp_divergence = self.detect_volume_price_divergence(df)

            return {
                'has_data': True,
                'rsi': {
                    'value': float(rsi_value),
                    'signal': rsi_signal,
                    'emoji': rsi_emoji
                },
                'volume_ratio': {
                    'value': float(volume_ratio),
                    'signal': vol_signal,
                    'emoji': vol_emoji
                },
                'ma': {
                    'ma20': float(ma20),
                    'ma60': float(ma60),
                    'deviation_20': float(ma_deviation_20),
                    'deviation_60': float(ma_deviation_60),
                    'signal': ma_signal,
                    'emoji': ma_emoji
                },
                'atr': {
                    'value': float(atr_value),
                    'stop_loss': float(stop_loss),
                    'take_profit': float(take_profit),
                    'risk_reward': '1:1.5'
                },
                'vwap': {
                    'value': float(vwap),
                    'diff_pct': float(vwap_diff),
                    'signal': vwap_signal,
                    'emoji': vwap_emoji
                },
                'volume_price_divergence': vp_divergence,
                'latest_price': float(current_price)
            }
        except Exception as e:
            logger.error(f"获取增强型技术信号失败: {e}")
            return {'status': f'分析失败: {e}', 'has_data': False}

    def format_enhanced_signals(self, signals: Dict) -> str:
        """
        格式化增强型技术信号报告

        Args:
            signals: 增强型技术信号字典

        Returns:
            格式化的Markdown文本
        """
        if not signals.get('has_data'):
            return "数据不足,无法分析\n"

        lines = []
        lines.append("**机构级技术指标**:")

        # 1. RSI
        rsi = signals.get('rsi', {})
        if 'value' in rsi:
            lines.append(f"- **RSI(14)**: {rsi['emoji']} {rsi['value']:.1f} ({rsi['signal']})")

        # 2. 量比
        vol = signals.get('volume_ratio', {})
        if 'value' in vol:
            lines.append(f"- **量比**: {vol['emoji']} {vol['value']:.2f}x ({vol['signal']})")

        # 3. 均线系统
        ma = signals.get('ma', {})
        if 'ma20' in ma:
            lines.append(f"- **均线**: {ma['emoji']} {ma['signal']}")
            lines.append(f"  - MA20: {ma['ma20']:.2f} (乖离率: {ma['deviation_20']:+.2f}%)")
            lines.append(f"  - MA60: {ma['ma60']:.2f} (乖离率: {ma['deviation_60']:+.2f}%)")

        # 4. ATR止损
        atr = signals.get('atr', {})
        if 'value' in atr:
            lines.append(f"- **ATR止损**: {atr['value']:.4f}")
            lines.append(f"  - 建议止损: {atr['stop_loss']:.2f}")
            lines.append(f"  - 建议止盈: {atr['take_profit']:.2f} (风险收益比{atr['risk_reward']})")

        # 5. VWAP
        vwap = signals.get('vwap', {})
        if 'value' in vwap:
            lines.append(f"- **VWAP**: {vwap['emoji']} {vwap['value']:.2f} ({vwap['signal']})")
            lines.append(f"  - 价格偏离VWAP: {vwap['diff_pct']:+.2f}%")

        # 6. 量价背离
        vp_div = signals.get('volume_price_divergence', {})
        if vp_div.get('has_divergence'):
            if vp_div.get('top_divergence'):
                lines.append(f"- **⚠️ 量价背离**: 价格上涨但成交量下降,上涨动能不足")
            if vp_div.get('bottom_divergence'):
                lines.append(f"- **✅ 量价背离**: 价格下跌但成交量放大,可能是恐慌性抛售")

        return '\n'.join(lines)

    def format_technical_report(self, analysis: Dict) -> str:
        """
        格式化技术分析报告

        Args:
            analysis: 技术分析结果

        Returns:
            格式化的Markdown文本
        """
        if not analysis.get('has_data'):
            return f"**{analysis['symbol']}**: 数据不足\n"

        lines = []

        # 量价关系
        vp = analysis.get('volume_price', {})
        if 'pattern' in vp:
            lines.append(f"- **量价关系**: {vp['emoji']} {vp['pattern']} - {vp['signal']}")

        # MACD
        macd = analysis.get('macd', {})
        if 'trend' in macd:
            lines.append(f"- **MACD**: {macd['trend']} (柱状图: {macd.get('histogram', 0):.2f})")

        # RSI
        rsi = analysis.get('rsi', {})
        if 'value' in rsi:
            lines.append(f"- **RSI**: {rsi['emoji']} {rsi['value']:.1f} ({rsi['signal']})")

        # 背离
        div = analysis.get('divergence', {})
        if div.get('has_divergence'):
            if div.get('top_divergence'):
                lines.append(f"- **⚠️ 顶背离**: 价格新高但MACD不创新高,看跌信号")
            if div.get('bottom_divergence'):
                lines.append(f"- **✅ 底背离**: 价格新低但MACD不创新低,看涨信号")

        return '\n'.join(lines)
