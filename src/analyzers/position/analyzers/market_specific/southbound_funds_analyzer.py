"""
南向资金详细分析器
分析港股通南向资金流向、持仓、集中度等,追踪内资"聪明钱"
"""
import akshare as ak
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SouthboundFundsAnalyzer:
    """南向资金详细分析器"""

    def __init__(self):
        """初始化南向资金分析器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 5分钟缓存

    def get_southbound_flow(self, period: int = 60) -> Optional[pd.DataFrame]:
        """
        获取南向资金流向数据

        Args:
            period: 获取天数

        Returns:
            南向资金流向DataFrame
        """
        cache_key = f"southbound_flow_{period}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info("使用缓存的南向资金流向数据")
                return self.cache[cache_key]

        try:
            # 获取沪深港通资金流向历史
            # 注意: stock_hsgt_fund_flow_summary_em只返回当日数据
            # 这里简化处理,只使用当日数据
            df_summary = ak.stock_hsgt_fund_flow_summary_em()

            if df_summary.empty:
                logger.warning("获取南向资金流向数据为空")
                return None

            # 筛选南向资金(港股通-沪和港股通-深)
            df_south = df_summary[df_summary['方向'].str.contains('港股通')].copy()

            if df_south.empty:
                logger.warning("没有找到港股通数据")
                return None

            # 尝试获取历史流向数据(使用hist接口)
            try:
                df_hist = ak.stock_hsgt_hist_em(symbol="港股通(沪)")
                df_hist_sz = ak.stock_hsgt_hist_em(symbol="港股通(深)")

                # 合并沪深港股通
                df = pd.concat([df_hist, df_hist_sz])
                df = df.groupby('日期').agg({'当日成交净买额': 'sum'}).reset_index()

                # 重命名
                df.rename(columns={'日期': 'date', '当日成交净买额': 'daily_flow'}, inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df = df.sort_index()

                # 取最近period天
                df = df.tail(period)

            except Exception as e:
                logger.warning(f"获取历史数据失败: {e}, 使用当日汇总数据")
                # 降级方案: 只使用当日数据
                df = df_south[['当日成交净买额']].copy()
                df.rename(columns={'当日成交净买额': 'daily_flow'}, inplace=True)
                df['date'] = datetime.now()
                df.set_index('date', inplace=True)

            # 缓存
            self.cache[cache_key] = df
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"获取南向资金流向数据成功: {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"获取南向资金流向失败: {str(e)}")
            return None

    def get_southbound_holdings(self, top_n: int = 20) -> Optional[pd.DataFrame]:
        """
        获取南向资金持仓TOP股票

        Args:
            top_n: 返回前N只股票

        Returns:
            持仓明细DataFrame
        """
        cache_key = f"southbound_holdings_{top_n}"

        # 检查缓存
        if cache_key in self.cache:
            if (datetime.now() - self.cache_time[cache_key]).seconds < self.cache_duration:
                logger.info("使用缓存的南向资金持仓数据")
                return self.cache[cache_key]

        try:
            # 获取港股通持股明细
            df = ak.stock_hsgt_hold_stock_em(market="沪股通")
            df_sz = ak.stock_hsgt_hold_stock_em(market="深股通")

            if df.empty and df_sz.empty:
                logger.warning("获取南向资金持仓数据为空")
                return None

            # 合并
            df = pd.concat([df, df_sz], ignore_index=True)

            # 按持股市值排序
            df = df.sort_values('持股市值', ascending=False)

            # 取前N只
            df = df.head(top_n)

            # 缓存
            self.cache[cache_key] = df
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"获取南向资金持仓TOP{top_n}成功")
            return df

        except Exception as e:
            logger.error(f"获取南向资金持仓失败: {str(e)}")
            return None

    def analyze_southbound_funds(self, period: int = 60) -> Dict[str, Any]:
        """
        分析南向资金综合情况

        Args:
            period: 分析周期(天)

        Returns:
            南向资金分析结果
        """
        flow_df = self.get_southbound_flow(period)

        if flow_df is None or flow_df.empty:
            return {'error': '无法获取南向资金流向数据'}

        try:
            # 当日流向
            today_flow = float(flow_df['daily_flow'].iloc[-1])

            # 累计流向
            cumulative_flow = float(flow_df['daily_flow'].sum())

            # 历史统计
            avg_daily_flow = float(flow_df['daily_flow'].mean())
            median_daily_flow = float(flow_df['daily_flow'].median())
            max_inflow = float(flow_df['daily_flow'].max())
            max_outflow = float(flow_df['daily_flow'].min())

            # 净流入天数统计
            inflow_days = int((flow_df['daily_flow'] > 0).sum())
            outflow_days = int((flow_df['daily_flow'] < 0).sum())
            inflow_ratio = inflow_days / len(flow_df) if len(flow_df) > 0 else 0

            # 流向趋势
            recent_5d_flow = float(flow_df['daily_flow'].tail(5).sum())
            recent_20d_flow = float(flow_df['daily_flow'].tail(20).sum())

            flow_trend = self._classify_trend(recent_5d_flow, recent_20d_flow)

            # 流向强度分级
            flow_strength = self._classify_strength(today_flow, avg_daily_flow)

            # 连续流入/流出天数
            consecutive_inflow = self._count_consecutive(flow_df['daily_flow'] > 0)
            consecutive_outflow = self._count_consecutive(flow_df['daily_flow'] < 0)

            # 持仓分析
            holdings_analysis = self._analyze_holdings()

            result = {
                'today_flow': today_flow,
                'today_flow_billion': f"{today_flow / 100000000:.2f}亿",
                'cumulative_flow': cumulative_flow,
                'cumulative_flow_billion': f"{cumulative_flow / 100000000:.2f}亿",
                'avg_daily_flow': avg_daily_flow,
                'median_daily_flow': median_daily_flow,
                'max_inflow': max_inflow,
                'max_outflow': max_outflow,
                'inflow_days': inflow_days,
                'outflow_days': outflow_days,
                'inflow_ratio': inflow_ratio,
                'recent_5d_flow': recent_5d_flow,
                'recent_20d_flow': recent_20d_flow,
                'flow_trend': flow_trend,
                'flow_strength': flow_strength,
                'consecutive_inflow_days': consecutive_inflow,
                'consecutive_outflow_days': consecutive_outflow,
                'holdings_analysis': holdings_analysis,
                'signal': self._generate_signal(
                    today_flow, flow_trend, flow_strength,
                    consecutive_inflow, consecutive_outflow
                ),
                'interpretation': self._generate_interpretation(
                    today_flow, cumulative_flow, flow_trend,
                    inflow_ratio, consecutive_inflow, consecutive_outflow
                )
            }

            return result

        except Exception as e:
            logger.error(f"分析南向资金失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_holdings(self) -> Dict[str, Any]:
        """
        分析持仓情况

        Returns:
            持仓分析结果
        """
        holdings_df = self.get_southbound_holdings(top_n=20)

        if holdings_df is None or holdings_df.empty:
            return {'error': '无法获取持仓数据'}

        try:
            # TOP持仓股票
            top_holdings = []
            for i in range(min(5, len(holdings_df))):
                row = holdings_df.iloc[i]
                top_holdings.append({
                    'name': row['股票名称'],
                    'code': row['股票代码'],
                    'holding_value': f"{row['持股市值']:.2f}亿",
                    'holding_pct': f"{row['持股占比']:.2f}%" if '持股占比' in row else 'N/A'
                })

            # 持仓集中度(TOP10持股市值占比)
            total_holding = holdings_df['持股市值'].sum()
            top10_holding = holdings_df.head(10)['持股市值'].sum()
            concentration = float(top10_holding / total_holding) if total_holding > 0 else 0

            return {
                'top_holdings': top_holdings,
                'total_holding_value': f"{total_holding:.2f}亿",
                'concentration_top10': f"{concentration:.1%}",
                'holding_stock_count': len(holdings_df)
            }

        except Exception as e:
            logger.error(f"分析持仓失败: {str(e)}")
            return {'error': str(e)}

    def _classify_trend(self, recent_5d: float, recent_20d: float) -> str:
        """
        分类流向趋势

        Returns:
            趋势描述
        """
        if recent_5d > 0 and recent_20d > 0:
            if recent_5d > recent_20d * 0.5:  # 5日流入占20日流入50%以上
                return '强劲流入'
            else:
                return '温和流入'
        elif recent_5d < 0 and recent_20d < 0:
            if abs(recent_5d) > abs(recent_20d) * 0.5:
                return '强劲流出'
            else:
                return '温和流出'
        elif recent_5d > 0 and recent_20d < 0:
            return '转向流入'
        elif recent_5d < 0 and recent_20d > 0:
            return '转向流出'
        else:
            return '震荡'

    def _classify_strength(self, today_flow: float, avg_flow: float) -> str:
        """
        分类流向强度

        Returns:
            强度描述
        """
        if today_flow > avg_flow * 2:
            return '超强流入'
        elif today_flow > avg_flow:
            return '强流入'
        elif today_flow < avg_flow * -2:
            return '超强流出'
        elif today_flow < 0:
            return '流出'
        else:
            return '中性'

    def _count_consecutive(self, condition: pd.Series) -> int:
        """
        计算连续满足条件的天数

        Returns:
            连续天数
        """
        if condition.iloc[-1]:
            consecutive = 1
            for i in range(len(condition) - 2, -1, -1):
                if condition.iloc[i]:
                    consecutive += 1
                else:
                    break
            return consecutive
        return 0

    def _generate_signal(
        self,
        today_flow: float,
        trend: str,
        strength: str,
        consecutive_inflow: int,
        consecutive_outflow: int
    ) -> str:
        """
        生成交易信号

        Returns:
            信号描述
        """
        # 强势看多
        if trend == '强劲流入' and consecutive_inflow >= 3:
            return '强势看多港股'

        # 持续看多
        if strength in ['超强流入', '强流入'] and consecutive_inflow >= 5:
            return '持续看多港股'

        # 转向看多
        if trend == '转向流入':
            return '开始看多港股'

        # 强势看空
        if trend == '强劲流出' and consecutive_outflow >= 3:
            return '看空港股'

        # 持续看空
        if strength in ['超强流出'] and consecutive_outflow >= 5:
            return '持续看空港股'

        # 转向看空
        if trend == '转向流出':
            return '开始看空港股'

        return '中性'

    def _generate_interpretation(
        self,
        today_flow: float,
        cumulative_flow: float,
        trend: str,
        inflow_ratio: float,
        consecutive_inflow: int,
        consecutive_outflow: int
    ) -> str:
        """
        生成解读文本

        Returns:
            解读文本
        """
        interpretation = []

        # 当日流向
        if today_flow > 50e8:  # 大于50亿
            interpretation.append(f"当日大幅净流入{today_flow/1e8:.1f}亿,内资看好港股")
        elif today_flow < -50e8:
            interpretation.append(f"当日大幅净流出{abs(today_flow)/1e8:.1f}亿,内资撤离港股")

        # 累计流向
        if cumulative_flow > 0:
            interpretation.append(
                f"近{60}日累计净流入{cumulative_flow/1e8:.1f}亿,整体看多"
            )

        # 趋势
        if trend in ['强劲流入', '温和流入']:
            interpretation.append(f"流向趋势{trend},内资持续南下配置港股")
        elif trend in ['强劲流出', '温和流出']:
            interpretation.append(f"流向趋势{trend},内资减少港股配置")

        # 连续形态
        if consecutive_inflow >= 5:
            interpretation.append(
                f"连续{consecutive_inflow}日净流入,内资信心坚定"
            )
        elif consecutive_outflow >= 5:
            interpretation.append(
                f"连续{consecutive_outflow}日净流出,内资情绪转弱"
            )

        # 胜率
        if inflow_ratio > 0.7:
            interpretation.append(f"近期流入频率{inflow_ratio:.0%},内资积极性高")
        elif inflow_ratio < 0.3:
            interpretation.append(f"近期流入频率仅{inflow_ratio:.0%},内资谨慎")

        return '; '.join(interpretation) if interpretation else '南向资金流向正常波动'


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    analyzer = SouthboundFundsAnalyzer()

    print("=" * 80)
    print("南向资金详细分析器测试")
    print("=" * 80)

    # 测试南向资金分析
    print("\n1. 南向资金流向分析:")
    print("-" * 80)
    result = analyzer.analyze_southbound_funds(period=60)

    if 'error' not in result:
        print(f"当日流向: {result['today_flow_billion']}")
        print(f"累计流向: {result['cumulative_flow_billion']}")
        print(f"流向趋势: {result['flow_trend']}")
        print(f"流向强度: {result['flow_strength']}")
        print(f"净流入天数: {result['inflow_days']}/{result['inflow_days']+result['outflow_days']}")
        print(f"交易信号: {result['signal']}")
        print(f"解读: {result['interpretation']}")

        # 持仓分析
        if 'holdings_analysis' in result and 'error' not in result['holdings_analysis']:
            holdings = result['holdings_analysis']
            print(f"\n持仓情况:")
            print(f"  总持仓市值: {holdings['total_holding_value']}")
            print(f"  TOP10集中度: {holdings['concentration_top10']}")
            print(f"  TOP5持仓:")
            for holding in holdings['top_holdings']:
                print(f"    {holding['name']} ({holding['code']}): {holding['holding_value']}")

    else:
        print(f"分析失败: {result['error']}")

    print("\n" + "=" * 80)
