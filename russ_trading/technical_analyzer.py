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
