"""
Alpha101 因子库
基于 WorldQuant Alpha101 论文，实现Top 10高效因子

参考文献:
- "101 Formulaic Alphas" by Zura Kakushadze (2016)
- WorldQuant Research
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class Alpha101Engine:
    """Alpha101 因子计算引擎"""

    def __init__(self, symbol: str, start_date: str = None, end_date: str = None):
        """
        初始化因子引擎

        Args:
            symbol: 股票代码
            start_date: 开始日期 (默认1年前)
            end_date: 结束日期 (默认今天)
        """
        self.symbol = symbol
        self.end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        self.start_date = start_date or (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # 下载数据
        self.data = yf.download(symbol, start=self.start_date, end=self.end_date, progress=False)

        # 处理多层索引
        if isinstance(self.data.columns, pd.MultiIndex):
            self.data = self.data.droplevel(1, axis=1)

        # 移除NaN
        self.data = self.data.dropna()

        # 基础数据
        self.close = self.data['Close']
        self.open = self.data['Open']
        self.high = self.data['High']
        self.low = self.data['Low']
        self.volume = self.data['Volume']

        # 预计算常用指标
        self.returns = self.close.pct_change()
        self.vwap = (self.high + self.low + self.close) / 3

    # ==================== 辅助函数 ====================

    def ts_sum(self, series: pd.Series, window: int) -> pd.Series:
        """时间序列求和"""
        return series.rolling(window=window).sum()

    def ts_mean(self, series: pd.Series, window: int) -> pd.Series:
        """时间序列均值"""
        return series.rolling(window=window).mean()

    def ts_std(self, series: pd.Series, window: int) -> pd.Series:
        """时间序列标准差"""
        return series.rolling(window=window).std()

    def ts_rank(self, series: pd.Series, window: int) -> pd.Series:
        """时间序列排名 (0-1标准化)"""
        return series.rolling(window=window).apply(
            lambda x: pd.Series(x).rank().iloc[-1] / len(x), raw=False
        )

    def ts_argmax(self, series: pd.Series, window: int) -> pd.Series:
        """时间序列最大值位置"""
        return series.rolling(window=window).apply(lambda x: x.argmax(), raw=True)

    def ts_argmin(self, series: pd.Series, window: int) -> pd.Series:
        """时间序列最小值位置"""
        return series.rolling(window=window).apply(lambda x: x.argmin(), raw=True)

    def delta(self, series: pd.Series, period: int = 1) -> pd.Series:
        """差分"""
        return series.diff(period)

    def delay(self, series: pd.Series, period: int = 1) -> pd.Series:
        """延迟"""
        return series.shift(period)

    def correlation(self, x: pd.Series, y: pd.Series, window: int) -> pd.Series:
        """滚动相关系数"""
        return x.rolling(window=window).corr(y)

    def covariance(self, x: pd.Series, y: pd.Series, window: int) -> pd.Series:
        """滚动协方差"""
        return x.rolling(window=window).cov(y)

    def rank(self, series: pd.Series) -> pd.Series:
        """横截面排名"""
        return series.rank(pct=True)

    def scale(self, series: pd.Series, k: float = 1) -> pd.Series:
        """标准化到和为k"""
        return series / series.abs().sum() * k

    def ts_max(self, series: pd.Series, window: int) -> pd.Series:
        """时间序列最大值"""
        return series.rolling(window=window).max()

    def ts_min(self, series: pd.Series, window: int) -> pd.Series:
        """时间序列最小值"""
        return series.rolling(window=window).min()

    # ==================== Top 10 Alpha因子 ====================

    def alpha001(self) -> pd.Series:
        """
        Alpha#1: 动量反转因子
        公式: rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5))

        逻辑: 当收益为负时使用波动率，否则使用价格，寻找5日内最大值的位置
        类型: 反转
        """
        condition = self.returns < 0
        stddev_20 = self.ts_std(self.returns, 20)
        inner = np.where(condition, stddev_20, self.close)
        power = np.power(inner, 2)
        return self.rank(self.ts_argmax(pd.Series(power, index=self.close.index), 5))

    def alpha002(self) -> pd.Series:
        """
        Alpha#2: 价格-成交量相关性
        公式: -1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6)

        逻辑: 成交量变化与价格振幅的负相关
        类型: 反转
        """
        log_volume = np.log(self.volume + 1)
        volume_delta = self.delta(log_volume, 2)
        price_change = (self.close - self.open) / self.open

        return -1 * self.correlation(
            self.rank(volume_delta),
            self.rank(price_change),
            6
        )

    def alpha003(self) -> pd.Series:
        """
        Alpha#3: 开盘价相关性
        公式: -1 * correlation(rank(open), rank(volume), 10)

        逻辑: 开盘价与成交量的负相关
        类型: 反转
        """
        return -1 * self.correlation(self.rank(self.open), self.rank(self.volume), 10)

    def alpha004(self) -> pd.Series:
        """
        Alpha#4: 低价动量
        公式: -1 * Ts_Rank(rank(low), 9)

        逻辑: 低价的时间序列排名的负值
        类型: 反转
        """
        return -1 * self.ts_rank(self.rank(self.low), 9)

    def alpha006(self) -> pd.Series:
        """
        Alpha#6: 开盘价-成交量相关性
        公式: -1 * correlation(open, volume, 10)

        逻辑: 开盘价与成交量的负相关
        类型: 反转
        """
        return -1 * self.correlation(self.open, self.volume, 10)

    def alpha007(self) -> pd.Series:
        """
        Alpha#7: 振幅-成交量因子
        公式: ((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : -1)

        逻辑: 基于成交量条件的价格变动排名
        类型: 趋势
        """
        adv20 = self.ts_mean(self.volume, 20)
        delta_close = self.delta(self.close, 7)
        condition = adv20 < self.volume

        result = np.where(
            condition,
            -1 * self.ts_rank(abs(delta_close), 60) * np.sign(delta_close),
            -1
        )
        return pd.Series(result, index=self.close.index)

    def alpha009(self) -> pd.Series:
        """
        Alpha#9: 收盘价delta因子
        公式: ((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) :
               ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))

        逻辑: 基于5日最小/最大delta的条件选择
        类型: 动量
        """
        delta_close = self.delta(self.close, 1)
        ts_min_5 = self.ts_min(delta_close, 5)
        ts_max_5 = self.ts_max(delta_close, 5)

        result = np.where(
            ts_min_5 > 0,
            delta_close,
            np.where(ts_max_5 < 0, delta_close, -1 * delta_close)
        )
        return pd.Series(result, index=self.close.index)

    def alpha012(self) -> pd.Series:
        """
        Alpha#12: 符号-成交量因子
        公式: sign(delta(volume, 1)) * (-1 * delta(close, 1))

        逻辑: 成交量变化符号与价格变化的反向关系
        类型: 反转
        """
        return np.sign(self.delta(self.volume, 1)) * (-1 * self.delta(self.close, 1))

    def alpha017(self) -> pd.Series:
        """
        Alpha#17: VWAP-收盘价相关性
        公式: (((-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1))) *
               rank(ts_rank((volume / adv20), 5)))

        逻辑: 综合价格排名、价格加速度、相对成交量
        类型: 复合
        """
        adv20 = self.ts_mean(self.volume, 20)
        part1 = -1 * self.rank(self.ts_rank(self.close, 10))
        part2 = self.rank(self.delta(self.delta(self.close, 1), 1))
        part3 = self.rank(self.ts_rank(self.volume / adv20, 5))

        return part1 * part2 * part3

    def alpha021(self) -> pd.Series:
        """
        Alpha#21: 线性回归因子
        公式: 复杂的条件分支，基于adv20和close的关系

        逻辑: 基于均值和线性回归的综合因子
        类型: 趋势
        """
        adv20 = self.ts_mean(self.volume, 20)
        mean_close = self.ts_mean(self.close, 8)

        # 简化版本: 使用收盘价相对均值的偏离
        condition1 = (mean_close + self.ts_std(self.close, 8)) < mean_close
        condition2 = mean_close < (mean_close - self.ts_std(self.close, 8))

        result = np.where(
            condition1,
            -1,
            np.where(
                condition2,
                1,
                np.where(
                    self.volume < adv20,
                    -1,
                    (self.close - mean_close) / mean_close
                )
            )
        )
        return pd.Series(result, index=self.close.index)

    # ==================== 因子评估 ====================

    def calculate_all_alphas(self) -> Dict[str, pd.Series]:
        """计算所有Top 10因子"""
        alphas = {
            'alpha001': self.alpha001(),
            'alpha002': self.alpha002(),
            'alpha003': self.alpha003(),
            'alpha004': self.alpha004(),
            'alpha006': self.alpha006(),
            'alpha007': self.alpha007(),
            'alpha009': self.alpha009(),
            'alpha012': self.alpha012(),
            'alpha017': self.alpha017(),
            'alpha021': self.alpha021()
        }
        return alphas

    def get_latest_signals(self) -> Dict[str, float]:
        """获取最新的因子信号"""
        alphas = self.calculate_all_alphas()
        signals = {}

        for name, series in alphas.items():
            # 获取最新的非NaN值
            latest = series.dropna().iloc[-1] if len(series.dropna()) > 0 else 0
            signals[name] = float(latest)

        return signals

    def comprehensive_analysis(self) -> Dict[str, Any]:
        """综合因子分析"""
        try:
            signals = self.get_latest_signals()

            # 计算因子统计
            alpha_stats = {}
            alphas = self.calculate_all_alphas()

            for name, series in alphas.items():
                clean_series = series.dropna()
                if len(clean_series) > 0:
                    alpha_stats[name] = {
                        'current': float(clean_series.iloc[-1]),
                        'mean': float(clean_series.mean()),
                        'std': float(clean_series.std()),
                        'min': float(clean_series.min()),
                        'max': float(clean_series.max()),
                        'percentile': float(self._calculate_percentile(clean_series, clean_series.iloc[-1]))
                    }

            # 综合信号
            positive_count = sum(1 for v in signals.values() if v > 0)
            negative_count = sum(1 for v in signals.values() if v < 0)
            avg_signal = np.mean(list(signals.values()))

            # 信号强度
            if positive_count >= 7:
                signal_strength = 'strong_bullish'
                recommendation = '✅ 强烈看多 - 多个因子共振'
            elif positive_count >= 5:
                signal_strength = 'bullish'
                recommendation = '⬆️ 看多 - 因子偏多'
            elif negative_count >= 7:
                signal_strength = 'strong_bearish'
                recommendation = '❌ 强烈看空 - 多个因子共振'
            elif negative_count >= 5:
                signal_strength = 'bearish'
                recommendation = '⬇️ 看空 - 因子偏空'
            else:
                signal_strength = 'neutral'
                recommendation = '➡️ 中性 - 因子分歧'

            return {
                'symbol': self.symbol,
                'analysis_date': self.end_date,
                'signals': signals,
                'alpha_stats': alpha_stats,
                'summary': {
                    'positive_count': positive_count,
                    'negative_count': negative_count,
                    'neutral_count': 10 - positive_count - negative_count,
                    'avg_signal': avg_signal,
                    'signal_strength': signal_strength,
                    'recommendation': recommendation
                }
            }

        except Exception as e:
            return {
                'symbol': self.symbol,
                'error': str(e),
                'analysis_date': self.end_date
            }

    def _calculate_percentile(self, series: pd.Series, value: float) -> float:
        """计算百分位"""
        from scipy import stats
        return stats.percentileofscore(series, value)


if __name__ == '__main__':
    # 测试代码
    print("=" * 80)
    print("Alpha101 因子引擎测试")
    print("=" * 80)

    # 测试纳斯达克
    print("\n纳斯达克综合指数 (^IXIC) Alpha因子分析:")
    print("-" * 80)

    engine = Alpha101Engine('^IXIC')
    result = engine.comprehensive_analysis()

    if 'error' not in result:
        print(f"\n📊 因子信号:")
        for name, value in result['signals'].items():
            signal = '📈' if value > 0 else '📉' if value < 0 else '➡️'
            print(f"  {name}: {value:>8.4f} {signal}")

        print(f"\n📈 综合评估:")
        summary = result['summary']
        print(f"  看多因子: {summary['positive_count']}/10")
        print(f"  看空因子: {summary['negative_count']}/10")
        print(f"  中性因子: {summary['neutral_count']}/10")
        print(f"  平均信号: {summary['avg_signal']:.4f}")
        print(f"  信号强度: {summary['signal_strength']}")
        print(f"  操作建议: {summary['recommendation']}")

        # 显示因子统计
        print(f"\n📊 因子统计 (前3个):")
        for i, (name, stats) in enumerate(list(result['alpha_stats'].items())[:3]):
            print(f"\n  {name}:")
            print(f"    当前值: {stats['current']:.4f}")
            print(f"    均值: {stats['mean']:.4f}")
            print(f"    标准差: {stats['std']:.4f}")
            print(f"    百分位: {stats['percentile']:.1f}%")
    else:
        print(f"❌ 分析失败: {result['error']}")
