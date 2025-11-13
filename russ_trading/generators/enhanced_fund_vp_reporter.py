#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版资金面和量价分析报告生成器
Enhanced Fund Flow & Volume-Price Reporter

为看多的标的生成详细的资金面和量价关系分析报告
其他标的只展示简洁结论

作者: Claude Code
日期: 2025-11-13
版本: v1.0
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from russ_trading.analyzers.fund_flow_analyzer import FundFlowAnalyzer
from russ_trading.analyzers.volume_price_analyzer import VolumePriceAnalyzer


class EnhancedFundVPReporter:
    """增强版资金面和量价分析报告生成器"""

    def __init__(self):
        """初始化生成器"""
        self.fund_analyzer = FundFlowAnalyzer()
        self.vp_analyzer = VolumePriceAnalyzer()

    def generate_detailed_fund_analysis(self, fund_data: Dict) -> str:
        """
        生成详细的资金流向分析报告(用于看多标的)

        Args:
            fund_data: 资金流向分析结果

        Returns:
            Markdown格式的详细报告
        """
        md = "\n#### 💰 资金流向深度分析\n\n"

        # 主力资金
        main_fund = fund_data.get('main_fund', {})
        md += "**主力资金**:\n"
        md += f"- **5日净流入**: {main_fund.get('net_inflow_5d', 0):+.2f}亿元\n"
        md += f"- **20日净流入**: {main_fund.get('net_inflow_20d', 0):+.2f}亿元\n"
        md += f"- **资金趋势**: {main_fund.get('trend', 'N/A')} ({main_fund.get('strength', 'N/A')})\n"
        md += f"- **趋势描述**: {main_fund.get('description', 'N/A')}\n\n"

        # 订单结构
        order_struct = fund_data.get('order_structure', {})
        md += "**订单结构** (今日):\n"
        md += f"- **超大单**: {order_struct.get('super_large', 0):+.2f}亿 {'✅' if order_struct.get('super_large', 0) > 0 else '🔴'}\n"
        md += f"- **大单**: {order_struct.get('large', 0):+.2f}亿 {'✅' if order_struct.get('large', 0) > 0 else '🔴'}\n"
        md += f"- **中单**: {order_struct.get('medium', 0):+.2f}亿\n"
        md += f"- **小单**: {order_struct.get('small', 0):+.2f}亿\n\n"

        md += f"**主力行为**: {order_struct.get('main_behavior', 'N/A')}\n"
        md += f"**散户行为**: {order_struct.get('retail_behavior', 'N/A')}\n"
        md += f"**博弈分析**: {order_struct.get('game_analysis', 'N/A')}\n\n"

        # 综合评价
        score = fund_data.get('fund_score', 0)
        signal = fund_data.get('signal', 'N/A')
        description = fund_data.get('description', 'N/A')

        md += f"**资金面评分**: {score}/100 "
        if score >= 80:
            md += "🔥🔥🔥\n"
        elif score >= 65:
            md += "✅✅\n"
        elif score >= 50:
            md += "✅\n"
        elif score >= 35:
            md += "⚖️\n"
        else:
            md += "⚠️\n"

        md += f"**操作信号**: {signal}\n"
        md += f"**操作建议**: {description}\n"

        return md

    def generate_simple_fund_summary(self, fund_data: Dict) -> str:
        """
        生成简洁的资金流向总结(用于非看多标的)

        Args:
            fund_data: 资金流向分析结果

        Returns:
            简洁的一行总结
        """
        score = fund_data.get('fund_score', 0)
        signal = fund_data.get('signal', 'N/A')
        trend = fund_data.get('main_fund', {}).get('trend', 'N/A')

        return f"- **资金面**: {score}/100分,{trend},{signal}\n"

    def generate_detailed_vp_analysis(self, vp_data: Dict) -> str:
        """
        生成详细的量价关系分析报告(用于看多标的)

        Args:
            vp_data: 量价关系分析结果

        Returns:
            Markdown格式的详细报告
        """
        md = "\n#### 📊 量价关系深度分析\n\n"

        # 量价配合
        cooperation = vp_data.get('cooperation', {})
        md += "**量价配合状态**:\n"
        md += f"- **整体状态**: {cooperation.get('overall_status', 'N/A')}\n"
        md += f"- **配合质量**: {cooperation.get('overall_quality', 'N/A')}\n"
        md += f"- **协同度**: {cooperation.get('cooperation_degree', 0)}/100\n"
        md += f"- **描述**: {cooperation.get('description', 'N/A')}\n\n"

        # 最近5日量价关系
        recent_relations = cooperation.get('recent_relations', [])
        if recent_relations:
            md += "**最近5日量价关系**:\n"
            for rel in recent_relations[-5:]:
                date = rel.get('date', 'N/A')
                relation = rel.get('relation', 'N/A')
                quality = rel.get('quality', 'N/A')

                quality_emoji = {
                    '健康': '✅',
                    '乏力': '⚠️',
                    '恐慌': '🔴',
                    '企稳': '🟡',
                    '观望': '⚖️'
                }.get(quality, '')

                md += f"- {date}: {relation} ({quality}) {quality_emoji}\n"
            md += "\n"

        # 量价背离检测
        divergence = vp_data.get('divergence', {})
        md += "**量价背离检测**:\n"
        md += f"- **顶背离**: {'是 ⚠️' if divergence.get('top_divergence', False) else '否 ✅'}\n"
        if divergence.get('top_divergence', False):
            md += f"  - {divergence.get('top_divergence_desc', '')}\n"
        md += f"- **底背离**: {'是 🟡' if divergence.get('bottom_divergence', False) else '否'}\n"
        if divergence.get('bottom_divergence', False):
            md += f"  - {divergence.get('bottom_divergence_desc', '')}\n"
        md += "\n"

        # 成交量特征
        volume_features = vp_data.get('volume_features', {})
        md += "**成交量特征**:\n"
        md += f"- **当前状态**: {volume_features.get('volume_status', 'N/A')}\n"
        md += f"- **相对5日均量**: {volume_features.get('volume_ratio_5d', 0):.2f}倍\n"
        md += f"- **相对20日均量**: {volume_features.get('volume_ratio_20d', 0):.2f}倍\n"
        md += f"- **量能趋势**: {volume_features.get('volume_trend', 'N/A')}\n"
        md += f"- **描述**: {volume_features.get('description', 'N/A')}\n\n"

        # 综合评价
        score = vp_data.get('vp_score', 0)
        signal = vp_data.get('signal', 'N/A')
        description = vp_data.get('description', 'N/A')

        md += f"**量价关系评分**: {score}/100 "
        if score >= 80:
            md += "🔥🔥🔥\n"
        elif score >= 65:
            md += "✅✅\n"
        elif score >= 50:
            md += "✅\n"
        elif score >= 35:
            md += "⚖️\n"
        else:
            md += "⚠️\n"

        md += f"**操作信号**: {signal}\n"
        md += f"**操作建议**: {description}\n"

        return md

    def generate_simple_vp_summary(self, vp_data: Dict) -> str:
        """
        生成简洁的量价关系总结(用于非看多标的)

        Args:
            vp_data: 量价关系分析结果

        Returns:
            简洁的一行总结
        """
        score = vp_data.get('vp_score', 0)
        signal = vp_data.get('signal', 'N/A')
        status = vp_data.get('cooperation', {}).get('overall_status', 'N/A')

        return f"- **量价关系**: {score}/100分,{status},{signal}\n"

    def generate_enhanced_section(
        self,
        asset_name: str,
        direction: str,
        fund_data: Optional[Dict] = None,
        vp_data: Optional[Dict] = None
    ) -> str:
        """
        生成增强版分析章节

        Args:
            asset_name: 资产名称
            direction: 方向判断 (强烈看多/看多/中性偏多/中性/看空/强烈看空)
            fund_data: 资金流向数据
            vp_data: 量价关系数据

        Returns:
            Markdown格式的分析报告
        """
        # 判断是否为看多标的
        is_bullish = direction in ['强烈看多', '看多']

        md = ""

        if is_bullish:
            # 看多标的: 展示详细分析
            if fund_data:
                md += self.generate_detailed_fund_analysis(fund_data)

            if vp_data:
                md += self.generate_detailed_vp_analysis(vp_data)
        else:
            # 非看多标的: 只展示简洁结论
            if fund_data or vp_data:
                md += "\n**增强分析** (简洁版):\n"

            if fund_data:
                md += self.generate_simple_fund_summary(fund_data)

            if vp_data:
                md += self.generate_simple_vp_summary(vp_data)

        return md


