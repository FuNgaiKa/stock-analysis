#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场洞察报告生成器
Market Insight Generator

基本面:技术面 = 55:45 的分析框架

生成每日市场洞察报告,包含:
1. 机构级核心指标(估值/市场宽度/融资融券)
2. 核心资产分析(基本面55% + 技术面45%)
3. 调仓建议
4. 情景分析

作者: Claude Code
日期: 2025-11-08
版本: v1.0
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class MarketInsightGenerator:
    """市场洞察报告生成器"""

    def __init__(self):
        """初始化生成器"""
        self.report_date = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"市场洞察报告生成器初始化完成: {self.report_date}")

    def analyze_asset_fundamental(
        self,
        asset_name: str,
        asset_type: str,
        current_price: float,
        pe_ratio: Optional[float] = None,
        pe_percentile: Optional[float] = None,
        pb_ratio: Optional[float] = None
    ) -> str:
        """
        生成基本面分析 (55%权重)

        Args:
            asset_name: 标的名称
            asset_type: 资产类型 (index/etf/stock)
            current_price: 当前价格
            pe_ratio: 市盈率
            pe_percentile: PE十年分位数
            pb_ratio: 市净率

        Returns:
            基本面分析Markdown文本
        """
        fundamental_md = "**基本面分析** (55%权重):\n"

        # 估值水平
        if pe_ratio and pe_percentile:
            valuation_rating = self._get_valuation_rating(pe_percentile)
            fundamental_md += f"- **估值水平**: PE {pe_ratio:.2f}倍, 十年分位数{pe_percentile:.1f}% {valuation_rating}\n"

            if pe_percentile < 30:
                fundamental_md += f"  - 处于历史低位,估值吸引力强\n"
            elif pe_percentile < 50:
                fundamental_md += f"  - 处于历史中低位,估值合理偏低\n"
            elif pe_percentile < 70:
                fundamental_md += f"  - 处于历史中位,估值中性\n"
            elif pe_percentile < 85:
                fundamental_md += f"  - 处于历史偏高位,需要谨慎\n"
            else:
                fundamental_md += f"  - 处于历史高位,估值泡沫风险\n"

        if pb_ratio:
            fundamental_md += f"  - PB: {pb_ratio:.2f}倍\n"

        # 行业景气度 (需要根据具体标的补充)
        fundamental_md += "- **行业景气度**: [需要根据实际情况补充]\n"
        fundamental_md += "- **业绩预期**: [需要根据实际情况补充]\n"
        fundamental_md += "- **政策环境**: [需要根据实际情况补充]\n"
        fundamental_md += "- **风险因素**: [需要根据实际情况补充]\n"

        return fundamental_md

    def analyze_asset_technical(
        self,
        asset_name: str,
        current_price: float,
        change_pct: float,
        support_levels: Optional[List[float]] = None,
        resistance_levels: Optional[List[float]] = None,
        macd_signal: Optional[str] = None,
        rsi_value: Optional[float] = None
    ) -> str:
        """
        生成技术面分析 (45%权重)

        Args:
            asset_name: 标的名称
            current_price: 当前价格
            change_pct: 涨跌幅
            support_levels: 支撑位列表
            resistance_levels: 阻力位列表
            macd_signal: MACD信号
            rsi_value: RSI值

        Returns:
            技术面分析Markdown文本
        """
        technical_md = "\n**技术面分析** (45%权重):\n"

        # 趋势判断
        if change_pct > 1:
            trend = "上涨趋势"
        elif change_pct > 0:
            trend = "震荡上行"
        elif change_pct > -1:
            trend = "震荡走弱"
        else:
            trend = "下跌趋势"

        technical_md += f"- **趋势判断**: {trend}\n"
        technical_md += f"- **当前价格**: {current_price:.2f} ({change_pct:+.2f}%)\n"

        # 支撑阻力
        if support_levels:
            supports_str = ", ".join([f"{s:.2f}" for s in support_levels])
            technical_md += f"- **关键支撑**: {supports_str}\n"

        if resistance_levels:
            resistances_str = ", ".join([f"{r:.2f}" for r in resistance_levels])
            technical_md += f"- **关键阻力**: {resistances_str}\n"

        # 技术指标
        technical_md += "- **技术指标**:\n"

        if macd_signal:
            technical_md += f"  - MACD: {macd_signal}\n"
        else:
            technical_md += f"  - MACD: [需要补充]\n"

        if rsi_value:
            rsi_status = self._get_rsi_status(rsi_value)
            technical_md += f"  - RSI: {rsi_value:.1f} ({rsi_status})\n"
        else:
            technical_md += f"  - RSI: [需要补充]\n"

        technical_md += "  - KDJ: [需要补充]\n"
        technical_md += "- **成交量**: [需要补充]\n"
        technical_md += "- **形态**: [需要补充]\n"

        return technical_md

    def generate_asset_analysis(
        self,
        asset_name: str,
        asset_type: str,
        recommendation: str,
        score: int,
        current_price: float,
        change_pct: float,
        position_pct: Optional[float] = None,
        pe_ratio: Optional[float] = None,
        pe_percentile: Optional[float] = None,
        pb_ratio: Optional[float] = None,
        support_levels: Optional[List[float]] = None,
        resistance_levels: Optional[List[float]] = None,
        macd_signal: Optional[str] = None,
        rsi_value: Optional[float] = None,
        operation_advice: str = ""
    ) -> str:
        """
        生成单个资产的完整分析

        Args:
            asset_name: 标的名称
            asset_type: 资产类型
            recommendation: 推荐等级 (强烈推荐/中性推荐/谨慎观察)
            score: 综合评分 (0-100)
            current_price: 当前价格
            change_pct: 涨跌幅
            position_pct: 当前仓位百分比
            pe_ratio: 市盈率
            pe_percentile: PE十年分位数
            pb_ratio: 市净率
            support_levels: 支撑位列表
            resistance_levels: 阻力位列表
            macd_signal: MACD信号
            rsi_value: RSI值
            operation_advice: 操作建议

        Returns:
            完整的资产分析Markdown文本
        """
        # 标题
        stars = "🌟" * (score // 30 + 1) if score >= 70 else "⚖️" * 2 if score >= 50 else "⚠️"
        analysis_md = f"\n#### **{asset_name}** {stars} **综合评分: {score}/100**\n\n"

        # 基本面分析 (55%)
        fundamental = self.analyze_asset_fundamental(
            asset_name, asset_type, current_price,
            pe_ratio, pe_percentile, pb_ratio
        )
        analysis_md += fundamental

        # 技术面分析 (45%)
        technical = self.analyze_asset_technical(
            asset_name, current_price, change_pct,
            support_levels, resistance_levels,
            macd_signal, rsi_value
        )
        analysis_md += technical

        # 操作建议
        if operation_advice:
            analysis_md += f"\n**操作建议**: {operation_advice}\n"

        return analysis_md

    def _get_valuation_rating(self, pe_percentile: float) -> str:
        """获取估值评级emoji"""
        if pe_percentile < 30:
            return "🟢"
        elif pe_percentile < 70:
            return "🟡"
        else:
            return "🔴"

    def _get_rsi_status(self, rsi: float) -> str:
        """获取RSI状态描述"""
        if rsi < 30:
            return "超卖"
        elif rsi < 50:
            return "中性偏弱"
        elif rsi < 70:
            return "中性偏强"
        else:
            return "超买"

    def generate_report_header(
        self,
        market_state: str = "震荡市",
        confidence: int = 65,
        total_assets: int = 9,
        turnover: float = 2.02,
        risk_level: str = "中等",
        recommended_position: str = "50%-70%"
    ) -> str:
        """
        生成报告头部

        Returns:
            报告头部Markdown文本
        """
        header = f"""# 📊 市场洞察报告

**生成时间**: {self.report_date}
**报告类型**: 每日市场分析 + 投资策略洞察
**市场状态**: {market_state} (置信度{confidence}%)

---

## 📋 分析概览

- **分析标的**: {total_assets}个核心资产
- **市场热度**: 极高 (成交{turnover:.2f}万亿)
- **风险等级**: {risk_level}
- **建议仓位**: {recommended_position}

---

"""
        return header

    def generate_full_report(
        self,
        market_data: Dict,
        positions: Dict,
        assets_analysis: List[Dict]
    ) -> str:
        """
        生成完整的市场洞察报告

        Args:
            market_data: 市场数据
            positions: 持仓数据
            assets_analysis: 资产分析列表

        Returns:
            完整报告Markdown文本
        """
        report = self.generate_report_header()

        # TODO: 添加更多章节
        # - 机构级核心指标
        # - 核心资产分析
        # - 调仓建议
        # - 情景分析

        return report


def main():
    """主函数 - 示例用法"""
    generator = MarketInsightGenerator()

    # 示例:生成创业板指分析
    cybz_analysis = generator.generate_asset_analysis(
        asset_name="创业板指",
        asset_type="index",
        recommendation="强烈推荐",
        score=82,
        current_price=3208.21,
        change_pct=-0.51,
        position_pct=1.0,
        pe_ratio=38.25,
        pe_percentile=37.6,
        pb_ratio=6.40,
        support_levels=[3150, 3100],
        resistance_levels=[3250, 3300],
        macd_signal="接近金叉",
        rsi_value=57.0,
        operation_advice="🎯 回调3150点分批加仓, 目标仓位20-25%"
    )

    print(cybz_analysis)


if __name__ == "__main__":
    main()
