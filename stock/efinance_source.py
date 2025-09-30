#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Efinance (东方财富) 数据源
免费实时行情数据接口
响应速度快，适合实时监控
"""

import efinance as ef
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class EfinanceDataSource:
    """Efinance (东方财富) 数据源"""

    def __init__(self):
        pass

    def get_market_data(self, date: str = None) -> Optional[Dict]:
        """
        获取市场数据

        Args:
            date: 日期，格式YYYYMMDD或YYYY-MM-DD，默认为今天

        Returns:
            包含市场数据的字典
        """
        data = {}

        try:
            # 获取主要指数数据
            indices = {
                'sz_index': '000001',     # 上证指数
                'sz_component': '399001',  # 深证成指
                'cyb_index': '399006'      # 创业板指
            }

            for name, code in indices.items():
                index_data = self._get_index_data(code)
                data[name] = index_data

            # 获取涨跌停数据
            limit_up, limit_down = self._get_limit_stocks()
            data['limit_up'] = limit_up
            data['limit_down'] = limit_down

            data['timestamp'] = datetime.now()

            return data

        except Exception as e:
            logger.error(f"Efinance获取市场数据失败: {str(e)}")
            return None

    def _get_index_data(self, code: str) -> Optional[pd.DataFrame]:
        """
        获取指数实时数据

        Args:
            code: 指数代码，如 000001

        Returns:
            指数数据DataFrame
        """
        try:
            # 获取实时行情
            quote = ef.stock.get_quote_history(code, beg='20000101')

            if quote is None or quote.empty:
                logger.warning(f"指数{code}数据为空")
                return None

            # 取最新一条数据
            latest = quote.iloc[-1]

            result = pd.DataFrame({
                '收盘': [latest['收盘']],
                '涨跌幅': [latest['涨跌幅']],
                '成交量': [latest['成交量']],
                '成交额': [latest['成交额']]
            })

            return result

        except Exception as e:
            logger.error(f"获取指数{code}数据异常: {str(e)}")
            return None

    def get_realtime_data(self) -> Optional[Dict]:
        """
        获取实时市场数据（简化版，更快）

        Returns:
            实时市场数据字典
        """
        try:
            data = {}

            # 获取主要指数实时行情
            indices_codes = ['000001', '399001', '399006']
            quotes = ef.stock.get_realtime_quotes(indices_codes)

            if quotes is not None and not quotes.empty:
                # 上证指数
                sz_quote = quotes[quotes['股票代码'] == '000001']
                if not sz_quote.empty:
                    data['sz_index'] = pd.DataFrame({
                        '收盘': [sz_quote['最新价'].iloc[0]],
                        '涨跌幅': [sz_quote['涨跌幅'].iloc[0]]
                    })

                # 深证成指
                sz_comp_quote = quotes[quotes['股票代码'] == '399001']
                if not sz_comp_quote.empty:
                    data['sz_component'] = pd.DataFrame({
                        '收盘': [sz_comp_quote['最新价'].iloc[0]],
                        '涨跌幅': [sz_comp_quote['涨跌幅'].iloc[0]]
                    })

                # 创业板指
                cyb_quote = quotes[quotes['股票代码'] == '399006']
                if not cyb_quote.empty:
                    data['cyb_index'] = pd.DataFrame({
                        '收盘': [cyb_quote['最新价'].iloc[0]],
                        '涨跌幅': [cyb_quote['涨跌幅'].iloc[0]]
                    })

            # 获取涨跌停数据
            limit_up, limit_down = self._get_limit_stocks()
            data['limit_up'] = limit_up
            data['limit_down'] = limit_down

            data['timestamp'] = datetime.now()

            return data

        except Exception as e:
            logger.error(f"Efinance获取实时数据失败: {str(e)}")
            return None

    def _get_limit_stocks(self) -> tuple:
        """
        获取涨跌停股票

        Returns:
            (涨停DataFrame, 跌停DataFrame)
        """
        try:
            # efinance 提供涨停板数据
            # 注意：efinance的接口可能会变化，这里使用常见的方法

            # 获取所有A股实时数据
            all_stocks = ef.stock.get_realtime_quotes()

            if all_stocks is None or all_stocks.empty:
                return pd.DataFrame(), pd.DataFrame()

            # 筛选涨停股票（涨跌幅 >= 9.8%，留一点余量）
            limit_up = all_stocks[all_stocks['涨跌幅'] >= 9.8].copy()

            # 筛选跌停股票（涨跌幅 <= -9.8%）
            limit_down = all_stocks[all_stocks['涨跌幅'] <= -9.8].copy()

            return limit_up, limit_down

        except Exception as e:
            logger.error(f"获取涨跌停数据异常: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()

    def get_stock_data(self, code: str, beg: str = None,
                       end: str = None, klt: int = 101) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据

        Args:
            code: 股票代码，如 600000
            beg: 开始日期，格式YYYYMMDD，默认19900101
            end: 结束日期，格式YYYYMMDD，默认今天
            klt: K线类型，1=1分钟，5=5分钟，15=15分钟，30=30分钟，60=60分钟，
                 101=日K，102=周K，103=月K

        Returns:
            股票历史数据DataFrame
        """
        try:
            if beg is None:
                beg = '19900101'
            if end is None:
                end = datetime.now().strftime('%Y%m%d')

            # 转换日期格式 YYYY-MM-DD -> YYYYMMDD
            if '-' in str(beg):
                beg = beg.replace('-', '')
            if '-' in str(end):
                end = end.replace('-', '')

            df = ef.stock.get_quote_history(code, beg=beg, end=end, klt=klt)

            return df

        except Exception as e:
            logger.error(f"获取股票{code}数据异常: {str(e)}")
            return None

    def get_stock_realtime(self, codes: List[str]) -> Optional[pd.DataFrame]:
        """
        获取多只股票实时行情

        Args:
            codes: 股票代码列表

        Returns:
            实时行情DataFrame
        """
        try:
            quotes = ef.stock.get_realtime_quotes(codes)
            return quotes

        except Exception as e:
            logger.error(f"获取实时行情异常: {str(e)}")
            return None

    def get_all_stock_codes(self) -> Optional[pd.DataFrame]:
        """
        获取所有A股股票代码

        Returns:
            股票列表DataFrame
        """
        try:
            # 获取沪深京A股列表
            stocks = ef.stock.get_realtime_quotes()

            if stocks is not None and not stocks.empty:
                # 只保留需要的列
                result = stocks[['股票代码', '股票名称']].copy()
                return result
            else:
                return None

        except Exception as e:
            logger.error(f"获取股票列表异常: {str(e)}")
            return None

    def get_market_summary(self) -> Optional[Dict]:
        """
        获取市场概览（快速版本）

        Returns:
            市场概览字典
        """
        try:
            summary = {}

            # 获取三大指数实时行情
            indices_codes = ['000001', '399001', '399006']
            quotes = ef.stock.get_realtime_quotes(indices_codes)

            if quotes is not None and not quotes.empty:
                for _, row in quotes.iterrows():
                    code = row['股票代码']
                    if code == '000001':
                        summary['sz_index'] = {
                            'name': '上证指数',
                            'price': row['最新价'],
                            'change_pct': row['涨跌幅']
                        }
                    elif code == '399001':
                        summary['sz_component'] = {
                            'name': '深证成指',
                            'price': row['最新价'],
                            'change_pct': row['涨跌幅']
                        }
                    elif code == '399006':
                        summary['cyb_index'] = {
                            'name': '创业板指',
                            'price': row['最新价'],
                            'change_pct': row['涨跌幅']
                        }

            # 获取涨跌停统计
            all_stocks = ef.stock.get_realtime_quotes()
            if all_stocks is not None and not all_stocks.empty:
                limit_up_count = len(all_stocks[all_stocks['涨跌幅'] >= 9.8])
                limit_down_count = len(all_stocks[all_stocks['涨跌幅'] <= -9.8])

                summary['limit_up_count'] = limit_up_count
                summary['limit_down_count'] = limit_down_count
                summary['total_stocks'] = len(all_stocks)

            summary['timestamp'] = datetime.now()

            return summary

        except Exception as e:
            logger.error(f"获取市场概览失败: {str(e)}")
            return None


