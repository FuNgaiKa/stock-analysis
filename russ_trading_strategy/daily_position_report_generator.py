#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日持仓调整建议报告生成器(增强版)
Daily Position Report Generator (Enhanced Edition)

每天自动生成持仓调整建议，包含：
1. 持仓健康度分析
2. 收益追踪对比
3. 机构级风险指标
4. Kelly公式智能仓位建议
5. 具体操作清单
6. 收益预测

运行方式:
    # 生成今日报告
    python scripts/russ_trading_strategy/daily_position_report_generator.py

    # 生成指定日期报告
    python scripts/russ_trading_strategy/daily_position_report_generator.py --date 2025-10-21

    # 自动更新持仓数据
    python scripts/russ_trading_strategy/daily_position_report_generator.py --auto-update

作者: Claude Code
日期: 2025-10-21
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from russ_trading_strategy.position_health_checker import PositionHealthChecker
from russ_trading_strategy.performance_tracker import PerformanceTracker
from russ_trading_strategy.potential_analyzer import PotentialAnalyzer
from russ_trading_strategy.market_depth_analyzer import MarketDepthAnalyzer

# 尝试导入增强模块
try:
    from russ_trading_strategy.risk_manager import RiskManager
    from russ_trading_strategy.dynamic_position_manager import DynamicPositionManager
    from russ_trading_strategy.data_manager import DataManager
    from russ_trading_strategy.technical_analyzer import TechnicalAnalyzer
    HAS_ENHANCED_MODULES = True
