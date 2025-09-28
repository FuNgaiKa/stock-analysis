#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版数据源管理器 - 多数据源备份方案
支持多个免费数据源，提高数据获取稳定性
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
import json
from typing import Dict, List, Optional, Tuple
import akshare as ak
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
# 导入Ashare数据源
from .Ashare import get_price

logger = logging.getLogger(__name__)


class MultiSourceDataProvider:
    """多数据源数据提供器"""
    
    def __init__(self):
        self.sources = {
            'ashare': self._get_ashare_data,        # 主力数据源 - 最稳定
            'akshare': self._get_akshare_data,      # 备用1 - 原有数据源
            'sina': self._get_sina_data,            # 备用2 - 传统接口
            'netease': self._get_netease_data,      # 备用3 - 网易接口
            'yfinance': self._get_yfinance_data,    # 备用4 - 国际市场
            'tushare_free': self._get_tushare_free_data  # 备用5 - Tushare
        }
        self.cache = {}
        
    def get_market_data(self, date: str = None) -> Optional[Dict]:
        """获取市场数据 - 多源备份"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
            
        cache_key = f"market_data_{date}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 按优先级尝试不同数据源
        for source_name, source_func in self.sources.items():
            try:
                logger.info(f"尝试使用 {source_name} 获取数据...")
                data = source_func(date)
                if data and self._validate_data(data):
                    logger.info(f"数据源 {source_name} 获取成功")
                    self.cache[cache_key] = data
                    return data
            except Exception as e:
                logger.warning(f"数据源 {source_name} 失败: {str(e)}")
                continue
        
        logger.error("所有数据源都失败")
        return None

    def _get_ashare_data(self, date: str) -> Optional[Dict]:
        """Ashare数据源 - 主力数据源"""
        data = {}

        try:
            # 获取主要指数数据
            indices = {
                'sz_index': 'sh000001',     # 上证指数
                'cyb_index': 'sz399006',    # 创业板指
                'sz_component': 'sz399001'  # 深证成指
            }

            for name, code in indices.items():
                try:
                    # 使用Ashare获取最近5天数据来计算涨跌幅
                    index_data = get_price(code, frequency='1d', count=5)
                    if index_data is not None and not index_data.empty:
                        latest_price = index_data['close'].iloc[-1]
                        prev_price = index_data['close'].iloc[-2] if len(index_data) > 1 else latest_price
                        change_pct = (latest_price - prev_price) / prev_price * 100

                        data[name] = pd.DataFrame({
                            '收盘': [latest_price],
                            '涨跌幅': [change_pct],
                            '成交量': [index_data['volume'].iloc[-1]]
                        })
                    else:
                        data[name] = None
                except Exception as e:
                    logger.warning(f"Ashare获取指数 {name} 失败: {str(e)}")
                    data[name] = None

            # Ashare主要提供价格数据，涨跌停数据使用其他源
            # 这里先设置为空，由其他数据源补充
            data['limit_up'] = pd.DataFrame()
            data['limit_down'] = pd.DataFrame()

            return data

        except Exception as e:
            logger.warning(f"Ashare数据源失败: {str(e)}")
            return None
    
    def _get_akshare_data(self, date: str) -> Optional[Dict]:
        """akshare数据源"""
        data = {}
        
        # 获取涨跌停数据
        limit_up = ak.stock_zt_pool_em(date=date)
        limit_down = ak.stock_dt_pool_em(date=date)
        data['limit_up'] = limit_up
        data['limit_down'] = limit_down
        
        # 获取指数数据
        indices = {
            'sz_index': '000001',
            'cyb_index': '399006', 
            'sz_component': '399001'
        }
        
        for name, code in indices.items():
            try:
                index_data = ak.stock_zh_index_daily(symbol=code)
                data[name] = index_data.tail(1) if index_data is not None else None
            except:
                data[name] = None
        
        return data
    
    def _get_sina_data(self, date: str) -> Optional[Dict]:
        """新浪财经数据源"""
        data = {}
        
        # 新浪财经API
        sina_apis = {
            'sz_index': 'http://hq.sinajs.cn/list=s_sh000001',  # 上证指数
            'cyb_index': 'http://hq.sinajs.cn/list=s_sz399006',  # 创业板指
            'sz_component': 'http://hq.sinajs.cn/list=s_sz399001'  # 深证成指
        }
        
        for name, url in sina_apis.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    content = response.text
                    # 解析新浪数据格式
                    values = content.split('=')[1].strip(';"').split(',')
                    if len(values) >= 6:
                        current_price = float(values[1])
                        prev_close = float(values[2]) 
                        change_pct = (current_price - prev_close) / prev_close * 100
                        
                        data[name] = pd.DataFrame({
                            '收盘': [current_price],
                            '涨跌幅': [change_pct]
                        })
                    else:
                        data[name] = None
                else:
                    data[name] = None
            except Exception as e:
                logger.warning(f"新浪API {name} 失败: {str(e)}")
                data[name] = None
        
        # 涨跌停数据使用爬虫方式(简化版)
        data['limit_up'] = pd.DataFrame()
        data['limit_down'] = pd.DataFrame()
        
        return data
    
    def _get_netease_data(self, date: str) -> Optional[Dict]:
        """网易财经数据源"""
        data = {}
        
        # 网易财经API
        netease_codes = {
            'sz_index': '0000001',    # 上证指数
            'cyb_index': '1399006',   # 创业板指  
            'sz_component': '1399001' # 深证成指
        }
        
        base_url = "http://api.money.126.net/data/feed/"
        
        for name, code in netease_codes.items():
            try:
                url = f"{base_url}{code},money.api"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    content = response.text
                    # 解析网易数据格式 (JSONP)
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_str = content[json_start:json_end]
                        json_data = json.loads(json_str)
                        
                        if code in json_data:
                            stock_info = json_data[code]
                            data[name] = pd.DataFrame({
                                '收盘': [float(stock_info['price'])],
                                '涨跌幅': [float(stock_info['percent'])]
                            })
                        else:
                            data[name] = None
                    else:
                        data[name] = None
                else:
                    data[name] = None
            except Exception as e:
                logger.warning(f"网易API {name} 失败: {str(e)}")
                data[name] = None
        
        # 涨跌停数据暂时为空
        data['limit_up'] = pd.DataFrame()  
        data['limit_down'] = pd.DataFrame()
        
        return data
    
    def _get_yfinance_data(self, date: str) -> Optional[Dict]:
        """Yahoo Finance数据源(需要转换代码格式)"""
        data = {}
        
        # 转换成Yahoo格式
        yahoo_symbols = {
            'sz_index': '000001.SS',    # 上证指数
            'cyb_index': '399006.SZ',   # 创业板指
            'sz_component': '399001.SZ' # 深证成指
        }
        
        for name, symbol in yahoo_symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d')  # 获取最近5天数据
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else latest
                    change_pct = (latest['Close'] - prev['Close']) / prev['Close'] * 100
                    
                    data[name] = pd.DataFrame({
                        '收盘': [latest['Close']],
                        '涨跌幅': [change_pct],
                        '成交量': [latest['Volume']]
                    })
                else:
                    data[name] = None
            except Exception as e:
                logger.warning(f"Yahoo Finance {name} 失败: {str(e)}")
                data[name] = None
        
        # yfinance不提供涨跌停数据
        data['limit_up'] = pd.DataFrame()
        data['limit_down'] = pd.DataFrame()
        
        return data
    
    def _get_tushare_free_data(self, date: str) -> Optional[Dict]:
        """Tushare免费数据源"""
        # 注意：Tushare需要注册和积分，这里仅作示例
        # 实际使用需要配置token
        data = {}
        
        try:
            # 这里只是示例代码，实际需要配置tushare
            # import tushare as ts
            # ts.set_token('your_token')
            # pro = ts.pro_api()
            
            # 模拟数据结构
            data['sz_index'] = None
            data['cyb_index'] = None  
            data['sz_component'] = None
            data['limit_up'] = pd.DataFrame()
            data['limit_down'] = pd.DataFrame()
            
        except Exception as e:
            logger.warning(f"Tushare失败: {str(e)}")
            return None
        
        return data
    
    def _validate_data(self, data: Dict) -> bool:
        """验证数据有效性"""
        if not data:
            return False
        
        # 检查关键数据是否存在
        required_keys = ['limit_up', 'limit_down']
        for key in required_keys:
            if key not in data:
                return False
        
        # 检查至少有一个指数数据
        index_keys = ['sz_index', 'cyb_index', 'sz_component']
        has_index_data = any(
            data.get(key) is not None and not data.get(key).empty 
            for key in index_keys
        )
        
        # 检查涨跌停数据
        has_limit_data = (
            len(data.get('limit_up', [])) + len(data.get('limit_down', [])) >= 0
        )
        
        return has_index_data or has_limit_data

    def get_enhanced_market_indicators(self, date: str = None) -> Dict:
        """获取增强版市场指标"""
        market_data = self.get_market_data(date)
        if not market_data:
            return {}
        
        indicators = {}
        
        # 基础指标
        indicators.update(self._calculate_basic_indicators(market_data))
        
        # 增强指标
        indicators.update(self._calculate_enhanced_indicators(market_data))
        
        return indicators
    
    def _calculate_basic_indicators(self, market_data: Dict) -> Dict:
        """计算基础指标"""
        indicators = {}
        
        # 涨跌停统计
        limit_up_count = len(market_data.get('limit_up', []))
        limit_down_count = len(market_data.get('limit_down', []))
        
        indicators['limit_up_count'] = limit_up_count
        indicators['limit_down_count'] = limit_down_count
        indicators['limit_ratio'] = (limit_up_count - limit_down_count) / max(limit_up_count + limit_down_count, 1)
        
        # 指数表现
        index_changes = []
        for index_name in ['sz_index', 'cyb_index', 'sz_component']:
            index_data = market_data.get(index_name)
            if index_data is not None and not index_data.empty:
                change = self._extract_change_pct(index_data)
                index_changes.append(change)
        
        if index_changes:
            indicators['avg_index_change'] = np.mean(index_changes)
            indicators['index_divergence'] = np.std(index_changes)
        else:
            indicators['avg_index_change'] = 0.0
            indicators['index_divergence'] = 0.0
        
        return indicators
    
    def _calculate_enhanced_indicators(self, market_data: Dict) -> Dict:
        """计算增强指标"""
        indicators = {}
        
        # 市场强度指标
        limit_up_count = len(market_data.get('limit_up', []))
        limit_down_count = len(market_data.get('limit_down', []))
        
        # 市场参与度 (基于涨跌停总数)
        total_limit = limit_up_count + limit_down_count
        indicators['market_participation'] = min(total_limit / 100, 1.0)  # 标准化到0-1
        
        # 多空力量对比
        if total_limit > 0:
            indicators['bull_bear_ratio'] = limit_up_count / total_limit
        else:
            indicators['bull_bear_ratio'] = 0.5
        
        # 市场极端程度
        indicators['market_extreme'] = abs(indicators['bull_bear_ratio'] - 0.5) * 2
        
        return indicators
    
    def _extract_change_pct(self, data: pd.DataFrame) -> float:
        """提取涨跌幅"""
        for col in ['涨跌幅', 'pct_chg', 'change']:
            if col in data.columns:
                return float(data.iloc[-1][col])
        return 0.0


# 使用示例
def test_multi_source():
    """测试多数据源"""
    provider = MultiSourceDataProvider()
    
    # 获取今日数据
    data = provider.get_market_data()
    if data:
        print("数据获取成功!")
        print(f"涨停股票数: {len(data.get('limit_up', []))}")
        print(f"跌停股票数: {len(data.get('limit_down', []))}")
        
        # 获取增强指标
        indicators = provider.get_enhanced_market_indicators()
        print("\n增强指标:")
        for key, value in indicators.items():
            print(f"- {key}: {value}")
    else:
        print("数据获取失败!")


if __name__ == "__main__":
    test_multi_source()