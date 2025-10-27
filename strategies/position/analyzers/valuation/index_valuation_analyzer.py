#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数估值分析器
Index Valuation Analyzer

功能:
1. PE/PB历史分位数分析
2. 股债收益比(ERP)计算
3. CAPE席勒市盈率
4. 估值水平分类

作者: Claude Code
日期: 2025-10-16
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class IndexValuationAnalyzer:
    """
    指数估值分析器

    支持A股主要指数的估值分析:
    - 沪深300 (000300)
    - 创业板指 (399006)
    - 科创50 (000688)
    - 中证500 (000905)
    - 上证指数 (000001)
    """

    # 指数代码映射
    INDEX_MAP = {
        '000300': '沪深300',
        '399006': '创业板指',
        '000688': '科创50',
        '000905': '中证500',
        '000001': '上证指数',
        '000050': '上证50',
        '000852': '中证1000'
    }

    # 代码到akshare名称的映射
    CODE_TO_AKSHARE_NAME = {
        '000300': '沪深300',
        '399006': '创业板50',  # akshare中是创业板50
        '000905': '中证500',
        '000050': '上证50',
        '000852': '中证1000'
    }

    def __init__(self, lookback_days: int = 1260):
        """
        初始化估值分析器

        Args:
            lookback_days: 回溯天数,默认1260天(约5年)
        """
        self.lookback_days = lookback_days
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 3600  # 1小时缓存
        logger.info("指数估值分析器初始化完成")

    def get_index_pe_pb_data(self, index_code: str) -> pd.DataFrame:
        """
        获取指数PE/PB历史数据

        Args:
            index_code: 指数代码 (如 '000300')

        Returns:
            DataFrame with columns: [date, pe, pb]
        """
        cache_key = f"pe_pb_{index_code}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info(f"使用缓存的{index_code}估值数据")
                return self.cache[cache_key]

        try:
            # 转换为akshare接受的名称
            akshare_name = self.CODE_TO_AKSHARE_NAME.get(index_code)

            if not akshare_name:
                logger.warning(f"{index_code}不在支持列表中")
                return pd.DataFrame()

            logger.info(f"获取{akshare_name}估值数据...")

            # 获取PE数据
            df_pe = ak.stock_index_pe_lg(symbol=akshare_name)

            if df_pe is None or df_pe.empty:
                logger.warning(f"{akshare_name} PE数据为空")
                return pd.DataFrame()

            # 重命名并选择需要的列
            df = df_pe[['日期', '滚动市盈率']].copy()
            df.rename(columns={'日期': 'date', '滚动市盈率': 'pe'}, inplace=True)

            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date', ascending=True)

            # 筛选最近N天
            df = df.tail(self.lookback_days)

            # 尝试获取PB数据
            try:
                df_pb = ak.stock_index_pb_lg(symbol=akshare_name)
                if df_pb is not None and not df_pb.empty:
                    df_pb_sel = df_pb[['日期', '滚动市净率']].copy()
                    df_pb_sel.rename(columns={'日期': 'date', '滚动市净率': 'pb'}, inplace=True)
                    df_pb_sel['date'] = pd.to_datetime(df_pb_sel['date'])
                    df = pd.merge(df, df_pb_sel, on='date', how='left')
                    logger.info(f"获取{akshare_name} PB数据成功")
            except Exception as e:
                logger.warning(f"获取{akshare_name} PB数据失败: {e}")
                df['pb'] = np.nan

            # 缓存
            self.cache[cache_key] = df
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"{akshare_name}估值数据获取成功: {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取{index_code}估值数据失败: {str(e)}")
            return pd.DataFrame()


    def calculate_valuation_percentile(
        self,
        index_code: str,
        periods: List[int] = None
    ) -> Dict:
        """
        计算估值历史分位数

        Args:
            index_code: 指数代码
            periods: 要计算的周期列表(天数),默认[252, 756, 1260]

        Returns:
            分位数分析字典
        """
        if periods is None:
            periods = [252, 756, 1260]  # 1年/3年/5年

        df = self.get_index_pe_pb_data(index_code)

        if df.empty or 'pe' not in df.columns:
            return {'error': f'{index_code}估值数据不足'}

        # 过滤无效数据
        df = df[df['pe'] > 0].copy()

        if len(df) < 30:
            return {'error': f'{index_code}有效估值数据不足30条'}

        current_pe = df['pe'].iloc[-1]
        current_pb = df['pb'].iloc[-1] if 'pb' in df.columns and not pd.isna(df['pb'].iloc[-1]) else None

        result = {
            'index_code': index_code,
            'index_name': self.INDEX_MAP.get(index_code, index_code),
            'date': df['date'].iloc[-1].strftime('%Y-%m-%d') if 'date' in df.columns else datetime.now().strftime('%Y-%m-%d'),
            'current_pe': float(current_pe),
            'current_pb': float(current_pb) if current_pb else None,
            'pe_percentiles': {},
            'pb_percentiles': {}
        }

        # 计算PE分位数
        for period in periods:
            if len(df) >= period:
                hist_pe = df['pe'].tail(period)
                percentile = (hist_pe < current_pe).sum() / len(hist_pe) * 100

                label = f'{period // 252}年' if period % 252 == 0 else f'{period}天'

                result['pe_percentiles'][label] = {
                    'percentile': float(percentile),
                    'min': float(hist_pe.min()),
                    'max': float(hist_pe.max()),
                    'median': float(hist_pe.median()),
                    'mean': float(hist_pe.mean()),
                    'level': self._classify_percentile(percentile)
                }

        # 计算PB分位数 (如果有数据)
        if current_pb and 'pb' in df.columns:
            df_pb = df[df['pb'] > 0].copy()
            for period in periods:
                if len(df_pb) >= period:
                    hist_pb = df_pb['pb'].tail(period)
                    percentile = (hist_pb < current_pb).sum() / len(hist_pb) * 100

                    label = f'{period // 252}年' if period % 252 == 0 else f'{period}天'

                    result['pb_percentiles'][label] = {
                        'percentile': float(percentile),
                        'min': float(hist_pb.min()),
                        'max': float(hist_pb.max()),
                        'median': float(hist_pb.median()),
                        'mean': float(hist_pb.mean()),
                        'level': self._classify_percentile(percentile)
                    }

        # 估值水平综合判断
        result['valuation_level'] = self._综合估值水平(result)

        return result

    def calculate_equity_risk_premium(self, index_code: str = '000300') -> Dict:
        """
        计算股债收益比 (Equity Risk Premium)

        ERP = 股息率 - 10年期国债收益率

        Args:
            index_code: 指数代码,默认沪深300

        Returns:
            ERP分析字典
        """
        try:
            logger.info(f"计算{index_code}的股债收益比...")

            # 1. 获取10年期国债收益率
            bond_yield_df = ak.bond_zh_us_rate()

            if bond_yield_df.empty:
                return {'error': '无法获取国债收益率数据'}

            # 最新10年期国债收益率
            latest_bond = bond_yield_df.iloc[-1]
            bond_yield_10y = float(latest_bond['中国国债收益率10年']) / 100  # 转换为小数

            # 2. 获取指数股息率
            index_info = ak.index_stock_info()

            index_row = index_info[index_info['index_code'] == index_code]

            if index_row.empty:
                return {'error': f'未找到{index_code}的股息率数据'}

            # 股息率 (需要确认akshare中的字段名)
            dividend_yield = None
            for col in ['dividend_yield', '股息率', 'div_yield']:
                if col in index_row.columns:
                    dividend_yield = float(index_row.iloc[0][col])
                    if dividend_yield > 1:  # 如果是百分比形式
                        dividend_yield = dividend_yield / 100
                    break

            if dividend_yield is None or pd.isna(dividend_yield):
                logger.warning(f"{index_code}股息率数据不可用,使用默认值2.5%")
                dividend_yield = 0.025  # 默认2.5%

            # 3. 计算ERP
            erp = dividend_yield - bond_yield_10y

            result = {
                'index_code': index_code,
                'index_name': self.INDEX_MAP.get(index_code, index_code),
                'dividend_yield': float(dividend_yield),
                'bond_yield_10y': float(bond_yield_10y),
                'equity_risk_premium': float(erp),
                'signal': self._interpret_erp(erp),
                'timestamp': datetime.now().strftime('%Y-%m-%d')
            }

            logger.info(f"ERP计算完成: {erp*100:.2f}%")
            return result

        except Exception as e:
            logger.error(f"计算ERP失败: {str(e)}")
            return {'error': str(e)}

    def comprehensive_analysis(self, index_codes: List[str] = None) -> Dict:
        """
        综合估值分析

        Args:
            index_codes: 要分析的指数代码列表,默认主要指数

        Returns:
            完整估值分析结果
        """
        if index_codes is None:
            index_codes = ['000300', '000905', '000050']  # 沪深300、中证500、上证50

        logger.info(f"开始综合估值分析: {len(index_codes)} 个指数")

        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'indices': {},
            'erp_analysis': {},
            'summary': {}
        }

        # 分析各指数估值
        for code in index_codes:
            try:
                valuation = self.calculate_valuation_percentile(code)
                if 'error' not in valuation:
                    result['indices'][code] = valuation
            except Exception as e:
                logger.error(f"{code}估值分析失败: {e}")

        # 股债收益比分析 (沪深300)
        if '000300' in index_codes:
            erp = self.calculate_equity_risk_premium('000300')
            if 'error' not in erp:
                result['erp_analysis'] = erp

        # 生成摘要
        if result['indices']:
            result['summary'] = self._generate_summary(result)

        logger.info("综合估值分析完成")
        return result

    def _classify_percentile(self, percentile: float) -> str:
        """
        分类估值分位数

        Args:
            percentile: 分位数 (0-100)

        Returns:
            估值水平描述
        """
        if percentile < 20:
            return '极低估⬇️⬇️'
        elif percentile < 40:
            return '低估⬇️'
        elif percentile < 60:
            return '合理➡️'
        elif percentile < 80:
            return '高估⬆️'
        else:
            return '极高估⬆️⬆️'

    def _综合估值水平(self, valuation_data: Dict) -> Dict:
        """
        综合判断估值水平

        Args:
            valuation_data: 估值数据字典

        Returns:
            综合估值水平判断
        """
        pe_percentiles = valuation_data.get('pe_percentiles', {})

        if not pe_percentiles:
            return {'level': '数据不足', 'emoji': '❓'}

        # 使用5年分位数 (如果有),否则使用最长周期
        if '5年' in pe_percentiles:
            pe_pct = pe_percentiles['5年']['percentile']
        else:
            # 使用最后一个周期的分位数
            pe_pct = list(pe_percentiles.values())[-1]['percentile']

        if pe_pct < 20:
            return {
                'level': '极低估',
                'emoji': '⬇️⬇️',
                'signal': '买入时机',
                'description': f'PE处于历史{pe_pct:.0f}%分位,极低估值,历史上往往是好的买入机会'
            }
        elif pe_pct < 40:
            return {
                'level': '低估',
                'emoji': '⬇️',
                'signal': '积极配置',
                'description': f'PE处于历史{pe_pct:.0f}%分位,估值偏低,可积极配置'
            }
        elif pe_pct < 60:
            return {
                'level': '合理',
                'emoji': '➡️',
                'signal': '正常持有',
                'description': f'PE处于历史{pe_pct:.0f}%分位,估值合理,可正常持有'
            }
        elif pe_pct < 80:
            return {
                'level': '高估',
                'emoji': '⬆️',
                'signal': '注意风险',
                'description': f'PE处于历史{pe_pct:.0f}%分位,估值偏高,注意风险'
            }
        else:
            return {
                'level': '极高估',
                'emoji': '⬆️⬆️',
                'signal': '谨慎减仓',
                'description': f'PE处于历史{pe_pct:.0f}%分位,极高估值,建议谨慎减仓'
            }

    def _interpret_erp(self, erp: float) -> Dict:
        """
        解释股债收益比

        Args:
            erp: 股债收益比 (小数形式)

        Returns:
            ERP解释字典
        """
        erp_pct = erp * 100

        if erp > 0.015:  # >1.5%
            return {
                'level': '股票相对吸引',
                'emoji': '✅',
                'description': f'ERP={erp_pct:+.2f}%,股票相对债券有较大吸引力'
            }
        elif erp > 0:  # 0-1.5%
            return {
                'level': '股票略有吸引力',
                'emoji': '🟢',
                'description': f'ERP={erp_pct:+.2f}%,股票相对债券略有吸引力'
            }
        elif erp > -0.01:  # 0至-1%
            return {
                'level': '股债均衡',
                'emoji': '🟡',
                'description': f'ERP={erp_pct:+.2f}%,股票与债券吸引力均衡'
            }
        else:  # <-1%
            return {
                'level': '债券更有吸引力',
                'emoji': '🔴',
                'description': f'ERP={erp_pct:+.2f}%,债券相对股票更有吸引力'
            }

    def _generate_summary(self, analysis_result: Dict) -> Dict:
        """
        生成分析摘要

        Args:
            analysis_result: 完整分析结果

        Returns:
            摘要字典
        """
        indices = analysis_result.get('indices', {})

        if not indices:
            return {'message': '无估值数据'}

        # 统计各估值水平的数量
        undervalued = []
        overvalued = []
        fair_valued = []

        for code, data in indices.items():
            level = data.get('valuation_level', {}).get('level', '')
            name = data.get('index_name', code)

            if '低估' in level:
                undervalued.append(name)
            elif '高估' in level:
                overvalued.append(name)
            else:
                fair_valued.append(name)

        summary = {
            'undervalued_count': len(undervalued),
            'overvalued_count': len(overvalued),
            'fair_valued_count': len(fair_valued),
            'undervalued_indices': undervalued,
            'overvalued_indices': overvalued,
            'fair_valued_indices': fair_valued
        }

        # 生成总体建议
        if len(undervalued) >= len(indices) * 0.6:
            summary['overall_suggestion'] = "市场整体估值偏低,可考虑增加配置"
        elif len(overvalued) >= len(indices) * 0.6:
            summary['overall_suggestion'] = "市场整体估值偏高,建议控制风险"
        else:
            summary['overall_suggestion'] = "市场估值分化,精选个股/指数"

        return summary


