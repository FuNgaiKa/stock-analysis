#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能评估模块
计算策略的各项性能指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """策略性能评估器"""

    def __init__(self):
        """初始化性能评估器"""
        pass

    @staticmethod
    def calculate_returns(df: pd.DataFrame, price_column: str = 'close') -> pd.Series:
        """
        计算收益率序列

        Args:
            df: 包含价格数据的DataFrame
            price_column: 价格列名

        Returns:
            收益率序列
        """
        return df[price_column].pct_change()

    @staticmethod
    def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
        """
        计算累计收益率

        Args:
            returns: 收益率序列

        Returns:
            累计收益率序列
        """
        return (1 + returns).cumprod() - 1

    @staticmethod
    def calculate_total_return(returns: pd.Series) -> float:
        """
        计算总收益率

        Args:
            returns: 收益率序列

        Returns:
            总收益率
        """
        return (1 + returns).prod() - 1

    @staticmethod
    def calculate_annual_return(returns: pd.Series, periods_per_year: int = 252) -> float:
        """
        计算年化收益率

        Args:
            returns: 收益率序列
            periods_per_year: 每年的交易周期数 (股票默认252个交易日)

        Returns:
            年化收益率
        """
        total_return = (1 + returns).prod()
        n_periods = len(returns)
        years = n_periods / periods_per_year

        if years == 0:
            return 0

        annual_return = total_return ** (1 / years) - 1
        return annual_return

    @staticmethod
    def calculate_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
        """
        计算年化波动率

        Args:
            returns: 收益率序列
            periods_per_year: 每年的交易周期数

        Returns:
            年化波动率
        """
        return returns.std() * np.sqrt(periods_per_year)

    @staticmethod
    def calculate_sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.03,
        periods_per_year: int = 252
    ) -> float:
        """
        计算夏普比率 (Sharpe Ratio)

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率 (年化)
            periods_per_year: 每年的交易周期数

        Returns:
            夏普比率
        """
        annual_return = PerformanceMetrics.calculate_annual_return(returns, periods_per_year)
        volatility = PerformanceMetrics.calculate_volatility(returns, periods_per_year)

        if volatility == 0:
            return 0

        sharpe = (annual_return - risk_free_rate) / volatility
        return sharpe

    @staticmethod
    def calculate_max_drawdown(returns: pd.Series) -> Dict[str, float]:
        """
        计算最大回撤

        Args:
            returns: 收益率序列

        Returns:
            {
                'max_drawdown': 最大回撤,
                'max_drawdown_duration': 最大回撤持续天数,
                'recovery_duration': 恢复天数
            }
        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max

        max_dd = drawdown.min()

        # 找到最大回撤的位置
        max_dd_idx = drawdown.idxmin()

        # 计算回撤持续时间
        if max_dd_idx is not None and not pd.isna(max_dd_idx):
            # 回撤开始点
            dd_start = running_max[:max_dd_idx].idxmax()

            # 回撤持续天数
            dd_duration = (max_dd_idx - dd_start).days if hasattr(max_dd_idx - dd_start, 'days') else 0

            # 恢复时间 (回撤后回到之前高点的时间)
            recovery_idx = cumulative[max_dd_idx:][cumulative >= running_max[max_dd_idx]].index
            if len(recovery_idx) > 0:
                recovery_duration = (recovery_idx[0] - max_dd_idx).days if hasattr(recovery_idx[0] - max_dd_idx, 'days') else 0
            else:
                recovery_duration = None  # 未恢复
        else:
            dd_duration = 0
            recovery_duration = None

        return {
            'max_drawdown': float(max_dd),
            'max_drawdown_duration': dd_duration,
            'recovery_duration': recovery_duration
        }

    @staticmethod
    def calculate_calmar_ratio(
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """
        计算卡玛比率 (Calmar Ratio)
        年化收益率 / 最大回撤

        Args:
            returns: 收益率序列
            periods_per_year: 每年的交易周期数

        Returns:
            卡玛比率
        """
        annual_return = PerformanceMetrics.calculate_annual_return(returns, periods_per_year)
        max_dd = PerformanceMetrics.calculate_max_drawdown(returns)['max_drawdown']

        if max_dd == 0:
            return 0

        return annual_return / abs(max_dd)

    @staticmethod
    def calculate_win_rate(trades: List[Dict]) -> Dict[str, float]:
        """
        计算胜率

        Args:
            trades: 交易记录列表 [{
                'entry_date': 入场日期,
                'exit_date': 出场日期,
                'entry_price': 入场价格,
                'exit_price': 出场价格,
                'return': 收益率,
                'pnl': 盈亏金额
            }, ...]

        Returns:
            {
                'win_rate': 胜率,
                'avg_win': 平均盈利,
                'avg_loss': 平均亏损,
                'profit_factor': 盈亏比
            }
        """
        if not trades:
            return {
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }

        wins = [t for t in trades if t['return'] > 0]
        losses = [t for t in trades if t['return'] <= 0]

        win_rate = len(wins) / len(trades) if trades else 0

        avg_win = np.mean([t['return'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['return'] for t in losses]) if losses else 0

        total_profit = sum([t['pnl'] for t in wins]) if wins else 0
        total_loss = abs(sum([t['pnl'] for t in losses])) if losses else 0

        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        return {
            'win_rate': float(win_rate),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'profit_factor': float(profit_factor)
        }

    @staticmethod
    def calculate_trade_statistics(trades: List[Dict]) -> Dict:
        """
        计算交易统计信息

        Args:
            trades: 交易记录列表

        Returns:
            交易统计字典
        """
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'avg_return_per_trade': 0,
                'avg_holding_days': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0
            }

        wins = [t for t in trades if t['return'] > 0]
        losses = [t for t in trades if t['return'] <= 0]

        avg_return = np.mean([t['return'] for t in trades])

        # 计算平均持仓天数
        holding_days = []
        for t in trades:
            if hasattr(t['exit_date'] - t['entry_date'], 'days'):
                holding_days.append((t['exit_date'] - t['entry_date']).days)
        avg_holding = np.mean(holding_days) if holding_days else 0

        # 计算最大连续盈利/亏损次数
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0

        for t in trades:
            if t['return'] > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)

        return {
            'total_trades': len(trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'avg_return_per_trade': float(avg_return),
            'avg_holding_days': float(avg_holding),
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses
        }

    def generate_performance_report(
        self,
        returns: pd.Series,
        trades: List[Dict],
        initial_capital: float = 100000,
        periods_per_year: int = 252,
        risk_free_rate: float = 0.03
    ) -> Dict:
        """
        生成完整的性能报告

        Args:
            returns: 收益率序列
            trades: 交易记录列表
            initial_capital: 初始资金
            periods_per_year: 每年交易周期数
            risk_free_rate: 无风险利率

        Returns:
            完整的性能指标字典
        """
        # 收益指标
        total_return = self.calculate_total_return(returns)
        annual_return = self.calculate_annual_return(returns, periods_per_year)

        # 风险指标
        volatility = self.calculate_volatility(returns, periods_per_year)
        max_dd_info = self.calculate_max_drawdown(returns)

        # 风险调整收益指标
        sharpe = self.calculate_sharpe_ratio(returns, risk_free_rate, periods_per_year)
        calmar = self.calculate_calmar_ratio(returns, periods_per_year)

        # 交易指标
        win_rate_info = self.calculate_win_rate(trades)
        trade_stats = self.calculate_trade_statistics(trades)

        # 资金指标
        final_capital = initial_capital * (1 + total_return)
        profit = final_capital - initial_capital

        report = {
            # 收益指标
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'final_capital': float(final_capital),
            'profit': float(profit),

            # 风险指标
            'volatility': float(volatility),
            'max_drawdown': float(max_dd_info['max_drawdown']),
            'max_drawdown_duration': max_dd_info['max_drawdown_duration'],
            'recovery_duration': max_dd_info['recovery_duration'],

            # 风险调整收益
            'sharpe_ratio': float(sharpe),
            'calmar_ratio': float(calmar),

            # 交易指标
            'win_rate': float(win_rate_info['win_rate']),
            'avg_win': float(win_rate_info['avg_win']),
            'avg_loss': float(win_rate_info['avg_loss']),
            'profit_factor': float(win_rate_info['profit_factor']),

            # 交易统计
            'total_trades': trade_stats['total_trades'],
            'winning_trades': trade_stats['winning_trades'],
            'losing_trades': trade_stats['losing_trades'],
            'avg_return_per_trade': float(trade_stats['avg_return_per_trade']),
            'avg_holding_days': float(trade_stats['avg_holding_days']),
            'max_consecutive_wins': trade_stats['max_consecutive_wins'],
            'max_consecutive_losses': trade_stats['max_consecutive_losses'],
        }

        return report

    def print_performance_report(self, report: Dict, strategy_name: str = "策略"):
        """
        打印格式化的性能报告

        Args:
            report: 性能报告字典
            strategy_name: 策略名称
        """
        print("\n" + "="*70)
        print(f"📊 {strategy_name} - 回测性能报告")
        print("="*70)

        print("\n【收益指标】")
        print(f"  总收益率: {report['total_return']*100:>8.2f}%")
        print(f"  年化收益率: {report['annual_return']*100:>6.2f}%")
        print(f"  期末资金: {report['final_capital']:>12,.0f} 元")
        print(f"  盈亏金额: {report['profit']:>12,.0f} 元")

        print("\n【风险指标】")
        print(f"  年化波动率: {report['volatility']*100:>6.2f}%")
        print(f"  最大回撤: {abs(report['max_drawdown'])*100:>8.2f}%")
        print(f"  回撤持续: {report['max_drawdown_duration']:>8} 天")
        if report['recovery_duration'] is not None:
            print(f"  恢复时间: {report['recovery_duration']:>8} 天")
        else:
            print(f"  恢复时间: {'未恢复':>8}")

        print("\n【风险调整收益】")
        print(f"  夏普比率: {report['sharpe_ratio']:>8.2f}")
        print(f"  卡玛比率: {report['calmar_ratio']:>8.2f}")

        print("\n【交易指标】")
        print(f"  总交易次数: {report['total_trades']:>6}")
        print(f"  盈利次数: {report['winning_trades']:>8}")
        print(f"  亏损次数: {report['losing_trades']:>8}")
        print(f"  胜率: {report['win_rate']*100:>12.2f}%")
        print(f"  平均盈利: {report['avg_win']*100:>8.2f}%")
        print(f"  平均亏损: {report['avg_loss']*100:>8.2f}%")
        print(f"  盈亏比: {report['profit_factor']:>10.2f}")

        print("\n【交易统计】")
        print(f"  单笔平均收益: {report['avg_return_per_trade']*100:>4.2f}%")
        print(f"  平均持仓天数: {report['avg_holding_days']:>4.1f} 天")
        print(f"  最大连胜: {report['max_consecutive_wins']:>8} 次")
        print(f"  最大连亏: {report['max_consecutive_losses']:>8} 次")

        print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    # 测试代码
    print("性能评估模块 - 测试\n")

    # 模拟收益率序列
    np.random.seed(42)
    returns = pd.Series(np.random.randn(252) * 0.02 + 0.001)  # 模拟一年的日收益率

    # 模拟交易记录
    trades = []
    for i in range(20):
        trade = {
            'entry_date': pd.Timestamp('2024-01-01') + pd.Timedelta(days=i*10),
            'exit_date': pd.Timestamp('2024-01-01') + pd.Timedelta(days=i*10+5),
            'entry_price': 100,
            'exit_price': 100 + np.random.randn() * 5,
            'return': np.random.randn() * 0.05,
            'pnl': np.random.randn() * 5000
        }
        trades.append(trade)

    # 生成性能报告
    metrics = PerformanceMetrics()
    report = metrics.generate_performance_report(
        returns=returns,
        trades=trades,
        initial_capital=100000
    )

    # 打印报告
    metrics.print_performance_report(report, "测试策略")
