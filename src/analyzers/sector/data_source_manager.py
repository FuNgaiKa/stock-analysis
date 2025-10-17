#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源管理器 - 支持多数据源自动切换
Data Source Manager with Auto Fallback

支持的数据源:
  - ashare: A股数据(轻量级，响应快)
  - yfinance: 国际市场数据(美股、港股、A股)
  - akshare: 全市场数据(功能全面)
  - finnhub: 美股专业数据(需API key，可选)
  - twelve_data: 多市场数据(需API key，可选)

作者: Claude Code
日期: 2025-10-16
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class DataSourceManager:
    """多数据源管理器 - 自动故障切换"""

    def __init__(self):
        """初始化数据源管理器"""
        self.cache = {}  # 数据缓存
        self.source_status = {}  # 数据源状态跟踪

        # 尝试加载各个数据源
        self._init_data_sources()

    def _init_data_sources(self):
        """初始化各数据源"""
        # 1. Ashare数据源
        try:
            from data_sources.Ashare import get_price
            self.ashare_get_price = get_price
            self.source_status['ashare'] = True
            logger.info("✓ Ashare数据源已就绪")
        except Exception as e:
            self.ashare_get_price = None
            self.source_status['ashare'] = False
            logger.warning(f"✗ Ashare数据源不可用: {str(e)}")

        # 2. yfinance数据源
        try:
            import yfinance as yf
            self.yfinance = yf
            self.source_status['yfinance'] = True
            logger.info("✓ yfinance数据源已就绪")
        except Exception as e:
            self.yfinance = None
            self.source_status['yfinance'] = False
            logger.warning(f"✗ yfinance数据源不可用: {str(e)}")

        # 3. akshare数据源
        try:
            import akshare as ak
            self.akshare = ak
            self.source_status['akshare'] = True
            logger.info("✓ akshare数据源已就绪")
        except Exception as e:
            self.akshare = None
            self.source_status['akshare'] = False
            logger.warning(f"✗ akshare数据源不可用: {str(e)}")

        # 4. finnhub数据源（可选，需要API key）
        try:
            import finnhub
            # 从环境变量读取API key
            import os
            api_key = os.getenv('FINNHUB_API_KEY')
            if api_key:
                self.finnhub = finnhub.Client(api_key=api_key)
                self.source_status['finnhub'] = True
                logger.info("✓ finnhub数据源已就绪")
            else:
                self.finnhub = None
                self.source_status['finnhub'] = False
                logger.debug("○ finnhub数据源未配置 (需要API key)")
        except Exception as e:
            self.finnhub = None
            self.source_status['finnhub'] = False
            logger.debug(f"○ finnhub数据源不可用: {str(e)}")

    def get_stock_data(
        self,
        symbol: str,
        period: str = "5y",
        market: str = "CN",
        prefer_source: str = None
    ) -> pd.DataFrame:
        """
        获取股票数据 - 支持多数据源自动切换

        Args:
            symbol: 股票代码
            period: 时间周期 (5y/3y/1y/6mo/3mo/1mo)
            market: 市场 (CN/HK/US)
            prefer_source: 优先使用的数据源 (ashare/yfinance/akshare)

        Returns:
            DataFrame with columns: open, high, low, close, volume, return
        """
        cache_key = f"{symbol}_{period}_{market}"

        # 检查缓存
        if cache_key in self.cache:
            logger.debug(f"使用缓存: {cache_key}")
            return self.cache[cache_key]

        # 确定数据源优先级
        source_priority = self._get_source_priority(market, prefer_source)

        # 依次尝试各数据源
        for source in source_priority:
            try:
                logger.info(f"尝试数据源: {source} (symbol={symbol}, period={period}, market={market})")

                if source == 'ashare':
                    df = self._fetch_ashare(symbol, period, market)
                elif source == 'yfinance':
                    df = self._fetch_yfinance(symbol, period, market)
                elif source == 'akshare':
                    df = self._fetch_akshare(symbol, period, market)
                else:
                    continue

                # 验证数据
                if self._validate_data(df):
                    logger.info(f"✓ 数据获取成功: {source} (共{len(df)}条记录)")
                    self.cache[cache_key] = df
                    return df
                else:
                    logger.warning(f"✗ 数据验证失败: {source}")

            except Exception as e:
                logger.warning(f"✗ {source}数据源失败: {str(e)}")
                continue

        # 所有数据源都失败
        logger.error(f"所有数据源均失败: {symbol}")
        return pd.DataFrame()

    def _get_source_priority(self, market: str, prefer_source: str = None) -> List[str]:
        """
        确定数据源优先级

        优先级策略:
          - A股(CN): ashare > akshare > yfinance
          - 港股(HK): yfinance > akshare > ashare
          - 美股(US): yfinance > finnhub > akshare
        """
        if prefer_source and self.source_status.get(prefer_source):
            # 如果指定了优先数据源，将其置顶
            priority = [prefer_source]
        else:
            priority = []

        # 根据市场确定默认优先级
        if market == 'CN':
            default_priority = ['ashare', 'akshare', 'yfinance']
        elif market == 'HK':
            default_priority = ['yfinance', 'akshare', 'ashare']
        elif market == 'US':
            default_priority = ['yfinance', 'finnhub', 'akshare']
        else:
            default_priority = ['yfinance', 'akshare', 'ashare']

        # 合并优先级，去重
        for source in default_priority:
            if source not in priority and self.source_status.get(source):
                priority.append(source)

        return priority

    def _fetch_ashare(self, symbol: str, period: str, market: str) -> pd.DataFrame:
        """使用Ashare获取数据"""
        if not self.ashare_get_price:
            raise RuntimeError("Ashare数据源未初始化")

        # 计算需要获取的数据条数
        period_to_days = {
            "10y": 2500, "5y": 1250, "3y": 750, "2y": 500,
            "1y": 250, "6mo": 125, "3mo": 63, "1mo": 21, "5d": 10
        }
        count = period_to_days.get(period, 1250)

        # 转换股票代码格式
        full_code = self._convert_symbol_to_ashare(symbol, market)

        # 获取数据
        df = self.ashare_get_price(full_code, count=count, frequency='1d')

        if df.empty:
            raise ValueError(f"Ashare返回空数据: {symbol}")

        # 统一列名为小写
        df.columns = df.columns.str.lower()

        # 添加return列
        if 'return' not in df.columns:
            df['return'] = df['close'].pct_change()

        return df

    def _fetch_yfinance(self, symbol: str, period: str, market: str) -> pd.DataFrame:
        """使用yfinance获取数据"""
        if not self.yfinance:
            raise RuntimeError("yfinance数据源未初始化")

        # 转换股票代码格式
        yf_symbol = self._convert_symbol_to_yfinance(symbol, market)

        # 获取数据
        ticker = self.yfinance.Ticker(yf_symbol)
        df = ticker.history(period=period)

        if df.empty:
            raise ValueError(f"yfinance返回空数据: {yf_symbol}")

        # 统一列名为小写
        df.columns = df.columns.str.lower()

        # 添加return列
        if 'return' not in df.columns:
            df['return'] = df['close'].pct_change()

        return df

    def _fetch_akshare(self, symbol: str, period: str, market: str) -> pd.DataFrame:
        """使用akshare获取数据"""
        if not self.akshare:
            raise RuntimeError("akshare数据源未初始化")

        # 转换日期范围
        from datetime import datetime, timedelta
        end_date = datetime.now()
        period_to_days = {
            "10y": 3650, "5y": 1825, "3y": 1095, "2y": 730,
            "1y": 365, "6mo": 180, "3mo": 90, "1mo": 30, "5d": 5
        }
        days = period_to_days.get(period, 1825)
        start_date = end_date - timedelta(days=days)

        # 根据市场选择akshare接口
        if market == 'CN':
            # A股数据
            df = self.akshare.stock_zh_a_hist(
                symbol=symbol,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adjust="qfq"  # 前复权
            )
        elif market == 'HK':
            # 港股数据
            df = self.akshare.stock_hk_hist(
                symbol=symbol,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adjust="qfq"
            )
        else:
            raise ValueError(f"akshare不支持市场: {market}")

        if df.empty:
            raise ValueError(f"akshare返回空数据: {symbol}")

        # 统一列名
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount'
        }
        df = df.rename(columns=column_mapping)

        # 设置日期索引
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

        # 添加return列
        if 'return' not in df.columns:
            df['return'] = df['close'].pct_change()

        return df

    def _convert_symbol_to_ashare(self, symbol: str, market: str) -> str:
        """转换代码为Ashare格式"""
        if market == "HK":
            # 港股: hk + 代码(去掉前导0)
            # 例如: 09988 -> hk9988
            symbol_clean = symbol.lstrip('0')
            return 'hk' + symbol_clean
        else:
            # A股/ETF代码格式: sh + 代码(上海) 或 sz + 代码(深圳)
            if symbol.startswith('51') or symbol.startswith('56') or symbol.startswith('6'):
                return 'sh' + symbol
            elif symbol.startswith('15') or symbol.startswith('00') or symbol.startswith('30'):
                return 'sz' + symbol
            else:
                return 'sh' + symbol

    def _convert_symbol_to_yfinance(self, symbol: str, market: str) -> str:
        """转换代码为yfinance格式"""
        # 如果已经包含后缀，直接返回
        if '.' in symbol or '-' in symbol:
            return symbol

        if market == 'HK':
            # 港股: 代码.HK (例如: 9988.HK)
            return f"{symbol.lstrip('0')}.HK"
        elif market == 'CN':
            # A股: 上海.SS / 深圳.SZ
            if symbol.startswith('6'):
                return f"{symbol}.SS"
            else:
                return f"{symbol}.SZ"
        elif market == 'US':
            # 美股: 直接使用symbol
            return symbol
        else:
            return symbol

    def _validate_data(self, df: pd.DataFrame) -> bool:
        """验证数据有效性"""
        if df is None or df.empty:
            return False

        # 检查必需列
        required_columns = ['close']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"缺少必需列: {col}")
                return False

        # 检查数据量（至少要有一些数据）
        if len(df) < 5:
            logger.warning(f"数据量过少: {len(df)} < 5")
            return False

        # 检查价格数据是否有效（非空、非零）
        if df['close'].isna().all() or (df['close'] == 0).all():
            logger.warning("价格数据全部为空或零")
            return False

        return True

    def get_source_status(self) -> Dict[str, bool]:
        """获取所有数据源状态"""
        return self.source_status.copy()

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("数据缓存已清空")


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("测试数据源管理器")
    print("=" * 80)

    manager = DataSourceManager()

    # 显示数据源状态
    print("\n数据源状态:")
    for source, status in manager.get_source_status().items():
        status_icon = "✓" if status else "✗"
        print(f"  {status_icon} {source}")

    # 测试A股数据
    print("\n" + "=" * 80)
    print("测试1: A股ETF数据 (512480 - 半导体ETF)")
    print("=" * 80)
    df1 = manager.get_stock_data('512480', period='1y', market='CN')
    if not df1.empty:
        print(f"✓ 数据获取成功: {len(df1)} 条记录")
        print(f"  日期范围: {df1.index[0]} ~ {df1.index[-1]}")
        print(f"  最新价格: {df1['close'].iloc[-1]:.2f}")
    else:
        print("✗ 数据获取失败")

    # 测试港股数据
    print("\n" + "=" * 80)
    print("测试2: 港股数据 (9988.HK - 阿里巴巴)")
    print("=" * 80)
    df2 = manager.get_stock_data('9988.HK', period='1y', market='HK')
    if not df2.empty:
        print(f"✓ 数据获取成功: {len(df2)} 条记录")
        print(f"  日期范围: {df2.index[0]} ~ {df2.index[-1]}")
        print(f"  最新价格: {df2['close'].iloc[-1]:.2f}")
    else:
        print("✗ 数据获取失败")

    # 测试美股数据
    print("\n" + "=" * 80)
    print("测试3: 美股数据 (AAPL - 苹果)")
    print("=" * 80)
    df3 = manager.get_stock_data('AAPL', period='1y', market='US')
    if not df3.empty:
        print(f"✓ 数据获取成功: {len(df3)} 条记录")
        print(f"  日期范围: {df3.index[0]} ~ {df3.index[-1]}")
        print(f"  最新价格: {df3['close'].iloc[-1]:.2f}")
    else:
        print("✗ 数据获取失败")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
