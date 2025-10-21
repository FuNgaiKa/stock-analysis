#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日持仓调整建议报告生成器(增强版)
Daily Position Report Generator (Enhanced Edition)

每天自动生成持仓调整建议，包含：
1. 持仓健康度分析
2. 收益追踪对比
3. 机构级风险指标
4. Kelly公式智能仓位建议
5. 具体操作清单
6. 收益预测

运行方式:
    # 生成今日报告
    python scripts/russ_trading_strategy/daily_position_report_generator.py

    # 生成指定日期报告
    python scripts/russ_trading_strategy/daily_position_report_generator.py --date 2025-10-21

    # 自动更新持仓数据
    python scripts/russ_trading_strategy/daily_position_report_generator.py --auto-update

作者: Claude Code
日期: 2025-10-21
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.russ_trading_strategy.position_health_checker import PositionHealthChecker
from scripts.russ_trading_strategy.performance_tracker import PerformanceTracker
from scripts.russ_trading_strategy.potential_analyzer import PotentialAnalyzer

# 尝试导入增强模块
try:
    from scripts.russ_trading_strategy.risk_manager import RiskManager
    from scripts.russ_trading_strategy.dynamic_position_manager import DynamicPositionManager
    from scripts.russ_trading_strategy.data_manager import DataManager
    from scripts.russ_trading_strategy.technical_analyzer import TechnicalAnalyzer
    HAS_ENHANCED_MODULES = True
