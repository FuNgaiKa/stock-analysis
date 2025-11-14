#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流动性分析器
Liquidity Analyzer

分析标的的流动性水平,评估变现能力和交易成本

主要功能:
- 计算日均成交量/成交额
- 估算换手率 (A股可实时获取)
- 计算买卖价差 (美股可获取)
- 综合流动性评分 (0-100)
- 流动性预警
- 估算平仓所需天数
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime, timedelta


class LiquidityAnalyzer:
    """
    流动性分析器

    使用方法:

    ```python
    from russ_trading.analyzers.liquidity_analyzer import LiquidityAnalyzer

    analyzer = LiquidityAnalyzer()

    # 分析单个标的
    result = analyzer.analyze_liquidity(
        symbol='510300.SS',
        price_data=df,  # 包含 Close, Volume, High, Low
        position_value=100000  # 持仓市值
    )

    print(f"流动性评分: {result['liquidity_score']}")
    print(f"流动性等级: {result['liquidity_level']}")
    print(f"平仓天数: {result['sell_days_needed']}天")

    if result['warning']:
        print(f"⚠️  {result['warning']}")
    ```
    """

    def __init__(self):
        """初始化流动性分析器"""
        pass

    def analyze_liquidity(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        position_value: float = 0,
        lookback_days: int = 20
    ) -> Dict:
        """
        分析标的流动性

        Args:
            symbol: 标的代码 (例: '510300.SS', '600519.SZ')
            price_data: 价格数据 (必须包含 'Close', 'Volume')
            position_value: 当前持仓市值 (用于计算平仓天数)
            lookback_days: 回溯天数 (默认20日)

        Returns:
            {
                'symbol': 标的代码,
                'avg_volume': 日均成交量,
                'avg_amount': 日均成交额 (元),
                'avg_turnover': 日均换手率 (0-1),
                'bid_ask_spread': 买卖价差百分比,
                'liquidity_score': 流动性评分 (0-100),
                'liquidity_level': 流动性等级 ('优秀'/'良好'/'一般'/'不足'),
                'warning': 预警信息 (如有),
                'sell_days_needed': 平仓所需天数 (基于持仓市值)
            }
        """
        # 数据校验
        if price_data.empty:
            return self._error_result(symbol, "价格数据为空")

        required_cols = ['Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in price_data.columns]
        if missing_cols:
            return self._error_result(symbol, f"缺少必需列: {missing_cols}")

        try:
            # 1. 计算日均成交量和成交额
            avg_volume, avg_amount = self._calculate_avg_trading_metrics(
                price_data, lookback_days
            )

            # 2. 估算换手率 (仅A股可获取)
            avg_turnover = self._estimate_turnover_rate(symbol, avg_volume, avg_amount)

            # 3. 计算买卖价差 (如果数据可用)
            bid_ask_spread = self._calculate_bid_ask_spread(price_data)

            # 4. 计算流动性评分
            liquidity_score = self._calculate_liquidity_score(
                avg_amount, avg_turnover, bid_ask_spread
            )

            # 5. 确定流动性等级
            if liquidity_score >= 80:
                liquidity_level = '优秀'
            elif liquidity_score >= 60:
                liquidity_level = '良好'
            elif liquidity_score >= 40:
                liquidity_level = '一般'
            else:
                liquidity_level = '不足'

            # 6. 生成预警
            warning = None
            if avg_amount < 10_000_000:  # 日均成交额 < 1000万
                warning = f"⚠️ 日均成交额仅{avg_amount/10000:.1f}万,流动性陷阱风险高,建议分批减仓"
            elif liquidity_score < 40:
                warning = f"⚠️ 流动性评分{liquidity_score}分,交易需谨慎"

            # 7. 计算卖出所需天数
            sell_days_needed = 0
            if position_value > 0 and avg_amount > 0:
                # 假设每天最多卖出日均成交额的10%,避免冲击价格
                daily_sell_limit = avg_amount * 0.10
                sell_days_needed = int(np.ceil(position_value / daily_sell_limit))

            return {
                'symbol': symbol,
                'avg_volume': avg_volume,
                'avg_amount': avg_amount,
                'avg_turnover': avg_turnover,
                'bid_ask_spread': bid_ask_spread,
                'liquidity_score': liquidity_score,
                'liquidity_level': liquidity_level,
                'warning': warning,
                'sell_days_needed': sell_days_needed
            }

        except Exception as e:
            return self._error_result(symbol, f"分析失败: {str(e)}")

    def _calculate_avg_trading_metrics(
        self, price_data: pd.DataFrame, lookback_days: int
    ) -> tuple:
        """
        计算日均成交量和成交额

        Args:
            price_data: 价格数据
            lookback_days: 回溯天数

        Returns:
            (avg_volume, avg_amount)
        """
        # 取最近N天的数据
        recent_data = price_data.tail(lookback_days)

        # 日均成交量
        avg_volume = recent_data['Volume'].mean()

        # 日均成交额 = 成交量 * 均价
        # 注意: yfinance 的 A股数据 Volume 单位为股,需要乘以价格
        avg_price = recent_data['Close'].mean()
        avg_amount = avg_volume * avg_price

        return avg_volume, avg_amount

    def _estimate_turnover_rate(
        self, symbol: str, avg_volume: float, avg_amount: float
    ) -> Optional[float]:
        """
        估算换手率

        对于A股,可以通过 akshare 实时获取
        对于美股/港股,暂时返回None

        Args:
            symbol: 标的代码
            avg_volume: 平均成交量
            avg_amount: 平均成交额

        Returns:
            换手率 (0-1) 或 None
        """
        try:
            # 尝试从 akshare 获取 (仅A股)
            if '.SS' in symbol or '.SZ' in symbol:
                import akshare as ak

                # 移除后缀
                code = symbol.replace('.SS', '').replace('.SZ', '')

                # 获取实时行情
                df = ak.stock_zh_a_spot_em()
                row = df[df['代码'] == code]

                if not row.empty:
                    turnover_rate = row['换手率'].values[0]
                    return turnover_rate / 100  # 转为小数

            # 其他市场返回 None
            return None

        except Exception:
            # 获取失败,返回 None
            return None

    def _calculate_bid_ask_spread(self, price_data: pd.DataFrame) -> Optional[float]:
        """
        计算买卖价差

        注意: yfinance 的 A股数据不包含 bid/ask,仅美股可用

        Args:
            price_data: 价格数据

        Returns:
            买卖价差百分比 或 None
        """
        try:
            if 'Bid' in price_data.columns and 'Ask' in price_data.columns:
                bid = price_data['Bid'].tail(20).mean()
                ask = price_data['Ask'].tail(20).mean()

                if bid > 0:
                    spread = (ask - bid) / bid
                    return spread

            return None

        except Exception:
            return None

    def _calculate_liquidity_score(
        self, avg_amount: float, avg_turnover: Optional[float],
        bid_ask_spread: Optional[float]
    ) -> float:
        """
        计算流动性评分

        流动性评分 = 成交额权重(60%) + 换手率权重(30%) + 价差权重(10%)

        Args:
            avg_amount: 日均成交额
            avg_turnover: 日均换手率
            bid_ask_spread: 买卖价差

        Returns:
            流动性评分 (0-100)
        """
        score = 0

        # 1. 成交额评分 (60%权重)
        # 分档标准:
        # >= 50亿: 100分
        # >= 10亿: 80分
        # >= 1亿: 60分
        # >= 1000万: 40分
        # < 1000万: 20分
        if avg_amount >= 5_000_000_000:
            amount_score = 100
        elif avg_amount >= 1_000_000_000:
            amount_score = 80
        elif avg_amount >= 100_000_000:
            amount_score = 60
        elif avg_amount >= 10_000_000:
            amount_score = 40
        else:
            amount_score = 20

        score += amount_score * 0.6

        # 2. 换手率评分 (30%权重)
        # 如果数据不可用,使用成交额评分代替
        if avg_turnover is not None:
            # 分档标准:
            # >= 10%: 100分 (极高)
            # >= 5%: 80分 (高)
            # >= 2%: 60分 (中等)
            # >= 1%: 40分 (偏低)
            # < 1%: 20分 (低)
            if avg_turnover >= 0.10:
                turnover_score = 100
            elif avg_turnover >= 0.05:
                turnover_score = 80
            elif avg_turnover >= 0.02:
                turnover_score = 60
            elif avg_turnover >= 0.01:
                turnover_score = 40
            else:
                turnover_score = 20

            score += turnover_score * 0.3
        else:
            # 换手率不可用,使用成交额评分代替
            score += amount_score * 0.3

        # 3. 价差评分 (10%权重)
        # 如果数据不可用,使用成交额评分代替
        if bid_ask_spread is not None:
            # 分档标准:
            # < 0.1%: 100分 (极窄)
            # < 0.5%: 80分 (窄)
            # < 1%: 60分 (中等)
            # < 2%: 40分 (宽)
            # >= 2%: 20分 (极宽)
            if bid_ask_spread < 0.001:
                spread_score = 100
            elif bid_ask_spread < 0.005:
                spread_score = 80
            elif bid_ask_spread < 0.01:
                spread_score = 60
            elif bid_ask_spread < 0.02:
                spread_score = 40
            else:
                spread_score = 20

            score += spread_score * 0.1
        else:
            # 价差不可用,使用成交额评分代替
            score += amount_score * 0.1

        return round(score, 1)

    def _error_result(self, symbol: str, error_msg: str) -> Dict:
        """
        返回错误结果

        Args:
            symbol: 标的代码
            error_msg: 错误信息

        Returns:
            包含错误信息的结果字典
        """
        return {
            'symbol': symbol,
            'avg_volume': 0,
            'avg_amount': 0,
            'avg_turnover': None,
            'bid_ask_spread': None,
            'liquidity_score': 0,
            'liquidity_level': '未知',
            'warning': f"❌ {error_msg}",
            'sell_days_needed': 0,
            'error': error_msg
        }


if __name__ == '__main__':
    """测试代码"""
    import yfinance as yf

    print("\n" + "="*60)
    print("流动性分析器测试")
    print("="*60)

    # 初始化分析器
    analyzer = LiquidityAnalyzer()

    # 测试1: 分析A股ETF (证券ETF)
    print("\n测试1: 证券ETF (512000.SS)")
    print("-" * 60)

    ticker = yf.Ticker('512000.SS')
    data = ticker.history(period='3mo')

    result = analyzer.analyze_liquidity(
        symbol='512000.SS',
        price_data=data,
        position_value=100000  # 假设持仓10万
    )

    print(f"标的: {result['symbol']}")
    print(f"日均成交量: {result['avg_volume']:,.0f}股")
    print(f"日均成交额: ¥{result['avg_amount']/100000000:.2f}亿")
    print(f"日均换手率: {result['avg_turnover']*100 if result['avg_turnover'] else 'N/A'}%")
    print(f"买卖价差: {result['bid_ask_spread']*100 if result['bid_ask_spread'] else 'N/A'}%")
    print(f"流动性评分: {result['liquidity_score']}分")
    print(f"流动性等级: {result['liquidity_level']}")
    print(f"平仓天数: {result['sell_days_needed']}天")

    if result['warning']:
        print(f"\n{result['warning']}")

    # 测试2: 分析小盘股 (模拟低流动性)
    print("\n测试2: 小盘股 (模拟低流动性)")
    print("-" * 60)

    # 创建模拟数据
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    low_liquidity_data = pd.DataFrame({
        'Close': np.random.uniform(10, 12, 30),
        'Volume': np.random.uniform(100000, 500000, 30),  # 低成交量
        'High': np.random.uniform(10, 12, 30),
        'Low': np.random.uniform(10, 12, 30)
    }, index=dates)

    result = analyzer.analyze_liquidity(
        symbol='SMALL_CAP',
        price_data=low_liquidity_data,
        position_value=50000  # 假设持仓5万
    )

    print(f"标的: {result['symbol']}")
    print(f"日均成交量: {result['avg_volume']:,.0f}股")
    print(f"日均成交额: ¥{result['avg_amount']/10000:.1f}万")
    print(f"流动性评分: {result['liquidity_score']}分")
    print(f"流动性等级: {result['liquidity_level']}")
    print(f"平仓天数: {result['sell_days_needed']}天")

    if result['warning']:
        print(f"\n{result['warning']}")

    print("\n" + "="*60)
    print("✅ 流动性分析器测试完成!")
    print("="*60)
