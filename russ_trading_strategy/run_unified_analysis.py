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
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from russ_trading_strategy.unified_config import (
    UNIFIED_ASSETS,
    list_all_assets,
    list_assets_by_analyzer,
    get_asset_config
)
from scripts.comprehensive_asset_analysis.asset_reporter import ComprehensiveAssetReporter
from scripts.sector_analysis.sector_reporter import SectorReporter
from russ_trading_strategy.unified_email_notifier import UnifiedEmailNotifier

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
        else:
            lines.append(f"总资产数: {total_count}")
            lines.append(f"成功分析: {success_count}")
            lines.append(f"失败数: {fail_count}")
            lines.append("")
            lines.append("=" * 80)
            lines.append("")

        # 生成汇总表格
        if format_type == 'markdown':
            summary_table = self._generate_summary_table(results)
            if summary_table:
                lines.append("## 📊 标的汇总")
                lines.append("")
                lines.append(summary_table)
                lines.append("")
            lines.append("---")
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

    def _generate_summary_table(self, results: dict) -> str:
        """生成所有标的汇总表格"""
        lines = []

        # 表头 (添加持有建议列)
        lines.append("| 标的名称 | 当前价格 | 涨跌幅 | 方向判断 | 建议仓位 | 20日上涨概率 | 风险等级 | 持有建议 |")
        lines.append("|----------|----------|--------|----------|----------|--------------|----------|----------|")

        # 遍历所有资产
        for asset_key, data in results['assets'].items():
            if 'error' in data:
                continue

            config = UNIFIED_ASSETS[asset_key]

            # 标的名称
            if config['analyzer_type'] == 'comprehensive':
                asset_name = data.get('asset_name', config['name'])
            else:
                asset_name = data.get('sector_name', config['name'])

            # 当前价格和涨跌幅 - 修复字段名称
            # comprehensive 类型使用 'historical_analysis', sector 类型也使用 'historical_analysis'
            hist = data.get('historical_analysis', {})

            current_price = hist.get('current_price', 0)
            change_pct = hist.get('current_change_pct', 0)
            # 中国股市习惯: 红涨绿跌
            change_emoji = "🔴" if change_pct >= 0 else "🟢"

            # 综合判断
            judgment = data.get('comprehensive_judgment', {})
            direction = judgment.get('direction', 'N/A')
            position = judgment.get('recommended_position', 'N/A')

            # 方向判断emoji
            direction_map = {
                '强烈看多': '✅✅',
                '看多': '✅',
                '中性偏多': '⚖️',
                '中性': '⚖️',
                '看空': '🔴'
            }
            direction_with_emoji = f"{direction}{direction_map.get(direction, '')}"

            # 20日上涨概率 (comprehensive 和 sector 使用相同字段)
            stats_20d = hist.get('20d', {})
            up_prob_20d = stats_20d.get('up_prob', 0)
            # 给上涨概率添加颜色: >=60%红色(看涨), <40%绿色(看跌), 40-60%无色
            if up_prob_20d >= 0.6:
                prob_emoji = "🔴"
            elif up_prob_20d < 0.4:
                prob_emoji = "🟢"
            else:
                prob_emoji = ""
            prob_display = f"{up_prob_20d:.1%} {prob_emoji}" if prob_emoji else f"{up_prob_20d:.1%}"

            # 风险等级
            risk = data.get('risk_assessment', {})
            risk_level = risk.get('risk_level', 'N/A')
            risk_emoji_map = {
                '极高风险': '🔴🔴🔴',
                '高风险': '🔴🔴',
                '中风险': '⚠️',
                '低风险': '✅'
            }
            risk_with_emoji = f"{risk_emoji_map.get(risk_level, '')} {risk_level}"

            # 持有建议 - 从 strategies 中提取包含"持有"的建议
            strategies = judgment.get('strategies', [])
            hold_suggestion = '-'
            for strategy in strategies:
                # 匹配包含"持有"关键词的建议
                if '持有' in strategy:
                    hold_suggestion = strategy
                    break

            # 生成表格行 (添加持有建议列)
            lines.append(
                f"| {asset_name} | {current_price:.2f} | "
                f"{change_pct:+.2f}% {change_emoji} | {direction_with_emoji} | {position} | "
                f"{prob_display} | {risk_with_emoji} | {hold_suggestion} |"
            )

        return '\n'.join(lines)

    def _format_sector_markdown(self, asset_key: str, data: dict, config: dict) -> str:
        """格式化单个板块为 Markdown (参考 SectorReporter 的格式)"""
        lines = []

        # 标题
        lines.append(f"## {config['category'].upper()}: {data.get('sector_name', config['name'])}")
        lines.append("")
        lines.append(f"**描述**: {config.get('description', 'N/A')}")
        lines.append("")

        # 1. 当前点位
        hist = data.get('historical_analysis', {})
        if hist and 'current_price' in hist:
            lines.append("### 当前点位")
            lines.append(f"- **最新价格**: {hist['current_price']:.2f}")

            change_pct = hist.get('current_change_pct', 0)
            # 中国股市习惯: 红涨绿跌
            change_emoji = "🔴" if change_pct >= 0 else "🟢"
            lines.append(f"- **涨跌幅**: {change_pct:+.2f}% {change_emoji}")
            lines.append(f"- **数据日期**: {hist.get('current_date', 'N/A')}")
            lines.append("")

        # 2. 综合判断
        judgment = data.get('comprehensive_judgment', {})
        if judgment:
            lines.append("### 综合判断")

            direction = judgment.get('direction', 'N/A')
            direction_emoji_map = {
                '强烈看多': '✅✅',
                '看多': '✅',
                '中性偏多': '⚖️',
                '中性': '⚖️',
                '看空': '🔴'
            }
            direction_emoji = direction_emoji_map.get(direction, '⚖️')
            lines.append(f"- **方向判断**: {direction}{direction_emoji}")
            lines.append(f"- **建议仓位**: {judgment.get('recommended_position', 'N/A')}")
            lines.append("")

            strategies = judgment.get('strategies', [])
            if strategies:
                lines.append("**操作策略**:")
                for strategy in strategies:
                    lines.append(f"  - {strategy}")
                lines.append("")

        # 3. 历史点位分析
        if hist and '20d' in hist:
            lines.append("### 历史点位分析")
            lines.append(f"- **相似点位**: {hist.get('similar_periods_count', 0)} 个")
            lines.append("")
            lines.append("| 周期 | 上涨概率 | 平均收益 | 收益中位 | 置信度 |")
            lines.append("|------|----------|----------|----------|--------|")

            stats_20d = hist.get('20d', {})
            if stats_20d:
                lines.append(
                    f"| 未来20日 | {stats_20d.get('up_prob', 0):.1%} | "
                    f"{stats_20d.get('mean_return', 0):+.2%} | "
                    f"{stats_20d.get('median_return', 0):+.2%} | "
                    f"{stats_20d.get('confidence', 0):.1%} |"
                )

            stats_60d = hist.get('60d', {})
            if stats_60d and stats_60d.get('confidence', 0) > 0:
                lines.append(
                    f"| 未来60日 | {stats_60d.get('up_prob', 0):.1%} | "
                    f"{stats_60d.get('mean_return', 0):+.2%} | - | - |"
                )

            lines.append("")

        # 4. 技术面分析
        tech = data.get('technical_analysis', {})
        if tech and 'error' not in tech:
            lines.append("### 技术面分析")

            # MACD
            if 'macd' in tech:
                macd_status = '✅ 金叉' if tech['macd']['status'] == 'golden_cross' else '🔴 死叉'
                lines.append(f"- **MACD**: {macd_status}")

            # RSI
            if 'rsi' in tech:
                rsi_val = tech['rsi']['value']
                rsi_status_map = {
                    'overbought': '⚠️ 超买',
                    'oversold': '✅ 超卖',
                    'normal': '😊 正常'
                }
                rsi_status = rsi_status_map.get(tech['rsi']['status'], '')
                lines.append(f"- **RSI**: {rsi_val:.1f} ({rsi_status})")

            # KDJ
            if 'kdj' in tech:
                kdj = tech['kdj']
                kdj_signal = '✅' if kdj['signal'] == 'golden_cross' else '🔴'
                lines.append(f"- **KDJ**: K={kdj['k']:.1f}, D={kdj['d']:.1f}, J={kdj['j']:.1f} {kdj_signal}")

            # 布林带
            if 'boll' in tech:
                boll = tech['boll']
                boll_pos_pct = boll['position'] * 100
                boll_status_map = {
                    'near_upper': '⚠️ 接近上轨',
                    'near_lower': '✅ 接近下轨',
                    'normal': '😊 中轨区域'
                }
                boll_status = boll_status_map.get(boll['status'], '')
                lines.append(f"- **布林带**: {boll_pos_pct:.0f}% ({boll_status})")

            # DMI/ADX
            if 'dmi_adx' in tech:
                dmi = tech['dmi_adx']
                trend_map = {'strong': 'strong 🔥', 'medium': 'medium 📊', 'weak': 'weak ⚡'}
                direction_emoji = '📈' if dmi['direction'] == 'bullish' else '📉'
                lines.append(
                    f"- **DMI/ADX**: {dmi['adx']:.1f} ({trend_map.get(dmi['trend'], '')}, {direction_emoji})"
                )

            lines.append("")

        # 5. 资金面分析
        capital = data.get('capital_flow', {})
        if capital and 'error' not in capital and capital.get('type'):
            lines.append("### 资金面分析")
            flow_type = '**北向资金(外资)**' if capital['type'] == 'northbound' else '**南向资金(内地)**'
            lines.append(f"{flow_type}:")
            lines.append(f"- **近5日累计**: {capital.get('recent_5d_flow', 0):.2f} 亿元")
            lines.append(f"- **流向状态**: {capital.get('status', 'N/A')}")
            lines.append(f"- **情绪评分**: {capital.get('sentiment_score', 50)}/100")
            lines.append("")

        # 6. 风险评估
        risk = data.get('risk_assessment', {})
        if risk:
            lines.append("### 风险评估")
            risk_level = risk.get('risk_level', 'N/A')
            risk_emoji_map = {
                '极高风险': '🔴🔴🔴',
                '高风险': '🔴🔴',
                '中风险': '⚠️',
                '低风险': '✅'
            }
            risk_emoji = risk_emoji_map.get(risk_level, '')
            lines.append(f"- **综合风险**: {risk.get('risk_score', 0):.2f} ({risk_emoji} {risk_level})")

            risk_factors = risk.get('risk_factors', [])
            if risk_factors:
                lines.append("- **风险因素**:")
                for factor in risk_factors:
                    lines.append(f"  - {factor}")

            lines.append("")

        # 7. 成交量分析
        volume = data.get('volume_analysis', {})
        if volume and 'error' not in volume:
            lines.append("### 成交量分析")
            obv = volume.get('obv_analysis', {})
            if obv:
                obv_trend = obv.get('trend', 'N/A')
                obv_emoji = '➡️' if obv_trend in ['上升', '下降', '平稳'] else ''
                lines.append(f"- **OBV趋势**: {obv_trend} {obv_emoji}")
            lines.append("")

        # 8. 支撑压力位
        sr = data.get('support_resistance', {})
        if sr and 'error' not in sr and sr.get('available', True):
            lines.append("### 支撑压力位")
            pivot = sr.get('pivot_points', {})
            if pivot:
                lines.append(f"- **轴心点**: {pivot.get('pivot', 0):.2f}")
                lines.append(f"- **阻力位**: R1={pivot.get('r1', 0):.2f}, R2={pivot.get('r2', 0):.2f}")
                lines.append(f"- **支撑位**: S1={pivot.get('s1', 0):.2f}, S2={pivot.get('s2', 0):.2f}")
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
    parser.add_argument(
        '--email',
        action='store_true',
        help='发送邮件到配置的收件人列表'
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

        # 发送邮件(始终使用文本格式)
        if args.email:
            logger.info("准备发送邮件到配置的收件人列表...")
            try:
                # 邮件发送使用文本格式报告
                text_report = runner.format_report(results, 'text')
                notifier = UnifiedEmailNotifier()
                success = notifier.send_unified_report(results, text_report)
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
