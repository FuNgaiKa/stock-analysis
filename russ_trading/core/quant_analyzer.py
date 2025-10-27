#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化分析模块
Quantitative Analyzer

提供相关性矩阵、夏普比率、因子暴露等高级分析功能
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class QuantAnalyzer:
    """量化分析器"""

    def __init__(self):
        """初始化量化分析器"""
        pass

    def calculate_correlation_matrix(
        self,
        returns_data: Dict[str, pd.Series],
        window: int = 60
    ) -> pd.DataFrame:
        """
        计算相关性矩阵

        Args:
            returns_data: {资产名称: 收益率序列}
            window: 滚动窗口(交易日)

        Returns:
            相关性矩阵DataFrame
        """
        if not returns_data:
            return pd.DataFrame()

        # 转换为DataFrame
        df = pd.DataFrame(returns_data)

        # 计算相关性
        correlation = df.tail(window).corr()

        return correlation

    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.03
    ) -> float:
        """
        计算夏普比率

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率(年化)

        Returns:
            夏普比率
        """
        if len(returns) == 0:
            return 0.0

        # 年化收益
        annual_return = returns.mean() * 252

        # 年化波动率
        annual_vol = returns.std() * np.sqrt(252)

        if annual_vol == 0:
            return 0.0

        # 夏普比率
        sharpe = (annual_return - risk_free_rate) / annual_vol

        return sharpe

    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.03
    ) -> float:
        """
        计算索提诺比率 (只考虑下行波动)

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率

        Returns:
            索提诺比率
        """
        if len(returns) == 0:
            return 0.0

        # 年化收益
        annual_return = returns.mean() * 252

        # 下行偏差 (只计算负收益)
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return float('inf')  # 没有负收益

        downside_std = negative_returns.std() * np.sqrt(252)

        if downside_std == 0:
            return 0.0

        # 索提诺比率
        sortino = (annual_return - risk_free_rate) / downside_std

        return sortino

    def calculate_max_drawdown(self, returns: pd.Series) -> Tuple[float, int]:
        """
        计算最大回撤

        Args:
            returns: 收益率序列

        Returns:
            (最大回撤, 回撤天数)
        """
        if len(returns) == 0:
            return 0.0, 0

        # 累计收益
        cumulative = (1 + returns).cumprod()

        # 历史最高点
        running_max = cumulative.cummax()

        # 回撤序列
        drawdown = (cumulative - running_max) / running_max

        # 最大回撤
        max_dd = drawdown.min()

        # 回撤天数
        dd_duration = 0
        if max_dd < 0:
            # 找到最大回撤的位置
            max_dd_idx = drawdown.idxmin()
            # 找到该回撤开始的位置(之前的最高点)
            peak_idx = running_max[:max_dd_idx].idxmax()
            dd_duration = (max_dd_idx - peak_idx).days if hasattr(max_dd_idx - peak_idx, 'days') else 0

        return abs(max_dd), dd_duration

    def calculate_win_rate(self, returns: pd.Series) -> float:
        """
        计算胜率

        Args:
            returns: 收益率序列

        Returns:
            胜率 (0-1)
        """
        if len(returns) == 0:
            return 0.0

        wins = (returns > 0).sum()
        total = len(returns)

        return wins / total if total > 0 else 0.0

    def analyze_factor_exposure(
        self,
        positions: List[Dict],
        market_data: Dict = None
    ) -> Dict:
        """
        因子暴露分析 (简化版)

        Args:
            positions: 持仓列表
            market_data: 市场数据

        Returns:
            因子暴露分析结果
        """
        # 简化的因子分析
        # 实际应该基于Barra模型或Fama-French因子

        exposure = {
            'market_beta': 0.0,  # 市场因子
            'growth': 0.0,       # 成长因子
            'value': 0.0,        # 价值因子
            'size': 0.0,         # 规模因子
            'momentum': 0.0      # 动量因子
        }

        if not positions:
            return exposure

        total_weight = 0.0

        for pos in positions:
            asset_name = pos.get('asset_name', '')
            ratio = pos.get('position_ratio', 0)

            # 根据资产名称估算因子暴露
            # 这里是简化版,实际应该基于历史数据回归

            # 市场Beta (所有股票都有市场暴露)
            if any(kw in asset_name for kw in ['ETF', 'etf']):
                beta = 0.95  # ETF接近市场
            else:
                beta = 1.1   # 个股波动更大

            # 成长因子
            if any(kw in asset_name for kw in ['科技', '创业', '科创', '恒科']):
                growth = 0.8  # 强成长
            elif any(kw in asset_name for kw in ['白酒', '消费', '医药']):
                growth = 0.4  # 中等成长
            else:
                growth = 0.0

            # 价值因子
            if any(kw in asset_name for kw in ['银行', '煤炭', '钢铁', '化工']):
                value = 0.6   # 强价值
            elif any(kw in asset_name for kw in ['白酒']):
                value = 0.3   # 中等价值
            else:
                value = -0.3  # 负价值(成长股)

            # 规模因子
            if any(kw in asset_name for kw in ['沪深300', '上证50']):
                size = 0.5    # 大盘
            elif any(kw in asset_name for kw in ['中证500', '科创']):
                size = -0.3   # 中小盘
            else:
                size = 0.0

            # 动量因子 (简化,实际需要历史数据)
            momentum = 0.3  # 假设当前趋势向上

            # 加权
            exposure['market_beta'] += beta * ratio
            exposure['growth'] += growth * ratio
            exposure['value'] += value * ratio
            exposure['size'] += size * ratio
            exposure['momentum'] += momentum * ratio

            total_weight += ratio

        # 归一化
        if total_weight > 0:
            for key in exposure:
                exposure[key] /= total_weight

        return exposure

    def format_factor_exposure_report(self, exposure: Dict) -> str:
        """
        格式化因子暴露报告

        Args:
            exposure: 因子暴露数据

        Returns:
            Markdown格式报告
        """
        lines = []
        lines.append("### 📊 因子暴露分析")
        lines.append("")
        lines.append("| 因子类型 | 暴露度 | 评级 | 说明 |")
        lines.append("|---------|--------|------|------|")

        # 市场因子
        market_beta = exposure.get('market_beta', 0)
        if market_beta > 1.0:
            rating = "⚠️ 高Beta"
            desc = "高波动,震荡期需降低仓位"
        elif market_beta > 0.8:
            rating = "✅ 正常"
            desc = "与市场同步"
        else:
            rating = "📉 低Beta"
            desc = "防守型,牛市收益有限"

        lines.append(f"| **市场因子** | {market_beta:.2f} | {rating} | {desc} |")

        # 成长因子
        growth = exposure.get('growth', 0)
        if growth > 0.5:
            rating = "🚀 强成长"
            desc = "牛市占优"
        elif growth > 0:
            rating = "✅ 偏成长"
            desc = "符合成长风格"
        else:
            rating = "📊 非成长"
            desc = "偏价值或防守"

        lines.append(f"| **成长因子** | {growth:.2f} | {rating} | {desc} |")

        # 价值因子
        value = exposure.get('value', 0)
        if value > 0.3:
            rating = "💰 强价值"
            desc = "估值合理,长期持有"
        elif value > 0:
            rating = "✅ 偏价值"
            desc = "有一定安全边际"
        else:
            rating = "📈 非价值"
            desc = "更关注成长性"

        lines.append(f"| **价值因子** | {value:.2f} | {rating} | {desc} |")

        # 规模因子
        size = exposure.get('size', 0)
        if size > 0.3:
            rating = "🏢 大盘股"
            desc = "稳健,流动性好"
        elif size < -0.3:
            rating = "🌱 小盘股"
            desc = "高弹性,风险高"
        else:
            rating = "⚖️ 均衡"
            desc = "大小盘均衡"

        lines.append(f"| **规模因子** | {size:.2f} | {rating} | {desc} |")

        # 动量因子
        momentum = exposure.get('momentum', 0)
        if momentum > 0.3:
            rating = "📈 强势"
            desc = "趋势向上"
        elif momentum < -0.3:
            rating = "📉 弱势"
            desc = "趋势向下"
        else:
            rating = "➡️ 中性"
            desc = "无明显趋势"

        lines.append(f"| **动量因子** | {momentum:.2f} | {rating} | {desc} |")

        lines.append("")

        # 综合结论
        lines.append("🎯 **组合风格总结**:")
        lines.append("")

        if growth > 0.5 and market_beta > 0.9:
            lines.append("- 高Beta+强成长风格,牛市进攻性强,熊市需要防守")
        elif value > 0.3 and market_beta < 0.8:
            lines.append("- 低Beta+价值风格,熊市防守性好,牛市收益有限")
        else:
            lines.append("- 均衡配置,攻守兼备")

        lines.append("")

        return '\n'.join(lines)


if __name__ == '__main__':
    # 测试量化分析
    print("=== 测试夏普比率计算 ===")
    analyzer = QuantAnalyzer()

    # 模拟收益率数据
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.02, 252))  # 252个交易日

    sharpe = analyzer.calculate_sharpe_ratio(returns)
    sortino = analyzer.calculate_sortino_ratio(returns)
    max_dd, dd_days = analyzer.calculate_max_drawdown(returns)
    win_rate = analyzer.calculate_win_rate(returns)

    print(f"夏普比率: {sharpe:.2f}")
    print(f"索提诺比率: {sortino:.2f}")
    print(f"最大回撤: {max_dd*100:.2f}%")
    print(f"胜率: {win_rate*100:.1f}%")

    print("\n=== 测试因子暴露分析 ===")
    positions = [
        {'asset_name': '恒生科技ETF', 'position_ratio': 0.28},
        {'asset_name': '证券ETF', 'position_ratio': 0.23},
        {'asset_name': '白酒ETF', 'position_ratio': 0.22},
    ]

    exposure = analyzer.analyze_factor_exposure(positions)
    report = analyzer.format_factor_exposure_report(exposure)
    print(report)
