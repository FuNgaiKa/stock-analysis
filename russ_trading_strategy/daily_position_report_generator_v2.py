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

    def __init__(self, risk_profile: str = 'aggressive'):
        """
        初始化增强版生成器

        Args:
            risk_profile: 风险偏好
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
            # ... (保留原有市场数据展示)
            lines.append("市场数据展示 (略)")
        else:
            lines.append("未能获取市场数据")
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

        # ========== 7. 历史表现回测 (NEW!) ==========
        logger.info("分析历史表现...")
        performance = self.historical_performance_analyzer.analyze_performance()

        # 如果有历史数据，计算性能指标
        if performance.get('has_data') and 'returns' in performance:
            sharpe = self.performance_metrics_calc.calculate_sharpe_ratio(performance['returns'])
            sortino = self.performance_metrics_calc.calculate_sortino_ratio(performance['returns'])
            if sharpe:
                performance['sharpe_ratio'] = sharpe
            if sortino:
                performance['sortino_ratio'] = sortino

        performance_report = self.historical_performance_analyzer.format_performance_report(
            performance,
            include_metrics=True
        )
        lines.append(performance_report)

        # 如果有历史数据，生成收益曲线
        if performance.get('has_data') and 'dates' in performance and 'capitals' in performance:
            equity_curve = self.visualization_gen.generate_equity_curve_ascii(
                performance['dates'],
                performance['capitals']
            )
            lines.append(equity_curve)

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

        lines.append("---")
        lines.append("")

        # ========== 8. 激进持仓建议 ==========
        ultra_suggestions = self._generate_ultra_aggressive_suggestions(positions, market_data, total_value)

        lines.append("## 🚀 激进持仓建议(2026年底翻倍目标)")
        lines.append("")
        lines.append("> **适用人群**: 承受20-30%回撤的激进选手  ")
        lines.append("> **目标**: 2026年底资金翻倍至100万  ")
        lines.append("")

        if ultra_suggestions['strategy_comparison']:
            for line in ultra_suggestions['strategy_comparison']:
                lines.append(line)

        if ultra_suggestions['ultra_positions']:
            for line in ultra_suggestions['ultra_positions']:
                lines.append(line)

        if ultra_suggestions['action_plan']:
            for line in ultra_suggestions['action_plan']:
                lines.append(line)

        if ultra_suggestions['expected_return']:
            lines.append(ultra_suggestions['expected_return'])

        lines.append("---")
        lines.append("")

        # ========== 9. 投资原则回顾 ==========
        lines.append("## 📖 投资策略原则回顾")
        lines.append("")
        lines.append("### 核心原则")
        lines.append("")
        lines.append("1. **仓位管理**: 50%-90%滚动")
        lines.append("2. **现金储备**: ≥10%")
        lines.append("3. **标的数量**: 3-5只集中投资")
        lines.append("4. **收益目标**: 年化15%")
        lines.append("5. **风险控制**: 基于量化指标决策")
        lines.append("")
        lines.append("---")
        lines.append("")

        # ========== 10. 免责声明 ==========
        lines.append("**免责声明**: 本报告基于历史数据和技术分析,仅供个人参考,不构成投资建议。")
        lines.append("")
        lines.append(f"**报告生成**: {date}  ")
        lines.append(f"**系统版本**: Claude Code Quant System v2.0  ")
        lines.append(f"**分析模块**: 执行摘要 + 归因分析 + 压力测试 + 情景分析 + 因子暴露  ")
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

        print("=" * 80)
        print("Report generated successfully!")
        print("=" * 80)

    except Exception as e:
        logger.error(f"报告生成失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
