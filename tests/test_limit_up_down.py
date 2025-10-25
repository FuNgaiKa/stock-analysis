#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试涨跌停数据统计

验证：
1. 涨跌停统计是否准确
2. ST股是否正确识别
3. 数据是否符合同花顺统计
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from russ_trading_strategy.market_depth_analyzer import MarketDepthAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_limit_up_down():
    """测试涨跌停统计"""
    print("=" * 70)
    print("  测试涨跌停数据统计")
    print("=" * 70)
    print()

    # 创建分析器
    analyzer = MarketDepthAnalyzer()

    # 测试市场情绪分析
    print("【测试】获取市场情绪数据...")
    print("-" * 70)

    result = analyzer.analyze_market_sentiment()

    print()
    print(f"涨停家数: {result['limit_up']} 只")
    print(f"跌停家数: {result['limit_down']} 只")
    print(f"上涨家数: {result['advance']} 只")
    print(f"下跌家数: {result['decline']} 只")
    print(f"涨跌比: {result['advance_decline_ratio']:.2f}:1")
    print()
    print(f"情绪评分: {result['sentiment_score']} 分")
    print(f"情绪等级: {result['sentiment_level']}")
    print(f"综合判断: {result['analysis']}")
    print()

    print("=" * 70)
    print("✅ 测试完成")
    print("=" * 70)
    print()
    print("💡 对比同花顺数据：")
    print("   - 涨停 71 只 vs 实际统计 {} 只".format(result['limit_up']))
    print("   - 跌停 10 只 vs 实际统计 {} 只".format(result['limit_down']))
    print()


if __name__ == '__main__':
    try:
        test_limit_up_down()
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)
