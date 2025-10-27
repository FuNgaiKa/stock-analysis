#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合资产分析执行脚本
运行方式:
  python scripts/comprehensive_asset_analysis/run_asset_analysis.py
  python scripts/comprehensive_asset_analysis/run_asset_analysis.py --email
  python scripts/comprehensive_asset_analysis/run_asset_analysis.py --save report.txt
  python scripts/comprehensive_asset_analysis/run_asset_analysis.py --format markdown --save report.md
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.comprehensive_asset_analysis.asset_reporter import ComprehensiveAssetReporter
from scripts.comprehensive_asset_analysis.asset_email_notifier import AssetEmailNotifier


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='综合资产分析 (四大科技指数 + 沪深300 + 黄金 + 比特币)')
    parser.add_argument('--email', action='store_true', help='发送邮件到 1264947688@qq.com')
    parser.add_argument('--save', type=str, help='保存报告到文件')
    parser.add_argument('--format', type=str, choices=['text', 'markdown'], default='text', help='报告格式 (text 或 markdown)')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    try:
        print("=" * 80)
        print("综合资产分析工具")
        print("分析对象: 四大科技指数 + 沪深300 + 黄金 + 比特币")
        print("=" * 80)

        logger.info("开始生成综合资产分析报告...")

        # 生成报告
        reporter = ComprehensiveAssetReporter()
        report = reporter.generate_comprehensive_report()

        # 根据格式生成报告内容
        if args.format == 'markdown':
            formatted_report = reporter.format_markdown_report(report)
            logger.info("使用Markdown格式生成报告")
        else:
            formatted_report = reporter.format_text_report(report)
            logger.info("使用文本格式生成报告")

        # 打印到控制台
        print("\n" + formatted_report)

        # 保存到文件
        if args.save:
            save_path = Path(args.save)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(formatted_report)
            logger.info(f"报告已保存到: {save_path}")

        # 发送邮件(始终使用文本格式)
        if args.email:
            logger.info("准备发送邮件到 1264947688@qq.com ...")
            try:
                # 邮件发送使用文本格式报告
                text_report = reporter.format_text_report(report)
                notifier = AssetEmailNotifier()
                success = notifier.send_asset_report(report, text_report)
                if success:
                    logger.info("✅ 邮件发送成功")
                else:
                    logger.error("❌ 邮件发送失败")
                    sys.exit(1)
            except Exception as e:
                logger.error(f"邮件发送异常: {str(e)}")
                logger.info("💡 提示: 请确保已配置 config/email_config.yaml")
                sys.exit(1)

        logger.info("✅ 分析任务完成")

    except Exception as e:
        logger.error(f"执行失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
