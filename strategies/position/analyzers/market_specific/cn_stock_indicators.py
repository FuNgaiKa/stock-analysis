#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股特色指标分析器
CN Stock Indicators Analyzer

专门针对A股市场的特色指标:
1. 量比 (Volume Ratio) - 当日成交量/5日平均成交量
2. 换手率 (Turnover Rate) - 成交量/流通股本
3. MACD柱状图能量
4. 港股通持股数据

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


class CNStockIndicators:
    """
    A股特色指标分析器

    针对A股市场的特殊性,提供以下分析:
    - 量比分析 (衡量当日成交活跃度)
    - 换手率分析 (衡量市场流动性)
    - MACD能量分析
    """

    def __init__(self):
        """初始化"""
        logger.info("A股特色指标分析器初始化完成")

    def calculate_volume_ratio(
        self,
        df: pd.DataFrame,
        ma_period: int = 5
    ) -> pd.DataFrame:
        """
        计算量比指标

        量比 = 当日成交量 / 过去N日平均成交量

        量比含义:
        - 量比 > 2: 成交量异常放大,可能有重大消息
        - 量比 > 1.5: 成交量明显放大
        - 量比 0.8-1.2: 成交量正常
        - 量比 < 0.5: 成交量萎缩

        Args:
            df: DataFrame with 'volume' column
            ma_period: 均量周期,默认5日

        Returns:
            添加了'volume_ma'和'volume_ratio'列的DataFrame
        """
        df = df.copy()

        if 'volume' not in df.columns:
            logger.warning("DataFrame缺少volume列")
            return df

        # 计算N日平均成交量
        df['volume_ma'] = df['volume'].rolling(window=ma_period).mean()

        # 计算量比
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        return df

    def analyze_volume_ratio(self, volume_ratio: float) -> Dict:
        """
        分析量比信号

        Args:
            volume_ratio: 量比值

        Returns:
            {
                'level': '极度放量'/'显著放量'/'正常'/'缩量'/'极度缩量',
                'signal': '强烈关注'/'关注'/'正常'/'观望',
                'description': 描述文字,
                'score': 0-100评分
            }
        """
        if volume_ratio >= 3.0:
            return {
                'level': '极度放量',
                'signal': '强烈关注',
                'description': f'量比{volume_ratio:.2f}倍,成交量异常放大,可能有重大消息或主力行为',
                'score': 95
            }
        elif volume_ratio >= 2.0:
            return {
                'level': '显著放量',
                'signal': '关注',
                'description': f'量比{volume_ratio:.2f}倍,成交量明显放大,市场活跃度高',
                'score': 80
            }
        elif volume_ratio >= 1.5:
            return {
                'level': '温和放量',
                'signal': '正常偏强',
                'description': f'量比{volume_ratio:.2f}倍,成交量有所放大,市场参与度提升',
                'score': 65
            }
        elif volume_ratio >= 0.8:
            return {
                'level': '正常',
                'signal': '正常',
                'description': f'量比{volume_ratio:.2f}倍,成交量正常,市场平稳',
                'score': 50
            }
        elif volume_ratio >= 0.5:
            return {
                'level': '缩量',
                'signal': '观望',
                'description': f'量比{volume_ratio:.2f}倍,成交量萎缩,市场观望情绪浓厚',
                'score': 30
            }
        else:
            return {
                'level': '极度缩量',
                'signal': '观望',
                'description': f'量比{volume_ratio:.2f}倍,成交量严重萎缩,市场极度冷清',
                'score': 10
            }

    def calculate_turnover_rate(
        self,
        df: pd.DataFrame,
        circulating_shares: float = None
    ) -> pd.DataFrame:
        """
        计算换手率

        换手率 = 成交量 / 流通股本 * 100%

        换手率含义:
        - 换手率 > 7%: 高换手,活跃股
        - 换手率 3-7%: 相对活跃
        - 换手率 1-3%: 正常
        - 换手率 < 1%: 冷门股

        Args:
            df: DataFrame with 'volume' column
            circulating_shares: 流通股本(股数),如为None则使用简化计算

        Returns:
            添加了'turnover_rate'列的DataFrame
        """
        df = df.copy()

        if 'volume' not in df.columns:
            logger.warning("DataFrame缺少volume列")
            return df

        if circulating_shares is not None:
            # 精确计算
            df['turnover_rate'] = (df['volume'] / circulating_shares) * 100
        else:
            # 简化计算: 使用成交额/流通市值的近似
            # 如果有成交额和收盘价,可以估算
            if 'amount' in df.columns and 'close' in df.columns:
                # 估算流通市值 = 成交额 / (成交量 / 总成交量)
                # 这是一个简化公式,实际应用需要获取真实流通股本
                logger.warning("未提供流通股本,使用简化计算")
                # 假设平均换手率约2%
                avg_volume = df['volume'].mean()
                df['turnover_rate'] = (df['volume'] / avg_volume) * 2
            else:
                logger.warning("无法计算换手率,缺少必要数据")
                df['turnover_rate'] = np.nan

        return df

    def analyze_turnover_rate(self, turnover_rate: float) -> Dict:
        """
        分析换手率信号

        Args:
            turnover_rate: 换手率(%)

        Returns:
            {
                'level': '极度活跃'/'活跃'/'正常'/'低迷'/'极度低迷',
                'signal': '高关注'/'关注'/'正常'/'观望',
                'description': 描述文字,
                'score': 0-100评分,
                'risk_level': '高'/'中'/'低'
            }
        """
        if turnover_rate >= 15:
            return {
                'level': '极度活跃',
                'signal': '高关注',
                'description': f'换手率{turnover_rate:.2f}%,极度活跃,可能存在主力资金操作或重大题材',
                'score': 90,
                'risk_level': '高'
            }
        elif turnover_rate >= 7:
            return {
                'level': '活跃',
                'signal': '关注',
                'description': f'换手率{turnover_rate:.2f}%,市场活跃,筹码流动性好',
                'score': 75,
                'risk_level': '中'
            }
        elif turnover_rate >= 3:
            return {
                'level': '相对活跃',
                'signal': '正常偏强',
                'description': f'换手率{turnover_rate:.2f}%,市场相对活跃',
                'score': 60,
                'risk_level': '中'
            }
        elif turnover_rate >= 1:
            return {
                'level': '正常',
                'signal': '正常',
                'description': f'换手率{turnover_rate:.2f}%,市场正常,筹码较稳定',
                'score': 50,
                'risk_level': '低'
            }
        elif turnover_rate >= 0.5:
            return {
                'level': '低迷',
                'signal': '观望',
                'description': f'换手率{turnover_rate:.2f}%,市场低迷,交易不活跃',
                'score': 30,
                'risk_level': '低'
            }
        else:
            return {
                'level': '极度低迷',
                'signal': '观望',
                'description': f'换手率{turnover_rate:.2f}%,市场极度低迷,几乎无人交易',
                'score': 10,
                'risk_level': '低'
            }

    def calculate_macd_energy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算MACD柱状图能量

        MACD能量 = MACD柱状图面积(绝对值累计)
        可用于判断趋势强度

        Args:
            df: DataFrame with 'macd_hist' column

        Returns:
            添加了'macd_energy'列的DataFrame
        """
        df = df.copy()

        if 'macd_hist' not in df.columns:
            # 如果没有macd_hist,计算MACD
            from strategies.trading.signal_generators.technical_indicators import TechnicalIndicators
            calc = TechnicalIndicators()
            df = calc.calculate_macd(df)

        # 计算MACD能量 (20日滚动累计绝对值)
        df['macd_energy'] = df['macd_hist'].abs().rolling(window=20).sum()

        return df

    def analyze_macd_energy(
        self,
        current_energy: float,
        avg_energy: float
    ) -> Dict:
        """
        分析MACD能量信号

        Args:
            current_energy: 当前MACD能量
            avg_energy: 平均MACD能量

        Returns:
            {
                'level': '强势'/'正常'/'弱势',
                'description': 描述文字,
                'score': 0-100评分
            }
        """
        ratio = current_energy / avg_energy if avg_energy > 0 else 1

        if ratio >= 1.5:
            return {
                'level': '强势',
                'description': f'MACD能量{ratio:.2f}倍于平均水平,趋势强劲',
                'score': 80
            }
        elif ratio >= 0.8:
            return {
                'level': '正常',
                'description': f'MACD能量{ratio:.2f}倍于平均水平,趋势正常',
                'score': 50
            }
        else:
            return {
                'level': '弱势',
                'description': f'MACD能量{ratio:.2f}倍于平均水平,趋势疲弱',
                'score': 30
            }

    def get_stock_realtime_data(self, symbol: str) -> Dict:
        """
        获取个股实时数据(包含量比、换手率)

        Args:
            symbol: 股票代码 (如 '000001' 或 'sz000001')

        Returns:
            {
                'symbol': 股票代码,
                'name': 股票名称,
                'price': 最新价,
                'change_pct': 涨跌幅,
                'volume': 成交量,
                'amount': 成交额,
                'volume_ratio': 量比,
                'turnover_rate': 换手率,
                'timestamp': 时间戳
            }
        """
        try:
            logger.info(f"获取{symbol}实时数据...")

            # 使用akshare获取实时行情
            df = ak.stock_zh_a_spot_em()

            if df is None or df.empty:
                return {'error': '获取数据失败'}

            # 查找指定股票
            stock_data = df[df['代码'] == symbol]

            if stock_data.empty:
                return {'error': f'未找到股票{symbol}'}

            row = stock_data.iloc[0]

            result = {
                'symbol': symbol,
                'name': row['名称'],
                'price': float(row['最新价']),
                'change_pct': float(row['涨跌幅']),
                'volume': float(row['成交量']),
                'amount': float(row['成交额']),
                'volume_ratio': float(row['量比']) if '量比' in row else 0,
                'turnover_rate': float(row['换手率']) if '换手率' in row else 0,
                'timestamp': datetime.now()
            }

            logger.info(f"{symbol} 实时数据获取成功")
            return result

        except Exception as e:
            logger.error(f"获取{symbol}实时数据失败: {str(e)}")
            return {'error': str(e)}

    def comprehensive_analysis(
        self,
        symbol: str,
        df: pd.DataFrame = None
    ) -> Dict:
        """
        综合分析个股的A股特色指标

        Args:
            symbol: 股票代码
            df: OHLCV数据DataFrame,如为None则获取实时数据

        Returns:
            完整的分析结果
        """
        try:
            logger.info(f"开始A股特色指标综合分析: {symbol}")

            result = {
                'symbol': symbol,
                'timestamp': datetime.now()
            }

            # 1. 获取实时数据
            realtime = self.get_stock_realtime_data(symbol)
            if 'error' in realtime:
                return {'error': realtime['error']}

            result['realtime'] = realtime

            # 2. 量比分析
            volume_ratio = realtime.get('volume_ratio', 0)
            if volume_ratio > 0:
                volume_analysis = self.analyze_volume_ratio(volume_ratio)
                result['volume_ratio_analysis'] = volume_analysis

            # 3. 换手率分析
            turnover_rate = realtime.get('turnover_rate', 0)
            if turnover_rate > 0:
                turnover_analysis = self.analyze_turnover_rate(turnover_rate)
                result['turnover_rate_analysis'] = turnover_analysis

            # 4. 如果提供了历史数据,计算MACD能量
            if df is not None and not df.empty:
                df = self.calculate_macd_energy(df)
                if 'macd_energy' in df.columns:
                    current_energy = df['macd_energy'].iloc[-1]
                    avg_energy = df['macd_energy'].mean()
                    macd_analysis = self.analyze_macd_energy(current_energy, avg_energy)
                    result['macd_energy_analysis'] = macd_analysis

            logger.info(f"{symbol} A股特色指标分析完成")
            return result

        except Exception as e:
            logger.error(f"{symbol} 综合分析失败: {str(e)}")
            return {'error': str(e)}


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 70)
    print("A股特色指标分析器测试")
    print("=" * 70)

    analyzer = CNStockIndicators()

    # 测试1: 量比分析
    print("\n1. 测试量比分析")
    print("-" * 70)
    for ratio in [3.5, 2.2, 1.2, 0.7, 0.3]:
        analysis = analyzer.analyze_volume_ratio(ratio)
        print(f"量比 {ratio:.1f}: {analysis['level']} - {analysis['signal']}")
        print(f"  {analysis['description']}")

    # 测试2: 换手率分析
    print("\n2. 测试换手率分析")
    print("-" * 70)
    for rate in [20, 8, 4, 1.5, 0.3]:
        analysis = analyzer.analyze_turnover_rate(rate)
        print(f"换手率 {rate:.1f}%: {analysis['level']} - {analysis['signal']} (风险: {analysis['risk_level']})")
        print(f"  {analysis['description']}")

    # 测试3: 实时数据获取
    print("\n3. 测试实时数据获取 (平安银行 000001)")
    print("-" * 70)
    result = analyzer.comprehensive_analysis('000001')

    if 'error' not in result:
        realtime = result['realtime']
        print(f"股票名称: {realtime['name']}")
        print(f"最新价: {realtime['price']:.2f}")
        print(f"涨跌幅: {realtime['change_pct']:+.2f}%")
        print(f"成交量: {realtime['volume']:.0f}")
        print(f"量比: {realtime['volume_ratio']:.2f}")
        print(f"换手率: {realtime['turnover_rate']:.2f}%")

        if 'volume_ratio_analysis' in result:
            vr = result['volume_ratio_analysis']
            print(f"\n量比分析: {vr['level']} ({vr['score']}分)")
            print(f"  {vr['description']}")

        if 'turnover_rate_analysis' in result:
            tr = result['turnover_rate_analysis']
            print(f"\n换手率分析: {tr['level']} ({tr['score']}分, 风险{tr['risk_level']})")
            print(f"  {tr['description']}")
    else:
        print(f"❌ 分析失败: {result['error']}")

    print("\n" + "=" * 70)
    print("✅ A股特色指标分析器测试完成")
    print("=" * 70)
