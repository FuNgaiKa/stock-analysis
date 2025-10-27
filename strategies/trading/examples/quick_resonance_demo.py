#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四指标共振策略 - 快速启动示例
支持股票、ETF、指数的买卖点分析
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import akshare as ak
import pandas as pd
from strategies.trading.signal_generators.technical_indicators import TechnicalIndicators
from strategies.trading.signal_generators.resonance_signals import ResonanceSignalGenerator


def analyze_stock(code: str, name: str = None, days: int = 100):
    """
    分析单只股票/ETF/指数的买卖点

    Args:
        code: 股票代码 (如 '000001', '512690', 'sh000001')
        name: 股票名称
        days: 获取最近多少天的数据
    """
    try:
        print(f"\n{'='*70}")
        print(f"正在分析: {name or code}")
        print(f"{'='*70}")

        # 1. 获取数据
        print(f"\n[1/3] 获取历史数据 (最近{days}天)...")

        # 判断类型
        if code.startswith('sh') or code.startswith('sz'):
            # 指数
            df = ak.stock_zh_index_daily(symbol=code)
        elif len(code) == 6 and code[0] in ['5', '1']:
            # ETF
            df = ak.fund_etf_hist_em(symbol=code, period="daily", adjust="qfq")
            df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close',
                                    '最高': 'high', '最低': 'low', '成交量': 'volume'})
        else:
            # 股票
            df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close',
                                    '最高': 'high', '最低': 'low', '成交量': 'volume'})

        df = df.tail(days)

        if df.empty:
            print(f"❌ 无法获取{code}的数据")
            return None

        print(f"✅ 成功获取 {len(df)} 天数据")

        # 2. 计算技术指标
        print(f"\n[2/3] 计算技术指标 (MACD, RSI, KDJ, MA)...")
        calculator = TechnicalIndicators()
        df = calculator.calculate_all_indicators(df)
        print(f"✅ 技术指标计算完成")

        # 3. 生成交易信号
        print(f"\n[3/3] 分析买卖点信号...")
        generator = ResonanceSignalGenerator()
        signal = generator.generate_trading_signal(df)
        print(f"✅ 信号生成完成\n")

        # 4. 打印报告
        generator.print_signal_report(signal, name or code)

        # 5. 显示最近5天的信号趋势
        print("【最近5天信号趋势】")
        recent_signals = generator.scan_signals_batch(df, lookback=5)

        print(f"\n{'日期':<12} {'收盘价':<8} {'信号':<15} {'买入':<6} {'卖出':<6} {'置信度':<6}")
        print("-" * 70)

        for _, row in recent_signals.iterrows():
            date_str = str(row['date'])[:10]
            print(f"{date_str:<12} {row['close']:<8.2f} {row['action']:<15} "
                  f"{row['buy_score']:<6.1f} {row['sell_score']:<6.1f} {row['confidence']:<6.2f}")

        return signal

    except Exception as e:
        print(f"❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def batch_analyze(targets: list):
    """
    批量分析多只标的

    Args:
        targets: [(code, name), ...] 列表
    """
    print("\n" + "="*70)
    print("📊 批量分析模式")
    print("="*70)

    results = []

    for code, name in targets:
        signal = analyze_stock(code, name, days=100)
        if signal:
            results.append({
                'code': code,
                'name': name,
                'action': signal['action'],
                'buy_score': signal['buy_score'],
                'sell_score': signal['sell_score'],
                'confidence': signal['confidence']
            })

    # 汇总报告
    if results:
        print("\n" + "="*70)
        print("📋 批量分析汇总")
        print("="*70)

        df_results = pd.DataFrame(results)
        print(df_results.to_string(index=False))

        # 筛选强买入信号
        strong_buys = df_results[df_results['action'].isin(['STRONG_BUY', 'BUY'])]
        if not strong_buys.empty:
            print("\n🟢 发现买入机会:")
            print(strong_buys[['name', 'action', 'buy_score', 'confidence']].to_string(index=False))


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         四指标共振买卖点策略 v1.0                            ║
║         基于 MACD + RSI + KDJ + MA 的组合信号                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    print("请选择分析模式:")
    print("1. 单只分析 (输入代码)")
    print("2. 批量分析 (预设列表)")
    print("3. 快速分析 (上证指数)")

    choice = input("\n请输入选项 (1/2/3): ").strip()

    if choice == '1':
        # 单只分析
        code = input("请输入股票/ETF/指数代码 (如 000001, 512690, sh000001): ").strip()
        name = input("请输入名称 (可选): ").strip() or None
        analyze_stock(code, name)

    elif choice == '2':
        # 批量分析
        print("\n将分析以下标的:")
        targets = [
            ('sh000001', '上证指数'),
            ('sz399006', '创业板指'),
            ('sh000300', '沪深300'),
            ('512690', '酒ETF'),
            ('512880', '证券ETF'),
            ('159870', '化工ETF'),
        ]

        for code, name in targets:
            print(f"  - {name} ({code})")

        confirm = input("\n确认开始分析? (y/n): ").strip().lower()
        if confirm == 'y':
            batch_analyze(targets)

    elif choice == '3':
        # 快速分析上证指数
        analyze_stock('sh000001', '上证指数')

    else:
        print("❌ 无效选项")


if __name__ == '__main__':
    main()
