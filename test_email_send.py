#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试邮件发送"""

import logging
from scripts.unified_analysis.unified_email_notifier import UnifiedEmailNotifier
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 读取最新的报告
report_path = Path("C:/Users/russell.fu/PycharmProjects/stock-analysis/reports/20251016_统一资产分析报告_22个标的.md")

with open(report_path, 'r', encoding='utf-8') as f:
    text_content = f.read()

# 构建简单的报告数据
report = {
    'date': '2025-10-16',
    'assets': {
        'test1': {
            'asset_name': '测试资产1',
            'comprehensive_judgment': {
                'direction': '看多',
                'recommended_position': '60-70%',
                'strategies': ['策略1', '策略2']
            },
            'historical_analysis': {
                'current_price': 100.0,
                'current_change_pct': 1.5,
                '20d': {
                    'up_prob': 0.65,
                    'mean_return': 0.03,
                    'confidence': 0.7
                }
            },
            'risk_assessment': {
                'risk_score': 0.3,
                'risk_level': '低风险🟢',
                'risk_factors': []
            }
        },
        'test2': {
            'asset_name': '测试资产2',
            'comprehensive_judgment': {
                'direction': '看空',
                'recommended_position': '20-30%',
                'strategies': ['策略3', '策略4']
            },
            'historical_analysis': {
                'current_price': 50.0,
                'current_change_pct': -2.0,
                '20d': {
                    'up_prob': 0.35,
                    'mean_return': -0.02,
                    'confidence': 0.6
                }
            },
            'risk_assessment': {
                'risk_score': 0.6,
                'risk_level': '中风险⚠️',
                'risk_factors': ['风险因素1']
            }
        }
    }
}

# 发送邮件
notifier = UnifiedEmailNotifier()
success = notifier.send_unified_report(report, text_content[:500])  # 只用前500字符做测试

if success:
    print("✅ 邮件发送测试完成")
else:
    print("❌ 邮件发送失败")
