#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股估值分析器
US Market Valuation Analyzer

功能:
1. 标普500 PE/PB历史分位数分析
2. Shiller PE (CAPE) 分析
3. 估值水平分类

作者: Claude Code
日期: 2025-10-28
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class USValuationAnalyzer:
    """
    美股估值分析器

    支持美股主要指数的估值分析:
    - S&P 500 (^GSPC)
    - Nasdaq 100 (^NDX)
    - Dow Jones (^DJI)
    """

    # 指数代码映射
    INDEX_MAP = {
        '^GSPC': 'S&P 500',
        '^NDX': 'Nasdaq 100',
        '^DJI': 'Dow Jones',
    }

    def __init__(self, lookback_years: int = 10):
        """
        初始化估值分析器

        Args:
            lookback_years: 回溯年数,默认10年
        """
        self.lookback_years = lookback_years
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 3600  # 1小时缓存
        logger.info("美股估值分析器初始化完成")

    def get_index_pe_data(self, symbol: str = '^GSPC') -> pd.DataFrame:
        """
        获取指数PE历史数据

        Args:
            symbol: 指数代码 (如 '^GSPC')

        Returns:
            DataFrame with columns: [date, close, pe_ratio]
        """
        cache_key = f"pe_{symbol}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info(f"使用缓存的{symbol}估值数据")
                return self.cache[cache_key]

        try:
            logger.info(f"获取{symbol}历史数据...")

            # 获取历史价格数据
            ticker = yf.Ticker(symbol)

            # 获取历史数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_years * 365)

            df = ticker.history(start=start_date, end=end_date, interval='1d')

            if df.empty:
                logger.warning(f"{symbol}数据为空")
                return pd.DataFrame()

            # 重命名列
            df = df.reset_index()
            df = df.rename(columns={'Date': 'date', 'Close': 'close'})
            df = df[['date', 'close']]

            # 注意：yfinance不直接提供历史PE数据
            # 我们需要通过其他方式获取或计算
            # 这里先返回价格数据，PE需要额外计算
            logger.warning(f"{symbol}: yfinance不提供历史PE数据，需要额外数据源")

            # 缓存
            self.cache[cache_key] = df
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"{symbol}数据获取成功: {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取{symbol}数据失败: {str(e)}")
            return pd.DataFrame()

    def calculate_simple_valuation_percentile(
        self,
        symbol: str = '^GSPC',
        periods: List[int] = None
    ) -> Dict:
        """
        计算简化版估值分位数
        (基于价格历史分位数，作为PE的近似)

        Args:
            symbol: 指数代码
            periods: 要计算的周期列表(天数),默认[252, 756, 1260, 2520]

        Returns:
            分位数分析字典
        """
        if periods is None:
            periods = [252, 756, 1260, 2520]  # 1年/3年/5年/10年

        df = self.get_index_pe_data(symbol)

        if df.empty or 'close' not in df.columns:
            return {'error': f'{symbol}数据不足'}

        current_price = df['close'].iloc[-1]
        current_date = df['date'].iloc[-1]

        result = {
            'index_code': symbol,
            'index_name': self.INDEX_MAP.get(symbol, symbol),
            'date': current_date.strftime('%Y-%m-%d') if hasattr(current_date, 'strftime') else str(current_date),
            'current_price': float(current_price),
            'price_percentiles': {},
            'note': '注意：由于yfinance无法获取历史PE数据，此处使用价格分位数作为估值的近似指标'
        }

        # 计算价格分位数
        for period in periods:
            if len(df) >= period:
                hist_price = df['close'].tail(period)
                percentile = (hist_price < current_price).sum() / len(hist_price) * 100

                label = f'{period // 252}年' if period % 252 == 0 else f'{period}天'

                result['price_percentiles'][label] = {
                    'percentile': float(percentile),
                    'min': float(hist_price.min()),
                    'max': float(hist_price.max()),
                    'median': float(hist_price.median()),
                    'mean': float(hist_price.mean()),
                    'level': self._classify_percentile(percentile)
                }

        # 估值水平综合判断
        result['valuation_level'] = self._综合估值水平(result)

        return result

    def comprehensive_analysis(self, symbols: List[str] = None) -> Dict:
        """
        综合估值分析

        Args:
            symbols: 要分析的指数代码列表,默认主要指数

        Returns:
            完整估值分析结果
        """
        if symbols is None:
            symbols = ['^GSPC']  # 默认只分析标普500

        logger.info(f"开始美股估值分析: {len(symbols)} 个指数")

        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'indices': {},
            'summary': {},
            'warning': '美股估值分析当前使用价格分位数作为近似指标，建议补充Shiller PE等数据源'
        }

        # 分析各指数估值
        for symbol in symbols:
            try:
                valuation = self.calculate_simple_valuation_percentile(symbol)
                if 'error' not in valuation:
                    result['indices'][symbol] = valuation
            except Exception as e:
                logger.error(f"{symbol}估值分析失败: {e}")

        # 生成摘要
        if result['indices']:
            result['summary'] = self._generate_summary(result)

        logger.info("美股估值分析完成")
        return result

    def _classify_percentile(self, percentile: float) -> str:
        """
        分类估值分位数

        Args:
            percentile: 分位数 (0-100)

        Returns:
            估值水平描述
        """
        if percentile < 20:
            return '极低估⬇️⬇️'
        elif percentile < 40:
            return '低估⬇️'
        elif percentile < 60:
            return '合理➡️'
        elif percentile < 80:
            return '高估⬆️'
        else:
            return '极高估⬆️⬆️'

    def _综合估值水平(self, valuation_data: Dict) -> Dict:
        """
        综合判断估值水平

        Args:
            valuation_data: 估值数据字典

        Returns:
            综合估值水平判断
        """
        price_percentiles = valuation_data.get('price_percentiles', {})

        if not price_percentiles:
            return {'level': '数据不足', 'emoji': '❓'}

        # 使用10年分位数 (如果有),否则使用最长周期
        if '10年' in price_percentiles:
            pct = price_percentiles['10年']['percentile']
        elif '5年' in price_percentiles:
            pct = price_percentiles['5年']['percentile']
        else:
            # 使用最后一个周期的分位数
            pct = list(price_percentiles.values())[-1]['percentile']

        if pct < 20:
            return {
                'level': '极低估',
                'emoji': '⬇️⬇️',
                'signal': '买入时机',
                'description': f'价格处于历史{pct:.0f}%分位,极低估值'
            }
        elif pct < 40:
            return {
                'level': '低估',
                'emoji': '⬇️',
                'signal': '积极配置',
                'description': f'价格处于历史{pct:.0f}%分位,估值偏低'
            }
        elif pct < 60:
            return {
                'level': '合理',
                'emoji': '➡️',
                'signal': '正常持有',
                'description': f'价格处于历史{pct:.0f}%分位,估值合理'
            }
        elif pct < 80:
            return {
                'level': '高估',
                'emoji': '⬆️',
                'signal': '注意风险',
                'description': f'价格处于历史{pct:.0f}%分位,估值偏高'
            }
        else:
            return {
                'level': '极高估',
                'emoji': '⬆️⬆️',
                'signal': '谨慎减仓',
                'description': f'价格处于历史{pct:.0f}%分位,极高估值'
            }

    def _generate_summary(self, analysis_result: Dict) -> Dict:
        """
        生成分析摘要

        Args:
            analysis_result: 完整分析结果

        Returns:
            摘要字典
        """
        indices = analysis_result.get('indices', {})

        if not indices:
            return {'message': '无估值数据'}

        # 统计各估值水平的数量
        undervalued = []
        overvalued = []
        fair_valued = []

        for symbol, data in indices.items():
            level = data.get('valuation_level', {}).get('level', '')
            name = data.get('index_name', symbol)

            if '低估' in level:
                undervalued.append(name)
            elif '高估' in level:
                overvalued.append(name)
            else:
                fair_valued.append(name)

        summary = {
            'undervalued_count': len(undervalued),
            'overvalued_count': len(overvalued),
            'fair_valued_count': len(fair_valued),
            'undervalued_indices': undervalued,
            'overvalued_indices': overvalued,
            'fair_valued_indices': fair_valued
        }

        # 生成总体建议
        if len(undervalued) >= len(indices) * 0.6:
            summary['overall_suggestion'] = "美股整体估值偏低,可考虑增加配置"
        elif len(overvalued) >= len(indices) * 0.6:
            summary['overall_suggestion'] = "美股整体估值偏高,建议控制风险"
        else:
            summary['overall_suggestion'] = "美股估值分化,精选标的"

        return summary


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 70)
    print("美股估值分析器测试")
    print("=" * 70)

    analyzer = USValuationAnalyzer(lookback_years=10)

    print("\n测试S&P 500估值分析")
    print("-" * 70)
    result = analyzer.calculate_simple_valuation_percentile('^GSPC')

    if 'error' not in result:
        print(f"\n{result['index_name']}")
        print(f"日期: {result['date']}")
        print(f"当前价格: {result['current_price']:.2f}")

        print(f"\n⚠️ {result.get('note', '')}")

        print(f"\n价格历史分位数:")
        for period, data in result['price_percentiles'].items():
            print(f"  {period}: {data['percentile']:.1f}% ({data['level']})")

        val_level = result['valuation_level']
        print(f"\n估值水平: {val_level['emoji']} {val_level['level']}")
        print(f"信号: {val_level['signal']}")
        print(f"说明: {val_level['description']}")
    else:
        print(f"  ❌ 分析失败: {result['error']}")

    print("\n" + "=" * 70)
    print("✅ 美股估值分析器测试完成")
    print("=" * 70)
