#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股VIX等价指标 - 中国波动率指数(iVIX)及替代方案

VIX背景:
- VIX (CBOE Volatility Index): 美股恐慌指数,基于S&P 500期权隐含波动率
- 反映市场对未来30天波动率的预期
- VIX > 30: 高波动/恐慌, VIX < 15: 低波动/平静

A股现状:
1. 官方iVIX: 中金所发布的中国波动率指数 (2015年推出)
   - 基于上证50ETF期权隐含波动率
   - 数据源有限,不易获取实时数据

2. 替代方案:
   - 历史波动率 (HV): 基于历史价格计算
   - ATR波动率
   - 涨跌停家数比率
   - 北向资金波动
"""

import pandas as pd
import numpy as np
import akshare as ak
from typing import Dict, Optional
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


class ChinaVolatilityIndex:
    """A股波动率指数计算器"""

    def __init__(self):
        self.index_code = 'sh000001'  # 上证指数
        self.data = None

    def calculate_historical_volatility(
        self,
        df: pd.DataFrame,
        window: int = 20
    ) -> pd.Series:
        """
        计算历史波动率 (Historical Volatility)

        公式: HV = std(returns) × sqrt(252)

        Args:
            df: 包含收盘价的DataFrame
            window: 滚动窗口(天数)

        Returns:
            年化历史波动率序列
        """
        returns = df['close'].pct_change()
        hv = returns.rolling(window).std() * np.sqrt(252)
        return hv

    def calculate_atr_volatility(
        self,
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.Series:
        """
        计算ATR波动率 (Average True Range)

        ATR是技术分析中常用的波动率指标

        Args:
            df: 包含high, low, close的DataFrame
            period: ATR周期

        Returns:
            ATR百分比序列
        """
        high = df['high']
        low = df['low']
        close = df['close']

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR
        atr = tr.rolling(period).mean()

        # ATR百分比
        atr_pct = atr / close * 100

        return atr_pct

    def calculate_parkinson_volatility(
        self,
        df: pd.DataFrame,
        window: int = 20
    ) -> pd.Series:
        """
        Parkinson波动率 (基于高低价)

        比简单历史波动率更精确,利用了日内高低价信息

        公式: Parkinson = sqrt(sum(ln(H/L)^2) / (4*ln(2)*N))

        Args:
            df: 包含high, low的DataFrame
            window: 窗口大小

        Returns:
            年化Parkinson波动率
        """
        hl_ratio = np.log(df['high'] / df['low'])
        parkinson = hl_ratio ** 2

        vol = np.sqrt(
            parkinson.rolling(window).sum() / (4 * np.log(2) * window)
        ) * np.sqrt(252)

        return vol

    def calculate_composite_vix(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        综合VIX替代指标

        结合多个维度:
        1. 历史波动率 (HV)
        2. Parkinson波动率
        3. ATR百分比
        4. 涨跌停家数比率

        Returns:
            包含多种波动率指标的DataFrame
        """
        result = df.copy()

        # 1. 历史波动率
        result['hv_20'] = self.calculate_historical_volatility(df, window=20)
        result['hv_60'] = self.calculate_historical_volatility(df, window=60)

        # 2. Parkinson波动率
        result['parkinson_vol'] = self.calculate_parkinson_volatility(df)

        # 3. ATR波动率
        result['atr_pct'] = self.calculate_atr_volatility(df)

        # 4. 综合VIX (加权平均)
        # 权重: HV(40%), Parkinson(30%), ATR(30%)
        result['composite_vix'] = (
            result['hv_20'] * 0.4 +
            result['parkinson_vol'] * 0.3 +
            result['atr_pct'] * 0.3
        )

        # 5. VIX分位数 (最近1年)
        result['vix_percentile'] = result['composite_vix'].rolling(
            252, min_periods=60
        ).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1]
        )

        return result

    def get_market_data(self, days: int = 500) -> pd.DataFrame:
        """获取市场数据"""
        print(f"正在获取上证指数最近{days}天数据...")

        df = ak.stock_zh_index_daily(symbol=self.index_code)
        df = df.tail(days).copy()

        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        print(f"数据获取成功: {len(df)}条")
        return df

    def analyze_current_volatility(self) -> Dict:
        """分析当前波动率状态"""
        # 获取数据
        df = self.get_market_data(days=500)

        # 计算波动率指标
        df_vol = self.calculate_composite_vix(df)

        # 最新值
        current = df_vol.iloc[-1]

        # 历史统计
        stats = {
            'date': current.name.strftime('%Y-%m-%d'),
            'close': current['close'],
            'hv_20': current['hv_20'],
            'hv_60': current['hv_60'],
            'parkinson_vol': current['parkinson_vol'],
            'atr_pct': current['atr_pct'],
            'composite_vix': current['composite_vix'],
            'vix_percentile': current['vix_percentile'],
            'vix_level': self._classify_vix_level(current['composite_vix']),
            'leverage_advice': self._get_leverage_advice(
                current['composite_vix'],
                current['vix_percentile']
            )
        }

        return stats

    def _classify_vix_level(self, vix: float) -> str:
        """分类VIX水平"""
        if vix < 15:
            return "极低波动 (市场平静)"
        elif vix < 20:
            return "低波动 (正常市场)"
        elif vix < 30:
            return "中等波动 (谨慎)"
        elif vix < 40:
            return "高波动 (恐慌)"
        else:
            return "极端波动 (危机)"

    def _get_leverage_advice(self, vix: float, percentile: float) -> str:
        """根据VIX给出杠杆建议"""
        if vix < 15 and percentile < 0.3:
            return "低波动环境,可考虑1.5-2倍杠杆"
        elif vix < 20 and percentile < 0.5:
            return "正常波动,可考虑1.2-1.5倍杠杆"
        elif vix < 30:
            return "波动加剧,建议1倍杠杆(无杠杆)"
        else:
            return "高波动/恐慌,禁止使用杠杆"

    def compare_with_us_vix(self):
        """对比美股VIX (如果有数据)"""
        # TODO: 需要yfinance或其他数据源获取VIX
        pass

    def plot_volatility_history(self, days: int = 252):
        """绘制波动率历史图 (需要matplotlib)"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # 使用非交互式后端
            import matplotlib.pyplot as plt

            matplotlib.rcParams['font.sans-serif'] = ['SimHei']
            matplotlib.rcParams['axes.unicode_minus'] = False

            df = self.get_market_data(days=days)
            df_vol = self.calculate_composite_vix(df)

            fig, axes = plt.subplots(2, 1, figsize=(14, 10))

            # 上图: 价格
            ax1 = axes[0]
            ax1.plot(df_vol.index, df_vol['close'], label='上证指数', color='blue')
            ax1.set_title('上证指数走势', fontsize=14, fontweight='bold')
            ax1.set_ylabel('点位', fontsize=12)
            ax1.legend()
            ax1.grid(alpha=0.3)

            # 下图: 波动率
            ax2 = axes[1]
            ax2.plot(df_vol.index, df_vol['composite_vix'], label='综合VIX', color='red', linewidth=2)
            ax2.plot(df_vol.index, df_vol['hv_20'], label='HV(20)', color='orange', alpha=0.6)

            # VIX阈值线
            ax2.axhline(y=15, color='green', linestyle='--', alpha=0.5, label='低波动线(15)')
            ax2.axhline(y=30, color='orange', linestyle='--', alpha=0.5, label='警戒线(30)')

            ax2.set_title('A股波动率指数 (VIX替代)', fontsize=14, fontweight='bold')
            ax2.set_ylabel('波动率 (%)', fontsize=12)
            ax2.set_xlabel('日期', fontsize=12)
            ax2.legend()
            ax2.grid(alpha=0.3)

            plt.tight_layout()
            plt.savefig('china_vix_history.png', dpi=150, bbox_inches='tight')
            print("\n图表已保存: china_vix_history.png")

        except ImportError:
            print("未安装matplotlib,跳过绘图")


def get_limit_up_down_ratio() -> Dict:
    """
    获取涨跌停家数比率 (情绪指标)

    涨跌停比率可以作为市场情绪/波动的辅助指标
    """
    try:
        print("\n正在获取涨跌停数据...")
        df = ak.stock_zh_a_spot_em()

        # 涨停: 涨幅 >= 9.9%
        # 跌停: 跌幅 <= -9.9%
        limit_up = (df['涨跌幅'] >= 9.9).sum()
        limit_down = (df['涨跌幅'] <= -9.9).sum()

        total = len(df)

        return {
            'limit_up_count': limit_up,
            'limit_down_count': limit_down,
            'limit_up_ratio': limit_up / total,
            'limit_down_ratio': limit_down / total,
            'total_stocks': total,
            'sentiment': '极度恐慌' if limit_down > 100 else '恐慌' if limit_down > 50 else '正常'
        }

    except Exception as e:
        print(f"获取涨跌停数据失败: {str(e)}")
        return {}


if __name__ == '__main__':
    print("=" * 100)
    print("A股VIX等价指标分析")
    print("=" * 100)

    # 1. 创建计算器
    calculator = ChinaVolatilityIndex()

    # 2. 分析当前波动率
    print("\n1. 当前市场波动率分析:")
    print("-" * 100)

    stats = calculator.analyze_current_volatility()

    print(f"\n日期: {stats['date']}")
    print(f"上证指数: {stats['close']:.2f}")
    print(f"\n波动率指标:")
    print(f"  20日历史波动率 (HV): {stats['hv_20']:.2f}%")
    print(f"  60日历史波动率 (HV): {stats['hv_60']:.2f}%")
    print(f"  Parkinson波动率: {stats['parkinson_vol']:.2f}%")
    print(f"  ATR波动率: {stats['atr_pct']:.2f}%")
    print(f"\n[综合VIX]: {stats['composite_vix']:.2f}%")
    print(f"VIX分位数 (1年): {stats['vix_percentile']:.1%}")
    print(f"波动率等级: {stats['vix_level']}")
    print(f"\n杠杆建议: {stats['leverage_advice']}")

    # 3. 涨跌停情绪指标
    print("\n2. 市场情绪指标 (涨跌停家数):")
    print("-" * 100)

    limit_stats = get_limit_up_down_ratio()
    if limit_stats:
        print(f"\n涨停股票: {limit_stats['limit_up_count']} ({limit_stats['limit_up_ratio']:.2%})")
        print(f"跌停股票: {limit_stats['limit_down_count']} ({limit_stats['limit_down_ratio']:.2%})")
        print(f"市场情绪: {limit_stats['sentiment']}")

    # 4. VIX参考标准
    print("\n3. VIX参考标准 (类比美股VIX):")
    print("-" * 100)
    print("""
波动率水平       VIX范围      市场状态          杠杆建议
------------------------------------------------------------
极低波动         < 15%        市场平静          可考虑1.5-2倍
低波动          15-20%       正常市场          可考虑1.2-1.5倍
中等波动        20-30%       谨慎观望          建议1倍(无杠杆)
高波动          30-40%       市场恐慌          禁止杠杆
极端波动         > 40%        危机状态          禁止杠杆

注:
- A股由于涨跌停限制,波动率通常低于美股
- A股VIX < 20% 对应美股VIX < 15 (相对平静)
- A股VIX > 30% 对应美股VIX > 20 (需要警惕)
    """)

    # 5. 绘制历史图表
    print("\n4. 生成历史波动率图表...")
    print("-" * 100)
    calculator.plot_volatility_history(days=252)

    print("\n" + "=" * 100)
    print("分析完成!")
    print("=" * 100)
