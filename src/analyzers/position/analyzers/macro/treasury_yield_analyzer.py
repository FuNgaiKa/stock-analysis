#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美债收益率分析器
Treasury Yield Analyzer

功能:
1. 获取美债收益率曲线数据(2年/5年/10年/30年)
2. 计算收益率曲线斜率
3. 判断倒挂风险
4. 生成经济周期信号

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


class TreasuryYieldAnalyzer:
    """
    美债收益率分析器

    功能:
    1. 获取多期限美债收益率
    2. 分析收益率曲线形态
    3. 检测倒挂信号
    4. 判断经济周期阶段
    """

    # 美债期限对应的yfinance ticker
    TREASURY_TICKERS = {
        '2Y': '^IRX',     # 13周(3个月)国债 - 作为短期替代
        '5Y': '^FVX',     # 5年期国债
        '10Y': '^TNX',    # 10年期国债
        '30Y': '^TYX'     # 30年期国债
    }

    def __init__(self, lookback_days: int = 252):
        """
        初始化美债收益率分析器

        Args:
            lookback_days: 回溯天数,默认252天(1年)
        """
        self.lookback_days = lookback_days
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 1800  # 30分钟缓存
        logger.info("美债收益率分析器初始化完成")

    def get_treasury_yield(self, period: str = '10Y', days: int = None) -> pd.DataFrame:
        """
        获取美债收益率历史数据

        Args:
            period: 期限 ('2Y', '5Y', '10Y', '30Y')
            days: 获取天数,默认使用lookback_days

        Returns:
            DataFrame with columns: [date, yield]
        """
        cache_key = f"treasury_{period}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info(f"使用缓存的{period}美债数据")
                return self.cache[cache_key]

        try:
            ticker = self.TREASURY_TICKERS.get(period)
            if not ticker:
                logger.error(f"不支持的期限: {period}")
                return pd.DataFrame()

            logger.info(f"获取{period}美债收益率数据 ({ticker})...")

            # 获取历史数据
            if days is None:
                days = self.lookback_days

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+30)  # 多取30天以防节假日

            treasury = yf.Ticker(ticker)
            df = treasury.history(start=start_date, end=end_date)

            if df.empty:
                logger.warning(f"{period}美债数据为空")
                return pd.DataFrame()

            # 处理数据
            result = pd.DataFrame({
                'date': df.index,
                'yield': df['Close']  # 收益率以百分比形式存储
            })

            result = result.sort_values('date', ascending=True).reset_index(drop=True)
            result = result.tail(days)

            # 缓存
            self.cache[cache_key] = result
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"{period}美债收益率数据获取成功: {len(result)} 条记录")
            return result

        except Exception as e:
            logger.error(f"获取{period}美债收益率失败: {str(e)}")
            return pd.DataFrame()

    def get_yield_curve(self, periods: List[str] = None) -> Dict:
        """
        获取完整收益率曲线

        Args:
            periods: 期限列表,默认['2Y', '5Y', '10Y', '30Y']

        Returns:
            {
                'date': 最新日期,
                'yields': {
                    '2Y': 收益率,
                    '5Y': 收益率,
                    ...
                },
                'curve_shape': 曲线形态描述
            }
        """
        if periods is None:
            periods = ['5Y', '10Y', '30Y']  # 默认不包括2Y(实际是3个月)

        try:
            yields = {}
            latest_date = None

            for period in periods:
                df = self.get_treasury_yield(period, days=5)
                if not df.empty:
                    yields[period] = float(df.iloc[-1]['yield'])
                    latest_date = df.iloc[-1]['date']

            if not yields:
                return {'error': '无法获取收益率数据'}

            # 分析曲线形态
            curve_shape = self._analyze_curve_shape(yields)

            # 计算曲线斜率
            slope = self._calculate_curve_slope(yields)

            result = {
                'date': latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else str(latest_date),
                'yields': yields,
                'curve_shape': curve_shape,
                'slope': slope,
                'inversion_signal': self._detect_inversion(yields)
            }

            logger.info(f"收益率曲线获取成功: {curve_shape['description']}")
            return result

        except Exception as e:
            logger.error(f"获取收益率曲线失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_curve_shape(self, yields: Dict[str, float]) -> Dict:
        """
        分析收益率曲线形态

        Args:
            yields: 各期限收益率字典

        Returns:
            曲线形态分析结果
        """
        if '10Y' not in yields or '5Y' not in yields:
            return {'shape': 'unknown', 'description': '数据不足', 'emoji': '❓'}

        y10 = yields.get('10Y', 0)
        y5 = yields.get('5Y', 0)
        y30 = yields.get('30Y', 0)

        spread_10_5 = y10 - y5

        # 判断曲线形态
        if spread_10_5 < -0.1:  # 倒挂
            return {
                'shape': 'inverted',
                'description': '倒挂(Inverted)',
                'emoji': '🔴',
                'signal': '衰退风险',
                'interpretation': '收益率曲线倒挂通常预示经济衰退'
            }
        elif spread_10_5 < 0.1:  # 平坦
            return {
                'shape': 'flat',
                'description': '平坦(Flat)',
                'emoji': '🟡',
                'signal': '经济放缓',
                'interpretation': '经济增长可能放缓,需警惕'
            }
        elif spread_10_5 < 0.5:  # 正常
            return {
                'shape': 'normal',
                'description': '正常(Normal)',
                'emoji': '🟢',
                'signal': '健康经济',
                'interpretation': '经济运行正常,健康状态'
            }
        else:  # 陡峭
            return {
                'shape': 'steep',
                'description': '陡峭(Steep)',
                'emoji': '📈',
                'signal': '经济扩张',
                'interpretation': '经济强劲复苏或扩张阶段'
            }

    def _calculate_curve_slope(self, yields: Dict[str, float]) -> Dict:
        """
        计算收益率曲线斜率

        Args:
            yields: 各期限收益率字典

        Returns:
            斜率分析结果
        """
        if '10Y' not in yields or '5Y' not in yields:
            return {'slope': 0, 'description': '数据不足'}

        # 10年-5年利差
        slope_10_5 = yields['10Y'] - yields['5Y']

        # 30年-10年利差(如果有)
        slope_30_10 = None
        if '30Y' in yields and '10Y' in yields:
            slope_30_10 = yields['30Y'] - yields['10Y']

        result = {
            'slope_10Y_5Y': slope_10_5,
            'slope_30Y_10Y': slope_30_10,
            'overall_slope': slope_10_5,
            'description': f"10Y-5Y利差: {slope_10_5:+.2f}%"
        }

        return result

    def _detect_inversion(self, yields: Dict[str, float]) -> Dict:
        """
        检测收益率倒挂

        Args:
            yields: 各期限收益率字典

        Returns:
            倒挂检测结果
        """
        inversions = []

        # 检测10Y-5Y倒挂
        if '10Y' in yields and '5Y' in yields:
            if yields['10Y'] < yields['5Y']:
                inversions.append({
                    'type': '10Y-5Y倒挂',
                    'spread': yields['10Y'] - yields['5Y'],
                    'severity': 'high' if yields['5Y'] - yields['10Y'] > 0.5 else 'medium'
                })

        # 检测30Y-10Y倒挂(罕见但严重)
        if '30Y' in yields and '10Y' in yields:
            if yields['30Y'] < yields['10Y']:
                inversions.append({
                    'type': '30Y-10Y倒挂',
                    'spread': yields['30Y'] - yields['10Y'],
                    'severity': 'critical'
                })

        if inversions:
            return {
                'inverted': True,
                'inversions': inversions,
                'risk_level': 'high',
                'warning': '⚠️ 收益率曲线出现倒挂,经济衰退风险上升'
            }
        else:
            return {
                'inverted': False,
                'risk_level': 'low',
                'status': '✅ 收益率曲线正常'
            }

    def comprehensive_analysis(self) -> Dict:
        """
        综合分析美债收益率

        Returns:
            完整的美债收益率分析结果
        """
        try:
            logger.info("开始美债收益率综合分析...")

            # 1. 获取收益率曲线
            curve = self.get_yield_curve()

            if 'error' in curve:
                return {
                    'error': curve['error'],
                    'timestamp': datetime.now()
                }

            # 2. 获取历史数据(用于趋势分析)
            df_10y = self.get_treasury_yield('10Y', days=60)

            trend = None
            if not df_10y.empty and len(df_10y) >= 20:
                # 计算趋势
                recent_avg = df_10y.tail(5)['yield'].mean()
                older_avg = df_10y.iloc[-20:-15]['yield'].mean()

                if recent_avg > older_avg + 0.1:
                    trend = {'direction': 'rising', 'emoji': '📈', 'description': '收益率上升'}
                elif recent_avg < older_avg - 0.1:
                    trend = {'direction': 'falling', 'emoji': '📉', 'description': '收益率下降'}
                else:
                    trend = {'direction': 'stable', 'emoji': '➡️', 'description': '收益率平稳'}

            # 3. 汇总结果
            result = {
                'date': curve['date'],
                'yields': curve['yields'],
                'curve_shape': curve['curve_shape'],
                'slope': curve['slope'],
                'inversion_signal': curve['inversion_signal'],
                'trend': trend,
                'timestamp': datetime.now()
            }

            logger.info("美债收益率综合分析完成")
            return result

        except Exception as e:
            logger.error(f"美债收益率综合分析失败: {str(e)}")
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
    print("美债收益率分析器测试")
    print("=" * 80)

    analyzer = TreasuryYieldAnalyzer(lookback_days=252)

    # 测试综合分析
    print("\n测试美债收益率综合分析")
    print("-" * 80)
    result = analyzer.comprehensive_analysis()

    if 'error' not in result:
        print(f"\n📊 美债收益率分析 ({result['date']})")
        print(f"\n收益率:")
        for period, value in result['yields'].items():
            print(f"  {period}: {value:.2f}%")

        shape = result['curve_shape']
        print(f"\n曲线形态: {shape['emoji']} {shape['description']}")
        print(f"  信号: {shape['signal']}")
        print(f"  解读: {shape['interpretation']}")

        slope = result['slope']
        print(f"\n曲线斜率:")
        print(f"  {slope['description']}")

        inversion = result['inversion_signal']
        if inversion['inverted']:
            print(f"\n⚠️ 倒挂警告: {inversion['warning']}")
            for inv in inversion['inversions']:
                print(f"  - {inv['type']}: {inv['spread']:+.2f}% (严重程度: {inv['severity']})")
        else:
            print(f"\n{inversion['status']}")

        if result.get('trend'):
            trend = result['trend']
            print(f"\n趋势: {trend['emoji']} {trend['description']}")
    else:
        print(f"  ❌ 分析失败: {result['error']}")

    print("\n" + "=" * 80)
    print("✅ 美债收益率分析器测试完成")
    print("=" * 80)