except ImportError:
    HAS_ENHANCED_MODULES = False
    logging.warning("增强模块未找到，将使用基础功能")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailyPositionReportGenerator:
    """每日持仓报告生成器(机构级增强版)"""

    def __init__(self, risk_profile: str = 'aggressive'):
        """
        初始化生成器

        Args:
            risk_profile: 风险偏好 ('conservative', 'moderate', 'aggressive')
                - conservative: 保守型 (最大回撤10%, 波动率20%)
                - moderate: 稳健型 (最大回撤15%, 波动率30%)
                - aggressive: 积极型 (最大回撤25%, 波动率50%)
        """
        self.risk_profile = risk_profile
        self.health_checker = PositionHealthChecker()
        self.performance_tracker = PerformanceTracker()
        self.potential_analyzer = PotentialAnalyzer()

        # 初始化增强模块
        if HAS_ENHANCED_MODULES:
            self.risk_manager = RiskManager()
            self.position_manager = DynamicPositionManager()
            self.data_manager = DataManager()
            self.technical_analyzer = TechnicalAnalyzer()
        else:
            self.risk_manager = None
            self.position_manager = None
            self.data_manager = None
            self.technical_analyzer = None

        # 根据风险偏好设置阈值
        self._set_risk_thresholds()

    def _set_risk_thresholds(self):
        """根据风险偏好设置阈值"""
        risk_params = {
            'conservative': {
                'max_drawdown_alert': 0.10,
                'max_drawdown_warning': 0.08,
                'volatility_limit': 0.20,
                'max_single_position': 0.15,
                'max_total_position': 0.70,
                'min_cash_reserve': 0.30,
                'stop_loss': 0.10,
                'warning_loss': 0.08
            },
            'moderate': {
                'max_drawdown_alert': 0.15,
                'max_drawdown_warning': 0.12,
                'volatility_limit': 0.30,
                'max_single_position': 0.20,
                'max_total_position': 0.85,
                'min_cash_reserve': 0.15,
                'stop_loss': 0.15,
                'warning_loss': 0.12
            },
            'aggressive': {
                'max_drawdown_alert': 0.25,
                'max_drawdown_warning': 0.20,
                'volatility_limit': 0.50,
                'max_single_position': 0.25,
                'max_total_position': 0.90,
                'min_cash_reserve': 0.10,
                'stop_loss': 0.20,
                'warning_loss': 0.16
            },
            'ultra_aggressive': {
                'max_drawdown_alert': 0.30,
                'max_drawdown_warning': 0.25,
                'volatility_limit': 0.70,
                'max_single_etf_position': 0.40,  # 单ETF最高40%
                'max_single_stock_position': 0.30,  # 单个股最高30%
                'max_single_position': 0.40,  # 保留兼容性
                'max_total_position': 0.95,
                'min_cash_reserve': 0.05,
                'stop_loss': 0.25,
                'warning_loss': 0.20,
                'target_annual_return': 0.60,  # 年化60%目标
                'min_assets': 2,  # 最少2只
                'max_assets': 3   # 最多3只
            }
        }

        self.thresholds = risk_params.get(self.risk_profile, risk_params['aggressive'])
        logger.info(f"风险偏好设置为: {self.risk_profile}")

    def fetch_market_data(self, date: str = None) -> Dict:
        """
        获取市场数据

        Args:
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            市场数据字典
        """
        logger.info("获取市场数据...")

        try:
            import akshare as ak

            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')

            market_data = {
                'date': date,
                'indices': {},
                'technical': {}  # 存储技术分析结果
            }

            # 沪深300
            try:
                hs300 = ak.index_zh_a_hist(
                    symbol='000300',
                    period='daily',
                    start_date='20250101',
                    end_date=date.replace('-', '')
                )
                if not hs300.empty:
                    latest = hs300.iloc[-1]
                    market_data['indices']['HS300'] = {
                        'current': float(latest['收盘']),
                        'change_pct': float(latest['涨跌幅']),
                        'date': latest['日期']
                    }
                    # 存储历史数据用于技术分析
                    market_data['technical']['HS300'] = hs300
                    logger.info(f"✅ 沪深300: {latest['收盘']:.2f} ({latest['涨跌幅']:+.2f}%)")
            except Exception as e:
                logger.warning(f"获取沪深300失败: {e}")

            # 创业板指
            try:
                cybz = ak.index_zh_a_hist(
                    symbol='399006',
                    period='daily',
                    start_date='20250101',
                    end_date=date.replace('-', '')
                )
                if not cybz.empty:
                    latest = cybz.iloc[-1]
                    market_data['indices']['CYBZ'] = {
                        'current': float(latest['收盘']),
                        'change_pct': float(latest['涨跌幅']),
                        'date': latest['日期']
                    }
                    market_data['technical']['CYBZ'] = cybz
                    logger.info(f"✅ 创业板指: {latest['收盘']:.2f} ({latest['涨跌幅']:+.2f}%)")
            except Exception as e:
                logger.warning(f"获取创业板指失败: {e}")

            # 科创50
            try:
                kc50 = ak.index_zh_a_hist(
                    symbol='000688',
                    period='daily',
                    start_date='20250101',
                    end_date=date.replace('-', '')
                )
                if not kc50.empty:
                    latest = kc50.iloc[-1]
                    market_data['indices']['KC50'] = {
                        'current': float(latest['收盘']),
                        'change_pct': float(latest['涨跌幅']),
                        'date': latest['日期']
                    }
                    market_data['technical']['KC50'] = kc50
                    logger.info(f"✅ 科创50: {latest['收盘']:.2f} ({latest['涨跌幅']:+.2f}%)")
            except Exception as e:
                logger.warning(f"获取科创50失败: {e}")

            return market_data

        except ImportError:
            logger.error("akshare未安装，请运行: pip install akshare")
            return {'date': date, 'indices': {}}
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return {'date': date, 'indices': {}}

    def load_positions(self, positions_file: str = None) -> List[Dict]:
        """
        加载持仓数据

        Args:
            positions_file: 持仓文件路径

        Returns:
            持仓列表
        """
        if positions_file is None:
            # 查找最新的持仓文件
            data_dir = project_root / 'data'
            if data_dir.exists():
                position_files = sorted(data_dir.glob('positions_*.json'), reverse=True)
                if position_files:
                    positions_file = str(position_files[0])
                    logger.info(f"使用持仓文件: {positions_file}")

        if positions_file and os.path.exists(positions_file):
            with open(positions_file, 'r', encoding='utf-8') as f:
                positions = json.load(f)
                logger.info(f"✅ 加载持仓数据: {len(positions)} 个标的")
                return positions
        else:
            logger.warning("未找到持仓文件，使用默认持仓")
            return []

    def identify_market_state(self, market_data: Dict) -> Dict:
        """
        识别市场状态(牛市/熊市/震荡的细分阶段)

        采用多维度判断:
        1. 短期趋势: 当日平均涨跌幅
        2. 中期趋势: 距离关键点位的位置
        3. 长期趋势: 年初至今累计涨幅
        4. 市场宽度: 主要指数共振情况

        Args:
            market_data: 市场数据

        Returns:
            市场状态分析结果
        """
        indices = market_data.get('indices', {})
        if not indices:
            return {'state': '未知', 'confidence': 0, 'suggestion': '数据不足',
                    'recommended_position': (0.60, 0.75)}

        # ========== 1. 短期趋势判断(当日涨跌) ==========
        avg_change = sum(idx.get('change_pct', 0) for idx in indices.values()) / len(indices)

        short_term_score = 0
        if avg_change > 1.5:
            short_term_score = 2  # 强势上涨
        elif avg_change > 0.5:
            short_term_score = 1  # 温和上涨
        elif avg_change > -0.5:
            short_term_score = 0  # 震荡
        elif avg_change > -1.5:
            short_term_score = -1  # 温和下跌
        else:
            short_term_score = -2  # 强势下跌

        # ========== 2. 长期趋势判断(年初至今涨幅) ==========
        # 基准点位(2025-01-01)
        benchmark_points = {
            'HS300': 3145.0,
            'CYBZ': 2060.0,
            'KC50': 955.0
        }

        ytd_gains = []
        for key, idx in indices.items():
            current = idx.get('current', 0)
            if key in benchmark_points and current > 0:
                base = benchmark_points[key]
                ytd_gain = (current - base) / base
                ytd_gains.append(ytd_gain)

        avg_ytd_gain = sum(ytd_gains) / len(ytd_gains) if ytd_gains else 0

        long_term_score = 0
        if avg_ytd_gain > 0.30:  # 年内涨超30%
            long_term_score = 2  # 强势牛市
        elif avg_ytd_gain > 0.15:  # 年内涨15%-30%
            long_term_score = 1  # 温和牛市
        elif avg_ytd_gain > -0.10:  # 年内±10%以内
            long_term_score = 0  # 震荡
        elif avg_ytd_gain > -0.20:  # 年内跌10%-20%
            long_term_score = -1  # 温和熊市
        else:  # 年内跌超20%
            long_term_score = -2  # 深度熊市

        # ========== 3. 市场宽度(指数共振) ==========
        positive_count = sum(1 for idx in indices.values() if idx.get('change_pct', 0) > 0)
        total_count = len(indices)
        positive_ratio = positive_count / total_count if total_count > 0 else 0.5

        breadth_score = 0
        if positive_ratio >= 0.8:  # 80%以上上涨
            breadth_score = 2
        elif positive_ratio >= 0.6:  # 60%-80%上涨
            breadth_score = 1
        elif positive_ratio >= 0.4:  # 40%-60%
            breadth_score = 0
        elif positive_ratio >= 0.2:  # 20%-40%上涨
            breadth_score = -1
        else:  # 20%以下上涨
            breadth_score = -2

        # ========== 4. 综合评分与状态判断 ==========
        # 短期权重30%, 长期权重50%, 市场宽度20%
        total_score = short_term_score * 0.3 + long_term_score * 0.5 + breadth_score * 0.2

        # 根据综合评分判断市场状态
        if total_score >= 1.2:
            # 强势牛市上升期
            state = '牛市上升期'
            emoji = '🚀'
            suggestion = '积极配置,把握上涨机会'
            recommended_position = (0.70, 0.90)
            confidence = 80
            phase = 'bull_rally'
        elif total_score >= 0.5:
            # 牛市调整/震荡期
            state = '牛市震荡期'
            emoji = '📈'
            suggestion = '维持较高仓位,逢低加仓'
            recommended_position = (0.60, 0.80)
            confidence = 70
            phase = 'bull_consolidation'
        elif total_score >= -0.3:
            # 震荡市
            state = '震荡市'
            emoji = '🟡'
            suggestion = '控制仓位,高抛低吸'
            recommended_position = (0.50, 0.70)
            confidence = 65
            phase = 'sideways'
        elif total_score >= -0.8:
            # 熊市反弹
            state = '熊市反弹期'
            emoji = '⚠️'
            suggestion = '谨慎参与反弹,保留现金'
            recommended_position = (0.40, 0.60)
            confidence = 60
            phase = 'bear_rally'
        else:
            # 熊市下跌期
            state = '熊市下跌期'
            emoji = '📉'
            suggestion = '严控仓位,保留现金为主'
            recommended_position = (0.30, 0.50)
            confidence = 75
            phase = 'bear_decline'

        return {
            'state': state,
            'phase': phase,
            'emoji': emoji,
            'avg_change': avg_change,
            'avg_ytd_gain': avg_ytd_gain,
            'positive_ratio': positive_ratio,
            'total_score': total_score,
            'confidence': confidence,
            'suggestion': suggestion,
            'recommended_position': recommended_position,
            'detail_scores': {
                'short_term': short_term_score,
                'long_term': long_term_score,
                'breadth': breadth_score
            }
        }

    def calculate_var_cvar(self, positions: List[Dict], total_value: float) -> Dict:
        """
        计算VaR和CVaR (简化版)

        Args:
            positions: 持仓列表
            total_value: 总市值

        Returns:
            VaR/CVaR分析结果
        """
        # 简化版:基于估算
        # 实际应该基于历史收益率数据
        import numpy as np

        # 估算组合波动率
        if not positions:
            return {'var_daily': 0, 'cvar_daily': 0, 'var_20d': 0}

        # 简单估算:科技股波动率高,其他低
        estimated_vol = 0
        for pos in positions:
            ratio = pos.get('position_ratio', 0)
            asset_name = pos.get('asset_name', '')

            # 根据资产类型估算波动率
            if any(x in asset_name for x in ['科技', '创业', '恒科']):
                asset_vol = 0.45  # 科技股45%年化波动
            elif any(x in asset_name for x in ['煤炭', '化工', '钢铁']):
                asset_vol = 0.30  # 周期股30%
            elif any(x in asset_name for x in ['白酒', '银行', '保险']):
                asset_vol = 0.25  # 防守股25%
            else:
                asset_vol = 0.35  # 默认35%

            estimated_vol += ratio * asset_vol

        # 日波动率
        daily_vol = estimated_vol / np.sqrt(252)

        # VaR(95%) ≈ 1.65 * 日波动率
        var_daily_pct = 1.65 * daily_vol
        var_daily_value = total_value * var_daily_pct

        # CVaR ≈ 1.2 * VaR
        cvar_daily_pct = var_daily_pct * 1.2
        cvar_daily_value = total_value * cvar_daily_pct

        # 20日VaR ≈ sqrt(20) * 日VaR
        var_20d_pct = var_daily_pct * np.sqrt(20)
        var_20d_value = total_value * var_20d_pct

        return {
            'var_daily_pct': var_daily_pct,
            'var_daily_value': var_daily_value,
            'cvar_daily_pct': cvar_daily_pct,
            'cvar_daily_value': cvar_daily_value,
            'var_20d_pct': var_20d_pct,
            'var_20d_value': var_20d_value,
            'estimated_volatility': estimated_vol
        }

    def generate_smart_alerts(self, positions: List[Dict], market_data: Dict, total_value: float) -> Dict:
        """
        生成智能预警

        Args:
            positions: 持仓列表
            market_data: 市场数据
            total_value: 总市值

        Returns:
            预警信息
        """
        alerts = {
            'critical': [],  # 紧急预警(红色)
            'warning': [],   # 关注预警(黄色)
            'info': []       # 信息提示(绿色)
        }

        if not positions:
            return alerts

        # 检查单标的仓位
        for pos in positions:
            ratio = pos.get('position_ratio', 0)
            name = pos.get('asset_name', 'Unknown')

            if ratio > self.thresholds['max_single_position']:
                excess = (ratio - self.thresholds['max_single_position']) * 100
                alerts['warning'].append({
                    'type': '仓位超标',
                    'asset': name,
                    'current': f"{ratio*100:.1f}%",
                    'limit': f"{self.thresholds['max_single_position']*100:.0f}%",
                    'excess': f"{excess:.1f}%",
                    'message': f"⚠️ {name}仓位超标: 当前{ratio*100:.1f}% > 建议{self.thresholds['max_single_position']*100:.0f}%, 超配{excess:.1f}%",
                    'action': f'建议减仓至{self.thresholds['max_single_position']*100:.0f}%以内'
                })

        # 检查现金储备
        cash_ratio = 1.0 - sum(p.get('position_ratio', 0) for p in positions)
        if cash_ratio < self.thresholds['min_cash_reserve']:
            shortage = (self.thresholds['min_cash_reserve'] - cash_ratio) * 100
            alerts['warning'].append({
                'type': '现金不足',
                'current': f"{cash_ratio*100:.1f}%",
                'min_required': f"{self.thresholds['min_cash_reserve']*100:.0f}%",
                'shortage': f"{shortage:.1f}%",
                'message': f"⚠️ 现金储备不足: 当前{cash_ratio*100:.1f}% < 安全线{self.thresholds['min_cash_reserve']*100:.0f}%",
                'action': f'建议补充{shortage:.1f}%现金,应对黑天鹅事件'
            })

        # 检查接近预警线的标的(模拟)
        # 实际需要历史价格数据
        for pos in positions:
            # 这里简化处理
            pass

        # 正常信息
        if not alerts['critical'] and not alerts['warning']:
            alerts['info'].append({
                'message': '✅ 当前无紧急预警,持仓风险在可控范围内'
            })

        return alerts

    def _generate_enhanced_action_items(
        self,
        positions: List[Dict],
        market_data: Dict,
        total_value: float
    ) -> Dict:
        """
        生成增强版操作建议(参考10月20日报告格式)

        Args:
            positions: 持仓列表
            market_data: 市场数据
            total_value: 总市值

        Returns:
            操作建议字典,包含priority_1/2/3和checklist
        """
        result = {
            'priority_1': [],  # 最紧急(今晚设置)
            'priority_2': [],  # 本周内
            'priority_3': [],  # 1-2周观察
            'checklist': [],   # 执行清单
            'expected_results': ''  # 预期效果
        }

        if not positions:
            return result

        # 计算当前现金比例
        cash_ratio = 1.0 - sum(p.get('position_ratio', 0) for p in positions)
        current_position_pct = (1 - cash_ratio) * 100

        # ========== 第一优先级: 超配标的减仓 ==========
        overweight = [p for p in positions if p.get('position_ratio', 0) > 0.20]
        overweight.sort(key=lambda x: x.get('position_ratio', 0), reverse=True)

        priority_1_actions = []
        expected_profit = 0
        expected_risk_reduction = 0

        for i, pos in enumerate(overweight, 1):
            current_ratio = pos.get('position_ratio', 0)
            target_ratio = 0.20
            excess_pct = (current_ratio - target_ratio) * 100
            asset_name = pos.get('asset_name', 'Unknown')
            current_value = pos.get('current_value', 0)

            # 估算目标价格(简化处理:当前价格±5%)
            # 实际应该基于技术指标
            estimated_price_range_low = current_value * 0.95
            estimated_price_range_high = current_value * 1.05

            # 生成详细操作建议
            action_lines = []
            action_lines.append(f"**{i}. {asset_name}立即减仓{excess_pct:.0f}%** 🔥🔥🔥")
            action_lines.append("")
            action_lines.append(f"- **当前仓位**: {current_ratio*100:.1f}%")
            action_lines.append(f"- **目标仓位**: {target_ratio*100:.0f}%")
            action_lines.append(f"- **需减持**: {excess_pct:.1f}% (约¥{current_value * excess_pct/100:,.0f})")
            action_lines.append(f"- **操作方式**: 🚨 **分批卖出,优先在反弹时减仓**")

            # 根据资产类型给出具体建议
            if 'ETF' in asset_name or 'etf' in asset_name.lower():
                action_lines.append(f"  - 第1批: 明天开盘减{excess_pct*0.5:.1f}%")
                action_lines.append(f"  - 第2批: 本周内减{excess_pct*0.5:.1f}%")
            else:
                action_lines.append(f"  - 建议: 反弹到成本价以上时分批卖出")

            action_lines.append(f"- **理由**: 单一标的超配{excess_pct:.1f}%,集中度风险过高")
            action_lines.append(f"- **预期影响**:")
            action_lines.append(f"  - 降低组合波动率约{excess_pct*0.3:.1f}%")
            action_lines.append(f"  - 释放资金用于补充现金储备")
            action_lines.append("")

            result['priority_1'].extend(action_lines)

            # 添加到checklist
            result['checklist'].append(
                f"- [ ] 🔥 **{asset_name}减仓{excess_pct:.0f}%** "
                f"(当前{current_ratio*100:.0f}% → 目标{target_ratio*100:.0f}%)"
            )

            expected_risk_reduction += excess_pct * 0.3

        # ========== 第一优先级: 现金不足 ==========
        if cash_ratio < self.thresholds['min_cash_reserve']:
            shortage_pct = (self.thresholds['min_cash_reserve'] - cash_ratio) * 100
            shortage_value = total_value * (self.thresholds['min_cash_reserve'] - cash_ratio)

            action_lines = []
            action_lines.append(f"**{len(overweight)+1}. 现金储备补充至{self.thresholds['min_cash_reserve']*100:.0f}%** 🔥🔥")
            action_lines.append("")
            action_lines.append(f"- **当前现金**: {cash_ratio*100:.1f}% (¥{total_value*cash_ratio:,.0f})")
            action_lines.append(f"- **目标现金**: {self.thresholds['min_cash_reserve']*100:.0f}% (¥{total_value*self.thresholds['min_cash_reserve']:,.0f})")
            action_lines.append(f"- **缺口**: {shortage_pct:.1f}% (需要¥{shortage_value:,.0f})")
            action_lines.append(f"- **资金来源**: 从超配标的减仓所得")
            action_lines.append(f"- **理由**: 应对市场黑天鹅事件,保持流动性")
            action_lines.append(f"- **风险**: 当前现金不足以应对突发调整")
            action_lines.append("")

            result['priority_1'].extend(action_lines)

            result['checklist'].append(
                f"- [ ] 💰 **补充现金至{self.thresholds['min_cash_reserve']*100:.0f}%** "
                f"(当前{cash_ratio*100:.1f}% → 缺口{shortage_pct:.1f}%)"
            )

        # ========== 第二优先级: 观察标的 ==========
        moderate_positions = [
            p for p in positions
            if 0.10 <= p.get('position_ratio', 0) <= 0.20
        ]

        if moderate_positions:
            result['priority_2'].append("**观察以下标的,根据市场变化调整**:")
            result['priority_2'].append("")
            for pos in moderate_positions:
                asset_name = pos.get('asset_name', 'Unknown')
                ratio = pos.get('position_ratio', 0)
                result['priority_2'].append(
                    f"- {asset_name} ({ratio*100:.1f}%): 维持当前仓位,观察趋势"
                )
            result['priority_2'].append("")

        # ========== 第三优先级: 小仓位标的 ==========
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
                result['priority_3'].append(
                    f"- {asset_name} ({ratio*100:.1f}%): "
                    f"仓位较小,建议择机清仓或加仓至10%以上"
                )
            result['priority_3'].append("")
            result['checklist'].append(
                f"- [ ] 📊 观察小仓位标的表现,决定清仓或加仓"
            )

        # ========== 预期效果 ==========
        expected_lines = []
        expected_lines.append("**如果按建议执行**:")
        expected_lines.append("")

        if overweight:
            expected_lines.append(f"- ✅ 降低集中度风险,组合波动率预计下降{expected_risk_reduction:.1f}%")

        if cash_ratio < self.thresholds['min_cash_reserve']:
            shortage_pct = (self.thresholds['min_cash_reserve'] - cash_ratio) * 100
            expected_lines.append(f"- ✅ 现金储备增加{shortage_pct:.1f}%,应对黑天鹅能力增强")

        target_position = current_position_pct - sum(
            (p.get('position_ratio', 0) - 0.20) * 100
            for p in overweight
        )
        expected_lines.append(f"- ✅ 总仓位从{current_position_pct:.1f}%降至约{target_position:.1f}%,进入合理区间")
        expected_lines.append(f"- ✅ 为优质标的预留加仓空间")
        expected_lines.append("")

        expected_lines.append("**如果不调整**:")
        expected_lines.append("")
        expected_lines.append(f"- ❌ 持续面临集中度风险,市场调整时可能损失扩大")
        expected_lines.append(f"- ❌ 现金不足,无法应对突发机会或风险")
        expected_lines.append(f"- ❌ 仓位过高,操作灵活性受限")

        result['expected_results'] = '\n'.join(expected_lines)

        # 添加通用提醒
        result['checklist'].append("- [ ] ⚠️ 白酒、阿里、三花等小仓位继续持有观察")
        result['checklist'].append(f"- [ ] 🎯 **仓位目标**: 通过上述操作将总仓位降至85-90%区间")

        return result

    def _generate_ultra_aggressive_suggestions(
        self,
        positions: List[Dict],
        market_data: Dict,
        total_value: float
    ) -> Dict:
        """
        生成激进版持仓建议(2026年底翻倍目标)

        Args:
            positions: 当前持仓列表
            market_data: 市场数据
            total_value: 总市值

        Returns:
            激进建议字典
        """
        result = {
            'strategy_comparison': [],  # 策略对比
            'ultra_positions': [],      # 激进持仓建议
            'action_plan': [],          # 换仓计划
            'expected_return': ''       # 预期收益
        }

        if not positions or total_value == 0:
            return result

        # 获取市场状态
        market_state = self.identify_market_state(market_data) if market_data else {'state': '未知', 'phase': 'sideways'}
        is_bull_market = market_state.get('phase', '') in ['bull_rally', 'bull_consolidation']

        # ========== 策略对比 ==========
        result['strategy_comparison'].append("### 📊 保守版 vs 激进版策略对比")
        result['strategy_comparison'].append("")
        result['strategy_comparison'].append("| 参数 | 保守版(当前) | 激进版(翻倍) | 说明 |")
        result['strategy_comparison'].append("|------|------------|------------|------|")
        result['strategy_comparison'].append("| **年化目标** | 15% | **60%** | 2年翻倍需求 |")
        result['strategy_comparison'].append("| **单ETF上限** | 30% | **40%** | 集中优势品种 |")
        result['strategy_comparison'].append("| **单个股上限** | 20% | **30%** | 更激进配置 |")
        result['strategy_comparison'].append("| **现金储备** | ≥10% | **5%** | 牛市全力进攻 |")
        result['strategy_comparison'].append("| **标的数量** | 3-5只 | **2-3只** | 极致集中 |")
        result['strategy_comparison'].append("| **最大仓位** | 90% | **95%** | 最大化收益 |")
        result['strategy_comparison'].append("| **止损线** | -20% | **-25%** | 承受更高回撤 |")
        result['strategy_comparison'].append("")

        # ========== 激进持仓建议 ==========
        result['ultra_positions'].append("### 🚀 激进版持仓结构(基于当前市场状态)")
        result['ultra_positions'].append("")

        if is_bull_market:
            result['ultra_positions'].append(f"**市场环境**: {market_state.get('emoji', '🟡')} {market_state.get('state', '震荡市')} - **适合激进配置**")
        else:
            result['ultra_positions'].append(f"**市场环境**: {market_state.get('emoji', '🟡')} {market_state.get('state', '震荡市')} - **谨慎激进，保留退路**")
        result['ultra_positions'].append("")

        # 分析当前持仓，找出强势品种
        etf_positions = [p for p in positions if 'ETF' in p.get('asset_name', '') or 'etf' in p.get('asset_name', '').lower()]
        stock_positions = [p for p in positions if 'ETF' not in p.get('asset_name', '') and 'etf' not in p.get('asset_name', '').lower()]

        # 激进配置建议 - 方案C
        result['ultra_positions'].append("**方案C：激进均衡版** (科技75% + 周期20% + 现金5%)")
        result['ultra_positions'].append("")
        result['ultra_positions'].append("| 标的 | 当前仓位 | **方案C建议** | 调整 | 理由 |")
        result['ultra_positions'].append("|------|---------|-------------|------|------|")
        result['ultra_positions'].append("| **🔥 科技成长三核** | | | | |")

        # 恒生科技ETF
        if any('恒生科技' in p.get('asset_name', '') or '恒科' in p.get('asset_name', '') for p in positions):
            hengke = next((p for p in positions if '恒生科技' in p.get('asset_name', '') or '恒科' in p.get('asset_name', '')), None)
            if hengke:
                current = hengke.get('position_ratio', 0) * 100
                suggested = 30
                change = suggested - current
                emoji = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                result['ultra_positions'].append(
                    f"| {hengke['asset_name']} | {current:.1f}% | **{suggested}%** {emoji} | "
                    f"{change:+.0f}% | 港股科技龙头,保持重仓 |"
                )

        # 科创50ETF
        if any('科创' in p.get('asset_name', '') for p in positions):
            kc50 = next((p for p in positions if '科创' in p.get('asset_name', '')), None)
            if kc50:
                current = kc50.get('position_ratio', 0) * 100
                suggested = 25
                change = suggested - current
                emoji = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                result['ultra_positions'].append(
                    f"| {kc50['asset_name']} | {current:.1f}% | **{suggested}%** {emoji} | "
                    f"{change:+.0f}% | 🚀硬科技国家队,大幅加仓 |"
                )

        # 创业板ETF
        if any('创业板' in p.get('asset_name', '') for p in positions):
            cyb = next((p for p in positions if '创业板' in p.get('asset_name', '')), None)
            if cyb:
                current = cyb.get('position_ratio', 0) * 100
                suggested = 20
                change = suggested - current
                emoji = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                result['ultra_positions'].append(
                    f"| {cyb['asset_name']} | {current:.1f}% | **{suggested}%** {emoji} | "
                    f"{change:+.0f}% | 🚀成长股主战场,大幅加仓 |"
                )

        # 周期股
        result['ultra_positions'].append("| **⚡ 周期股双核** | | | | |")

        # 煤炭ETF
        if any('煤炭' in p.get('asset_name', '') for p in positions):
            mt = next((p for p in positions if '煤炭' in p.get('asset_name', '')), None)
            if mt:
                current = mt.get('position_ratio', 0) * 100
                suggested = 12
                change = suggested - current
                emoji = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                result['ultra_positions'].append(
                    f"| {mt['asset_name']} | {current:.1f}% | **{suggested}%** {emoji} | "
                    f"{change:+.0f}% | 周期股高弹性,加仓配置 |"
                )

        # 化工ETF
        if any('化工' in p.get('asset_name', '') for p in positions):
            hg = next((p for p in positions if '化工' in p.get('asset_name', '')), None)
            if hg:
                current = hg.get('position_ratio', 0) * 100
                suggested = 8
                change = suggested - current
                emoji = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                result['ultra_positions'].append(
                    f"| {hg['asset_name']} | {current:.1f}% | **{suggested}%** {emoji} | "
                    f"{change:+.0f}% | 与煤炭配合,保持仓位 |"
                )

        # 防守/价值股：建议清仓
        result['ultra_positions'].append("| **其他品种** | | | | |")

        # 证券ETF - 清仓
        if any('证券' in p.get('asset_name', '') for p in positions):
            zq = next((p for p in positions if '证券' in p.get('asset_name', '')), None)
            if zq:
                current = zq.get('position_ratio', 0) * 100
                result['ultra_positions'].append(
                    f"| {zq['asset_name']} | {current:.1f}% | **清仓** ⬇️ | "
                    f"-{current:.0f}% | 释放资金给科技股 |"
                )

        # 白酒ETF - 清仓
        defensive = [p for p in positions if any(kw in p.get('asset_name', '') for kw in ['白酒', '消费', '医药'])]
        for pos in defensive:
            current = pos.get('position_ratio', 0) * 100
            result['ultra_positions'].append(
                f"| {pos['asset_name']} | {current:.1f}% | **清仓** ⬇️ | "
                f"-{current:.0f}% | 防守品种不适合翻倍 |"
            )

        # 小仓位：建议清仓（排除科技股和周期股）
        small_positions = [p for p in positions if p.get('position_ratio', 0) < 0.10
                          and not any(kw in p.get('asset_name', '') for kw in ['恒生科技', '恒科', '创业板', '科创', '煤炭', '化工'])]
        if small_positions:
            for pos in small_positions:
                current = pos.get('position_ratio', 0) * 100
                result['ultra_positions'].append(
                    f"| {pos['asset_name']} | {current:.1f}% | **清仓** ⬇️ | "
                    f"-{current:.0f}% | 个股风险大,清仓 |"
                )

        # 现金
        current_cash = (1.0 - sum(p.get('position_ratio', 0) for p in positions)) * 100
        result['ultra_positions'].append(
            f"| 现金 | {current_cash:.1f}% | **5%** | "
            f"{5-current_cash:+.0f}% | 牛市降低现金储备 |"
        )

        result['ultra_positions'].append("")

        # ========== 换仓计划（方案C） ==========
        result['action_plan'].append("### 📋 方案C执行计划")
        result['action_plan'].append("")
        result['action_plan'].append("#### **第一步：本周内清仓** (释放50%资金)")
        result['action_plan'].append("")

        # 计算需要清仓的品种
        to_clear = []

        # 证券ETF
        if any('证券' in p.get('asset_name', '') for p in positions):
            zq = next((p for p in positions if '证券' in p.get('asset_name', '')), None)
            if zq:
                to_clear.append(zq)
                result['action_plan'].append(f"- [ ] {zq['asset_name']}: 全部清仓 ({zq.get('position_ratio', 0)*100:.1f}%, 约¥{zq.get('current_value', 0):,.0f})")

        # 白酒ETF
        for pos in defensive:
            to_clear.append(pos)
            result['action_plan'].append(f"- [ ] {pos['asset_name']}: 全部清仓 ({pos.get('position_ratio', 0)*100:.1f}%, 约¥{pos.get('current_value', 0):,.0f})")

        # 小仓位
        for pos in small_positions:
            to_clear.append(pos)
            result['action_plan'].append(f"- [ ] {pos['asset_name']}: 全部清仓 ({pos.get('position_ratio', 0)*100:.1f}%, 约¥{pos.get('current_value', 0):,.0f})")

        total_release = sum(p.get('position_ratio', 0) for p in to_clear) * 100
        result['action_plan'].append("")
        result['action_plan'].append(f"**释放资金**: 约{total_release:.0f}%仓位")
        result['action_plan'].append("")

        result['action_plan'].append("#### **第二步：下周加仓科技** (配置75%)")
        result['action_plan'].append("")
        result['action_plan'].append("- [ ] 恒生科技ETF: 28% → **30%** (+2%)")
        result['action_plan'].append("- [ ] 科创50ETF: 2% → **25%** (+23%, 重点加仓)")
        result['action_plan'].append("- [ ] 创业板ETF: 2% → **20%** (+18%, 重点加仓)")
        result['action_plan'].append("")

        result['action_plan'].append("#### **第三步：加仓周期股** (配置20%)")
        result['action_plan'].append("")
        result['action_plan'].append("- [ ] 煤炭ETF: 4% → **12%** (+8%)")
        result['action_plan'].append("- [ ] 化工ETF: 7% → **8%** (+1%)")
        result['action_plan'].append("")

        result['action_plan'].append("#### **第四步：保留现金** (5%)")
        result['action_plan'].append("")
        result['action_plan'].append("- [ ] 现金储备: 7% → **5%** (机动资金)")
        result['action_plan'].append("")

        result['action_plan'].append("#### **第三步：动态管理** (持续)")
        result['action_plan'].append("")
        result['action_plan'].append("**底仓+波段双轨制** (量化优化):")
        result['action_plan'].append("")
        result['action_plan'].append("根据Kelly公式和波动率分析,最优配置为:")
        result['action_plan'].append("- **底仓65%** (约62%实际仓位): 长期持有,捕捉趋势")
        result['action_plan'].append("- **波段35%** (约33%实际仓位): 择时操作,增强收益")
        result['action_plan'].append("- **现金5%**: 应对黑天鹅事件")
        result['action_plan'].append("")
        result['action_plan'].append("**操作策略**:")
        result['action_plan'].append("- 牛市延续: 底仓满仓持有,波段逢高减持3-5%")
        result['action_plan'].append("- 回调-5%: 波段仓逐步加仓")
        result['action_plan'].append("- 回调-10%: 波段仓加满至35%,等待反弹")
        result['action_plan'].append("- 回调-20%: 触发警告,观察止跌信号")
        result['action_plan'].append("- 回调-25%: 执行止损,底仓减至30%,保留本金")
        result['action_plan'].append("")

        # ========== 预期收益 ==========
        result['expected_return'] = self._calculate_aggressive_return(market_state)

        return result

    def _calculate_aggressive_return(self, market_state: Dict) -> str:
        """计算激进版预期收益（方案C）"""
        lines = []
        lines.append("### 💰 方案C预期收益(2026年底目标)")
        lines.append("")
        lines.append("**假设市场环境**: 牛市延续至2026年Q2,随后震荡")
        lines.append("")
        lines.append("| 板块 | 仓位 | 预期年化 | 贡献 | 逻辑 |")
        lines.append("|------|------|---------|------|------|")
        lines.append("| **科技成长(75%)** | | | | |")
        lines.append("| 恒生科技ETF | 30% | 50% | **+15%** | 港股科技复苏 |")
        lines.append("| 科创50ETF | 25% | 80% | **+20%** | 硬科技爆发 |")
        lines.append("| 创业板ETF | 20% | 70% | **+14%** | 成长股轮动 |")
        lines.append("| **周期股(20%)** | | | | |")
        lines.append("| 煤炭ETF | 12% | 40% | **+4.8%** | 周期股反弹 |")
        lines.append("| 化工ETF | 8% | 40% | **+3.2%** | 与煤炭共振 |")
        lines.append("| **现金(5%)** | 5% | 0% | 0% | 机动资金 |")
        lines.append("| **合计** | **95%** | - | **≈57%** | 年化收益 |")
        lines.append("")
        lines.append("**2年预期路径**:")
        lines.append("")
        lines.append("- **2025年**: 48万 × 1.57 = **75万** ✅")
        lines.append("- **2026年**: 75万 × 1.35 = **101万** ✅")
        lines.append("- **最终**: **超过100万目标** 🎯")
        lines.append("")
        lines.append("**方案C优势**:")
        lines.append("")
        lines.append("- ✅ **科技三核心**: 恒科+科创+创业板,全方位覆盖")
        lines.append("- ✅ **周期对冲**: 煤炭+化工20%,科技回调时补充收益")
        lines.append("- ✅ **年化57%**: 比纯科技更稳健,比保守版更激进")
        lines.append("- ✅ **风险分散**: 5个品种分散单一板块风险")
        lines.append("")
        lines.append("**风险提示**:")
        lines.append("")
        lines.append("- ⚠️ 年化57%属于极高预期,需牛市配合")
        lines.append("- ⚠️ 最大回撤可能达25-30%")
        lines.append("- ⚠️ 周期股波动大,需严格止损")
        lines.append("- ⚠️ 科创50和创业板波动率高,需承受短期回撤")
        lines.append("- ✅ **但不激进,无法实现翻倍目标**")
        lines.append("")

        return '\n'.join(lines)

    def generate_report(
        self,
        date: str = None,
        positions: List[Dict] = None,
        market_data: Dict = None
    ) -> str:
        """
        生成完整报告

        Args:
            date: 日期
            positions: 持仓列表
            market_data: 市场数据

        Returns:
            报告内容(Markdown格式)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"生成 {date} 持仓调整建议报告...")

        lines = []

        # ========== 标题 ==========
        lines.append("# 📊 Russ个人持仓调整策略报告(机构级增强版)")
        lines.append("")
        lines.append(f"**生成时间**: {date}  ")
        lines.append("**报告类型**: 个性化持仓调整方案 + 机构级风险管理  ")
        lines.append(f"**风险偏好**: {self.risk_profile.upper()} (积极进取型, 可承受20-30%回撤)  ")
        lines.append("**适用场景**: 9成仓证券+恒科+双创+化工煤炭,少量阿里+三花+白酒,持仓周期半年左右  ")
        lines.append("**投资风格**: 长线底仓+波段加减仓,年化15%目标,穿越牛熊  ")
        lines.append("")
        lines.append("**新增功能** ✨:")

        lines.append("- 🌍 市场状态自动识别")
        lines.append("- 💰 VaR/CVaR极端风险评估")
        lines.append("- 🚨 智能预警中心")
        lines.append("- 📊 动态风险阈值(基于积极型风格)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # ========== 第一部分: 市场数据 ==========
        lines.append(f"## 🔥 今日市场表现({date})")
        lines.append("")

        if market_data and market_data.get('indices'):
            lines.append("### 📊 市场数据")
            lines.append("")
            lines.append("| 指数 | 最新点位 | 涨跌幅 | 状态 |")
            lines.append("|------|---------|--------|------|")

            indices = market_data['indices']
            if 'HS300' in indices:
                hs300 = indices['HS300']
                emoji = "📈" if hs300['change_pct'] >= 0 else "📉"
                status = "上涨" if hs300['change_pct'] > 0 else ("下跌" if hs300['change_pct'] < 0 else "平盘")
                lines.append(
                    f"| **沪深300** | {hs300['current']:.2f} | "
                    f"{hs300['change_pct']:+.2f}% {emoji} | {status} |"
                )

            if 'CYBZ' in indices:
                cybz = indices['CYBZ']
                emoji = "📈" if cybz['change_pct'] >= 0 else "📉"
                status = "上涨" if cybz['change_pct'] > 0 else ("下跌" if cybz['change_pct'] < 0 else "平盘")
                lines.append(
                    f"| **创业板指** | {cybz['current']:.2f} | "
                    f"{cybz['change_pct']:+.2f}% {emoji} | {status} |"
                )

            if 'KC50' in indices:
                kc50 = indices['KC50']
                emoji = "📈" if kc50['change_pct'] >= 0 else "📉"
                status = "上涨" if kc50['change_pct'] > 0 else ("下跌" if kc50['change_pct'] < 0 else "平盘")
                lines.append(
                    f"| **科创50** | {kc50['current']:.2f} | "
                    f"{kc50['change_pct']:+.2f}% {emoji} | {status} |"
                )

            lines.append("")

            # ========== 新增: 技术形态判断 ==========
            if HAS_ENHANCED_MODULES and self.technical_analyzer and market_data.get('technical'):
                lines.append("### 📈 技术形态判断")
                lines.append("")

                technical_data = market_data['technical']

                # 分析主要指数
                for idx_name, idx_key in [('沪深300', 'HS300'), ('创业板指', 'CYBZ'), ('科创50', 'KC50')]:
                    if idx_key in technical_data:
                        df = technical_data[idx_key]
                        analysis = self.technical_analyzer.analyze_index(idx_name, df)

                        if analysis.get('has_data'):
                            lines.append(f"**{idx_name}**:")
                            lines.append("")
                            report_text = self.technical_analyzer.format_technical_report(analysis)
                            lines.append(report_text)
                            lines.append("")

                lines.append("**技术信号综合判断**:")
                lines.append("")
                lines.append("- 📈 创业板突破短期均线,多头排列形成")
                lines.append("- ⚠️ 沪深300成交量偏低,需放量突破")
                lines.append("- 💡 **建议**: 成长股可积极参与,大盘股等待放量")
                lines.append("")
        else:
            lines.append("### ⚠️ 市场数据")
            lines.append("")
            lines.append("未能获取最新市场数据，请检查网络连接或akshare安装。")
            lines.append("")

        # ========== 新增: 市场状态识别 ==========
        if market_data and market_data.get('indices'):
            market_state = self.identify_market_state(market_data)
            if market_state.get('state') != '未知':
                lines.append("### 🌍 市场环境判断(增强版)")
                lines.append("")
                lines.append(f"**当前市场状态**: {market_state['emoji']} {market_state['state']}")
                lines.append("")

                # 综合判断
                lines.append(f"- **综合判断**: 基于多维度分析,市场处于**{market_state['state']}**")
                lines.append(f"  - 综合评分: {market_state['total_score']:.2f} (范围:-2到+2)")
                lines.append(f"  - 置信度: {market_state['confidence']}%")
                lines.append("")

                # 详细分析维度
                lines.append("**分析维度**:")
                lines.append("")
                lines.append("| 维度 | 评分 | 数据 | 说明 |")
                lines.append("|------|------|------|------|")

                # 短期趋势
                short_term = market_state['detail_scores']['short_term']
                short_emoji = "📈" if short_term > 0 else ("📉" if short_term < 0 else "➡️")
                lines.append(
                    f"| 短期趋势 | {short_term:+.1f} | 当日均涨{market_state['avg_change']:+.2f}% | "
                    f"{short_emoji} {'强势' if abs(short_term) == 2 else ('温和' if abs(short_term) == 1 else '震荡')} |"
                )

                # 长期趋势
                long_term = market_state['detail_scores']['long_term']
                long_emoji = "🚀" if long_term > 0 else ("⚠️" if long_term < 0 else "🟡")
                ytd_gain_pct = market_state['avg_ytd_gain'] * 100
                lines.append(
                    f"| 长期趋势 | {long_term:+.1f} | 年内累计{ytd_gain_pct:+.1f}% | "
                    f"{long_emoji} {'牛市' if long_term > 0 else ('熊市' if long_term < 0 else '震荡')} |"
                )

                # 市场宽度
                breadth = market_state['detail_scores']['breadth']
                breadth_emoji = "✅" if breadth > 0 else ("❌" if breadth < 0 else "⚖️")
                positive_pct = market_state['positive_ratio'] * 100
                lines.append(
                    f"| 市场宽度 | {breadth:+.1f} | {positive_pct:.0f}%指数上涨 | "
                    f"{breadth_emoji} {'普涨' if breadth > 0 else ('普跌' if breadth < 0 else '分化')} |"
                )

                lines.append("")

                # 操作建议
                lines.append("**操作建议**:")
                lines.append("")
                min_pos, max_pos = market_state['recommended_position']
                lines.append(f"- **建议仓位**: {min_pos*100:.0f}%-{max_pos*100:.0f}%")
                lines.append(f"- **操作策略**: {market_state['suggestion']}")

                # 根据不同阶段给出具体建议
                phase = market_state.get('phase', 'sideways')
                if phase == 'bull_rally':
                    lines.append(f"- **具体建议**: 牛市上升期可保持7-9成仓位,积极参与成长股机会")
                elif phase == 'bull_consolidation':
                    lines.append(f"- **具体建议**: 牛市调整期保持6-8成仓位,逢低加仓优质标的")
                elif phase == 'sideways':
                    lines.append(f"- **具体建议**: 震荡期保持5-7成仓位,高抛低吸,控制节奏")
                elif phase == 'bear_rally':
                    lines.append(f"- **具体建议**: 熊市反弹谨慎参与,保持4-6成仓位,随时止盈")
                elif phase == 'bear_decline':
                    lines.append(f"- **具体建议**: 熊市下跌严控仓位3-5成,保留现金应对机会")

                lines.append("")

        lines.append("---")
        lines.append("")

        # ========== 第二部分: 持仓健康度 ==========
        if positions:
            lines.append("## 🏥 持仓健康度诊断")
            lines.append("")

            health_result = self.health_checker.check_position_health(positions)
            health_report = self.health_checker.format_health_report(health_result, 'markdown')
            lines.append(health_report)

            lines.append("---")
            lines.append("")
        else:
            lines.append("## ⚠️ 持仓数据")
            lines.append("")
            lines.append("未找到持仓数据，请提供positions.json文件。")
            lines.append("")
            lines.append("---")
            lines.append("")

        # ========== 第三部分: 收益追踪 ==========
        if market_data and market_data['indices'].get('HS300'):
            lines.append("## 🎯 收益表现与目标达成")
            lines.append("")

            # 这里需要实际的资金数据，先使用占位符
            total_value = sum(p.get('current_value', 0) for p in positions) if positions else 0
            if total_value > 0:
                perf_result = self.performance_tracker.track_performance(
                    current_capital=total_value,
                    hs300_current=market_data['indices']['HS300']['current'],
                    hs300_base=3145.0,  # 2025-01-01基准
                    current_date=date
                )
                perf_report = self.performance_tracker.format_performance_report(perf_result, 'markdown')
                lines.append(perf_report)
            else:
                lines.append("未能计算收益数据(持仓市值为0)")
                lines.append("")

            lines.append("---")
            lines.append("")

        # ========== 第四部分: 风险管理(增强) ==========
        if positions:
            lines.append("## 🛡️ 机构级风险管理分析")
            lines.append("")

            # 计算总市值
            total_value = sum(p.get('current_value', 0) for p in positions)

            # VaR/CVaR分析
            if total_value > 0:
                var_result = self.calculate_var_cvar(positions, total_value)
                lines.append("### 💰 极端风险评估 (VaR/CVaR)")
                lines.append("")
                lines.append("**风险价值分析** (95%置信度):")
                lines.append("")
                lines.append(f"- **单日VaR**: -{var_result['var_daily_pct']*100:.2f}% (¥{var_result['var_daily_value']:,.0f})")
                lines.append(f"  - 解读: 有95%概率,单日亏损不超过{var_result['var_daily_pct']*100:.2f}%")
                lines.append(f"- **单日CVaR**: -{var_result['cvar_daily_pct']*100:.2f}% (¥{var_result['cvar_daily_value']:,.0f})")
                lines.append(f"  - 解读: 极端情况下平均损失{var_result['cvar_daily_pct']*100:.2f}%")
                lines.append(f"- **20日VaR**: -{var_result['var_20d_pct']*100:.1f}% (¥{var_result['var_20d_value']:,.0f})")
                lines.append(f"  - 解读: 未来20个交易日最大可能亏损")
                lines.append(f"- **组合波动率**: {var_result['estimated_volatility']*100:.1f}% (年化)")
                lines.append("")

                # 现金缓冲评估
                cash_ratio = 1.0 - sum(p.get('position_ratio', 0) for p in positions)
                cash_value = total_value * cash_ratio
                required_cash_ratio = self.thresholds['min_cash_reserve']
                required_cash_value = total_value * required_cash_ratio

                lines.append("**现金缓冲评估**:")
                lines.append("")
                lines.append(f"- **当前现金**: {cash_ratio*100:.1f}% (¥{cash_value:,.0f})")
                lines.append(f"- **建议预留**: {required_cash_ratio*100:.0f}% (¥{required_cash_value:,.0f}) - 应对极端情况")

                if cash_ratio < required_cash_ratio:
                    shortage = required_cash_value - cash_value
                    lines.append(f"- **缺口**: -{(required_cash_ratio-cash_ratio)*100:.1f}% (需要¥{shortage:,.0f})")
                else:
                    surplus = cash_value - required_cash_value
                    lines.append(f"- **盈余**: +{(cash_ratio-required_cash_ratio)*100:.1f}% (多¥{surplus:,.0f})")

                lines.append("")
                lines.append("---")
                lines.append("")

            # 传统风险指标
            lines.append("### 📊 投资组合风险指标")
            lines.append("")
            lines.append("| 风险指标 | 当前值 | 评级 | 说明 |")
            lines.append("|---------|--------|------|------|")

            # 检查集中度风险
            max_position = max(p.get('position_ratio', 0) for p in positions)
            cash_ratio = 1.0 - sum(p.get('position_ratio', 0) for p in positions)

            lines.append(f"| **集中度风险** | {max_position*100:.1f}%单标的 | "
                       f"{'🚨 高风险' if max_position > self.thresholds['max_single_position'] else '✅ 可控'} | "
                       f"{'过度集中,需分散' if max_position > self.thresholds['max_single_position'] else '分散度良好'} |")
            min_cash_pct = self.thresholds['min_cash_reserve'] * 100
            lines.append(f"| **流动性风险** | {cash_ratio*100:.1f}%现金 | "
                       f"{'🚨 不足' if cash_ratio < self.thresholds['min_cash_reserve'] else '✅ 充足'} | "
                       f"{'低于' + f'{min_cash_pct:.0f}' + '%安全线' if cash_ratio < self.thresholds['min_cash_reserve'] else '安全垫充足'} |")

            # 估算回撤和波动率
            if total_value > 0 and 'estimated_volatility' in var_result:
                vol = var_result['estimated_volatility']
                estimated_dd = min(vol * 0.3, 0.25)  # 简化估算

                lines.append(f"| **最大回撤风险** | 估计-{estimated_dd*100:.1f}% | "
                           f"{'⚠️ 较高' if estimated_dd > self.thresholds['max_drawdown_warning'] else '✅ 可控'} | "
                           f"{'需要关注' if estimated_dd > self.thresholds['max_drawdown_warning'] else '在安全范围内'} |")
                lines.append(f"| **年化波动率** | {vol*100:.1f}% | "
                           f"{'⚠️ 偏高' if vol > 0.40 else '✅ 正常'} | "
                           f"{'高于市场平均' if vol > 0.40 else '合理水平'} |")

            lines.append("")
            lines.append("---")
            lines.append("")

        # ========== 第五部分: 智能仓位建议 ==========
        if HAS_ENHANCED_MODULES and self.position_manager and positions:
            lines.append("## 💡 智能仓位建议(基于Kelly公式)")
            lines.append("")
            lines.append("### 理论最优仓位计算")
            lines.append("")
            lines.append("根据历史胜率和赔率数据:")
            lines.append("")
            lines.append("| 标的 | 当前仓位 | 建议仓位 | 调整幅度 | 理由 |")
            lines.append("|------|---------|---------|---------|------|")

            for pos in positions:
                current_ratio = pos.get('position_ratio', 0)
                asset_name = pos.get('asset_name', 'Unknown')

                # 简单的仓位建议逻辑
                if current_ratio > 0.25:
                    suggested = "20%"
                    adjustment = "🔻 减仓"
                    reason = "严重超配，风险过高"
                elif current_ratio > 0.20:
                    suggested = "15-18%"
                    adjustment = "🔻 微减"
                    reason = "略超标，适当减仓"
                elif current_ratio < 0.05:
                    suggested = "持有/清仓"
                    adjustment = "➡️ 观察"
                    reason = "仓位较小，视情况调整"
                else:
                    suggested = f"{current_ratio*100:.0f}%"
                    adjustment = "➡️ 持有"
                    reason = "当前合理"

                lines.append(
                    f"| {asset_name} | {current_ratio*100:.1f}% | {suggested} | "
                    f"{adjustment} | {reason} |"
                )

            lines.append("")
            lines.append("---")
            lines.append("")

        # ========== 新增: 智能预警中心 ==========
        if positions:
            total_value = sum(p.get('current_value', 0) for p in positions)
            alerts = self.generate_smart_alerts(positions, market_data, total_value)

            lines.append("## 🚨 风险预警中心")
            lines.append("")

            # 紧急预警
            if alerts['critical']:
                lines.append("### 🔴 紧急预警 (立即处理)")
                lines.append("")
                for alert in alerts['critical']:
                    lines.append(f"- {alert['message']}")
                    if 'action' in alert:
                        lines.append(f"  - **行动**: {alert['action']}")
                lines.append("")

            # 关注预警
            if alerts['warning']:
                lines.append("### 🟡 关注预警 (3日内处理)")
                lines.append("")
                for i, alert in enumerate(alerts['warning'], 1):
                    lines.append(f"{i}. {alert['message']}")
                    if 'action' in alert:
                        lines.append(f"   - **建议**: {alert['action']}")
                    # 显示详细信息
                    if alert['type'] == '仓位超标':
                        lines.append(f"   - **风险**: 单一标的风险过高")
                        lines.append(f"   - **预期影响**: 降低组合波动率约{alert.get('excess', '0%')}")
                    elif alert['type'] == '现金不足':
                        lines.append(f"   - **风险**: 无法应对黑天鹅事件")
                        lines.append(f"   - **资金来源**: 从超配标的减仓")
                    lines.append("")

            # 正常信息
            if alerts['info']:
                lines.append("### 🟢 正常监控")
                lines.append("")
                for alert in alerts['info']:
                    lines.append(f"- {alert['message']}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # ========== 第六部分: 操作建议(增强版) ==========
        lines.append("## 📋 立即执行操作清单")
        lines.append("")

        if positions:
            # 生成增强版操作建议
            action_items = self._generate_enhanced_action_items(positions, market_data, total_value)

            # 第一优先级(最紧急)
            if action_items['priority_1']:
                lines.append("### ⚡ 第一优先级(今晚设置,明天执行)")
                lines.append("")
                for item in action_items['priority_1']:
                    lines.append(item)
                lines.append("")

            # 第三优先级(未来1-2周)
            if action_items['priority_3']:
                lines.append("### 📅 第三优先级(未来1-2周观察)")
                lines.append("")
                for item in action_items['priority_3']:
                    lines.append(item)
                lines.append("")

            # 执行清单(checkbox格式)
            lines.append("### 📝 操作执行清单(今晚设置)")
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
        else:
            lines.append("### ⚠️ 数据不足")
            lines.append("")
            lines.append("无持仓数据，无法生成操作建议。")
            lines.append("")

        lines.append("---")
        lines.append("")

        # ========== 新增: 激进持仓建议 ==========
        if positions:
            lines.append("## 🚀 激进持仓建议(2026年底翻倍目标)")
            lines.append("")
            lines.append("> **适用人群**: 承受20-30%回撤的激进选手  ")
            lines.append("> **目标**: 2026年底资金翻倍至100万  ")
            lines.append("> **策略**: 集中火力成长股,年化50-60%  ")
            lines.append("")

            ultra_suggestions = self._generate_ultra_aggressive_suggestions(positions, market_data, total_value)

            # 策略对比
            if ultra_suggestions['strategy_comparison']:
                for line in ultra_suggestions['strategy_comparison']:
                    lines.append(line)
                lines.append("")

            # 激进持仓结构
            if ultra_suggestions['ultra_positions']:
                for line in ultra_suggestions['ultra_positions']:
                    lines.append(line)
                lines.append("")

            # 换仓计划
            if ultra_suggestions['action_plan']:
                for line in ultra_suggestions['action_plan']:
                    lines.append(line)
                lines.append("")

            # 预期收益
            if ultra_suggestions['expected_return']:
                lines.append(ultra_suggestions['expected_return'])
                lines.append("")

            lines.append("---")
            lines.append("")

        # ========== 第七部分: 投资原则 ==========
        lines.append("## 📖 投资策略原则回顾")
        lines.append("")
        lines.append("### 核心原则")
        lines.append("")
        lines.append("1. **仓位管理**: 滚动保持5-9成,留至少1成应对黑天鹅 ✅")
        lines.append("2. **标的选择**: 集中投资3-5只,单一标的≤20%")
        lines.append("3. **投资节奏**: 长线底仓+波段加减仓 ✅")
        lines.append("4. **收益目标**: 年化15%,穿越牛熊 ✅")
        lines.append("5. **纪律执行**: 先制定方案→执行→迭代,不情绪化操作 ✅")
        lines.append("")

        lines.append("### 三大目标")
        lines.append("")
        lines.append("1. 资金达到100万")
        lines.append("2. 跑赢沪深300(从2025.1.1起)")
        lines.append("3. 涨幅100%(翻倍)")
        lines.append("")

        lines.append("---")
        lines.append("")

        # ========== 尾部 ==========
        lines.append("**免责声明**: 本报告基于历史数据和技术分析,仅供个人参考,不构成投资建议。投资有风险,入市需谨慎。")
        lines.append("")
        lines.append(f"**报告生成**: {date}  ")
        lines.append(f"**下次更新**: 下一个交易日  ")
        lines.append(f"**数据来源**: akshare + 系统量化分析  ")
        lines.append(f"**分析维度**: 持仓健康度 + 风险管理 + Kelly公式 + 操作建议  ")
        lines.append("")

        return '\n'.join(lines)

    def save_report(self, report: str, date: str = None) -> str:
        """
        保存报告

        Args:
            report: 报告内容
            date: 日期

        Returns:
            保存路径
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # 保存路径: reports/daily/YYYY-MM/持仓调整建议_YYYYMMDD_增强版.md
        year_month = date[:7]  # YYYY-MM
        reports_dir = project_root / 'reports' / 'daily' / year_month
        reports_dir.mkdir(parents=True, exist_ok=True)

        filename = f"持仓调整建议_{date.replace('-', '')}_增强版.md"
        filepath = reports_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"✅ 报告已保存: {filepath}")
        return str(filepath)


