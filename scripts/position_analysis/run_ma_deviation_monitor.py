#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
均线偏离度监控脚本
运行方式:
  python scripts/position_analysis/run_ma_deviation_monitor.py           # 控制台输出
  python scripts/position_analysis/run_ma_deviation_monitor.py --email   # 发送邮件
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from position_analysis.monitoring.ma_deviation_monitor import MADeviationMonitor
from position_analysis.reporting.email_notifier import EmailNotifier
import logging
import argparse
import time
from datetime import datetime


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_monitor_with_retry(max_retries=3):
    """
    运行监控,失败自动重试

    Args:
        max_retries: 最大重试次数

    Returns:
        (all_alerts, report) 或 (None, None) 如果失败
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"开始监控 (第 {attempt + 1}/{max_retries} 次尝试)")

            monitor = MADeviationMonitor()

            # 监控所有指数
            all_alerts = monitor.monitor_all_indices()

            # 生成报告
            report = monitor.generate_alert_report(all_alerts)

            logger.info("监控成功完成")
            return all_alerts, report, monitor

        except Exception as e:
            logger.error(f"监控失败 (第 {attempt + 1}/{max_retries} 次): {str(e)}")

            if attempt < max_retries - 1:
                wait_seconds = (attempt + 1) * 30  # 递增等待时间: 30s, 60s, 90s
                logger.info(f"等待 {wait_seconds} 秒后重试...")
                time.sleep(wait_seconds)
            else:
                logger.error("达到最大重试次数,监控失败")
                return None, None, None

    return None, None, None


def print_console_report(all_alerts, report, monitor):
    """控制台输出报告"""
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


def send_email_report(all_alerts, report, monitor):
    """发送邮件报告"""
    try:
        notifier = EmailNotifier()

        if all_alerts:
            # 生成完整报告（包含历史分析）
            full_report = report + "\n"

            # 添加历史偏离分析
            full_report += "\n" + "=" * 70 + "\n"
            full_report += "📈 历史偏离事件回测分析\n"
            full_report += "=" * 70 + "\n"

            analyzed_count = 0
            for index_code in all_alerts.keys():
                if analyzed_count >= 3:  # 只分析前3个
                    break

                full_report += f"\n【{monitor.INDICES[index_code]['name']}】\n"

                try:
                    # 获取历史偏离事件
                    events = monitor.get_historical_deviation_events(
                        index_code,
                        ma_period=60,
                        threshold=30.0,
                        lookback_days=1000
                    )

                    if not events.empty:
                        full_report += f"  近1000天内偏离60日均线>30%事件: {len(events)} 次\n"
                        if len(events) > 0:
                            full_report += f"  最近一次: {events.index[-1].strftime('%Y-%m-%d')}\n"

                    # 分析后续表现
                    performance = monitor.analyze_post_deviation_performance(
                        index_code,
                        ma_period=60,
                        threshold=30.0
                    )

                    if performance and performance.get('upward_events_count', 0) > 0:
                        full_report += f"\n  📊 向上偏离>30%后的历史表现 (样本: {performance['upward_events_count']} 次):\n"
                        for period, stats in performance['upward_performance'].items():
                            full_report += (
                                f"    {period:>3}: 平均收益{stats['mean_return']:+6.2f}%, "
                                f"上涨概率{stats['positive_ratio']:5.1%}, "
                                f"样本数{stats['sample_size']}\n"
                            )

                    if performance and performance.get('downward_events_count', 0) > 0:
                        full_report += f"\n  📊 向下偏离>30%后的历史表现 (样本: {performance['downward_events_count']} 次):\n"
                        for period, stats in performance['downward_performance'].items():
                            full_report += (
                                f"    {period:>3}: 平均收益{stats['mean_return']:+6.2f}%, "
                                f"上涨概率{stats['positive_ratio']:5.1%}, "
                                f"样本数{stats['sample_size']}\n"
                            )

                    analyzed_count += 1

                except Exception as e:
                    full_report += f"  分析失败: {str(e)}\n"
                    continue

            # 统计预警级别
            alert_count = sum(len(alerts) for alerts in all_alerts.values())
            has_level3 = any('三级预警' in alert.message for alerts in all_alerts.values() for alert in alerts)
            has_level2 = any('二级预警' in alert.message for alerts in all_alerts.values() for alert in alerts)

            logger.info(f"发送预警邮件: {alert_count} 个信号")
            success = notifier.send_alert_email(
                alert_report=full_report,
                alert_count=alert_count,
                has_level3=has_level3,
                has_level2=has_level2
            )

            if success:
                logger.info("✅ 预警邮件发送成功")
            else:
                logger.error("❌ 预警邮件发送失败")

            return success
        else:
            logger.info("无预警,发送正常监控邮件")
            success = notifier.send_no_alert_email()

            if success:
                logger.info("✅ 正常监控邮件发送成功")
            else:
                logger.error("❌ 正常监控邮件发送失败")

            return success

    except FileNotFoundError:
        logger.error("❌ 邮件配置文件未找到!")
        logger.info("请参考 email_config.yaml.template 创建 email_config.yaml 配置文件")
        return False
    except Exception as e:
        logger.error(f"❌ 发送邮件失败: {str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='均线偏离度监控系统')
    parser.add_argument(
        '--email',
        action='store_true',
        help='发送邮件通知 (需要先配置 email_config.yaml)'
    )
    parser.add_argument(
        '--retry',
        type=int,
        default=3,
        help='失败重试次数 (默认: 3)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式,不输出到控制台'
    )

    args = parser.parse_args()

    if not args.quiet:
        print("=" * 70)
        print("🔍 均线偏离度监控系统")
        print("=" * 70)
        print("监控范围:")
        print("  A股: 上证指数、沪深300、创业板指、科创50、深证成指")
        print("       中小板指、上证50、中证500、中证1000")
        print("  港股: 恒生指数、恒生科技")
        print("=" * 70)
        print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if args.email:
            print("邮件通知: 已启用")
        print("=" * 70)

    # 运行监控(带重试)
    all_alerts, report, monitor = run_monitor_with_retry(max_retries=args.retry)

    if report is None:
        logger.error("❌ 监控失败,无法生成报告")
        sys.exit(1)

    # 控制台输出
    if not args.quiet:
        print_console_report(all_alerts, report, monitor)
        print("\n" + "=" * 70)
        print("✅ 监控完成！")
        print("=" * 70)

    # 发送邮件
    if args.email:
        success = send_email_report(all_alerts, report, monitor)
        if not success:
            sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
