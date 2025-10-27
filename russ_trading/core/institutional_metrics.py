#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机构级绩效评估指标计算模块
Institutional-Grade Performance Metrics Calculator

提供Goldman Sachs/Morgan Stanley标准的机构级指标计算
包括: Information Ratio, Tracking Error, Up/Down Capture, HHI, Omega, Max DD Duration

Author: Claude Code
Date: 2025-10-21
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class InstitutionalMetricsCalculator:
    """机构级指标计算器 (Goldman Sachs标准)"""

    def __init__(self, benchmark_returns: Optional[List[float]] = None):
        """
        初始化计算器

        Args:
            benchmark_returns: 基准收益率序列（如沪深300），用于计算IR和TE
        """
        self.benchmark_returns = benchmark_returns

    def calculate_information_ratio(
        self,
        portfolio_returns: List[float],
        benchmark_returns: Optional[List[float]] = None,
        periods_per_year: int = 252
    ) -> Optional[float]:
        """
        计算信息比率 (Information Ratio)

        公式: (组合收益率 - 基准收益率) / 跟踪误差
        衡量主动管理的价值，IR > 0.75为顶级水平

        Args:
            portfolio_returns: 组合日收益率
            benchmark_returns: 基准日收益率（可选，未提供则使用初始化时的基准）
            periods_per_year: 每年交易周期数

        Returns:
            信息比率，无法计算时返回None
        """
        if benchmark_returns is None:
            benchmark_returns = self.benchmark_returns

        if not portfolio_returns or not benchmark_returns:
            logger.warning("收益率数据不足，无法计算信息比率")
            return None

        if len(portfolio_returns) != len(benchmark_returns):
            logger.warning("组合与基准长度不一致")
            return None

        try:
            port_array = np.array(portfolio_returns)
            bench_array = np.array(benchmark_returns)

            # 计算主动收益
            active_returns = port_array - bench_array

            # 计算年化主动收益
            mean_active = np.mean(active_returns) * periods_per_year

            # 计算跟踪误差（年化）
            tracking_error = np.std(active_returns, ddof=1) * np.sqrt(periods_per_year)

            if tracking_error == 0:
                logger.warning("跟踪误差为0，无法计算信息比率")
                return None

            ir = mean_active / tracking_error

            return ir

        except Exception as e:
            logger.error(f"计算信息比率失败: {e}")
            return None

    def calculate_tracking_error(
        self,
        portfolio_returns: List[float],
        benchmark_returns: Optional[List[float]] = None,
        periods_per_year: int = 252
    ) -> Optional[float]:
        """
        计算跟踪误差 (Tracking Error)

        公式: std(组合收益率 - 基准收益率) * sqrt(252)
        衡量与基准的偏离程度，年化标准差

        Args:
            portfolio_returns: 组合日收益率
            benchmark_returns: 基准日收益率
            periods_per_year: 每年交易周期数

        Returns:
            跟踪误差（年化百分比），无法计算时返回None
        """
        if benchmark_returns is None:
            benchmark_returns = self.benchmark_returns

        if not portfolio_returns or not benchmark_returns:
            logger.warning("收益率数据不足，无法计算跟踪误差")
            return None

        if len(portfolio_returns) != len(benchmark_returns):
            logger.warning("组合与基准长度不一致")
            return None

        try:
            port_array = np.array(portfolio_returns)
            bench_array = np.array(benchmark_returns)

            # 计算主动收益
            active_returns = port_array - bench_array

            # 年化跟踪误差
            te = np.std(active_returns, ddof=1) * np.sqrt(periods_per_year)

            return te

        except Exception as e:
            logger.error(f"计算跟踪误差失败: {e}")
            return None

    def calculate_capture_ratios(
        self,
        portfolio_returns: List[float],
        benchmark_returns: Optional[List[float]] = None
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        计算上行/下行捕获比率 (Up/Down Capture Ratio)

        Up Capture = 组合牛市平均收益 / 基准牛市平均收益
        Down Capture = 组合熊市平均收益 / 基准熊市平均收益

        理想状态：Up > 100%, Down < 100%（牛市跑赢，熊市抗跌）

        Args:
            portfolio_returns: 组合日收益率
            benchmark_returns: 基准日收益率

        Returns:
            (上行捕获比率, 下行捕获比率)，无法计算时返回(None, None)
        """
        if benchmark_returns is None:
            benchmark_returns = self.benchmark_returns

        if not portfolio_returns or not benchmark_returns:
            logger.warning("收益率数据不足，无法计算捕获比率")
            return None, None

        if len(portfolio_returns) != len(benchmark_returns):
            logger.warning("组合与基准长度不一致")
            return None, None

        try:
            port_array = np.array(portfolio_returns)
            bench_array = np.array(benchmark_returns)

            # 上行期（基准为正）
            up_mask = bench_array > 0
            up_port = port_array[up_mask]
            up_bench = bench_array[up_mask]

            # 下行期（基准为负）
            down_mask = bench_array < 0
            down_port = port_array[down_mask]
            down_bench = bench_array[down_mask]

            # 计算上行捕获
            up_capture = None
            if len(up_port) > 0 and np.mean(up_bench) != 0:
                up_capture = np.mean(up_port) / np.mean(up_bench)

            # 计算下行捕获
            down_capture = None
            if len(down_port) > 0 and np.mean(down_bench) != 0:
                down_capture = np.mean(down_port) / np.mean(down_bench)

            return up_capture, down_capture

        except Exception as e:
            logger.error(f"计算捕获比率失败: {e}")
            return None, None

    def calculate_hhi_concentration(
        self,
        position_weights: List[float]
    ) -> Optional[float]:
        """
        计算HHI集中度 (Herfindahl-Hirschman Index)

        公式: Σ(权重^2)
        HHI范围: [1/N, 1]
        - 完全分散: 1/N (如10个股票均仓为0.1)
        - 完全集中: 1.0 (单一持仓)

        有效标的数 = 1 / HHI

        Args:
            position_weights: 各持仓的权重列表（百分比形式，如[0.3, 0.25, 0.2, 0.15, 0.1]）

        Returns:
            HHI指数，无法计算时返回None
        """
        if not position_weights:
            logger.warning("持仓权重数据为空")
            return None

        try:
            weights = np.array(position_weights)

            # 确保权重和为1
            weights = weights / np.sum(weights)

            # 计算HHI
            hhi = np.sum(weights ** 2)

            return hhi

        except Exception as e:
            logger.error(f"计算HHI集中度失败: {e}")
            return None

    def calculate_omega_ratio(
        self,
        returns: List[float],
        threshold: float = 0.0
    ) -> Optional[float]:
        """
        计算Omega比率 (Omega Ratio)

        公式: E[max(R-L, 0)] / E[max(L-R, 0)]
        其中L为阈值收益率，通常取0

        Omega > 1表示正期望，值越大越好
        考虑收益分布的全貌（不仅仅是均值和方差）

        Args:
            returns: 收益率序列
            threshold: 阈值收益率（默认0）

        Returns:
            Omega比率，无法计算时返回None
        """
        if not returns or len(returns) < 2:
            logger.warning("收益率数据不足，无法计算Omega比率")
            return None

        try:
            returns_array = np.array(returns)

            # 超额收益（高于阈值的部分）
            gains = np.maximum(returns_array - threshold, 0)

            # 损失（低于阈值的部分）
            losses = np.maximum(threshold - returns_array, 0)

            expected_gains = np.mean(gains)
            expected_losses = np.mean(losses)

            if expected_losses == 0:
                logger.info("无损失期，Omega比率极高")
                return None  # 或返回极大值

            omega = expected_gains / expected_losses

            return omega

        except Exception as e:
            logger.error(f"计算Omega比率失败: {e}")
            return None

    def calculate_max_drawdown_duration(
        self,
        cumulative_returns: List[float]
    ) -> Optional[int]:
        """
        计算最大回撤持续期 (Max Drawdown Duration)

        从峰值到谷底再恢复到峰值的最长天数
        衡量投资者承受痛苦的时间长度

        Args:
            cumulative_returns: 累计收益率序列

        Returns:
            最大回撤持续天数，无法计算时返回None
        """
        if not cumulative_returns or len(cumulative_returns) < 2:
            logger.warning("数据不足，无法计算回撤持续期")
            return None

        try:
            cum_returns = np.array(cumulative_returns)

            # 计算历史最高点
            running_max = np.maximum.accumulate(cum_returns)

            # 标记是否处于回撤期
            in_drawdown = cum_returns < running_max

            # 计算所有回撤期的长度
            max_duration = 0
            current_duration = 0

            for i, is_dd in enumerate(in_drawdown):
                if is_dd:
                    current_duration += 1
                    max_duration = max(max_duration, current_duration)
                else:
                    current_duration = 0

            return max_duration if max_duration > 0 else None

        except Exception as e:
            logger.error(f"计算最大回撤持续期失败: {e}")
            return None

    def format_institutional_metrics_report(
        self,
        portfolio_returns: List[float],
        cumulative_returns: List[float],
        position_weights: List[float],
        benchmark_returns: Optional[List[float]] = None,
        periods_per_year: int = 252
    ) -> str:
        """
        生成机构级绩效评估报告 (Goldman Sachs标准)

        Args:
            portfolio_returns: 组合日收益率
            cumulative_returns: 累计收益率序列
            position_weights: 持仓权重列表
            benchmark_returns: 基准收益率（可选）
            periods_per_year: 每年交易周期数

        Returns:
            格式化的Markdown报告
        """
        lines = []

        lines.append("## 🏆 机构级绩效评估 (Goldman Sachs标准)")
        lines.append("")

        # 计算所有指标
        ir = self.calculate_information_ratio(portfolio_returns, benchmark_returns, periods_per_year)
        te = self.calculate_tracking_error(portfolio_returns, benchmark_returns, periods_per_year)
        up_cap, down_cap = self.calculate_capture_ratios(portfolio_returns, benchmark_returns)
        hhi = self.calculate_hhi_concentration(position_weights)
        omega = self.calculate_omega_ratio(portfolio_returns, threshold=0.0)
        max_dd_duration = self.calculate_max_drawdown_duration(cumulative_returns)

        # 主动管理价值部分
        lines.append("### 📊 主动管理价值")
        lines.append("")
        lines.append("| 指标 | 数值 | 评级 | 说明 |")
        lines.append("|------|------|------|------|")

        if ir is not None:
            ir_rating = self._rate_information_ratio(ir)
            lines.append(f"| **Information Ratio** | {ir:.2f} | {ir_rating} | 超额收益稳定性 |")
        else:
            lines.append("| **Information Ratio** | N/A | - | 需要基准数据 |")

        if te is not None:
            te_level = self._assess_tracking_error(te)
            lines.append(f"| **Tracking Error** | {te*100:.1f}% | {te_level} | vs沪深300偏离度 |")
        else:
            lines.append("| **Tracking Error** | N/A | - | 需要基准数据 |")

        if up_cap is not None:
            up_rating = self._rate_up_capture(up_cap)
            lines.append(f"| **Up Capture** | {up_cap*100:.0f}% | {up_rating} | 牛市捕获能力 |")
        else:
            lines.append("| **Up Capture** | N/A | - | 需要基准数据 |")

        if down_cap is not None:
            down_rating = self._rate_down_capture(down_cap)
            down_desc = f"熊市{'多跌' if down_cap > 1 else '抗跌'}{abs(down_cap-1)*100:.0f}%"
            lines.append(f"| **Down Capture** | {down_cap*100:.0f}% | {down_rating} | {down_desc} |")
        else:
            lines.append("| **Down Capture** | N/A | - | 需要基准数据 |")

        lines.append("")

        # 组合特征评估部分
        lines.append("### 🎯 组合特征评估")
        lines.append("")

        if hhi is not None:
            effective_n = 1.0 / hhi
            concentration_level = self._assess_concentration(hhi)
            lines.append(f"- **HHI集中度**: {hhi:.2f} ({concentration_level}, {effective_n:.1f}个有效标的)")

        if max_dd_duration is not None:
            lines.append(f"- **最大回撤周期**: 历史最长{max_dd_duration}天")

        if omega is not None:
            omega_rating = self._rate_omega(omega)
            lines.append(f"- **Omega(0%)**: {omega:.2f} ({omega_rating})")

        lines.append("")

        # 添加说明
        lines.append("**机构级指标说明**:")
        lines.append("")
        lines.append("- **Information Ratio**: >0.75为顶级主动管理，衡量每单位风险的超额收益")
        lines.append("- **Tracking Error**: 与基准的年化偏离度，主动型基金通常5%-15%")
        lines.append("- **Up/Down Capture**: 理想状态是Up>100%且Down<100%（牛市跑赢，熊市抗跌）")
        lines.append("- **HHI集中度**: <0.15为分散，0.15-0.25为适度，>0.25为高度集中")
        lines.append("- **Omega比率**: >1表示正期望，>1.5为优秀，考虑收益分布全貌")
        lines.append("- **最大回撤周期**: 衡量投资者承受痛苦的时间长度，越短越好")
        lines.append("")

        return '\n'.join(lines)

    def _rate_information_ratio(self, ir: float) -> str:
        """评级信息比率"""
        if ir >= 0.75:
            return "⭐⭐⭐⭐⭐"
        elif ir >= 0.5:
            return "⭐⭐⭐⭐"
        elif ir >= 0.25:
            return "⭐⭐⭐"
        elif ir >= 0:
            return "⭐⭐"
        else:
            return "⭐"

    def _assess_tracking_error(self, te: float) -> str:
        """评估跟踪误差"""
        if te < 0.05:
            return "🟢 低"
        elif te < 0.15:
            return "🟡 适中"
        else:
            return "🔴 高"

    def _rate_up_capture(self, up_cap: float) -> str:
        """评级上行捕获"""
        if up_cap >= 1.2:
            return "✅✅✅"
        elif up_cap >= 1.1:
            return "✅✅"
        elif up_cap >= 1.0:
            return "✅"
        else:
            return "⚠️"

    def _rate_down_capture(self, down_cap: float) -> str:
        """评级下行捕获（越低越好）"""
        if down_cap <= 0.8:
            return "✅✅✅"
        elif down_cap <= 0.9:
            return "✅✅"
        elif down_cap <= 1.0:
            return "✅"
        else:
            return "⚠️"

    def _assess_concentration(self, hhi: float) -> str:
        """评估集中度"""
        if hhi < 0.15:
            return "分散"
        elif hhi < 0.25:
            return "适度集中"
        else:
            return "高度集中"

    def _rate_omega(self, omega: float) -> str:
        """评级Omega比率"""
        if omega >= 1.5:
            return "正期望强"
        elif omega >= 1.0:
            return "正期望"
        else:
            return "负期望"


# 示例用法
if __name__ == "__main__":
    # 模拟数据
    np.random.seed(42)

    # 组合收益率（日度，年化60%对应日度0.19%左右）
    portfolio_returns = np.random.normal(0.0019, 0.025, 252)

    # 基准收益率（沪深300，年化10%）
    benchmark_returns = np.random.normal(0.0004, 0.015, 252)

    # 累计收益率
    cumulative_returns = np.cumprod(1 + portfolio_returns) - 1

    # 持仓权重（5个股票）
    position_weights = [0.35, 0.25, 0.20, 0.12, 0.08]

    # 创建计算器
    calculator = InstitutionalMetricsCalculator(benchmark_returns=benchmark_returns.tolist())

    # 计算各项指标
    ir = calculator.calculate_information_ratio(portfolio_returns.tolist())
    te = calculator.calculate_tracking_error(portfolio_returns.tolist())
    up_cap, down_cap = calculator.calculate_capture_ratios(portfolio_returns.tolist())
    hhi = calculator.calculate_hhi_concentration(position_weights)
    omega = calculator.calculate_omega_ratio(portfolio_returns.tolist())
    max_dd_duration = calculator.calculate_max_drawdown_duration(cumulative_returns.tolist())

    print(f"Information Ratio: {ir:.2f}")
    print(f"Tracking Error: {te*100:.1f}%")
    print(f"Up Capture: {up_cap*100:.0f}%")
    print(f"Down Capture: {down_cap*100:.0f}%")
    print(f"HHI: {hhi:.2f} (有效标的: {1/hhi:.1f}个)")
    print(f"Omega: {omega:.2f}")
    print(f"最大回撤周期: {max_dd_duration}天")

    # 生成报告
    report = calculator.format_institutional_metrics_report(
        portfolio_returns.tolist(),
        cumulative_returns.tolist(),
        position_weights,
        benchmark_returns.tolist()
    )
    print("\n" + report)
