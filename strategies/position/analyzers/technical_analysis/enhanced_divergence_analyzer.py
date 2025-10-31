#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强量价背离分析器
Enhanced Divergence Analyzer

整合量价背离、MACD背驰、RSI背离，提供综合判断

功能：
1. 综合量价背离检测
2. 背离强度评分
3. 风险等级判断
4. 操作建议生成

作者: Claude Code
日期: 2025-10-31
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

# 导入现有分析器
try:
    from .volume_analyzer import VolumeAnalyzer
    from .divergence_analyzer import DivergenceAnalyzer
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    from strategies.position.analyzers.technical_analysis.volume_analyzer import VolumeAnalyzer
    from strategies.position.analyzers.technical_analysis.divergence_analyzer import DivergenceAnalyzer

logger = logging.getLogger(__name__)


class EnhancedDivergenceAnalyzer:
    """
    增强量价背离分析器

    整合多个技术指标的背离分析，提供综合判断
    """

    def __init__(self):
        """初始化增强背离分析器"""
        self.volume_analyzer = VolumeAnalyzer()
        self.divergence_analyzer = DivergenceAnalyzer()
        self.logger = logging.getLogger(__name__)

    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        完整量价背离分析

        Args:
            df: OHLCV数据，需包含 close, volume 列

        Returns:
            {
                'divergence_type': str,      # 'top' / 'bottom' / 'none'
                'strength': int,             # 强度评分 0-100
                'risk_level': str,           # 'high' / 'medium' / 'low'
                'signals': List[Dict],       # 背离信号列表
                'recommendation': str,       # 操作建议
                'confidence': float,         # 置信度 0-1
                'summary': str              # 摘要
            }
        """
        try:
            # 数据验证
            if df.empty or len(df) < 20:
                return {'error': '数据不足'}

            if 'close' not in df.columns or 'volume' not in df.columns:
                return {'error': '缺少必需列'}

            # 1. 量价关系分析
            volume_result = self.volume_analyzer.analyze_volume(df, periods=20)

            # 2. 技术指标背离分析
            divergence_result = self.divergence_analyzer.comprehensive_analysis(df)

            # 3. 综合判断
            synthesis = self._synthesize_signals(volume_result, divergence_result, df)

            # 4. 生成建议
            recommendation = self._generate_recommendation(synthesis)

            result = {
                'divergence_type': synthesis['divergence_type'],
                'strength': synthesis['strength'],
                'risk_level': synthesis['risk_level'],
                'signals': synthesis['signals'],
                'recommendation': recommendation,
                'confidence': synthesis['confidence'],
                'summary': self._generate_summary(synthesis, recommendation)
            }

            return result

        except Exception as e:
            self.logger.error(f"增强背离分析失败: {str(e)}")
            return {'error': str(e)}

    def _synthesize_signals(
        self,
        volume_result: Dict,
        divergence_result: Dict,
        df: pd.DataFrame
    ) -> Dict:
        """
        综合分析各类信号

        Returns:
            {
                'divergence_type': str,
                'strength': int,
                'risk_level': str,
                'signals': List[Dict],
                'confidence': float
            }
        """
        signals = []
        total_strength = 0
        signal_count = 0

        # 1. 分析量价关系
        if 'price_volume_relation' in volume_result:
            pv_signal = self._analyze_price_volume_signal(
                volume_result['price_volume_relation']
            )
            if pv_signal:
                signals.append(pv_signal)
                total_strength += pv_signal['strength']
                signal_count += 1

        # 2. 分析MACD背离
        if 'macd_divergence' in divergence_result and divergence_result['macd_divergence']:
            macd_div = divergence_result['macd_divergence']
            if macd_div.get('has_divergence'):
                signal = {
                    'type': 'MACD背离',
                    'divergence_type': macd_div.get('divergence_type', 'unknown'),
                    'strength': macd_div.get('strength', 50),
                    'description': f"MACD{macd_div.get('divergence_type', '')}背离",
                    'risk_level': 'medium'
                }
                signals.append(signal)
                total_strength += signal['strength']
                signal_count += 1

        # 3. 分析RSI背离
        if 'rsi_divergence' in divergence_result and divergence_result['rsi_divergence']:
            rsi_div = divergence_result['rsi_divergence']
            if rsi_div.get('has_divergence'):
                signal = {
                    'type': 'RSI背离',
                    'divergence_type': rsi_div.get('divergence_type', 'unknown'),
                    'strength': rsi_div.get('strength', 50),
                    'description': f"RSI{rsi_div.get('divergence_type', '')}背离",
                    'risk_level': 'medium'
                }
                signals.append(signal)
                total_strength += signal['strength']
                signal_count += 1

        # 4. 综合判断背离类型
        divergence_type = self._determine_overall_divergence_type(signals)

        # 5. 计算综合强度
        if signal_count > 0:
            avg_strength = total_strength / signal_count
            # 如果多个信号都指向同一方向，增强强度
            if len(signals) >= 2:
                same_direction = all(
                    s.get('divergence_type') == divergence_type
                    for s in signals if 'divergence_type' in s
                )
                if same_direction:
                    avg_strength = min(avg_strength * 1.3, 100)
        else:
            avg_strength = 0

        # 6. 判断风险等级
        risk_level = self._determine_risk_level(divergence_type, avg_strength)

        # 7. 计算置信度
        confidence = self._calculate_confidence(signals, avg_strength)

        return {
            'divergence_type': divergence_type,
            'strength': int(avg_strength),
            'risk_level': risk_level,
            'signals': signals,
            'confidence': round(confidence, 2)
        }

    def _analyze_price_volume_signal(self, pv_relations: List[Dict]) -> Optional[Dict]:
        """
        分析量价关系信号

        重点关注：
        - 价涨量缩：见顶信号
        - 价跌量增：恐慌信号

        Returns:
            信号字典或None
        """
        if not pv_relations:
            return None

        # 统计最近的量价关系
        recent_relations = pv_relations[-5:]  # 最近5天

        # 统计各类关系出现次数
        relation_counts = {}
        for rel in recent_relations:
            relation_type = rel.get('relation', '')
            relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1

        # 判断是否形成背离
        if relation_counts.get('价涨量缩', 0) >= 3:
            return {
                'type': '价涨量缩',
                'divergence_type': 'top',
                'strength': 80,
                'description': '近期连续价涨量缩，上涨乏力，见顶信号',
                'risk_level': 'high'
            }

        elif relation_counts.get('价跌量增', 0) >= 3:
            return {
                'type': '价跌量增',
                'divergence_type': 'bottom',
                'strength': 70,
                'description': '近期连续价跌量增，恐慌性抛售，可能见底',
                'risk_level': 'medium'
            }

        elif relation_counts.get('价涨量增', 0) >= 4:
            return {
                'type': '价涨量增',
                'divergence_type': 'none',
                'strength': 0,
                'description': '量价配合良好，趋势健康',
                'risk_level': 'low'
            }

        return None

    def _determine_overall_divergence_type(self, signals: List[Dict]) -> str:
        """
        综合判断背离类型

        Returns:
            'top' / 'bottom' / 'none'
        """
        if not signals:
            return 'none'

        # 统计各类型背离数量
        top_count = sum(1 for s in signals if s.get('divergence_type') == 'top')
        bottom_count = sum(1 for s in signals if s.get('divergence_type') == 'bottom')

        if top_count > bottom_count and top_count >= 2:
            return 'top'
        elif bottom_count > top_count and bottom_count >= 2:
            return 'bottom'
        elif top_count >= 1 and bottom_count == 0:
            return 'top'
        elif bottom_count >= 1 and top_count == 0:
            return 'bottom'
        else:
            return 'none'

    def _determine_risk_level(self, divergence_type: str, strength: int) -> str:
        """
        判断风险等级

        Returns:
            'high' / 'medium' / 'low'
        """
        if divergence_type == 'none':
            return 'low'

        if divergence_type == 'top':
            # 顶背离表示见顶风险
            if strength > 70:
                return 'high'
            elif strength > 40:
                return 'medium'
            else:
                return 'low'

        elif divergence_type == 'bottom':
            # 底背离表示机会
            return 'low'

        return 'low'

    def _calculate_confidence(self, signals: List[Dict], strength: int) -> float:
        """
        计算置信度

        基于：
        1. 信号数量
        2. 信号强度
        3. 信号一致性

        Returns:
            置信度 0-1
        """
        if not signals:
            return 0.0

        # 基础置信度基于强度
        base_confidence = min(strength / 100, 1.0)

        # 信号数量加成
        signal_bonus = min(len(signals) * 0.15, 0.3)

        # 检查信号一致性
        divergence_types = [s.get('divergence_type') for s in signals if 'divergence_type' in s]
        if divergence_types:
            most_common = max(set(divergence_types), key=divergence_types.count)
            consistency = divergence_types.count(most_common) / len(divergence_types)
            consistency_bonus = consistency * 0.2
        else:
            consistency_bonus = 0

        confidence = min(base_confidence + signal_bonus + consistency_bonus, 1.0)

        return confidence

    def _generate_recommendation(self, synthesis: Dict) -> str:
        """
        生成操作建议

        Returns:
            建议文本
        """
        divergence_type = synthesis['divergence_type']
        strength = synthesis['strength']
        risk_level = synthesis['risk_level']

        if divergence_type == 'top':
            if risk_level == 'high':
                return "⚠️ 建议：强烈建议减仓，警惕短期回调风险"
            elif risk_level == 'medium':
                return "⚠️ 建议：注意减仓，控制仓位"
            else:
                return "建议：保持观望，注意风险"

        elif divergence_type == 'bottom':
            if strength > 70:
                return "✅ 建议：可考虑适当建仓，等待反弹"
            elif strength > 40:
                return "建议：观望为主，等待更明确信号"
            else:
                return "建议：继续观察"

        else:
            return "建议：量价配合正常，维持原策略"

    def _generate_summary(self, synthesis: Dict, recommendation: str) -> str:
        """
        生成分析摘要

        Returns:
            摘要文本
        """
        divergence_type = synthesis['divergence_type']
        strength = synthesis['strength']
        signals = synthesis['signals']
        confidence = synthesis['confidence']

        # 背离类型描述
        type_map = {
            'top': '顶背离',
            'bottom': '底背离',
            'none': '无明显背离'
        }
        type_desc = type_map.get(divergence_type, '未知')

        # 信号描述
        if signals:
            signal_desc = '、'.join([s.get('type', '') for s in signals[:3]])
        else:
            signal_desc = '无显著信号'

        # 强度描述
        if strength > 70:
            strength_desc = '强'
        elif strength > 40:
            strength_desc = '中等'
        else:
            strength_desc = '弱'

        summary = (
            f"{type_desc}（强度：{strength_desc} {strength}/100），"
            f"信号：{signal_desc}，"
            f"置信度：{confidence:.0%}"
        )

        return summary


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 创建测试数据（价涨量缩场景）
    dates = pd.date_range('2024-01-01', periods=60, freq='D')

    # 价格上涨
    prices = 100 + np.arange(60) * 2 + np.random.randn(60) * 5

    # 成交量下降（价涨量缩）
    volumes = 10000000 - np.arange(60) * 100000 + np.random.randint(-1000000, 1000000, 60)

    df = pd.DataFrame({
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'volume': volumes
    }, index=dates)

    # 测试
    analyzer = EnhancedDivergenceAnalyzer()
    result = analyzer.analyze(df)

    print("\n=== 增强量价背离分析结果 ===")
    print(f"背离类型: {result['divergence_type']}")
    print(f"强度: {result['strength']}/100")
    print(f"风险等级: {result['risk_level']}")
    print(f"置信度: {result['confidence']:.0%}")
    print(f"建议: {result['recommendation']}")
    print(f"摘要: {result['summary']}")
    print(f"\n信号详情:")
    for sig in result['signals']:
        print(f"  - {sig['type']}: {sig['description']}")
