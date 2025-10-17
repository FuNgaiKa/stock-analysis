#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块综合分析执行脚本
Sector Analysis Runner

运行方式:
  python scripts/sector_analysis/run_sector_analysis.py
  python scripts/sector_analysis/run_sector_analysis.py --sectors HK_BIOTECH HK_BATTERY
  python scripts/sector_analysis/run_sector_analysis.py --save report.txt
  python scripts/sector_analysis/run_sector_analysis.py --email

作者: Claude Code
日期: 2025-10-16
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.sector_analysis.sector_reporter import SectorReporter
from scripts.sector_analysis.sector_config import list_all_sectors


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='板块综合分析工具')
    parser.add_argument(
        '--sectors',
        nargs='+',
        help='指定板块(如 HK_BIOTECH HK_BATTERY)，不指定则分析所有板块'
    )
    parser.add_argument('--save', type=str, help='保存报告到文件')
    parser.add_argument('--email', action='store_true', help='发送邮件(待实现)')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('--list', action='store_true', help='列出所有可用板块')
    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    # 列出所有板块
    if args.list:
        print("=" * 80)
        print("所有可用板块:")
        print("=" * 80)
        for key, name, category in list_all_sectors():
            print(f"  [{key}] {name} ({category})")
        print("=" * 80)
        return

    try:
        print("=" * 80)
        print("板块综合分析工具")
        print("=" * 80)

        # 确定要分析的板块
        sector_keys = args.sectors
        if sector_keys:
            print(f"分析板块: {', '.join(sector_keys)}")
        else:
            all_sectors = [key for key, _, _ in list_all_sectors()]
            sector_keys = all_sectors
            print(f"分析所有板块: {', '.join(sector_keys)}")

        print("=" * 80)

        logger.info("开始生成板块综合分析报告...")

        # 生成报告
        reporter = SectorReporter()
        report = reporter.generate_comprehensive_report(sector_keys)

        # 打印到控制台 (Windows GBK编码处理)
        text_report = reporter.format_text_report(report)
        try:
            print("\n" + text_report)
        except UnicodeEncodeError:
            # Windows控制台GBK编码不支持emoji和特殊字符,转换后输出
            text_safe = text_report.encode('gbk', errors='ignore').decode('gbk')
            print("\n" + text_safe)

        # 保存到文件
        if args.save:
            save_path = Path(args.save)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(text_report)
            logger.info(f"报告已保存到: {save_path}")

        # 发送邮件(待实现)
        if args.email:
            logger.warning("邮件功能待实现，请使用 --save 保存报告")

        logger.info("分析任务完成")

    except Exception as e:
        logger.error(f"执行失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