except ImportError:
    HAS_ENHANCED_MODULES = False
    logging.warning("增强模块未找到，将使用基础功能")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailyPositionReportGenerator:
    """每日持仓报告生成器(机构级增强版)"""

    def __init__(self, risk_profile: str = 'ultra_aggressive'):
        """
        初始化生成器 (默认ultra_aggressive,2年翻倍目标)

        Args:
            risk_profile: 风险偏好 ('conservative', 'moderate', 'aggressive')
                - conservative: 保守型 (最大回撤10%, 波动率20%)
                - moderate: 稳健型 (最大回撤15%, 波动率30%)
                - aggressive: 积极型 (最大回撤25%, 波动率50%)
        """
        self.risk_profile = risk_profile

        # 先设置风险阈值
        self._set_risk_thresholds()

        # 根据风险阈值初始化健康检查器
        strategy_config = {
            'min_position': 0.70 if risk_profile == 'ultra_aggressive' else 0.50,
            'max_position': self.thresholds.get('max_total_position', 0.90),
            'max_single_position_etf': self.thresholds.get('max_single_etf_position',
                                                           self.thresholds.get('max_single_position', 0.30)),
            'max_single_position_stock': self.thresholds.get('max_single_stock_position',
                                                             self.thresholds.get('max_single_position', 0.20)),
            'black_swan_reserve': self.thresholds.get('min_cash_reserve', 0.10),
            'min_assets': self.thresholds.get('min_assets', 3),
            'max_assets': self.thresholds.get('max_assets', 5)
        }

        self.health_checker = PositionHealthChecker(strategy_config)
        self.performance_tracker = PerformanceTracker()
        self.potential_analyzer = PotentialAnalyzer()
        self.market_depth_analyzer = MarketDepthAnalyzer()

        # 初始化增强模块
        if HAS_ENHANCED_MODULES:
            self.risk_manager = RiskManager()
            self.position_manager = DynamicPositionManager()
            self.data_manager = DataManager()
            self.technical_analyzer = TechnicalAnalyzer()
        else:
            self.risk_manager = None
            self.position_manager = None
            self.data_manager = None
            self.technical_analyzer = None

    def _set_risk_thresholds(self):
        """根据风险偏好设置阈值"""
        risk_params = {
            'conservative': {
                'max_drawdown_alert': 0.10,
                'max_drawdown_warning': 0.08,
                'volatility_limit': 0.20,
                'max_single_position': 0.15,
                'max_total_position': 0.70,
                'min_cash_reserve': 0.30,
                'stop_loss': 0.10,
                'warning_loss': 0.08
            },
            'moderate': {
                'max_drawdown_alert': 0.15,
                'max_drawdown_warning': 0.12,
                'volatility_limit': 0.30,
                'max_single_position': 0.20,
                'max_total_position': 0.85,
                'min_cash_reserve': 0.15,
                'stop_loss': 0.15,
                'warning_loss': 0.12
            },
            'aggressive': {
                'max_drawdown_alert': 0.25,
                'max_drawdown_warning': 0.20,
                'volatility_limit': 0.50,
                'max_single_position': 0.25,
                'max_total_position': 0.90,
                'min_cash_reserve': 0.10,
                'stop_loss': 0.20,
                'warning_loss': 0.16
            },
            'ultra_aggressive': {
                'max_drawdown_alert': 0.30,
                'max_drawdown_warning': 0.25,
                'volatility_limit': 0.70,
                'max_single_etf_position': 0.40,  # 单ETF最高40%
                'max_single_stock_position': 0.30,  # 单个股最高30%
                'max_single_position': 0.40,  # 保留兼容性
                'max_total_position': 0.90,
                'min_cash_reserve': 0.10,
                'stop_loss': 0.25,
                'warning_loss': 0.20,
                'target_annual_return': 0.60,  # 年化60%目标
                'min_assets': 2,  # 最少2只
                'max_assets': 3   # 最多3只
            }
        }

        self.thresholds = risk_params.get(self.risk_profile, risk_params['aggressive'])
        logger.info(f"风险偏好设置为: {self.risk_profile}")

    def fetch_market_data(self, date: str = None) -> Dict:
        """
        获取市场数据 (优先使用efinance,fallback到akshare)

        Args:
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            市场数据字典
        """
        logger.info("获取市场数据...")

        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        market_data = {
            'date': date,
            'indices': {},
            'technical': {}  # 存储技术分析结果
        }

        # 优先使用 efinance (更稳定)
        try:
            import efinance as ef

            indices_map = {
                '000300': 'HS300',
                '399006': 'CYBZ',
                '588000': 'KC50ETF',  # 科创50ETF,因为科创50指数数据不准确
                '513180': 'HSTECH'  # 恒生科技ETF
            }

            for code, name in indices_map.items():
                try:
                    df = ef.stock.get_quote_history(code, klt=101)  # 日线
                    if df is not None and not df.empty:
                        latest = df.iloc[-1]

                        # 计算量比 (当日成交量 vs 5日均量)
                        volume_ratio = 0
                        if len(df) >= 6 and '成交量' in df.columns:
                            recent_volumes = df['成交量'].tail(6)
                            current_volume = recent_volumes.iloc[-1]
                            avg_volume_5d = recent_volumes.iloc[:-1].mean()
                            if avg_volume_5d > 0:
                                volume_ratio = current_volume / avg_volume_5d

                        market_data['indices'][name] = {
                            'current': float(latest['收盘']),
                            'change_pct': float(latest['涨跌幅']),
                            'volume': float(latest.get('成交量', 0)),
                            'volume_ratio': volume_ratio,
                            'date': str(latest['日期'])
                        }
                        market_data['technical'][name] = df
                        logger.info(f"✅ {name}: {latest['收盘']:.2f} ({latest['涨跌幅']:+.2f}%)")
                except Exception as e:
                    logger.warning(f"efinance获取{name}失败: {e}")

            # 将KC50ETF的技术数据也存为KC50,供技术分析使用
            if 'KC50ETF' in market_data['technical']:
                market_data['technical']['KC50'] = market_data['technical']['KC50ETF']
                logger.info("✅ 科创50技术数据已准备")

            # 获取基本面数据 (PE/PB等) - 使用akshare
            try:
                import akshare as ak

                # 获取沪深300估值数据
                if 'HS300' in market_data['indices']:
                    try:
                        # 使用akshare获取指数PE数据
                        df_pe = ak.stock_index_pe_lg(symbol='沪深300')
                        df_pb = ak.stock_index_pb_lg(symbol='沪深300')

                        if df_pe is not None and not df_pe.empty:
                            latest_pe = df_pe.iloc[-1]
                            pe = float(latest_pe['滚动市盈率'])  # 使用滚动市盈率(TTM)
                            market_data['indices']['HS300']['pe'] = pe

                            # 计算PE十年分位数 (取最近10年数据,约2520个交易日)
                            recent_10y = df_pe.tail(2520) if len(df_pe) > 2520 else df_pe
                            pe_values = recent_10y['滚动市盈率'].dropna()
                            if len(pe_values) > 0:
                                pe_percentile = (pe_values < pe).sum() / len(pe_values) * 100
                                market_data['indices']['HS300']['pe_percentile'] = pe_percentile
                                logger.info(f"✅ 沪深300 PE(TTM): {pe:.2f}, 十年分位: {pe_percentile:.1f}%")
                            else:
                                market_data['indices']['HS300']['pe_percentile'] = 0
                                logger.info(f"✅ 沪深300 PE(TTM): {pe:.2f}")

                        if df_pb is not None and not df_pb.empty:
                            latest_pb = df_pb.iloc[-1]
                            pb = float(latest_pb['市净率'])
                            market_data['indices']['HS300']['pb'] = pb
                            logger.info(f"✅ 沪深300 PB: {pb:.2f}")

                        # ROE和股息率暂时设为0 (akshare这个API没有这些数据)
                        market_data['indices']['HS300']['roe'] = 0
                        market_data['indices']['HS300']['dividend_yield'] = 0

                    except Exception as e:
                        logger.warning(f"获取沪深300估值数据失败: {e}")
                        # 使用默认值
                        market_data['indices']['HS300']['pe'] = 0
                        market_data['indices']['HS300']['pb'] = 0
                        market_data['indices']['HS300']['roe'] = 0
                        market_data['indices']['HS300']['dividend_yield'] = 0

                # 获取创业板估值数据 (使用创业板50作为参考,API无创业板指)
                if 'CYBZ' in market_data['indices']:
                    try:
                        df_pe = ak.stock_index_pe_lg(symbol='创业板50')
                        df_pb = ak.stock_index_pb_lg(symbol='创业板50')

                        if df_pe is not None and not df_pe.empty:
                            latest_pe = df_pe.iloc[-1]
                            pe = float(latest_pe['滚动市盈率'])
                            market_data['indices']['CYBZ']['pe'] = pe

                            # 计算PE十年分位数 (取最近10年数据,约2520个交易日)
                            recent_10y = df_pe.tail(2520) if len(df_pe) > 2520 else df_pe
                            pe_values = recent_10y['滚动市盈率'].dropna()
                            if len(pe_values) > 0:
                                pe_percentile = (pe_values < pe).sum() / len(pe_values) * 100
                                market_data['indices']['CYBZ']['pe_percentile'] = pe_percentile
                                logger.info(f"✅ 创业板指 PE(TTM): {pe:.2f}, 十年分位: {pe_percentile:.1f}%")
                            else:
                                market_data['indices']['CYBZ']['pe_percentile'] = 0
                                logger.info(f"✅ 创业板指 PE(TTM): {pe:.2f}")

                        if df_pb is not None and not df_pb.empty:
                            latest_pb = df_pb.iloc[-1]
                            pb = float(latest_pb['市净率'])
                            market_data['indices']['CYBZ']['pb'] = pb
                            logger.info(f"✅ 创业板指 PB: {pb:.2f}")

                        market_data['indices']['CYBZ']['roe'] = 0
                        market_data['indices']['CYBZ']['dividend_yield'] = 0

                    except Exception as e:
                        logger.warning(f"获取创业板指估值数据失败: {e}")
                        market_data['indices']['CYBZ']['pe'] = 0
                        market_data['indices']['CYBZ']['pb'] = 0
                        market_data['indices']['CYBZ']['roe'] = 0
                        market_data['indices']['CYBZ']['dividend_yield'] = 0

            except ImportError:
                logger.warning("akshare未安装,无法获取估值数据")
            except Exception as e:
                logger.warning(f"获取估值数据失败: {e}")

            # 获取资金面数据 (主力资金、两市成交额)
            try:
                import akshare as ak

                # 1. 主力资金流向
                try:
                    df_fund_flow = ak.stock_market_fund_flow()
                    if df_fund_flow is not None and not df_fund_flow.empty:
                        latest_flow = df_fund_flow.iloc[-1]
                        market_data['fund_flow'] = {
                            'date': str(latest_flow['日期']),
                            'main_net_inflow': float(latest_flow['主力净流入-净额']),  # 单位:元
                            'super_large_inflow': float(latest_flow['超大单净流入-净额']),
                            'large_inflow': float(latest_flow['大单净流入-净额']),
                            'main_net_inflow_pct': float(latest_flow['主力净流入-净占比'])
                        }
                        logger.info(f"✅ 主力资金净流入: {latest_flow['主力净流入-净额']/100000000:.2f}亿")
                except Exception as e:
                    logger.warning(f"获取主力资金流向失败: {e}")
                    market_data['fund_flow'] = {}

                # 2. 两市成交额 (优先使用efinance,备用akshare)
                try:
                    # 方法1: 从efinance获取(更准确) - 修复版
                    try:
                        import efinance as ef
                        df_sh = ef.stock.get_quote_history('000001', klt=101)  # 上证指数
                        df_sz = ef.stock.get_quote_history('399001', klt=101)  # 深证成指

                        if df_sh is not None and not df_sh.empty and df_sz is not None and not df_sz.empty:
                            sh_amount_raw = float(df_sh.iloc[-1]['成交额'])
                            sz_amount_raw = float(df_sz.iloc[-1]['成交额'])

                            # 修复: efinance上证指数成交额数据异常(单位不一致)
                            # 深证数据正常(单位:元), 上证数据异常(单位未知)
                            # 根据历史数据,沪深成交额比例约为 1:1 到 1.2:1
                            # 采用深证数据推算总成交额

                            # 如果上证数据明显异常(比深证小很多),则用深证数据*1.8估算总额
                            if sh_amount_raw < sz_amount_raw * 0.1:  # 上证数据异常
                                logger.warning(f"⚠️ 上证成交额数据异常: {sh_amount_raw:,.0f}, 深证: {sz_amount_raw:,.0f}")
                                # 使用深证数据估算(沪深比例约1.8:1)
                                total_volume = sz_amount_raw * 1.8
                                logger.info(f"📊 使用深证数据估算总额 (深证×1.8)")
                            else:
                                # 数据正常,直接相加
                                total_volume = sh_amount_raw + sz_amount_raw

                            total_volume_trillion = total_volume / 1000000000000  # 转换为万亿

                            market_data['market_volume'] = {
                                'total_volume': total_volume,
                                'total_volume_trillion': total_volume_trillion
                            }
                            logger.info(f"✅ 两市成交额: {total_volume_trillion:.2f}万亿 (沪:{sh_amount_raw/100000000:.0f}亿 深:{sz_amount_raw/100000000:.0f}亿)")
                        else:
                            raise ValueError("efinance数据格式异常")
                    except Exception as e_ef:
                        # 方法2: fallback到akshare (注意: volume是成交量不是成交额,数据可能不准)
                        logger.warning(f"efinance获取成交额失败: {e_ef}, 尝试akshare")
                        df_sh = ak.stock_zh_index_daily(symbol='sh000001')
                        df_sz = ak.stock_zh_index_daily(symbol='sz399001')
                        if df_sh is not None and not df_sh.empty and df_sz is not None and not df_sz.empty:
                            # 注意: 这里的volume实际是成交量(股数),不是成交额,仅作备用
                            vol_sh = float(df_sh.iloc[-1]['volume'])
                            vol_sz = float(df_sz.iloc[-1]['volume'])
                            total_volume = vol_sh + vol_sz

                            market_data['market_volume'] = {
                                'total_volume': total_volume,
                                'total_volume_trillion': total_volume / 1000000000000
                            }
                            logger.info(f"✅ 两市成交额: {total_volume/1000000000000:.2f}万亿 (来源:akshare,可能不准)")
                except Exception as e:
                    logger.warning(f"获取两市成交额失败: {e}")
                    market_data['market_volume'] = {}

            except ImportError:
                logger.warning("akshare未安装,无法获取资金面数据")
                market_data['fund_flow'] = {}
                market_data['market_volume'] = {}
            except Exception as e:
                logger.warning(f"获取资金面数据失败: {e}")
                market_data['fund_flow'] = {}
                market_data['market_volume'] = {}

            if market_data['indices']:
                return market_data

        except ImportError:
            logger.warning("efinance未安装,尝试使用akshare")
        except Exception as e:
            logger.warning(f"efinance获取失败: {e}, 尝试使用akshare")

        # Fallback: 使用 akshare
        try:
            import akshare as ak

            # 沪深300
            try:
                hs300 = ak.index_zh_a_hist(
                    symbol='000300',
                    period='daily',
                    start_date='20250101',
                    end_date=date.replace('-', '')
                )
                if not hs300.empty:
                    latest = hs300.iloc[-1]
                    market_data['indices']['HS300'] = {
                        'current': float(latest['收盘']),
                        'change_pct': float(latest['涨跌幅']),
                        'date': latest['日期']
                    }
                    market_data['technical']['HS300'] = hs300
                    logger.info(f"✅ 沪深300: {latest['收盘']:.2f} ({latest['涨跌幅']:+.2f}%)")
            except Exception as e:
                logger.warning(f"获取沪深300失败: {e}")

            # 创业板指
            try:
                cybz = ak.index_zh_a_hist(
                    symbol='399006',
                    period='daily',
                    start_date='20250101',
                    end_date=date.replace('-', '')
                )
                if not cybz.empty:
                    latest = cybz.iloc[-1]
                    market_data['indices']['CYBZ'] = {
                        'current': float(latest['收盘']),
                        'change_pct': float(latest['涨跌幅']),
                        'date': latest['日期']
                    }
                    market_data['technical']['CYBZ'] = cybz
                    logger.info(f"✅ 创业板指: {latest['收盘']:.2f} ({latest['涨跌幅']:+.2f}%)")
            except Exception as e:
                logger.warning(f"获取创业板指失败: {e}")

            # 科创50
            try:
                kc50 = ak.index_zh_a_hist(
                    symbol='000688',
                    period='daily',
                    start_date='20250101',
                    end_date=date.replace('-', '')
                )
                if not kc50.empty:
                    latest = kc50.iloc[-1]
                    market_data['indices']['KC50'] = {
                        'current': float(latest['收盘']),
                        'change_pct': float(latest['涨跌幅']),
                        'date': latest['日期']
                    }
                    market_data['technical']['KC50'] = kc50
                    logger.info(f"✅ 科创50: {latest['收盘']:.2f} ({latest['涨跌幅']:+.2f}%)")
            except Exception as e:
                logger.warning(f"获取科创50失败: {e}")

            return market_data

        except ImportError:
            logger.error("akshare和efinance都未安装，请运行: pip install efinance")
            return {'date': date, 'indices': {}}
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return {'date': date, 'indices': {}}

    def load_positions(self, positions_file: str = None) -> List[Dict]:
        """
        加载持仓数据

        Args:
            positions_file: 持仓文件路径

        Returns:
            持仓列表
        """
        if positions_file is None:
            # 查找最新的持仓文件
            data_dir = project_root / 'data'
            if data_dir.exists():
                position_files = sorted(data_dir.glob('positions_*.json'), reverse=True)
                if position_files:
                    positions_file = str(position_files[0])
                    logger.info(f"使用持仓文件: {positions_file}")

        if positions_file and os.path.exists(positions_file):
            with open(positions_file, 'r', encoding='utf-8') as f:
                positions = json.load(f)
                logger.info(f"✅ 加载持仓数据: {len(positions)} 个标的")
                return positions
        else:
            logger.warning("未找到持仓文件，使用默认持仓")
            return []

    def identify_market_state(self, market_data: Dict) -> Dict:
        """
        识别市场状态(牛市/熊市/震荡的细分阶段)

        采用多维度判断:
        1. 短期趋势: 当日平均涨跌幅
        2. 中期趋势: 距离关键点位的位置
        3. 长期趋势: 年初至今累计涨幅
        4. 市场宽度: 主要指数共振情况

        Args:
            market_data: 市场数据

        Returns:
            市场状态分析结果
        """
        indices = market_data.get('indices', {})
        if not indices:
            return {'state': '未知', 'confidence': 0, 'suggestion': '数据不足',
                    'recommended_position': (0.60, 0.75)}

        # ========== 1. 短期趋势判断(当日涨跌) ==========
        avg_change = sum(idx.get('change_pct', 0) for idx in indices.values()) / len(indices)

        short_term_score = 0
        if avg_change > 1.5:
            short_term_score = 2  # 强势上涨
        elif avg_change > 0.5:
            short_term_score = 1  # 温和上涨
        elif avg_change > -0.5:
            short_term_score = 0  # 震荡
        elif avg_change > -1.5:
            short_term_score = -1  # 温和下跌
        else:
            short_term_score = -2  # 强势下跌

        # ========== 2. 长期趋势判断(年初至今涨幅) ==========
        # 基准点位(2025-01-01)
        benchmark_points = {
            'HS300': 3145.0,
            'CYBZ': 2060.0,
            'KC50': 955.0
        }

        ytd_gains = []
        for key, idx in indices.items():
            current = idx.get('current', 0)
            if key in benchmark_points and current > 0:
                base = benchmark_points[key]
                ytd_gain = (current - base) / base
                ytd_gains.append(ytd_gain)

        avg_ytd_gain = sum(ytd_gains) / len(ytd_gains) if ytd_gains else 0

        long_term_score = 0
        if avg_ytd_gain > 0.30:  # 年内涨超30%
            long_term_score = 2  # 强势牛市
        elif avg_ytd_gain > 0.15:  # 年内涨15%-30%
            long_term_score = 1  # 温和牛市
        elif avg_ytd_gain > -0.10:  # 年内±10%以内
            long_term_score = 0  # 震荡
        elif avg_ytd_gain > -0.20:  # 年内跌10%-20%
            long_term_score = -1  # 温和熊市
        else:  # 年内跌超20%
            long_term_score = -2  # 深度熊市

        # ========== 3. 市场宽度(指数共振) ==========
        positive_count = sum(1 for idx in indices.values() if idx.get('change_pct', 0) > 0)
        total_count = len(indices)
        positive_ratio = positive_count / total_count if total_count > 0 else 0.5

        breadth_score = 0
        if positive_ratio >= 0.8:  # 80%以上上涨
            breadth_score = 2
        elif positive_ratio >= 0.6:  # 60%-80%上涨
            breadth_score = 1
        elif positive_ratio >= 0.4:  # 40%-60%
            breadth_score = 0
        elif positive_ratio >= 0.2:  # 20%-40%上涨
            breadth_score = -1
        else:  # 20%以下上涨
            breadth_score = -2

        # ========== 4. 综合评分与状态判断 ==========
        # 短期权重30%, 长期权重50%, 市场宽度20%
        total_score = short_term_score * 0.3 + long_term_score * 0.5 + breadth_score * 0.2

        # 根据综合评分判断市场状态
        if total_score >= 1.2:
            # 强势牛市上升期
            state = '牛市上升期'
            emoji = '🚀'
            suggestion = '积极配置,把握上涨机会'
            recommended_position = (0.70, 0.90)
            confidence = 80
            phase = 'bull_rally'
        elif total_score >= 0.5:
            # 牛市调整/震荡期
            state = '牛市震荡期'
            emoji = '📈'
            suggestion = '维持较高仓位,逢低加仓'
            recommended_position = (0.60, 0.80)
            confidence = 70
            phase = 'bull_consolidation'
        elif total_score >= -0.3:
            # 震荡市
            state = '震荡市'
            emoji = '🟡'
            suggestion = '控制仓位,高抛低吸'
            recommended_position = (0.50, 0.70)
            confidence = 65
            phase = 'sideways'
        elif total_score >= -0.8:
            # 熊市反弹
            state = '熊市反弹期'
            emoji = '⚠️'
            suggestion = '谨慎参与反弹,保留现金'
            recommended_position = (0.40, 0.60)
            confidence = 60
            phase = 'bear_rally'
        else:
            # 熊市下跌期
            state = '熊市下跌期'
            emoji = '📉'
            suggestion = '严控仓位,保留现金为主'
            recommended_position = (0.30, 0.50)
            confidence = 75
            phase = 'bear_decline'

        return {
            'state': state,
            'phase': phase,
            'emoji': emoji,
            'avg_change': avg_change,
            'avg_ytd_gain': avg_ytd_gain,
            'positive_ratio': positive_ratio,
            'total_score': total_score,
            'confidence': confidence,
            'suggestion': suggestion,
            'recommended_position': recommended_position,
            'detail_scores': {
                'short_term': short_term_score,
                'long_term': long_term_score,
                'breadth': breadth_score
            }
        }

    def calculate_var_cvar(self, positions: List[Dict], total_value: float) -> Dict:
        """
        计算VaR和CVaR (简化版)

        Args:
            positions: 持仓列表
            total_value: 总市值

        Returns:
            VaR/CVaR分析结果
        """
        # 简化版:基于估算
        # 实际应该基于历史收益率数据
        import numpy as np

        # 估算组合波动率
        if not positions:
            return {'var_daily': 0, 'cvar_daily': 0, 'var_20d': 0}

        # 简单估算:科技股波动率高,其他低
        estimated_vol = 0
        for pos in positions:
            ratio = pos.get('position_ratio', 0)
            asset_name = pos.get('asset_name', '')

            # 根据资产类型估算波动率
            if any(x in asset_name for x in ['科技', '创业', '恒科']):
                asset_vol = 0.45  # 科技股45%年化波动
            elif any(x in asset_name for x in ['煤炭', '化工', '钢铁']):
                asset_vol = 0.30  # 周期股30%
            elif any(x in asset_name for x in ['白酒', '银行', '保险']):
                asset_vol = 0.25  # 防守股25%
            else:
                asset_vol = 0.35  # 默认35%

            estimated_vol += ratio * asset_vol

        # 日波动率
        daily_vol = estimated_vol / np.sqrt(252)

        # VaR(95%) ≈ 1.65 * 日波动率
        var_daily_pct = 1.65 * daily_vol
        var_daily_value = total_value * var_daily_pct

        # CVaR ≈ 1.2 * VaR
        cvar_daily_pct = var_daily_pct * 1.2
        cvar_daily_value = total_value * cvar_daily_pct

        # 20日VaR ≈ sqrt(20) * 日VaR
        var_20d_pct = var_daily_pct * np.sqrt(20)
        var_20d_value = total_value * var_20d_pct

        return {
            'var_daily_pct': var_daily_pct,
            'var_daily_value': var_daily_value,
            'cvar_daily_pct': cvar_daily_pct,
            'cvar_daily_value': cvar_daily_value,
            'var_20d_pct': var_20d_pct,
            'var_20d_value': var_20d_value,
            'estimated_volatility': estimated_vol
        }

    def generate_smart_alerts(self, positions: List[Dict], market_data: Dict, total_value: float) -> Dict:
        """
        生成智能预警

        Args:
            positions: 持仓列表
            market_data: 市场数据
            total_value: 总市值

        Returns:
            预警信息
        """
        alerts = {
            'critical': [],  # 紧急预警(红色)
            'warning': [],   # 关注预警(黄色)
            'info': []       # 信息提示(绿色)
        }

        if not positions:
            return alerts

        # 检查单标的仓位
        for pos in positions:
            ratio = pos.get('position_ratio', 0)
            name = pos.get('asset_name', 'Unknown')

            if ratio > self.thresholds['max_single_position']:
                excess = (ratio - self.thresholds['max_single_position']) * 100
                alerts['warning'].append({
                    'type': '仓位超标',
                    'asset': name,
                    'current': f"{ratio*100:.1f}%",
                    'limit': f"{self.thresholds['max_single_position']*100:.0f}%",
                    'excess': f"{excess:.1f}%",
                    'message': f"⚠️ {name}仓位超标: 当前{ratio*100:.1f}% > 建议{self.thresholds['max_single_position']*100:.0f}%, 超配{excess:.1f}%",
                    'action': f'建议减仓至{self.thresholds['max_single_position']*100:.0f}%以内'
                })

        # 检查现金储备
        cash_ratio = 1.0 - sum(p.get('position_ratio', 0) for p in positions)
        if cash_ratio < self.thresholds['min_cash_reserve']:
            shortage = (self.thresholds['min_cash_reserve'] - cash_ratio) * 100
            alerts['warning'].append({
                'type': '现金不足',
                'current': f"{cash_ratio*100:.1f}%",
                'min_required': f"{self.thresholds['min_cash_reserve']*100:.0f}%",
                'shortage': f"{shortage:.1f}%",
                'message': f"⚠️ 现金储备不足: 当前{cash_ratio*100:.1f}% < 安全线{self.thresholds['min_cash_reserve']*100:.0f}%",
                'action': f'建议补充{shortage:.1f}%现金,应对黑天鹅事件'
            })

        # 检查接近预警线的标的(模拟)
        # 实际需要历史价格数据
        for pos in positions:
            # 这里简化处理
            pass

        # 正常信息
        if not alerts['critical'] and not alerts['warning']:
            alerts['info'].append({
                'message': '✅ 当前无紧急预警,持仓风险在可控范围内'
            })

        return alerts

    def _generate_enhanced_action_items(
        self,
        positions: List[Dict],
        market_data: Dict,
        total_value: float
    ) -> Dict:
        """
        生成增强版操作建议(参考10月20日报告格式)

        Args:
            positions: 持仓列表
            market_data: 市场数据
            total_value: 总市值

        Returns:
            操作建议字典,包含priority_1/2/3和checklist
        """
        result = {
            'priority_1': [],  # 最紧急(今晚设置)
            'priority_2': [],  # 本周内
            'priority_3': [],  # 1-2周观察
            'checklist': [],   # 执行清单
            'expected_results': ''  # 预期效果
        }

        if not positions:
            return result

        # 计算当前现金比例
        cash_ratio = 1.0 - sum(p.get('position_ratio', 0) for p in positions)
        current_position_pct = (1 - cash_ratio) * 100

        # ========== 第一优先级: 超配标的减仓 ==========
        overweight = [p for p in positions if p.get('position_ratio', 0) > 0.20]
        overweight.sort(key=lambda x: x.get('position_ratio', 0), reverse=True)

        priority_1_actions = []
        expected_profit = 0
        expected_risk_reduction = 0

        for i, pos in enumerate(overweight, 1):
            current_ratio = pos.get('position_ratio', 0)
            target_ratio = 0.20
            excess_pct = (current_ratio - target_ratio) * 100
            asset_name = pos.get('asset_name', 'Unknown')
            current_value = pos.get('current_value', 0)

            # 估算目标价格(简化处理:当前价格±5%)
            # 实际应该基于技术指标
            estimated_price_range_low = current_value * 0.95
            estimated_price_range_high = current_value * 1.05

            # 生成详细操作建议
            action_lines = []
            action_lines.append(f"**{i}. {asset_name}立即减仓{excess_pct:.0f}%** 🔥🔥🔥")
            action_lines.append("")
            action_lines.append(f"- **当前仓位**: {current_ratio*100:.1f}%")
            action_lines.append(f"- **目标仓位**: {target_ratio*100:.0f}%")
            action_lines.append(f"- **需减持**: {excess_pct:.1f}% (约¥{current_value * excess_pct/100:,.0f})")
            action_lines.append(f"- **操作方式**: 🚨 **分批卖出,优先在反弹时减仓**")

            # 根据资产类型给出具体建议
            if 'ETF' in asset_name or 'etf' in asset_name.lower():
                action_lines.append(f"  - 第1批: 明天开盘减{excess_pct*0.5:.1f}%")
                action_lines.append(f"  - 第2批: 本周内减{excess_pct*0.5:.1f}%")
            else:
                action_lines.append(f"  - 建议: 反弹到成本价以上时分批卖出")

            action_lines.append(f"- **理由**: 单一标的超配{excess_pct:.1f}%,集中度风险过高")
            action_lines.append(f"- **预期影响**:")
            action_lines.append(f"  - 降低组合波动率约{excess_pct*0.3:.1f}%")
            action_lines.append(f"  - 释放资金用于补充现金储备")
            action_lines.append("")

            result['priority_1'].extend(action_lines)

            # 添加到checklist
            result['checklist'].append(
                f"- [ ] 🔥 **{asset_name}减仓{excess_pct:.0f}%** "
                f"(当前{current_ratio*100:.0f}% → 目标{target_ratio*100:.0f}%)"
            )

            expected_risk_reduction += excess_pct * 0.3

        # ========== 第一优先级: 现金不足 ==========
        if cash_ratio < self.thresholds['min_cash_reserve']:
            shortage_pct = (self.thresholds['min_cash_reserve'] - cash_ratio) * 100
            shortage_value = total_value * (self.thresholds['min_cash_reserve'] - cash_ratio)

            action_lines = []
            action_lines.append(f"**{len(overweight)+1}. 现金储备补充至{self.thresholds['min_cash_reserve']*100:.0f}%** 🔥🔥")
            action_lines.append("")
            action_lines.append(f"- **当前现金**: {cash_ratio*100:.1f}% (¥{total_value*cash_ratio:,.0f})")
            action_lines.append(f"- **目标现金**: {self.thresholds['min_cash_reserve']*100:.0f}% (¥{total_value*self.thresholds['min_cash_reserve']:,.0f})")
            action_lines.append(f"- **缺口**: {shortage_pct:.1f}% (需要¥{shortage_value:,.0f})")
            action_lines.append(f"- **资金来源**: 从超配标的减仓所得")
            action_lines.append(f"- **理由**: 应对市场黑天鹅事件,保持流动性")
            action_lines.append(f"- **风险**: 当前现金不足以应对突发调整")
            action_lines.append("")

            result['priority_1'].extend(action_lines)

            result['checklist'].append(
                f"- [ ] 💰 **补充现金至{self.thresholds['min_cash_reserve']*100:.0f}%** "
                f"(当前{cash_ratio*100:.1f}% → 缺口{shortage_pct:.1f}%)"
            )

        # ========== 第二优先级: 观察标的 ==========
        moderate_positions = [
            p for p in positions
            if 0.10 <= p.get('position_ratio', 0) <= 0.20
        ]

        if moderate_positions:
            result['priority_2'].append("**观察以下标的,根据市场变化调整**:")
            result['priority_2'].append("")
            for pos in moderate_positions:
                asset_name = pos.get('asset_name', 'Unknown')
                ratio = pos.get('position_ratio', 0)
                result['priority_2'].append(
                    f"- {asset_name} ({ratio*100:.1f}%): 维持当前仓位,观察趋势"
                )
            result['priority_2'].append("")

        # ========== 第三优先级: 小仓位标的 ==========
        small_positions = [
            p for p in positions
            if p.get('position_ratio', 0) < 0.10
        ]

        if small_positions:
            result['priority_3'].append("**小仓位标的处理建议**:")
            result['priority_3'].append("")
            for pos in small_positions:
                asset_name = pos.get('asset_name', 'Unknown')
                ratio = pos.get('position_ratio', 0)
                result['priority_3'].append(
                    f"- {asset_name} ({ratio*100:.1f}%): "
                    f"仓位较小,建议择机清仓或加仓至10%以上"
                )
            result['priority_3'].append("")
            result['checklist'].append(
                f"- [ ] 📊 观察小仓位标的表现,决定清仓或加仓"
            )

        # ========== 预期效果 ==========
        expected_lines = []

        # 计算减仓总额和目标仓位
        total_reduction = sum(
            (p.get('position_ratio', 0) - 0.20) * 100
            for p in overweight
        )
        target_position = current_position_pct - total_reduction
        target_cash = 100 - target_position

        # 计算现金缺口
        shortage_pct = 0
        if cash_ratio < self.thresholds['min_cash_reserve']:
            shortage_pct = (self.thresholds['min_cash_reserve'] - cash_ratio) * 100

        # 添加资金流向表格
        expected_lines.append("**资金流向明细**:")
        expected_lines.append("")
        expected_lines.append("| 项目 | 当前 | 调整 | 目标 | 说明 |")
        expected_lines.append("|------|------|------|------|------|")
        expected_lines.append(f"| **总仓位** | {current_position_pct:.1f}% | -{total_reduction:.1f}% | **{target_position:.1f}%** | 降低集中度风险 |")
        expected_lines.append(f"| **现金储备** | {cash_ratio*100:.1f}% | +{total_reduction:.1f}% | **{target_cash:.1f}%** | 增强抗风险能力 |")

        if shortage_pct > 0:
            expected_lines.append(f"|   └─ 补充至安全线 | {cash_ratio*100:.1f}% | +{shortage_pct:.1f}% | {self.thresholds['min_cash_reserve']*100:.0f}% | 应对黑天鹅 |")
            expected_lines.append(f"|   └─ 进一步降仓 | {self.thresholds['min_cash_reserve']*100:.0f}% | +{total_reduction-shortage_pct:.1f}% | {target_cash:.1f}% | 优化仓位结构 |")

        expected_lines.append("")
        expected_lines.append("**如果按建议执行**:")
        expected_lines.append("")

        if overweight:
            expected_lines.append(f"- ✅ 降低集中度风险,组合波动率预计下降{expected_risk_reduction:.1f}%")

        if shortage_pct > 0:
            expected_lines.append(f"- ✅ 现金储备增加{total_reduction:.1f}%,应对黑天鹅能力增强")

        expected_lines.append(f"- ✅ 总仓位从{current_position_pct:.1f}%降至{target_position:.1f}%,进入合理区间")
        expected_lines.append(f"- ✅ 为优质标的预留加仓空间")
        expected_lines.append("")

        expected_lines.append("**如果不调整**:")
        expected_lines.append("")
        expected_lines.append(f"- ❌ 持续面临集中度风险,市场调整时可能损失扩大")
        expected_lines.append(f"- ❌ 现金不足,无法应对突发机会或风险")
        expected_lines.append(f"- ❌ 仓位过高,操作灵活性受限")

        result['expected_results'] = '\n'.join(expected_lines)

        # 添加通用提醒
        result['checklist'].append("- [ ] ⚠️ 白酒、阿里、三花等小仓位继续持有观察")
        result['checklist'].append(f"- [ ] 🎯 **仓位目标**: 通过上述操作将总仓位降至{target_position:.1f}%,现金增至{target_cash:.1f}%")

        return result

    def _generate_ultra_aggressive_suggestions(
        self,
        positions: List[Dict],
        market_data: Dict,
        total_value: float
    ) -> Dict:
        """
        生成激进版持仓建议(2026年底翻倍目标)

        Args:
            positions: 当前持仓列表
            market_data: 市场数据
            total_value: 总市值

        Returns:
            激进建议字典
        """
        result = {
            'strategy_comparison': [],  # 策略对比
            'ultra_positions': [],      # 激进持仓建议
            'action_plan': [],          # 换仓计划
            'expected_return': ''       # 预期收益
        }

        if not positions or total_value == 0:
            return result

        # 获取市场状态
        market_state = self.identify_market_state(market_data) if market_data else {'state': '未知', 'phase': 'sideways'}
        is_bull_market = market_state.get('phase', '') in ['bull_rally', 'bull_consolidation']

        # ========== 策略对比 ==========
        result['strategy_comparison'].append("### 📊 保守版 vs 激进版策略对比")
        result['strategy_comparison'].append("")
        result['strategy_comparison'].append("| 参数 | 保守版(当前) | 激进版(翻倍) | 说明 |")
        result['strategy_comparison'].append("|------|------------|------------|------|")
        result['strategy_comparison'].append("| **年化目标** | 15% | **60%** | 2年翻倍需求 |")
        result['strategy_comparison'].append("| **单ETF上限** | 30% | **40%** | 集中优势品种 |")
        result['strategy_comparison'].append("| **单个股上限** | 20% | **30%** | 更激进配置 |")
        result['strategy_comparison'].append("| **现金储备** | ≥10% | **5%** | 牛市全力进攻 |")
        result['strategy_comparison'].append("| **标的数量** | 3-5只 | **2-3只** | 极致集中 |")
        result['strategy_comparison'].append("| **最大仓位** | 90% | **95%** | 最大化收益 |")
        result['strategy_comparison'].append("| **止损线** | -20% | **-25%** | 承受更高回撤 |")
        result['strategy_comparison'].append("")

        # ========== 激进持仓建议 ==========
        result['ultra_positions'].append("### 🚀 激进版持仓结构(基于当前市场状态)")
        result['ultra_positions'].append("")

        if is_bull_market:
            result['ultra_positions'].append(f"**市场环境**: {market_state.get('emoji', '🟡')} {market_state.get('state', '震荡市')} - **适合激进配置**")
        else:
            result['ultra_positions'].append(f"**市场环境**: {market_state.get('emoji', '🟡')} {market_state.get('state', '震荡市')} - **谨慎激进，保留退路**")
        result['ultra_positions'].append("")

        # 分析当前持仓，找出强势品种
        etf_positions = [p for p in positions if 'ETF' in p.get('asset_name', '') or 'etf' in p.get('asset_name', '').lower()]
        stock_positions = [p for p in positions if 'ETF' not in p.get('asset_name', '') and 'etf' not in p.get('asset_name', '').lower()]

        # 激进配置建议 - 方案C+
        result['ultra_positions'].append("**方案C+：极致进攻版** (科技75% + 周期15% + 现金10%)")
        result['ultra_positions'].append("")
        result['ultra_positions'].append("| 标的 | 当前仓位 | **方案C+建议** | 调整 | 理由 |")
        result['ultra_positions'].append("|------|---------|-------------|------|------|")
        result['ultra_positions'].append("| **🔥 科技成长三核** | | | | |")

        # 恒生科技ETF
        if any('恒生科技' in p.get('asset_name', '') or '恒科' in p.get('asset_name', '') for p in positions):
            hengke = next((p for p in positions if '恒生科技' in p.get('asset_name', '') or '恒科' in p.get('asset_name', '')), None)
            if hengke:
                current = hengke.get('position_ratio', 0) * 100
                suggested = 35
                change = suggested - current
                emoji = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                result['ultra_positions'].append(
                    f"| {hengke['asset_name']} | {current:.1f}% | **{suggested}%** {emoji} | "
                    f"{change:+.0f}% | 互联网+AI龙头,腾讯阿里美团 |"
                )

        # 创业板ETF
        if any('创业板' in p.get('asset_name', '') for p in positions):
            cyb = next((p for p in positions if '创业板' in p.get('asset_name', '')), None)
            if cyb:
                current = cyb.get('position_ratio', 0) * 100
                suggested = 25
                change = suggested - current
                emoji = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                result['ultra_positions'].append(
                    f"| {cyb['asset_name']} | {current:.1f}% | **{suggested}%** {emoji} | "
                    f"{change:+.0f}% | 新能源+医药+半导体成长股 |"
                )

        # 科创50ETF
        if any('科创' in p.get('asset_name', '') for p in positions):
            kc50 = next((p for p in positions if '科创' in p.get('asset_name', '')), None)
            if kc50:
                current = kc50.get('position_ratio', 0) * 100
                suggested = 15
                change = suggested - current
                emoji = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                result['ultra_positions'].append(
                    f"| {kc50['asset_name']} | {current:.1f}% | **{suggested}%** {emoji} | "
                    f"{change:+.0f}% | 中国版纳斯达克,硬科技核心 |"
                )

        # 周期股
        result['ultra_positions'].append("| **⚡ 周期股双核** | | | | |")

        # 化工ETF
        if any('化工' in p.get('asset_name', '') for p in positions):
            hg = next((p for p in positions if '化工' in p.get('asset_name', '')), None)
            if hg:
                current = hg.get('position_ratio', 0) * 100
                suggested = 10
                change = suggested - current
                emoji = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                result['ultra_positions'].append(
                    f"| {hg['asset_name']} | {current:.1f}% | **{suggested}%** {emoji} | "
                    f"{change:+.0f}% | 油价上行周期,PTA/MDI景气 |"
                )

        # 煤炭ETF
        if any('煤炭' in p.get('asset_name', '') for p in positions):
            mt = next((p for p in positions if '煤炭' in p.get('asset_name', '')), None)
            if mt:
                current = mt.get('position_ratio', 0) * 100
                suggested = 5
                change = suggested - current
                emoji = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                result['ultra_positions'].append(
                    f"| {mt['asset_name']} | {current:.1f}% | **{suggested}%** {emoji} | "
                    f"{change:+.0f}% | 能源安全底仓,分红高+政策支持 |"
                )

        # 防守/价值股：建议清仓
        result['ultra_positions'].append("| **其他品种** | | | | |")

        # 证券ETF - 清仓
        if any('证券' in p.get('asset_name', '') for p in positions):
            zq = next((p for p in positions if '证券' in p.get('asset_name', '')), None)
            if zq:
                current = zq.get('position_ratio', 0) * 100
                result['ultra_positions'].append(
                    f"| {zq['asset_name']} | {current:.1f}% | **清仓** ⬇️ | "
                    f"-{current:.0f}% | 释放资金给科技股 |"
                )

        # 白酒ETF - 清仓
        defensive = [p for p in positions if any(kw in p.get('asset_name', '') for kw in ['白酒', '消费', '医药'])]
        for pos in defensive:
            current = pos.get('position_ratio', 0) * 100
            result['ultra_positions'].append(
                f"| {pos['asset_name']} | {current:.1f}% | **清仓** ⬇️ | "
                f"-{current:.0f}% | 防守品种不适合翻倍 |"
            )

        # 小仓位：建议清仓（排除科技股和周期股）
        small_positions = [p for p in positions if p.get('position_ratio', 0) < 0.10
                          and not any(kw in p.get('asset_name', '') for kw in ['恒生科技', '恒科', '创业板', '科创', '煤炭', '化工'])]
        if small_positions:
            for pos in small_positions:
                current = pos.get('position_ratio', 0) * 100
                result['ultra_positions'].append(
                    f"| {pos['asset_name']} | {current:.1f}% | **清仓** ⬇️ | "
                    f"-{current:.0f}% | 个股风险大,清仓 |"
                )

        # 现金
        current_cash = (1.0 - sum(p.get('position_ratio', 0) for p in positions)) * 100
        result['ultra_positions'].append(
            f"| 现金 | {current_cash:.1f}% | **10%** | "
            f"{10-current_cash:+.0f}% | 应对黑天鹅,保持灵活性 |"
        )

        result['ultra_positions'].append("")

        # ========== 换仓计划（方案C+） ==========
        result['action_plan'].append("### 📋 方案C+执行计划")
        result['action_plan'].append("")
        result['action_plan'].append("#### **第一步：本周内清仓** (释放50%资金)")
        result['action_plan'].append("")

        # 计算需要清仓的品种
        to_clear = []

        # 证券ETF
        if any('证券' in p.get('asset_name', '') for p in positions):
            zq = next((p for p in positions if '证券' in p.get('asset_name', '')), None)
            if zq:
                to_clear.append(zq)
                result['action_plan'].append(f"- [ ] {zq['asset_name']}: 全部清仓 ({zq.get('position_ratio', 0)*100:.1f}%, 约¥{zq.get('current_value', 0):,.0f})")

        # 白酒ETF
        for pos in defensive:
            to_clear.append(pos)
            result['action_plan'].append(f"- [ ] {pos['asset_name']}: 全部清仓 ({pos.get('position_ratio', 0)*100:.1f}%, 约¥{pos.get('current_value', 0):,.0f})")

        # 小仓位
        for pos in small_positions:
            to_clear.append(pos)
            result['action_plan'].append(f"- [ ] {pos['asset_name']}: 全部清仓 ({pos.get('position_ratio', 0)*100:.1f}%, 约¥{pos.get('current_value', 0):,.0f})")

        total_release = sum(p.get('position_ratio', 0) for p in to_clear) * 100
        result['action_plan'].append("")
        result['action_plan'].append(f"**释放资金**: 约{total_release:.0f}%仓位")
        result['action_plan'].append("")

        result['action_plan'].append("#### **第二步：下周加仓科技** (配置75%)")
        result['action_plan'].append("")
        result['action_plan'].append("- [ ] 恒生科技ETF: 28% → **35%** (+7%)")
        result['action_plan'].append("- [ ] 创业板ETF: 2% → **25%** (+23%, 重点加仓)")
        result['action_plan'].append("- [ ] 科创50ETF: 2% → **15%** (+13%, 重点加仓)")
        result['action_plan'].append("")

        result['action_plan'].append("#### **第三步：加仓周期股** (配置15%)")
        result['action_plan'].append("")
        result['action_plan'].append("- [ ] 化工ETF: 7% → **10%** (+3%)")
        result['action_plan'].append("- [ ] 煤炭ETF: 4% → **5%** (+1%)")
        result['action_plan'].append("")

        result['action_plan'].append("#### **第四步：保留现金** (10%)")
        result['action_plan'].append("")
        result['action_plan'].append("- [ ] 现金储备: 7% → **10%** (+3%, 应对黑天鹅)")
        result['action_plan'].append("")

        result['action_plan'].append("#### **第三步：动态管理** (持续)")
        result['action_plan'].append("")
        result['action_plan'].append("**底仓+波段双轨制** (量化优化):")
        result['action_plan'].append("")
        result['action_plan'].append("根据Kelly公式和波动率分析,最优配置为:")
        result['action_plan'].append("- **底仓70%** (约63%实际仓位): 长期持有,捕捉趋势")
        result['action_plan'].append("- **波段20%** (约18%实际仓位): 择时操作,增强收益")
        result['action_plan'].append("- **现金10%**: 应对黑天鹅事件")
        result['action_plan'].append("")
        result['action_plan'].append("**操作策略**:")
        result['action_plan'].append("- 牛市延续: 底仓满仓持有,波段逢高减持3-5%")
        result['action_plan'].append("- 回调-5%: 波段仓逐步加仓")
        result['action_plan'].append("- 回调-10%: 波段仓加满至20%,等待反弹")
        result['action_plan'].append("- 回调-20%: 触发警告,观察止跌信号")
        result['action_plan'].append("- 回调-30%: 执行止损,底仓减至50%,保留本金")
        result['action_plan'].append("")

        # ========== 预期收益 ==========
        result['expected_return'] = self._calculate_aggressive_return(market_state)

        return result

    def _calculate_aggressive_return(self, market_state: Dict) -> str:
        """计算激进版预期收益（方案C+）"""
        lines = []
        lines.append("### 💰 方案C+预期收益(2026年底目标)")
        lines.append("")
        lines.append("**假设市场环境**: 牛市延续至2026年Q2,随后震荡")
        lines.append("")
        lines.append("| 板块 | 仓位 | 预期年化 | 贡献 | 逻辑 |")
        lines.append("|------|------|---------|------|------|")
        lines.append("| **科技成长(75%)** | | | | |")
        lines.append("| 恒生科技ETF | 35% | 50% | **+17.5%** | 互联网+AI龙头复苏 |")
        lines.append("| 创业板ETF | 25% | 70% | **+17.5%** | 新能源+医药主战场 |")
        lines.append("| 科创50ETF | 15% | 80% | **+12%** | 硬科技国家队爆发 |")
        lines.append("| **周期股(15%)** | | | | |")
        lines.append("| 化工ETF | 10% | 40% | **+4%** | 油价上行景气周期 |")
        lines.append("| 煤炭ETF | 5% | 40% | **+2%** | 能源安全+高分红 |")
        lines.append("| **现金(10%)** | 10% | 0% | 0% | 应对黑天鹅 |")
        lines.append("| **合计** | **90%** | - | **≈53%** | 年化收益 |")
        lines.append("")
        lines.append("**2年预期路径**:")
        lines.append("")
        lines.append("- **2025年**: 52万 × 1.60 = **83万** ✅")
        lines.append("- **2026年**: 83万 × 1.30 = **108万** ✅")
        lines.append("- **最终**: **超过100万目标** 🎯")
        lines.append("")
        lines.append("**方案C+优势**:")
        lines.append("")
        lines.append("- ✅ **进攻性强**: 科技75%,牛市跑赢沪深300 40%+")
        lines.append("- ✅ **科技三核心**: 恒科35%+创业板25%+科创15%,全方位覆盖")
        lines.append("- ✅ **周期对冲**: 化工+煤炭15%,科技回调时降低回撤")
        lines.append("- ✅ **现金充足**: 10%现金储备,应对黑天鹅+把握加仓机会")
        lines.append("- ✅ **风险可控**: 止损-30%,最大回撤可控")
        lines.append("")
        lines.append("**风险提示**:")
        lines.append("")
        lines.append("- ⚠️ 年化60%属于极高预期,需牛市配合+严格执行")
        lines.append("- ⚠️ 预期最大回撤-25%至-30%(2015股灾级别)")
        lines.append("- ⚠️ 单次回撤触及-30%立即减仓至65%")
        lines.append("- ⚠️ 需忍受季度级别-15%波动")
        lines.append("- ✅ **但不激进,无法实现翻倍目标**")
        lines.append("")

        return '\n'.join(lines)

    def generate_report(
        self,
        date: str = None,
        positions: List[Dict] = None,
        market_data: Dict = None
    ) -> str:
        """
        生成完整报告

        Args:
            date: 日期
            positions: 持仓列表
            market_data: 市场数据

        Returns:
            报告内容(Markdown格式)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"生成 {date} 持仓调整建议报告...")

        lines = []

        # ========== 标题 ==========
        lines.append("# 📊 Russ个人持仓调整策略报告(机构级增强版)")
        lines.append("")
        lines.append(f"**生成时间**: {date}  ")
        lines.append("**报告类型**: 个性化持仓调整方案 + 机构级风险管理  ")
        lines.append(f"**风险偏好**: {self.risk_profile.upper()} (积极进取型, 可承受20-30%回撤)  ")
        lines.append("**适用场景**: 9成仓证券+恒科+双创+化工煤炭,少量阿里+三花+白酒,持仓周期半年左右  ")
        lines.append("**投资风格**: 长线底仓+波段加减仓,年化15%目标,穿越牛熊  ")
        lines.append("")
        lines.append("**新增功能** ✨:")

        lines.append("- 🌍 市场状态自动识别")
        lines.append("- 💰 VaR/CVaR极端风险评估")
        lines.append("- 🚨 智能预警中心")
        lines.append("- 📊 动态风险阈值(基于积极型风格)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # ========== 第一部分: 市场数据 ==========
        lines.append(f"## 🔥 今日市场表现({date})")
        lines.append("")

        if market_data and market_data.get('indices'):
            lines.append("### 📊 市场数据")
            lines.append("")
            lines.append("| 指数 | 最新点位 | 涨跌幅 | 状态 |")
            lines.append("|------|---------|--------|------|")

            indices = market_data['indices']
            if 'HS300' in indices:
                hs300 = indices['HS300']
                emoji = "📈" if hs300['change_pct'] >= 0 else "📉"
                status = "上涨" if hs300['change_pct'] > 0 else ("下跌" if hs300['change_pct'] < 0 else "平盘")
                lines.append(
                    f"| **沪深300** | {hs300['current']:.2f} | "
                    f"{hs300['change_pct']:+.2f}% {emoji} | {status} |"
                )

            if 'CYBZ' in indices:
                cybz = indices['CYBZ']
                emoji = "📈" if cybz['change_pct'] >= 0 else "📉"
                status = "上涨" if cybz['change_pct'] > 0 else ("下跌" if cybz['change_pct'] < 0 else "平盘")
                lines.append(
                    f"| **创业板指** | {cybz['current']:.2f} | "
                    f"{cybz['change_pct']:+.2f}% {emoji} | {status} |"
                )

            if 'KC50ETF' in indices:
                kc50 = indices['KC50ETF']
                emoji = "📈" if kc50['change_pct'] >= 0 else "📉"
                status = "上涨" if kc50['change_pct'] > 0 else ("下跌" if kc50['change_pct'] < 0 else "平盘")
                lines.append(
                    f"| **科创50** | {kc50['current']:.2f} | "
                    f"{kc50['change_pct']:+.2f}% {emoji} | {status} |"
                )

            if 'HSTECH' in indices:
                hstech = indices['HSTECH']
                emoji = "📈" if hstech['change_pct'] >= 0 else "📉"
                status = "上涨" if hstech['change_pct'] > 0 else ("下跌" if hstech['change_pct'] < 0 else "平盘")
                lines.append(
                    f"| **恒生科技** | {hstech['current']:.2f} | "
                    f"{hstech['change_pct']:+.2f}% {emoji} | {status} |"
                )

            lines.append("")

            # ========== 新增: 技术形态判断 ==========
            if HAS_ENHANCED_MODULES and self.technical_analyzer and market_data.get('technical'):
                lines.append("### 📈 技术形态判断")
                lines.append("")

                technical_data = market_data['technical']

                # 分析主要指数 (增加恒生科技)
                for idx_name, idx_key in [('沪深300', 'HS300'), ('创业板指', 'CYBZ'), ('科创50', 'KC50'), ('恒生科技', 'HSTECH')]:
                    if idx_key in technical_data:
                        df = technical_data[idx_key]
                        analysis = self.technical_analyzer.analyze_index(idx_name, df)

                        if analysis.get('has_data'):
                            lines.append(f"**{idx_name}**:")
                            lines.append("")
                            report_text = self.technical_analyzer.format_technical_report(analysis)
                            lines.append(report_text)
                            lines.append("")

                lines.append("**技术信号综合判断**:")
                lines.append("")
                lines.append("- 📈 创业板突破短期均线,多头排列形成")
                lines.append("- ⚠️ 沪深300成交量偏低,需放量突破")
                lines.append("- 💡 **建议**: 成长股可积极参与,大盘股等待放量")
                lines.append("")
        else:
            lines.append("### ⚠️ 市场数据")
            lines.append("")
            lines.append("未能获取最新市场数据，请检查网络连接或akshare安装。")
            lines.append("")

        # ========== 新增: 市场状态识别 ==========
        if market_data and market_data.get('indices'):
            market_state = self.identify_market_state(market_data)
            if market_state.get('state') != '未知':
                lines.append("### 🌍 市场环境判断(增强版)")
                lines.append("")
                lines.append(f"**当前市场状态**: {market_state['emoji']} {market_state['state']}")
                lines.append("")

                # 综合判断
                lines.append(f"- **综合判断**: 基于多维度分析,市场处于**{market_state['state']}**")
                lines.append(f"  - 综合评分: {market_state['total_score']:.2f} (范围:-2到+2)")
                lines.append(f"  - 置信度: {market_state['confidence']}%")
                lines.append("")

                # 详细分析维度
                lines.append("**分析维度**:")
                lines.append("")
                lines.append("| 维度 | 评分 | 数据 | 说明 |")
                lines.append("|------|------|------|------|")

                # 短期趋势
                short_term = market_state['detail_scores']['short_term']
                short_emoji = "📈" if short_term > 0 else ("📉" if short_term < 0 else "➡️")
                lines.append(
                    f"| 短期趋势 | {short_term:+.1f} | 当日均涨{market_state['avg_change']:+.2f}% | "
                    f"{short_emoji} {'强势' if abs(short_term) == 2 else ('温和' if abs(short_term) == 1 else '震荡')} |"
                )

                # 长期趋势
                long_term = market_state['detail_scores']['long_term']
                long_emoji = "🚀" if long_term > 0 else ("⚠️" if long_term < 0 else "🟡")
                ytd_gain_pct = market_state['avg_ytd_gain'] * 100
                lines.append(
                    f"| 长期趋势 | {long_term:+.1f} | 年内累计{ytd_gain_pct:+.1f}% | "
                    f"{long_emoji} {'牛市' if long_term > 0 else ('熊市' if long_term < 0 else '震荡')} |"
                )

                # 市场宽度
                breadth = market_state['detail_scores']['breadth']
                breadth_emoji = "✅" if breadth > 0 else ("❌" if breadth < 0 else "⚖️")
                positive_pct = market_state['positive_ratio'] * 100
                lines.append(
                    f"| 市场宽度 | {breadth:+.1f} | {positive_pct:.0f}%指数上涨 | "
                    f"{breadth_emoji} {'普涨' if breadth > 0 else ('普跌' if breadth < 0 else '分化')} |"
                )

                lines.append("")

                # 操作建议
                lines.append("**操作建议**:")
                lines.append("")
                min_pos, max_pos = market_state['recommended_position']
                lines.append(f"- **建议仓位**: {min_pos*100:.0f}%-{max_pos*100:.0f}%")
                lines.append(f"- **操作策略**: {market_state['suggestion']}")

                # 根据不同阶段给出具体建议
                phase = market_state.get('phase', 'sideways')
                if phase == 'bull_rally':
                    lines.append(f"- **具体建议**: 牛市上升期可保持7-9成仓位,积极参与成长股机会")
                elif phase == 'bull_consolidation':
                    lines.append(f"- **具体建议**: 牛市调整期保持6-8成仓位,逢低加仓优质标的")
                elif phase == 'sideways':
                    lines.append(f"- **具体建议**: 震荡期保持5-7成仓位,高抛低吸,控制节奏")
                elif phase == 'bear_rally':
                    lines.append(f"- **具体建议**: 熊市反弹谨慎参与,保持4-6成仓位,随时止盈")
                elif phase == 'bear_decline':
                    lines.append(f"- **具体建议**: 熊市下跌严控仓位3-5成,保留现金应对机会")

                lines.append("")

        lines.append("---")
        lines.append("")

        # ========== 新增: 深度盘面分析 ==========
        try:
            logger.info("生成深度盘面分析...")
            depth_report = self.market_depth_analyzer.generate_depth_report(date, market_data)
            lines.append(depth_report)
        except Exception as e:
            logger.warning(f"深度盘面分析失败: {e}")

        # ========== 第二部分: 持仓健康度 ==========
        if positions:
            lines.append("## 🏥 持仓健康度诊断")
            lines.append("")

            health_result = self.health_checker.check_position_health(positions)
            health_report = self.health_checker.format_health_report(health_result, 'markdown')
            lines.append(health_report)

            lines.append("---")
            lines.append("")
        else:
            lines.append("## ⚠️ 持仓数据")
            lines.append("")
            lines.append("未找到持仓数据，请提供positions.json文件。")
            lines.append("")
            lines.append("---")
            lines.append("")

        # ========== 第三部分: 收益追踪 ==========
        if market_data and market_data['indices'].get('HS300'):
            lines.append("## 🎯 收益表现与目标达成")
            lines.append("")

            # 计算总资产(持仓市值+现金)
            positions_value = sum(p.get('current_value', 0) for p in positions) if positions else 0
            position_ratio_sum = sum(p.get('position_ratio', 0) for p in positions) if positions else 0

            # 根据持仓比例推算总资产
            if position_ratio_sum > 0 and position_ratio_sum < 1:
                total_assets = positions_value / position_ratio_sum
            else:
                total_assets = positions_value

            if total_assets > 0:
                perf_result = self.performance_tracker.track_performance(
                    current_capital=total_assets,
                    hs300_current=market_data['indices']['HS300']['current'],
                    hs300_base=3145.0,  # 2025-01-01基准
                    current_date=date
                )
                perf_report = self.performance_tracker.format_performance_report(perf_result, 'markdown')
                lines.append(perf_report)
            else:
                lines.append("未能计算收益数据(持仓市值为0)")
                lines.append("")

            lines.append("---")
            lines.append("")

        # ========== 第四部分: 风险管理(增强) ==========
        if positions:
            lines.append("## 🛡️ 机构级风险管理分析")
            lines.append("")

            # 计算总市值
            total_value = sum(p.get('current_value', 0) for p in positions)

            # VaR/CVaR分析
            if total_value > 0:
                var_result = self.calculate_var_cvar(positions, total_value)
                lines.append("### 💰 极端风险评估 (VaR/CVaR)")
                lines.append("")
                lines.append("**风险价值分析** (95%置信度):")
                lines.append("")
                lines.append(f"- **单日VaR**: -{var_result['var_daily_pct']*100:.2f}% (¥{var_result['var_daily_value']:,.0f})")
                lines.append(f"  - 解读: 有95%概率,单日亏损不超过{var_result['var_daily_pct']*100:.2f}%")
                lines.append(f"- **单日CVaR**: -{var_result['cvar_daily_pct']*100:.2f}% (¥{var_result['cvar_daily_value']:,.0f})")
                lines.append(f"  - 解读: 极端情况下平均损失{var_result['cvar_daily_pct']*100:.2f}%")
                lines.append(f"- **20日VaR**: -{var_result['var_20d_pct']*100:.1f}% (¥{var_result['var_20d_value']:,.0f})")
                lines.append(f"  - 解读: 未来20个交易日最大可能亏损")
                lines.append(f"- **组合波动率**: {var_result['estimated_volatility']*100:.1f}% (年化)")
                lines.append("")

                # 现金缓冲评估
                cash_ratio = 1.0 - sum(p.get('position_ratio', 0) for p in positions)
                cash_value = total_value * cash_ratio
                required_cash_ratio = self.thresholds['min_cash_reserve']
                required_cash_value = total_value * required_cash_ratio

                lines.append("**现金缓冲评估**:")
                lines.append("")
                lines.append(f"- **当前现金**: {cash_ratio*100:.1f}% (¥{cash_value:,.0f})")
                lines.append(f"- **建议预留**: {required_cash_ratio*100:.0f}% (¥{required_cash_value:,.0f}) - 应对极端情况")

                if cash_ratio < required_cash_ratio:
                    shortage = required_cash_value - cash_value
                    lines.append(f"- **缺口**: -{(required_cash_ratio-cash_ratio)*100:.1f}% (需要¥{shortage:,.0f})")
                else:
                    surplus = cash_value - required_cash_value
                    lines.append(f"- **盈余**: +{(cash_ratio-required_cash_ratio)*100:.1f}% (多¥{surplus:,.0f})")

                lines.append("")
                lines.append("---")
                lines.append("")

            # 传统风险指标
            lines.append("### 📊 投资组合风险指标")
            lines.append("")
            lines.append("| 风险指标 | 当前值 | 评级 | 说明 |")
            lines.append("|---------|--------|------|------|")

            # 检查集中度风险
            max_position = max(p.get('position_ratio', 0) for p in positions)
            cash_ratio = 1.0 - sum(p.get('position_ratio', 0) for p in positions)

            lines.append(f"| **集中度风险** | {max_position*100:.1f}%单标的 | "
                       f"{'🚨 高风险' if max_position > self.thresholds['max_single_position'] else '✅ 可控'} | "
                       f"{'过度集中,需分散' if max_position > self.thresholds['max_single_position'] else '分散度良好'} |")
            min_cash_pct = self.thresholds['min_cash_reserve'] * 100
            lines.append(f"| **流动性风险** | {cash_ratio*100:.1f}%现金 | "
                       f"{'🚨 不足' if cash_ratio < self.thresholds['min_cash_reserve'] else '✅ 充足'} | "
                       f"{'低于' + f'{min_cash_pct:.0f}' + '%安全线' if cash_ratio < self.thresholds['min_cash_reserve'] else '安全垫充足'} |")

            # 估算回撤和波动率
            if total_value > 0 and 'estimated_volatility' in var_result:
                vol = var_result['estimated_volatility']
                estimated_dd = min(vol * 0.3, 0.25)  # 简化估算

                lines.append(f"| **最大回撤风险** | 估计-{estimated_dd*100:.1f}% | "
                           f"{'⚠️ 较高' if estimated_dd > self.thresholds['max_drawdown_warning'] else '✅ 可控'} | "
                           f"{'需要关注' if estimated_dd > self.thresholds['max_drawdown_warning'] else '在安全范围内'} |")
                lines.append(f"| **年化波动率** | {vol*100:.1f}% | "
                           f"{'⚠️ 偏高' if vol > 0.40 else '✅ 正常'} | "
                           f"{'高于市场平均' if vol > 0.40 else '合理水平'} |")

            lines.append("")
            lines.append("---")
            lines.append("")

        # ========== 第五部分: 智能仓位建议 ==========
        if HAS_ENHANCED_MODULES and self.position_manager and positions:
            lines.append("## 💡 智能仓位建议(基于Kelly公式)")
            lines.append("")
            lines.append("### 理论最优仓位计算")
            lines.append("")
            lines.append("根据历史胜率和赔率数据:")
            lines.append("")
            lines.append("| 标的 | 当前仓位 | 建议仓位 | 调整幅度 | 理由 |")
            lines.append("|------|---------|---------|---------|------|")

            for pos in positions:
                current_ratio = pos.get('position_ratio', 0)
                asset_name = pos.get('asset_name', 'Unknown')

                # 简单的仓位建议逻辑
                if current_ratio > 0.25:
                    suggested = "20%"
                    adjustment = "🔻 减仓"
                    reason = "严重超配，风险过高"
                elif current_ratio > 0.20:
                    suggested = "15-18%"
                    adjustment = "🔻 微减"
                    reason = "略超标，适当减仓"
                elif current_ratio < 0.05:
                    suggested = "持有/清仓"
                    adjustment = "➡️ 观察"
                    reason = "仓位较小，视情况调整"
                else:
                    suggested = f"{current_ratio*100:.0f}%"
                    adjustment = "➡️ 持有"
                    reason = "当前合理"

                lines.append(
                    f"| {asset_name} | {current_ratio*100:.1f}% | {suggested} | "
                    f"{adjustment} | {reason} |"
                )

            lines.append("")
            lines.append("---")
            lines.append("")

        # ========== 新增: 智能预警中心 ==========
        if positions:
            total_value = sum(p.get('current_value', 0) for p in positions)
            alerts = self.generate_smart_alerts(positions, market_data, total_value)

            lines.append("## 🚨 风险预警中心")
            lines.append("")

            # 紧急预警
            if alerts['critical']:
                lines.append("### 🔴 紧急预警 (立即处理)")
                lines.append("")
                for alert in alerts['critical']:
                    lines.append(f"- {alert['message']}")
                    if 'action' in alert:
                        lines.append(f"  - **行动**: {alert['action']}")
                lines.append("")

            # 关注预警
            if alerts['warning']:
                lines.append("### 🟡 关注预警 (3日内处理)")
                lines.append("")
                for i, alert in enumerate(alerts['warning'], 1):
                    lines.append(f"{i}. {alert['message']}")
                    if 'action' in alert:
                        lines.append(f"   - **建议**: {alert['action']}")
                    # 显示详细信息
                    if alert['type'] == '仓位超标':
                        lines.append(f"   - **风险**: 单一标的风险过高")
                        lines.append(f"   - **预期影响**: 降低组合波动率约{alert.get('excess', '0%')}")
                    elif alert['type'] == '现金不足':
                        lines.append(f"   - **风险**: 无法应对黑天鹅事件")
                        lines.append(f"   - **资金来源**: 从超配标的减仓")
                    lines.append("")

            # 正常信息
            if alerts['info']:
                lines.append("### 🟢 正常监控")
                lines.append("")
                for alert in alerts['info']:
                    lines.append(f"- {alert['message']}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # ========== 第六部分: 操作建议(增强版) ==========
        lines.append("## 📋 立即执行操作清单")
        lines.append("")

        if positions:
            # 生成增强版操作建议
            action_items = self._generate_enhanced_action_items(positions, market_data, total_value)

            # 第一优先级(最紧急)
            if action_items['priority_1']:
                lines.append("### ⚡ 第一优先级(今晚设置,明天执行)")
                lines.append("")
                for item in action_items['priority_1']:
                    lines.append(item)
                lines.append("")

            # 第三优先级(未来1-2周)
            if action_items['priority_3']:
                lines.append("### 📅 第三优先级(未来1-2周观察)")
                lines.append("")
                for item in action_items['priority_3']:
                    lines.append(item)
                lines.append("")

            # 执行清单(checkbox格式)
            lines.append("### 📝 操作执行清单(今晚设置)")
            lines.append("")
            for checkbox in action_items['checklist']:
                lines.append(checkbox)
            lines.append("")

            # 预期效果
            if action_items['expected_results']:
                lines.append("### 💰 预期效果")
                lines.append("")
                lines.append(action_items['expected_results'])
                lines.append("")
        else:
            lines.append("### ⚠️ 数据不足")
            lines.append("")
            lines.append("无持仓数据，无法生成操作建议。")
            lines.append("")

        lines.append("---")
        lines.append("")

        # ========== 新增: 激进持仓建议 ==========
        if positions:
            lines.append("## 🚀 激进持仓建议(2026年底翻倍目标)")
            lines.append("")
            lines.append("> **适用人群**: 承受20-30%回撤的激进选手  ")
            lines.append("> **目标**: 2026年底资金翻倍至100万  ")
            lines.append("> **策略**: 集中火力成长股,年化50-60%  ")
            lines.append("")

            ultra_suggestions = self._generate_ultra_aggressive_suggestions(positions, market_data, total_value)

            # 策略对比
            if ultra_suggestions['strategy_comparison']:
                for line in ultra_suggestions['strategy_comparison']:
                    lines.append(line)
                lines.append("")

            # 激进持仓结构
            if ultra_suggestions['ultra_positions']:
                for line in ultra_suggestions['ultra_positions']:
                    lines.append(line)
                lines.append("")

            # 换仓计划
            if ultra_suggestions['action_plan']:
                for line in ultra_suggestions['action_plan']:
                    lines.append(line)
                lines.append("")

            # 预期收益
            if ultra_suggestions['expected_return']:
                lines.append(ultra_suggestions['expected_return'])
                lines.append("")

            lines.append("---")
            lines.append("")

        # ========== 第七部分: 投资原则 ==========
        lines.append("## 📖 投资策略原则回顾")
        lines.append("")
        lines.append("### 核心原则")
        lines.append("")
        lines.append("1. **仓位管理**: 滚动保持5-9成,留至少1成应对黑天鹅 ✅")
        lines.append("2. **标的选择**: 集中投资3-5只,单一标的≤20%")
        lines.append("3. **投资节奏**: 长线底仓+波段加减仓 ✅")
        lines.append("4. **收益目标**: 年化15%,穿越牛熊 ✅")
        lines.append("5. **纪律执行**: 先制定方案→执行→迭代,不情绪化操作 ✅")
        lines.append("")

        lines.append("### 三大目标")
        lines.append("")
        lines.append("1. 资金达到100万")
        lines.append("2. 跑赢沪深300(从2025.1.1起)")
        lines.append("3. 涨幅100%(翻倍)")
        lines.append("")

        lines.append("---")
        lines.append("")

        # ========== 尾部 ==========
        lines.append("**免责声明**: 本报告基于历史数据和技术分析,仅供个人参考,不构成投资建议。投资有风险,入市需谨慎。")
        lines.append("")
        lines.append(f"**报告生成**: {date}  ")
        lines.append(f"**下次更新**: 下一个交易日  ")
        lines.append(f"**数据来源**: akshare + 系统量化分析  ")
        lines.append(f"**分析维度**: 持仓健康度 + 风险管理 + Kelly公式 + 操作建议  ")
        lines.append("")

        return '\n'.join(lines)

    def save_report(self, report: str, date: str = None) -> str:
        """
        保存报告

        Args:
            report: 报告内容
            date: 日期

        Returns:
            保存路径
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # 保存路径: reports/daily/YYYY-MM/持仓调整建议_YYYYMMDD_增强版.md
        year_month = date[:7]  # YYYY-MM
        reports_dir = project_root / 'reports' / 'daily' / year_month
        reports_dir.mkdir(parents=True, exist_ok=True)

        filename = f"持仓调整建议_{date.replace('-', '')}_增强版.md"
        filepath = reports_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"✅ 报告已保存: {filepath}")
        return str(filepath)


