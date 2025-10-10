#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四指标共振策略 - 自动测试脚本
无需交互，直接运行测试
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


def test_strategy():
    """测试策略"""
    print("\n" + "="*70)
    print("四指标共振策略 - 自动测试")
    print("="*70)

    # 测试列表
    test_targets = [
        ('sh000001', '上证指数'),
        ('sz399006', '创业板指'),
        ('512690', '酒ETF'),
    ]

    for code, name in test_targets:
        try:
            print(f"\n{'='*70}")
            print(f"正在分析: {name} ({code})")
            print(f"{'='*70}")

            # 1. 获取数据
            print(f"\n[1/3] 获取历史数据...")
            if code.startswith('sh') or code.startswith('sz'):
                df = ak.stock_zh_index_daily(symbol=code)
            else:
                df = ak.fund_etf_hist_em(symbol=code, period="daily", adjust="qfq")
                df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close',
                                        '最高': 'high', '最低': 'low', '成交量': 'volume'})

            df = df.tail(100)
            print(f"✅ 成功获取 {len(df)} 天数据")

            # 2. 计算指标
            print(f"[2/3] 计算技术指标...")
            calculator = TechnicalIndicators()
            df = calculator.calculate_all_indicators(df)
            print(f"✅ 技术指标计算完成")

            # 3. 生成信号
            print(f"[3/3] 生成交易信号...")
            generator = ResonanceSignalGenerator()
            signal = generator.generate_trading_signal(df)
            print(f"✅ 信号生成完成\n")

            # 4. 打印报告
            generator.print_signal_report(signal, name)

        except Exception as e:
            print(f"❌ 分析{name}失败: {str(e)}\n")
            continue

    print("\n" + "="*70)
    print("✅ 测试完成！")
    print("="*70)


if __name__ == '__main__':
    test_strategy()
