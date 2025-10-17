"""
趋势斜率分析器
用于分析市场趋势的斜率特征，识别过热、修复等状态
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any
import yfinance as yf
from datetime import datetime, timedelta


class SlopeAnalyzer:
    """趋势斜率分析器"""

    def __init__(self, symbol: str, start_date: str = None, end_date: str = None):
        """
        初始化斜率分析器

        Args:
            symbol: 股票代码 (如 ^IXIC, ^GSPC, ^HSI)
            start_date: 开始日期 (默认为1年前)
            end_date: 结束日期 (默认为今天)
        """
        self.symbol = symbol
        self.end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        self.start_date = start_date or (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # 下载数据
        self.data = yf.download(symbol, start=self.start_date, end=self.end_date, progress=False)

        # 处理多层索引 (yfinance 新版本)
        if isinstance(self.data.columns, pd.MultiIndex):
            self.prices = self.data['Close'][symbol]
        else:
            self.prices = self.data['Close']

        # 移除NaN
        self.prices = self.prices.dropna()

    def linear_slope(self, days: int = 60) -> Dict[str, Any]:
        """
        计算线性回归斜率

        Args:
            days: 回归周期

        Returns:
            dict: 包含斜率、年化收益率、R²、标准误差等指标
        """
        if len(self.prices) < days:
            raise ValueError(f"数据不足：需要{days}天，实际{len(self.prices)}天")

        prices = self.prices[-days:].values
        x = np.arange(len(prices))

        # 线性回归
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, prices)

        # 计算每日斜率（百分比）
        daily_slope = slope / prices[0]

        # 年化收益率（基于斜率）
        annual_return = daily_slope * 365 * 100

        # 预测值
        fitted_line = slope * x + intercept

        # 残差分析
        residuals = prices - fitted_line
        residual_std = np.std(residuals)

        return {
            'slope': slope,
            'daily_slope': daily_slope,
            'annual_return': annual_return,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'std_err': std_err,
            'residual_std': residual_std,
            'start_price': prices[0],
            'end_price': prices[-1],
            'fitted_start': fitted_line[0],
            'fitted_end': fitted_line[-1]
        }

    def slope_volatility(self, window: int = 60, lookback: int = 252) -> Dict[str, Any]:
        """
        计算斜率波动率（衡量趋势稳定性）

        Args:
            window: 滚动窗口
            lookback: 历史回溯期

        Returns:
            dict: 斜率波动率统计
        """
        if len(self.prices) < lookback:
            lookback = len(self.prices)

        prices = self.prices[-lookback:]
        slopes = []

        # 滚动计算斜率
        for i in range(window, len(prices) + 1):
            period_prices = prices[i-window:i].values
            x = np.arange(len(period_prices))
            slope, _, _, _, _ = stats.linregress(x, period_prices)
            daily_slope = slope / period_prices[0]
            slopes.append(daily_slope)

        slopes = np.array(slopes)

        return {
            'slope_std': np.std(slopes),
            'slope_mean': np.mean(slopes),
            'slope_cv': np.std(slopes) / abs(np.mean(slopes)) if np.mean(slopes) != 0 else np.inf,
            'current_slope': slopes[-1],
            'slope_percentile': stats.percentileofscore(slopes, slopes[-1])
        }

    def slope_relative_to_ma(self, ma_period: int = 200, slope_period: int = 60) -> Dict[str, Any]:
        """
        计算当前斜率相对于均线的偏离度

        Args:
            ma_period: 均线周期
            slope_period: 斜率计算周期

        Returns:
            dict: 斜率偏离统计
        """
        if len(self.prices) < ma_period:
            ma_period = len(self.prices)

        # 计算均线
        ma = self.prices.rolling(window=ma_period).mean()

        # 当前价格相对均线的偏离
        current_price = self.prices.iloc[-1]
        current_ma = ma.iloc[-1]
        price_deviation = (current_price - current_ma) / current_ma

        # 计算斜率
        slope_info = self.linear_slope(slope_period)

        return {
            'price_deviation_pct': price_deviation * 100,
            'current_price': current_price,
            'ma_value': current_ma,
            'slope_annual_return': slope_info['annual_return'],
            'is_above_ma': current_price > current_ma,
            'deviation_level': self._classify_deviation(abs(price_deviation))
        }

    def slope_zscore(self, window: int = 60, lookback: int = 252) -> Dict[str, Any]:
        """
        计算斜率的Z-Score（用于均值回归判断）

        Args:
            window: 斜率计算窗口
            lookback: 历史回溯期

        Returns:
            dict: Z-Score 统计
        """
        vol_info = self.slope_volatility(window, lookback)

        current_slope = vol_info['current_slope']
        mean_slope = vol_info['slope_mean']
        std_slope = vol_info['slope_std']

        # 计算Z-Score
        zscore = (current_slope - mean_slope) / std_slope if std_slope > 0 else 0

        return {
            'zscore': zscore,
            'current_slope': current_slope,
            'mean_slope': mean_slope,
            'std_slope': std_slope,
            'zscore_level': self._classify_zscore(zscore),
            'reversion_signal': self._get_reversion_signal(zscore)
        }

    def slope_acceleration(self, short_period: int = 60, long_period: int = 120) -> Dict[str, Any]:
        """
        计算斜率加速度（判断趋势是加速还是减速）

        Args:
            short_period: 短期斜率周期
            long_period: 长期斜率周期

        Returns:
            dict: 加速度统计
        """
        slope_short = self.linear_slope(short_period)
        slope_long = self.linear_slope(long_period)

        # 加速度 = (短期斜率 - 长期斜率) / 时间差
        acceleration = (slope_short['daily_slope'] - slope_long['daily_slope']) / short_period

        return {
            'acceleration': acceleration,
            'short_slope': slope_short['daily_slope'],
            'long_slope': slope_long['daily_slope'],
            'short_annual': slope_short['annual_return'],
            'long_annual': slope_long['annual_return'],
            'is_accelerating': slope_short['daily_slope'] > slope_long['daily_slope'],
            'acceleration_level': self._classify_acceleration(acceleration)
        }

    def comprehensive_analysis(self) -> Dict[str, Any]:
        """
        综合斜率分析

        Returns:
            dict: 包含所有斜率指标的综合分析
        """
        try:
            slope_60 = self.linear_slope(60)
            slope_120 = self.linear_slope(120)
            volatility = self.slope_volatility(60, 252)
            ma_relative = self.slope_relative_to_ma(200, 60)
            zscore_info = self.slope_zscore(60, 252)
            acceleration = self.slope_acceleration(60, 120)

            # 综合风险评分 (0-100)
            risk_score = self._calculate_risk_score(
                slope_60['annual_return'],
                zscore_info['zscore'],
                ma_relative['price_deviation_pct'],
                acceleration['acceleration']
            )

            return {
                'symbol': self.symbol,
                'analysis_date': self.end_date,
                'data_points': len(self.prices),
                'current_price': self.prices.iloc[-1],

                # 斜率指标
                'slope_60d': {
                    'annual_return': slope_60['annual_return'],
                    'r_squared': slope_60['r_squared'],
                    'daily_slope': slope_60['daily_slope']
                },
                'slope_120d': {
                    'annual_return': slope_120['annual_return'],
                    'r_squared': slope_120['r_squared'],
                    'daily_slope': slope_120['daily_slope']
                },

                # 波动率
                'volatility': {
                    'slope_std': volatility['slope_std'],
                    'slope_cv': volatility['slope_cv'],
                    'percentile': volatility['slope_percentile']
                },

                # 相对均线
                'ma_relative': {
                    'deviation_pct': ma_relative['price_deviation_pct'],
                    'deviation_level': ma_relative['deviation_level'],
                    'is_above_ma': ma_relative['is_above_ma']
                },

                # Z-Score
                'zscore': {
                    'value': zscore_info['zscore'],
                    'level': zscore_info['zscore_level'],
                    'signal': zscore_info['reversion_signal']
                },

                # 加速度
                'acceleration': {
                    'value': acceleration['acceleration'],
                    'is_accelerating': acceleration['is_accelerating'],
                    'level': acceleration['acceleration_level']
                },

                # 综合评分
                'risk_score': risk_score,
                'risk_level': self._classify_risk(risk_score),
                'recommendation': self._get_recommendation(risk_score, zscore_info['zscore'])
            }
        except Exception as e:
            return {
                'symbol': self.symbol,
                'error': str(e),
                'analysis_date': self.end_date
            }

    # 辅助分类方法
    def _classify_deviation(self, deviation: float) -> str:
        """分类价格偏离程度"""
        if deviation < 0.05:
            return '正常'
        elif deviation < 0.10:
            return '轻度偏离'
        elif deviation < 0.15:
            return '中度偏离'
        else:
            return '严重偏离'

    def _classify_zscore(self, zscore: float) -> str:
        """分类Z-Score水平"""
        abs_z = abs(zscore)
        if abs_z < 1:
            return '正常区间'
        elif abs_z < 1.5:
            return '轻度异常'
        elif abs_z < 2:
            return '中度异常'
        else:
            return '极端异常'

    def _get_reversion_signal(self, zscore: float) -> str:
        """获取均值回归信号"""
        if zscore > 2:
            return '强烈超买-考虑做空'
        elif zscore > 1.5:
            return '超买-谨慎看多'
        elif zscore < -2:
            return '强烈超卖-考虑做多'
        elif zscore < -1.5:
            return '超卖-谨慎看空'
        else:
            return '中性'

    def _classify_acceleration(self, acceleration: float) -> str:
        """分类加速度水平"""
        if acceleration > 0.0001:
            return '快速加速'
        elif acceleration > 0:
            return '温和加速'
        elif acceleration > -0.0001:
            return '温和减速'
        else:
            return '快速减速'

    def _calculate_risk_score(self, annual_return: float, zscore: float,
                             deviation_pct: float, acceleration: float) -> float:
        """
        计算综合风险评分 (0-100)

        评分逻辑：
        - 斜率过高 -> 风险增加
        - Z-Score过高 -> 风险增加
        - 偏离均线过大 -> 风险增加
        - 加速度过大 -> 风险增加
        """
        score = 50  # 基准分

        # 斜率贡献 (-20 to +20)
        if annual_return > 30:
            score += 20
        elif annual_return > 20:
            score += 10
        elif annual_return < -20:
            score += 15
        elif annual_return < -10:
            score += 5

        # Z-Score贡献 (-15 to +15)
        score += min(abs(zscore) * 7.5, 15)

        # 偏离度贡献 (-10 to +10)
        score += min(abs(deviation_pct) * 0.5, 10)

        # 加速度贡献 (-5 to +5)
        if acceleration > 0.0001:
            score += 5
        elif acceleration < -0.0001:
            score -= 5

        return min(max(score, 0), 100)

    def _classify_risk(self, risk_score: float) -> str:
        """分类风险等级"""
        if risk_score < 30:
            return '低风险'
        elif risk_score < 50:
            return '中低风险'
        elif risk_score < 70:
            return '中高风险'
        else:
            return '高风险'

    def _get_recommendation(self, risk_score: float, zscore: float) -> str:
        """获取操作建议"""
        if risk_score > 75:
            if zscore > 2:
                return '⚠️ 高风险-严重超买，建议减仓或空仓观望'
            else:
                return '⚠️ 高风险区域，建议降低仓位'
        elif risk_score > 60:
            return '⚡ 中高风险，建议谨慎操作，控制仓位'
        elif risk_score < 40:
            if zscore < -1.5:
                return '✅ 低风险-超卖区域，可考虑逢低布局'
            else:
                return '✅ 低风险区域，可正常持仓'
        else:
            return '➡️ 中性区域，维持现有策略'


def compare_slopes(symbols: list, days: int = 60) -> pd.DataFrame:
    """
    比较多个市场的斜率

    Args:
        symbols: 股票代码列表
        days: 分析周期

    Returns:
        DataFrame: 对比结果
    """
    results = []

    for symbol in symbols:
        try:
            analyzer = SlopeAnalyzer(symbol)
            analysis = analyzer.comprehensive_analysis()

            results.append({
                '指数': symbol,
                '当前价格': round(analysis['current_price'], 2),
                '60日年化收益': f"{analysis['slope_60d']['annual_return']:.2f}%",
                '120日年化收益': f"{analysis['slope_120d']['annual_return']:.2f}%",
                '相对MA偏离': f"{analysis['ma_relative']['deviation_pct']:.2f}%",
                'Z-Score': round(analysis['zscore']['value'], 2),
                'Z-Score等级': analysis['zscore']['level'],
                '风险评分': round(analysis['risk_score'], 1),
                '风险等级': analysis['risk_level'],
                '操作建议': analysis['recommendation']
            })
        except Exception as e:
            results.append({
                '指数': symbol,
                '错误': str(e)
            })

    return pd.DataFrame(results)


if __name__ == '__main__':
    # 测试代码
    print("=" * 80)
    print("趋势斜率分析器测试")
    print("=" * 80)

    # 测试单个指数
    print("\n1. 纳斯达克综合指数 (^IXIC) 分析:")
    print("-" * 80)
    analyzer = SlopeAnalyzer('^IXIC')
    result = analyzer.comprehensive_analysis()

    print(f"当前价格: {result['current_price']:.2f}")
    print(f"60日年化收益: {result['slope_60d']['annual_return']:.2f}%")
    print(f"120日年化收益: {result['slope_120d']['annual_return']:.2f}%")
    print(f"Z-Score: {result['zscore']['value']:.2f} ({result['zscore']['level']})")
    print(f"风险评分: {result['risk_score']:.1f} ({result['risk_level']})")
    print(f"操作建议: {result['recommendation']}")

    # 对比分析
    print("\n2. 美股vs港股对比分析:")
    print("-" * 80)
    comparison = compare_slopes(['^IXIC', '^GSPC', '^HSI'])
    print(comparison.to_string(index=False))
