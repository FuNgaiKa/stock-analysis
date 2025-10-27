#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支撑位/压力位分析器
基于历史价格、斐波那契回调、均线等计算关键价位
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import yfinance as yf
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SupportResistanceAnalyzer:
    """支撑位/压力位分析器"""

    def __init__(self, symbol: str, lookback_days: int = 252):
        """
        初始化

        Args:
            symbol: 资产代码
            lookback_days: 回溯天数
        """
        self.symbol = symbol
        self.lookback_days = lookback_days
        self.data = None
        self.current_price = None

    def fetch_data(self) -> bool:
        """获取数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days + 100)

            logger.info(f"获取 {self.symbol} 数据...")
            ticker = yf.Ticker(self.symbol)
            hist = ticker.history(start=start_date.strftime('%Y-%m-%d'),
                                 end=end_date.strftime('%Y-%m-%d'))

            if hist.empty:
                logger.error(f"{self.symbol} 数据为空")
                return False

            self.data = hist.tail(self.lookback_days)
            self.current_price = self.data['Close'].iloc[-1]
            logger.info(f"数据获取成功: {len(self.data)} 条, 当前价: {self.current_price:.2f}")
            return True

        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
            return False

    def calculate_pivot_points(self) -> Dict[str, float]:
        """
        计算枢轴点 (Pivot Points)

        基于昨日高低收计算今日支撑/压力位
        """
        if self.data is None or len(self.data) < 2:
            return {}

        high = self.data['High'].iloc[-2]
        low = self.data['Low'].iloc[-2]
        close = self.data['Close'].iloc[-2]

        # 标准枢轴点
        pivot = (high + low + close) / 3

        # 支撑位
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)

        # 压力位
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)

        return {
            'pivot': pivot,
            'resistance_1': r1,
            'resistance_2': r2,
            'resistance_3': r3,
            'support_1': s1,
            'support_2': s2,
            'support_3': s3,
        }

    def calculate_fibonacci_levels(self) -> Dict[str, float]:
        """
        计算斐波那契回调位

        基于最近波段高点和低点
        """
        if self.data is None or len(self.data) < 60:
            return {}

        # 找最近60天的高点和低点
        recent_high = self.data['High'].tail(60).max()
        recent_low = self.data['Low'].tail(60).min()

        diff = recent_high - recent_low

        # 斐波那契回调比例
        fib_levels = {
            'high': recent_high,
            'fib_0.236': recent_high - diff * 0.236,
            'fib_0.382': recent_high - diff * 0.382,
            'fib_0.500': recent_high - diff * 0.500,
            'fib_0.618': recent_high - diff * 0.618,
            'fib_0.786': recent_high - diff * 0.786,
            'low': recent_low,
        }

        return fib_levels

    def find_historical_sr_levels(
        self,
        num_levels: int = 5,
        touch_tolerance: float = 0.02
    ) -> Dict[str, List[float]]:
        """
        识别历史支撑/压力位

        通过聚类分析找出价格多次触及的区域

        Args:
            num_levels: 返回的支撑/压力位数量
            touch_tolerance: 触及容差（百分比）

        Returns:
            {'supports': [...], 'resistances': [...]}
        """
        if self.data is None:
            return {'supports': [], 'resistances': []}

        highs = self.data['High'].values
        lows = self.data['Low'].values

        # 找出局部高点和低点
        local_highs = []
        local_lows = []

        window = 5
        for i in range(window, len(self.data) - window):
            # 局部高点
            if highs[i] == max(highs[i-window:i+window+1]):
                local_highs.append(highs[i])
            # 局部低点
            if lows[i] == min(lows[i-window:i+window+1]):
                local_lows.append(lows[i])

        # 聚类相近的价位
        def cluster_prices(prices, tolerance):
            if not prices:
                return []

            prices = sorted(prices)
            clusters = []
            current_cluster = [prices[0]]

            for price in prices[1:]:
                if abs(price - np.mean(current_cluster)) / np.mean(current_cluster) <= tolerance:
                    current_cluster.append(price)
                else:
                    clusters.append(np.mean(current_cluster))
                    current_cluster = [price]

            clusters.append(np.mean(current_cluster))
            return clusters

        resistance_levels = cluster_prices(local_highs, touch_tolerance)
        support_levels = cluster_prices(local_lows, touch_tolerance)

        # 过滤：只保留在当前价附近的关键位
        resistances = [r for r in resistance_levels if r > self.current_price][:num_levels]
        supports = [s for s in support_levels if s < self.current_price][-num_levels:]

        return {
            'supports': sorted(supports, reverse=True),
            'resistances': sorted(resistances)
        }

    def calculate_moving_average_sr(self) -> Dict[str, float]:
        """计算均线作为支撑/压力"""
        if self.data is None:
            return {}

        ma_sr = {}

        for period in [20, 50, 60, 120, 200, 250]:
            if len(self.data) >= period:
                ma = self.data['Close'].rolling(period).mean().iloc[-1]
                ma_sr[f'MA{period}'] = ma

        return ma_sr

    def comprehensive_analysis(self) -> Dict[str, Any]:
        """
        综合支撑/压力位分析

        Returns:
            完整分析结果
        """
        logger.info(f"开始分析 {self.symbol} 的支撑/压力位...")

        if not self.fetch_data():
            return {'error': '数据获取失败'}

        # 枢轴点
        pivots = self.calculate_pivot_points()

        # 斐波那契
        fib_levels = self.calculate_fibonacci_levels()

        # 历史支撑/压力
        historical_sr = self.find_historical_sr_levels()

        # 均线支撑/压力
        ma_sr = self.calculate_moving_average_sr()

        # 整合所有支撑位
        all_supports = []
        if pivots:
            all_supports.extend([pivots['support_1'], pivots['support_2'], pivots['support_3']])
        all_supports.extend(historical_sr['supports'])
        all_supports.extend([v for k, v in ma_sr.items() if v < self.current_price])

        # 整合所有压力位
        all_resistances = []
        if pivots:
            all_resistances.extend([pivots['resistance_1'], pivots['resistance_2'], pivots['resistance_3']])
        all_resistances.extend(historical_sr['resistances'])
        all_resistances.extend([v for k, v in ma_sr.items() if v > self.current_price])

        # 去重并排序
        all_supports = sorted(list(set([round(s, 2) for s in all_supports if s > 0])), reverse=True)[:5]
        all_resistances = sorted(list(set([round(r, 2) for r in all_resistances if r > self.current_price])))[:5]

        # 计算52周高低点
        high_52w = self.data['High'].max()
        low_52w = self.data['Low'].min()

        # 生成交易建议
        trading_advice = self._generate_trading_advice(
            self.current_price,
            all_supports,
            all_resistances,
            high_52w,
            low_52w
        )

        result = {
            'symbol': self.symbol,
            'timestamp': datetime.now(),
            'current_price': float(self.current_price),
            'pivot_points': pivots,
            'fibonacci_levels': fib_levels,
            'ma_levels': ma_sr,
            'key_supports': [
                {
                    'price': s,
                    'distance': float((s - self.current_price) / self.current_price * 100),
                    'strength': self._assess_level_strength(s, all_supports)
                }
                for s in all_supports
            ],
            'key_resistances': [
                {
                    'price': r,
                    'distance': float((r - self.current_price) / self.current_price * 100),
                    'strength': self._assess_level_strength(r, all_resistances)
                }
                for r in all_resistances
            ],
            '52_week_high': float(high_52w),
            '52_week_low': float(low_52w),
            'dist_to_52w_high_pct': float((self.current_price - high_52w) / high_52w * 100),
            'dist_to_52w_low_pct': float((self.current_price - low_52w) / low_52w * 100),
            'trading_advice': trading_advice
        }

        logger.info(f"分析完成: {len(all_supports)} 个支撑位, {len(all_resistances)} 个压力位")
        return result

    def _assess_level_strength(self, level: float, all_levels: List[float]) -> str:
        """评估价位强度"""
        count = all_levels.count(level)
        if count >= 3:
            return "强"
        elif count == 2:
            return "中"
        else:
            return "弱"

    def _generate_trading_advice(
        self,
        current: float,
        supports: List[float],
        resistances: List[float],
        high_52w: float,
        low_52w: float
    ) -> List[str]:
        """生成交易建议"""
        advice = []

        # 检查位置
        if resistances and len(resistances) > 0:
            nearest_resistance = resistances[0]
            dist_to_r = (nearest_resistance - current) / current * 100

            if dist_to_r < 2:
                advice.append(f"⚠️ 当前价接近压力位 ${nearest_resistance:.2f}，突破确认后可追涨")
            elif dist_to_r < 5:
                advice.append(f"📊 接近压力位 ${nearest_resistance:.2f} ({dist_to_r:+.1f}%)，观察突破")

        if supports and len(supports) > 0:
            nearest_support = supports[0]
            dist_to_s = (current - nearest_support) / current * 100

            if dist_to_s < 2:
                advice.append(f"🟢 当前价接近支撑位 ${nearest_support:.2f}，回踩可考虑买入")
            elif dist_to_s < 5:
                advice.append(f"📉 如跌破支撑位 ${nearest_support:.2f}，及时止损")

        # 52周位置
        dist_to_high = (current - high_52w) / high_52w * 100
        if abs(dist_to_high) < 3:
            advice.append(f"🔥 接近52周高点，突破后空间打开")
        elif dist_to_high < -20:
            advice.append(f"💡 距52周高点 {abs(dist_to_high):.1f}%，有上涨空间")

        if not advice:
            advice.append("➡️ 当前处于中性区域，观望为主")

        return advice


if __name__ == '__main__':
    # 测试
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("="*80)
    print("支撑/压力位分析测试")
    print("="*80)

    analyzer = SupportResistanceAnalyzer('GC=F', lookback_days=252)
    result = analyzer.comprehensive_analysis()

    if 'error' not in result:
        print(f"\n✅ {result['symbol']} 分析完成")
        print(f"   当前价: ${result['current_price']:.2f}")

        print(f"\n【压力位】")
        for r in result['key_resistances']:
            print(f"   ${r['price']:.2f} ({r['distance']:+.1f}%) - 强度: {r['strength']}")

        print(f"\n【支撑位】")
        for s in result['key_supports']:
            print(f"   ${s['price']:.2f} ({s['distance']:.1f}%) - 强度: {s['strength']}")

        print(f"\n【交易建议】")
        for adv in result['trading_advice']:
            print(f"   • {adv}")
    else:
        print(f"❌ 分析失败: {result['error']}")

    print("\n" + "="*80)
