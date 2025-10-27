#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业轮动分析器 - Phase 3
分析11大行业ETF的强弱,识别市场轮动模式,提供行业配置建议
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class SectorRotationAnalyzer:
    """
    行业轮动分析器

    分析美股11大行业的强弱变化,识别市场风险偏好和轮动模式
    """

    # 11大行业ETF (SPDR Sector ETFs)
    SECTOR_ETFS = {
        'XLK': '科技',          # Technology
        'XLF': '金融',          # Financials
        'XLE': '能源',          # Energy
        'XLV': '医疗',          # Health Care
        'XLI': '工业',          # Industrials
        'XLP': '必需消费',       # Consumer Staples
        'XLY': '可选消费',       # Consumer Discretionary
        'XLB': '材料',          # Materials
        'XLRE': '房地产',       # Real Estate
        'XLU': '公用事业',       # Utilities
        'XLC': '通讯服务'        # Communication Services
    }

    # 行业分类
    OFFENSIVE_SECTORS = ['XLK', 'XLY', 'XLF', 'XLI']  # 进攻型(风险偏好)
    DEFENSIVE_SECTORS = ['XLV', 'XLP', 'XLU']         # 防守型(避险)
    CYCLICAL_SECTORS = ['XLE', 'XLB']                 # 周期型(通胀敏感)

    def __init__(self, data_source):
        """
        初始化行业轮动分析器

        Args:
            data_source: 数据源实例 (USStockDataSource)
        """
        self.data_source = data_source

    def analyze_sector_rotation(
        self,
        periods: List[int] = [1, 5, 20, 60],
        benchmark_symbol: str = 'SPY'
    ) -> Dict:
        """
        完整行业轮动分析

        Args:
            periods: 要分析的周期列表(天数)
            benchmark_symbol: 基准指数代码(用于计算相对强度)

        Returns:
            行业轮动分析结果
        """
        try:
            # 1. 获取所有行业ETF数据
            sector_data = self._get_all_sector_data(period="1y")

            if not sector_data:
                return {'error': '行业ETF数据获取失败'}

            # 2. 获取基准数据
            benchmark_df = self.data_source.get_us_stock_hist(benchmark_symbol, period="1y")

            result = {
                'timestamp': datetime.now(),
                'performance': self.get_sector_performance(sector_data, periods),
                'strength': self.calculate_sector_strength(sector_data, benchmark_df, periods),
                'pattern': self.identify_rotation_pattern(sector_data, periods),
                'allocation': None  # 稍后添加
            }

            # 3. 基于当前模式生成配置建议
            if result['pattern']:
                result['allocation'] = self.generate_sector_allocation(result['pattern'])

            return result

        except Exception as e:
            logger.error(f"行业轮动分析失败: {str(e)}")
            return {'error': str(e)}

    def _get_all_sector_data(self, period: str = "1y") -> Dict[str, pd.DataFrame]:
        """
        批量获取所有行业ETF数据

        Args:
            period: 历史数据周期

        Returns:
            {ETF代码: DataFrame} 字典
        """
        sector_data = {}

        for etf_code in self.SECTOR_ETFS.keys():
            try:
                df = self.data_source.get_us_stock_hist(etf_code, period=period)
                if not df.empty:
                    sector_data[etf_code] = df
                    logger.debug(f"{etf_code} ({self.SECTOR_ETFS[etf_code]}) 数据获取成功")
                else:
                    logger.warning(f"{etf_code} 数据为空")
            except Exception as e:
                logger.error(f"获取{etf_code}数据失败: {str(e)}")
                continue

        logger.info(f"成功获取 {len(sector_data)}/{len(self.SECTOR_ETFS)} 个行业ETF数据")
        return sector_data

    def get_sector_performance(
        self,
        sector_data: Dict[str, pd.DataFrame],
        periods: List[int] = [1, 5, 20, 60]
    ) -> pd.DataFrame:
        """
        计算各行业表现

        Args:
            sector_data: 行业ETF数据字典
            periods: 计算周期列表

        Returns:
            行业表现DataFrame
        """
        performance = []

        for etf_code, df in sector_data.items():
            if df.empty or len(df) < max(periods):
                continue

            row = {
                'etf_code': etf_code,
                'sector_name': self.SECTOR_ETFS[etf_code],
                'latest_price': float(df['close'].iloc[-1])
            }

            # 计算各周期涨跌幅
            for period in periods:
                if len(df) >= period + 1:
                    current_price = df['close'].iloc[-1]
                    past_price = df['close'].iloc[-(period + 1)]
                    ret = (current_price - past_price) / past_price * 100
                    row[f'{period}d_return'] = float(ret)

            performance.append(row)

        df_perf = pd.DataFrame(performance)

        # 按20日涨跌幅排序
        if '20d_return' in df_perf.columns:
            df_perf = df_perf.sort_values('20d_return', ascending=False)

        return df_perf

    def calculate_sector_strength(
        self,
        sector_data: Dict[str, pd.DataFrame],
        benchmark_df: pd.DataFrame,
        periods: List[int] = [20, 60]
    ) -> pd.DataFrame:
        """
        计算行业相对强度 (RS = 行业涨幅 / 基准涨幅)

        Args:
            sector_data: 行业ETF数据
            benchmark_df: 基准指数数据
            periods: 计算周期

        Returns:
            行业相对强度DataFrame
        """
        if benchmark_df.empty:
            logger.warning("基准数据为空,无法计算相对强度")
            return pd.DataFrame()

        strength_data = []

        for etf_code, df in sector_data.items():
            if df.empty or len(df) < max(periods):
                continue

            row = {
                'etf_code': etf_code,
                'sector_name': self.SECTOR_ETFS[etf_code]
            }

            for period in periods:
                if len(df) >= period + 1 and len(benchmark_df) >= period + 1:
                    # 行业涨幅
                    sector_ret = (df['close'].iloc[-1] - df['close'].iloc[-(period + 1)]) / df['close'].iloc[-(period + 1)]

                    # 基准涨幅
                    benchmark_ret = (benchmark_df['close'].iloc[-1] - benchmark_df['close'].iloc[-(period + 1)]) / benchmark_df['close'].iloc[-(period + 1)]

                    # 相对强度
                    rs = (sector_ret / benchmark_ret) if benchmark_ret != 0 else 1.0
                    row[f'rs_{period}d'] = float(rs)

                    # RS评级
                    if rs > 1.2:
                        rating = "强势"
                    elif rs > 1.05:
                        rating = "偏强"
                    elif rs > 0.95:
                        rating = "中性"
                    elif rs > 0.8:
                        rating = "偏弱"
                    else:
                        rating = "弱势"

                    row[f'rating_{period}d'] = rating

            strength_data.append(row)

        df_strength = pd.DataFrame(strength_data)

        # 按20日RS排序
        if 'rs_20d' in df_strength.columns:
            df_strength = df_strength.sort_values('rs_20d', ascending=False)

        return df_strength

    def identify_rotation_pattern(
        self,
        sector_data: Dict[str, pd.DataFrame],
        periods: List[int] = [20]
    ) -> Dict:
        """
        识别行业轮动模式

        Args:
            sector_data: 行业ETF数据
            periods: 分析周期

        Returns:
            轮动模式字典
        """
        if not sector_data:
            return {}

        # 使用20日周期判断
        period = periods[0] if periods else 20

        # 计算各行业涨跌幅
        sector_returns = {}
        for etf_code, df in sector_data.items():
            if df.empty or len(df) < period + 1:
                continue

            ret = (df['close'].iloc[-1] - df['close'].iloc[-(period + 1)]) / df['close'].iloc[-(period + 1)]
            sector_returns[etf_code] = ret

        if not sector_returns:
            return {}

        # 计算进攻型/防守型/周期型行业平均表现
        offensive_perf = np.mean([sector_returns.get(s, 0) for s in self.OFFENSIVE_SECTORS if s in sector_returns])
        defensive_perf = np.mean([sector_returns.get(s, 0) for s in self.DEFENSIVE_SECTORS if s in sector_returns])
        cyclical_perf = np.mean([sector_returns.get(s, 0) for s in self.CYCLICAL_SECTORS if s in sector_returns])

        # 统计上涨/下跌行业数量
        up_count = sum(1 for ret in sector_returns.values() if ret > 0)
        total_count = len(sector_returns)

        # 识别轮动模式
        if offensive_perf > defensive_perf * 1.2:
            pattern = "进攻模式"
            description = "进攻型行业(科技/消费/金融)走强,市场风险偏好上升"
            market_sentiment = "风险偏好"
            phase = "牛市特征"
        elif defensive_perf > offensive_perf * 1.2:
            pattern = "防守模式"
            description = "防守型行业(医疗/必需消费/公用事业)走强,市场避险情绪上升"
            market_sentiment = "风险厌恶"
            phase = "熊市特征"
        elif cyclical_perf > max(offensive_perf, defensive_perf) * 1.15:
            pattern = "周期模式"
            description = "周期型行业(能源/材料)走强,通胀预期上升或经济复苏"
            market_sentiment = "通胀预期"
            phase = "经济扩张"
        elif up_count >= total_count * 0.8:
            pattern = "普涨模式"
            description = f"{up_count}/{total_count}个行业上涨,市场整体向好"
            market_sentiment = "全面乐观"
            phase = "强势上涨"
        elif up_count <= total_count * 0.3:
            pattern = "普跌模式"
            description = f"仅{up_count}/{total_count}个行业上涨,市场整体疲软"
            market_sentiment = "全面悲观"
            phase = "深度调整"
        else:
            pattern = "分化模式"
            description = "行业表现分化,市场方向不明"
            market_sentiment = "观望"
            phase = "震荡整理"

        return {
            'pattern': pattern,
            'description': description,
            'market_sentiment': market_sentiment,
            'market_phase': phase,
            'offensive_performance': float(offensive_perf * 100),
            'defensive_performance': float(defensive_perf * 100),
            'cyclical_performance': float(cyclical_perf * 100),
            'up_count': up_count,
            'total_count': total_count,
            'breadth': float(up_count / total_count * 100) if total_count > 0 else 0
        }

    def generate_sector_allocation(self, pattern_info: Dict) -> Dict:
        """
        基于轮动模式生成行业配置建议

        Args:
            pattern_info: 轮动模式信息

        Returns:
            配置建议字典
        """
        pattern = pattern_info.get('pattern', '分化模式')

        # 根据不同模式给出配置建议
        if pattern == "进攻模式":
            allocation = {
                '科技(XLK)': 35,
                '可选消费(XLY)': 20,
                '金融(XLF)': 15,
                '工业(XLI)': 10,
                '通讯(XLC)': 10,
                '其他': 10
            }
            strategy = "加配进攻型行业,享受牛市红利"

        elif pattern == "防守模式":
            allocation = {
                '医疗(XLV)': 30,
                '必需消费(XLP)': 25,
                '公用事业(XLU)': 20,
                '房地产(XLRE)': 10,
                '其他': 15
            }
            strategy = "转向防守型行业,降低风险"

        elif pattern == "周期模式":
            allocation = {
                '能源(XLE)': 25,
                '材料(XLB)': 20,
                '工业(XLI)': 20,
                '金融(XLF)': 15,
                '科技(XLK)': 15,
                '其他': 5
            }
            strategy = "配置周期型行业,抓住经济扩张机会"

        elif pattern == "普涨模式":
            allocation = {
                '科技(XLK)': 25,
                '金融(XLF)': 15,
                '医疗(XLV)': 15,
                '可选消费(XLY)': 15,
                '工业(XLI)': 10,
                '其他': 20
            }
            strategy = "均衡配置,重点配置龙头行业"

        elif pattern == "普跌模式":
            allocation = {
                '必需消费(XLP)': 35,
                '医疗(XLV)': 30,
                '公用事业(XLU)': 20,
                '现金': 15
            }
            strategy = "防守为主,保留现金,等待机会"

        else:  # 分化模式
            allocation = {
                '科技(XLK)': 20,
                '医疗(XLV)': 20,
                '金融(XLF)': 15,
                '必需消费(XLP)': 15,
                '其他': 30
            }
            strategy = "均衡配置,兼顾进攻与防守"

        return {
            'allocation': allocation,
            'strategy': strategy,
            'rebalance_frequency': '月度调整',
            'notes': f"基于当前'{pattern}'制定的配置方案"
        }


