#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨资产相关性分析器
分析不同市场资产之间的相关性，发现潜在的市场联动
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Any
import yfinance as yf
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """跨资产相关性分析器"""

    def __init__(self, lookback_days: int = 252):
        """
        初始化相关性分析器

        Args:
            lookback_days: 回溯天数，默认252天(约1年)
        """
        self.lookback_days = lookback_days
        self.assets_data = {}

    def fetch_asset_data(self, symbols: List[str]) -> Dict[str, pd.Series]:
        """
        批量获取资产数据

        Args:
            symbols: 资产代码列表

        Returns:
            {symbol: price_series} 字典
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days + 100)  # 多拿些数据以防节假日

        results = {}

        for symbol in symbols:
            try:
                logger.info(f"获取 {symbol} 数据...")
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date.strftime('%Y-%m-%d'),
                                     end=end_date.strftime('%Y-%m-%d'))

                if not hist.empty:
                    # 只保留最近lookback_days的数据
                    prices = hist['Close'].tail(self.lookback_days)
                    results[symbol] = prices
                    logger.info(f"{symbol}: {len(prices)} 条数据")
                else:
                    logger.warning(f"{symbol} 数据为空")

            except Exception as e:
                logger.error(f"获取 {symbol} 数据失败: {str(e)}")

        self.assets_data = results
        return results

    def calculate_correlation_matrix(
        self,
        method: str = 'pearson'
    ) -> pd.DataFrame:
        """
        计算相关性矩阵

        Args:
            method: 相关性计算方法 ('pearson', 'spearman', 'kendall')

        Returns:
            相关性矩阵 DataFrame
        """
        if not self.assets_data:
            logger.error("没有数据，请先调用 fetch_asset_data()")
            return pd.DataFrame()

        # 对齐所有资产的日期 - 使用插值填充缺失值
        df = pd.DataFrame(self.assets_data)

        # 使用前向填充 + 后向填充来处理不同市场的交易日差异
        df = df.ffill().bfill()

        # 再次检查是否有缺失值
        if df.isnull().any().any():
            logger.warning("仍有缺失值，使用插值填充")
            df = df.interpolate(method='linear')
            df = df.ffill().bfill()  # 确保首尾没有NaN

        if df.empty or len(df) < 30:
            logger.error(f"数据不足: {len(df)} 条")
            return pd.DataFrame()

        logger.info(f"计算相关性矩阵 (方法: {method}, 数据点: {len(df)})")

        # 计算收益率相关性（更稳定）
        returns = df.pct_change().dropna()
        corr_matrix = returns.corr(method=method)

        return corr_matrix

    def find_high_correlations(
        self,
        threshold: float = 0.7,
        top_n: int = 10
    ) -> List[Tuple[str, str, float]]:
        """
        找出高相关性资产对

        Args:
            threshold: 相关性阈值（绝对值）
            top_n: 返回前N对

        Returns:
            [(asset1, asset2, correlation), ...] 列表
        """
        corr_matrix = self.calculate_correlation_matrix()

        if corr_matrix.empty:
            return []

        high_corr = []

        # 遍历上三角矩阵（避免重复和对角线）
        for i in range(len(corr_matrix)):
            for j in range(i+1, len(corr_matrix)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= threshold:
                    asset1 = corr_matrix.index[i]
                    asset2 = corr_matrix.columns[j]
                    high_corr.append((asset1, asset2, corr_value))

        # 按相关性绝对值排序
        high_corr.sort(key=lambda x: abs(x[2]), reverse=True)

        return high_corr[:top_n]

    def calculate_rolling_correlation(
        self,
        asset1: str,
        asset2: str,
        window: int = 60
    ) -> pd.Series:
        """
        计算滚动相关性

        Args:
            asset1: 资产1代码
            asset2: 资产2代码
            window: 滚动窗口

        Returns:
            滚动相关性时间序列
        """
        if asset1 not in self.assets_data or asset2 not in self.assets_data:
            logger.error(f"资产数据不存在: {asset1} 或 {asset2}")
            return pd.Series()

        df = pd.DataFrame({
            asset1: self.assets_data[asset1],
            asset2: self.assets_data[asset2]
        }).dropna()

        # 计算收益率
        returns = df.pct_change().dropna()

        # 滚动相关性
        rolling_corr = returns[asset1].rolling(window).corr(returns[asset2])

        return rolling_corr

    def detect_correlation_changes(
        self,
        asset1: str,
        asset2: str,
        window: int = 60,
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        检测相关性的显著变化

        Args:
            asset1: 资产1
            asset2: 资产2
            window: 滚动窗口
            threshold: 变化阈值

        Returns:
            变化检测结果
        """
        rolling_corr = self.calculate_rolling_correlation(asset1, asset2, window)

        if rolling_corr.empty:
            return {}

        current_corr = rolling_corr.iloc[-1]
        avg_corr = rolling_corr.mean()
        std_corr = rolling_corr.std()

        # 计算Z-Score
        zscore = (current_corr - avg_corr) / std_corr if std_corr > 0 else 0

        # 判断是否异常
        is_anomaly = abs(zscore) > 2.0

        # 检测趋势
        recent_trend = rolling_corr.tail(20).mean()
        long_trend = rolling_corr.mean()
        trend_change = recent_trend - long_trend

        return {
            'asset_pair': f"{asset1} vs {asset2}",
            'current_correlation': current_corr,
            'average_correlation': avg_corr,
            'std_dev': std_corr,
            'zscore': zscore,
            'is_anomaly': is_anomaly,
            'recent_trend': recent_trend,
            'long_term_trend': long_trend,
            'trend_change': trend_change,
            'interpretation': self._interpret_correlation_change(
                current_corr, avg_corr, zscore, trend_change
            )
        }

    def _interpret_correlation_change(
        self,
        current: float,
        average: float,
        zscore: float,
        trend_change: float
    ) -> str:
        """解释相关性变化"""
        if abs(zscore) > 2.5:
            if current > average:
                return f"⚠️ 异常强化：相关性显著增强 (Z={zscore:.2f})，市场联动性增加"
            else:
                return f"⚠️ 异常弱化：相关性显著减弱 (Z={zscore:.2f})，市场分化加剧"
        elif abs(zscore) > 1.5:
            if current > average:
                return f"📈 温和强化：相关性略有增强 (Z={zscore:.2f})"
            else:
                return f"📉 温和弱化：相关性略有减弱 (Z={zscore:.2f})"
        else:
            if trend_change > 0.1:
                return f"➡️ 趋势上升：相关性呈上升趋势 (+{trend_change:.3f})"
            elif trend_change < -0.1:
                return f"➡️ 趋势下降：相关性呈下降趋势 ({trend_change:.3f})"
            else:
                return f"✅ 稳定正常：相关性维持在正常区间"

    def comprehensive_analysis(
        self,
        symbols: List[str],
        asset_names: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        综合相关性分析

        Args:
            symbols: 资产代码列表
            asset_names: 资产名称映射 {symbol: name}

        Returns:
            完整分析结果
        """
        logger.info(f"开始综合相关性分析: {len(symbols)} 个资产")

        # 获取数据
        self.fetch_asset_data(symbols)

        # 计算相关性矩阵
        corr_matrix = self.calculate_correlation_matrix()

        if corr_matrix.empty:
            return {'error': '无法计算相关性矩阵'}

        # 高相关性对
        high_corr_pairs = self.find_high_correlations(threshold=0.6, top_n=10)

        # 负相关性对（对冲）
        negative_corr_pairs = [
            (a1, a2, corr) for a1, a2, corr in
            self.find_high_correlations(threshold=0.0, top_n=50)
            if corr < -0.5
        ][:5]

        # 构建结果
        result = {
            'timestamp': datetime.now(),
            'lookback_days': self.lookback_days,
            'num_assets': len(symbols),
            'correlation_matrix': corr_matrix.to_dict(),
            'high_correlations': [
                {
                    'asset1': a1,
                    'asset1_name': asset_names.get(a1, a1) if asset_names else a1,
                    'asset2': a2,
                    'asset2_name': asset_names.get(a2, a2) if asset_names else a2,
                    'correlation': float(corr),
                    'strength': self._classify_correlation(corr)
                }
                for a1, a2, corr in high_corr_pairs
            ],
            'negative_correlations': [
                {
                    'asset1': a1,
                    'asset1_name': asset_names.get(a1, a1) if asset_names else a1,
                    'asset2': a2,
                    'asset2_name': asset_names.get(a2, a2) if asset_names else a2,
                    'correlation': float(corr),
                    'hedge_potential': '高' if corr < -0.7 else '中'
                }
                for a1, a2, corr in negative_corr_pairs
            ]
        }

        logger.info("相关性分析完成")
        return result

    def _classify_correlation(self, corr: float) -> str:
        """分类相关性强度"""
        abs_corr = abs(corr)
        if abs_corr >= 0.9:
            return "极强" + ("正相关" if corr > 0 else "负相关")
        elif abs_corr >= 0.7:
            return "强" + ("正相关" if corr > 0 else "负相关")
        elif abs_corr >= 0.5:
            return "中等" + ("正相关" if corr > 0 else "负相关")
        else:
            return "弱相关"


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("="*80)
    print("跨资产相关性分析测试")
    print("="*80)

    # 测试资产
    test_symbols = [
        '^IXIC',    # 纳斯达克
        '^GSPC',    # 标普500
        '^HSI',     # 恒生指数
        'GC=F',     # 黄金
        'BTC-USD',  # 比特币
        'CL=F',     # 原油
    ]

    asset_names = {
        '^IXIC': '纳斯达克',
        '^GSPC': '标普500',
        '^HSI': '恒生指数',
        'GC=F': '黄金',
        'BTC-USD': '比特币',
        'CL=F': '原油',
    }

    analyzer = CorrelationAnalyzer(lookback_days=252)
    result = analyzer.comprehensive_analysis(test_symbols, asset_names)

    if 'error' not in result:
        print(f"\n✅ 分析完成 ({result['num_assets']} 个资产)")

        print("\n【高相关性资产对】")
        for item in result['high_correlations'][:5]:
            print(f"  {item['asset1_name']} vs {item['asset2_name']}: "
                  f"{item['correlation']:.3f} ({item['strength']})")

        print("\n【负相关性资产对（对冲）】")
        for item in result['negative_correlations']:
            print(f"  {item['asset1_name']} vs {item['asset2_name']}: "
                  f"{item['correlation']:.3f} (对冲潜力: {item['hedge_potential']})")
    else:
        print(f"❌ 分析失败: {result['error']}")

    print("\n" + "="*80)
