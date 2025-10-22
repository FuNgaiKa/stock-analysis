#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用资产综合分析报告生成器
Comprehensive Asset Reporter

分析对象: 四大科技指数 + 沪深300 + 黄金 + 比特币
分析维度(11大维度):
  1. 历史点位分析
  2. 技术面分析(MACD/RSI/KDJ/布林带/ATR/DMI/ADX/均线/背离)
  3. 资金面分析(北向/南向资金)
  4. 估值分析(PE/PB分位数)
  5. 市场情绪(涨跌停统计)
  6. 风险评估
  7. 综合判断(方向+仓位+策略+组合匹配)
  8. 成交量分析(OBV/量比/量价关系)
  9. 支撑压力位(轴心点/斐波那契/历史高低点)
  10. 市场宽度(新高新低统计,仅A股)
  11. 恐慌指数(VIX/VHSI)

作者: Claude Code
日期: 2025-10-15
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

from position_analysis.market_analyzers.cn_market_analyzer import CNMarketAnalyzer, CN_INDICES
from position_analysis.market_analyzers.hk_market_analyzer import HKMarketAnalyzer, HK_INDICES
from position_analysis.market_analyzers.us_market_analyzer import USMarketAnalyzer, US_INDICES
from position_analysis.analyzers.technical_analysis.divergence_analyzer import DivergenceAnalyzer
from position_analysis.analyzers.market_specific.cn_stock_indicators import CNStockIndicators
from position_analysis.analyzers.market_specific.hk_connect_analyzer import HKConnectAnalyzer
from data_sources.us_stock_source import USStockDataSource

# 新增的分析器(维度8-11)
from position_analysis.analyzers.technical_analysis.volume_analyzer import VolumeAnalyzer
from position_analysis.analyzers.technical_analysis.support_resistance import SupportResistanceAnalyzer
from position_analysis.analyzers.market_structure.market_breadth_analyzer import MarketBreadthAnalyzer
from position_analysis.analyzers.market_indicators.vix_analyzer import VIXAnalyzer
from position_analysis.analyzers.market_indicators.vhsi_analyzer import VHSIAnalyzer
from position_analysis.analyzers.market_structure.sentiment_index import MarketSentimentIndex
from position_analysis.analyzers.market_indicators.cn_volatility_index import CNVolatilityIndex
from position_analysis.analyzers.market_indicators.hk_volatility_index import HKVolatilityIndex

logger = logging.getLogger(__name__)


# 7大资产配置
COMPREHENSIVE_ASSETS = {
    # 四大科技指数
    'CYBZ': {
        'type': 'index',
        'market': 'CN',
        'name': '创业板指',
        'code': 'CYBZ',
        'category': 'tech_index'
    },
    'KECHUANG50': {
        'type': 'index',
        'market': 'CN',
        'name': '科创50',
        'code': 'KECHUANG50',
        'category': 'tech_index'
    },
    'HKTECH': {
        'type': 'index',
        'market': 'HK',
        'name': '恒生科技',
        'code': 'HSTECH',
        'category': 'tech_index'
    },
    'NASDAQ': {
        'type': 'index',
        'market': 'US',
        'name': '纳斯达克',
        'code': 'NASDAQ',
        'category': 'tech_index'
    },

    # 宽基指数
    'HS300': {
        'type': 'index',
        'market': 'CN',
        'name': '沪深300',
        'code': 'HS300',
        'category': 'broad_index'
    },

    # 大宗商品
    'GOLD': {
        'type': 'commodity',
        'market': 'US',
        'name': '黄金',
        'code': 'GOLD',
        'category': 'commodity'
    },

    # 加密货币
    'BTC': {
        'type': 'crypto',
        'market': 'US',
        'name': '比特币',
        'code': 'BTC',
        'category': 'crypto'
    }
}


