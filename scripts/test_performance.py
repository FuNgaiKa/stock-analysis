#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本
测试优化前后的性能差异
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from russ_trading.runners.run_unified_analysis import UnifiedAnalysisRunner
from russ_trading.utils.data_cache_manager import get_cache_manager


def test_parallel_vs_serial():
    """测试并发vs串行性能"""
    print("=" * 80)
    print("性能对比测试: 并发 vs 串行")
    print("=" * 80)

    # 测试资产(选择前5个避免时间太长)
    test_assets = ['CYBZ', 'KECHUANG50', 'HKTECH', 'NASDAQ', 'HS300']

    # 1. 串行执行
    print("\n【测试1】串行执行模式...")
    runner_serial = UnifiedAnalysisRunner(enable_parallel=False)
    start = time.time()
    results_serial = runner_serial.analyze_assets(test_assets)
    time_serial = time.time() - start
    print(f"✓ 串行执行完成: {time_serial:.2f}秒")
    print(f"  成功: {len([r for r in results_serial['assets'].values() if 'error' not in r])}/{len(test_assets)}")

    # 清理缓存,确保公平对比
    cache = get_cache_manager()
    cache.clear_memory_cache()
    print("  缓存已清理")

    # 2. 并发执行
    print("\n【测试2】并发执行模式(6线程)...")
    runner_parallel = UnifiedAnalysisRunner(enable_parallel=True, max_workers=6)
    start = time.time()
    results_parallel = runner_parallel.analyze_assets(test_assets)
    time_parallel = time.time() - start
    print(f"✓ 并发执行完成: {time_parallel:.2f}秒")
    print(f"  成功: {len([r for r in results_parallel['assets'].values() if 'error' not in r])}/{len(test_assets)}")

    # 3. 性能对比
    print("\n" + "=" * 80)
    print("性能对比结果:")
    print("=" * 80)
    print(f"串行执行: {time_serial:.2f}秒")
    print(f"并发执行: {time_parallel:.2f}秒")
    speedup = time_serial / time_parallel if time_parallel > 0 else 0
    print(f"性能提升: {speedup:.2f}倍 ({(speedup-1)*100:.1f}%)")
    print("=" * 80)


def test_cache_effectiveness():
    """测试缓存效果"""
    print("\n\n" + "=" * 80)
    print("缓存效果测试")
    print("=" * 80)

    test_assets = ['CYBZ', 'KECHUANG50', 'HKTECH']
    runner = UnifiedAnalysisRunner(enable_parallel=True, max_workers=6)

    # 1. 第一次运行(无缓存)
    print("\n【测试1】首次运行(冷启动)...")
    cache = get_cache_manager()
    cache.clear_memory_cache()
    cache.clear_file_cache(days_to_keep=0)

    start = time.time()
    results1 = runner.analyze_assets(test_assets)
    time_cold = time.time() - start
    print(f"✓ 首次运行完成: {time_cold:.2f}秒")

    # 2. 第二次运行(有缓存)
    print("\n【测试2】第二次运行(缓存命中)...")
    start = time.time()
    results2 = runner.analyze_assets(test_assets)
    time_hot = time.time() - start
    print(f"✓ 第二次运行完成: {time_hot:.2f}秒")

    # 3. 缓存统计
    stats = cache.get_cache_stats()
    print("\n缓存统计:")
    print(f"  内存缓存: {stats['memory_cache_size']} 项")
    print(f"  文件缓存: {stats.get('file_cache_count', 0)} 文件")
    print(f"  缓存大小: {stats.get('file_cache_size_mb', 0)} MB")

    # 4. 性能对比
    print("\n" + "=" * 80)
    print("缓存效果:")
    print("=" * 80)
    print(f"首次运行: {time_cold:.2f}秒")
    print(f"缓存运行: {time_hot:.2f}秒")
    speedup = time_cold / time_hot if time_hot > 0 else 0
    print(f"缓存提升: {speedup:.2f}倍 ({(1-time_hot/time_cold)*100:.1f}% 时间节省)")
    print("=" * 80)


if __name__ == '__main__':
    try:
        # 测试1: 并发vs串行
        test_parallel_vs_serial()

        # 测试2: 缓存效果
        test_cache_effectiveness()

        print("\n\n✅ 所有性能测试完成!")

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
