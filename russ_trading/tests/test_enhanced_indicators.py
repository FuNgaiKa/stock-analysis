#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强型技术指标
Test Enhanced Technical Indicators

测试新增的7个机构级技术指标:
1. RSI (相对强弱指标)
2. 量比
3. MA20/MA60 (均线系统)
4. ATR (止损位计算)
5. VWAP (成交量加权平均价)
6. 量价背离检测

作者: Claude Code
日期: 2025-11-11
"""

import sys
from pathlib import Path
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from russ_trading.analyzers.technical_analyzer import TechnicalAnalyzer


def test_enhanced_indicators(symbol: str, name: str):
    """
    测试单个标的的增强型技术指标

    Args:
        symbol: 标的代码
        name: 标的名称
    """
    print(f"\n{'='*80}")
    print(f"测试标的: {name} ({symbol})")
    print(f"{'='*80}\n")

    try:
        # 1. 获取数据
        print("📊 正在获取历史数据...")

        # 使用akshare获取指数数据
        try:
            # 计算开始日期(约1年前)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

            # 获取指数数据
            df_raw = ak.stock_zh_index_daily(symbol=symbol)

            # 过滤日期范围
            df_raw['date'] = pd.to_datetime(df_raw['date'])
            df_raw = df_raw[df_raw['date'] >= start_date].copy()

            # 重命名列为中文
            df = pd.DataFrame()
            df['日期'] = df_raw['date']
            df['开盘'] = df_raw['open']
            df['最高'] = df_raw['high']
            df['最低'] = df_raw['low']
            df['收盘'] = df_raw['close']
            df['成交量'] = df_raw['volume']

        except Exception as e:
            print(f"❌ 无法获取 {name} 的数据: {e}")
            return

        if df.empty:
            print(f"❌ 无法获取 {name} 的数据")
            return

        print(f"✅ 获取到 {len(df)} 条数据")
        print(f"   日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
        print(f"   当前价格: {df['收盘'].iloc[-1]:.2f}")
        print(f"   涨跌幅: {((df['收盘'].iloc[-1] - df['收盘'].iloc[-2]) / df['收盘'].iloc[-2] * 100):+.2f}%")

        # 2. 计算增强型技术指标
        print("\n🔧 正在计算机构级技术指标...")
        analyzer = TechnicalAnalyzer()
        signals = analyzer.get_enhanced_signals(df.copy())

        if not signals.get('has_data'):
            print(f"❌ 数据不足,无法计算指标")
            return

        # 3. 格式化输出
        print(f"\n{'='*80}")
        print(f"机构级技术指标分析结果 - {name}")
        print(f"{'='*80}\n")

        report = analyzer.format_enhanced_signals(signals)
        print(report)

        # 4. 详细指标值
        print(f"\n{'='*80}")
        print("详细数值:")
        print(f"{'='*80}")

        print(f"\n1️⃣ RSI (相对强弱指标):")
        rsi = signals.get('rsi', {})
        print(f"   - RSI值: {rsi.get('value', 0):.2f}")
        print(f"   - 信号: {rsi.get('signal', 'N/A')}")
        if rsi.get('value', 50) > 70:
            print(f"   ⚠️ 警告: RSI>70,处于超买区域,可能回调")
        elif rsi.get('value', 50) < 30:
            print(f"   ✅ 提示: RSI<30,处于超卖区域,可能反弹")

        print(f"\n2️⃣ 量比分析:")
        vol = signals.get('volume_ratio', {})
        print(f"   - 量比: {vol.get('value', 1):.2f}x")
        print(f"   - 信号: {vol.get('signal', 'N/A')}")
        if vol.get('value', 1) > 2.0:
            print(f"   🔊 成交量显著放大,关注资金动向")
        elif vol.get('value', 1) < 0.5:
            print(f"   🔉 成交量萎缩,上涨/下跌动能不足")

        print(f"\n3️⃣ 均线系统:")
        ma = signals.get('ma', {})
        print(f"   - MA20: {ma.get('ma20', 0):.2f} (乖离率: {ma.get('deviation_20', 0):+.2f}%)")
        print(f"   - MA60: {ma.get('ma60', 0):.2f} (乖离率: {ma.get('deviation_60', 0):+.2f}%)")
        print(f"   - 趋势: {ma.get('signal', 'N/A')}")
        if ma.get('signal') == '多头排列':
            print(f"   ✅ 价格>MA20>MA60,多头趋势")
        elif ma.get('signal') == '空头排列':
            print(f"   ⚠️ 价格<MA20<MA60,空头趋势")

        print(f"\n4️⃣ ATR 止损止盈:")
        atr = signals.get('atr', {})
        current_price = signals.get('latest_price', 0)
        print(f"   - ATR值: {atr.get('value', 0):.4f}")
        print(f"   - 当前价格: {current_price:.2f}")
        print(f"   - 建议止损: {atr.get('stop_loss', 0):.2f} ({((atr.get('stop_loss', 0) - current_price) / current_price * 100):+.2f}%)")
        print(f"   - 建议止盈: {atr.get('take_profit', 0):.2f} ({((atr.get('take_profit', 0) - current_price) / current_price * 100):+.2f}%)")
        print(f"   - 风险收益比: {atr.get('risk_reward', 'N/A')}")

        print(f"\n5️⃣ VWAP (成交量加权平均价):")
        vwap = signals.get('vwap', {})
        print(f"   - VWAP: {vwap.get('value', 0):.2f}")
        print(f"   - 价格偏离: {vwap.get('diff_pct', 0):+.2f}%")
        print(f"   - 信号: {vwap.get('signal', 'N/A')}")
        if current_price > vwap.get('value', 0):
            print(f"   ✅ 价格>VWAP,资金推动强势")
        else:
            print(f"   ⚠️ 价格<VWAP,资金支撑较弱")

        print(f"\n6️⃣ 量价背离检测:")
        vp_div = signals.get('volume_price_divergence', {})
        if vp_div.get('has_divergence'):
            if vp_div.get('top_divergence'):
                print(f"   ⚠️ 检测到量价顶背离:")
                print(f"      价格上涨但成交量下降")
                print(f"      上涨动能不足,警惕回调风险")
            if vp_div.get('bottom_divergence'):
                print(f"   ✅ 检测到量价底背离:")
                print(f"      价格下跌但成交量放大")
                print(f"      可能是恐慌性抛售,关注反弹机会")
        else:
            print(f"   ➡️ 未检测到显著量价背离")

        # 5. 综合判断
        print(f"\n{'='*80}")
        print("🎯 综合判断:")
        print(f"{'='*80}")

        bullish_signals = 0
        bearish_signals = 0

        # RSI
        if rsi.get('value', 50) < 30:
            bullish_signals += 1
        elif rsi.get('value', 50) > 70:
            bearish_signals += 1

        # 均线
        if ma.get('signal') == '多头排列':
            bullish_signals += 1
        elif ma.get('signal') == '空头排列':
            bearish_signals += 1

        # VWAP
        if current_price > vwap.get('value', 0):
            bullish_signals += 1
        else:
            bearish_signals += 1

        # 量价背离
        if vp_div.get('top_divergence'):
            bearish_signals += 1
        elif vp_div.get('bottom_divergence'):
            bullish_signals += 1

        print(f"\n看多信号: {bullish_signals} 个 ✅")
        print(f"看空信号: {bearish_signals} 个 ⚠️")

        if bullish_signals > bearish_signals:
            print(f"\n💡 结论: 技术面偏多,可以考虑逢低买入")
            print(f"   建议止损: {atr.get('stop_loss', 0):.2f}")
        elif bearish_signals > bullish_signals:
            print(f"\n💡 结论: 技术面偏空,建议谨慎或减仓")
            print(f"   如持有,建议止盈: {atr.get('take_profit', 0):.2f}")
        else:
            print(f"\n💡 结论: 技术面中性,等待更明确信号")

        print(f"\n{'='*80}\n")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 增强型技术指标测试程序")
    print("="*80)

    # 测试标的列表 (使用akshare的指数代码格式)
    test_targets = [
        ('sh000001', '上证指数'),
        ('sz399006', '创业板指'),
        ('sz399300', '沪深300'),
    ]

    for symbol, name in test_targets:
        test_enhanced_indicators(symbol, name)

    print("\n" + "="*80)
    print("✅ 测试完成!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
