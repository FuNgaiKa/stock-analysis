#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
杠杆策略分析 - CLI入口脚本
快速运行杠杆策略分析，生成完整的决策建议
"""

import sys
from pathlib import Path
import argparse
import logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analyzers.macro.leverage.leverage_strategy_engine import LeverageStrategyEngine


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/leverage_strategy.log')
        ]
    )


def run_strategy_analysis(
    index_code: str,
    index_name: str,
    win_rate: float = None,
    avg_win: float = None,
    avg_loss: float = None,
    detailed: bool = True
):
    """运行杠杆策略分析"""

    print(f"\n正在分析 {index_name} ({index_code}) 的杠杆策略...\n")

    # 创建引擎
    engine = LeverageStrategyEngine()

    # 生成策略报告
    report = engine.generate_comprehensive_leverage_strategy(
        index_code=index_code,
        index_name=index_name,
        historical_win_rate=win_rate,
        historical_avg_win=avg_win,
        historical_avg_loss=avg_loss,
        include_detailed_analysis=detailed
    )

    # 打印报告
    engine.print_strategy_report(report)

    return report


def main():
    """主函数"""

    parser = argparse.ArgumentParser(
        description='杠杆策略分析工具 - 基于Kelly公式和五维度市场评分',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:

1. 分析上证指数:
   python run_leverage_strategy.py

2. 分析沪深300，并提供历史胜率数据:
   python run_leverage_strategy.py --index hs300 --win-rate 0.58 --avg-win 0.08 --avg-loss 0.05

3. 简化分析（不包含详细操作指导）:
   python run_leverage_strategy.py --no-detailed

4. 查看调试日志:
   python run_leverage_strategy.py --verbose
        """
    )

    # 参数配置
    parser.add_argument(
        '--index',
        type=str,
        default='sz',
        choices=['sz', 'hs300', 'cyb', 'kc50'],
        help='指数代码: sz=上证, hs300=沪深300, cyb=创业板, kc50=科创50 (默认: sz)'
    )

    parser.add_argument(
        '--win-rate',
        type=float,
        default=None,
        help='历史胜率 (0-1)，例如 0.55 表示55%%胜率 (可选)'
    )

    parser.add_argument(
        '--avg-win',
        type=float,
        default=None,
        help='历史平均盈利率，例如 0.08 表示8%%平均盈利 (可选)'
    )

    parser.add_argument(
        '--avg-loss',
        type=float,
        default=None,
        help='历史平均亏损率，例如 0.05 表示5%%平均亏损 (可选)'
    )

    parser.add_argument(
        '--no-detailed',
        action='store_true',
        help='不包含详细操作指导（只显示核心建议）'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )

    args = parser.parse_args()

    # 指数映射
    index_mapping = {
        'sz': ('sh000001', '上证指数'),
        'hs300': ('sh000300', '沪深300'),
        'cyb': ('sz399006', '创业板指'),
        'kc50': ('sh000688', '科创50')
    }

    index_code, index_name = index_mapping[args.index]

    # 配置日志
    setup_logging(args.verbose)

    # 打印欢迎信息
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║          杠杆策略分析工具 - Leverage Strategy Analyzer        ║
    ║                                                              ║
    ║  基于《杠杆与风险管理指南》设计                                ║
    ║  整合 Kelly公式 + 五维度市场评分                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    try:
        # 运行分析
        report = run_strategy_analysis(
            index_code=index_code,
            index_name=index_name,
            win_rate=args.win_rate,
            avg_win=args.avg_win,
            avg_loss=args.avg_loss,
            detailed=not args.no_detailed
        )

        print("\n✅ 分析完成！")

        # 提示信息
        print("\n💡 使用提示:")
        print("  1. 当前版本使用模拟数据演示框架")
        print("  2. 如需接入真实市场数据，请联系开发团队")
        print("  3. 建议结合《杠杆与风险管理指南》理解分析结果")
        print("  4. 杠杆交易有风险，投资需谨慎")

        return 0

    except Exception as e:
        print(f"\n❌ 分析失败: {str(e)}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
