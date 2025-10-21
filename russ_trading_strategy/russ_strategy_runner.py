"""
Russ个人交易策略主程序

整合以下功能模块:
1. 持仓健康度检查 (PositionHealthChecker)
2. 收益追踪对比 (PerformanceTracker)
3. 潜在空间评估 (PotentialAnalyzer)
4. 月度计划生成 (MonthlyPlanGenerator)
5. 统一资产分析 (UnifiedAnalysisRunner)

Usage:
    # 完整策略报告(包含所有模块)
    python russ_strategy_runner.py --full-report

    # 持仓健康度检查
    python russ_strategy_runner.py --health-check --positions positions.json

    # 收益追踪
    python russ_strategy_runner.py --performance --capital 550000 --hs300 4538

    # 潜在空间评估
    python russ_strategy_runner.py --potential --assets CYBZ,HS300,KECHUANG50

    # 月度计划
    python russ_strategy_runner.py --monthly-plan --month 2025-11

    # 保存报告
    python russ_strategy_runner.py --full-report --save reports/russ_strategy.md
"""

import sys
import os
import argparse
import json
from datetime import datetime
from typing import Dict, List, Optional

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from russ_trading_strategy.position_health_checker import PositionHealthChecker
from russ_trading_strategy.performance_tracker import PerformanceTracker
from russ_trading_strategy.potential_analyzer import PotentialAnalyzer
from russ_trading_strategy.monthly_plan_generator import MonthlyPlanGenerator

# 新增模块导入
try:
    from russ_trading_strategy.risk_manager import RiskManager
    from russ_trading_strategy.dynamic_position_manager import DynamicPositionManager
    from russ_trading_strategy.backtest_engine_enhanced import BacktestEngineEnhanced
    from russ_trading_strategy.data_manager import DataManager
    from russ_trading_strategy.visualizer import Visualizer
    HAS_ENHANCED_MODULES = True
except ImportError as e:
    print(f"警告: 部分增强模块导入失败: {e}")
    HAS_ENHANCED_MODULES = False


