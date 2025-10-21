#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能指标计算模块
Performance Metrics Calculator

提供夏普比率、索提诺比率等性能指标计算

Author: Claude Code
Date: 2025-10-21
"""

import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PerformanceMetricsCalculator:
    """性能指标计算器"""

    def __init__(self, risk_free_rate: float = 0.025):
        """
        初始化计算器

        Args:
            risk_free_rate: 无风险利率（年化），默认2.5%（中国10年期国债收益率）
        """
        self.risk_free_rate = risk_free_rate

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        periods_per_year: int = 252
    ) -> Optional[float]:
        """
        计算夏普比率 (Sharpe Ratio)

        公式: (年化收益率 - 无风险利率) / 年化波动率

        Args:
            returns: 日收益率序列
            periods_per_year: 每年交易周期数（日度=252，月度=12）

        Returns:
            夏普比率，无法计算时返回None
        """
        if not returns or len(returns) < 2:
            logger.warning("收益率数据不足，无法计算夏普比率")
            return None

        try:
            returns_array = np.array(returns)

            # 计算平均收益率（日度）
            mean_return = np.mean(returns_array)

            # 计算收益率标准差（日度）
            std_return = np.std(returns_array, ddof=1)

            if std_return == 0:
                logger.warning("收益率波动为0，无法计算夏普比率")
                return None

            # 年化
            annual_return = mean_return * periods_per_year
            annual_std = std_return * np.sqrt(periods_per_year)

            # 夏普比率
            sharpe = (annual_return - self.risk_free_rate) / annual_std

            return sharpe

        except Exception as e:
            logger.error(f"计算夏普比率失败: {e}")
            return None

    def calculate_sortino_ratio(
        self,
        returns: List[float],
        periods_per_year: int = 252,
        target_return: float = 0.0
    ) -> Optional[float]:
        """
        计算索提诺比率 (Sortino Ratio)

        公式: (年化收益率 - 目标收益率) / 下行波动率

        与夏普比率的区别：只考虑下行波动（负收益），更关注下行风险

        Args:
            returns: 日收益率序列
            periods_per_year: 每年交易周期数（日度=252，月度=12）
            target_return: 目标收益率（日度），默认0

        Returns:
            索提诺比率，无法计算时返回None
        """
        if not returns or len(returns) < 2:
            logger.warning("收益率数据不足，无法计算索提诺比率")
            return None

        try:
            returns_array = np.array(returns)

            # 计算平均收益率（日度）
            mean_return = np.mean(returns_array)

            # 计算下行偏差（只考虑低于目标收益率的部分）
            downside_returns = returns_array[returns_array < target_return]

            if len(downside_returns) == 0:
                logger.info("无下行收益，索提诺比率极高")
                return None  # 或者返回一个很大的值

            downside_std = np.std(downside_returns, ddof=1)

            if downside_std == 0:
                logger.warning("下行波动为0，无法计算索提诺比率")
                return None

            # 年化
            annual_return = mean_return * periods_per_year
            annual_downside_std = downside_std * np.sqrt(periods_per_year)

            # 索提诺比率
            sortino = (annual_return - target_return * periods_per_year) / annual_downside_std

            return sortino

        except Exception as e:
            logger.error(f"计算索提诺比率失败: {e}")
            return None

    def calculate_calmar_ratio(
        self,
        cumulative_returns: List[float],
        periods_per_year: int = 252
    ) -> Optional[float]:
        """
        计算卡玛比率 (Calmar Ratio)

        公式: 年化收益率 / 最大回撤

        Args:
            cumulative_returns: 累计收益率序列
            periods_per_year: 每年交易周期数

        Returns:
            卡玛比率，无法计算时返回None
        """
        if not cumulative_returns or len(cumulative_returns) < 2:
            logger.warning("数据不足，无法计算卡玛比率")
            return None

        try:
            cum_returns = np.array(cumulative_returns)

            # 计算年化收益率
            total_return = cum_returns[-1] - cum_returns[0]
            periods = len(cum_returns) - 1
            annual_return = (1 + total_return) ** (periods_per_year / periods) - 1

            # 计算最大回撤
            running_max = np.maximum.accumulate(cum_returns)
            drawdown = (cum_returns - running_max) / running_max
            max_drawdown = np.min(drawdown)

            if max_drawdown == 0:
                logger.warning("最大回撤为0，无法计算卡玛比率")
                return None

            # 卡玛比率
            calmar = annual_return / abs(max_drawdown)

            return calmar

        except Exception as e:
            logger.error(f"计算卡玛比率失败: {e}")
            return None

    def format_metrics_report(
        self,
        returns: List[float],
        cumulative_returns: Optional[List[float]] = None,
        periods_per_year: int = 252
    ) -> str:
        """
        生成性能指标报告

        Args:
            returns: 日收益率序列
            cumulative_returns: 累计收益率序列（可选）
            periods_per_year: 每年交易周期数

        Returns:
            格式化的Markdown报告
        """
        lines = []

        lines.append("### 📊 性能指标分析")
        lines.append("")

        # 计算夏普比率
        sharpe = self.calculate_sharpe_ratio(returns, periods_per_year)
        sortino = self.calculate_sortino_ratio(returns, periods_per_year)

        if sharpe is not None or sortino is not None:
            lines.append("| 指标 | 数值 | 评级 | 说明 |")
            lines.append("|------|------|------|------|")

            if sharpe is not None:
                sharpe_rating = self._rate_sharpe(sharpe)
                lines.append(f"| **夏普比率** | {sharpe:.2f} | {sharpe_rating} | 风险调整后收益 |")

            if sortino is not None:
                sortino_rating = self._rate_sortino(sortino)
                lines.append(f"| **索提诺比率** | {sortino:.2f} | {sortino_rating} | 下行风险调整后收益 |")

            # 如果有累计收益率数据，计算卡玛比率
            if cumulative_returns:
                calmar = self.calculate_calmar_ratio(cumulative_returns, periods_per_year)
                if calmar is not None:
                    calmar_rating = self._rate_calmar(calmar)
                    lines.append(f"| **卡玛比率** | {calmar:.2f} | {calmar_rating} | 最大回撤调整后收益 |")

            lines.append("")

            # 添加说明
            lines.append("**指标说明**:")
            lines.append("")
            lines.append("- **夏普比率**: 衡量单位风险的超额收益，>1为优秀，>2为卓越")
            lines.append("- **索提诺比率**: 只关注下行风险，适合保守投资者参考")
            lines.append("- **卡玛比率**: 衡量承受最大回撤的收益，>3为优秀")
            lines.append("")

        else:
            lines.append("⚠️ 数据不足，无法计算性能指标")
            lines.append("")

        return '\n'.join(lines)

    def _rate_sharpe(self, sharpe: float) -> str:
        """评级夏普比率"""
        if sharpe >= 2.0:
            return "🌟🌟🌟 卓越"
        elif sharpe >= 1.0:
            return "⭐⭐ 优秀"
        elif sharpe >= 0.5:
            return "⭐ 良好"
        elif sharpe >= 0:
            return "➡️ 中性"
        else:
            return "⚠️ 较差"

    def _rate_sortino(self, sortino: float) -> str:
        """评级索提诺比率"""
        if sortino >= 2.5:
            return "🌟🌟🌟 卓越"
        elif sortino >= 1.5:
            return "⭐⭐ 优秀"
        elif sortino >= 0.75:
            return "⭐ 良好"
        elif sortino >= 0:
            return "➡️ 中性"
        else:
            return "⚠️ 较差"

    def _rate_calmar(self, calmar: float) -> str:
        """评级卡玛比率"""
        if calmar >= 3.0:
            return "🌟🌟🌟 卓越"
        elif calmar >= 2.0:
            return "⭐⭐ 优秀"
        elif calmar >= 1.0:
            return "⭐ 良好"
        elif calmar >= 0:
            return "➡️ 中性"
        else:
            return "⚠️ 较差"


# 示例用法
if __name__ == "__main__":
    # 模拟日收益率数据
    np.random.seed(42)
    daily_returns = np.random.normal(0.001, 0.02, 252)  # 252个交易日

    # 计算累计收益率
    cumulative_returns = np.cumprod(1 + daily_returns) - 1

    # 创建计算器
    calculator = PerformanceMetricsCalculator()

    # 计算各项指标
    sharpe = calculator.calculate_sharpe_ratio(daily_returns.tolist())
    sortino = calculator.calculate_sortino_ratio(daily_returns.tolist())
    calmar = calculator.calculate_calmar_ratio(cumulative_returns.tolist())

    print(f"夏普比率: {sharpe:.2f}")
    print(f"索提诺比率: {sortino:.2f}")
    print(f"卡玛比率: {calmar:.2f}")

    # 生成报告
    report = calculator.format_metrics_report(
        daily_returns.tolist(),
        cumulative_returns.tolist()
    )
    print("\n" + report)
