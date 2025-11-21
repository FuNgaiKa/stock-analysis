#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用板块综合分析报告生成器
Sector Comprehensive Reporter

分析对象: 可配置的任意板块(创新药、电池、半导体等)
分析维度(11大维度):
  1. 历史点位分析 - 相似点位涨跌概率
  2. 技术面分析 - MACD/RSI/KDJ/布林带/ATR/DMI/均线/背离
  3. 资金面分析 - 北向/南向资金流向
  4. 估值分析 - PE/PB历史分位数
  5. 市场情绪 - 板块热度/涨跌家数
  6. 风险评估 - 综合风险评分
  7. 综合判断 - 方向/仓位/策略建议
  8. 成交量分析 - OBV/量比/量价关系
  9. 支撑压力位 - 轴心点/斐波那契
  10. 市场宽度 - 板块内部强度
  11. 行业景气度 - 特定行业指标(待扩展)

作者: Claude Code
日期: 2025-10-16
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
import pandas as pd
import numpy as np

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.analysis.sector_analysis.sector_config import get_sector_config, list_all_sectors
from scripts.analysis.sector_analysis.data_source_manager import DataSourceManager
from strategies.position.market_analyzers.cn_market_analyzer import CNMarketAnalyzer
from strategies.position.analyzers.technical_analysis.divergence_analyzer import DivergenceAnalyzer
from strategies.position.analyzers.market_specific.cn_stock_indicators import CNStockIndicators
from strategies.position.analyzers.market_specific.hk_connect_analyzer import HKConnectAnalyzer
from strategies.position.analyzers.technical_analysis.volume_analyzer import VolumeAnalyzer
from strategies.position.analyzers.technical_analysis.support_resistance import SupportResistanceAnalyzer
from strategies.position.analyzers.market_structure.market_breadth_analyzer import MarketBreadthAnalyzer
from strategies.position.analyzers.valuation.index_valuation_analyzer import IndexValuationAnalyzer
from russ_trading.analyzers.volume_price_analyzer import VolumePriceAnalyzer

# 导入因子合成模块
from russ_trading.core.factor_synthesis import FactorSynthesizer, DEFAULT_FACTOR_PRIORITY

logger = logging.getLogger(__name__)


