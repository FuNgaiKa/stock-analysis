#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化模块
Visualization Module

提供持仓饼图、收益曲线等图表生成功能

Author: Claude Code
Date: 2025-10-21
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VisualizationGenerator:
    """可视化生成器"""

    def __init__(self, output_dir: str = "reports/charts"):
        """
        初始化生成器

        Args:
            output_dir: 图表输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_position_pie_chart_ascii(
        self,
        positions: List[Dict],
        max_width: int = 50
    ) -> str:
        """
        生成ASCII持仓饼图（用于Markdown）

        Args:
            positions: 持仓列表
            max_width: 最大宽度

        Returns:
            ASCII图表字符串
        """
        if not positions:
            return "暂无持仓数据"

        lines = []
        lines.append("### 📊 持仓分布图")
        lines.append("")
        lines.append("```")

        # 按仓位比例排序
        sorted_positions = sorted(
            positions,
            key=lambda x: x.get('position_ratio', 0),
            reverse=True
        )

        # 计算总仓位
        total_ratio = sum(p.get('position_ratio', 0) for p in sorted_positions)

        for pos in sorted_positions:
            name = pos.get('asset_name', 'Unknown')
            ratio = pos.get('position_ratio', 0)
            pct = ratio * 100

            # 计算条形长度
            bar_length = int((ratio / total_ratio) * max_width) if total_ratio > 0 else 0
            bar = '█' * bar_length

            # 格式化输出（固定宽度）
            lines.append(f"{name:15s} [{pct:5.1f}%] {bar}")

        lines.append("```")
        lines.append("")

        # 添加汇总
        lines.append(f"**总仓位**: {total_ratio*100:.1f}%")
        lines.append(f"**现金储备**: {(1-total_ratio)*100:.1f}%")
        lines.append("")

        return '\n'.join(lines)

    def generate_equity_curve_ascii(
        self,
        dates: List[str],
        capitals: List[float],
        height: int = 15,
        width: int = 60
    ) -> str:
        """
        生成ASCII收益曲线（用于Markdown）

        Args:
            dates: 日期列表
            capitals: 资金列表
            height: 图表高度
            width: 图表宽度

        Returns:
            ASCII图表字符串
        """
        if not dates or not capitals or len(dates) != len(capitals):
            return "暂无收益曲线数据"

        lines = []
        lines.append("### 📈 收益曲线")
        lines.append("")
        lines.append("```")

        # 标准化资金到0-height范围
        min_capital = min(capitals)
        max_capital = max(capitals)
        capital_range = max_capital - min_capital

        if capital_range == 0:
            lines.append("收益曲线无变化")
            lines.append("```")
            return '\n'.join(lines)

        # 创建画布
        canvas = [[' ' for _ in range(width)] for _ in range(height)]

        # 计算每个点的位置
        for i, capital in enumerate(capitals):
            x = int((i / (len(capitals) - 1)) * (width - 1)) if len(capitals) > 1 else 0
            normalized = (capital - min_capital) / capital_range
            y = height - 1 - int(normalized * (height - 1))

            if 0 <= x < width and 0 <= y < height:
                canvas[y][x] = '●'

        # 绘制Y轴标签和图表
        for i, row in enumerate(canvas):
            # Y轴标签
            value_ratio = (height - 1 - i) / (height - 1)
            value = min_capital + value_ratio * capital_range
            label = f"¥{value/10000:.1f}万 |"

            lines.append(f"{label:12s} {''.join(row)}")

        # X轴
        lines.append(" " * 12 + "+" + "-" * width)

        # 日期标签（首尾）
        if len(dates) >= 2:
            first_date = dates[0]
            last_date = dates[-1]
            lines.append(f" " * 12 + f" {first_date}" + " " * (width - len(first_date) - len(last_date) - 1) + last_date)

        lines.append("```")
        lines.append("")

        # 添加统计
        initial = capitals[0]
        final = capitals[-1]
        total_return = (final - initial) / initial if initial > 0 else 0

        lines.append(f"**起始资金**: ¥{initial:,.0f}")
        lines.append(f"**最终资金**: ¥{final:,.0f}")
        lines.append(f"**累计收益**: {total_return*100:+.2f}%")
        lines.append("")

        return '\n'.join(lines)

    def generate_position_pie_chart_matplotlib(
        self,
        positions: List[Dict],
        filename: str = "position_pie.png"
    ) -> Optional[str]:
        """
        生成matplotlib持仓饼图（用于HTML）

        Args:
            positions: 持仓列表
            filename: 文件名

        Returns:
            图片路径，失败返回None
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # 非GUI后端
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            if not positions:
                logger.warning("无持仓数据，无法生成饼图")
                return None

            # 准备数据
            labels = []
            sizes = []
            colors = []

            # 预定义颜色
            color_palette = [
                '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',
                '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2',
                '#F8B739', '#52B788'
            ]

            for i, pos in enumerate(positions):
                name = pos.get('asset_name', 'Unknown')
                ratio = pos.get('position_ratio', 0)
                if ratio > 0:
                    labels.append(f"{name}\n{ratio*100:.1f}%")
                    sizes.append(ratio)
                    colors.append(color_palette[i % len(color_palette)])

            # 添加现金
            total_position = sum(sizes)
            if total_position < 1.0:
                cash_ratio = 1.0 - total_position
                labels.append(f"现金\n{cash_ratio*100:.1f}%")
                sizes.append(cash_ratio)
                colors.append('#CCCCCC')

            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 8))

            wedges, texts = ax.pie(
                sizes,
                labels=labels,
                colors=colors,
                startangle=90,
                textprops={'fontsize': 10}
            )

            ax.set_title('持仓分布', fontsize=16, pad=20)

            # 保存
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"饼图已生成: {filepath}")
            return str(filepath)

        except ImportError:
            logger.warning("matplotlib未安装，无法生成饼图")
            return None
        except Exception as e:
            logger.error(f"生成饼图失败: {e}")
            return None

    def generate_equity_curve_matplotlib(
        self,
        dates: List[str],
        capitals: List[float],
        filename: str = "equity_curve.png"
    ) -> Optional[str]:
        """
        生成matplotlib收益曲线（用于HTML）

        Args:
            dates: 日期列表
            capitals: 资金列表
            filename: 文件名

        Returns:
            图片路径，失败返回None
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            if not dates or not capitals:
                logger.warning("无数据，无法生成收益曲线")
                return None

            # 转换日期
            date_objects = [datetime.strptime(d, '%Y-%m-%d') for d in dates]

            # 创建图表
            fig, ax = plt.subplots(figsize=(12, 6))

            # 绘制曲线
            ax.plot(date_objects, capitals, linewidth=2, color='#4ECDC4', label='账户资金')

            # 填充区域
            initial_capital = capitals[0]
            ax.fill_between(
                date_objects,
                capitals,
                initial_capital,
                where=[c >= initial_capital for c in capitals],
                alpha=0.3,
                color='#52B788',
                label='盈利区域'
            )
            ax.fill_between(
                date_objects,
                capitals,
                initial_capital,
                where=[c < initial_capital for c in capitals],
                alpha=0.3,
                color='#FF6B6B',
                label='亏损区域'
            )

            # 添加初始资金线
            ax.axhline(y=initial_capital, color='gray', linestyle='--', linewidth=1, alpha=0.5)

            # 格式化
            ax.set_title('账户资金曲线', fontsize=16, pad=20)
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('资金 (元)', fontsize=12)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)

            # 格式化日期轴
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.xticks(rotation=45)

            # 格式化Y轴（添加千位分隔符）
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}'))

            # 保存
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"收益曲线已生成: {filepath}")
            return str(filepath)

        except ImportError:
            logger.warning("matplotlib未安装，无法生成收益曲线")
            return None
        except Exception as e:
            logger.error(f"生成收益曲线失败: {e}")
            return None


# 示例用法
if __name__ == "__main__":
    # 测试数据
    test_positions = [
        {'asset_name': '恒生科技ETF', 'position_ratio': 0.28},
        {'asset_name': '证券ETF', 'position_ratio': 0.23},
        {'asset_name': '白酒ETF', 'position_ratio': 0.22},
        {'asset_name': '化工ETF', 'position_ratio': 0.07},
        {'asset_name': '煤炭ETF', 'position_ratio': 0.04},
    ]

    test_dates = ['2025-01-01', '2025-01-05', '2025-01-10', '2025-01-15']
    test_capitals = [500000, 520000, 515000, 530000]

    # 创建生成器
    viz = VisualizationGenerator()

    # 生成ASCII图表
    print(viz.generate_position_pie_chart_ascii(test_positions))
    print(viz.generate_equity_curve_ascii(test_dates, test_capitals))

    # 生成matplotlib图表
    viz.generate_position_pie_chart_matplotlib(test_positions)
    viz.generate_equity_curve_matplotlib(test_dates, test_capitals)

    print("\nmatplotlib图表已保存到 reports/charts/")
