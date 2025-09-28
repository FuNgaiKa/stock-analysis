#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新的akshare测试文件，使用重新整理后的目录结构
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_sources.akshare_optimized import AkshareOptimized
from stock.stock import MarketHeatAnalyzer

def test_new_structure():
    """测试新的目录结构"""
    print("=== 测试新目录结构 ===")

    try:
        # 测试数据源
        akshare_source = AkshareOptimized()
        print("✓ AkshareOptimized 导入成功")

        # 测试市场分析器
        analyzer = MarketHeatAnalyzer()
        print("✓ MarketHeatAnalyzer 导入成功")

        # 简单的功能测试
        heat_score = analyzer.analyze_market_heat()
        print(f"✓ 市场火热度分析完成，得分: {heat_score}")

    except Exception as e:
        print(f"✗ 测试失败: {e}")

if __name__ == "__main__":
    test_new_structure()