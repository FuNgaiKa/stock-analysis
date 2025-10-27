"""
增强版美联储降息周期分析 - 支持多周期对比、特朗普执政期、A股牛市分析
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.fed_rate_cut_analysis.fed_cycle_analyzer import FedCycleAnalyzer
from scripts.fed_rate_cut_analysis.cycle_data_provider import FedRateCutDataProvider
from scripts.fed_rate_cut_analysis.special_period_analyzer import SpecialPeriodAnalyzer
from scripts.fed_rate_cut_analysis.special_period_provider import SpecialPeriodProvider


def print_header(title: str = "美联储降息周期市场分析系统"):
    """打印程序标题"""
    print("\n" + "=" * 100)
    print(" " * 30 + title)
    print(" " * 35 + f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100 + "\n")


def analyze_multiple_cycles(analyzer: FedCycleAnalyzer, cycle_names: list, market: str):
    """分析多个指定的降息周期"""
    provider = FedRateCutDataProvider()

    print(f"\n正在对比 {len(cycle_names)} 个降息周期...\n")

    results = []
    for cycle_name in cycle_names:
        try:
            cycle = provider.get_cycle_by_name(cycle_name)
            print(f"[OK] 已加载周期: {cycle.name}")
            result = analyzer.analyze_cycle(cycle, market=market)
            results.append(result)
        except ValueError as e:
            print(f"[ERROR] 错误: {e}")

    if not results:
        print("\n没有有效的分析结果")
        return

    # 生成对比表格
    summary = analyzer.generate_summary_table(results)
    print(summary)

    # 保存报告
    save_report(results, analyzer, market, "multi_cycle")


def analyze_trump_periods(market: str):
    """分析特朗普执政期"""
    print_header("特朗普执政期市场分析")

    analyzer = SpecialPeriodAnalyzer()
    provider = SpecialPeriodProvider()

    # 打印背景信息
    print(provider.get_special_period_summary(category="trump"))

    print("\n开始分析特朗普执政期市场表现...\n")
    results = analyzer.analyze_trump_periods(market=market)

    # 生成对比表格
    summary = analyzer.generate_comparison_table(results)
    print(summary)

    # 保存报告
    save_special_report(results, "trump_periods", market)


def analyze_cn_bull_markets():
    """分析A股历史牛市"""
    print_header("A股历史牛市分析")

    analyzer = SpecialPeriodAnalyzer()
    provider = SpecialPeriodProvider()

    # 打印背景信息
    print(provider.get_special_period_summary(category="bull"))

    print("\n开始分析A股历史牛市表现...\n")
    results = analyzer.analyze_cn_bull_markets()

    # 生成对比表格
    summary = analyzer.generate_comparison_table(results)
    print(summary)

    # 生成关键洞察
    print("\n" + "=" * 100)
    print("关键洞察")
    print("=" * 100 + "\n")

    for result in results:
        period_name = result["period_info"].name
        print(f"\n【{period_name}】")

        for symbol, analysis in result["indices_analysis"].items():
            metrics = analysis["metrics"]
            if metrics:
                total_return = metrics.get('总收益率(%)', 0)
                annual_return = metrics.get('年化收益率(%)', 0)
                max_dd = metrics.get('最大回撤(%)', 0)

                print(f"  {analysis['name']}: 总收益 {total_return}%, "
                      f"年化收益 {annual_return}%, 最大回撤 {max_dd}%")

    # 保存报告
    save_special_report(results, "cn_bull_markets", "cn")


def save_report(results, analyzer, market: str, report_type: str):
    """保存降息周期分析报告"""
    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_type}_{market}_{timestamp}.txt"
    filepath = report_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("美联储降息周期市场分析报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 100 + "\n\n")

        summary = analyzer.generate_summary_table(results)
        f.write(summary)

        f.write("\n\n最佳表现排名 (按总收益率)\n")
        f.write("=" * 100 + "\n")
        best_performers = analyzer.get_best_performers(results, metric="总收益率(%)")
        if not best_performers.empty:
            f.write(best_performers.to_string(index=False))

    print(f"\n>> 详细报告已保存至: {filepath}")


def save_special_report(results, report_type: str, market: str):
    """保存特殊时期分析报告"""
    from scripts.fed_rate_cut_analysis.special_period_analyzer import SpecialPeriodAnalyzer

    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_type}_{market}_{timestamp}.txt"
    filepath = report_dir / filename

    analyzer = SpecialPeriodAnalyzer()

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{'特朗普执政期' if 'trump' in report_type else 'A股历史牛市'}市场分析报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 100 + "\n\n")

        summary = analyzer.generate_comparison_table(results)
        f.write(summary)

    print(f"\n>> 详细报告已保存至: {filepath}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="增强版美联储降息周期市场分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 对比多个降息周期
  python run_enhanced_analysis.py --mode multi --cycles "2019年预防式降息" "2024年软着陆降息"

  # 分析特朗普执政期
  python run_enhanced_analysis.py --mode trump --market all

  # 分析A股历史牛市
  python run_enhanced_analysis.py --mode bull

  # 对比2001和2007两次纾困式降息
  python run_enhanced_analysis.py --mode multi --cycles "2001年互联网泡沫" "2007-2008年金融危机" --market us
        """
    )

    parser.add_argument(
        "--mode",
        choices=["multi", "trump", "bull"],
        required=True,
        help="分析模式: multi(多周期对比), trump(特朗普执政期), bull(A股牛市)"
    )

    parser.add_argument(
        "--cycles",
        nargs='+',
        help="指定要对比的降息周期名称(用于multi模式,支持多个)"
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

    # 根据模式执行分析
    if args.mode == "multi":
        # 多周期对比
        if not args.cycles:
            print("错误: multi模式需要指定 --cycles 参数\n")
            print("可用的降息周期:")
            provider = FedRateCutDataProvider()
            for i, c in enumerate(provider.get_all_cycles(), 1):
                print(f"  {i}. {c.name}")
            print("\n示例用法:")
            print('  python run_enhanced_analysis.py --mode multi --cycles "2019年预防式降息" "2024年软着陆降息"')
            return

        analyzer = FedCycleAnalyzer()
        analyze_multiple_cycles(analyzer, args.cycles, args.market)

    elif args.mode == "trump":
        # 特朗普执政期分析
        analyze_trump_periods(args.market)

    elif args.mode == "bull":
        # A股牛市分析
        analyze_cn_bull_markets()

    print("\n" + "=" * 100)
    print("分析完成!")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
