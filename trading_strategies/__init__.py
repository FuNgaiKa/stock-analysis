#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四指标共振买卖点策略模块
基于MACD、RSI、KDJ、MA的组合信号
"""

__version__ = '1.0.0'
__author__ = 'Claude & Russ'

from .signal_generators.technical_indicators import TechnicalIndicators
from .signal_generators.resonance_signals import ResonanceSignalGenerator

__all__ = [
    'TechnicalIndicators',
    'ResonanceSignalGenerator',
]
