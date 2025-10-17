#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baostock (证券宝) 数据源
免费、开源的Python证券数据接口
适合历史数据回测
"""

import baostock as bs
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BaostockDataSource:
    """Baostock数据源"""

    def __init__(self):
        self.logged_in = False
        self._login()

    def _login(self):
        """登录Baostock系统"""
        try:
            lg = bs.login()
            if lg.error_code == '0':
                self.logged_in = True
                logger.info("Baostock登录成功")
            else:
                logger.error(f"Baostock登录失败: {lg.error_msg}")
        except Exception as e:
            logger.error(f"Baostock登录异常: {str(e)}")

    def _logout(self):
        """登出Baostock系统"""
        if self.logged_in:
            bs.logout()
            self.logged_in = False

    def __del__(self):
        """析构函数，自动登出"""
        self._logout()

    def get_market_data(self, date: str = None) -> Optional[Dict]:
        """
        获取市场数据

        Args:
            date: 日期，格式YYYY-MM-DD，默认为今天

        Returns:
            包含市场数据的字典
        """
        if not self.logged_in:
            self._login()

        if not self.logged_in:
            return None

        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        else:
            # 转换日期格式 YYYYMMDD -> YYYY-MM-DD
            if len(date) == 8 and date.isdigit():
                date = f"{date[:4]}-{date[4:6]}-{date[6:]}"

        data = {}

        try:
            # 获取主要指数数据
            indices = {
                'sz_index': 'sh.000001',     # 上证指数
                'sz_component': 'sz.399001',  # 深证成指
                'cyb_index': 'sz.399006'      # 创业板指
            }

            for name, code in indices.items():
                index_data = self._get_index_data(code, date)
                data[name] = index_data

            # Baostock没有直接的涨跌停数据接口
            # 可以通过全市场扫描实现，但比较耗时
            # 这里暂时返回空DataFrame，由其他数据源补充
            data['limit_up'] = pd.DataFrame()
            data['limit_down'] = pd.DataFrame()

            # 获取全市场股票列表和价格（可选，比较耗时）
            # data['all_stocks'] = self._get_all_stocks_data(date)

            return data

        except Exception as e:
            logger.error(f"Baostock获取市场数据失败: {str(e)}")
            return None

    def _get_index_data(self, code: str, date: str) -> Optional[pd.DataFrame]:
        """
        获取指数数据

        Args:
            code: 指数代码，如 sh.000001
            date: 日期

        Returns:
            指数数据DataFrame
        """
        try:
            # 获取最近5天的数据
            end_date = datetime.strptime(date, '%Y-%m-%d')
            start_date = end_date - timedelta(days=7)  # 多取几天以防节假日

            rs = bs.query_history_k_data_plus(
                code,
                "date,code,close,pctChg,volume,amount",
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=date,
                frequency="d",
                adjustflag="3"  # 不复权
            )

            if rs.error_code != '0':
                logger.error(f"查询指数{code}失败: {rs.error_msg}")
                return None

            # 转换为DataFrame
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return None

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 数据类型转换
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['pctChg'] = pd.to_numeric(df['pctChg'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

            # 取最后一条数据
            if not df.empty:
                latest = df.iloc[-1]
                result = pd.DataFrame({
                    '收盘': [latest['close']],
                    '涨跌幅': [latest['pctChg']],
                    '成交量': [latest['volume']],
                    '成交额': [latest['amount']]
                })
                return result
            else:
                return None

        except Exception as e:
            logger.error(f"获取指数{code}数据异常: {str(e)}")
            return None

    def get_stock_data(self, code: str, start_date: str = None,
                       end_date: str = None, frequency: str = 'd') -> Optional[pd.DataFrame]:
        """
        获取股票历史数据

        Args:
            code: 股票代码，如 sh.600000
            start_date: 开始日期，格式YYYY-MM-DD
            end_date: 结束日期，格式YYYY-MM-DD
            frequency: 频率 d=日，w=周，m=月，5=5分钟，15=15分钟，30=30分钟，60=60分钟

        Returns:
            股票历史数据DataFrame
        """
        if not self.logged_in:
            self._login()

        if not self.logged_in:
            return None

        try:
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag="3"  # 不复权
            )

            if rs.error_code != '0':
                logger.error(f"查询股票{code}失败: {rs.error_msg}")
                return None

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return None

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 数据类型转换
            numeric_cols = ['open', 'high', 'low', 'close', 'preclose', 'volume',
                          'amount', 'turn', 'pctChg']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            df['date'] = pd.to_datetime(df['date'])

            return df

        except Exception as e:
            logger.error(f"获取股票{code}数据异常: {str(e)}")
            return None

    def get_all_stock_codes(self) -> Optional[pd.DataFrame]:
        """
        获取所有股票代码列表

        Returns:
            股票列表DataFrame
        """
        if not self.logged_in:
            self._login()

        if not self.logged_in:
            return None

        try:
            # 获取沪深A股股票列表
            rs = bs.query_all_stock(day=datetime.now().strftime('%Y-%m-%d'))

            if rs.error_code != '0':
                logger.error(f"查询股票列表失败: {rs.error_msg}")
                return None

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return None

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 只保留A股股票（code_name包含'sz'或'sh'的）
            df = df[df['code'].str.contains('sz.|sh.', na=False)]

            return df

        except Exception as e:
            logger.error(f"获取股票列表异常: {str(e)}")
            return None


def test_baostock():
    """测试Baostock数据源"""
    source = BaostockDataSource()

    print("=" * 60)
    print("测试Baostock数据源")
    print("=" * 60)

    # 测试市场数据获取
    print("\n1. 获取市场数据...")
    market_data = source.get_market_data()

    if market_data:
        print("✓ 市场数据获取成功")

        for index_name in ['sz_index', 'sz_component', 'cyb_index']:
            index_data = market_data.get(index_name)
            if index_data is not None and not index_data.empty:
                print(f"\n{index_name}:")
                print(f"  收盘: {index_data['收盘'].iloc[0]:.2f}")
                print(f"  涨跌幅: {index_data['涨跌幅'].iloc[0]:.2f}%")
    else:
        print("✗ 市场数据获取失败")

    # 测试单只股票数据获取
    print("\n2. 获取平安银行(sz.000001)最近10天数据...")
    stock_data = source.get_stock_data(
        'sz.000001',
        start_date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    )

    if stock_data is not None and not stock_data.empty:
        print(f"✓ 获取到 {len(stock_data)} 条数据")
        print(stock_data.tail())
    else:
        print("✗ 股票数据获取失败")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_baostock()