class ComprehensiveAssetReporter:
    """通用资产综合分析报告生成器"""

    def __init__(self):
        """初始化分析器"""
        logger.info("初始化综合资产分析系统...")

        # 市场分析器
        self.cn_analyzer = CNMarketAnalyzer()
        self.hk_analyzer = HKMarketAnalyzer()
        self.us_analyzer = USMarketAnalyzer()
        self.us_source = USStockDataSource()

        # 技术分析器
        self.divergence_analyzer = DivergenceAnalyzer()

        # A股专项分析器
        self.cn_indicators = CNStockIndicators()
        self.hk_connect = HKConnectAnalyzer()

        # 新增分析器(维度8-11)
        self.volume_analyzer = VolumeAnalyzer()
        # SupportResistanceAnalyzer需要每个资产单独实例化
        self.market_breadth_analyzer = MarketBreadthAnalyzer()  # 仅A股
        self.vix_analyzer = VIXAnalyzer(self.us_source)  # 美股恐慌指数
        self.vhsi_analyzer = VHSIAnalyzer()  # 港股恐慌指数(可能失效)
        self.cn_volatility_analyzer = CNVolatilityIndex()  # A股自定义波动率指数
        self.hk_volatility_analyzer = HKVolatilityIndex()  # 港股自定义波动率指数
        self.sentiment_analyzer = MarketSentimentIndex()  # 综合情绪指数(所有资产)

        logger.info("综合资产分析系统初始化完成")

    def analyze_single_asset(self, asset_key: str) -> Dict:
        """
        综合分析单个资产

        Args:
            asset_key: 资产代码(CYBZ/KECHUANG50/HKTECH/NASDAQ/CSI300/GOLD/BTC)

        Returns:
            完整分析结果
        """
        config = COMPREHENSIVE_ASSETS[asset_key]
        logger.info(f"开始分析 {config['name']}...")

        result = {
            'asset_key': asset_key,
            'asset_name': config['name'],
            'asset_type': config['type'],
            'market': config['market'],
            'category': config['category'],
            'timestamp': datetime.now()
        }

        try:
            # 1. 历史点位分析
            result['historical_analysis'] = self._analyze_historical_position(
                config['market'], config['code'], config['type']
            )

            # 2. 技术面分析
            result['technical_analysis'] = self._analyze_technical(
                config['market'], config['code'], config['type']
            )

            # 3. 资金面分析(仅A股/港股指数)
            if config['market'] in ['CN', 'HK'] and config['type'] == 'index':
                result['capital_flow'] = self._analyze_capital_flow(
                    config['market'], config['code']
                )

            # 4. 估值分析(指数)
            if config['type'] == 'index':
                result['valuation'] = self._analyze_valuation(
                    config['market'], config['code']
                )

            # 5. 市场情绪(仅A股) - 暂时禁用
            # if config['market'] == 'CN' and config['type'] == 'index':
            #     result['market_sentiment'] = self._analyze_sentiment()

            # 6. 风险评估
            result['risk_assessment'] = self._calculate_risk_score(result)

            # 7. 综合判断
            result['comprehensive_judgment'] = self._generate_judgment(result, config)

            # 8. 成交量分析(所有资产)
            result['volume_analysis'] = self._analyze_volume(
                config['market'], config['code'], config['type']
            )

            # 9. 支撑压力位(所有资产)
            result['support_resistance'] = self._analyze_support_resistance(
                config['market'], config['code'], config['type']
            )

            # 10. 市场宽度(仅A股指数)
            if config['market'] == 'CN' and config['type'] == 'index':
                result['market_breadth'] = self._analyze_market_breadth()

            # 11. 恐慌指数/市场情绪(所有资产)
            # 11.1 综合情绪指数(适用所有资产)
            result['market_sentiment'] = self._analyze_market_sentiment()

            # 11.2 专属恐慌指数
            if config['market'] == 'US':
                # 美股使用VIX
                result['panic_index'] = self._analyze_panic_index('VIX', config)
            elif config['market'] == 'HK':
                # 港股优先VHSI,失败时使用自定义波动率指数
                result['panic_index'] = self._analyze_panic_index('VHSI', config)
            elif config['market'] == 'CN':
                # A股使用自定义波动率指数
                result['panic_index'] = self._analyze_panic_index('CNVI', config)

            # 12. 宏观环境分析(美股、黄金、比特币)
            if config['market'] in ['US', 'crypto', 'commodity']:
                result['macro_environment'] = self._analyze_macro_environment(config['market'])

            logger.info(f"{config['name']} 分析完成")

        except Exception as e:
            logger.error(f"分析{config['name']}失败: {str(e)}")
            result['error'] = str(e)

        return result

    def _analyze_historical_position(self, market: str, code: str, asset_type: str) -> Dict:
        """历史点位分析"""
        try:
            # 对于大宗商品和加密货币,使用US数据源获取历史数据
            if asset_type in ['commodity', 'crypto']:
                df = self.us_source.get_us_index_daily(code, period='5y')
                if df.empty:
                    return {'error': '数据获取失败'}

                # 手动计算历史点位概率(简化版)
                current_price = df['close'].iloc[-1]
                tolerance = 0.05

                # 找相似点位
                similar_mask = (df['close'] >= current_price * (1 - tolerance)) & \
                              (df['close'] <= current_price * (1 + tolerance))
                similar_indices = df.index[similar_mask]

                if len(similar_indices) < 10:
                    return {
                        'current_price': float(current_price),
                        'current_date': df.index[-1].strftime('%Y-%m-%d'),
                        'similar_periods_count': len(similar_indices),
                        'note': '相似样本过少,置信度低'
                    }

                # 计算20日后涨跌
                future_returns_20d = []
                for idx in similar_indices:
                    idx_loc = df.index.get_loc(idx)
                    if idx_loc + 20 < len(df):
                        future_price = df['close'].iloc[idx_loc + 20]
                        ret = (future_price - df['close'].iloc[idx_loc]) / df['close'].iloc[idx_loc]
                        future_returns_20d.append(ret)

                # 返回基本信息（即使无未来数据）
                result = {
                    'current_price': float(current_price),
                    'current_date': df.index[-1].strftime('%Y-%m-%d'),
                    'current_change_pct': float((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0.0,
                    'similar_periods_count': len(similar_indices)
                }

                if future_returns_20d:
                    up_count = sum(1 for r in future_returns_20d if r > 0)
                    down_count = len(future_returns_20d) - up_count

                    result['20d'] = {
                        'up_prob': up_count / len(future_returns_20d),
                        'down_prob': down_count / len(future_returns_20d),
                        'mean_return': float(np.mean(future_returns_20d)),
                        'median_return': float(np.median(future_returns_20d)),
                        'confidence': min(100, len(future_returns_20d) / 30 * 100) / 100
                    }
                else:
                    result['20d'] = {
                        'up_prob': 0.0,
                        'down_prob': 0.0,
                        'mean_return': 0.0,
                        'median_return': 0.0,
                        'confidence': 0.0
                    }
                    result['note'] = '无足够未来数据计算预测'

                return result

            # 指数使用原有分析器
            if market == 'CN':
                analyzer_result = self.cn_analyzer.analyze_single_index(code, tolerance=0.05)
            elif market == 'HK':
                analyzer_result = self.hk_analyzer.analyze_single_index(code, tolerance=0.05)
            else:  # US
                analyzer_result = self.us_analyzer.analyze_single_index(code, tolerance=0.05)

            if 'error' in analyzer_result:
                return {'error': analyzer_result['error']}

            # 提取关键数据
            period_20d = analyzer_result.get('period_analysis', {}).get('20d', {})
            period_60d = analyzer_result.get('period_analysis', {}).get('60d', {})

            return {
                'current_price': analyzer_result.get('current_price', 0),
                'current_date': analyzer_result.get('current_date', ''),
                'current_change_pct': analyzer_result.get('current_change_pct', 0),
                'similar_periods_count': analyzer_result.get('similar_periods_count', 0),
                '20d': {
                    'up_prob': period_20d.get('up_prob', 0),
                    'down_prob': period_20d.get('down_prob', 0),
                    'mean_return': period_20d.get('mean_return', 0),
                    'median_return': period_20d.get('median_return', 0),
                    'confidence': period_20d.get('confidence', 0),
                    'position_advice': period_20d.get('position_advice', {})
                },
                '60d': {
                    'up_prob': period_60d.get('up_prob', 0),
                    'down_prob': period_60d.get('down_prob', 0),
                    'mean_return': period_60d.get('mean_return', 0),
                    'median_return': period_60d.get('median_return', 0),
                    'confidence': period_60d.get('confidence', 0)
                }
            }

        except Exception as e:
            logger.error(f"历史点位分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_technical(self, market: str, code: str, asset_type: str) -> Dict:
        """技术面分析"""
        try:
            # 获取资产数据
            if asset_type in ['commodity', 'crypto']:
                df = self.us_source.get_us_index_daily(code, period='5y')
                symbol = code
            elif market == 'CN':
                df = self.cn_analyzer.get_index_data(code, period="5y")
                symbol = CN_INDICES[code].symbol
            elif market == 'HK':
                df = self.hk_analyzer.get_index_data(code, period="5y")
                symbol = HK_INDICES[code].symbol
            else:  # US
                df = self.us_analyzer.get_index_data(code, period="5y")
                symbol = US_INDICES[code].symbol

            if df.empty:
                return {'error': '数据获取失败'}

            # 背离分析
            divergence_result = self.divergence_analyzer.comprehensive_analysis(df, symbol=code, market=market)

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

    def _analyze_volume(self, market: str, code: str, asset_type: str) -> Dict:
        """成交量分析(维度8)"""
        try:
            # 获取资产数据
            if asset_type in ['commodity', 'crypto']:
                df = self.us_source.get_us_index_daily(code, period='1y')
            elif market == 'CN':
                df = self.cn_analyzer.get_index_data(code, period="1y")
            elif market == 'HK':
                df = self.hk_analyzer.get_index_data(code, period="1y")
            else:  # US
                df = self.us_analyzer.get_index_data(code, period="1y")

            if df.empty:
                return {'error': '数据获取失败'}

            # 调用VolumeAnalyzer (不需要symbol参数)
            volume_result = self.volume_analyzer.analyze_volume(df)

            if 'error' in volume_result:
                return volume_result

            # 提取关键数据
            return {
                'obv': volume_result.get('obv', {}),
                'volume_ratio': volume_result.get('volume_ratio', {}),
                'price_volume_relation': volume_result.get('price_volume_relation', {}),
                'anomaly': volume_result.get('anomaly_detection', {})
            }

        except Exception as e:
            logger.error(f"成交量分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_support_resistance(self, market: str, code: str, asset_type: str) -> Dict:
        """支撑压力位分析(维度9)"""
        try:
            # 获取资产数据
            if asset_type in ['commodity', 'crypto']:
                df = self.us_source.get_us_index_daily(code, period='1y')
                symbol = code
            elif market == 'CN':
                df = self.cn_analyzer.get_index_data(code, period="1y")
                symbol = CN_INDICES[code].symbol
            elif market == 'HK':
                df = self.hk_analyzer.get_index_data(code, period="1y")
                symbol = HK_INDICES[code].symbol
            else:  # US
                df = self.us_analyzer.get_index_data(code, period="1y")
                symbol = US_INDICES[code].symbol

            if df.empty:
                return {'error': '数据获取失败'}

            # 实例化SupportResistanceAnalyzer
            from position_analysis.analyzers.technical_analysis.support_resistance import SupportResistanceAnalyzer
            sr_analyzer = SupportResistanceAnalyzer(symbol, df)

            # 综合分析 (捕获异常)
            try:
                sr_result = sr_analyzer.comprehensive_analysis()
            except Exception as e:
                logger.warning(f"支撑压力位分析异常: {str(e)}")
                return {'error': f'分析异常: {str(e)}'}

            if 'error' in sr_result:
                return sr_result

            # 提取关键数据
            return {
                'pivot_points': sr_result.get('pivot_points', {}),
                'fibonacci': sr_result.get('fibonacci_levels', {}),
                'historical_sr': sr_result.get('historical_levels', {}),
                'current_position': sr_result.get('current_position', {})
            }

        except Exception as e:
            logger.error(f"支撑压力位分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_market_breadth(self) -> Dict:
        """市场宽度分析(维度10,仅A股)"""
        try:
            # 调用时需要传入metrics参数
            breadth_result = self.market_breadth_analyzer.analyze_market_strength(metrics=['new_high_low'])

            if 'error' in breadth_result:
                return breadth_result

            # 提取关键数据
            return {
                'new_high_low': breadth_result.get('new_high_low', {}),
                'strength_score': breadth_result.get('strength_score', 0),
                'interpretation': breadth_result.get('interpretation', ''),
                'signal': breadth_result.get('signal', {})
            }

        except Exception as e:
            logger.error(f"市场宽度分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_panic_index(self, index_type: str, config: Dict) -> Dict:
        """恐慌指数分析(维度11)"""
        try:
            if index_type == 'VIX':
                # 美股VIX
                vix_result = self.vix_analyzer.analyze_vix(period='1y')
                if 'error' in vix_result:
                    return vix_result

                return {
                    'type': 'VIX',
                    'current_state': vix_result.get('current_state', {}),
                    'percentile': vix_result.get('percentile', {}),
                    'signal': vix_result.get('signal', {}),
                    'correlation': vix_result.get('correlation', {})
                }

            elif index_type == 'VHSI':
                # 港股VHSI,失败时自动切换到HKVI
                vhsi_result = self.vhsi_analyzer.analyze_vhsi(period='1y')

                if 'error' in vhsi_result:
                    logger.warning(f"VHSI数据获取失败,使用港股自定义波动率指数HKVI: {vhsi_result['error']}")
                    # 切换到HKVI
                    df = self.hk_analyzer.get_index_data(config['code'], period="1y")
                    if df.empty:
                        return {'error': 'VHSI和HKVI数据都无法获取'}

                    hkvi_result = self.hk_volatility_analyzer.calculate_hkvi(df)
                    if 'error' in hkvi_result:
                        return hkvi_result

                    return {
                        'type': 'HKVI',
                        'index_value': hkvi_result['hkvi_value'],
                        'status': hkvi_result['status'],
                        'level': hkvi_result['level'],
                        'emoji': hkvi_result['emoji'],
                        'signal': hkvi_result['signal'],
                        'percentile': hkvi_result.get('percentile', {}),
                        'note': '港股自定义波动率指数(VHSI数据不可用)'
                    }

                return {
                    'type': 'VHSI',
                    'current_vhsi': vhsi_result.get('current_vhsi', 0),
                    'panic_level': vhsi_result.get('panic_level', ''),
                    'percentile': vhsi_result.get('vhsi_percentile', 0),
                    'trend': vhsi_result.get('trend', ''),
                    'signal': vhsi_result.get('signal', ''),
                    'trading_advice': vhsi_result.get('trading_advice', ''),
                    'risk_alert': vhsi_result.get('risk_alert', None)
                }

            elif index_type == 'CNVI':
                # A股自定义波动率指数
                df = self.cn_analyzer.get_index_data(config['code'], period="1y")
                if df.empty:
                    return {'error': 'A股数据获取失败'}

                cnvi_result = self.cn_volatility_analyzer.calculate_cnvi(df)
                if 'error' in cnvi_result:
                    return cnvi_result

                return {
                    'type': 'CNVI',
                    'index_value': cnvi_result['cnvi_value'],
                    'status': cnvi_result['status'],
                    'level': cnvi_result['level'],
                    'emoji': cnvi_result['emoji'],
                    'signal': cnvi_result['signal'],
                    'percentile': cnvi_result.get('percentile', {}),
                    'note': 'A股自定义波动率指数'
                }

            else:
                return {'error': f'未知恐慌指数类型: {index_type}'}

        except Exception as e:
            logger.error(f"恐慌指数分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_market_sentiment(self) -> Dict:
        """综合市场情绪指数分析(维度11,所有资产)"""
        try:
            # 调用MarketSentimentIndex计算综合情绪
            sentiment_result = self.sentiment_analyzer.calculate_comprehensive_sentiment()

            if 'error' in sentiment_result:
                return sentiment_result

            # 提取关键数据
            return {
                'sentiment_score': sentiment_result.get('sentiment_score', 50),
                'rating': sentiment_result.get('rating', '中性'),
                'emoji': sentiment_result.get('emoji', '😐'),
                'suggestion': sentiment_result.get('suggestion', ''),
                'components': {
                    'vix_score': sentiment_result.get('components', {}).get('vix_sentiment', {}).get('score', 50),
                    'vix_level': sentiment_result.get('components', {}).get('vix_sentiment', {}).get('level', ''),
                    'momentum_score': sentiment_result.get('components', {}).get('nasdaq_momentum', {}).get('score', 50),
                    'volume_score': sentiment_result.get('components', {}).get('nasdaq_volume', {}).get('score', 50)
                }
            }

        except Exception as e:
            logger.error(f"综合市场情绪分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_capital_flow(self, market: str, code: str) -> Dict:
        """资金面分析(维度3)"""
        try:
            if market == 'CN':
                # A股: 北向资金 + 融资融券
                north_flow = self.hk_connect.comprehensive_analysis(direction='north')

                # 融资融券分析
                from position_analysis.analyzers.market_specific.margin_trading_analyzer import MarginTradingAnalyzer
                margin_analyzer = MarginTradingAnalyzer(lookback_days=252)
                margin_result = margin_analyzer.comprehensive_analysis(market='sse')  # 使用上交所数据

                result = {
                    'type': 'northbound',
                    'recent_5d_flow': north_flow.get('flow_analysis', {}).get('recent_5d', 0),
                    'status': north_flow.get('sentiment_analysis', {}).get('sentiment', '未知'),
                    'sentiment_score': north_flow.get('sentiment_analysis', {}).get('sentiment_score', 50)
                }

                # 添加融资融券数据
                if 'error' not in margin_result:
                    metrics = margin_result.get('metrics', {})
                    sentiment = margin_result.get('sentiment_analysis', {})

                    result['margin_trading'] = {
                        'available': True,
                        'latest_date': metrics.get('latest_date', ''),
                        'margin_balance': metrics.get('latest_margin_balance', 0),
                        'margin_change_1d': metrics.get('margin_change_pct_1d', 0),
                        'margin_change_5d': metrics.get('margin_change_pct_5d', 0),
                        'margin_change_20d': metrics.get('margin_change_pct_20d', 0),
                        'trend': metrics.get('trend', ''),
                        'percentile': metrics.get('percentile_252d', 50),
                        'sentiment': sentiment.get('sentiment', '未知'),
                        'sentiment_score': sentiment.get('sentiment_score', 50),
                        'signal': sentiment.get('signal', '观望')
                    }
                else:
                    result['margin_trading'] = {'available': False, 'error': margin_result.get('error')}

                return result

            elif market == 'HK':
                # 南向资金
                south_flow = self.hk_connect.comprehensive_analysis(direction='south')
                return {
                    'type': 'southbound',
                    'recent_5d_flow': south_flow.get('flow_analysis', {}).get('recent_5d', 0),
                    'status': south_flow.get('sentiment_analysis', {}).get('sentiment', '未知'),
                    'sentiment_score': south_flow.get('sentiment_analysis', {}).get('sentiment_score', 50)
                }
            else:
                return {'available': False}

        except Exception as e:
            logger.error(f"资金面分析失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_valuation(self, market: str, code: str) -> Dict:
        """
        估值分析(维度4)

        数据源说明:
        - 使用akshare的stock_index_pe_lg接口
        - 支持指数: 沪深300(000300)、创业板指(399006)、中证500(000905)、上证50(000016)
        - 不支持: 科创50(000688)、恒生科技(HSTECH) - 免费数据源暂无历史PE/PB数据
        """
        try:
            # 仅支持A股指数
            if market != 'CN':
                return {'available': False, 'reason': '仅支持A股指数估值分析'}

            # 导入估值分析器
            from position_analysis.analyzers.valuation.index_valuation_analyzer import IndexValuationAnalyzer

            # 代码映射(asset_reporter中的code -> akshare code)
            # 注意: 仅包含akshare的stock_index_pe_lg接口支持的指数
            code_map = {
                'HS300': '000300',      # 沪深300 ✅ 支持
                'CYBZ': '399006',       # 创业板指 ✅ 支持
                # 'KECHUANG50': '000688', # 科创50 ❌ 不支持(数据源无历史PE数据)
            }

            # 转换代码
            index_code = code_map.get(code)
            if not index_code:
                return {'available': False, 'reason': f'指数 {code} 暂不支持PE估值(免费数据源限制)'}

            # 创建分析器实例(10年历史数据)
            valuation_analyzer = IndexValuationAnalyzer(lookback_days=2520)

            # 1. 计算PE/PB分位数
            valuation_result = valuation_analyzer.calculate_valuation_percentile(
                index_code=index_code,
                periods=[252, 756, 1260, 2520]  # 1年、3年、5年、10年
            )

            if 'error' in valuation_result:
                return {'available': False, 'error': valuation_result['error']}

            # 2. 计算股债收益比(ERP)
            erp_result = valuation_analyzer.calculate_equity_risk_premium(index_code=index_code)

            if 'error' in erp_result:
                logger.warning(f"ERP计算失败: {erp_result['error']}")
                erp_result = None

            # 3. 汇总结果
            return {
                'available': True,
                'index_name': valuation_result.get('index_name', ''),

                # PE估值
                'current_pe': valuation_result.get('current_pe', 0),
                'pe_percentiles': valuation_result.get('pe_percentiles', {}),

                # PB估值
                'current_pb': valuation_result.get('current_pb', 0),
                'pb_percentiles': valuation_result.get('pb_percentiles', {}),

                # 估值水平判断
                'valuation_level': valuation_result.get('valuation_level', {}),

                # 股债收益比(ERP)
                'erp': erp_result if erp_result else {'available': False},

                # 数据日期
                'data_date': valuation_result.get('data_date', '')
            }

        except Exception as e:
            logger.error(f"估值分析失败: {str(e)}")
            return {'available': False, 'error': str(e)}

    def _analyze_macro_environment(self, market: str) -> Dict:
        """
        宏观环境分析(维度12: 美债收益率 + 美元指数)

        Args:
            market: 市场代码 ('US', 'CN', 'HK', 'crypto', 'commodity')

        Returns:
            宏观环境分析结果
        """
        try:
            # 仅对美股、黄金、比特币提供宏观分析
            if market not in ['US', 'crypto', 'commodity']:
                return {'available': False, 'reason': '宏观分析仅适用于美股/黄金/比特币'}

            result = {}

            # 1. 美债收益率分析
            try:
                from position_analysis.analyzers.macro.treasury_yield_analyzer import TreasuryYieldAnalyzer
                treasury_analyzer = TreasuryYieldAnalyzer(lookback_days=252)
                treasury_result = treasury_analyzer.comprehensive_analysis()

                if 'error' not in treasury_result:
                    result['treasury_yield'] = {
                        'available': True,
                        'date': treasury_result['date'],
                        'yields': treasury_result['yields'],
                        'curve_shape': treasury_result['curve_shape'],
                        'slope': treasury_result['slope'],
                        'inversion_signal': treasury_result['inversion_signal'],
                        'trend': treasury_result.get('trend')
                    }
                else:
                    result['treasury_yield'] = {'available': False, 'error': treasury_result['error']}
            except Exception as e:
                logger.error(f"美债收益率分析失败: {str(e)}")
                result['treasury_yield'] = {'available': False, 'error': str(e)}

            # 2. 美元指数分析
            try:
                from position_analysis.analyzers.macro.dxy_analyzer import DXYAnalyzer
                dxy_analyzer = DXYAnalyzer(lookback_days=252)
                dxy_result = dxy_analyzer.comprehensive_analysis()

                if 'error' not in dxy_result:
                    result['dxy'] = {
                        'available': True,
                        'date': dxy_result['date'],
                        'current_price': dxy_result['current_price'],
                        'indicators': dxy_result['indicators'],
                        'strength_analysis': dxy_result['strength_analysis']
                    }
                else:
                    result['dxy'] = {'available': False, 'error': dxy_result['error']}
            except Exception as e:
                logger.error(f"美元指数分析失败: {str(e)}")
                result['dxy'] = {'available': False, 'error': str(e)}

            result['available'] = True
            return result

        except Exception as e:
            logger.error(f"宏观环境分析失败: {str(e)}")
            return {'available': False, 'error': str(e)}

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
                risk_level = '极高风险🔴'
            elif risk_score >= 0.5:
                risk_level = '高风险⚠️'
            elif risk_score >= 0.3:
                risk_level = '中风险🟡'
            else:
                risk_level = '低风险🟢'

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

    def _generate_judgment(self, result: Dict, config: Dict) -> Dict:
        """生成综合判断"""
        try:
            hist = result.get('historical_analysis', {})
            tech = result.get('technical_analysis', {})
            risk = result.get('risk_assessment', {})

            up_prob_20d = hist.get('20d', {}).get('up_prob', 0)
            risk_score = risk.get('risk_score', 0.5)

            # 判断方向
            if up_prob_20d >= 0.7 and risk_score < 0.3:
                direction = '强烈看多✅✅'
                position = '70-80%'
            elif up_prob_20d >= 0.6 and risk_score < 0.5:
                direction = '看多✅'
                position = '60-70%'
            elif up_prob_20d >= 0.5 and risk_score < 0.6:
                direction = '中性偏多⚖️'
                position = '50-60%'
            elif up_prob_20d < 0.4 or risk_score > 0.7:
                direction = '看空🔴'
                position = '20-30%'
            else:
                direction = '中性⚖️'
                position = '40-50%'

            # 操作策略
            strategies = []

            # 基于历史概率
            if up_prob_20d > 0.6:
                strategies.append('历史概率支持,可以配置')
            elif up_prob_20d < 0.4:
                strategies.append('历史概率偏空,建议减仓')

            # 基于技术面
            has_macd_top_div = False
            divergence_summary = tech.get('divergence', [])
            if isinstance(divergence_summary, list):
                for sig in divergence_summary:
                    if isinstance(sig, dict) and 'MACD' in sig.get('type', '') and '顶背' in sig.get('direction', ''):
                        has_macd_top_div = True
                        strategies.append('MACD顶背离,警惕回调')
                        break

            rsi_value = tech.get('rsi', {}).get('value', 50)
            if rsi_value > 70:
                strategies.append('RSI超买,不追高')
            elif rsi_value < 30:
                strategies.append('RSI超卖,可分批买入')

            # 基于风险
            if risk_score > 0.7:
                strategies.append('⚠️ 高风险,强烈建议减仓')
            elif risk_score < 0.3:
                strategies.append('✅ 低风险,可以持有')

            # 持有建议逻辑增强：即使看空，低风险资产也可以继续持有
            # 黄金、避险资产等特殊场景
            if direction == '看空🔴' and risk_score < 0.3:
                # 看空但低风险，给出持有建议
                if config['category'] == 'commodity':
                    # 避险资产虽然看空，但可以继续持有
                    if '✅ 低风险,可以持有' not in strategies:
                        strategies.append('✅ 低风险,可以持有')
                elif up_prob_20d >= 0.35:
                    # 看空但概率不是特别差（35%-40%），低风险可以继续持有
                    if '✅ 低风险,可以持有' not in strategies:
                        strategies.append('✅ 低风险,可以持有')

            # 特殊资产提示
            if config['category'] == 'commodity':
                strategies.append('💰 避险资产,关注地缘政治和通胀')
            elif config['category'] == 'crypto':
                strategies.append('₿ 波动较大,控制仓位,注意风险')

            # 组合策略匹配
            strategy_match = self._match_combo_strategies(result)

            return {
                'direction': direction,
                'recommended_position': position,
                'strategies': strategies,
                'combo_strategy_match': strategy_match
            }

        except Exception as e:
            logger.error(f"综合判断生成失败: {str(e)}", exc_info=True)
            return {
                'direction': '未知',
                'recommended_position': '50%',
                'strategies': ['数据不足'],
                'combo_strategy_match': {}
            }

    def _match_combo_strategies(self, result: Dict) -> Dict:
        """匹配组合策略"""
        hist = result.get('historical_analysis', {})
        tech = result.get('technical_analysis', {})
        capital = result.get('capital_flow', {})
        risk = result.get('risk_assessment', {})

        up_prob = hist.get('20d', {}).get('up_prob', 0)
        risk_score = risk.get('risk_score', 0.5)
        rsi_value = tech.get('rsi', {}).get('value', 50)
        macd_status = tech.get('macd', {}).get('status', '')

        matches = {}

        # 策略1: 牛市确认组合
        bull_conditions = [
            ('历史概率>60%', up_prob > 0.6),
            ('风险评分<0.4', risk_score < 0.4),
            ('MACD金叉', macd_status == 'golden_cross'),
            ('RSI健康(30-70)', 30 < rsi_value < 70),
            ('资金流入', capital.get('sentiment_score', 50) > 60 if capital.get('sentiment_score') else False)
        ]
        bull_matched = sum(1 for _, cond in bull_conditions if cond)
        matches['bull_confirmation'] = {
            'matched': bull_matched,
            'total': len(bull_conditions),
            'conditions': [name for name, cond in bull_conditions if cond]
        }

        # 策略2: 熊市确认组合
        has_macd_top_div = False
        divergence_summary = tech.get('divergence', [])
        if isinstance(divergence_summary, list):
            for sig in divergence_summary:
                if isinstance(sig, dict) and 'MACD' in sig.get('type', '') and '顶背' in sig.get('direction', ''):
                    has_macd_top_div = True
                    break

        bear_conditions = [
            ('历史概率<40%', up_prob < 0.4),
            ('风险评分>0.6', risk_score > 0.6),
            ('MACD死叉或顶背离', macd_status == 'death_cross' or has_macd_top_div),
            ('RSI超买', rsi_value > 70),
            ('资金流出', capital.get('sentiment_score', 50) < 40 if capital.get('sentiment_score') else False)
        ]
        bear_matched = sum(1 for _, cond in bear_conditions if cond)
        matches['bear_confirmation'] = {
            'matched': bear_matched,
            'total': len(bear_conditions),
            'conditions': [name for name, cond in bear_conditions if cond]
        }

        # 策略3: 抄底组合
        bottom_conditions = [
            ('RSI<30', rsi_value < 30),
            ('资金开始流入', capital.get('sentiment_score', 50) > 50 if capital.get('sentiment_score') else False),
            ('历史概率>50%', up_prob > 0.5)
        ]
        bottom_matched = sum(1 for _, cond in bottom_conditions if cond)
        matches['bottom_fishing'] = {
            'matched': bottom_matched,
            'total': len(bottom_conditions),
            'conditions': [name for name, cond in bottom_conditions if cond]
        }

        # 策略4: 逃顶组合
        escape_conditions = [
            ('MACD顶背离', has_macd_top_div),
            ('RSI>80', rsi_value > 80),
            ('风险评分>0.7', risk_score > 0.7),
            ('资金流出', capital.get('sentiment_score', 50) < 40 if capital.get('sentiment_score') else False)
        ]
        escape_matched = sum(1 for _, cond in escape_conditions if cond)
        matches['top_escape'] = {
            'matched': escape_matched,
            'total': len(escape_conditions),
            'conditions': [name for name, cond in escape_conditions if cond]
        }

        return matches

    def generate_comprehensive_report(self) -> Dict:
        """生成综合资产分析报告"""
        logger.info("开始生成综合资产分析报告...")

        report = {
            'timestamp': datetime.now(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'assets': {}
        }

        # 分析7大资产
        for asset_key in COMPREHENSIVE_ASSETS.keys():
            report['assets'][asset_key] = self.analyze_single_asset(asset_key)

        logger.info("综合资产分析报告生成完成")
        return report

    def format_text_report(self, report: Dict) -> str:
        """格式化为文本报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("综合资产分析报告")
        lines.append("分析对象: 四大科技指数 + 沪深300 + 黄金 + 比特币")
        lines.append(f"分析时间: {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        # 按类别分组
        tech_indices = []
        broad_indices = []
        commodities = []
        cryptos = []

        for asset_key, data in report['assets'].items():
            if 'error' in data:
                continue
            category = data.get('category', '')
            if category == 'tech_index':
                tech_indices.append((asset_key, data))
            elif category == 'broad_index':
                broad_indices.append((asset_key, data))
            elif category == 'commodity':
                commodities.append((asset_key, data))
            elif category == 'crypto':
                cryptos.append((asset_key, data))

        # 输出各类别
        for category_name, assets in [
            ('【四大科技指数】', tech_indices),
            ('【宽基指数】', broad_indices),
            ('【大宗商品】', commodities),
            ('【加密货币】', cryptos)
        ]:
            if not assets:
                continue

            lines.append(f"\n{category_name}")
            lines.append("=" * 80)

            for asset_key, data in assets:
                lines.append(f"\n{'─' * 80}")
                lines.append(f"【{data['asset_name']}】")
                lines.append('─' * 80)

                # 1. 当前点位
                hist = data.get('historical_analysis', {})
                if hist and 'current_price' in hist:
                    lines.append(f"\n【当前点位】")
                    lines.append(f"  最新价格: {hist['current_price']:.2f}")
                    if 'current_change_pct' in hist:
                        lines.append(f"  涨跌幅: {hist['current_change_pct']:+.2f}%")
                    lines.append(f"  数据日期: {hist.get('current_date', '')}")

                # 2. 历史点位分析
                if hist and '20d' in hist:
                    lines.append(f"\n【历史点位分析】")
                    lines.append(f"  相似点位: {hist.get('similar_periods_count', 0)} 个")
                    lines.append(f"\n  未来20日:")
                    lines.append(f"    上涨概率: {hist['20d']['up_prob']:.1%} (下跌概率: {hist['20d']['down_prob']:.1%})")
                    lines.append(f"    平均收益: {hist['20d']['mean_return']:+.2%}")
                    lines.append(f"    收益中位: {hist['20d']['median_return']:+.2%}")
                    lines.append(f"    置信度: {hist['20d']['confidence']:.1%}")

                    if hist.get('60d'):
                        lines.append(f"\n  未来60日:")
                        lines.append(f"    上涨概率: {hist['60d']['up_prob']:.1%}")
                        lines.append(f"    平均收益: {hist['60d']['mean_return']:+.2%}")

                # 3. 技术面分析
                tech = data.get('technical_analysis', {})
                if tech and 'error' not in tech:
                    lines.append(f"\n【技术面分析】")

                    if 'macd' in tech:
                        macd_status = '金叉✅' if tech['macd']['status'] == 'golden_cross' else '死叉🔴'
                        lines.append(f"  MACD: {macd_status}")

                    if 'rsi' in tech:
                        rsi_val = tech['rsi']['value']
                        rsi_status = tech['rsi']['status']
                        rsi_emoji = '⚠️' if rsi_status == 'overbought' else ('✅' if rsi_status == 'oversold' else '😊')
                        lines.append(f"  RSI: {rsi_val:.1f} {rsi_emoji}")

                    if 'kdj' in tech:
                        kdj = tech['kdj']
                        kdj_signal = '金叉✅' if kdj['signal'] == 'golden_cross' else '死叉🔴'
                        kdj_status_emoji = '⚠️' if kdj['status'] == 'overbought' else ('✅' if kdj['status'] == 'oversold' else '😊')
                        lines.append(f"  KDJ: K={kdj['k']:.1f}, D={kdj['d']:.1f}, J={kdj['j']:.1f} {kdj_signal} {kdj_status_emoji}")

                    if 'boll' in tech:
                        boll = tech['boll']
                        boll_pos_pct = boll['position'] * 100
                        if boll['status'] == 'near_upper':
                            boll_emoji = '⚠️ 接近上轨'
                        elif boll['status'] == 'near_lower':
                            boll_emoji = '✅ 接近下轨'
                        else:
                            boll_emoji = '😊  中轨区域'
                        lines.append(f"  布林带: 上={boll['upper']:.2f}, 中={boll['mid']:.2f}, 下={boll['lower']:.2f}")
                        lines.append(f"         当前位置: {boll_pos_pct:.0f}% {boll_emoji}")

                    if 'atr' in tech:
                        atr = tech['atr']
                        lines.append(f"  ATR(波动率): {atr['value']:.2f} ({atr['pct']:.2f}%)")

                    if 'dmi_adx' in tech:
                        dmi = tech['dmi_adx']
                        trend_emoji = '🔥' if dmi['trend'] == 'strong' else ('📊' if dmi['trend'] == 'medium' else '💤')
                        direction_emoji = '📈' if dmi['direction'] == 'bullish' else '📉'
                        lines.append(f"  DMI/ADX: +DI={dmi['plus_di']:.1f}, -DI={dmi['minus_di']:.1f}, ADX={dmi['adx']:.1f}")
                        lines.append(f"          趋势强度: {dmi['trend']} {trend_emoji}, 方向: {direction_emoji}")

                    if 'ma' in tech:
                        ma = tech['ma']
                        lines.append(f"  均线偏离:")
                        lines.append(f"    MA5: {ma['price_to_ma5_pct']:+.2f}%")
                        lines.append(f"    MA20: {ma['price_to_ma20_pct']:+.2f}%")
                        lines.append(f"    MA60: {ma['price_to_ma60_pct']:+.2f}%")

                # 4. 资金面分析
                capital = data.get('capital_flow', {})
                if capital and 'error' not in capital and capital.get('type'):
                    lines.append(f"\n【资金面分析】")
                    flow_type = '北向资金(外资)' if capital['type'] == 'northbound' else '南向资金(内地)'
                    lines.append(f"  {flow_type}")
                    lines.append(f"    近5日累计: {capital['recent_5d_flow']:.2f} 亿元")
                    lines.append(f"    流向状态: {capital['status']}")
                    lines.append(f"    情绪评分: {capital['sentiment_score']}/100")

                    # 融资融券数据(仅A股)
                    margin = capital.get('margin_trading', {})
                    if margin and margin.get('available'):
                        lines.append(f"\n  融资融券(杠杆指标):")
                        lines.append(f"    数据日期: {margin.get('latest_date', 'N/A')}")

                        balance_billion = margin.get('margin_balance', 0) / 1e8
                        lines.append(f"    融资余额: {balance_billion:.2f} 亿元")

                        change_1d = margin.get('margin_change_1d', 0)
                        change_5d = margin.get('margin_change_5d', 0)
                        change_20d = margin.get('margin_change_20d', 0)
                        lines.append(f"    单日变化: {change_1d:+.2f}%")
                        lines.append(f"    5日变化: {change_5d:+.2f}%")
                        lines.append(f"    20日变化: {change_20d:+.2f}%")

                        trend = margin.get('trend', '未知')
                        trend_emoji = '📈' if trend == '上升' else ('📉' if trend == '下降' else '➡️')
                        lines.append(f"    趋势: {trend} {trend_emoji}")

                        percentile = margin.get('percentile', 50)
                        lines.append(f"    历史分位: {percentile:.1f}%")

                        sentiment = margin.get('sentiment', '未知')
                        sentiment_score = margin.get('sentiment_score', 50)
                        signal = margin.get('signal', '观望')
                        lines.append(f"    市场情绪: {sentiment} ({sentiment_score}/100)")
                        lines.append(f"    交易信号: {signal}")

                # 4.5 估值分析(维度4,仅A股指数)
                valuation = data.get('valuation', {})
                if valuation and valuation.get('available'):
                    lines.append(f"\n【估值分析】(A股专属)")

                    # PE估值
                    current_pe = valuation.get('current_pe', 0) or 0
                    pe_percentiles = valuation.get('pe_percentiles', {})
                    if current_pe > 0 and pe_percentiles:
                        lines.append(f"  PE估值:")
                        lines.append(f"    当前PE: {current_pe:.2f}")
                        lines.append(f"    历史分位:")
                        for period_name, data in pe_percentiles.items():
                            if isinstance(data, dict):
                                pct = data.get('percentile', 0) / 100
                                level = data.get('level', '')
                                lines.append(f"      {period_name}: {pct:.1%} ({level})")
                            else:
                                lines.append(f"      {period_name}: {data:.1%}")

                    # PB估值
                    current_pb = valuation.get('current_pb', 0) or 0
                    pb_percentiles = valuation.get('pb_percentiles', {})
                    if current_pb > 0 and pb_percentiles:
                        lines.append(f"  PB估值:")
                        lines.append(f"    当前PB: {current_pb:.2f}")
                        lines.append(f"    历史分位:")
                        for period_name, data in pb_percentiles.items():
                            if isinstance(data, dict):
                                pct = data.get('percentile', 0) / 100
                                level = data.get('level', '')
                                lines.append(f"      {period_name}: {pct:.1%} ({level})")
                            else:
                                lines.append(f"      {period_name}: {data:.1%}")

                    # 估值水平判断
                    val_level = valuation.get('valuation_level', {})
                    if val_level:
                        pe_level = val_level.get('pe_level', {})
                        pb_level = val_level.get('pb_level', {})
                        if pe_level:
                            level_desc = pe_level.get('level', '合理')
                            emoji = pe_level.get('emoji', '➡️')
                            lines.append(f"  估值水平: {level_desc} {emoji}")

                    # 股债收益比(ERP)
                    erp = valuation.get('erp', {})
                    if erp and erp.get('available'):
                        erp_value = erp.get('erp_value', 0)
                        erp_pct = erp_value * 100
                        signal = erp.get('signal', {})
                        if signal:
                            erp_desc = signal.get('description', '')
                            lines.append(f"  股债收益比(ERP): {erp_pct:+.2f}% ({erp_desc})")

                # 5. 风险评估
                risk = data.get('risk_assessment', {})
                if risk:
                    lines.append(f"\n【风险评估】")
                    lines.append(f"  综合风险: {risk['risk_score']:.2f} ({risk['risk_level']})")
                    if risk.get('risk_factors'):
                        lines.append(f"  风险因素:")
                        for factor in risk['risk_factors']:
                            lines.append(f"    • {factor}")

                # 6. 综合判断
                judgment = data.get('comprehensive_judgment', {})
                if judgment:
                    lines.append(f"\n【综合判断】")
                    lines.append(f"  方向判断: {judgment['direction']}")
                    lines.append(f"  建议仓位: {judgment['recommended_position']}")

                    if judgment.get('strategies'):
                        lines.append(f"\n  操作策略:")
                        for strategy in judgment['strategies']:
                            lines.append(f"    • {strategy}")

                    # 组合策略匹配
                    combo = judgment.get('combo_strategy_match', {})
                    if combo:
                        lines.append(f"\n  组合策略匹配:")

                        bull = combo.get('bull_confirmation', {})
                        if bull.get('matched', 0) > 0:
                            emoji = '✅✅' if bull['matched'] >= 4 else ('✅' if bull['matched'] >= 3 else '⚖️')
                            lines.append(f"    {emoji} 牛市确认组合: {bull['matched']}/{bull['total']}项")
                            if bull.get('conditions'):
                                for cond in bull['conditions']:
                                    lines.append(f"         ✓ {cond}")

                        bear = combo.get('bear_confirmation', {})
                        if bear.get('matched', 0) >= 2:
                            emoji = '🔴' if bear['matched'] >= 3 else '⚠️'
                            lines.append(f"    {emoji} 熊市确认组合: {bear['matched']}/{bear['total']}项")
                            if bear.get('conditions'):
                                for cond in bear['conditions']:
                                    lines.append(f"         ✗ {cond}")

                        bottom = combo.get('bottom_fishing', {})
                        if bottom.get('matched', 0) >= 2:
                            lines.append(f"    💎 抄底组合: {bottom['matched']}/{bottom['total']}项")

                        escape = combo.get('top_escape', {})
                        if escape.get('matched', 0) >= 2:
                            lines.append(f"    🚨 逃顶组合: {escape['matched']}/{escape['total']}项")

                # 7. 成交量分析(维度8)
                volume = data.get('volume_analysis', {})
                if volume and 'error' not in volume:
                    lines.append(f"\n【成交量分析】")

                    obv = volume.get('obv', {})
                    if obv:
                        trend_emoji = '📈' if obv.get('trend') == 'uptrend' else ('📉' if obv.get('trend') == 'downtrend' else '➡️')
                        lines.append(f"  OBV趋势: {obv.get('trend', 'N/A')} {trend_emoji}")

                    volume_ratio = volume.get('volume_ratio', {})
                    if volume_ratio and 'current' in volume_ratio:
                        ratio = volume_ratio['current']
                        ratio_emoji = '🔥' if ratio > 2 else ('📊' if ratio > 1 else '💤')
                        lines.append(f"  量比: {ratio:.2f} {ratio_emoji}")

                    pv_relation = volume.get('price_volume_relation', {})
                    if pv_relation and 'signal' in pv_relation:
                        lines.append(f"  量价关系: {pv_relation.get('signal', 'N/A')}")

                # 8. 支撑压力位(维度9)
                sr = data.get('support_resistance', {})
                if sr and 'error' not in sr:
                    lines.append(f"\n【支撑压力位】")

                    pivot = sr.get('pivot_points', {})
                    if pivot:
                        lines.append(f"  轴心点位:")
                        if 'r1' in pivot:
                            lines.append(f"    压力1: {pivot['r1']:.2f}")
                        if 'pivot' in pivot:
                            lines.append(f"    轴心: {pivot['pivot']:.2f}")
                        if 's1' in pivot:
                            lines.append(f"    支撑1: {pivot['s1']:.2f}")

                    current_pos = sr.get('current_position', {})
                    if current_pos and 'nearest_support' in current_pos:
                        lines.append(f"  当前位置:")
                        lines.append(f"    最近支撑: {current_pos['nearest_support']:.2f}")
                        lines.append(f"    最近压力: {current_pos.get('nearest_resistance', 0):.2f}")

                # 9. 市场宽度(维度10,仅A股)
                breadth = data.get('market_breadth', {})
                if breadth and 'error' not in breadth:
                    lines.append(f"\n【市场宽度】(A股专属)")

                    new_hl = breadth.get('new_high_low', {})
                    if new_hl:
                        lines.append(f"  创新高数: {new_hl.get('new_high_count', 0)}")
                        lines.append(f"  创新低数: {new_hl.get('new_low_count', 0)}")

                    strength = breadth.get('strength_score', 0)
                    if strength:
                        strength_emoji = '💪' if strength > 0.7 else ('😊' if strength > 0.3 else '😰')
                        lines.append(f"  市场强度: {strength:.2f} {strength_emoji}")

                    if breadth.get('interpretation'):
                        lines.append(f"  解读: {breadth['interpretation']}")

                # 10. 综合市场情绪(维度11,所有资产)
                sentiment = data.get('market_sentiment', {})
                if sentiment and 'error' not in sentiment:
                    lines.append(f"\n【综合市场情绪】")
                    lines.append(f"  情绪评分: {sentiment['sentiment_score']:.1f}/100 {sentiment.get('emoji', '😐')}")
                    lines.append(f"  情绪等级: {sentiment.get('rating', '中性')}")
                    if sentiment.get('suggestion'):
                        lines.append(f"  操作建议: {sentiment['suggestion']}")

                    # 显示情绪组件详情(可选)
                    components = sentiment.get('components', {})
                    if components and any(components.values()):
                        lines.append(f"  情绪组件:")
                        if components.get('vix_score'):
                            lines.append(f"    VIX情绪: {components['vix_score']:.1f} ({components.get('vix_level', 'N/A')})")
                        if components.get('momentum_score'):
                            lines.append(f"    价格动量: {components['momentum_score']:.1f}")
                        if components.get('volume_score'):
                            lines.append(f"    成交量: {components['volume_score']:.1f}")

                # 11. 专属恐慌指数(美股VIX/港股VHSI/A股CNVI/港股HKVI)
                panic = data.get('panic_index', {})
                if panic and 'error' not in panic:
                    panic_type = panic.get('type', '')
                    lines.append(f"\n【{panic_type}恐慌指数】")

                    if panic.get('note'):
                        lines.append(f"  说明: {panic['note']}")

                    if panic_type == 'VIX':
                        state = panic.get('current_state', {})
                        if state:
                            vix_val = state.get('vix_value', 0)
                            status = state.get('status', '')
                            status_emoji = '😱' if vix_val > 30 else ('⚠️' if vix_val > 20 else '😊')
                            lines.append(f"  VIX值: {vix_val:.2f} ({status}) {status_emoji}")

                        signal = panic.get('signal', {})
                        if signal and 'action' in signal:
                            lines.append(f"  操作建议: {signal['action']}")

                    elif panic_type == 'VHSI':
                        vhsi_val = panic.get('current_vhsi', 0)
                        panic_level = panic.get('panic_level', '')
                        vhsi_emoji = '😱' if vhsi_val > 30 else ('⚠️' if vhsi_val > 20 else '😊')
                        lines.append(f"  VHSI值: {vhsi_val:.2f} ({panic_level}) {vhsi_emoji}")

                        if panic.get('signal'):
                            lines.append(f"  信号: {panic['signal']}")

                        if panic.get('risk_alert'):
                            lines.append(f"  风险提示: {panic['risk_alert']}")

                    elif panic_type in ['CNVI', 'HKVI']:
                        # A股CNVI或港股HKVI
                        index_val = panic.get('index_value', 0)
                        status = panic.get('status', '')
                        emoji = panic.get('emoji', '😊')
                        lines.append(f"  指数值: {index_val:.2f} ({status}) {emoji}")

                        signal = panic.get('signal', {})
                        if signal:
                            lines.append(f"  信号: {signal.get('signal', 'N/A')}")
                            if signal.get('action'):
                                lines.append(f"  操作建议: {signal['action']}")

                        percentile = panic.get('percentile', {})
                        if percentile:
                            lines.append(f"  历史分位: {percentile.get('description', 'N/A')}")

        lines.append("\n" + "=" * 80)
        lines.append("由 Claude Code 量化分析系统生成")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        return '\n'.join(lines)

    def format_markdown_report(self, report: Dict) -> str:
        """格式化为Markdown报告"""
        lines = []
        lines.append("# 综合资产分析报告")
        lines.append("")
        lines.append(f"**分析对象**: 四大科技指数 + 沪深300 + 黄金 + 比特币")
        lines.append(f"**分析时间**: {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**分析维度**: 11大维度全面覆盖")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 按类别分组
        tech_indices = []
        broad_indices = []
        commodities = []
        cryptos = []

        for asset_key, data in report['assets'].items():
            if 'error' in data:
                continue
            category = data.get('category', '')
            if category == 'tech_index':
                tech_indices.append((asset_key, data))
            elif category == 'broad_index':
                broad_indices.append((asset_key, data))
            elif category == 'commodity':
                commodities.append((asset_key, data))
            elif category == 'crypto':
                cryptos.append((asset_key, data))

        # 输出各类别
        for category_name, assets in [
            ('四大科技指数', tech_indices),
            ('宽基指数', broad_indices),
            ('大宗商品', commodities),
            ('加密货币', cryptos)
        ]:
            if not assets:
                continue

            lines.append(f"## {category_name}")
            lines.append("")

            for asset_key, data in assets:
                lines.append(f"### {data['asset_name']}")
                lines.append("")

                # 1. 当前点位
                hist = data.get('historical_analysis', {})
                if hist and 'current_price' in hist:
                    lines.append("#### 当前点位")
                    lines.append(f"- **最新价格**: {hist['current_price']:.2f}")
                    if 'current_change_pct' in hist:
                        change_emoji = '📈' if hist['current_change_pct'] > 0 else ('📉' if hist['current_change_pct'] < 0 else '➡️')
                        lines.append(f"- **涨跌幅**: {hist['current_change_pct']:+.2f}% {change_emoji}")
                    lines.append(f"- **数据日期**: {hist.get('current_date', '')}")
                    lines.append("")

                # 2. 综合判断 (最重要,放在最前面)
                judgment = data.get('comprehensive_judgment', {})
                if judgment:
                    lines.append("#### 综合判断")
                    lines.append(f"- **方向判断**: {judgment['direction']}")
                    lines.append(f"- **建议仓位**: {judgment['recommended_position']}")

                    if judgment.get('strategies'):
                        lines.append("")
                        lines.append("**操作策略**:")
                        for strategy in judgment['strategies']:
                            lines.append(f"  - {strategy}")
                    lines.append("")

                # 3. 历史点位分析
                if hist and '20d' in hist:
                    lines.append("#### 历史点位分析")
                    lines.append(f"- **相似点位**: {hist.get('similar_periods_count', 0)} 个")
                    lines.append("")
                    lines.append("| 周期 | 上涨概率 | 平均收益 | 收益中位 | 置信度 |")
                    lines.append("|------|----------|----------|----------|--------|")
                    up_prob = hist['20d']['up_prob'] * 100
                    mean_ret = hist['20d']['mean_return'] * 100
                    median_ret = hist['20d']['median_return'] * 100
                    confidence = hist['20d']['confidence'] * 100
                    lines.append(f"| 未来20日 | {up_prob:.1f}% | {mean_ret:+.2f}% | {median_ret:+.2f}% | {confidence:.1f}% |")

                    if hist.get('60d'):
                        up_prob_60 = hist['60d']['up_prob'] * 100
                        mean_ret_60 = hist['60d']['mean_return'] * 100
                        lines.append(f"| 未来60日 | {up_prob_60:.1f}% | {mean_ret_60:+.2f}% | - | - |")
                    lines.append("")

                # 3. 技术面分析
                tech = data.get('technical_analysis', {})
                if tech and 'error' not in tech:
                    lines.append("#### 技术面分析")

                    indicators = []
                    if 'macd' in tech:
                        macd_status = '✅ 金叉' if tech['macd']['status'] == 'golden_cross' else '🔴 死叉'
                        indicators.append(f"**MACD**: {macd_status}")

                    if 'rsi' in tech:
                        rsi_val = tech['rsi']['value']
                        rsi_emoji = '⚠️ 超买' if rsi_val > 70 else ('✅ 超卖' if rsi_val < 30 else '😊 正常')
                        indicators.append(f"**RSI**: {rsi_val:.1f} ({rsi_emoji})")

                    if 'kdj' in tech:
                        kdj = tech['kdj']
                        kdj_signal = '✅' if kdj['signal'] == 'golden_cross' else '🔴'
                        indicators.append(f"**KDJ**: K={kdj['k']:.1f}, D={kdj['d']:.1f}, J={kdj['j']:.1f} {kdj_signal}")

                    if 'boll' in tech:
                        boll = tech['boll']
                        boll_pos_pct = boll['position'] * 100
                        boll_status = '⚠️ 接近上轨' if boll['status'] == 'near_upper' else ('✅ 接近下轨' if boll['status'] == 'near_lower' else '😊 中轨区域')
                        indicators.append(f"**布林带**: {boll_pos_pct:.0f}% ({boll_status})")

                    if 'dmi_adx' in tech:
                        dmi = tech['dmi_adx']
                        trend_emoji = '🔥' if dmi['trend'] == 'strong' else ('📊' if dmi['trend'] == 'medium' else '💤')
                        direction_emoji = '📈' if dmi['direction'] == 'bullish' else '📉'
                        indicators.append(f"**DMI/ADX**: {dmi['adx']:.1f} ({dmi['trend']} {trend_emoji}, {direction_emoji})")

                    for indicator in indicators:
                        lines.append(f"- {indicator}")
                    lines.append("")

                # 3.5 估值分析(维度4,仅A股指数)
                valuation = data.get('valuation', {})
                if valuation and valuation.get('available'):
                    lines.append("#### 估值分析 (A股专属)")

                    # PE/PB估值表格
                    current_pe = valuation.get('current_pe', 0) or 0
                    current_pb = valuation.get('current_pb', 0) or 0
                    pe_percentiles = valuation.get('pe_percentiles', {})
                    pb_percentiles = valuation.get('pb_percentiles', {})

                    if current_pe > 0 and pe_percentiles:
                        lines.append("")
                        lines.append("**PE估值**:")
                        lines.append(f"- **当前PE**: {current_pe:.2f}")
                        lines.append("- **历史分位**:")
                        for period_name, data in pe_percentiles.items():
                            if isinstance(data, dict):
                                pct = data.get('percentile', 0) / 100
                                level = data.get('level', '')
                                lines.append(f"  - {period_name}: {pct:.1%} ({level})")
                            else:
                                lines.append(f"  - {period_name}: {data:.1%}")

                    if current_pb > 0 and pb_percentiles:
                        lines.append("")
                        lines.append("**PB估值**:")
                        lines.append(f"- **当前PB**: {current_pb:.2f}")
                        lines.append("- **历史分位**:")
                        for period_name, data in pb_percentiles.items():
                            if isinstance(data, dict):
                                pct = data.get('percentile', 0) / 100
                                level = data.get('level', '')
                                lines.append(f"  - {period_name}: {pct:.1%} ({level})")
                            else:
                                lines.append(f"  - {period_name}: {data:.1%}")

                    # 估值水平
                    val_level = valuation.get('valuation_level', {})
                    if val_level:
                        pe_level = val_level.get('pe_level', {})
                        if pe_level:
                            level_desc = pe_level.get('level', '合理')
                            emoji = pe_level.get('emoji', '➡️')
                            lines.append(f"\n**估值水平**: {level_desc} {emoji}")

                    # ERP
                    erp = valuation.get('erp', {})
                    if erp and erp.get('available'):
                        erp_value = erp.get('erp_value', 0)
                        erp_pct = erp_value * 100
                        signal = erp.get('signal', {})
                        if signal:
                            erp_desc = signal.get('description', '')
                            lines.append(f"**股债收益比(ERP)**: {erp_pct:+.2f}% ({erp_desc})")

                    lines.append("")

                # 3.7 资金面分析(仅A股/港股指数)
                capital = data.get('capital_flow', {})
                if capital and 'error' not in capital and capital.get('type'):
                    lines.append("#### 资金面分析")
                    flow_type = '北向资金(外资)' if capital['type'] == 'northbound' else '南向资金(内地)'
                    lines.append(f"**{flow_type}**:")
                    lines.append(f"- **近5日累计**: {capital['recent_5d_flow']:.2f} 亿元")
                    lines.append(f"- **流向状态**: {capital['status']}")
                    lines.append(f"- **情绪评分**: {capital['sentiment_score']}/100")

                    # 融资融券数据(仅A股)
                    margin = capital.get('margin_trading', {})
                    if margin and margin.get('available'):
                        lines.append("")
                        lines.append("**融资融券(杠杆指标)**:")
                        lines.append(f"- **数据日期**: {margin.get('latest_date', 'N/A')}")

                        balance_billion = margin.get('margin_balance', 0) / 1e8
                        lines.append(f"- **融资余额**: {balance_billion:.2f} 亿元")

                        change_1d = margin.get('margin_change_1d', 0)
                        change_5d = margin.get('margin_change_5d', 0)
                        change_20d = margin.get('margin_change_20d', 0)
                        lines.append(f"- **单日变化**: {change_1d:+.2f}%")
                        lines.append(f"- **5日变化**: {change_5d:+.2f}%")
                        lines.append(f"- **20日变化**: {change_20d:+.2f}%")

                        trend = margin.get('trend', '未知')
                        trend_emoji = '📈' if trend == '上升' else ('📉' if trend == '下降' else '➡️')
                        lines.append(f"- **趋势**: {trend} {trend_emoji}")

                        percentile = margin.get('percentile', 50)
                        lines.append(f"- **历史分位**: {percentile:.1f}%")

                        sentiment = margin.get('sentiment', '未知')
                        sentiment_score = margin.get('sentiment_score', 50)
                        signal = margin.get('signal', '观望')
                        lines.append(f"- **市场情绪**: {sentiment} ({sentiment_score}/100)")
                        lines.append(f"- **交易信号**: {signal}")

                    lines.append("")

                # 5. 成交量分析
                volume = data.get('volume_analysis', {})
                if volume and 'error' not in volume:
                    lines.append("#### 成交量分析")

                    obv = volume.get('obv', {})
                    if obv and 'trend' in obv:
                        trend_emoji = '📈' if obv['trend'] == 'uptrend' else ('📉' if obv['trend'] == 'downtrend' else '➡️')
                        lines.append(f"- **OBV趋势**: {obv['trend']} {trend_emoji}")

                    volume_ratio = volume.get('volume_ratio', {})
                    if volume_ratio and 'current' in volume_ratio:
                        ratio = volume_ratio['current']
                        ratio_emoji = '🔥' if ratio > 2 else ('📊' if ratio > 1 else '💤')
                        lines.append(f"- **量比**: {ratio:.2f} {ratio_emoji}")
                    lines.append("")

                # 6. 支撑压力位
                sr = data.get('support_resistance', {})
                if sr and 'error' not in sr:
                    lines.append("#### 支撑压力位")

                    pivot = sr.get('pivot_points', {})
                    if pivot:
                        lines.append("| 类型 | 点位 |")
                        lines.append("|------|------|")
                        if 'r1' in pivot:
                            lines.append(f"| 压力1 | {pivot['r1']:.2f} |")
                        if 'pivot' in pivot:
                            lines.append(f"| 轴心 | {pivot['pivot']:.2f} |")
                        if 's1' in pivot:
                            lines.append(f"| 支撑1 | {pivot['s1']:.2f} |")
                    lines.append("")

                # 7. 市场宽度(仅A股)
                breadth = data.get('market_breadth', {})
                if breadth and 'error' not in breadth:
                    lines.append("#### 市场宽度 (A股专属)")

                    new_hl = breadth.get('new_high_low', {})
                    if new_hl:
                        lines.append(f"- **创新高数**: {new_hl.get('new_high_count', 0)}")
                        lines.append(f"- **创新低数**: {new_hl.get('new_low_count', 0)}")

                    strength = breadth.get('strength_score', 0)
                    if strength:
                        strength_emoji = '💪' if strength > 0.7 else ('😊' if strength > 0.3 else '😰')
                        lines.append(f"- **市场强度**: {strength:.2f} {strength_emoji}")
                    lines.append("")

                # 6. 综合市场情绪(所有资产)
                sentiment = data.get('market_sentiment', {})
                if sentiment and 'error' not in sentiment:
                    lines.append("#### 综合市场情绪")
                    lines.append(f"- **情绪评分**: {sentiment['sentiment_score']:.1f}/100 {sentiment.get('emoji', '😐')}")
                    lines.append(f"- **情绪等级**: {sentiment.get('rating', '中性')}")
                    if sentiment.get('suggestion'):
                        lines.append(f"- **操作建议**: {sentiment['suggestion']}")
                    lines.append("")

                # 7. 专属恐慌指数(美股VIX/港股VHSI/A股CNVI/港股HKVI)
                panic = data.get('panic_index', {})
                if panic and 'error' not in panic:
                    panic_type = panic.get('type', '')
                    lines.append(f"#### 恐慌指数 ({panic_type})")

                    if panic.get('note'):
                        lines.append(f"*{panic['note']}*")
                        lines.append("")

                    if panic_type == 'VIX':
                        state = panic.get('current_state', {})
                        if state:
                            vix_val = state.get('vix_value', 0)
                            status = state.get('status', '')
                            status_emoji = '😱' if vix_val > 30 else ('⚠️' if vix_val > 20 else '😊')
                            lines.append(f"- **VIX值**: {vix_val:.2f} ({status}) {status_emoji}")

                        signal = panic.get('signal', {})
                        if signal and 'action' in signal:
                            lines.append(f"- **操作建议**: {signal['action']}")

                    elif panic_type == 'VHSI':
                        vhsi_val = panic.get('current_vhsi', 0)
                        panic_level = panic.get('panic_level', '')
                        vhsi_emoji = '😱' if vhsi_val > 30 else ('⚠️' if vhsi_val > 20 else '😊')
                        lines.append(f"- **VHSI值**: {vhsi_val:.2f} ({panic_level}) {vhsi_emoji}")

                        if panic.get('signal'):
                            lines.append(f"- **信号**: {panic['signal']}")

                    elif panic_type in ['CNVI', 'HKVI']:
                        # A股CNVI或港股HKVI
                        index_val = panic.get('index_value', 0)
                        status = panic.get('status', '')
                        emoji = panic.get('emoji', '😊')
                        lines.append(f"- **指数值**: {index_val:.2f} ({status}) {emoji}")

                        signal = panic.get('signal', {})
                        if signal and signal.get('action'):
                            lines.append(f"- **操作建议**: {signal['action']}")

                    lines.append("")

                lines.append("---")
                lines.append("")

        lines.append("## 报告信息")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**生成系统**: Claude Code 量化分析系统")
        lines.append(f"**分析维度**: 11大维度 (历史点位、技术面、资金面、估值、情绪、风险、综合判断、成交量、支撑压力位、市场宽度、恐慌指数)")
        lines.append("")

        return '\n'.join(lines)


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("测试综合资产分析系统...\n")

    reporter = ComprehensiveAssetReporter()
    report = reporter.generate_comprehensive_report()

    text_report = reporter.format_text_report(report)
    print(text_report)

    # 生成并保存Markdown报告
    markdown_report = reporter.format_markdown_report(report)
    md_path = '/tmp/comprehensive_asset_report.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_report)

    print(f"\n✅ 测试完成")
    print(f"📄 Markdown报告已保存至: {md_path}")
