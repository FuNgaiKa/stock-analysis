#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股数据源模块 - 基于 yfinance
提供美股指数、个股、ETF历史数据及技术指标计算
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, List
import time

logger = logging.getLogger(__name__)


class USStockDataSource:
    """美股数据源 - 使用 yfinance"""

    # 美股主要指数映射
    US_INDICES = {
        'SPX': '^GSPC',      # 标普500
        'NASDAQ': '^IXIC',   # 纳斯达克综合
        'NDX': '^NDX',       # 纳斯达克100
        'DJI': '^DJI',       # 道琼斯工业
        'VIX': '^VIX',       # 恐慌指数
        'RUT': '^RUT',       # 罗素2000
        'SOX': '^SOX',       # 费城半导体
    }

    # A股主要指数
    A_INDICES = {
        'SSE': '000001.SS',  # 上证指数
        'SZSE': '399001.SZ', # 深证成指
        'CSI300': '000300.SS', # 沪深300
    }

    # 大宗商品期货
    COMMODITIES = {
        'GOLD': 'GC=F',      # 纽约黄金期货 (COMEX Gold)
        'SILVER': 'SI=F',    # 纽约白银期货 (COMEX Silver)
        'OIL': 'CL=F',       # 纽约原油期货 (WTI Crude Oil)
    }

    # 加密货币
    CRYPTO = {
        'BTC': 'BTC-USD',    # 比特币/美元
        'ETH': 'ETH-USD',    # 以太坊/美元
    }

    # 主要ETF
    US_ETFS = {
        'SPY': 'SPY',   # SPDR S&P 500 ETF
        'QQQ': 'QQQ',   # Invesco QQQ (NASDAQ-100)
        'DIA': 'DIA',   # SPDR Dow Jones Industrial Average ETF
        'IWM': 'IWM',   # iShares Russell 2000 ETF
    }

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
        logger.info("美股数据源初始化完成")

    def get_us_index_daily(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "5y"
    ) -> pd.DataFrame:
        """
        获取美股指数历史日线数据

        Args:
            symbol: 指数代码
                - SPX/^GSPC: 标普500
                - NASDAQ/^IXIC: 纳斯达克综合
                - NDX/^NDX: 纳斯达克100
                - VIX/^VIX: 恐慌指数
            start_date: 开始日期 (YYYY-MM-DD), 可选
            end_date: 结束日期 (YYYY-MM-DD), 可选
            period: 时间周期 (1d/5d/1mo/3mo/6mo/1y/2y/5y/10y/ytd/max)

        Returns:
            DataFrame with columns: [Open, High, Low, Close, Volume]
            索引为日期 (DatetimeIndex)
        """
        # 标准化symbol - 支持指数、商品、加密货币、A股
        if symbol in self.US_INDICES:
            symbol = self.US_INDICES[symbol]
        elif symbol in self.A_INDICES:
            symbol = self.A_INDICES[symbol]
        elif symbol in self.COMMODITIES:
            symbol = self.COMMODITIES[symbol]
        elif symbol in self.CRYPTO:
            symbol = self.CRYPTO[symbol]

        cache_key = f"us_index_{symbol}_{start_date}_{end_date}_{period}"

        # 检查缓存
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                logger.info(f"使用缓存的{symbol}指数数据")
                return cached_data

        try:
            logger.info(f"获取美股指数数据: {symbol}")
            ticker = yf.Ticker(symbol)

            # 根据参数选择获取方式
            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date)
            else:
                df = ticker.history(period=period)

            if df is not None and not df.empty:
                # 标准化列名 (yfinance已经是标准格式)
                # 列名: Open, High, Low, Close, Volume, Dividends, Stock Splits

                # 只保留OHLCV
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

                # 重命名为小写(与港股保持一致)
                df.columns = ['open', 'high', 'low', 'close', 'volume']

                # 确保索引是日期类型
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()

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

    def get_us_stock_hist(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "5y"
    ) -> pd.DataFrame:
        """
        获取美股个股/ETF历史数据

        Args:
            symbol: 股票代码 (如 "AAPL", "MSFT", "SPY")
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            period: 时间周期

        Returns:
            DataFrame with columns: [open, high, low, close, volume]
        """
        try:
            logger.info(f"获取美股个股/ETF历史数据: {symbol}")
            ticker = yf.Ticker(symbol)

            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date)
            else:
                df = ticker.history(period=period)

            if df is not None and not df.empty:
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                df.columns = ['open', 'high', 'low', 'close', 'volume']
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()

                logger.info(f"{symbol}历史数据获取成功: {len(df)} 条记录")
                return df
            else:
                logger.warning(f"{symbol}历史数据为空")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取{symbol}历史数据失败: {str(e)}")
            return pd.DataFrame()

    def get_multiple_indices(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "5y"
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多个指数数据

        Args:
            symbols: 指数代码列表
            start_date: 开始日期
            end_date: 结束日期
            period: 时间周期

        Returns:
            字典 {symbol: DataFrame}
        """
        results = {}

        for symbol in symbols:
            df = self.get_us_index_daily(symbol, start_date, end_date, period)
            if not df.empty:
                results[symbol] = df
            # 添加短暂延迟,避免频繁请求
            time.sleep(0.2)

        return results

    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """
        计算技术指标

        Args:
            df: OHLCV数据

        Returns:
            技术指标字典
        """
        if df.empty or len(df) < 2:
            return {}

        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            indicators = {}

            # 基础价格信息
            indicators['latest_price'] = float(latest['close'])
            indicators['prev_close'] = float(prev['close'])
            indicators['change'] = float(latest['close'] - prev['close'])
            indicators['change_pct'] = float((latest['close'] - prev['close']) / prev['close'] * 100)
            indicators['latest_date'] = df.index[-1].strftime('%Y-%m-%d')

            # 均线 (MA)
            for period in [5, 10, 20, 60, 120, 250]:
                if len(df) >= period:
                    ma = df['close'].rolling(period).mean().iloc[-1]
                    indicators[f'ma{period}'] = float(ma)
                    # 价格与均线的偏离度
                    indicators[f'ma{period}_deviation'] = float((latest['close'] - ma) / ma * 100)

            # RSI
            if len(df) >= 15:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi'] = float(rsi.iloc[-1])

            # MACD
            if len(df) >= 26:
                ema12 = df['close'].ewm(span=12, adjust=False).mean()
                ema26 = df['close'].ewm(span=26, adjust=False).mean()
                dif = ema12 - ema26
                dea = dif.ewm(span=9, adjust=False).mean()
                macd_hist = (dif - dea) * 2

                indicators['macd_dif'] = float(dif.iloc[-1])
                indicators['macd_dea'] = float(dea.iloc[-1])
                indicators['macd_hist'] = float(macd_hist.iloc[-1])

            # 布林带
            if len(df) >= 20:
                bb_period = 20
                bb_std = 2
                bb_middle = df['close'].rolling(bb_period).mean()
                bb_std_dev = df['close'].rolling(bb_period).std()
                bb_upper = bb_middle + (bb_std * bb_std_dev)
                bb_lower = bb_middle - (bb_std * bb_std_dev)

                indicators['bb_upper'] = float(bb_upper.iloc[-1])
                indicators['bb_middle'] = float(bb_middle.iloc[-1])
                indicators['bb_lower'] = float(bb_lower.iloc[-1])

                # 布林带宽度
                indicators['bb_width'] = float((bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_middle.iloc[-1] * 100)

                # 价格在布林带中的位置
                bb_position = (latest['close'] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) * 100
                indicators['bb_position'] = float(bb_position)

            # ATR (Average True Range)
            if len(df) >= 15:
                high_low = df['high'] - df['low']
                high_close = abs(df['high'] - df['close'].shift())
                low_close = abs(df['low'] - df['close'].shift())
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = true_range.rolling(14).mean()
                indicators['atr'] = float(atr.iloc[-1])
                indicators['atr_pct'] = float(atr.iloc[-1] / latest['close'] * 100)

            # 波动率
            if len(df) >= 20:
                returns = df['close'].pct_change()
                volatility = returns.std() * np.sqrt(252) * 100
                indicators['volatility'] = float(volatility)

            # 52周高低点
            lookback = min(252, len(df))
            high_52w = df['high'].tail(lookback).max()
            low_52w = df['low'].tail(lookback).min()

            indicators['high_52w'] = float(high_52w)
            indicators['low_52w'] = float(low_52w)
            indicators['dist_to_high_pct'] = float((latest['close'] - high_52w) / high_52w * 100)
            indicators['dist_to_low_pct'] = float((latest['close'] - low_52w) / low_52w * 100)

            # 成交量指标
            if 'volume' in df.columns:
                indicators['volume_latest'] = float(latest['volume'])

                if len(df) >= 20:
                    avg_volume_20 = df['volume'].rolling(20).mean().iloc[-1]
                    indicators['volume_ma20'] = float(avg_volume_20)
                    indicators['volume_ratio'] = float(latest['volume'] / avg_volume_20) if avg_volume_20 > 0 else 1.0

            return indicators

        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            return {}

    def get_market_summary(self) -> Dict:
        """
        获取美股市场概况

        Returns:
            市场概况数据字典
        """
        try:
            logger.info("获取美股市场概况...")

            summary = {
                'timestamp': datetime.now(),
                'market': 'US'
            }

            # 获取四大核心指数
            core_indices = ['SPX', 'NASDAQ', 'NDX', 'VIX']

            for idx in core_indices:
                df = self.get_us_index_daily(idx, period='5d')  # 只获取最近5天
                if not df.empty:
                    indicators = self.calculate_technical_indicators(df)
                    summary[idx.lower()] = indicators

            logger.info("美股市场概况获取成功")
            return summary

        except Exception as e:
            logger.error(f"获取美股市场概况失败: {str(e)}")
            return {'timestamp': datetime.now(), 'market': 'US', 'error': str(e)}

    def get_index_info(self, symbol: str) -> Dict:
        """
        获取指数基本信息

        Args:
            symbol: 指数代码

        Returns:
            指数信息字典
        """
        if symbol in self.US_INDICES:
            symbol = self.US_INDICES[symbol]

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'US'),
                'quote_type': info.get('quoteType', 'INDEX')
            }

        except Exception as e:
            logger.error(f"获取{symbol}信息失败: {str(e)}")
            return {'symbol': symbol, 'error': str(e)}


def test_us_data_source():
    """测试美股数据源"""
    print("=" * 70)
    print("美股数据源测试")
    print("=" * 70)

    source = USStockDataSource()

    # 1. 测试标普500历史数据
    print("\n1. 测试标普500历史数据")
    spx_df = source.get_us_index_daily("SPX", period="1y")
    if not spx_df.empty:
        print(f"   [OK] 标普500数据: {len(spx_df)} 条记录")
        print(f"   最新收盘: {spx_df.iloc[-1]['close']:.2f}")
        print(f"   数据范围: {spx_df.index[0].date()} 至 {spx_df.index[-1].date()}")
    else:
        print("   [FAIL] 标普500数据获取失败")

    # 2. 测试技术指标计算
    print("\n2. 测试技术指标计算")
    if not spx_df.empty:
        indicators = source.calculate_technical_indicators(spx_df)
        if indicators:
            print(f"   [OK] 技术指标计算成功")
            print(f"   最新价格: {indicators['latest_price']:.2f}")
            print(f"   涨跌幅: {indicators['change_pct']:+.2f}%")
            print(f"   RSI: {indicators.get('rsi', 0):.2f}")
            print(f"   距52周高点: {indicators.get('dist_to_high_pct', 0):+.2f}%")
        else:
            print("   [FAIL] 技术指标计算失败")

    # 3. 测试批量获取多指数
    print("\n3. 测试批量获取多指数数据")
    indices = ['SPX', 'NASDAQ', 'NDX', 'VIX']
    multi_data = source.get_multiple_indices(indices, period="1mo")
    if multi_data:
        print(f"   [OK] 成功获取 {len(multi_data)}/{len(indices)} 个指数")
        for symbol, df in multi_data.items():
            print(f"   - {symbol}: {len(df)} 条记录, 最新: {df.iloc[-1]['close']:.2f}")
    else:
        print("   [FAIL] 批量获取失败")

    # 4. 测试市场概况
    print("\n4. 测试市场概况")
    summary = source.get_market_summary()
    if summary and 'error' not in summary:
        print(f"   [OK] 市场概况获取成功")
        if 'spx' in summary:
            spx = summary['spx']
            print(f"   标普500: {spx.get('latest_price', 0):.2f} ({spx.get('change_pct', 0):+.2f}%)")
        if 'vix' in summary:
            vix = summary['vix']
            print(f"   VIX: {vix.get('latest_price', 0):.2f}")
    else:
        print(f"   [FAIL] 市场概况获取失败: {summary.get('error', '未知错误')}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_us_data_source()
