"""
SKEW指数分析器 (尾部风险指数)
用于预警极端市场风险(黑天鹅事件)
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SKEWAnalyzer:
    """SKEW指数分析器 - 黑天鹅风险预警"""

    def __init__(self):
        """初始化SKEW分析器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 5分钟缓存

        # SKEW关键阈值
        self.high_risk_threshold = 145  # 高风险阈值
        self.normal_threshold = 120     # 正常阈值

    def get_skew_data(self, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        获取SKEW指数历史数据

        Args:
            period: 时间周期 (默认1年)

        Returns:
            SKEW数据DataFrame
        """
        cache_key = f"skew_{period}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info("使用缓存的SKEW数据")
                return self.cache[cache_key]

        try:
            # 获取SKEW指数
            ticker = yf.Ticker("^SKEW")
            df = ticker.history(period=period)

            if df.empty:
                logger.warning("获取SKEW数据为空")
                return None

            # 缓存
            self.cache[cache_key] = df
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"获取SKEW数据成功: {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"获取SKEW数据失败: {str(e)}")
            return None

    def analyze_skew(self, period: str = "1y") -> Dict[str, Any]:
        """
        分析SKEW指数

        Args:
            period: 分析周期

        Returns:
            SKEW分析结果
        """
        df = self.get_skew_data(period)

        if df is None or df.empty:
            return {'error': '无法获取SKEW数据'}

        try:
            # 当前SKEW值
            current_skew = float(df['Close'].iloc[-1])

            # 历史统计
            avg_skew = float(df['Close'].mean())
            median_skew = float(df['Close'].median())
            std_skew = float(df['Close'].std())
            max_skew = float(df['Close'].max())
            min_skew = float(df['Close'].min())

            # 分位数
            skew_percentile = float((df['Close'] <= current_skew).sum() / len(df) * 100)

            # 趋势分析
            recent_5d_avg = float(df['Close'].tail(5).mean())
            recent_20d_avg = float(df['Close'].tail(20).mean()) if len(df) >= 20 else avg_skew
            trend = 'rising' if recent_5d_avg > recent_20d_avg * 1.02 else (
                'falling' if recent_5d_avg < recent_20d_avg * 0.98 else 'stable'
            )

            # 风险等级
            risk_level = self._classify_risk(current_skew)

            # 与历史极值比较
            distance_to_high = current_skew - self.high_risk_threshold
            is_extreme = current_skew > self.high_risk_threshold

            # Z-Score
            zscore = (current_skew - avg_skew) / std_skew if std_skew > 0 else 0

            result = {
                'current_skew': current_skew,
                'avg_skew': avg_skew,
                'median_skew': median_skew,
                'std_skew': std_skew,
                'max_skew': max_skew,
                'min_skew': min_skew,
                'skew_percentile': skew_percentile,
                'risk_level': risk_level,
                'trend': trend,
                'recent_5d_avg': recent_5d_avg,
                'recent_20d_avg': recent_20d_avg,
                'is_extreme_risk': is_extreme,
                'distance_to_high_risk': distance_to_high,
                'zscore': zscore,
                'signal': self._generate_signal(current_skew, trend, is_extreme),
                'interpretation': self._generate_interpretation(
                    current_skew, risk_level, trend, skew_percentile
                ),
                'risk_alert': self._generate_risk_alert(current_skew, trend, zscore)
            }

            return result

        except Exception as e:
            logger.error(f"分析SKEW失败: {str(e)}")
            return {'error': str(e)}

    def _classify_risk(self, skew: float) -> str:
        """风险等级分类"""
        if skew > 150:
            return '极高风险'
        elif skew > 145:
            return '高风险'
        elif skew > 135:
            return '中高风险'
        elif skew > 120:
            return '正常'
        else:
            return '低风险'

    def _generate_signal(self, current_skew: float, trend: str, is_extreme: bool) -> str:
        """生成交易信号"""
        if is_extreme and trend == 'rising':
            return '强烈警告: 黑天鹅风险激增,建议大幅降低仓位'

        if current_skew > 145:
            return '警告: 尾部风险高,建议降低仓位或买入保护性看跌期权'

        if current_skew > 135 and trend == 'rising':
            return '谨慎: 尾部风险上升,关注风险事件'

        if current_skew < 120:
            return '低风险: 市场尾部风险低,可正常配置'

        return '中性: SKEW处于正常区间'

    def _generate_interpretation(
        self, current_skew: float, risk_level: str,
        trend: str, percentile: float
    ) -> str:
        """生成解读文本"""
        interpretation = []

        interpretation.append(f"当前SKEW指数{current_skew:.1f}")
        interpretation.append(f"风险等级: {risk_level}")

        if percentile > 80:
            interpretation.append(f"处于历史高位({percentile:.0f}%分位),尾部风险显著")
        elif percentile < 20:
            interpretation.append(f"处于历史低位({percentile:.0f}%分位),尾部风险较低")

        if trend == 'rising':
            interpretation.append("近期趋势上升,黑天鹅风险增加")
        elif trend == 'falling':
            interpretation.append("近期趋势下降,尾部风险缓解")

        return '; '.join(interpretation)

    def _generate_risk_alert(
        self, current_skew: float, trend: str, zscore: float
    ) -> Optional[str]:
        """生成风险提示"""
        alerts = []

        if current_skew > 150:
            alerts.append("⚠️⚠️⚠️ SKEW>150,黑天鹅风险极高,历史罕见")

        if current_skew > 145 and trend == 'rising':
            alerts.append("⚠️⚠️ SKEW>145且上升,极端下跌概率大幅增加")

        if zscore > 2:
            alerts.append("⚠️ SKEW异常偏高(>2σ),市场高度不安")

        if current_skew > 140 and trend == 'rising':
            alerts.append("建议: 增加对冲头寸或降低股票仓位")

        return ' | '.join(alerts) if alerts else None


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    analyzer = SKEWAnalyzer()

    print("=" * 80)
    print("SKEW指数分析器测试 (黑天鹅风险预警)")
    print("=" * 80)

    result = analyzer.analyze_skew(period="1y")

    if 'error' not in result:
        print(f"\n当前SKEW指数: {result['current_skew']:.2f}")
        print(f"历史均值: {result['avg_skew']:.2f}")
        print(f"风险等级: {result['risk_level']}")
        print(f"历史分位数: {result['skew_percentile']:.1f}%")
        print(f"趋势: {result['trend']}")
        print(f"是否极端风险: {'是' if result['is_extreme_risk'] else '否'}")
        print(f"\n交易信号: {result['signal']}")
        print(f"解读: {result['interpretation']}")
        if result['risk_alert']:
            print(f"\n风险提示: {result['risk_alert']}")
    else:
        print(f"分析失败: {result['error']}")

    print("\n" + "=" * 80)