def test_sector_analyzer():
    """测试行业轮动分析器"""
    print("=" * 80)
    print("行业轮动分析器测试")
    print("=" * 80)

    from src.data_sources.us_stock_source import USStockDataSource

    data_source = USStockDataSource()
    analyzer = SectorRotationAnalyzer(data_source)

    # 完整行业轮动分析
    print("\n测试行业轮动分析...")
    result = analyzer.analyze_sector_rotation(periods=[1, 5, 20, 60])

    if 'error' not in result:
        # 行业表现
        perf = result.get('performance')
        if perf is not None and not perf.empty:
            print(f"\n行业表现排名 (20日涨跌幅):")
            print(f"  {'排名':<4} {'行业':<12} {'1日':<8} {'5日':<8} {'20日':<8} {'60日':<8}")
            print(f"  {'-'*50}")
            for idx, row in perf.iterrows():
                if idx >= 5:  # 只显示前5
                    break
                print(f"  {idx+1:<4} {row['sector_name']:<12} "
                      f"{row.get('1d_return', 0):>6.2f}% "
                      f"{row.get('5d_return', 0):>6.2f}% "
                      f"{row.get('20d_return', 0):>6.2f}% "
                      f"{row.get('60d_return', 0):>6.2f}%")

        # 轮动模式
        pattern = result.get('pattern', {})
        if pattern:
            print(f"\n轮动模式识别:")
            print(f"  模式: {pattern.get('pattern', 'N/A')}")
            print(f"  描述: {pattern.get('description', 'N/A')}")
            print(f"  市场情绪: {pattern.get('market_sentiment', 'N/A')}")
            print(f"  市场阶段: {pattern.get('market_phase', 'N/A')}")
            print(f"  上涨行业: {pattern.get('up_count', 0)}/{pattern.get('total_count', 0)} ({pattern.get('breadth', 0):.1f}%)")

        # 配置建议
        allocation = result.get('allocation', {})
        if allocation and 'allocation' in allocation:
            print(f"\n配置建议:")
            print(f"  策略: {allocation.get('strategy', 'N/A')}")
            print(f"  配置方案:")
            for sector, weight in allocation['allocation'].items():
                print(f"    {sector}: {weight}%")

    else:
        print(f"\n分析失败: {result.get('error', '未知错误')}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    test_sector_analyzer()
