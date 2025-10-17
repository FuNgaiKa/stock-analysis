#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
均线偏离度监控预警系统

功能：
1. 监控指数价格偏离均线的程度
2. 当偏离超过预警阈值时发出警告
3. 统计历史偏离事件及后续表现
4. 支持A股和港股主要指数
"""

import pandas as pd
import numpy as np
import akshare as ak
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeviationAlert:
    """偏离度预警"""
    index_name: str
    index_code: str
    current_price: float
    ma_period: int
    ma_value: float
    deviation_pct: float
    alert_level: str  # '一级预警', '二级预警', '三级预警'
    direction: str  # '向上偏离', '向下偏离'
    date: str
    message: str


class MADeviationMonitor:
    """均线偏离度监控器"""

    # 支持的指数配置
    INDICES = {
        # A股主要指数
        'sh000001': {'name': '上证指数', 'type': 'a_stock'},
        'sh000300': {'name': '沪深300', 'type': 'a_stock'},
        'sz399006': {'name': '创业板指', 'type': 'a_stock'},
        'sh000688': {'name': '科创50', 'type': 'a_stock'},
        'sz399001': {'name': '深证成指', 'type': 'a_stock'},
        'sz399005': {'name': '中小板指', 'type': 'a_stock'},
        'sh000016': {'name': '上证50', 'type': 'a_stock'},
        'sh000905': {'name': '中证500', 'type': 'a_stock'},
        'sh000852': {'name': '中证1000', 'type': 'a_stock'},
        # 港股
        'hk_hstech': {'name': '恒生科技', 'type': 'hk_stock', 'symbol': 'HSTECH'},
        'hk_hsi': {'name': '恒生指数', 'type': 'hk_stock', 'symbol': 'HSI'},
    }

    # 预警阈值配置
    ALERT_THRESHOLDS = {
        'level_1': 20.0,  # 一级预警：偏离20%
        'level_2': 30.0,  # 二级预警：偏离30%
        'level_3': 40.0,  # 三级预警：偏离40%
    }

    # 监控的均线周期
    MA_PERIODS = [20, 60, 120]

    def __init__(self):
        self._cache = {}
        logger.info("均线偏离度监控器初始化完成")

    def get_index_data(self, index_code: str) -> pd.DataFrame:
        """获取指数历史数据"""
        if index_code in self._cache:
            return self._cache[index_code]

        try:
            config = self.INDICES.get(index_code)
            if not config:
                raise ValueError(f"不支持的指数: {index_code}")

            logger.info(f"获取 {config['name']} 历史数据...")

            if config['type'] == 'hk_stock':
                # 港股数据
                symbol = config['symbol']
                df = ak.stock_hk_index_daily_em(symbol=symbol)
                # 标准化列名
                if 'latest' in df.columns:
                    df = df.rename(columns={'latest': 'close'})
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date').sort_index()
            else:
                # A股数据
                df = ak.stock_zh_index_daily(symbol=index_code)
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date').sort_index()

            # 缓存
            self._cache[index_code] = df
            logger.info(f"{config['name']} 数据获取成功: {len(df)} 条")
            return df

        except Exception as e:
            logger.error(f"获取 {index_code} 数据失败: {str(e)}")
            return pd.DataFrame()

    def calculate_ma_deviation(
        self,
        index_code: str,
        ma_periods: List[int] = None
    ) -> Dict:
        """
        计算均线偏离度

        Args:
            index_code: 指数代码
            ma_periods: 均线周期列表

        Returns:
            偏离度数据字典
        """
        if ma_periods is None:
            ma_periods = self.MA_PERIODS

        df = self.get_index_data(index_code)
        if df.empty:
            return {}

        config = self.INDICES[index_code]
        current_price = df['close'].iloc[-1]
        current_date = df.index[-1]

        # 计算各周期均线
        result = {
            'index_name': config['name'],
            'index_code': index_code,
            'current_price': float(current_price),
            'date': current_date.strftime('%Y-%m-%d'),
            'deviations': {}
        }

        for period in ma_periods:
            ma = df['close'].rolling(period).mean()
            ma_value = ma.iloc[-1]

            if pd.isna(ma_value):
                continue

            # 计算偏离度
            deviation_pct = (current_price - ma_value) / ma_value * 100

            result['deviations'][f'ma{period}'] = {
                'ma_value': float(ma_value),
                'deviation_pct': float(deviation_pct),
                'direction': '向上偏离' if deviation_pct > 0 else '向下偏离',
                'abs_deviation': abs(float(deviation_pct))
            }

        return result

    def check_deviation_alerts(
        self,
        index_code: str,
        ma_periods: List[int] = None
    ) -> List[DeviationAlert]:
        """
        检查偏离度预警

        Args:
            index_code: 指数代码
            ma_periods: 均线周期列表

        Returns:
            预警列表
        """
        deviation_data = self.calculate_ma_deviation(index_code, ma_periods)
        if not deviation_data:
            return []

        alerts = []

        for ma_key, dev_info in deviation_data['deviations'].items():
            abs_dev = dev_info['abs_deviation']
            deviation_pct = dev_info['deviation_pct']
            ma_period = int(ma_key.replace('ma', ''))

            # 判断预警级别
            alert_level = None
            if abs_dev >= self.ALERT_THRESHOLDS['level_3']:
                alert_level = '🚨 三级预警'
            elif abs_dev >= self.ALERT_THRESHOLDS['level_2']:
                alert_level = '⚠️  二级预警'
            elif abs_dev >= self.ALERT_THRESHOLDS['level_1']:
                alert_level = '⚠️  一级预警'

            if alert_level:
                # 生成预警消息
                direction_desc = '大幅上涨' if deviation_pct > 0 else '大幅下跌'
                message = (
                    f"{deviation_data['index_name']} {direction_desc}！"
                    f"当前价格 {deviation_data['current_price']:.2f}，"
                    f"偏离{ma_period}日均线 {abs_dev:.1f}%"
                )

                alert = DeviationAlert(
                    index_name=deviation_data['index_name'],
                    index_code=index_code,
                    current_price=deviation_data['current_price'],
                    ma_period=ma_period,
                    ma_value=dev_info['ma_value'],
                    deviation_pct=deviation_pct,
                    alert_level=alert_level,
                    direction=dev_info['direction'],
                    date=deviation_data['date'],
                    message=message
                )

                alerts.append(alert)

        return alerts

    def monitor_all_indices(self) -> Dict[str, List[DeviationAlert]]:
        """
        监控所有指数

        Returns:
            {index_code: [alerts]}
        """
        logger.info("=" * 70)
        logger.info("开始监控所有指数的均线偏离度...")
        logger.info("=" * 70)

        all_alerts = {}

        for index_code in self.INDICES.keys():
            try:
                alerts = self.check_deviation_alerts(index_code)
                if alerts:
                    all_alerts[index_code] = alerts
            except Exception as e:
                logger.error(f"监控 {index_code} 失败: {str(e)}")
                continue

        return all_alerts

    def get_historical_deviation_events(
        self,
        index_code: str,
        ma_period: int = 60,
        threshold: float = 30.0,
        lookback_days: int = 1000
    ) -> pd.DataFrame:
        """
        获取历史偏离事件

        Args:
            index_code: 指数代码
            ma_period: 均线周期
            threshold: 偏离阈值
            lookback_days: 回溯天数

        Returns:
            历史偏离事件DataFrame
        """
        df = self.get_index_data(index_code)
        if df.empty:
            return pd.DataFrame()

        # 只取最近N天
        df = df.tail(lookback_days)

        # 计算均线和偏离度
        df['ma'] = df['close'].rolling(ma_period).mean()
        df['deviation_pct'] = (df['close'] - df['ma']) / df['ma'] * 100

        # 筛选偏离事件
        events = df[abs(df['deviation_pct']) >= threshold].copy()
        events['direction'] = events['deviation_pct'].apply(
            lambda x: '向上' if x > 0 else '向下'
        )

        logger.info(
            f"{self.INDICES[index_code]['name']} "
            f"近{lookback_days}天内偏离{ma_period}日均线超过{threshold}%的事件: "
            f"{len(events)} 次"
        )

        return events

    def analyze_post_deviation_performance(
        self,
        index_code: str,
        ma_period: int = 60,
        threshold: float = 30.0,
        forward_days: List[int] = [5, 10, 20, 60]
    ) -> Dict:
        """
        分析偏离事件后的表现

        Args:
            index_code: 指数代码
            ma_period: 均线周期
            threshold: 偏离阈值
            forward_days: 未来观察周期

        Returns:
            表现统计
        """
        df = self.get_index_data(index_code)
        if df.empty:
            return {}

        # 计算均线和偏离度
        df['ma'] = df['close'].rolling(ma_period).mean()
        df['deviation_pct'] = (df['close'] - df['ma']) / df['ma'] * 100

        # 筛选偏离事件
        upward_events = df[df['deviation_pct'] >= threshold].copy()
        downward_events = df[df['deviation_pct'] <= -threshold].copy()

        result = {
            'index_name': self.INDICES[index_code]['name'],
            'ma_period': ma_period,
            'threshold': threshold,
            'upward_events_count': len(upward_events),
            'downward_events_count': len(downward_events),
            'upward_performance': {},
            'downward_performance': {}
        }

        # 分析向上偏离后的表现
        for period in forward_days:
            returns = []
            for date in upward_events.index:
                future_data = df[df.index > date]
                if len(future_data) >= period:
                    future_price = future_data['close'].iloc[period-1]
                    current_price = df.loc[date, 'close']
                    ret = (future_price - current_price) / current_price * 100
                    returns.append(ret)

            if returns:
                result['upward_performance'][f'{period}d'] = {
                    'mean_return': np.mean(returns),
                    'median_return': np.median(returns),
                    'positive_ratio': sum(1 for r in returns if r > 0) / len(returns),
                    'sample_size': len(returns)
                }

        # 分析向下偏离后的表现
        for period in forward_days:
            returns = []
            for date in downward_events.index:
                future_data = df[df.index > date]
                if len(future_data) >= period:
                    future_price = future_data['close'].iloc[period-1]
                    current_price = df.loc[date, 'close']
                    ret = (future_price - current_price) / current_price * 100
                    returns.append(ret)

            if returns:
                result['downward_performance'][f'{period}d'] = {
                    'mean_return': np.mean(returns),
                    'median_return': np.median(returns),
                    'positive_ratio': sum(1 for r in returns if r > 0) / len(returns),
                    'sample_size': len(returns)
                }

        return result

    def generate_alert_report(self, all_alerts: Dict[str, List[DeviationAlert]]) -> str:
        """
        生成预警报告

        Args:
            all_alerts: 所有预警

        Returns:
            格式化的报告文本
        """
        if not all_alerts:
            return "✅ 所有指数均线偏离度正常，无预警信号。"

        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("🚨 均线偏离度预警报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 70)

        # 统计预警数量
        total_alerts = sum(len(alerts) for alerts in all_alerts.values())
        level_3_count = sum(
            1 for alerts in all_alerts.values()
            for alert in alerts if '三级' in alert.alert_level
        )
        level_2_count = sum(
            1 for alerts in all_alerts.values()
            for alert in alerts if '二级' in alert.alert_level and '三级' not in alert.alert_level
        )

        report_lines.append(f"\n📊 预警总览:")
        report_lines.append(f"  - 触发预警指数: {len(all_alerts)} 个")
        report_lines.append(f"  - 预警信号总数: {total_alerts} 个")
        report_lines.append(f"  - 三级预警(>40%): {level_3_count} 个")
        report_lines.append(f"  - 二级预警(>30%): {level_2_count} 个")

        # 详细预警
        report_lines.append(f"\n📋 详细预警信息:")
        for index_code, alerts in all_alerts.items():
            report_lines.append(f"\n【{alerts[0].index_name}】")
            for alert in alerts:
                report_lines.append(f"  {alert.alert_level} | {alert.message}")

        report_lines.append("\n" + "=" * 70)
        report_lines.append("💡 投资建议:")
        report_lines.append("  - 偏离30%以上属于极端情况，历史上往往伴随回调或反弹")
        report_lines.append("  - 向上大幅偏离：警惕短期获利回吐风险")
        report_lines.append("  - 向下大幅偏离：可能出现超跌反弹机会")
        report_lines.append("  - 建议结合估值、资金流向等多维度判断")
        report_lines.append("=" * 70)

        return "\n".join(report_lines)


def main():
    """主函数"""
    monitor = MADeviationMonitor()

    # 1. 监控所有指数
    all_alerts = monitor.monitor_all_indices()

    # 2. 生成并打印报告
    report = monitor.generate_alert_report(all_alerts)
    print(report)

    # 3. 如果有预警，分析历史表现
    if all_alerts:
        print("\n" + "=" * 70)
        print("📈 历史偏离事件分析")
        print("=" * 70)

        for index_code in list(all_alerts.keys())[:3]:  # 只分析前3个
            print(f"\n【{monitor.INDICES[index_code]['name']}】")

            # 获取历史偏离事件
            events = monitor.get_historical_deviation_events(
                index_code,
                ma_period=60,
                threshold=30.0,
                lookback_days=1000
            )

            if not events.empty:
                print(f"  近1000天内偏离60日均线>30%事件: {len(events)} 次")
                print(f"  最近一次: {events.index[-1].strftime('%Y-%m-%d')}")

            # 分析后续表现
            performance = monitor.analyze_post_deviation_performance(
                index_code,
                ma_period=60,
                threshold=30.0
            )

            if performance:
                print(f"\n  向上偏离后表现 (样本: {performance['upward_events_count']} 次):")
                for period, stats in performance['upward_performance'].items():
                    print(
                        f"    {period}: 平均{stats['mean_return']:+.2f}%, "
                        f"上涨概率{stats['positive_ratio']:.1%}"
                    )

                print(f"\n  向下偏离后表现 (样本: {performance['downward_events_count']} 次):")
                for period, stats in performance['downward_performance'].items():
                    print(
                        f"    {period}: 平均{stats['mean_return']:+.2f}%, "
                        f"上涨概率{stats['positive_ratio']:.1%}"
                    )


if __name__ == '__main__':
    main()
