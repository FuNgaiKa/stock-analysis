"""
美元指数(DXY)分析器
用于跨资产配置和大宗商品定价参考
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DXYAnalyzer:
    """美元指数分析器"""

    def __init__(self):
        """初始化DXY分析器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 5分钟缓存

        # 美元指数关键阈值(基于历史经验)
        self.strong_threshold = 105  # 强势美元
        self.normal_high = 100       # 正常偏高
        self.normal_low = 95         # 正常偏低
        self.weak_threshold = 90     # 弱势美元

    def get_dxy_data(self, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        获取美元指数历史数据

        Args:
            period: 时间周期

        Returns:
            DXY数据DataFrame
        """
        cache_key = f"dxy_{period}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info("使用缓存的DXY数据")
                return self.cache[cache_key]

        try:
            # 获取美元指数
            ticker = yf.Ticker("DX-Y.NYB")
            df = ticker.history(period=period)

            if df.empty:
                logger.warning("获取DXY数据为空")
                return None

            # 缓存
            self.cache[cache_key] = df
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"获取DXY数据成功: {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"获取DXY数据失败: {str(e)}")
            return None

    def analyze_dxy(self, period: str = "1y") -> Dict[str, Any]:
        """
        分析美元指数

        Args:
            period: 分析周期

        Returns:
            DXY分析结果
        """
        df = self.get_dxy_data(period)

        if df is None or df.empty:
            return {'error': '无法获取美元指数数据'}

        try:
            # 当前美元指数
            current_dxy = float(df['Close'].iloc[-1])

            # 历史统计
            avg_dxy = float(df['Close'].mean())
            median_dxy = float(df['Close'].median())
            std_dxy = float(df['Close'].std())
            max_dxy = float(df['Close'].max())
            min_dxy = float(df['Close'].min())

            # 分位数
            dxy_percentile = float((df['Close'] <= current_dxy).sum() / len(df) * 100)

            # 短期/长期趋势
            recent_5d_avg = float(df['Close'].tail(5).mean())
            recent_20d_avg = float(df['Close'].tail(20).mean()) if len(df) >= 20 else avg_dxy
            recent_60d_avg = float(df['Close'].tail(60).mean()) if len(df) >= 60 else avg_dxy

            short_term_trend = 'rising' if recent_5d_avg > recent_20d_avg * 1.01 else (
                'falling' if recent_5d_avg < recent_20d_avg * 0.99 else 'stable'
            )
            long_term_trend = 'rising' if recent_20d_avg > recent_60d_avg * 1.01 else (
                'falling' if recent_20d_avg < recent_60d_avg * 0.99 else 'stable'
            )

            # 波动率
            recent_volatility = float(df['Close'].tail(20).std()) if len(df) >= 20 else std_dxy

            # 强弱分类
            strength_level = self._classify_strength(current_dxy)

            # Z-Score
            zscore = (current_dxy - avg_dxy) / std_dxy if std_dxy > 0 else 0

            # 涨跌幅
            if len(df) >= 2:
                change_1d = float((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100)
            else:
                change_1d = 0

            if len(df) >= 20:
                change_20d = float((df['Close'].iloc[-1] - df['Close'].iloc[-20]) / df['Close'].iloc[-20] * 100)
            else:
                change_20d = 0

            result = {
                'current_dxy': current_dxy,
                'avg_dxy': avg_dxy,
                'median_dxy': median_dxy,
                'std_dxy': std_dxy,
                'max_dxy': max_dxy,
                'min_dxy': min_dxy,
                'dxy_percentile': dxy_percentile,
                'strength_level': strength_level,
                'short_term_trend': short_term_trend,
                'long_term_trend': long_term_trend,
                'recent_5d_avg': recent_5d_avg,
                'recent_20d_avg': recent_20d_avg,
                'recent_60d_avg': recent_60d_avg,
                'recent_volatility': recent_volatility,
                'zscore': zscore,
                'change_1d_pct': change_1d,
                'change_20d_pct': change_20d,
                'signal': self._generate_signal(
                    current_dxy, strength_level, short_term_trend, long_term_trend
                ),
                'interpretation': self._generate_interpretation(
                    current_dxy, strength_level, short_term_trend, dxy_percentile
                ),
                'allocation_advice': self._generate_allocation_advice(
                    current_dxy, strength_level, short_term_trend
                ),
                'risk_alert': self._generate_risk_alert(current_dxy, zscore, recent_volatility)
            }

            return result

        except Exception as e:
            logger.error(f"分析DXY失败: {str(e)}")
            return {'error': str(e)}

    def _classify_strength(self, dxy: float) -> str:
        """强弱分类"""
        if dxy > 110:
            return '极强美元'
        elif dxy > self.strong_threshold:
            return '强美元'
        elif dxy > self.normal_high:
            return '正常偏强'
        elif dxy > self.normal_low:
            return '正常'
        elif dxy > self.weak_threshold:
            return '正常偏弱'
        else:
            return '弱美元'

    def _generate_signal(
        self, current_dxy: float, strength: str,
        short_trend: str, long_trend: str
    ) -> str:
        """生成交易信号"""
        if strength == '极强美元' and short_trend == 'rising':
            return '强烈警告: 美元极强且上升,大宗商品/新兴市场承压严重'

        if strength == '强美元':
            return '警告: 强美元环境,利空黄金/大宗商品/新兴市场股票'

        if strength == '弱美元' and short_trend == 'falling':
            return '积极: 弱美元环境,利好大宗商品/黄金/新兴市场'

        if strength in ['正常偏弱', '弱美元']:
            return '正面: 美元偏弱,利好大宗商品和非美资产'

        if short_trend == 'rising' and long_trend == 'falling':
            return '转折: 美元短期反弹,但长期趋势仍下行'

        if short_trend == 'falling' and long_trend == 'rising':
            return '调整: 美元短期回调,但长期趋势仍上行'

        return '中性: 美元处于正常区间'

    def _generate_interpretation(
        self, current_dxy: float, strength: str,
        trend: str, percentile: float
    ) -> str:
        """生成解读文本"""
        interpretation = []

        interpretation.append(f"当前美元指数{current_dxy:.2f}")
        interpretation.append(f"强度等级: {strength}")

        if percentile > 80:
            interpretation.append(f"处于历史高位({percentile:.0f}%分位)")
        elif percentile < 20:
            interpretation.append(f"处于历史低位({percentile:.0f}%分位)")

        if trend == 'rising':
            interpretation.append("短期趋势上升")
        elif trend == 'falling':
            interpretation.append("短期趋势下降")

        return '; '.join(interpretation)

    def _generate_allocation_advice(
        self, current_dxy: float, strength: str, trend: str
    ) -> str:
        """生成配置建议"""
        if strength == '极强美元':
            return '建议: 增持美元资产,减持大宗商品/黄金/新兴市场股票'

        if strength == '强美元':
            return '建议: 偏向美股/美元资产,谨慎大宗商品/新兴市场'

        if strength in ['正常偏弱', '弱美元']:
            return '建议: 增配黄金/大宗商品/新兴市场,减持美元现金'

        if trend == 'rising':
            return '中性偏谨慎: 美元上升对非美资产不利,等待企稳'
        elif trend == 'falling':
            return '中性偏积极: 美元下降对非美资产有利,可适度增配'

        return '均衡配置: 美元处于中性区间,各类资产均衡配置'

    def _generate_risk_alert(
        self, current_dxy: float, zscore: float, volatility: float
    ) -> Optional[str]:
        """生成风险提示"""
        alerts = []

        if current_dxy > 110:
            alerts.append("⚠️⚠️⚠️ 美元指数超过110,历史罕见,新兴市场危机风险")

        if current_dxy > 105 and zscore > 1.5:
            alerts.append("⚠️⚠️ 强美元+高估值,大宗商品/新兴市场风险高")

        if volatility > 2:
            alerts.append("⚠️ 美元波动率高,外汇市场不稳定")

        if current_dxy < 90:
            alerts.append("⚠️ 美元极度疲软,关注美国通胀/债务风险")

        return ' | '.join(alerts) if alerts else None


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    analyzer = DXYAnalyzer()

    print("=" * 80)
    print("美元指数(DXY)分析器测试")
    print("=" * 80)

    result = analyzer.analyze_dxy(period="1y")

    if 'error' not in result:
        print(f"\n当前美元指数: {result['current_dxy']:.2f}")
        print(f"历史均值: {result['avg_dxy']:.2f}")
        print(f"强度等级: {result['strength_level']}")
        print(f"历史分位数: {result['dxy_percentile']:.1f}%")
        print(f"短期趋势: {result['short_term_trend']}")
        print(f"长期趋势: {result['long_term_trend']}")
        print(f"1日涨跌: {result['change_1d_pct']:.2f}%")
        print(f"20日涨跌: {result['change_20d_pct']:.2f}%")
        print(f"\n交易信号: {result['signal']}")
        print(f"解读: {result['interpretation']}")
        print(f"配置建议: {result['allocation_advice']}")
        if result['risk_alert']:
            print(f"\n风险提示: {result['risk_alert']}")
    else:
        print(f"分析失败: {result['error']}")

    print("\n" + "=" * 80)
