#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股自定义波动率恐慌指数分析器
Hong Kong Market Volatility Index (HKVI)

基于港股市场历史波动率、成交量、南向资金等指标构建恐慌指数
参考VIX和VHSI的计算逻辑,针对港股市场特点进行定制
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class HKVolatilityIndex:
    """
    港股自定义波动率恐慌指数分析器

    计算方法:
    1. 历史波动率 (Historical Volatility, 40%权重)
       - 计算20日/60日历史波动率
    2. 涨跌幅波动 (Price Range Volatility, 30%权重)
       - 基于日内最高最低价波动
    3. 成交量波动 (Volume Volatility, 30%权重)
       - 成交量异常放大时市场恐慌

    指数区间(参考VHSI):
    - HKVI > 30: 极度恐慌
    - HKVI 25-30: 恐慌上升
    - HKVI 15-25: 正常区间
    - HKVI < 15: 过度乐观
    """

    # 阈值定义(与VHSI对齐)
    PANIC_THRESHOLD = 30
    HIGH_THRESHOLD = 25
    NORMAL_HIGH = 25
    NORMAL_LOW = 15
    COMPLACENT_THRESHOLD = 12

    def __init__(self):
        """初始化港股波动率指数分析器"""
        logger.info("港股波动率恐慌指数分析器初始化")

    def calculate_hkvi(self, df: pd.DataFrame) -> Dict:
        """
        计算港股波动率恐慌指数

        Args:
            df: 指数历史数据,需包含 open/high/low/close/volume

        Returns:
            HKVI分析结果字典
        """
        try:
            if df.empty or len(df) < 60:
                return {'error': '港股数据不足,无法计算波动率指数'}

            # 1. 计算历史波动率 (Historical Volatility)
            hv_component = self._calculate_historical_volatility(df)

            # 2. 计算价格区间波动率 (Price Range Volatility)
            prv_component = self._calculate_price_range_volatility(df)

            # 3. 计算成交量波动率 (Volume Volatility)
            vv_component = self._calculate_volume_volatility(df)

            # 加权计算HKVI
            hkvi_value = (
                hv_component['score'] * 0.4 +
                prv_component['score'] * 0.3 +
                vv_component['score'] * 0.3
            )

            # 状态判断
            status_info = self._get_status(hkvi_value)

            # 生成信号
            signal_info = self._generate_signal(hkvi_value, df)

            # 历史分位数
            percentile_info = self._calculate_percentile(df, hkvi_value)

            result = {
                'hkvi_value': float(hkvi_value),
                'status': status_info['status'],
                'level': status_info['level'],
                'emoji': status_info['emoji'],
                'components': {
                    'historical_volatility': hv_component,
                    'price_range_volatility': prv_component,
                    'volume_volatility': vv_component
                },
                'signal': signal_info,
                'percentile': percentile_info,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            logger.info(f"港股HKVI: {hkvi_value:.2f} ({status_info['status']})")
            return result

        except Exception as e:
            logger.error(f"港股波动率指数计算失败: {str(e)}")
            return {'error': str(e)}

    def _calculate_historical_volatility(self, df: pd.DataFrame) -> Dict:
        """
        计算历史波动率(HV)

        Args:
            df: 历史数据

        Returns:
            历史波动率组件字典
        """
        # 计算对数收益率
        returns = np.log(df['close'] / df['close'].shift(1)).dropna()

        # 20日滚动波动率(年化)
        hv_20 = returns.rolling(window=20).std() * np.sqrt(252) * 100

        # 最近的20日波动率
        current_hv = hv_20.iloc[-1] if len(hv_20) > 0 else 20

        # 归一化到0-100分数
        # 港股正常波动率约18-28%,映射到18-45分
        score = current_hv * 1.8
        score = min(100, max(0, score))  # 限制在0-100

        return {
            'score': float(score),
            'current_hv_20d': float(current_hv),
            'description': f'20日历史波动率: {current_hv:.2f}%'
        }

    def _calculate_price_range_volatility(self, df: pd.DataFrame) -> Dict:
        """
        计算价格区间波动率(PRV)
        基于日内高低价波动幅度

        Args:
            df: 历史数据

        Returns:
            价格区间波动率组件字典
        """
        # 日内波动率 = (high - low) / close
        daily_range = (df['high'] - df['low']) / df['close']

        # 20日平均日内波动率
        avg_range_20 = daily_range.rolling(window=20).mean()

        current_range = avg_range_20.iloc[-1] if len(avg_range_20) > 0 else 0.025

        # 归一化到0-100分数
        # 港股正常日内波动2.5-5%,映射到25-50分
        score = (current_range * 100) * 1.2
        score = min(100, max(0, score))

        return {
            'score': float(score),
            'current_range_20d': float(current_range * 100),
            'description': f'20日平均日内波动: {current_range * 100:.2f}%'
        }

    def _calculate_volume_volatility(self, df: pd.DataFrame) -> Dict:
        """
        计算成交量波动率(VV)
        成交量异常放大通常伴随恐慌

        Args:
            df: 历史数据

        Returns:
            成交量波动率组件字典
        """
        if 'volume' not in df.columns or df['volume'].sum() == 0:
            # 没有成交量数据,返回中性分数
            return {
                'score': 25.0,
                'volume_ratio': 1.0,
                'description': '成交量数据不可用'
            }

        # 当日成交量 / 20日平均成交量
        avg_volume_20 = df['volume'].rolling(window=20).mean()
        volume_ratio = df['volume'] / avg_volume_20

        current_ratio = volume_ratio.iloc[-1] if len(volume_ratio) > 0 else 1.0

        # 归一化到0-100分数
        # 港股量比1.0-2.0对应20-40分, >3.0对应恐慌
        if current_ratio < 1.0:
            score = 18  # 缩量,市场冷清
        elif current_ratio < 2.0:
            score = 20 + (current_ratio - 1.0) * 20  # 1.0-2.0映射到20-40
        elif current_ratio < 3.0:
            score = 40 + (current_ratio - 2.0) * 30  # 2.0-3.0映射到40-70
        else:
            score = min(100, 70 + (current_ratio - 3.0) * 15)  # >3.0映射到70+

        return {
            'score': float(score),
            'volume_ratio': float(current_ratio),
            'description': f'成交量比: {current_ratio:.2f}x'
        }

    def _get_status(self, hkvi_value: float) -> Dict:
        """
        根据HKVI值判断市场状态

        Args:
            hkvi_value: HKVI指数值

        Returns:
            状态信息字典
        """
        if hkvi_value >= self.PANIC_THRESHOLD:
            return {
                'status': '极度恐慌',
                'level': 'extreme_panic',
                'emoji': '😱'
            }
        elif hkvi_value >= self.HIGH_THRESHOLD:
            return {
                'status': '恐慌上升',
                'level': 'high',
                'emoji': '⚠️'
            }
        elif hkvi_value >= self.NORMAL_LOW:
            return {
                'status': '正常区间',
                'level': 'normal',
                'emoji': '😊'
            }
        elif hkvi_value >= self.COMPLACENT_THRESHOLD:
            return {
                'status': '偏低',
                'level': 'low',
                'emoji': '🙂'
            }
        else:
            return {
                'status': '过度乐观',
                'level': 'complacent',
                'emoji': '😌'
            }

    def _generate_signal(self, hkvi_value: float, df: pd.DataFrame) -> Dict:
        """
        生成交易信号

        Args:
            hkvi_value: HKVI指数值
            df: 历史数据

        Returns:
            交易信号字典
        """
        # HKVI突变检测
        if len(df) >= 6:
            # 检测价格波动变化
            recent_volatility = df['close'].pct_change().tail(5).std()
            avg_volatility = df['close'].pct_change().tail(60).std()

            if recent_volatility > avg_volatility * 2:
                spike_signal = "港股波动率快速上升,市场不确定性增加"
            elif recent_volatility < avg_volatility * 0.5:
                spike_signal = "港股波动率快速下降,市场趋于稳定"
            else:
                spike_signal = "港股波动率变化正常"
        else:
            spike_signal = "数据不足"

        # 基于HKVI值的信号
        if hkvi_value >= self.PANIC_THRESHOLD:
            signal = "强烈关注"
            description = f"HKVI>={self.PANIC_THRESHOLD},港股市场极度恐慌,可能是抄底良机"
            action = "逢低布局优质港股,分批建仓"
        elif hkvi_value >= self.HIGH_THRESHOLD:
            signal = "关注"
            description = f"HKVI>{self.HIGH_THRESHOLD},港股恐慌上升,波动加大"
            action = "控制仓位,等待市场企稳"
        elif hkvi_value >= self.NORMAL_LOW:
            signal = "正常"
            description = f"HKVI在正常区间,港股市场情绪稳定"
            action = "正常操作,可适度乐观"
        else:
            signal = "警惕"
            description = f"HKVI<{self.NORMAL_LOW},港股市场过度乐观,警惕调整风险"
            action = "降低仓位,锁定利润,警惕回调"

        return {
            'signal': signal,
            'description': description,
            'action': action,
            'spike_signal': spike_signal
        }

    def _calculate_percentile(self, df: pd.DataFrame, current_hkvi: float) -> Dict:
        """
        计算HKVI历史分位数(简化版)

        Args:
            df: 历史数据
            current_hkvi: 当前HKVI值

        Returns:
            分位数信息
        """
        # 简化:基于历史波动率估算分位数
        returns = np.log(df['close'] / df['close'].shift(1)).dropna()
        hv_series = returns.rolling(window=20).std() * np.sqrt(252) * 100

        # 当前波动率在历史中的分位数
        if len(hv_series) > 60:
            percentile = (hv_series < hv_series.iloc[-1]).sum() / len(hv_series) * 100
        else:
            percentile = 50.0

        return {
            'percentile_60d': float(percentile),
            'description': f'当前波动率处于近60日的 {percentile:.1f}% 分位'
        }


def test_hk_volatility_index():
    """测试港股波动率指数"""
    print("=" * 80)
    print("港股自定义波动率恐慌指数测试")
    print("=" * 80)

    # 生成模拟数据
    dates = pd.date_range(start='2024-01-01', end='2025-10-15', freq='D')
    np.random.seed(43)

    # 模拟股价数据(港股波动略大)
    close = 100 + np.cumsum(np.random.randn(len(dates)) * 2.5)
    high = close + np.abs(np.random.randn(len(dates))) * 2.5
    low = close - np.abs(np.random.randn(len(dates))) * 2.5
    volume = np.random.randint(2000000, 8000000, len(dates))

    df = pd.DataFrame({
        'close': close,
        'high': high,
        'low': low,
        'open': close,
        'volume': volume
    }, index=dates)

    analyzer = HKVolatilityIndex()
    result = analyzer.calculate_hkvi(df)

    if 'error' not in result:
        print(f"\n当前HKVI: {result['hkvi_value']:.2f} {result['emoji']}")
        print(f"状态: {result['status']}")
        print(f"\n组件分解:")
        for comp_name, comp_data in result['components'].items():
            print(f"  {comp_name}:")
            print(f"    分数: {comp_data['score']:.2f}")
            print(f"    {comp_data['description']}")

        print(f"\n信号:")
        print(f"  {result['signal']['signal']}: {result['signal']['description']}")
        print(f"  建议: {result['signal']['action']}")
    else:
        print(f"\n计算失败: {result['error']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    test_hk_volatility_index()