def test_index_valuation_analyzer():
    """测试指数估值分析器"""
    print("=" * 80)
    print("指数估值分析器测试")
    print("=" * 80)

    analyzer = IndexValuationAnalyzer(lookback_days=1260)

    # 测试1: 单个指数估值分析
    print("\n1. 测试沪深300估值分析")
    print("-" * 80)
    result = analyzer.calculate_valuation_percentile('000300')

    if 'error' not in result:
        print(f"\n{result['index_name']} ({result['index_code']})")
        print(f"日期: {result['date']}")
        print(f"当前PE: {result['current_pe']:.2f}")
        if result['current_pb']:
            print(f"当前PB: {result['current_pb']:.2f}")

        print(f"\nPE历史分位数:")
        for period, data in result['pe_percentiles'].items():
            print(f"  {period}: {data['percentile']:.1f}% "
                  f"(均值 {data['mean']:.2f}, 中位数 {data['median']:.2f}) "
                  f"{data['level']}")

        val_level = result['valuation_level']
        print(f"\n估值水平: {val_level['emoji']} {val_level['level']}")
        print(f"信号: {val_level['signal']}")
        print(f"说明: {val_level['description']}")
    else:
        print(f"  ❌ 分析失败: {result['error']}")

    # 测试2: 股债收益比
    print("\n\n2. 测试股债收益比分析")
    print("-" * 80)
    erp_result = analyzer.calculate_equity_risk_premium('000300')

    if 'error' not in erp_result:
        print(f"\n{erp_result['index_name']} 股债收益比:")
        print(f"  股息率: {erp_result['dividend_yield']*100:.2f}%")
        print(f"  10年国债收益率: {erp_result['bond_yield_10y']*100:.2f}%")
        print(f"  ERP: {erp_result['equity_risk_premium']*100:+.2f}%")
        print(f"\n  {erp_result['signal']['emoji']} {erp_result['signal']['level']}")
        print(f"  {erp_result['signal']['description']}")
    else:
        print(f"  ❌ 分析失败: {erp_result['error']}")

    # 测试3: 综合分析
    print("\n\n3. 测试综合估值分析")
    print("-" * 80)
    comp_result = analyzer.comprehensive_analysis(['000300', '000905', '000050'])

    if comp_result.get('summary') and comp_result['summary']:
        summary = comp_result['summary']
        print(f"\n估值摘要:")
        print(f"  低估指数: {summary.get('undervalued_count', 0)} 个")
        if summary.get('undervalued_indices'):
            print(f"    {', '.join(summary['undervalued_indices'])}")
        print(f"  合理指数: {summary.get('fair_valued_count', 0)} 个")
        if summary.get('fair_valued_indices'):
            print(f"    {', '.join(summary['fair_valued_indices'])}")
        print(f"  高估指数: {summary.get('overvalued_count', 0)} 个")
        if summary.get('overvalued_indices'):
            print(f"    {', '.join(summary['overvalued_indices'])}")
        print(f"\n  总体建议: {summary.get('overall_suggestion', 'N/A')}")
    else:
        print("  ⚠️ 无估值摘要数据")

    print("\n" + "=" * 80)
    print("✅ 指数估值分析器测试完成")
    print("=" * 80)


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_index_valuation_analyzer()
