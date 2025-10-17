"""
简单实用的回测引擎
支持斜率策略、Alpha因子策略的回测和性能评估
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable
from datetime import datetime
import yfinance as yf


class BacktestEngine:
    """回测引擎"""

    def __init__(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 100000.0,
        commission: float = 0.001  # 0.1% 手续费
    ):
        """
        初始化回测引擎

        Args:
            symbol: 股票代码
            start_date: 回测开始日期
            end_date: 回测结束日期
            initial_capital: 初始资金
            commission: 手续费率
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.commission = commission

        # 下载数据
        self.data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        if isinstance(self.data.columns, pd.MultiIndex):
            self.data = self.data.droplevel(1, axis=1)
        self.data = self.data.dropna()

        # 回测结果
        self.trades = []
        self.equity_curve = []

    def run_strategy(
        self,
        strategy_func: Callable,
        strategy_name: str = "Custom Strategy"
    ) -> Dict[str, Any]:
        """
        运行回测策略

        Args:
            strategy_func: 策略函数，接收 (data, index) 返回 signal (-1, 0, 1)
            strategy_name: 策略名称

        Returns:
            回测结果字典
        """
        print(f"\n{'='*80}")
        print(f"回测策略: {strategy_name}")
        print(f"标的: {self.symbol}")
        print(f"周期: {self.start_date} 至 {self.end_date}")
        print(f"初始资金: ${self.initial_capital:,.2f}")
        print(f"{'='*80}\n")

        # 初始化
        cash = self.initial_capital
        position = 0  # 持仓数量
        equity = self.initial_capital
        self.trades = []
        self.equity_curve = []

        # 遍历每个交易日
        for i in range(len(self.data)):
            current_price = self.data['Close'].iloc[i]
            current_date = self.data.index[i]

            # 生成信号
            signal = strategy_func(self.data, i)

            # 执行交易
            if signal == 1 and position == 0:  # 买入信号
                # 全仓买入
                shares = int(cash / current_price)
                if shares > 0:
                    cost = shares * current_price * (1 + self.commission)
                    if cost <= cash:
                        position = shares
                        cash -= cost
                        self.trades.append({
                            'date': current_date,
                            'action': 'BUY',
                            'price': current_price,
                            'shares': shares,
                            'cost': cost
                        })

            elif signal == -1 and position > 0:  # 卖出信号
                # 全部卖出
                proceeds = position * current_price * (1 - self.commission)
                cash += proceeds
                self.trades.append({
                    'date': current_date,
                    'action': 'SELL',
                    'price': current_price,
                    'shares': position,
                    'proceeds': proceeds
                })
                position = 0

            # 计算当前权益
            equity = cash + position * current_price
            self.equity_curve.append({
                'date': current_date,
                'equity': equity,
                'cash': cash,
                'position_value': position * current_price
            })

        # 最后一天强制平仓
        if position > 0:
            final_price = self.data['Close'].iloc[-1]
            proceeds = position * final_price * (1 - self.commission)
            cash += proceeds
            self.trades.append({
                'date': self.data.index[-1],
                'action': 'SELL',
                'price': final_price,
                'shares': position,
                'proceeds': proceeds
            })

        # 计算性能指标
        performance = self._calculate_performance()

        return performance

    def _calculate_performance(self) -> Dict[str, Any]:
        """计算回测性能指标"""
        if len(self.equity_curve) == 0:
            return {}

        # 转换为DataFrame
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('date', inplace=True)

        # 计算收益率
        returns = equity_df['equity'].pct_change().dropna()

        # 最终权益
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital

        # 年化收益率
        days = (equity_df.index[-1] - equity_df.index[0]).days
        annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0

        # 夏普比率 (假设无风险利率为3%)
        risk_free_rate = 0.03
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0

        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # 胜率
        winning_trades = [t for t in self.trades if t['action'] == 'SELL']
        if len(winning_trades) > 1:
            profits = []
            for i in range(len(winning_trades)):
                if i > 0:
                    buy_trade = self.trades[self.trades.index(winning_trades[i]) - 1]
                    sell_trade = winning_trades[i]
                    profit = sell_trade['proceeds'] - buy_trade['cost']
                    profits.append(profit)
            win_rate = sum(1 for p in profits if p > 0) / len(profits) if len(profits) > 0 else 0
        else:
            win_rate = 0

        # Buy & Hold 基准
        buy_hold_return = (self.data['Close'].iloc[-1] - self.data['Close'].iloc[0]) / self.data['Close'].iloc[0]
        buy_hold_annual = (1 + buy_hold_return) ** (365 / days) - 1 if days > 0 else 0

        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len([t for t in self.trades if t['action'] == 'BUY']),
            'buy_hold_return': buy_hold_return,
            'buy_hold_annual': buy_hold_annual,
            'excess_return': annual_return - buy_hold_annual
        }

    def print_performance(self, performance: Dict[str, Any]):
        """打印性能报告"""
        print(f"\n{'='*80}")
        print("📊 回测性能报告")
        print(f"{'='*80}\n")

        print(f"💰 收益指标:")
        print(f"  初始资金: ${performance['initial_capital']:>15,.2f}")
        print(f"  最终权益: ${performance['final_equity']:>15,.2f}")
        print(f"  总收益率: {performance['total_return']:>15.2%}")
        print(f"  年化收益率: {performance['annual_return']:>13.2%}")

        print(f"\n📈 风险指标:")
        print(f"  夏普比率: {performance['sharpe_ratio']:>16.2f}")
        print(f"  最大回撤: {performance['max_drawdown']:>16.2%}")

        print(f"\n🎯 交易指标:")
        print(f"  交易次数: {performance['total_trades']:>17}")
        print(f"  胜率: {performance['win_rate']:>21.2%}")

        print(f"\n📊 基准对比:")
        print(f"  Buy&Hold收益: {performance['buy_hold_return']:>13.2%}")
        print(f"  Buy&Hold年化: {performance['buy_hold_annual']:>13.2%}")
        print(f"  超额收益: {performance['excess_return']:>16.2%}")

        # 评级
        print(f"\n⭐ 策略评级:")
        rating = self._rate_strategy(performance)
        print(f"  {rating}")

        print(f"\n{'='*80}\n")

    def _rate_strategy(self, perf: Dict[str, Any]) -> str:
        """策略评级"""
        score = 0

        # 年化收益
        if perf['annual_return'] > 0.20:
            score += 2
        elif perf['annual_return'] > 0.10:
            score += 1

        # 夏普比率
        if perf['sharpe_ratio'] > 2.0:
            score += 2
        elif perf['sharpe_ratio'] > 1.0:
            score += 1

        # 最大回撤
        if perf['max_drawdown'] > -0.10:
            score += 2
        elif perf['max_drawdown'] > -0.20:
            score += 1

        # 超额收益
        if perf['excess_return'] > 0.10:
            score += 2
        elif perf['excess_return'] > 0.05:
            score += 1

        # 胜率
        if perf['win_rate'] > 0.60:
            score += 2
        elif perf['win_rate'] > 0.50:
            score += 1

        if score >= 8:
            return "⭐⭐⭐⭐⭐ 优秀 - 强烈推荐"
        elif score >= 6:
            return "⭐⭐⭐⭐ 良好 - 值得考虑"
        elif score >= 4:
            return "⭐⭐⭐ 中等 - 谨慎使用"
        elif score >= 2:
            return "⭐⭐ 较差 - 需要优化"
        else:
            return "⭐ 很差 - 不推荐"


