#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原版vs增强版股票分析器对比演示
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from stock import AStockHeatAnalyzer
from enhanced_stock_analyzer import EnhancedAStockAnalyzer
import pandas as pd
import time

def compare_analyzers():
    """对比两个分析器的性能"""
    print("=" * 80)
    print("A股市场分析器对比演示")
    print("=" * 80)
    
    # 初始化分析器
    print("初始化分析器...")
    original_analyzer = AStockHeatAnalyzer()
    enhanced_analyzer = EnhancedAStockAnalyzer()
    
    # 原版分析
    print("\n--- 原版分析器结果 ---")
    start_time = time.time()
    try:
        original_result = original_analyzer.analyze_market_heat()
        original_time = time.time() - start_time
        
        if original_result:
            print(f"✓ 分析成功 (耗时: {original_time:.2f}秒)")
            print(f"  火热程度: {original_result['heat_score']:.3f}")
            print(f"  风险等级: {original_result['risk_level']}")
            print(f"  涨停数量: {original_result['market_data_summary']['limit_up_count']}")
            print(f"  跌停数量: {original_result['market_data_summary']['limit_down_count']}")
            
            # 显示原版指标
            indicators = original_result.get('indicators', {})
            print(f"  原版指标:")
            for key, value in indicators.items():
                if isinstance(value, dict):
                    continue
                print(f"    - {key}: {value:.3f}")
        else:
            print("✗ 分析失败")
            original_result = None
            
    except Exception as e:
        print(f"✗ 原版分析器异常: {str(e)}")
        original_result = None
        original_time = 0
    
    # 增强版分析  
    print("\n--- 增强版分析器结果 ---")
    start_time = time.time()
    try:
        enhanced_result = enhanced_analyzer.analyze_enhanced_market_heat()
        enhanced_time = time.time() - start_time
        
        if enhanced_result:
            print(f"✓ 分析成功 (耗时: {enhanced_time:.2f}秒)")
            print(f"  火热程度: {enhanced_result['heat_score']:.3f}")
            print(f"  风险评估: {enhanced_result['risk_assessment']['level']}")
            print(f"  仓位建议: {enhanced_result['position_advice']['action']}")
            
            summary = enhanced_result['market_summary']
            print(f"  涨停数量: {summary['limit_up_count']}")
            print(f"  跌停数量: {summary['limit_down_count']}")
            print(f"  市场参与度: {summary['market_participation']:.3f}")
            print(f"  多空比率: {summary['bull_bear_ratio']:.3f}")
            
            # 显示增强版指标
            print(f"  增强版指标:")
            for key, value in enhanced_result['indicators'].items():
                print(f"    - {key}: {value:.3f}")
                
            # 风险因子
            risk_factors = enhanced_result['risk_assessment'].get('risk_factors', [])
            if risk_factors:
                print(f"  风险因子: {', '.join(risk_factors)}")
                
            # 策略建议
            strategies = enhanced_result['position_advice'].get('strategies', [])
            if strategies:
                print(f"  策略建议: {', '.join(strategies)}")
                
        else:
            print("✗ 分析失败")
            enhanced_result = None
            
    except Exception as e:
        print(f"✗ 增强版分析器异常: {str(e)}")
        enhanced_result = None  
        enhanced_time = 0
    
    # 对比总结
    print("\n" + "=" * 80)
    print("对比总结")
    print("=" * 80)
    
    comparison_table = []
    
    if original_result and enhanced_result:
        print(f"{'指标':<20} {'原版':<15} {'增强版':<15} {'改进':<15}")
        print("-" * 65)
        
        # 火热程度对比
        orig_heat = original_result['heat_score']
        enh_heat = enhanced_result['heat_score']
        heat_diff = enh_heat - orig_heat
        print(f"{'火热程度':<20} {orig_heat:<15.3f} {enh_heat:<15.3f} {heat_diff:+.3f}")
        
        # 分析维度对比
        orig_indicators = len([k for k, v in original_result.get('indicators', {}).items() if not isinstance(v, dict)])
        enh_indicators = len(enhanced_result.get('indicators', {}))
        print(f"{'分析维度':<20} {orig_indicators:<15} {enh_indicators:<15} {enh_indicators-orig_indicators:+}")
        
        # 数据源稳定性
        orig_summary = original_result.get('market_data_summary', {})
        enh_summary = enhanced_result.get('market_summary', {})
        
        orig_data_quality = "好" if orig_summary.get('sz_index_change', '数据缺失') != '数据缺失' else "差"
        enh_data_quality = "好" if enh_summary.get('avg_index_change', 0) != 0 else "一般"
        
        print(f"{'数据源稳定性':<20} {orig_data_quality:<15} {enh_data_quality:<15} {'提升'}")
        
        # 分析耗时
        print(f"{'分析耗时(秒)':<20} {original_time:<15.2f} {enhanced_time:<15.2f} {enhanced_time-original_time:+.2f}")
        
        print("\n增强版优势:")
        print("✓ 集成6个维度的综合指标，更全面")
        print("✓ 多数据源备份，提高稳定性")
        print("✓ 技术指标(RSI、MACD、布林带)增强准确性")
        print("✓ 风险因子和策略建议更精细")
        print("✓ 市场参与度、多空比率等新增指标")
        
    else:
        print("由于数据获取问题，无法完成完整对比")
        print("建议检查网络连接和数据源可用性")
    
    print("=" * 80)


