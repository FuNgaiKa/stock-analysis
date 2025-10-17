"""
美债收益率曲线分析器
用于判断经济周期和衰退风险
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TreasuryYieldAnalyzer:
    """美债收益率曲线分析器"""

    def __init__(self):
        """初始化美债分析器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 5分钟缓存

        # 美债代码映射
        self.tickers = {
            '3m': '^IRX',   # 13周国债
            '2y': '^FVX',   # 5年期(代替2年期)
            '10y': '^TNX',  # 10年期
        }

    def get_yield_data(self, period: str = "1y") -> Optional[Dict[str, pd.DataFrame]]:
        """
        获取美债收益率数据

        Args:
            period: 时间周期

        Returns:
            各期限收益率数据字典
        """
        cache_key = f"treasury_{period}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info("使用缓存的美债数据")
                return self.cache[cache_key]

        try:
            data = {}
            for name, ticker in self.tickers.items():
                t = yf.Ticker(ticker)
                df = t.history(period=period)
                if not df.empty:
                    data[name] = df
                    logger.info(f"获取{name}美债数据: {len(df)}条")

            if not data:
                logger.warning("所有美债数据获取失败")
                return None

            # 缓存
            self.cache[cache_key] = data
            self.cache_time[cache_key] = datetime.now()

            return data

        except Exception as e:
            logger.error(f"获取美债数据失败: {str(e)}")
            return None

    def analyze_yield_curve(self, period: str = "1y") -> Dict[str, Any]:
        """
        分析美债收益率曲线

        Args:
            period: 分析周期

        Returns:
            收益率曲线分析结果
        """
        data = self.get_yield_data(period)

        if data is None or len(data) == 0:
            return {'error': '无法获取美债数据'}

        try:
            # 当前收益率
            current_yields = {}
            for name, df in data.items():
                current_yields[name] = float(df['Close'].iloc[-1])

            # 计算收益率差(利差)
            spread_2y_10y = current_yields.get('10y', 0) - current_yields.get('2y', 0)
            spread_3m_10y = current_yields.get('10y', 0) - current_yields.get('3m', 0)

            # 判断是否倒挂
            is_inverted_2y_10y = spread_2y_10y < 0
            is_inverted_3m_10y = spread_3m_10y < 0

            # 历史利差统计
            if '10y' in data and '2y' in data:
                df_10y = data['10y']['Close']
                df_2y = data['2y']['Close']

                # 对齐索引
                common_index = df_10y.index.intersection(df_2y.index)
                if len(common_index) > 0:
                    spread_history = df_10y[common_index] - df_2y[common_index]
                    avg_spread = float(spread_history.mean())
                    spread_percentile = float(
                        (spread_history <= spread_2y_10y).sum() / len(spread_history) * 100
                    )

                    # 倒挂持续天数
                    inverted_days = self._count_consecutive_inverted(spread_history)
                else:
                    avg_spread = 0
                    spread_percentile = 50
                    inverted_days = 0
            else:
                avg_spread = 0
                spread_percentile = 50
                inverted_days = 0

            # 曲线形态
            curve_shape = self._classify_curve(spread_2y_10y, spread_3m_10y)

            # 经济周期阶段
            economic_phase = self._identify_economic_phase(
                spread_2y_10y, is_inverted_2y_10y, inverted_days
            )

            # 衰退概率估算(基于历史规律)
            recession_probability = self._estimate_recession_probability(
                is_inverted_2y_10y, inverted_days
            )

            result = {
                'current_yields': current_yields,
                'spread_2y_10y': spread_2y_10y,
                'spread_3m_10y': spread_3m_10y,
                'is_inverted_2y_10y': is_inverted_2y_10y,
                'is_inverted_3m_10y': is_inverted_3m_10y,
                'avg_spread': avg_spread,
                'spread_percentile': spread_percentile,
                'inverted_days': inverted_days,
                'curve_shape': curve_shape,
                'economic_phase': economic_phase,
                'recession_probability': recession_probability,
                'signal': self._generate_signal(
                    is_inverted_2y_10y, economic_phase, recession_probability
                ),
                'interpretation': self._generate_interpretation(
                    spread_2y_10y, curve_shape, economic_phase, inverted_days
                ),
                'risk_alert': self._generate_risk_alert(
                    is_inverted_2y_10y, inverted_days, recession_probability
                )
            }

            return result

        except Exception as e:
            logger.error(f"分析美债曲线失败: {str(e)}")
            return {'error': str(e)}

    def _count_consecutive_inverted(self, spread_series: pd.Series) -> int:
        """计算连续倒挂天数"""
        if spread_series.iloc[-1] >= 0:
            return 0

        count = 0
        for i in range(len(spread_series) - 1, -1, -1):
            if spread_series.iloc[i] < 0:
                count += 1
            else:
                break
        return count

    def _classify_curve(self, spread_2y_10y: float, spread_3m_10y: float) -> str:
        """分类曲线形态"""
        if spread_2y_10y < -0.2:
            return '深度倒挂'
        elif spread_2y_10y < 0:
            return '倒挂'
        elif spread_2y_10y < 0.5:
            return '平坦'
        elif spread_2y_10y < 1.5:
            return '正常'
        else:
            return '陡峭'

    def _identify_economic_phase(
        self, spread: float, is_inverted: bool, inverted_days: int
    ) -> str:
        """识别经济周期阶段"""
        if is_inverted and inverted_days > 90:
            return '衰退前期(倒挂持续90+日)'
        elif is_inverted:
            return '扩张晚期(收益率曲线倒挂)'
        elif spread > 1.5:
            return '扩张早期(曲线陡峭)'
        elif spread > 0.5:
            return '扩张中期(曲线正常)'
        else:
            return '扩张放缓(曲线平坦)'

    def _estimate_recession_probability(
        self, is_inverted: bool, inverted_days: int
    ) -> float:
        """估算衰退概率"""
        if not is_inverted:
            return 0.0

        # 基于历史统计:倒挂后6-18个月衰退概率90%+
        if inverted_days > 180:  # 半年以上
            return 0.9
        elif inverted_days > 90:  # 3-6个月
            return 0.7
        elif inverted_days > 30:  # 1-3个月
            return 0.5
        else:
            return 0.3

    def _generate_signal(
        self, is_inverted: bool, economic_phase: str, recession_prob: float
    ) -> str:
        """生成交易信号"""
        if recession_prob > 0.7:
            return '强烈警告: 衰退风险高,建议大幅降低股票仓位,增持债券/现金'

        if is_inverted:
            return '警告: 收益率曲线倒挂,未来6-18个月衰退概率高,降低风险敞口'

        if economic_phase == '扩张早期(曲线陡峭)':
            return '积极: 经济扩张早期,可加大股票配置'

        if economic_phase == '扩张中期(曲线正常)':
            return '正常: 经济扩张中期,维持标准配置'

        if economic_phase == '扩张放缓(曲线平坦)':
            return '谨慎: 经济扩张放缓,关注衰退信号'

        return '中性'

    def _generate_interpretation(
        self, spread: float, shape: str, phase: str, inverted_days: int
    ) -> str:
        """生成解读文本"""
        interpretation = []

        interpretation.append(f"当前10年-2年期利差{spread:.2f}%")
        interpretation.append(f"曲线形态: {shape}")
        interpretation.append(f"经济阶段: {phase}")

        if inverted_days > 0:
            interpretation.append(f"已连续倒挂{inverted_days}日")

        return '; '.join(interpretation)

    def _generate_risk_alert(
        self, is_inverted: bool, inverted_days: int, recession_prob: float
    ) -> Optional[str]:
        """生成风险提示"""
        alerts = []

        if recession_prob > 0.7:
            alerts.append("⚠️⚠️⚠️ 衰退概率>70%,强烈建议降低风险资产配置")

        if is_inverted and inverted_days > 180:
            alerts.append("⚠️⚠️ 倒挂持续半年以上,历史上100%进入衰退")

        if is_inverted and inverted_days > 90:
            alerts.append("⚠️ 倒挂持续3个月以上,衰退风险显著")

        if is_inverted:
            alerts.append("建议: 增加防御性配置(必需消费品/公用事业/债券)")

        return ' | '.join(alerts) if alerts else None


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    analyzer = TreasuryYieldAnalyzer()

    print("=" * 80)
    print("美债收益率曲线分析器测试 (经济衰退预警)")
    print("=" * 80)

    result = analyzer.analyze_yield_curve(period="1y")

    if 'error' not in result:
        print(f"\n当前收益率:")
        for name, yield_val in result['current_yields'].items():
            print(f"  {name}: {yield_val:.2f}%")

        print(f"\n10Y-2Y利差: {result['spread_2y_10y']:.2f}%")
        print(f"是否倒挂: {'是' if result['is_inverted_2y_10y'] else '否'}")
        print(f"曲线形态: {result['curve_shape']}")
        print(f"经济阶段: {result['economic_phase']}")
        print(f"衰退概率: {result['recession_probability']:.0%}")

        if result['inverted_days'] > 0:
            print(f"倒挂天数: {result['inverted_days']}日")

        print(f"\n交易信号: {result['signal']}")
        print(f"解读: {result['interpretation']}")

        if result['risk_alert']:
            print(f"\n风险提示: {result['risk_alert']}")
    else:
        print(f"分析失败: {result['error']}")

    print("\n" + "=" * 80)
