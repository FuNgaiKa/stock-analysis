"""
斜率分析测试脚本
分析纳指、标普、恒指的斜率状态，验证"美股过热、港股修复"假设
"""
from strategies.position.analyzers.technical_analysis.slope_analyzer import SlopeAnalyzer, compare_slopes
import pandas as pd
from datetime import datetime


def detailed_analysis(symbol: str, name: str):
    """详细分析单个指数"""
    print(f"\n{'=' * 100}")
    print(f"{name} ({symbol}) - 详细斜率分析")
    print(f"{'=' * 100}")

    analyzer = SlopeAnalyzer(symbol)
    result = analyzer.comprehensive_analysis()

    if 'error' in result:
        print(f"❌ 分析失败: {result['error']}")
        return None

    # 基本信息
    print(f"\n📊 基本信息:")
    print(f"  分析日期: {result['analysis_date']}")
    print(f"  数据点数: {result['data_points']} 个交易日")
    print(f"  当前价格: {result['current_price']:.2f}")

    # 斜率指标
    print(f"\n📈 斜率指标:")
    print(f"  60日年化收益率: {result['slope_60d']['annual_return']:>8.2f}%  (R²={result['slope_60d']['r_squared']:.3f})")
    print(f"  120日年化收益率: {result['slope_120d']['annual_return']:>7.2f}%  (R²={result['slope_120d']['r_squared']:.3f})")

    # 波动率
    print(f"\n📊 斜率波动性:")
    print(f"  标准差: {result['volatility']['slope_std']:.6f}")
    print(f"  变异系数: {result['volatility']['slope_cv']:.3f}")
    print(f"  百分位数: {result['volatility']['percentile']:.1f}% (历史排名)")

    # 相对均线
    print(f"\n📉 相对200日均线:")
    print(f"  偏离程度: {result['ma_relative']['deviation_pct']:>7.2f}%")
    print(f"  偏离等级: {result['ma_relative']['deviation_level']}")
    print(f"  位置: {'均线上方 ✅' if result['ma_relative']['is_above_ma'] else '均线下方 ⚠️'}")

    # Z-Score
    print(f"\n🎯 Z-Score (均值回归):")
    print(f"  Z值: {result['zscore']['value']:>7.2f}")
    print(f"  等级: {result['zscore']['level']}")
    print(f"  信号: {result['zscore']['signal']}")

    # 加速度
    print(f"\n⚡ 趋势加速度:")
    print(f"  加速度: {result['acceleration']['value']:.6f}")
    print(f"  状态: {'加速中 🔥' if result['acceleration']['is_accelerating'] else '减速中 ❄️'}")
    print(f"  等级: {result['acceleration']['level']}")

    # 综合评估
    print(f"\n{'=' * 100}")
    print(f"💡 综合评估:")
    print(f"  风险评分: {result['risk_score']:.1f}/100")
    print(f"  风险等级: {result['risk_level']}")
    print(f"  操作建议: {result['recommendation']}")
    print(f"{'=' * 100}")

    return result


def cross_market_comparison():
    """跨市场对比分析"""
    print(f"\n{'=' * 100}")
    print("🌍 美股 vs 港股 - 斜率对比分析")
    print(f"{'=' * 100}")

    symbols = {
        '^IXIC': '纳斯达克综合指数',
        '^GSPC': '标普500指数',
        '^DJI': '道琼斯工业指数',
        '^HSI': '恒生指数'
    }

    results = {}
    for symbol, name in symbols.items():
        results[symbol] = detailed_analysis(symbol, name)

    # 生成对比表格
    print(f"\n{'=' * 100}")
    print("📊 核心指标对比表")
    print(f"{'=' * 100}")

    comparison_df = compare_slopes(list(symbols.keys()))
    print(comparison_df.to_string(index=False))

    # 假设验证
    print(f"\n{'=' * 100}")
    print("🔬 假设验证: '美股斜率过高、港股处于修复期'")
    print(f"{'=' * 100}")

    if results.get('^IXIC') and results.get('^HSI'):
        nasdaq = results['^IXIC']
        hsi = results['^HSI']

        print(f"\n1️⃣ 斜率对比:")
        print(f"  纳斯达克60日年化: {nasdaq['slope_60d']['annual_return']:.2f}%")
        print(f"  恒生指数60日年化: {hsi['slope_60d']['annual_return']:.2f}%")
        print(f"  差异: {nasdaq['slope_60d']['annual_return'] - hsi['slope_60d']['annual_return']:.2f}%")

        print(f"\n2️⃣ Z-Score对比 (过热/超卖判断):")
        print(f"  纳斯达克Z-Score: {nasdaq['zscore']['value']:.2f} - {nasdaq['zscore']['level']}")
        print(f"  恒生指数Z-Score: {hsi['zscore']['value']:.2f} - {hsi['zscore']['level']}")

        print(f"\n3️⃣ 风险评分对比:")
        print(f"  纳斯达克: {nasdaq['risk_score']:.1f}/100 ({nasdaq['risk_level']})")
        print(f"  恒生指数: {hsi['risk_score']:.1f}/100 ({hsi['risk_level']})")

        print(f"\n4️⃣ 相对均线偏离:")
        print(f"  纳斯达克: {nasdaq['ma_relative']['deviation_pct']:.2f}% ({nasdaq['ma_relative']['deviation_level']})")
        print(f"  恒生指数: {hsi['ma_relative']['deviation_pct']:.2f}% ({hsi['ma_relative']['deviation_level']})")

        # 结论
        print(f"\n{'=' * 100}")
        print("📌 分析结论:")
        print(f"{'=' * 100}")

        # 判断1: 美股是否过热
        nasdaq_overheated = (
            nasdaq['slope_60d']['annual_return'] > 25 or
            nasdaq['zscore']['value'] > 1.5 or
            nasdaq['risk_score'] > 70
        )

        # 判断2: 港股是否在修复
        hsi_recovering = (
            hsi['slope_60d']['annual_return'] > 0 and
            hsi['zscore']['value'] < 0 and
            hsi['ma_relative']['deviation_pct'] < 0
        )

        print(f"\n✅ 美股状态判断:")
        if nasdaq_overheated:
            print(f"  ⚠️  确实存在过热迹象!")
            print(f"     - 60日年化收益率: {nasdaq['slope_60d']['annual_return']:.2f}% (偏高)")
            print(f"     - Z-Score: {nasdaq['zscore']['value']:.2f} ({nasdaq['zscore']['level']})")
            print(f"     - 风险评分: {nasdaq['risk_score']:.1f} ({nasdaq['risk_level']})")
        else:
            print(f"  ✅ 未发现明显过热")

        print(f"\n✅ 港股状态判断:")
        if hsi_recovering:
            print(f"  ✅ 确实处于修复期!")
            print(f"     - 60日年化收益率: {hsi['slope_60d']['annual_return']:.2f}% (温和上涨)")
            print(f"     - Z-Score: {hsi['zscore']['value']:.2f} (未超买)")
            print(f"     - 相对均线: {hsi['ma_relative']['deviation_pct']:.2f}% (低位修复)")
        else:
            print(f"  ⚠️  不完全符合修复期特征")

        print(f"\n💡 操作策略建议:")
        print(f"  美股: {nasdaq['recommendation']}")
        print(f"  港股: {hsi['recommendation']}")

    print(f"\n{'=' * 100}\n")


def generate_report():
    """生成完整报告"""
    print("=" * 100)
    print(f"📋 斜率分析完整报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

    cross_market_comparison()

    print("\n✅ 分析完成!")
    print("=" * 100)


if __name__ == '__main__':
    generate_report()
