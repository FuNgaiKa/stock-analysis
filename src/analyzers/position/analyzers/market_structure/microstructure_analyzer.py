"""
市场微观结构分析器
实现VWAP、订单流、买卖价差、市场深度等高级指标
"""
import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class MicrostructureAnalyzer:
    """市场微观结构分析器"""

    def __init__(self, symbol: str, start_date: str = None, end_date: str = None):
        """
        初始化微观结构分析器

        Args:
            symbol: 股票代码
            start_date: 开始日期 (默认为3个月前)
            end_date: 结束日期 (默认为今天)
        """
        self.symbol = symbol
        self.end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        self.start_date = start_date or (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        # 下载数据
        self.data = yf.download(symbol, start=self.start_date, end=self.end_date, progress=False)

        # 处理多层索引
        if isinstance(self.data.columns, pd.MultiIndex):
            self.data = self.data.droplevel(1, axis=1)

        # 移除NaN
        self.data = self.data.dropna()

    def calculate_vwap(self, period: int = 20) -> Dict[str, Any]:
        """
        计算成交量加权平均价 (VWAP) 及其偏离度

        VWAP = Σ(Price × Volume) / Σ(Volume)

        Args:
            period: 计算周期

        Returns:
            dict: VWAP相关指标
        """
        # 典型价格 (Typical Price)
        typical_price = (self.data['High'] + self.data['Low'] + self.data['Close']) / 3

        # 计算VWAP
        tpv = typical_price * self.data['Volume']
        vwap = tpv.rolling(window=period).sum() / self.data['Volume'].rolling(window=period).sum()

        # 当前价格相对VWAP的偏离
        current_price = self.data['Close'].iloc[-1]
        current_vwap = vwap.iloc[-1]
        vwap_deviation = (current_price - current_vwap) / current_vwap * 100

        # 历史偏离度统计
        historical_deviation = (self.data['Close'] - vwap) / vwap * 100
        historical_deviation = historical_deviation.dropna()

        # VWAP斜率 (判断趋势强度)
        vwap_values = vwap.dropna().values[-period:]
        if len(vwap_values) >= 2:
            vwap_slope = (vwap_values[-1] - vwap_values[0]) / len(vwap_values)
            vwap_trend = 'up' if vwap_slope > 0 else 'down'
        else:
            vwap_slope = 0
            vwap_trend = 'neutral'

        return {
            'current_price': current_price,
            'current_vwap': current_vwap,
            'vwap_deviation_pct': vwap_deviation,
            'deviation_percentile': self._calculate_percentile(historical_deviation, vwap_deviation),
            'vwap_slope': vwap_slope,
            'vwap_trend': vwap_trend,
            'signal': self._vwap_signal(vwap_deviation),
            'strength': self._vwap_strength(vwap_deviation)
        }

    def calculate_order_flow(self, period: int = 20) -> Dict[str, Any]:
        """
        计算订单流指标

        使用价格变动和成交量来估算买卖压力

        Args:
            period: 计算周期

        Returns:
            dict: 订单流指标
        """
        # 价格变动
        price_change = self.data['Close'].diff()

        # 根据价格变动判断主动买卖
        # 上涨 = 主动买入，下跌 = 主动卖出
        buy_volume = self.data['Volume'].where(price_change > 0, 0)
        sell_volume = self.data['Volume'].where(price_change < 0, 0)

        # 计算净买入量
        net_buy_volume = buy_volume - sell_volume

        # 滚动窗口统计
        buy_volume_sum = buy_volume.rolling(window=period).sum()
        sell_volume_sum = sell_volume.rolling(window=period).sum()
        total_volume_sum = self.data['Volume'].rolling(window=period).sum()

        # 买入强度 (买入占比)
        buy_ratio = buy_volume_sum / total_volume_sum * 100

        # 净买入强度
        net_buy_ratio = (buy_volume_sum - sell_volume_sum) / total_volume_sum * 100

        # 当前值
        current_buy_ratio = buy_ratio.iloc[-1]
        current_net_buy = net_buy_ratio.iloc[-1]

        # 大单交易检测 (成交量 > 平均值的2倍)
        avg_volume = self.data['Volume'].rolling(window=period).mean()
        large_orders = self.data['Volume'] > (avg_volume * 2)
        large_buy_orders = large_orders & (price_change > 0)
        large_sell_orders = large_orders & (price_change < 0)

        recent_large_buy = large_buy_orders.tail(period).sum()
        recent_large_sell = large_sell_orders.tail(period).sum()

        return {
            'buy_ratio': current_buy_ratio,
            'net_buy_ratio': current_net_buy,
            'recent_large_buy_count': recent_large_buy,
            'recent_large_sell_count': recent_large_sell,
            'order_flow_signal': self._order_flow_signal(current_net_buy),
            'order_imbalance': self._classify_imbalance(current_net_buy),
            'large_order_bias': 'buy' if recent_large_buy > recent_large_sell else 'sell' if recent_large_sell > recent_large_buy else 'neutral'
        }

    def calculate_spread_metrics(self, period: int = 20) -> Dict[str, Any]:
        """
        计算买卖价差指标

        使用High-Low作为日内价差的代理

        Args:
            period: 计算周期

        Returns:
            dict: 价差指标
        """
        # 日内价差
        daily_spread = self.data['High'] - self.data['Low']

        # 相对价差 (百分比)
        relative_spread = daily_spread / self.data['Close'] * 100

        # 统计指标
        avg_spread = relative_spread.rolling(window=period).mean()
        current_spread = relative_spread.iloc[-1]
        avg_spread_value = avg_spread.iloc[-1]

        # 价差百分位 (判断流动性)
        spread_percentile = self._calculate_percentile(relative_spread.tail(period * 2), current_spread)

        # 价差趋势 (价差扩大 = 流动性下降)
        spread_trend = relative_spread.tail(period).values
        if len(spread_trend) >= 2:
            spread_slope = (spread_trend[-1] - spread_trend[0]) / len(spread_trend)
            liquidity_trend = 'deteriorating' if spread_slope > 0 else 'improving'
        else:
            spread_slope = 0
            liquidity_trend = 'stable'

        return {
            'current_spread_pct': current_spread,
            'avg_spread_pct': avg_spread_value,
            'spread_percentile': spread_percentile,
            'spread_slope': spread_slope,
            'liquidity_trend': liquidity_trend,
            'liquidity_level': self._classify_liquidity(current_spread, avg_spread_value)
        }

    def calculate_depth_metrics(self, period: int = 20) -> Dict[str, Any]:
        """
        计算市场深度指标

        使用成交量和价格波动作为深度的代理

        Args:
            period: 计算周期

        Returns:
            dict: 市场深度指标
        """
        # 价格冲击 = 价格变动 / 成交量
        # 成交量越大但价格变动越小 -> 市场深度越好
        price_change = self.data['Close'].pct_change()
        volume_normalized = self.data['Volume'] / self.data['Volume'].rolling(window=period).mean()

        # 深度指标 = 成交量 / abs(价格变动)
        # 避免除以0
        depth_proxy = volume_normalized / (abs(price_change) + 0.0001)

        # 统计
        avg_depth = depth_proxy.rolling(window=period).mean()
        current_depth = depth_proxy.iloc[-1]
        avg_depth_value = avg_depth.iloc[-1]

        # 深度百分位
        depth_percentile = self._calculate_percentile(depth_proxy.tail(period * 2), current_depth)

        # 成交量稳定性 (成交量波动越小 -> 市场越稳定)
        volume_cv = (
            self.data['Volume'].rolling(window=period).std() /
            self.data['Volume'].rolling(window=period).mean()
        )
        current_volume_cv = volume_cv.iloc[-1]

        return {
            'depth_score': current_depth,
            'avg_depth_score': avg_depth_value,
            'depth_percentile': depth_percentile,
            'volume_cv': current_volume_cv,
            'market_stability': self._classify_stability(current_volume_cv),
            'depth_level': self._classify_depth(depth_percentile)
        }

    def comprehensive_analysis(self) -> Dict[str, Any]:
        """
        综合微观结构分析

        Returns:
            dict: 所有微观结构指标
        """
        try:
            vwap = self.calculate_vwap(20)
            order_flow = self.calculate_order_flow(20)
            spread = self.calculate_spread_metrics(20)
            depth = self.calculate_depth_metrics(20)

            # 综合评分 (0-100)
            microstructure_score = self._calculate_microstructure_score(vwap, order_flow, spread, depth)

            return {
                'symbol': self.symbol,
                'analysis_date': self.end_date,
                'data_points': len(self.data),

                # VWAP指标
                'vwap': {
                    'current_price': vwap['current_price'],
                    'current_vwap': vwap['current_vwap'],
                    'deviation_pct': vwap['vwap_deviation_pct'],
                    'trend': vwap['vwap_trend'],
                    'signal': vwap['signal'],
                    'strength': vwap['strength']
                },

                # 订单流
                'order_flow': {
                    'buy_ratio': order_flow['buy_ratio'],
                    'net_buy_ratio': order_flow['net_buy_ratio'],
                    'large_buy_count': order_flow['recent_large_buy_count'],
                    'large_sell_count': order_flow['recent_large_sell_count'],
                    'signal': order_flow['order_flow_signal'],
                    'imbalance': order_flow['order_imbalance'],
                    'bias': order_flow['large_order_bias']
                },

                # 价差 (流动性)
                'spread': {
                    'current_pct': spread['current_spread_pct'],
                    'avg_pct': spread['avg_spread_pct'],
                    'percentile': spread['spread_percentile'],
                    'trend': spread['liquidity_trend'],
                    'level': spread['liquidity_level']
                },

                # 市场深度
                'depth': {
                    'score': depth['depth_score'],
                    'percentile': depth['depth_percentile'],
                    'volume_cv': depth['volume_cv'],
                    'stability': depth['market_stability'],
                    'level': depth['depth_level']
                },

                # 综合评分
                'microstructure_score': microstructure_score,
                'microstructure_level': self._classify_microstructure(microstructure_score),
                'recommendation': self._get_microstructure_recommendation(microstructure_score, vwap, order_flow)
            }
        except Exception as e:
            return {
                'symbol': self.symbol,
                'error': str(e),
                'analysis_date': self.end_date
            }

    # 辅助方法
    def _calculate_percentile(self, series: pd.Series, value: float) -> float:
        """计算百分位"""
        from scipy import stats
        series_clean = series.dropna()
        if len(series_clean) == 0:
            return 50.0
        return stats.percentileofscore(series_clean, value)

    def _vwap_signal(self, deviation: float) -> str:
        """VWAP信号"""
        if deviation > 2:
            return 'strong_overbought'
        elif deviation > 1:
            return 'overbought'
        elif deviation < -2:
            return 'strong_oversold'
        elif deviation < -1:
            return 'oversold'
        else:
            return 'neutral'

    def _vwap_strength(self, deviation: float) -> str:
        """VWAP强度"""
        abs_dev = abs(deviation)
        if abs_dev > 2:
            return 'very_strong'
        elif abs_dev > 1:
            return 'strong'
        elif abs_dev > 0.5:
            return 'moderate'
        else:
            return 'weak'

    def _order_flow_signal(self, net_buy_ratio: float) -> str:
        """订单流信号"""
        if net_buy_ratio > 20:
            return 'strong_buying'
        elif net_buy_ratio > 10:
            return 'buying'
        elif net_buy_ratio < -20:
            return 'strong_selling'
        elif net_buy_ratio < -10:
            return 'selling'
        else:
            return 'balanced'

    def _classify_imbalance(self, net_buy_ratio: float) -> str:
        """订单不平衡分类"""
        abs_ratio = abs(net_buy_ratio)
        if abs_ratio > 30:
            return 'extreme'
        elif abs_ratio > 20:
            return 'high'
        elif abs_ratio > 10:
            return 'moderate'
        else:
            return 'low'

    def _classify_liquidity(self, current_spread: float, avg_spread: float) -> str:
        """流动性分类"""
        ratio = current_spread / avg_spread if avg_spread > 0 else 1
        if ratio > 1.5:
            return 'poor'
        elif ratio > 1.2:
            return 'below_average'
        elif ratio < 0.8:
            return 'excellent'
        else:
            return 'good'

    def _classify_stability(self, volume_cv: float) -> str:
        """市场稳定性分类"""
        if volume_cv > 2:
            return 'very_unstable'
        elif volume_cv > 1:
            return 'unstable'
        elif volume_cv < 0.5:
            return 'very_stable'
        else:
            return 'stable'

    def _classify_depth(self, percentile: float) -> str:
        """市场深度分类"""
        if percentile > 80:
            return 'excellent'
        elif percentile > 60:
            return 'good'
        elif percentile > 40:
            return 'average'
        else:
            return 'poor'

    def _calculate_microstructure_score(self, vwap: dict, order_flow: dict,
                                       spread: dict, depth: dict) -> float:
        """
        计算微观结构综合评分 (0-100)

        评分逻辑:
        - VWAP偏离度适中 -> 加分
        - 买入订单流 -> 加分
        - 流动性好 -> 加分
        - 市场深度好 -> 加分
        """
        score = 50  # 基准分

        # VWAP贡献 (-10 to +10)
        vwap_dev = abs(vwap['vwap_deviation_pct'])
        if vwap_dev < 0.5:
            score += 10
        elif vwap_dev < 1:
            score += 5
        elif vwap_dev > 2:
            score -= 10
        elif vwap_dev > 1.5:
            score -= 5

        # 订单流贡献 (-15 to +15)
        net_buy = order_flow['net_buy_ratio']
        if net_buy > 20:
            score += 15
        elif net_buy > 10:
            score += 10
        elif net_buy < -20:
            score -= 15
        elif net_buy < -10:
            score -= 10

        # 流动性贡献 (-10 to +10)
        liquidity = spread['liquidity_level']
        liquidity_score_map = {
            'excellent': 10,
            'good': 5,
            'below_average': -5,
            'poor': -10
        }
        score += liquidity_score_map.get(liquidity, 0)

        # 市场深度贡献 (-15 to +15)
        depth_percentile = depth['depth_percentile']
        if depth_percentile > 80:
            score += 15
        elif depth_percentile > 60:
            score += 10
        elif depth_percentile < 20:
            score -= 15
        elif depth_percentile < 40:
            score -= 10

        return min(max(score, 0), 100)

    def _classify_microstructure(self, score: float) -> str:
        """微观结构评级"""
        if score >= 80:
            return 'excellent'
        elif score >= 65:
            return 'good'
        elif score >= 50:
            return 'fair'
        elif score >= 35:
            return 'poor'
        else:
            return 'very_poor'

    def _get_microstructure_recommendation(self, score: float, vwap: dict, order_flow: dict) -> str:
        """微观结构操作建议"""
        if score >= 75:
            if vwap['signal'] in ['oversold', 'strong_oversold'] and order_flow['order_flow_signal'] in ['buying', 'strong_buying']:
                return '✅ 优秀微观结构+买入信号，强烈建议做多'
            else:
                return '✅ 微观结构优秀，市场健康，可正常交易'
        elif score >= 60:
            return '➡️ 微观结构良好，可适度参与'
        elif score >= 40:
            return '⚠️ 微观结构一般，建议观望或减仓'
        else:
            if order_flow['order_flow_signal'] in ['strong_selling']:
                return '❌ 微观结构差+卖压严重，建议远离或做空'
            else:
                return '❌ 微观结构较差，不建议交易'


if __name__ == '__main__':
    # 测试代码
    print("=" * 80)
    print("市场微观结构分析器测试")
    print("=" * 80)

    # 测试纳斯达克
    print("\n纳斯达克综合指数 (^IXIC) 微观结构分析:")
    print("-" * 80)
    analyzer = MicrostructureAnalyzer('^IXIC')
    result = analyzer.comprehensive_analysis()

    if 'error' not in result:
        print(f"\n📊 VWAP指标:")
        print(f"  当前价格: {result['vwap']['current_price']:.2f}")
        print(f"  VWAP: {result['vwap']['current_vwap']:.2f}")
        print(f"  偏离度: {result['vwap']['deviation_pct']:.2f}%")
        print(f"  信号: {result['vwap']['signal']}")

        print(f"\n📈 订单流:")
        print(f"  买入占比: {result['order_flow']['buy_ratio']:.2f}%")
        print(f"  净买入: {result['order_flow']['net_buy_ratio']:.2f}%")
        print(f"  大单买入: {result['order_flow']['large_buy_count']}")
        print(f"  大单卖出: {result['order_flow']['large_sell_count']}")
        print(f"  信号: {result['order_flow']['signal']}")

        print(f"\n💧 流动性:")
        print(f"  当前价差: {result['spread']['current_pct']:.2f}%")
        print(f"  流动性等级: {result['spread']['level']}")
        print(f"  趋势: {result['spread']['trend']}")

        print(f"\n🏊 市场深度:")
        print(f"  深度评分: {result['depth']['score']:.2f}")
        print(f"  稳定性: {result['depth']['stability']}")
        print(f"  深度等级: {result['depth']['level']}")

        print(f"\n💡 综合评估:")
        print(f"  微观结构评分: {result['microstructure_score']:.1f}/100")
        print(f"  评级: {result['microstructure_level']}")
        print(f"  建议: {result['recommendation']}")
    else:
        print(f"❌ 分析失败: {result['error']}")
