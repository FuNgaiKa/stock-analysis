#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筹码分布分析器
Chip Distribution Analyzer

功能：
1. 主力成本计算
2. 筹码集中度分析
3. 盈利筹码比例
4. 控盘程度判断
5. 主力行为识别（吸筹/派发/稳定）

原理：
- 通过成交量加权计算主力持仓成本
- 基于换手率判断筹码锁定程度
- 通过筹码分布图判断支撑压力位

作者: Claude Code
日期: 2025-10-31
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ChipDistributionAnalyzer:
    """
    筹码分布分析器

    通过成交量和价格数据，计算筹码分布情况，识别主力行为
    """

    def __init__(self, lookback_days: int = 60):
        """
        初始化筹码分布分析器

        Args:
            lookback_days: 筹码分析回溯天数，默认60天
        """
        self.lookback_days = lookback_days
        self.logger = logging.getLogger(__name__)

    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        完整筹码分布分析

        Args:
            df: OHLCV数据，必须包含 close, volume, turnover(换手率) 列

        Returns:
            筹码分布分析结果
        """
        try:
            # 数据验证
            if df.empty:
                return {'error': '数据为空'}

            required_cols = ['close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {'error': f'缺少必需列: {missing_cols}'}

            if len(df) < self.lookback_days:
                return {'error': f'数据不足，需要至少{self.lookback_days}天数据'}

            # 取最近lookback_days的数据
            recent_df = df.tail(self.lookback_days).copy()

            # 1. 计算主力成本
            main_cost_data = self._calculate_main_cost(recent_df)

            # 2. 计算筹码集中度
            concentration = self._calculate_concentration(recent_df)

            # 3. 计算当前价格相对成本的位置
            current_price = recent_df['close'].iloc[-1]
            main_cost = main_cost_data['main_cost']
            position_vs_cost = ((current_price - main_cost) / main_cost) * 100

            # 4. 计算盈利筹码比例
            profit_ratio = self._calculate_profit_ratio(recent_df, current_price)

            # 5. 判断控盘程度
            control_level = self._determine_control_level(recent_df, concentration)

            # 6. 识别主力行为
            signal = self._identify_main_behavior(recent_df, concentration)

            # 7. 生成筹码分布图数据
            distribution_chart = self._generate_distribution_chart(recent_df)

            result = {
                'main_cost': round(main_cost, 2),
                'cost_range': (
                    round(main_cost_data['cost_lower'], 2),
                    round(main_cost_data['cost_upper'], 2)
                ),
                'concentration': round(concentration, 1),
                'current_price': round(current_price, 2),
                'position_vs_cost': round(position_vs_cost, 2),
                'profit_ratio': round(profit_ratio, 1),
                'control_level': control_level,
                'signal': signal,
                'distribution_chart': distribution_chart,
                'summary': self._generate_summary(
                    main_cost, current_price, position_vs_cost,
                    concentration, control_level, signal
                )
            }

            return result

        except Exception as e:
            self.logger.error(f"筹码分布分析失败: {str(e)}")
            return {'error': str(e)}

    def _calculate_main_cost(self, df: pd.DataFrame) -> Dict:
        """
        计算主力成本

        使用成交量加权平均价格（VWAP）作为主力成本

        Returns:
            {
                'main_cost': float,      # 主力成本
                'cost_lower': float,     # 成本区间下限
                'cost_upper': float      # 成本区间上限
            }
        """
        # 计算成交额（如果没有的话）
        if 'amount' not in df.columns:
            # 使用 (high + low + close) / 3 作为均价估计
            df = df.copy()
            if 'high' in df.columns and 'low' in df.columns:
                avg_price = (df['high'] + df['low'] + df['close']) / 3
            else:
                avg_price = df['close']
            df['amount'] = avg_price * df['volume']

        # 计算成交量加权平均价格（VWAP）
        total_amount = df['amount'].sum()
        total_volume = df['volume'].sum()

        if total_volume > 0:
            main_cost = total_amount / total_volume
        else:
            main_cost = df['close'].mean()

        # 计算成本区间（±1个标准差）
        prices = df['close']
        volumes = df['volume']

        # 成交量加权标准差
        variance = np.average((prices - main_cost) ** 2, weights=volumes)
        std = np.sqrt(variance)

        cost_lower = main_cost - std
        cost_upper = main_cost + std

        return {
            'main_cost': main_cost,
            'cost_lower': max(cost_lower, 0),  # 价格不能为负
            'cost_upper': cost_upper
        }

    def _calculate_concentration(self, df: pd.DataFrame) -> float:
        """
        计算筹码集中度

        算法：计算70%成交量集中在多大的价格区间内
        区间越小，集中度越高

        Returns:
            集中度分数 (0-100)，分数越高表示筹码越集中
        """
        # 将价格分成N个区间
        n_bins = 20
        price_min = df['close'].min()
        price_max = df['close'].max()

        if price_max == price_min:
            return 100.0  # 价格没变化，完全集中

        bins = np.linspace(price_min, price_max, n_bins + 1)

        # 统计每个价格区间的成交量
        volume_distribution = np.zeros(n_bins)

        for i in range(len(df)):
            price = df['close'].iloc[i]
            volume = df['volume'].iloc[i]

            # 找到价格所在的区间
            bin_idx = np.searchsorted(bins, price, side='right') - 1
            bin_idx = min(max(bin_idx, 0), n_bins - 1)

            volume_distribution[bin_idx] += volume

        # 按成交量从大到小排序
        sorted_volumes = np.sort(volume_distribution)[::-1]
        total_volume = sorted_volumes.sum()

        if total_volume == 0:
            return 0.0

        # 计算需要多少个区间才能包含70%的成交量
        cumsum = 0
        target_ratio = 0.70
        bins_needed = 0

        for vol in sorted_volumes:
            cumsum += vol
            bins_needed += 1
            if cumsum >= total_volume * target_ratio:
                break

        # 集中度分数：需要的区间越少，集中度越高
        # bins_needed=1 => 100分, bins_needed=n_bins => 0分
        concentration = max(0, 100 * (1 - (bins_needed - 1) / (n_bins - 1)))

        return concentration

    def _calculate_profit_ratio(self, df: pd.DataFrame, current_price: float) -> float:
        """
        计算盈利筹码比例

        计算有多少比例的筹码当前处于盈利状态

        Returns:
            盈利筹码比例 (0-100)
        """
        # 统计低于当前价格的成交量占比
        profit_volume = df[df['close'] < current_price]['volume'].sum()
        total_volume = df['volume'].sum()

        if total_volume > 0:
            profit_ratio = (profit_volume / total_volume) * 100
        else:
            profit_ratio = 50.0  # 默认50%

        return profit_ratio

    def _determine_control_level(self, df: pd.DataFrame, concentration: float) -> str:
        """
        判断控盘程度

        综合考虑：
        1. 筹码集中度
        2. 换手率（如果有）

        Returns:
            'high' / 'medium' / 'low'
        """
        # 基于筹码集中度判断
        if concentration > 70:
            base_level = 'high'
        elif concentration > 40:
            base_level = 'medium'
        else:
            base_level = 'low'

        # 如果有换手率数据，进一步判断
        if 'turnover' in df.columns:
            avg_turnover = df['turnover'].tail(20).mean()

            # 低换手率 + 高集中度 => 高控盘
            if avg_turnover < 2 and concentration > 60:
                return 'high'
            # 高换手率 => 降低控盘等级
            elif avg_turnover > 10:
                if base_level == 'high':
                    return 'medium'
                elif base_level == 'medium':
                    return 'low'

        return base_level

    def _identify_main_behavior(self, df: pd.DataFrame, concentration: float) -> str:
        """
        识别主力行为

        通过分析筹码集中度变化趋势，判断主力是在吸筹、派发还是稳定持仓

        Returns:
            'accumulate' (吸筹) / 'distribute' (派发) / 'stable' (稳定)
        """
        # 计算前半段和后半段的集中度
        mid_point = len(df) // 2

        first_half = df.iloc[:mid_point]
        second_half = df.iloc[mid_point:]

        conc_first = self._calculate_concentration(first_half)
        conc_second = self._calculate_concentration(second_half)

        # 集中度上升 => 吸筹
        # 集中度下降 => 派发
        diff = conc_second - conc_first

        if diff > 10:
            return 'accumulate'  # 筹码集中度上升，主力吸筹
        elif diff < -10:
            return 'distribute'  # 筹码集中度下降，主力派发
        else:
            return 'stable'  # 筹码分布稳定

    def _generate_distribution_chart(self, df: pd.DataFrame, n_bins: int = 20) -> Dict:
        """
        生成筹码分布图数据

        Returns:
            {
                'price_levels': List[float],      # 价格水平
                'chip_percentage': List[float],   # 筹码占比
                'main_cost_position': int         # 主力成本所在的区间索引
            }
        """
        price_min = df['close'].min()
        price_max = df['close'].max()

        bins = np.linspace(price_min, price_max, n_bins + 1)
        price_levels = [(bins[i] + bins[i + 1]) / 2 for i in range(n_bins)]

        # 统计每个价格区间的成交量
        volume_distribution = np.zeros(n_bins)

        for i in range(len(df)):
            price = df['close'].iloc[i]
            volume = df['volume'].iloc[i]

            bin_idx = np.searchsorted(bins, price, side='right') - 1
            bin_idx = min(max(bin_idx, 0), n_bins - 1)

            volume_distribution[bin_idx] += volume

        # 转换为百分比
        total_volume = volume_distribution.sum()
        if total_volume > 0:
            chip_percentage = (volume_distribution / total_volume * 100).tolist()
        else:
            chip_percentage = [0] * n_bins

        # 找到主力成本所在区间
        main_cost_data = self._calculate_main_cost(df)
        main_cost = main_cost_data['main_cost']
        main_cost_position = np.searchsorted(bins, main_cost, side='right') - 1
        main_cost_position = min(max(main_cost_position, 0), n_bins - 1)

        return {
            'price_levels': [round(p, 2) for p in price_levels],
            'chip_percentage': [round(p, 2) for p in chip_percentage],
            'main_cost_position': int(main_cost_position)
        }

    def _generate_summary(
        self,
        main_cost: float,
        current_price: float,
        position_vs_cost: float,
        concentration: float,
        control_level: str,
        signal: str
    ) -> str:
        """
        生成分析摘要

        Returns:
            摘要文本
        """
        # 价格相对成本位置
        if position_vs_cost > 10:
            price_status = f"大幅高于主力成本（+{position_vs_cost:.1f}%）"
            price_emoji = "⬆️"
        elif position_vs_cost > 3:
            price_status = f"高于主力成本（+{position_vs_cost:.1f}%）"
            price_emoji = "↗️"
        elif position_vs_cost > -3:
            price_status = f"接近主力成本（{position_vs_cost:+.1f}%）"
            price_emoji = "➡️"
        elif position_vs_cost > -10:
            price_status = f"低于主力成本（{position_vs_cost:.1f}%）"
            price_emoji = "↘️"
        else:
            price_status = f"大幅低于主力成本（{position_vs_cost:.1f}%）"
            price_emoji = "⬇️"

        # 集中度描述
        if concentration > 70:
            conc_desc = "高度集中"
        elif concentration > 40:
            conc_desc = "中等集中"
        else:
            conc_desc = "分散"

        # 控盘程度描述
        control_map = {
            'high': '高控盘',
            'medium': '中等控盘',
            'low': '低控盘'
        }
        control_desc = control_map.get(control_level, control_level)

        # 主力行为描述
        signal_map = {
            'accumulate': '主力持续吸筹✅',
            'distribute': '主力减仓派发⚠️',
            'stable': '筹码分布稳定➡️'
        }
        signal_desc = signal_map.get(signal, signal)

        summary = (
            f"{price_emoji} {price_status}，"
            f"筹码{conc_desc}（{concentration:.0f}分），"
            f"{control_desc}，"
            f"{signal_desc}"
        )

        return summary


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=120, freq='D')

    # 模拟价格数据（主力在3000附近吸筹）
    np.random.seed(42)
    base_price = 3000
    prices = base_price + np.random.randn(120).cumsum() * 50

    # 模拟成交量（在主力成本附近放量）
    volumes = []
    for price in prices:
        if abs(price - base_price) < 100:
            volume = np.random.randint(8000000, 15000000)  # 成本区附近放量
        else:
            volume = np.random.randint(2000000, 5000000)
        volumes.append(volume)

    df = pd.DataFrame({
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'volume': volumes,
        'turnover': np.random.rand(120) * 5  # 换手率0-5%
    }, index=dates)

    # 测试
    analyzer = ChipDistributionAnalyzer(lookback_days=60)
    result = analyzer.analyze(df)

    print("\n=== 筹码分布分析结果 ===")
    print(f"主力成本: ¥{result['main_cost']:.2f}")
    print(f"成本区间: ¥{result['cost_range'][0]:.2f} - ¥{result['cost_range'][1]:.2f}")
    print(f"当前价格: ¥{result['current_price']:.2f}")
    print(f"相对成本: {result['position_vs_cost']:+.2f}%")
    print(f"筹码集中度: {result['concentration']:.1f}/100")
    print(f"盈利筹码: {result['profit_ratio']:.1f}%")
    print(f"控盘程度: {result['control_level']}")
    print(f"主力行为: {result['signal']}")
    print(f"\n摘要: {result['summary']}")
