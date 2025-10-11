#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股市场分析器 - Phase 1 MVP版本
基于历史点位对比分析,支持标普500、纳斯达克、纳斯达克100、VIX
复用historical_position_analyzer.py的核心逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from data_sources.us_stock_source import USStockDataSource
from .analyzers import VIXAnalyzer, SectorRotationAnalyzer, VolumeAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class USIndexConfig:
    """美股指数配置"""
    code: str
    name: str
    symbol: str  # yfinance symbol


# 支持的美股指数
US_INDICES = {
    'SPX': USIndexConfig('SPX', '标普500', '^GSPC'),
    'NASDAQ': USIndexConfig('NASDAQ', '纳斯达克综合', '^IXIC'),
    'NDX': USIndexConfig('NDX', '纳斯达克100', '^NDX'),
    'VIX': USIndexConfig('VIX', 'VIX恐慌指数', '^VIX'),
    'DJI': USIndexConfig('DJI', '道琼斯工业', '^DJI'),
    'RUT': USIndexConfig('RUT', '罗素2000', '^RUT'),
}

# 默认分析的指数
DEFAULT_US_INDICES = ['SPX', 'NASDAQ', 'NDX', 'VIX']


class USMarketAnalyzer:
    """美股市场分析器"""

    def __init__(self):
        self.data_source = USStockDataSource()
        self.data_cache = {}  # 数据缓存

        # Phase 3: 初始化分析器
        self.vix_analyzer = VIXAnalyzer(self.data_source)
        self.sector_analyzer = SectorRotationAnalyzer(self.data_source)
        self.volume_analyzer = VolumeAnalyzer()

        logger.info("美股市场分析器初始化完成")

    def get_index_data(
        self,
        index_code: str,
        period: str = "5y"
    ) -> pd.DataFrame:
        """
        获取指数历史数据

        Args:
            index_code: 指数代码 (SPX/NASDAQ/NDX/VIX)
            period: 时间周期 (默认5年)

        Returns:
            包含OHLCV的DataFrame
        """
        # 检查缓存
        cache_key = f"{index_code}_{period}"
        if cache_key in self.data_cache:
            logger.info(f"使用缓存的{index_code}数据")
            return self.data_cache[cache_key]

        # 从数据源获取
        df = self.data_source.get_us_index_daily(index_code, period=period)

        if not df.empty:
            # 计算收益率
            df['return'] = df['close'].pct_change()
            # 缓存
            self.data_cache[cache_key] = df

        return df

    def get_current_positions(
        self,
        indices: List[str] = None
    ) -> Dict[str, Dict]:
        """
        获取当前各指数点位

        Args:
            indices: 指数代码列表,默认为DEFAULT_US_INDICES

        Returns:
            {index_code: {'name': xx, 'price': xx, 'date': xx}}
        """
        if indices is None:
            indices = DEFAULT_US_INDICES

        positions = {}

        for code in indices:
            if code not in US_INDICES:
                logger.warning(f"不支持的指数代码: {code}")
                continue

            try:
                config = US_INDICES[code]
                df = self.get_index_data(code, period="5d")  # 只获取最近5天

                if df.empty:
                    logger.warning(f"{config.name}数据为空")
                    continue

                current_price = df['close'].iloc[-1]
                positions[code] = {
                    'name': config.name,
                    'price': float(current_price),
                    'date': df.index[-1].strftime('%Y-%m-%d'),
                    'change_pct': float((current_price - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0.0
                }
                logger.info(f"{config.name}: {current_price:.2f} ({positions[code]['change_pct']:+.2f}%)")

            except Exception as e:
                logger.error(f"获取{code}当前点位失败: {str(e)}")
                continue

        return positions

    def find_similar_periods(
        self,
        index_code: str,
        current_price: float = None,
        tolerance: float = 0.05,
        min_gap_days: int = 5,
        period: str = "5y"
    ) -> pd.DataFrame:
        """
        查找历史相似点位时期

        Args:
            index_code: 指数代码
            current_price: 当前价格(如不提供则使用最新价格)
            tolerance: 相似度容差(默认±5%)
            min_gap_days: 相似时期最小间隔天数
            period: 历史数据周期

        Returns:
            包含相似时期的DataFrame
        """
        df = self.get_index_data(index_code, period=period)

        if df.empty:
            logger.warning(f"{index_code}数据为空")
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
            f"{US_INDICES[index_code].name} "
            f"在 {lower_bound:.2f}-{upper_bound:.2f} 区间 "
            f"共找到 {len(similar)} 个相似点位"
        )

        return similar

    def find_similar_periods_enhanced(
        self,
        index_code: str,
        current_price: float = None,
        tolerance: float = 0.05,
        min_gap_days: int = 5,
        period: str = "5y",
        use_technical_filter: bool = True,
        rsi_tolerance: float = 15.0,
        percentile_tolerance: float = 15.0
    ) -> pd.DataFrame:
        """
        Phase 2: 技术指标增强的相似点位查找

        在价格匹配基础上,增加技术指标过滤:
        1. RSI相似度(识别超买/超卖状态)
        2. 距52周高点的位置相似
        3. 均线排列状态相同

        Args:
            index_code: 指数代码
            current_price: 当前价格
            tolerance: 价格相似度容差
            min_gap_days: 最小间隔天数
            period: 历史数据周期
            use_technical_filter: 是否启用技术指标过滤
            rsi_tolerance: RSI容差(默认±15)
            percentile_tolerance: 52周分位数容差(默认±15%)

        Returns:
            技术指标增强过滤后的相似时期DataFrame
        """
        # 1. 基础价格过滤(Phase 1)
        similar = self.find_similar_periods(
            index_code,
            current_price,
            tolerance,
            min_gap_days,
            period
        )

        if similar.empty or not use_technical_filter:
            return similar

        # 获取完整历史数据用于计算指标
        df_full = self.get_index_data(index_code, period="10y")
        if df_full.empty:
            logger.warning("无法获取完整历史数据,跳过技术指标过滤")
            return similar

        # 2. 计算当前技术指标
        current_df = df_full.copy()
        current_indicators = self.data_source.calculate_technical_indicators(current_df)

        if not current_indicators:
            logger.warning("无法计算当前技术指标,跳过技术指标过滤")
            return similar

        current_rsi = current_indicators.get('rsi', 50)
        current_dist_to_high = current_indicators.get('dist_to_high_pct', 0)
        current_ma_state = self._get_ma_state(current_indicators)

        logger.info(
            f"当前技术指标: RSI={current_rsi:.1f}, "
            f"距52周高点={current_dist_to_high:+.1f}%, "
            f"均线状态={current_ma_state}"
        )

        # 3. 过滤技术指标相似的时期
        filtered_dates = []

        for date in similar.index:
            # 获取该日期之前的数据(模拟当时的市场状态)
            hist_df = df_full[df_full.index <= date].tail(250)  # 最近250个交易日

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

        filtered_similar = df_full.loc[filtered_dates]

        logger.info(
            f"{US_INDICES[index_code].name} 技术指标增强匹配: "
            f"{len(similar)}个 → {len(filtered_similar)}个相似点位 "
            f"(过滤率{(1-len(filtered_similar)/len(similar))*100:.1f}%)"
        )

        return filtered_similar

    def _get_ma_state(self, indicators: Dict) -> str:
        """
        判断均线排列状态

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

        综合RSI、距52周高点、均线状态等判断:
        - 牛市顶部: RSI>70, 距高点<5%, 多头排列
        - 熊市底部: RSI<30, 距高点<-40%, 空头排列
        - 牛市中期: 多头排列 + 距高点-10%~-20%
        - 熊市中期: 空头排列 + 距高点-20%~-40%
        - 震荡市: 其他情况

        Returns:
            市场环境类型
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
        index_code: str,
        similar_periods: pd.DataFrame,
        periods: List[int] = [5, 10, 20, 60]
    ) -> pd.DataFrame:
        """
        计算相似时期的后续收益率

        Args:
            index_code: 指数代码
            similar_periods: 相似时期的DataFrame
            periods: 要计算的未来周期(天数)

        Returns:
            包含未来收益率的DataFrame
        """
        df = self.get_index_data(index_code, period="10y")  # 获取更长时间数据

        if df.empty:
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

    def calculate_probability_statistics(
        self,
        returns: pd.Series
    ) -> Dict:
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

    def calculate_confidence(
        self,
        sample_size: int,
        consistency: float
    ) -> float:
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

    def calculate_position_advice(
        self,
        up_prob: float,
        confidence: float,
        mean_return: float,
        std: float,
        market_environment: str = None
    ) -> Dict:
        """
        Phase 2: 计算仓位建议(考虑市场环境)

        Args:
            up_prob: 上涨概率
            confidence: 置信度
            mean_return: 平均收益率
            std: 收益率标准差
            market_environment: 市场环境('牛市顶部'/'熊市底部'等)

        Returns:
            仓位建议字典
        """
        # 基础仓位(基于概率)
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

        # Kelly公式调整(如果有正期望)
        if mean_return > 0 and std > 0:
            # 简化Kelly: f = mean / variance
            kelly = mean_return / (std ** 2) if std > 0 else 0
            kelly = max(0, min(1, kelly * 0.5))  # 半凯利,限制在0-1

            # 混合基础仓位和Kelly仓位
            final_position = 0.7 * base_position + 0.3 * kelly
        else:
            final_position = base_position

        # Phase 2: 根据市场环境调整仓位
        risk_adjustment = 1.0
        adjustment_reason = ""

        if market_environment:
            if market_environment == '牛市顶部':
                risk_adjustment = 0.7  # 高位降低30%仓位
                adjustment_reason = "高位风险,降低仓位"
                # 如果是买入信号,降级
                if signal in ['强买入', '买入']:
                    signal = "谨慎买入"
            elif market_environment == '熊市底部':
                risk_adjustment = 1.2  # 底部可以适度激进
                adjustment_reason = "底部区域,可适度加仓"
                # 如果是卖出信号,升级为中性
                if signal in ['卖出', '强卖出']:
                    signal = "逢低布局"
            elif market_environment == '牛市中期':
                risk_adjustment = 0.9  # 略微谨慎
                adjustment_reason = "牛市中期,保持警惕"
            elif market_environment == '熊市中期':
                risk_adjustment = 0.8  # 较为谨慎
                adjustment_reason = "熊市中期,控制仓位"

        final_position = final_position * risk_adjustment
        final_position = max(0.1, min(0.9, final_position))  # 限制在10%-90%

        result = {
            'signal': signal,
            'recommended_position': float(final_position),
            'base_position': float(base_position),
            'description': self._get_position_description(final_position, signal)
        }

        if market_environment:
            result['market_environment'] = market_environment
            result['risk_adjustment'] = risk_adjustment
            result['adjustment_reason'] = adjustment_reason

        return result

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
            market_env: 市场环境('牛市顶部'/'牛市中期'/'熊市底部'/'熊市中期'/'震荡市')

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
        """获取仓位描述"""
        if position >= 0.8:
            return f"{signal}:建议重仓配置({position*100:.0f}%左右)"
        elif position >= 0.6:
            return f"{signal}:建议标准配置({position*100:.0f}%左右)"
        elif position >= 0.4:
            return f"{signal}:建议轻仓观望({position*100:.0f}%左右)"
        else:
            return f"{signal}:建议低仓防守({position*100:.0f}%左右)"

    def analyze_single_index(
        self,
        index_code: str,
        tolerance: float = 0.05,
        periods: List[int] = [5, 10, 20, 60],
        use_phase2: bool = False,
        use_phase3: bool = False
    ) -> Dict:
        """
        单指数完整分析

        Args:
            index_code: 指数代码
            tolerance: 相似度容差
            periods: 分析周期
            use_phase2: 是否使用Phase 2技术指标增强匹配
            use_phase3: 是否使用Phase 3深度分析(VIX/行业/成交量)

        Returns:
            完整分析结果
        """
        # 确定分析阶段标签
        if use_phase3:
            phase_label = "Phase 3(深度分析)"
        elif use_phase2:
            phase_label = "Phase 2(技术指标增强)"
        else:
            phase_label = "Phase 1(价格匹配)"

        logger.info(f"开始分析 {US_INDICES[index_code].name} [{phase_label}]...")

        result = {
            'index_code': index_code,
            'index_name': US_INDICES[index_code].name,
            'timestamp': datetime.now(),
            'analysis_phase': phase_label
        }

        try:
            # 1. 获取当前点位
            positions = self.get_current_positions([index_code])
            if index_code not in positions:
                result['error'] = '获取当前点位失败'
                return result

            current_info = positions[index_code]
            result['current_price'] = current_info['price']
            result['current_date'] = current_info['date']
            result['current_change_pct'] = current_info['change_pct']

            # 2. 计算当前技术指标和市场环境(Phase 2)
            market_env_type = '震荡市'  # 默认值
            if use_phase2:
                df = self.get_index_data(index_code, period="5y")
                if not df.empty:
                    current_indicators = self.data_source.calculate_technical_indicators(df)
                    if current_indicators:
                        rsi = current_indicators.get('rsi', 50)
                        dist_to_high = current_indicators.get('dist_to_high_pct', 0)
                        ma_state = self._get_ma_state(current_indicators)
                        market_env_type = self.identify_market_environment(current_indicators)

                        result['market_environment'] = {
                            'environment': market_env_type,
                            'rsi': rsi,
                            'dist_to_high_pct': dist_to_high,
                            'ma_state': ma_state
                        }

            # 3. 查找相似时期
            if use_phase2:
                similar = self.find_similar_periods_enhanced(
                    index_code,
                    tolerance=tolerance,
                    use_technical_filter=True
                )
            else:
                similar = self.find_similar_periods(index_code, tolerance=tolerance)

            if similar.empty:
                result['warning'] = '未找到相似历史点位'
                return result

            result['similar_periods_count'] = len(similar)

            # 4. 计算未来收益率
            future_returns = self.calculate_future_returns(index_code, similar, periods)

            # 5. 对每个周期计算概率统计
            result['period_analysis'] = {}

            for period in periods:
                col = f'return_{period}d'
                if col in future_returns.columns:
                    stats = self.calculate_probability_statistics(future_returns[col])

                    # 计算置信度
                    consistency = max(stats['up_prob'], stats['down_prob'])
                    confidence = self.calculate_confidence(stats['sample_size'], consistency)
                    stats['confidence'] = confidence

                    # 计算仓位建议 (Phase 2会考虑市场环境调整)
                    if stats['sample_size'] > 0:
                        position_advice = self.calculate_position_advice_enhanced(
                            stats['up_prob'],
                            confidence,
                            stats['mean_return'],
                            stats['std'],
                            market_env_type if use_phase2 else '震荡市'
                        )
                        stats['position_advice'] = position_advice

                    result['period_analysis'][f'{period}d'] = stats

            # Phase 3: 深度分析
            if use_phase3:
                logger.info(f"Phase 3: 执行深度分析...")
                result['phase3_analysis'] = {}

                # 1. VIX分析(只对SPX/NASDAQ/NDX执行,不对VIX自身执行)
                if index_code != 'VIX':
                    try:
                        vix_result = self.vix_analyzer.analyze_vix(period="5y")
                        if 'error' not in vix_result:
                            result['phase3_analysis']['vix'] = vix_result
                            logger.info("VIX恐慌指数分析完成")
                    except Exception as e:
                        logger.warning(f"VIX分析失败: {str(e)}")

                # 2. 行业轮动分析(对所有指数执行)
                try:
                    sector_result = self.sector_analyzer.analyze_sector_rotation(periods=[1, 5, 20, 60])
                    if 'error' not in sector_result:
                        result['phase3_analysis']['sector_rotation'] = sector_result
                        logger.info("行业轮动分析完成")
                except Exception as e:
                    logger.warning(f"行业轮动分析失败: {str(e)}")

                # 3. 成交量分析(对主要指数执行)
                if index_code in ['SPX', 'NASDAQ', 'NDX']:
                    try:
                        df = self.get_index_data(index_code, period="5y")
                        if not df.empty:
                            volume_result = self.volume_analyzer.analyze_volume(df, periods=20)
                            if 'error' not in volume_result:
                                result['phase3_analysis']['volume'] = volume_result
                                logger.info(f"{US_INDICES[index_code].name}成交量分析完成")
                    except Exception as e:
                        logger.warning(f"成交量分析失败: {str(e)}")

            logger.info(f"{US_INDICES[index_code].name} 分析完成 [{phase_label}]")

        except Exception as e:
            logger.error(f"分析{index_code}失败: {str(e)}")
            result['error'] = str(e)

        return result

    def analyze_multiple_indices(
        self,
        indices: List[str] = None,
        tolerance: float = 0.05,
        periods: List[int] = [5, 10, 20, 60],
        use_phase2: bool = False,
        use_phase3: bool = False
    ) -> Dict:
        """
        多指数联合分析

        Args:
            indices: 指数代码列表
            tolerance: 相似度容差
            periods: 分析周期
            use_phase2: 是否使用Phase 2技术指标增强匹配
            use_phase3: 是否使用Phase 3深度分析

        Returns:
            多指数分析结果汇总
        """
        if indices is None:
            indices = DEFAULT_US_INDICES

        # 确定分析阶段标签
        if use_phase3:
            phase_label = "Phase 3(深度分析)"
        elif use_phase2:
            phase_label = "Phase 2(技术指标增强)"
        else:
            phase_label = "Phase 1(价格匹配)"

        logger.info(f"开始多指数联合分析 [{phase_label}]: {', '.join([US_INDICES[i].name for i in indices])}")

        result = {
            'timestamp': datetime.now(),
            'indices_analyzed': indices,
            'analysis_phase': phase_label,
            'individual_analysis': {}
        }

        # 分析每个指数
        for index_code in indices:
            if index_code not in US_INDICES:
                logger.warning(f"跳过不支持的指数: {index_code}")
                continue

            analysis = self.analyze_single_index(index_code, tolerance, periods, use_phase2, use_phase3)
            result['individual_analysis'][index_code] = analysis

        # 综合评估
        result['summary'] = self._generate_summary(result['individual_analysis'])

        logger.info(f"多指数联合分析完成 [{phase_label}]")
        return result

    def _generate_summary(self, individual_results: Dict) -> Dict:
        """
        生成综合评估摘要

        Args:
            individual_results: 各指数的分析结果

        Returns:
            综合评估摘要
        """
        summary = {
            'total_indices': len(individual_results),
            'successful_analyses': 0,
            'average_confidence': 0.0,
            'bullish_indices': [],
            'bearish_indices': [],
            'neutral_indices': []
        }

        confidences = []
        for index_code, analysis in individual_results.items():
            if 'error' in analysis or 'warning' in analysis:
                continue

            summary['successful_analyses'] += 1

            # 获取20日周期的分析结果
            if 'period_analysis' in analysis and '20d' in analysis['period_analysis']:
                stats_20d = analysis['period_analysis']['20d']

                if 'confidence' in stats_20d:
                    confidences.append(stats_20d['confidence'])

                # 分类指数
                up_prob = stats_20d.get('up_prob', 0.5)
                if up_prob >= 0.6:
                    summary['bullish_indices'].append(US_INDICES[index_code].name)
                elif up_prob <= 0.4:
                    summary['bearish_indices'].append(US_INDICES[index_code].name)
                else:
                    summary['neutral_indices'].append(US_INDICES[index_code].name)

        if confidences:
            summary['average_confidence'] = float(np.mean(confidences))

        return summary


def test_us_market_analyzer():
    """测试美股市场分析器"""
    print("=" * 80)
    print("美股市场分析器测试")
    print("=" * 80)

    analyzer = USMarketAnalyzer()

    # 测试1: 获取当前点位
    print("\n1. 测试获取当前点位")
    positions = analyzer.get_current_positions()
    for code, info in positions.items():
        print(f"   {info['name']}: {info['price']:.2f} ({info['change_pct']:+.2f}%)")

    # 测试2: 单指数分析
    print("\n2. 测试单指数分析 (标普500)")
    result = analyzer.analyze_single_index('SPX', tolerance=0.05)

    if 'error' not in result:
        print(f"   当前点位: {result['current_price']:.2f}")
        print(f"   相似时期: {result.get('similar_periods_count', 0)} 个")

        if 'period_analysis' in result and '20d' in result['period_analysis']:
            stats = result['period_analysis']['20d']
            print(f"   20日后上涨概率: {stats['up_prob']:.1%}")
            print(f"   平均收益率: {stats['mean_return']:.2%}")
            print(f"   置信度: {stats.get('confidence', 0):.1%}")

            if 'position_advice' in stats:
                advice = stats['position_advice']
                print(f"   建议仓位: {advice['recommended_position']:.1%}")
                print(f"   操作信号: {advice['signal']}")
    else:
        print(f"   分析失败: {result['error']}")

    # 测试3: 多指数联合分析
    print("\n3. 测试多指数联合分析")
    multi_result = analyzer.analyze_multiple_indices(
        indices=['SPX', 'NASDAQ', 'NDX', 'VIX'],
        tolerance=0.05
    )

    if 'summary' in multi_result:
        summary = multi_result['summary']
        print(f"   成功分析: {summary['successful_analyses']}/{summary['total_indices']} 个指数")
        print(f"   平均置信度: {summary['average_confidence']:.1%}")
        print(f"   看涨指数: {', '.join(summary['bullish_indices']) if summary['bullish_indices'] else '无'}")
        print(f"   看跌指数: {', '.join(summary['bearish_indices']) if summary['bearish_indices'] else '无'}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_us_market_analyzer()
