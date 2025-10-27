#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的 akshare 数据源 - 使用稳定接口
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class OptimizedAkshareSource:
    """优化的 akshare 数据源"""

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存

    def get_market_data(self) -> Optional[Dict]:
        """获取市场数据 - 使用稳定的 akshare 接口"""
        try:
            logger.info("开始获取 akshare 市场数据 (优化版)...")

            data = {}

            # 1. 获取全市场股票数据 (新浪源，较稳定)
            market_data = self._get_market_summary_optimized()
            data['market_summary'] = market_data

            # 2. 获取指数数据 (从市场数据中提取)
            index_data = self._extract_index_data(market_data)
            data.update(index_data)

            # 3. 获取涨跌停数据 (东财源，较快)
            limit_data = self._get_limit_data_optimized()
            data.update(limit_data)

            data['timestamp'] = datetime.now()
            logger.info("akshare 数据获取成功 (优化版)")

            return data

        except Exception as e:
            logger.error(f"akshare 优化版数据获取失败: {str(e)}")
            return None

    def _get_market_summary_optimized(self) -> pd.DataFrame:
        """获取市场概况 - 使用稳定接口"""
        cache_key = "market_summary"

        # 检查缓存
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                logger.info("使用缓存的市场数据")
                return cached_data

        try:
            # 使用新浪数据源 (已测试可用)
            logger.info("获取新浪A股市场数据...")
            df = ak.stock_zh_a_spot()

            if df is not None and not df.empty:
                # 缓存数据
                self.cache[cache_key] = (datetime.now(), df)
                logger.info(f"新浪数据获取成功: {len(df)} 只股票")
                return df
            else:
                logger.warning("新浪数据为空")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取新浪市场数据失败: {str(e)}")
            return pd.DataFrame()

    def _extract_index_data(self, market_df: pd.DataFrame) -> Dict:
        """从市场数据中提取指数信息"""
        index_data = {
            'sz_index': None,
            'sz_component': None,
            'cyb_index': None
        }

        if market_df.empty:
            return index_data

        try:
            # 主要指数代码映射
            index_codes = {
                'sz_index': '000001',      # 上证指数
                'sz_component': '399001',  # 深证成指
                'cyb_index': '399006'      # 创业板指
            }

            for name, code in index_codes.items():
                # 从市场数据中查找指数
                index_row = market_df[market_df['代码'] == code]

                if not index_row.empty:
                    row = index_row.iloc[0]
                    index_data[name] = pd.DataFrame({
                        '收盘': [row['最新价']],
                        '涨跌幅': [row['涨跌幅']]  # 已经是百分比
                    })
                    logger.info(f"提取指数 {name}: {row['最新价']:.2f} ({row['涨跌幅']:+.2f}%)")
                else:
                    logger.warning(f"未找到指数 {name} ({code})")

        except Exception as e:
            logger.warning(f"提取指数数据失败: {str(e)}")

        return index_data

    def _get_limit_data_optimized(self) -> Dict:
        """获取涨跌停数据 - 使用稳定接口"""
        limit_data = {
            'limit_up': pd.DataFrame(),
            'limit_down': pd.DataFrame()
        }

        today = datetime.now().strftime("%Y%m%d")

        # 获取涨停数据 (已测试可用)
        try:
            logger.info("获取涨停股池数据...")
            limit_up = ak.stock_zt_pool_em(date=today)
            if limit_up is not None and not limit_up.empty:
                limit_data['limit_up'] = limit_up
                logger.info(f"涨停股池: {len(limit_up)} 只")
            else:
                logger.info("今日无涨停股票")
        except Exception as e:
            logger.warning(f"获取涨停数据失败: {str(e)}")

        # 跌停数据接口可能不存在，尝试其他方式
        try:
            # 从市场数据中筛选跌停股票
            market_df = self._get_market_summary_optimized()
            if not market_df.empty:
                # 筛选跌幅超过9.5%的股票作为跌停股票
                down_stocks = market_df[market_df['涨跌幅'] <= -9.5]
                if not down_stocks.empty:
                    limit_data['limit_down'] = down_stocks
                    logger.info(f"跌停股票: {len(down_stocks)} 只")
                else:
                    logger.info("今日无跌停股票")
        except Exception as e:
            logger.warning(f"筛选跌停股票失败: {str(e)}")

        return limit_data

    def test_stability(self) -> Dict:
        """测试接口稳定性"""
        results = {}

        # 测试市场数据接口
        start_time = time.time()
        try:
            market_df = self._get_market_summary_optimized()
            duration = time.time() - start_time
            results['market_summary'] = {
                'success': not market_df.empty,
                'duration': duration,
                'count': len(market_df) if not market_df.empty else 0
            }
        except Exception as e:
            results['market_summary'] = {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }

        # 测试涨停接口
        start_time = time.time()
        try:
            today = datetime.now().strftime("%Y%m%d")
            limit_up = ak.stock_zt_pool_em(date=today)
            duration = time.time() - start_time
            results['limit_up'] = {
                'success': limit_up is not None,
                'duration': duration,
                'count': len(limit_up) if limit_up is not None and not limit_up.empty else 0
            }
        except Exception as e:
            results['limit_up'] = {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }

        return results


def test_optimized_akshare():
    """测试优化的 akshare 数据源"""
    print("🔍 测试优化的 akshare 数据源...")

    source = OptimizedAkshareSource()

    # 稳定性测试
    print("\n📊 接口稳定性测试:")
    stability = source.test_stability()

    for interface, result in stability.items():
        if result['success']:
            print(f"✅ {interface}: 成功 ({result['duration']:.2f}s, {result.get('count', 0)}条数据)")
        else:
            print(f"❌ {interface}: 失败 - {result.get('error', '未知错误')}")

    # 完整数据获取测试
    print(f"\n📈 完整数据获取测试:")
    start_time = time.time()
    data = source.get_market_data()
    duration = time.time() - start_time

    if data:
        print(f"✅ 完整数据获取成功 ({duration:.2f}s)")

        # 显示指数数据
        for index_name in ['sz_index', 'sz_component', 'cyb_index']:
            index_df = data.get(index_name)
            if index_df is not None and not index_df.empty:
                price = index_df['收盘'].iloc[0]
                change = index_df['涨跌幅'].iloc[0]
                print(f"   {index_name}: {price:.2f} ({change:+.2f}%)")

        # 显示涨跌停统计
        limit_up_count = len(data.get('limit_up', []))
        limit_down_count = len(data.get('limit_down', []))
        print(f"   涨停: {limit_up_count} 只")
        print(f"   跌停: {limit_down_count} 只")

        # 显示市场概况统计
        market_df = data.get('market_summary')
        if market_df is not None and not market_df.empty:
            print(f"   总股票数: {len(market_df)} 只")
    else:
        print(f"❌ 完整数据获取失败 ({duration:.2f}s)")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    test_optimized_akshare()