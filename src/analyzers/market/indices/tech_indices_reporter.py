#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四大科技指数综合分析报告生成器
Tech Indices Comprehensive Reporter

分析对象: 创业板指、科创50、恒生科技、纳斯达克
分析维度: 历史点位、技术面、资金面、估值、情绪、风险、综合判断

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

logger = logging.getLogger(__name__)


# 四大科技指数配置
TECH_INDICES = {
    'CYBZ': {'market': 'CN', 'name': '创业板指', 'code': 'CYBZ'},
    'KECHUANG50': {'market': 'CN', 'name': '科创50', 'code': 'KECHUANG50'},
    'HKTECH': {'market': 'HK', 'name': '恒生科技', 'code': 'HSTECH'},
    'NASDAQ': {'market': 'US', 'name': '纳斯达克', 'code': 'NASDAQ'}
}


class TechIndicesReporter:
    """四大科技指数综合分析报告生成器"""

    def __init__(self):
        """初始化分析器"""
        logger.info("初始化四大科技指数分析系统...")

        # 市场分析器
        self.cn_analyzer = CNMarketAnalyzer()
        self.hk_analyzer = HKMarketAnalyzer()
        self.us_analyzer = USMarketAnalyzer()

        # 技术分析器
        self.divergence_analyzer = DivergenceAnalyzer()

        # A股专项分析器
        self.cn_indicators = CNStockIndicators()
        self.hk_connect = HKConnectAnalyzer()

        logger.info("四大科技指数分析系统初始化完成")

    def analyze_single_tech_index(self, index_key: str) -> Dict:
        """
        综合分析单个科技指数

        Args:
            index_key: 指数代码(CYBZ/KECHUANG50/HKTECH/NASDAQ)

        Returns:
            完整分析结果
        """
        config = TECH_INDICES[index_key]
        logger.info(f"开始分析 {config['name']}...")

        result = {
            'index_key': index_key,
            'index_name': config['name'],
            'market': config['market'],
            'timestamp': datetime.now()
        }

        try:
            # 1. 历史点位分析
            result['historical_analysis'] = self._analyze_historical_position(
                config['market'], config['code']
            )

            # 2. 技术面分析
            result['technical_analysis'] = self._analyze_technical(
                config['market'], config['code']
            )

            # 3. 资金面分析(仅A股/港股)
            if config['market'] in ['CN', 'HK']:
                result['capital_flow'] = self._analyze_capital_flow(
                    config['market'], config['code']
                )

            # 4. 估值分析(如适用)
            result['valuation'] = self._analyze_valuation(
                config['market'], config['code']
            )

            # 5. 市场情绪(仅A股) - 暂时禁用
            # if config['market'] == 'CN':
            #     result['market_sentiment'] = self._analyze_sentiment()

            # 6. 风险评估
            result['risk_assessment'] = self._calculate_risk_score(result)

            # 7. 综合判断
            result['comprehensive_judgment'] = self._generate_judgment(result)

            logger.info(f"{config['name']} 分析完成")

        except Exception as e:
            logger.error(f"分析{config['name']}失败: {str(e)}")
            result['error'] = str(e)

        return result

    def _analyze_historical_position(self, market: str, code: str) -> Dict:
        """历史点位分析"""
        try:
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

    def _analyze_technical(self, market: str, code: str) -> Dict:
        """技术面分析"""
        try:
            # 获取指数数据
            if market == 'CN':
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
            # 计算价格在布林带中的位置 (0-1之间)
            boll_position = (df['close'] - boll_lower) / (boll_upper - boll_lower)

            # 计算ATR
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift(1))
            low_close = abs(df['low'] - df['close'].shift(1))
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean()

            # 计算DMI/ADX
            # +DM和-DM
            high_diff = df['high'].diff()
            low_diff = -df['low'].diff()
            plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
            minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

            # 平滑处理
            plus_dm_smooth = plus_dm.rolling(window=14).mean()
            minus_dm_smooth = minus_dm.rolling(window=14).mean()
            atr_smooth = true_range.rolling(window=14).mean()

            # +DI和-DI
            plus_di = 100 * plus_dm_smooth / atr_smooth
            minus_di = 100 * minus_dm_smooth / atr_smooth

            # DX和ADX
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
                    'position': float(boll_position.iloc[-1]),  # 0=下轨, 0.5=中轨, 1=上轨
                    'status': 'near_upper' if boll_position.iloc[-1] > 0.8 else ('near_lower' if boll_position.iloc[-1] < 0.2 else 'normal')
                },
                'atr': {
                    'value': float(atr.iloc[-1]),
                    'pct': float(atr.iloc[-1] / latest['close'] * 100)  # ATR占价格的百分比
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

    def _analyze_capital_flow(self, market: str, code: str) -> Dict:
        """资金面分析"""
        try:
            if market == 'CN':
                # 北向资金
                north_flow = self.hk_connect.comprehensive_analysis(direction='north')
                return {
                    'type': 'northbound',
                    'recent_5d_flow': north_flow.get('flow_analysis', {}).get('recent_5d', 0),
                    'status': north_flow.get('sentiment_analysis', {}).get('sentiment', '未知'),
                    'sentiment_score': north_flow.get('sentiment_analysis', {}).get('sentiment_score', 50)
                }
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
        """估值分析"""
        # 注: 指数级别的估值分析需要专门的数据源,这里先返回占位符
        # 后续可以集成 PE/PB 分位数数据
        return {
            'available': False,
            'note': 'PE/PB分位数分析需要专门数据源,待后续集成'
        }

    def _analyze_sentiment(self) -> Dict:
        """市场情绪分析(仅A股)"""
        try:
            # 获取涨跌停数据
            limit_up = self.cn_indicators.get_limit_up_count()
            limit_down = self.cn_indicators.get_limit_down_count()

            indicators = {
                'limit_up_count': limit_up,
                'limit_down_count': limit_down
            }

            return {
                'limit_up_count': limit_up,
                'limit_down_count': limit_down,
                'new_high_count': 0,  # 暂时禁用
                'new_low_count': 0,  # 暂时禁用
                'status': self._interpret_sentiment(indicators)
            }
        except Exception as e:
            logger.error(f"市场情绪分析失败: {str(e)}")
            return {'error': str(e)}

    def _interpret_sentiment(self, indicators: Dict) -> str:
        """解读市场情绪"""
        limit_up = indicators.get('limit_up_count', 0)

        if limit_up > 150:
            return '极度狂热🔥'
        elif limit_up > 100:
            return '高涨📈'
        elif limit_up > 50:
            return '良好😊'
        elif limit_up > 20:
            return '平淡😐'
        else:
            return '冷清😔'

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

            # MACD顶背离 (检查divergence summary列表)
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

            # 4. 市场情绪风险(权重20%,仅A股) - 暂时禁用
            # sentiment = result.get('market_sentiment', {})
            # if sentiment:
            #     limit_up = sentiment.get('limit_up_count', 0)
            #     if limit_up > 150:
            #         risk_score += 0.2
            #         risk_factors.append('涨停数>150只,情绪过热')
            #     elif limit_up > 100:
            #         risk_score += 0.1
            #         risk_factors.append('涨停数>100只,偏热')

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

    def _generate_judgment(self, result: Dict) -> Dict:
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

            # 基于技术面 - 检查MACD顶背离
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
        # 检查MACD顶背离
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
            ('MACD顶背离', has_macd_top_div),  # 使用前面计算的has_macd_top_div
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
        """生成四大科技指数综合报告"""
        logger.info("开始生成四大科技指数综合报告...")

        report = {
            'timestamp': datetime.now(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'indices': {}
        }

        # 分析四大指数
        for index_key in TECH_INDICES.keys():
            report['indices'][index_key] = self.analyze_single_tech_index(index_key)

        logger.info("四大科技指数综合报告生成完成")
        return report

    def format_text_report(self, report: Dict) -> str:
        """格式化为文本报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("四大科技指数综合分析报告")
        lines.append(f"分析时间: {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        for index_key, data in report['indices'].items():
            if 'error' in data:
                lines.append(f"\n【{data['index_name']}】分析失败: {data['error']}")
                continue

            lines.append(f"\n{'=' * 80}")
            lines.append(f"【{data['index_name']}】")
            lines.append('=' * 80)

            # 1. 当前点位
            hist = data.get('historical_analysis', {})
            if hist and 'current_price' in hist:
                lines.append(f"\n【当前点位】")
                lines.append(f"  最新价格: {hist['current_price']:.2f}")
                lines.append(f"  涨跌幅: {hist['current_change_pct']:+.2f}%")
                lines.append(f"  数据日期: {hist['current_date']}")

            # 2. 历史点位分析
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

            # 3. 技术面分析
            tech = data.get('technical_analysis', {})
            if tech and 'error' not in tech:
                lines.append(f"\n【技术面分析】")

                # MACD
                if 'macd' in tech:
                    macd_status = '金叉✅' if tech['macd']['status'] == 'golden_cross' else '死叉🔴'
                    lines.append(f"  MACD: {macd_status}")

                # RSI
                if 'rsi' in tech:
                    rsi_val = tech['rsi']['value']
                    rsi_status = tech['rsi']['status']
                    rsi_emoji = '⚠️' if rsi_status == 'overbought' else ('✅' if rsi_status == 'oversold' else '😊')
                    lines.append(f"  RSI: {rsi_val:.1f} {rsi_emoji}")

                # KDJ
                if 'kdj' in tech:
                    kdj = tech['kdj']
                    kdj_signal = '金叉✅' if kdj['signal'] == 'golden_cross' else '死叉🔴'
                    kdj_status_emoji = '⚠️' if kdj['status'] == 'overbought' else ('✅' if kdj['status'] == 'oversold' else '😊')
                    lines.append(f"  KDJ: K={kdj['k']:.1f}, D={kdj['d']:.1f}, J={kdj['j']:.1f} {kdj_signal} {kdj_status_emoji}")

                # 布林带
                if 'boll' in tech:
                    boll = tech['boll']
                    current_price = hist.get('current_price', 0)
                    boll_pos_pct = boll['position'] * 100
                    if boll['status'] == 'near_upper':
                        boll_emoji = '⚠️ 接近上轨'
                    elif boll['status'] == 'near_lower':
                        boll_emoji = '✅ 接近下轨'
                    else:
                        boll_emoji = '😊  中轨区域'
                    lines.append(f"  布林带: 上={boll['upper']:.2f}, 中={boll['mid']:.2f}, 下={boll['lower']:.2f}")
                    lines.append(f"         当前位置: {boll_pos_pct:.0f}% {boll_emoji}")

                # ATR (波动率)
                if 'atr' in tech:
                    atr = tech['atr']
                    lines.append(f"  ATR(波动率): {atr['value']:.2f} ({atr['pct']:.2f}%)")

                # DMI/ADX (趋势强度)
                if 'dmi_adx' in tech:
                    dmi = tech['dmi_adx']
                    trend_emoji = '🔥' if dmi['trend'] == 'strong' else ('📊' if dmi['trend'] == 'medium' else '💤')
                    direction_emoji = '📈' if dmi['direction'] == 'bullish' else '📉'
                    lines.append(f"  DMI/ADX: +DI={dmi['plus_di']:.1f}, -DI={dmi['minus_di']:.1f}, ADX={dmi['adx']:.1f}")
                    lines.append(f"          趋势强度: {dmi['trend']} {trend_emoji}, 方向: {direction_emoji}")

                # 均线
                if 'ma' in tech:
                    ma = tech['ma']
                    lines.append(f"  均线偏离:")
                    lines.append(f"    MA5: {ma['price_to_ma5_pct']:+.2f}%")
                    lines.append(f"    MA20: {ma['price_to_ma20_pct']:+.2f}%")
                    lines.append(f"    MA60: {ma['price_to_ma60_pct']:+.2f}%")

                # 背离
                if 'divergence' in tech and isinstance(tech['divergence'], dict):
                    div_summary = tech['divergence']
                    if div_summary and len(div_summary) > 0:
                        # summary是一个列表，包含所有背离信号
                        for sig in div_summary[:2]:  # 只显示前2个
                            if isinstance(sig, dict):
                                lines.append(f"  背离信号: {sig.get('type', '')} {sig.get('direction', '')} 🚨")

            # 4. 资金面分析
            capital = data.get('capital_flow', {})
            if capital and 'error' not in capital and capital.get('type'):
                lines.append(f"\n【资金面分析】")
                flow_type = '北向资金(外资)' if capital['type'] == 'northbound' else '南向资金(内地)'
                lines.append(f"  {flow_type}")
                lines.append(f"    近5日累计: {capital['recent_5d_flow']:.2f} 亿元")
                lines.append(f"    流向状态: {capital['status']}")
                lines.append(f"    情绪评分: {capital['sentiment_score']}/100")

            # 5. 市场情绪(仅A股)
            sentiment = data.get('market_sentiment', {})
            if sentiment and 'error' not in sentiment:
                lines.append(f"\n【市场情绪】(A股整体)")
                lines.append(f"  涨停数: {sentiment['limit_up_count']} 只")
                lines.append(f"  跌停数: {sentiment['limit_down_count']} 只")
                lines.append(f"  市场状态: {sentiment['status']}")

            # 6. 风险评估
            risk = data.get('risk_assessment', {})
            if risk:
                lines.append(f"\n【风险评估】")
                lines.append(f"  综合风险: {risk['risk_score']:.2f} ({risk['risk_level']})")
                if risk.get('risk_factors'):
                    lines.append(f"  风险因素:")
                    for factor in risk['risk_factors']:
                        lines.append(f"    • {factor}")

            # 7. 综合判断
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

        lines.append("\n" + "=" * 80)
        lines.append("由 Claude Code 量化分析系统生成")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        return '\n'.join(lines)


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("测试四大科技指数综合分析系统...\n")

    reporter = TechIndicesReporter()
    report = reporter.generate_comprehensive_report()

    text_report = reporter.format_text_report(report)
    print(text_report)

    print("\n✅ 测试完成")
