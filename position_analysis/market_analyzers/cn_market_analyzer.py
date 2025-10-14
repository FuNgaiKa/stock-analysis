#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股市场分析器
支持上证指数、深证成指、创业板指等A股指数的点位分析
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Phase 3.2: 导入专业分析器
from ..analyzers.market_specific.turnover_analyzer import TurnoverAnalyzer
from ..analyzers.market_specific.ah_premium_analyzer import AHPremiumAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class CNIndexConfig:
    """A股指数配置"""
    code: str
    name: str
    symbol: str  # yfinance symbol


# 支持的A股指数
CN_INDICES = {
    'SSE': CNIndexConfig('SSE', '上证指数', '000001'),
    'SZSE': CNIndexConfig('SZSE', '深证成指', '399001'),
    'CYBZ': CNIndexConfig('CYBZ', '创业板指', '399006'),
    'HS300': CNIndexConfig('HS300', '沪深300', '000300'),
    'ZZ500': CNIndexConfig('ZZ500', '中证500', '000905'),
    'KECHUANG50': CNIndexConfig('KECHUANG50', '科创50', '000688'),
}

# 默认分析的指数
DEFAULT_CN_INDICES = ['SSE', 'SZSE', 'CYBZ']


class CNMarketAnalyzer:
    """A股市场分析器"""

    def __init__(self):
        """初始化A股市场分析器"""
        try:
            # 导入Ashare数据源(腾讯+新浪双核心)
            from data_sources.Ashare import get_price
            self.get_price = get_price
            logger.info("使用Ashare数据源(腾讯+新浪双核心)")
        except:
            logger.error("无法导入Ashare数据源")
            self.get_price = None

        self.data_cache = {}

        # Phase 3.2: 初始化机构级专业分析器
        self.turnover_analyzer = TurnoverAnalyzer()
        self.ah_premium_analyzer = AHPremiumAnalyzer()

        logger.info("A股市场分析器初始化完成(含换手率/AH溢价)")

    def get_index_data(self, index_code: str, period: str = "5y") -> pd.DataFrame:
        """获取A股指数历史数据"""
        cache_key = f"CN_{index_code}_{period}"
        if cache_key in self.data_cache:
            logger.info(f"使用缓存的{index_code}数据")
            return self.data_cache[cache_key]

        if index_code not in CN_INDICES:
            logger.error(f"不支持的A股指数: {index_code}")
            return pd.DataFrame()

        if not self.get_price:
            logger.error("Ashare数据源未初始化")
            return pd.DataFrame()

        config = CN_INDICES[index_code]

        try:
            # 计算需要获取的数据条数
            if period == "5y":
                count = 5 * 250  # 5年交易日
            elif period == "10y":
                count = 10 * 250  # 10年交易日
            elif period == "5d":
                count = 10  # 5个交易日(多取几天防止节假日)
            else:
                count = 5 * 250  # 默认5年

            # 使用Ashare获取指数数据
            # sh + 代码 对应上海交易所指数, sz + 代码 对应深圳交易所指数
            code_prefix = 'sh' if config.symbol.startswith('000') else 'sz'
            full_code = code_prefix + config.symbol

            df = self.get_price(full_code, count=count, frequency='1d')

            if df.empty:
                logger.warning(f"{config.name}数据为空")
                return pd.DataFrame()

            # 数据已经是标准格式,只需添加return列
            df['return'] = df['close'].pct_change()
            self.data_cache[cache_key] = df

            logger.info(f"{config.name}数据获取成功: {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取{config.name}数据失败: {str(e)}")
            return pd.DataFrame()

    def get_current_positions(self, indices: List[str] = None) -> Dict[str, Dict]:
        """获取当前各指数点位"""
        if indices is None:
            indices = DEFAULT_CN_INDICES

        positions = {}

        for code in indices:
            if code not in CN_INDICES:
                logger.warning(f"不支持的A股指数代码: {code}")
                continue

            try:
                config = CN_INDICES[code]
                df = self.get_index_data(code, period="5d")

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
        """查找历史相似点位时期"""
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

        # 过滤: 排除最近的数据点
        cutoff_date = df.index[-1] - timedelta(days=min_gap_days)
        similar = similar[similar.index <= cutoff_date]

        logger.info(
            f"{CN_INDICES[index_code].name} "
            f"在 {lower_bound:.2f}-{upper_bound:.2f} 区间 "
            f"共找到 {len(similar)} 个相似点位"
        )

        return similar

    def calculate_future_returns(
        self,
        index_code: str,
        similar_periods: pd.DataFrame,
        periods: List[int] = [5, 10, 20, 30, 60]
    ) -> pd.DataFrame:
        """计算相似时期的后续收益率"""
        df = self.get_index_data(index_code, period="10y")

        if df.empty:
            return pd.DataFrame()

        results = []

        for date in similar_periods.index:
            row = {
                'date': date,
                'price': similar_periods.loc[date, 'close']
            }

            for period in periods:
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

    def calculate_max_drawdown(self, index_code: str, similar_periods: pd.DataFrame, period: int = 20) -> Dict:
        """计算相似时期的最大回撤统计"""
        df = self.get_index_data(index_code, period="10y")

        if df.empty:
            return {'max_dd': 0.0, 'avg_dd': 0.0, 'dd_prob': 0.0}

        drawdowns = []

        for date in similar_periods.index:
            future_data = df[df.index > date]

            if len(future_data) >= period:
                # 获取未来N天的价格序列
                prices = future_data['close'].iloc[:period]
                current_price = similar_periods.loc[date, 'close']

                # 计算相对于买入点的累计最大回撤
                cummax = prices.expanding().max()
                dd = ((prices - cummax) / current_price).min()
                drawdowns.append(dd)

        if len(drawdowns) == 0:
            return {'max_dd': 0.0, 'avg_dd': 0.0, 'dd_prob': 0.0}

        drawdowns = pd.Series(drawdowns)

        return {
            'max_dd': float(drawdowns.min()),  # 最大回撤(负值)
            'avg_dd': float(drawdowns.mean()),  # 平均回撤
            'dd_prob': float((drawdowns < -0.05).sum() / len(drawdowns)),  # 回撤超过5%的概率
            'dd_std': float(drawdowns.std())  # 回撤标准差
        }

    def calculate_probability_statistics(self, returns: pd.Series) -> Dict:
        """计算涨跌概率及统计指标"""
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

        # 计算胜率和盈亏比
        winning_returns = valid_returns[valid_returns > 0]
        losing_returns = valid_returns[valid_returns < 0]

        win_rate = float(len(winning_returns) / total if total > 0 else 0)
        avg_win = float(winning_returns.mean() if len(winning_returns) > 0 else 0)
        avg_loss = float(losing_returns.mean() if len(losing_returns) > 0 else 0)
        profit_loss_ratio = float(abs(avg_win / avg_loss) if avg_loss != 0 else 0)

        # 量化机构专业指标
        mean_return = float(valid_returns.mean())
        std_return = float(valid_returns.std())

        # 1. 夏普比率 (Sharpe Ratio) - 假设无风险利率3%
        risk_free_rate = 0.03 / 252  # 日度无风险利率
        sharpe_ratio = float((mean_return - risk_free_rate) / std_return if std_return > 0 else 0)

        # 2. 索提诺比率 (Sortino Ratio) - 只考虑下行波动
        downside_returns = valid_returns[valid_returns < 0]
        downside_std = float(downside_returns.std() if len(downside_returns) > 0 else std_return)
        sortino_ratio = float((mean_return - risk_free_rate) / downside_std if downside_std > 0 else 0)

        # 3. 卡玛比率 (Calmar Ratio) - 需要与最大回撤配合使用,这里先预留
        # 实际计算在有最大回撤数据后进行

        # 4. 偏度 (Skewness) - 收益分布的对称性
        skewness = float(valid_returns.skew())

        # 5. 峰度 (Kurtosis) - 收益分布的尾部厚度
        kurtosis = float(valid_returns.kurtosis())

        # 6. VaR (Value at Risk) 95%置信度
        var_95 = float(valid_returns.quantile(0.05))  # 5%分位数

        # 7. CVaR (Conditional VaR) 超出VaR的平均损失
        cvar_95 = float(valid_returns[valid_returns <= var_95].mean() if (valid_returns <= var_95).any() else var_95)

        return {
            'sample_size': total,
            'up_prob': float(up_count / total if total > 0 else 0),
            'down_prob': float(down_count / total if total > 0 else 0),
            'up_count': int(up_count),
            'down_count': int(down_count),
            'mean_return': mean_return,
            'median_return': float(valid_returns.median()),
            'max_return': float(valid_returns.max()),
            'min_return': float(valid_returns.min()),
            'std': std_return,
            'percentile_25': float(valid_returns.quantile(0.25)),
            'percentile_75': float(valid_returns.quantile(0.75)),
            # 基础新增指标
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_loss_ratio': profit_loss_ratio,
            'volatility': float(std_return * np.sqrt(252)),  # 年化波动率
            # 量化机构专业指标
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'var_95': var_95,
            'cvar_95': cvar_95,
        }

    def calculate_confidence(self, sample_size: int, consistency: float) -> float:
        """计算置信度"""
        size_score = 1 / (1 + np.exp(-(sample_size - 20) / 10))
        consistency_score = max(0, (consistency - 0.5) / 0.5)
        confidence = 0.6 * size_score + 0.4 * consistency_score
        return min(1.0, max(0.0, confidence))

    def calculate_position_advice(
        self,
        up_prob: float,
        confidence: float,
        mean_return: float,
        std: float
    ) -> Dict:
        """计算仓位建议"""
        # 基础仓位
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

        # Kelly公式调整
        if mean_return > 0 and std > 0:
            kelly = mean_return / (std ** 2) if std > 0 else 0
            kelly = max(0, min(1, kelly * 0.5))
            final_position = 0.7 * base_position + 0.3 * kelly
        else:
            final_position = base_position

        final_position = max(0.1, min(0.9, final_position))

        return {
            'signal': signal,
            'recommended_position': float(final_position),
            'base_position': float(base_position),
            'description': self._get_position_description(final_position, signal)
        }

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
        periods: List[int] = [5, 10, 20, 30, 60]
    ) -> Dict:
        """单指数完整分析"""
        logger.info(f"开始分析A股 {CN_INDICES[index_code].name}...")

        result = {
            'index_code': index_code,
            'index_name': CN_INDICES[index_code].name,
            'timestamp': datetime.now(),
            'market': 'CN'
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

            # 2. 查找相似时期
            similar = self.find_similar_periods(index_code, tolerance=tolerance)

            if similar.empty:
                result['warning'] = '未找到相似历史点位'
                return result

            result['similar_periods_count'] = len(similar)

            # 3. 计算未来收益率
            future_returns = self.calculate_future_returns(index_code, similar, periods)

            # 4. 对每个周期计算概率统计
            result['period_analysis'] = {}

            for period in periods:
                col = f'return_{period}d'
                if col in future_returns.columns:
                    stats = self.calculate_probability_statistics(future_returns[col])

                    # 计算置信度
                    consistency = max(stats['up_prob'], stats['down_prob'])
                    confidence = self.calculate_confidence(stats['sample_size'], consistency)
                    stats['confidence'] = confidence

                    # 计算最大回撤
                    drawdown_stats = self.calculate_max_drawdown(index_code, similar, period)
                    stats.update(drawdown_stats)

                    # 计算卡玛比率 (Calmar Ratio) = 年化收益率 / |最大回撤|
                    if drawdown_stats.get('max_dd', 0) < 0:
                        annualized_return = stats['mean_return'] * (252 / period)  # 年化收益
                        calmar_ratio = float(annualized_return / abs(drawdown_stats['max_dd']))
                        stats['calmar_ratio'] = calmar_ratio
                    else:
                        stats['calmar_ratio'] = 0.0

                    # 计算仓位建议
                    if stats['sample_size'] > 0:
                        position_advice = self.calculate_position_advice(
                            stats['up_prob'],
                            confidence,
                            stats['mean_return'],
                            stats['std']
                        )
                        stats['position_advice'] = position_advice

                    result['period_analysis'][f'{period}d'] = stats

            # Phase 3.2: 深度分析 - 机构级专业指标
            result['phase3_analysis'] = {}

            # 1. 换手率分析
            try:
                turnover_result = self.turnover_analyzer.analyze_turnover(
                    index_symbol=CN_INDICES[index_code].symbol,
                    period=60  # 60天历史数据
                )
                if 'error' not in turnover_result:
                    result['phase3_analysis']['turnover'] = turnover_result
                    logger.info("换手率分析完成")
            except Exception as e:
                logger.warning(f"换手率分析失败: {str(e)}")

            # 2. AH溢价分析(对所有A股指数都适用,反映市场整体情绪)
            try:
                ah_premium_result = self.ah_premium_analyzer.analyze_ah_premium()
                if 'error' not in ah_premium_result:
                    result['phase3_analysis']['ah_premium'] = ah_premium_result
                    logger.info("AH溢价分析完成")
            except Exception as e:
                logger.warning(f"AH溢价分析失败: {str(e)}")

            logger.info(f"{CN_INDICES[index_code].name} 分析完成(含深度分析)")

        except Exception as e:
            logger.error(f"分析{index_code}失败: {str(e)}")
            result['error'] = str(e)

        return result


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    analyzer = CNMarketAnalyzer()

    print("\n=== A股市场分析器测试 ===")

    # 测试完整分析
    result = analyzer.analyze_single_index('HS300', tolerance=0.05)

    if 'error' not in result:
        print(f"\n{result['index_name']}:")
        print(f"当前点位: {result['current_price']:.2f}")
        print(f"相似时期: {result.get('similar_periods_count', 0)} 个")

        if 'period_analysis' in result and '20d' in result['period_analysis']:
            stats = result['period_analysis']['20d']
            print(f"20日后上涨概率: {stats['up_prob']:.1%}")
            print(f"平均收益率: {stats['mean_return']:.2%}")
            print(f"置信度: {stats.get('confidence', 0):.1%}")

            if 'position_advice' in stats:
                advice = stats['position_advice']
                print(f"建议仓位: {advice['recommended_position']:.1%}")
                print(f"操作信号: {advice['signal']}")
    else:
        print(f"分析失败: {result.get('error', '未知错误')}")
