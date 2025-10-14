#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四大科技指数综合分析执行脚本
运行方式:
  python scripts/tech_indices_analysis/run_tech_comprehensive_analysis.py
  python scripts/tech_indices_analysis/run_tech_comprehensive_analysis.py --email
  python scripts/tech_indices_analysis/run_tech_comprehensive_analysis.py --save report.txt
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.tech_indices_analysis.tech_indices_reporter import TechIndicesReporter
from scripts.tech_indices_analysis.tech_email_notifier import TechEmailNotifier


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='四大科技指数综合分析')
    parser.add_argument('--email', action='store_true', help='发送邮件到 1264947688@qq.com')
    parser.add_argument('--save', type=str, help='保存报告到文件')
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
        print("四大科技指数综合分析工具")
        print("分析对象: 创业板指、科创50、恒生科技、纳斯达克")
        print("=" * 80)

        logger.info("开始生成四大科技指数综合分析报告...")

        # 生成报告
        reporter = TechIndicesReporter()
        report = reporter.generate_comprehensive_report()

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
            logger.info("准备发送邮件到 1264947688@qq.com ...")
            try:
                notifier = TechEmailNotifier()
                success = notifier.send_tech_report(report, text_report)
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
