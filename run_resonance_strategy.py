#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四指标共振策略 - 快速启动脚本
放在项目根目录，方便直接运行
"""

import sys
import os

# 确保能找到trading_strategies模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trading_strategies.examples.quick_resonance_demo import main

if __name__ == '__main__':
    main()
