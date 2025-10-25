#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试缓存数据

在网络不可用时，用于验证缓存机制
"""

import json
from pathlib import Path
from datetime import datetime

# 创建缓存目录
cache_dir = Path(__file__).parent / 'data' / 'cache'
cache_dir.mkdir(parents=True, exist_ok=True)

# 创建模拟的板块轮动数据
test_data = {
    'timestamp': datetime.now().isoformat(),
    'data': {
        'top_gainers': [
            {'name': '半导体', 'change_pct': 5.23, 'leader': '中芯国际'},
            {'name': '人工智能', 'change_pct': 4.87, 'leader': '科大讯飞'},
            {'name': '新能源车', 'change_pct': 3.45, 'leader': '比亚迪'},
            {'name': '光伏', 'change_pct': 2.98, 'leader': '隆基绿能'},
            {'name': '锂电池', 'change_pct': 2.34, 'leader': '宁德时代'}
        ],
        'top_losers': [
            {'name': '房地产', 'change_pct': -3.21, 'leader': 'N/A'},
            {'name': '银行', 'change_pct': -2.87, 'leader': 'N/A'},
            {'name': '钢铁', 'change_pct': -2.54, 'leader': 'N/A'},
            {'name': '煤炭', 'change_pct': -1.98, 'leader': 'N/A'},
            {'name': '化工', 'change_pct': -1.76, 'leader': 'N/A'}
        ],
        'capital_flow': [
            {'sector': '半导体', 'net_inflow': 45.8, 'net_inflow_pct': 8.5},
            {'sector': '人工智能', 'net_inflow': 32.4, 'net_inflow_pct': 6.7},
            {'sector': '新能源车', 'net_inflow': 28.9, 'net_inflow_pct': 5.2}
        ],
        'rotation_signal': '✅ 防守→进攻切换,科技股启动',
        'analysis': '今日领涨: 半导体(+5.2%), 资金流向: 半导体净流入45.8亿',
        'data_source': 'realtime'
    }
}

# 保存到缓存文件
cache_file = cache_dir / 'sector_rotation.json'
with open(cache_file, 'w', encoding='utf-8') as f:
    json.dump(test_data, f, ensure_ascii=False, indent=2)

print(f"✅ 测试缓存已创建: {cache_file}")
print(f"   缓存时间: {test_data['timestamp']}")
print(f"   数据包含: {len(test_data['data']['top_gainers'])} 个领涨板块")
