#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史点位对比分析器 - Phase 1 基础版本
功能：
1. 单/多指数历史点位查找
2. 概率统计分析
3. 仓位建议计算
"""

import pandas as pd
import numpy as np
import akshare as ak
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IndexConfig:
    """指数配置"""
    code: str
    name: str
    symbol: str  # akshare 的 symbol


# 支持的指数配置
SUPPORTED_INDICES = {
    'sh000001': IndexConfig('sh000001', '上证指数', 'sh000001'),
    'sh000300': IndexConfig('sh000300', '沪深300', 'sh000300'),
    'sz399006': IndexConfig('sz399006', '创业板指', 'sz399006'),
    'sh000688': IndexConfig('sh000688', '科创50', 'sh000688'),
    'sz399001': IndexConfig('sz399001', '深证成指', 'sz399001'),
}


class DataCache:
    """数据缓存管理"""

    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> Optional[pd.DataFrame]:
        if key in self._cache:
            logger.debug(f"从缓存获取数据: {key}")
            return self._cache[key].copy()
        return None

    def set(self, key: str, data: pd.DataFrame):
        self._cache[key] = data.copy()
        logger.debug(f"缓存数据: {key}, 大小: {len(data)}")

    def clear(self):
        self._cache.clear()
        logger.info("缓存已清空")


class HistoricalPositionAnalyzer:
    """历史点位对比分析器"""

    def __init__(self, cache_enabled: bool = True):
        self.cache = DataCache() if cache_enabled else None
        self.data = {}  # 存储各指数的历史数据
        logger.info("历史点位分析器初始化完成")

    def get_index_data(self, index_code: str) -> pd.DataFrame:
        """获取指数历史数据"""
        # 检查缓存
        if self.cache:
            cached = self.cache.get(index_code)
            if cached is not None:
                return cached

        # 从 akshare 获取数据
        try:
            logger.info(f"正在获取 {index_code} 历史数据...")
            df = ak.stock_zh_index_daily(symbol=index_code)

            # 数据处理
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            # 计算收益率
            df['return'] = df['close'].pct_change()

            # 缓存
            if self.cache:
                self.cache.set(index_code, df)

            logger.info(f"{index_code} 数据获取成功，共 {len(df)} 条")
            return df

        except Exception as e:
            logger.error(f"获取 {index_code} 数据失败: {str(e)}")
            raise

    def get_current_positions(self) -> Dict[str, float]:
        """获取当前各指数点位"""
        positions = {}

        for code, config in SUPPORTED_INDICES.items():
            try:
                df = self.get_index_data(code)
                current_price = df['close'].iloc[-1]
                positions[code] = {
                    'name': config.name,
                    'price': current_price,
                    'date': df.index[-1].strftime('%Y-%m-%d')
                }
                logger.info(f"{config.name}: {current_price:.2f}")
            except Exception as e:
                logger.warning(f"获取 {config.name} 当前点位失败: {str(e)}")
                continue

        return positions

    def find_similar_periods(
        self,
        index_code: str,
        current_price: float = None,
        tolerance: float = 0.05,
        min_gap_days: int = 5
    ) -> pd.DataFrame:
        """
        查找历史相似点位时期

        Args:
            index_code: 指数代码
            current_price: 当前价格（如不提供则使用最新价格）
            tolerance: 相似度容差（默认±5%）
            min_gap_days: 相似时期最小间隔天数（避免重复计数）

        Returns:
            包含相似时期的DataFrame
        """
        df = self.get_index_data(index_code)

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

        # 过滤：排除最近的数据点（避免用当前预测当前）
        cutoff_date = df.index[-1] - timedelta(days=min_gap_days)
        similar = similar[similar.index <= cutoff_date]

        logger.info(
            f"{SUPPORTED_INDICES[index_code].name} "
            f"在 {lower_bound:.2f}-{upper_bound:.2f} 区间"
            f"共找到 {len(similar)} 个相似点位"
        )

        return similar

    def find_similar_periods_enhanced(
        self,
        index_code: str,
        current_price: float = None,
        current_volume: float = None,
        price_tolerance: float = 0.05,
        volume_tolerance: float = 0.3,
        use_volume_filter: bool = True,
        min_gap_days: int = 5
    ) -> pd.DataFrame:
        """
        增强版相似点位查找（价格+成交量双重匹配）

        Args:
            index_code: 指数代码
            current_price: 当前价格
            current_volume: 当前成交量
            price_tolerance: 价格容差
            volume_tolerance: 成交量容差（相对于均量的偏差）
            use_volume_filter: 是否启用成交量过滤
            min_gap_days: 最小间隔天数

        Returns:
            增强匹配的相似时期DataFrame
        """
        df = self.get_index_data(index_code)

        if current_price is None:
            current_price = df['close'].iloc[-1]
        if current_volume is None:
            current_volume = df['volume'].iloc[-1]

        # 价格相似区间
        price_lower = current_price * (1 - price_tolerance)
        price_upper = current_price * (1 + price_tolerance)

        # 基础价格过滤
        similar = df[
            (df['close'] >= price_lower) &
            (df['close'] <= price_upper)
        ].copy()

        # 成交量增强过滤
        if use_volume_filter and len(similar) > 0:
            # 计算移动平均量
            df['volume_ma20'] = df['volume'].rolling(20).mean()

            # 当前相对量比
            current_volume_ratio = current_volume / df['volume_ma20'].iloc[-1] if df['volume_ma20'].iloc[-1] > 0 else 1.0

            # 筛选成交量相似的时期
            similar = similar[similar.index.isin(df.index)].copy()
            similar['volume_ma20'] = df.loc[similar.index, 'volume_ma20']
            similar['volume_ratio'] = similar['volume'] / similar['volume_ma20']

            # 成交量相似：量比在当前量比的 ±volume_tolerance 范围内
            volume_ratio_lower = current_volume_ratio * (1 - volume_tolerance)
            volume_ratio_upper = current_volume_ratio * (1 + volume_tolerance)

            similar = similar[
                (similar['volume_ratio'] >= volume_ratio_lower) &
                (similar['volume_ratio'] <= volume_ratio_upper)
            ]

            logger.info(
                f"  [增强匹配] 当前量比: {current_volume_ratio:.2f}, "
                f"筛选后剩余: {len(similar)} 个时期"
            )

        # 过滤最近数据
        cutoff_date = df.index[-1] - timedelta(days=min_gap_days)
        similar = similar[similar.index <= cutoff_date]

        logger.info(
            f"{SUPPORTED_INDICES[index_code].name} 增强匹配 "
            f"(价格±{price_tolerance:.0%}, 量比±{volume_tolerance:.0%}): "
            f"共 {len(similar)} 个时期"
        )

        return similar

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
            periods: 要计算的未来周期（天数）

        Returns:
            包含未来收益率的DataFrame
        """
        df = self.get_index_data(index_code)
        results = []

        for date in similar_periods.index:
            row = {'date': date, 'price': similar_periods.loc[date, 'close']}

            for period in periods:
                future_date = date + timedelta(days=period * 1.5)  # 考虑周末

                # 查找最接近的交易日
                future_data = df[df.index > date]
                if len(future_data) >= period:
                    future_price = future_data['close'].iloc[min(period-1, len(future_data)-1)]
                    current_price = similar_periods.loc[date, 'close']
                    ret = (future_price - current_price) / current_price
                    row[f'return_{period}d'] = ret
                else:
                    row[f'return_{period}d'] = np.nan

            results.append(row)

        return pd.DataFrame(results)

    def find_multi_index_match(
        self,
        positions: Dict[str, Dict],
        tolerance: float = 0.05,
        min_match_count: int = 3
    ) -> pd.DataFrame:
        """
        多指数联合匹配

        Args:
            positions: 各指数当前点位字典
            tolerance: 相似度容差
            min_match_count: 最少匹配指数数量

        Returns:
            多指数同时匹配的时期
        """
        logger.info(f"开始多指数联合匹配（需匹配至少 {min_match_count} 个指数）...")

        # 存储每个指数的相似时期
        similar_periods_by_index = {}

        for index_code, pos_info in positions.items():
            similar = self.find_similar_periods(
                index_code,
                pos_info['price'],
                tolerance
            )
            similar_periods_by_index[index_code] = set(similar.index)

        # 找出所有日期的交集
        all_dates = set()
        for dates in similar_periods_by_index.values():
            all_dates.update(dates)

        # 统计每个日期匹配了几个指数
        match_results = []
        for date in sorted(all_dates):
            matched_indices = [
                code for code, dates in similar_periods_by_index.items()
                if date in dates
            ]

            if len(matched_indices) >= min_match_count:
                match_results.append({
                    'date': date,
                    'match_count': len(matched_indices),
                    'matched_indices': ','.join(matched_indices)
                })

        result_df = pd.DataFrame(match_results)

        if len(result_df) > 0:
            logger.info(f"找到 {len(result_df)} 个多指数匹配时期")
        else:
            logger.warning("未找到满足条件的多指数匹配时期")

        return result_df


