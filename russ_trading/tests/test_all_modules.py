#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有新模块
Test All New Modules

快速验证所有新功能是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("Testing All New Modules")
print("=" * 80)

# 测试1: 配置加载
print("\n✅ 测试1: 配置加载器")
try:
    from russ_trading.utils.config_loader import get_risk_profile, get_benchmarks
    config = get_risk_profile('aggressive')
    benchmarks = get_benchmarks()
    print(f"   - 风险配置加载成功: {config['name']}")
    print(f"   - 基准点位加载成功: 沪深300={benchmarks['hs300']}")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# 测试2: 日志系统
print("\n✅ 测试2: 日志系统")
try:
    from russ_trading.utils.logger import setup_logger
    logger = setup_logger('test', log_to_file=False)
    logger.info("测试日志")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# 测试3: 缓存系统
print("\n✅ 测试3: 缓存系统")
try:
    from russ_trading.utils.cache_manager import SimpleCache
    cache = SimpleCache()
    cache.set('test_key', 'test_value', ttl=60)
    value = cache.get('test_key')
    assert value == 'test_value', "缓存值不匹配"
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# 测试4: 量化分析
print("\n✅ 测试4: 量化分析器")
try:
    from russ_trading.core.quant_analyzer import QuantAnalyzer
    import pandas as pd
    import numpy as np

    analyzer = QuantAnalyzer()
    returns = pd.Series(np.random.normal(0.001, 0.02, 252))
    sharpe = analyzer.calculate_sharpe_ratio(returns)
    print(f"   - 夏普比率: {sharpe:.2f}")

    positions = [
        {'asset_name': '恒生科技ETF', 'position_ratio': 0.28},
        {'asset_name': '证券ETF', 'position_ratio': 0.23},
    ]
    exposure = analyzer.analyze_factor_exposure(positions)
    print(f"   - 成长因子暴露: {exposure['growth']:.2f}")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# 测试5: 压力测试
print("\n✅ 测试5: 压力测试器")
try:
    from russ_trading.core.stress_tester import StressTester

    tester = StressTester()
    positions = [
        {'asset_name': '恒生科技ETF', 'position_ratio': 0.28, 'current_value': 144200},
    ]
    result = tester.run_stress_test(positions, 500000)
    print(f"   - 测试场景数: {len(result['tests'])}")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# 测试6: 情景分析
print("\n✅ 测试6: 情景分析器")
try:
    from russ_trading.core.scenario_analyzer import ScenarioAnalyzer

    analyzer = ScenarioAnalyzer()
    positions = [
        {'asset_name': '恒生科技ETF', 'position_ratio': 0.28},
    ]
    result = analyzer.analyze_scenarios(positions, 500000)
    print(f"   - 期望收益: {result['expected_return']*100:.1f}%")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# 测试7: 归因分析
print("\n✅ 测试7: 归因分析器")
try:
    from russ_trading.core.attribution_analyzer import AttributionAnalyzer

    analyzer = AttributionAnalyzer()
    health_result = {
        'health_score': 45.0,
        'checks': {
            'total_position': {'passed': False, 'penalty': 15.0, 'message': '仓位超标'},
        }
    }
    attribution = analyzer.analyze_health_attribution(health_result)
    print(f"   - 扣分项数: {len(attribution['deductions'])}")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# 测试8: 执行摘要
print("\n✅ 测试8: 执行摘要生成器")
try:
    from russ_trading.core.executive_summary import ExecutiveSummaryGenerator

    generator = ExecutiveSummaryGenerator()
    health_result = {'health_score': 45.0, 'health_level': 'danger'}
    action_items = {'priority_1': [], 'checklist': []}
    summary = generator.generate_summary(health_result, action_items)
    assert len(summary) > 0, "执行摘要为空"
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# 测试9: 图表生成
print("\n✅ 测试9: 图表生成器")
try:
    from russ_trading.core.chart_generator import ChartGenerator

    generator = ChartGenerator()
    positions = [
        {'asset_name': '恒生科技ETF', 'position_ratio': 0.28},
        {'asset_name': '证券ETF', 'position_ratio': 0.23},
    ]
    chart = generator.generate_position_bar_chart(positions)
    assert len(chart) > 0, "图表为空"
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

print("\n" + "=" * 80)
print("All Tests Completed!")
print("=" * 80)
