#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量价关系增强分析器
Volume-Price Relationship Analyzer

分析量价配合、量价背离、量价齐升/齐跌等关系
评估量价协同度,生成操作建议

作者: Claude Code
日期: 2025-11-13
版本: v1.0
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class VolumePriceAnalyzer:
    """
    量价关系增强分析器

    功能:
    1. 检测量价背离(顶背离/底背离)
    2. 分析量价配合(价涨量增/价跌量缩等)
    3. 计算量价关系评分
    4. 生成量价关系操作建议
    5. OBV背离检测
    6. 换手率和量比分析
    """

    def __init__(self):
        """初始化量价关系分析器"""
        logger.info("量价关系增强分析器初始化完成")

    def detect_obv_divergence(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        检测OBV背离

        OBV (On Balance Volume) 能量潮背离检测:
        - 顶背离: 价格创新高,但OBV未创新高 → 看跌信号
        - 底背离: 价格创新低,但OBV未创新低 → 看涨信号

        Args:
            df: OHLCV数据,必须包含 close, volume 列
            lookback: 回溯周期

        Returns:
            OBV背离检测结果
        """
        if df.empty or len(df) < lookback + 5:
            return {
                'obv_trend': '数据不足',
                'top_divergence': False,
                'bottom_divergence': False,
                'has_divergence': False,
                'divergence_desc': '数据不足,无法检测OBV背离'
            }

        try:
            recent_df = df.tail(lookback + 5).copy()

            # 计算OBV
            price_direction = recent_df['close'].diff()
            obv = pd.Series(index=recent_df.index, dtype=float)
            obv.iloc[0] = recent_df['volume'].iloc[0]

            for i in range(1, len(recent_df)):
                if price_direction.iloc[i] > 0:
                    obv.iloc[i] = obv.iloc[i-1] + recent_df['volume'].iloc[i]
                elif price_direction.iloc[i] < 0:
                    obv.iloc[i] = obv.iloc[i-1] - recent_df['volume'].iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i-1]

            # OBV趋势判断
            obv_ma = obv.rolling(10).mean()
            obv_latest = obv.iloc[-1]
            obv_ma_latest = obv_ma.iloc[-1]

            if obv_latest > obv_ma_latest * 1.05:
                obv_trend = "上升"
            elif obv_latest < obv_ma_latest * 0.95:
                obv_trend = "下降"
            else:
                obv_trend = "平稳"

            # 寻找价格和OBV的峰值/谷值
            price_peaks = self._find_peaks(recent_df['close'].values)
            price_troughs = self._find_troughs(recent_df['close'].values)
            obv_peaks = self._find_peaks(obv.values)
            obv_troughs = self._find_troughs(obv.values)

            # 检测顶背离
            top_divergence = False
            if len(price_peaks) >= 2 and len(obv_peaks) >= 2:
                last_price_peaks = sorted(price_peaks[-2:])
                last_obv_peaks = sorted(obv_peaks[-2:])

                # 价格创新高但OBV未创新高
                if (recent_df['close'].iloc[last_price_peaks[-1]] >
                    recent_df['close'].iloc[last_price_peaks[0]]):
                    if obv.iloc[last_obv_peaks[-1]] < obv.iloc[last_obv_peaks[0]]:
                        top_divergence = True

            # 检测底背离
            bottom_divergence = False
            if len(price_troughs) >= 2 and len(obv_troughs) >= 2:
                last_price_troughs = sorted(price_troughs[-2:])
                last_obv_troughs = sorted(obv_troughs[-2:])

                # 价格创新低但OBV未创新低
                if (recent_df['close'].iloc[last_price_troughs[-1]] <
                    recent_df['close'].iloc[last_price_troughs[0]]):
                    if obv.iloc[last_obv_troughs[-1]] > obv.iloc[last_obv_troughs[0]]:
                        bottom_divergence = True

            # 生成描述
            if top_divergence:
                divergence_desc = "价格创新高但OBV未新高,顶背离看跌"
            elif bottom_divergence:
                divergence_desc = "价格创新低但OBV未新低,底背离看涨"
            else:
                divergence_desc = "无OBV背离"

            return {
                'obv_trend': obv_trend,
                'obv_latest': float(obv_latest),
                'top_divergence': top_divergence,
                'bottom_divergence': bottom_divergence,
                'has_divergence': top_divergence or bottom_divergence,
                'divergence_desc': divergence_desc
            }

        except Exception as e:
            logger.error(f"OBV背离检测失败: {str(e)}")
            return {
                'obv_trend': '分析失败',
                'top_divergence': False,
                'bottom_divergence': False,
                'has_divergence': False,
                'divergence_desc': f'分析失败: {str(e)}'
            }

    def get_turnover_rate(self, symbol: str) -> Optional[float]:
        """
        获取A股换手率

        Args:
            symbol: 股票代码 (如 '512880', '300803')

        Returns:
            换手率(小数形式,如0.025表示2.5%),非A股返回None
        """
        try:
            import akshare as ak

            # 清理代码格式
            code = symbol.replace('.SS', '').replace('.SZ', '').replace('.HK', '')

            # 只支持A股
            if len(code) != 6 or not code.isdigit():
                return None

            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            row = df[df['代码'] == code]

            if not row.empty:
                turnover_rate = row['换手率'].values[0]
                return float(turnover_rate) / 100  # 转为小数

            return None

        except Exception as e:
            logger.debug(f"获取换手率失败 {symbol}: {str(e)}")
            return None

    def analyze_turnover_and_volume_ratio(
        self,
        df: pd.DataFrame,
        symbol: str = None
    ) -> Dict:
        """
        分析换手率和量比

        Args:
            df: OHLCV数据
            symbol: 股票代码(用于获取实时换手率)

        Returns:
            换手率和量比分析结果
        """
        result = {
            'turnover_rate': None,
            'turnover_level': 'N/A',
            'volume_ratio': 1.0,
            'volume_ratio_level': '正常',
            'signal': '中性',
            'description': ''
        }

        try:
            # 1. 获取换手率(仅A股)
            if symbol:
                turnover = self.get_turnover_rate(symbol)
                if turnover is not None:
                    result['turnover_rate'] = turnover

                    # 换手率水平判断
                    if turnover >= 0.10:
                        result['turnover_level'] = '极高'
                    elif turnover >= 0.05:
                        result['turnover_level'] = '高'
                    elif turnover >= 0.02:
                        result['turnover_level'] = '中等'
                    elif turnover >= 0.01:
                        result['turnover_level'] = '偏低'
                    else:
                        result['turnover_level'] = '低'

            # 2. 计算量比
            if not df.empty and 'volume' in df.columns and len(df) >= 5:
                latest_volume = df['volume'].iloc[-1]
                avg_volume_5d = df['volume'].tail(5).mean()

                if avg_volume_5d > 0:
                    volume_ratio = latest_volume / avg_volume_5d
                    result['volume_ratio'] = float(volume_ratio)

                    # 量比水平判断
                    if volume_ratio >= 3.0:
                        result['volume_ratio_level'] = '巨量'
                    elif volume_ratio >= 2.0:
                        result['volume_ratio_level'] = '显著放量'
                    elif volume_ratio >= 1.5:
                        result['volume_ratio_level'] = '放量'
                    elif volume_ratio >= 0.8:
                        result['volume_ratio_level'] = '正常'
                    elif volume_ratio >= 0.5:
                        result['volume_ratio_level'] = '缩量'
                    else:
                        result['volume_ratio_level'] = '极度缩量'

            # 3. 综合信号判断
            turnover_level = result['turnover_level']
            vr_level = result['volume_ratio_level']

            if vr_level in ['巨量', '显著放量'] and turnover_level in ['极高', '高']:
                result['signal'] = '异常活跃'
                result['description'] = f"换手率{result['turnover_rate']*100:.1f}%,量比{result['volume_ratio']:.1f},交易异常活跃,关注变盘"
            elif vr_level in ['巨量', '显著放量', '放量']:
                result['signal'] = '放量'
                result['description'] = f"量比{result['volume_ratio']:.1f},成交放量,关注价格方向"
            elif vr_level in ['缩量', '极度缩量']:
                result['signal'] = '缩量'
                result['description'] = f"量比{result['volume_ratio']:.1f},成交缩量,观望为主"
            else:
                result['signal'] = '正常'
                if result['turnover_rate']:
                    result['description'] = f"换手率{result['turnover_rate']*100:.1f}%,量比{result['volume_ratio']:.1f},交易正常"
                else:
                    result['description'] = f"量比{result['volume_ratio']:.1f},交易正常"

            return result

        except Exception as e:
            logger.error(f"换手率和量比分析失败: {str(e)}")
            result['description'] = f'分析失败: {str(e)}'
            return result

    def analyze_volume_price_relationship(
        self,
        df: pd.DataFrame,
        lookback: int = 20
    ) -> Dict:
        """
        完整的量价关系分析

        Args:
            df: OHLCV数据,必须包含 close, volume 列
            lookback: 回溯周期,默认20日

        Returns:
            量价关系分析结果
        """
        if df.empty or len(df) < lookback:
            return {'error': '数据不足,无法进行量价分析'}

        try:
            result = {
                'cooperation': self.analyze_cooperation(df, lookback),
                'divergence': self.detect_divergence(df, lookback),
                'volume_features': self.analyze_volume_features(df, lookback),
                'vp_score': 0,
                'signal': '',
                'description': ''
            }

            # 计算量价关系评分
            score = self._calculate_vp_score(result)
            result['vp_score'] = score

            # 生成操作信号
            signal_info = self._generate_vp_signal(score, result)
            result['signal'] = signal_info['signal']
            result['description'] = signal_info['description']

            return result

        except Exception as e:
            logger.error(f"量价关系分析失败: {str(e)}")
            return {'error': str(e)}

    def analyze_cooperation(self, df: pd.DataFrame, lookback: int = 5) -> Dict:
        """
        分析量价配合关系

        Args:
            df: OHLCV数据
            lookback: 回溯周期

        Returns:
            量价配合分析结果
        """
        if df.empty or len(df) < lookback + 1:
            return {}

        # 取最近N天的数据
        recent_df = df.tail(lookback + 1).copy()

        # 计算价格和成交量变化
        recent_df['price_change'] = recent_df['close'].diff()
        recent_df['volume_change'] = recent_df['volume'].diff()

        # 统计各类量价关系
        relations = []
        for i in range(1, len(recent_df)):
            price_chg = recent_df['price_change'].iloc[i]
            volume_chg = recent_df['volume_change'].iloc[i]

            # 判断量价关系
            if price_chg > 0 and volume_chg > 0:
                relation = "价涨量增"
                quality = "健康"
                score = 10
            elif price_chg > 0 and volume_chg < 0:
                relation = "价涨量缩"
                quality = "乏力"
                score = -5
            elif price_chg < 0 and volume_chg > 0:
                relation = "价跌量增"
                quality = "恐慌"
                score = -10
            elif price_chg < 0 and volume_chg < 0:
                relation = "价跌量缩"
                quality = "企稳"
                score = 5
            else:
                relation = "价平量平"
                quality = "观望"
                score = 0

            relations.append({
                'date': recent_df.index[i].strftime('%Y-%m-%d') if hasattr(recent_df.index[i], 'strftime') else str(recent_df.index[i]),
                'price_change': float(price_chg),
                'volume_change': float(volume_chg),
                'relation': relation,
                'quality': quality,
                'score': score
            })

        # 统计量价关系分布
        quality_counts = {}
        total_score = 0
        for rel in relations:
            quality = rel['quality']
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
            total_score += rel['score']

        # 判断整体量价配合状态
        healthy_count = quality_counts.get('健康', 0)
        weak_count = quality_counts.get('乏力', 0)
        panic_count = quality_counts.get('恐慌', 0)
        stable_count = quality_counts.get('企稳', 0)

        if healthy_count >= lookback * 0.6:
            overall_status = "量价齐升"
            overall_quality = "优秀"
            description = "量价配合良好,价涨量增,上涨健康"
        elif weak_count >= lookback * 0.5:
            overall_status = "量价背离"
            overall_quality = "偏弱"
            description = "价涨量缩,上涨乏力,警惕回调"
        elif panic_count >= lookback * 0.5:
            overall_status = "量价齐跌"
            overall_quality = "极弱"
            description = "价跌量增,恐慌性抛售,继续观望"
        elif stable_count >= lookback * 0.5:
            overall_status = "缩量筑底"
            overall_quality = "偏强"
            description = "价跌量缩,抛压减轻,可能企稳"
        else:
            overall_status = "震荡"
            overall_quality = "中性"
            description = "量价关系不明确,处于震荡状态"

        # 计算量价协同度 (0-100)
        cooperation_degree = max(0, min(100, 50 + total_score))

        return {
            'recent_relations': relations,
            'overall_status': overall_status,
            'overall_quality': overall_quality,
            'quality_distribution': quality_counts,
            'cooperation_degree': int(cooperation_degree),
            'description': description
        }

    def detect_divergence(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        检测量价背离

        Args:
            df: OHLCV数据
            lookback: 回溯周期

        Returns:
            量价背离检测结果
        """
        if df.empty or len(df) < lookback + 10:
            return {}

        recent_df = df.tail(lookback + 10).copy()

        # 计算价格和成交量的移动平均
        recent_df['price_ma'] = recent_df['close'].rolling(5).mean()
        recent_df['volume_ma'] = recent_df['volume'].rolling(5).mean()

        # 寻找价格高点和低点
        price_peaks = self._find_peaks(recent_df['close'].values)
        price_troughs = self._find_troughs(recent_df['close'].values)

        # 寻找成交量高点和低点
        volume_peaks = self._find_peaks(recent_df['volume'].values)
        volume_troughs = self._find_troughs(recent_df['volume'].values)

        # 检测顶背离 (价格新高,成交量不再新高)
        top_divergence = False
        top_divergence_desc = ""
        if len(price_peaks) >= 2:
            last_price_peaks = sorted(price_peaks[-2:])
            if recent_df['close'].iloc[last_price_peaks[-1]] > recent_df['close'].iloc[last_price_peaks[0]]:
                # 价格创新高
                if len(volume_peaks) >= 2:
                    last_volume_peaks = sorted(volume_peaks[-2:])
                    if recent_df['volume'].iloc[last_volume_peaks[-1]] < recent_df['volume'].iloc[last_volume_peaks[0]]:
                        # 成交量未创新高
                        top_divergence = True
                        top_divergence_desc = "价格创新高但成交量萎缩,存在顶背离,警惕回调"

        # 检测底背离 (价格新低,成交量不再新低)
        bottom_divergence = False
        bottom_divergence_desc = ""
        if len(price_troughs) >= 2:
            last_price_troughs = sorted(price_troughs[-2:])
            if recent_df['close'].iloc[last_price_troughs[-1]] < recent_df['close'].iloc[last_price_troughs[0]]:
                # 价格创新低
                if len(volume_troughs) >= 2:
                    last_volume_troughs = sorted(volume_troughs[-2:])
                    if recent_df['volume'].iloc[last_volume_troughs[-1]] < recent_df['volume'].iloc[last_volume_troughs[0]]:
                        # 成交量未创新低(即成交量增加)
                        bottom_divergence = True
                        bottom_divergence_desc = "价格创新低但成交量未萎缩,存在底背离,可能反弹"

        return {
            'top_divergence': top_divergence,
            'top_divergence_desc': top_divergence_desc if top_divergence else "无顶背离",
            'bottom_divergence': bottom_divergence,
            'bottom_divergence_desc': bottom_divergence_desc if bottom_divergence else "无底背离",
            'has_divergence': top_divergence or bottom_divergence
        }

    def analyze_volume_features(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        分析成交量特征

        Args:
            df: OHLCV数据
            lookback: 回溯周期

        Returns:
            成交量特征分析
        """
        if df.empty or len(df) < lookback:
            return {}

        recent_df = df.tail(lookback)

        # 计算均量
        volume_ma_5 = recent_df['volume'].tail(5).mean()
        volume_ma_20 = recent_df['volume'].tail(20).mean()

        latest_volume = recent_df['volume'].iloc[-1]

        # 相对均量比值
        volume_ratio_5d = latest_volume / volume_ma_5 if volume_ma_5 > 0 else 1.0
        volume_ratio_20d = latest_volume / volume_ma_20 if volume_ma_20 > 0 else 1.0

        # 判断放量/缩量
        if volume_ratio_5d > 2.0:
            volume_status = "极度放量"
            volume_desc = f"成交量是5日均量的{volume_ratio_5d:.1f}倍,极度放量"
        elif volume_ratio_5d > 1.5:
            volume_status = "显著放量"
            volume_desc = f"成交量是5日均量的{volume_ratio_5d:.1f}倍,显著放量"
        elif volume_ratio_5d > 1.2:
            volume_status = "温和放量"
            volume_desc = f"成交量略高于5日均量({volume_ratio_5d:.1f}倍)"
        elif volume_ratio_5d > 0.8:
            volume_status = "正常"
            volume_desc = "成交量正常"
        elif volume_ratio_5d > 0.5:
            volume_status = "温和缩量"
            volume_desc = f"成交量低于5日均量({volume_ratio_5d:.1f}倍)"
        else:
            volume_status = "极度缩量"
            volume_desc = f"成交量极度萎缩({volume_ratio_5d:.1f}倍)"

        # 判断量能趋势
        if volume_ma_5 > volume_ma_20 * 1.1:
            volume_trend = "放大"
        elif volume_ma_5 < volume_ma_20 * 0.9:
            volume_trend = "萎缩"
        else:
            volume_trend = "平稳"

        return {
            'latest_volume': float(latest_volume),
            'volume_ma_5': float(volume_ma_5),
            'volume_ma_20': float(volume_ma_20),
            'volume_ratio_5d': float(volume_ratio_5d),
            'volume_ratio_20d': float(volume_ratio_20d),
            'volume_status': volume_status,
            'volume_trend': volume_trend,
            'description': volume_desc
        }

    def _find_peaks(self, data: np.ndarray, order: int = 3) -> List[int]:
        """
        寻找峰值点

        Args:
            data: 数据数组
            order: 邻域大小

        Returns:
            峰值点索引列表
        """
        peaks = []
        for i in range(order, len(data) - order):
            if all(data[i] > data[i-j] for j in range(1, order+1)) and \
               all(data[i] > data[i+j] for j in range(1, order+1)):
                peaks.append(i)
        return peaks

    def _find_troughs(self, data: np.ndarray, order: int = 3) -> List[int]:
        """
        寻找谷值点

        Args:
            data: 数据数组
            order: 邻域大小

        Returns:
            谷值点索引列表
        """
        troughs = []
        for i in range(order, len(data) - order):
            if all(data[i] < data[i-j] for j in range(1, order+1)) and \
               all(data[i] < data[i+j] for j in range(1, order+1)):
                troughs.append(i)
        return troughs

    def _calculate_vp_score(self, result: Dict) -> int:
        """
        计算量价关系评分 (0-100)

        评分逻辑:
        - 量价协同度: 50%权重
        - 无背离: +20分
        - 顶背离: -20分
        - 底背离: +10分
        - 放量配合: +10分

        Returns:
            量价关系评分(0-100)
        """
        score = 0

        # 1. 量价协同度 (0-50分)
        cooperation = result.get('cooperation', {})
        cooperation_degree = cooperation.get('cooperation_degree', 50)
        score += cooperation_degree * 0.5

        # 2. 背离检测 (±20分)
        divergence = result.get('divergence', {})
        if divergence.get('top_divergence', False):
            score -= 20  # 顶背离扣分
        elif divergence.get('bottom_divergence', False):
            score += 10  # 底背离加分
        else:
            score += 20  # 无背离加分

        # 3. 成交量配合 (±10分)
        volume_features = result.get('volume_features', {})
        volume_status = volume_features.get('volume_status', '正常')
        overall_quality = cooperation.get('overall_quality', '中性')

        if volume_status in ['显著放量', '极度放量'] and overall_quality == '优秀':
            score += 10  # 放量上涨加分
        elif volume_status in ['显著放量', '极度放量'] and overall_quality == '极弱':
            score -= 10  # 放量下跌扣分

        # 确保分数在0-100之间
        score = max(0, min(100, score))

        return int(score)

    def _generate_vp_signal(self, score: int, result: Dict) -> Dict:
        """
        生成量价关系操作信号

        Args:
            score: 量价关系评分
            result: 分析结果

        Returns:
            操作信号和描述
        """
        cooperation = result.get('cooperation', {})
        divergence = result.get('divergence', {})
        volume_features = result.get('volume_features', {})

        # 根据评分生成信号
        if score >= 80:
            signal = "强烈买入"
            description = "量价配合极佳,量价齐升,可积极配置"
        elif score >= 65:
            signal = "买入"
            description = "量价配合良好,价涨量增,可正常配置"
        elif score >= 50:
            signal = "中性偏多"
            description = "量价关系尚可,可小仓位参与"
        elif score >= 35:
            signal = "观望"
            description = "量价配合一般,建议观望为主"
        elif score >= 20:
            signal = "减仓"
            description = "量价背离,上涨乏力,建议减仓"
        else:
            signal = "清仓"
            description = "量价严重背离,建议清仓规避"

        # 结合背离情况调整
        if divergence.get('top_divergence', False):
            description += ",存在顶背离,警惕回调风险"
        elif divergence.get('bottom_divergence', False):
            description += ",存在底背离,关注反弹机会"

        return {
            'signal': signal,
            'description': description
        }


def test_volume_price_analyzer():
    """测试量价关系分析器"""
    print("=" * 80)
    print("量价关系增强分析器测试")
    print("=" * 80)

    # 创建模拟数据
    dates = pd.date_range(start='2025-10-01', periods=30, freq='D')

    # 场景1: 量价齐升
    prices1 = np.linspace(100, 120, 30) + np.random.randn(30) * 2
    volumes1 = np.linspace(1000000, 1500000, 30) + np.random.randn(30) * 100000

    df1 = pd.DataFrame({
        'close': prices1,
        'volume': volumes1
    }, index=dates)

    analyzer = VolumePriceAnalyzer()

    print("\n测试场景1: 量价齐升")
    result1 = analyzer.analyze_volume_price_relationship(df1, lookback=20)

    if 'error' not in result1:
        print(f"量价配合状态: {result1['cooperation']['overall_status']}")
        print(f"量价协同度: {result1['cooperation']['cooperation_degree']}/100")
        print(f"顶背离: {'是' if result1['divergence']['top_divergence'] else '否'}")
        print(f"底背离: {'是' if result1['divergence']['bottom_divergence'] else '否'}")
        print(f"成交量状态: {result1['volume_features']['volume_status']}")
        print(f"量价评分: {result1['vp_score']}/100")
        print(f"操作信号: {result1['signal']}")
        print(f"操作建议: {result1['description']}")
    else:
        print(f"分析失败: {result1['error']}")

    print("\n" + "=" * 80)

    # 场景2: 量价背离
    prices2 = np.linspace(100, 120, 30) + np.random.randn(30) * 2
    volumes2 = np.linspace(1500000, 1000000, 30) + np.random.randn(30) * 100000

    df2 = pd.DataFrame({
        'close': prices2,
        'volume': volumes2
    }, index=dates)

    print("\n测试场景2: 价涨量缩(量价背离)")
    result2 = analyzer.analyze_volume_price_relationship(df2, lookback=20)

    if 'error' not in result2:
        print(f"量价配合状态: {result2['cooperation']['overall_status']}")
        print(f"量价协同度: {result2['cooperation']['cooperation_degree']}/100")
        print(f"成交量趋势: {result2['volume_features']['volume_trend']}")
        print(f"量价评分: {result2['vp_score']}/100")
        print(f"操作信号: {result2['signal']}")
        print(f"操作建议: {result2['description']}")
    else:
        print(f"分析失败: {result2['error']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    test_volume_price_analyzer()