class ProbabilityAnalyzer:
    """概率统计分析器"""

    @staticmethod
    def calculate_probability(returns: pd.Series) -> Dict:
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
            'up_prob': up_count / total if total > 0 else 0,
            'down_prob': down_count / total if total > 0 else 0,
            'up_count': int(up_count),
            'down_count': int(down_count),
            'mean_return': valid_returns.mean(),
            'median_return': valid_returns.median(),
            'max_return': valid_returns.max(),
            'min_return': valid_returns.min(),
            'std': valid_returns.std(),
            'percentile_25': valid_returns.quantile(0.25),
            'percentile_75': valid_returns.quantile(0.75),
        }

    @staticmethod
    def calculate_confidence(
        sample_size: int,
        consistency: float,
        time_diversity: float = 1.0
    ) -> float:
        """
        计算置信度

        Args:
            sample_size: 样本数量
            consistency: 结果一致性 (上涨概率或下跌概率的最大值)
            time_diversity: 时间分散度 (0-1, 1表示分散在不同年份)

        Returns:
            置信度分数 (0-1)
        """
        # 样本量得分 (sigmoid函数)
        size_score = 1 / (1 + np.exp(-(sample_size - 20) / 10))

        # 一致性得分 (线性映射 0.5-1.0 -> 0-1)
        consistency_score = max(0, (consistency - 0.5) / 0.5)

        # 综合得分
        confidence = (
            0.5 * size_score +
            0.3 * consistency_score +
            0.2 * time_diversity
        )

        return min(1.0, max(0.0, confidence))

    @staticmethod
    def classify_market_environment(period_data: pd.DataFrame) -> str:
        """
        市场环境分类

        Args:
            period_data: 包含价格和成交量的时期数据

        Returns:
            市场环境类型
        """
        # 简化版本：基于前期走势判断
        if len(period_data) < 20:
            return "数据不足"

        recent_20d = period_data['close'].iloc[-20:]
        returns_20d = recent_20d.pct_change().dropna()

        avg_return = returns_20d.mean()
        volatility = returns_20d.std()

        # 分类逻辑
        if avg_return > 0.01:  # 平均日涨幅 > 1%
            return "牛市中期"
        elif avg_return > 0.005:
            return "牛市末期"
        elif avg_return < -0.01:
            return "熊市中期"
        else:
            return "震荡市"


