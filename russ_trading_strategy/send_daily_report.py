#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送每日持仓调整报告邮件

⚠️ 重要：禁止自动发送持仓报告邮件！
只生成MD文档，不发送邮件。
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# ==================== 安全开关 ====================
# ⚠️ 禁止发送持仓报告到邮件
ENABLE_EMAIL_SENDING = False  # 设置为 False 禁止发送邮件
# ==================================================

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from russ_trading_strategy.unified_email_notifier import UnifiedEmailNotifier

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def send_today_report(date: str = None):
    """
    发送今天的持仓调整报告

    Args:
        date: 报告日期，格式YYYY-MM-DD，默认为今天
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    # 构建报告文件路径
    year_month = date[:7]  # YYYY-MM
    report_filename = f"持仓调整建议_{date.replace('-', '')}_v2.md"

    project_root = Path(__file__).parent.parent
    report_path = project_root / 'reports' / 'daily' / year_month / report_filename

    logger.info(f"查找报告文件: {report_path}")

    # 检查报告文件是否存在
    if not report_path.exists():
        logger.error(f"报告文件不存在: {report_path}")
        logger.info("请先运行 daily_position_report_generator_v2.py 生成报告")
        return False

    # 读取报告内容
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        logger.info(f"✅ 成功读取报告文件 ({len(report_content)} 字符)")
    except Exception as e:
        logger.error(f"读取报告文件失败: {e}")
        return False

    # 创建邮件通知器
    try:
        notifier = UnifiedEmailNotifier()
        logger.info("✅ 邮件通知器初始化成功")
    except Exception as e:
        logger.error(f"邮件通知器初始化失败: {e}")
        logger.info("请检查 config/email_config.yaml 配置文件")
        return False

    # 检查安全开关
    if not ENABLE_EMAIL_SENDING:
        logger.warning("=" * 80)
        logger.warning("⚠️  邮件发送已被禁止！")
        logger.warning("⚠️  持仓报告只会生成MD文档，不会发送邮件")
        logger.warning("⚠️  如需发送邮件，请修改 ENABLE_EMAIL_SENDING = True")
        logger.warning("=" * 80)
        logger.info(f"✅ 报告文件已生成: {report_path}")
        return True

    # 发送邮件
    logger.info("开始发送邮件...")
    try:
        report_data = {
            'date': date,
            'title': f'持仓调整建议报告 v2.0 - {date}'
        }

        success = notifier.send_position_report(
            report_data=report_data,
            text_content=report_content,
            date=date
        )

        if success:
            logger.info("🎉 邮件发送成功!")
            return True
        else:
            logger.error("❌ 邮件发送失败")
            return False

    except Exception as e:
        logger.error(f"发送邮件时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='发送每日持仓调整报告邮件')
    parser.add_argument('--date', type=str, help='报告日期 (格式: YYYY-MM-DD)')

    args = parser.parse_args()

    print("=" * 80)
    print("每日持仓调整报告邮件发送工具")
    print("=" * 80)

    success = send_today_report(date=args.date)

    sys.exit(0 if success else 1)
