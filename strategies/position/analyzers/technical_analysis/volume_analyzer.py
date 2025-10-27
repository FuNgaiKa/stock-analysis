#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成交量分析器 - Phase 3
分析量价关系,检测成交量异常,计算OBV等指标
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class VolumeAnalyzer:
    """
    成交量分析器

    分析成交量特征,识别量价配合度,检测异常放量/缩量
    """

    def __init__(self):
        """初始化成交量分析器"""
        pass

    def analyze_volume(self, df: pd.DataFrame, periods: int = 20) -> Dict:
        """
        完整成交量分析

        Args:
            df: OHLCV数据
            periods: 分析周期(默认20日)

        Returns:
            成交量分析结果
        """
        if df.empty or 'volume' not in df.columns or len(df) < periods:
            return {'error': '数据不足或缺少成交量数据'}

        try:
            result = {
                'price_volume_relation': self.analyze_price_volume_relationship(df),
                'volume_status': self.detect_volume_anomaly(df, periods),
                'obv': self.calculate_obv(df),
                'signal': self.generate_volume_signal(df, periods)
            }

            return result

        except Exception as e:
            logger.error(f"成交量分析失败: {str(e)}")
            return {'error': str(e)}

    def analyze_price_volume_relationship(self, df: pd.DataFrame, lookback: int = 5) -> Dict:
        """
        分析近期量价关系

        Args:
            df: OHLCV数据
            lookback: 回看周期

        Returns:
            量价关系字典
        """
        if df.empty or len(df) < lookback + 1:
            return {}

        # 取最近N天的数据
        recent_df = df.tail(lookback + 1)

        relations = []
        for i in range(1, len(recent_df)):
            prev = recent_df.iloc[i-1]
            curr = recent_df.iloc[i]

            price_change = curr['close'] - prev['close']
            volume_change = curr['volume'] - prev['volume']

            # 判断量价关系
            if price_change > 0 and volume_change > 0:
                relation = "价涨量增"
                quality = "健康"
            elif price_change > 0 and volume_change < 0:
                relation = "价涨量缩"
                quality = "乏力"
            elif price_change < 0 and volume_change > 0:
                relation = "价跌量增"
                quality = "恐慌"
            elif price_change < 0 and volume_change < 0:
                relation = "价跌量缩"
                quality = "企稳"
            else:
                relation = "价平量平"
                quality = "观望"

            relations.append({
                'date': recent_df.index[i].strftime('%Y-%m-%d'),
                'price_change': float(price_change),
                'volume_change': float(volume_change),
                'relation': relation,
                'quality': quality
            })

        # 统计最近的量价关系
        quality_counts = {}
        for rel in relations:
            quality = rel['quality']
            quality_counts[quality] = quality_counts.get(quality, 0) + 1

        # 判断整体趋势
        if quality_counts.get('健康', 0) >= lookback * 0.6:
            overall = "量价配合良好,上涨健康"
        elif quality_counts.get('乏力', 0) >= lookback * 0.5:
            overall = "价涨量缩,上涨乏力,警惕回调"
        elif quality_counts.get('恐慌', 0) >= lookback * 0.5:
            overall = "价跌量增,恐慌性抛售"
        elif quality_counts.get('企稳', 0) >= lookback * 0.5:
            overall = "价跌量缩,抛压减轻,可能企稳"
        else:
            overall = "量价关系正常"

        return {
            'recent_relations': relations,
            'overall_assessment': overall,
            'quality_distribution': quality_counts
        }

    def detect_volume_anomaly(self, df: pd.DataFrame, periods: int = 20) -> Dict:
        """
        检测成交量异常

        Args:
            df: OHLCV数据
            periods: 计算均量的周期

        Returns:
            成交量状态字典
        """
        if df.empty or 'volume' not in df.columns or len(df) < periods:
            return {}

        # 计算成交量均值
        volume_ma = df['volume'].rolling(periods).mean()

        latest_volume = df['volume'].iloc[-1]
        avg_volume = volume_ma.iloc[-1]

        volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1.0

        # 计算成交量分位数
        percentile = (df['volume'].tail(periods * 2) < latest_volume).sum() / min(periods * 2, len(df)) * 100

        # 判断成交量状态
        if volume_ratio > 2.0:
            status = "极度放量"
            description = f"成交量是均量的{volume_ratio:.1f}倍,可能有重大消息"
            signal_type = "强"
        elif volume_ratio > 1.5:
            status = "显著放量"
            description = f"成交量是均量的{volume_ratio:.1f}倍,关注突破"
            signal_type = "中"
        elif volume_ratio > 1.2:
            status = "温和放量"
            description = f"成交量略高于均量({volume_ratio:.1f}倍)"
            signal_type = "弱"
        elif volume_ratio > 0.8:
            status = "正常"
            description = "成交量正常"
            signal_type = "中性"
        elif volume_ratio > 0.5:
            status = "温和缩量"
            description = f"成交量低于均量({volume_ratio:.1f}倍)"
            signal_type = "弱"
        else:
            status = "极度缩量"
            description = f"成交量极度萎缩({volume_ratio:.1f}倍),市场观望"
            signal_type = "强"

        return {
            'status': status,
            'description': description,
            'signal_type': signal_type,
            'latest_volume': float(latest_volume),
            'average_volume': float(avg_volume),
            'volume_ratio': float(volume_ratio),
            'percentile': float(percentile)
        }

    def calculate_obv(self, df: pd.DataFrame) -> Dict:
        """
        计算OBV (On Balance Volume) 能量潮指标

        OBV原理:
        - 价格上涨日: OBV += 成交量
        - 价格下跌日: OBV -= 成交量
        - OBV上升: 多头力量占优
        - OBV下降: 空头力量占优

        Args:
            df: OHLCV数据

        Returns:
            OBV分析字典
        """
        if df.empty or 'volume' not in df.columns or len(df) < 2:
            return {}

        # 计算价格变化方向
        price_direction = df['close'].diff()

        # 计算OBV
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df['volume'].iloc[0]

        for i in range(1, len(df)):
            if price_direction.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif price_direction.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]

        # OBV趋势判断
        if len(obv) >= 20:
            obv_ma = obv.rolling(20).mean()
            obv_latest = obv.iloc[-1]
            obv_ma_latest = obv_ma.iloc[-1]

            if obv_latest > obv_ma_latest * 1.05:
                trend = "上升"
                description = "OBV高于均线,多头力量占优"
            elif obv_latest < obv_ma_latest * 0.95:
                trend = "下降"
                description = "OBV低于均线,空头力量占优"
            else:
                trend = "平稳"
                description = "OBV围绕均线波动"

            # 计算OBV变化率
            if len(obv) >= 21:
                obv_change = (obv.iloc[-1] - obv.iloc[-21]) / abs(obv.iloc[-21]) * 100 if obv.iloc[-21] != 0 else 0
            else:
                obv_change = 0
        else:
            trend = "数据不足"
            description = "OBV历史数据不足"
            obv_change = 0

        return {
            'latest_obv': float(obv.iloc[-1]),
            'trend': trend,
            'description': description,
            'obv_20d_change_pct': float(obv_change)
        }

    def generate_volume_signal(self, df: pd.DataFrame, periods: int = 20) -> Dict:
        """
        生成成交量交易信号

        Args:
            df: OHLCV数据
            periods: 分析周期

        Returns:
            交易信号字典
        """
        if df.empty or len(df) < periods:
            return {}

        # 获取各项分析结果
        pv_relation = self.analyze_price_volume_relationship(df, lookback=5)
        volume_status = self.detect_volume_anomaly(df, periods)
        obv_info = self.calculate_obv(df)

        # 综合判断
        recent_relations = pv_relation.get('recent_relations', [])
        latest_relation = recent_relations[-1] if recent_relations else {}

        volume_ratio = volume_status.get('volume_ratio', 1.0)
        obv_trend = obv_info.get('trend', '平稳')

        # 生成信号
        signals = []

        # 1. 放量突破信号
        if volume_ratio > 1.5 and latest_relation.get('quality') == '健康':
            signals.append("放量突破,多头力量强")

        # 2. 缩量整理信号
        if volume_ratio < 0.7 and latest_relation.get('price_change', 0) >= 0:
            signals.append("缩量整理,等待方向选择")

        # 3. 量价背离信号
        if volume_ratio < 0.8 and latest_relation.get('quality') == '乏力':
            signals.append("量价背离,警惕回调")

        # 4. OBV信号
        if obv_trend == "上升":
            signals.append("OBV上升,资金流入")
        elif obv_trend == "下降":
            signals.append("OBV下降,资金流出")

        # 综合信号
        if not signals:
            overall_signal = "中性"
            description = "成交量表现正常,无明显信号"
        elif any("放量突破" in s for s in signals):
            overall_signal = "积极"
            description = "成交量支持上涨,可跟进"
        elif any("背离" in s or "流出" in s for s in signals):
            overall_signal = "谨慎"
            description = "成交量显示风险,建议观望"
        else:
            overall_signal = "中性偏多"
            description = "成交量配合尚可"

        return {
            'signal': overall_signal,
            'description': description,
            'signals': signals,
            'latest_relation': latest_relation.get('relation', 'N/A')
        }


