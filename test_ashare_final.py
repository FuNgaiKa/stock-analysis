#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化Ashare数据源测试 - 避免编码问题
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
    print("Ashare导入成功")
except ImportError as e:
    print(f"Ashare导入失败: {e}")
    ashare_available = False

def test_ashare_basic():
    """基础Ashare功能测试"""
    print("\n=== Ashare基础功能测试 ===")

    if not ashare_available:
        print("FAIL: Ashare不可用")
        return False

    try:
        # 测试1: 获取上证指数数据
        print("1. 测试上证指数数据获取...")
        data = get_price('sh000001', frequency='1d', count=3)

        if data is not None and not data.empty:
            print("PASS: 上证指数数据获取成功")
            print(f"数据形状: {data.shape}")
            print(f"列名: {list(data.columns)}")
            print("最新数据:")
            print(data.tail(1))

            # 检查必要的列
            required_cols = ['open', 'close', 'high', 'low', 'volume']
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                print(f"WARN: 缺少列: {missing_cols}")
            else:
                print("PASS: 数据结构完整")
        else:
            print("FAIL: 上证指数数据获取失败")
            return False

        # 测试2: 获取深证成指数据
        print("\n2. 测试深证成指数据获取...")
        data2 = get_price('sz399001', frequency='1d', count=2)

        if data2 is not None and not data2.empty:
            print("PASS: 深证成指数据获取成功")
            print(f"最新收盘价: {data2['close'].iloc[-1]}")
        else:
            print("FAIL: 深证成指数据获取失败")

        # 测试3: 获取个股数据
        print("\n3. 测试个股数据获取...")
        data3 = get_price('sz000001', frequency='1d', count=2)

        if data3 is not None and not data3.empty:
            print("PASS: 平安银行数据获取成功")
            print(f"最新收盘价: {data3['close'].iloc[-1]}")
        else:
            print("WARN: 平安银行数据获取失败（可能是非交易时间）")

        return True

    except Exception as e:
        print(f"FAIL: Ashare测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_processing():
    """测试数据处理功能"""
    print("\n=== 数据处理测试 ===")

    if not ashare_available:
        print("FAIL: Ashare不可用")
        return False

    try:
        # 获取数据并进行处理
        data = get_price('sh000001', frequency='1d', count=10)

        if data is None or data.empty:
            print("FAIL: 无法获取测试数据")
            return False

        # 计算涨跌幅
        data['change_pct'] = data['close'].pct_change() * 100

        # 计算简单移动平均
        data['ma5'] = data['close'].rolling(window=5).mean()

        print("PASS: 数据处理测试成功")
        print(f"处理后数据形状: {data.shape}")
        print("最新数据（包含计算指标）:")
        print(data.tail(3)[['close', 'change_pct', 'ma5']])

        return True

    except Exception as e:
        print(f"FAIL: 数据处理测试失败: {e}")
        return False

def test_multiple_symbols():
    """测试多个股票代码"""
    print("\n=== 多代码测试 ===")

    if not ashare_available:
        print("FAIL: Ashare不可用")
        return False

    symbols = [
        ('sh000001', '上证指数'),
        ('sz399006', '创业板指'),
        ('sz399001', '深证成指')
    ]

    results = []

    for code, name in symbols:
        try:
            data = get_price(code, frequency='1d', count=3)
            if data is not None and not data.empty:
                latest_price = data['close'].iloc[-1]
                results.append({
                    'code': code,
                    'name': name,
                    'price': latest_price,
                    'status': 'SUCCESS'
                })
                print(f"PASS: {name} ({code}): {latest_price:.2f}")
            else:
                results.append({
                    'code': code,
                    'name': name,
                    'status': 'FAIL'
                })
                print(f"FAIL: {name} ({code}): 无数据")
        except Exception as e:
            results.append({
                'code': code,
                'name': name,
                'status': 'ERROR',
                'error': str(e)
            })
            print(f"ERROR: {name} ({code}): {e}")

    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    print(f"\n多代码测试结果: {success_count}/{len(symbols)} 成功")

    return success_count >= 2  # 至少2个成功算通过

def main():
    """主测试函数"""
    print("开始Ashare简化集成测试...")

    # 功能测试
    tests = [
        ('basic', test_ashare_basic),
        ('processing', test_data_processing),
        ('multiple', test_multiple_symbols)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"ERROR: 测试 {test_name} 异常: {e}")
            results[test_name] = False

    print("\n" + "="*50)
    print("测试结果汇总:")
    print("="*50)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    partial_passed = any(results.values())

    print(f"\n总体结果: ", end="")
    if all_passed:
        print("PASS - 所有测试通过")
        print("\nSUCCESS: Ashare数据源基础功能正常!")
        print("可以进行下一步的完整集成。")
    elif partial_passed:
        print("PARTIAL - 部分测试通过")
        print("\nWARN: 部分功能正常，可能存在网络或配置问题。")
    else:
        print("FAIL - 所有测试失败")
        print("\nERROR: 需要检查网络连接或Ashare配置。")

    return all_passed

if __name__ == "__main__":
    main()