#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四指标共振信号生成器
基于MACD、RSI、KDJ、MA的组合买卖信号

策略口诀: "先定方向(MACD)，再选时机(KDJ/RSI)，始终管风险(ATR)"
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from .technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class ResonanceSignalGenerator:
    """四指标共振信号生成器"""

    def __init__(self):
        """初始化信号生成器"""
        self.indicator_calculator = TechnicalIndicators()

    def generate_buy_signal(self, df: pd.DataFrame, index: int = -1) -> Dict:
        """
        生成买入信号

        买入条件(四指标共振):
        1. MA: 股价突破5日/10日均线，呈多头排列
        2. MACD: 零轴下方金叉，红柱扩大
        3. KDJ: 低位金叉，J线突破向上
        4. RSI: 从超卖区(<30)反弹，突破50确认

        Args:
            df: 包含技术指标的DataFrame
            index: 要分析的行索引

        Returns:
            {
                'signal': 'STRONG_BUY' / 'BUY' / 'WEAK_BUY' / 'NEUTRAL',
                'score': 0-100的评分,
                'reasons': 买入理由列表,
                'confidence': 置信度 0-1
            }
        """
        if index < 0:
            index = len(df) + index

        # 获取各指标信号
        ma_signal = self.indicator_calculator.identify_ma_pattern(df, index)
        macd_signal = self.indicator_calculator.identify_macd_signal(df, index)
        rsi_signal = self.indicator_calculator.identify_rsi_signal(df, index)
        kdj_signal = self.indicator_calculator.identify_kdj_signal(df, index)

        # 计算综合评分
        score = 0
        reasons = []
        resonance_count = 0  # 共振数量

        # 1. MA指标评分(权重25%)
        ma_score = ma_signal['strength'] * 2.5
        score += ma_score

        if ma_signal['pattern'] in ['完美多头排列', '多头排列(价格回调)']:
            reasons.append(f"✅ MA: {ma_signal['pattern']}")
            resonance_count += 1
        else:
            reasons.append(f"⚠️  MA: {ma_signal['pattern']}")

        # 2. MACD指标评分(权重30%)
        macd_score = macd_signal['strength'] * 3.0
        score += macd_score

        if macd_signal['signal'] in ['金叉', '多头']:
            reasons.append(f"✅ MACD: {macd_signal['signal']} - {macd_signal['position']}")
            resonance_count += 1
            # 零轴下方金叉更有效
            if macd_signal['position'] == '零轴下方' and macd_signal['signal'] == '金叉':
                score += 5  # 加分
                reasons[-1] += " (强势信号)"
        else:
            reasons.append(f"⚠️  MACD: {macd_signal['signal']}")

        # 3. KDJ指标评分(权重25%)
        kdj_score = kdj_signal['strength'] * 2.5
        score += kdj_score

        if kdj_signal['signal'] in ['低位金叉', '超卖', '多头']:
            reasons.append(f"✅ KDJ: {kdj_signal['signal']} (K:{kdj_signal['k']:.1f}, D:{kdj_signal['d']:.1f})")
            resonance_count += 1
            # 低位金叉最强
            if kdj_signal['signal'] == '低位金叉':
                score += 5  # 加分
        else:
            reasons.append(f"⚠️  KDJ: {kdj_signal['signal']}")

        # 4. RSI指标评分(权重20%)
        rsi_score = rsi_signal['strength'] * 2.0
        score += rsi_score

        if rsi_signal['signal'] in ['超卖', '中性偏多'] or (rsi_signal['value'] > 50 and rsi_signal['trend'] == '上升'):
            reasons.append(f"✅ RSI: {rsi_signal['signal']} ({rsi_signal['value']:.1f})")
            resonance_count += 1
        else:
            reasons.append(f"⚠️  RSI: {rsi_signal['signal']} ({rsi_signal['value']:.1f})")

        # 共振加成: 4个指标同时看多，额外加分
        if resonance_count == 4:
            score += 10
            reasons.insert(0, "🎯 四指标完美共振!")

        # 计算置信度
        confidence = min(1.0, score / 100)

        # 判断信号强度
        if score >= 85 and resonance_count >= 3:
            signal = 'STRONG_BUY'
        elif score >= 70 and resonance_count >= 2:
            signal = 'BUY'
        elif score >= 55:
            signal = 'WEAK_BUY'
        else:
            signal = 'NEUTRAL'

        return {
            'signal': signal,
            'score': round(score, 2),
            'resonance_count': resonance_count,
            'reasons': reasons,
            'confidence': round(confidence, 2),
            'details': {
                'ma': ma_signal,
                'macd': macd_signal,
                'rsi': rsi_signal,
                'kdj': kdj_signal
            }
        }

    def generate_sell_signal(self, df: pd.DataFrame, index: int = -1) -> Dict:
        """
        生成卖出信号

        卖出条件(四指标共振):
        1. MA: 股价跌破5日/10日均线，空头排列
        2. MACD: 零轴上方死叉，绿柱扩大
        3. KDJ: 高位死叉，J线向下
        4. RSI: 进入超买区(>70)后回落，跌破50确认

        Args:
            df: 包含技术指标的DataFrame
            index: 要分析的行索引

        Returns:
            {
                'signal': 'STRONG_SELL' / 'SELL' / 'WEAK_SELL' / 'NEUTRAL',
                'score': 0-100的评分,
                'reasons': 卖出理由列表,
                'confidence': 置信度 0-1
            }
        """
        if index < 0:
            index = len(df) + index

        # 获取各指标信号
        ma_signal = self.indicator_calculator.identify_ma_pattern(df, index)
        macd_signal = self.indicator_calculator.identify_macd_signal(df, index)
        rsi_signal = self.indicator_calculator.identify_rsi_signal(df, index)
        kdj_signal = self.indicator_calculator.identify_kdj_signal(df, index)

        # 计算综合评分 (卖出信号越强，分数越高)
        score = 0
        reasons = []
        resonance_count = 0

        # 1. MA指标评分(权重25%)
        # 空头排列得高分
        ma_score = (10 - ma_signal['strength']) * 2.5
        score += ma_score

        if ma_signal['pattern'] in ['完美空头排列', '空头排列(价格反弹)']:
            reasons.append(f"✅ MA: {ma_signal['pattern']}")
            resonance_count += 1
        else:
            reasons.append(f"⚠️  MA: {ma_signal['pattern']}")

        # 2. MACD指标评分(权重30%)
        macd_score = (10 - macd_signal['strength']) * 3.0
        score += macd_score

        if macd_signal['signal'] in ['死叉', '空头']:
            reasons.append(f"✅ MACD: {macd_signal['signal']} - {macd_signal['position']}")
            resonance_count += 1
            # 零轴上方死叉更危险
            if macd_signal['position'] == '零轴上方' and macd_signal['signal'] == '死叉':
                score += 5
                reasons[-1] += " (高危信号)"
        else:
            reasons.append(f"⚠️  MACD: {macd_signal['signal']}")

        # 3. KDJ指标评分(权重25%)
        kdj_score = (10 - kdj_signal['strength']) * 2.5
        score += kdj_score

        if kdj_signal['signal'] in ['高位死叉', '超买', '空头']:
            reasons.append(f"✅ KDJ: {kdj_signal['signal']} (K:{kdj_signal['k']:.1f}, D:{kdj_signal['d']:.1f})")
            resonance_count += 1
            if kdj_signal['signal'] == '高位死叉':
                score += 5
        else:
            reasons.append(f"⚠️  KDJ: {kdj_signal['signal']}")

        # 4. RSI指标评分(权重20%)
        rsi_score = (10 - rsi_signal['strength']) * 2.0
        score += rsi_score

        if rsi_signal['signal'] in ['超买', '中性偏空'] or (rsi_signal['value'] < 50 and rsi_signal['trend'] == '下降'):
            reasons.append(f"✅ RSI: {rsi_signal['signal']} ({rsi_signal['value']:.1f})")
            resonance_count += 1
        else:
            reasons.append(f"⚠️  RSI: {rsi_signal['signal']} ({rsi_signal['value']:.1f})")

        # 共振加成
        if resonance_count == 4:
            score += 10
            reasons.insert(0, "🎯 四指标完美共振!")

        # 计算置信度
        confidence = min(1.0, score / 100)

        # 判断信号强度
        if score >= 85 and resonance_count >= 3:
            signal = 'STRONG_SELL'
        elif score >= 70 and resonance_count >= 2:
            signal = 'SELL'
        elif score >= 55:
            signal = 'WEAK_SELL'
        else:
            signal = 'NEUTRAL'

        return {
            'signal': signal,
            'score': round(score, 2),
            'resonance_count': resonance_count,
            'reasons': reasons,
            'confidence': round(confidence, 2),
            'details': {
                'ma': ma_signal,
                'macd': macd_signal,
                'rsi': rsi_signal,
                'kdj': kdj_signal
            }
        }

    def generate_trading_signal(self, df: pd.DataFrame, index: int = -1) -> Dict:
        """
        生成综合交易信号

        Args:
            df: 包含技术指标的DataFrame
            index: 要分析的行索引

        Returns:
            {
                'action': 'STRONG_BUY' / 'BUY' / 'HOLD' / 'SELL' / 'STRONG_SELL',
                'buy_score': 买入评分,
                'sell_score': 卖出评分,
                'confidence': 置信度,
                'suggestion': 操作建议,
                'reasons': 理由列表
            }
        """
        # 分别计算买入和卖出信号
        buy_signal = self.generate_buy_signal(df, index)
        sell_signal = self.generate_sell_signal(df, index)

        # 综合判断
        buy_score = buy_signal['score']
        sell_score = sell_signal['score']

        # 确定最终行动
        if buy_score >= 70 and buy_score > sell_score + 15:
            action = buy_signal['signal']
            confidence = buy_signal['confidence']
            reasons = buy_signal['reasons']
            suggestion = self._get_buy_suggestion(action, buy_score)
        elif sell_score >= 70 and sell_score > buy_score + 15:
            action = sell_signal['signal']
            confidence = sell_signal['confidence']
            reasons = sell_signal['reasons']
            suggestion = self._get_sell_suggestion(action, sell_score)
        else:
            action = 'HOLD'
            confidence = 0.5
            reasons = ['买卖信号不明确，建议观望']
            suggestion = '当前多空信号混杂，建议持币观望或持股不动，等待明确信号'

        return {
            'action': action,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'buy_resonance': buy_signal['resonance_count'],
            'sell_resonance': sell_signal['resonance_count'],
            'confidence': confidence,
            'suggestion': suggestion,
            'reasons': reasons,
            'buy_details': buy_signal,
            'sell_details': sell_signal
        }

    @staticmethod
    def _get_buy_suggestion(signal: str, score: float) -> str:
        """获取买入建议"""
        suggestions = {
            'STRONG_BUY': f'强烈买入信号(评分{score:.1f}/100)！四指标共振，可以积极建仓，建议仓位60-80%',
            'BUY': f'买入信号(评分{score:.1f}/100)，多个指标支持，可以适度买入，建议仓位40-60%',
            'WEAK_BUY': f'弱买入信号(评分{score:.1f}/100)，可以小仓位试探，建议仓位20-40%'
        }
        return suggestions.get(signal, '观望')

    @staticmethod
    def _get_sell_suggestion(signal: str, score: float) -> str:
        """获取卖出建议"""
        suggestions = {
            'STRONG_SELL': f'强烈卖出信号(评分{score:.1f}/100)！四指标共振，建议立即清仓或减至20%以下',
            'SELL': f'卖出信号(评分{score:.1f}/100)，多个指标转弱，建议减仓至40%以下',
            'WEAK_SELL': f'弱卖出信号(评分{score:.1f}/100)，可以考虑部分止盈，减仓至60%左右'
        }
        return suggestions.get(signal, '观望')

    def scan_signals_batch(self, df: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
        """
        批量扫描最近N天的交易信号

        Args:
            df: 包含技术指标的DataFrame
            lookback: 回溯天数

        Returns:
            包含信号的DataFrame
        """
        results = []

        for i in range(-lookback, 0):
            try:
                signal = self.generate_trading_signal(df, index=i)

                row_data = {
                    'date': df.iloc[i].get('date', i),
                    'close': df.iloc[i]['close'],
                    'action': signal['action'],
                    'buy_score': signal['buy_score'],
                    'sell_score': signal['sell_score'],
                    'confidence': signal['confidence'],
                    'buy_resonance': signal['buy_resonance'],
                    'sell_resonance': signal['sell_resonance']
                }

                results.append(row_data)

            except Exception as e:
                logger.warning(f"第{i}天信号计算失败: {str(e)}")
                continue

        return pd.DataFrame(results)

    def print_signal_report(self, signal: Dict, stock_name: str = "目标股票"):
        """
        打印格式化的信号报告

        Args:
            signal: generate_trading_signal返回的信号字典
            stock_name: 股票名称
        """
        print("=" * 70)
        print(f"📊 {stock_name} - 四指标共振交易信号报告")
        print("=" * 70)

        # 主信号
        action_emoji = {
            'STRONG_BUY': '🟢🟢🟢',
            'BUY': '🟢🟢',
            'WEAK_BUY': '🟢',
            'HOLD': '⚪',
            'WEAK_SELL': '🔴',
            'SELL': '🔴🔴',
            'STRONG_SELL': '🔴🔴🔴'
        }

        print(f"\n【交易信号】{action_emoji.get(signal['action'], '⚪')} {signal['action']}")
        print(f"【置信度】{'⭐' * int(signal['confidence'] * 5)} ({signal['confidence']*100:.0f}%)")
        print(f"\n【评分对比】")
        print(f"  买入评分: {signal['buy_score']:.1f}/100 (共振: {signal['buy_resonance']}/4)")
        print(f"  卖出评分: {signal['sell_score']:.1f}/100 (共振: {signal['sell_resonance']}/4)")

        print(f"\n【操作建议】")
        print(f"  {signal['suggestion']}")

        print(f"\n【详细理由】")
        for reason in signal['reasons']:
            print(f"  {reason}")

        print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    # 测试代码
    import akshare as ak
    from technical_indicators import TechnicalIndicators

    print("=" * 70)
    print("四指标共振信号生成器 - 测试")
    print("=" * 70)

    # 获取测试数据
    print("\n1. 获取上证指数数据...")
    df = ak.stock_zh_index_daily(symbol='sh000001')
    df = df.tail(100)

    # 计算技术指标
    print("2. 计算技术指标...")
    calculator = TechnicalIndicators()
    df = calculator.calculate_all_indicators(df)

    # 生成信号
    print("3. 生成交易信号...\n")
    generator = ResonanceSignalGenerator()

    # 当前信号
    current_signal = generator.generate_trading_signal(df)
    generator.print_signal_report(current_signal, "上证指数")

    # 批量扫描最近5天
    print("\n4. 扫描最近5天的信号...")
    batch_signals = generator.scan_signals_batch(df, lookback=5)
    print(batch_signals.to_string())
