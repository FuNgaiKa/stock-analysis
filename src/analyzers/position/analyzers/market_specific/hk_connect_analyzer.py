#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股通持股数据分析器
HK Stock Connect Holdings Analyzer

分析北向资金(港股通)的持股变化:
- 持股金额变化
- 持股占比变化
- 资金流入流出
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


class HKConnectAnalyzer:
    """
    港股通持股分析器

    功能:
    1. 获取港股通(南向)资金流向数据
    2. 分析北向资金持股变化
    3. 识别外资偏好股票
    4. 生成资金流向信号
    """

    def __init__(self, lookback_days: int = 60):
        """
        初始化

        Args:
            lookback_days: 回溯天数,默认60天
        """
        self.lookback_days = lookback_days
        logger.info("港股通持股分析器初始化完成")

    def get_south_capital_flow(self, days: int = None) -> pd.DataFrame:
        """
        获取南向资金流向数据(港股通)

        Args:
            days: 获取最近N天数据

        Returns:
            DataFrame with columns: [日期, 沪港通(亿), 深港通(亿), 南向资金(亿), ...]
        """
        try:
            logger.info("获取南向资金流向数据...")

            if days is None:
                days = self.lookback_days

            # 使用akshare获取港股通资金流向
            df = ak.stock_hsgt_fund_flow_summary_em()

            if df is None or df.empty:
                logger.warning("南向资金数据为空")
                return pd.DataFrame()

            # 筛选南向数据
            df_south = df[df['资金方向'] == '南向'].copy()

            # 转换日期格式
            df_south['交易日'] = pd.to_datetime(df_south['交易日'])
            df_south = df_south.sort_values('交易日', ascending=True)

            # 筛选最近N天
            df_south = df_south.tail(days)

            logger.info(f"南向资金数据获取成功: {len(df_south)} 条记录")
            return df_south

        except Exception as e:
            logger.error(f"获取南向资金数据失败: {str(e)}")
            return pd.DataFrame()

    def get_north_capital_flow(self, days: int = None) -> pd.DataFrame:
        """
        获取北向资金流向数据(沪深股通)

        Args:
            days: 获取最近N天数据

        Returns:
            DataFrame with columns: [日期, 沪股通(亿), 深股通(亿), 北向资金(亿), ...]
        """
        try:
            logger.info("获取北向资金流向数据...")

            if days is None:
                days = self.lookback_days

            # 获取沪深港通资金流向
            df = ak.stock_hsgt_fund_flow_summary_em()

            if df is None or df.empty:
                logger.warning("北向资金数据为空")
                return pd.DataFrame()

            # 筛选北向数据
            df_north = df[df['资金方向'] == '北向'].copy()

            # 转换日期格式
            df_north['交易日'] = pd.to_datetime(df_north['交易日'])
            df_north = df_north.sort_values('交易日', ascending=True)

            # 筛选最近N天
            df_north = df_north.tail(days)

            logger.info(f"北向资金数据获取成功: {len(df_north)} 条记录")
            return df_north

        except Exception as e:
            logger.error(f"获取北向资金数据失败: {str(e)}")
            return pd.DataFrame()

    def get_top_holdings(self, market: str = 'hk', top_n: int = 20) -> pd.DataFrame:
        """
        获取港股通/沪深股通前N大持仓股票

        Args:
            market: 'hk'(港股通) 或 'sh'(沪股通) 或 'sz'(深股通)
            top_n: 返回前N名

        Returns:
            DataFrame with columns: [排名, 股票代码, 股票名称, 持股市值, 持股占比, ...]
        """
        try:
            logger.info(f"获取{market}前{top_n}大持仓股票...")

            if market == 'hk':
                # 获取港股通十大成交股
                df = ak.stock_hsgt_stock_statistics_em(symbol='港股通')
            elif market == 'sh':
                # 获取沪股通十大成交股
                df = ak.stock_hsgt_stock_statistics_em(symbol='沪股通')
            elif market == 'sz':
                # 获取深股通十大成交股
                df = ak.stock_hsgt_stock_statistics_em(symbol='深股通')
            else:
                raise ValueError(f"不支持的市场: {market}")

            if df is None or df.empty:
                logger.warning(f"{market}持仓数据为空")
                return pd.DataFrame()

            # 取前N名
            df = df.head(top_n)

            logger.info(f"{market}前{top_n}大持仓获取成功")
            return df

        except Exception as e:
            logger.error(f"获取{market}持仓数据失败: {str(e)}")
            return pd.DataFrame()

    def calculate_flow_metrics(self, df: pd.DataFrame) -> Dict:
        """
        计算资金流向关键指标

        Args:
            df: 资金流向数据DataFrame

        Returns:
            {
                'latest_date': 最新日期,
                'latest_inflow': 最新流入(亿),
                'total_inflow_5d': 5日累计流入(亿),
                'total_inflow_20d': 20日累计流入(亿),
                'avg_inflow_5d': 5日平均流入(亿),
                'avg_inflow_20d': 20日平均流入(亿),
                'inflow_trend': '持续流入'/'持续流出'/'震荡',
                'consecutive_days': 连续流入/流出天数
            }
        """
        if df.empty or len(df) < 2:
            return {}

        try:
            # 最新数据
            latest = df.iloc[-1]
            latest_date = latest['交易日']
            latest_inflow = float(latest.get('资金净流入', 0))

            # 累计流入
            total_inflow_5d = float(df.tail(5)['资金净流入'].sum()) if len(df) >= 5 else latest_inflow
            total_inflow_20d = float(df.tail(20)['资金净流入'].sum()) if len(df) >= 20 else total_inflow_5d

            # 平均流入
            avg_inflow_5d = total_inflow_5d / min(5, len(df))
            avg_inflow_20d = total_inflow_20d / min(20, len(df))

            # 趋势判断
            consecutive_days = 0
            last_sign = np.sign(latest_inflow)

            for i in range(len(df) - 1, -1, -1):
                flow = df.iloc[i]['资金净流入']
                if np.sign(flow) == last_sign:
                    consecutive_days += 1
                else:
                    break

            if consecutive_days >= 3 and latest_inflow > 0:
                inflow_trend = '持续流入'
            elif consecutive_days >= 3 and latest_inflow < 0:
                inflow_trend = '持续流出'
            else:
                inflow_trend = '震荡'

            metrics = {
                'latest_date': latest_date.strftime('%Y-%m-%d'),
                'latest_inflow': latest_inflow,
                'total_inflow_5d': total_inflow_5d,
                'total_inflow_20d': total_inflow_20d,
                'avg_inflow_5d': avg_inflow_5d,
                'avg_inflow_20d': avg_inflow_20d,
                'inflow_trend': inflow_trend,
                'consecutive_days': consecutive_days
            }

            return metrics

        except Exception as e:
            logger.error(f"计算资金流向指标失败: {str(e)}")
            return {}

    def analyze_capital_sentiment(self, metrics: Dict) -> Dict:
        """
        根据资金流向分析市场情绪

        Args:
            metrics: 资金流向指标字典

        Returns:
            {
                'sentiment': '极度乐观'/'乐观'/'中性'/'悲观'/'极度悲观',
                'sentiment_score': 0-100分,
                'signal': '强买入'/'买入'/'中性'/'卖出'/'强卖出',
                'reasoning': 判断理由列表
            }
        """
        if not metrics:
            return {
                'sentiment': '未知',
                'sentiment_score': 50,
                'signal': '中性',
                'reasoning': ['数据不足']
            }

        reasoning = []
        score = 50  # 基础分50分

        # 1. 最新流向
        latest_inflow = metrics.get('latest_inflow', 0)
        if latest_inflow > 50:
            score += 15
            reasoning.append(f'单日净流入{latest_inflow:.1f}亿,外资大幅买入')
        elif latest_inflow > 20:
            score += 10
            reasoning.append(f'单日净流入{latest_inflow:.1f}亿,外资积极买入')
        elif latest_inflow < -50:
            score -= 15
            reasoning.append(f'单日净流出{abs(latest_inflow):.1f}亿,外资大幅卖出')
        elif latest_inflow < -20:
            score -= 10
            reasoning.append(f'单日净流出{abs(latest_inflow):.1f}亿,外资卖出')

        # 2. 5日累计
        total_5d = metrics.get('total_inflow_5d', 0)
        if total_5d > 100:
            score += 15
            reasoning.append(f'5日累计流入{total_5d:.1f}亿,持续买入')
        elif total_5d > 30:
            score += 8
            reasoning.append(f'5日累计流入{total_5d:.1f}亿,稳定流入')
        elif total_5d < -100:
            score -= 15
            reasoning.append(f'5日累计流出{abs(total_5d):.1f}亿,持续卖出')
        elif total_5d < -30:
            score -= 8
            reasoning.append(f'5日累计流出{abs(total_5d):.1f}亿,稳定流出')

        # 3. 趋势判断
        trend = metrics.get('inflow_trend', '震荡')
        consecutive_days = metrics.get('consecutive_days', 0)

        if trend == '持续流入':
            score += 10
            reasoning.append(f'连续{consecutive_days}日净流入,外资看多')
        elif trend == '持续流出':
            score -= 10
            reasoning.append(f'连续{consecutive_days}日净流出,外资看空')
        else:
            reasoning.append('资金流向震荡,外资观望')

        # 限制分数范围
        score = max(0, min(100, score))

        # 情绪判断
        if score >= 80:
            sentiment = '极度乐观'
            signal = '强买入'
        elif score >= 65:
            sentiment = '乐观'
            signal = '买入'
        elif score >= 45:
            sentiment = '中性'
            signal = '中性'
        elif score >= 30:
            sentiment = '悲观'
            signal = '卖出'
        else:
            sentiment = '极度悲观'
            signal = '强卖出'

        return {
            'sentiment': sentiment,
            'sentiment_score': score,
            'signal': signal,
            'reasoning': reasoning
        }

    def comprehensive_analysis(self, direction: str = 'north') -> Dict:
        """
        综合分析港股通/沪深股通资金流向

        Args:
            direction: 'north'(北向,沪深股通) 或 'south'(南向,港股通)

        Returns:
            完整的分析结果字典
        """
        try:
            logger.info(f"开始港股通资金流向综合分析 (方向: {direction})...")

            # 获取数据
            if direction == 'north':
                df = self.get_north_capital_flow()
                market_name = '北向资金(沪深股通)'
            elif direction == 'south':
                df = self.get_south_capital_flow()
                market_name = '南向资金(港股通)'
            else:
                raise ValueError(f"不支持的方向: {direction}")

            if df.empty:
                return {
                    'error': '获取数据失败',
                    'timestamp': datetime.now()
                }

            # 计算指标
            metrics = self.calculate_flow_metrics(df)

            # 分析情绪
            sentiment_analysis = self.analyze_capital_sentiment(metrics)

            # 准备时间序列数据 (最近30天)
            timeseries = []
            for idx, row in df.tail(30).iterrows():
                timeseries.append({
                    'date': row['交易日'].strftime('%Y-%m-%d'),
                    'inflow': float(row.get('资金净流入', 0)),
                    'balance': float(row.get('当日资金余额', 0))
                })

            # 获取前10大持仓(仅北向资金)
            top_holdings = {}
            if direction == 'north':
                try:
                    sh_holdings = self.get_top_holdings(market='sh', top_n=10)
                    sz_holdings = self.get_top_holdings(market='sz', top_n=10)

                    if not sh_holdings.empty:
                        top_holdings['sh'] = sh_holdings.head(10).to_dict('records')
                    if not sz_holdings.empty:
                        top_holdings['sz'] = sz_holdings.head(10).to_dict('records')
                except Exception as e:
                    logger.warning(f"获取持仓数据失败: {str(e)}")

            result = {
                'market': market_name,
                'direction': direction,
                'metrics': metrics,
                'sentiment_analysis': sentiment_analysis,
                'timeseries': timeseries,
                'top_holdings': top_holdings,
                'timestamp': datetime.now()
            }

            logger.info("港股通资金流向综合分析完成")
            return result

        except Exception as e:
            logger.error(f"港股通综合分析失败: {str(e)}")
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
    print("港股通持股数据分析器测试")
    print("=" * 70)

    analyzer = HKConnectAnalyzer(lookback_days=60)

    # 测试北向资金分析
    print("\n1. 测试北向资金(沪深股通)分析")
    print("-" * 70)
    result = analyzer.comprehensive_analysis(direction='north')

    if 'error' not in result:
        metrics = result['metrics']
        sentiment = result['sentiment_analysis']

        print(f"\n📊 资金流向指标:")
        print(f"  日期: {metrics['latest_date']}")
        print(f"  最新流入: {metrics['latest_inflow']:.2f} 亿元")
        print(f"  5日累计: {metrics['total_inflow_5d']:.2f} 亿元")
        print(f"  20日累计: {metrics['total_inflow_20d']:.2f} 亿元")
        print(f"  5日均值: {metrics['avg_inflow_5d']:.2f} 亿元/日")
        print(f"  趋势: {metrics['inflow_trend']}")
        print(f"  连续天数: {metrics['consecutive_days']} 天")

        print(f"\n💡 市场情绪分析:")
        print(f"  情绪: {sentiment['sentiment']}")
        print(f"  评分: {sentiment['sentiment_score']}/100")
        print(f"  信号: {sentiment['signal']}")
        print(f"  理由:")
        for reason in sentiment['reasoning']:
            print(f"    - {reason}")

        print(f"\n📈 时间序列: {len(result['timeseries'])} 天数据")

        if result.get('top_holdings'):
            print(f"\n📋 前10大持仓股票:")
            if 'sh' in result['top_holdings']:
                print(f"  沪股通: {len(result['top_holdings']['sh'])} 只")
            if 'sz' in result['top_holdings']:
                print(f"  深股通: {len(result['top_holdings']['sz'])} 只")
    else:
        print(f"  ❌ 分析失败: {result['error']}")

    # 测试南向资金分析
    print("\n2. 测试南向资金(港股通)分析")
    print("-" * 70)
    result_south = analyzer.comprehensive_analysis(direction='south')

    if 'error' not in result_south:
        metrics_s = result_south['metrics']
        sentiment_s = result_south['sentiment_analysis']

        print(f"\n📊 南向资金指标:")
        print(f"  日期: {metrics_s['latest_date']}")
        print(f"  最新流入: {metrics_s['latest_inflow']:.2f} 亿元")
        print(f"  5日累计: {metrics_s['total_inflow_5d']:.2f} 亿元")
        print(f"  趋势: {metrics_s['inflow_trend']}")

        print(f"\n💡 情绪: {sentiment_s['sentiment']} ({sentiment_s['sentiment_score']}/100)")
        print(f"  信号: {sentiment_s['signal']}")
    else:
        print(f"  ❌ 分析失败: {result_south['error']}")

    print("\n" + "=" * 70)
    print("✅ 港股通持股数据分析器测试完成")
    print("=" * 70)
