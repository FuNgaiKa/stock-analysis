#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIX分析运行包装器 - 解决编码问题
"""
import sys
import io

# 设置UTF-8编码输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入并运行VIX分析
from china_vix_equivalent import ChinaVolatilityIndex, get_limit_up_down_ratio

if __name__ == '__main__':
    print("=" * 100)
    print("A股VIX等价指标分析")
    print("=" * 100)

    # 1. 创建计算器
    calculator = ChinaVolatilityIndex()

    # 2. 分析当前波动率
    print("\n【1. 当前市场波动率分析】")
    print("-" * 100)

    stats = calculator.analyze_current_volatility()

    print(f"\n日期: {stats['date']}")
    print(f"上证指数: {stats['close']:.2f}")
    print(f"\n波动率指标:")
    print(f"  20日历史波动率 (HV): {stats['hv_20']:.2f}%")
    print(f"  60日历史波动率 (HV): {stats['hv_60']:.2f}%")
    print(f"  Parkinson波动率: {stats['parkinson_vol']:.2f}%")
    print(f"  ATR波动率: {stats['atr_pct']:.2f}%")
    print(f"\n>>> [综合VIX]: {stats['composite_vix']:.2f}%")
    print(f">>> VIX分位数 (1年): {stats['vix_percentile']:.1%}")
    print(f">>> 波动率等级: {stats['vix_level']}")
    print(f"\n>>> 杠杆建议: {stats['leverage_advice']}")

    # 3. 涨跌停情绪指标
    print("\n【2. 市场情绪指标 (涨跌停家数)】")
    print("-" * 100)

    limit_stats = get_limit_up_down_ratio()
    if limit_stats:
        print(f"\n涨停股票: {limit_stats['limit_up_count']} ({limit_stats['limit_up_ratio']:.2%})")
        print(f"跌停股票: {limit_stats['limit_down_count']} ({limit_stats['limit_down_ratio']:.2%})")
        print(f"市场情绪: {limit_stats['sentiment']}")

    # 4. 解读
    print("\n【3. 综合解读】")
    print("-" * 100)

    vix = stats['composite_vix']
    percentile = stats['vix_percentile']

    print(f"\n当前综合VIX为 {vix:.2f}%, 处于历史 {percentile:.0%} 分位")

    if vix < 15:
        print("\n✅ 市场波动率极低,处于平静期")
        print("   - 这是使用杠杆的相对安全时期")
        print("   - 但需要警惕: 低波动后可能迎来高波动")
        print("   - 建议: 可考虑1.2-1.5倍杠杆,但要有止损")
    elif vix < 20:
        print("\n✓ 市场波动率正常,属于常规状态")
        print("   - 可以适度使用杠杆")
        print("   - 建议: 1.2倍以内杠杆")
    elif vix < 30:
        print("\n⚠ 市场波动率偏高,需要谨慎")
        print("   - 不建议使用杠杆")
        print("   - 建议: 降低仓位,观望为主")
    else:
        print("\n🚨 市场波动率极高,处于恐慌状态")
        print("   - 严禁使用杠杆")
        print("   - 建议: 大幅降低仓位或清仓观望")

    if percentile > 0.8:
        print(f"\n⚠ 注意: 当前VIX处于过去1年的高位 ({percentile:.0%}分位)")
        print("   历史上看,高波动率后可能继续保持或突然回落")
    elif percentile < 0.2:
        print(f"\n💡 提示: 当前VIX处于过去1年的低位 ({percentile:.0%}分位)")
        print("   历史上看,极低波动率后可能迎来波动率上升")

    # 5. VIX参考标准
    print("\n【4. VIX参考标准】")
    print("-" * 100)
    print("""
波动率水平       VIX范围      市场状态          杠杆建议
------------------------------------------------------------
极低波动         < 15%        市场平静          可考虑1.5-2倍
低波动          15-20%       正常市场          可考虑1.2-1.5倍
中等波动        20-30%       谨慎观望          建议1倍(无杠杆)
高波动          30-40%       市场恐慌          禁止杠杆
极端波动         > 40%        危机状态          禁止杠杆

注: A股由于涨跌停限制,波动率通常低于美股
    """)

    print("\n" + "=" * 100)
    print("分析完成!")
    print("=" * 100)