class RussStrategyRunner:
    """Russ个人交易策略运行器"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化策略运行器

        Args:
            config: 配置字典,包含各模块的配置
        """
        if config is None:
            config = self._load_default_config()

        self.config = config

        # 初始化各模块
        self.health_checker = PositionHealthChecker(config.get('strategy', {}))
        self.performance_tracker = PerformanceTracker(config.get('targets', {}))
        self.potential_analyzer = PotentialAnalyzer()
        self.monthly_plan_generator = MonthlyPlanGenerator(config.get('strategy', {}))

        # 初始化增强模块(如果可用)
        if HAS_ENHANCED_MODULES:
            self.risk_manager = RiskManager(risk_free_rate=config.get('risk_free_rate', 0.03))
            self.position_manager = DynamicPositionManager(config.get('strategy', {}))
            self.backtest_engine = BacktestEngineEnhanced()
            self.data_manager = DataManager(data_dir=config.get('data_dir', 'data/russ_trading'))
            self.visualizer = Visualizer(output_dir=config.get('charts_dir', 'charts'))
        else:
            self.risk_manager = None
            self.position_manager = None
            self.backtest_engine = None
            self.data_manager = None
            self.visualizer = None

    def _load_default_config(self) -> Dict:
        """加载默认配置"""
        return {
            'strategy': {
                'min_position': 0.50,  # 最小仓位50%
                'max_position': 0.90,  # 最大仓位90%
                'max_single_position': 0.20,  # 单一标的最大20%
                'black_swan_reserve': 0.10,  # 黑天鹅预留10%
                'min_assets': 3,  # 最少3只
                'max_assets': 5,  # 最多5只
                'target_annual_return': 0.15,  # 年化15%
                'risk_preference': 'moderate'  # 风险偏好
            },
            'targets': {
                'stage_targets': [500000, 600000, 700000, 1000000],  # 阶段目标
                'base_date': '2025-01-01',  # 基准日期
                'initial_capital': 500000,  # 初始资金50万
                'target_annual_return': 0.15  # 年化15%
            },
            'benchmarks': {
                'hs300_base': 3145.0,  # 沪深300基准点位
                'cybz_base': 2060.0,  # 创业板基准点位
                'kechuang50_base': 955.0  # 科创50基准点位
            }
        }

    def run_full_report(
        self,
        positions: Optional[List[Dict]] = None,
        current_capital: Optional[float] = None,
        market_data: Optional[Dict] = None
    ) -> str:
        """
        生成完整策略报告

        Args:
            positions: 当前持仓列表
            current_capital: 当前资金
            market_data: 市场数据

        Returns:
            完整的Markdown报告
        """
        lines = []

        # 标题
        lines.append("# 📊 Russ个人交易策略完整报告")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. 持仓健康度检查
        if positions:
            lines.append("# 第一部分: 持仓健康度检查")
            lines.append("")
            health_result = self.health_checker.check_position_health(positions)
            health_report = self.health_checker.format_health_report(health_result, 'markdown')
            lines.append(health_report)
            lines.append("")
            lines.append("---")
            lines.append("")

        # 2. 收益追踪对比
        if current_capital and market_data:
            lines.append("# 第二部分: 收益追踪对比")
            lines.append("")
            hs300_current = market_data.get('indices', {}).get('HS300', {}).get('current', 4538)
            perf_result = self.performance_tracker.track_performance(
                current_capital=current_capital,
                hs300_current=hs300_current,
                hs300_base=self.config['benchmarks']['hs300_base']
            )
            perf_report = self.performance_tracker.format_performance_report(perf_result, 'markdown')
            lines.append(perf_report)
            lines.append("")
            lines.append("---")
            lines.append("")

        # 3. 潜在空间评估
        if market_data:
            lines.append("# 第三部分: 潜在空间评估")
            lines.append("")

            indices = market_data.get('indices', {})
            assets_to_analyze = []

            for key in ['HS300', 'CYBZ', 'KECHUANG50']:
                if key in indices:
                    assets_to_analyze.append({
                        'asset_key': key,
                        'current_price': indices[key].get('current', 0)
                    })

            if assets_to_analyze:
                potential_result = self.potential_analyzer.analyze_multiple_assets(
                    assets_to_analyze,
                    scenario='average'
                )
                potential_report = self.potential_analyzer.format_potential_report(
                    potential_result,
                    format_type='markdown',
                    single_asset=False
                )
                lines.append(potential_report)
            lines.append("")
            lines.append("---")
            lines.append("")

        # 底部说明
        lines.append("## 📖 使用说明")
        lines.append("")
        lines.append("### 投资策略原则")
        lines.append("")
        lines.append("1. **仓位管理**: 滚动保持5-9成,留至少1成应对黑天鹅")
        lines.append("2. **标的选择**: 集中投资3-5只,单一标的≤20%")
        lines.append("3. **投资节奏**: 长线底仓+波段加减仓")
        lines.append("4. **收益目标**: 年化15%,穿越牛熊")
        lines.append("5. **纪律执行**: 先制定方案→执行→迭代,不情绪化操作")
        lines.append("")

        lines.append("### 三大目标")
        lines.append("")
        lines.append("1. 资金达到100万")
        lines.append("2. 跑赢沪深300(从2025.1.1起)")
        lines.append("3. 涨幅100%(翻倍)")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("**免责声明**: 本报告基于历史数据和技术分析,仅供个人参考,不构成投资建议。投资有风险,入市需谨慎。")
        lines.append("")

        return "\n".join(lines)

    def run_health_check(self, positions: List[Dict]) -> str:
        """运行持仓健康度检查"""
        result = self.health_checker.check_position_health(positions)
        return self.health_checker.format_health_report(result, 'markdown')

    def run_performance_tracking(
        self,
        current_capital: float,
        hs300_current: float,
        current_date: Optional[str] = None
    ) -> str:
        """运行收益追踪"""
        result = self.performance_tracker.track_performance(
            current_capital=current_capital,
            hs300_current=hs300_current,
            hs300_base=self.config['benchmarks']['hs300_base'],
            current_date=current_date
        )
        return self.performance_tracker.format_performance_report(result, 'markdown')

    def run_potential_analysis(self, asset_keys: List[str], current_prices: Dict[str, float]) -> str:
        """运行潜在空间评估"""
        assets = [
            {'asset_key': key, 'current_price': current_prices.get(key, 0)}
            for key in asset_keys
        ]
        result = self.potential_analyzer.analyze_multiple_assets(assets, scenario='all')
        return self.potential_analyzer.format_potential_report(result, 'markdown', single_asset=False)

    def run_monthly_plan(
        self,
        plan_month: str,
        market_data: Dict,
        blogger_insights: Optional[List[str]] = None,
        current_positions: Optional[List[Dict]] = None
    ) -> str:
        """运行月度计划生成"""
        result = self.monthly_plan_generator.generate_monthly_plan(
            plan_month=plan_month,
            market_data=market_data,
            blogger_insights=blogger_insights,
            current_positions=current_positions
        )
        return self.monthly_plan_generator.format_monthly_plan(result, 'markdown')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Russ个人交易策略系统')

    # 报告类型
    parser.add_argument('--full-report', action='store_true', help='生成完整策略报告')
    parser.add_argument('--health-check', action='store_true', help='持仓健康度检查')
    parser.add_argument('--performance', action='store_true', help='收益追踪对比')
    parser.add_argument('--potential', action='store_true', help='潜在空间评估')
    parser.add_argument('--monthly-plan', action='store_true', help='月度计划生成')

    # 参数
    parser.add_argument('--positions', type=str, help='持仓数据JSON文件路径')
    parser.add_argument('--capital', type=float, help='当前资金')
    parser.add_argument('--hs300', type=float, help='沪深300当前点位')
    parser.add_argument('--assets', type=str, help='资产代码,逗号分隔(如: CYBZ,HS300,KECHUANG50)')
    parser.add_argument('--prices', type=str, help='资产价格JSON字符串')
    parser.add_argument('--month', type=str, help='计划月份(格式: YYYY-MM)')
    parser.add_argument('--market-data', type=str, help='市场数据JSON文件路径')

    # 输出选项
    parser.add_argument('--save', type=str, help='保存报告到文件')
    parser.add_argument('--format', type=str, choices=['markdown', 'text'], default='markdown', help='输出格式')

    args = parser.parse_args()

    # 创建运行器
    runner = RussStrategyRunner()

    report = ""

    try:
        # 1. 完整报告
        if args.full_report:
            # 加载数据
            positions = None
            if args.positions:
                with open(args.positions, 'r') as f:
                    positions = json.load(f)

            market_data = None
            if args.market_data:
                with open(args.market_data, 'r') as f:
                    market_data = json.load(f)
            elif args.hs300:
                # 构造简单的市场数据
                market_data = {
                    'indices': {
                        'HS300': {'current': args.hs300}
                    }
                }

            report = runner.run_full_report(
                positions=positions,
                current_capital=args.capital,
                market_data=market_data
            )

        # 2. 持仓健康度检查
        elif args.health_check:
            if not args.positions:
                print("错误: 持仓健康度检查需要提供 --positions 参数")
                sys.exit(1)

            with open(args.positions, 'r') as f:
                positions = json.load(f)

            report = runner.run_health_check(positions)

        # 3. 收益追踪
        elif args.performance:
            if not args.capital or not args.hs300:
                print("错误: 收益追踪需要提供 --capital 和 --hs300 参数")
                sys.exit(1)

            report = runner.run_performance_tracking(
                current_capital=args.capital,
                hs300_current=args.hs300
            )

        # 4. 潜在空间评估
        elif args.potential:
            if not args.assets or not args.prices:
                print("错误: 潜在空间评估需要提供 --assets 和 --prices 参数")
                sys.exit(1)

            asset_keys = args.assets.split(',')
            current_prices = json.loads(args.prices)

            report = runner.run_potential_analysis(asset_keys, current_prices)

        # 5. 月度计划
        elif args.monthly_plan:
            if not args.month or not args.market_data:
                print("错误: 月度计划需要提供 --month 和 --market-data 参数")
                sys.exit(1)

            with open(args.market_data, 'r') as f:
                market_data = json.load(f)

            positions = None
            if args.positions:
                with open(args.positions, 'r') as f:
                    positions = json.load(f)

            report = runner.run_monthly_plan(
                plan_month=args.month,
                market_data=market_data,
                current_positions=positions
            )

        else:
            parser.print_help()
            sys.exit(0)

        # 输出报告
        if args.save:
            # 确保目录存在
            os.makedirs(os.path.dirname(args.save), exist_ok=True)
            with open(args.save, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"报告已保存到: {args.save}")
        else:
            print(report)

    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
