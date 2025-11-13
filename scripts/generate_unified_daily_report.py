#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成统一每日报告
包含市场洞察 + 个人持仓分析

运行方式:
  python scripts/generate_unified_daily_report.py
  python scripts/generate_unified_daily_report.py --positions data/positions_20251107.json
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from russ_trading.runners.run_unified_analysis import UnifiedAnalysisRunner
from russ_trading.generators.daily_position_report_generator import DailyPositionReportGenerator

def main():
    """生成统一每日报告"""
    parser = argparse.ArgumentParser(description='生成统一每日报告')
    parser.add_argument(
        '--positions',
        help='持仓数据文件路径(JSON格式)',
        default=None
    )
    parser.add_argument(
        '--output',
        help='输出文件路径',
        default=None
    )
    args = parser.parse_args()

    date = datetime.now().strftime('%Y-%m-%d')
    date_str = datetime.now().strftime('%Y%m%d')
    year_month = datetime.now().strftime('%Y-%m')

    print("=" * 80)
    print(f"📊 生成统一每日报告 - {date}")
    print("=" * 80)

    # ========== 1. 加载持仓数据 ==========
    positions = None
    if args.positions:
        positions_file = Path(args.positions)
        if positions_file.exists():
            with open(positions_file, 'r', encoding='utf-8') as f:
                positions = json.load(f)
            print(f"✅ 加载持仓数据: {len(positions)} 个持仓 ({positions_file.name})")
        else:
            print(f"⚠️  持仓文件不存在: {args.positions}")
    else:
        # 尝试加载最新的持仓文件
        positions_dir = project_root / "data"
        if positions_dir.exists():
            position_files = list(positions_dir.glob("positions_*.json"))
            if position_files:
                latest_file = sorted(position_files)[-1]
                with open(latest_file, 'r', encoding='utf-8') as f:
                    positions = json.load(f)
                print(f"✅ 自动加载最新持仓: {len(positions)} 个持仓 ({latest_file.name})")
            else:
                print("⚠️  未找到持仓数据文件")
        else:
            print("⚠️  未找到持仓数据")

    # ========== 2. 获取市场数据 ==========
    print("\n获取市场数据...")
    try:
        position_generator = DailyPositionReportGenerator()
        market_data = position_generator.fetch_market_data()
        print("✅ 市场数据获取成功")
    except Exception as e:
        print(f"⚠️  市场数据获取失败: {e}")
        market_data = None

    # ========== 3. 运行统一分析 ==========
    print("\n运行统一资产分析...")
    try:
        runner = UnifiedAnalysisRunner()

        # 获取所有资产的keys
        from russ_trading.config.unified_config import UNIFIED_ASSETS
        asset_keys = list(UNIFIED_ASSETS.keys())

        print(f"分析 {len(asset_keys)} 个资产...")
        results = runner.analyze_assets(asset_keys)
        print(f"✅ 资产分析完成")

    except Exception as e:
        print(f"❌ 资产分析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ========== 4. 生成统一报告 ==========
    print("\n生成统一报告...")
    try:
        report = runner.format_report(
            results=results,
            format_type='markdown',
            positions=positions,
            market_data=market_data
        )
        print(f"✅ 报告生成成功")
        print(f"📄 报告长度: {len(report)} 字符, {len(report.split(chr(10)))} 行")

    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ========== 5. 保存报告 ==========
    if args.output:
        output_file = Path(args.output)
    else:
        output_dir = project_root / "russ_trading" / "reports" / "daily" / year_month
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"市场洞察报告_{date_str}.md"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 报告已保存: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
