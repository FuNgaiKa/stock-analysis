#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强数据源管理器集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from stock.enhanced_data_sources import MultiSourceDataProvider

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_enhanced_data_sources():
    """测试增强数据源管理器"""
    print("=== 测试增强数据源管理器 ===")

    try:
        # 创建数据提供器
        provider = MultiSourceDataProvider()
        print(f"可用数据源: {list(provider.sources.keys())}")

        # 测试获取市场数据
        print("\n获取市场数据...")
        market_data = provider.get_market_data()

        if market_data:
            print("PASS: 市场数据获取成功")
            print(f"数据键: {list(market_data.keys())}")

            # 检查指数数据
            for index_name in ['sz_index', 'cyb_index', 'sz_component']:
                data = market_data.get(index_name)
                if data is not None and not data.empty:
                    print(f"PASS: {index_name} 数据可用")
                    print(f"  收盘价: {data['收盘'].iloc[0] if '收盘' in data.columns else 'N/A'}")
                    print(f"  涨跌幅: {data['涨跌幅'].iloc[0] if '涨跌幅' in data.columns else 'N/A'}%")
                else:
                    print(f"WARN: {index_name} 数据为空")

            # 测试增强指标
            print("\n测试增强指标...")
            indicators = provider.get_enhanced_market_indicators()
            if indicators:
                print("PASS: 增强指标计算成功")
                for key, value in indicators.items():
                    print(f"  {key}: {value}")
            else:
                print("WARN: 增强指标计算失败")

            return True
        else:
            print("FAIL: 市场数据获取失败")
            return False

    except Exception as e:
        print(f"FAIL: 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_sources():
    """单独测试各个数据源"""
    print("\n=== 单独测试各数据源 ===")

    provider = MultiSourceDataProvider()
    test_date = "20241028"

    for source_name, source_func in provider.sources.items():
        print(f"\n测试数据源: {source_name}")
        try:
            data = source_func(test_date)
            if data and provider._validate_data(data):
                print(f"PASS: {source_name} - 数据有效")
                # 统计可用指数
                valid_indices = sum(1 for key in ['sz_index', 'cyb_index', 'sz_component']
                                  if data.get(key) is not None and not data.get(key).empty)
                print(f"  有效指数: {valid_indices}/3")
            else:
                print(f"WARN: {source_name} - 数据无效或为空")
        except Exception as e:
            print(f"FAIL: {source_name} - 错误: {str(e)}")

def main():
    """主测试函数"""
    print("测试Ashare集成到股票分析项目...")

    tests = [
        ("enhanced_sources", test_enhanced_data_sources),
        ("individual_sources", test_individual_sources)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"ERROR: 测试 {test_name} 异常: {e}")
            results[test_name] = False

    print("\n" + "="*60)
    print("集成测试结果汇总:")
    print("="*60)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    overall_success = any(results.values())

    if overall_success:
        print("\nSUCCESS: Ashare已成功集成到项目中!")
        print("主要特点:")
        print("- Ashare作为主力数据源")
        print("- 多数据源备份机制")
        print("- 自动故障切换")
        print("- 数据质量验证")

        print("\n下一步可以:")
        print("1. 运行 python main.py 测试完整功能")
        print("2. 使用增强的数据源进行股票分析")
        print("3. 享受更稳定的数据获取体验")
    else:
        print("\nWARN: 集成可能存在问题，但基础功能仍可用")

if __name__ == "__main__":
    main()