class PositionManager:
    """仓位管理器"""

    @staticmethod
    def calculate_position_advice(
        up_prob: float,
        confidence: float,
        mean_return: float,
        std: float
    ) -> Dict:
        """
        计算仓位建议

        Args:
            up_prob: 上涨概率
            confidence: 置信度
            mean_return: 平均收益率
            std: 收益率标准差

        Returns:
            仓位建议字典
        """
        # 基础仓位（基于概率）
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

        # Kelly公式调整（如果有正期望）
        if mean_return > 0 and std > 0:
            # 简化Kelly: f = mean / variance
            kelly = mean_return / (std ** 2) if std > 0 else 0
            kelly = max(0, min(1, kelly * 0.5))  # 半凯利，限制在0-1

            # 混合基础仓位和Kelly仓位
            final_position = 0.7 * base_position + 0.3 * kelly
        else:
            final_position = base_position

        final_position = max(0.1, min(0.9, final_position))  # 限制在10%-90%

        return {
            'signal': signal,
            'recommended_position': final_position,
            'base_position': base_position,
            'description': PositionManager._get_position_description(final_position, signal)
        }

    @staticmethod
    def calculate_stop_loss_take_profit(
        current_price: float,
        max_loss_percentile: float,
        avg_gain_percentile: float
    ) -> Dict:
        """
        计算止损止盈位

        Args:
            current_price: 当前价格
            max_loss_percentile: 历史最大亏损分位数（如95%分位数）
            avg_gain_percentile: 历史平均盈利分位数（如75%分位数）

        Returns:
            止损止盈建议
        """
        stop_loss = current_price * (1 + max_loss_percentile)  # max_loss是负数
        take_profit = current_price * (1 + avg_gain_percentile)

        return {
            'stop_loss_price': stop_loss,
            'stop_loss_pct': max_loss_percentile,
            'take_profit_price': take_profit,
            'take_profit_pct': avg_gain_percentile,
            'risk_reward_ratio': abs(avg_gain_percentile / max_loss_percentile) if max_loss_percentile != 0 else 0
        }

    @staticmethod
    def _get_position_description(position: float, signal: str) -> str:
        """获取仓位描述"""
        if position >= 0.8:
            return f"{signal}：建议重仓配置（{position*100:.0f}%左右）"
        elif position >= 0.6:
            return f"{signal}：建议标准配置（{position*100:.0f}%左右）"
        elif position >= 0.4:
            return f"{signal}：建议轻仓观望（{position*100:.0f}%左右）"
        else:
            return f"{signal}：建议低仓防守（{position*100:.0f}%左右）"


if __name__ == '__main__':
    # 简单测试
    analyzer = HistoricalPositionAnalyzer()

    # 测试单指数
    print("=== 测试单指数分析 ===")
    positions = analyzer.get_current_positions()

    if 'sh000001' in positions:
        similar = analyzer.find_similar_periods('sh000001')
        print(f"\n上证指数相似点位数量: {len(similar)}")

        if len(similar) > 0:
            future_returns = analyzer.calculate_future_returns('sh000001', similar)
            print(f"\n未来收益率样本数: {len(future_returns)}")

            # 测试概率分析
            prob_analyzer = ProbabilityAnalyzer()
            stats_20d = prob_analyzer.calculate_probability(future_returns['return_20d'])
            print(f"\n20日后上涨概率: {stats_20d['up_prob']:.2%}")
            print(f"平均收益率: {stats_20d['mean_return']:.2%}")
