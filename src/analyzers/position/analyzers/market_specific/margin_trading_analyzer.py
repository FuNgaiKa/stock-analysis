#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融资融券深度分析器
Margin Trading Analyzer

A股特色杠杆指标分析:
- 融资融券余额
- 融资买入额
- 融券卖出量
- 杠杆率变化
- 市场情绪判断

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


class MarginTradingAnalyzer:
    """
    融资融券分析器

    功能:
    1. 获取融资融券余额数据
    2. 计算杠杆率指标
    3. 分析市场情绪
    4. 生成交易信号
    """

    def __init__(self, lookback_days: int = 252):
        """
        初始化

        Args:
            lookback_days: 回溯天数,默认252天(1年)
        """
        self.lookback_days = lookback_days
        logger.info("融资融券分析器初始化完成")

    def get_margin_data_sse(self, days: int = None) -> pd.DataFrame:
        """
        获取上交所融资融券数据

        Args:
            days: 获取最近N天数据,默认使用lookback_days

        Returns:
            DataFrame with columns: [信用交易日期, 融资余额, 融资买入额, 融券余量, ...]
        """
        try:
            logger.info("获取上交所融资融券数据(宏观接口)...")
            # 使用宏观数据接口获取最新数据
            df = ak.macro_china_market_margin_sh()

            if df is None or df.empty:
                logger.warning("上交所融资融券数据为空")
                return pd.DataFrame()

            # 统一列名格式
            df = df.rename(columns={
                '日期': '信用交易日期',
                '融资买入额': '融资买入额',
                '融资余额': '融资余额',
                '融券卖出量': '融券卖出量',
                '融券余量': '融券余量',
                '融券余额': '融券余量金额',
                '融资融券余额': '融资融券余额'
            })

            # 转换日期格式
            df['信用交易日期'] = pd.to_datetime(df['信用交易日期'])
            df = df.sort_values('信用交易日期', ascending=True)

            # 筛选最近N天
            if days is None:
                days = self.lookback_days

            df = df.tail(days)

            logger.info(f"上交所融资融券数据获取成功: {len(df)} 条记录, 最新日期: {df.iloc[-1]['信用交易日期'].strftime('%Y-%m-%d')}")
            return df

        except Exception as e:
            logger.error(f"获取上交所融资融券数据失败: {str(e)}")
            return pd.DataFrame()

    def get_margin_data_szse(self, days: int = None) -> pd.DataFrame:
        """
        获取深交所融资融券数据

        Args:
            days: 获取最近N天数据

        Returns:
            DataFrame with columns: [信用交易日期, 融资余额, 融资买入额, 融券余量, ...]
        """
        try:
            logger.info("获取深交所融资融券数据(宏观接口)...")
            # 使用宏观数据接口获取最新数据
            df = ak.macro_china_market_margin_sz()

            if df is None or df.empty:
                logger.warning("深交所融资融券数据为空")
                return pd.DataFrame()

            # 统一列名格式
            df = df.rename(columns={
                '日期': '信用交易日期',
                '融资买入额': '融资买入额',
                '融资余额': '融资余额',
                '融券卖出量': '融券卖出量',
                '融券余量': '融券余量',
                '融券余额': '融券余量金额',
                '融资融券余额': '融资融券余额'
            })

            # 转换日期格式
            df['信用交易日期'] = pd.to_datetime(df['信用交易日期'])
            df = df.sort_values('信用交易日期', ascending=True)

            # 筛选最近N天
            if days is None:
                days = self.lookback_days

            df = df.tail(days)

            logger.info(f"深交所融资融券数据获取成功: {len(df)} 条记录, 最新日期: {df.iloc[-1]['信用交易日期'].strftime('%Y-%m-%d')}")
            return df

        except Exception as e:
            logger.error(f"获取深交所融资融券数据失败: {str(e)}")
            return pd.DataFrame()

    def calculate_margin_metrics(self, df: pd.DataFrame) -> Dict:
        """
        计算融资融券关键指标

        Args:
            df: 融资融券数据DataFrame

        Returns:
            {
                'latest_margin_balance': 最新融资余额,
                'latest_short_balance': 最新融券余额,
                'margin_balance_ma5': 5日均值,
                'margin_balance_ma20': 20日均值,
                'margin_change_pct_1d': 单日变化率,
                'margin_change_pct_5d': 5日变化率,
                'margin_change_pct_20d': 20日变化率,
                'leverage_ratio': 杠杆率 (融资余额/融券余额),
                'percentile_252d': 252日历史分位数,
                'trend': '上升'/'下降'/'震荡'
            }
        """
        if df.empty or len(df) < 2:
            return {}

        try:
            # 最新数据
            latest = df.iloc[-1]
            latest_date = latest['信用交易日期']

            # 融资余额
            margin_balance = float(latest['融资余额'])
            # 融券余额
            short_balance = float(latest['融券余量金额']) if '融券余量金额' in latest else 0

            # 移动平均
            margin_balance_ma5 = float(df['融资余额'].tail(5).mean())
            margin_balance_ma20 = float(df['融资余额'].tail(20).mean()) if len(df) >= 20 else margin_balance_ma5

            # 变化率
            margin_1d_ago = float(df.iloc[-2]['融资余额'])
            margin_5d_ago = float(df.iloc[-6]['融资余额']) if len(df) >= 6 else margin_1d_ago
            margin_20d_ago = float(df.iloc[-21]['融资余额']) if len(df) >= 21 else margin_5d_ago

            margin_change_1d = (margin_balance - margin_1d_ago) / margin_1d_ago * 100
            margin_change_5d = (margin_balance - margin_5d_ago) / margin_5d_ago * 100
            margin_change_20d = (margin_balance - margin_20d_ago) / margin_20d_ago * 100

            # 杠杆率 (融资/融券比值)
            leverage_ratio = margin_balance / short_balance if short_balance > 0 else 0

            # 历史分位数
            percentile_252d = (df['融资余额'] < margin_balance).sum() / len(df) * 100

            # 趋势判断
            if margin_balance > margin_balance_ma5 and margin_balance_ma5 > margin_balance_ma20:
                trend = '上升'
            elif margin_balance < margin_balance_ma5 and margin_balance_ma5 < margin_balance_ma20:
                trend = '下降'
            else:
                trend = '震荡'

            metrics = {
                'latest_date': latest_date.strftime('%Y-%m-%d'),
                'latest_margin_balance': margin_balance,
                'latest_short_balance': short_balance,
                'latest_total_balance': margin_balance + short_balance,
                'margin_balance_ma5': margin_balance_ma5,
                'margin_balance_ma20': margin_balance_ma20,
                'margin_change_pct_1d': margin_change_1d,
                'margin_change_pct_5d': margin_change_5d,
                'margin_change_pct_20d': margin_change_20d,
                'leverage_ratio': leverage_ratio,
                'percentile_252d': percentile_252d,
                'trend': trend
            }

            return metrics

        except Exception as e:
            logger.error(f"计算融资融券指标失败: {str(e)}")
            return {}

    def analyze_market_sentiment(self, metrics: Dict) -> Dict:
        """
        根据融资融券指标分析市场情绪

        Args:
            metrics: 融资融券指标字典

        Returns:
            {
                'sentiment': '极度乐观'/'乐观'/'中性'/'悲观'/'极度悲观',
                'sentiment_score': 0-100分,
                'signal': '做多'/'观望'/'做空',
                'reasoning': 判断理由列表
            }
        """
        if not metrics:
            return {
                'sentiment': '未知',
                'sentiment_score': 50,
                'signal': '观望',
                'reasoning': ['数据不足']
            }

        reasoning = []
        score = 50  # 基础分50分(中性)

        # 1. 融资余额变化
        margin_change_1d = metrics.get('margin_change_pct_1d', 0)
        margin_change_5d = metrics.get('margin_change_pct_5d', 0)

        if margin_change_1d > 1:
            score += 10
            reasoning.append(f'单日融资增加{margin_change_1d:.2f}%,市场积极')
        elif margin_change_1d < -1:
            score -= 10
            reasoning.append(f'单日融资减少{abs(margin_change_1d):.2f}%,市场谨慎')

        if margin_change_5d > 3:
            score += 15
            reasoning.append(f'5日融资增加{margin_change_5d:.2f}%,做多情绪升温')
        elif margin_change_5d < -3:
            score -= 15
            reasoning.append(f'5日融资减少{abs(margin_change_5d):.2f}%,做空情绪增强')

        # 2. 趋势判断
        trend = metrics.get('trend', '震荡')
        if trend == '上升':
            score += 10
            reasoning.append('融资余额处于上升趋势')
        elif trend == '下降':
            score -= 10
            reasoning.append('融资余额处于下降趋势')
        else:
            reasoning.append('融资余额震荡整理')

        # 3. 历史分位数
        percentile = metrics.get('percentile_252d', 50)
        if percentile > 90:
            score -= 10
            reasoning.append(f'融资余额处于历史高位({percentile:.0f}%分位),警惕过度乐观')
        elif percentile > 70:
            score -= 5
            reasoning.append(f'融资余额较高({percentile:.0f}%分位),注意风险')
        elif percentile < 10:
            score += 10
            reasoning.append(f'融资余额处于历史低位({percentile:.0f}%分位),可能超跌')
        elif percentile < 30:
            score += 5
            reasoning.append(f'融资余额较低({percentile:.0f}%分位),市场谨慎')

        # 4. 杠杆率
        leverage = metrics.get('leverage_ratio', 0)
        if leverage > 15:
            reasoning.append(f'杠杆率较高({leverage:.1f}倍),做多意愿强')
        elif leverage < 10:
            reasoning.append(f'杠杆率较低({leverage:.1f}倍),做空意愿相对增强')

        # 限制分数范围
        score = max(0, min(100, score))

        # 情绪判断
        if score >= 80:
            sentiment = '极度乐观'
            signal = '谨慎做多'
        elif score >= 65:
            sentiment = '乐观'
            signal = '做多'
        elif score >= 45:
            sentiment = '中性'
            signal = '观望'
        elif score >= 30:
            sentiment = '悲观'
            signal = '做空'
        else:
            sentiment = '极度悲观'
            signal = '谨慎做空'

        return {
            'sentiment': sentiment,
            'sentiment_score': score,
            'signal': signal,
            'reasoning': reasoning
        }

    def comprehensive_analysis(self, market: str = 'sse') -> Dict:
        """
        综合分析融资融券数据

        Args:
            market: 'sse'(上交所) 或 'szse'(深交所)

        Returns:
            完整的分析结果字典
        """
        try:
            logger.info(f"开始融资融券综合分析 (市场: {market})...")

            # 获取数据
            if market == 'sse':
                df = self.get_margin_data_sse()
            elif market == 'szse':
                df = self.get_margin_data_szse()
            else:
                raise ValueError(f"不支持的市场: {market}")

            if df.empty:
                return {
                    'error': '获取数据失败',
                    'timestamp': datetime.now()
                }

            # 计算指标
            metrics = self.calculate_margin_metrics(df)

            # 分析情绪
            sentiment_analysis = self.analyze_market_sentiment(metrics)

            # 准备时间序列数据 (最近60天)
            timeseries = []
            for idx, row in df.tail(60).iterrows():
                timeseries.append({
                    'date': row['信用交易日期'].strftime('%Y-%m-%d'),
                    'margin_balance': float(row['融资余额']),
                    'short_balance': float(row.get('融券余量金额', 0)),
                    'margin_buy': float(row.get('融资买入额', 0)),
                    'short_sell': float(row.get('融券卖出量', 0))
                })

            result = {
                'market': '上交所' if market == 'sse' else '深交所',
                'metrics': metrics,
                'sentiment_analysis': sentiment_analysis,
                'timeseries': timeseries,
                'timestamp': datetime.now()
            }

            logger.info("融资融券综合分析完成")
            return result

        except Exception as e:
            logger.error(f"融资融券综合分析失败: {str(e)}")
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
    print("融资融券深度分析器测试")
    print("=" * 70)

    analyzer = MarginTradingAnalyzer(lookback_days=252)

    # 测试上交所数据
    print("\n1. 测试上交所融资融券分析")
    print("-" * 70)
    result = analyzer.comprehensive_analysis(market='sse')

    if 'error' not in result:
        metrics = result['metrics']
        sentiment = result['sentiment_analysis']

        print(f"\n📊 融资融券指标:")
        print(f"  日期: {metrics['latest_date']}")
        print(f"  融资余额: {metrics['latest_margin_balance'] / 1e12:.2f} 万亿")
        print(f"  融券余额: {metrics['latest_short_balance'] / 1e12:.2f} 万亿")
        print(f"  杠杆率: {metrics['leverage_ratio']:.1f}倍")
        print(f"  单日变化: {metrics['margin_change_pct_1d']:+.2f}%")
        print(f"  5日变化: {metrics['margin_change_pct_5d']:+.2f}%")
        print(f"  历史分位: {metrics['percentile_252d']:.1f}%")
        print(f"  趋势: {metrics['trend']}")

        print(f"\n💡 市场情绪分析:")
        print(f"  情绪: {sentiment['sentiment']}")
        print(f"  评分: {sentiment['sentiment_score']}/100")
        print(f"  信号: {sentiment['signal']}")
        print(f"  理由:")
        for reason in sentiment['reasoning']:
            print(f"    - {reason}")

        print(f"\n📈 时间序列: {len(result['timeseries'])} 天数据")
    else:
        print(f"  ❌ 分析失败: {result['error']}")

    print("\n" + "=" * 70)
    print("✅ 融资融券分析器测试完成")
    print("=" * 70)
