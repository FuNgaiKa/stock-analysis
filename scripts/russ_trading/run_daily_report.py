#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日市场报告执行脚本
运行方式: python scripts/run_daily_report.py --email
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategies.position.reporting.daily_market_reporter import DailyMarketReporter
from strategies.position.reporting.email_notifier import EmailNotifier


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='每日市场报告生成和发送')
    parser.add_argument('--email', action='store_true', help='发送邮件')
    parser.add_argument('--save', type=str, help='保存报告到文件')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    try:
        logger.info("开始生成每日市场报告...")

        # 生成报告
        reporter = DailyMarketReporter()
        report = reporter.generate_daily_report()

        # 检查是否有错误
        if 'error' in report:
            logger.error(f"生成报告失败: {report['error']}")
            sys.exit(1)

        # 打印到控制台
        text_report = reporter.format_text_report(report)
        print("\n" + text_report)

        # 保存到文件
        if args.save:
            save_path = Path(args.save)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(text_report)
            logger.info(f"报告已保存到: {save_path}")

        # 发送邮件
        if args.email:
            logger.info("准备发送邮件...")
            try:
                notifier = EmailNotifier()
                success = notifier.send_daily_report(report)
                if success:
                    logger.info("✅ 邮件发送成功")
                else:
                    logger.error("❌ 邮件发送失败")
                    sys.exit(1)
            except Exception as e:
                logger.error(f"邮件发送异常: {str(e)}")
                sys.exit(1)

        logger.info("✅ 每日报告任务完成")

    except Exception as e:
        logger.error(f"执行失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
