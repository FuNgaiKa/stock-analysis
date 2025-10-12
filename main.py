#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序入口 (软链接到 scripts/cli.py)
为了保持向后兼容，保留此文件
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入真正的CLI主程序
from scripts.cli import main

if __name__ == '__main__':
    main()
