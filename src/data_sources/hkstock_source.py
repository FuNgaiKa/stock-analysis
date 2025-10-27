#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股数据源模块 - 基于 AKShare
提供港股指数、个股、资金流向、AH股溢价等数据
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class HKStockDataSource:
    """港股数据源 - 使用 AKShare"""

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
        logger.info("港股数据源初始化完成")

    def get_hk_index_daily(
        self,
        symbol: str = "HSI",
        period: str = "daily",
        adjust: str = ""
    ) -> pd.DataFrame:
        """
        获取港股指数历史数据

        Args:
            symbol: 指数代码
                - HSI: 恒生指数
                - HSCEI: 恒生国企指数
                - HSTECH: 恒生科技指数
            period: 周期 (daily/weekly/monthly)
            adjust: 复权类型 (qfq前复权/hfq后复权/空字符串不复权)

        Returns:
            DataFrame with columns: [日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额]
        """
        cache_key = f"hk_index_{symbol}_{period}"

        # 检查缓存
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                logger.info(f"使用缓存的{symbol}指数数据")
                return cached_data

        try:
            logger.info(f"获取港股指数数据: {symbol} ({period})")
            df = ak.stock_hk_index_daily_em(symbol=symbol)

            if df is not None and not df.empty:
                # AKShare返回的列名: date, open, high, low, latest
                # 标准化列名: latest -> close
                if 'latest' in df.columns:
                    df = df.rename(columns={'latest': 'close'})

                # 确保有date列
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date').sort_index()

                # 如果没有volume列，添加空列（港股指数数据可能不包含成交量）
                if 'volume' not in df.columns:
                    df['volume'] = 0
                if 'amount' not in df.columns:
                    df['amount'] = 0

                # 缓存数据
                self.cache[cache_key] = (datetime.now(), df)
                logger.info(f"{symbol}数据获取成功: {len(df)} 条记录")
                return df
            else:
                logger.warning(f"{symbol}数据为空")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取{symbol}指数数据失败: {str(e)}")
            return pd.DataFrame()

    def get_hk_stock_spot(self) -> pd.DataFrame:
        """
        获取港股实时行情

        Returns:
            DataFrame with columns: [代码, 名称, 最新价, 涨跌额, 涨跌幅, ...]
        """
        cache_key = "hk_stock_spot"

        # 检查缓存
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                logger.info("使用缓存的港股实时行情")
                return cached_data

        try:
            logger.info("获取港股实时行情...")
            df = ak.stock_hk_spot_em()

            if df is not None and not df.empty:
                self.cache[cache_key] = (datetime.now(), df)
                logger.info(f"港股实时行情获取成功: {len(df)} 只股票")
                return df
            else:
                logger.warning("港股实时行情为空")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取港股实时行情失败: {str(e)}")
            return pd.DataFrame()

    def get_hk_stock_hist(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = "",
        end_date: str = "",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取港股个股历史数据

        Args:
            symbol: 股票代码 (如 "00700" 腾讯控股)
            period: 周期 (daily/weekly/monthly)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型

        Returns:
            DataFrame with columns: [日期, 开盘, 收盘, 最高, 最低, 成交量, ...]
        """
        try:
            logger.info(f"获取港股个股历史数据: {symbol}")
            df = ak.stock_hk_hist(
                symbol=symbol,
                period=period,
                start_date=start_date if start_date else "20200101",
                end_date=end_date if end_date else datetime.now().strftime("%Y%m%d"),
                adjust=adjust
            )

            if df is not None and not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期').sort_index()
                logger.info(f"{symbol}历史数据获取成功: {len(df)} 条记录")
                return df
            else:
                logger.warning(f"{symbol}历史数据为空")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取{symbol}历史数据失败: {str(e)}")
            return pd.DataFrame()

    def get_south_capital_flow(self, days: int = 30) -> pd.DataFrame:
        """
        获取南向资金流向数据 (港股通)

        Args:
            days: 获取最近N天的数据

        Returns:
            DataFrame with columns: [日期, 沪港通, 深港通, 南向资金, ...]
        """
        cache_key = f"south_capital_flow_{days}"

        # 检查缓存
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                logger.info("使用缓存的南向资金数据")
                return cached_data

        try:
            logger.info(f"获取南向资金流向数据 (最近{days}天)...")

            # 获取沪深港通资金流向
            df = ak.stock_hsgt_fund_flow_summary_em()

            if df is not None and not df.empty:
                # 筛选南向数据
                df_south = df[df['资金方向'] == '南向'].copy()
                df_south['交易日'] = pd.to_datetime(df_south['交易日'])
                df_south = df_south.sort_values('交易日', ascending=False).head(days)

                self.cache[cache_key] = (datetime.now(), df_south)
                logger.info(f"南向资金数据获取成功: {len(df_south)} 条记录")
                return df_south
            else:
                logger.warning("南向资金数据为空")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取南向资金数据失败: {str(e)}")
            return pd.DataFrame()

    def get_ah_price_comparison(self) -> pd.DataFrame:
        """
        获取AH股比价数据

        Returns:
            DataFrame with columns: [代码, A股代码, H股代码, A股价格, H股价格, 溢价率, ...]
        """
        cache_key = "ah_price_comparison"

        # 检查缓存
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                logger.info("使用缓存的AH股比价数据")
                return cached_data

        try:
            logger.info("获取AH股比价数据...")
            df = ak.stock_zh_ah_spot()

            if df is not None and not df.empty:
                self.cache[cache_key] = (datetime.now(), df)
                logger.info(f"AH股比价数据获取成功: {len(df)} 只股票")
                return df
            else:
                logger.warning("AH股比价数据为空")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取AH股比价数据失败: {str(e)}")
            return pd.DataFrame()

    def get_ah_premium_index_history(self) -> pd.DataFrame:
        """
        获取AH股溢价指数历史数据

        Returns:
            DataFrame with columns: [日期, AH股溢价指数]
        """
        cache_key = "ah_premium_index"

        # 检查缓存
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                logger.info("使用缓存的AH溢价指数数据")
                return cached_data

        try:
            logger.info("获取AH股溢价指数历史数据...")
            df = ak.stock_zh_ah_index_em()

            if df is not None and not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期').sort_index()

                self.cache[cache_key] = (datetime.now(), df)
                logger.info(f"AH溢价指数数据获取成功: {len(df)} 条记录")
                return df
            else:
                logger.warning("AH溢价指数数据为空")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取AH溢价指数失败: {str(e)}")
            return pd.DataFrame()

    def get_hk_main_board_list(self) -> pd.DataFrame:
        """
        获取港股主板股票列表

        Returns:
            DataFrame with columns: [股票代码, 股票名称, ...]
        """
        try:
            logger.info("获取港股主板股票列表...")
            df = ak.stock_hk_main_board_spot_em()

            if df is not None and not df.empty:
                logger.info(f"港股主板列表获取成功: {len(df)} 只股票")
                return df
            else:
                logger.warning("港股主板列表为空")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取港股主板列表失败: {str(e)}")
            return pd.DataFrame()

    def get_hk_stock_statistics(self, symbol: str) -> Dict:
        """
        获取港股个股统计数据

        Args:
            symbol: 股票代码

        Returns:
            统计数据字典
        """
        try:
            # 获取历史数据计算统计指标
            df = self.get_hk_stock_hist(symbol, period="daily")

            if df.empty:
                return {}

            latest = df.iloc[-1]

            # 计算统计指标
            stats = {
                'symbol': symbol,
                'latest_price': float(latest['收盘']),
                'change_pct': float((latest['收盘'] - df.iloc[-2]['收盘']) / df.iloc[-2]['收盘'] * 100) if len(df) > 1 else 0,
                'volume_latest': float(latest['成交量']),
                'volume_ma5': float(df['成交量'].tail(5).mean()),
                'volume_ma20': float(df['成交量'].tail(20).mean()),
                'price_ma20': float(df['收盘'].tail(20).mean()),
                'price_ma60': float(df['收盘'].tail(60).mean()),
                'high_52w': float(df['最高'].tail(252).max()),
                'low_52w': float(df['最低'].tail(252).min())
            }

            return stats

        except Exception as e:
            logger.error(f"获取{symbol}统计数据失败: {str(e)}")
            return {}

    def get_market_summary(self) -> Dict:
        """
        获取港股市场概况

        Returns:
            市场概况数据字典
        """
        try:
            logger.info("获取港股市场概况...")

            summary = {
                'timestamp': datetime.now(),
                'market': 'HK'
            }

            # 1. 恒生指数数据
            hsi_df = self.get_hk_index_daily("HSI")
            if not hsi_df.empty:
                hsi_latest = hsi_df.iloc[-1]
                hsi_prev = hsi_df.iloc[-2] if len(hsi_df) > 1 else hsi_latest
                summary['hsi'] = {
                    'close': float(hsi_latest['close']),
                    'change': float(hsi_latest['close'] - hsi_prev['close']),
                    'change_pct': float((hsi_latest['close'] - hsi_prev['close']) / hsi_prev['close'] * 100),
                    'volume': float(hsi_latest['volume'])
                }

            # 2. 恒生科技指数
            hstech_df = self.get_hk_index_daily("HSTECH")
            if not hstech_df.empty:
                tech_latest = hstech_df.iloc[-1]
                tech_prev = hstech_df.iloc[-2] if len(hstech_df) > 1 else tech_latest
                summary['hstech'] = {
                    'close': float(tech_latest['close']),
                    'change': float(tech_latest['close'] - tech_prev['close']),
                    'change_pct': float((tech_latest['close'] - tech_prev['close']) / tech_prev['close'] * 100)
                }

            # 3. 南向资金
            south_df = self.get_south_capital_flow(days=5)
            if not south_df.empty:
                latest_flow = south_df.iloc[0]
                summary['south_capital'] = {
                    'today_inflow': float(latest_flow.get('当日资金流向', 0)),
                    'cumulative_5d': float(south_df['当日资金流向'].sum()) if '当日资金流向' in south_df.columns else 0
                }

            # 4. AH溢价指数
            ah_df = self.get_ah_premium_index_history()
            if not ah_df.empty:
                summary['ah_premium'] = {
                    'index': float(ah_df.iloc[-1]['AH股溢价指数']),
                    'percentile': float((ah_df['AH股溢价指数'] < ah_df.iloc[-1]['AH股溢价指数']).sum() / len(ah_df))
                }

            # 5. 市场广度（涨跌家数）
            spot_df = self.get_hk_stock_spot()
            if not spot_df.empty:
                up_count = len(spot_df[spot_df['涨跌幅'] > 0])
                down_count = len(spot_df[spot_df['涨跌幅'] < 0])
                summary['market_breadth'] = {
                    'total': len(spot_df),
                    'up_count': up_count,
                    'down_count': down_count,
                    'up_ratio': float(up_count / len(spot_df))
                }

            logger.info("港股市场概况获取成功")
            return summary

        except Exception as e:
            logger.error(f"获取港股市场概况失败: {str(e)}")
            return {'timestamp': datetime.now(), 'market': 'HK', 'error': str(e)}


def test_hk_data_source():
    """测试港股数据源"""
    print("=" * 70)
    print("港股数据源测试")
    print("=" * 70)

    source = HKStockDataSource()

    # 1. 测试恒生指数历史数据
    print("\n1. 测试恒生指数历史数据")
    hsi_df = source.get_hk_index_daily("HSI")
    if not hsi_df.empty:
        print(f"   [OK] 恒生指数数据: {len(hsi_df)} 条记录")
        print(f"   最新收盘: {hsi_df.iloc[-1]['close']:.2f}")
        print(f"   数据范围: {hsi_df.index[0].date()} 至 {hsi_df.index[-1].date()}")
    else:
        print("   [FAIL] 恒生指数数据获取失败")

    # 2. 测试南向资金
    print("\n2. 测试南向资金流向")
    south_df = source.get_south_capital_flow(days=5)
    if not south_df.empty:
        print(f"   [OK] 南向资金数据: {len(south_df)} 条记录")
        if '当日资金流向' in south_df.columns:
            print(f"   最近5日累计: {south_df['当日资金流向'].sum():.2f} 亿元")
    else:
        print("   [FAIL] 南向资金数据获取失败")

    # 3. 测试AH股溢价
    print("\n3. 测试AH股溢价指数")
    ah_df = source.get_ah_premium_index_history()
    if not ah_df.empty:
        print(f"   [OK] AH溢价指数数据: {len(ah_df)} 条记录")
        print(f"   当前指数: {ah_df.iloc[-1]['AH股溢价指数']:.2f}")
    else:
        print("   [FAIL] AH溢价指数数据获取失败")

    # 4. 测试市场概况
    print("\n4. 测试市场概况")
    summary = source.get_market_summary()
    if summary and 'error' not in summary:
        print(f"   [OK] 市场概况获取成功")
        if 'hsi' in summary:
            print(f"   恒生指数: {summary['hsi']['close']:.2f} ({summary['hsi']['change_pct']:+.2f}%)")
        if 'market_breadth' in summary:
            print(f"   市场广度: {summary['market_breadth']['up_count']}/{summary['market_breadth']['total']} 上涨")
    else:
        print(f"   [FAIL] 市场概况获取失败: {summary.get('error', '未知错误')}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_hk_data_source()
