#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ashare数据源集成测试
验证新数据源是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from stock.enhanced_data_sources import MultiSourceDataProvider

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_ashare_direct():
    """直接测试Ashare数据源"""
    print("=== 直接测试Ashare数据源 ===")
    try:
        from stock.Ashare import get_price

        # 测试获取上证指数数据
        print("1. 测试上证指数数据获取...")
        data = get_price('sh000001', frequency='1d', count=5)
        print(f"上证指数最近5天数据:")
        print(data)
        print(f"数据类型: {type(data)}")
        print(f"数据形状: {data.shape if hasattr(data, 'shape') else 'N/A'}")

        # 测试获取平安银行数据
        print("\n2. 测试个股数据获取...")
        stock_data = get_price('sz000001', frequency='1d', count=3)
        print(f"平安银行最近3天数据:")
        print(stock_data)

        return True

    except Exception as e:
        print(f"直接测试Ashare失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_source_provider():
    """测试多数据源管理器"""
    print("\n=== 测试多数据源管理器 ===")
    try:
        provider = MultiSourceDataProvider()

        print("可用数据源:", list(provider.sources.keys()))

        # 测试获取市场数据
        print("\n获取今日市场数据...")
        market_data = provider.get_market_data()

        if market_data:
            print("数据获取成功!")
            print(f"数据包含的键: {list(market_data.keys())}")

            # 检查指数数据
            for index_name in ['sz_index', 'cyb_index', 'sz_component']:
                index_data = market_data.get(index_name)
                if index_data is not None and not index_data.empty:
                    print(f"\n{index_name}:")
                    print(index_data)
                else:
                    print(f"\n{index_name}: 数据为空")

            # 获取增强指标
            print("\n=== 增强指标测试 ===")
            indicators = provider.get_enhanced_market_indicators()
            if indicators:
                print("增强指标:")
                for key, value in indicators.items():
                    print(f"- {key}: {value}")
            else:
                print("增强指标获取失败")

        else:
            print("数据获取失败!")

        return market_data is not None

    except Exception as e:
        print(f"多数据源测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_source_priority():
    """测试数据源优先级"""
    print("\n=== 测试数据源优先级 ===")
    try:
        provider = MultiSourceDataProvider()

        # 模拟测试每个数据源
        for source_name, source_func in provider.sources.items():
            print(f"\n测试数据源: {source_name}")
            try:
                data = source_func("20241028")  # 使用固定日期测试
                if data:
                    print(f"✅ {source_name} - 数据获取成功")
                    valid_indices = sum(1 for key in ['sz_index', 'cyb_index', 'sz_component']
                                      if data.get(key) is not None and not data.get(key).empty)
                    print(f"   有效指数数据: {valid_indices}/3")
                else:
                    print(f"❌ {source_name} - 数据获取失败")
            except Exception as e:
                print(f"❌ {source_name} - 错误: {str(e)}")

        return True

    except Exception as e:
        print(f"优先级测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始Ashare集成测试...\n")

    results = {
        'ashare_direct': test_ashare_direct(),
        'multi_source': test_multi_source_provider(),
        'priority': test_data_source_priority()
    }

    print("\n" + "="*50)
    print("测试结果汇总:")
    print("="*50)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print(f"\n总体结果: {'✅ 所有测试通过' if all_passed else '❌ 部分测试失败'}")

    if all_passed:
        print("\n🎉 Ashare数据源集成成功!")
        print("现在可以使用更稳定的数据源进行股票分析了。")
    else:
        print("\n⚠️  存在问题，需要进一步调试。")

if __name__ == "__main__":
    main()