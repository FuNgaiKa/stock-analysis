#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表生成器 - 用于HTML可视化报告
使用 plotly 生成交互式图表
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging

logger = logging.getLogger(__name__)


class ChartGenerator:
    """图表生成器"""

    @staticmethod
    def create_candlestick_comparison(
        current_data: pd.DataFrame,
        historical_cases: List[Dict],
        index_name: str
    ) -> str:
        """
        创建K线对比图

        Args:
            current_data: 当前走势数据
            historical_cases: 历史相似案例列表 [{'date': date, 'data': df, 'future_return': float}]
            index_name: 指数名称

        Returns:
            Plotly HTML
        """
        # 创建子图
        n_cases = len(historical_cases)
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                f'{index_name} - 当前走势',
                f'历史案例1 (后续{historical_cases[0]["future_return"]:+.1%})' if n_cases > 0 else '',
                f'历史案例2 (后续{historical_cases[1]["future_return"]:+.1%})' if n_cases > 1 else '',
                f'历史案例3 (后续{historical_cases[2]["future_return"]:+.1%})' if n_cases > 2 else ''
            ),
            specs=[[{"type": "candlestick"}, {"type": "candlestick"}],
                   [{"type": "candlestick"}, {"type": "candlestick"}]]
        )

        # 当前走势
        if current_data is not None and len(current_data) > 0:
            fig.add_trace(
                go.Candlestick(
                    x=current_data.index,
                    open=current_data['open'],
                    high=current_data['high'],
                    low=current_data['low'],
                    close=current_data['close'],
                    name='当前'
                ),
                row=1, col=1
            )

        # 历史案例
        positions = [(1, 2), (2, 1), (2, 2)]
        for i, case in enumerate(historical_cases[:3]):
            if i < len(positions):
                row, col = positions[i]
                data = case['data']

                fig.add_trace(
                    go.Candlestick(
                        x=data.index,
                        open=data['open'],
                        high=data['high'],
                        low=data['low'],
                        close=data['close'],
                        name=f'案例{i+1}'
                    ),
                    row=row, col=col
                )

        fig.update_layout(
            height=800,
            showlegend=False,
            title_text=f"{index_name} - 历史相似走势对比"
        )

        fig.update_xaxes(rangeslider_visible=False)

        return fig.to_html(include_plotlyjs=False, div_id=f"candlestick_{index_name}")

    @staticmethod
    def create_probability_chart(
        prob_data: Dict[str, Dict],
        periods: List[int] = [5, 10, 20, 60]
    ) -> str:
        """
        创建概率柱状图

        Args:
            prob_data: 概率数据字典 {period: {up_prob, down_prob, ...}}
            periods: 周期列表

        Returns:
            Plotly HTML
        """
        up_probs = []
        down_probs = []
        labels = []

        for period in periods:
            key = f'period_{period}d'
            if key in prob_data:
                up_probs.append(prob_data[key]['up_prob'] * 100)
                down_probs.append(prob_data[key]['down_prob'] * 100)
                labels.append(f'{period}日')

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='上涨概率',
            x=labels,
            y=up_probs,
            marker_color='#28a745',
            text=[f'{v:.1f}%' for v in up_probs],
            textposition='outside'
        ))

        fig.add_trace(go.Bar(
            name='下跌概率',
            x=labels,
            y=down_probs,
            marker_color='#dc3545',
            text=[f'{v:.1f}%' for v in down_probs],
            textposition='outside'
        ))

        fig.update_layout(
            title='不同周期涨跌概率对比',
            xaxis_title='预测周期',
            yaxis_title='概率 (%)',
            barmode='group',
            height=400
        )

        return fig.to_html(include_plotlyjs=False, div_id="probability_chart")

    @staticmethod
    def create_return_distribution(
        returns: pd.Series,
        period: int,
        index_name: str
    ) -> str:
        """
        创建收益率分布直方图

        Args:
            returns: 收益率序列
            period: 周期
            index_name: 指数名称

        Returns:
            Plotly HTML
        """
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=returns * 100,
            nbinsx=30,
            marker_color='#667eea',
            opacity=0.75,
            name='收益率分布'
        ))

        # 添加均值线
        mean_return = returns.mean() * 100
        fig.add_vline(
            x=mean_return,
            line_dash="dash",
            line_color="red",
            annotation_text=f"均值: {mean_return:.2f}%",
            annotation_position="top right"
        )

        # 添加中位数线
        median_return = returns.median() * 100
        fig.add_vline(
            x=median_return,
            line_dash="dash",
            line_color="green",
            annotation_text=f"中位数: {median_return:.2f}%",
            annotation_position="top left"
        )

        fig.update_layout(
            title=f'{index_name} - {period}日后收益率分布',
            xaxis_title='收益率 (%)',
            yaxis_title='频数',
            height=400
        )

        return fig.to_html(include_plotlyjs=False, div_id=f"distribution_{period}d")

    @staticmethod
    def create_similarity_heatmap(
        similarity_matrix: pd.DataFrame,
        index_names: List[str]
    ) -> str:
        """
        创建相似度热力图

        Args:
            similarity_matrix: 相似度矩阵
            index_names: 指数名称列表

        Returns:
            Plotly HTML
        """
        fig = go.Figure(data=go.Heatmap(
            z=similarity_matrix.values,
            x=similarity_matrix.columns,
            y=similarity_matrix.index,
            colorscale='RdYlGn',
            text=similarity_matrix.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
            colorbar=dict(title="相似度")
        ))

        fig.update_layout(
            title='多维度相似度热力图',
            xaxis_title='特征维度',
            yaxis_title='历史时期',
            height=600
        )

        return fig.to_html(include_plotlyjs=False, div_id="heatmap")

    @staticmethod
    def create_funnel_chart(
        stages: List[Dict]
    ) -> str:
        """
        创建概率漏斗图

        Args:
            stages: 阶段数据 [{'name': '相似点位', 'sample': 100, 'prob': 0.6}, ...]

        Returns:
            Plotly HTML
        """
        fig = go.Figure()

        values = [stage['sample'] for stage in stages]
        labels = [f"{stage['name']}<br>样本数:{stage['sample']}<br>上涨概率:{stage['prob']:.1%}"
                  for stage in stages]

        fig.add_trace(go.Funnel(
            y=labels,
            x=values,
            textposition="inside",
            textinfo="value+percent initial",
            marker={"color": ["#667eea", "#764ba2", "#f093fb", "#4facfe"]},
        ))

        fig.update_layout(
            title='多因子过滤后概率变化',
            height=500
        )

        return fig.to_html(include_plotlyjs=False, div_id="funnel_chart")

    @staticmethod
    def create_confidence_gauge(
        confidence: float,
        title: str = "综合置信度"
    ) -> str:
        """
        创建置信度仪表盘

        Args:
            confidence: 置信度 (0-1)
            title: 标题

        Returns:
            Plotly HTML
        """
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=confidence * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': 70},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#667eea"},
                'steps': [
                    {'range': [0, 40], 'color': "#ffe6e6"},
                    {'range': [40, 60], 'color': "#fff4e6"},
                    {'range': [60, 80], 'color': "#e6f7ff"},
                    {'range': [80, 100], 'color': "#e6ffe6"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))

        fig.update_layout(height=300)

        return fig.to_html(include_plotlyjs=False, div_id="confidence_gauge")

    @staticmethod
    def create_timeline_chart(
        matched_periods: pd.DataFrame,
        index_code: str
    ) -> str:
        """
        创建时间线图 - 显示历史匹配时期分布

        Args:
            matched_periods: 匹配时期DataFrame
            index_code: 指数代码

        Returns:
            Plotly HTML
        """
        if len(matched_periods) == 0:
            return "<p>无数据</p>"

        fig = go.Figure()

        # 按年份分组
        matched_periods['year'] = matched_periods['date'].dt.year
        year_counts = matched_periods['year'].value_counts().sort_index()

        fig.add_trace(go.Scatter(
            x=year_counts.index,
            y=year_counts.values,
            mode='lines+markers',
            marker=dict(size=10, color='#667eea'),
            line=dict(width=2, color='#667eea'),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.2)'
        ))

        fig.update_layout(
            title='历史相似点位年份分布',
            xaxis_title='年份',
            yaxis_title='出现次数',
            height=400
        )

        return fig.to_html(include_plotlyjs=False, div_id="timeline_chart")


if __name__ == '__main__':
    # 测试
    chart_gen = ChartGenerator()

    # 测试概率图表
    prob_data = {
        'period_5d': {'up_prob': 0.65, 'down_prob': 0.35},
        'period_10d': {'up_prob': 0.60, 'down_prob': 0.40},
        'period_20d': {'up_prob': 0.55, 'down_prob': 0.45},
        'period_60d': {'up_prob': 0.48, 'down_prob': 0.52},
    }

    html = chart_gen.create_probability_chart(prob_data)
    print("概率图表生成成功")

    # 测试置信度仪表盘
    gauge_html = chart_gen.create_confidence_gauge(0.75)
    print("置信度仪表盘生成成功")
