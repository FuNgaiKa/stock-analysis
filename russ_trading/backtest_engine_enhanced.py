#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版回测引擎
基于现有回测引擎,新增:
1. 压力测试 (Stress Testing)
2. 蒙特卡洛模拟 (Monte Carlo Simulation)
3. 敏感性分析 (Sensitivity Analysis)
4. 多场景回测
5. 风险敞口分析

Author: Russ
Created: 2025-10-20
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

# 添加父目录到路径以便导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from russ_trading.risk_manager import RiskManager
except ImportError:
    RiskManager = None

logger = logging.getLogger(__name__)


class MarketScenario(Enum):
    """市场场景枚举"""
    NORMAL = "normal"              # 正常市场
    BULL = "bull"                  # 牛市
    BEAR = "bear"                  # 熊市
    HIGH_VOLATILITY = "high_vol"   # 高波动
    CRASH = "crash"                # 市场崩溃
    RECOVERY = "recovery"          # 市场恢复
    SIDEWAYS = "sideways"          # 横盘


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 100000
    commission: float = 0.0003      # 手续费率0.03%
    slippage: float = 0.0001        # 滑点0.01%
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_position: float = 0.90      # 最大仓位
    risk_free_rate: float = 0.03    # 无风险利率

    # 高级配置
    enable_leverage: bool = False   # 是否允许杠杆
    max_leverage: float = 1.0       # 最大杠杆倍数
    margin_call_threshold: float = 0.3  # 追加保证金阈值


@dataclass
class StressTestScenario:
    """压力测试场景"""
    name: str
    description: str
    price_shock: float              # 价格冲击 (如-0.20表示下跌20%)
    volatility_multiplier: float    # 波动率乘数
    correlation_change: float = 0   # 相关性变化
    liquidity_impact: float = 0     # 流动性影响
    duration_days: int = 1          # 持续天数