# ==================== 预定义策略 ====================

def slope_momentum_strategy(data: pd.DataFrame, index: int, threshold: float = 0.20) -> int:
    """
    斜率动量策略

    逻辑:
    - 计算60日线性回归斜率
    - 斜率 > threshold: 买入
    - 斜率 < -threshold: 卖出

    Args:
        data: 价格数据
        index: 当前索引
        threshold: 斜率阈值 (默认20%)

    Returns:
        1: 买入, -1: 卖出, 0: 持有
    """
    if index < 60:
        return 0

    # 获取最近60天的收盘价
    prices = data['Close'].iloc[index-60:index+1].values
    x = np.arange(len(prices))

    # 线性回归
    from scipy import stats
    slope, _, _, _, _ = stats.linregress(x, prices)

    # 计算年化斜率
    daily_slope = slope / prices[0]
    annual_slope = daily_slope * 365

    if annual_slope > threshold:
        return 1  # 买入
    elif annual_slope < -threshold:
        return -1  # 卖出
    else:
        return 0  # 持有


def ma_cross_strategy(data: pd.DataFrame, index: int, fast: int = 20, slow: int = 60) -> int:
    """
    均线交叉策略

    逻辑:
    - 快线上穿慢线: 买入
    - 快线下穿慢线: 卖出

    Args:
        data: 价格数据
        index: 当前索引
        fast: 快线周期
        slow: 慢线周期

    Returns:
        1: 买入, -1: 卖出, 0: 持有
    """
    if index < slow:
        return 0

    close = data['Close']
    ma_fast = close.iloc[index-fast+1:index+1].mean()
    ma_slow = close.iloc[index-slow+1:index+1].mean()

    # 前一天的均线
    if index >= slow + 1:
        ma_fast_prev = close.iloc[index-fast:index].mean()
        ma_slow_prev = close.iloc[index-slow:index].mean()

        # 金叉
        if ma_fast > ma_slow and ma_fast_prev <= ma_slow_prev:
            return 1

        # 死叉
        elif ma_fast < ma_slow and ma_fast_prev >= ma_slow_prev:
            return -1

    return 0


if __name__ == '__main__':
    # 测试回测引擎
    print("=" * 80)
    print("回测引擎测试")
    print("=" * 80)

    # 回测纳斯达克 - 斜率动量策略
    engine = BacktestEngine(
        symbol='^IXIC',
        start_date='2024-01-01',
        end_date='2025-10-12',
        initial_capital=100000
    )

    # 策略1: 斜率动量
    performance1 = engine.run_strategy(
        strategy_func=lambda data, i: slope_momentum_strategy(data, i, threshold=0.15),
        strategy_name="斜率动量策略 (阈值15%)"
    )
    engine.print_performance(performance1)

    # 策略2: 均线交叉
    engine2 = BacktestEngine(
        symbol='^IXIC',
        start_date='2024-01-01',
        end_date='2025-10-12',
        initial_capital=100000
    )
    performance2 = engine2.run_strategy(
        strategy_func=ma_cross_strategy,
        strategy_name="均线交叉策略 (20/60)"
    )
    engine2.print_performance(performance2)
