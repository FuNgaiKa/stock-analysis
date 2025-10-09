#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强数据获取模块 - Phase 1.5
获取成交量、市场情绪、宏观指标等增强因子
"""

import pandas as pd
import numpy as np
import akshare as ak
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class EnhancedDataProvider:
    """增强数据提供器"""

    def __init__(self):
        self._cache = {}
        logger.info("增强数据提供器初始化完成")

    def get_volume_metrics(self, index_code: str, date: datetime = None) -> Dict:
        """
        获取成交量相关指标

        Returns:
            {
                'current_volume': 当前成交量,
                'volume_ma5': 5日均量,
                'volume_ma20': 20日均量,
                'volume_percentile': 成交量历史分位数,
                'volume_ratio': 量比 (当前/5日均)
            }
        """
        try:
            df = ak.stock_zh_index_daily(symbol=index_code)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            if date is None:
                date = df.index[-1]

            # 确保date在索引中
            if date not in df.index:
                date = df.index[df.index <= date][-1]

            current_volume = df.loc[date, 'volume']

            # 均量
            df['volume_ma5'] = df['volume'].rolling(5).mean()
            df['volume_ma20'] = df['volume'].rolling(20).mean()

            # 历史分位数
            historical_volumes = df['volume'].loc[:date]
            volume_percentile = (historical_volumes < current_volume).sum() / len(historical_volumes)

            # 量比
            volume_ma5 = df.loc[date, 'volume_ma5']
            volume_ratio = current_volume / volume_ma5 if volume_ma5 > 0 else 1.0

            return {
                'current_volume': float(current_volume),
                'volume_ma5': float(volume_ma5),
                'volume_ma20': float(df.loc[date, 'volume_ma20']),
                'volume_percentile': float(volume_percentile),
                'volume_ratio': float(volume_ratio),
                'volume_status': self._classify_volume_status(volume_ratio, volume_percentile)
            }

        except Exception as e:
            logger.warning(f"获取成交量指标失败: {str(e)}")
            return {}

    def get_market_sentiment(self, date_str: str = None) -> Dict:
        """
        获取市场情绪指标

        Returns:
            {
                'limit_up_count': 涨停数量,
                'limit_down_count': 跌停数量,
                'limit_up_ratio': 涨停比率,
                'sentiment_score': 情绪得分 (-1到1)
            }
        """
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y%m%d')

            # 涨停数据
            try:
                df_up = ak.stock_zt_pool_em(date=date_str)
                limit_up_count = len(df_up)
            except:
                limit_up_count = 0

            # 跌停数据
            try:
                df_down = ak.stock_zt_pool_dtgc_em(date=date_str)
                limit_down_count = len(df_down)
            except:
                limit_down_count = 0

            # A股总数约5000只
            total_stocks = 5000
            limit_up_ratio = limit_up_count / total_stocks
            limit_down_ratio = limit_down_count / total_stocks

            # 情绪得分：涨停多为正，跌停多为负
            sentiment_score = (limit_up_count - limit_down_count) / total_stocks
            sentiment_score = max(-1, min(1, sentiment_score))  # 限制在-1到1

            sentiment_level = self._classify_sentiment(limit_up_count, limit_down_count)

            return {
                'limit_up_count': limit_up_count,
                'limit_down_count': limit_down_count,
                'limit_up_ratio': float(limit_up_ratio),
                'limit_down_ratio': float(limit_down_ratio),
                'sentiment_score': float(sentiment_score),
                'sentiment_level': sentiment_level
            }

        except Exception as e:
            logger.warning(f"获取市场情绪指标失败: {str(e)}")
            return {}

    def get_macro_indicators(self) -> Dict:
        """
        获取宏观指标

        Returns:
            {
                'bond_yield_10y': 10年期国债收益率,
                'risk_free_rate': 无风险利率,
            }
        """
        try:
            # 国债收益率
            df = ak.bond_china_yield()
            latest_yield = df['中国国债收益率10年'].iloc[-1]

            return {
                'bond_yield_10y': float(latest_yield),
                'risk_free_rate': float(latest_yield),
                'data_date': df['曲线名称'].iloc[-1]
            }

        except Exception as e:
            logger.warning(f"获取宏观指标失败: {str(e)}")
            return {
                'bond_yield_10y': 2.5,  # 默认值
                'risk_free_rate': 2.5
            }

    def get_volume_price_divergence(
        self,
        index_code: str,
        lookback_days: int = 20
    ) -> Dict:
        """
        检测量价背离

        Returns:
            {
                'has_divergence': 是否背离,
                'divergence_type': '顶背离' / '底背离' / None,
                'divergence_score': 背离强度 (0-1)
            }
        """
        try:
            df = ak.stock_zh_index_daily(symbol=index_code)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            # 最近N天数据
            recent = df.tail(lookback_days)

            # 价格趋势
            price_start = recent['close'].iloc[0]
            price_end = recent['close'].iloc[-1]
            price_trend = (price_end - price_start) / price_start

            # 成交量趋势
            volume_start = recent['volume'].iloc[:5].mean()
            volume_end = recent['volume'].iloc[-5:].mean()
            volume_trend = (volume_end - volume_start) / volume_start

            # 判断背离
            divergence_type = None
            has_divergence = False
            divergence_score = 0

            # 顶背离：价格上涨，成交量萎缩
            if price_trend > 0.05 and volume_trend < -0.2:
                divergence_type = '顶背离'
                has_divergence = True
                divergence_score = min(1.0, abs(volume_trend) * 2)

            # 底背离：价格下跌，成交量放大
            elif price_trend < -0.05 and volume_trend > 0.2:
                divergence_type = '底背离'
                has_divergence = True
                divergence_score = min(1.0, volume_trend * 2)

            return {
                'has_divergence': has_divergence,
                'divergence_type': divergence_type,
                'divergence_score': float(divergence_score),
                'price_trend': float(price_trend),
                'volume_trend': float(volume_trend)
            }

        except Exception as e:
            logger.warning(f"量价背离检测失败: {str(e)}")
            return {
                'has_divergence': False,
                'divergence_type': None,
                'divergence_score': 0
            }

    @staticmethod
    def _classify_volume_status(volume_ratio: float, volume_percentile: float) -> str:
        """分类成交量状态"""
        if volume_ratio >= 2.0:
            return "放量突破"
        elif volume_ratio >= 1.5:
            return "温和放量"
        elif volume_ratio >= 0.8:
            return "正常水平"
        elif volume_ratio >= 0.5:
            return "温和缩量"
        else:
            return "严重缩量"

    @staticmethod
    def _classify_sentiment(limit_up: int, limit_down: int) -> str:
        """分类市场情绪"""
        if limit_up > 100:
            return "极度狂热"
        elif limit_up > 50:
            return "情绪高涨"
        elif limit_up > 20:
            return "情绪积极"
        elif limit_down > 50:
            return "恐慌情绪"
        elif limit_down > 20:
            return "情绪低迷"
        else:
            return "情绪平稳"

    def get_valuation_metrics(self, date: datetime = None) -> Dict:
        """
        获取市场估值指标 (A股整体)

        Returns:
            {
                'pe_ttm': 市盈率TTM中位数,
                'pe_percentile_all': PE历史分位数(全部历史),
                'pe_percentile_10y': PE历史分位数(近10年),
                'pb': 市净率中位数,
                'pb_percentile_all': PB历史分位数(全部历史),
                'pb_percentile_10y': PB历史分位数(近10年),
                'valuation_level': 估值水平分类
            }
        """
        try:
            # 获取PE数据
            df_pe = ak.stock_a_ttm_lyr()
            df_pe['date'] = pd.to_datetime(df_pe['date'])
            df_pe = df_pe.set_index('date').sort_index()

            # 获取PB数据
            df_pb = ak.stock_a_all_pb()
            df_pb['date'] = pd.to_datetime(df_pb['date'])
            df_pb = df_pb.set_index('date').sort_index()

            # 直接使用最新数据(估值数据通常滞后,不做复杂的日期匹配)
            latest_pe_date = df_pe.index[-1]
            latest_pb_date = df_pb.index[-1]

            # 提取PE数据
            pe_ttm = float(df_pe.iloc[-1]['middlePETTM'])
            pe_pct_all = float(df_pe.iloc[-1]['quantileInAllHistoryMiddlePeTtm'])
            pe_pct_10y = float(df_pe.iloc[-1]['quantileInRecent10YearsMiddlePeTtm'])

            # 提取PB数据
            pb = float(df_pb.iloc[-1]['middlePB'])
            pb_pct_all = float(df_pb.iloc[-1]['quantileInAllHistoryMiddlePB'])
            pb_pct_10y = float(df_pb.iloc[-1]['quantileInRecent10YearsMiddlePB'])

            # 使用较新的日期作为数据日期
            data_date = max(latest_pe_date, latest_pb_date)

            # 估值水平分类
            valuation_level = self._classify_valuation(pe_pct_10y, pb_pct_10y)

            return {
                'pe_ttm': pe_ttm,
                'pe_percentile_all': pe_pct_all,
                'pe_percentile_10y': pe_pct_10y,
                'pb': pb,
                'pb_percentile_all': pb_pct_all,
                'pb_percentile_10y': pb_pct_10y,
                'valuation_level': valuation_level,
                'data_date': data_date.strftime('%Y-%m-%d')
            }

        except Exception as e:
            logger.warning(f"获取估值指标失败: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return {}

    def get_north_capital_flow(self, lookback_days: int = 5) -> Dict:
        """
        获取北向资金流向指标

        Args:
            lookback_days: 回溯天数,用于计算累计流入

        Returns:
            {
                'today_net_inflow': 当日净流入(亿元),
                'cumulative_5d': 近5日累计净流入,
                'cumulative_20d': 近20日累计净流入,
                'flow_status': 资金流向状态,
                'recent_trend': 近期趋势(流入/流出)
            }
        """
        try:
            # 获取北向资金历史数据
            df = ak.stock_hsgt_fund_flow_summary_em()

            # 筛选北向数据(沪股通+深股通)
            df_north = df[df['资金方向'] == '北向'].copy()
            df_north['交易日'] = pd.to_datetime(df_north['交易日'])
            df_north = df_north.sort_values('交易日', ascending=False)

            if len(df_north) == 0:
                return {}

            # 当日净流入
            today_inflow = df_north.iloc[0]['资金净流入']

            # 计算累计流入
            df_recent = df_north.head(lookback_days)
            cumulative_5d = df_recent['资金净流入'].sum()

            df_20d = df_north.head(20) if len(df_north) >= 20 else df_north
            cumulative_20d = df_20d['资金净流入'].sum()

            # 判断趋势
            recent_trend = '持续流入' if cumulative_5d > 0 else '持续流出'

            # 流向状态
            flow_status = self._classify_capital_flow(today_inflow, cumulative_5d)

            return {
                'today_net_inflow': float(today_inflow),
                'cumulative_5d': float(cumulative_5d),
                'cumulative_20d': float(cumulative_20d),
                'flow_status': flow_status,
                'recent_trend': recent_trend,
                'data_date': df_north.iloc[0]['交易日'].strftime('%Y-%m-%d')
            }

        except Exception as e:
            logger.warning(f"获取北向资金流向失败: {str(e)}")
            return {}

    def get_market_breadth_metrics(self) -> Dict:
        """
        获取市场宽度指标

        Returns:
            {
                'total_stocks': 总股票数,
                'up_count': 上涨家数,
                'down_count': 下跌家数,
                'flat_count': 平盘家数,
                'up_ratio': 上涨比例,
                'advance_decline_ratio': 涨跌比(上涨/下跌),
                'breadth_level': 市场宽度水平
            }
        """
        try:
            # 从情绪数据中提取(因为直接获取实时行情可能超时)
            # 使用涨跌停数据作为替代
            sentiment = self.get_market_sentiment()

            if not sentiment:
                return {}

            # 估算市场宽度(基于涨跌停数据)
            limit_up = sentiment.get('limit_up_count', 0)
            limit_down = sentiment.get('limit_down_count', 0)

            # A股约5000只
            total_stocks = 5000

            # 根据涨跌停推算上涨/下跌家数(经验公式)
            # 一般涨停占上涨家数的5-10%
            estimated_up = min(total_stocks, int(limit_up * 15)) if limit_up > 0 else 0
            estimated_down = min(total_stocks, int(limit_down * 15)) if limit_down > 0 else 0
            estimated_flat = total_stocks - estimated_up - estimated_down

            up_ratio = estimated_up / total_stocks if total_stocks > 0 else 0
            ad_ratio = estimated_up / estimated_down if estimated_down > 0 else 99.9

            breadth_level = self._classify_market_breadth(up_ratio, ad_ratio)

            return {
                'total_stocks': total_stocks,
                'up_count': estimated_up,
                'down_count': estimated_down,
                'flat_count': estimated_flat,
                'up_ratio': float(up_ratio),
                'advance_decline_ratio': float(ad_ratio),
                'breadth_level': breadth_level,
                'note': '基于涨跌停数据估算'
            }

        except Exception as e:
            logger.warning(f"获取市场宽度指标失败: {str(e)}")
            return {}

    def get_technical_indicators(self, index_code: str, lookback_days: int = 100) -> Dict:
        """
        获取技术指标 (MACD, RSI)

        Args:
            index_code: 指数代码
            lookback_days: 回溯天数

        Returns:
            {
                'macd': MACD值,
                'signal': 信号线,
                'histogram': MACD柱,
                'rsi': RSI值,
                'macd_signal': MACD信号(金叉/死叉),
                'rsi_signal': RSI信号(超买/超卖/中性)
            }
        """
        try:
            # 获取历史数据
            df = ak.stock_zh_index_daily(symbol=index_code)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            df = df.tail(lookback_days)

            close = df['close'].values

            # 计算MACD (12, 26, 9)
            exp1 = pd.Series(close).ewm(span=12, adjust=False).mean()
            exp2 = pd.Series(close).ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal

            # 计算RSI (14)
            delta = pd.Series(close).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # 取最新值
            current_macd = float(macd.iloc[-1])
            current_signal = float(signal.iloc[-1])
            current_histogram = float(histogram.iloc[-1])
            current_rsi = float(rsi.iloc[-1])

            # MACD信号判断
            prev_histogram = float(histogram.iloc[-2])
            if current_histogram > 0 and prev_histogram < 0:
                macd_signal = '金叉'
            elif current_histogram < 0 and prev_histogram > 0:
                macd_signal = '死叉'
            elif current_histogram > 0:
                macd_signal = '多头'
            else:
                macd_signal = '空头'

            # RSI信号判断
            if current_rsi > 70:
                rsi_signal = '超买'
            elif current_rsi < 30:
                rsi_signal = '超卖'
            else:
                rsi_signal = '中性'

            return {
                'macd': current_macd,
                'signal': current_signal,
                'histogram': current_histogram,
                'rsi': current_rsi,
                'macd_signal': macd_signal,
                'rsi_signal': rsi_signal
            }

        except Exception as e:
            logger.warning(f"获取技术指标失败: {str(e)}")
            return {}

    def get_volatility_metrics(self, index_code: str, lookback_days: int = 252) -> Dict:
        """
        获取波动率指标

        Args:
            index_code: 指数代码
            lookback_days: 回溯天数(默认一年)

        Returns:
            {
                'current_volatility': 当前波动率(年化),
                'volatility_20d': 20日波动率,
                'volatility_60d': 60日波动率,
                'volatility_percentile': 波动率历史分位数,
                'volatility_level': 波动率水平
            }
        """
        try:
            # 获取历史数据
            df = ak.stock_zh_index_daily(symbol=index_code)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            # 计算收益率
            df['return'] = df['close'].pct_change()

            # 波动率计算(年化)
            vol_20d = df['return'].tail(20).std() * np.sqrt(252)
            vol_60d = df['return'].tail(60).std() * np.sqrt(252)
            current_vol = vol_20d  # 使用20日波动率作为当前值

            # 历史波动率序列
            df['vol_rolling'] = df['return'].rolling(20).std() * np.sqrt(252)
            historical_vols = df['vol_rolling'].dropna()

            # 分位数
            vol_percentile = (historical_vols < current_vol).sum() / len(historical_vols)

            # 波动率水平分类
            vol_level = self._classify_volatility(vol_percentile)

            return {
                'current_volatility': float(current_vol),
                'volatility_20d': float(vol_20d),
                'volatility_60d': float(vol_60d),
                'volatility_percentile': float(vol_percentile),
                'volatility_level': vol_level
            }

        except Exception as e:
            logger.warning(f"获取波动率指标失败: {str(e)}")
            return {}

    @staticmethod
    def _classify_valuation(pe_pct: float, pb_pct: float) -> str:
        """分类估值水平"""
        avg_pct = (pe_pct + pb_pct) / 2

        if avg_pct < 0.2:
            return "极低估值"
        elif avg_pct < 0.4:
            return "低估值"
        elif avg_pct < 0.6:
            return "合理估值"
        elif avg_pct < 0.8:
            return "高估值"
        else:
            return "极高估值"

    @staticmethod
    def _classify_capital_flow(today: float, recent_5d: float) -> str:
        """分类资金流向状态"""
        if today > 100 and recent_5d > 300:
            return "大幅流入"
        elif today > 50 and recent_5d > 100:
            return "持续流入"
        elif today > 0:
            return "小幅流入"
        elif today > -50 and recent_5d > -100:
            return "小幅流出"
        elif today > -100 and recent_5d > -300:
            return "持续流出"
        else:
            return "大幅流出"

    @staticmethod
    def _classify_market_breadth(up_ratio: float, ad_ratio: float) -> str:
        """分类市场宽度"""
        if up_ratio > 0.7 and ad_ratio > 3:
            return "普涨行情"
        elif up_ratio > 0.6:
            return "多数上涨"
        elif up_ratio > 0.4:
            return "涨跌平衡"
        elif up_ratio > 0.3:
            return "多数下跌"
        else:
            return "普跌行情"

    @staticmethod
    def _classify_volatility(percentile: float) -> str:
        """分类波动率水平"""
        if percentile < 0.2:
            return "极低波动"
        elif percentile < 0.4:
            return "低波动"
        elif percentile < 0.6:
            return "正常波动"
        elif percentile < 0.8:
            return "高波动"
        else:
            return "极高波动"

    def get_margin_trading_metrics(self, market: str = '沪深两市') -> Dict:
        """
        获取融资融券指标 - Phase 3新增

        Args:
            market: 市场范围 ('沪深两市', '沪市', '深市')

        Returns:
            {
                'margin_balance': 融资余额(亿元),
                'margin_balance_change': 融资余额变化(亿元),
                'margin_balance_pct_change': 融资余额变化率(%),
                'short_balance': 融券余额(亿元),
                'total_balance': 两融余额(亿元),
                'leverage_level': 杠杆水平分类
            }
        """
        try:
            # 获取融资融券汇总数据
            df = ak.stock_margin_underlying_info_szse(date="20231201")

            # 获取最新日期的汇总数据(使用全市场数据)
            df_summary = ak.stock_margin_szse(symbol="融资融券标的")

            if len(df_summary) == 0:
                return {}

            # 取最新数据
            latest = df_summary.iloc[-1]
            prev = df_summary.iloc[-2] if len(df_summary) >= 2 else latest

            # 提取数据(单位转换为亿元)
            margin_balance = float(latest.get('融资余额', 0)) / 100000000
            prev_margin_balance = float(prev.get('融资余额', 0)) / 100000000

            margin_change = margin_balance - prev_margin_balance
            margin_pct_change = (margin_change / prev_margin_balance * 100) if prev_margin_balance > 0 else 0

            short_balance = float(latest.get('融券余额', 0)) / 100000000
            total_balance = margin_balance + short_balance

            # 杠杆水平分类
            leverage_level = self._classify_leverage_level(margin_pct_change)

            return {
                'margin_balance': float(margin_balance),
                'margin_balance_change': float(margin_change),
                'margin_balance_pct_change': float(margin_pct_change),
                'short_balance': float(short_balance),
                'total_balance': float(total_balance),
                'leverage_level': leverage_level,
                'data_date': str(latest.get('交易日期', ''))
            }

        except Exception as e:
            logger.warning(f"获取融资融券指标失败: {str(e)}")
            return {}

    def get_main_fund_flow(self, index_code: str = 'sh000001', lookback_days: int = 5) -> Dict:
        """
        获取主力资金流向 - Phase 3新增

        Args:
            index_code: 指数代码
            lookback_days: 回溯天数

        Returns:
            {
                'today_main_inflow': 当日主力净流入(亿元),
                'today_super_inflow': 当日超级大单净流入(亿元),
                'today_big_inflow': 当日大单净流入(亿元),
                'cumulative_5d': 近5日主力累计净流入,
                'main_participation_rate': 主力参与度(%),
                'fund_flow_status': 资金流向状态
            }
        """
        try:
            # 获取个股资金流(使用上证指数作为市场整体代理)
            # 注: AKShare的主力资金接口主要针对个股,对指数支持有限
            # 这里使用市场整体资金流向数据
            df = ak.stock_individual_fund_flow_rank(indicator="今日")

            if len(df) == 0:
                return {}

            # 计算市场整体主力资金(汇总前100只个股)
            top_stocks = df.head(100)

            today_main = top_stocks['主力净流入-净额'].sum() / 100000000  # 转亿元
            today_super = top_stocks['超大单净流入-净额'].sum() / 100000000
            today_big = top_stocks['大单净流入-净额'].sum() / 100000000

            # 近5日数据
            df_5d = ak.stock_individual_fund_flow_rank(indicator="5日")
            top_5d = df_5d.head(100)
            cumulative_5d = top_5d['主力净流入-净额'].sum() / 100000000

            # 主力参与度(主力成交额/总成交额)
            total_amount = top_stocks['今日收盘'].sum()
            main_amount = abs(top_stocks['主力净流入-净额'].sum())
            participation_rate = (main_amount / total_amount * 100) if total_amount > 0 else 0

            # 资金流向状态
            fund_flow_status = self._classify_fund_flow(today_main, cumulative_5d)

            return {
                'today_main_inflow': float(today_main),
                'today_super_inflow': float(today_super),
                'today_big_inflow': float(today_big),
                'cumulative_5d': float(cumulative_5d),
                'main_participation_rate': float(participation_rate),
                'fund_flow_status': fund_flow_status
            }

        except Exception as e:
            logger.warning(f"获取主力资金流向失败: {str(e)}")
            return {}

    def get_dragon_tiger_list_metrics(self, lookback_days: int = 5) -> Dict:
        """
        获取龙虎榜指标 - Phase 3新增

        Args:
            lookback_days: 回溯天数

        Returns:
            {
                'lhb_stock_count': 龙虎榜股票数量,
                'institution_buy_count': 机构买入席位数,
                'institution_sell_count': 机构卖出席位数,
                'institution_net_buy': 机构净买入额(亿元),
                'activity_level': 活跃度水平
            }
        """
        try:
            # 获取最近的龙虎榜汇总数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)

            df = ak.stock_lhb_detail_em(
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )

            if len(df) == 0:
                return {}

            # 统计股票数量
            lhb_count = df['代码'].nunique()

            # 获取机构数据
            df_institution = ak.stock_lhb_jgmmtj_em(start_date=start_date.strftime('%Y%m%d'), end_date=end_date.strftime('%Y%m%d'))

            if len(df_institution) > 0:
                inst_buy_count = len(df_institution[df_institution['买方机构数'] > 0])
                inst_sell_count = len(df_institution[df_institution['卖方机构数'] > 0])
                inst_net_buy = df_institution['机构买入总额'].sum() - df_institution['机构卖出总额'].sum()
                inst_net_buy = inst_net_buy / 100000000  # 转亿元
            else:
                inst_buy_count = 0
                inst_sell_count = 0
                inst_net_buy = 0

            # 活跃度分类
            activity_level = self._classify_lhb_activity(lhb_count)

            return {
                'lhb_stock_count': int(lhb_count),
                'institution_buy_count': int(inst_buy_count),
                'institution_sell_count': int(inst_sell_count),
                'institution_net_buy': float(inst_net_buy),
                'activity_level': activity_level
            }

        except Exception as e:
            logger.warning(f"获取龙虎榜指标失败: {str(e)}")
            return {}

    def get_moving_averages(self, index_code: str, periods: list = [20, 60, 120]) -> Dict:
        """
        获取均线数据 - Phase 3新增

        Args:
            index_code: 指数代码
            periods: 均线周期列表

        Returns:
            {
                'current_price': 当前价格,
                'ma20': 20日均线,
                'ma60': 60日均线,
                'ma120': 120日均线,
                'ma_arrangement': 均线排列状态,
                'distance_to_ma20': 距20日均线距离(%),
                'distance_to_ma60': 距60日均线距离(%),
                'trend_strength': 趋势强度分数
            }
        """
        try:
            # 获取历史数据
            df = ak.stock_zh_index_daily(symbol=index_code)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

            # 计算均线
            for period in periods:
                df[f'ma{period}'] = df['close'].rolling(period).mean()

            # 最新数据
            latest = df.iloc[-1]
            current_price = float(latest['close'])

            result = {
                'current_price': current_price
            }

            # 添加各周期均线
            for period in periods:
                ma_value = float(latest[f'ma{period}'])
                result[f'ma{period}'] = ma_value

                # 计算距离
                distance = (current_price - ma_value) / ma_value * 100
                result[f'distance_to_ma{period}'] = float(distance)

            # 判断均线排列
            ma_values = [result[f'ma{p}'] for p in sorted(periods)]

            if all(ma_values[i] > ma_values[i+1] for i in range(len(ma_values)-1)):
                if current_price > ma_values[0]:
                    ma_arrangement = "完美多头排列"
                else:
                    ma_arrangement = "多头排列(价格回调)"
            elif all(ma_values[i] < ma_values[i+1] for i in range(len(ma_values)-1)):
                if current_price < ma_values[0]:
                    ma_arrangement = "完美空头排列"
                else:
                    ma_arrangement = "空头排列(价格反弹)"
            else:
                ma_arrangement = "均线粘合/交叉"

            result['ma_arrangement'] = ma_arrangement

            # 趋势强度(基于价格与均线的关系)
            distances = [result[f'distance_to_ma{p}'] for p in periods]
            avg_distance = sum(distances) / len(distances)
            trend_strength = min(10, max(0, abs(avg_distance)))  # 0-10分
            result['trend_strength'] = float(trend_strength)

            return result

        except Exception as e:
            logger.warning(f"获取均线数据失败: {str(e)}")
            return {}

    @staticmethod
    def _classify_leverage_level(margin_pct_change: float) -> str:
        """分类杠杆水平"""
        if margin_pct_change > 2:
            return "杠杆快速上升"
        elif margin_pct_change > 0.5:
            return "杠杆温和上升"
        elif margin_pct_change > -0.5:
            return "杠杆稳定"
        elif margin_pct_change > -2:
            return "杠杆温和下降"
        else:
            return "杠杆快速下降"

    @staticmethod
    def _classify_fund_flow(today: float, recent_5d: float) -> str:
        """分类资金流向状态"""
        if today > 100 and recent_5d > 300:
            return "主力大幅流入"
        elif today > 50 and recent_5d > 100:
            return "主力持续流入"
        elif today > 0:
            return "主力小幅流入"
        elif today > -50 and recent_5d > -100:
            return "主力小幅流出"
        elif today > -100 and recent_5d > -300:
            return "主力持续流出"
        else:
            return "主力大幅流出"

    @staticmethod
    def _classify_lhb_activity(lhb_count: int) -> str:
        """分类龙虎榜活跃度"""
        if lhb_count > 100:
            return "极度活跃"
        elif lhb_count > 50:
            return "非常活跃"
        elif lhb_count > 20:
            return "活跃"
        elif lhb_count > 10:
            return "一般"
        else:
            return "低迷"

    def get_comprehensive_metrics(
        self,
        index_code: str,
        date: datetime = None
    ) -> Dict:
        """
        获取综合指标（一次性获取所有增强数据）

        Returns:
            包含所有增强指标的字典
        """
        logger.info(f"正在获取 {index_code} 的综合增强指标...")

        date_str = date.strftime('%Y%m%d') if date else None

        metrics = {
            'volume_metrics': self.get_volume_metrics(index_code, date),
            'sentiment_metrics': self.get_market_sentiment(date_str),
            'macro_metrics': self.get_macro_indicators(),
            'divergence_metrics': self.get_volume_price_divergence(index_code),
            'valuation_metrics': self.get_valuation_metrics(date),
            'capital_flow_metrics': self.get_north_capital_flow(),
            'market_breadth_metrics': self.get_market_breadth_metrics(),
            'technical_indicators': self.get_technical_indicators(index_code),
            'volatility_metrics': self.get_volatility_metrics(index_code)
        }

        logger.info(f"成交量状态: {metrics['volume_metrics'].get('volume_status', 'N/A')}")
        logger.info(f"市场情绪: {metrics['sentiment_metrics'].get('sentiment_level', 'N/A')}")
        logger.info(f"估值水平: {metrics['valuation_metrics'].get('valuation_level', 'N/A')}")
        logger.info(f"北向资金: {metrics['capital_flow_metrics'].get('flow_status', 'N/A')}")

        return metrics


if __name__ == '__main__':
    # 测试
    provider = EnhancedDataProvider()

    print("=== 测试增强数据获取 ===\n")

    # 1. 成交量指标
    print("1. 成交量指标")
    volume_metrics = provider.get_volume_metrics('sh000001')
    for k, v in volume_metrics.items():
        print(f"   {k}: {v}")

    # 2. 市场情绪
    print("\n2. 市场情绪指标")
    sentiment = provider.get_market_sentiment()
    for k, v in sentiment.items():
        print(f"   {k}: {v}")

    # 3. 宏观指标
    print("\n3. 宏观指标")
    macro = provider.get_macro_indicators()
    for k, v in macro.items():
        print(f"   {k}: {v}")

    # 4. 量价背离
    print("\n4. 量价背离检测")
    divergence = provider.get_volume_price_divergence('sh000001')
    for k, v in divergence.items():
        print(f"   {k}: {v}")

    # 5. 综合指标
    print("\n5. 综合指标")
    comprehensive = provider.get_comprehensive_metrics('sh000001')
    print(f"   获取成功，包含 {len(comprehensive)} 个维度")
