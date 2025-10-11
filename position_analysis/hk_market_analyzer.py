#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场分析器
支持恒生指数、恒生科技指数等港股指数的点位分析
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from data_sources.us_stock_source import USStockDataSource  # 可复用yfinance

logger = logging.getLogger(__name__)


@dataclass
class HKIndexConfig:
    """港股指数配置"""
    code: str
    name: str
    symbol: str  # yfinance symbol


# 支持的港股指数
HK_INDICES = {
    'HSI': HKIndexConfig('HSI', '恒生指数', '^HSI'),
    'HSCEI': HKIndexConfig('HSCEI', '国企指数', '^HSCE'),
    'HSTECH': HKIndexConfig('HSTECH', '恒生科技指数', '3032.HK'),  # 使用恒生科技ETF代替指数
}

# 默认分析的指数
DEFAULT_HK_INDICES = ['HSI', 'HSCEI', 'HSTECH']


class HKMarketAnalyzer:
    """港股市场分析器"""

    def __init__(self):
        self.data_source = USStockDataSource()  # 使用yfinance获取港股数据
        self.data_cache = {}
        logger.info("港股市场分析器初始化完成")

    def get_index_data(self, index_code: str, period: str = "5y") -> pd.DataFrame:
        """获取港股指数历史数据"""
        cache_key = f"HK_{index_code}_{period}"
        if cache_key in self.data_cache:
            logger.info(f"使用缓存的{index_code}数据")
            return self.data_cache[cache_key]

        if index_code not in HK_INDICES:
            logger.error(f"不支持的港股指数: {index_code}")
            return pd.DataFrame()

        config = HK_INDICES[index_code]
        # 使用yfinance获取港股数据
        df = self.data_source.get_us_index_daily(config.symbol, period=period)

        if not df.empty:
            df['return'] = df['close'].pct_change()
            self.data_cache[cache_key] = df

        return df

    def get_current_positions(self, indices: List[str] = None) -> Dict[str, Dict]:
        """获取当前各指数点位"""
        if indices is None:
            indices = DEFAULT_HK_INDICES

        positions = {}

        for code in indices:
            if code not in HK_INDICES:
                logger.warning(f"不支持的港股指数代码: {code}")
                continue

            try:
                config = HK_INDICES[code]
                df = self.get_index_data(code, period="5d")

                if df.empty:
                    logger.warning(f"{config.name}数据为空")
                    continue

                current_price = df['close'].iloc[-1]
                positions[code] = {
                    'name': config.name,
                    'price': float(current_price),
                    'date': df.index[-1].strftime('%Y-%m-%d'),
                    'change_pct': float((current_price - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0.0
                }
                logger.info(f"{config.name}: {current_price:.2f} ({positions[code]['change_pct']:+.2f}%)")

            except Exception as e:
                logger.error(f"获取{code}当前点位失败: {str(e)}")
                continue

        return positions

    def analyze_single_index(
        self,
        index_code: str,
        tolerance: float = 0.05,
        periods: List[int] = [5, 10, 20, 60]
    ) -> Dict:
        """单指数完整分析（简化版，复用美股分析逻辑）"""
        logger.info(f"开始分析港股 {HK_INDICES[index_code].name}...")

        result = {
            'index_code': index_code,
            'index_name': HK_INDICES[index_code].name,
            'timestamp': datetime.now(),
            'market': 'HK'
        }

        try:
            # 获取当前点位
            positions = self.get_current_positions([index_code])
            if index_code not in positions:
                result['error'] = '获取当前点位失败'
                return result

            current_info = positions[index_code]
            result['current_price'] = current_info['price']
            result['current_date'] = current_info['date']
            result['current_change_pct'] = current_info['change_pct']

            logger.info(f"{HK_INDICES[index_code].name} 分析完成")

        except Exception as e:
            logger.error(f"分析{index_code}失败: {str(e)}")
            result['error'] = str(e)

        return result


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    analyzer = HKMarketAnalyzer()

    print("\n=== 港股市场分析器测试 ===")
    positions = analyzer.get_current_positions()

    for code, info in positions.items():
        print(f"{info['name']}: {info['price']:.2f} ({info['change_pct']:+.2f}%)")
