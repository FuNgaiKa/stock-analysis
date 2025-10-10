#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本 - 历史点位对比分析
"""

import sys
import os

# 确保能找到项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from position_analysis.main import main

if __name__ == '__main__':
    sys.exit(main())
