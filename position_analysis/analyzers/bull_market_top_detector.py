"""
牛市见顶检测器
基于雪球专栏《牛市见顶的信号是什么?》实现
综合8个指标判断A股/港股牛市见顶风险
"""
import akshare as ak
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BullMarketTopDetector:
    """牛市见顶检测器"""

    def __init__(self):
        """初始化牛市见顶检测器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 3600  # 1小时缓存(宏观数据更新频率低)

        # 历史阈值(基于文章研究)
        self.thresholds = {
            # 信号一: 成交量/居民存款
            'turnover_ratio': {
                'extreme': 0.04,    # 4%: 极度危险
                'high': 0.03,       # 3%: 高风险
                'elevated': 0.02,   # 2%: 警惕
                'normal': 0.015     # 1.5%: 正常
            },
            # 信号二: 股债利差
            'equity_bond_spread': {
                'bottom': 0.06,     # 6%: 底部区间
                'safe': 0.04,       # 4%: 安全
                'warning': 0.03,    # 3%: 警告
                'top': 0.02         # 2%: 顶部区间(文章说<3%)
            },
            # 信号三: 沪深300 PE分位数
            'hs300_pe_percentile': {
                'bottom': 20,       # <20%: 底部
                'safe': 50,         # 50%: 正常
                'elevated': 70,     # 70%: 偏高
                'top': 80           # >80%: 顶部
            },
            # 信号四: 巴菲特指标
            'buffett_indicator': {
                'bottom': 0.50,     # <50%: 底部
                'safe': 0.80,       # 80%: 安全
                'elevated': 1.00,   # 100%: 警惕
                'top': 1.20         # >120%: 泡沫
            },
            # 信号五: 融资融券/居民存款
            'margin_ratio': {
                'bottom': 0.01,     # 1%: 底部
                'normal': 0.02,     # 2%: 正常
                'elevated': 0.03,   # 3%: 警惕
                'extreme': 0.04     # 4%: 极度过热
            }
        }

    def _get_cached_data(self, key: str, fetch_func, *args, **kwargs):
        """通用缓存获取方法"""
        if key in self.cache:
            if (datetime.now() - self.cache_time[key]).seconds < self.cache_duration:
                logger.info(f"使用缓存的{key}数据")
                return self.cache[key]

        try:
            data = fetch_func(*args, **kwargs)
            self.cache[key] = data
            self.cache_time[key] = datetime.now()
            return data
        except Exception as e:
            logger.error(f"获取{key}数据失败: {str(e)}")
            return None

    def get_resident_deposits(self) -> Optional[float]:
        """
        获取居民总存款(万亿元)

        Returns:
            居民总存款数值
        """
        try:
            # 获取货币供应量数据
            df = ak.macro_china_money_supply()
            if df.empty:
                return None

            # 最新的居民存款数据(住户存款)
            # 列名通常是: 月份, 货币和准货币(M2), 货币(M1), 流通中现金(M0), 住户存款等
            df = df.sort_values('月份', ascending=False)

            # 尝试获取住户存款列
            deposit_col = None
            for col in df.columns:
                if '住户' in str(col) or '居民' in str(col):
                    deposit_col = col
                    break

            if deposit_col:
                deposits = float(df[deposit_col].iloc[0])
                logger.info(f"居民总存款: {deposits:.2f}万亿")
                return deposits
            else:
                # 如果找不到住户存款,估算: M2 * 0.6 (经验比例)
                m2 = float(df['货币和准货币(M2)'].iloc[0]) if '货币和准货币(M2)' in df.columns else None
                if m2:
                    deposits = m2 * 0.6
                    logger.info(f"居民总存款(估算): {deposits:.2f}万亿")
                    return deposits

            return None
        except Exception as e:
            logger.error(f"获取居民存款失败: {str(e)}")
            return None

    def calculate_turnover_ratio(self) -> Dict[str, Any]:
        """
        信号一: 成交量/居民存款比值
        使用上证+深证指数成交量之和

        Returns:
            成交量比值分析结果
        """
        try:
            # 获取上证和深证指数最新交易量
            df_sh = ak.stock_zh_index_daily(symbol="sh000001")  # 上证指数
            df_sz = ak.stock_zh_index_daily(symbol="sz399001")  # 深证成指

            if df_sh.empty or df_sz.empty:
                return {'error': '无法获取交易量数据'}

            # 最新交易日成交额(元),转换为亿元
            # yfinance返回的volume对股票是股数,对指数是成交额(元)
            sh_volume = float(df_sh['volume'].iloc[-1]) / 100000000  # 转为亿元
            sz_volume = float(df_sz['volume'].iloc[-1]) / 100000000
            latest_volume = sh_volume + sz_volume

            # 获取居民存款(万亿元)
            deposits = self.get_resident_deposits()
            if not deposits:
                return {'error': '无法获取居民存款数据'}

            # 计算比值
            ratio = latest_volume / (deposits * 10000)  # deposits单位是万亿,转换为亿

            # 风险等级
            if ratio > self.thresholds['turnover_ratio']['extreme']:
                risk_level = '极度危险'
                score = 100
            elif ratio > self.thresholds['turnover_ratio']['high']:
                risk_level = '高风险'
                score = 75
            elif ratio > self.thresholds['turnover_ratio']['elevated']:
                risk_level = '警惕'
                score = 50
            elif ratio > self.thresholds['turnover_ratio']['normal']:
                risk_level = '正常'
                score = 25
            else:
                risk_level = '低风险'
                score = 0

            return {
                'ratio': ratio * 100,  # 转换为百分比
                'latest_volume': latest_volume,
                'resident_deposits': deposits,
                'risk_level': risk_level,
                'score': score,
                'threshold_extreme': self.thresholds['turnover_ratio']['extreme'] * 100,
                'signal': f"成交量/居民存款={ratio*100:.2f}%, {risk_level}",
                'interpretation': self._interpret_turnover_ratio(ratio)
            }
        except Exception as e:
            logger.error(f"计算成交量比值失败: {str(e)}")
            return {'error': str(e)}

    def _interpret_turnover_ratio(self, ratio: float) -> str:
        """解读成交量比值"""
        ratio_pct = ratio * 100
        if ratio > 0.04:
            return f"成交量/居民存款={ratio_pct:.2f}%,超过4%极限阈值,增量资金接近顶峰,牛市见顶风险极高"
        elif ratio > 0.03:
            return f"成交量/居民存款={ratio_pct:.2f}%,接近危险区域,市场过热"
        elif ratio > 0.02:
            return f"成交量/居民存款={ratio_pct:.2f}%,市场活跃度高,需警惕"
        else:
            return f"成交量/居民存款={ratio_pct:.2f}%,市场活跃度正常"

    def calculate_equity_bond_spread(self) -> Dict[str, Any]:
        """
        信号二: 股债利差
        沪深300市盈率倒数 - 十年国债收益率

        Returns:
            股债利差分析结果
        """
        try:
            # 获取沪深300估值(使用中证指数估值数据)
            df_pe = ak.stock_zh_index_value_csindex(symbol="000300")  # 沪深300
            if df_pe.empty:
                return {'error': '无法获取沪深300估值数据'}

            # 最新PE(使用市盈率1列,按位置索引避免中文列名问题)
            # 列顺序: 日期,指数代码,指数名称全称,指数名称简称,指数英文全称,指数英文简称,市盈率1,市盈率2,股息率1,股息率2
            latest_pe = float(df_pe.iloc[-1, 6])  # 第7列是市盈率1
            earnings_yield = 1 / latest_pe if latest_pe > 0 else 0  # 盈利收益率 = PE倒数

            # 获取十年国债收益率
            df_bond = ak.bond_zh_us_rate()
            if df_bond.empty:
                return {'error': '无法获取国债收益率数据'}

            # 中国十年国债收益率(列索引3: 中国国债收益率10年)
            # 取最新非NaN值
            bond_series = pd.to_numeric(df_bond.iloc[:, 3], errors='coerce').dropna()
            if bond_series.empty:
                return {'error': '无法获取有效的国债收益率'}
            cn_10y = float(bond_series.iloc[-1]) / 100  # 转换为小数

            # 股债利差
            spread = earnings_yield - cn_10y

            # 风险等级
            if spread < self.thresholds['equity_bond_spread']['top']:
                risk_level = '极度危险'
                score = 100
            elif spread < self.thresholds['equity_bond_spread']['warning']:
                risk_level = '高风险'
                score = 75
            elif spread < self.thresholds['equity_bond_spread']['safe']:
                risk_level = '警惕'
                score = 50
            elif spread < self.thresholds['equity_bond_spread']['bottom']:
                risk_level = '正常'
                score = 25
            else:
                risk_level = '低风险'
                score = 0

            return {
                'spread': spread * 100,  # 百分比
                'hs300_pe': latest_pe,
                'earnings_yield': earnings_yield * 100,
                'bond_10y_yield': cn_10y * 100,
                'risk_level': risk_level,
                'score': score,
                'threshold_warning': self.thresholds['equity_bond_spread']['warning'] * 100,
                'signal': f"股债利差={spread*100:.2f}%, {risk_level}",
                'interpretation': self._interpret_spread(spread)
            }
        except Exception as e:
            logger.error(f"计算股债利差失败: {str(e)}")
            return {'error': str(e)}

    def _interpret_spread(self, spread: float) -> str:
        """解读股债利差"""
        spread_pct = spread * 100
        if spread < 0.02:
            return f"股债利差={spread_pct:.2f}%,低于2%危险区,股票吸引力大幅下降,历史上牛市见顶"
        elif spread < 0.03:
            return f"股债利差={spread_pct:.2f}%,低于3%警戒线,接近顶部区间"
        elif spread < 0.04:
            return f"股债利差={spread_pct:.2f}%,正常偏低,需关注"
        elif spread > 0.06:
            return f"股债利差={spread_pct:.2f}%,大于6%,处于底部区间,股票性价比高"
        else:
            return f"股债利差={spread_pct:.2f}%,正常区间"

    def calculate_hs300_pe_percentile(self) -> Dict[str, Any]:
        """
        信号三: 沪深300 PE分位数

        Returns:
            PE分位数分析结果
        """
        try:
            # 获取沪深300历史估值
            df = ak.stock_zh_index_value_csindex(symbol="000300")
            if df.empty or len(df) < 252:  # 至少需要1年数据
                return {'error': '沪深300历史数据不足'}

            # 计算近10年PE分位数
            df_10y = df.tail(252 * 10) if len(df) >= 252 * 10 else df

            # 使用市盈率1(第7列,索引6)
            current_pe = float(df.iloc[-1, 6])
            pe_series = pd.to_numeric(df_10y.iloc[:, 6], errors='coerce').dropna()

            # 计算分位数
            percentile = float((pe_series <= current_pe).sum() / len(pe_series) * 100)

            # 历史统计
            avg_pe = float(pe_series.mean())
            median_pe = float(pe_series.median())
            min_pe = float(pe_series.min())
            max_pe = float(pe_series.max())

            # 风险等级
            if percentile > self.thresholds['hs300_pe_percentile']['top']:
                risk_level = '极度危险'
                score = 100
            elif percentile > self.thresholds['hs300_pe_percentile']['elevated']:
                risk_level = '高风险'
                score = 75
            elif percentile > self.thresholds['hs300_pe_percentile']['safe']:
                risk_level = '警惕'
                score = 50
            elif percentile > self.thresholds['hs300_pe_percentile']['bottom']:
                risk_level = '正常'
                score = 25
            else:
                risk_level = '低风险'
                score = 0

            return {
                'current_pe': current_pe,
                'percentile': percentile,
                'avg_pe': avg_pe,
                'median_pe': median_pe,
                'min_pe': min_pe,
                'max_pe': max_pe,
                'risk_level': risk_level,
                'score': score,
                'threshold_top': self.thresholds['hs300_pe_percentile']['top'],
                'signal': f"沪深300 PE分位数={percentile:.1f}%, {risk_level}",
                'interpretation': self._interpret_pe_percentile(percentile, current_pe, avg_pe)
            }
        except Exception as e:
            logger.error(f"计算沪深300 PE分位数失败: {str(e)}")
            return {'error': str(e)}

    def _interpret_pe_percentile(self, percentile: float, current_pe: float, avg_pe: float) -> str:
        """解读PE分位数"""
        if percentile > 80:
            return f"PE分位数={percentile:.1f}%,处于历史高位,估值被高估,牛市结束风险高"
        elif percentile > 70:
            return f"PE分位数={percentile:.1f}%,估值偏高,需警惕泡沫风险"
        elif percentile < 20:
            return f"PE分位数={percentile:.1f}%,处于历史低位,估值被低估,安全边际高"
        else:
            return f"PE分位数={percentile:.1f}%,当前PE={current_pe:.1f},历史均值={avg_pe:.1f},估值正常"

    def calculate_buffett_indicator(self) -> Dict[str, Any]:
        """
        信号四: 巴菲特指标
        股市总市值 / GDP
        使用历史月度数据估算当前总市值

        Returns:
            巴菲特指标分析结果
        """
        try:
            # 获取A股总市值(月度历史数据)
            df_market_cap = ak.macro_china_stock_market_cap()
            if df_market_cap.empty:
                return {'error': '无法获取A股总市值'}

            # 最新总市值(使用深沪两市流通市值之和,列索引3和4)
            # 列: 月份,总股本-上海,总股本-深圳,流通市值-上海,流通市值-深圳,...
            sh_cap = float(df_market_cap.iloc[-1, 3])  # 流通市值-上海(亿元)
            sz_cap = float(df_market_cap.iloc[-1, 4])  # 流通市值-深圳(亿元)
            total_market_cap = sh_cap + sz_cap

            # 获取GDP数据
            df_gdp = ak.macro_china_gdp()
            if df_gdp.empty:
                return {'error': '无法获取GDP数据'}

            # 最新GDP(亿元) - 使用国内生产总值-现价(列索引1)
            # 数据可能是季度累计值,直接使用最新值
            latest_gdp_value = float(df_gdp.iloc[-1, 1])

            # 检查是否是季度数据还是年度数据(通过时间列判断)
            # 如果是季度数据,需要年化(×4);如果已经是年度,直接使用
            # 简化处理:如果数据<50万亿,认为是季度值,否则是年度值
            if latest_gdp_value < 500000:
                latest_gdp_annual = latest_gdp_value * 4
            else:
                latest_gdp_annual = latest_gdp_value

            # 巴菲特指标
            buffett_ratio = total_market_cap / latest_gdp_annual

            # 风险等级
            if buffett_ratio > self.thresholds['buffett_indicator']['top']:
                risk_level = '极度危险'
                score = 100
            elif buffett_ratio > self.thresholds['buffett_indicator']['elevated']:
                risk_level = '高风险'
                score = 75
            elif buffett_ratio > self.thresholds['buffett_indicator']['safe']:
                risk_level = '警惕'
                score = 50
            elif buffett_ratio > self.thresholds['buffett_indicator']['bottom']:
                risk_level = '正常'
                score = 25
            else:
                risk_level = '低风险'
                score = 0

            return {
                'buffett_ratio': buffett_ratio * 100,  # 百分比
                'market_cap': total_market_cap,
                'gdp': latest_gdp_annual,
                'risk_level': risk_level,
                'score': score,
                'threshold_top': self.thresholds['buffett_indicator']['top'] * 100,
                'signal': f"巴菲特指标={buffett_ratio*100:.1f}%, {risk_level}",
                'interpretation': self._interpret_buffett(buffett_ratio)
            }
        except Exception as e:
            logger.error(f"计算巴菲特指标失败: {str(e)}")
            return {'error': str(e)}

    def _interpret_buffett(self, ratio: float) -> str:
        """解读巴菲特指标"""
        ratio_pct = ratio * 100
        if ratio > 1.20:
            return f"巴菲特指标={ratio_pct:.1f}%,超过120%泡沫阈值,市场处于泡沫状态"
        elif ratio > 1.00:
            return f"巴菲特指标={ratio_pct:.1f}%,超过100%警戒线,市场估值偏高"
        elif ratio < 0.50:
            return f"巴菲特指标={ratio_pct:.1f}%,低于50%,市场处于底部区域"
        else:
            return f"巴菲特指标={ratio_pct:.1f}%,估值正常"

    def calculate_margin_ratio(self) -> Dict[str, Any]:
        """
        信号五: 融资融券余额/居民存款

        Returns:
            两融比值分析结果
        """
        try:
            # 获取融资融券余额(上海+深圳)
            df_margin_sh = ak.macro_china_market_margin_sh()
            df_margin_sz = ak.macro_china_market_margin_sz()

            if df_margin_sh.empty or df_margin_sz.empty:
                return {'error': '无法获取融资融券数据'}

            # 最新两融余额(元),转换为亿元
            # 上海: 列索引6是融资融券余额, 深圳: 列索引6也是融资融券余额
            sh_margin = float(df_margin_sh.iloc[-1, 6]) / 100000000
            sz_margin = float(df_margin_sz.iloc[-1, 6]) / 100000000
            margin_balance = sh_margin + sz_margin

            # 获取居民存款(万亿元)
            deposits = self.get_resident_deposits()
            if not deposits:
                return {'error': '无法获取居民存款数据'}

            # 计算比值
            ratio = margin_balance / (deposits * 10000)  # deposits单位是万亿,转换为亿

            # 风险等级
            if ratio > self.thresholds['margin_ratio']['extreme']:
                risk_level = '极度危险'
                score = 100
            elif ratio > self.thresholds['margin_ratio']['elevated']:
                risk_level = '高风险'
                score = 75
            elif ratio > self.thresholds['margin_ratio']['normal']:
                risk_level = '警惕'
                score = 50
            elif ratio > self.thresholds['margin_ratio']['bottom']:
                risk_level = '正常'
                score = 25
            else:
                risk_level = '低风险'
                score = 0

            return {
                'ratio': ratio * 100,  # 百分比
                'margin_balance': margin_balance,
                'resident_deposits': deposits,
                'risk_level': risk_level,
                'score': score,
                'threshold_extreme': self.thresholds['margin_ratio']['extreme'] * 100,
                'signal': f"融资融券/居民存款={ratio*100:.2f}%, {risk_level}",
                'interpretation': self._interpret_margin_ratio(ratio)
            }
        except Exception as e:
            logger.error(f"计算两融比值失败: {str(e)}")
            return {'error': str(e)}

    def _interpret_margin_ratio(self, ratio: float) -> str:
        """解读两融比值"""
        ratio_pct = ratio * 100
        if ratio > 0.04:
            return f"融资融券/居民存款={ratio_pct:.2f}%,超过4%极限,市场情绪极度过热,触发降温风险"
        elif ratio > 0.03:
            return f"融资融券/居民存款={ratio_pct:.2f}%,接近危险区,杠杆情绪高涨"
        elif ratio > 0.02:
            return f"融资融券/居民存款={ratio_pct:.2f}%,杠杆使用正常偏高"
        else:
            return f"融资融券/居民存款={ratio_pct:.2f}%,杠杆使用合理"

    def calculate_bbi_signal(self, index_code: str = "000001") -> Dict[str, Any]:
        """
        信号六: BBI多空线
        BBI = (MA5 + MA10 + MA20 + MA60) / 4

        Args:
            index_code: 指数代码,默认上证指数

        Returns:
            BBI分析结果
        """
        try:
            # 获取指数历史数据
            df = ak.stock_zh_index_daily(symbol=f"sh{index_code}")
            if df.empty or len(df) < 60:
                return {'error': 'BBI计算数据不足'}

            df = df.tail(250)  # 取最近一年数据

            # 计算均线
            df['ma5'] = df['close'].rolling(5).mean()
            df['ma10'] = df['close'].rolling(10).mean()
            df['ma20'] = df['close'].rolling(20).mean()
            df['ma60'] = df['close'].rolling(60).mean()

            # 计算BBI
            df['bbi'] = (df['ma5'] + df['ma10'] + df['ma20'] + df['ma60']) / 4

            # 去除NaN
            df = df.dropna()

            # 最新数据
            current_price = float(df['close'].iloc[-1])
            current_bbi = float(df['bbi'].iloc[-1])

            # 判断趋势
            above_bbi = current_price > current_bbi
            bbi_slope = (df['bbi'].iloc[-1] - df['bbi'].iloc[-20]) / df['bbi'].iloc[-20]  # 20日斜率

            # 统计K线在BBI上方的天数占比
            days_above = (df['close'] > df['bbi']).sum()
            ratio_above = days_above / len(df)

            # 风险评估
            if above_bbi and bbi_slope > 0 and ratio_above > 0.8:
                risk_level = '牛市中后期'
                score = 60
            elif above_bbi and bbi_slope > 0:
                risk_level = '牛市中期'
                score = 40
            elif not above_bbi and bbi_slope < 0 and ratio_above < 0.2:
                risk_level = '熊市'
                score = 0
            elif not above_bbi and bbi_slope < 0:
                risk_level = '调整/熊市'
                score = 20
            else:
                risk_level = '震荡'
                score = 30

            return {
                'current_price': current_price,
                'current_bbi': current_bbi,
                'above_bbi': above_bbi,
                'bbi_slope': bbi_slope * 100,
                'days_above_ratio': ratio_above * 100,
                'risk_level': risk_level,
                'score': score,
                'signal': f"BBI多空线: {'牛市趋势' if above_bbi else '熊市趋势'}, {risk_level}",
                'interpretation': self._interpret_bbi(above_bbi, bbi_slope, ratio_above)
            }
        except Exception as e:
            logger.error(f"计算BBI失败: {str(e)}")
            return {'error': str(e)}

    def _interpret_bbi(self, above: bool, slope: float, ratio: float) -> str:
        """解读BBI"""
        if above and slope > 0 and ratio > 0.8:
            return f"价格持续在BBI上方运行且BBI向上,处于牛市中后期,警惕见顶"
        elif above and slope > 0:
            return f"价格在BBI上方且BBI向上,处于牛市趋势"
        elif not above and slope < 0:
            return f"价格在BBI下方且BBI向下,处于熊市/调整趋势"
        else:
            return f"价格与BBI纠缠,处于震荡市"

    def detect_top_risk(self, index_code: str = "000001") -> Dict[str, Any]:
        """
        综合检测牛市见顶风险

        Args:
            index_code: 指数代码,默认上证指数

        Returns:
            综合分析结果
        """
        result = {
            'timestamp': datetime.now(),
            'index_code': index_code,
            'signals': {},
            'overall_risk': {},
        }

        # 计算各项指标
        signals = [
            ('turnover_ratio', self.calculate_turnover_ratio),
            ('equity_bond_spread', self.calculate_equity_bond_spread),
            ('hs300_pe_percentile', self.calculate_hs300_pe_percentile),
            ('buffett_indicator', self.calculate_buffett_indicator),
            ('margin_ratio', self.calculate_margin_ratio),
            ('bbi_signal', lambda: self.calculate_bbi_signal(index_code)),
        ]

        total_score = 0
        valid_signals = 0

        for signal_name, calc_func in signals:
            signal_result = calc_func()
            result['signals'][signal_name] = signal_result

            if 'error' not in signal_result and 'score' in signal_result:
                total_score += signal_result['score']
                valid_signals += 1

        # 计算综合得分
        if valid_signals > 0:
            avg_score = total_score / valid_signals

            # 综合风险等级
            if avg_score >= 85:
                overall_risk = '极度危险'
                recommendation = '强烈建议: 立即减仓至30%以下,大概率接近牛市顶部'
            elif avg_score >= 70:
                overall_risk = '高风险'
                recommendation = '建议: 减仓至50%,多个指标接近见顶阈值'
            elif avg_score >= 50:
                overall_risk = '警惕'
                recommendation = '谨慎: 控制仓位在60-70%,密切关注市场信号'
            elif avg_score >= 30:
                overall_risk = '正常'
                recommendation = '正常配置: 维持标准仓位70-80%'
            else:
                overall_risk = '安全'
                recommendation = '积极配置: 可保持80-90%仓位'

            result['overall_risk'] = {
                'score': avg_score,
                'level': overall_risk,
                'recommendation': recommendation,
                'valid_signals': valid_signals,
                'summary': self._generate_summary(result['signals'])
            }

        return result

    def _generate_summary(self, signals: Dict) -> str:
        """生成风险总结"""
        summary_parts = []

        # 统计各风险等级信号数量
        extreme_count = 0
        high_count = 0
        warning_count = 0

        for signal_name, signal_data in signals.items():
            if 'error' in signal_data:
                continue

            risk_level = signal_data.get('risk_level', '')
            if risk_level in ['极度危险', '极度过热']:
                extreme_count += 1
            elif risk_level in ['高风险', '危险']:
                high_count += 1
            elif risk_level in ['警惕', '警告']:
                warning_count += 1

        if extreme_count > 0:
            summary_parts.append(f"{extreme_count}个指标达到极度危险水平")
        if high_count > 0:
            summary_parts.append(f"{high_count}个指标处于高风险状态")
        if warning_count > 0:
            summary_parts.append(f"{warning_count}个指标发出警惕信号")

        if not summary_parts:
            return "所有指标处于正常或安全水平"

        return "; ".join(summary_parts)


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    detector = BullMarketTopDetector()

    print("=" * 80)
    print("牛市见顶检测器测试")
    print("=" * 80)

    result = detector.detect_top_risk(index_code="000001")

    if 'overall_risk' in result:
        overall = result['overall_risk']
        print(f"\n综合风险评分: {overall['score']:.1f}/100")
        print(f"风险等级: {overall['level']}")
        print(f"建议: {overall['recommendation']}")
        print(f"风险总结: {overall['summary']}")

        print(f"\n各项指标详情:")
        for signal_name, signal_data in result['signals'].items():
            if 'error' not in signal_data:
                print(f"\n{signal_name}:")
                print(f"  信号: {signal_data.get('signal', 'N/A')}")
                print(f"  解读: {signal_data.get('interpretation', 'N/A')}")
    else:
        print("检测失败")

    print("\n" + "=" * 80)
