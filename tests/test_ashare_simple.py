#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化Ashare数据源测试
仅测试核心功能，避免复杂依赖
"""

import sys
import os
import json
import requests
import pandas as pd

# 直接导入Ashare
sys.path.append(os.path.join(os.path.dirname(__file__), 'stock'))
try:
    from Ashare import get_price
    ashare_available = True
except ImportError as e:
    print(f"Ashare导入失败: {e}")
    ashare_available = False

def test_ashare_basic():
    """基础Ashare功能测试"""
    print("=== Ashare基础功能测试 ===")

    if not ashare_available:
        print("❌ Ashare不可用")
        return False

    try:
        # 测试1: 获取上证指数数据
        print("1. 测试上证指数数据获取...")
        data = get_price('sh000001', frequency='1d', count=3)

        if data is not None and not data.empty:
            print("OK 上证指数数据获取成功")
            print(f"数据形状: {data.shape}")
            print(f"列名: {list(data.columns)}")
            print("最新数据:")
            print(data.tail(1))

            # 检查必要的列
            required_cols = ['open', 'close', 'high', 'low', 'volume']
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                print(f"WARNING 缺少列: {missing_cols}")
            else:
                print("OK 数据结构完整")
        else:
            print("❌ 上证指数数据获取失败")
            return False

        # 测试2: 获取深证成指数据
        print("\n2. 测试深证成指数据获取...")
        data2 = get_price('sz399001', frequency='1d', count=2)

        if data2 is not None and not data2.empty:
            print("✅ 深证成指数据获取成功")
            print(f"最新收盘价: {data2['close'].iloc[-1]}")
        else:
            print("❌ 深证成指数据获取失败")

        # 测试3: 获取个股数据
        print("\n3. 测试个股数据获取...")
        data3 = get_price('sz000001', frequency='1d', count=2)

        if data3 is not None and not data3.empty:
            print("✅ 平安银行数据获取成功")
            print(f"最新收盘价: {data3['close'].iloc[-1]}")
        else:
            print("⚠️  平安银行数据获取失败（可能是非交易时间）")

        return True

    except Exception as e:
        print(f"❌ Ashare测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ashare_in_class():
    """测试在类中使用Ashare"""
    print("\n=== 类集成测试 ===")

    if not ashare_available:
        print("❌ Ashare不可用")
        return False

    try:
        class SimpleDataProvider:
            def __init__(self):
                self.cache = {}

            def get_index_data(self, code, name):
                """获取指数数据"""
                try:
                    data = get_price(code, frequency='1d', count=5)
                    if data is not None and not data.empty:
                        latest_price = data['close'].iloc[-1]
                        prev_price = data['close'].iloc[-2] if len(data) > 1 else latest_price
                        change_pct = (latest_price - prev_price) / prev_price * 100

                        return {
                            'name': name,
                            'price': latest_price,
                            'change_pct': change_pct,
                            'volume': data['volume'].iloc[-1]
                        }
                    return None
                except Exception as e:
                    print(f"获取{name}数据失败: {e}")
                    return None

        # 测试类功能
        provider = SimpleDataProvider()

        indices = [
            ('sh000001', '上证指数'),
            ('sz399006', '创业板指'),
            ('sz399001', '深证成指')
        ]

        results = []
        for code, name in indices:
            result = provider.get_index_data(code, name)
            if result:
                results.append(result)
                print(f"✅ {name}: {result['price']:.2f} ({result['change_pct']:+.2f}%)")
            else:
                print(f"❌ {name}: 数据获取失败")

        if len(results) >= 2:
            print("✅ 类集成测试成功")
            return True
        else:
            print("❌ 类集成测试失败，获取数据太少")
            return False

    except Exception as e:
        print(f"❌ 类集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_network_connectivity():
    """测试网络连接"""
    print("\n=== 网络连接测试 ===")

    test_urls = [
        'http://web.ifzq.gtimg.cn',
        'http://money.finance.sina.com.cn'
    ]

    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {url} - 连接正常")
            else:
                print(f"⚠️  {url} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - 连接失败: {e}")

def main():
    """主测试函数"""
    print("开始Ashare简化集成测试...\n")

    # 网络连接测试
    test_network_connectivity()

    # 功能测试
    results = {
        'basic': test_ashare_basic(),
        'class_integration': test_ashare_in_class()
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
        print("\n🎉 Ashare数据源基础功能正常!")
        print("可以进行下一步的完整集成。")
    else:
        print("\n⚠️  存在问题，需要检查网络或代码。")

if __name__ == "__main__":
    main()