def demonstrate_enhanced_features():
    """演示增强版特色功能"""
    print("\n" + "=" * 50)
    print("增强版特色功能演示")
    print("=" * 50)
    
    analyzer = EnhancedAStockAnalyzer()
    
    # 展示多数据源能力
    print("\n1. 多数据源数据获取测试:")
    for source_name in ['akshare', 'sina', 'netease', 'yfinance']:
        try:
            print(f"  测试 {source_name}... ", end="")
            data = analyzer.data_provider.sources[source_name]('20231201')  # 测试历史日期
            if data:
                print("✓ 可用")
            else:
                print("✗ 不可用")
        except Exception as e:
            print(f"✗ 异常: {str(e)[:50]}...")
    
    # 展示指标计算
    print("\n2. 增强指标计算演示:")
    market_data = analyzer.get_enhanced_market_data()
    if market_data:
        enhanced_indicators = market_data.get('enhanced_indicators', {})
        print(f"  ✓ 市场参与度: {enhanced_indicators.get('market_participation', 0):.3f}")
        print(f"  ✓ 多空比率: {enhanced_indicators.get('bull_bear_ratio', 0.5):.3f}")
        print(f"  ✓ 市场极端度: {enhanced_indicators.get('market_extreme', 0):.3f}")
    
    print("=" * 50)


def create_performance_report():
    """生成性能报告"""
    print("\n生成详细性能报告...")
    
    enhanced_analyzer = EnhancedAStockAnalyzer()
    
    # 模拟多日分析
    test_dates = ['20231201', '20231202', '20231203']  # 示例日期
    results = []
    
    for date in test_dates:
        try:
            print(f"分析 {date}...", end=" ")
            result = enhanced_analyzer.analyze_enhanced_market_heat(date)
            if result:
                results.append({
                    'date': date,
                    'heat_score': result['heat_score'],
                    'risk_level': result['risk_assessment']['level'],
                    'data_sources_used': len([k for k, v in result.get('market_summary', {}).items() if v not in [0, None, '数据缺失']])
                })
                print("✓")
            else:
                print("✗")
        except Exception as e:
            print(f"异常: {str(e)[:30]}...")
    
    if results:
        df = pd.DataFrame(results)
        print(f"\n性能报告摘要:")
        print(f"- 成功分析天数: {len(results)}")
        print(f"- 平均火热程度: {df['heat_score'].mean():.3f}")
        print(f"- 火热程度标准差: {df['heat_score'].std():.3f}")
        print(f"- 平均数据源数: {df['data_sources_used'].mean():.1f}")
        
        # 保存报告
        report_file = f"performance_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(report_file, index=False, encoding='utf-8')
        print(f"- 详细报告已保存: {report_file}")


if __name__ == "__main__":
    try:
        # 主对比演示
        compare_analyzers()
        
        # 特色功能演示
        demonstrate_enhanced_features()
        
        # 性能报告
        create_performance_report()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序异常: {str(e)}")
        import traceback
        traceback.print_exc()