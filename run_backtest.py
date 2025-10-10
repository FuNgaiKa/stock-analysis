#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整回测示例
四指标共振策略的历史回测
"""

import sys
import os

# 设置UTF-8输出
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import akshare as ak
import pandas as pd
from trading_strategies.signal_generators.technical_indicators import TechnicalIndicators
from trading_strategies.signal_generators.resonance_signals import ResonanceSignalGenerator
from trading_strategies.backtesting.backtest_engine import BacktestEngine
from trading_strategies.backtesting.performance_metrics import PerformanceMetrics


def run_full_backtest(
    code: str = 'sh000001',
    name: str = '上证指数',
    days: int = 500,
    initial_capital: float = 100000,
    stop_loss: float = 0.08,
    take_profit: float = 0.15
):
    """
    运行完整回测

    Args:
        code: 标的代码
        name: 标的名称
        days: 回测天数
        initial_capital: 初始资金
        stop_loss: 止损比例
        take_profit: 止盈比例
    """
    print("\n" + "="*70)
    print(f"📊 四指标共振策略 - 完整回测")
    print("="*70)
    print(f"\n标的: {name} ({code})")
    print(f"初始资金: {initial_capital:,.0f} 元")
    print(f"回测周期: {days} 天")
    print(f"止损: {stop_loss*100:.0f}%")
    print(f"止盈: {take_profit*100:.0f}%")

    try:
        # 1. 获取数据
        print(f"\n[步骤1/5] 获取历史数据...")
        if code.startswith('sh') or code.startswith('sz'):
            df = ak.stock_zh_index_daily(symbol=code)
        else:
            df = ak.fund_etf_hist_em(symbol=code, period="daily", adjust="qfq")
            df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close',
                                    '最高': 'high', '最低': 'low', '成交量': 'volume'})

        df = df.tail(days)
        df = df.set_index('date')
        print(f"✅ 成功获取 {len(df)} 天数据 ({df.index[0]} 至 {df.index[-1]})")

        # 2. 计算技术指标
        print(f"\n[步骤2/5] 计算技术指标...")
        calculator = TechnicalIndicators()
        df = calculator.calculate_all_indicators(df)
        print(f"✅ 技术指标计算完成")

        # 3. 运行回测
        print(f"\n[步骤3/5] 运行回测...")
        generator = ResonanceSignalGenerator()
        engine = BacktestEngine(
            initial_capital=initial_capital,
            commission=0.0003,  # 0.03%手续费
            slippage=0.0001,    # 0.01%滑点
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        result = engine.run_backtest_with_strategy(df, generator)
        print(f"✅ 回测完成")

        # 4. 计算性能指标
        print(f"\n[步骤4/5] 计算性能指标...")
        metrics = PerformanceMetrics()
        performance = metrics.generate_performance_report(
            returns=result['daily_returns'],
            trades=result['trades'],
            initial_capital=initial_capital
        )
        print(f"✅ 性能指标计算完成")

        # 5. 打印报告
        print(f"\n[步骤5/5] 生成报告...")
        metrics.print_performance_report(performance, f"{name} - 四指标共振策略")

        # 打印交易明细
        print_trade_details(result['trades'])

        # 绘图 (可选)
        print(f"\n是否生成可视化图表? (y/n): ", end='')
        try:
            choice = input().strip().lower()
            if choice == 'y':
                engine.plot_results(df, save_path=f'backtest_{code}.png')
        except:
            print("跳过绘图")

        return result, performance

    except Exception as e:
        print(f"\n❌ 回测失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def print_trade_details(trades: list):
    """打印交易明细"""
    if not trades:
        print("\n⚠️  没有交易记录")
        return

    print("\n" + "="*70)
    print("📋 交易明细 (前10笔)")
    print("="*70)

    print(f"\n{'入场日期':<12} {'出场日期':<12} {'入场价':<8} {'出场价':<8} {'收益率':<8} {'盈亏':<10} {'信号':<12}")
    print("-"*70)

    for i, trade in enumerate(trades[:10]):
        entry_date = str(trade['entry_date'])[:10]
        exit_date = str(trade['exit_date'])[:10]
        entry_price = trade['entry_price']
        exit_price = trade['exit_price']
        ret = trade['return'] * 100
        pnl = trade['pnl']
        signal = trade.get('signal', 'SELL')

        print(f"{entry_date:<12} {exit_date:<12} {entry_price:<8.2f} {exit_price:<8.2f} "
              f"{ret:>7.2f}% {pnl:>9.2f} {signal:<12}")

    if len(trades) > 10:
        print(f"\n... 还有 {len(trades) - 10} 笔交易未显示")


def batch_backtest():
    """批量回测多个标的"""
    print("\n" + "="*70)
    print("📊 批量回测模式")
    print("="*70)

    targets = [
        ('sh000001', '上证指数'),
        ('sz399006', '创业板指'),
        ('sh000300', '沪深300'),
    ]

    results = []

    for code, name in targets:
        result, performance = run_full_backtest(
            code=code,
            name=name,
            days=500,
            initial_capital=100000,
            stop_loss=0.08,
            take_profit=0.15
        )

        if performance:
            results.append({
                'code': code,
                'name': name,
                'total_return': performance['total_return'],
                'annual_return': performance['annual_return'],
                'sharpe_ratio': performance['sharpe_ratio'],
                'max_drawdown': performance['max_drawdown'],
                'win_rate': performance['win_rate'],
                'total_trades': performance['total_trades']
            })

        print("\n" + "-"*70 + "\n")

    # 汇总对比
    if results:
        print("\n" + "="*70)
        print("📊 批量回测汇总对比")
        print("="*70 + "\n")

        df_results = pd.DataFrame(results)
        print(df_results.to_string(index=False))


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         四指标共振策略 - 回测系统 v1.0                      ║
║         验证策略的历史表现                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    print("请选择回测模式:")
    print("1. 单个回测 (自定义参数)")
    print("2. 快速回测 (上证指数, 500天, 10万初始)")
    print("3. 批量回测 (3个主要指数)")

    try:
        choice = input("\n请输入选项 (1/2/3): ").strip()

        if choice == '1':
            # 单个回测
            code = input("请输入代码 (如 sh000001, 512690): ").strip()
            name = input("请输入名称: ").strip()
            days = int(input("回测天数 (建议500-1000): ").strip() or "500")
            initial = float(input("初始资金 (元, 默认100000): ").strip() or "100000")
            stop_loss = float(input("止损比例 (如0.08表示8%, 默认0.08): ").strip() or "0.08")
            take_profit = float(input("止盈比例 (如0.15表示15%, 默认0.15): ").strip() or "0.15")

            run_full_backtest(code, name, days, initial, stop_loss, take_profit)

        elif choice == '2':
            # 快速回测
            run_full_backtest('sh000001', '上证指数', 500, 100000, 0.08, 0.15)

        elif choice == '3':
            # 批量回测
            batch_backtest()

        else:
            print("❌ 无效选项")

    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
