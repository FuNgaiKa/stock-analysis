"""
VHSI恒生指数波动率分析器 (港股版VIX)
用于衡量港股市场恐慌程度
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VHSIAnalyzer:
    """VHSI恒生指数波动率分析器 - 港股恐慌指数"""

    def __init__(self):
        """初始化VHSI分析器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 5分钟缓存

        # VHSI关键阈值(参考VIX标准)
        self.extreme_fear_threshold = 30  # 极度恐慌
        self.fear_threshold = 20          # 恐慌
        self.normal_high = 18             # 正常偏高
        self.normal_low = 12              # 正常偏低
        self.complacent_threshold = 10    # 极度乐观

    def get_vhsi_data(self, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        获取VHSI历史数据

        Args:
            period: 时间周期

        Returns:
            VHSI数据DataFrame
        """
        cache_key = f"vhsi_{period}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info("使用缓存的VHSI数据")
                return self.cache[cache_key]

        try:
            # 获取VHSI指数
            ticker = yf.Ticker("^VHSI")
            df = ticker.history(period=period)

            if df.empty:
                logger.warning("获取VHSI数据为空")
                return None

            # 缓存
            self.cache[cache_key] = df
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"获取VHSI数据成功: {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"获取VHSI数据失败: {str(e)}")
            return None

    def analyze_vhsi(self, period: str = "1y") -> Dict[str, Any]:
        """
        分析VHSI波动率指数

        Args:
            period: 分析周期

        Returns:
            VHSI分析结果
        """
        df = self.get_vhsi_data(period)

        if df is None or df.empty:
            return {'error': '无法获取VHSI数据'}

        try:
            # 当前VHSI值
            current_vhsi = float(df['Close'].iloc[-1])

            # 历史统计
            avg_vhsi = float(df['Close'].mean())
            median_vhsi = float(df['Close'].median())
            std_vhsi = float(df['Close'].std())
            max_vhsi = float(df['Close'].max())
            min_vhsi = float(df['Close'].min())

            # 分位数
            vhsi_percentile = float((df['Close'] <= current_vhsi).sum() / len(df) * 100)

            # 趋势分析
            recent_5d_avg = float(df['Close'].tail(5).mean())
            recent_20d_avg = float(df['Close'].tail(20).mean()) if len(df) >= 20 else avg_vhsi

            trend = 'rising' if recent_5d_avg > recent_20d_avg * 1.05 else (
                'falling' if recent_5d_avg < recent_20d_avg * 0.95 else 'stable'
            )

            # 恐慌等级
            panic_level = self._classify_panic(current_vhsi)

            # Z-Score
            zscore = (current_vhsi - avg_vhsi) / std_vhsi if std_vhsi > 0 else 0

            # 涨跌幅
            if len(df) >= 2:
                change_1d = float((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100)
            else:
                change_1d = 0

            if len(df) >= 5:
                change_5d = float((df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5] * 100)
            else:
                change_5d = 0

            result = {
                'current_vhsi': current_vhsi,
                'avg_vhsi': avg_vhsi,
                'median_vhsi': median_vhsi,
                'std_vhsi': std_vhsi,
                'max_vhsi': max_vhsi,
                'min_vhsi': min_vhsi,
                'vhsi_percentile': vhsi_percentile,
                'panic_level': panic_level,
                'trend': trend,
                'recent_5d_avg': recent_5d_avg,
                'recent_20d_avg': recent_20d_avg,
                'zscore': zscore,
                'change_1d_pct': change_1d,
                'change_5d_pct': change_5d,
                'signal': self._generate_signal(current_vhsi, trend, panic_level),
                'interpretation': self._generate_interpretation(
                    current_vhsi, panic_level, trend, vhsi_percentile
                ),
                'trading_advice': self._generate_trading_advice(current_vhsi, panic_level, trend),
                'risk_alert': self._generate_risk_alert(current_vhsi, zscore, trend)
            }

            return result

        except Exception as e:
            logger.error(f"分析VHSI失败: {str(e)}")
            return {'error': str(e)}

    def _classify_panic(self, vhsi: float) -> str:
        """恐慌等级分类"""
        if vhsi > self.extreme_fear_threshold:
            return '极度恐慌'
        elif vhsi > self.fear_threshold:
            return '恐慌'
        elif vhsi > self.normal_high:
            return '正常偏高'
        elif vhsi > self.normal_low:
            return '正常'
        elif vhsi > self.complacent_threshold:
            return '乐观'
        else:
            return '极度乐观'

    def _generate_signal(self, current_vhsi: float, trend: str, panic_level: str) -> str:
        """生成交易信号"""
        if current_vhsi > 30 and trend == 'rising':
            return '强烈买入信号: 极度恐慌,市场超卖,抄底良机'

        if current_vhsi > 25:
            return '买入信号: 恐慌情绪浓厚,港股估值吸引力上升'

        if current_vhsi > 20 and trend == 'falling':
            return '谨慎买入: 恐慌缓解,可逢低布局'

        if current_vhsi < 12 and trend == 'falling':
            return '卖出信号: 市场过度乐观,警惕回调风险'

        if current_vhsi < 10:
            return '强烈卖出信号: 极度乐观,泡沫风险,建议减仓'

        return '中性: VHSI处于正常区间,观望为主'

    def _generate_interpretation(
        self, current_vhsi: float, panic_level: str,
        trend: str, percentile: float
    ) -> str:
        """生成解读文本"""
        interpretation = []

        interpretation.append(f"当前VHSI指数{current_vhsi:.1f}")
        interpretation.append(f"恐慌等级: {panic_level}")

        if percentile > 80:
            interpretation.append(f"处于历史高位({percentile:.0f}%分位),市场恐慌")
        elif percentile < 20:
            interpretation.append(f"处于历史低位({percentile:.0f}%分位),市场乐观")

        if trend == 'rising':
            interpretation.append("恐慌情绪上升,波动率增加")
        elif trend == 'falling':
            interpretation.append("恐慌情绪下降,波动率回落")

        return '; '.join(interpretation)

    def _generate_trading_advice(
        self, current_vhsi: float, panic_level: str, trend: str
    ) -> str:
        """生成交易建议"""
        if panic_level == '极度恐慌':
            return '建议: 分批抄底港股,重点配置恒指成分股/红筹蓝筹'

        if panic_level == '恐慌':
            return '建议: 逢低布局,优选高股息/低估值标的'

        if panic_level in ['正常偏高', '正常']:
            return '中性配置: 维持标准仓位,均衡配置'

        if panic_level == '乐观':
            return '建议: 警惕回调,适度减仓,落袋为安'

        if panic_level == '极度乐观':
            return '建议: 大幅减仓,规避泡沫风险,增持现金'

        return '观望为主,等待更明确信号'

    def _generate_risk_alert(
        self, current_vhsi: float, zscore: float, trend: str
    ) -> Optional[str]:
        """生成风险提示"""
        alerts = []

        if current_vhsi > 35:
            alerts.append("⚠️⚠️⚠️ VHSI>35,港股极度恐慌,历史罕见抄底机会")

        if current_vhsi > 30 and trend == 'rising':
            alerts.append("⚠️⚠️ VHSI>30且上升,恐慌加剧,但往往是最佳买点")

        if zscore > 2:
            alerts.append("⚠️ VHSI异常偏高(>2σ),市场极度不安")

        if current_vhsi < 10 and trend == 'falling':
            alerts.append("⚠️⚠️ VHSI<10且下降,市场过度乐观,警惕黑天鹅")

        if current_vhsi < 8:
            alerts.append("⚠️⚠️⚠️ VHSI<8,极度乐观,泡沫风险极高")

        return ' | '.join(alerts) if alerts else None


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    analyzer = VHSIAnalyzer()

    print("=" * 80)
    print("VHSI恒生指数波动率分析器测试 (港股恐慌指数)")
    print("=" * 80)

    result = analyzer.analyze_vhsi(period="1y")

    if 'error' not in result:
        print(f"\n当前VHSI指数: {result['current_vhsi']:.2f}")
        print(f"历史均值: {result['avg_vhsi']:.2f}")
        print(f"恐慌等级: {result['panic_level']}")
        print(f"历史分位数: {result['vhsi_percentile']:.1f}%")
        print(f"趋势: {result['trend']}")
        print(f"1日涨跌: {result['change_1d_pct']:.2f}%")
        print(f"5日涨跌: {result['change_5d_pct']:.2f}%")
        print(f"\n交易信号: {result['signal']}")
        print(f"解读: {result['interpretation']}")
        print(f"交易建议: {result['trading_advice']}")
        if result['risk_alert']:
            print(f"\n风险提示: {result['risk_alert']}")
    else:
        print(f"分析失败: {result['error']}")

    print("\n" + "=" * 80)
