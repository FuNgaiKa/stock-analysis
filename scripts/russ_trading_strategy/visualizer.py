#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化模块
生成各类图表用于策略分析

功能:
1. 权益曲线图
2. 回撤图
3. 收益分布图
4. 相关性热力图
5. 月度收益热力图

Author: Russ
Created: 2025-10-20
"""

import os
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Visualizer:
    """可视化工具类"""

    def __init__(self, output_dir: str = "charts"):
        """
        初始化可视化工具

        Args:
            output_dir: 图表输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 尝试导入matplotlib
        try:
            import matplotlib
            matplotlib.use('Agg')  # 无显示后端
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib import rcParams

            # 中文字体配置
            rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial', 'DejaVu Sans']
            rcParams['axes.unicode_minus'] = False

            self.plt = plt
            self.mdates = mdates
            self.has_matplotlib = True

        except ImportError:
            logger.warning("matplotlib未安装,可视化功能不可用")
            self.has_matplotlib = False

        # 尝试导入seaborn
        try:
            import seaborn as sns
            self.sns = sns
            self.has_seaborn = True
        except ImportError:
            logger.warning("seaborn未安装,部分可视化功能不可用")
            self.has_seaborn = False

    def plot_equity_curve(
        self,
        dates: List[str],
        equity_values: List[float],
        benchmark_values: Optional[List[float]] = None,
        title: str = "权益曲线",
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        绘制权益曲线

        Args:
            dates: 日期列表
            equity_values: 权益价值列表
            benchmark_values: 基准价值列表(可选)
            title: 图表标题
            save_path: 保存路径(如果为None,自动生成)

        Returns:
            保存的文件路径
        """
        if not self.has_matplotlib:
            return None

        if save_path is None:
            save_path = os.path.join(self.output_dir, "equity_curve.png")

        fig, ax = self.plt.subplots(figsize=(12, 6))

        # 绘制权益曲线
        ax.plot(dates, equity_values, label='投资组合', color='#2E86AB', linewidth=2)

        # 绘制基准曲线
        if benchmark_values:
            ax.plot(dates, benchmark_values, label='基准', color='#F24236', linewidth=1.5, linestyle='--')

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('资金 (元)', fontsize=12)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')

        # 格式化y轴为千分位
        ax.yaxis.set_major_formatter(self.plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

        self.plt.tight_layout()
        self.plt.savefig(save_path, dpi=300, bbox_inches='tight')
        self.plt.close()

        logger.info(f"权益曲线已保存到: {save_path}")
        return save_path

    def plot_drawdown(
        self,
        dates: List[str],
        equity_values: List[float],
        title: str = "回撤分析",
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        绘制回撤图

        Args:
            dates: 日期列表
            equity_values: 权益价值列表
            title: 图表标题
            save_path: 保存路径

        Returns:
            保存的文件路径
        """
        if not self.has_matplotlib:
            return None

        if save_path is None:
            save_path = os.path.join(self.output_dir, "drawdown.png")

        # 计算回撤
        drawdowns = []
        peak = equity_values[0]

        for value in equity_values:
            if value > peak:
                peak = value
            dd = (value - peak) / peak
            drawdowns.append(dd * 100)  # 转换为百分比

        fig, (ax1, ax2) = self.plt.subplots(2, 1, figsize=(12, 8))

        # 上图:权益曲线
        ax1.plot(dates, equity_values, color='#2E86AB', linewidth=2)
        ax1.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax1.set_ylabel('资金 (元)', fontsize=12)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.yaxis.set_major_formatter(self.plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

        # 下图:回撤曲线
        ax2.fill_between(range(len(drawdowns)), drawdowns, 0, color='#F24236', alpha=0.3)
        ax2.plot(drawdowns, color='#F24236', linewidth=1.5)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_ylabel('回撤 (%)', fontsize=12)
        ax2.grid(True, alpha=0.3, linestyle='--')

        # 标注最大回撤
        max_dd_idx = drawdowns.index(min(drawdowns))
        max_dd = min(drawdowns)
        ax2.plot(max_dd_idx, max_dd, 'ro', markersize=8)
        ax2.annotate(f'最大回撤: {max_dd:.2f}%',
                    xy=(max_dd_idx, max_dd),
                    xytext=(10, 20),
                    textcoords='offset points',
                    fontsize=10,
                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        self.plt.tight_layout()
        self.plt.savefig(save_path, dpi=300, bbox_inches='tight')
        self.plt.close()

        logger.info(f"回撤图已保存到: {save_path}")
        return save_path

    def plot_returns_distribution(
        self,
        returns: List[float],
        title: str = "收益率分布",
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        绘制收益率分布图

        Args:
            returns: 收益率列表
            title: 图表标题
            save_path: 保存路径

        Returns:
            保存的文件路径
        """
        if not self.has_matplotlib:
            return None

        if save_path is None:
            save_path = os.path.join(self.output_dir, "returns_distribution.png")

        fig, (ax1, ax2) = self.plt.subplots(1, 2, figsize=(14, 5))

        # 左图:直方图
        returns_pct = [r * 100 for r in returns]
        ax1.hist(returns_pct, bins=50, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', linewidth=2, label='零收益')
        ax1.set_title('收益率直方图', fontsize=14, fontweight='bold')
        ax1.set_xlabel('日收益率 (%)', fontsize=12)
        ax1.set_ylabel('频数', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 右图:箱线图
        ax2.boxplot(returns_pct, vert=True)
        ax2.set_title('收益率箱线图', fontsize=14, fontweight='bold')
        ax2.set_ylabel('日收益率 (%)', fontsize=12)
        ax2.grid(True, alpha=0.3)

        fig.suptitle(title, fontsize=16, fontweight='bold', y=1.02)

        self.plt.tight_layout()
        self.plt.savefig(save_path, dpi=300, bbox_inches='tight')
        self.plt.close()

        logger.info(f"收益率分布图已保存到: {save_path}")
        return save_path

    def plot_correlation_heatmap(
        self,
        correlation_matrix: Dict[str, Dict[str, float]],
        title: str = "资产相关性热力图",
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        绘制相关性热力图

        Args:
            correlation_matrix: 相关性矩阵 {asset1: {asset2: corr}}
            title: 图表标题
            save_path: 保存路径

        Returns:
            保存的文件路径
        """
        if not self.has_matplotlib or not self.has_seaborn:
            logger.warning("需要matplotlib和seaborn才能绘制热力图")
            return None

        if save_path is None:
            save_path = os.path.join(self.output_dir, "correlation_heatmap.png")

        # 转换为二维列表
        assets = list(correlation_matrix.keys())
        n = len(assets)
        matrix = [[correlation_matrix[a1].get(a2, 0) for a2 in assets] for a1 in assets]

        fig, ax = self.plt.subplots(figsize=(10, 8))

        # 使用seaborn绘制热力图
        self.sns.heatmap(
            matrix,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            center=0,
            square=True,
            linewidths=1,
            cbar_kws={"shrink": 0.8},
            xticklabels=assets,
            yticklabels=assets,
            ax=ax
        )

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

        self.plt.tight_layout()
        self.plt.savefig(save_path, dpi=300, bbox_inches='tight')
        self.plt.close()

        logger.info(f"相关性热力图已保存到: {save_path}")
        return save_path

    def plot_monthly_returns_heatmap(
        self,
        monthly_returns: Dict[str, Dict[str, float]],
        title: str = "月度收益率热力图",
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        绘制月度收益率热力图

        Args:
            monthly_returns: 月度收益率 {year: {month: return}}
            title: 图表标题
            save_path: 保存路径

        Returns:
            保存的文件路径
        """
        if not self.has_matplotlib or not self.has_seaborn:
            return None

        if save_path is None:
            save_path = os.path.join(self.output_dir, "monthly_returns_heatmap.png")

        # 准备数据
        years = sorted(monthly_returns.keys())
        months = list(range(1, 13))

        data = []
        for year in years:
            row = [monthly_returns[year].get(m, 0) * 100 for m in months]  # 转为百分比
            data.append(row)

        fig, ax = self.plt.subplots(figsize=(12, 6))

        # 使用seaborn绘制热力图
        self.sns.heatmap(
            data,
            annot=True,
            fmt='.1f',
            cmap='RdYlGn',
            center=0,
            linewidths=1,
            cbar_kws={"shrink": 0.8, "label": "收益率 (%)"},
            xticklabels=[f'{m}月' for m in months],
            yticklabels=years,
            ax=ax
        )

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('年份', fontsize=12)

        self.plt.tight_layout()
        self.plt.savefig(save_path, dpi=300, bbox_inches='tight')
        self.plt.close()

        logger.info(f"月度收益率热力图已保存到: {save_path}")
        return save_path

    def create_comprehensive_dashboard(
        self,
        dates: List[str],
        equity_values: List[float],
        returns: List[float],
        benchmark_values: Optional[List[float]] = None,
        title: str = "投资组合综合仪表盘",
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        创建综合仪表盘(包含多个子图)

        Args:
            dates: 日期列表
            equity_values: 权益价值列表
            returns: 收益率列表
            benchmark_values: 基准价值列表
            title: 图表标题
            save_path: 保存路径

        Returns:
            保存的文件路径
        """
        if not self.has_matplotlib:
            return None

        if save_path is None:
            save_path = os.path.join(self.output_dir, "comprehensive_dashboard.png")

        fig = self.plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # 1. 权益曲线
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(dates, equity_values, label='投资组合', color='#2E86AB', linewidth=2)
        if benchmark_values:
            ax1.plot(dates, benchmark_values, label='基准', color='#F24236', linewidth=1.5, linestyle='--')
        ax1.set_title('权益曲线', fontsize=12, fontweight='bold')
        ax1.set_ylabel('资金 (元)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(self.plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

        # 2. 回撤曲线
        ax2 = fig.add_subplot(gs[1, 0])
        drawdowns = []
        peak = equity_values[0]
        for value in equity_values:
            if value > peak:
                peak = value
            dd = (value - peak) / peak
            drawdowns.append(dd * 100)

        ax2.fill_between(range(len(drawdowns)), drawdowns, 0, color='#F24236', alpha=0.3)
        ax2.plot(drawdowns, color='#F24236', linewidth=1.5)
        ax2.set_title('回撤曲线', fontsize=12, fontweight='bold')
        ax2.set_ylabel('回撤 (%)')
        ax2.grid(True, alpha=0.3)

        # 3. 收益率分布
        ax3 = fig.add_subplot(gs[1, 1])
        returns_pct = [r * 100 for r in returns]
        ax3.hist(returns_pct, bins=30, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax3.axvline(x=0, color='red', linestyle='--', linewidth=1)
        ax3.set_title('收益率分布', fontsize=12, fontweight='bold')
        ax3.set_xlabel('日收益率 (%)')
        ax3.set_ylabel('频数')
        ax3.grid(True, alpha=0.3)

        # 4. 累计收益
        ax4 = fig.add_subplot(gs[2, 0])
        cumulative_returns = [(equity_values[i] - equity_values[0]) / equity_values[0] * 100
                              for i in range(len(equity_values))]
        ax4.fill_between(range(len(cumulative_returns)), cumulative_returns, 0,
                        where=[cr >= 0 for cr in cumulative_returns],
                        color='#23CE6B', alpha=0.3, label='盈利期')
        ax4.fill_between(range(len(cumulative_returns)), cumulative_returns, 0,
                        where=[cr < 0 for cr in cumulative_returns],
                        color='#F24236', alpha=0.3, label='亏损期')
        ax4.plot(cumulative_returns, color='#2E86AB', linewidth=2)
        ax4.set_title('累计收益率', fontsize=12, fontweight='bold')
        ax4.set_ylabel('收益率 (%)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # 5. 滚动波动率
        ax5 = fig.add_subplot(gs[2, 1])
        window = min(20, len(returns) // 4)
        if window > 1:
            import numpy as np
            rolling_vol = [np.std(returns[max(0, i-window):i+1]) * np.sqrt(252) * 100
                          for i in range(len(returns))]
            ax5.plot(rolling_vol, color='#FFA500', linewidth=1.5)
            ax5.set_title(f'滚动波动率 ({window}日)', fontsize=12, fontweight='bold')
            ax5.set_ylabel('年化波动率 (%)')
            ax5.grid(True, alpha=0.3)

        fig.suptitle(title, fontsize=18, fontweight='bold', y=0.995)

        self.plt.savefig(save_path, dpi=300, bbox_inches='tight')
        self.plt.close()

        logger.info(f"综合仪表盘已保存到: {save_path}")
        return save_path


# 示例用法
if __name__ == "__main__":
    import numpy as np

    # 创建可视化工具
    viz = Visualizer(output_dir="charts")

    if not viz.has_matplotlib:
        print("matplotlib未安装,无法运行示例")
        exit(1)

    # 生成模拟数据
    np.random.seed(42)
    n_days = 252

    dates = [f"2024-{(i//21)+1:02d}-{(i%21)+1:02d}" for i in range(n_days)]

    # 模拟权益曲线(带趋势和波动)
    trend = np.linspace(100000, 120000, n_days)
    noise = np.cumsum(np.random.normal(0, 1000, n_days))
    equity_values = trend + noise

    # 模拟基准
    benchmark_values = np.linspace(100000, 110000, n_days) + np.cumsum(np.random.normal(0, 500, n_days))

    # 计算收益率
    returns = [(equity_values[i] - equity_values[i-1]) / equity_values[i-1]
              for i in range(1, len(equity_values))]
    returns.insert(0, 0)

    # 生成各类图表
    print("生成权益曲线...")
    viz.plot_equity_curve(dates, equity_values, benchmark_values)

    print("生成回撤图...")
    viz.plot_drawdown(dates, equity_values)

    print("生成收益率分布图...")
    viz.plot_returns_distribution(returns)

    print("生成综合仪表盘...")
    viz.create_comprehensive_dashboard(dates, equity_values, returns, benchmark_values)

    print("\n所有图表已生成完成!")
