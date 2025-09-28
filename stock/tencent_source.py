#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯财经数据源 - 免费、快速、稳定
API文档: 腾讯财经开放接口
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TencentDataSource:
    """腾讯财经数据源"""

    def __init__(self):
        self.base_url = "http://qt.gtimg.cn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def get_realtime_data(self, symbols: List[str]) -> Dict:
        """获取实时行情数据

        Args:
            symbols: 股票代码列表，格式如 ['sh000001', 'sz399001']

        Returns:
            解析后的股票数据字典
        """
        try:
            # 构建请求URL
            symbol_str = ','.join(symbols)
            url = f"{self.base_url}/q={symbol_str}"

            logger.info(f"获取腾讯数据: {url}")
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                return self._parse_response(response.text, symbols)
            else:
                logger.error(f"腾讯API请求失败: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"腾讯数据获取失败: {str(e)}")
            return {}

    def _parse_response(self, response_text: str, symbols: List[str]) -> Dict:
        """解析腾讯API响应数据"""
        data = {}
        lines = response_text.strip().split('\n')

        for i, line in enumerate(lines):
            if i >= len(symbols):
                break

            try:
                # 解析数据格式: v_sh000001="1~上证指数~000001~3830.72~3854.79~..."
                symbol = symbols[i]
                if '="' in line and '~' in line:
                    content = line.split('="')[1].rstrip('";')
                    fields = content.split('~')

                    if len(fields) >= 32:  # 确保有足够的字段
                        parsed_data = self._parse_stock_fields(fields, symbol)
                        data[symbol] = parsed_data
                        logger.info(f"解析 {symbol} 成功: 价格={parsed_data.get('current', 'N/A')}")
                    else:
                        logger.warning(f"数据字段不足 {symbol}: {len(fields)} 字段")

            except Exception as e:
                logger.warning(f"解析数据失败 {symbol}: {str(e)}")
                continue

        return data

    def _parse_stock_fields(self, fields: List[str], symbol: str) -> Dict:
        """解析股票字段数据

        腾讯API字段说明:
        0: 未知, 1: 名称, 2: 代码, 3: 当前价, 4: 昨收价, 5: 今开价,
        6: 成交量(手), 7: 外盘, 8: 内盘, 9: 买一, 10: 买一量,
        11: 买二, 12: 买二量, ..., 29: 日期, 30: 时间
        """
        try:
            current_price = float(fields[3]) if fields[3] else 0.0
            prev_close = float(fields[4]) if fields[4] else 0.0
            open_price = float(fields[5]) if fields[5] else 0.0
            volume = int(fields[6]) if fields[6] else 0

            # 计算涨跌幅
            change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0.0
            change_amount = current_price - prev_close

            return {
                'symbol': symbol,
                'name': fields[1],
                'current': current_price,
                'prev_close': prev_close,
                'open': open_price,
                'volume': volume,
                'change_pct': change_pct,
                'change_amount': change_amount,
                'date': fields[29] if len(fields) > 29 else '',
                'time': fields[30] if len(fields) > 30 else '',
                'timestamp': datetime.now()
            }

        except Exception as e:
            logger.error(f"字段解析失败: {str(e)}")
            return {'symbol': symbol, 'error': str(e)}

    def get_market_summary(self) -> Dict:
        """获取市场概况"""
        # 主要指数
        indices = ['sh000001', 'sz399001', 'sz399006']  # 上证、深证成指、创业板指

        index_data = self.get_realtime_data(indices)

        summary = {
            'sz_index': None,
            'sz_component': None,
            'cyb_index': None,
            'timestamp': datetime.now()
        }

        # 转换为标准格式
        if 'sh000001' in index_data:
            sz_data = index_data['sh000001']
            summary['sz_index'] = pd.DataFrame({
                '收盘': [sz_data.get('current', 0)],
                '涨跌幅': [sz_data.get('change_pct', 0)]
            })

        if 'sz399001' in index_data:
            szc_data = index_data['sz399001']
            summary['sz_component'] = pd.DataFrame({
                '收盘': [szc_data.get('current', 0)],
                '涨跌幅': [szc_data.get('change_pct', 0)]
            })

        if 'sz399006' in index_data:
            cyb_data = index_data['sz399006']
            summary['cyb_index'] = pd.DataFrame({
                '收盘': [cyb_data.get('current', 0)],
                '涨跌幅': [cyb_data.get('change_pct', 0)]
            })

        return summary

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            test_data = self.get_realtime_data(['sh000001'])
            return bool(test_data)
        except:
            return False


# 使用示例和测试
def test_tencent_source():
    """测试腾讯数据源"""
    print("🔍 测试腾讯财经数据源...")

    source = TencentDataSource()

    # 测试连接
    if source.test_connection():
        print("✅ 腾讯数据源连接成功")
    else:
        print("❌ 腾讯数据源连接失败")
        return

    # 获取指数数据
    print("\n📊 获取主要指数数据:")
    indices = ['sh000001', 'sz399001', 'sz399006']
    data = source.get_realtime_data(indices)

    for symbol, info in data.items():
        if 'error' not in info:
            print(f"   {info['name']}: {info['current']:.2f} ({info['change_pct']:+.2f}%)")
        else:
            print(f"   {symbol}: 获取失败")

    # 获取市场概况
    print("\n📈 市场概况:")
    summary = source.get_market_summary()
    for key, df in summary.items():
        if key != 'timestamp' and df is not None and not df.empty:
            price = df['收盘'].iloc[0]
            change = df['涨跌幅'].iloc[0]
            print(f"   {key}: {price:.2f} ({change:+.2f}%)")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    test_tencent_source()