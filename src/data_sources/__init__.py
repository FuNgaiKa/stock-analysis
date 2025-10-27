#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源模块
包含多种股票数据源的接口封装
"""

from .Ashare import *
from .akshare_optimized import *
from .tencent_source import *
from .tushare_source import *

__all__ = [
    'Ashare',
    'akshare_optimized',
    'tencent_source',
    'tushare_source'
]