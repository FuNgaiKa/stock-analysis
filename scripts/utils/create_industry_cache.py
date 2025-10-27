#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建行业板块测试缓存数据
"""

import json
from pathlib import Path
from datetime import datetime

# 创建缓存目录
cache_dir = Path(__file__).parent / 'data' / 'cache'
cache_dir.mkdir(parents=True, exist_ok=True)

# 创建模拟的行业板块轮动数据（基于真实申万行业分类）
test_data = {
    'timestamp': datetime.now().isoformat(),
    'data': {
        'top_gainers': [
            {'name': '电子', 'change_pct': 4.58, 'leader': '中芯国际'},
            {'name': '计算机', 'change_pct': 3.92, 'leader': '科大讯飞'},
            {'name': '电力设备', 'change_pct': 3.15, 'leader': '宁德时代'},
            {'name': '通信', 'change_pct': 2.87, 'leader': '中兴通讯'},
            {'name': '传媒', 'change_pct': 2.34, 'leader': '芒果超媒'}
        ],
        'top_losers': [
            {'name': '房地产', 'change_pct': -2.81, 'leader': 'N/A'},
            {'name': '银行', 'change_pct': -1.95, 'leader': 'N/A'},
            {'name': '钢铁', 'change_pct': -1.67, 'leader': 'N/A'},
            {'name': '煤炭', 'change_pct': -1.42, 'leader': 'N/A'},
            {'name': '建筑材料', 'change_pct': -1.28, 'leader': 'N/A'}
        ],
        'capital_flow': [
            {'sector': '电子', 'net_inflow': 52.3, 'net_inflow_pct': 9.2},
            {'sector': '计算机', 'net_inflow': 38.7, 'net_inflow_pct': 7.5},
            {'sector': '电力设备', 'net_inflow': 31.5, 'net_inflow_pct': 6.1}
        ],
        'rotation_signal': '✅ 进攻信号 - 科技/成长板块领涨',
        'analysis': '今日领涨: 电子(+4.6%), 资金流向: 电子净流入52.3亿',
        'data_source': 'realtime'
    }
}

# 保存到缓存文件
cache_file = cache_dir / 'sector_rotation.json'
with open(cache_file, 'w', encoding='utf-8') as f:
    json.dump(test_data, f, ensure_ascii=False, indent=2)

print(f"✅ 行业板块测试缓存已创建: {cache_file}")
print(f"   缓存时间: {test_data['timestamp']}")
print(f"   数据包含: {len(test_data['data']['top_gainers'])} 个领涨行业")
print(f"   领涨行业: {', '.join([x['name'] for x in test_data['data']['top_gainers']])}")