class SectorReporter:
    """通用板块综合分析报告生成器"""

    def __init__(self):
        """初始化分析器"""
        logger.info("初始化板块分析系统...")

        # 多数据源管理器 (替代原有的单一Ashare数据源)
        self.data_source_manager = DataSourceManager()
        logger.info(f"数据源管理器初始化完成: {self.data_source_manager.get_source_status()}")

        # 市场分析器
        self.cn_analyzer = CNMarketAnalyzer()

        # 技术分析器
        self.divergence_analyzer = DivergenceAnalyzer()
        self.volume_analyzer = VolumeAnalyzer()
        self.vp_analyzer = VolumePriceAnalyzer()

        # A股专项分析器
        self.cn_indicators = CNStockIndicators()
        self.hk_connect = HKConnectAnalyzer()

        # 估值分析器
        self.valuation_analyzer = IndexValuationAnalyzer()

        # 市场宽度分析器(仅A股)
        self.market_breadth_analyzer = MarketBreadthAnalyzer()

        # 因子合成器 (用于多因子评分)
        self.factor_synthesizer = FactorSynthesizer()

        logger.info("板块分析系统初始化完成")

    def analyze_single_sector(self, sector_key: str) -> Dict:
        """
        综合分析单个板块

        Args:
            sector_key: 板块代码(如 'HK_BIOTECH', 'HK_BATTERY')

        Returns:
            完整分析结果
        """
        config = get_sector_config(sector_key)
        logger.info(f"开始分析 {config['name']}...")

        result = {
            'sector_key': sector_key,
            'sector_name': config['name'],
            'market': config['market'],
            'category': config['category'],
            'symbols': config['symbols'],
            'timestamp': datetime.now()
        }

        try:
            # 获取板块数据(目前仅支持单个ETF，后续可扩展为多个股票组合)
            primary_symbol = config['symbols'][0]
            prefer_source = config.get('data_source', None)  # None表示自动选择，或指定'yfinance'等

            # 1. 历史点位分析
            result['historical_analysis'] = self._analyze_historical_position(
                config['market'], primary_symbol, prefer_source
            )

            # 2. 技术面分析
            result['technical_analysis'] = self._analyze_technical(
                config['market'], primary_symbol, prefer_source
            )

            # 3. 资金面分析(A股)
            if config['market'] == 'CN':
                result['capital_flow'] = self._analyze_capital_flow(
                    config['market'], primary_symbol
                )

            # 4. 估值分析
            result['valuation'] = self._analyze_valuation(
                config['market'], primary_symbol
            )

            # 5. 市场情绪(A股) - 暂时禁用
            # if config['market'] == 'CN':
            #     result['market_sentiment'] = self._analyze_sentiment()

            # 6. 风险评估
            result['risk_assessment'] = self._calculate_risk_score(result)

            # 7. 综合判断(基于多因子评分)
            result['comprehensive_judgment'] = self._generate_judgment(result, config)

            # 8. 成交量分析
            result['volume_analysis'] = self._analyze_volume(
                config['market'], primary_symbol, prefer_source
            )

            # 9. 支撑压力位
            result['support_resistance'] = self._analyze_support_resistance(
                config['market'], primary_symbol, prefer_source
            )

            # 10. 市场宽度(仅A股)
            if config['market'] == 'CN':
                result['market_breadth'] = self._analyze_market_breadth()

            # 11. 行业景气度 - 待扩展
            result['industry_prosperity'] = {
                'available': False,
                'note': '行业特色指标需外部数据源，待后续集成'
            }

            logger.info(f"{config['name']} 分析完成")

        except Exception as e:
            logger.error(f"分析{config['name']}失败: {str(e)}", exc_info=True)
            result['error'] = str(e)

        return result

    def get_etf_data(self, symbol: str, period: str = "5y", market: str = "CN", prefer_source: str = None) -> pd.DataFrame:
        """获取ETF/个股历史数据 (使用多数据源管理器)

        Args:
            symbol: 股票代码
            period: 时间周期 (5y/10y/1y/5d)
            market: 市场类型 (CN/HK/US)
            prefer_source: 优先使用的数据源 (ashare/yfinance/akshare)，None表示自动选择

        Returns:
            DataFrame with columns: open, high, low, close, volume, return
        """
        # 使用数据源管理器获取数据，支持自动故障切换
        df = self.data_source_manager.get_stock_data(
            symbol=symbol,
            period=period,
            market=market,
            prefer_source=prefer_source
        )

        return df

    def _analyze_historical_position(self, market: str, symbol: str, prefer_source: str = None) -> Dict:
        """历史点位分析"""
        try:
            # 获取ETF/个股数据
            df = self.get_etf_data(symbol, period="5y", market=market, prefer_source=prefer_source)
            if df.empty:
                return {'error': '数据获取失败'}

            # 计算当前点位
            current_price = df['close'].iloc[-1]
            current_date = df.index[-1].strftime('%Y-%m-%d')
            current_change_pct = float((current_price - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0.0

            # 查找相似点位
            tolerance = 0.05
            lower_bound = current_price * (1 - tolerance)
            upper_bound = current_price * (1 + tolerance)

            similar = df[
                (df['close'] >= lower_bound) &
                (df['close'] <= upper_bound)
            ].copy()

            # 过滤最近5天
            from datetime import timedelta
            cutoff_date = df.index[-1] - timedelta(days=5)
            similar = similar[similar.index <= cutoff_date]

            if similar.empty:
                logger.warning(f"{symbol}未找到相似点位")
                return {
                    'current_price': float(current_price),
                    'current_date': current_date,
                    'current_change_pct': current_change_pct,
                    'similar_periods_count': 0,
                    'warning': '未找到相似历史点位'
                }

            # 计算未来收益率
            results_20d = []
            results_60d = []

            for date in similar.index:
                future_data = df[df.index > date]

                # 20日收益
                if len(future_data) >= 20:
                    future_price_20d = future_data['close'].iloc[19]
                    ret_20d = (future_price_20d - similar.loc[date, 'close']) / similar.loc[date, 'close']
                    results_20d.append(ret_20d)

                # 60日收益
                if len(future_data) >= 60:
                    future_price_60d = future_data['close'].iloc[59]
                    ret_60d = (future_price_60d - similar.loc[date, 'close']) / similar.loc[date, 'close']
                    results_60d.append(ret_60d)

            # 计算统计指标
            def calc_stats(returns):
                if len(returns) == 0:
                    return {'up_prob': 0, 'down_prob': 0, 'mean_return': 0, 'median_return': 0, 'confidence': 0}

                returns_series = pd.Series(returns)
                up_count = (returns_series > 0).sum()
                total = len(returns_series)

                return {
                    'up_prob': float(up_count / total if total > 0 else 0),
                    'down_prob': float((total - up_count) / total if total > 0 else 0),
                    'mean_return': float(returns_series.mean()),
                    'median_return': float(returns_series.median()),
                    'confidence': float(min(1.0, total / 30))  # 简单置信度
                }

            return {
                'current_price': float(current_price),
                'current_date': current_date,
                'current_change_pct': current_change_pct,
                'similar_periods_count': len(similar),
                '20d': calc_stats(results_20d),
                '60d': calc_stats(results_60d)
            }

        except Exception as e:
            logger.error(f"历史点位分析失败: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def _analyze_technical(self, market: str, symbol: str, prefer_source: str = None) -> Dict:
        """技术面分析"""
        try:
            # 获取ETF/个股数据
            df = self.get_etf_data(symbol, period="5y", market=market, prefer_source=prefer_source)

            if df.empty:
                return {'error': '数据获取失败'}

            # 背离分析
            divergence_result = self.divergence_analyzer.comprehensive_analysis(
                df, symbol=symbol, market=market
            )

            # 提取关键技术指标
            latest = df.iloc[-1]

            # 计算MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()

            # 计算RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # 计算均线
            ma5 = df['close'].rolling(window=5).mean()
            ma20 = df['close'].rolling(window=20).mean()
            ma60 = df['close'].rolling(window=60).mean()

            # 计算KDJ
            low_9 = df['low'].rolling(window=9).min()
            high_9 = df['high'].rolling(window=9).max()
            rsv = (df['close'] - low_9) / (high_9 - low_9) * 100
            kdj_k = rsv.ewm(span=3, adjust=False).mean()
            kdj_d = kdj_k.ewm(span=3, adjust=False).mean()
            kdj_j = 3 * kdj_k - 2 * kdj_d

            # 计算布林带
            boll_mid = df['close'].rolling(window=20).mean()
            boll_std = df['close'].rolling(window=20).std()
            boll_upper = boll_mid + (boll_std * 2)
            boll_lower = boll_mid - (boll_std * 2)
            boll_position = (df['close'] - boll_lower) / (boll_upper - boll_lower)

            # 计算ATR
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift(1))
            low_close = abs(df['low'] - df['close'].shift(1))
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean()

            # 计算DMI/ADX
            high_diff = df['high'].diff()
            low_diff = -df['low'].diff()
            plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
            minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

            plus_dm_smooth = plus_dm.rolling(window=14).mean()
            minus_dm_smooth = minus_dm.rolling(window=14).mean()
            atr_smooth = true_range.rolling(window=14).mean()

            plus_di = 100 * plus_dm_smooth / atr_smooth
            minus_di = 100 * minus_dm_smooth / atr_smooth

            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=14).mean()

            return {
                'macd': {
                    'value': float(macd.iloc[-1]),
                    'signal': float(signal.iloc[-1]),
                    'status': 'golden_cross' if macd.iloc[-1] > signal.iloc[-1] else 'death_cross'
                },
                'rsi': {
                    'value': float(rsi.iloc[-1]),
                    'status': 'overbought' if rsi.iloc[-1] > 70 else ('oversold' if rsi.iloc[-1] < 30 else 'normal')
                },
                'kdj': {
                    'k': float(kdj_k.iloc[-1]),
                    'd': float(kdj_d.iloc[-1]),
                    'j': float(kdj_j.iloc[-1]),
                    'status': 'overbought' if kdj_j.iloc[-1] > 100 else ('oversold' if kdj_j.iloc[-1] < 0 else 'normal'),
                    'signal': 'golden_cross' if kdj_k.iloc[-1] > kdj_d.iloc[-1] else 'death_cross'
                },
                'boll': {
                    'upper': float(boll_upper.iloc[-1]),
                    'mid': float(boll_mid.iloc[-1]),
                    'lower': float(boll_lower.iloc[-1]),
                    'position': float(boll_position.iloc[-1]),
                    'status': 'near_upper' if boll_position.iloc[-1] > 0.8 else ('near_lower' if boll_position.iloc[-1] < 0.2 else 'normal')
                },
                'atr': {
                    'value': float(atr.iloc[-1]),
                    'pct': float(atr.iloc[-1] / latest['close'] * 100)
                },
                'dmi_adx': {
                    'plus_di': float(plus_di.iloc[-1]),
                    'minus_di': float(minus_di.iloc[-1]),
                    'adx': float(adx.iloc[-1]),
                    'trend': 'strong' if adx.iloc[-1] > 25 else ('medium' if adx.iloc[-1] > 20 else 'weak'),
                    'direction': 'bullish' if plus_di.iloc[-1] > minus_di.iloc[-1] else 'bearish'
                },
                'ma': {
                    'ma5': float(ma5.iloc[-1]),
                    'ma20': float(ma20.iloc[-1]),
                    'ma60': float(ma60.iloc[-1]),
                    'price_to_ma5_pct': float((latest['close'] - ma5.iloc[-1]) / ma5.iloc[-1] * 100),
                    'price_to_ma20_pct': float((latest['close'] - ma20.iloc[-1]) / ma20.iloc[-1] * 100),
                    'price_to_ma60_pct': float((latest['close'] - ma60.iloc[-1]) / ma60.iloc[-1] * 100)
                },
                'divergence': divergence_result.get('summary', {})
            }

        except Exception as e:
            logger.error(f"技术面分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_capital_flow(self, market: str, symbol: str) -> Dict:
        """资金面分析"""
        try:
            if market != 'CN':
                return {'available': False}

            # 北向资金
            north_flow = self.hk_connect.comprehensive_analysis(direction='north')

            # 修复: 使用正确的数据路径 metrics.total_inflow_5d
            north_metrics = north_flow.get('metrics', {})
            north_sentiment = north_flow.get('sentiment_analysis', {})

            # 检查北向资金数据是否可用（东方财富数据源可能返回0）
            recent_5d_flow = north_metrics.get('total_inflow_5d', 0)
            data_available = recent_5d_flow != 0 or north_metrics.get('latest_inflow', 0) != 0

            return {
                'type': 'northbound',
                'recent_5d_flow': recent_5d_flow,
                'status': north_sentiment.get('sentiment', '未知'),
                'sentiment_score': north_sentiment.get('sentiment_score', 50),
                'data_available': data_available,
                'data_note': '' if data_available else '北向资金数据暂不可用(数据源问题)'
            }

        except Exception as e:
            logger.error(f"资金面分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_valuation(self, market: str, symbol: str) -> Dict:
        """估值分析"""
        try:
            # ETF的估值分析需要专门数据源，暂时返回占位符
            return {
                'available': False,
                'note': 'ETF估值分析需要专门数据源，待后续集成'
            }
        except Exception as e:
            logger.error(f"估值分析失败: {str(e)}")
            return {'error': str(e)}

    def _calculate_risk_score(self, result: Dict) -> Dict:
        """计算风险评分(0-1,越高越危险)"""
        risk_factors = []
        risk_score = 0.0

        try:
            # 1. 历史概率风险(权重30%)
            hist = result.get('historical_analysis', {})
            down_prob_20d = hist.get('20d', {}).get('down_prob', 0)
            if down_prob_20d > 0.7:
                risk_score += 0.3
                risk_factors.append('历史20日下跌概率>70%')
            elif down_prob_20d > 0.6:
                risk_score += 0.2
                risk_factors.append('历史20日下跌概率>60%')
            elif down_prob_20d > 0.5:
                risk_score += 0.1

            # 2. 技术面风险(权重30%)
            tech = result.get('technical_analysis', {})

            # MACD顶背离
            divergence_summary = tech.get('divergence', [])
            if isinstance(divergence_summary, list):
                for sig in divergence_summary:
                    if isinstance(sig, dict) and 'MACD' in sig.get('type', '') and '顶背' in sig.get('direction', ''):
                        risk_score += 0.15
                        risk_factors.append('MACD顶背离')
                        break

            # RSI超买
            rsi_value = tech.get('rsi', {}).get('value', 50)
            if rsi_value > 80:
                risk_score += 0.1
                risk_factors.append('RSI严重超买(>80)')
            elif rsi_value > 70:
                risk_score += 0.05
                risk_factors.append('RSI超买(>70)')

            # 均线偏离
            ma_deviation = tech.get('ma', {}).get('price_to_ma20_pct', 0)
            if abs(ma_deviation) > 15:
                risk_score += 0.1
                risk_factors.append(f'MA20偏离>{abs(ma_deviation):.1f}%')

            # 3. 资金面风险(权重20%)
            capital = result.get('capital_flow', {})
            if capital and 'sentiment_score' in capital:
                sentiment_score = capital['sentiment_score']
                if sentiment_score < 30:
                    risk_score += 0.2
                    risk_factors.append('资金大幅流出')
                elif sentiment_score < 40:
                    risk_score += 0.1
                    risk_factors.append('资金持续流出')

            # 限制在0-1范围
            risk_score = min(1.0, max(0.0, risk_score))

            # 风险等级
            if risk_score >= 0.7:
                risk_level = '极高风险'
            elif risk_score >= 0.5:
                risk_level = '高风险'
            elif risk_score >= 0.3:
                risk_level = '中风险'
            else:
                risk_level = '低风险'

            return {
                'risk_score': float(risk_score),
                'risk_level': risk_level,
                'risk_factors': risk_factors
            }

        except Exception as e:
            logger.error(f"风险评分计算失败: {str(e)}")
            return {
                'risk_score': 0.5,
                'risk_level': '未知',
                'risk_factors': []
            }

    def _calculate_multi_factor_score(self, result: Dict, config: Dict) -> Dict:
        """
        计算多因子综合评分

        因子权重(等权):
        - 历史点位: 17%
        - 技术面: 17%
        - 估值面: 17%
        - 成交量: 17%
        - 资金面: 17%
        - 市场情绪: 17%
        """
        try:
            # 1. 历史点位评分
            hist_score = self._calc_hist_factor_score(result)

            # 2. 技术面评分
            tech_score = self._calc_tech_factor_score(result)

            # 3. 估值面评分
            valuation_score = self._calc_valuation_factor_score(result)

            # 4. 成交量评分
            volume_score = self._calc_volume_factor_score(result)

            # 5. 资金面评分
            capital_score = self._calc_capital_factor_score(result, config)

            # 6. 市场情绪评分
            sentiment_score = self._calc_sentiment_factor_score(result)

            # ========== 直接等权合成 (不使用正交化) ==========
            # 原因: 当前数据源限制导致很多因子默认值相同(50分)
            # Schmidt正交化会认为这些因子高度相关,过度修正导致所有标的得分趋同
            # 直接等权平均更符合实际需求

            # 构建因子字典
            raw_factors = {
                '估值面': valuation_score['score'],
                '历史点位': hist_score['score'],
                '技术面': tech_score['score'],
                '资金面': capital_score['score'],
                '成交量': volume_score['score'],
                '市场情绪': sentiment_score['score']
            }

            # 直接等权平均
            total_score = sum(raw_factors.values()) / len(raw_factors)

            # 等权权重(仅用于显示)
            equal_weight = 1.0 / 6

            # 正交化后的分数就是原始分数(因为不做正交化)
            factors_orth = raw_factors.copy()

            return {
                'total_score': float(total_score),
                'method': '等权合成',
                'factors': {
                    'hist': {
                        'score': hist_score['score'],
                        'orth_score': factors_orth.get('历史点位', hist_score['score']),
                        'weight': equal_weight,
                        'detail': hist_score['detail']
                    },
                    'tech': {
                        'score': tech_score['score'],
                        'orth_score': factors_orth.get('技术面', tech_score['score']),
                        'weight': equal_weight,
                        'detail': tech_score['detail']
                    },
                    'valuation': {
                        'score': valuation_score['score'],
                        'orth_score': factors_orth.get('估值面', valuation_score['score']),
                        'weight': equal_weight,
                        'detail': valuation_score['detail']
                    },
                    'volume': {
                        'score': volume_score['score'],
                        'orth_score': factors_orth.get('成交量', volume_score['score']),
                        'weight': equal_weight,
                        'detail': volume_score['detail']
                    },
                    'capital': {
                        'score': capital_score['score'],
                        'orth_score': factors_orth.get('资金面', capital_score['score']),
                        'weight': equal_weight,
                        'detail': capital_score['detail']
                    },
                    'sentiment': {
                        'score': sentiment_score['score'],
                        'orth_score': factors_orth.get('市场情绪', sentiment_score['score']),
                        'weight': equal_weight,
                        'detail': sentiment_score['detail']
                    }
                }
            }

        except Exception as e:
            logger.error(f"多因子评分计算失败: {str(e)}")
            return {
                'total_score': 50.0,
                'factors': {}
            }

    def _calc_hist_factor_score(self, result: Dict) -> Dict:
        """历史点位因子评分"""
        hist = result.get('historical_analysis', {})
        up_prob = hist.get('20d', {}).get('up_prob', 0.5)

        # 直接转换为0-100分
        score = up_prob * 100

        return {
            'score': float(score),
            'detail': f"上涨概率{up_prob*100:.1f}%"
        }

    def _calc_tech_factor_score(self, result: Dict) -> Dict:
        """技术面因子评分"""
        tech = result.get('technical_analysis', {})
        score = 50  # 基础分
        details = []

        # RSI评分
        rsi = tech.get('rsi', {}).get('value', 50)
        if rsi < 30:
            score += 20
            details.append('RSI超卖')
        elif rsi < 40:
            score += 10
            details.append('RSI偏低')
        elif rsi > 70:
            score -= 20
            details.append('RSI超买')
        elif rsi > 60:
            score -= 10
            details.append('RSI偏高')

        # MACD评分
        macd_status = tech.get('macd', {}).get('status', '')
        if macd_status == 'golden_cross':
            score += 15
            details.append('MACD金叉')
        elif macd_status == 'death_cross':
            score -= 10
            details.append('MACD死叉')

        # 布林带评分
        boll = tech.get('bollinger', {})
        if boll:
            position = boll.get('position', 50)
            if position < 20:
                score += 10
                details.append('布林下轨')
            elif position > 80:
                score -= 10
                details.append('布林上轨')

        # 背离评分
        divergence = tech.get('divergence', [])
        if isinstance(divergence, list):
            for sig in divergence:
                if isinstance(sig, dict):
                    if '底背' in sig.get('direction', ''):
                        score += 15
                        details.append('底背离')
                        break
                    elif '顶背' in sig.get('direction', ''):
                        score -= 15
                        details.append('顶背离')
                        break

        # 限制在0-100
        score = min(100, max(0, score))

        return {
            'score': float(score),
            'detail': '+'.join(details) if details else '中性'
        }

    def _calc_valuation_factor_score(self, result: Dict) -> Dict:
        """估值面因子评分"""
        valuation = result.get('valuation_analysis', {})
        score = 100  # 默认满分(适用于无估值数据的标的)
        details = []

        # 如果没有估值数据,返回中性评分
        if not valuation or 'error' in valuation:
            return {
                'score': 100.0,
                'detail': '估值中性'
            }

        score = 50  # 有估值数据时,从基础分开始

        # PE分位数
        pe_percentile = valuation.get('pe_percentile', 50)
        if pe_percentile < 20:
            score += 30
            details.append(f'PE低估({pe_percentile:.0f}%)')
        elif pe_percentile < 40:
            score += 15
            details.append(f'PE偏低({pe_percentile:.0f}%)')
        elif pe_percentile > 80:
            score -= 30
            details.append(f'PE高估({pe_percentile:.0f}%)')
        elif pe_percentile > 60:
            score -= 15
            details.append(f'PE偏高({pe_percentile:.0f}%)')

        # PB分位数
        pb_percentile = valuation.get('pb_percentile', 50)
        if pb_percentile < 30:
            score += 10
            details.append('PB低估')
        elif pb_percentile > 70:
            score -= 10
            details.append('PB高估')

        # 限制在0-100
        score = min(100, max(0, score))

        return {
            'score': float(score),
            'detail': '+'.join(details) if details else '估值中性'
        }

    def _calc_volume_factor_score(self, result: Dict) -> Dict:
        """成交量因子评分"""
        volume = result.get('volume_analysis', {})
        score = 50  # 基础分
        details = []

        # 量价配合
        vp_cooperation = volume.get('vp_cooperation', {})
        if vp_cooperation:
            quality = vp_cooperation.get('overall_quality', '')
            if quality == '优秀':
                score += 25
                details.append('量价配合优秀')
            elif quality in ['偏强', '中性']:
                score += 10
                details.append('量价配合中性')
            elif quality == '偏弱':
                score -= 10
                details.append('量价配合偏弱')

        # OBV趋势
        obv = volume.get('obv_analysis', {})
        if obv:
            obv_trend = obv.get('trend', '')
            if obv_trend == '上升':
                score += 15
                details.append('OBV上升')
            elif obv_trend == '下降':
                score -= 15
                details.append('OBV下降')

        # 量比
        turnover = volume.get('turnover', {})
        if turnover:
            volume_ratio = turnover.get('volume_ratio', 1.0)
            if volume_ratio > 2.0:
                score += 10
                details.append(f'放量({volume_ratio:.1f}x)')
            elif volume_ratio < 0.5:
                score -= 5
                details.append('极度缩量')

        # 限制在0-100
        score = min(100, max(0, score))

        return {
            'score': float(score),
            'detail': '+'.join(details) if details else '量能中性'
        }

    def _calc_capital_factor_score(self, result: Dict, config: Dict) -> Dict:
        """资金面因子评分"""
        capital = result.get('capital_flow', {})
        score = 50  # 基础分
        details = []

        market = config.get('market', 'CN')

        # 检查数据是否可用
        if not capital or 'error' in capital or not capital.get('data_available', True):
            return {
                'score': 50.0,
                'detail': '资金中性'
            }

        if market == 'CN':
            # A股: 北向资金
            sentiment_score = capital.get('sentiment_score', 50)
            if sentiment_score > 60:
                score += 25
                details.append('北向资金流入')
            elif sentiment_score > 50:
                score += 10
                details.append('北向资金小幅流入')
            elif sentiment_score < 40:
                score -= 25
                details.append('北向资金流出')
            elif sentiment_score < 50:
                score -= 10
                details.append('北向资金小幅流出')

        elif market == 'HK':
            # 港股: 南向资金
            sentiment_score = capital.get('sentiment_score', 50)
            status = capital.get('status', '')
            if sentiment_score > 60 or '乐观' in status:
                score += 25
                details.append('南向资金流入')
            elif sentiment_score > 50:
                score += 10
                details.append('南向资金小幅流入')
            elif sentiment_score < 40 or '悲观' in status:
                score -= 25
                details.append('南向资金流出')
            elif sentiment_score < 50:
                score -= 10
                details.append('南向资金小幅流出')

        else:
            # 其他市场
            sentiment_score = capital.get('sentiment_score', 50)
            if sentiment_score > 60:
                score += 15
                details.append('资金情绪偏多')
            elif sentiment_score < 40:
                score -= 15
                details.append('资金情绪偏空')

        # 限制在0-100
        score = min(100, max(0, score))

        return {
            'score': float(score),
            'detail': '+'.join(details) if details else '资金中性'
        }

    def _calc_sentiment_factor_score(self, result: Dict) -> Dict:
        """市场情绪因子评分"""
        sentiment = result.get('market_sentiment', {})
        panic = result.get('panic_index', {})
        score = 50  # 基础分
        details = []

        # 恐慌指数（反向指标：恐慌时是买入机会）
        if panic and 'error' not in panic:
            panic_type = panic.get('type', '')
            if panic_type == 'VIX':
                vix_value = panic.get('current_state', {}).get('vix_value', 20)
            elif panic_type in ['HKVI', 'CNVI']:
                vix_value = panic.get('index_value', 20)
            elif panic_type == 'VHSI':
                vix_value = panic.get('current_state', {}).get('vhsi_value', 20)
            else:
                vix_value = 20

            if vix_value >= 30:
                score += 30
                details.append(f'极度恐慌({vix_value:.1f})')
            elif vix_value >= 25:
                score += 15
                details.append(f'恐慌偏高({vix_value:.1f})')
            elif vix_value < 15:
                score -= 15
                details.append(f'过度乐观({vix_value:.1f})')

        # 综合情绪评分
        sentiment_score = sentiment.get('sentiment_score', 50)
        if sentiment_score < 30:
            score += 10
            details.append('情绪低迷')
        elif sentiment_score > 70:
            score -= 10
            details.append('情绪亢奋')

        # 限制在0-100
        score = min(100, max(0, score))

        return {
            'score': float(score),
            'detail': '+'.join(details) if details else '情绪中性'
        }

    def _generate_judgment(self, result: Dict, config: Dict) -> Dict:
        """生成综合判断(基于多因子评分)"""
        try:
            hist = result.get('historical_analysis', {})
            tech = result.get('technical_analysis', {})
            risk = result.get('risk_assessment', {})

            # 计算多因子综合评分
            multi_factor = self._calculate_multi_factor_score(result, config)
            total_score = multi_factor.get('total_score', 50)

            # 基于多因子总分判断方向
            if total_score >= 75:
                direction = '强烈看多'
                position = '70-80%'
            elif total_score >= 60:
                direction = '看多'
                position = '60-70%'
            elif total_score >= 50:
                direction = '中性偏多'
                position = '50-60%'
            elif total_score >= 40:
                direction = '中性'
                position = '40-50%'
            else:
                direction = '看空'
                position = '20-30%'

            # 保留原有变量供后续策略使用
            up_prob_20d = hist.get('20d', {}).get('up_prob', 0)
            risk_score = risk.get('risk_score', 0.5)

            # 操作策略
            strategies = []

            # 基于历史概率
            if up_prob_20d > 0.6:
                strategies.append('历史概率支持，可以配置')
            elif up_prob_20d < 0.4:
                strategies.append('历史概率偏空，建议减仓')

            # 基于技术面
            has_macd_top_div = False
            divergence_summary = tech.get('divergence', [])
            if isinstance(divergence_summary, list):
                for sig in divergence_summary:
                    if isinstance(sig, dict) and 'MACD' in sig.get('type', '') and '顶背' in sig.get('direction', ''):
                        has_macd_top_div = True
                        strategies.append('MACD顶背离，警惕回调')
                        break

            rsi_value = tech.get('rsi', {}).get('value', 50)
            if rsi_value > 70:
                strategies.append('RSI超买，不追高')
            elif rsi_value < 30:
                strategies.append('RSI超卖，可分批买入')

            # 基于风险
            if risk_score > 0.7:
                strategies.append('高风险，强烈建议减仓')
            elif risk_score < 0.3:
                strategies.append('低风险，可以持有')

            # 持有建议逻辑增强：即使看空，低风险资产也可以继续持有
            if direction == '看空' and risk_score < 0.3:
                # 看空但低风险，给出持有建议
                if up_prob_20d >= 0.35:
                    # 看空但概率不是特别差（35%-40%），低风险可以继续持有
                    if '低风险，可以持有' not in strategies:
                        strategies.append('低风险，可以持有')

            return {
                'direction': direction,
                'recommended_position': position,
                'strategies': strategies,
                'multi_factor_score': multi_factor
            }

        except Exception as e:
            logger.error(f"综合判断生成失败: {str(e)}", exc_info=True)
            return {
                'direction': '未知',
                'recommended_position': '50%',
                'strategies': ['数据不足']
            }

    def _analyze_volume(self, market: str, symbol: str, prefer_source: str = None) -> Dict:
        """成交量分析 - 增强版"""
        try:
            df = self.get_etf_data(symbol, period="1y", market=market, prefer_source=prefer_source)
            if df.empty:
                return {'error': '数据获取失败'}

            # 1. 基础成交量分析 (OBV等)
            basic_volume = self.volume_analyzer.analyze_volume(df, periods=20)

            # 2. 量价配合分析
            vp_analysis = self.vp_analyzer.analyze_volume_price_relationship(df, lookback=20)

            # 3. 换手率和量比分析
            turnover_analysis = self.vp_analyzer.analyze_turnover_and_volume_ratio(df, symbol)

            # 4. OBV背离检测
            obv_divergence = self.vp_analyzer.detect_obv_divergence(df, lookback=20)

            # 5. 成交量突破确认分析
            volume_breakout = self.vp_analyzer.analyze_volume_breakout(df, lookback=20)

            # 合并结果
            result = {
                'obv_analysis': basic_volume.get('obv', {}),
                'price_volume_relation': basic_volume.get('price_volume_relation', {}),
                'volume_status': basic_volume.get('volume_status', {}),
                'vp_cooperation': vp_analysis.get('cooperation', {}),
                'vp_divergence': vp_analysis.get('divergence', {}),
                'vp_score': vp_analysis.get('vp_score', 0),
                'vp_signal': vp_analysis.get('signal', ''),
                'vp_description': vp_analysis.get('description', ''),
                'turnover': turnover_analysis,
                'obv_divergence': obv_divergence,
                'volume_breakout': volume_breakout
            }

            return result

        except Exception as e:
            logger.error(f"成交量分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_support_resistance(self, market: str, symbol: str, prefer_source: str = None) -> Dict:
        """支撑压力位分析"""
        try:
            df = self.get_etf_data(symbol, period="1y", market=market, prefer_source=prefer_source)
            if df.empty:
                return {'error': '数据获取失败'}

            # 暂时跳过支撑压力位分析，避免错误
            # sr_analyzer = SupportResistanceAnalyzer(df)
            # sr_result = sr_analyzer.comprehensive_analysis()
            # return sr_result
            return {
                'available': False,
                'note': '支撑压力位分析待优化'
            }

        except Exception as e:
            logger.error(f"支撑压力位分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_market_breadth(self) -> Dict:
        """市场宽度分析(仅A股)"""
        try:
            breadth_result = self.market_breadth_analyzer.comprehensive_analysis()
            return breadth_result

        except Exception as e:
            logger.error(f"市场宽度分析失败: {str(e)}")
            return {'error': str(e)}

    def generate_comprehensive_report(self, sector_keys: List[str] = None) -> Dict:
        """
        生成综合报告

        Args:
            sector_keys: 板块列表，None表示所有板块

        Returns:
            综合报告
        """
        if sector_keys is None:
            sector_keys = [key for key, _, _ in list_all_sectors()]

        logger.info(f"开始生成板块综合报告，共{len(sector_keys)}个板块...")

        report = {
            'timestamp': datetime.now(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'sectors': {}
        }

        # 分析各板块
        for sector_key in sector_keys:
            report['sectors'][sector_key] = self.analyze_single_sector(sector_key)

        logger.info("板块综合报告生成完成")
        return report

    def _generate_investment_summary(self, report: Dict) -> List:
        """生成投资建议总结"""
        strong_buy = []  # 强烈推荐
        neutral = []     # 中性持有
        reduce = []      # 减仓观望

        for sector_key, data in report['sectors'].items():
            if 'error' in data:
                continue

            sector_name = data.get('sector_name', sector_key)
            judgment = data.get('comprehensive_judgment', {})
            hist = data.get('historical_analysis', {})
            risk = data.get('risk_assessment', {})

            up_prob_20d = hist.get('20d', {}).get('up_prob', 0)
            risk_score = risk.get('risk_score', 0.5)
            direction = judgment.get('direction', '未知')

            # 构建指标描述
            metrics = f"20日上涨概率 {up_prob_20d:.1%}, 风险评分 {risk_score:.2f}"

            # 分类
            if direction in ['强烈看多', '看多'] and up_prob_20d >= 0.6:
                strong_buy.append((sector_name, metrics))
            elif direction in ['看空'] or up_prob_20d < 0.4:
                reduce.append((sector_name, metrics))
            else:
                neutral.append((sector_name, metrics))

        # 构建输出
        summary_sections = []
        if strong_buy:
            summary_sections.append(("✅ 强烈推荐 (高胜率+低风险):", strong_buy))
        if neutral:
            summary_sections.append(("⚖️ 中性持有 (观望为主):", neutral))
        if reduce:
            summary_sections.append(("⚠️ 减仓观望 (风险较高):", reduce))

        return summary_sections

    def format_text_report(self, report: Dict) -> str:
        """格式化为文本报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("板块综合分析报告")
        lines.append(f"分析时间: {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        # 添加投资建议总结
        summary_sections = self._generate_investment_summary(report)
        if summary_sections:
            lines.append("\n" + "=" * 80)
            lines.append("【投资建议总结】")
            lines.append("=" * 80)

            for section_title, sectors_info in summary_sections:
                lines.append(f"\n{section_title}")
                for sector_name, metrics in sectors_info:
                    lines.append(f"  • {sector_name}")
                    lines.append(f"    - {metrics}")

            lines.append("\n" + "=" * 80)
            lines.append("【详细分析】")
            lines.append("=" * 80)

        for sector_key, data in report['sectors'].items():
            if 'error' in data:
                lines.append(f"\n【{data['sector_name']}】分析失败: {data['error']}")
                continue

            lines.append(f"\n{'=' * 80}")
            lines.append(f"【{data['sector_name']}】")
            lines.append(f"板块代码: {sector_key} | 分类: {data['category']} | 标的: {', '.join(data['symbols'])}")
            lines.append('=' * 80)

            # 1. 当前点位
            hist = data.get('historical_analysis', {})
            if hist and 'current_price' in hist:
                lines.append(f"\n【当前点位】")
                lines.append(f"  最新价格: {hist['current_price']:.2f}")
                lines.append(f"  涨跌幅: {hist['current_change_pct']:+.2f}%")
                lines.append(f"  数据日期: {hist['current_date']}")

            # 2. 综合判断(提前展示)
            judgment = data.get('comprehensive_judgment', {})
            if judgment:
                lines.append(f"\n【综合判断】")
                lines.append(f"  方向判断: {judgment['direction']}")
                lines.append(f"  建议仓位: {judgment['recommended_position']}")

                if judgment.get('strategies'):
                    lines.append(f"\n  操作策略:")
                    for strategy in judgment['strategies']:
                        lines.append(f"    • {strategy}")

            # 3. 风险评估
            risk = data.get('risk_assessment', {})
            if risk:
                lines.append(f"\n【风险评估】")
                lines.append(f"  综合风险: {risk['risk_score']:.2f} ({risk['risk_level']})")
                if risk.get('risk_factors'):
                    lines.append(f"  风险因素:")
                    for factor in risk['risk_factors']:
                        lines.append(f"    • {factor}")

            # 4. 历史点位分析
            if hist and '20d' in hist:
                lines.append(f"\n【历史点位分析】")
                lines.append(f"  相似点位: {hist['similar_periods_count']} 个")
                lines.append(f"\n  未来20日:")
                lines.append(f"    上涨概率: {hist['20d']['up_prob']:.1%} (下跌概率: {hist['20d']['down_prob']:.1%})")
                lines.append(f"    平均收益: {hist['20d']['mean_return']:+.2%}")
                lines.append(f"    收益中位: {hist['20d']['median_return']:+.2%}")
                lines.append(f"    置信度: {hist['20d']['confidence']:.1%}")

                if hist.get('60d'):
                    lines.append(f"\n  未来60日:")
                    lines.append(f"    上涨概率: {hist['60d']['up_prob']:.1%} (下跌概率: {hist['60d']['down_prob']:.1%})")
                    lines.append(f"    平均收益: {hist['60d']['mean_return']:+.2%}")

            # 5. 技术面分析
            tech = data.get('technical_analysis', {})
            if tech and 'error' not in tech:
                lines.append(f"\n【技术面分析】")

                # MACD
                if 'macd' in tech:
                    macd_status = '金叉' if tech['macd']['status'] == 'golden_cross' else '死叉'
                    lines.append(f"  MACD: {macd_status}")

                # RSI
                if 'rsi' in tech:
                    rsi_val = tech['rsi']['value']
                    lines.append(f"  RSI: {rsi_val:.1f}")

                # KDJ
                if 'kdj' in tech:
                    kdj = tech['kdj']
                    kdj_signal = '金叉' if kdj['signal'] == 'golden_cross' else '死叉'
                    lines.append(f"  KDJ: K={kdj['k']:.1f}, D={kdj['d']:.1f}, J={kdj['j']:.1f} {kdj_signal}")

                # 布林带
                if 'boll' in tech:
                    boll = tech['boll']
                    boll_pos_pct = boll['position'] * 100
                    boll_status_map = {
                        'near_upper': '接近上轨',
                        'near_lower': '接近下轨',
                        'normal': '中轨区域'
                    }
                    lines.append(f"  布林带: 上={boll['upper']:.2f}, 中={boll['mid']:.2f}, 下={boll['lower']:.2f}")
                    lines.append(f"         当前位置: {boll_pos_pct:.0f}% ({boll_status_map.get(boll['status'], '')})")

                # ATR
                if 'atr' in tech:
                    atr = tech['atr']
                    lines.append(f"  ATR(波动率): {atr['value']:.2f} ({atr['pct']:.2f}%)")

                # DMI/ADX
                if 'dmi_adx' in tech:
                    dmi = tech['dmi_adx']
                    lines.append(f"  DMI/ADX: +DI={dmi['plus_di']:.1f}, -DI={dmi['minus_di']:.1f}, ADX={dmi['adx']:.1f}")
                    lines.append(f"          趋势强度: {dmi['trend']}, 方向: {dmi['direction']}")

                # 均线
                if 'ma' in tech:
                    ma = tech['ma']
                    lines.append(f"  均线偏离:")
                    lines.append(f"    MA5: {ma['price_to_ma5_pct']:+.2f}%")
                    lines.append(f"    MA20: {ma['price_to_ma20_pct']:+.2f}%")
                    lines.append(f"    MA60: {ma['price_to_ma60_pct']:+.2f}%")

            # 6. 资金面分析
            capital = data.get('capital_flow', {})
            if capital and 'error' not in capital and capital.get('type'):
                lines.append(f"\n【资金面分析】")
                flow_type = '北向资金(外资)' if capital['type'] == 'northbound' else '南向资金(内地)'
                lines.append(f"  {flow_type}")
                lines.append(f"    近5日累计: {capital['recent_5d_flow']:.2f} 亿元")
                lines.append(f"    流向状态: {capital['status']}")
                lines.append(f"    情绪评分: {capital['sentiment_score']}/100")

            # 7. 成交量分析
            volume = data.get('volume_analysis', {})
            if volume and 'error' not in volume:
                lines.append(f"\n【成交量分析】")
                obv = volume.get('obv_analysis', {})
                if obv:
                    lines.append(f"  OBV趋势: {obv.get('trend', '未知')}")

            # 8. 支撑压力位
            sr = data.get('support_resistance', {})
            if sr and 'error' not in sr:
                lines.append(f"\n【支撑压力位】")
                pivot = sr.get('pivot_points', {})
                if pivot:
                    lines.append(f"  轴心点: {pivot.get('pivot', 0):.2f}")
                    lines.append(f"  阻力位: R1={pivot.get('r1', 0):.2f}, R2={pivot.get('r2', 0):.2f}")
                    lines.append(f"  支撑位: S1={pivot.get('s1', 0):.2f}, S2={pivot.get('s2', 0):.2f}")

        lines.append("\n" + "=" * 80)
        lines.append("由 Claude Code 板块分析系统生成")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        return '\n'.join(lines)


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("测试板块综合分析系统...\n")

    reporter = SectorReporter()
    report = reporter.generate_comprehensive_report()

    text_report = reporter.format_text_report(report)
    print(text_report)

    print("\n测试完成")
