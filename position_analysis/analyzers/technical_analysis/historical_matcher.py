#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史点位匹配分析器
包含Phase 1(基础价格匹配)和Phase 2(技术指标增强匹配)的核心逻辑
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class HistoricalMatcher:
    """
    历史点位匹配器
    负责查找历史相似点位并计算未来收益率
    """

    def __init__(self, data_source):
        """
        初始化历史匹配器

        Args:
            data_source: 数据源实例 (USStockDataSource)
        """
        self.data_source = data_source

    def find_similar_periods(
        self,
        df: pd.DataFrame,
        current_price: float = None,
        tolerance: float = 0.05,
        min_gap_days: int = 5
    ) -> pd.DataFrame:
        """
        Phase 1: 基础价格匹配
        查找历史上价格相似的时期

        Args:
            df: 指数历史数据
            current_price: 当前价格(如不提供则使用最新价格)
            tolerance: 相似度容差(默认±5%)
            min_gap_days: 相似时期最小间隔天数

        Returns:
            包含相似时期的DataFrame
        """
        if df.empty:
            logger.warning("数据为空,无法查找相似时期")
            return pd.DataFrame()

        if current_price is None:
            current_price = df['close'].iloc[-1]

        # 定义相似区间
        lower_bound = current_price * (1 - tolerance)
        upper_bound = current_price * (1 + tolerance)

        # 筛选相似点位
        similar = df[
            (df['close'] >= lower_bound) &
            (df['close'] <= upper_bound)
        ].copy()

        # 过滤: 排除最近的数据点(避免用当前预测当前)
        cutoff_date = df.index[-1] - timedelta(days=min_gap_days)
        similar = similar[similar.index <= cutoff_date]

        logger.info(
            f"在 {lower_bound:.2f}-{upper_bound:.2f} 区间 "
            f"共找到 {len(similar)} 个相似点位"
        )

        return similar

    def find_similar_periods_enhanced(
        self,
        df: pd.DataFrame,
        current_price: float = None,
        tolerance: float = 0.05,
        min_gap_days: int = 5,
        use_technical_filter: bool = True,
        rsi_tolerance: float = 15.0,
        percentile_tolerance: float = 15.0
    ) -> pd.DataFrame:
        """
        Phase 2: 技术指标增强匹配
        在价格匹配基础上,增加技术指标过滤

        Args:
            df: 指数历史数据
            current_price: 当前价格
            tolerance: 价格相似度容差
            min_gap_days: 最小间隔天数
            use_technical_filter: 是否启用技术指标过滤
            rsi_tolerance: RSI容差(默认±15)
            percentile_tolerance: 52周分位数容差(默认±15%)

        Returns:
            技术指标增强过滤后的相似时期DataFrame
        """
        # 1. 基础价格过滤(Phase 1)
        similar = self.find_similar_periods(
            df,
            current_price,
            tolerance,
            min_gap_days
        )

        if similar.empty or not use_technical_filter:
            return similar

        # 2. 计算当前技术指标
        current_indicators = self.data_source.calculate_technical_indicators(df)

        if not current_indicators:
            logger.warning("无法计算当前技术指标,跳过技术指标过滤")
            return similar

        current_rsi = current_indicators.get('rsi', 50)
        current_dist_to_high = current_indicators.get('dist_to_high_pct', 0)
        current_ma_state = self._get_ma_state(current_indicators)

        logger.debug(
            f"当前技术指标: RSI={current_rsi:.1f}, "
            f"距52周高点={current_dist_to_high:+.1f}%, "
            f"均线状态={current_ma_state}"
        )

        # 3. 过滤技术指标相似的时期
        filtered_dates = []

        for date in similar.index:
            # 获取该日期之前的数据(模拟当时的市场状态)
            hist_df = df[df.index <= date].tail(250)  # 最近250个交易日

            if len(hist_df) < 60:  # 数据不足,跳过
                continue

            hist_indicators = self.data_source.calculate_technical_indicators(hist_df)

            if not hist_indicators:
                continue

            # 检查RSI相似度
            hist_rsi = hist_indicators.get('rsi', 50)
            if abs(current_rsi - hist_rsi) > rsi_tolerance:
                continue

            # 检查距52周高点位置相似度
            hist_dist_to_high = hist_indicators.get('dist_to_high_pct', 0)
            if abs(current_dist_to_high - hist_dist_to_high) > percentile_tolerance:
                continue

            # 检查均线状态
            hist_ma_state = self._get_ma_state(hist_indicators)
            if current_ma_state != hist_ma_state:
                continue

            filtered_dates.append(date)

        # 4. 返回过滤后的结果
        if len(filtered_dates) == 0:
            logger.warning(
                f"技术指标过滤后无匹配时期 "
                f"(原{len(similar)}个 → 0个)"
            )
            return pd.DataFrame()

        filtered_similar = df.loc[filtered_dates]

        logger.info(
            f"技术指标增强匹配: "
            f"{len(similar)}个 → {len(filtered_similar)}个相似点位 "
            f"(过滤率{(1-len(filtered_similar)/len(similar))*100:.1f}%)"
        )

        return filtered_similar

    def _get_ma_state(self, indicators: Dict) -> str:
        """
        判断均线排列状态

        Args:
            indicators: 技术指标字典

        Returns:
            '多头排列' / '空头排列' / '震荡'
        """
        price = indicators.get('latest_price', 0)
        ma20 = indicators.get('ma20', price)
        ma60 = indicators.get('ma60', price)
        ma250 = indicators.get('ma250', price)

        # 完美多头: 价格 > MA20 > MA60 > MA250
        if price > ma20 and ma20 > ma60 and ma60 > ma250:
            return '多头排列'

        # 完美空头: 价格 < MA20 < MA60 < MA250
        if price < ma20 and ma20 < ma60 and ma60 < ma250:
            return '空头排列'

        # 其他情况视为震荡
        return '震荡'

    def identify_market_environment(self, indicators: Dict) -> str:
        """
        Phase 2: 识别市场环境

        综合RSI、距52周高点、均线状态等判断市场环境:
        - 牛市顶部: RSI>70, 距高点<5%, 多头排列
        - 熊市底部: RSI<30, 距高点<-40%, 空头排列
        - 牛市中期: 多头排列 + 距高点-10%~-20%
        - 熊市中期: 空头排列 + 距高点-20%~-40%
        - 震荡市: 其他情况

        Args:
            indicators: 技术指标字典

        Returns:
            市场环境类型字符串
        """
        rsi = indicators.get('rsi', 50)
        dist_to_high = indicators.get('dist_to_high_pct', 0)
        ma_state = self._get_ma_state(indicators)

        # 牛市顶部特征
        if rsi > 70 and dist_to_high > -5 and ma_state == '多头排列':
            return '牛市顶部'

        # 牛市中期
        if -20 < dist_to_high < -5 and ma_state == '多头排列':
            return '牛市中期'

        # 熊市底部特征
        if rsi < 30 and dist_to_high < -40 and ma_state == '空头排列':
            return '熊市底部'

        # 熊市中期
        if -40 < dist_to_high < -20 and ma_state == '空头排列':
            return '熊市中期'

        # 震荡市
        return '震荡市'

    def calculate_future_returns(
        self,
        df: pd.DataFrame,
        similar_periods: pd.DataFrame,
        periods: List[int] = [5, 10, 20, 60]
    ) -> pd.DataFrame:
        """
        计算相似时期的后续收益率

        Args:
            df: 完整历史数据
            similar_periods: 相似时期的DataFrame
            periods: 要计算的未来周期(天数)

        Returns:
            包含未来收益率的DataFrame
        """
        if df.empty or similar_periods.empty:
            return pd.DataFrame()

        results = []

        for date in similar_periods.index:
            row = {
                'date': date,
                'price': similar_periods.loc[date, 'close']
            }

            for period in periods:
                # 查找未来第N个交易日
                future_data = df[df.index > date]

                if len(future_data) >= period:
                    future_price = future_data['close'].iloc[period - 1]
                    current_price = similar_periods.loc[date, 'close']
                    ret = (future_price - current_price) / current_price
                    row[f'return_{period}d'] = ret
                else:
                    row[f'return_{period}d'] = np.nan

            results.append(row)

        return pd.DataFrame(results)

    def calculate_probability_statistics(self, returns: pd.Series) -> Dict:
        """
        计算涨跌概率及统计指标

        Args:
            returns: 收益率序列

        Returns:
            概率统计结果字典
        """
        # 过滤NaN
        valid_returns = returns.dropna()

        if len(valid_returns) == 0:
            return {
                'sample_size': 0,
                'up_prob': 0.0,
                'down_prob': 0.0,
                'mean_return': 0.0,
                'median_return': 0.0,
                'max_return': 0.0,
                'min_return': 0.0,
                'std': 0.0,
                'warning': '样本量不足'
            }

        up_count = (valid_returns > 0).sum()
        down_count = (valid_returns < 0).sum()
        total = len(valid_returns)

        return {
            'sample_size': total,
            'up_prob': float(up_count / total if total > 0 else 0),
            'down_prob': float(down_count / total if total > 0 else 0),
            'up_count': int(up_count),
            'down_count': int(down_count),
            'mean_return': float(valid_returns.mean()),
            'median_return': float(valid_returns.median()),
            'max_return': float(valid_returns.max()),
            'min_return': float(valid_returns.min()),
            'std': float(valid_returns.std()),
            'percentile_25': float(valid_returns.quantile(0.25)),
            'percentile_75': float(valid_returns.quantile(0.75)),
        }

    def calculate_confidence(self, sample_size: int, consistency: float) -> float:
        """
        计算置信度

        Args:
            sample_size: 样本数量
            consistency: 结果一致性(上涨概率或下跌概率的最大值)

        Returns:
            置信度分数(0-1)
        """
        # 样本量得分(sigmoid函数)
        size_score = 1 / (1 + np.exp(-(sample_size - 20) / 10))

        # 一致性得分(线性映射 0.5-1.0 -> 0-1)
        consistency_score = max(0, (consistency - 0.5) / 0.5)

        # 综合得分
        confidence = 0.6 * size_score + 0.4 * consistency_score

        return min(1.0, max(0.0, confidence))

    def calculate_position_advice_enhanced(
        self,
        up_prob: float,
        confidence: float,
        mean_return: float,
        std: float,
        market_env: str = '震荡市'
    ) -> Dict:
        """
        Phase 2: 考虑市场环境的增强仓位建议

        在Phase 1基础上,根据市场环境调整仓位:
        - 牛市顶部: 即使上涨概率高,也降低仓位(高位风险)
        - 熊市底部: 即使下跌概率高,也提高仓位(抄底机会)

        Args:
            up_prob: 上涨概率
            confidence: 置信度
            mean_return: 平均收益率
            std: 收益率标准差
            market_env: 市场环境

        Returns:
            增强的仓位建议字典
        """
        # 1. 基础仓位(Phase 1逻辑)
        if up_prob >= 0.75 and confidence >= 0.8:
            base_position = 0.8
            signal = "强买入"
        elif up_prob >= 0.65 and confidence >= 0.7:
            base_position = 0.65
            signal = "买入"
        elif up_prob <= 0.35 and confidence >= 0.7:
            base_position = 0.3
            signal = "卖出"
        elif up_prob <= 0.25 and confidence >= 0.8:
            base_position = 0.2
            signal = "强卖出"
        else:
            base_position = 0.5
            signal = "中性"

        # 2. Kelly公式调整
        if mean_return > 0 and std > 0:
            kelly = mean_return / (std ** 2) if std > 0 else 0
            kelly = max(0, min(1, kelly * 0.5))  # 半凯利
            final_position = 0.7 * base_position + 0.3 * kelly
        else:
            final_position = base_position

        # 3. 根据市场环境调整(Phase 2核心)
        env_factor = 1.0
        warning = None

        if market_env == '牛市顶部':
            # 高位风险,大幅降低仓位
            env_factor = 0.6
            warning = "⚠️ 当前处于牛市顶部,建议谨慎,降低仓位"
            if signal in ['强买入', '买入']:
                signal = "谨慎观望"

        elif market_env == '牛市中期':
            # 牛市中期,略微降低仓位
            env_factor = 0.85
            warning = "当前处于牛市中期,注意回调风险"

        elif market_env == '熊市底部':
            # 抄底机会,提高仓位
            env_factor = 1.2
            warning = "当前处于熊市底部,可能是抄底机会"
            if signal in ['卖出', '强卖出']:
                signal = "等待企稳"

        elif market_env == '熊市中期':
            # 熊市中期,保守
            env_factor = 0.9

        # 应用环境调整因子
        final_position = final_position * env_factor
        final_position = max(0.1, min(0.9, final_position))  # 限制在10%-90%

        result = {
            'signal': signal,
            'recommended_position': float(final_position),
            'base_position': float(base_position),
            'market_environment': market_env,
            'env_adjustment_factor': float(env_factor),
            'description': self._get_position_description(final_position, signal)
        }

        if warning:
            result['warning'] = warning

        return result

    def _get_position_description(self, position: float, signal: str) -> str:
        """
        获取仓位描述

        Args:
            position: 仓位比例
            signal: 操作信号

        Returns:
            仓位描述字符串
        """
        if position >= 0.8:
            return f"{signal}:建议重仓配置({position*100:.0f}%左右)"
        elif position >= 0.6:
            return f"{signal}:建议标准配置({position*100:.0f}%左右)"
        elif position >= 0.4:
            return f"{signal}:建议轻仓观望({position*100:.0f}%左右)"
        else:
            return f"{signal}:建议低仓防守({position*100:.0f}%左右)"
