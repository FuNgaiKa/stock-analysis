"""
换手率分析器
用于分析A股换手率,识别放量突破、缩量下跌等关键形态
"""
import akshare as ak
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TurnoverAnalyzer:
    """换手率分析器"""

    def __init__(self):
        """初始化换手率分析器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 5分钟缓存

    def get_index_turnover(self, index_symbol: str, period: int = 60) -> Optional[pd.DataFrame]:
        """
        获取指数换手率数据

        注意: AKShare的指数数据不包含换手率,这里使用成交量/流通市值的估算方法

        Args:
            index_symbol: 指数代码(如 '000001' 上证指数)
            period: 获取天数

        Returns:
            包含换手率(估算)的DataFrame
        """
        cache_key = f"turnover_{index_symbol}_{period}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info(f"使用缓存的{index_symbol}换手率数据")
                return self.cache[cache_key]

        try:
            # 获取指数历史数据
            # sh + 代码 = 上海, sz + 代码 = 深圳
            code_prefix = 'sh' if index_symbol.startswith('0000') or index_symbol.startswith('0003') else 'sz'
            full_code = code_prefix + index_symbol

            # 使用 stock_zh_index_daily 获取指数数据
            df = ak.stock_zh_index_daily(symbol=full_code)

            if df.empty:
                logger.warning(f"获取{index_symbol}换手率数据为空")
                return None

            # 取最近period天
            df = df.tail(period).copy()

            # 设置日期索引
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            # 计算换手率估算值
            # 换手率 = (成交量 / 平均成交量) * 基准换手率
            # 这里使用相对换手率指标,以均值为基准
            base_turnover = 2.5  # 上证指数历史平均换手率约2.5%
            avg_volume = df['volume'].mean()
            df['turnover'] = (df['volume'] / avg_volume) * base_turnover

            # 计算涨跌幅
            df['change_pct'] = df['close'].pct_change() * 100

            # 缓存
            self.cache[cache_key] = df
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"获取{index_symbol}换手率数据成功: {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"获取{index_symbol}换手率数据失败: {str(e)}")
            return None

    def analyze_turnover(self, index_symbol: str, period: int = 60) -> Dict[str, Any]:
        """
        分析换手率特征

        Args:
            index_symbol: 指数代码
            period: 分析周期

        Returns:
            换手率分析结果
        """
        df = self.get_index_turnover(index_symbol, period)

        if df is None or df.empty:
            return {'error': '无法获取换手率数据'}

        try:
            # 当前换手率
            current_turnover = float(df['turnover'].iloc[-1])

            # 历史统计
            avg_turnover = float(df['turnover'].mean())
            median_turnover = float(df['turnover'].median())
            std_turnover = float(df['turnover'].std())
            max_turnover = float(df['turnover'].max())
            min_turnover = float(df['turnover'].min())

            # 换手率分位数
            turnover_percentile = float((df['turnover'] <= current_turnover).sum() / len(df) * 100)

            # 换手率趋势(最近5日平均 vs 最近20日平均)
            recent_5d_avg = float(df['turnover'].tail(5).mean())
            recent_20d_avg = float(df['turnover'].tail(20).mean()) if len(df) >= 20 else avg_turnover
            turnover_trend = 'up' if recent_5d_avg > recent_20d_avg * 1.1 else ('down' if recent_5d_avg < recent_20d_avg * 0.9 else 'stable')

            # 换手率等级分类
            turnover_level = self._classify_turnover(current_turnover)

            # 量价配合分析
            current_price_change = float(df['change_pct'].iloc[-1])
            volume_price_pattern = self._analyze_volume_price(
                current_turnover, current_price_change, avg_turnover
            )

            # 异常检测
            is_abnormal = current_turnover > avg_turnover + 2 * std_turnover

            # 连续放量/缩量检测
            consecutive_high = self._count_consecutive(df['turnover'] > avg_turnover * 1.5)
            consecutive_low = self._count_consecutive(df['turnover'] < avg_turnover * 0.5)

            result = {
                'current_turnover': current_turnover,
                'current_turnover_pct': f"{current_turnover:.2f}%",
                'avg_turnover': avg_turnover,
                'median_turnover': median_turnover,
                'std_turnover': std_turnover,
                'max_turnover': max_turnover,
                'min_turnover': min_turnover,
                'turnover_percentile': turnover_percentile,
                'turnover_level': turnover_level,
                'turnover_trend': turnover_trend,
                'recent_5d_avg': recent_5d_avg,
                'recent_20d_avg': recent_20d_avg,
                'is_abnormal': is_abnormal,
                'consecutive_high_days': consecutive_high,
                'consecutive_low_days': consecutive_low,
                'volume_price_pattern': volume_price_pattern,
                'current_price_change': current_price_change,
                'signal': self._generate_signal(
                    current_turnover, avg_turnover, turnover_level,
                    volume_price_pattern, current_price_change
                ),
                'interpretation': self._generate_interpretation(
                    current_turnover, avg_turnover, turnover_level,
                    volume_price_pattern, is_abnormal, consecutive_high, consecutive_low
                )
            }

            return result

        except Exception as e:
            logger.error(f"分析换手率失败: {str(e)}")
            return {'error': str(e)}

    def _classify_turnover(self, turnover: float) -> str:
        """
        换手率等级分类

        Args:
            turnover: 换手率(%)

        Returns:
            等级描述
        """
        if turnover < 1:
            return '冷清'
        elif turnover < 3:
            return '正常'
        elif turnover < 7:
            return '活跃'
        elif turnover < 15:
            return '高度活跃'
        else:
            return '异常活跃'

    def _analyze_volume_price(self, turnover: float, price_change: float, avg_turnover: float) -> str:
        """
        量价配合分析

        Args:
            turnover: 当前换手率
            price_change: 价格涨跌幅(%)
            avg_turnover: 平均换手率

        Returns:
            量价形态
        """
        high_volume = turnover > avg_turnover * 1.5
        low_volume = turnover < avg_turnover * 0.5
        price_up = price_change > 1
        price_down = price_change < -1

        if high_volume and price_up:
            return '放量上涨'
        elif high_volume and price_down:
            return '放量下跌'
        elif low_volume and price_up:
            return '缩量上涨'
        elif low_volume and price_down:
            return '缩量下跌'
        elif high_volume:
            return '放量震荡'
        elif low_volume:
            return '缩量震荡'
        else:
            return '正常波动'

    def _count_consecutive(self, condition: pd.Series) -> int:
        """
        计算连续满足条件的天数

        Args:
            condition: 布尔序列

        Returns:
            连续天数
        """
        if condition.iloc[-1]:
            consecutive = 1
            for i in range(len(condition) - 2, -1, -1):
                if condition.iloc[i]:
                    consecutive += 1
                else:
                    break
            return consecutive
        return 0

    def _generate_signal(
        self,
        current_turnover: float,
        avg_turnover: float,
        turnover_level: str,
        volume_price_pattern: str,
        price_change: float
    ) -> str:
        """
        生成交易信号

        Returns:
            信号描述
        """
        # 放量突破
        if volume_price_pattern == '放量上涨' and current_turnover > avg_turnover * 2:
            return '强势突破'

        # 缩量下跌
        if volume_price_pattern == '缩量下跌':
            return '弱势下跌,抛压不重'

        # 放量下跌
        if volume_price_pattern == '放量下跌' and current_turnover > avg_turnover * 2:
            return '恐慌性下跌'

        # 异常活跃
        if turnover_level == '异常活跃' and price_change > 3:
            return '天量天价,警惕见顶'

        # 缩量上涨
        if volume_price_pattern == '缩量上涨' and price_change > 2:
            return '惜售上涨,后续可能加速'

        return '中性'

    def _generate_interpretation(
        self,
        current_turnover: float,
        avg_turnover: float,
        turnover_level: str,
        volume_price_pattern: str,
        is_abnormal: bool,
        consecutive_high: int,
        consecutive_low: int
    ) -> str:
        """
        生成解读文本

        Returns:
            解读文本
        """
        interpretation = []

        # 换手率水平
        if turnover_level == '冷清':
            interpretation.append("换手率低迷,市场交易清淡,筹码锁定")
        elif turnover_level == '异常活跃':
            interpretation.append("换手率异常活跃,需警惕换庄或见顶风险")

        # 量价形态
        if volume_price_pattern == '放量上涨':
            interpretation.append("放量上涨,多头积极,如突破关键位可能是有效突破")
        elif volume_price_pattern == '放量下跌':
            interpretation.append("放量下跌,恐慌盘涌出,需警惕进一步下跌")
        elif volume_price_pattern == '缩量上涨':
            interpretation.append("缩量上涨,持股惜售,后续可能加速上涨")
        elif volume_price_pattern == '缩量下跌':
            interpretation.append("缩量下跌,抛压不重,可能是假摔")

        # 连续形态
        if consecutive_high >= 3:
            interpretation.append(f"连续{consecutive_high}日高换手率,市场活跃度持续升高")
        elif consecutive_low >= 3:
            interpretation.append(f"连续{consecutive_low}日低换手率,市场观望情绪浓厚")

        # 异常检测
        if is_abnormal:
            interpretation.append("当前换手率显著偏离均值(>2σ),属于异常状态")

        return '; '.join(interpretation) if interpretation else '换手率处于正常波动区间'


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    analyzer = TurnoverAnalyzer()

    print("=" * 80)
    print("换手率分析器测试")
    print("=" * 80)

    # 测试上证指数
    print("\n1. 上证指数换手率分析:")
    print("-" * 80)
    result = analyzer.analyze_turnover('000001', period=60)

    if 'error' not in result:
        print(f"当前换手率: {result['current_turnover_pct']}")
        print(f"历史均值: {result['avg_turnover']:.2f}%")
        print(f"换手率等级: {result['turnover_level']}")
        print(f"换手率分位数: {result['turnover_percentile']:.1f}%")
        print(f"量价形态: {result['volume_price_pattern']}")
        print(f"交易信号: {result['signal']}")
        print(f"解读: {result['interpretation']}")
    else:
        print(f"分析失败: {result['error']}")

    print("\n" + "=" * 80)