def test_volume_analyzer():
    """测试成交量分析器"""
    print("=" * 80)
    print("成交量分析器测试")
    print("=" * 80)

    from src.data_sources.us_stock_source import USStockDataSource

    # 获取标普500数据
    data_source = USStockDataSource()
    df = data_source.get_us_index_daily('SPX', period="3mo")

    if df.empty:
        print("数据获取失败")
        return

    # 创建分析器
    analyzer = VolumeAnalyzer()

    # 完整成交量分析
    print("\n测试成交量分析...")
    result = analyzer.analyze_volume(df, periods=20)

    if 'error' not in result:
        # 量价关系
        pv_rel = result.get('price_volume_relation', {})
        if pv_rel:
            print(f"\n量价关系:")
            print(f"  整体评估: {pv_rel.get('overall_assessment', 'N/A')}")

            recent = pv_rel.get('recent_relations', [])
            if recent:
                print(f"  最近5日:")
                for rel in recent[-5:]:
                    print(f"    {rel['date']}: {rel['relation']} ({rel['quality']})")

        # 成交量状态
        vol_status = result.get('volume_status', {})
        if vol_status:
            print(f"\n成交量状态:")
            print(f"  状态: {vol_status.get('status', 'N/A')}")
            print(f"  描述: {vol_status.get('description', 'N/A')}")
            print(f"  量比: {vol_status.get('volume_ratio', 0):.2f}")

        # OBV
        obv = result.get('obv', {})
        if obv:
            print(f"\nOBV能量潮:")
            print(f"  趋势: {obv.get('trend', 'N/A')}")
            print(f"  描述: {obv.get('description', 'N/A')}")
            print(f"  20日变化: {obv.get('obv_20d_change_pct', 0):+.2f}%")

        # 交易信号
        signal = result.get('signal', {})
        if signal:
            print(f"\n交易信号:")
            print(f"  综合信号: {signal.get('signal', 'N/A')}")
            print(f"  描述: {signal.get('description', 'N/A')}")
            signals = signal.get('signals', [])
            if signals:
                print(f"  具体信号:")
                for s in signals:
                    print(f"    - {s}")

    else:
        print(f"\n分析失败: {result.get('error', '未知错误')}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    test_volume_analyzer()
