#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一资产分析执行脚本
Unified Asset Analysis Runner

一次运行分析所有标的(指数、板块、个股)
整合了 comprehensive_asset_analysis 和 sector_analysis 的功能

运行方式:
  python scripts/unified_analysis/run_unified_analysis.py
  python scripts/unified_analysis/run_unified_analysis.py --assets CYBZ HK_BIOTECH SANHUA_A
  python scripts/unified_analysis/run_unified_analysis.py --save reports/unified_report.md
  python scripts/unified_analysis/run_unified_analysis.py --format markdown
  python scripts/unified_analysis/run_unified_analysis.py --list

作者: Claude Code
日期: 2025-10-16
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.unified_analysis.unified_config import (
    UNIFIED_ASSETS,
    list_all_assets,
    list_assets_by_analyzer,
    get_asset_config
)
from scripts.comprehensive_asset_analysis.asset_reporter import ComprehensiveAssetReporter
from scripts.sector_analysis.sector_reporter import SectorReporter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedAnalysisRunner:
    """统一资产分析执行器"""

    def __init__(self):
        """初始化分析器"""
        self.comprehensive_reporter = None
        self.sector_reporter = None

    def analyze_assets(self, asset_keys: list = None) -> dict:
        """
        分析资产

        Args:
            asset_keys: 资产代码列表,None表示分析所有资产

        Returns:
            分析结果字典
        """
        if asset_keys is None:
            asset_keys = list(UNIFIED_ASSETS.keys())

        logger.info(f"准备分析 {len(asset_keys)} 个资产...")

        results = {
            'timestamp': datetime.now(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'assets': {}
        }

        # 按分析器类型分组
        comprehensive_assets = []
        sector_assets = []

        for asset_key in asset_keys:
            if asset_key not in UNIFIED_ASSETS:
                logger.warning(f"资产 {asset_key} 不存在，跳过")
                continue

            config = UNIFIED_ASSETS[asset_key]
            if config['analyzer_type'] == 'comprehensive':
                comprehensive_assets.append(asset_key)
            elif config['analyzer_type'] == 'sector':
                sector_assets.append(asset_key)

        # 分析指数类资产 (使用 ComprehensiveAssetReporter)
        if comprehensive_assets:
            logger.info(f"分析指数类资产: {', '.join(comprehensive_assets)}")
            if self.comprehensive_reporter is None:
                self.comprehensive_reporter = ComprehensiveAssetReporter()

            for asset_key in comprehensive_assets:
                try:
                    logger.info(f"分析 {UNIFIED_ASSETS[asset_key]['name']}...")
                    result = self.comprehensive_reporter.analyze_single_asset(asset_key)
                    results['assets'][asset_key] = result
                except Exception as e:
                    logger.error(f"分析 {asset_key} 失败: {str(e)}")
                    results['assets'][asset_key] = {
                        'error': str(e),
                        'asset_name': UNIFIED_ASSETS[asset_key]['name']
                    }

        # 分析板块类资产 (使用 SectorReporter)
        if sector_assets:
            logger.info(f"分析板块类资产: {', '.join(sector_assets)}")
            if self.sector_reporter is None:
                self.sector_reporter = SectorReporter()

            for asset_key in sector_assets:
                try:
                    logger.info(f"分析 {UNIFIED_ASSETS[asset_key]['name']}...")
                    result = self.sector_reporter.analyze_single_sector(asset_key)
                    results['assets'][asset_key] = result
                except Exception as e:
                    logger.error(f"分析 {asset_key} 失败: {str(e)}")
                    results['assets'][asset_key] = {
                        'error': str(e),
                        'asset_name': UNIFIED_ASSETS[asset_key]['name']
                    }

        logger.info("所有资产分析完成")
        return results

    def format_report(self, results: dict, format_type: str = 'markdown') -> str:
        """
        格式化报告

        直接调用原有报告生成器的方法,确保数据完整展示

        Args:
            results: 分析结果
            format_type: 报告格式 ('text' 或 'markdown')

        Returns:
            格式化后的报告文本
        """
        lines = []

        # 报告头部
        if format_type == 'markdown':
            lines.append("# 📊 统一资产分析报告")
            lines.append("")
            lines.append(f"**生成时间**: {results['date']}")
            lines.append("")
            lines.append("---")
            lines.append("")
        else:
            lines.append("=" * 80)
            lines.append("统一资产分析报告".center(80))
            lines.append(f"生成时间: {results['date']}".center(80))
            lines.append("=" * 80)
            lines.append("")

        # 统计信息
        total_count = len(results['assets'])
        success_count = sum(1 for data in results['assets'].values() if 'error' not in data)
        fail_count = total_count - success_count

        if format_type == 'markdown':
            lines.append("## 📋 分析概览")
            lines.append("")
            lines.append(f"- **总资产数**: {total_count}")
            lines.append(f"- **成功分析**: {success_count}")
            lines.append(f"- **失败数**: {fail_count}")
            lines.append("")
            lines.append("---")
            lines.append("")
        else:
            lines.append(f"总资产数: {total_count}")
            lines.append(f"成功分析: {success_count}")
            lines.append(f"失败数: {fail_count}")
            lines.append("")
            lines.append("=" * 80)
            lines.append("")

        # 分组整理报告数据
        comprehensive_report = {'assets': {}}
        sector_reports = []

        for asset_key, data in results['assets'].items():
            if 'error' in data:
                continue

            config = UNIFIED_ASSETS[asset_key]
            if config['analyzer_type'] == 'comprehensive':
                comprehensive_report['assets'][asset_key] = data
            elif config['analyzer_type'] == 'sector':
                sector_reports.append((asset_key, data, config))

        # 生成指数类资产报告 (使用 ComprehensiveAssetReporter)
        if comprehensive_report['assets'] and self.comprehensive_reporter:
            comprehensive_report['timestamp'] = results['timestamp']
            comprehensive_report['date'] = results['date']

            if format_type == 'markdown':
                lines.append(self.comprehensive_reporter.format_markdown_report(comprehensive_report))
            else:
                lines.append(self.comprehensive_reporter.format_text_report(comprehensive_report))

        # 生成板块类资产报告 (使用 SectorReporter)
        if sector_reports and self.sector_reporter:
            for asset_key, data, config in sector_reports:
                # 构造单个板块的报告数据
                single_sector_report = {
                    'timestamp': results['timestamp'],
                    'date': results['date'],
                    'sectors': {asset_key: data}
                }

                if format_type == 'markdown':
                    # SectorReporter 只有 format_text_report,我们需要手动生成 markdown
                    lines.append(self._format_sector_markdown(asset_key, data, config))
                else:
                    lines.append(self.sector_reporter.format_text_report(single_sector_report))

        # 失败的资产
        if fail_count > 0:
            if format_type == 'markdown':
                lines.append("## ⚠️ 分析失败")
                lines.append("")
                for asset_key, data in results['assets'].items():
                    if 'error' in data:
                        lines.append(f"- **{data.get('asset_name', asset_key)}**: {data['error']}")
                lines.append("")
            else:
                lines.append("-" * 80)
                lines.append("分析失败")
                lines.append("-" * 80)
                for asset_key, data in results['assets'].items():
                    if 'error' in data:
                        lines.append(f"{data.get('asset_name', asset_key)}: {data['error']}")
                lines.append("")

        # 报告尾部
        if format_type == 'markdown':
            lines.append("---")
            lines.append("")
            lines.append("**免责声明**: 本报告仅供参考,不构成投资建议。投资有风险,入市需谨慎。")
            lines.append("")
            lines.append(f"*报告生成时间: {results['date']}*")
        else:
            lines.append("=" * 80)
            lines.append("免责声明: 本报告仅供参考,不构成投资建议。投资有风险,入市需谨慎。")
            lines.append("=" * 80)

        return '\n'.join(lines)

    def _format_sector_markdown(self, asset_key: str, data: dict, config: dict) -> str:
        """格式化单个板块为 Markdown (参考 SectorReporter 的格式)"""
        lines = []

        lines.append(f"## {config['category'].upper()}: {data.get('name', config['name'])}")
        lines.append("")
        lines.append(f"**描述**: {config.get('description', 'N/A')}")
        lines.append("")

        # 当前价格
        if 'current_price' in data:
            lines.append("### 💰 当前价格")
            lines.append("")
            lines.append("| 指标 | 数值 |")
            lines.append("|------|------|")
            lines.append(f"| **当前价格** | {data['current_price']:.2f} |")

            if 'change_pct' in data:
                change_emoji = "📈" if data['change_pct'] >= 0 else "📉"
                lines.append(f"| **涨跌幅** | {change_emoji} {data['change_pct']:+.2f}% |")

            if 'change' in data:
                lines.append(f"| **涨跌额** | {data['change']:+.2f} |")

            lines.append("")

        # 技术指标
        if 'technical_indicators' in data:
            tech = data['technical_indicators']
            lines.append("### 📊 技术指标")
            lines.append("")
            lines.append("| 指标 | 数值 |")
            lines.append("|------|------|")

            for key, value in tech.items():
                if isinstance(value, (int, float)):
                    lines.append(f"| **{key}** | {value:.2f} |")
                else:
                    lines.append(f"| **{key}** | {value} |")

            lines.append("")

        # 市场情绪
        if 'market_sentiment' in data:
            sentiment = data['market_sentiment']
            lines.append("### 😊 市场情绪")
            lines.append("")
            lines.append(f"{sentiment.get('description', 'N/A')}")
            lines.append("")

        # 投资建议
        if 'recommendation' in data:
            rec = data['recommendation']
            lines.append("### 💡 投资建议")
            lines.append("")

            rating = rec.get('rating', 'N/A')
            emoji_map = {
                '强烈买入': '🟢🟢🟢',
                '买入': '🟢🟢',
                '持有': '🟡',
                '卖出': '🔴🔴',
                '强烈卖出': '🔴🔴🔴'
            }
            rating_emoji = emoji_map.get(rating, '')

            lines.append(f"**评级**: {rating_emoji} {rating}")
            lines.append("")

            if 'reason' in rec:
                lines.append(f"**理由**: {rec['reason']}")
                lines.append("")

            if 'target_price' in rec:
                lines.append(f"**目标价**: {rec['target_price']:.2f}")
                lines.append("")

        # 风险提示
        if 'risk_warning' in data:
            warnings = data['risk_warning']
            if warnings:
                lines.append("### ⚠️ 风险提示")
                lines.append("")
                for warning in warnings:
                    lines.append(f"- {warning}")
                lines.append("")

        lines.append("---")
        lines.append("")

        return '\n'.join(lines)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='统一资产分析工具 (整合指数、板块、个股分析)'
    )
    parser.add_argument(
        '--assets',
        nargs='+',
        help='指定资产代码(如 CYBZ HK_BIOTECH SANHUA_A)，不指定则分析所有资产'
    )
    parser.add_argument(
        '--save',
        type=str,
        help='保存报告到文件'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['text', 'markdown'],
        default='markdown',
        help='报告格式 (text 或 markdown)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有可用资产'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )

    args = parser.parse_args()

    # 配置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 列出所有资产
    if args.list:
        print("=" * 80)
        print("所有可用资产:")
        print("=" * 80)
        print(f"{'代码':<20} {'名称':<20} {'类别':<15} {'分析器':<15}")
        print("-" * 80)

        for key, name, category, analyzer_type in list_all_assets():
            print(f"{key:<20} {name:<20} {category:<15} {analyzer_type:<15}")

        print("=" * 80)
        print(f"总计: {len(UNIFIED_ASSETS)} 个资产")
        print("=" * 80)
        return

    try:
        print("=" * 80)
        print("统一资产分析工具")
        print("=" * 80)

        # 确定要分析的资产
        asset_keys = args.assets
        if asset_keys:
            print(f"分析资产: {', '.join(asset_keys)}")
        else:
            all_assets = list(UNIFIED_ASSETS.keys())
            asset_keys = all_assets
            print(f"分析所有资产 ({len(asset_keys)} 个)")

        print("=" * 80)

        # 执行分析
        runner = UnifiedAnalysisRunner()
        results = runner.analyze_assets(asset_keys)

        # 格式化报告
        report = runner.format_report(results, args.format)

        # 打印到控制台 (处理 Windows GBK 编码)
        try:
            print("\n" + report)
        except UnicodeEncodeError:
            # Windows 控制台 GBK 编码不支持 emoji 和特殊字符
            text_safe = report.encode('gbk', errors='ignore').decode('gbk')
            print("\n" + text_safe)

        # 保存到文件
        if args.save:
            save_path = Path(args.save)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"报告已保存到: {save_path}")

        logger.info("✅ 分析任务完成")

    except Exception as e:
        logger.error(f"执行失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
