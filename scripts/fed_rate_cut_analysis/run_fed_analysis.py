"""
美联储降息周期分析 - 主执行脚本
"""
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.fed_rate_cut_analysis.fed_cycle_analyzer import FedCycleAnalyzer
from scripts.fed_rate_cut_analysis.cycle_data_provider import FedRateCutDataProvider


def print_header():
    """打印程序标题"""
    print("\n" + "=" * 80)
    print(" " * 20 + "美联储降息周期市场分析系统")
    print(" " * 25 + f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


def analyze_single_cycle(analyzer: FedCycleAnalyzer, cycle_name: str, market: str):
    """分析单个降息周期"""
    provider = FedRateCutDataProvider()

    try:
        cycle = provider.get_cycle_by_name(cycle_name)
    except ValueError as e:
        print(f"错误: {e}")
        print("\n可用的降息周期:")
        for c in provider.get_all_cycles():
            print(f"  - {c.name}")
        return

    print(f"\n正在分析: {cycle.name}")
    print(f"时间范围: {cycle.start_date} ~ {cycle.end_date}")
    print(f"周期类型: {cycle.cycle_type}")
    print(f"经济背景: {cycle.background}\n")

    result = analyzer.analyze_cycle(cycle, market=market)

    # 打印结果
    print("\n" + "=" * 80)
    print("分析结果")
    print("=" * 80 + "\n")

    for symbol, analysis in result["indices_analysis"].items():
        print(f"\n【{analysis['name']} ({symbol})】")
        print("-" * 80)

        for stage_name, metrics in analysis["stages"].items():
            if metrics:
                print(f"\n{stage_name}:")
                for key, value in metrics.items():
                    print(f"  {key}: {value}")


def analyze_all_cycles(analyzer: FedCycleAnalyzer, market: str):
    """分析所有降息周期并生成对比报告"""
    print("\n正在分析所有降息周期,请稍候...\n")

    results = analyzer.analyze_all_cycles(market=market)

    # 生成摘要
    summary = analyzer.generate_summary_table(results)
    print(summary)

    # 生成最佳表现排名
    print("\n" + "=" * 80)
    print("最佳表现排名 (按总收益率)")
    print("=" * 80 + "\n")

    best_performers = analyzer.get_best_performers(results, metric="总收益率(%)")
    if not best_performers.empty:
        print(best_performers.to_string(index=False))
    else:
        print("无数据可显示")

    # 保存详细报告
    save_report(results, analyzer, market)


def analyze_comparison(analyzer: FedCycleAnalyzer, market: str):
    """对比最近两个降息周期(2019 vs 2024)"""
    provider = FedRateCutDataProvider()
    recent_cycles = provider.get_recent_cycles(n=2)

    print("\n正在对比最近两个降息周期...\n")
    print(f"周期1: {recent_cycles[0].name}")
    print(f"周期2: {recent_cycles[1].name}\n")

    results = []
    for cycle in recent_cycles:
        result = analyzer.analyze_cycle(cycle, market=market)
        results.append(result)

    # 生成对比表格
    summary = analyzer.generate_summary_table(results)
    print(summary)


def save_report(results, analyzer: FedCycleAnalyzer, market: str):
    """保存分析报告到文件"""
    # 使用项目根目录的reports文件夹
    project_root = Path(__file__).parent.parent.parent
    report_dir = project_root / "reports"
    report_dir.mkdir(exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"fed_cycle_analysis_{market}_{timestamp}.txt"
    filepath = report_dir / filename

    # 写入增强版报告
    with open(filepath, "w", encoding="utf-8") as f:
        # 使用增强版报告生成器
        enhanced_report = analyzer.generate_enhanced_report(results)
        f.write(enhanced_report)

        # 追加最佳表现排名
        f.write("\n\n" + "=" * 100 + "\n")
        f.write("最佳表现排名 (按总收益率)\n")
        f.write("=" * 100 + "\n\n")
        best_performers = analyzer.get_best_performers(results, metric="总收益率(%)")
        if not best_performers.empty:
            f.write(best_performers.to_string(index=False))

    print(f"\n✅ 增强版分析报告已保存至: {filepath}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="美联储降息周期市场分析")

    parser.add_argument(
        "--mode",
        choices=["all", "single", "compare", "current"],
        default="all",
        help="分析模式: all(所有周期), single(单个周期), compare(对比最近两个), current(仅当前周期)"
    )

    parser.add_argument(
        "--cycle",
        type=str,
        help="指定要分析的降息周期名称(用于single模式)"
    )

    parser.add_argument(
        "--market",
        choices=["all", "us", "cn", "hk"],
        default="all",
        help="市场选择: all(全部), us(美股), cn(A股), hk(港股)"
    )

    args = parser.parse_args()

    # 打印标题
    print_header()

    # 创建分析器
    analyzer = FedCycleAnalyzer()
    provider = FedRateCutDataProvider()

    # 根据模式执行分析
    if args.mode == "all":
        # 分析所有周期
        analyze_all_cycles(analyzer, args.market)

    elif args.mode == "single":
        # 分析单个周期
        if not args.cycle:
            print("错误: single模式需要指定 --cycle 参数\n")
            print("可用的降息周期:")
            for c in provider.get_all_cycles():
                print(f"  - {c.name}")
            return

        analyze_single_cycle(analyzer, args.cycle, args.market)

    elif args.mode == "compare":
        # 对比最近两个周期
        analyze_comparison(analyzer, args.market)

    elif args.mode == "current":
        # 仅分析当前周期
        current_cycle = provider.get_current_cycle()
        analyze_single_cycle(analyzer, current_cycle.name, args.market)

    print("\n" + "=" * 80)
    print("分析完成!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
