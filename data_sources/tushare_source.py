#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare 数据源 - 最稳定的选择
需要配置 token
"""

import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TushareDataSource:
    """Tushare 专业数据源"""

    def __init__(self, token: str = None):
        """
        初始化 Tushare 数据源

        Args:
            token: Tushare token，如果不提供则使用默认配置
        """
        if token:
            ts.set_token(token)

        try:
            self.pro = ts.pro_api()
            self.token_valid = True
            logger.info("Tushare 数据源初始化成功")
        except Exception as e:
            logger.error(f"Tushare 初始化失败: {str(e)}")
            self.pro = None
            self.token_valid = False

    def get_market_summary(self) -> Dict:
        """获取市场概况"""
        if not self.token_valid:
            return {}

        try:
            data = {}
            today = datetime.now().strftime('%Y%m%d')

            # 获取主要指数数据
            indices = {
                'sz_index': '000001.SH',    # 上证综指
                'sz_component': '399001.SZ', # 深证成指
                'cyb_index': '399006.SZ'     # 创业板指
            }

            for name, ts_code in indices.items():
                try:
                    # 获取指数日线数据
                    df = self.pro.index_daily(ts_code=ts_code, end_date=today, limit=2)
                    if not df.empty:
                        latest = df.iloc[0]
                        prev = df.iloc[1] if len(df) > 1 else latest

                        # 计算涨跌幅
                        change_pct = (latest['close'] - prev['close']) / prev['close'] * 100

                        data[name] = pd.DataFrame({
                            '收盘': [latest['close']],
                            '涨跌幅': [change_pct],
                            '成交量': [latest['vol']],
                            '成交额': [latest['amount']]
                        })
                        logger.info(f"获取 {name} 成功: {latest['close']:.2f} ({change_pct:+.2f}%)")
                    else:
                        data[name] = None
                        logger.warning(f"获取 {name} 数据为空")

                except Exception as e:
                    logger.warning(f"获取指数 {name} 失败: {str(e)}")
                    data[name] = None

            # 获取涨跌停数据
            try:
                # 涨停股票
                limit_up_df = self.pro.limit_list_d(trade_date=today, limit_type='U')
                data['limit_up'] = limit_up_df if not limit_up_df.empty else pd.DataFrame()

                # 跌停股票
                limit_down_df = self.pro.limit_list_d(trade_date=today, limit_type='D')
                data['limit_down'] = limit_down_df if not limit_down_df.empty else pd.DataFrame()

                logger.info(f"涨跌停数据: 涨停{len(data['limit_up'])}只, 跌停{len(data['limit_down'])}只")

            except Exception as e:
                logger.warning(f"获取涨跌停数据失败: {str(e)}")
                data['limit_up'] = pd.DataFrame()
                data['limit_down'] = pd.DataFrame()

            data['timestamp'] = datetime.now()
            return data

        except Exception as e:
            logger.error(f"获取市场数据失败: {str(e)}")
            return {}

    def get_stock_basic_info(self, limit: int = 100) -> pd.DataFrame:
        """获取股票基本信息"""
        if not self.token_valid:
            return pd.DataFrame()

        try:
            df = self.pro.stock_basic(exchange='', list_status='L', limit=limit)
            return df
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {str(e)}")
            return pd.DataFrame()

    def get_daily_data(self, ts_code: str, days: int = 20) -> pd.DataFrame:
        """获取个股日线数据"""
        if not self.token_valid:
            return pd.DataFrame()

        try:
            end_date = datetime.now().strftime('%Y%m%d')
            df = self.pro.daily(ts_code=ts_code, end_date=end_date, limit=days)
            return df.sort_values('trade_date').reset_index(drop=True)
        except Exception as e:
            logger.error(f"获取 {ts_code} 日线数据失败: {str(e)}")
            return pd.DataFrame()

    def test_connection(self) -> bool:
        """测试连接"""
        if not self.token_valid:
            return False

        try:
            # 简单测试：获取股票基本信息
            df = self.pro.stock_basic(limit=1)
            return not df.empty
        except Exception as e:
            logger.warning(f"连接测试失败: {str(e)}")
            return False


def test_tushare_source():
    """测试 tushare 数据源"""
    print("🔍 测试 Tushare 数据源...")

    # 使用你的 token
    token = "031dcac5944b21aa209828f616aa0130153f9886a945c8a5d64c0486"
    source = TushareDataSource(token=token)

    if not source.token_valid:
        print("❌ Tushare token 无效")
        return

    # 测试连接
    if source.test_connection():
        print("✅ Tushare 连接成功")
    else:
        print("⚠️ Tushare 积分不足，但可以尝试免费接口")

    # 获取市场概况
    print("\n📊 获取市场数据:")
    market_data = source.get_market_summary()

    if market_data:
        for key, df in market_data.items():
            if key in ['sz_index', 'sz_component', 'cyb_index'] and df is not None and not df.empty:
                price = df['收盘'].iloc[0]
                change = df['涨跌幅'].iloc[0]
                print(f"   {key}: {price:.2f} ({change:+.2f}%)")

        print(f"\n   涨停股票: {len(market_data.get('limit_up', []))} 只")
        print(f"   跌停股票: {len(market_data.get('limit_down', []))} 只")
    else:
        print("   获取市场数据失败")

    # 测试股票基本信息
    print("\n📋 股票基本信息测试:")
    basic_info = source.get_stock_basic_info(limit=5)
    if not basic_info.empty:
        print(f"   获取到 {len(basic_info)} 只股票基本信息")
        print(f"   示例: {basic_info[['ts_code', 'name', 'industry']].head(3).to_dict('records')}")
    else:
        print("   获取股票基本信息失败")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    test_tushare_source()