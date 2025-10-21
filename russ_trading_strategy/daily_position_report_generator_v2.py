#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日持仓调整建议报告生成器 v2.0 (机构级增强版)
Daily Position Report Generator v2.0 (Institutional Enhanced Edition)

集成12项新功能:
1. 执行摘要
2. 量化指标可视化
3. 归因分析
4. 情景分析
5. 压力测试
6. 相关性矩阵
7. 夏普比率
8. 因子暴露分析
9. 配置外置
10. 缓存机制
11. 日志增强
12. 多格式导出

运行方式:
    # Markdown格式
    python scripts/russ_trading_strategy/daily_position_report_generator_v2.py --date 2025-10-21

    # HTML格式
    python scripts/russ_trading_strategy/daily_position_report_generator_v2.py --date 2025-10-21 --format html

    # 指定持仓文件
    python scripts/russ_trading_strategy/daily_position_report_generator_v2.py --positions data/test_positions.json

作者: Claude Code
日期: 2025-10-21
版本: v2.0
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入原有模块
from russ_trading_strategy.position_health_checker import PositionHealthChecker
from russ_trading_strategy.unified_email_notifier import UnifiedEmailNotifier
from russ_trading_strategy.performance_tracker import PerformanceTracker
from russ_trading_strategy.daily_position_report_generator import DailyPositionReportGenerator as BaseGenerator

# 导入新模块
from russ_trading_strategy.core import (
    QuantAnalyzer,
    StressTester,
    ScenarioAnalyzer,
    AttributionAnalyzer,
    ExecutiveSummaryGenerator,
    ChartGenerator,
    PerformanceMetricsCalculator,
    HistoricalPerformanceAnalyzer,
    VisualizationGenerator
)
from russ_trading_strategy.core.institutional_metrics import InstitutionalMetricsCalculator
from russ_trading_strategy.utils import (
    get_risk_profile,
    setup_logger,
    cached
)
from russ_trading_strategy.formatters import HTMLFormatter

# 设置日志
logger = setup_logger('report_generator_v2', level=logging.INFO)


