#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIX恐慌指数分析器 - Phase 3
提供VIX深度分析,包括分位数、相关性、交易信号等
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class VIXAnalyzer:
    """
    VIX恐慌指数分析器

    VIX (CBOE Volatility Index) 是衡量市场恐慌程度的指标
    - VIX > 30: 极度恐慌,可能是抄底机会
    - VIX 20-30: 恐慌上升,市场不确定性增加
    - VIX 15-20: 正常区间,市场情绪稳定
    - VIX < 15: 过度乐观,警惕调整风险
    """

    # VIX阈值定义
    VIX_PANIC_THRESHOLD = 30  # 恐慌阈值
    VIX_HIGH_THRESHOLD = 25   # 高位阈值
    VIX_NORMAL_HIGH = 20      # 正常上限
    VIX_NORMAL_LOW = 15       # 正常下限
    VIX_COMPLACENT_THRESHOLD = 12  # 过度乐观阈值

    def __init__(self, data_source):
        """
        初始化VIX分析器

        Args:
            data_source: 数据源实例 (USStockDataSource)
        """
        self.data_source = data_source

    def analyze_vix(self, period: str = "5y") -> Dict:
        """
        完整VIX分析

        Args:
            period: 历史数据周期

        Returns:
            VIX分析结果字典
        """
        try:
            # 获取VIX历史数据
            vix_df = self.data_source.get_us_index_daily('VIX', period=period)

            if vix_df.empty:
                return {'error': 'VIX数据获取失败'}

            # 获取标普500数据(用于相关性分析)
            spx_df = self.data_source.get_us_index_daily('SPX', period=period)

            result = {
                'timestamp': datetime.now(),
                'current_state': self.get_vix_current_state(vix_df),
                'percentile': self.calculate_vix_percentile(vix_df),
                'signal': self.generate_vix_signal(vix_df)
            }

            # 如果有标普500数据,计算相关性
            if not spx_df.empty:
                result['correlation'] = self.analyze_vix_spx_correlation(vix_df, spx_df)

            return result

        except Exception as e:
            logger.error(f"VIX分析失败: {str(e)}")
            return {'error': str(e)}

    def get_vix_current_state(self, vix_df: pd.DataFrame) -> Dict:
        """
        获取VIX当前状态

        Args:
            vix_df: VIX历史数据

        Returns:
            当前状态字典
        """
        if vix_df.empty or len(vix_df) < 2:
            return {}

        latest = vix_df.iloc[-1]
        prev = vix_df.iloc[-2]

        current_vix = float(latest['close'])
        change = float(latest['close'] - prev['close'])
        change_pct = float(change / prev['close'] * 100)

        # 判断VIX状态
        if current_vix >= self.VIX_PANIC_THRESHOLD:
            status = "极度恐慌"
            level = "extreme_panic"
        elif current_vix >= self.VIX_HIGH_THRESHOLD:
            status = "恐慌上升"
            level = "high"
        elif current_vix >= self.VIX_NORMAL_LOW:
            status = "正常区间"
            level = "normal"
        elif current_vix >= self.VIX_COMPLACENT_THRESHOLD:
            status = "偏低"
            level = "low"
        else:
            status = "过度乐观"
            level = "complacent"

        # 周变化
        if len(vix_df) >= 5:
            week_ago = vix_df.iloc[-6]
            week_change = float(latest['close'] - week_ago['close'])
            week_change_pct = float(week_change / week_ago['close'] * 100)
        else:
            week_change = 0
            week_change_pct = 0

        return {
            'vix_value': current_vix,
            'change': change,
            'change_pct': change_pct,
            'week_change': week_change,
            'week_change_pct': week_change_pct,
            'status': status,
            'level': level,
            'date': vix_df.index[-1].strftime('%Y-%m-%d')
        }

    def calculate_vix_percentile(
        self,
        vix_df: pd.DataFrame,
        periods: list = None
    ) -> Dict:
        """
        计算VIX历史分位数

        Args:
            vix_df: VIX历史数据
            periods: 要计算的周期列表(天数),默认[30, 60, 252, 1260]

        Returns:
            分位数字典
        """
        if periods is None:
            periods = [30, 60, 252, 1260]  # 1个月/2个月/1年/5年

        if vix_df.empty:
            return {}

        current_vix = vix_df['close'].iloc[-1]
        percentiles = {}

        for period in periods:
            if len(vix_df) >= period:
                hist_data = vix_df['close'].tail(period)
                # 计算当前VIX在历史中的分位数
                percentile = (hist_data < current_vix).sum() / len(hist_data) * 100

                # 确定周期标签
                if period == 30:
                    label = '1个月'
                elif period == 60:
                    label = '2个月'
                elif period == 252:
                    label = '1年'
                elif period == 1260:
                    label = '5年'
                else:
                    label = f'{period}天'

                percentiles[label] = {
                    'percentile': float(percentile),
                    'min': float(hist_data.min()),
                    'max': float(hist_data.max()),
                    'median': float(hist_data.median()),
                    'mean': float(hist_data.mean())
                }

        return percentiles

    def analyze_vix_spx_correlation(
        self,
        vix_df: pd.DataFrame,
        spx_df: pd.DataFrame
    ) -> Dict:
        """
        分析VIX与标普500的相关性

        Args:
            vix_df: VIX历史数据
            spx_df: 标普500历史数据

        Returns:
            相关性分析字典
        """
        # 对齐数据
        common_dates = vix_df.index.intersection(spx_df.index)

        if len(common_dates) < 30:
            return {'error': '数据不足,无法计算相关性'}

        vix_aligned = vix_df.loc[common_dates, 'close']
        spx_aligned = spx_df.loc[common_dates, 'close']

        # 计算收益率
        vix_returns = vix_aligned.pct_change().dropna()
        spx_returns = spx_aligned.pct_change().dropna()

        # 对齐收益率数据
        common_return_dates = vix_returns.index.intersection(spx_returns.index)
        vix_returns = vix_returns.loc[common_return_dates]
        spx_returns = spx_returns.loc[common_return_dates]

        # 计算相关系数
        correlation = vix_returns.corr(spx_returns)

        # 分析VIX高位时标普500的表现
        vix_high = vix_aligned > self.VIX_HIGH_THRESHOLD
        vix_low = vix_aligned < self.VIX_NORMAL_LOW

        # VIX高位(>25)时,未来20日标普500表现
        high_vix_future_returns = []
        for date in vix_aligned[vix_high].index:
            future_dates = spx_aligned.index[spx_aligned.index > date]
            if len(future_dates) >= 20:
                future_date = future_dates[19]  # 第20个交易日
                ret = (spx_aligned[future_date] - spx_aligned[date]) / spx_aligned[date]
                high_vix_future_returns.append(ret)

        # VIX低位(<15)时,未来20日标普500表现
        low_vix_future_returns = []
        for date in vix_aligned[vix_low].index:
            future_dates = spx_aligned.index[spx_aligned.index > date]
            if len(future_dates) >= 20:
                future_date = future_dates[19]
                ret = (spx_aligned[future_date] - spx_aligned[date]) / spx_aligned[date]
                low_vix_future_returns.append(ret)

        result = {
            'correlation_coefficient': float(correlation),
            'correlation_strength': self._interpret_correlation(correlation),
        }

        if high_vix_future_returns:
            result['high_vix_performance'] = {
                'sample_size': len(high_vix_future_returns),
                'mean_return_20d': float(np.mean(high_vix_future_returns) * 100),
                'median_return_20d': float(np.median(high_vix_future_returns) * 100),
                'up_prob': float((np.array(high_vix_future_returns) > 0).sum() / len(high_vix_future_returns))
            }

        if low_vix_future_returns:
            result['low_vix_performance'] = {
                'sample_size': len(low_vix_future_returns),
                'mean_return_20d': float(np.mean(low_vix_future_returns) * 100),
                'median_return_20d': float(np.median(low_vix_future_returns) * 100),
                'up_prob': float((np.array(low_vix_future_returns) > 0).sum() / len(low_vix_future_returns))
            }

        return result

    def _interpret_correlation(self, corr: float) -> str:
        """
        解释相关系数

        Args:
            corr: 相关系数

        Returns:
            相关性强度描述
        """
        if corr < -0.7:
            return "强负相关"
        elif corr < -0.5:
            return "中等负相关"
        elif corr < -0.3:
            return "弱负相关"
        elif corr < 0.3:
            return "几乎无相关"
        elif corr < 0.5:
            return "弱正相关"
        elif corr < 0.7:
            return "中等正相关"
        else:
            return "强正相关"

    def generate_vix_signal(self, vix_df: pd.DataFrame) -> Dict:
        """
        生成VIX交易信号

        Args:
            vix_df: VIX历史数据

        Returns:
            交易信号字典
        """
        if vix_df.empty:
            return {}

        current_vix = vix_df['close'].iloc[-1]

        # VIX突变检测(5日内涨幅)
        if len(vix_df) >= 6:
            vix_5d_ago = vix_df['close'].iloc[-6]
            vix_spike = (current_vix - vix_5d_ago) / vix_5d_ago

            # VIX飙升>50%,可能是恐慌性抛售
            if vix_spike > 0.5:
                spike_signal = "VIX飙升>50%,恐慌性抛售,关注抄底机会"
            elif vix_spike > 0.3:
                spike_signal = "VIX快速上升,市场不确定性增加"
            elif vix_spike < -0.3:
                spike_signal = "VIX快速下降,恐慌情绪缓解"
            else:
                spike_signal = "VIX变化正常"
        else:
            vix_spike = 0
            spike_signal = "数据不足"

        # 基于当前VIX值的信号
        if current_vix >= self.VIX_PANIC_THRESHOLD:
            signal = "强烈关注"
            description = f"VIX>={self.VIX_PANIC_THRESHOLD},市场极度恐慌,历史上往往是抄底良机"
            action = "逢低布局优质资产,分批建仓"
            risk_level = "高"
        elif current_vix >= self.VIX_HIGH_THRESHOLD:
            signal = "关注"
            description = f"VIX>{self.VIX_HIGH_THRESHOLD},市场恐慌上升,波动加大"
            action = "控制仓位,等待市场企稳"
            risk_level = "中高"
        elif current_vix >= self.VIX_NORMAL_HIGH:
            signal = "正常"
            description = f"VIX在正常区间上沿({self.VIX_NORMAL_LOW}-{self.VIX_NORMAL_HIGH})"
            action = "正常操作,适度谨慎"
            risk_level = "中"
        elif current_vix >= self.VIX_NORMAL_LOW:
            signal = "正常"
            description = f"VIX在正常区间下沿({self.VIX_NORMAL_LOW}-{self.VIX_NORMAL_HIGH})"
            action = "正常操作,可适度乐观"
            risk_level = "低"
        else:
            signal = "警惕"
            description = f"VIX<{self.VIX_NORMAL_LOW},市场过度乐观,警惕调整风险"
            action = "降低仓位,锁定利润,警惕回调"
            risk_level = "中"

        return {
            'signal': signal,
            'description': description,
            'action': action,
            'risk_level': risk_level,
            'vix_value': float(current_vix),
            'vix_5d_change_pct': float(vix_spike * 100),
            'spike_signal': spike_signal
        }


