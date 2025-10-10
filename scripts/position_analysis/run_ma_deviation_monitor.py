#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
均线偏离度监控脚本
运行方式: python scripts/position_analysis/run_ma_deviation_monitor.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from position_analysis.ma_deviation_monitor import MADeviationMonitor
import logging

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 只显示警告和错误
    format='%(levelname)s: %(message)s'
)


def main():
    """主函数"""
    print("=" * 70)
    print("🔍 均线偏离度监控系统")
    print("=" * 70)
    print("监控范围:")
    print("  A股: 上证指数、沪深300、创业板指、科创50、深证成指")
    print("       中小板指、上证50、中证500、中证1000")
    print("  港股: 恒生指数、恒生科技")
    print("=" * 70)

    monitor = MADeviationMonitor()

    # 监控所有指数
    print("\n正在监控各指数偏离度...")
    all_alerts = monitor.monitor_all_indices()

    # 生成并打印报告
    report = monitor.generate_alert_report(all_alerts)
    print("\n" + report)

    # 如果有预警，分析历史表现
    if all_alerts:
        print("\n" + "=" * 70)
        print("📈 历史偏离事件分析")
        print("=" * 70)

        analyzed_count = 0
        for index_code in all_alerts.keys():
            if analyzed_count >= 3:  # 只详细分析前3个
                break

            print(f"\n【{monitor.INDICES[index_code]['name']}】")

            try:
                # 获取历史偏离事件
                events = monitor.get_historical_deviation_events(
                    index_code,
                    ma_period=60,
                    threshold=30.0,
                    lookback_days=1000
                )

                if not events.empty:
                    print(f"  近1000天内偏离60日均线>30%事件: {len(events)} 次")
                    if len(events) > 0:
                        print(f"  最近一次: {events.index[-1].strftime('%Y-%m-%d')}")

                # 分析后续表现
                performance = monitor.analyze_post_deviation_performance(
                    index_code,
                    ma_period=60,
                    threshold=30.0
                )

                if performance and performance.get('upward_events_count', 0) > 0:
                    print(f"\n  📊 向上偏离>30%后的历史表现 (样本: {performance['upward_events_count']} 次):")
                    for period, stats in performance['upward_performance'].items():
                        print(
                            f"    {period:>3}: 平均收益{stats['mean_return']:+6.2f}%, "
                            f"上涨概率{stats['positive_ratio']:5.1%}, "
                            f"样本数{stats['sample_size']}"
                        )

                if performance and performance.get('downward_events_count', 0) > 0:
                    print(f"\n  📊 向下偏离>30%后的历史表现 (样本: {performance['downward_events_count']} 次):")
                    for period, stats in performance['downward_performance'].items():
                        print(
                            f"    {period:>3}: 平均收益{stats['mean_return']:+6.2f}%, "
                            f"上涨概率{stats['positive_ratio']:5.1%}, "
                            f"样本数{stats['sample_size']}"
                        )

                analyzed_count += 1

            except Exception as e:
                print(f"  分析失败: {str(e)}")
                continue

    print("\n" + "=" * 70)
    print("✅ 监控完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