def test_efinance():
    """测试Efinance数据源"""
    source = EfinanceDataSource()

    print("=" * 60)
    print("测试Efinance数据源")
    print("=" * 60)

    # 测试实时数据获取（快速）
    print("\n1. 获取实时市场数据（快速版）...")
    realtime_data = source.get_realtime_data()

    if realtime_data:
        print("✓ 实时数据获取成功")

        for index_name in ['sz_index', 'sz_component', 'cyb_index']:
            index_data = realtime_data.get(index_name)
            if index_data is not None and not index_data.empty:
                print(f"\n{index_name}:")
                print(f"  收盘: {index_data['收盘'].iloc[0]:.2f}")
                print(f"  涨跌幅: {index_data['涨跌幅'].iloc[0]:.2f}%")

        print(f"\n涨停股票数: {len(realtime_data.get('limit_up', []))}")
        print(f"跌停股票数: {len(realtime_data.get('limit_down', []))}")
    else:
        print("✗ 实时数据获取失败")

    # 测试市场概览
    print("\n2. 获取市场概览...")
    summary = source.get_market_summary()

    if summary:
        print("✓ 市场概览获取成功")
        print(f"  涨停: {summary.get('limit_up_count', 0)} 只")
        print(f"  跌停: {summary.get('limit_down_count', 0)} 只")
        print(f"  总股票数: {summary.get('total_stocks', 0)} 只")
    else:
        print("✗ 市场概览获取失败")

    # 测试单只股票数据
    print("\n3. 获取平安银行(000001)最近5天数据...")
    stock_data = source.get_stock_data('000001', klt=101)

    if stock_data is not None and not stock_data.empty:
        print(f"✓ 获取到 {len(stock_data)} 条数据")
        print(stock_data.tail(5))
    else:
        print("✗ 股票数据获取失败")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_efinance()