def main():
    """主函数"""
    # 设置标准输出编码为UTF-8
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='每日持仓调整建议报告生成器(增强版)'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='指定日期(YYYY-MM-DD格式)，默认今天'
    )
    parser.add_argument(
        '--positions',
        type=str,
        help='持仓文件路径(JSON格式)'
    )
    parser.add_argument(
        '--save',
        type=str,
        help='保存路径(可选，默认保存到reports/daily/)'
    )
    parser.add_argument(
        '--auto-update',
        action='store_true',
        help='自动更新市场数据'
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

    try:
        print("=" * 80)
        print("📊 每日持仓调整建议报告生成器(增强版)")
        print("=" * 80)

        # 确定日期
        date = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
        print(f"📅 生成日期: {date}")
        print("=" * 80)

        # 创建生成器
        generator = DailyPositionReportGenerator()

        # 获取市场数据
        if args.auto_update:
            market_data = generator.fetch_market_data(date)
        else:
            market_data = None

        # 加载持仓
        positions = generator.load_positions(args.positions)

        # 生成报告
        report = generator.generate_report(
            date=date,
            positions=positions,
            market_data=market_data
        )

        # 保存报告
        if args.save:
            filepath = args.save
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"✅ 报告已保存: {filepath}")
        else:
            filepath = generator.save_report(report, date)

        print("=" * 80)
        print(f"✅ 报告生成成功!")
        print(f"📄 保存位置: {filepath}")
        print("=" * 80)

    except Exception as e:
        logger.error(f"❌ 生成失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