class BacktestEngineEnhanced:
    """增强版回测引擎"""

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        初始化增强版回测引擎

        Args:
            config: 回测配置对象
        """
        self.config = config or BacktestConfig()
        self.risk_manager = RiskManager(risk_free_rate=self.config.risk_free_rate) if RiskManager else None

        # 回测结果存储
        self.portfolio_values = []
        self.positions_history = []
        self.trades = []
        self.daily_returns = []
        self.equity_curve = []

        # 风险指标历史
        self.risk_metrics_history = []

    def run_simple_backtest(
        self,
        prices: pd.Series,
        signals: pd.Series,
        dates: Optional[pd.DatetimeIndex] = None
    ) -> Dict:
        """
        简单回测 (单资产,简化版)

        Args:
            prices: 价格序列
            signals: 交易信号 ('BUY', 'SELL', 'HOLD')
            dates: 日期索引

        Returns:
            回测结果字典
        """
        if dates is None:
            dates = prices.index if hasattr(prices, 'index') else range(len(prices))

        cash = self.config.initial_capital
        position = 0
        entry_price = 0
        entry_date = None

        portfolio_values = []
        daily_returns = []
        trades = []
        equity_curve = []

        for i, (date, price) in enumerate(zip(dates, prices)):
            signal = signals.iloc[i] if i < len(signals) else 'HOLD'

            # 检查止损止盈
            if position > 0 and entry_price > 0:
                current_return = (price - entry_price) / entry_price

                if self.config.stop_loss and current_return <= -self.config.stop_loss:
                    signal = 'STOP_LOSS'
                elif self.config.take_profit and current_return >= self.config.take_profit:
                    signal = 'TAKE_PROFIT'

            # 处理交易
            if signal in ['BUY', 'STRONG_BUY'] and position == 0:
                # 买入
                buy_price = price * (1 + self.config.slippage)
                max_shares = int((cash * self.config.max_position) / buy_price)

                if max_shares > 0:
                    cost = max_shares * buy_price
                    commission = cost * self.config.commission

                    cash -= (cost + commission)
                    position = max_shares
                    entry_price = buy_price
                    entry_date = date

            elif signal in ['SELL', 'STRONG_SELL', 'STOP_LOSS', 'TAKE_PROFIT'] and position > 0:
                # 卖出
                sell_price = price * (1 - self.config.slippage)
                revenue = position * sell_price
                commission = revenue * self.config.commission

                cash += (revenue - commission)

                # 记录交易
                trade_return = (sell_price - entry_price) / entry_price
                pnl = (sell_price - entry_price) * position - commission * 2

                trades.append({
                    'entry_date': entry_date,
                    'exit_date': date,
                    'entry_price': entry_price,
                    'exit_price': sell_price,
                    'shares': position,
                    'return': trade_return,
                    'pnl': pnl,
                    'signal': signal
                })

                position = 0
                entry_price = 0
                entry_date = None

            # 计算组合价值
            position_value = position * price if position > 0 else 0
            total_value = cash + position_value
            portfolio_values.append(total_value)
            equity_curve.append(total_value)

            # 计算日收益率
            if i > 0:
                daily_return = (total_value - portfolio_values[i-1]) / portfolio_values[i-1]
                daily_returns.append(daily_return)
            else:
                daily_returns.append(0)

        # 保存结果
        self.portfolio_values = portfolio_values
        self.trades = trades
        self.daily_returns = daily_returns
        self.equity_curve = equity_curve

        return self._generate_backtest_result()

    def run_stress_test(
        self,
        base_result: Dict,
        scenarios: Optional[List[StressTestScenario]] = None
    ) -> Dict:
        """
        压力测试

        Args:
            base_result: 基础回测结果
            scenarios: 压力测试场景列表

        Returns:
            压力测试结果
        """
        if scenarios is None:
            scenarios = self._get_default_stress_scenarios()

        stress_results = {}

        for scenario in scenarios:
            # 模拟压力场景
            stressed_returns = self._apply_stress_scenario(
                self.daily_returns,
                scenario
            )

            # 计算压力场景下的指标
            stressed_equity = self._calculate_equity_curve(stressed_returns)
            stressed_metrics = self._calculate_stressed_metrics(
                stressed_equity,
                stressed_returns
            )

            stress_results[scenario.name] = {
                'description': scenario.description,
                'final_value': stressed_equity[-1] if stressed_equity else 0,
                'total_return': (stressed_equity[-1] - self.config.initial_capital) / self.config.initial_capital if stressed_equity else 0,
                'max_drawdown': stressed_metrics.get('max_drawdown', 0),
                'worst_day': min(stressed_returns) if stressed_returns else 0,
                'volatility': stressed_metrics.get('volatility', 0),
                'var_95': stressed_metrics.get('var_95', 0),
                'survival_probability': stressed_metrics.get('survival_prob', 0)
            }

        return {
            'scenarios': stress_results,
            'base_metrics': self._get_base_metrics(base_result),
            'stress_summary': self._summarize_stress_results(stress_results)
        }

    def run_monte_carlo_simulation(
        self,
        n_simulations: int = 1000,
        n_days: int = 252,
        use_historical_returns: bool = True
    ) -> Dict:
        """
        蒙特卡洛模拟

        Args:
            n_simulations: 模拟次数
            n_days: 模拟天数
            use_historical_returns: 是否使用历史收益率分布

        Returns:
            蒙特卡洛模拟结果
        """
        if not self.daily_returns:
            return {'error': '需要先运行回测以获取历史收益率'}

        # 计算收益率统计
        returns_array = np.array(self.daily_returns)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)

        simulation_paths = []
        final_values = []

        for _ in range(n_simulations):
            if use_historical_returns:
                # 从历史收益率中随机抽样
                simulated_returns = np.random.choice(returns_array, size=n_days, replace=True)
            else:
                # 使用正态分布生成
                simulated_returns = np.random.normal(mean_return, std_return, n_days)

            # 计算模拟路径
            equity_path = [self.config.initial_capital]
            for ret in simulated_returns:
                equity_path.append(equity_path[-1] * (1 + ret))

            simulation_paths.append(equity_path)
            final_values.append(equity_path[-1])

        # 统计分析
        final_values = np.array(final_values)

        return {
            'n_simulations': n_simulations,
            'n_days': n_days,
            'simulation_paths': simulation_paths,
            'statistics': {
                'mean_final_value': np.mean(final_values),
                'median_final_value': np.median(final_values),
                'std_final_value': np.std(final_values),
                'percentile_5': np.percentile(final_values, 5),
                'percentile_25': np.percentile(final_values, 25),
                'percentile_75': np.percentile(final_values, 75),
                'percentile_95': np.percentile(final_values, 95),
                'probability_profit': np.sum(final_values > self.config.initial_capital) / n_simulations,
                'probability_loss_50pct': np.sum(final_values < self.config.initial_capital * 0.5) / n_simulations,
                'expected_return': (np.mean(final_values) - self.config.initial_capital) / self.config.initial_capital,
                'expected_shortfall_5pct': self._calculate_expected_shortfall(final_values, 0.05)
            }
        }

    def run_sensitivity_analysis(
        self,
        backtest_func: Callable,
        parameter_ranges: Dict[str, List]
    ) -> Dict:
        """
        敏感性分析

        Args:
            backtest_func: 回测函数
            parameter_ranges: 参数范围字典 {'param_name': [value1, value2, ...]}

        Returns:
            敏感性分析结果
        """
        sensitivity_results = {}

        for param_name, values in parameter_ranges.items():
            param_results = []

            for value in values:
                # 修改配置参数
                original_value = getattr(self.config, param_name, None)
                setattr(self.config, param_name, value)

                # 运行回测
                try:
                    result = backtest_func()
                    param_results.append({
                        'value': value,
                        'total_return': result.get('total_return', 0),
                        'sharpe_ratio': result.get('sharpe_ratio', 0),
                        'max_drawdown': result.get('max_drawdown', 0),
                        'win_rate': result.get('win_rate', 0)
                    })
                except Exception as e:
                    logger.error(f"参数 {param_name}={value} 回测失败: {e}")

                # 恢复原值
                if original_value is not None:
                    setattr(self.config, param_name, original_value)

            sensitivity_results[param_name] = param_results

        return sensitivity_results

    def run_multi_scenario_backtest(
        self,
        prices: pd.Series,
        signals: pd.Series,
        scenarios: Optional[List[MarketScenario]] = None
    ) -> Dict:
        """
        多场景回测

        Args:
            prices: 价格序列
            signals: 交易信号
            scenarios: 市场场景列表

        Returns:
            多场景回测结果
        """
        if scenarios is None:
            scenarios = [MarketScenario.NORMAL, MarketScenario.BULL,
                        MarketScenario.BEAR, MarketScenario.HIGH_VOLATILITY]

        scenario_results = {}

        for scenario in scenarios:
            # 调整价格和信号以模拟不同场景
            adjusted_prices, adjusted_signals = self._adjust_for_scenario(
                prices, signals, scenario
            )

            # 运行回测
            result = self.run_simple_backtest(adjusted_prices, adjusted_signals)

            scenario_results[scenario.value] = result

        return {
            'scenarios': scenario_results,
            'comparison': self._compare_scenarios(scenario_results)
        }

    def generate_comprehensive_report(
        self,
        include_stress_test: bool = True,
        include_monte_carlo: bool = True,
        format_type: str = 'markdown'
    ) -> str:
        """
        生成综合回测报告

        Args:
            include_stress_test: 是否包含压力测试
            include_monte_carlo: 是否包含蒙特卡洛模拟
            format_type: 输出格式 ('markdown' 或 'text')

        Returns:
            格式化的报告字符串
        """
        lines = []

        if format_type == 'markdown':
            lines.append("# 📊 增强版回测报告")
            lines.append("")
            lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            lines.append("")
            lines.append("---")
            lines.append("")

            # 基础回测结果
            lines.append("## 1. 基础回测结果")
            lines.append("")
            result = self._generate_backtest_result()
            lines.append(self._format_basic_results(result))
            lines.append("")

            # 风险指标
            if self.risk_manager and self.equity_curve and self.daily_returns:
                lines.append("## 2. 风险指标")
                lines.append("")
                risk_report = self.risk_manager.generate_risk_report(
                    equity_curve=self.equity_curve,
                    returns=self.daily_returns,
                    positions=[],
                    market_returns=None
                )
                lines.append(self.risk_manager.format_risk_report(risk_report, 'markdown'))
                lines.append("")

            # 压力测试
            if include_stress_test:
                lines.append("## 3. 压力测试")
                lines.append("")
                base_result = self._generate_backtest_result()
                stress_results = self.run_stress_test(base_result)
                lines.append(self._format_stress_test_results(stress_results))
                lines.append("")

            # 蒙特卡洛模拟
            if include_monte_carlo and self.daily_returns:
                lines.append("## 4. 蒙特卡洛模拟")
                lines.append("")
                mc_results = self.run_monte_carlo_simulation(n_simulations=1000)
                lines.append(self._format_monte_carlo_results(mc_results))
                lines.append("")

            lines.append("---")
            lines.append("")
            lines.append("**免责声明**: 回测结果基于历史数据,不代表未来表现。过去的业绩不能保证未来的结果。")

        else:  # text format
            lines.append("=" * 70)
            lines.append("增强版回测报告")
            lines.append("=" * 70)
            lines.append("")
            # ... (类似的文本格式输出)

        return "\n".join(lines)

    # ========== 私有辅助方法 ==========

    def _generate_backtest_result(self) -> Dict:
        """生成回测结果字典"""
        if not self.portfolio_values:
            return {}

        final_value = self.portfolio_values[-1]
        total_return = (final_value - self.config.initial_capital) / self.config.initial_capital

        # 交易统计
        wins = [t for t in self.trades if t['return'] > 0]
        win_rate = len(wins) / len(self.trades) if self.trades else 0

        return {
            'initial_capital': self.config.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_trades': len(self.trades),
            'win_rate': win_rate,
            'portfolio_values': self.portfolio_values,
            'daily_returns': self.daily_returns,
            'trades': self.trades
        }

    def _get_default_stress_scenarios(self) -> List[StressTestScenario]:
        """获取默认压力测试场景"""
        return [
            StressTestScenario(
                name="market_crash",
                description="市场崩盘: 单日下跌20%",
                price_shock=-0.20,
                volatility_multiplier=3.0,
                duration_days=1
            ),
            StressTestScenario(
                name="severe_bear",
                description="严重熊市: 持续下跌30%",
                price_shock=-0.30,
                volatility_multiplier=2.0,
                duration_days=20
            ),
            StressTestScenario(
                name="high_volatility",
                description="高波动: 波动率翻倍",
                price_shock=0,
                volatility_multiplier=2.0,
                duration_days=60
            ),
            StressTestScenario(
                name="flash_crash",
                description="闪电崩盘: 瞬间下跌15%后恢复",
                price_shock=-0.15,
                volatility_multiplier=5.0,
                duration_days=1
            ),
            StressTestScenario(
                name="slow_bleed",
                description="慢性失血: 持续小幅下跌",
                price_shock=-0.50,
                volatility_multiplier=1.2,
                duration_days=180
            )
        ]

    def _apply_stress_scenario(
        self,
        returns: List[float],
        scenario: StressTestScenario
    ) -> List[float]:
        """应用压力场景到收益率序列"""
        stressed_returns = returns.copy()

        # 应用价格冲击
        if scenario.price_shock != 0:
            shock_per_day = scenario.price_shock / scenario.duration_days
            for i in range(min(scenario.duration_days, len(stressed_returns))):
                stressed_returns[i] += shock_per_day

        # 应用波动率乘数
        if scenario.volatility_multiplier != 1.0:
            mean_ret = np.mean(stressed_returns)
            stressed_returns = [
                mean_ret + (r - mean_ret) * scenario.volatility_multiplier
                for r in stressed_returns
            ]

        return stressed_returns

    def _calculate_equity_curve(self, returns: List[float]) -> List[float]:
        """根据收益率计算权益曲线"""
        equity = [self.config.initial_capital]
        for ret in returns:
            equity.append(equity[-1] * (1 + ret))
        return equity

    def _calculate_stressed_metrics(
        self,
        equity_curve: List[float],
        returns: List[float]
    ) -> Dict:
        """计算压力场景下的指标"""
        if not equity_curve or not returns:
            return {}

        # 最大回撤
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd

        # 波动率
        volatility = np.std(returns) * np.sqrt(252) if returns else 0

        # VaR 95%
        var_95 = np.percentile(returns, 5) if returns else 0

        # 生存概率 (不触及破产线)
        bankruptcy_threshold = self.config.initial_capital * 0.5
        survival_prob = sum(1 for v in equity_curve if v > bankruptcy_threshold) / len(equity_curve)

        return {
            'max_drawdown': max_dd,
            'volatility': volatility,
            'var_95': var_95,
            'survival_prob': survival_prob
        }

    def _get_base_metrics(self, result: Dict) -> Dict:
        """获取基础回测指标"""
        return {
            'total_return': result.get('total_return', 0),
            'final_value': result.get('final_value', 0),
            'win_rate': result.get('win_rate', 0),
            'total_trades': result.get('total_trades', 0)
        }

    def _summarize_stress_results(self, stress_results: Dict) -> Dict:
        """汇总压力测试结果"""
        worst_scenario = None
        worst_return = float('inf')

        for name, result in stress_results.items():
            if result['total_return'] < worst_return:
                worst_return = result['total_return']
                worst_scenario = name

        return {
            'worst_scenario': worst_scenario,
            'worst_return': worst_return,
            'average_stressed_return': np.mean([r['total_return'] for r in stress_results.values()]),
            'scenarios_with_profit': sum(1 for r in stress_results.values() if r['total_return'] > 0)
        }

    def _calculate_expected_shortfall(self, values: np.ndarray, alpha: float) -> float:
        """计算期望损失 (CVaR)"""
        var = np.percentile(values, alpha * 100)
        return np.mean(values[values <= var])

    def _adjust_for_scenario(
        self,
        prices: pd.Series,
        signals: pd.Series,
        scenario: MarketScenario
    ) -> Tuple[pd.Series, pd.Series]:
        """根据市场场景调整价格和信号"""
        adjusted_prices = prices.copy()
        adjusted_signals = signals.copy()

        if scenario == MarketScenario.BULL:
            # 牛市: 价格普遍上涨,波动降低
            trend = np.linspace(1.0, 1.3, len(prices))
            adjusted_prices = prices * trend

        elif scenario == MarketScenario.BEAR:
            # 熊市: 价格普遍下跌
            trend = np.linspace(1.0, 0.7, len(prices))
            adjusted_prices = prices * trend

        elif scenario == MarketScenario.HIGH_VOLATILITY:
            # 高波动: 增加随机波动
            noise = np.random.normal(1.0, 0.05, len(prices))
            adjusted_prices = prices * noise

        elif scenario == MarketScenario.CRASH:
            # 崩盘: 前期正常,后期暴跌
            crash_point = len(prices) // 2
            multiplier = np.ones(len(prices))
            multiplier[crash_point:] = 0.7
            adjusted_prices = prices * multiplier

        # NORMAL 和其他场景保持不变

        return adjusted_prices, adjusted_signals

    def _compare_scenarios(self, scenario_results: Dict) -> Dict:
        """对比不同场景的结果"""
        comparison = {
            'best_scenario': None,
            'worst_scenario': None,
            'most_stable': None
        }

        best_return = float('-inf')
        worst_return = float('inf')
        lowest_volatility = float('inf')

        for name, result in scenario_results.items():
            ret = result.get('total_return', 0)

            if ret > best_return:
                best_return = ret
                comparison['best_scenario'] = name

            if ret < worst_return:
                worst_return = ret
                comparison['worst_scenario'] = name

            # 如果有波动率数据
            vol = result.get('volatility', float('inf'))
            if vol < lowest_volatility:
                lowest_volatility = vol
                comparison['most_stable'] = name

        return comparison

    def _format_basic_results(self, result: Dict) -> str:
        """格式化基础回测结果"""
        lines = []
        lines.append(f"- **初始资金**: {result.get('initial_capital', 0):,.0f} 元")
        lines.append(f"- **期末资金**: {result.get('final_value', 0):,.0f} 元")
        lines.append(f"- **总收益率**: {result.get('total_return', 0)*100:.2f}%")
        lines.append(f"- **总交易次数**: {result.get('total_trades', 0)}")
        lines.append(f"- **胜率**: {result.get('win_rate', 0)*100:.2f}%")
        return "\n".join(lines)

    def _format_stress_test_results(self, stress_results: Dict) -> str:
        """格式化压力测试结果"""
        lines = []

        lines.append("### 压力场景测试结果")
        lines.append("")
        lines.append("| 场景 | 描述 | 总收益率 | 最大回撤 | 最差单日 | VaR(95%) |")
        lines.append("|------|------|----------|----------|----------|----------|")

        for name, result in stress_results.get('scenarios', {}).items():
            lines.append(
                f"| {name} | {result['description']} | "
                f"{result['total_return']*100:.2f}% | "
                f"{result['max_drawdown']*100:.2f}% | "
                f"{result['worst_day']*100:.2f}% | "
                f"{result['var_95']*100:.2f}% |"
            )

        lines.append("")
        summary = stress_results.get('stress_summary', {})
        lines.append("### 压力测试总结")
        lines.append("")
        lines.append(f"- **最差场景**: {summary.get('worst_scenario', 'N/A')}")
        lines.append(f"- **最差收益率**: {summary.get('worst_return', 0)*100:.2f}%")
        lines.append(f"- **平均压力收益率**: {summary.get('average_stressed_return', 0)*100:.2f}%")

        return "\n".join(lines)

    def _format_monte_carlo_results(self, mc_results: Dict) -> str:
        """格式化蒙特卡洛模拟结果"""
        lines = []
        stats = mc_results.get('statistics', {})

        lines.append(f"**模拟次数**: {mc_results.get('n_simulations', 0)}")
        lines.append(f"**模拟天数**: {mc_results.get('n_days', 0)}")
        lines.append("")

        lines.append("### 模拟统计结果")
        lines.append("")
        lines.append(f"- **平均期末资金**: {stats.get('mean_final_value', 0):,.0f} 元")
        lines.append(f"- **中位数期末资金**: {stats.get('median_final_value', 0):,.0f} 元")
        lines.append(f"- **标准差**: {stats.get('std_final_value', 0):,.0f} 元")
        lines.append("")

        lines.append("### 分位数分析")
        lines.append("")
        lines.append(f"- **5%分位数**: {stats.get('percentile_5', 0):,.0f} 元")
        lines.append(f"- **25%分位数**: {stats.get('percentile_25', 0):,.0f} 元")
        lines.append(f"- **75%分位数**: {stats.get('percentile_75', 0):,.0f} 元")
        lines.append(f"- **95%分位数**: {stats.get('percentile_95', 0):,.0f} 元")
        lines.append("")

        lines.append("### 风险评估")
        lines.append("")
        lines.append(f"- **盈利概率**: {stats.get('probability_profit', 0)*100:.2f}%")
        lines.append(f"- **亏损50%以上概率**: {stats.get('probability_loss_50pct', 0)*100:.2f}%")
        lines.append(f"- **期望收益率**: {stats.get('expected_return', 0)*100:.2f}%")
        lines.append(f"- **期望损失(CVaR 5%)**: {stats.get('expected_shortfall_5pct', 0):,.0f} 元")

        return "\n".join(lines)


def demo_backtest():
    """示例: 演示增强版回测引擎的功能"""
    print("=" * 70)
    print("增强版回测引擎 - 演示")
    print("=" * 70)

    # 1. 创建模拟数据
    np.random.seed(42)
    n_days = 252
    dates = pd.date_range(start='2024-01-01', periods=n_days, freq='D')

    # 模拟价格 (带趋势和噪声)
    trend = np.linspace(100, 120, n_days)
    noise = np.random.normal(0, 5, n_days)
    prices = pd.Series(trend + noise, index=dates)

    # 模拟简单信号 (基于移动平均)
    ma_short = prices.rolling(window=20).mean()
    ma_long = prices.rolling(window=60).mean()

    signals = pd.Series('HOLD', index=dates)
    signals[ma_short > ma_long] = 'BUY'
    signals[ma_short < ma_long] = 'SELL'

    # 2. 创建回测引擎
    config = BacktestConfig(
        initial_capital=100000,
        commission=0.0003,
        stop_loss=0.08,
        take_profit=0.15
    )

    engine = BacktestEngineEnhanced(config)

    # 3. 运行回测
    print("\n[1/4] 运行基础回测...")
    result = engine.run_simple_backtest(prices, signals, dates)
    print(f"✅ 回测完成: 总收益率 {result['total_return']*100:.2f}%")

    # 4. 压力测试
    print("\n[2/4] 运行压力测试...")
    stress_results = engine.run_stress_test(result)
    print(f"✅ 压力测试完成: {len(stress_results['scenarios'])} 个场景")

    # 5. 蒙特卡洛模拟
    print("\n[3/4] 运行蒙特卡洛模拟...")
    mc_results = engine.run_monte_carlo_simulation(n_simulations=1000)
    print(f"✅ 模拟完成: 盈利概率 {mc_results['statistics']['probability_profit']*100:.2f}%")

    # 6. 生成报告
    print("\n[4/4] 生成综合报告...")
    report = engine.generate_comprehensive_report(
        include_stress_test=True,
        include_monte_carlo=True
    )

    print("\n" + "=" * 70)
    print(report)

    return engine, result


if __name__ == '__main__':
    demo_backtest()
