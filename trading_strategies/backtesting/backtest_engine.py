#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎模块
回测四指标共振策略的历史表现
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BacktestEngine:
    """回测引擎"""

    def __init__(
        self,
        initial_capital: float = 100000,
        commission: float = 0.0003,  # 手续费率 0.03%
        slippage: float = 0.0001,    # 滑点 0.01%
        stop_loss: Optional[float] = None,  # 止损比例
        take_profit: Optional[float] = None,  # 止盈比例
    ):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金
            commission: 手续费率 (买卖双向)
            slippage: 滑点
            stop_loss: 止损比例 (如0.05表示下跌5%止损)
            take_profit: 止盈比例 (如0.15表示上涨15%止盈)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.stop_loss = stop_loss
        self.take_profit = take_profit

        # 回测结果
        self.portfolio_value = []  # 组合价值历史
        self.positions = []        # 持仓记录
        self.trades = []           # 交易记录
        self.daily_returns = []    # 日收益率

    def run_backtest(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        price_column: str = 'close'
    ) -> Dict:
        """
        运行回测

        Args:
            df: 包含价格数据的DataFrame
            signals: 交易信号序列 ('BUY', 'SELL', 'HOLD', etc.)
            price_column: 价格列名

        Returns:
            回测结果字典
        """
        logger.info("开始回测...")

        cash = self.initial_capital
        position = 0  # 持仓数量
        position_value = 0  # 持仓市值
        entry_price = 0  # 入场价格
        entry_date = None  # 入场日期

        portfolio_values = []
        daily_returns = []
        trades = []

        for i in range(len(df)):
            date = df.index[i] if hasattr(df.index[i], 'date') else df.iloc[i].get('date', i)
            price = df.iloc[i][price_column]
            signal = signals.iloc[i] if i < len(signals) else 'HOLD'

            # 检查止损止盈
            if position > 0 and entry_price > 0:
                current_return = (price - entry_price) / entry_price

                # 止损
                if self.stop_loss and current_return <= -self.stop_loss:
                    signal = 'STOP_LOSS'
                    logger.info(f"{date}: 触发止损 ({current_return*100:.2f}%)")

                # 止盈
                elif self.take_profit and current_return >= self.take_profit:
                    signal = 'TAKE_PROFIT'
                    logger.info(f"{date}: 触发止盈 ({current_return*100:.2f}%)")

            # 处理交易信号
            if signal in ['STRONG_BUY', 'BUY'] and position == 0:
                # 买入
                buy_price = price * (1 + self.slippage)
                shares = int(cash / buy_price)

                if shares > 0:
                    cost = shares * buy_price
                    commission_fee = cost * self.commission

                    cash -= (cost + commission_fee)
                    position = shares
                    entry_price = buy_price
                    entry_date = date

                    logger.info(f"{date}: 买入 {shares} 股 @ {buy_price:.2f}, 手续费 {commission_fee:.2f}")

            elif signal in ['STRONG_SELL', 'SELL', 'STOP_LOSS', 'TAKE_PROFIT'] and position > 0:
                # 卖出
                sell_price = price * (1 - self.slippage)
                revenue = position * sell_price
                commission_fee = revenue * self.commission

                cash += (revenue - commission_fee)

                # 记录交易
                trade_return = (sell_price - entry_price) / entry_price
                pnl = (sell_price - entry_price) * position - commission_fee * 2

                trade = {
                    'entry_date': entry_date,
                    'exit_date': date,
                    'entry_price': entry_price,
                    'exit_price': sell_price,
                    'shares': position,
                    'return': trade_return,
                    'pnl': pnl,
                    'signal': signal
                }
                trades.append(trade)

                logger.info(f"{date}: 卖出 {position} 股 @ {sell_price:.2f}, "
                           f"收益率 {trade_return*100:.2f}%, 盈亏 {pnl:.2f}")

                position = 0
                entry_price = 0
                entry_date = None

            # 计算组合价值
            position_value = position * price if position > 0 else 0
            total_value = cash + position_value
            portfolio_values.append(total_value)

            # 计算日收益率
            if i > 0:
                daily_return = (total_value - portfolio_values[i-1]) / portfolio_values[i-1]
                daily_returns.append(daily_return)
            else:
                daily_returns.append(0)

        # 保存结果
        self.portfolio_value = portfolio_values
        self.trades = trades
        self.daily_returns = pd.Series(daily_returns)

        # 生成回测结果
        result = {
            'portfolio_value': portfolio_values,
            'daily_returns': self.daily_returns,
            'trades': trades,
            'final_capital': portfolio_values[-1] if portfolio_values else self.initial_capital,
            'total_return': (portfolio_values[-1] - self.initial_capital) / self.initial_capital if portfolio_values else 0
        }

        logger.info("回测完成")
        return result

    def run_backtest_with_strategy(
        self,
        df: pd.DataFrame,
        signal_generator,
        price_column: str = 'close'
    ) -> Dict:
        """
        使用策略对象运行回测

        Args:
            df: 包含技术指标的DataFrame
            signal_generator: 信号生成器对象 (ResonanceSignalGenerator)
            price_column: 价格列名

        Returns:
            回测结果字典
        """
        logger.info("使用策略生成器进行回测...")

        # 生成所有交易信号
        signals = []
        for i in range(len(df)):
            try:
                signal = signal_generator.generate_trading_signal(df, index=i)
                signals.append(signal['action'])
            except Exception as e:
                logger.warning(f"第{i}天信号生成失败: {str(e)}")
                signals.append('HOLD')

        signals_series = pd.Series(signals, index=df.index)

        # 运行回测
        return self.run_backtest(df, signals_series, price_column)

    def get_trade_statistics(self) -> Dict:
        """
        获取交易统计信息

        Returns:
            交易统计字典
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_return': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }

        wins = [t for t in self.trades if t['return'] > 0]
        losses = [t for t in self.trades if t['return'] <= 0]

        win_rate = len(wins) / len(self.trades)
        avg_return = np.mean([t['return'] for t in self.trades])
        avg_win = np.mean([t['return'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['return'] for t in losses]) if losses else 0

        total_profit = sum([t['pnl'] for t in wins])
        total_loss = abs(sum([t['pnl'] for t in losses]))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        return {
            'total_trades': len(self.trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': win_rate,
            'avg_return': avg_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }

    def plot_results(self, df: pd.DataFrame, save_path: Optional[str] = None):
        """
        绘制回测结果 (使用matplotlib)

        Args:
            df: 原始数据DataFrame
            save_path: 保存路径
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib import rcParams

            # 设置中文字体
            rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
            rcParams['axes.unicode_minus'] = False

            fig, axes = plt.subplots(3, 1, figsize=(14, 10))

            # 1. 组合价值曲线
            ax1 = axes[0]
            ax1.plot(self.portfolio_value, label='组合价值', color='blue', linewidth=2)
            ax1.axhline(y=self.initial_capital, color='red', linestyle='--', label='初始资金')
            ax1.set_title('组合价值曲线', fontsize=14, fontweight='bold')
            ax1.set_ylabel('资金 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # 2. 价格和买卖点
            ax2 = axes[1]
            ax2.plot(df.index, df['close'], label='收盘价', color='black', linewidth=1)

            # 标记买卖点
            for trade in self.trades:
                entry_idx = df.index.get_loc(trade['entry_date']) if trade['entry_date'] in df.index else None
                exit_idx = df.index.get_loc(trade['exit_date']) if trade['exit_date'] in df.index else None

                if entry_idx is not None:
                    ax2.scatter(entry_idx, trade['entry_price'], color='green', marker='^', s=100, zorder=5)

                if exit_idx is not None:
                    color = 'red' if trade['return'] > 0 else 'blue'
                    ax2.scatter(exit_idx, trade['exit_price'], color=color, marker='v', s=100, zorder=5)

            ax2.set_title('价格走势与交易点', fontsize=14, fontweight='bold')
            ax2.set_ylabel('价格 (元)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            # 3. 累计收益率
            ax3 = axes[2]
            cumulative_returns = (1 + self.daily_returns).cumprod() - 1
            ax3.plot(cumulative_returns, label='累计收益率', color='green', linewidth=2)
            ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax3.set_title('累计收益率', fontsize=14, fontweight='bold')
            ax3.set_ylabel('收益率')
            ax3.set_xlabel('时间')
            ax3.legend()
            ax3.grid(True, alpha=0.3)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"回测图表已保存至: {save_path}")

            plt.show()

        except ImportError:
            logger.warning("matplotlib未安装，无法绘图")

    def print_summary(self):
        """打印回测摘要"""
        stats = self.get_trade_statistics()

        print("\n" + "="*70)
        print("📊 回测摘要")
        print("="*70)

        print(f"\n初始资金: {self.initial_capital:,.0f} 元")
        print(f"期末资金: {self.portfolio_value[-1]:,.0f} 元" if self.portfolio_value else "N/A")
        print(f"总收益率: {((self.portfolio_value[-1] - self.initial_capital) / self.initial_capital * 100):.2f}%" if self.portfolio_value else "N/A")

        print(f"\n总交易次数: {stats['total_trades']}")
        print(f"盈利次数: {stats['winning_trades']}")
        print(f"亏损次数: {stats['losing_trades']}")
        print(f"胜率: {stats['win_rate']*100:.2f}%")
        print(f"平均收益: {stats['avg_return']*100:.2f}%")
        print(f"平均盈利: {stats['avg_win']*100:.2f}%")
        print(f"平均亏损: {stats['avg_loss']*100:.2f}%")
        print(f"盈亏比: {stats['profit_factor']:.2f}")

        print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    # 测试代码
    import akshare as ak
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from signal_generators.technical_indicators import TechnicalIndicators
    from signal_generators.resonance_signals import ResonanceSignalGenerator

    print("="*70)
    print("回测引擎 - 测试")
    print("="*70)

    # 1. 获取数据
    print("\n1. 获取测试数据...")
    df = ak.stock_zh_index_daily(symbol='sh000001')
    df = df.tail(500)  # 最近500天
    df = df.set_index('date')
    print(f"✅ 获取 {len(df)} 天数据")

    # 2. 计算指标
    print("2. 计算技术指标...")
    calculator = TechnicalIndicators()
    df = calculator.calculate_all_indicators(df)
    print("✅ 指标计算完成")

    # 3. 运行回测
    print("3. 运行回测...")
    generator = ResonanceSignalGenerator()
    engine = BacktestEngine(
        initial_capital=100000,
        commission=0.0003,
        stop_loss=0.08,      # 8%止损
        take_profit=0.15      # 15%止盈
    )

    result = engine.run_backtest_with_strategy(df, generator)
    print("✅ 回测完成")

    # 4. 打印结果
    engine.print_summary()

    # 5. 绘图 (可选)
    # engine.plot_results(df, save_path='backtest_result.png')
