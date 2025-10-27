#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场情绪综合指数
整合多维度指标，量化市场情绪状态（0-100）
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import yfinance as yf
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MarketSentimentIndex:
    """市场情绪综合指数分析器"""

    def __init__(self, symbols: Dict[str, str] = None):
        """
        初始化

        Args:
            symbols: 监控的资产字典 {code: name}
        """
        self.symbols = symbols or {
            '^VIX': 'VIX恐慌指数',
            '^IXIC': '纳斯达克',
            'GC=F': '黄金',
            'BTC-USD': '比特币',
        }
        self.data_cache = {}

    def fetch_asset_data(self, symbol: str, days: int = 60) -> pd.DataFrame:
        """获取资产数据"""
        if symbol in self.data_cache:
            return self.data_cache[symbol]

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 30)

            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date.strftime('%Y-%m-%d'),
                                 end=end_date.strftime('%Y-%m-%d'))

            if not hist.empty:
                df = hist[['Close', 'Volume']].tail(days)
                self.data_cache[symbol] = df
                return df

        except Exception as e:
            logger.error(f"获取 {symbol} 数据失败: {str(e)}")

        return pd.DataFrame()

    def calculate_vix_sentiment(self) -> Dict[str, Any]:
        """
        VIX情绪评分 (0-100)

        VIX < 15: 极度乐观 (100)
        VIX 15-20: 正常乐观 (70-90)
        VIX 20-30: 正常 (40-70)
        VIX 30-40: 恐慌 (20-40)
        VIX > 40: 极度恐慌 (0-20)
        """
        df = self.fetch_asset_data('^VIX', days=5)

        if df.empty:
            return {'score': 50, 'level': '无数据'}

        current_vix = df['Close'].iloc[-1]

        # VIX评分：越低越乐观
        if current_vix < 15:
            score = 100
            level = '极度乐观'
        elif current_vix < 20:
            score = 70 + (20 - current_vix) / 5 * 30
            level = '正常乐观'
        elif current_vix < 30:
            score = 40 + (30 - current_vix) / 10 * 30
            level = '正常'
        elif current_vix < 40:
            score = 20 + (40 - current_vix) / 10 * 20
            level = '恐慌'
        else:
            score = max(0, 20 - (current_vix - 40) * 2)
            level = '极度恐慌'

        return {
            'score': float(score),
            'level': level,
            'vix_value': float(current_vix),
            'interpretation': self._interpret_vix(current_vix, level)
        }

    def calculate_price_momentum_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        价格动量情绪 (0-100)

        基于RSI + 价格相对52周高低点位置
        """
        df = self.fetch_asset_data(symbol, days=260)

        if df.empty or len(df) < 60:
            return {'score': 50, 'level': '无数据'}

        current_price = df['Close'].iloc[-1]

        # RSI计算
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        # 52周位置
        high_52w = df['Close'].max()
        low_52w = df['Close'].min()
        position_52w = (current_price - low_52w) / (high_52w - low_52w) * 100

        # 综合评分
        rsi_score = current_rsi
        position_score = position_52w

        # 加权平均 (RSI 60%, 52周位置 40%)
        score = rsi_score * 0.6 + position_score * 0.4

        # 评级
        if score >= 80:
            level = '极度强势'
        elif score >= 70:
            level = '强势'
        elif score >= 30:
            level = '正常'
        elif score >= 20:
            level = '弱势'
        else:
            level = '极度弱势'

        return {
            'score': float(score),
            'level': level,
            'rsi': float(current_rsi),
            'position_52w': float(position_52w),
        }

    def calculate_volume_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        成交量情绪 (0-100)

        量增价涨 = 看多
        量增价跌 = 看空
        """
        df = self.fetch_asset_data(symbol, days=60)

        if df.empty or len(df) < 30:
            return {'score': 50, 'level': '无数据'}

        # 成交量均值
        vol_ma20 = df['Volume'].rolling(20).mean()
        current_vol = df['Volume'].iloc[-1]
        avg_vol = vol_ma20.iloc[-1]

        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0

        # 价格变化
        price_change = df['Close'].pct_change().iloc[-1]

        # 量价配合评分
        if vol_ratio > 1.5:  # 放量
            if price_change > 0:
                score = 70 + min(vol_ratio - 1.5, 1.0) * 30  # 量增价涨 70-100
                level = '强势放量'
            else:
                score = 30 - min(vol_ratio - 1.5, 1.0) * 30  # 量增价跌 0-30
                level = '恐慌性抛售'
        elif vol_ratio < 0.7:  # 缩量
            score = 40 + (0.7 - vol_ratio) * 20  # 缩量 40-50
            level = '观望缩量'
        else:  # 正常量
            score = 50 + price_change * 200  # 正常量 40-60
            level = '正常'

        score = max(0, min(100, score))

        return {
            'score': float(score),
            'level': level,
            'volume_ratio': float(vol_ratio),
            'price_change_pct': float(price_change * 100),
        }

    def calculate_comprehensive_sentiment(self) -> Dict[str, Any]:
        """
        计算综合市场情绪指数 (0-100)

        整合：
        1. VIX情绪 (30%)
        2. 主要指数动量 (40%)
        3. 成交量 (30%)
        """
        logger.info("开始计算综合市场情绪指数...")

        # 1. VIX情绪
        vix_sentiment = self.calculate_vix_sentiment()

        # 2. 纳指动量
        nasdaq_momentum = self.calculate_price_momentum_sentiment('^IXIC')

        # 3. 纳指成交量
        nasdaq_volume = self.calculate_volume_sentiment('^IXIC')

        # 加权综合评分
        weights = {
            'vix': 0.30,
            'momentum': 0.40,
            'volume': 0.30,
        }

        total_score = (
            vix_sentiment['score'] * weights['vix'] +
            nasdaq_momentum['score'] * weights['momentum'] +
            nasdaq_volume['score'] * weights['volume']
        )

        # 评级
        if total_score >= 80:
            rating = '极度贪婪'
            emoji = '🔥'
            suggestion = '市场过热，警惕回调风险，建议适当减仓'
        elif total_score >= 70:
            rating = '贪婪'
            emoji = '📈'
            suggestion = '市场情绪乐观，可持仓观望，注意控制仓位'
        elif total_score >= 60:
            rating = '偏乐观'
            emoji = '😊'
            suggestion = '市场健康，可正常配置'
        elif total_score >= 40:
            rating = '中性'
            emoji = '😐'
            suggestion = '市场平衡，观望为主'
        elif total_score >= 30:
            rating = '偏悲观'
            emoji = '😟'
            suggestion = '市场偏弱，谨慎操作'
        elif total_score >= 20:
            rating = '恐慌'
            emoji = '😰'
            suggestion = '市场恐慌，等待企稳信号'
        else:
            rating = '极度恐慌'
            emoji = '💀'
            suggestion = '市场极度恐慌，可能是抄底机会，但需等待确认'

        result = {
            'timestamp': datetime.now(),
            'sentiment_score': float(total_score),
            'rating': rating,
            'emoji': emoji,
            'suggestion': suggestion,
            'components': {
                'vix_sentiment': vix_sentiment,
                'nasdaq_momentum': nasdaq_momentum,
                'nasdaq_volume': nasdaq_volume,
            },
            'weights': weights,
        }

        logger.info(f"综合情绪指数: {total_score:.1f} ({rating})")
        return result

    def _interpret_vix(self, vix: float, level: str) -> str:
        """解释VIX水平"""
        if vix < 15:
            return f"VIX={vix:.1f}，市场极度乐观，可能过度自信"
        elif vix < 20:
            return f"VIX={vix:.1f}，市场情绪正常偏乐观"
        elif vix < 30:
            return f"VIX={vix:.1f}，市场情绪中性"
        elif vix < 40:
            return f"VIX={vix:.1f}，市场恐慌情绪上升"
        else:
            return f"VIX={vix:.1f}，市场极度恐慌，可能超跌反弹"

    def get_historical_sentiment(self, days: int = 30) -> pd.Series:
        """获取历史情绪指数（简化版）"""
        # TODO: 实现历史情绪序列
        pass


if __name__ == '__main__':
    # 测试
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("="*80)
    print("市场情绪综合指数测试")
    print("="*80)

    analyzer = MarketSentimentIndex()
    result = analyzer.calculate_comprehensive_sentiment()

    print(f"\n{result['emoji']} 综合情绪指数: {result['sentiment_score']:.1f}/100")
    print(f"   评级: {result['rating']}")
    print(f"   建议: {result['suggestion']}")

    print(f"\n【各维度得分】")
    print(f"   VIX情绪: {result['components']['vix_sentiment']['score']:.1f} "
          f"({result['components']['vix_sentiment']['level']})")
    print(f"   价格动量: {result['components']['nasdaq_momentum']['score']:.1f} "
          f"({result['components']['nasdaq_momentum']['level']})")
    print(f"   成交量: {result['components']['nasdaq_volume']['score']:.1f} "
          f"({result['components']['nasdaq_volume']['level']})")

    print("\n" + "="*80)