def test_vix_analyzer():
    """测试VIX分析器"""
    print("=" * 80)
    print("VIX恐慌指数分析器测试")
    print("=" * 80)

    from src.data_sources.us_stock_source import USStockDataSource

    data_source = USStockDataSource()
    analyzer = VIXAnalyzer(data_source)

    # 完整VIX分析
    print("\n测试VIX完整分析...")
    result = analyzer.analyze_vix(period="5y")

    if 'error' not in result:
        # 当前状态
        state = result.get('current_state', {})
        print(f"\n当前VIX状态:")
        print(f"  VIX值: {state.get('vix_value', 0):.2f}")
        print(f"  日变化: {state.get('change', 0):+.2f} ({state.get('change_pct', 0):+.2f}%)")
        print(f"  状态: {state.get('status', 'N/A')}")

        # 分位数
        percentiles = result.get('percentile', {})
        if percentiles:
            print(f"\nVIX历史分位数:")
            for period, data in percentiles.items():
                print(f"  {period}: {data['percentile']:.1f}% (均值 {data['mean']:.2f})")

        # 交易信号
        signal = result.get('signal', {})
        if signal:
            print(f"\nVIX交易信号:")
            print(f"  信号: {signal.get('signal', 'N/A')}")
            print(f"  描述: {signal.get('description', 'N/A')}")
            print(f"  建议: {signal.get('action', 'N/A')}")

        # 相关性
        corr = result.get('correlation', {})
        if corr and 'error' not in corr:
            print(f"\nVIX与标普500相关性:")
            print(f"  相关系数: {corr.get('correlation_coefficient', 0):.3f}")
            print(f"  相关强度: {corr.get('correlation_strength', 'N/A')}")

            if 'high_vix_performance' in corr:
                perf = corr['high_vix_performance']
                print(f"\n  VIX高位(>25)后20日标普500表现:")
                print(f"    样本量: {perf['sample_size']} 次")
                print(f"    平均收益: {perf['mean_return_20d']:+.2f}%")
                print(f"    上涨概率: {perf['up_prob']:.1%}")

    else:
        print(f"\n分析失败: {result.get('error', '未知错误')}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    test_vix_analyzer()
