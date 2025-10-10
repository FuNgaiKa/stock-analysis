#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测框架自动测试
无需交互，直接运行
"""

import sys
import os

# 设置UTF-8输出
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import akshare as ak
from trading_strategies.signal_generators.technical_indicators import TechnicalIndicators
from trading_strategies.signal_generators.resonance_signals import ResonanceSignalGenerator
from trading_strategies.backtesting.backtest_engine import BacktestEngine
from trading_strategies.backtesting.performance_metrics import PerformanceMetrics


def test_backtest():
    """测试回测框架"""
    print("\n" + "="*70)
    print("四指标共振策略 - 回测框架测试")
    print("="*70)

    try:
        # 1. 获取数据
        print("\n[1/5] 获取测试数据 (上证指数, 500天)...")
        df = ak.stock_zh_index_daily(symbol='sh000001')
        df = df.tail(500)
        df = df.set_index('date')
        print(f"✅ 获取 {len(df)} 天数据 ({df.index[0]} 至 {df.index[-1]})")

        # 2. 计算指标
        print("\n[2/5] 计算技术指标...")
        calculator = TechnicalIndicators()
        df = calculator.calculate_all_indicators(df)
        print("✅ 技术指标计算完成")

        # 3. 运行回测
        print("\n[3/5] 运行回测...")
        generator = ResonanceSignalGenerator()
        engine = BacktestEngine(
            initial_capital=100000,
            commission=0.0003,
            stop_loss=0.08,
            take_profit=0.15
        )

        result = engine.run_backtest_with_strategy(df, generator)
        print("✅ 回测完成")

        # 4. 计算性能
        print("\n[4/5] 计算性能指标...")
        metrics = PerformanceMetrics()
        performance = metrics.generate_performance_report(
            returns=result['daily_returns'],
            trades=result['trades'],
            initial_capital=100000
        )
        print("✅ 性能指标计算完成")

        # 5. 打印报告
        print("\n[5/5] 生成报告...\n")
        metrics.print_performance_report(performance, "上证指数 - 四指标共振策略")

        # 打印部分交易明细
        if result['trades']:
            print("="*70)
            print("📋 交易明细 (前5笔)")
            print("="*70)
            print(f"\n{'入场日期':<12} {'出场日期':<12} {'入场价':<8} {'出场价':<8} {'收益率':<10}")
            print("-"*70)

            for i, trade in enumerate(result['trades'][:5]):
                entry_date = str(trade['entry_date'])[:10]
                exit_date = str(trade['exit_date'])[:10]
                print(f"{entry_date:<12} {exit_date:<12} {trade['entry_price']:<8.2f} "
                      f"{trade['exit_price']:<8.2f} {trade['return']*100:>8.2f}%")

            if len(result['trades']) > 5:
                print(f"\n... 还有 {len(result['trades']) - 5} 笔交易未显示")

        print("\n" + "="*70)
        print("✅ 回测框架测试完成！")
        print("="*70)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_backtest()
