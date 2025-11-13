#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金流向深度分析器
Fund Flow Analyzer

分析主力资金净流入/流出、超大单/大单/中小单的资金流向
评估资金面强弱,生成操作建议

作者: Claude Code
日期: 2025-11-13
版本: v1.0
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class FundFlowAnalyzer:
    """
    资金流向深度分析器

    功能:
    1. 获取主力资金净流入/流出数据
    2. 分析超大单/大单/中小单的资金流向
    3. 计算资金面评分
    4. 生成资金流向操作建议
    """

    def __init__(self):
        """初始化资金流向分析器"""
        logger.info("资金流向深度分析器初始化完成")

    def get_individual_fund_flow(self, symbol: str, days: int = 20) -> Optional[pd.DataFrame]:
        """
        获取个股资金流向数据

        Args:
            symbol: 股票代码 (如: '600519')
            days: 获取最近N天数据

        Returns:
            资金流向DataFrame,失败返回None
        """
        try:
            logger.info(f"获取 {symbol} 的资金流向数据...")

            # 使用akshare获取个股资金流
            df = ak.stock_individual_fund_flow_rank(indicator="今日")

            if df is None or df.empty:
                logger.warning(f"{symbol} 资金流向数据为空")
                return None

            # 筛选该股票
            df_stock = df[df['代码'] == symbol]

            if df_stock.empty:
                logger.warning(f"未找到 {symbol} 的资金流向数据")
                return None

            return df_stock

        except Exception as e:
            logger.error(f"获取 {symbol} 资金流向数据失败: {str(e)}")
            return None

    def get_sector_fund_flow(self, sector_name: str, days: int = 20) -> Optional[pd.DataFrame]:
        """
        获取板块资金流向数据

        Args:
            sector_name: 板块名称
            days: 获取最近N天数据

        Returns:
            资金流向DataFrame,失败返回None
        """
        try:
            logger.info(f"获取 {sector_name} 板块的资金流向数据...")

            # 使用akshare获取板块资金流
            df = ak.stock_sector_fund_flow_rank(indicator="今日")

            if df is None or df.empty:
                logger.warning(f"{sector_name} 板块资金流向数据为空")
                return None

            # 筛选该板块
            df_sector = df[df['名称'].str.contains(sector_name, na=False)]

            if df_sector.empty:
                logger.warning(f"未找到 {sector_name} 的板块资金流向数据")
                return None

            return df_sector

        except Exception as e:
            logger.error(f"获取 {sector_name} 板块资金流向数据失败: {str(e)}")
            return None

    def analyze_fund_flow(
        self,
        main_net_inflow_5d: float,
        main_net_inflow_20d: float,
        super_large_inflow: float,
        large_inflow: float,
        medium_inflow: float,
        small_inflow: float
    ) -> Dict:
        """
        分析资金流向

        Args:
            main_net_inflow_5d: 5日主力资金净流入(亿元)
            main_net_inflow_20d: 20日主力资金净流入(亿元)
            super_large_inflow: 超大单净流入(亿元)
            large_inflow: 大单净流入(亿元)
            medium_inflow: 中单净流入(亿元)
            small_inflow: 小单净流入(亿元)

        Returns:
            资金流向分析结果
        """
        result = {
            'main_fund': {},
            'order_structure': {},
            'fund_score': 0,
            'signal': '',
            'description': ''
        }

        # 1. 主力资金分析
        main_trend = self._analyze_main_fund_trend(main_net_inflow_5d, main_net_inflow_20d)
        result['main_fund'] = {
            'net_inflow_5d': main_net_inflow_5d,
            'net_inflow_20d': main_net_inflow_20d,
            'trend': main_trend['trend'],
            'strength': main_trend['strength'],
            'description': main_trend['description']
        }

        # 2. 订单结构分析
        order_analysis = self._analyze_order_structure(
            super_large_inflow, large_inflow, medium_inflow, small_inflow
        )
        result['order_structure'] = order_analysis

        # 3. 计算资金面评分 (0-100)
        score = self._calculate_fund_score(
            main_net_inflow_5d, main_net_inflow_20d,
            super_large_inflow, large_inflow,
            medium_inflow, small_inflow
        )
        result['fund_score'] = score

        # 4. 生成操作信号
        signal_info = self._generate_fund_signal(score, main_trend, order_analysis)
        result['signal'] = signal_info['signal']
        result['description'] = signal_info['description']

        return result

    def _analyze_main_fund_trend(self, inflow_5d: float, inflow_20d: float) -> Dict:
        """
        分析主力资金趋势

        Args:
            inflow_5d: 5日净流入
            inflow_20d: 20日净流入

        Returns:
            主力资金趋势分析
        """
        # 判断趋势
        if inflow_5d > 0 and inflow_20d > 0:
            trend = "持续流入"
            if inflow_5d > inflow_20d / 4:  # 5日流入超过20日均值
                strength = "强势"
                description = "主力资金持续大量流入,资金面强势"
            else:
                strength = "温和"
                description = "主力资金持续流入,资金面向好"
        elif inflow_5d > 0 and inflow_20d < 0:
            trend = "短期流入"
            strength = "中性"
            description = "主力资金短期流入,但20日仍为流出状态"
        elif inflow_5d < 0 and inflow_20d > 0:
            trend = "短期流出"
            strength = "偏弱"
            description = "主力资金短期流出,警惕趋势转变"
        else:
            trend = "持续流出"
            if abs(inflow_5d) > abs(inflow_20d) / 4:
                strength = "弱势"
                description = "主力资金持续大量流出,资金面弱势"
            else:
                strength = "温和"
                description = "主力资金持续流出,资金面承压"

        return {
            'trend': trend,
            'strength': strength,
            'description': description
        }

    def _analyze_order_structure(
        self,
        super_large: float,
        large: float,
        medium: float,
        small: float
    ) -> Dict:
        """
        分析订单结构

        Args:
            super_large: 超大单净流入
            large: 大单净流入
            medium: 中单净流入
            small: 小单净流入

        Returns:
            订单结构分析
        """
        # 计算各类资金的占比
        total_abs = abs(super_large) + abs(large) + abs(medium) + abs(small)

        if total_abs == 0:
            return {
                'super_large': 0,
                'large': 0,
                'medium': 0,
                'small': 0,
                'main_behavior': '观望',
                'retail_behavior': '观望',
                'game_analysis': '市场观望,无明显博弈'
            }

        # 主力资金 = 超大单 + 大单
        main_inflow = super_large + large
        retail_inflow = medium + small

        # 判断主力行为
        if main_inflow > 0:
            if super_large > 0 and large > 0:
                main_behavior = "主力强势吸筹"
            elif super_large > 0:
                main_behavior = "机构大资金建仓"
            else:
                main_behavior = "主力小幅吸筹"
        elif main_inflow < 0:
            if super_large < 0 and large < 0:
                main_behavior = "主力全面出货"
            elif super_large < 0:
                main_behavior = "机构大资金撤离"
            else:
                main_behavior = "主力小幅减仓"
        else:
            main_behavior = "主力观望"

        # 判断散户行为
        if retail_inflow > 0:
            if abs(retail_inflow) > abs(main_inflow):
                retail_behavior = "散户追高(警惕)"
            else:
                retail_behavior = "散户跟进"
        elif retail_inflow < 0:
            if abs(retail_inflow) > abs(main_inflow):
                retail_behavior = "散户恐慌割肉"
            else:
                retail_behavior = "散户小幅减仓"
        else:
            retail_behavior = "散户观望"

        # 博弈分析
        if main_inflow > 0 and retail_inflow < 0:
            game_analysis = "✅ 主力吸筹+散户割肉,筹码从散户转向主力(积极信号)"
        elif main_inflow < 0 and retail_inflow > 0:
            game_analysis = "⚠️ 主力出货+散户接盘,筹码从主力转向散户(警惕信号)"
        elif main_inflow > 0 and retail_inflow > 0:
            game_analysis = "主力和散户共同买入,市场一致看多"
        elif main_inflow < 0 and retail_inflow < 0:
            game_analysis = "主力和散户共同卖出,市场一致看空"
        else:
            game_analysis = "资金博弈不明显"

        return {
            'super_large': super_large,
            'large': large,
            'medium': medium,
            'small': small,
            'main_inflow': main_inflow,
            'retail_inflow': retail_inflow,
            'main_behavior': main_behavior,
            'retail_behavior': retail_behavior,
            'game_analysis': game_analysis
        }

    def _calculate_fund_score(
        self,
        inflow_5d: float,
        inflow_20d: float,
        super_large: float,
        large: float,
        medium: float,
        small: float
    ) -> int:
        """
        计算资金面评分 (0-100)

        评分逻辑:
        - 主力5日流入: +30分
        - 主力20日流入: +20分
        - 超大单流入: +20分
        - 大单流入: +15分
        - 散户割肉(主力买入时): +15分

        Returns:
            资金面评分(0-100)
        """
        score = 50  # 基础分

        # 1. 主力5日流入得分 (±30分)
        if inflow_5d > 0:
            score += min(30, inflow_5d * 3)  # 流入1亿加3分,最多30分
        else:
            score += max(-30, inflow_5d * 3)  # 流出1亿减3分,最多-30分

        # 2. 主力20日流入得分 (±20分)
        avg_20d = inflow_20d / 20  # 日均流入
        if avg_20d > 0:
            score += min(20, avg_20d * 20)
        else:
            score += max(-20, avg_20d * 20)

        # 3. 超大单得分 (±20分)
        if super_large > 0:
            score += min(20, super_large * 4)
        else:
            score += max(-20, super_large * 4)

        # 4. 大单得分 (±15分)
        if large > 0:
            score += min(15, large * 3)
        else:
            score += max(-15, large * 3)

        # 5. 主力吸筹+散户割肉加分 (+15分)
        main_inflow = super_large + large
        retail_inflow = medium + small
        if main_inflow > 0 and retail_inflow < 0:
            score += 15
        elif main_inflow < 0 and retail_inflow > 0:
            score -= 15

        # 确保分数在0-100之间
        score = max(0, min(100, score))

        return int(score)

    def _generate_fund_signal(self, score: int, main_trend: Dict, order_analysis: Dict) -> Dict:
        """
        生成资金流向操作信号

        Args:
            score: 资金面评分
            main_trend: 主力资金趋势
            order_analysis: 订单结构分析

        Returns:
            操作信号和描述
        """
        # 根据评分生成信号
        if score >= 80:
            signal = "强烈买入"
            description = "资金面极强,主力大量流入,可积极配置"
        elif score >= 65:
            signal = "买入"
            description = "资金面向好,主力持续流入,可正常配置"
        elif score >= 50:
            signal = "中性偏多"
            description = "资金面尚可,可小仓位参与"
        elif score >= 35:
            signal = "观望"
            description = "资金面偏弱,建议观望为主"
        elif score >= 20:
            signal = "减仓"
            description = "资金面弱势,主力流出,建议减仓"
        else:
            signal = "清仓"
            description = "资金面极弱,主力大量流出,建议清仓规避"

        # 结合博弈分析调整
        game = order_analysis.get('game_analysis', '')
        if "主力吸筹+散户割肉" in game:
            description += ",主力吸筹散户割肉,积极信号"
        elif "主力出货+散户接盘" in game:
            description += ",主力出货散户接盘,警惕风险"

        return {
            'signal': signal,
            'description': description
        }


