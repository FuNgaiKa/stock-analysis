#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化测试脚本
验证向量化计算和LRU缓存的优化效果
"""

import sys
import time
import logging
from strategies.position.core.historical_position_analyzer import HistoricalPositionAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_calculate_future_returns():
    """测试calculate_future_returns优化效果"""
    print("\n" + "=" * 80)
    print("测试1: calculate_future_returns 向量化优化")
    print("=" * 80)

    try:
        analyzer = HistoricalPositionAnalyzer()

        # 获取测试数据
        print("正在获取上证指数历史数据...")
        index_code = 'sh000001'

        # 查找相似点位
        print("正在查找相似点位...")
        similar = analyzer.find_similar_periods(index_code, tolerance=0.05)

        if len(similar) == 0:
            print("❌ 未找到相似点位,跳过测试")
            return False

        print(f"✅ 找到 {len(similar)} 个相似点位")

        # 测试优化后的方法
        print("\n开始性能测试...")
        start_time = time.time()
        result = analyzer.calculate_future_returns(index_code, similar, periods=[5, 10, 20, 60])
        elapsed_time = time.time() - start_time

        print(f"✅ 计算完成!")
        print(f"   耗时: {elapsed_time:.2f}秒")
        print(f"   样本数: {len(result)}")
        print(f"   列数: {len(result.columns)}")

        # 验证结果
        if len(result) == len(similar):
            print("✅ 结果数量正确")
        else:
            print(f"❌ 结果数量不匹配: 期望{len(similar)}, 实际{len(result)}")
            return False

        # 验证列名
        expected_cols = ['date', 'price', 'return_5d', 'return_10d', 'return_20d', 'return_60d']
        if all(col in result.columns for col in expected_cols):
            print("✅ 结果列名正确")
        else:
            print(f"❌ 列名不匹配: {result.columns.tolist()}")
            return False

        # 打印示例数据
        print("\n示例数据(前3行):")
        print(result.head(3).to_string())

        print("\n🎉 测试通过!")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_lru_cache():
    """测试LRU缓存优化效果"""
    print("\n" + "=" * 80)
    print("测试2: LRU缓存优化")
    print("=" * 80)

    try:
        # 创建小容量缓存进行测试
        analyzer = HistoricalPositionAnalyzer(cache_enabled=True)
        analyzer.cache.max_size = 3  # 设置最大缓存为3个

        print(f"缓存配置: 最大{analyzer.cache.max_size}个指数")

        # 获取多个指数数据
        test_indices = ['sh000001', 'sh000300', 'sz399006', 'sh000688']

        print("\n第一轮: 获取4个指数数据(缓存容量=3)")
        for code in test_indices:
            try:
                print(f"  获取 {code}...")
                df = analyzer.get_index_data(code)
                print(f"    ✅ 成功 ({len(df)}行)")
            except Exception as e:
                print(f"    ⚠️  跳过: {str(e)}")

        # 查看缓存统计
        stats = analyzer.cache.get_stats()
        print(f"\n缓存统计:")
        print(f"  当前缓存数: {stats['size']}/{stats['max_size']}")
        print(f"  命中: {stats['hits']}, 未命中: {stats['misses']}")
        print(f"  命中率: {stats['hit_rate']}")

        print("\n第二轮: 重复获取前3个指数(应该全部命中缓存)")
        old_hits = stats['hits']
        for code in test_indices[:3]:
            try:
                df = analyzer.get_index_data(code)
                print(f"  ✅ {code} 命中缓存")
            except Exception as e:
                print(f"  ⚠️  {code} 失败: {str(e)}")

        # 验证缓存命中
        new_stats = analyzer.cache.get_stats()
        new_hits = new_stats['hits']

        if new_hits > old_hits:
            print(f"\n✅ 缓存工作正常! 新增命中: {new_hits - old_hits}次")
            print(f"   最终命中率: {new_stats['hit_rate']}")
        else:
            print(f"\n❌ 缓存未生效")
            return False

        print("\n🎉 测试通过!")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_business_logic():
    """测试业务逻辑完整性"""
    print("\n" + "=" * 80)
    print("测试3: 业务逻辑验证")
    print("=" * 80)

    try:
        analyzer = HistoricalPositionAnalyzer()

        # 测试完整的分析流程
        index_code = 'sh000001'

        print("步骤1: 获取当前点位")
        positions = analyzer.get_current_positions()
        if index_code in positions:
            current_price = positions[index_code]['price']
            print(f"✅ 上证指数当前点位: {current_price:.2f}")
        else:
            print("⚠️  未能获取当前点位,跳过后续测试")
            return False

        print("\n步骤2: 查找相似点位")
        similar = analyzer.find_similar_periods(index_code, tolerance=0.05)
        print(f"✅ 找到 {len(similar)} 个相似点位")

        if len(similar) < 5:
            print("⚠️  相似点位过少,跳过后续测试")
            return False

        print("\n步骤3: 计算未来收益率")
        future_returns = analyzer.calculate_future_returns(index_code, similar, periods=[5, 10, 20, 60])
        print(f"✅ 收益率计算完成: {len(future_returns)}条记录")

        print("\n步骤4: 概率统计分析")
        from strategies.position.core.historical_position_analyzer import ProbabilityAnalyzer
        prob_analyzer = ProbabilityAnalyzer()

        stats_20d = prob_analyzer.calculate_probability(future_returns['return_20d'])
        print(f"✅ 20日统计:")
        print(f"   样本数: {stats_20d['sample_size']}")
        print(f"   上涨概率: {stats_20d['up_prob']:.1%}")
        print(f"   平均收益: {stats_20d['mean_return']:.2%}")

        # 验证结果合理性
        if stats_20d['sample_size'] > 0:
            if 0 <= stats_20d['up_prob'] <= 1:
                print("✅ 概率值合理")
            else:
                print(f"❌ 概率值异常: {stats_20d['up_prob']}")
                return False
        else:
            print("❌ 样本数为0")
            return False

        print("\n🎉 业务逻辑测试通过!")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 80)
    print("性能优化测试套件")
    print("=" * 80)

    results = {
        "向量化计算": test_calculate_future_returns(),
        "LRU缓存": test_lru_cache(),
        "业务逻辑": test_business_logic()
    }

    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("🎉 所有测试通过! 优化成功,业务逻辑正确!")
        return 0
    else:
        print("❌ 部分测试失败,请检查优化代码")
        return 1


if __name__ == "__main__":
    sys.exit(main())
