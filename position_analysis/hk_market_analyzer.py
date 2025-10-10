#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场分析器
提供港股指数、个股、资金流向、AH股溢价等综合分析
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, List
from data_sources.hkstock_source import HKStockDataSource

logger = logging.getLogger(__name__)


class HKMarketAnalyzer:
    """港股市场分析器"""

    def __init__(self):
        self.data_source = HKStockDataSource()
        logger.info("港股市场分析器初始化完成")

    def analyze_index_trend(self, symbol: str = "HSI", lookback_days: int = 252) -> Dict:
        """
        分析指数趋势

        Args:
            symbol: 指数代码 (HSI/HSCEI/HSTECH)
            lookback_days: 回溯天数

        Returns:
            趋势分析结果
        """
        try:
            df = self.data_source.get_hk_index_daily(symbol)

            if df.empty:
                return {'error': '数据获取失败'}

            # 只取最近N天
            df_recent = df.tail(lookback_days)

            latest = df_recent.iloc[-1]
            prev = df_recent.iloc[-2] if len(df_recent) > 1 else latest

            # 计算技术指标
            df_recent['ma20'] = df_recent['close'].rolling(20).mean()
            df_recent['ma60'] = df_recent['close'].rolling(60).mean()
            df_recent['ma120'] = df_recent['close'].rolling(120).mean()

            # RSI
            delta = df_recent['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # KDJ 指标
            kdj_period = 9
            kdj_k_smooth = 3
            kdj_d_smooth = 3

            # 计算 RSV (未成熟随机值)
            low_min = df_recent['low'].rolling(kdj_period).min()
            high_max = df_recent['high'].rolling(kdj_period).max()
            rsv = (df_recent['close'] - low_min) / (high_max - low_min) * 100
            rsv = rsv.fillna(50)  # 初始值设为50

            # 计算 K 值 (RSV 的移动平均)
            kdj_k = rsv.ewm(alpha=1/kdj_k_smooth, adjust=False).mean()

            # 计算 D 值 (K 值的移动平均)
            kdj_d = kdj_k.ewm(alpha=1/kdj_d_smooth, adjust=False).mean()

            # 计算 J 值 (3K - 2D)
            kdj_j = 3 * kdj_k - 2 * kdj_d

            # KDJ 信号判断
            if len(df_recent) >= 2:
                prev_k = kdj_k.iloc[-2]
                prev_d = kdj_d.iloc[-2]
                curr_k = kdj_k.iloc[-1]
                curr_d = kdj_d.iloc[-1]
                curr_j = kdj_j.iloc[-1]

                # 金叉/死叉判断
                if prev_k <= prev_d and curr_k > curr_d:
                    if curr_k < 20:
                        kdj_signal = "低位金叉"
                    else:
                        kdj_signal = "金叉"
                elif prev_k >= prev_d and curr_k < curr_d:
                    if curr_k > 80:
                        kdj_signal = "高位死叉"
                    else:
                        kdj_signal = "死叉"
                elif curr_k > 80 and curr_d > 80:
                    kdj_signal = "超买"
                elif curr_k < 20 and curr_d < 20:
                    kdj_signal = "超卖"
                elif curr_j > 100:
                    kdj_signal = "J值超买"
                elif curr_j < 0:
                    kdj_signal = "J值超卖"
                elif curr_k > curr_d:
                    kdj_signal = "多头"
                else:
                    kdj_signal = "空头"
            else:
                kdj_signal = "数据不足"

            # DMI/ADX 指标
            dmi_period = 14

            # 计算 TR (True Range) - 需要先计算，因为DMI和ATR都要用
            high_low = df_recent['high'] - df_recent['low']
            high_close = abs(df_recent['high'] - df_recent['close'].shift())
            low_close = abs(df_recent['low'] - df_recent['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

            # 计算 +DM 和 -DM
            high_diff = df_recent['high'].diff()
            low_diff = -df_recent['low'].diff()

            plus_dm = pd.Series(0.0, index=df_recent.index)
            minus_dm = pd.Series(0.0, index=df_recent.index)

            # +DM: 当前高点 - 前一高点 > 前一低点 - 当前低点 且 > 0
            plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
            # -DM: 前一低点 - 当前低点 > 当前高点 - 前一高点 且 > 0
            minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

            # 计算平滑的 +DM, -DM, TR (使用 Wilder's smoothing)
            plus_dm_smooth = plus_dm.ewm(alpha=1/dmi_period, adjust=False).mean()
            minus_dm_smooth = minus_dm.ewm(alpha=1/dmi_period, adjust=False).mean()
            tr_smooth = true_range.ewm(alpha=1/dmi_period, adjust=False).mean()

            # 计算 +DI 和 -DI
            plus_di = 100 * plus_dm_smooth / tr_smooth
            minus_di = 100 * minus_dm_smooth / tr_smooth

            # 计算 DX (方向指数)
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            dx = dx.fillna(0)

            # 计算 ADX (DX的平滑移动平均)
            adx = dx.ewm(alpha=1/dmi_period, adjust=False).mean()

            # DMI 信号判断
            if len(df_recent) >= 2:
                prev_plus_di = plus_di.iloc[-2]
                prev_minus_di = minus_di.iloc[-2]
                curr_plus_di = plus_di.iloc[-1]
                curr_minus_di = minus_di.iloc[-1]
                curr_adx = adx.iloc[-1]
                prev_adx = adx.iloc[-2]

                # 趋势强度判断
                if curr_adx > 50:
                    trend_strength = "极强趋势"
                elif curr_adx > 25:
                    trend_strength = "强趋势"
                elif curr_adx > 20:
                    trend_strength = "趋势形成"
                else:
                    trend_strength = "无趋势/震荡"

                # 方向判断
                if prev_plus_di <= prev_minus_di and curr_plus_di > curr_minus_di:
                    if curr_adx > 25:
                        dmi_signal = f"强势金叉({trend_strength})"
                    else:
                        dmi_signal = "金叉"
                elif prev_plus_di >= prev_minus_di and curr_plus_di < curr_minus_di:
                    if curr_adx > 25:
                        dmi_signal = f"强势死叉({trend_strength})"
                    else:
                        dmi_signal = "死叉"
                elif curr_plus_di > curr_minus_di:
                    if curr_adx > prev_adx:
                        dmi_signal = f"多头加强({trend_strength})"
                    else:
                        dmi_signal = f"多头({trend_strength})"
                else:
                    if curr_adx > prev_adx:
                        dmi_signal = f"空头加强({trend_strength})"
                    else:
                        dmi_signal = f"空头({trend_strength})"
            else:
                dmi_signal = "数据不足"
                trend_strength = "未知"

            # MACD
            ema12 = df_recent['close'].ewm(span=12, adjust=False).mean()
            ema26 = df_recent['close'].ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            macd_hist = (dif - dea) * 2

            # MACD信号判断
            if len(df_recent) >= 2:
                prev_dif = dif.iloc[-2]
                prev_dea = dea.iloc[-2]
                curr_dif = dif.iloc[-1]
                curr_dea = dea.iloc[-1]

                # 金叉/死叉判断
                if prev_dif <= prev_dea and curr_dif > curr_dea:
                    macd_signal = "金叉"
                elif prev_dif >= prev_dea and curr_dif < curr_dea:
                    macd_signal = "死叉"
                elif curr_dif > curr_dea:
                    macd_signal = "多头"
                else:
                    macd_signal = "空头"
            else:
                macd_signal = "数据不足"

            # 布林带 (Bollinger Bands)
            bb_period = 20
            bb_std = 2
            bb_middle = df_recent['close'].rolling(bb_period).mean()
            bb_std_dev = df_recent['close'].rolling(bb_period).std()
            bb_upper = bb_middle + (bb_std * bb_std_dev)
            bb_lower = bb_middle - (bb_std * bb_std_dev)

            # 布林带宽度百分比
            bb_width = ((bb_upper - bb_lower) / bb_middle * 100).iloc[-1] if not pd.isna(bb_middle.iloc[-1]) else 0

            # 价格在布林带中的位置 (0-100%)
            if not pd.isna(bb_upper.iloc[-1]) and not pd.isna(bb_lower.iloc[-1]):
                bb_position = (latest['close'] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) * 100
            else:
                bb_position = 50

            # 布林带信号判断
            if bb_position > 100:
                bb_signal = "突破上轨"
            elif bb_position > 80:
                bb_signal = "接近上轨"
            elif bb_position > 60:
                bb_signal = "中轨上方"
            elif bb_position > 40:
                bb_signal = "中轨附近"
            elif bb_position > 20:
                bb_signal = "中轨下方"
            elif bb_position > 0:
                bb_signal = "接近下轨"
            else:
                bb_signal = "突破下轨"

            # ATR (Average True Range) - 使用前面已计算的 true_range
            atr_period = 14
            atr = true_range.rolling(atr_period).mean()
            atr_pct = (atr.iloc[-1] / latest['close'] * 100) if not pd.isna(atr.iloc[-1]) else 0

            # 成交量指标
            if 'volume' in df_recent.columns:
                # OBV (On Balance Volume)
                obv = (df_recent['volume'] * df_recent['close'].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))).cumsum()

                # 量比 (当日成交量 / 近20日平均成交量)
                avg_volume_20 = df_recent['volume'].rolling(20).mean()
                volume_ratio = (latest['volume'] / avg_volume_20.iloc[-1]) if not pd.isna(avg_volume_20.iloc[-1]) and avg_volume_20.iloc[-1] > 0 else 1.0

                # 量价背离检测（简化版：比较最近20日）
                recent_20 = df_recent.tail(20)
                if len(recent_20) >= 20:
                    price_high_idx = recent_20['close'].idxmax()
                    obv_high_idx = obv.tail(20).idxmax()

                    if price_high_idx == recent_20.index[-1] and obv_high_idx != obv.tail(20).index[-1]:
                        volume_divergence = "顶背离"
                    elif recent_20['close'].iloc[-1] == recent_20['close'].min() and obv.iloc[-1] != obv.tail(20).min():
                        volume_divergence = "底背离"
                    else:
                        volume_divergence = "无"
                else:
                    volume_divergence = "数据不足"

                obv_value = float(obv.iloc[-1]) if not pd.isna(obv.iloc[-1]) else 0
            else:
                obv_value = 0
                volume_ratio = 1.0
                volume_divergence = "无成交量数据"

            # 波动率
            returns = df_recent['close'].pct_change()
            volatility = returns.std() * np.sqrt(252)

            # 52周高低点
            high_52w = df_recent['high'].tail(252).max() if len(df_recent) >= 252 else df_recent['high'].max()
            low_52w = df_recent['low'].tail(252).min() if len(df_recent) >= 252 else df_recent['low'].min()

            # 距离52周高低点百分比
            dist_to_high = (latest['close'] - high_52w) / high_52w * 100
            dist_to_low = (latest['close'] - low_52w) / low_52w * 100

            # 均线状态
            ma20 = df_recent.iloc[-1]['ma20'] if not pd.isna(df_recent.iloc[-1]['ma20']) else latest['close']
            ma60 = df_recent.iloc[-1]['ma60'] if not pd.isna(df_recent.iloc[-1]['ma60']) else latest['close']
            ma120 = df_recent.iloc[-1]['ma120'] if not pd.isna(df_recent.iloc[-1]['ma120']) else latest['close']

            # 趋势判断
            if latest['close'] > ma20 > ma60 > ma120:
                trend = "完美多头排列"
            elif latest['close'] > ma20 and ma20 > ma60:
                trend = "多头趋势"
            elif latest['close'] < ma20 < ma60 < ma120:
                trend = "完美空头排列"
            elif latest['close'] < ma20 and ma20 < ma60:
                trend = "空头趋势"
            else:
                trend = "震荡整理"

            return {
                'symbol': symbol,
                'latest_price': float(latest['close']),
                'change': float(latest['close'] - prev['close']),
                'change_pct': float((latest['close'] - prev['close']) / prev['close'] * 100),
                'ma20': float(ma20),
                'ma60': float(ma60),
                'ma120': float(ma120),
                'rsi': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50,
                'kdj_k': float(kdj_k.iloc[-1]) if not pd.isna(kdj_k.iloc[-1]) else 50,
                'kdj_d': float(kdj_d.iloc[-1]) if not pd.isna(kdj_d.iloc[-1]) else 50,
                'kdj_j': float(kdj_j.iloc[-1]) if not pd.isna(kdj_j.iloc[-1]) else 50,
                'kdj_signal': kdj_signal,
                'dmi_plus': float(plus_di.iloc[-1]) if not pd.isna(plus_di.iloc[-1]) else 0,
                'dmi_minus': float(minus_di.iloc[-1]) if not pd.isna(minus_di.iloc[-1]) else 0,
                'adx': float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0,
                'dmi_signal': dmi_signal,
                'macd_dif': float(dif.iloc[-1]) if not pd.isna(dif.iloc[-1]) else 0,
                'macd_dea': float(dea.iloc[-1]) if not pd.isna(dea.iloc[-1]) else 0,
                'macd_hist': float(macd_hist.iloc[-1]) if not pd.isna(macd_hist.iloc[-1]) else 0,
                'macd_signal': macd_signal,
                'bb_upper': float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else 0,
                'bb_middle': float(bb_middle.iloc[-1]) if not pd.isna(bb_middle.iloc[-1]) else 0,
                'bb_lower': float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else 0,
                'bb_width': float(bb_width),
                'bb_position': float(bb_position),
                'bb_signal': bb_signal,
                'atr': float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0,
                'atr_pct': float(atr_pct),
                'obv': obv_value,
                'volume_ratio': float(volume_ratio),
                'volume_divergence': volume_divergence,
                'volatility': float(volatility),
                'high_52w': float(high_52w),
                'low_52w': float(low_52w),
                'dist_to_high_pct': float(dist_to_high),
                'dist_to_low_pct': float(dist_to_low),
                'trend': trend,
                'data_date': df_recent.index[-1].strftime('%Y-%m-%d')
            }

        except Exception as e:
            logger.error(f"指数趋势分析失败: {str(e)}")
            return {'error': str(e)}

    def analyze_capital_flow(self, days: int = 20) -> Dict:
        """
        分析南向资金流向

        Args:
            days: 分析天数

        Returns:
            资金流向分析结果
        """
        try:
            df = self.data_source.get_south_capital_flow(days=days)

            if df.empty:
                return {'error': '数据获取失败'}

            # 确保有资金流向列
            if '当日资金流向' not in df.columns:
                # 尝试其他列名
                flow_col = None
                for col in df.columns:
                    if '流入' in col or '净买' in col:
                        flow_col = col
                        break

                if flow_col is None:
                    return {'error': '无资金流向数据'}
            else:
                flow_col = '当日资金流向'

            # 统计分析
            total_flow = df[flow_col].sum()
            avg_flow = df[flow_col].mean()
            recent_3d_flow = df[flow_col].head(3).sum() if len(df) >= 3 else total_flow
            recent_5d_flow = df[flow_col].head(5).sum() if len(df) >= 5 else total_flow

            # 流向趋势
            positive_days = len(df[df[flow_col] > 0])
            negative_days = len(df[df[flow_col] < 0])

            # 状态判断
            if recent_5d_flow > 100 and recent_3d_flow > 50:
                status = "持续大幅流入"
            elif recent_5d_flow > 50:
                status = "持续流入"
            elif recent_5d_flow > 0:
                status = "小幅流入"
            elif recent_5d_flow > -50:
                status = "小幅流出"
            elif recent_5d_flow > -100:
                status = "持续流出"
            else:
                status = "持续大幅流出"

            return {
                'total_flow': float(total_flow),
                'avg_daily_flow': float(avg_flow),
                'recent_3d_flow': float(recent_3d_flow),
                'recent_5d_flow': float(recent_5d_flow),
                'positive_days': int(positive_days),
                'negative_days': int(negative_days),
                'status': status,
                'data_days': len(df)
            }

        except Exception as e:
            logger.error(f"资金流向分析失败: {str(e)}")
            return {'error': str(e)}

    def analyze_ah_premium(self) -> Dict:
        """
        分析AH股溢价

        Returns:
            AH股溢价分析结果
        """
        try:
            df = self.data_source.get_ah_price_comparison()

            if df.empty:
                return {'error': '数据获取失败'}

            # 计算整体溢价率
            # 列名可能是中文
            price_ratio_col = None
            for col in df.columns:
                if '溢价率' in col or '比价' in col:
                    price_ratio_col = col
                    break

            if price_ratio_col:
                avg_premium = df[price_ratio_col].mean()
                median_premium = df[price_ratio_col].median()
                max_premium = df[price_ratio_col].max()
                min_premium = df[price_ratio_col].min()

                # 溢价分布
                high_premium = len(df[df[price_ratio_col] > 130])  # 溢价超过30%
                negative_premium = len(df[df[price_ratio_col] < 100])  # H股更贵

                # 溢价水平判断
                if median_premium > 130:
                    level = "A股高溢价"
                elif median_premium > 115:
                    level = "A股温和溢价"
                elif median_premium > 100:
                    level = "基本平价"
                else:
                    level = "H股溢价"

                return {
                    'total_stocks': len(df),
                    'avg_premium': float(avg_premium),
                    'median_premium': float(median_premium),
                    'max_premium': float(max_premium),
                    'min_premium': float(min_premium),
                    'high_premium_count': int(high_premium),
                    'negative_premium_count': int(negative_premium),
                    'level': level
                }
            else:
                # 无溢价率列，返回基本信息
                return {
                    'total_stocks': len(df),
                    'level': '数据不完整'
                }

        except Exception as e:
            logger.error(f"AH股溢价分析失败: {str(e)}")
            return {'error': str(e)}

    def analyze_market_breadth(self) -> Dict:
        """
        分析市场广度（涨跌家数）

        Returns:
            市场广度分析结果
        """
        try:
            df = self.data_source.get_hk_stock_spot()

            if df.empty:
                return {'error': '数据获取失败'}

            total = len(df)

            # 找涨跌幅列
            change_col = None
            for col in df.columns:
                if '涨跌幅' in col or '涨幅' in col:
                    change_col = col
                    break

            if not change_col:
                return {'error': '无涨跌幅数据'}

            up_count = len(df[df[change_col] > 0])
            down_count = len(df[df[change_col] < 0])
            flat_count = total - up_count - down_count

            up_ratio = up_count / total if total > 0 else 0

            # 涨幅分布
            up_3pct = len(df[df[change_col] > 3])
            up_5pct = len(df[df[change_col] > 5])
            down_3pct = len(df[df[change_col] < -3])
            down_5pct = len(df[df[change_col] < -5])

            # 市场状态判断
            if up_ratio > 0.7:
                status = "普涨行情"
            elif up_ratio > 0.6:
                status = "多数上涨"
            elif up_ratio > 0.4:
                status = "涨跌均衡"
            elif up_ratio > 0.3:
                status = "多数下跌"
            else:
                status = "普跌行情"

            return {
                'total_stocks': total,
                'up_count': int(up_count),
                'down_count': int(down_count),
                'flat_count': int(flat_count),
                'up_ratio': float(up_ratio),
                'up_3pct_count': int(up_3pct),
                'up_5pct_count': int(up_5pct),
                'down_3pct_count': int(down_3pct),
                'down_5pct_count': int(down_5pct),
                'status': status
            }

        except Exception as e:
            logger.error(f"市场广度分析失败: {str(e)}")
            return {'error': str(e)}

    def comprehensive_analysis(self) -> Dict:
        """
        综合市场分析

        Returns:
            综合分析结果
        """
        logger.info("开始港股市场综合分析...")

        result = {
            'timestamp': datetime.now(),
            'market': 'HK'
        }

        # 1. 恒生指数分析
        logger.info("分析恒生指数...")
        result['hsi_analysis'] = self.analyze_index_trend("HSI")

        # 2. 恒生科技指数分析
        logger.info("分析恒生科技指数...")
        result['hstech_analysis'] = self.analyze_index_trend("HSTECH")

        # 3. 南向资金分析
        logger.info("分析南向资金...")
        result['capital_flow'] = self.analyze_capital_flow(days=20)

        # 4. AH股溢价分析
        logger.info("分析AH股溢价...")
        result['ah_premium'] = self.analyze_ah_premium()

        # 5. 市场广度分析
        logger.info("分析市场广度...")
        result['market_breadth'] = self.analyze_market_breadth()

        # 6. 综合评分（简化版，类似A股分析）
        result['comprehensive_score'] = self._calculate_comprehensive_score(result)

        logger.info("港股市场综合分析完成")
        return result

    def _calculate_comprehensive_score(self, analysis: Dict) -> Dict:
        """
        计算综合评分

        Args:
            analysis: 综合分析结果

        Returns:
            评分结果
        """
        score = 0
        factors = []

        # 1. 指数趋势评分 (30%)
        hsi = analysis.get('hsi_analysis', {})
        if 'error' not in hsi:
            rsi = hsi.get('rsi', 50)
            trend = hsi.get('trend', '')

            if '多头' in trend:
                trend_score = 0.8
            elif '空头' in trend:
                trend_score = 0.2
            else:
                trend_score = 0.5

            # RSI修正
            if rsi > 70:
                rsi_factor = 0.3  # 超买，降低分数
            elif rsi < 30:
                rsi_factor = 0.7  # 超卖，提高分数
            else:
                rsi_factor = 0.5

            index_score = (trend_score + rsi_factor) / 2 * 0.3
            score += index_score
            factors.append(f"指数趋势: {index_score:.2f}")

        # 2. 资金流向评分 (30%)
        capital = analysis.get('capital_flow', {})
        if 'error' not in capital:
            flow_5d = capital.get('recent_5d_flow', 0)
            if flow_5d > 100:
                capital_score = 0.3
            elif flow_5d > 0:
                capital_score = 0.2
            elif flow_5d > -50:
                capital_score = 0.1
            else:
                capital_score = 0.05

            score += capital_score
            factors.append(f"资金流向: {capital_score:.2f}")

        # 3. 市场广度评分 (20%)
        breadth = analysis.get('market_breadth', {})
        if 'error' not in breadth:
            up_ratio = breadth.get('up_ratio', 0.5)
            breadth_score = up_ratio * 0.2

            score += breadth_score
            factors.append(f"市场广度: {breadth_score:.2f}")

        # 4. AH溢价评分 (20%)
        ah = analysis.get('ah_premium', {})
        if 'error' not in ah:
            median_premium = ah.get('median_premium', 110)

            # 溢价合理范围 100-120
            if 100 <= median_premium <= 120:
                ah_score = 0.2
            elif median_premium > 140:
                ah_score = 0.05  # 过高溢价，风险增加
            else:
                ah_score = 0.1

            score += ah_score
            factors.append(f"AH溢价: {ah_score:.2f}")

        # 评级
        if score >= 0.7:
            rating = "强势"
        elif score >= 0.5:
            rating = "中性偏强"
        elif score >= 0.3:
            rating = "中性偏弱"
        else:
            rating = "弱势"

        return {
            'score': float(score),
            'rating': rating,
            'factors': factors
        }


def test_hk_analyzer():
    """测试港股分析器"""
    print("=" * 70)
    print("港股市场分析器测试")
    print("=" * 70)

    analyzer = HKMarketAnalyzer()

    # 综合分析
    print("\n开始综合分析...")
    result = analyzer.comprehensive_analysis()

    # 输出结果
    print("\n" + "=" * 70)
    print("港股市场综合分析报告")
    print(f"分析时间: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. 恒生指数
    if 'hsi_analysis' in result and 'error' not in result['hsi_analysis']:
        hsi = result['hsi_analysis']
        print(f"\n[恒生指数]")
        print(f"  最新点位: {hsi['latest_price']:.2f} ({hsi['change_pct']:+.2f}%)")
        print(f"  趋势状态: {hsi['trend']}")
        print(f"  RSI: {hsi['rsi']:.2f}")
        print(f"  距52周高点: {hsi['dist_to_high_pct']:+.2f}%")

    # 2. 恒生科技
    if 'hstech_analysis' in result and 'error' not in result['hstech_analysis']:
        tech = result['hstech_analysis']
        print(f"\n[恒生科技指数]")
        print(f"  最新点位: {tech['latest_price']:.2f} ({tech['change_pct']:+.2f}%)")
        print(f"  趋势状态: {tech['trend']}")

    # 3. 南向资金
    if 'capital_flow' in result and 'error' not in result['capital_flow']:
        flow = result['capital_flow']
        print(f"\n[南向资金]")
        print(f"  近5日累计: {flow['recent_5d_flow']:.2f} 亿元")
        print(f"  流向状态: {flow['status']}")
        print(f"  净流入天数: {flow['positive_days']}/{flow['data_days']} 天")

    # 4. AH股溢价
    if 'ah_premium' in result and 'error' not in result['ah_premium']:
        ah = result['ah_premium']
        print(f"\n[AH股溢价]")
        print(f"  AH股对数: {ah['total_stocks']} 只")
        if 'median_premium' in ah:
            print(f"  中位溢价率: {ah['median_premium']:.2f}%")
            print(f"  溢价水平: {ah['level']}")

    # 5. 市场广度
    if 'market_breadth' in result and 'error' not in result['market_breadth']:
        breadth = result['market_breadth']
        print(f"\n[市场广度]")
        print(f"  上涨家数: {breadth['up_count']}/{breadth['total_stocks']} ({breadth['up_ratio']:.1%})")
        print(f"  市场状态: {breadth['status']}")

    # 6. 综合评分
    if 'comprehensive_score' in result:
        comp = result['comprehensive_score']
        print(f"\n[综合评分]")
        print(f"  综合得分: {comp['score']:.2f}")
        print(f"  市场评级: {comp['rating']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_hk_analyzer()