def test_fund_flow_analyzer():
    """测试资金流向分析器"""
    print("=" * 80)
    print("资金流向深度分析器测试")
    print("=" * 80)

    analyzer = FundFlowAnalyzer()

    # 模拟数据测试
    print("\n测试场景1: 主力持续流入 + 散户割肉")
    result1 = analyzer.analyze_fund_flow(
        main_net_inflow_5d=5.2,   # 5日主力净流入5.2亿
        main_net_inflow_20d=18.5,  # 20日主力净流入18.5亿
        super_large_inflow=3.5,    # 超大单流入3.5亿
        large_inflow=1.7,          # 大单流入1.7亿
        medium_inflow=-1.8,        # 中单流出1.8亿
        small_inflow=-3.2          # 小单流出3.2亿
    )

    print(f"主力资金: {result1['main_fund']['trend']} ({result1['main_fund']['strength']})")
    print(f"描述: {result1['main_fund']['description']}")
    print(f"\n订单结构:")
    print(f"  超大单: {result1['order_structure']['super_large']:+.2f}亿")
    print(f"  大单: {result1['order_structure']['large']:+.2f}亿")
    print(f"  中单: {result1['order_structure']['medium']:+.2f}亿")
    print(f"  小单: {result1['order_structure']['small']:+.2f}亿")
    print(f"  主力行为: {result1['order_structure']['main_behavior']}")
    print(f"  散户行为: {result1['order_structure']['retail_behavior']}")
    print(f"  博弈分析: {result1['order_structure']['game_analysis']}")
    print(f"\n资金面评分: {result1['fund_score']}/100")
    print(f"操作信号: {result1['signal']}")
    print(f"操作建议: {result1['description']}")

    print("\n" + "=" * 80)
    print("\n测试场景2: 主力流出 + 散户接盘")
    result2 = analyzer.analyze_fund_flow(
        main_net_inflow_5d=-3.5,   # 5日主力净流出3.5亿
        main_net_inflow_20d=-12.8, # 20日主力净流出12.8亿
        super_large_inflow=-2.8,   # 超大单流出2.8亿
        large_inflow=-0.7,         # 大单流出0.7亿
        medium_inflow=1.2,         # 中单流入1.2亿
        small_inflow=2.3           # 小单流入2.3亿
    )

    print(f"主力资金: {result2['main_fund']['trend']} ({result2['main_fund']['strength']})")
    print(f"描述: {result2['main_fund']['description']}")
    print(f"\n订单结构:")
    print(f"  主力行为: {result2['order_structure']['main_behavior']}")
    print(f"  散户行为: {result2['order_structure']['retail_behavior']}")
    print(f"  博弈分析: {result2['order_structure']['game_analysis']}")
    print(f"\n资金面评分: {result2['fund_score']}/100")
    print(f"操作信号: {result2['signal']}")
    print(f"操作建议: {result2['description']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    test_fund_flow_analyzer()
