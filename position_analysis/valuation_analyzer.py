#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
估值分析器 - 增强版
提供个股、行业、指数的估值分析及历史分位数计算

根据数据源测试结果，优先实现可用功能：
✅ 可用: stock_a_ttm_lyr (全市场PE/PB)
✅ 可用: stock_market_pe_lg (指数历史PE，但列名是'平均市盈率')
✅ 可用: stock_board_industry_name_em (行业列表和实时数据)
❌ 不可用: stock_zh_valuation_baidu (个股估值 - 接口失效)
❌ 不可用: stock_index_pe_lg (行业PE - 参数错误)
"""

import pandas as pd
import numpy as np
import akshare as ak
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class ValuationAnalyzer:
    """估值分析器 - 提供多维度估值分析"""

    def __init__(self):
        self._cache = {}
        logger.info("估值分析器初始化完成")

    def get_index_valuation_history(
        self,
        index_name: str = "上证",
        lookback_months: int = 120  # 默认10年
    ) -> pd.DataFrame:
        """
        获取指数历史估值时序数据（用于回测和分位数计算）

        Args:
            index_name: 指数名称 ('上证', '深证', '沪深300')
            lookback_months: 回溯月数

        Returns:
            包含日期、指数点位、平均市盈率的DataFrame
        """
        try:
            cache_key = f"index_pe_{index_name}_{lookback_months}"
            if cache_key in self._cache:
                return self._cache[cache_key].copy()

            # 获取历史PE数据
            df = ak.stock_market_pe_lg(symbol=index_name)

            # 数据清洗
            df = df.rename(columns={
                '日期': 'date',
                '指数': 'index',
                '平均市盈率': 'pe'
            })
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            # 过滤时间范围
            cutoff_date = datetime.now() - timedelta(days=lookback_months * 30)
            df = df[df.index >= cutoff_date]

            # 计算PE分位数
            df['pe_percentile'] = df['pe'].rank(pct=True)

            # 缓存
            self._cache[cache_key] = df.copy()

            logger.info(f"{index_name}指数历史PE数据: {len(df)} 条")
            return df

        except Exception as e:
            logger.error(f"获取{index_name}指数历史PE失败: {str(e)}")
            return pd.DataFrame()

    def get_current_index_valuation(self, index_name: str = "上证") -> Dict:
        """
        获取指数当前估值及历史分位数

        Returns:
            {
                'current_pe': 当前PE,
                'pe_percentile_10y': PE历史分位数(近10年),
                'pe_percentile_all': PE全历史分位数,
                'valuation_level': 估值水平,
                'is_undervalued': 是否低估,
                'is_overvalued': 是否高估
            }
        """
        try:
            # 获取历史数据
            df_10y = self.get_index_valuation_history(index_name, lookback_months=120)
            df_all = self.get_index_valuation_history(index_name, lookback_months=600)  # 50年

            if len(df_10y) == 0:
                return {}

            # 当前PE
            current_pe = df_10y['pe'].iloc[-1]

            # 10年分位数
            pe_pct_10y = df_10y['pe_percentile'].iloc[-1]

            # 全历史分位数
            if len(df_all) > 0:
                pe_pct_all = (df_all['pe'] < current_pe).sum() / len(df_all)
            else:
                pe_pct_all = pe_pct_10y

            # 估值水平分类
            valuation_level = self._classify_valuation_level(pe_pct_10y)

            return {
                'index_name': index_name,
                'current_pe': float(current_pe),
                'pe_percentile_10y': float(pe_pct_10y),
                'pe_percentile_all': float(pe_pct_all),
                'valuation_level': valuation_level,
                'is_undervalued': pe_pct_10y < 0.3,  # 30%分位以下为低估
                'is_overvalued': pe_pct_10y > 0.7,   # 70%分位以上为高估
                'data_date': df_10y.index[-1].strftime('%Y-%m-%d')
            }

        except Exception as e:
            logger.error(f"获取{index_name}当前估值失败: {str(e)}")
            return {}

    def get_market_valuation_comprehensive(self) -> Dict:
        """
        获取全市场综合估值（A股整体PE/PB + 分位数）

        Returns:
            {
                'pe_ttm': 市盈率TTM中位数,
                'pe_percentile_10y': PE近10年分位数,
                'pb': 市净率中位数,
                'pb_percentile_10y': PB近10年分位数,
                'valuation_score': 综合估值得分(-1到+1),
                'valuation_level': 估值水平分类
            }
        """
        try:
            # 获取A股整体估值数据
            df_pe = ak.stock_a_ttm_lyr()
            df_pe['date'] = pd.to_datetime(df_pe['date'])
            df_pe = df_pe.set_index('date').sort_index()

            df_pb = ak.stock_a_all_pb()
            df_pb['date'] = pd.to_datetime(df_pb['date'])
            df_pb = df_pb.set_index('date').sort_index()

            # 提取最新数据
            latest_pe = df_pe.iloc[-1]
            latest_pb = df_pb.iloc[-1]

            pe_ttm = float(latest_pe['middlePETTM'])
            pe_pct_10y = float(latest_pe['quantileInRecent10YearsMiddlePeTtm'])

            pb = float(latest_pb['middlePB'])
            pb_pct_10y = float(latest_pb['quantileInRecent10YearsMiddlePB'])

            # 综合估值得分 (分位数越低越好)
            avg_pct = (pe_pct_10y + pb_pct_10y) / 2
            valuation_score = (0.5 - avg_pct) * 2  # -1到+1

            # 估值水平分类
            valuation_level = self._classify_valuation_level(avg_pct)

            return {
                'pe_ttm': pe_ttm,
                'pe_percentile_all': float(latest_pe['quantileInAllHistoryMiddlePeTtm']),
                'pe_percentile_10y': pe_pct_10y,
                'pb': pb,
                'pb_percentile_all': float(latest_pb['quantileInAllHistoryMiddlePB']),
                'pb_percentile_10y': pb_pct_10y,
                'valuation_score': float(valuation_score),
                'valuation_level': valuation_level,
                'is_undervalued': avg_pct < 0.3,
                'is_overvalued': avg_pct > 0.7,
                'data_date': latest_pe.name.strftime('%Y-%m-%d')
            }

        except Exception as e:
            logger.error(f"获取全市场估值失败: {str(e)}")
            return {}

    def get_industry_valuation_comparison(self, top_n: int = 10) -> pd.DataFrame:
        """
        获取行业估值对比（基于实时行情数据）

        Args:
            top_n: 返回前N个行业

        Returns:
            行业估值对比DataFrame，按市值排序
        """
        try:
            # 获取行业实时数据
            df = ak.stock_board_industry_name_em()

            # 数据清洗
            df = df.rename(columns={
                '板块名称': 'industry_name',
                '板块代码': 'industry_code',
                '最新价': 'price',
                '涨跌幅': 'change_pct',
                '总市值': 'market_cap',
                '换手率': 'turnover_rate',
                '上涨家数': 'up_count',
                '下跌家数': 'down_count'
            })

            # 计算行业强度指标
            df['strength_score'] = (
                df['change_pct'] * 0.3 +
                df['turnover_rate'] * 0.2 +
                (df['up_count'] / (df['up_count'] + df['down_count'] + 1)) * 50 * 0.5
            )

            # 排序
            df = df.sort_values('market_cap', ascending=False).head(top_n)

            logger.info(f"成功获取 {len(df)} 个行业估值对比数据")
            return df[['industry_name', 'price', 'change_pct', 'market_cap',
                      'turnover_rate', 'up_count', 'down_count', 'strength_score']]

        except Exception as e:
            logger.error(f"获取行业估值对比失败: {str(e)}")
            return pd.DataFrame()

    def get_historical_pe_at_date(
        self,
        index_name: str,
        target_date: datetime
    ) -> Optional[float]:
        """
        获取指定日期的历史PE（用于回测中的估值过滤）

        Args:
            index_name: 指数名称
            target_date: 目标日期

        Returns:
            该日期的PE值，如果没有则返回None
        """
        try:
            df = self.get_index_valuation_history(index_name)

            if len(df) == 0:
                return None

            # 查找最接近的日期
            closest_date = df.index[df.index <= target_date]
            if len(closest_date) == 0:
                return None

            pe = df.loc[closest_date[-1], 'pe']
            return float(pe)

        except Exception as e:
            logger.warning(f"获取{target_date}的历史PE失败: {str(e)}")
            return None

    def calculate_pe_percentile_at_date(
        self,
        index_name: str,
        target_date: datetime,
        lookback_years: int = 10
    ) -> Optional[float]:
        """
        计算指定日期的PE历史分位数（用于多维度历史匹配）

        Args:
            index_name: 指数名称
            target_date: 目标日期
            lookback_years: 向前回溯年数

        Returns:
            PE分位数 (0-1)
        """
        try:
            df = self.get_index_valuation_history(index_name)

            if len(df) == 0:
                return None

            # 筛选截止到target_date的数据
            df_historical = df[df.index <= target_date]

            if len(df_historical) == 0:
                return None

            # 计算分位数
            cutoff_date = target_date - timedelta(days=lookback_years * 365)
            df_window = df_historical[df_historical.index >= cutoff_date]

            if len(df_window) < 10:  # 样本量太少
                return None

            current_pe = df_historical.loc[df_historical.index[-1], 'pe']
            percentile = (df_window['pe'] < current_pe).sum() / len(df_window)

            return float(percentile)

        except Exception as e:
            logger.warning(f"计算{target_date}的PE分位数失败: {str(e)}")
            return None

    def compare_valuation_with_history(
        self,
        index_name: str = "上证",
        reference_dates: List[str] = None
    ) -> pd.DataFrame:
        """
        将当前估值与历史关键时点对比

        Args:
            index_name: 指数名称
            reference_dates: 参考日期列表（如['2007-10-16', '2015-06-12', '2020-07-06']）

        Returns:
            对比结果DataFrame
        """
        if reference_dates is None:
            # 默认参考点：历史重要时刻
            reference_dates = [
                '2007-10-16',  # 6124点
                '2015-06-12',  # 5178点
                '2018-01-29',  # 3587点
                '2020-07-06',  # 3400点
                '2021-02-10'   # 3731点
            ]

        try:
            df_history = self.get_index_valuation_history(index_name, lookback_months=240)
            current_valuation = self.get_current_index_valuation(index_name)

            if len(df_history) == 0 or not current_valuation:
                return pd.DataFrame()

            results = []

            # 当前估值
            results.append({
                'date': current_valuation['data_date'],
                'period': '当前',
                'index_value': df_history['index'].iloc[-1],
                'pe': current_valuation['current_pe'],
                'pe_percentile': current_valuation['pe_percentile_10y'],
                'valuation_level': current_valuation['valuation_level']
            })

            # 历史参考点
            for ref_date in reference_dates:
                try:
                    ref_datetime = pd.to_datetime(ref_date)
                    if ref_datetime not in df_history.index:
                        # 找最近的日期
                        closest = df_history.index[df_history.index <= ref_datetime]
                        if len(closest) == 0:
                            continue
                        ref_datetime = closest[-1]

                    row = df_history.loc[ref_datetime]
                    results.append({
                        'date': ref_datetime.strftime('%Y-%m-%d'),
                        'period': ref_date,
                        'index_value': row['index'],
                        'pe': row['pe'],
                        'pe_percentile': row['pe_percentile'],
                        'valuation_level': self._classify_valuation_level(row['pe_percentile'])
                    })
                except:
                    continue

            return pd.DataFrame(results)

        except Exception as e:
            logger.error(f"估值历史对比失败: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def _classify_valuation_level(percentile: float) -> str:
        """估值水平分类"""
        if percentile < 0.2:
            return "极低估值"
        elif percentile < 0.4:
            return "低估值"
        elif percentile < 0.6:
            return "合理估值"
        elif percentile < 0.8:
            return "高估值"
        else:
            return "极高估值"


if __name__ == '__main__':
    # 测试
    print("=" * 70)
    print("估值分析器测试")
    print("=" * 70)

    analyzer = ValuationAnalyzer()

    # 1. 全市场估值
    print("\n1. 全市场综合估值")
    market_val = analyzer.get_market_valuation_comprehensive()
    for k, v in market_val.items():
        print(f"  {k}: {v}")

    # 2. 上证指数当前估值
    print("\n2. 上证指数当前估值")
    index_val = analyzer.get_current_index_valuation("上证")
    for k, v in index_val.items():
        print(f"  {k}: {v}")

    # 3. 历史估值对比
    print("\n3. 当前估值 vs 历史关键时点")
    comparison = analyzer.compare_valuation_with_history()
    if len(comparison) > 0:
        print(comparison.to_string(index=False))

    # 4. 行业估值对比
    print("\n4. 行业估值对比（TOP 5）")
    industry = analyzer.get_industry_valuation_comparison(top_n=5)
    if len(industry) > 0:
        print(industry.to_string(index=False))

    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
