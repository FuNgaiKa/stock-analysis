"""
收益追踪对比模块(增强版)

追踪投资收益并与基准对比:
1. 阶段性目标进度(50万→60万→70万→100万)
2. 与沪深300涨幅对比
3. 翻倍目标进度(100%涨幅)
4. 年化收益率计算

增强功能:
5. 风险指标集成(夏普比率、最大回撤、波动率)
6. 滚动收益率分析(月度、季度、年度)
7. 收益归因分析(Brinson模型)
8. 风险调整后收益
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import math
import sys
import os

# 添加父目录到路径以便导入RiskManager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from russ_trading.risk_manager import RiskManager
except ImportError:
    RiskManager = None

# 导入配置加载器
try:
    from russ_trading.config.investment_config import get_investment_config
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False


class PerformanceTracker:
    """投资收益追踪器"""

    def __init__(self, targets_config: Dict = None):
        """
        初始化收益追踪器

        Args:
            targets_config: 目标配置字典,包含:
                - stage_targets: 阶段性目标列表
                - base_date: 基准日期
                - initial_capital: 初始资金
                - target_annual_return: 目标年化收益率
                - risk_free_rate: 无风险利率 (默认3%)

        如果不提供 targets_config，将从 config/investment_goals.yaml 读取
        """
        if targets_config is None:
            targets_config = {}

        # 尝试从配置文件加载
        if HAS_CONFIG:
            try:
                config = get_investment_config()
                self.stage_targets = targets_config.get('stage_targets', config.stage_targets)
                self.base_date = targets_config.get('base_date', config.base_date)
                self.initial_capital = targets_config.get('initial_capital', config.initial_capital)
                self.target_annual_return = targets_config.get('target_annual_return', config.target_annual_return)
                self.final_target = config.final_target
                self.config = config  # 保存配置对象用于格式化
            except Exception as e:
                # 配置加载失败，使用默认值
                self.stage_targets = targets_config.get('stage_targets', [500000, 750000, 1000000])
                self.base_date = targets_config.get('base_date', '2025-01-01')
                self.initial_capital = targets_config.get('initial_capital', 500000)
                self.target_annual_return = targets_config.get('target_annual_return', 0.15)
                self.final_target = 1000000
                self.config = None
        else:
            # 无配置模块，使用传入的值或默认值
            self.stage_targets = targets_config.get('stage_targets', [500000, 750000, 1000000])
            self.base_date = targets_config.get('base_date', '2025-01-01')
            self.initial_capital = targets_config.get('initial_capital', 500000)
            self.target_annual_return = targets_config.get('target_annual_return', 0.15)
            self.final_target = targets_config.get('final_target', 1000000)
            self.config = None

        # 增强功能配置
        risk_free_rate = targets_config.get('risk_free_rate', 0.03)
        self.risk_manager = RiskManager(risk_free_rate=risk_free_rate) if RiskManager else None

        # 历史数据存储(用于滚动收益率等高级分析)
        self.equity_history = []  # [(date, value), ...]
        self.returns_history = []  # [(date, return), ...]

    def track_performance(
        self,
        current_capital: float,
        hs300_current: float,
        hs300_base: float = 3145.0,
        current_date: Optional[str] = None
    ) -> Dict:
        """
        追踪收益表现

        Args:
            current_capital: 当前资金
            hs300_current: 沪深300当前点位
            hs300_base: 沪深300基准点位 (2025.1.1约3145点)
            current_date: 当前日期,格式'YYYY-MM-DD'

        Returns:
            收益追踪结果字典
        """
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')

        # 计算收益率
        total_return = (current_capital - self.initial_capital) / self.initial_capital
        total_return_pct = total_return * 100

        # 计算沪深300收益率
        hs300_return = (hs300_current - hs300_base) / hs300_base
        hs300_return_pct = hs300_return * 100

        # 计算超额收益
        excess_return = total_return - hs300_return
        excess_return_pct = excess_return * 100

        # 计算年化收益率
        days = self._calculate_days(self.base_date, current_date)
        years = days / 365.0
        annual_return = self._calculate_annualized_return(total_return, years) if years > 0 else 0
        annual_return_pct = annual_return * 100

        # 翻倍进度
        double_target = self.initial_capital * 2
        double_progress = current_capital / double_target
        double_progress_pct = double_progress * 100

        # 当前阶段目标
        current_stage = self._find_current_stage(current_capital)

        results = {
            'track_date': current_date,
            'days_since_base': days,
            'years_since_base': round(years, 2),
            'current_capital': current_capital,
            'initial_capital': self.initial_capital,
            'total_return': total_return,
            'total_return_pct': f"{total_return_pct:.2f}%",
            'annual_return': annual_return,
            'annual_return_pct': f"{annual_return_pct:.2f}%",
            'target_annual_return_pct': f"{self.target_annual_return*100:.0f}%",
            'hs300_base': hs300_base,
            'hs300_current': hs300_current,
            'hs300_return': hs300_return,
            'hs300_return_pct': f"{hs300_return_pct:.2f}%",
            'excess_return': excess_return,
            'excess_return_pct': f"{excess_return_pct:.2f}%",
            'double_target': double_target,
            'double_progress': double_progress,
            'double_progress_pct': f"{double_progress_pct:.1f}%",
            'current_stage': current_stage,
            'achievements': self._calculate_achievements(current_capital, total_return, hs300_return, annual_return),
            'warnings': [],
            'suggestions': []
        }

        # 生成警告和建议
        self._generate_warnings_and_suggestions(results)

        return results

    def _calculate_days(self, start_date: str, end_date: str) -> int:
        """计算日期间隔天数"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        return (end - start).days

    def _calculate_annualized_return(self, total_return: float, years: float) -> float:
        """计算年化收益率"""
        if years <= 0:
            return 0
        return math.pow(1 + total_return, 1 / years) - 1

    def _find_current_stage(self, current_capital: float) -> Dict:
        """找到当前所处的阶段目标"""
        completed_stages = []
        next_stage = None
        current_stage_progress = 0

        for i, target in enumerate(self.stage_targets):
            # 使用配置格式化目标金额（脱敏显示）
            if self.config:
                target_text = self.config.format_target_description(target, i)
            else:
                target_text = f"{target/10000:.0f}万"

            if current_capital >= target:
                completed_stages.append({
                    'stage': i + 1,
                    'target': target,
                    'target_text': target_text,
                    'completed': True
                })
            else:
                if next_stage is None:
                    remaining = target - current_capital
                    # 使用配置格式化剩余金额
                    if self.config:
                        remaining_text = self.config.format_amount(remaining)
                    else:
                        remaining_text = f"{remaining/10000:.1f}万"

                    next_stage = {
                        'stage': i + 1,
                        'target': target,
                        'target_text': target_text,
                        'remaining': remaining,
                        'remaining_text': remaining_text
                    }
                    # 计算当前阶段进度
                    if i == 0:
                        prev_target = self.initial_capital
                    else:
                        prev_target = self.stage_targets[i - 1]

                    # 防止除零错误
                    if target - prev_target > 0:
                        current_stage_progress = (current_capital - prev_target) / (target - prev_target)
                    else:
                        current_stage_progress = 0.0

        return {
            'completed_stages': completed_stages,
            'completed_count': len(completed_stages),
            'total_stages': len(self.stage_targets),
            'next_stage': next_stage,
            'current_stage_progress': current_stage_progress,
            'current_stage_progress_pct': f"{current_stage_progress * 100:.1f}%"
        }

    def _calculate_achievements(
        self,
        current_capital: float,
        total_return: float,
        hs300_return: float,
        annual_return: float
    ) -> Dict:
        """计算各项成就达成情况"""
        # 使用配置中的最终目标，而不是硬编码
        final_target = self.final_target

        # 获取目标名称（脱敏显示）
        if self.config:
            final_target_text = self.config.format_target_description(final_target, len(self.stage_targets) - 1)
        else:
            final_target_text = f"{final_target/10000:.0f}万"

        achievements = {
            'target_final': {
                'name': f'资金达到{final_target_text}',
                'achieved': current_capital >= final_target,
                'progress': current_capital / final_target,
                'progress_pct': f"{(current_capital / final_target) * 100:.1f}%"
            },
            'beat_hs300': {
                'name': '跑赢沪深300',
                'achieved': total_return > hs300_return,
                'excess_return': (total_return - hs300_return) * 100,
                'excess_return_pct': f"{(total_return - hs300_return) * 100:.2f}%"
            },
            'double_capital': {
                'name': '资金翻倍(100%涨幅)',
                'achieved': total_return >= self.target_annual_return if self.target_annual_return > 0.5 else total_return >= 1.0,
                'progress': (1 + total_return) / (1 + self.target_annual_return) if self.target_annual_return > 0.5 else (1 + total_return) / 2.0,
                'progress_pct': f"{((1 + total_return) / (1 + self.target_annual_return) if self.target_annual_return > 0.5 else (1 + total_return) / 2.0) * 100:.1f}%"
            },
            'annual_target': {
                'name': f'年化收益达到{self.target_annual_return*100:.0f}%',
                'achieved': annual_return >= self.target_annual_return,
                'current_annual': annual_return * 100,
                'current_annual_pct': f"{annual_return * 100:.2f}%"
            }
        }

        # 保持向后兼容（旧代码可能用 target_100w）
        achievements['target_100w'] = achievements['target_final']

        return achievements

    def _generate_warnings_and_suggestions(self, results: Dict):
        """生成警告和建议"""
        # 检查是否跑赢沪深300
        if results['excess_return'] < 0:
            results['warnings'].append(
                f"⚠️ 当前收益率落后沪深300约{abs(float(results['excess_return_pct'][:-1])):.2f}%"
            )
            results['suggestions'].append("建议复盘投资策略,考虑增加指数ETF配置")

        # 检查年化收益率
        annual_return = results['annual_return']
        if annual_return < self.target_annual_return:
            gap = (self.target_annual_return - annual_return) * 100
            results['warnings'].append(
                f"⚠️ 当前年化收益率{results['annual_return_pct']}低于目标{results['target_annual_return_pct']}"
            )
            results['suggestions'].append(f"需要提升{gap:.2f}%年化收益率才能达到目标")

        # 翻倍进度提示
        double_progress = results['double_progress']
        if double_progress < 0.3:
            results['suggestions'].append("翻倍目标进度较慢,建议关注高潜力品种")
        elif double_progress >= 0.5:
            results['suggestions'].append("翻倍目标已完成过半,继续保持!")

        # 阶段目标提示
        next_stage = results['current_stage']['next_stage']
        if next_stage:
            results['suggestions'].append(
                f"距离下一个阶段目标{next_stage['target_text']}还需{next_stage['remaining_text']}"
            )

    # ========== 增强功能方法 ==========

    def update_equity_history(self, date: str, equity_value: float):
        """
        更新权益历史记录

        Args:
            date: 日期字符串
            equity_value: 权益价值
        """
        self.equity_history.append((date, equity_value))

        # 计算收益率
        if len(self.equity_history) > 1:
            prev_value = self.equity_history[-2][1]
            daily_return = (equity_value - prev_value) / prev_value
            self.returns_history.append((date, daily_return))

    def calculate_risk_metrics(
        self,
        equity_curve: Optional[List[float]] = None,
        returns: Optional[List[float]] = None
    ) -> Dict:
        """
        计算风险指标

        Args:
            equity_curve: 权益曲线 (如果为None,使用历史数据)
            returns: 收益率序列 (如果为None,使用历史数据)

        Returns:
            风险指标字典
        """
        if not self.risk_manager:
            return {'error': 'RiskManager未初始化'}

        # 使用提供的数据或历史数据
        if equity_curve is None:
            equity_curve = [v for _, v in self.equity_history]

        if returns is None:
            returns = [r for _, r in self.returns_history]

        if not equity_curve or not returns:
            return {'error': '缺少历史数据'}

        # 计算各项风险指标
        risk_metrics = {}

        # 最大回撤
        dd_result = self.risk_manager.calculate_max_drawdown(equity_curve)
        risk_metrics['max_drawdown'] = dd_result

        # 波动率
        vol_result = self.risk_manager.calculate_volatility(returns, annualize=True)
        risk_metrics['volatility'] = vol_result

        # 夏普比率
        sharpe_result = self.risk_manager.calculate_sharpe_ratio(returns)
        risk_metrics['sharpe_ratio'] = sharpe_result

        # Sortino比率
        sortino_result = self.risk_manager.calculate_sortino_ratio(returns)
        risk_metrics['sortino_ratio'] = sortino_result

        # Calmar比率
        if dd_result['max_drawdown'] > 0 and len(returns) > 0:
            annual_return = self._calculate_annualized_return(
                sum(returns), len(returns) / 252.0
            )
            calmar_result = self.risk_manager.calculate_calmar_ratio(
                annual_return, dd_result['max_drawdown']
            )
            risk_metrics['calmar_ratio'] = calmar_result

        # VaR
        var_result = self.risk_manager.calculate_var(returns, confidence=0.95)
        risk_metrics['var'] = var_result

        return risk_metrics

    def calculate_rolling_returns(
        self,
        period_days: int = 30,
        min_periods: int = 20
    ) -> Dict:
        """
        计算滚动收益率

        Args:
            period_days: 滚动窗口天数
            min_periods: 最小周期数

        Returns:
            滚动收益率分析结果
        """
        if len(self.equity_history) < min_periods:
            return {'error': f'数据不足,需要至少{min_periods}个数据点'}

        rolling_returns = []

        for i in range(period_days, len(self.equity_history)):
            start_date, start_value = self.equity_history[i - period_days]
            end_date, end_value = self.equity_history[i]

            period_return = (end_value - start_value) / start_value
            rolling_returns.append({
                'start_date': start_date,
                'end_date': end_date,
                'return': period_return,
                'return_pct': f"{period_return * 100:.2f}%"
            })

        if not rolling_returns:
            return {'error': '无法计算滚动收益率'}

        # 统计分析
        returns_values = [r['return'] for r in rolling_returns]

        import numpy as np
        return {
            'period_days': period_days,
            'n_periods': len(rolling_returns),
            'rolling_returns': rolling_returns,
            'statistics': {
                'mean': np.mean(returns_values),
                'median': np.median(returns_values),
                'std': np.std(returns_values),
                'min': min(returns_values),
                'max': max(returns_values),
                'positive_periods': sum(1 for r in returns_values if r > 0),
                'negative_periods': sum(1 for r in returns_values if r < 0),
                'win_rate': sum(1 for r in returns_values if r > 0) / len(returns_values)
            }
        }

    def calculate_monthly_returns(self) -> Dict:
        """
        计算月度收益率

        Returns:
            月度收益率字典
        """
        return self._calculate_periodic_returns('month')

    def calculate_quarterly_returns(self) -> Dict:
        """
        计算季度收益率

        Returns:
            季度收益率字典
        """
        return self._calculate_periodic_returns('quarter')

    def calculate_yearly_returns(self) -> Dict:
        """
        计算年度收益率

        Returns:
            年度收益率字典
        """
        return self._calculate_periodic_returns('year')

    def _calculate_periodic_returns(self, period_type: str) -> Dict:
        """
        计算周期性收益率

        Args:
            period_type: 'month', 'quarter', 或 'year'

        Returns:
            周期性收益率字典
        """
        if not self.equity_history:
            return {'error': '没有历史数据'}

        from collections import defaultdict

        period_data = defaultdict(list)

        for date_str, value in self.equity_history:
            date = datetime.strptime(date_str, '%Y-%m-%d')

            if period_type == 'month':
                key = f"{date.year}-{date.month:02d}"
            elif period_type == 'quarter':
                quarter = (date.month - 1) // 3 + 1
                key = f"{date.year}-Q{quarter}"
            elif period_type == 'year':
                key = str(date.year)
            else:
                return {'error': f'无效的周期类型: {period_type}'}

            period_data[key].append((date_str, value))

        # 计算每个周期的收益率
        period_returns = []

        for period_key, values in sorted(period_data.items()):
            if len(values) < 2:
                continue

            start_date, start_value = values[0]
            end_date, end_value = values[-1]

            period_return = (end_value - start_value) / start_value

            period_returns.append({
                'period': period_key,
                'start_date': start_date,
                'end_date': end_date,
                'start_value': start_value,
                'end_value': end_value,
                'return': period_return,
                'return_pct': f"{period_return * 100:.2f}%"
            })

        return {
            'period_type': period_type,
            'n_periods': len(period_returns),
            'periods': period_returns
        }

    def calculate_attribution_analysis(
        self,
        portfolio_returns: Dict[str, float],
        benchmark_returns: Dict[str, float],
        portfolio_weights: Dict[str, float],
        benchmark_weights: Dict[str, float]
    ) -> Dict:
        """
        收益归因分析(简化版Brinson模型)

        Args:
            portfolio_returns: 投资组合各资产收益率 {'asset': return}
            benchmark_returns: 基准各资产收益率 {'asset': return}
            portfolio_weights: 投资组合各资产权重 {'asset': weight}
            benchmark_weights: 基准各资产权重 {'asset': weight}

        Returns:
            归因分析结果
        """
        # 确保资产名称一致
        assets = set(portfolio_returns.keys()) | set(benchmark_returns.keys())

        attribution = {
            'allocation_effect': 0,  # 配置效应
            'selection_effect': 0,   # 选择效应
            'interaction_effect': 0,  # 交互效应
            'total_active_return': 0,  # 总主动收益
            'details': {}
        }

        for asset in assets:
            p_weight = portfolio_weights.get(asset, 0)
            b_weight = benchmark_weights.get(asset, 0)
            p_return = portfolio_returns.get(asset, 0)
            b_return = benchmark_returns.get(asset, 0)

            # Brinson归因模型
            # 配置效应 = (组合权重 - 基准权重) * 基准收益率
            allocation = (p_weight - b_weight) * b_return

            # 选择效应 = 基准权重 * (组合收益率 - 基准收益率)
            selection = b_weight * (p_return - b_return)

            # 交互效应 = (组合权重 - 基准权重) * (组合收益率 - 基准收益率)
            interaction = (p_weight - b_weight) * (p_return - b_return)

            attribution['allocation_effect'] += allocation
            attribution['selection_effect'] += selection
            attribution['interaction_effect'] += interaction

            attribution['details'][asset] = {
                'allocation_effect': allocation,
                'selection_effect': selection,
                'interaction_effect': interaction,
                'total_contribution': allocation + selection + interaction
            }

        # 总主动收益
        attribution['total_active_return'] = (
            attribution['allocation_effect'] +
            attribution['selection_effect'] +
            attribution['interaction_effect']
        )

        return attribution

    def calculate_risk_adjusted_performance(self) -> Dict:
        """
        计算风险调整后的收益指标

        Returns:
            风险调整收益字典
        """
        if not self.equity_history or not self.returns_history:
            return {'error': '缺少历史数据'}

        equity_values = [v for _, v in self.equity_history]
        returns_values = [r for _, r in self.returns_history]

        # 总收益率
        total_return = (equity_values[-1] - equity_values[0]) / equity_values[0]

        # 风险指标
        risk_metrics = self.calculate_risk_metrics(equity_values, returns_values)

        if 'error' in risk_metrics:
            return risk_metrics

        # 风险调整后的收益
        sharpe = risk_metrics['sharpe_ratio'].get('sharpe_ratio', 0)
        sortino = risk_metrics['sortino_ratio'].get('sortino_ratio', 0)
        max_dd = risk_metrics['max_drawdown'].get('max_drawdown', 0)

        # Calmar比率 (年化收益 / 最大回撤)
        days = len(returns_values)
        years = days / 252.0
        annual_return = self._calculate_annualized_return(total_return, years) if years > 0 else 0
        calmar = annual_return / max_dd if max_dd > 0 else 0

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_dd,
            'volatility': risk_metrics['volatility'].get('annual_volatility', 0),
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'risk_adjusted_return': total_return / max_dd if max_dd > 0 else 0,
            'return_to_risk_ratio': total_return / risk_metrics['volatility'].get('annual_volatility', 0.01)
        }

    def format_performance_report(self, result: Dict, format_type: str = 'markdown') -> str:
        """
        格式化收益追踪报告

        Args:
            result: track_performance()返回的结果
            format_type: 报告格式 ('markdown' 或 'text')

        Returns:
            格式化后的报告文本
        """
        if format_type == 'markdown':
            return self._format_markdown_report(result)
        else:
            return self._format_text_report(result)

    def _format_markdown_report(self, result: Dict) -> str:
        """生成Markdown格式的收益报告"""
        lines = []

        # 标题
        lines.append("## 📈 收益追踪对比")
        lines.append("")
        lines.append(f"**追踪日期**: {result['track_date']}")
        lines.append(f"**基准日期**: {self.base_date} (已运行{result['days_since_base']}天/{result['years_since_base']}年)")
        lines.append("")

        # 收益概况（使用配置格式化金额）
        lines.append("### 收益概况")
        lines.append("")
        if self.config:
            lines.append(f"- **初始资金**: {self.config.format_amount(result['initial_capital'])}")
            lines.append(f"- **当前资金**: {self.config.format_amount(result['current_capital'])}")
        else:
            lines.append(f"- **初始资金**: ¥{result['initial_capital']:,.0f}")
            lines.append(f"- **当前资金**: ¥{result['current_capital']:,.0f}")
        lines.append(f"- **总收益率**: {result['total_return_pct']}")
        lines.append(f"- **年化收益率**: {result['annual_return_pct']}")
        lines.append(f"- **目标年化**: {result['target_annual_return_pct']}")
        lines.append("")

        # 基准对比
        lines.append("### 📊 基准对比(沪深300)")
        lines.append("")
        lines.append("| 指标 | 我的收益 | 沪深300 | 超额收益 |")
        lines.append("|------|---------|---------|---------|")
        lines.append(
            f"| 总收益率 | {result['total_return_pct']} | "
            f"{result['hs300_return_pct']} | {result['excess_return_pct']} |"
        )

        excess = float(result['excess_return_pct'][:-1])
        if excess > 0:
            lines.append(f"\n✅ **跑赢沪深300约{excess:.2f}%!**")
        else:
            lines.append(f"\n⚠️ **落后沪深300约{abs(excess):.2f}%**")
        lines.append("")

        # 目标说明
        lines.append("### 🎯 收益目标体系")
        lines.append("")
        lines.append(f"**长期目标**: 年化{self.target_annual_return*100:.0f}%,穿越牛熊")
        lines.append("")
        lines.append("**短期目标**(到2026年底,按优先级排序):")

        # 使用配置获取最终目标名称
        if self.config:
            final_target_name = self.config.format_target_description(self.final_target, len(self.stage_targets) - 1)
        else:
            final_target_name = f"{self.final_target/10000:.0f}万"

        lines.append(f"1. 🥇 资金达到{final_target_name} (最优先)")
        lines.append("2. 🥈 跑赢沪深300 (次优先)")
        lines.append(f"3. 🥉 资金涨幅达到{self.target_annual_return*100:.0f}% (第三优先)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 三大目标达成情况
        lines.append("### 📊 短期目标达成情况")
        lines.append("")

        achievements = result['achievements']

        # 目标1: 最终目标 (最优先) - 使用 target_100w 保持兼容
        target_100w = achievements['target_100w']
        status_emoji = "✅" if target_100w['achieved'] else "🔄"
        lines.append(f"#### {status_emoji} 🥇 优先级1: {target_100w['name']}")
        lines.append(f"- 当前进度: {target_100w['progress_pct']}")
        if not target_100w['achieved']:
            remaining = self.final_target - result['current_capital']
            if self.config:
                remaining_text = self.config.format_amount(remaining)
            else:
                remaining_text = f"¥{remaining:,.0f} ({remaining/10000:.1f}万)"
            lines.append(f"- 还需: {remaining_text}")
            lines.append(f"- **优先级**: 最高 - 这是首要目标")
        lines.append("")

        # 目标2: 跑赢沪深300 (次优先)
        beat_hs300 = achievements['beat_hs300']
        status_emoji = "✅" if beat_hs300['achieved'] else "❌"
        lines.append(f"#### {status_emoji} 🥈 优先级2: 跑赢沪深300")
        if beat_hs300['achieved']:
            lines.append(f"- 超额收益: {beat_hs300['excess_return_pct']}")
        else:
            lines.append(f"- 落后幅度: {beat_hs300['excess_return_pct']}")
        lines.append(f"- **优先级**: 次高 - 在达成{final_target_name}基础上追求超额收益")
        lines.append("")

        # 目标3: 翻倍 (第三优先)
        double = achievements['double_capital']
        status_emoji = "✅" if double['achieved'] else "🔄"
        lines.append(f"#### {status_emoji} 🥉 优先级3: {double['name']}")
        lines.append(f"- 当前进度: {double['progress_pct']}")
        if self.config:
            double_target_text = self.config.format_amount(result['double_target'])
        else:
            double_target_text = f"¥{result['double_target']:,.0f}"
        lines.append(f"- 翻倍目标: {double_target_text}")
        if not double['achieved']:
            remaining = result['double_target'] - result['current_capital']
            if self.config:
                remaining_text = self.config.format_amount(remaining)
            else:
                remaining_text = f"¥{remaining:,.0f} ({remaining/10000:.1f}万)"
            lines.append(f"- 还需: {remaining_text}")
        lines.append(f"- **优先级**: 第三 - 在前两个目标基础上的进阶目标")
        lines.append("")

        # 阶段性目标
        lines.append("### 🏆 阶段性目标进度")
        lines.append("")

        stage_info = result['current_stage']
        completed_count = stage_info['completed_count']
        total_stages = stage_info['total_stages']

        lines.append(f"**已完成阶段**: {completed_count}/{total_stages}")
        lines.append("")

        # 已完成的阶段
        if stage_info['completed_stages']:
            for stage in stage_info['completed_stages']:
                lines.append(f"- ✅ 阶段{stage['stage']}: {stage['target_text']}")
            lines.append("")

        # 当前阶段
        if stage_info['next_stage']:
            next_stage = stage_info['next_stage']
            lines.append(f"**当前阶段**: 第{next_stage['stage']}阶段 - 目标{next_stage['target_text']}")
            lines.append(f"- 进度: {stage_info['current_stage_progress_pct']}")
            lines.append(f"- 还需: {next_stage['remaining_text']}")
            lines.append("")
        else:
            lines.append("🎉 **恭喜!所有阶段目标已完成!**")
            lines.append("")

        # 警告信息
        if result['warnings']:
            lines.append("### ⚠️ 注意事项")
            lines.append("")
            for warning in result['warnings']:
                lines.append(f"- {warning}")
            lines.append("")

        # 优化建议
        if result['suggestions']:
            lines.append("### 💡 优化建议")
            lines.append("")
            for suggestion in result['suggestions']:
                lines.append(f"- {suggestion}")
            lines.append("")

        return "\n".join(lines)

    def _format_text_report(self, result: Dict) -> str:
        """生成纯文本格式的收益报告"""
        lines = []

        lines.append("=" * 60)
        lines.append("收益追踪对比报告")
        lines.append("=" * 60)
        lines.append(f"追踪日期: {result['track_date']}")
        lines.append(f"运行天数: {result['days_since_base']}天")
        lines.append("")

        lines.append("收益概况:")
        lines.append(f"  当前资金: ¥{result['current_capital']:,.0f}")
        lines.append(f"  总收益率: {result['total_return_pct']}")
        lines.append(f"  年化收益: {result['annual_return_pct']}")
        lines.append("")

        lines.append("基准对比:")
        lines.append(f"  我的收益: {result['total_return_pct']}")
        lines.append(f"  沪深300: {result['hs300_return_pct']}")
        lines.append(f"  超额收益: {result['excess_return_pct']}")
        lines.append("")

        lines.append("三大目标:")
        achievements = result['achievements']
        lines.append(f"  [{'√' if achievements['target_100w']['achieved'] else ' '}] 资金达到100万 ({achievements['target_100w']['progress_pct']})")
        lines.append(f"  [{'√' if achievements['beat_hs300']['achieved'] else ' '}] 跑赢沪深300 ({achievements['beat_hs300']['excess_return_pct']})")
        lines.append(f"  [{'√' if achievements['double_capital']['achieved'] else ' '}] 资金翻倍 ({achievements['double_capital']['progress_pct']})")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


# 示例用法
if __name__ == "__main__":
    # 创建追踪器
    tracker = PerformanceTracker({
        'initial_capital': 500000,  # 50万起步
        'base_date': '2025-01-01',
        'target_annual_return': 0.15  # 15%年化
    })

    # 追踪当前收益
    result = tracker.track_performance(
        current_capital=550000,  # 当前55万
        hs300_current=4538.22,   # 沪深300当前点位
        hs300_base=3145.0,       # 2025.1.1基准点位
        current_date='2025-10-20'
    )

    # 打印报告
    report = tracker.format_performance_report(result, format_type='markdown')
    print(report)
