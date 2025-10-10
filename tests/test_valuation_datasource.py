#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 AKShare 估值数据源可用性
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import sys
import io

# 修复 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_individual_stock_valuation():
    """测试个股估值数据"""
    print("\n=== 1. 测试个股估值（理想数据源） ===")

    # 1.1 测试百度股市通个股估值
    try:
        print("\n1.1 百度股市通个股估值 (stock_zh_valuation_baidu)")
        df = ak.stock_zh_valuation_baidu(symbol="000858", indicator="市盈率", period="近一年")
        print(f"[OK] 成功获取 {len(df)} 条数据")
        print(f"列名: {df.columns.tolist()}")
        print(df.head(3))
        print(f"\n当前市盈率: {df['value'].iloc[-1]}")
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

    # 1.2 测试东方财富个股估值对比
    try:
        print("\n1.2 东方财富个股估值对比 (stock_zh_valuation_comparison_em)")
        df = ak.stock_zh_valuation_comparison_em(symbol="000858")
        print(f"[OK] 成功获取 {len(df)} 条数据")
        print(f"列名: {df.columns.tolist()}")
        print(df.head(3))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")


def test_industry_valuation():
    """测试行业估值数据"""
    print("\n=== 2. 测试行业估值 ===")

    # 2.1 行业PE数据（理杏仁）
    try:
        print("\n2.1 行业市盈率 (stock_index_pe_lg)")
        df = ak.stock_index_pe_lg(symbol="银行")
        print(f"[OK] 成功获取 {len(df)} 条数据")
        print(f"列名: {df.columns.tolist()}")
        print(df.tail(3))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

    # 2.2 行业PB数据
    try:
        print("\n2.2 行业市净率 (stock_index_pb_lg)")
        df = ak.stock_index_pb_lg(symbol="银行")
        print(f"[OK] 成功获取 {len(df)} 条数据")
        print(f"列名: {df.columns.tolist()}")
        print(df.tail(3))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

    # 2.3 市场整体PE
    try:
        print("\n2.3 市场整体市盈率 (stock_market_pe_lg)")
        df = ak.stock_market_pe_lg(symbol="上证")
        print(f"[OK] 成功获取 {len(df)} 条数据")
        print(f"列名: {df.columns.tolist()}")
        print(df.tail(3))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

    # 2.4 行业列表
    try:
        print("\n2.4 行业列表 (stock_board_industry_name_em)")
        df = ak.stock_board_industry_name_em()
        print(f"✅ 成功获取 {len(df)} 个行业")
        print(f"列名: {df.columns.tolist()}")
        print(df.head(10))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

    # 2.5 申万行业PE
    try:
        print("\n2.5 申万行业市盈率 (stock_industry_pe_ratio_cninfo)")
        df = ak.stock_industry_pe_ratio_cninfo(symbol="801780", start_date="20240101")
        print(f"[OK] 成功获取 {len(df)} 条数据")
        print(f"列名: {df.columns.tolist()}")
        print(df.tail(3))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")


def test_historical_valuation():
    """测试历史估值时序数据"""
    print("\n=== 3. 测试历史估值时序数据 ===")

    # 3.1 个股历史估值（百度）
    try:
        print("\n3.1 个股历史估值时序 (stock_zh_valuation_baidu - 近三年)")
        df = ak.stock_zh_valuation_baidu(symbol="000858", indicator="市盈率", period="近三年")
        print(f"[OK] 成功获取 {len(df)} 条数据")
        print(f"列名: {df.columns.tolist()}")
        print(df.head(3))
        print(f"日期范围: {df['date'].min()} 到 {df['date'].max()}")

        # 计算分位数
        current_pe = df['value'].iloc[-1]
        percentile = (df['value'] < current_pe).sum() / len(df)
        print(f"\n当前PE: {current_pe:.2f}")
        print(f"近三年分位数: {percentile:.1%}")
    except Exception as e:
        print(f"[FAIL] 失败: {e}")


def test_index_valuation():
    """测试指数估值"""
    print("\n=== 4. 测试指数估值 ===")

    # 4.1 已知：A股整体PE/PB（现有代码使用）
    try:
        print("\n4.1 A股整体PE (stock_a_ttm_lyr)")
        df = ak.stock_a_ttm_lyr()
        print(f"[OK] 成功获取 {len(df)} 条数据")
        print(f"列名: {df.columns.tolist()}")
        print(df.tail(1))
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

    # 4.2 上证指数历史PE
    try:
        print("\n4.2 上证指数历史PE (stock_market_pe_lg)")
        df = ak.stock_market_pe_lg(symbol="上证")
        print(f"[OK] 成功获取 {len(df)} 条数据")
        print(f"列名: {df.columns.tolist()}")
        print(df.tail(3))

        # 计算当前分位数
        current_pe = df['pe'].iloc[-1]
        percentile = (df['pe'] < current_pe).sum() / len(df)
        print(f"\n当前PE: {current_pe:.2f}")
        print(f"全历史分位数: {percentile:.1%}")
    except Exception as e:
        print(f"[FAIL] 失败: {e}")


if __name__ == '__main__':
    print("=" * 70)
    print("测试 AKShare 估值数据源")
    print("=" * 70)

    test_individual_stock_valuation()
    test_industry_valuation()
    test_historical_valuation()
    test_index_valuation()

    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