def test_enhanced_reporter():
    """测试增强版报告生成器"""
    print("=" * 80)
    print("增强版资金面和量价分析报告生成器测试")
    print("=" * 80)

    reporter = EnhancedFundVPReporter()

    # 模拟资金流向数据
    fund_data = {
        'main_fund': {
            'net_inflow_5d': 5.2,
            'net_inflow_20d': 18.5,
            'trend': '持续流入',
            'strength': '强势',
            'description': '主力资金持续大量流入,资金面强势'
        },
        'order_structure': {
            'super_large': 3.5,
            'large': 1.7,
            'medium': -1.8,
            'small': -3.2,
            'main_inflow': 5.2,
            'retail_inflow': -5.0,
            'main_behavior': '主力强势吸筹',
            'retail_behavior': '散户恐慌割肉',
            'game_analysis': '✅ 主力吸筹+散户割肉,筹码从散户转向主力(积极信号)'
        },
        'fund_score': 85,
        'signal': '强烈买入',
        'description': '资金面极强,主力大量流入,可积极配置,主力吸筹散户割肉,积极信号'
    }

    # 模拟量价关系数据
    vp_data = {
        'cooperation': {
            'overall_status': '量价齐升',
            'overall_quality': '优秀',
            'cooperation_degree': 92,
            'description': '量价配合良好,价涨量增,上涨健康',
            'recent_relations': [
                {'date': '2025-11-09', 'relation': '价涨量增', 'quality': '健康'},
                {'date': '2025-11-10', 'relation': '价涨量增', 'quality': '健康'},
                {'date': '2025-11-11', 'relation': '价涨量缩', 'quality': '乏力'},
                {'date': '2025-11-12', 'relation': '价涨量增', 'quality': '健康'},
                {'date': '2025-11-13', 'relation': '价涨量增', 'quality': '健康'}
            ]
        },
        'divergence': {
            'top_divergence': False,
            'top_divergence_desc': '无顶背离',
            'bottom_divergence': False,
            'bottom_divergence_desc': '无底背离'
        },
        'volume_features': {
            'volume_status': '显著放量',
            'volume_ratio_5d': 1.65,
            'volume_ratio_20d': 1.42,
            'volume_trend': '放大',
            'description': '成交量是5日均量的1.7倍,显著放量'
        },
        'vp_score': 88,
        'signal': '强烈买入',
        'description': '量价配合极佳,量价齐升,可积极配置'
    }

    print("\n测试场景1: 看多标的(详细分析)")
    print("-" * 80)
    report1 = reporter.generate_enhanced_section(
        asset_name="港股创新药",
        direction="强烈看多",
        fund_data=fund_data,
        vp_data=vp_data
    )
    print(report1)

    print("\n" + "=" * 80)
    print("\n测试场景2: 看空标的(简洁结论)")
    print("-" * 80)
    report2 = reporter.generate_enhanced_section(
        asset_name="A股白酒",
        direction="看空",
        fund_data=fund_data,
        vp_data=vp_data
    )
    print(report2)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_enhanced_reporter()
