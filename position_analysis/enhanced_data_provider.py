#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强数据获取模块 - Phase 1.5
获取成交量、市场情绪、宏观指标等增强因子
"""

import pandas as pd
import numpy as np
import akshare as ak
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class EnhancedDataProvider:
    """增强数据提供器"""

    def __init__(self):
        self._cache = {}
        logger.info("增强数据提供器初始化完成")

    def get_volume_metrics(self, index_code: str, date: datetime = None) -> Dict:
        """
        获取成交量相关指标

        Returns:
            {
                'current_volume': 当前成交量,
                'volume_ma5': 5日均量,
                'volume_ma20': 20日均量,
                'volume_percentile': 成交量历史分位数,
                'volume_ratio': 量比 (当前/5日均)
            }
        """
        try:
            df = ak.stock_zh_index_daily(symbol=index_code)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            if date is None:
                date = df.index[-1]

            # 确保date在索引中
            if date not in df.index:
                date = df.index[df.index <= date][-1]

            current_volume = df.loc[date, 'volume']

            # 均量
            df['volume_ma5'] = df['volume'].rolling(5).mean()
            df['volume_ma20'] = df['volume'].rolling(20).mean()

            # 历史分位数
            historical_volumes = df['volume'].loc[:date]
            volume_percentile = (historical_volumes < current_volume).sum() / len(historical_volumes)

            # 量比
            volume_ma5 = df.loc[date, 'volume_ma5']
            volume_ratio = current_volume / volume_ma5 if volume_ma5 > 0 else 1.0

            return {
                'current_volume': float(current_volume),
                'volume_ma5': float(volume_ma5),
                'volume_ma20': float(df.loc[date, 'volume_ma20']),
                'volume_percentile': float(volume_percentile),
                'volume_ratio': float(volume_ratio),
                'volume_status': self._classify_volume_status(volume_ratio, volume_percentile)
            }

        except Exception as e:
            logger.warning(f"获取成交量指标失败: {str(e)}")
            return {}

    def get_market_sentiment(self, date_str: str = None) -> Dict:
        """
        获取市场情绪指标

        Returns:
            {
                'limit_up_count': 涨停数量,
                'limit_down_count': 跌停数量,
                'limit_up_ratio': 涨停比率,
                'sentiment_score': 情绪得分 (-1到1)
            }
        """
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y%m%d')

            # 涨停数据
            try:
                df_up = ak.stock_zt_pool_em(date=date_str)
                limit_up_count = len(df_up)
            except:
                limit_up_count = 0

            # 跌停数据
            try:
                df_down = ak.stock_zt_pool_dtgc_em(date=date_str)
                limit_down_count = len(df_down)
            except:
                limit_down_count = 0

            # A股总数约5000只
            total_stocks = 5000
            limit_up_ratio = limit_up_count / total_stocks
            limit_down_ratio = limit_down_count / total_stocks

            # 情绪得分：涨停多为正，跌停多为负
            sentiment_score = (limit_up_count - limit_down_count) / total_stocks
            sentiment_score = max(-1, min(1, sentiment_score))  # 限制在-1到1

            sentiment_level = self._classify_sentiment(limit_up_count, limit_down_count)

            return {
                'limit_up_count': limit_up_count,
                'limit_down_count': limit_down_count,
                'limit_up_ratio': float(limit_up_ratio),
                'limit_down_ratio': float(limit_down_ratio),
                'sentiment_score': float(sentiment_score),
                'sentiment_level': sentiment_level
            }

        except Exception as e:
            logger.warning(f"获取市场情绪指标失败: {str(e)}")
            return {}

    def get_macro_indicators(self) -> Dict:
        """
        获取宏观指标

        Returns:
            {
                'bond_yield_10y': 10年期国债收益率,
                'risk_free_rate': 无风险利率,
            }
        """
        try:
            # 国债收益率
            df = ak.bond_china_yield()
            latest_yield = df['中国国债收益率10年'].iloc[-1]

            return {
                'bond_yield_10y': float(latest_yield),
                'risk_free_rate': float(latest_yield),
                'data_date': df['曲线名称'].iloc[-1]
            }

        except Exception as e:
            logger.warning(f"获取宏观指标失败: {str(e)}")
            return {
                'bond_yield_10y': 2.5,  # 默认值
                'risk_free_rate': 2.5
            }

    def get_volume_price_divergence(
        self,
        index_code: str,
        lookback_days: int = 20
    ) -> Dict:
        """
        检测量价背离

        Returns:
            {
                'has_divergence': 是否背离,
                'divergence_type': '顶背离' / '底背离' / None,
                'divergence_score': 背离强度 (0-1)
            }
        """
        try:
            df = ak.stock_zh_index_daily(symbol=index_code)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            # 最近N天数据
            recent = df.tail(lookback_days)

            # 价格趋势
            price_start = recent['close'].iloc[0]
            price_end = recent['close'].iloc[-1]
            price_trend = (price_end - price_start) / price_start

            # 成交量趋势
            volume_start = recent['volume'].iloc[:5].mean()
            volume_end = recent['volume'].iloc[-5:].mean()
            volume_trend = (volume_end - volume_start) / volume_start

            # 判断背离
            divergence_type = None
            has_divergence = False
            divergence_score = 0

            # 顶背离：价格上涨，成交量萎缩
            if price_trend > 0.05 and volume_trend < -0.2:
                divergence_type = '顶背离'
                has_divergence = True
                divergence_score = min(1.0, abs(volume_trend) * 2)

            # 底背离：价格下跌，成交量放大
            elif price_trend < -0.05 and volume_trend > 0.2:
                divergence_type = '底背离'
                has_divergence = True
                divergence_score = min(1.0, volume_trend * 2)

            return {
                'has_divergence': has_divergence,
                'divergence_type': divergence_type,
                'divergence_score': float(divergence_score),
                'price_trend': float(price_trend),
                'volume_trend': float(volume_trend)
            }

        except Exception as e:
            logger.warning(f"量价背离检测失败: {str(e)}")
            return {
                'has_divergence': False,
                'divergence_type': None,
                'divergence_score': 0
            }

    @staticmethod
    def _classify_volume_status(volume_ratio: float, volume_percentile: float) -> str:
        """分类成交量状态"""
        if volume_ratio >= 2.0:
            return "放量突破"
        elif volume_ratio >= 1.5:
            return "温和放量"
        elif volume_ratio >= 0.8:
            return "正常水平"
        elif volume_ratio >= 0.5:
            return "温和缩量"
        else:
            return "严重缩量"

    @staticmethod
    def _classify_sentiment(limit_up: int, limit_down: int) -> str:
        """分类市场情绪"""
        if limit_up > 100:
            return "极度狂热"
        elif limit_up > 50:
            return "情绪高涨"
        elif limit_up > 20:
            return "情绪积极"
        elif limit_down > 50:
            return "恐慌情绪"
        elif limit_down > 20:
            return "情绪低迷"
        else:
            return "情绪平稳"

    def get_comprehensive_metrics(
        self,
        index_code: str,
        date: datetime = None
    ) -> Dict:
        """
        获取综合指标（一次性获取所有增强数据）

        Returns:
            包含所有增强指标的字典
        """
        logger.info(f"正在获取 {index_code} 的综合增强指标...")

        date_str = date.strftime('%Y%m%d') if date else None

        metrics = {
            'volume_metrics': self.get_volume_metrics(index_code, date),
            'sentiment_metrics': self.get_market_sentiment(date_str),
            'macro_metrics': self.get_macro_indicators(),
            'divergence_metrics': self.get_volume_price_divergence(index_code)
        }

        logger.info(f"成交量状态: {metrics['volume_metrics'].get('volume_status', 'N/A')}")
        logger.info(f"市场情绪: {metrics['sentiment_metrics'].get('sentiment_level', 'N/A')}")

        return metrics


if __name__ == '__main__':
    # 测试
    provider = EnhancedDataProvider()

    print("=== 测试增强数据获取 ===\n")

    # 1. 成交量指标
    print("1. 成交量指标")
    volume_metrics = provider.get_volume_metrics('sh000001')
    for k, v in volume_metrics.items():
        print(f"   {k}: {v}")

    # 2. 市场情绪
    print("\n2. 市场情绪指标")
    sentiment = provider.get_market_sentiment()
    for k, v in sentiment.items():
        print(f"   {k}: {v}")

    # 3. 宏观指标
    print("\n3. 宏观指标")
    macro = provider.get_macro_indicators()
    for k, v in macro.items():
        print(f"   {k}: {v}")

    # 4. 量价背离
    print("\n4. 量价背离检测")
    divergence = provider.get_volume_price_divergence('sh000001')
    for k, v in divergence.items():
        print(f"   {k}: {v}")

    # 5. 综合指标
    print("\n5. 综合指标")
    comprehensive = provider.get_comprehensive_metrics('sh000001')
    print(f"   获取成功，包含 {len(comprehensive)} 个维度")
