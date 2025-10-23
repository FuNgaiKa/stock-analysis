#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场深度分析器
提供板块轮动、市场情绪、量价关系等深度盘面分析

功能:
1. 板块轮动分析 (领涨/领跌板块, 资金流向)
2. 市场情绪温度计 (涨跌停, 涨跌家数, 北向资金)
3. 量价关系深度分析 (量比, 主力资金)

Author: Claude Code
Created: 2025-10-24
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import akshare as ak
import efinance as ef

logger = logging.getLogger(__name__)


class MarketDepthAnalyzer:
    """市场深度分析器"""

    def __init__(self):
        """初始化分析器"""
        self.logger = logger

    def analyze_sector_rotation(self, date: str = None) -> Dict:
        """
        分析板块轮动

        Args:
            date: 日期 (YYYY-MM-DD), 默认今天

        Returns:
            板块轮动分析结果
        """
        result = {
            'top_gainers': [],      # 领涨板块
            'top_losers': [],       # 领跌板块
            'capital_flow': [],     # 资金流向
            'rotation_signal': '',  # 轮动信号
            'analysis': ''          # 综合分析
        }

        try:
            # 1. 获取板块行情数据
            self.logger.info("获取板块行情数据...")

            # 使用akshare获取申万一级行业数据
            try:
                df_sector = ak.stock_board_industry_name_em()
                df_sector_info = ak.stock_board_industry_cons_em(symbol="小金属")  # 示例,获取详细信息

                # 获取今日板块涨跌幅
                # 注意: 这里需要根据实际可用接口调整
                sectors_data = []

                # 使用东方财富的板块数据
                try:
                    # 获取概念板块
                    df_concept = ak.stock_board_concept_name_em()
                    if df_concept is not None and len(df_concept) > 0:
                        # 按涨跌幅排序
                        df_concept = df_concept.sort_values('涨跌幅', ascending=False)

                        # 领涨板块 (前5)
                        for idx, row in df_concept.head(5).iterrows():
                            result['top_gainers'].append({
                                'name': row['板块名称'],
                                'change_pct': float(row['涨跌幅']),
                                'leader': row.get('领涨股票', 'N/A')
                            })

                        # 领跌板块 (后5)
                        for idx, row in df_concept.tail(5).iterrows():
                            result['top_losers'].append({
                                'name': row['板块名称'],
                                'change_pct': float(row['涨跌幅']),
                                'leader': row.get('领涨股票', 'N/A')
                            })

                        self.logger.info(f"✅ 获取到 {len(df_concept)} 个概念板块数据")

                except Exception as e:
                    self.logger.warning(f"获取概念板块数据失败: {e}")

            except Exception as e:
                self.logger.warning(f"获取板块数据失败: {e}")

            # 2. 获取板块资金流向
            try:
                # 获取主力资金流向
                df_flow = ak.stock_sector_fund_flow_rank(indicator="今日")
                if df_flow is not None and len(df_flow) > 0:
                    for idx, row in df_flow.head(5).iterrows():
                        result['capital_flow'].append({
                            'sector': row['名称'],
                            'net_inflow': float(row['主力净流入-净额']) / 1e8,  # 转换为亿
                            'net_inflow_pct': float(row['主力净流入-净占比'])
                        })
                    self.logger.info(f"✅ 获取资金流向数据")
            except Exception as e:
                self.logger.warning(f"获取资金流向失败: {e}")

            # 3. 判断轮动信号
            result['rotation_signal'] = self._analyze_rotation_signal(result)

            # 4. 生成综合分析
            result['analysis'] = self._generate_rotation_analysis(result)

        except Exception as e:
            self.logger.error(f"板块轮动分析失败: {e}", exc_info=True)

        return result

    def _analyze_rotation_signal(self, data: Dict) -> str:
        """分析轮动信号"""
        try:
            if not data['top_gainers']:
                return "数据不足"

            # 检查领涨板块类型
            tech_sectors = ['半导体', '新能源', '互联网', '人工智能', '芯片', '软件']
            defensive_sectors = ['白酒', '银行', '保险', '地产', '公用事业']

            top_gainer = data['top_gainers'][0]['name'] if data['top_gainers'] else ''

            # 判断进攻/防守切换
            is_tech_leading = any(s in top_gainer for s in tech_sectors)

            if is_tech_leading:
                return "✅ 防守→进攻切换,科技股启动"
            else:
                return "⚠️ 市场风格轮动中,关注板块变化"

        except Exception as e:
            self.logger.warning(f"轮动信号分析失败: {e}")
            return "分析失败"

    def _generate_rotation_analysis(self, data: Dict) -> str:
        """生成板块轮动综合分析"""
        try:
            lines = []

            # 领涨分析
            if data['top_gainers']:
                top = data['top_gainers'][0]
                lines.append(f"今日领涨: {top['name']}(+{top['change_pct']:.1f}%)")

            # 资金流向
            if data['capital_flow']:
                top_flow = data['capital_flow'][0]
                lines.append(f"资金流向: {top_flow['sector']}净流入{top_flow['net_inflow']:.1f}亿")

            return ", ".join(lines) if lines else "数据获取中"

        except Exception as e:
            self.logger.warning(f"生成分析失败: {e}")
            return "分析失败"

    def analyze_market_sentiment(self, date: str = None) -> Dict:
        """
        分析市场情绪

        Args:
            date: 日期 (YYYY-MM-DD), 默认今天

        Returns:
            市场情绪分析结果
        """
        result = {
            'limit_up': 0,          # 涨停数
            'limit_down': 0,        # 跌停数
            'advance': 0,           # 上涨家数
            'decline': 0,           # 下跌家数
            'advance_decline_ratio': 0,  # 涨跌比
            'northbound_flow': 0,   # 北向资金净流入(亿)
            'northbound_trend': '', # 北向资金趋势
            'sentiment_score': 0,   # 情绪评分(0-100)
            'sentiment_level': '',  # 情绪等级
            'analysis': ''          # 综合分析
        }

        try:
            # 1. 获取涨跌停数据
            self.logger.info("获取涨跌停数据...")
            try:
                # 获取涨停股
                df_limit_up = ak.stock_zt_pool_em(date=datetime.now().strftime('%Y%m%d'))
                if df_limit_up is not None:
                    result['limit_up'] = len(df_limit_up)
                    self.logger.info(f"✅ 涨停: {result['limit_up']}只")

                # 获取跌停股
                df_limit_down = ak.stock_dt_pool_em(date=datetime.now().strftime('%Y%m%d'))
                if df_limit_down is not None:
                    result['limit_down'] = len(df_limit_down)
                    self.logger.info(f"✅ 跌停: {result['limit_down']}只")

            except Exception as e:
                self.logger.warning(f"获取涨跌停数据失败: {e}")

            # 2. 获取涨跌家数
            try:
                # 使用实时行情统计
                df_realtime = ak.stock_zh_a_spot_em()
                if df_realtime is not None:
                    result['advance'] = len(df_realtime[df_realtime['涨跌幅'] > 0])
                    result['decline'] = len(df_realtime[df_realtime['涨跌幅'] < 0])

                    if result['decline'] > 0:
                        result['advance_decline_ratio'] = result['advance'] / result['decline']

                    self.logger.info(f"✅ 上涨: {result['advance']}只, 下跌: {result['decline']}只")

            except Exception as e:
                self.logger.warning(f"获取涨跌家数失败: {e}")

            # 3. 获取北向资金
            try:
                df_northbound = ak.stock_hsgt_fund_flow_summary_em()
                if df_northbound is not None and len(df_northbound) > 0:
                    # 获取最新一天的数据
                    latest = df_northbound.iloc[0]
                    result['northbound_flow'] = float(latest['北向资金']) / 1e8  # 转换为亿

                    # 判断趋势(需要历史数据)
                    if len(df_northbound) >= 3:
                        recent_flows = [float(df_northbound.iloc[i]['北向资金']) for i in range(3)]
                        if all(f > 0 for f in recent_flows):
                            result['northbound_trend'] = '连续流入'
                        elif all(f < 0 for f in recent_flows):
                            result['northbound_trend'] = '连续流出'
                        else:
                            result['northbound_trend'] = '震荡'

                    self.logger.info(f"✅ 北向资金: {result['northbound_flow']:.1f}亿")

            except Exception as e:
                self.logger.warning(f"获取北向资金失败: {e}")

            # 4. 计算情绪评分
            result['sentiment_score'] = self._calculate_sentiment_score(result)
            result['sentiment_level'] = self._get_sentiment_level(result['sentiment_score'])

            # 5. 生成综合分析
            result['analysis'] = self._generate_sentiment_analysis(result)

        except Exception as e:
            self.logger.error(f"市场情绪分析失败: {e}", exc_info=True)

        return result

    def _calculate_sentiment_score(self, data: Dict) -> int:
        """
        计算市场情绪评分 (0-100)

        评分规则:
        - 涨跌比: 40分
        - 涨跌停比: 20分
        - 北向资金: 40分
        """
        score = 50  # 基础分

        try:
            # 1. 涨跌比贡献 (最多40分)
            if data['advance_decline_ratio'] > 0:
                ratio_score = min(data['advance_decline_ratio'] * 20, 40)
                score += ratio_score - 20  # 调整为相对分数

            # 2. 涨跌停比贡献 (最多20分)
            if data['limit_up'] > 0 or data['limit_down'] > 0:
                limit_ratio = data['limit_up'] / max(data['limit_down'], 1)
                limit_score = min(limit_ratio * 10, 20)
                score += limit_score - 10

            # 3. 北向资金贡献 (最多40分)
            if data['northbound_flow'] != 0:
                # 流入为正,流出为负
                nb_score = max(-20, min(20, data['northbound_flow'] / 10))
                score += nb_score

            # 限制在0-100范围
            score = max(0, min(100, score))

        except Exception as e:
            self.logger.warning(f"情绪评分计算失败: {e}")
            score = 50

        return int(score)

    def _get_sentiment_level(self, score: int) -> str:
        """获取情绪等级"""
        if score >= 80:
            return "极度乐观(谨防追高)"
        elif score >= 65:
            return "偏热(注意追高风险)"
        elif score >= 50:
            return "中性偏暖"
        elif score >= 35:
            return "偏冷"
        else:
            return "极度悲观(关注抄底机会)"

    def _generate_sentiment_analysis(self, data: Dict) -> str:
        """生成市场情绪综合分析"""
        try:
            lines = []

            # 涨跌比分析
            if data['advance_decline_ratio'] > 1.5:
                lines.append(f"涨跌比{data['advance_decline_ratio']:.1f}:1,市场偏多")
            elif data['advance_decline_ratio'] < 0.8:
                lines.append(f"涨跌比{data['advance_decline_ratio']:.1f}:1,市场偏空")

            # 北向资金分析
            if abs(data['northbound_flow']) > 50:
                direction = "流入" if data['northbound_flow'] > 0 else "流出"
                lines.append(f"北向资金大幅{direction}{abs(data['northbound_flow']):.0f}亿")

            return ", ".join(lines) if lines else "市场情绪中性"

        except Exception as e:
            self.logger.warning(f"生成分析失败: {e}")
            return "分析失败"

    def analyze_volume_price(self, date: str = None) -> Dict:
        """
        量价关系深度分析

        Args:
            date: 日期 (YYYY-MM-DD), 默认今天

        Returns:
            量价关系分析结果
        """
        result = {
            'hs300_volume': 0,          # 沪深300成交额(万亿)
            'hs300_volume_ratio': 0,    # 沪深300量比
            'cyb_volume': 0,            # 创业板成交额(亿)
            'cyb_volume_ratio': 0,      # 创业板量比
            'total_turnover': 0,        # 两市总成交额(万亿)
            'main_net_inflow': 0,       # 主力资金净流入(亿)
            'large_order_ratio': 0,     # 大单占比
            'conclusion': '',           # 结论
            'analysis': ''              # 综合分析
        }

        try:
            # 1. 获取两市成交额
            self.logger.info("获取成交额数据...")
            try:
                # 使用efinance获取实时数据
                df_market = ef.stock.get_realtime_quotes()
                if df_market is not None and len(df_market) > 0:
                    # 计算总成交额(单位:万亿)
                    total_amount = df_market['成交额'].sum() / 1e12
                    result['total_turnover'] = total_amount
                    self.logger.info(f"✅ 两市成交额: {total_amount:.2f}万亿")

            except Exception as e:
                self.logger.warning(f"获取成交额失败: {e}")

            # 2. 获取主力资金流向
            try:
                df_flow = ak.stock_individual_fund_flow_rank(indicator="今日")
                if df_flow is not None and len(df_flow) > 0:
                    # 计算主力资金净流入总额
                    result['main_net_inflow'] = df_flow['主力净流入-净额'].sum() / 1e8

                    # 计算大单占比
                    total_inflow = df_flow['主力净流入-净额'].sum()
                    large_order = df_flow['超大单净流入-净额'].sum()
                    if total_inflow != 0:
                        result['large_order_ratio'] = (large_order / total_inflow) * 100

                    self.logger.info(f"✅ 主力资金净流入: {result['main_net_inflow']:.1f}亿")

            except Exception as e:
                self.logger.warning(f"获取主力资金失败: {e}")

            # 3. 生成结论和分析
            result['conclusion'] = self._generate_volume_conclusion(result)
            result['analysis'] = self._generate_volume_analysis(result)

        except Exception as e:
            self.logger.error(f"量价关系分析失败: {e}", exc_info=True)

        return result

    def _generate_volume_conclusion(self, data: Dict) -> str:
        """生成量价关系结论"""
        try:
            if data['main_net_inflow'] > 100:
                return "放量上涨,资金面强力支持"
            elif data['main_net_inflow'] > 0:
                return "温和放量,资金面支持"
            elif data['main_net_inflow'] > -50:
                return "缩量震荡,观望情绪浓厚"
            else:
                return "放量下跌,谨慎观望"
        except:
            return "数据不足"

    def _generate_volume_analysis(self, data: Dict) -> str:
        """生成量价关系综合分析"""
        try:
            lines = []

            # 成交额分析
            if data['total_turnover'] > 2.0:
                lines.append(f"两市成交{data['total_turnover']:.2f}万亿(放量)")
            elif data['total_turnover'] > 1.5:
                lines.append(f"两市成交{data['total_turnover']:.2f}万亿(温和)")
            else:
                lines.append(f"两市成交{data['total_turnover']:.2f}万亿(缩量)")

            # 资金流向
            if abs(data['main_net_inflow']) > 50:
                direction = "净流入" if data['main_net_inflow'] > 0 else "净流出"
                lines.append(f"主力资金{direction}{abs(data['main_net_inflow']):.0f}亿")

            return ", ".join(lines) if lines else "数据获取中"

        except Exception as e:
            self.logger.warning(f"生成分析失败: {e}")
            return "分析失败"

    def generate_depth_report(self, date: str = None, market_data: Dict = None) -> str:
        """
        生成深度盘面分析报告

        Args:
            date: 日期
            market_data: 市场数据(包含成交额等信息)

        Returns:
            Markdown格式的分析报告
        """
        lines = []

        lines.append("## 📊 深度盘面分析")
        lines.append("")

        # 1. 板块轮动
        lines.append("### 🔥 板块轮动追踪")
        lines.append("")

        sector_data = self.analyze_sector_rotation(date)

        # 领涨板块
        if sector_data['top_gainers']:
            lines.append("**今日领涨板块**:")
            lines.append("")
            for sector in sector_data['top_gainers'][:5]:
                emoji = "🔥" if sector['change_pct'] > 3 else "📈"
                lines.append(f"- {emoji} **{sector['name']}**: +{sector['change_pct']:.2f}%")
            lines.append("")

        # 领跌板块
        if sector_data['top_losers']:
            lines.append("**今日领跌板块**:")
            lines.append("")
            for sector in sector_data['top_losers'][:5]:
                emoji = "💥" if sector['change_pct'] < -3 else "📉"
                lines.append(f"- {emoji} **{sector['name']}**: {sector['change_pct']:.2f}%")
            lines.append("")

        # 资金流向
        if sector_data['capital_flow']:
            lines.append("**主力资金流向**:")
            lines.append("")
            for flow in sector_data['capital_flow'][:3]:
                emoji = "💰" if flow['net_inflow'] > 0 else "💸"
                lines.append(f"- {emoji} {flow['sector']}: {flow['net_inflow']:+.1f}亿 ({flow['net_inflow_pct']:+.1f}%)")
            lines.append("")

        # 轮动信号
        if sector_data['rotation_signal']:
            lines.append(f"**轮动信号**: {sector_data['rotation_signal']}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # 2. 市场情绪
        lines.append("### 🌡️ 市场情绪温度计")
        lines.append("")

        sentiment_data = self.analyze_market_sentiment(date)

        lines.append("| 指标 | 数据 | 说明 |")
        lines.append("|------|------|------|")

        # 涨跌停
        lines.append(f"| 涨停/跌停 | {sentiment_data['limit_up']}只 / {sentiment_data['limit_down']}只 | "
                    f"{'🔥 情绪火热' if sentiment_data['limit_up'] > 50 else '➡️ 正常' if sentiment_data['limit_up'] > 20 else '❄️ 情绪冷淡'} |")

        # 涨跌家数
        if sentiment_data['advance'] > 0 or sentiment_data['decline'] > 0:
            lines.append(f"| 上涨/下跌 | {sentiment_data['advance']}只 / {sentiment_data['decline']}只 | "
                        f"涨跌比 {sentiment_data['advance_decline_ratio']:.1f}:1 |")

        # 北向资金
        if sentiment_data['northbound_flow'] != 0:
            direction = "净流入" if sentiment_data['northbound_flow'] > 0 else "净流出"
            emoji = "💰" if sentiment_data['northbound_flow'] > 0 else "💸"
            trend = f"({sentiment_data['northbound_trend']})" if sentiment_data['northbound_trend'] else ""
            lines.append(f"| 北向资金 | {emoji} {direction} ¥{abs(sentiment_data['northbound_flow']):.1f}亿 | {trend} |")

        # 情绪评分
        lines.append(f"| **情绪评分** | **{sentiment_data['sentiment_score']}分** | {sentiment_data['sentiment_level']} |")

        lines.append("")

        if sentiment_data['analysis']:
            lines.append(f"**综合判断**: {sentiment_data['analysis']}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # 3. 量价关系
        lines.append("### 📈 量价关系深度")
        lines.append("")

        volume_data = self.analyze_volume_price(date)

        # 如果market_data有成交额数据,优先使用
        if market_data:
            if 'market_volume' in market_data and 'total_volume_trillion' in market_data['market_volume']:
                turnover = market_data['market_volume']['total_volume_trillion']
                if turnover > 0:
                    self.logger.info(f"使用market_data中的成交额: {turnover:.2f}万亿")
                    volume_data['total_turnover'] = turnover

            # 如果有主力资金数据,也使用
            if 'fund_flow' in market_data and market_data['fund_flow'] and 'main_net_inflow' in market_data['fund_flow']:
                main_inflow_yuan = market_data['fund_flow']['main_net_inflow']
                main_inflow_yi = main_inflow_yuan / 100000000  # 转换为亿
                self.logger.info(f"使用market_data中的主力资金: {main_inflow_yi:.2f}亿")
                volume_data['main_net_inflow'] = main_inflow_yi

            # 重新生成分析和结论
            volume_data['conclusion'] = self._generate_volume_conclusion(volume_data)
            volume_data['analysis'] = self._generate_volume_analysis(volume_data)

        lines.append("| 指标 | 数据 | 分析 |")
        lines.append("|------|------|------|")

        # 两市成交额
        if volume_data['total_turnover'] > 0:
            volume_level = "🔥 放量" if volume_data['total_turnover'] > 2.0 else "➡️ 温和" if volume_data['total_turnover'] > 1.5 else "❄️ 缩量"
            lines.append(f"| 两市成交额 | {volume_data['total_turnover']:.2f}万亿 | {volume_level} |")

        # 主力资金
        if volume_data['main_net_inflow'] != 0:
            direction = "净流入" if volume_data['main_net_inflow'] > 0 else "净流出"
            emoji = "💰" if volume_data['main_net_inflow'] > 0 else "💸"
            lines.append(f"| 主力资金 | {emoji} {direction} ¥{abs(volume_data['main_net_inflow']):.1f}亿 | "
                        f"{'大单主导' if volume_data['large_order_ratio'] > 60 else '散户主导'} |")

        # 结论 (只有在有数据时才显示)
        if volume_data['total_turnover'] > 0 or volume_data['main_net_inflow'] != 0:
            lines.append(f"| **结论** | **{volume_data['conclusion']}** | - |")

        lines.append("")

        # 量价分析 (只有在有数据时才显示)
        if volume_data['analysis'] and (volume_data['total_turnover'] > 0 or volume_data['main_net_inflow'] != 0):
            lines.append(f"**量价分析**: {volume_data['analysis']}")
            lines.append("")
        elif volume_data['total_turnover'] == 0 and volume_data['main_net_inflow'] == 0:
            lines.append(f"**量价分析**: 数据获取失败,请稍后重试")
            lines.append("")

        lines.append("---")
        lines.append("")

        return '\n'.join(lines)


if __name__ == '__main__':
    # 测试
    logging.basicConfig(level=logging.INFO)

    analyzer = MarketDepthAnalyzer()
    report = analyzer.generate_depth_report()

    print(report)
