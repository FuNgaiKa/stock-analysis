#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相对强度分析器 - Alpha/Beta 核心指标
Relative Strength Analyzer

功能：
1. 计算Alpha（超额收益）
2. 计算Beta（系统性风险）
3. 相对强度指数
4. 跑赢/跑输判断
5. 相对强度趋势

作者: Claude Code
日期: 2025-10-31
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class RelativeStrengthAnalyzer:
    """
    相对强度分析器

    机构投资者核心指标：通过Alpha/Beta判断资产相对大盘的表现
    """

    def __init__(self):
        """初始化相对强度分析器"""
        self.logger = logging.getLogger(__name__)

    def analyze(
        self,
        asset_df: pd.DataFrame,
        benchmark_df: pd.DataFrame,
        periods: List[int] = None
    ) -> Dict:
        """
        完整相对强度分析

        Args:
            asset_df: 资产价格数据，必须包含'close'列
            benchmark_df: 基准价格数据，必须包含'close'列
            periods: 分析周期列表，默认[20, 60, 120, 252]

        Returns:
            相对强度分析结果
        """
        if periods is None:
            periods = [20, 60, 120, 252]

        try:
            # 数据验证
            if asset_df.empty or benchmark_df.empty:
                return {'error': '数据为空'}

            if 'close' not in asset_df.columns or 'close' not in benchmark_df.columns:
                return {'error': '缺少close列'}

            # 对齐数据
            aligned_asset, aligned_benchmark = self._align_data(asset_df, benchmark_df)

            if len(aligned_asset) < max(periods):
                return {'error': f'数据不足，需要至少{max(periods)}天数据'}

            # 计算各周期指标
            period_analysis = {}
            for period in periods:
                if len(aligned_asset) >= period:
                    period_result = self._analyze_period(
                        aligned_asset,
                        aligned_benchmark,
                        period
                    )
                    period_key = f'{period}d'
                    period_analysis[period_key] = period_result

            # 计算综合指标（使用最长周期）
            longest_period = max([p for p in periods if len(aligned_asset) >= p])
            overall = self._analyze_period(aligned_asset, aligned_benchmark, longest_period)

            # 判断相对强度趋势
            trend = self._determine_trend(period_analysis)

            result = {
                'alpha': overall['alpha'],
                'beta': overall['beta'],
                'relative_strength': overall['relative_strength'],
                'outperformance': overall['outperformance'],
                'trend': trend,
                'period_analysis': period_analysis,
                'summary': self._generate_summary(overall, trend)
            }

            return result

        except Exception as e:
            self.logger.error(f"相对强度分析失败: {str(e)}")
            return {'error': str(e)}

    def _align_data(
        self,
        asset_df: pd.DataFrame,
        benchmark_df: pd.DataFrame
    ) -> tuple:
        """
        对齐资产和基准数据的时间序列

        Returns:
            (aligned_asset, aligned_benchmark)
        """
        # 确保索引是日期时间类型
        if not isinstance(asset_df.index, pd.DatetimeIndex):
            asset_df = asset_df.copy()
            asset_df.index = pd.to_datetime(asset_df.index)

        if not isinstance(benchmark_df.index, pd.DatetimeIndex):
            benchmark_df = benchmark_df.copy()
            benchmark_df.index = pd.to_datetime(benchmark_df.index)

        # 找到共同的日期范围
        common_dates = asset_df.index.intersection(benchmark_df.index)

        if len(common_dates) == 0:
            raise ValueError("资产和基准没有共同的交易日")

        aligned_asset = asset_df.loc[common_dates].copy()
        aligned_benchmark = benchmark_df.loc[common_dates].copy()

        return aligned_asset, aligned_benchmark

    def _analyze_period(
        self,
        asset_df: pd.DataFrame,
        benchmark_df: pd.DataFrame,
        period: int
    ) -> Dict:
        """
        分析单个周期的相对强度

        Returns:
            {
                'alpha': float,
                'beta': float,
                'relative_strength': float,
                'outperformance': bool,
                'asset_return': float,
                'benchmark_return': float,
                'rank': str
            }
        """
        # 取最近period天的数据
        asset_recent = asset_df['close'].tail(period)
        benchmark_recent = benchmark_df['close'].tail(period)

        # 计算收益率序列
        asset_returns = asset_recent.pct_change().dropna()
        benchmark_returns = benchmark_recent.pct_change().dropna()

        # 确保长度一致
        min_len = min(len(asset_returns), len(benchmark_returns))
        asset_returns = asset_returns.tail(min_len)
        benchmark_returns = benchmark_returns.tail(min_len)

        # 计算Beta
        covariance = np.cov(asset_returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0

        # 计算累计收益率
        asset_total_return = (asset_recent.iloc[-1] / asset_recent.iloc[0] - 1) * 100
        benchmark_total_return = (benchmark_recent.iloc[-1] / benchmark_recent.iloc[0] - 1) * 100

        # 计算Alpha（超额收益）
        alpha = asset_total_return - (beta * benchmark_total_return)

        # 计算相对强度指数
        if benchmark_total_return != 0:
            relative_strength = (asset_total_return / benchmark_total_return) * 100
        else:
            relative_strength = 100.0

        # 判断是否跑赢
        outperformance = asset_total_return > benchmark_total_return

        # 评级
        if alpha > 5:
            rank = '大幅跑赢'
        elif alpha > 2:
            rank = '跑赢大盘'
        elif alpha > -2:
            rank = '接近大盘'
        elif alpha > -5:
            rank = '跑输大盘'
        else:
            rank = '大幅跑输'

        return {
            'alpha': round(alpha, 2),
            'beta': round(beta, 2),
            'relative_strength': round(relative_strength, 1),
            'outperformance': outperformance,
            'asset_return': round(asset_total_return, 2),
            'benchmark_return': round(benchmark_total_return, 2),
            'rank': rank
        }

    def _determine_trend(self, period_analysis: Dict) -> str:
        """
        判断相对强度趋势

        通过比较不同周期的Alpha，判断相对强度是增强还是减弱

        Returns:
            'strengthening' / 'weakening' / 'stable'
        """
        if not period_analysis:
            return 'unknown'

        # 提取各周期的Alpha
        alphas = []
        for period_key in sorted(period_analysis.keys(), key=lambda x: int(x.replace('d', ''))):
            alpha = period_analysis[period_key].get('alpha', 0)
            alphas.append(alpha)

        if len(alphas) < 2:
            return 'stable'

        # 短期Alpha > 长期Alpha => 相对强度增强
        short_term_alpha = np.mean(alphas[:2]) if len(alphas) >= 2 else alphas[0]
        long_term_alpha = np.mean(alphas[-2:]) if len(alphas) >= 2 else alphas[-1]

        diff = short_term_alpha - long_term_alpha

        if diff > 2:
            return 'strengthening'  # 相对强度增强
        elif diff < -2:
            return 'weakening'  # 相对强度减弱
        else:
            return 'stable'  # 相对强度稳定

    def _generate_summary(self, overall: Dict, trend: str) -> str:
        """
        生成分析摘要

        Returns:
            摘要文本
        """
        alpha = overall['alpha']
        beta = overall['beta']
        rank = overall['rank']

        # Alpha描述
        if alpha > 0:
            alpha_desc = f"超额收益+{alpha:.1f}%"
        else:
            alpha_desc = f"超额收益{alpha:.1f}%"

        # Beta描述
        if beta > 1.2:
            beta_desc = "高波动"
        elif beta > 0.8:
            beta_desc = "正常波动"
        else:
            beta_desc = "低波动"

        # 趋势描述
        trend_map = {
            'strengthening': '相对强度增强中📈',
            'weakening': '相对强度减弱中📉',
            'stable': '相对强度稳定➡️'
        }
        trend_desc = trend_map.get(trend, '')

        summary = f"{rank}，{alpha_desc}，{beta_desc}（Beta={beta:.2f}），{trend_desc}"

        return summary


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=252, freq='D')

    # 资产数据（模拟跑赢大盘）
    asset_prices = pd.DataFrame({
        'close': 100 * (1 + np.random.randn(252).cumsum() * 0.02)
    }, index=dates)

    # 基准数据
    benchmark_prices = pd.DataFrame({
        'close': 100 * (1 + np.random.randn(252).cumsum() * 0.015)
    }, index=dates)

    # 测试
    analyzer = RelativeStrengthAnalyzer()
    result = analyzer.analyze(asset_prices, benchmark_prices)

    print("\n=== 相对强度分析结果 ===")
    print(f"Alpha: {result['alpha']:.2f}%")
    print(f"Beta: {result['beta']:.2f}")
    print(f"相对强度: {result['relative_strength']:.1f}")
    print(f"跑赢大盘: {result['outperformance']}")
    print(f"趋势: {result['trend']}")
    print(f"摘要: {result['summary']}")
    print("\n各周期分析:")
    for period, data in result['period_analysis'].items():
        print(f"  {period}: Alpha={data['alpha']:.2f}%, {data['rank']}")
