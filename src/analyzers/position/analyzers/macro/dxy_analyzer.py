#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美元指数分析器
DXY (US Dollar Index) Analyzer

功能:
1. 获取美元指数历史数据
2. 分析美元强弱趋势
3. 计算技术指标
4. 判断对全球资产的影响

作者: Claude Code
日期: 2025-10-16
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class DXYAnalyzer:
    """
    美元指数分析器

    功能:
    1. 获取DXY历史数据
    2. 分析美元强弱
    3. 计算移动平均和趋势
    4. 判断对资产价格的影响
    """

    DXY_TICKER = 'DX-Y.NYB'  # 美元指数ticker

    # 美元指数关键水平
    KEY_LEVELS = {
        'strong_support': 95.0,   # 强支撑
        'support': 100.0,          # 支撑
        'neutral': 102.5,          # 中性
        'resistance': 105.0,       # 阻力
        'strong_resistance': 110.0 # 强阻力
    }

    def __init__(self, lookback_days: int = 252):
        """
        初始化美元指数分析器

        Args:
            lookback_days: 回溯天数,默认252天(1年)
        """
        self.lookback_days = lookback_days
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 1800  # 30分钟缓存
        logger.info("美元指数分析器初始化完成")

    def get_dxy_data(self, days: int = None) -> pd.DataFrame:
        """
        获取美元指数历史数据

        Args:
            days: 获取天数,默认使用lookback_days

        Returns:
            DataFrame with columns: [date, close, high, low, volume]
        """
        cache_key = "dxy_data"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info("使用缓存的美元指数数据")
                return self.cache[cache_key]

        try:
            logger.info(f"获取美元指数数据 ({self.DXY_TICKER})...")

            if days is None:
                days = self.lookback_days

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+30)

            dxy = yf.Ticker(self.DXY_TICKER)
            df = dxy.history(start=start_date, end=end_date)

            if df.empty:
                logger.warning("美元指数数据为空")
                return pd.DataFrame()

            # 处理数据
            result = pd.DataFrame({
                'date': df.index,
                'close': df['Close'],
                'high': df['High'],
                'low': df['Low'],
                'volume': df['Volume']
            })

            result = result.sort_values('date', ascending=True).reset_index(drop=True)
            result = result.tail(days)

            # 缓存
            self.cache[cache_key] = result
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"美元指数数据获取成功: {len(result)} 条记录")
            return result

        except Exception as e:
            logger.error(f"获取美元指数数据失败: {str(e)}")
            return pd.DataFrame()

    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """
        计算技术指标

        Args:
            df: 美元指数数据

        Returns:
            技术指标字典
        """
        if df.empty or len(df) < 20:
            return {}

        try:
            current_price = float(df.iloc[-1]['close'])

            # 移动平均
            ma5 = float(df['close'].tail(5).mean())
            ma20 = float(df['close'].tail(20).mean())
            ma60 = float(df['close'].tail(60).mean()) if len(df) >= 60 else ma20

            # 价格相对位置
            price_vs_ma5 = (current_price - ma5) / ma5 * 100
            price_vs_ma20 = (current_price - ma20) / ma20 * 100
            price_vs_ma60 = (current_price - ma60) / ma60 * 100

            # 价格变化
            change_1d = (current_price - float(df.iloc[-2]['close'])) / float(df.iloc[-2]['close']) * 100
            change_5d = (current_price - float(df.iloc[-6]['close'])) / float(df.iloc[-6]['close']) * 100 if len(df) >= 6 else 0
            change_20d = (current_price - float(df.iloc[-21]['close'])) / float(df.iloc[-21]['close']) * 100 if len(df) >= 21 else 0

            # 波动率 (20日标准差)
            volatility = float(df['close'].tail(20).std())
            volatility_pct = volatility / current_price * 100

            indicators = {
                'current_price': current_price,
                'ma5': ma5,
                'ma20': ma20,
                'ma60': ma60,
                'price_vs_ma5': price_vs_ma5,
                'price_vs_ma20': price_vs_ma20,
                'price_vs_ma60': price_vs_ma60,
                'change_1d': change_1d,
                'change_5d': change_5d,
                'change_20d': change_20d,
                'volatility': volatility,
                'volatility_pct': volatility_pct
            }

            return indicators

        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            return {}

    def analyze_strength(self, price: float, indicators: Dict) -> Dict:
        """
        分析美元强弱

        Args:
            price: 当前价格
            indicators: 技术指标

        Returns:
            强弱分析结果
        """
        # 判断美元强弱
        if price > self.KEY_LEVELS['strong_resistance']:
            strength = 'extremely_strong'
            strength_desc = '极强'
            emoji = '🔴🔴'
            impact = '全球风险资产承压,利空股市/黄金/比特币'
        elif price > self.KEY_LEVELS['resistance']:
            strength = 'strong'
            strength_desc = '强势'
            emoji = '🔴'
            impact = '美元走强,压制风险资产,利空新兴市场'
        elif price > self.KEY_LEVELS['neutral']:
            strength = 'moderate'
            strength_desc = '中性偏强'
            emoji = '🟡'
            impact = '美元略强,对资产价格影响中性'
        elif price > self.KEY_LEVELS['support']:
            strength = 'neutral'
            strength_desc = '中性'
            emoji = '⚪'
            impact = '美元中性,风险资产可正常配置'
        elif price > self.KEY_LEVELS['strong_support']:
            strength = 'weak'
            strength_desc = '弱势'
            emoji = '🟢'
            impact = '美元走弱,利好风险资产,利多黄金/大宗商品'
        else:
            strength = 'extremely_weak'
            strength_desc = '极弱'
            emoji = '🟢🟢'
            impact = '美元极度走弱,强烈利好风险资产'

        # 趋势判断
        if indicators:
            price_vs_ma20 = indicators.get('price_vs_ma20', 0)
            change_20d = indicators.get('change_20d', 0)

            if price_vs_ma20 > 2 and change_20d > 2:
                trend = {'direction': 'uptrend', 'emoji': '📈', 'description': '上升趋势'}
            elif price_vs_ma20 < -2 and change_20d < -2:
                trend = {'direction': 'downtrend', 'emoji': '📉', 'description': '下降趋势'}
            else:
                trend = {'direction': 'sideways', 'emoji': '➡️', 'description': '震荡整理'}
        else:
            trend = {'direction': 'unknown', 'emoji': '❓', 'description': '未知'}

        return {
            'strength': strength,
            'strength_desc': strength_desc,
            'emoji': emoji,
            'impact': impact,
            'trend': trend,
            'key_levels': self.KEY_LEVELS
        }

    def comprehensive_analysis(self) -> Dict:
        """
        综合分析美元指数

        Returns:
            完整的美元指数分析结果
        """
        try:
            logger.info("开始美元指数综合分析...")

            # 1. 获取数据
            df = self.get_dxy_data()

            if df.empty:
                return {
                    'error': '无法获取美元指数数据',
                    'timestamp': datetime.now()
                }

            # 2. 计算技术指标
            indicators = self.calculate_technical_indicators(df)

            if not indicators:
                return {
                    'error': '技术指标计算失败',
                    'timestamp': datetime.now()
                }

            # 3. 分析强弱
            strength_analysis = self.analyze_strength(indicators['current_price'], indicators)

            # 4. 汇总结果
            result = {
                'date': df.iloc[-1]['date'].strftime('%Y-%m-%d') if hasattr(df.iloc[-1]['date'], 'strftime') else str(df.iloc[-1]['date']),
                'current_price': indicators['current_price'],
                'indicators': indicators,
                'strength_analysis': strength_analysis,
                'timestamp': datetime.now()
            }

            logger.info("美元指数综合分析完成")
            return result

        except Exception as e:
            logger.error(f"美元指数综合分析失败: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now()
            }


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("美元指数分析器测试")
    print("=" * 80)

    analyzer = DXYAnalyzer(lookback_days=252)

    # 测试综合分析
    print("\n测试美元指数综合分析")
    print("-" * 80)
    result = analyzer.comprehensive_analysis()

    if 'error' not in result:
        print(f"\n📊 美元指数 (DXY) - {result['date']}")
        print(f"  当前价格: {result['current_price']:.2f}")

        indicators = result['indicators']
        print(f"\n技术指标:")
        print(f"  MA5: {indicators['ma5']:.2f}")
        print(f"  MA20: {indicators['ma20']:.2f}")
        print(f"  MA60: {indicators['ma60']:.2f}")
        print(f"  相对MA20: {indicators['price_vs_ma20']:+.2f}%")

        print(f"\n价格变化:")
        print(f"  单日: {indicators['change_1d']:+.2f}%")
        print(f"  5日: {indicators['change_5d']:+.2f}%")
        print(f"  20日: {indicators['change_20d']:+.2f}%")

        print(f"\n波动率: {indicators['volatility_pct']:.2f}%")

        strength = result['strength_analysis']
        print(f"\n美元强弱: {strength['emoji']} {strength['strength_desc']}")
        print(f"  趋势: {strength['trend']['emoji']} {strength['trend']['description']}")
        print(f"  市场影响: {strength['impact']}")

        print(f"\n关键水平:")
        for level_name, level_value in strength['key_levels'].items():
            status = "✅ 已突破" if result['current_price'] > level_value else "⬇️ 下方"
            print(f"  {level_name}: {level_value:.2f} ({status})")
    else:
        print(f"  ❌ 分析失败: {result['error']}")

    print("\n" + "=" * 80)
    print("✅ 美元指数分析器测试完成")
    print("=" * 80)
