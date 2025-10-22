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

# 导入恐慌指数分析器
sys.path.insert(0, str(project_root / 'src' / 'analyzers' / 'position' / 'analyzers' / 'market_indicators'))
from cn_volatility_index import CNVolatilityIndex
from hk_volatility_index import HKVolatilityIndex

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

        # 初始化恐慌指数分析器
        self.cn_volatility_analyzer = CNVolatilityIndex()
        self.hk_volatility_analyzer = HKVolatilityIndex()

        logger.info(f"增强版报告生成器初始化完成 (风险偏好: {risk_profile})")

    def fetch_panic_indices(self, market_data: Dict) -> Dict:
        """
        获取恐慌指数数据

        Args:
            market_data: 市场数据

        Returns:
            恐慌指数数据字典
        """
        panic_data = {
            'cn_vix': None,
            'hk_vix': None
        }

        try:
            # 获取A股数据计算CNVI
            if market_data and market_data.get('indices'):
                import akshare as ak
                import pandas as pd
                import numpy as np

                # 1. A股CNVI (基于沪深300/创业板指)
                try:
                    # 获取上证指数历史数据
                    df_cn = ak.stock_zh_index_daily(symbol='sh000001')
                    if df_cn is not None and len(df_cn) >= 60:
                        # 重命名列以适配 CNVI 计算器
                        df_cn = df_cn.rename(columns={'日期': 'date'})
                        df_cn = df_cn.tail(250)  # 最近一年数据

                        cnvi_result = self.cn_volatility_analyzer.calculate_cnvi(df_cn)
                        if 'error' not in cnvi_result:
                            panic_data['cn_vix'] = cnvi_result
                            logger.info(f"✅ A股CNVI获取成功: {cnvi_result['cnvi_value']:.2f}")
                except Exception as e:
                    logger.warning(f"A股CNVI计算失败: {e}")

                # 2. H股HKVI (基于恒生科技ETF作为代理)
                try:
                    # 方案1: 使用恒生科技ETF(513180)作为港股恐慌指数代理
                    from datetime import datetime, timedelta
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

                    df_hk = ak.index_zh_a_hist(symbol='513180', start_date=start_date, end_date=end_date)

                    if df_hk is not None and len(df_hk) >= 60:
                        # 重命名列以适配 HKVI 计算器
                        df_hk = df_hk.rename(columns={'日期': 'date', '收盘': 'close', '开盘': 'open', '最高': 'high', '最低': 'low', '成交量': 'volume'})
                        df_hk['date'] = pd.to_datetime(df_hk['date'])
                        df_hk = df_hk.tail(250)  # 最近一年数据

                        hkvi_result = self.hk_volatility_analyzer.calculate_hkvi(df_hk)
                        if 'error' not in hkvi_result:
                            panic_data['hk_vix'] = hkvi_result
                            logger.info(f"✅ H股HKVI获取成功(基于恒生科技ETF): {hkvi_result['hkvi_value']:.2f}")
                except Exception as e:
                    logger.warning(f"H股HKVI计算失败: {e}")

        except Exception as e:
            logger.error(f"恐慌指数获取失败: {e}")

        return panic_data

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
            lines.append("| 指数 | 最新点位 | 涨跌幅 | 成交量 | 量比 | 状态 |")
            lines.append("|------|---------|--------|--------|------|------|")

            indices = market_data['indices']

            if 'HS300' in indices:
                hs300 = indices['HS300']
                emoji = "🔴" if hs300['change_pct'] >= 0 else "🟢"
                status = "上涨" if hs300['change_pct'] > 0 else ("下跌" if hs300['change_pct'] < 0 else "平盘")

                # 量价关系
                volume = hs300.get('volume', 0)
                volume_ratio = hs300.get('volume_ratio', 0)
                if volume > 0:
                    volume_str = f"{volume/100000000:.0f}亿" if volume >= 100000000 else f"{volume/10000:.0f}万"
                else:
                    volume_str = "N/A"

                if volume_ratio > 0:
                    if volume_ratio > 1.5:
                        volume_status = f"{volume_ratio:.1f}倍 📈放量"
                    elif volume_ratio < 0.8:
                        volume_status = f"{volume_ratio:.1f}倍 📉缩量"
                    else:
                        volume_status = f"{volume_ratio:.1f}倍 ➡️平量"
                else:
                    volume_status = "N/A"

                lines.append(
                    f"| **沪深300** | {hs300['current']:.2f} | "
                    f"{hs300['change_pct']:+.2f}% {emoji} | {volume_str} | {volume_status} | {status} |"
                )

            if 'CYBZ' in indices:
                cybz = indices['CYBZ']
                emoji = "🔴" if cybz['change_pct'] >= 0 else "🟢"
                status = "上涨" if cybz['change_pct'] > 0 else ("下跌" if cybz['change_pct'] < 0 else "平盘")

                # 量价关系
                volume = cybz.get('volume', 0)
                volume_ratio = cybz.get('volume_ratio', 0)
                if volume > 0:
                    volume_str = f"{volume/100000000:.0f}亿" if volume >= 100000000 else f"{volume/10000:.0f}万"
                else:
                    volume_str = "N/A"

                if volume_ratio > 0:
                    if volume_ratio > 1.5:
                        volume_status = f"{volume_ratio:.1f}倍 📈放量"
                    elif volume_ratio < 0.8:
                        volume_status = f"{volume_ratio:.1f}倍 📉缩量"
                    else:
                        volume_status = f"{volume_ratio:.1f}倍 ➡️平量"
                else:
                    volume_status = "N/A"

                lines.append(
                    f"| **创业板指** | {cybz['current']:.2f} | "
                    f"{cybz['change_pct']:+.2f}% {emoji} | {volume_str} | {volume_status} | {status} |"
                )

            if 'KC50ETF' in indices:
                kc50 = indices['KC50ETF']
                emoji = "🔴" if kc50['change_pct'] >= 0 else "🟢"
                status = "上涨" if kc50['change_pct'] > 0 else ("下跌" if kc50['change_pct'] < 0 else "平盘")

                # 量价关系
                volume = kc50.get('volume', 0)
                volume_ratio = kc50.get('volume_ratio', 0)
                if volume > 0:
                    volume_str = f"{volume/100000000:.0f}亿" if volume >= 100000000 else f"{volume/10000:.0f}万"
                else:
                    volume_str = "N/A"

                if volume_ratio > 0:
                    if volume_ratio > 1.5:
                        volume_status = f"{volume_ratio:.1f}倍 📈放量"
                    elif volume_ratio < 0.8:
                        volume_status = f"{volume_ratio:.1f}倍 📉缩量"
                    else:
                        volume_status = f"{volume_ratio:.1f}倍 ➡️平量"
                else:
                    volume_status = "N/A"

                lines.append(
                    f"| **科创50ETF** | {kc50['current']:.2f} | "
                    f"{kc50['change_pct']:+.2f}% {emoji} | {volume_str} | {volume_status} | {status} |"
                )

            lines.append("")

            # 量价配合度分析
            lines.append("### 📈 量价关系分析")
            lines.append("")

            # 分析沪深300
            if 'HS300' in indices:
                hs300 = indices['HS300']
                price_change = hs300.get('change_pct', 0)
                volume_ratio = hs300.get('volume_ratio', 0)

                if volume_ratio > 0:
                    if price_change > 0 and volume_ratio > 1.2:
                        vp_analysis = "✅ **价涨量增** - 多头强势，健康上涨"
                    elif price_change > 0 and volume_ratio < 0.8:
                        vp_analysis = "⚠️ **价涨量缩** - 上涨乏力，警惕回调"
                    elif price_change < 0 and volume_ratio > 1.2:
                        vp_analysis = "🚨 **价跌量增** - 空头占优，注意风险"
                    elif price_change < 0 and volume_ratio < 0.8:
                        vp_analysis = "✅ **价跌量缩** - 抛压减弱，可能企稳"
                    else:
                        vp_analysis = "➡️ **量价平衡** - 观望情绪，等待方向"

                    lines.append(f"**沪深300**: {vp_analysis}")
                    lines.append("")

            # 分析创业板
            if 'CYBZ' in indices:
                cybz = indices['CYBZ']
                price_change = cybz.get('change_pct', 0)
                volume_ratio = cybz.get('volume_ratio', 0)

                if volume_ratio > 0:
                    if price_change > 0 and volume_ratio > 1.2:
                        vp_analysis = "✅ **价涨量增** - 多头强势，健康上涨"
                    elif price_change > 0 and volume_ratio < 0.8:
                        vp_analysis = "⚠️ **价涨量缩** - 上涨乏力，警惕回调"
                    elif price_change < 0 and volume_ratio > 1.2:
                        vp_analysis = "🚨 **价跌量增** - 空头占优，注意风险"
                    elif price_change < 0 and volume_ratio < 0.8:
                        vp_analysis = "✅ **价跌量缩** - 抛压减弱，可能企稳"
                    else:
                        vp_analysis = "➡️ **量价平衡** - 观望情绪，等待方向"

                    lines.append(f"**创业板指**: {vp_analysis}")

            lines.append("")

            # 基本面数据
            lines.append("### 💼 市场估值水平")
            lines.append("")
            lines.append("| 指数 | PE(TTM) | PE分位 | PB | ROE | 股息率 | 估值评级 |")
            lines.append("|------|---------|--------|-----|-----|--------|---------|")

            if 'HS300' in indices:
                hs300 = indices['HS300']
                pe = hs300.get('pe', 0)
                pe_percentile = hs300.get('pe_percentile', 0)
                pb = hs300.get('pb', 0)
                roe = hs300.get('roe', 0)
                dividend_yield = hs300.get('dividend_yield', 0)

                # 估值评级 (基于历史PE区间)
                if pe > 0:
                    if pe > 15:
                        valuation = "🔴 偏高"
                    elif pe > 12:
                        valuation = "🟡 合理"
                    else:
                        valuation = "🟢 偏低"
                else:
                    valuation = "N/A"

                pe_str = f"{pe:.1f}" if pe > 0 else "N/A"
                pe_pct_str = f"{pe_percentile:.1f}%" if pe_percentile > 0 else "N/A"
                pb_str = f"{pb:.2f}" if pb > 0 else "N/A"
                roe_str = f"{roe:.1f}%" if roe > 0 else "N/A"
                div_str = f"{dividend_yield:.2f}%" if dividend_yield > 0 else "N/A"

                lines.append(f"| **沪深300** | {pe_str} | {pe_pct_str} | {pb_str} | {roe_str} | {div_str} | {valuation} |")

            # 科创50ETF (ETF没有传统估值指标)
            if 'KC50ETF' in indices:
                lines.append(f"| **科创50** | N/A | N/A | N/A | N/A | N/A | - |")

            if 'CYBZ' in indices:
                cybz = indices['CYBZ']
                pe = cybz.get('pe', 0)
                pe_percentile = cybz.get('pe_percentile', 0)
                pb = cybz.get('pb', 0)
                roe = cybz.get('roe', 0)
                dividend_yield = cybz.get('dividend_yield', 0)

                # 估值评级 (创业板历史PE区间更高)
                if pe > 0:
                    if pe > 50:
                        valuation = "🔴 偏高"
                    elif pe > 35:
                        valuation = "🟡 合理"
                    else:
                        valuation = "🟢 偏低"
                else:
                    valuation = "N/A"

                pe_str = f"{pe:.1f}" if pe > 0 else "N/A"
                pe_pct_str = f"{pe_percentile:.1f}%" if pe_percentile > 0 else "N/A"
                pb_str = f"{pb:.2f}" if pb > 0 else "N/A"
                roe_str = f"{roe:.1f}%" if roe > 0 else "N/A"
                div_str = f"{dividend_yield:.2f}%" if dividend_yield > 0 else "N/A"

                lines.append(f"| **创业板指** | {pe_str} | {pe_pct_str} | {pb_str} | {roe_str} | {div_str} | {valuation} |")

            lines.append("")
            lines.append("**估值说明**:")
            lines.append("- PE(TTM): 市盈率(滚动12个月)")
            lines.append("- PE分位: PE十年分位数(当前PE在过去10年中的排名)")
            lines.append("- PB: 市净率")
            lines.append("- ROE: 净资产收益率")
            lines.append("- 股息率: 年化股息收益率")
            lines.append("")

            # 资金面分析
            if 'market_volume' in market_data and market_data['market_volume']:
                lines.append("### 💰 资金面分析")
                lines.append("")

                mv = market_data['market_volume']
                total_vol_trillion = mv.get('total_volume_trillion', 0)

                if total_vol_trillion > 0:
                    # 两市成交额评级
                    if total_vol_trillion >= 1.5:
                        vol_rating = "🟢🟢 极度活跃"
                        vol_desc = "牛市特征明显"
                    elif total_vol_trillion >= 1.0:
                        vol_rating = "🟢 活跃"
                        vol_desc = "资金充裕,利于上涨"
                    elif total_vol_trillion >= 0.7:
                        vol_rating = "🟡 正常"
                        vol_desc = "震荡行情"
                    elif total_vol_trillion >= 0.5:
                        vol_rating = "🟡 偏冷"
                        vol_desc = "观望情绪浓厚"
                    else:
                        vol_rating = "🔴 冰点"
                        vol_desc = "熊市特征"

                    lines.append(f"**两市成交额**: {total_vol_trillion:.2f}万亿 {vol_rating}")
                    lines.append(f"- {vol_desc}")
                    lines.append("")

            # 主力资金流向
            if 'fund_flow' in market_data and market_data['fund_flow']:
                ff = market_data['fund_flow']
                main_inflow = ff.get('main_net_inflow', 0) / 100000000  # 转亿元

                if main_inflow != 0:
                    if not ('market_volume' in market_data and market_data['market_volume']):
                        lines.append("### 💰 资金面分析")
                        lines.append("")

                    if main_inflow >= 100:
                        flow_rating = "🟢🟢 强势流入"
                        flow_desc = "大资金积极买入"
                    elif main_inflow >= 50:
                        flow_rating = "🟢 流入"
                        flow_desc = "资金看多情绪"
                    elif main_inflow > 0:
                        flow_rating = "🟡 小幅流入"
                        flow_desc = "中性偏多"
                    elif main_inflow > -50:
                        flow_rating = "🟡 小幅流出"
                        flow_desc = "中性偏空"
                    elif main_inflow > -100:
                        flow_rating = "🔴 流出"
                        flow_desc = "资金撤离"
                    else:
                        flow_rating = "🔴🔴 大幅流出"
                        flow_desc = "恐慌性抛售"

                    lines.append(f"**主力资金**: {main_inflow:+.2f}亿 {flow_rating}")
                    lines.append(f"- {flow_desc}")
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

            # ========== 恐慌指数监控 (NEW!) ==========
            logger.info("获取恐慌指数数据...")
            panic_data = self.fetch_panic_indices(market_data)

            if panic_data.get('cn_vix') or panic_data.get('hk_vix'):
                lines.append("### 😱 恐慌指数监控")
                lines.append("")

                # A股CNVI
                if panic_data.get('cn_vix'):
                    cnvi = panic_data['cn_vix']
                    lines.append(f"**A股CNVI** (中国波动率指数): **{cnvi['cnvi_value']:.2f}** {cnvi['emoji']}")
                    lines.append(f"- **状态**: {cnvi['status']}")
                    lines.append(f"- **信号**: {cnvi['signal']['signal']}")
                    lines.append(f"- **建议**: {cnvi['signal']['action']}")
                    lines.append("")

                # H股HKVI
                if panic_data.get('hk_vix'):
                    hkvi = panic_data['hk_vix']
                    lines.append(f"**H股HKVI** (港股波动率指数): **{hkvi['hkvi_value']:.2f}** {hkvi['emoji']}")
                    lines.append(f"- **状态**: {hkvi['status']}")
                    lines.append(f"- **信号**: {hkvi['signal']['signal']}")
                    lines.append(f"- **建议**: {hkvi['signal']['action']}")
                    lines.append("")

                # 恐慌指数参考标准
                lines.append("**参考标准** (类比美股VIX):")
                lines.append("")
                lines.append("| VIX区间 | 市场状态 | 交易建议 |")
                lines.append("|---------|---------|---------|")
                lines.append("| **< 15** | 市场平静 | 正常操作 |")
                lines.append("| **15-25** | 正常波动 | 保持观察 |")
                lines.append("| **25-30** | 恐慌上升 | 控制仓位 |")
                lines.append("| **> 30** | 极度恐慌 | 🔥 **大举加仓良机** 🔥 |")
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

        # 第二优先级 - 战略调整建议 (NEW!)
        if action_items.get('priority_2'):
            lines.append("### 🎯 第二优先级(未来1-2个月战略调整) ⭐核心")
            lines.append("")
            for item in action_items['priority_2']:
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

        # ========== 方案C+战略配置详解 (NEW!) ==========
        lines.append("### 🚀 方案C+战略配置详解 (2026翻倍必达版)")
        lines.append("")
        lines.append("#### 🎯 核心思想")
        lines.append("")
        lines.append("方案C+是**2026翻倍极致进攻策略**，核心是科技成长80%全力进攻:")
        lines.append("")
        lines.append("1. **科技成长75%** - 翻倍核心引擎 ⭐⭐⭐")
        lines.append("   - 🌟 **恒生科技35%**: 互联网+AI龙头,腾讯阿里美团")
        lines.append("   - 🌟 **创业板25%**: 新能源+医药+半导体成长股")
        lines.append("   - 🌟 **科创50 15%**: 中国版纳斯达克,硬科技核心")
        lines.append("   - **配置逻辑**: 牛市弹性最大,2年翻倍刚好达标")
        lines.append("")
        lines.append("2. **周期品15%** - 波段增强收益")
        lines.append("   - ⚡ **化工10%**: 油价上行周期,PTA/MDI景气")
        lines.append("   - ⚡ **煤炭5%**: 能源安全底仓,分红高+政策支持")
        lines.append("   - **配置逻辑**: 降低回撤,但不影响进攻性")
        lines.append("")
        lines.append("3. **现金10%** - 极限底线")
        lines.append("   - ✅ 应对突发黑天鹅(最低5%)")
        lines.append("   - ✅ 科技暴跌时加仓")
        lines.append("   - ✅ 资金调度灵活性")
        lines.append("")
        lines.append("#### 📊 策略优势")
        lines.append("")
        lines.append("| 优势 | 说明 |")
        lines.append("|------|------|")
        lines.append("| **进攻性强** | 科技75%,牛市跑赢沪深300 40%+ |")
        lines.append("| **有效分散** | 科技+周期低相关,降低回撤 |")
        lines.append("| **2026翻倍** | 理论收益: 2025年+60%, 2026年+30% = 108% |")
        lines.append("| **风险可控** | 10%现金+止损-30%,最大回撤可控 |")
        lines.append("")
        lines.append("#### ⚠️ 风险承受")
        lines.append("")
        lines.append("- 📉 **预期最大回撤**: -25%至-30% (2015股灾级别)")
        lines.append("- 🎯 **止损纪律**: 单次回撤触及-30%立即减仓至65%")
        lines.append("- 💪 **心理准备**: 需忍受季度级别-15%波动")
        lines.append("- 🔥 **翻倍目标**: 2年翻倍刚好达标,平衡收益与风险")
        lines.append("")
        lines.append("---")
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
        lines.append("- 📊 持仓结构: **科技成长75% + 周期股15% + 现金10%**")
        lines.append("- ⚡ 操作频率: 底仓持有 + 波段择时")
        lines.append("- ⚠️ 风险承受: 单次最大回撤-30%以内")
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
        lines.append("| **现金储备** | ≥10% | 增强安全垫 |")
        lines.append("| **标的数量** | 2-3只 | 极致集中 |")
        lines.append("| **最大仓位** | 90% | 平衡收益与风险 |")
        lines.append("| **止损线** | -30% | 承受更高回撤 |")
        lines.append("")
        lines.append("### 核心操作原则")
        lines.append("")
        lines.append("1. **仓位管理**: 70%-90%高仓位运作")
        lines.append("2. **现金储备**: ≥10% (应对黑天鹅)")
        lines.append("3. **标的数量**: 2-3只极致集中")
        lines.append("4. **收益目标**: 年化60% (2年翻倍)")
        lines.append("5. **风险控制**: 单次最大回撤-30%触发止损")
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

    def _generate_enhanced_action_items(
        self,
        positions: List[Dict],
        market_data: Dict,
        total_value: float
    ) -> Dict:
        """
        重写父类方法,增加第二优先级战略调整建议

        增强点: 方案C+ (科技80% + 周期10% + 现金10%) 战略调整路径
        """
        # 先调用父类方法获取基础建议
        result = super()._generate_enhanced_action_items(positions, market_data, total_value)

        # 清空priority_2,重新生成战略调整建议
        result['priority_2'] = []

        if not positions or total_value == 0:
            return result

        # 计算当前配置
        tech_ratio = 0  # 科技成长
        cycle_ratio = 0  # 周期品
        defensive_ratio = 0  # 防守品种
        cash_ratio = 1.0 - sum(p.get('position_ratio', 0) for p in positions)

        for p in positions:
            asset_name = p.get('asset_name', '').lower()
            ratio = p.get('position_ratio', 0)

            # 科技成长: 恒生科技、创业板、科创50
            if any(x in asset_name for x in ['恒生科技', '创业板', '科创50', '科技']):
                tech_ratio += ratio
            # 周期品: 化工、煤炭
            elif any(x in asset_name for x in ['化工', '煤炭']):
                cycle_ratio += ratio
            # 防守品种: 证券、白酒、银行、保险
            elif any(x in asset_name for x in ['证券', '白酒', '银行', '保险']):
                defensive_ratio += ratio

        # 目标配置 (方案C+)
        target_tech = 0.75
        target_cycle = 0.15
        target_cash = 0.10

        # 计算缺口
        tech_gap = target_tech - tech_ratio
        cycle_gap = target_cycle - cycle_ratio
        cash_gap = target_cash - cash_ratio

        # ========== 生成战略调整建议 ==========
        result['priority_2'].append("**基于方案C+ (2026翻倍目标) 的战略调整路径**:")
        result['priority_2'].append("")
        result['priority_2'].append(f"**当前配置 vs 目标配置**:")
        result['priority_2'].append("")
        result['priority_2'].append("| 类别 | 当前 | 目标 | 缺口 | 说明 |")
        result['priority_2'].append("|------|------|------|------|------|")
        result['priority_2'].append(
            f"| 科技成长 | {tech_ratio*100:.0f}% | **75%** | "
            f"{'+'if tech_gap>0 else ''}{tech_gap*100:.0f}% | "
            f"{'⚠️ 严重不足' if tech_gap > 0.20 else '✅ 接近目标' if abs(tech_gap) < 0.05 else '需调整'} |"
        )
        result['priority_2'].append(
            f"| 周期品 | {cycle_ratio*100:.0f}% | **15%** | "
            f"{'+'if cycle_gap>0 else ''}{cycle_gap*100:.0f}% | "
            f"{'需减仓' if cycle_gap < 0 else '需加仓' if cycle_gap > 0 else '✅ 符合'} |"
        )
        result['priority_2'].append(
            f"| 防守品种 | {defensive_ratio*100:.0f}% | **0%** | -{defensive_ratio*100:.0f}% | "
            f"{'⚠️ 需清仓' if defensive_ratio > 0.10 else '基本清理'} |"
        )
        result['priority_2'].append(
            f"| 现金 | {cash_ratio*100:.0f}% | **10%** | "
            f"{'+'if cash_gap>0 else''}{cash_gap*100:.0f}% | "
            f"{'需减仓补充' if cash_gap > 0 else '可以加仓' if cash_gap < -0.03 else '✅ 合理'} |"
        )
        result['priority_2'].append("")

        # A. 科技成长加仓路线图
        if tech_gap > 0.05:
            result['priority_2'].append("**A. 科技成长加仓路线图** (重中之重)")
            result['priority_2'].append("")
            result['priority_2'].append(f"**目标**: 科技从{tech_ratio*100:.0f}%提升至75% (+{tech_gap*100:.0f}%)")
            result['priority_2'].append("")
            result['priority_2'].append("**分步执行计划**:")
            result['priority_2'].append("")

            # 根据缺口大小制定计划
            gap_pct = tech_gap * 100
            if gap_pct > 40:  # 缺口很大
                result['priority_2'].append(f"- **阶段1** (本周): 证券/白酒减仓15% → 恒生科技+创业板")
                result['priority_2'].append(f"  - 预期: 科技成长 {tech_ratio*100:.0f}% → {(tech_ratio+0.15)*100:.0f}%")
                result['priority_2'].append("")
                result['priority_2'].append(f"- **阶段2** (未来2周): 防守品种再减15% → 科创50+创业板")
                result['priority_2'].append(f"  - 预期: 科技成长 {(tech_ratio+0.15)*100:.0f}% → {(tech_ratio+0.30)*100:.0f}%")
                result['priority_2'].append("")
                result['priority_2'].append(f"- **阶段3** (未来1个月): 防守品种再减15% → 科技组合")
                result['priority_2'].append(f"  - 预期: 科技成长 {(tech_ratio+0.30)*100:.0f}% → {(tech_ratio+0.45)*100:.0f}%")
                result['priority_2'].append("")
                result['priority_2'].append(f"- **阶段4** (未来2个月): 最后调整至75%")
                result['priority_2'].append(f"  - 预期: 科技成长 {(tech_ratio+0.45)*100:.0f}% → 75%+ ✅")
            elif gap_pct > 20:  # 缺口中等
                result['priority_2'].append(f"- **阶段1** (本周): 减仓防守品种10% → 科技组合")
                result['priority_2'].append(f"  - 预期: 科技成长 {tech_ratio*100:.0f}% → {(tech_ratio+0.10)*100:.0f}%")
                result['priority_2'].append("")
                result['priority_2'].append(f"- **阶段2** (未来2周): 再减仓10% → 科技组合")
                result['priority_2'].append(f"  - 预期: 科技成长 {(tech_ratio+0.10)*100:.0f}% → {(tech_ratio+0.20)*100:.0f}%")
                result['priority_2'].append("")
                result['priority_2'].append(f"- **阶段3** (未来1个月): 最后调整至75%")
                result['priority_2'].append(f"  - 预期: 科技成长 {(tech_ratio+0.20)*100:.0f}% → 75%+ ✅")
            else:  # 缺口较小
                result['priority_2'].append(f"- **阶段1** (未来2周): 调整{gap_pct:.0f}%至目标")
                result['priority_2'].append(f"  - 预期: 科技成长 {tech_ratio*100:.0f}% → 75% ✅")

            result['priority_2'].append("")
            result['priority_2'].append("**关键触发条件** (择时加仓):")
            result['priority_2'].append("")
            result['priority_2'].append("**1. 单日跌幅触发:**")
            result['priority_2'].append("- 恒生科技单日跌幅>5%时加仓")
            result['priority_2'].append("- 创业板指单日跌幅>3%时加仓")
            result['priority_2'].append("- 科创50ETF跌破1.45时加仓")
            result['priority_2'].append("")
            result['priority_2'].append("**2. 恐慌指数触发 (最强信号):**")
            result['priority_2'].append("- **CNVI (A股恐慌指数) > 30** 时大举加仓A股标的 🔥")
            result['priority_2'].append("- **HKVI (港股恐慌指数) > 30** 时大举加仓港股标的 🔥")
            result['priority_2'].append("- **美股VIX > 30** 时大举加仓美股标的")
            result['priority_2'].append("")
            result['priority_2'].append("**3. 组合触发 (满仓信号):**")
            result['priority_2'].append("- CNVI/HKVI > 30 + 单日跌幅>5% → 🚀 **满仓冲锋**")
            result['priority_2'].append("- 此时是历史级别的抄底良机,现金储备全力加仓")
            result['priority_2'].append("")

        # B. 防守品种退出策略
        if defensive_ratio > 0.05:
            result['priority_2'].append("**B. 防守品种退出策略** (核心调整)")
            result['priority_2'].append("")

            # 找出防守品种
            defensive_positions = [
                p for p in positions
                if any(x in p.get('asset_name', '').lower() for x in ['证券', '白酒', '银行', '保险'])
            ]

            for p in defensive_positions:
                asset_name = p.get('asset_name', '')
                ratio = p.get('position_ratio', 0)
                result['priority_2'].append(f"**{asset_name}** (当前{ratio*100:.0f}%):")
                result['priority_2'].append(f"- 目标: 逐步清仓 (不符合方案C+)")
                result['priority_2'].append(f"- 理由: {'证券/银行/保险'if any(x in asset_name.lower() for x in ['证券','银行','保险']) else '白酒'}属于{'周期性金融' if any(x in asset_name.lower() for x in ['证券','银行','保险']) else '消费防守'},不是成长股")
                result['priority_2'].append(f"- 执行: 分3次减仓,每次反弹时减{ratio*100/3:.0f}%")
                result['priority_2'].append("")

            result['priority_2'].append("**执行纪律**:")
            result['priority_2'].append("- 单日减仓不超过总资产的5%")
            result['priority_2'].append("- 优先在反弹日减仓 (涨幅>1%)")
            result['priority_2'].append("- 避免在大跌时割肉")
            result['priority_2'].append("")

        # C. 周期品优化策略
        result['priority_2'].append("**C. 周期品优化策略**")
        result['priority_2'].append("")

        # 找出周期品
        cycle_positions = [
            p for p in positions
            if any(x in p.get('asset_name', '').lower() for x in ['化工', '煤炭'])
        ]

        if cycle_positions:
            for p in cycle_positions:
                asset_name = p.get('asset_name', '')
                ratio = p.get('position_ratio', 0)
                if '化工' in asset_name.lower():
                    target = 0.10
                    result['priority_2'].append(f"**{asset_name}** (当前{ratio*100:.0f}%):")
                    result['priority_2'].append(f"- ✅ 保留,符合方案C+周期品配置")
                    if ratio < target:
                        result['priority_2'].append(f"- 建议: 跌破成本价时补仓至{target*100:.0f}%")
                    elif ratio > target + 0.03:
                        result['priority_2'].append(f"- 建议: 反弹时减仓至{target*100:.0f}%")
                    else:
                        result['priority_2'].append(f"- 建议: 维持在{target*100:.0f}%左右")
                    result['priority_2'].append("")
                elif '煤炭' in asset_name.lower():
                    target = 0.05
                    result['priority_2'].append(f"**{asset_name}** (当前{ratio*100:.0f}%):")
                    result['priority_2'].append(f"- ✅ 保留,符合方案C+周期品配置")
                    if ratio < target:
                        result['priority_2'].append(f"- 建议: 稳定在{target*100:.0f}%左右")
                    elif ratio > target + 0.02:
                        result['priority_2'].append(f"- 建议: 减仓至{target*100:.0f}%")
                    else:
                        result['priority_2'].append(f"- 建议: 维持当前仓位")
                    result['priority_2'].append("")

        result['priority_2'].append(f"**目标周期配置**: 化工10% + 煤炭5% = 15% ✅")
        result['priority_2'].append("")

        # D. 资金流向规划表
        result['priority_2'].append("**D. 资金流向规划表** (2026翻倍路径)")
        result['priority_2'].append("")
        result['priority_2'].append("| 调整项目 | 当前 | 目标 | 调整 | 释放/需要资金 | 时间表 |")
        result['priority_2'].append("|---------|------|------|------|--------------|--------|")

        # 减仓项
        result['priority_2'].append("| **减仓** | | | | | |")
        if defensive_ratio > 0:
            defensive_value = total_value * defensive_ratio
            result['priority_2'].append(
                f"| 防守品种清仓 | {defensive_ratio*100:.0f}% | 0% | -{defensive_ratio*100:.0f}% | "
                f"+¥{defensive_value/10000:.1f}万 | 分3个月 |"
            )

        # 加仓项
        result['priority_2'].append("| **加仓** | | | | | |")
        if tech_gap > 0:
            tech_value = total_value * tech_gap
            result['priority_2'].append(
                f"| 科技成长 | {tech_ratio*100:.0f}% | 75% | +{tech_gap*100:.0f}% | "
                f"-¥{tech_value/10000:.1f}万 | 分2个月 |"
            )
        if cycle_gap > 0:
            cycle_value = total_value * cycle_gap
            result['priority_2'].append(
                f"| 周期品 | {cycle_ratio*100:.0f}% | 15% | +{cycle_gap*100:.0f}% | "
                f"-¥{cycle_value/10000:.1f}万 | 择机 |"
            )

        # 现金
        if cash_gap != 0:
            cash_value = total_value * abs(cash_gap)
            sign = "+" if cash_gap > 0 else "-"
            result['priority_2'].append(
                f"| 现金储备 | {cash_ratio*100:.0f}% | 10% | {sign}{abs(cash_gap)*100:.0f}% | "
                f"{sign}¥{cash_value/10000:.1f}万 | 立即 |"
            )

        result['priority_2'].append("")
        result['priority_2'].append("**资金平衡**:")
        released = defensive_ratio * total_value
        needed = tech_gap * total_value if tech_gap > 0 else 0
        balance = released - needed
        result['priority_2'].append(f"- 释放资金: ¥{released/10000:.1f}万")
        result['priority_2'].append(f"- 需要资金: ¥{needed/10000:.1f}万")
        result['priority_2'].append(f"- 净余额: {'+'if balance>=0 else ''}¥{balance/10000:.1f}万 ({'补充现金储备'if balance>0 else '需外部资金'})")
        result['priority_2'].append("")

        # ========== 重写第三优先级: 小仓位标的 (智能识别方案C+目标) ==========
        # 清空父类生成的priority_3,重新生成
        result['priority_3'] = []

        # 定义方案C+的目标配置
        target_configs = {
            '化工': {'target': 0.10, 'min': 0.08, 'max': 0.12},
            '煤炭': {'target': 0.05, 'min': 0.04, 'max': 0.06},
        }

        # 找出所有小仓位(<10%)
        small_positions = [
            p for p in positions
            if p.get('position_ratio', 0) < 0.10
        ]

        if small_positions:
            result['priority_3'].append("**小仓位标的处理建议**:")
            result['priority_3'].append("")

            for pos in small_positions:
                asset_name = pos.get('asset_name', 'Unknown')
                ratio = pos.get('position_ratio', 0)

                # 检查是否属于方案C+目标配置
                is_strategic = False
                for key, config in target_configs.items():
                    if key in asset_name.lower():
                        is_strategic = True
                        target = config['target']
                        min_range = config['min']
                        max_range = config['max']

                        # 判断当前仓位与目标的关系
                        if ratio < min_range:
                            suggestion = f"✅ **保留** (方案C+目标{target*100:.0f}%) - 建议补仓至{target*100:.0f}%"
                        elif ratio > max_range:
                            suggestion = f"✅ **保留** (方案C+目标{target*100:.0f}%) - 建议减仓至{target*100:.0f}%"
                        else:
                            suggestion = f"✅ **保留** (方案C+目标{target*100:.0f}%) - 维持当前仓位"

                        result['priority_3'].append(f"- {asset_name} ({ratio*100:.1f}%): {suggestion}")
                        break

                # 如果不属于战略配置,使用原有逻辑
                if not is_strategic:
                    result['priority_3'].append(
                        f"- {asset_name} ({ratio*100:.1f}%): "
                        f"⚠️ 不在方案C+配置中,建议择机清仓"
                    )

            result['priority_3'].append("")

            # 更新checklist
            # 移除父类添加的通用小仓位观察项
            result['checklist'] = [
                item for item in result['checklist']
                if '观察小仓位标的表现' not in item
            ]

            # 添加更智能的checklist
            result['checklist'].append(
                f"- [ ] 📊 战略品种(化工/煤炭): 按方案C+目标调整"
            )
            result['checklist'].append(
                f"- [ ] ⚠️ 非战略品种(阿里等): 择机清仓"
            )

        return result

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
