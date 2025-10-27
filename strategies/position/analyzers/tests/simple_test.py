#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单测试背离分析器"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from divergence_analyzer import DivergenceAnalyzer, normalize_dataframe_columns
from src.data_sources.us_stock_source import USStockDataSource

print("=" * 60)
print("背离分析器快速测试")
print("=" * 60)

# 获取标普500数据
print("\n[1] 获取标普500数据...")
source = USStockDataSource()
df = source.get_us_index_daily('SPX', period='6mo')
df = normalize_dataframe_columns(df)

print(f"    数据条数: {len(df)}")
print(f"    日期范围: {df.index[0].date()} 至 {df.index[-1].date()}")
print(f"    最新价格: {df['close'].iloc[-1]:.2f}")

# 创建分析器
print("\n[2] 初始化分析器...")
analyzer = DivergenceAnalyzer()

# 综合分析
print("\n[3] 执行综合背离分析...")
result = analyzer.comprehensive_analysis(df, symbol='S&P 500', market='US')

print(f"\n[4] 分析结果:")
print(f"    发现背离: {result['has_any_divergence']}")

if result['has_any_divergence']:
    print(f"    背离信号数: {len(result['summary'])}")
    for i, signal in enumerate(result['summary'], 1):
        print(f"\n    信号 {i}:")
        print(f"      类型: {signal['type']} - {signal['direction']}")
        print(f"      强度: {signal['strength']}/100")
        print(f"      置信度: {signal['confidence']}")
        print(f"      描述: {signal['description']}")

    if 'overall_assessment' in result:
        ass = result['overall_assessment']
        print(f"\n    综合评估: {ass['signal']}")
        print(f"    建议: {ass['advice']}")
else:
    print(f"    评估: {result['overall_assessment']['advice']}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