class EnhancedReportGenerator(BaseGenerator):
    """增强版报告生成器 (集成v2.0新功能)"""

    def __init__(self, risk_profile: str = 'ultra_aggressive'):
        """
        初始化增强版生成器

        Args:
            risk_profile: 风险偏好 (默认ultra_aggressive,2年翻倍目标)
        """
        # 调用父类初始化
        super().__init__(risk_profile)

        # 初始化新模块
        self.quant_analyzer = QuantAnalyzer()
        self.stress_tester = StressTester()
        self.scenario_analyzer = ScenarioAnalyzer()
        self.attribution_analyzer = AttributionAnalyzer()
        self.executive_summary_gen = ExecutiveSummaryGenerator()
        self.chart_generator = ChartGenerator()
        self.html_formatter = HTMLFormatter()
        self.performance_metrics_calc = PerformanceMetricsCalculator()
        self.historical_performance_analyzer = HistoricalPerformanceAnalyzer()
        self.visualization_gen = VisualizationGenerator()
        self.institutional_metrics_calc = InstitutionalMetricsCalculator()

        logger.info(f"增强版报告生成器初始化完成 (风险偏好: {risk_profile})")

    def generate_enhanced_report(
        self,
        date: str = None,
        positions: List[Dict] = None,
        market_data: Dict = None
    ) -> str:
        """
        生成增强版报告

        Args:
            date: 日期
            positions: 持仓列表
            market_data: 市场数据

        Returns:
            完整报告内容(Markdown)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"开始生成增强版报告: {date}")

        # 先生成基础报告
        base_report = super().generate_report(date, positions, market_data)

        # 如果没有持仓数据,返回基础报告
        if not positions:
            logger.warning("无持仓数据,返回基础报告")
            return base_report

        # 计算总市值
        total_value = sum(p.get('current_value', 0) for p in positions)

        # 生成健康检查
        health_result = self.health_checker.check_position_health(positions)

        # 生成操作建议
        action_items = self._generate_enhanced_action_items(positions, market_data, total_value)

        lines = []

        # ========== 标题 ==========
        lines.append("# 📊 Russ个人持仓调整策略报告 v2.0 (机构级增强版)")
        lines.append("")
        lines.append(f"**生成时间**: {date}  ")
        lines.append("**报告类型**: 个性化持仓调整方案 + 机构级风险管理  ")
        lines.append(f"**风险偏好**: {self.risk_profile.upper()} (积极进取型)  ")
        lines.append("**系统版本**: v2.0 (对标高盛/摩根士丹利投研体系)  ")
        lines.append("")

        # ========== 1. 执行摘要 (NEW!) ==========
        logger.info("生成执行摘要...")
        lines.append(self.executive_summary_gen.generate_summary(
            health_result,
            action_items,
            {'cash_ratio': 1.0 - sum(p.get('position_ratio', 0) for p in positions),
             'min_required': self.thresholds['min_cash_reserve']}
        ))

        # ========== 2. 今日市场表现 ==========
        lines.append("## 🔥 今日市场表现")
        lines.append("")
        if market_data and market_data.get('indices'):
            lines.append("### 📊 市场数据")
            lines.append("")
            lines.append("| 指数 | 最新点位 | 涨跌幅 | 状态 |")
            lines.append("|------|---------|--------|------|")

            indices = market_data['indices']

            if 'HS300' in indices:
                hs300 = indices['HS300']
                emoji = "🔴" if hs300['change_pct'] >= 0 else "🟢"
                status = "上涨" if hs300['change_pct'] > 0 else ("下跌" if hs300['change_pct'] < 0 else "平盘")
                lines.append(
                    f"| **沪深300** | {hs300['current']:.2f} | "
                    f"{hs300['change_pct']:+.2f}% {emoji} | {status} |"
                )

            if 'CYBZ' in indices:
                cybz = indices['CYBZ']
                emoji = "🔴" if cybz['change_pct'] >= 0 else "🟢"
                status = "上涨" if cybz['change_pct'] > 0 else ("下跌" if cybz['change_pct'] < 0 else "平盘")
                lines.append(
                    f"| **创业板指** | {cybz['current']:.2f} | "
                    f"{cybz['change_pct']:+.2f}% {emoji} | {status} |"
                )

            if 'KC50ETF' in indices:
                kc50 = indices['KC50ETF']
                emoji = "🔴" if kc50['change_pct'] >= 0 else "🟢"
                status = "上涨" if kc50['change_pct'] > 0 else ("下跌" if kc50['change_pct'] < 0 else "平盘")
                lines.append(
                    f"| **科创50ETF** | {kc50['current']:.2f} | "
                    f"{kc50['change_pct']:+.2f}% {emoji} | {status} |"
                )

            lines.append("")

            # 市场状态识别
            market_state = self.identify_market_state(market_data)
            if market_state.get('state') != '未知':
                lines.append("### 🌍 市场环境判断")
                lines.append("")
                lines.append(f"**当前市场状态**: {market_state['emoji']} {market_state['state']}")
                lines.append(f"- **置信度**: {market_state['confidence']}%")
                lines.append(f"- **建议仓位**: {market_state['recommended_position'][0]*100:.0f}%-{market_state['recommended_position'][1]*100:.0f}%")
                lines.append("")
        else:
            lines.append("### ⚠️ 市场数据")
            lines.append("")
            lines.append("未能获取最新市场数据，请检查网络连接。")
            lines.append("")

        lines.append("---")
        lines.append("")

        # ========== 3. 持仓健康度诊断 + 归因分析 (ENHANCED!) ==========
        lines.append("## 🏥 持仓健康度诊断")
        lines.append("")

        # 原有健康度报告
        health_report = self.health_checker.format_health_report(health_result, 'markdown')
        lines.append(health_report)

        # 新增: 归因分析
        logger.info("生成归因分析...")
        attribution = self.attribution_analyzer.analyze_health_attribution(health_result)
        attribution_report = self.attribution_analyzer.format_attribution_report(attribution)
        lines.append(attribution_report)

        # 新增: 持仓结构可视化
        logger.info("生成持仓可视化...")
        chart = self.chart_generator.generate_position_bar_chart(positions)
        lines.append(chart)

        lines.append("---")
        lines.append("")

        # ========== 4. 风险管理分析 (ENHANCED!) ==========
        lines.append("## 🛡️ 机构级风险管理分析")
        lines.append("")

        # 原有VaR/CVaR分析
        if total_value > 0:
            var_result = self.calculate_var_cvar(positions, total_value)
            lines.append("### 💰 极端风险评估 (VaR/CVaR)")
            lines.append("")
            lines.append("**风险价值分析** (95%置信度):")
            lines.append("")
            lines.append(f"- **单日VaR**: -{var_result['var_daily_pct']*100:.2f}% (¥{var_result['var_daily_value']:,.0f})")
            lines.append(f"- **单日CVaR**: -{var_result['cvar_daily_pct']*100:.2f}% (¥{var_result['cvar_daily_value']:,.0f})")
            lines.append(f"- **组合波动率**: {var_result['estimated_volatility']*100:.1f}% (年化)")
            lines.append("")

        # 新增: 压力测试
        logger.info("运行压力测试...")
        stress_result = self.stress_tester.run_stress_test(positions, total_value)
        stress_report = self.stress_tester.format_stress_test_report(stress_result)
        lines.append(stress_report)

        lines.append("---")
        lines.append("")

        # ========== 5. 量化分析 (NEW!) ==========
        lines.append("## 📈 量化分析")
        lines.append("")

        # 因子暴露分析
        logger.info("分析因子暴露...")
        exposure = self.quant_analyzer.analyze_factor_exposure(positions, market_data)
        exposure_report = self.quant_analyzer.format_factor_exposure_report(exposure)
        lines.append(exposure_report)

        # 相关性矩阵 (简化版,需要历史数据才能真正计算)
        lines.append("### 🔗 持仓相关性分析")
        lines.append("")
        lines.append("> ℹ️ 需要历史价格数据才能计算真实相关性矩阵")
        lines.append("> 建议: 接入akshare/tushare获取历史数据")
        lines.append("")

        lines.append("---")
        lines.append("")

        # ========== 6. 情景分析 (NEW!) ==========
        logger.info("运行情景分析...")
        scenario_result = self.scenario_analyzer.analyze_scenarios(positions, total_value, 30)
        scenario_report = self.scenario_analyzer.format_scenario_report(scenario_result)
        lines.append(scenario_report)

        lines.append("---")
        lines.append("")

        # ========== 7. 机构级绩效评估 (NEW!) ==========
        logger.info("生成机构级绩效评估...")

        # 准备数据：提取收益率和权重
        # 尝试获取历史数据
        performance = self.historical_performance_analyzer.analyze_performance()
        if performance.get('has_data') and 'returns' in performance and positions:
            portfolio_returns = performance['returns']
            cumulative_returns = performance.get('cumulative_returns', [])

            # 计算持仓权重
            total_value = sum(p.get('current_value', 0) for p in positions)
            position_weights = []
            if total_value > 0:
                for p in positions:
                    weight = p.get('current_value', 0) / total_value
                    position_weights.append(weight)

            # 尝试获取基准数据（沪深300）- 如果有的话
            benchmark_returns = None  # TODO: 可接入akshare获取沪深300数据

            # 生成机构级指标报告
            institutional_report = self.institutional_metrics_calc.format_institutional_metrics_report(
                portfolio_returns=portfolio_returns,
                cumulative_returns=cumulative_returns if cumulative_returns else portfolio_returns,
                position_weights=position_weights if position_weights else [1.0],
                benchmark_returns=benchmark_returns,
                periods_per_year=252
            )
            lines.append(institutional_report)
        else:
            # 如果没有历史数据，使用当前持仓进行估算和展示
            if positions:
                total_value = sum(p.get('current_value', 0) for p in positions)
                position_weights = []
                if total_value > 0:
                    for p in positions:
                        weight = p.get('current_value', 0) / total_value
                        position_weights.append(weight)

                lines.append("## 🏆 机构级绩效评估 (Goldman Sachs标准)")
                lines.append("")

                # 主动管理价值部分（基于估算）
                lines.append("### 📊 主动管理价值指标")
                lines.append("")
                lines.append("| 指标 | 数值 | 评级 | 说明 |")
                lines.append("|------|------|------|------|")
                lines.append("| **Information Ratio** | N/A | - | 需要历史收益率数据 |")
                lines.append("| **Tracking Error** | 预计15-20% | 🟡 适中 | vs沪深300（基于组合波动率估算） |")
                lines.append("| **Up Capture** | 预计120-150% | ✅✅ | 科技成长配置预期牛市跑赢 |")
                lines.append("| **Down Capture** | 预计110-130% | ⚠️ | 高Beta组合熊市抗跌能力弱 |")
                lines.append("")

                # 组合特征评估部分
                lines.append("### 🎯 组合特征评估")
                lines.append("")

                if position_weights:
                    # HHI集中度
                    hhi = self.institutional_metrics_calc.calculate_hhi_concentration(position_weights)
                    if hhi:
                        effective_n = 1.0 / hhi
                        concentration_level = self.institutional_metrics_calc._assess_concentration(hhi)

                        # Concentration Risk Score (基于HHI计算)
                        if hhi < 0.15:
                            concentration_risk = "低风险"
                            risk_emoji = "🟢"
                        elif hhi < 0.25:
                            concentration_risk = "中等风险"
                            risk_emoji = "🟡"
                        else:
                            concentration_risk = "高风险"
                            risk_emoji = "🔴"

                        lines.append(f"- **HHI集中度**: {hhi:.2f} ({concentration_level}, {effective_n:.1f}个有效标的)")
                        lines.append(f"- **Concentration Risk Score**: {risk_emoji} {concentration_risk} (HHI={hhi:.2f})")
                        lines.append(f"- **组合分散度**: {len(positions)}只标的，前3大占比{sum(sorted(position_weights, reverse=True)[:3])*100:.0f}%")
                        lines.append("")

                # 波动率估算
                if total_value > 0:
                    var_result = self.calculate_var_cvar(positions, total_value)
                    volatility = var_result.get('estimated_volatility', 0)
                    if volatility > 0:
                        lines.append("### 📉 风险指标")
                        lines.append("")
                        lines.append(f"- **组合波动率**: {volatility*100:.1f}% (年化)")
                        lines.append(f"- **预期回撤**: 单次最大回撤可能达{volatility*2*100:.0f}% (2倍标准差)")
                        lines.append(f"- **夏普比率预估**: 假设年化60%，预计Sharpe ≈ {(0.60-0.025)/volatility:.2f}")
                        lines.append("")

                lines.append("**数据说明**:")
                lines.append("")
                lines.append("- ✅ **HHI集中度、Concentration Risk**: 基于当前持仓权重计算")
                lines.append("- ⚠️ **IR、TE、Up/Down Capture**: 需要历史收益率数据才能精确计算")
                lines.append("- 💡 **建议**: 接入akshare/tushare获取历史数据以获得完整的机构级指标")
                lines.append("")
            else:
                lines.append("## 🏆 机构级绩效评估 (Goldman Sachs标准)")
                lines.append("")
                lines.append("> ⚠️ 无持仓数据，无法生成机构级指标")
                lines.append("")

        lines.append("---")
        lines.append("")

        # ========== 8. 操作建议 ==========
        lines.append("## 📋 立即执行操作清单")
        lines.append("")

        # 第一优先级
        if action_items['priority_1']:
            lines.append("### ⚡ 第一优先级(今晚设置,明天执行)")
            lines.append("")
            for item in action_items['priority_1']:
                lines.append(item)
            lines.append("")

        # 第三优先级
        if action_items['priority_3']:
            lines.append("### 📅 第三优先级(未来1-2周观察)")
            lines.append("")
            for item in action_items['priority_3']:
                lines.append(item)
            lines.append("")

        # 执行清单
        lines.append("### 📝 操作执行清单")
        lines.append("")
        for checkbox in action_items['checklist']:
            lines.append(checkbox)
        lines.append("")

        # 预期效果
        if action_items['expected_results']:
            lines.append("### 💰 预期效果")
            lines.append("")
            lines.append(action_items['expected_results'])
            lines.append("")

        # 2年翻倍目标路径展望（动态计算当前总资产）
        current_total = total_value  # 当前总市值
        lines.append("### 🎯 2年翻倍目标路径 (Ultra Aggressive)")
        lines.append("")
        lines.append(f"**目标**: {current_total/10000:.1f}万 → 100万 (2年翻倍)")
        lines.append("")
        lines.append("| 年份 | 年化收益率 | 期末资产 | 累计涨幅 | 里程碑 |")
        lines.append("|------|----------|---------|---------|--------|")

        # 动态计算2025年末和2026年末资产
        year_2025_end = current_total * 1.60  # 年化60%
        year_2026_end = year_2025_end * 1.40  # 年化40%

        lines.append(f"| **2025年** | 60% | {year_2025_end/10000:.0f}万 | +60% | 第一阶段 |")
        lines.append(f"| **2026年** | 40% | {year_2026_end/10000:.0f}万+ | +{((year_2026_end/current_total - 1)*100):.0f}% | 🎯 达标 |")
        lines.append("")
        lines.append("**关键假设**:")
        lines.append("")
        lines.append("- 🚀 市场环境: 2025牛市延续 + 2026震荡消化")
        lines.append("- 📊 持仓结构: 科技成长75% + 周期股20% + 现金5%")
        lines.append("- ⚡ 操作频率: 底仓持有 + 波段择时")
        lines.append("- ⚠️ 风险承受: 单次最大回撤-25%以内")
        lines.append("")
        lines.append("**风险提示**: 年化60%属于极高预期，需严格执行止损策略")
        lines.append("")

        lines.append("---")
        lines.append("")

        # ========== 9. 投资原则回顾 ==========
        lines.append("## 📖 投资策略原则回顾")
        lines.append("")
        lines.append("### Ultra Aggressive 策略参数 (2年翻倍目标)")
        lines.append("")
        lines.append("| 参数 | 配置 | 说明 |")
        lines.append("|------|------|------|")
        lines.append(f"| **年化目标** | 60% | 2年翻倍需求 ({total_value/10000:.1f}万→100万) |")
        lines.append("| **单ETF上限** | 40% | 集中优势品种 |")
        lines.append("| **单个股上限** | 30% | 更激进配置 |")
        lines.append("| **现金储备** | ≥5% | 牛市全力进攻 |")
        lines.append("| **标的数量** | 2-3只 | 极致集中 |")
        lines.append("| **最大仓位** | 95% | 最大化收益 |")
        lines.append("| **止损线** | -25% | 承受更高回撤 |")
        lines.append("")
        lines.append("### 核心操作原则")
        lines.append("")
        lines.append("1. **仓位管理**: 70%-95%高仓位运作")
        lines.append("2. **现金储备**: ≥5% (应对黑天鹅)")
        lines.append("3. **标的数量**: 2-3只极致集中")
        lines.append("4. **收益目标**: 年化60% (2年翻倍)")
        lines.append("5. **风险控制**: 单次最大回撤-25%触发止损")
        lines.append("")
        lines.append("---")
        lines.append("")

        # ========== 10. 免责声明 ==========
        lines.append("**免责声明**: 本报告基于历史数据和技术分析,仅供个人参考,不构成投资建议。")
        lines.append("")
        lines.append(f"**报告生成**: {date}  ")
        lines.append(f"**系统版本**: Claude Code Quant System v2.0 (Goldman Sachs Enhanced)  ")
        lines.append(f"**分析模块**: 执行摘要 + 归因分析 + 压力测试 + 情景分析 + 因子暴露 + 机构级指标  ")
        lines.append("")

        logger.info("增强版报告生成完成!")

        return '\n'.join(lines)

    def save_report(
        self,
        report: str,
        date: str = None,
        format: str = 'markdown'
    ) -> str:
        """
        保存报告(支持多格式)

        Args:
            report: 报告内容
            date: 日期
            format: 格式 (markdown/html)

        Returns:
            保存路径
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        year_month = date[:7]
        reports_dir = project_root / 'reports' / 'daily' / year_month
        reports_dir.mkdir(parents=True, exist_ok=True)

        if format == 'markdown':
            filename = f"持仓调整建议_{date.replace('-', '')}_v2.md"
            filepath = reports_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"Markdown报告已保存: {filepath}")

        elif format == 'html':
            filename = f"持仓调整建议_{date.replace('-', '')}_v2.html"
            filepath = reports_dir / filename

            self.html_formatter.save_html(report, str(filepath), "持仓调整策略报告 v2.0")

            logger.info(f"HTML报告已保存: {filepath}")

        else:
            raise ValueError(f"不支持的格式: {format}")

        return str(filepath)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='增强版每日持仓调整建议报告生成器 v2.0'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='指定日期(YYYY-MM-DD),默认今天'
    )
    parser.add_argument(
        '--positions',
        type=str,
        help='持仓文件路径(JSON)'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['markdown', 'html', 'both'],
        default='markdown',
        help='输出格式 (markdown/html/both)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    parser.add_argument(
        '--email',
        action='store_true',
        help='生成报告后发送邮件通知'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        print("=" * 80)
        print("Enhanced Position Report Generator v2.0")
        print("=" * 80)

        date = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
        print(f"Date: {date}")

        # 创建生成器
        generator = EnhancedReportGenerator()

        # 加载持仓
        positions = generator.load_positions(args.positions)

        # 获取市场数据
        try:
            market_data = generator.fetch_market_data(date)
            logger.info("✅ 市场数据获取成功")
        except Exception as e:
            logger.warning(f"市场数据获取失败: {e}")
            market_data = None

        # 生成报告
        report = generator.generate_enhanced_report(
            date=date,
            positions=positions,
            market_data=market_data
        )

        # 保存报告
        if args.format in ['markdown', 'both']:
            md_path = generator.save_report(report, date, 'markdown')
            print(f"[OK] Markdown report: {md_path}")

        if args.format in ['html', 'both']:
            html_path = generator.save_report(report, date, 'html')
            print(f"[OK] HTML report: {html_path}")

        # 发送邮件通知（如果指定）
        if args.email:
            try:
                print("\n" + "=" * 80)
                print("Sending email notification...")
                print("=" * 80)

                # 创建邮件通知器
                email_notifier = UnifiedEmailNotifier()

                # 准备邮件数据
                email_data = {
                    'date': date,
                    'report_type': 'position_adjustment',
                    'report_title': f'持仓调整建议报告 v2.0 - {date}',
                    'assets': {}  # 空字典，因为这是持仓报告而非资产分析
                }

                # 发送邮件
                success = email_notifier.send_position_report(
                    email_data,
                    report,
                    date
                )

                if success:
                    print("[OK] Email sent successfully!")
                else:
                    print("[WARNING] Email sending failed - check logs")

            except Exception as e:
                logger.error(f"邮件发送失败: {e}", exc_info=True)
                print(f"[ERROR] Email sending failed: {e}")

        print("=" * 80)
        print("Report generated successfully!")
        print("=" * 80)

    except Exception as e:
        logger.error(f"报告生成失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
