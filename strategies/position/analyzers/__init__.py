#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析器模块 - Analyzers Package

专业分析器工具集，包含技术分析、市场指标、风险检测等
"""

# 市场指标
from .market_indicators import (
    VIXAnalyzer,
    DXYAnalyzer,
    VHSIAnalyzer,
    SKEWAnalyzer,
)

# 技术分析
from .technical_analysis import (
    DivergenceAnalyzer,
    normalize_dataframe_columns,
    VolumeAnalyzer,
    SlopeAnalyzer,
    SupportResistanceAnalyzer,
    CorrelationAnalyzer,
    HistoricalMatcher,
)

# 市场结构
from .market_structure import (
    MarketBreadthAnalyzer,
    SectorRotationAnalyzer,
    MicrostructureAnalyzer,
    MarketSentimentIndex,
)

# 估值分析
from .valuation import (
    FinancialAnalyzer,
    CreditSpreadAnalyzer,
    TreasuryYieldAnalyzer,
)

# 市场特色
from .market_specific import (
    CNStockIndicators,
    MarginTradingAnalyzer,
    HKConnectAnalyzer,
    SouthboundFundsAnalyzer,
    AHPremiumAnalyzer,
    TurnoverAnalyzer,
)

# 风险检测
from .risk_detection import (
    BullMarketTopDetector,
    USMarketTopDetector,
    HKMarketTopDetector,
)

# 量化因子
from .quantitative import (
    Alpha101Engine,
)

__all__ = [
    # 市场指标
    'VIXAnalyzer',
    'DXYAnalyzer',
    'VHSIAnalyzer',
    'SKEWAnalyzer',
    # 技术分析
    'DivergenceAnalyzer',
    'normalize_dataframe_columns',
    'VolumeAnalyzer',
    'SlopeAnalyzer',
    'SupportResistanceAnalyzer',
    'CorrelationAnalyzer',
    'HistoricalMatcher',
    # 市场结构
    'MarketBreadthAnalyzer',
    'SectorRotationAnalyzer',
    'MicrostructureAnalyzer',
    'MarketSentimentIndex',
    # 估值分析
    'FinancialAnalyzer',
    'CreditSpreadAnalyzer',
    'TreasuryYieldAnalyzer',
    # 市场特色
    'CNStockIndicators',
    'MarginTradingAnalyzer',
    'HKConnectAnalyzer',
    'SouthboundFundsAnalyzer',
    'AHPremiumAnalyzer',
    'TurnoverAnalyzer',
    # 风险检测
    'BullMarketTopDetector',
    'USMarketTopDetector',
    'HKMarketTopDetector',
    # 量化因子
    'Alpha101Engine',
]
