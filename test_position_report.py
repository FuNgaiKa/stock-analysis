#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试持仓调整建议报告生成
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from russ_trading.generators.daily_position_report_generator import DailyPositionReportGenerator
from datetime import datetime
import json

def main():
    """测试生成报告"""

    # 初始化生成器
    generator = DailyPositionReportGenerator()

    # 使用测试持仓数据
    test_positions_file = project_root / "data" / "positions_20251107.json"

    positions = []
    if test_positions_file.exists():
        with open(test_positions_file, 'r', encoding='utf-8') as f:
            positions = json.load(f)
        print(f"✅ 加载持仓数据: {len(positions)} 个持仓")
    else:
        print("⚠️  未找到持仓数据，将生成默认报告")

    # 生成报告
    print("\n开始生成报告...")
    date = datetime.now().strftime('%Y-%m-%d')

    # 获取市场数据
    try:
        market_data = generator.fetch_market_data()
        print("✅ 获取市场数据成功")
    except Exception as e:
        print(f"⚠️  获取市场数据失败: {e}")
        market_data = None

    # 生成报告
    report = generator.generate_report(
        date=date,
        positions=positions,
        market_data=market_data
    )

    # 保存报告
    output_dir = project_root / "russ_trading" / "reports" / "daily" / "2025-11"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"持仓调整建议_{datetime.now().strftime('%Y%m%d')}_test.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 报告已生成: {output_file}")
    print(f"📄 报告长度: {len(report)} 字符")

    # 显示报告前50行
    lines = report.split('\n')
    print(f"\n📝 报告预览（前50行）:")
    print("=" * 80)
    for line in lines[:50]:
        print(line)
    print("=" * 80)
    print(f"... 共 {len(lines)} 行")

if __name__ == "__main__":
    main()
