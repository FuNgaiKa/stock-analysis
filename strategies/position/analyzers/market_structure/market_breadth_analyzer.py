#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场宽度分析器 - 新高新低指数
Market Breadth Analyzer - New High/Low Index

市场宽度指标分析:
- 创新高个股数 (20/60/120日)
- 创新低个股数 (20/60/120日)
- 新高新低比率
- 市场宽度得分
- 趋势强度判断

作者: Claude Code
日期: 2025-10-12
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class MarketBreadthAnalyzer:
    """
    市场宽度分析器

    功能:
    1. 获取新高新低统计数据
    2. 计算市场宽度指标
    3. 分析市场内部强度
    4. 生成交易信号
    """

    def __init__(self, lookback_days: int = 60):
        """
        初始化

        Args:
            lookback_days: 回溯天数,默认60天
        """
        self.lookback_days = lookback_days
        logger.info("市场宽度分析器初始化完成")

    def get_high_low_data(self) -> pd.DataFrame:
        """
        获取A股新高新低统计数据

        Returns:
            DataFrame with columns: [date, close, high20, low20, high60, low60, high120, low120]
        """
        try:
            logger.info("获取新高新低数据...")
            df = ak.stock_a_high_low_statistics()

            if df is None or df.empty:
                logger.warning("新高新低数据为空")
                return pd.DataFrame()

            # 确保日期列格式正确
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date', ascending=True)

            # 筛选最近N天
            df = df.tail(self.lookback_days)

            logger.info(f"新高新低数据获取成功: {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取新高新低数据失败: {str(e)}")
            return pd.DataFrame()

    def calculate_breadth_metrics(self, df: pd.DataFrame) -> Dict:
        """
        计算市场宽度指标

        Args:
            df: 新高新低数据DataFrame

        Returns:
            {
                'latest_date': 最新日期,
                'index_close': 指数收盘价,
                'high20': 20日新高个股数,
                'low20': 20日新低个股数,
                'ratio20': 新高新低比率(20日),
                'high60': 60日新高个股数,
                'low60': 60日新低个股数,
                'ratio60': 新高新低比率(60日),
                'high120': 120日新高个股数,
                'low120': 120日新低个股数,
                'ratio120': 新高新低比率(120日),
                'avg_ratio': 平均比率,
                'breadth_score': 市场宽度得分(0-100),
                'trend': '极强'/'强'/'中性'/'弱'/'极弱'
            }
        """
        if df.empty or len(df) < 1:
            return {}

        try:
            # 最新数据
            latest = df.iloc[-1]
            latest_date = latest['date']
            index_close = float(latest['close'])

            # 新高新低个股数
            high20 = int(latest['high20'])
            low20 = int(latest['low20'])
            high60 = int(latest['high60'])
            low60 = int(latest['low60'])
            high120 = int(latest['high120'])
            low120 = int(latest['low120'])

            # 新高新低比率 (避免除零)
            ratio20 = high20 / low20 if low20 > 0 else (10.0 if high20 > 0 else 1.0)
            ratio60 = high60 / low60 if low60 > 0 else (10.0 if high60 > 0 else 1.0)
            ratio120 = high120 / low120 if low120 > 0 else (10.0 if high120 > 0 else 1.0)

            # 平均比率
            avg_ratio = (ratio20 + ratio60 + ratio120) / 3

            # 市场宽度得分 (0-100)
            score = 50  # 基础分

            # 20日新高新低评分
            if ratio20 > 3:
                score += 15
            elif ratio20 > 1.5:
                score += 10
            elif ratio20 > 1:
                score += 5
            elif ratio20 < 0.33:
                score -= 15
            elif ratio20 < 0.67:
                score -= 10
            else:
                score -= 5

            # 60日新高新低评分
            if ratio60 > 3:
                score += 15
            elif ratio60 > 1.5:
                score += 10
            elif ratio60 > 1:
                score += 5
            elif ratio60 < 0.33:
                score -= 15
            elif ratio60 < 0.67:
                score -= 10
            else:
                score -= 5

            # 120日新高新低评分
            if ratio120 > 3:
                score += 10
            elif ratio120 > 1.5:
                score += 7
            elif ratio120 > 1:
                score += 3
            elif ratio120 < 0.33:
                score -= 10
            elif ratio120 < 0.67:
                score -= 7
            else:
                score -= 3

            # 新高绝对数量评分
            if high20 > 500:
                score += 10
            elif high20 > 300:
                score += 5
            elif high20 < 100:
                score -= 5

            # 限制分数范围
            score = max(0, min(100, score))

            # 趋势判断
            if score >= 80:
                trend = '极强'
            elif score >= 65:
                trend = '强'
            elif score >= 45:
                trend = '中性'
            elif score >= 30:
                trend = '弱'
            else:
                trend = '极弱'

            metrics = {
                'latest_date': latest_date.strftime('%Y-%m-%d'),
                'index_close': index_close,
                'high20': high20,
                'low20': low20,
                'ratio20': ratio20,
                'high60': high60,
                'low60': low60,
                'ratio60': ratio60,
                'high120': high120,
                'low120': low120,
                'ratio120': ratio120,
                'avg_ratio': avg_ratio,
                'breadth_score': score,
                'trend': trend
            }

            return metrics

        except Exception as e:
            logger.error(f"计算市场宽度指标失败: {str(e)}")
            return {}

    def analyze_market_strength(self, metrics: Dict) -> Dict:
        """
        分析市场内部强度

        Args:
            metrics: 市场宽度指标字典

        Returns:
            {
                'strength': '极强'/'强'/'中性'/'弱'/'极弱',
                'strength_score': 0-100分,
                'signal': '强买入'/'买入'/'中性'/'卖出'/'强卖出',
                'reasoning': 判断理由列表
            }
        """
        if not metrics:
            return {
                'strength': '未知',
                'strength_score': 50,
                'signal': '中性',
                'reasoning': ['数据不足']
            }

        reasoning = []
        score = metrics.get('breadth_score', 50)

        # 1. 20日新高新低比率分析
        ratio20 = metrics.get('ratio20', 1)
        high20 = metrics.get('high20', 0)
        low20 = metrics.get('low20', 0)

        if ratio20 > 3:
            reasoning.append(f'20日新高{high20}只 > 新低{low20}只×3,短期趋势极强')
        elif ratio20 > 1.5:
            reasoning.append(f'20日新高{high20}只 > 新低{low20}只,短期偏强')
        elif ratio20 < 0.33:
            reasoning.append(f'20日新高{high20}只 < 新低{low20}只×3,短期趋势极弱')
        elif ratio20 < 0.67:
            reasoning.append(f'20日新高{high20}只 < 新低{low20}只,短期偏弱')
        else:
            reasoning.append(f'20日新高新低比率{ratio20:.2f},短期中性')

        # 2. 60日新高新低比率分析
        ratio60 = metrics.get('ratio60', 1)
        high60 = metrics.get('high60', 0)
        low60 = metrics.get('low60', 0)

        if ratio60 > 2:
            reasoning.append(f'60日新高{high60}只显著多于新低{low60}只,中期趋势强劲')
        elif ratio60 < 0.5:
            reasoning.append(f'60日新高{high60}只显著少于新低{low60}只,中期趋势疲软')

        # 3. 120日新高新低比率分析
        ratio120 = metrics.get('ratio120', 1)
        high120 = metrics.get('high120', 0)
        low120 = metrics.get('low120')

        if ratio120 > 2:
            reasoning.append(f'120日新高{high120}只 >> 新低{low120}只,长期趋势向上')
        elif ratio120 < 0.5:
            reasoning.append(f'120日新高{high120}只 << 新低{low120}只,长期趋势向下')

        # 4. 平均比率
        avg_ratio = metrics.get('avg_ratio', 1)
        if avg_ratio > 2:
            reasoning.append(f'平均新高新低比率{avg_ratio:.2f},市场宽度优秀')
        elif avg_ratio < 0.5:
            reasoning.append(f'平均新高新低比率{avg_ratio:.2f},市场宽度较差')

        # 信号判断
        if score >= 80:
            strength = '极强'
            signal = '强买入'
        elif score >= 65:
            strength = '强'
            signal = '买入'
        elif score >= 45:
            strength = '中性'
            signal = '中性'
        elif score >= 30:
            strength = '弱'
            signal = '卖出'
        else:
            strength = '极弱'
            signal = '强卖出'

        return {
            'strength': strength,
            'strength_score': score,
            'signal': signal,
            'reasoning': reasoning
        }

    def comprehensive_analysis(self) -> Dict:
        """
        综合市场宽度分析

        Returns:
            完整的市场宽度分析结果
        """
        try:
            logger.info("开始市场宽度综合分析...")

            # 获取数据
            df = self.get_high_low_data()

            if df.empty:
                return {
                    'error': '获取数据失败',
                    'timestamp': datetime.now()
                }

            # 计算指标
            metrics = self.calculate_breadth_metrics(df)

            # 分析市场强度
            strength_analysis = self.analyze_market_strength(metrics)

            # 准备时间序列数据 (最近30天)
            timeseries = []
            for idx, row in df.tail(30).iterrows():
                high_low_ratio = row['high20'] / row['low20'] if row['low20'] > 0 else 10
                timeseries.append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'close': float(row['close']),
                    'high20': int(row['high20']),
                    'low20': int(row['low20']),
                    'high60': int(row['high60']),
                    'low60': int(row['low60']),
                    'ratio20': float(high_low_ratio)
                })

            result = {
                'metrics': metrics,
                'strength_analysis': strength_analysis,
                'timeseries': timeseries,
                'timestamp': datetime.now()
            }

            logger.info("市场宽度综合分析完成")
            return result

        except Exception as e:
            logger.error(f"市场宽度综合分析失败: {str(e)}")
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

    print("=" * 70)
    print("市场宽度分析器测试")
    print("=" * 70)

    analyzer = MarketBreadthAnalyzer(lookback_days=60)

    print("\n📊 A股市场宽度分析")
    print("-" * 70)
    result = analyzer.comprehensive_analysis()

    if 'error' not in result:
        metrics = result['metrics']
        strength = result['strength_analysis']

        print(f"\n📈 市场宽度指标:")
        print(f"  日期: {metrics['latest_date']}")
        print(f"  指数收盘: {metrics['index_close']:.2f}")
        print(f"  20日新高: {metrics['high20']}只")
        print(f"  20日新低: {metrics['low20']}只")
        print(f"  20日比率: {metrics['ratio20']:.2f}")
        print(f"  60日新高: {metrics['high60']}只")
        print(f"  60日新低: {metrics['low60']}只")
        print(f"  60日比率: {metrics['ratio60']:.2f}")
        print(f"  120日新高: {metrics['high120']}只")
        print(f"  120日新低: {metrics['low120']}只")
        print(f"  120日比率: {metrics['ratio120']:.2f}")
        print(f"  平均比率: {metrics['avg_ratio']:.2f}")
        print(f"  市场宽度得分: {metrics['breadth_score']}/100")
        print(f"  市场趋势: {metrics['trend']}")

        print(f"\n💡 市场强度分析:")
        print(f"  内部强度: {strength['strength']}")
        print(f"  强度得分: {strength['strength_score']}/100")
        print(f"  交易信号: {strength['signal']}")
        print(f"  分析理由:")
        for reason in strength['reasoning']:
            print(f"    - {reason}")

        print(f"\n📊 时间序列: {len(result['timeseries'])} 天数据")
    else:
        print(f"  ❌ 分析失败: {result['error']}")

    print("\n" + "=" * 70)
    print("✅ 市场宽度分析器测试完成")
    print("=" * 70)
