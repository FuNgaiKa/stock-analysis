#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新每日报告（市场洞察报告 + 持仓调整建议）
使用最新的市场数据
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from russ_trading.generators.market_insight_generator import MarketInsightGenerator
from russ_trading.generators.daily_position_report_generator import DailyPositionReportGenerator
from datetime import datetime
import json

def main():
    """生成最新的市场洞察报告和持仓调整建议"""

    date = datetime.now().strftime('%Y-%m-%d')
    date_str = datetime.now().strftime('%Y%m%d')
    year_month = datetime.now().strftime('%Y-%m')

    print(f"=" * 80)
    print(f"📊 更新每日报告 - {date}")
    print(f"=" * 80)

    # ========== 1. 生成市场洞察报告 ==========
    print(f"\n{'='*80}")
    print("1️⃣  生成市场洞察报告...")
    print(f"{'='*80}\n")

    try:
        market_generator = MarketInsightGenerator()
        market_report = market_generator.generate_full_report()

        # 保存市场洞察报告
        market_output_dir = project_root / "reports" / "daily" / year_month
        market_output_dir.mkdir(parents=True, exist_ok=True)

        market_output_file = market_output_dir / f"市场洞察报告_{date_str}.md"
        with open(market_output_file, 'w', encoding='utf-8') as f:
            f.write(market_report)

        print(f"✅ 市场洞察报告已生成: {market_output_file}")
        print(f"📄 报告长度: {len(market_report)} 字符, {len(market_report.split(chr(10)))} 行")

    except Exception as e:
        print(f"❌ 市场洞察报告生成失败: {e}")
        import traceback
        traceback.print_exc()

    # ========== 2. 生成持仓调整建议 ==========
    print(f"\n{'='*80}")
    print("2️⃣  生成持仓调整建议...")
    print(f"{'='*80}\n")

    try:
        position_generator = DailyPositionReportGenerator()

        # 加载持仓数据（如果有）
        positions_file = project_root / "data" / f"positions_{date_str}.json"
        if not positions_file.exists():
            # 尝试最新的持仓文件
            positions_dir = project_root / "data"
            if positions_dir.exists():
                position_files = list(positions_dir.glob("positions_*.json"))
                if position_files:
                    positions_file = sorted(position_files)[-1]
                    print(f"📂 使用最新持仓文件: {positions_file.name}")

        positions = []
        if positions_file.exists():
            with open(positions_file, 'r', encoding='utf-8') as f:
                positions = json.load(f)
            print(f"✅ 加载持仓数据: {len(positions)} 个持仓")
        else:
            print("⚠️  未找到持仓数据，将生成默认报告")

        # 获取市场数据
        try:
            market_data = position_generator.fetch_market_data()
            print("✅ 获取市场数据成功")
        except Exception as e:
            print(f"⚠️  获取市场数据失败: {e}")
            market_data = None

        # 生成报告
        position_report = position_generator.generate_report(
            date=date,
            positions=positions,
            market_data=market_data
        )

        # 保存持仓调整建议
        position_output_dir = project_root / "russ_trading" / "reports" / "daily" / year_month
        position_output_dir.mkdir(parents=True, exist_ok=True)

        position_output_file = position_output_dir / f"持仓调整建议_{date_str}.md"
        with open(position_output_file, 'w', encoding='utf-8') as f:
            f.write(position_report)

        print(f"✅ 持仓调整建议已生成: {position_output_file}")
        print(f"📄 报告长度: {len(position_report)} 字符, {len(position_report.split(chr(10)))} 行")

    except Exception as e:
        print(f"❌ 持仓调整建议生成失败: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*80}")
    print(f"✅ 报告更新完成")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
