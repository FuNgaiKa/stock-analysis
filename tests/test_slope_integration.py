"""
测试斜率维度集成到 Phase 3 市场状态检测系统
"""
from position_analysis.core.market_state_detector import MarketStateDetector
from position_analysis.analyzers.technical_analysis.slope_analyzer import SlopeAnalyzer
import pandas as pd


def test_slope_integration():
    """测试斜率维度集成"""
    print("=" * 100)
    print("斜率维度集成测试 - Phase 3 系统")
    print("=" * 100)

    # 1. 创建斜率分析器获取纳斯达克指数斜率指标
    print("\n1. 获取纳斯达克斜率指标...")
    slope_analyzer = SlopeAnalyzer('^IXIC')
    slope_analysis = slope_analyzer.comprehensive_analysis()

    if 'error' in slope_analysis:
        print(f"❌ 斜率分析失败: {slope_analysis['error']}")
        return

    # 提取斜率指标
    slope_metrics = {
        'annual_return_60d': slope_analysis['slope_60d']['annual_return'],
        'annual_return_120d': slope_analysis['slope_120d']['annual_return'],
        'zscore': slope_analysis['zscore']['value'],
        'risk_score': slope_analysis['risk_score'],
        'is_accelerating': slope_analysis['acceleration']['is_accelerating']
    }

    print(f"  60日年化收益率: {slope_metrics['annual_return_60d']:.2f}%")
    print(f"  120日年化收益率: {slope_metrics['annual_return_120d']:.2f}%")
    print(f"  Z-Score: {slope_metrics['zscore']:.2f}")
    print(f"  风险评分: {slope_metrics['risk_score']:.1f}/100")
    print(f"  加速状态: {'加速中' if slope_metrics['is_accelerating'] else '减速中'}")

    # 2. 创建市场状态检测器
    print("\n2. 初始化市场状态检测器...")
    detector = MarketStateDetector()
    print(f"  ✅ 13维度权重配置: {detector.dimension_weights}")
    print(f"  ✅ 斜率维度权重: {detector.dimension_weights['slope']}")

    # 3. 测试单独的斜率评分方法
    print("\n3. 测试斜率评分方法...")
    slope_score = detector._score_slope(slope_metrics)
    print(f"  斜率维度得分: {slope_score:.3f}")

    # 解读得分
    if slope_score > 0.5:
        interpretation = "✅ 趋势强劲且健康"
    elif slope_score > 0:
        interpretation = "➡️ 趋势温和向上"
    elif slope_score > -0.5:
        interpretation = "⚠️ 趋势中性或略弱"
    else:
        interpretation = "❌ 趋势下行或过热"

    print(f"  得分解读: {interpretation}")

    # 4. 模拟完整的市场状态检测（简化版，只传斜率）
    print("\n4. 模拟市场状态检测...")

    # 创建模拟数据 (实际应用中这些数据来自真实数据源)
    mock_ma_metrics = {'ma_arrangement': '多头排列', 'trend_strength': 7}
    mock_price_data = pd.DataFrame({
        'close': [100 * (1 + 0.001 * i) for i in range(60)]
    })
    mock_valuation = {'pe_percentile_10y': 0.4, 'pb_percentile_10y': 0.45}
    mock_capital_flow = {'cumulative_5d': 50, 'cumulative_20d': 200}
    mock_sentiment = {'limit_up_count': 20, 'limit_down_count': 5}
    mock_breadth = {'up_ratio': 0.65}
    mock_margin = {'margin_balance_pct_change': 0.01}
    mock_main_fund = {'today_main_inflow': 30, 'cumulative_5d': 120}
    mock_lhb = {'institution_buy_count': 5, 'institution_sell_count': 2, 'institution_net_buy': 10}
    mock_volatility = {'volatility_percentile': 0.3}
    mock_volume = {'volume_ratio': 1.2, 'volume_percentile': 0.55}
    mock_technical = {'macd_signal': '金叉', 'rsi_signal': '中性', 'rsi': 55}

    # 调用检测方法
    result = detector.detect_market_state(
        ma_metrics=mock_ma_metrics,
        price_data=mock_price_data,
        valuation_metrics=mock_valuation,
        capital_flow_metrics=mock_capital_flow,
        sentiment_metrics=mock_sentiment,
        breadth_metrics=mock_breadth,
        margin_metrics=mock_margin,
        main_fund_metrics=mock_main_fund,
        lhb_metrics=mock_lhb,
        volatility_metrics=mock_volatility,
        volume_metrics=mock_volume,
        technical_metrics=mock_technical,
        slope_metrics=slope_metrics  # 🔥 添加斜率维度
    )

    # 5. 输出完整结果
    print("\n" + "=" * 100)
    print("📊 市场状态诊断结果 (含斜率维度)")
    print("=" * 100)

    print(f"\n🎯 市场状态: {result['state']}")
    print(f"   状态描述: {result['state_description']}")
    print(f"   置信度: {result['confidence']:.1%}")
    print(f"   综合评分: {result['overall_score']:.3f}")

    print(f"\n📈 13维度评分明细:")
    dimension_names = {
        'trend': '趋势',
        'price_change': '涨跌幅',
        'valuation': '估值',
        'capital_flow': '北向资金',
        'sentiment': '情绪',
        'breadth': '市场宽度',
        'leverage': '融资融券',
        'main_fund': '主力资金',
        'institution': '机构行为',
        'volatility': '波动率',
        'volume': '成交量',
        'technical': '技术形态',
        'slope': '趋势斜率'  # 🔥 新增
    }

    for dim_key, dim_name in dimension_names.items():
        if dim_key in result['dimension_scores']:
            score = result['dimension_scores'][dim_key]
            weight = detector.dimension_weights[dim_key]
            contribution = score * weight
            print(f"  {dim_name:8s}: {score:>6.3f} (权重 {weight:.0%}) → 贡献 {contribution:>6.3f}")

    print(f"\n✅ 关键信号:")
    for signal in result['key_signals']:
        print(f"  - {signal}")

    if result['risk_alerts']:
        print(f"\n⚠️ 风险警告:")
        for alert in result['risk_alerts']:
            print(f"  - {alert}")

    # 6. 仓位建议
    print(f"\n💡 操作建议:")
    position_rec = detector.get_position_recommendation(
        result['state'],
        result['overall_score'],
        result['confidence']
    )
    print(f"  建议仓位: {position_rec['position_center']:.0%} ({position_rec['position_min']:.0%}-{position_rec['position_max']:.0%})")
    print(f"  策略: {position_rec['strategy']}")
    print(f"  行动: {position_rec['action']}")

    print("\n" + "=" * 100)
    print("✅ 斜率维度集成测试完成！")
    print("=" * 100)


if __name__ == '__main__':
    test_slope_integration()