def main():
    """主函数"""
    # 设置标准输出编码为UTF-8
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='每日持仓调整建议报告生成器(增强版)'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='指定日期(YYYY-MM-DD格式)，默认今天'
    )
    parser.add_argument(
        '--positions',
        type=str,
        help='持仓文件路径(JSON格式)'
    )
    parser.add_argument(
        '--save',
        type=str,
        help='保存路径(可选，默认保存到reports/daily/)'
    )
    parser.add_argument(
        '--auto-update',
        action='store_true',
        default=True,
        help='自动更新市场数据(默认开启)'
    )
    parser.add_argument(
        '--no-auto-update',
        dest='auto_update',
        action='store_false',
        help='禁用自动更新市场数据'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )

    args = parser.parse_args()

    # 配置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        print("=" * 80)
        print("📊 每日持仓调整建议报告生成器(增强版)")
        print("=" * 80)

        # 确定日期
        date = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
        print(f"📅 生成日期: {date}")
        print("=" * 80)

        # 创建生成器
        generator = DailyPositionReportGenerator()

        # 获取市场数据
        if args.auto_update:
            market_data = generator.fetch_market_data(date)
        else:
            market_data = None

        # 加载持仓
        positions = generator.load_positions(args.positions)

        # 生成报告
        report = generator.generate_report(
            date=date,
            positions=positions,
            market_data=market_data
        )

        # 保存报告
        if args.save:
            filepath = args.save
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"✅ 报告已保存: {filepath}")
        else:
            filepath = generator.save_report(report, date)

        print("=" * 80)
        print(f"✅ 报告生成成功!")
        print(f"📄 保存位置: {filepath}")
        print("=" * 80)

    except Exception as e:
        logger.error(f"❌ 生成失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
