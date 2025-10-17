"""
信用利差分析器 (High Yield Spread)
通过HYG(高收益债ETF) vs AGG(投资级债ETF)监控信用风险
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CreditSpreadAnalyzer:
    """信用利差分析器 - 信用风险监控"""

    def __init__(self):
        """初始化信用利差分析器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 5分钟缓存

        # 利差关键阈值(基于历史经验)
        self.crisis_threshold = 0.10      # 危机水平(利差>10%)
        self.high_risk_threshold = 0.06   # 高风险(利差>6%)
        self.elevated_threshold = 0.04    # 风险上升(利差>4%)
        self.normal_threshold = 0.02      # 正常(利差2-4%)

    def get_etf_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        获取ETF历史数据

        Args:
            ticker: ETF代码 (HYG或AGG)
            period: 时间周期

        Returns:
            ETF数据DataFrame
        """
        cache_key = f"{ticker}_{period}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info(f"使用缓存的{ticker}数据")
                return self.cache[cache_key]

        try:
            # 获取ETF数据
            etf = yf.Ticker(ticker)
            df = etf.history(period=period)

            if df.empty:
                logger.warning(f"获取{ticker}数据为空")
                return None

            # 缓存
            self.cache[cache_key] = df
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"获取{ticker}数据成功: {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"获取{ticker}数据失败: {str(e)}")
            return None

    def analyze_credit_spread(self, period: str = "1y") -> Dict[str, Any]:
        """
        分析信用利差

        Args:
            period: 分析周期

        Returns:
            信用利差分析结果
        """
        # 获取高收益债ETF和投资级债ETF数据
        hyg_df = self.get_etf_data("HYG", period)
        agg_df = self.get_etf_data("AGG", period)

        if hyg_df is None or agg_df is None or hyg_df.empty or agg_df.empty:
            return {'error': '无法获取债券ETF数据'}

        try:
            # 对齐数据(使用共同日期)
            common_dates = hyg_df.index.intersection(agg_df.index)
            if len(common_dates) < 10:
                return {'error': '有效数据点不足'}

            hyg_prices = hyg_df.loc[common_dates, 'Close']
            agg_prices = agg_df.loc[common_dates, 'Close']

            # 计算收益率(简化:用价格反向变动近似收益率)
            # 债券价格下跌 = 收益率上升
            hyg_returns = -hyg_prices.pct_change()
            agg_returns = -agg_prices.pct_change()

            # 计算利差(高收益债收益率 - 投资级债收益率)
            # 正值=风险溢价,数值越大=信用风险越高
            spread_series = hyg_returns - agg_returns

            # 当前利差(用最近5天平均,平滑噪音)
            current_spread = float(spread_series.tail(5).mean())

            # 历史统计
            avg_spread = float(spread_series.mean())
            median_spread = float(spread_series.median())
            std_spread = float(spread_series.std())
            max_spread = float(spread_series.max())
            min_spread = float(spread_series.min())

            # 分位数
            spread_percentile = float((spread_series <= current_spread).sum() / len(spread_series) * 100)

            # 趋势分析
            recent_20d_avg = float(spread_series.tail(20).mean()) if len(spread_series) >= 20 else avg_spread
            recent_60d_avg = float(spread_series.tail(60).mean()) if len(spread_series) >= 60 else avg_spread

            trend = 'widening' if current_spread > recent_20d_avg * 1.1 else (
                'tightening' if current_spread < recent_20d_avg * 0.9 else 'stable'
            )

            # 风险等级
            risk_level = self._classify_risk(current_spread)

            # Z-Score
            zscore = (current_spread - avg_spread) / std_spread if std_spread > 0 else 0

            # 当前ETF价格
            current_hyg = float(hyg_prices.iloc[-1])
            current_agg = float(agg_prices.iloc[-1])

            # 涨跌幅
            hyg_change_1d = float((hyg_prices.iloc[-1] - hyg_prices.iloc[-2]) / hyg_prices.iloc[-2] * 100) if len(hyg_prices) > 1 else 0
            agg_change_1d = float((agg_prices.iloc[-1] - agg_prices.iloc[-2]) / agg_prices.iloc[-2] * 100) if len(agg_prices) > 1 else 0

            result = {
                'current_spread': current_spread * 100,  # 转换为百分比
                'avg_spread': avg_spread * 100,
                'median_spread': median_spread * 100,
                'std_spread': std_spread * 100,
                'max_spread': max_spread * 100,
                'min_spread': min_spread * 100,
                'spread_percentile': spread_percentile,
                'risk_level': risk_level,
                'trend': trend,
                'recent_20d_avg': recent_20d_avg * 100,
                'recent_60d_avg': recent_60d_avg * 100,
                'zscore': zscore,
                'hyg_price': current_hyg,
                'agg_price': current_agg,
                'hyg_change_1d_pct': hyg_change_1d,
                'agg_change_1d_pct': agg_change_1d,
                'signal': self._generate_signal(current_spread, trend, risk_level),
                'interpretation': self._generate_interpretation(
                    current_spread, risk_level, trend, spread_percentile
                ),
                'trading_advice': self._generate_trading_advice(current_spread, risk_level, trend),
                'risk_alert': self._generate_risk_alert(current_spread, zscore, trend)
            }

            return result

        except Exception as e:
            logger.error(f"分析信用利差失败: {str(e)}")
            return {'error': str(e)}

    def _classify_risk(self, spread: float) -> str:
        """风险等级分类"""
        if spread > self.crisis_threshold:
            return '危机水平'
        elif spread > self.high_risk_threshold:
            return '高风险'
        elif spread > self.elevated_threshold:
            return '风险上升'
        elif spread > self.normal_threshold:
            return '正常'
        elif spread > 0:
            return '低风险'
        else:
            return '极低风险'

    def _generate_signal(self, current_spread: float, trend: str, risk_level: str) -> str:
        """生成交易信号"""
        if risk_level == '危机水平' and trend == 'widening':
            return '强烈警告: 信用风险危机,股市大跌风险极高,增持现金/国债'

        if risk_level == '高风险':
            return '警告: 信用风险高企,企业违约概率上升,降低股票仓位'

        if risk_level == '风险上升' and trend == 'widening':
            return '谨慎: 信用利差扩大,市场风险偏好下降,警惕股市调整'

        if risk_level == '正常' and trend == 'stable':
            return '中性: 信用市场平稳,可正常配置股票'

        if risk_level == '低风险' and trend == 'tightening':
            return '积极: 信用利差收窄,风险偏好回升,可增配股票'

        if risk_level == '极低风险':
            return '乐观: 信用风险极低,市场流动性充裕,股市利好'

        return '中性观望'

    def _generate_interpretation(
        self, current_spread: float, risk_level: str,
        trend: str, percentile: float
    ) -> str:
        """生成解读文本"""
        interpretation = []

        interpretation.append(f"当前信用利差{current_spread*100:.2f}%")
        interpretation.append(f"风险等级: {risk_level}")

        if percentile > 80:
            interpretation.append(f"处于历史高位({percentile:.0f}%分位),信用风险显著")
        elif percentile < 20:
            interpretation.append(f"处于历史低位({percentile:.0f}%分位),信用风险低")

        if trend == 'widening':
            interpretation.append("利差扩大,信用风险上升")
        elif trend == 'tightening':
            interpretation.append("利差收窄,信用风险下降")

        return '; '.join(interpretation)

    def _generate_trading_advice(
        self, current_spread: float, risk_level: str, trend: str
    ) -> str:
        """生成交易建议"""
        if risk_level in ['危机水平', '高风险']:
            return '建议: 大幅降低股票仓位至30%以下,增持国债/现金,规避信用风险'

        if risk_level == '风险上升' and trend == 'widening':
            return '建议: 降低股票仓位至50%,增加防御性配置(必需消费/公用事业)'

        if risk_level == '正常':
            return '中性配置: 维持标准股债配比60/40或50/50'

        if risk_level == '低风险' and trend == 'tightening':
            return '建议: 可增配股票至70%,优选高成长/科技股'

        if risk_level == '极低风险':
            return '建议: 激进配置股票80%+,流动性充裕环境下股市表现佳'

        return '观望为主,等待更明确信号'

    def _generate_risk_alert(
        self, current_spread: float, zscore: float, trend: str
    ) -> Optional[str]:
        """生成风险提示"""
        alerts = []

        if current_spread > 0.10:
            alerts.append("⚠️⚠️⚠️ 信用利差>10%,信用危机级别,历史上伴随股市暴跌")

        if current_spread > 0.06 and trend == 'widening':
            alerts.append("⚠️⚠️ 信用利差>6%且扩大,企业违约风险激增,股市承压")

        if zscore > 2:
            alerts.append("⚠️ 信用利差异常偏高(>2σ),市场极度不安")

        if current_spread > 0.04 and trend == 'widening':
            alerts.append("警告: 利差扩大趋势,建议降低风险资产配置")

        return ' | '.join(alerts) if alerts else None


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    analyzer = CreditSpreadAnalyzer()

    print("=" * 80)
    print("信用利差分析器测试 (高收益债 vs 投资级债)")
    print("=" * 80)

    result = analyzer.analyze_credit_spread(period="1y")

    if 'error' not in result:
        print(f"\n当前信用利差: {result['current_spread']:.2f}%")
        print(f"历史均值: {result['avg_spread']:.2f}%")
        print(f"风险等级: {result['risk_level']}")
        print(f"历史分位数: {result['spread_percentile']:.1f}%")
        print(f"趋势: {result['trend']}")
        print(f"Z-Score: {result['zscore']:.2f}")
        print(f"\nHYG价格: ${result['hyg_price']:.2f} ({result['hyg_change_1d_pct']:+.2f}%)")
        print(f"AGG价格: ${result['agg_price']:.2f} ({result['agg_change_1d_pct']:+.2f}%)")
        print(f"\n交易信号: {result['signal']}")
        print(f"解读: {result['interpretation']}")
        print(f"交易建议: {result['trading_advice']}")
        if result['risk_alert']:
            print(f"\n风险提示: {result['risk_alert']}")
    else:
        print(f"分析失败: {result['error']}")

    print("\n" + "=" * 80)
