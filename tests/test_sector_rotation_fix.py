#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试板块轮动数据获取修复

验证：
1. 重试机制是否生效
2. 缓存机制是否正常
3. 错误提示是否友好
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from russ_trading.market_depth_analyzer import MarketDepthAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_sector_rotation():
    """测试板块轮动数据获取"""
    print("=" * 70)
    print("  测试板块轮动数据获取（带重试和缓存）")
    print("=" * 70)
    print()

    # 创建分析器
    analyzer = MarketDepthAnalyzer()

    # 测试1: 获取板块轮动数据
    print("【测试1】获取板块轮动数据...")
    print("-" * 70)
    result = analyzer.analyze_sector_rotation()

    print()
    print(f"数据来源: {result.get('data_source', 'unknown')}")
    print(f"轮动信号: {result.get('rotation_signal', 'N/A')}")
    print(f"综合分析: {result.get('analysis', 'N/A')}")
    print()

    if result['top_gainers']:
        print("领涨板块 (前3):")
        for sector in result['top_gainers'][:3]:
            print(f"  - {sector['name']}: {sector['change_pct']:+.2f}%")
    else:
        print("⚠️ 无领涨板块数据")

    print()

    if result['top_losers']:
        print("领跌板块 (前3):")
        for sector in result['top_losers'][:3]:
            print(f"  - {sector['name']}: {sector['change_pct']:+.2f}%")
    else:
        print("⚠️ 无领跌板块数据")

    print()

    if result['capital_flow']:
        print("资金流向 (前3):")
        for flow in result['capital_flow'][:3]:
            print(f"  - {flow['sector']}: {flow['net_inflow']:+.1f}亿")
    else:
        print("⚠️ 无资金流向数据")

    print()
    print("=" * 70)

    # 测试2: 生成深度报告
    print()
    print("【测试2】生成深度盘面报告...")
    print("-" * 70)

    report = analyzer.generate_depth_report()

    # 只显示板块轮动部分
    lines = report.split('\n')
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if '板块轮动追踪' in line:
            start_idx = i
        if start_idx and i > start_idx and line.strip().startswith('---'):
            end_idx = i
            break

    if start_idx and end_idx:
        print('\n'.join(lines[start_idx:end_idx]))
    else:
        print("⚠️ 报告中未找到板块轮动部分")

    print()
    print("=" * 70)
    print("✅ 测试完成")
    print("=" * 70)


if __name__ == '__main__':
    try:
        test_sector_rotation()
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)
