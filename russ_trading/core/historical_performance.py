#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史表现分析模块
Historical Performance Analyzer

分析历史持仓快照数据，生成回测报告

Author: Claude Code
Date: 2025-10-21
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class HistoricalPerformanceAnalyzer:
    """历史表现分析器"""

    def __init__(self, data_manager=None):
        """
        初始化分析器

        Args:
            data_manager: DataManager实例，用于读取历史快照
        """
        self.data_manager = data_manager

    def analyze_performance(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        分析历史表现

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            分析结果字典
        """
        if not self.data_manager:
            logger.warning("未提供DataManager，无法分析历史表现")
            return self._empty_result()

        try:
            # 获取历史快照
            snapshots = self.data_manager.get_snapshots(start_date, end_date)

            if not snapshots or len(snapshots) < 2:
                logger.warning("历史数据不足，至少需要2个快照")
                return self._empty_result()

            # 提取数据
            dates = [s.date for s in snapshots]
            capitals = [s.total_capital for s in snapshots]
            returns = [s.daily_return for s in snapshots]

            # 计算累计收益率
            initial_capital = capitals[0]
            final_capital = capitals[-1]
            total_return = (final_capital - initial_capital) / initial_capital

            # 计算最大回撤
            max_drawdown = self._calculate_max_drawdown(capitals)

            # 计算波动率（年化）
            volatility = self._calculate_volatility(returns)

            # 计算胜率
            win_rate = self._calculate_win_rate(returns)

            # 计算平均盈亏比
            profit_loss_ratio = self._calculate_profit_loss_ratio(returns)

            # 计算年化收益率
            days = len(snapshots) - 1
            annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0

            return {
                'has_data': True,
                'start_date': dates[0],
                'end_date': dates[-1],
                'trading_days': len(snapshots),
                'initial_capital': initial_capital,
                'final_capital': final_capital,
                'total_return': total_return,
                'annualized_return': annualized_return,
                'max_drawdown': max_drawdown,
                'volatility': volatility,
                'win_rate': win_rate,
                'profit_loss_ratio': profit_loss_ratio,
                'dates': dates,
                'capitals': capitals,
                'returns': returns
            }

        except Exception as e:
            logger.error(f"分析历史表现失败: {e}", exc_info=True)
            return self._empty_result()

    def _empty_result(self) -> Dict:
        """返回空结果"""
        return {
            'has_data': False,
            'message': '暂无历史数据'
        }

    def _calculate_max_drawdown(self, capitals: List[float]) -> float:
        """
        计算最大回撤

        Args:
            capitals: 资金序列

        Returns:
            最大回撤（负数）
        """
        if not capitals:
            return 0.0

        peak = capitals[0]
        max_dd = 0.0

        for capital in capitals:
            if capital > peak:
                peak = capital
            dd = (capital - peak) / peak
            if dd < max_dd:
                max_dd = dd

        return max_dd

    def _calculate_volatility(self, returns: List[float], periods_per_year: int = 365) -> float:
        """
        计算波动率（年化）

        Args:
            returns: 收益率序列
            periods_per_year: 每年周期数

        Returns:
            年化波动率
        """
        if not returns or len(returns) < 2:
            return 0.0

        import numpy as np
        returns_array = np.array(returns)
        std = np.std(returns_array, ddof=1)
        annual_volatility = std * np.sqrt(periods_per_year)

        return annual_volatility

    def _calculate_win_rate(self, returns: List[float]) -> float:
        """
        计算胜率

        Args:
            returns: 收益率序列

        Returns:
            胜率（0-1之间）
        """
        if not returns:
            return 0.0

        wins = sum(1 for r in returns if r > 0)
        total = len(returns)

        return wins / total if total > 0 else 0.0

    def _calculate_profit_loss_ratio(self, returns: List[float]) -> Optional[float]:
        """
        计算盈亏比

        Args:
            returns: 收益率序列

        Returns:
            盈亏比，无亏损时返回None
        """
        if not returns:
            return None

        profits = [r for r in returns if r > 0]
        losses = [abs(r) for r in returns if r < 0]

        if not profits or not losses:
            return None

        avg_profit = sum(profits) / len(profits)
        avg_loss = sum(losses) / len(losses)

        return avg_profit / avg_loss if avg_loss > 0 else None

    def format_performance_report(
        self,
        performance: Dict,
        include_metrics: bool = True
    ) -> str:
        """
        生成历史表现报告

        Args:
            performance: 分析结果
            include_metrics: 是否包含性能指标（夏普/索提诺比率）

        Returns:
            Markdown格式报告
        """
        if not performance.get('has_data'):
            return self._format_no_data_message(performance)

        lines = []

        lines.append("### 📈 历史表现回测")
        lines.append("")
        lines.append(f"**回测周期**: {performance['start_date']} 至 {performance['end_date']} ({performance['trading_days']}天)")
        lines.append("")

        # 收益指标
        lines.append("#### 💰 收益指标")
        lines.append("")
        lines.append("| 指标 | 数值 | 说明 |")
        lines.append("|------|------|------|")
        lines.append(f"| **初始资金** | ¥{performance['initial_capital']:,.0f} | 回测起始资金 |")
        lines.append(f"| **最终资金** | ¥{performance['final_capital']:,.0f} | 回测结束资金 |")
        lines.append(f"| **累计收益率** | {performance['total_return']*100:+.2f}% | 总回报 |")
        lines.append(f"| **年化收益率** | {performance['annualized_return']*100:+.2f}% | 折算年化 |")
        lines.append("")

        # 风险指标
        lines.append("#### ⚠️ 风险指标")
        lines.append("")
        lines.append("| 指标 | 数值 | 评级 |")
        lines.append("|------|------|------|")

        # 最大回撤
        max_dd = performance['max_drawdown']
        dd_rating = self._rate_drawdown(max_dd)
        lines.append(f"| **最大回撤** | {max_dd*100:.2f}% | {dd_rating} |")

        # 波动率
        volatility = performance['volatility']
        vol_rating = self._rate_volatility(volatility)
        lines.append(f"| **年化波动率** | {volatility*100:.2f}% | {vol_rating} |")

        # 胜率
        win_rate = performance['win_rate']
        wr_rating = self._rate_win_rate(win_rate)
        lines.append(f"| **胜率** | {win_rate*100:.1f}% | {wr_rating} |")

        # 盈亏比
        pl_ratio = performance['profit_loss_ratio']
        if pl_ratio:
            pl_rating = self._rate_profit_loss_ratio(pl_ratio)
            lines.append(f"| **盈亏比** | {pl_ratio:.2f} | {pl_rating} |")

        lines.append("")

        # 性能指标（如果有）
        if include_metrics and 'sharpe_ratio' in performance:
            lines.append("#### 📊 风险调整后收益")
            lines.append("")
            lines.append("| 指标 | 数值 | 评级 |")
            lines.append("|------|------|------|")

            if performance.get('sharpe_ratio'):
                sharpe = performance['sharpe_ratio']
                sharpe_rating = self._rate_sharpe(sharpe)
                lines.append(f"| **夏普比率** | {sharpe:.2f} | {sharpe_rating} |")

            if performance.get('sortino_ratio'):
                sortino = performance['sortino_ratio']
                sortino_rating = self._rate_sortino(sortino)
                lines.append(f"| **索提诺比率** | {sortino:.2f} | {sortino_rating} |")

            lines.append("")

        return '\n'.join(lines)

    def _format_no_data_message(self, performance: Dict) -> str:
        """格式化无数据消息"""
        lines = []
        lines.append("### 📈 历史表现回测")
        lines.append("")
        lines.append(f"⚠️ {performance.get('message', '暂无历史数据')}")
        lines.append("")
        lines.append("**建议**:")
        lines.append("")
        lines.append("- 使用 `DataManager` 记录每日持仓快照")
        lines.append("- 积累至少7天的历史数据后可查看回测")
        lines.append("- 参考文档: `russ_trading_strategy/data_manager.py`")
        lines.append("")
        return '\n'.join(lines)

    def _rate_drawdown(self, dd: float) -> str:
        """评级最大回撤"""
        if dd >= -0.05:
            return "✅ 优秀"
        elif dd >= -0.10:
            return "⭐ 良好"
        elif dd >= -0.15:
            return "➡️ 中性"
        elif dd >= -0.20:
            return "⚠️ 偏高"
        else:
            return "🚨 危险"

    def _rate_volatility(self, vol: float) -> str:
        """评级波动率"""
        if vol <= 0.15:
            return "✅ 低波动"
        elif vol <= 0.25:
            return "⭐ 中等"
        elif vol <= 0.35:
            return "➡️ 偏高"
        else:
            return "⚠️ 高波动"

    def _rate_win_rate(self, wr: float) -> str:
        """评级胜率"""
        if wr >= 0.60:
            return "🌟 卓越"
        elif wr >= 0.50:
            return "✅ 优秀"
        elif wr >= 0.45:
            return "⭐ 良好"
        else:
            return "⚠️ 偏低"

    def _rate_profit_loss_ratio(self, pl: float) -> str:
        """评级盈亏比"""
        if pl >= 2.0:
            return "🌟 卓越"
        elif pl >= 1.5:
            return "✅ 优秀"
        elif pl >= 1.0:
            return "⭐ 良好"
        else:
            return "⚠️ 偏低"

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


# 示例用法
if __name__ == "__main__":
    from russ_trading.managers.data_manager import DataManager

    # 创建数据管理器（使用测试数据目录）
    dm = DataManager(data_dir="data/russ_trading")

    # 创建分析器
    analyzer = HistoricalPerformanceAnalyzer(dm)

    # 分析历史表现
    performance = analyzer.analyze_performance()

    # 生成报告
    report = analyzer.format_performance_report(performance)
    print(report)
