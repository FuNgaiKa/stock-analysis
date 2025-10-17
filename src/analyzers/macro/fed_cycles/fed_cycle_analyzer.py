"""
美联储降息周期市场分析器
分析不同降息周期下各市场指数的表现
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging

from cycle_data_provider import FedRateCutDataProvider, RateCutCycle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FedCycleAnalyzer:
    """美联储降息周期分析器"""

    def __init__(self):
        """初始化分析器"""
        self.provider = FedRateCutDataProvider()

    def fetch_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取指数数据

        Args:
            symbol: 指数代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含价格数据的DataFrame
        """
        try:
            logger.info(f"正在获取 {symbol} 数据: {start_date} ~ {end_date}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)

            if df.empty:
                logger.warning(f"{symbol} 未获取到数据")
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.error(f"获取 {symbol} 数据失败: {e}")
            return pd.DataFrame()

    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """计算关键指标

        Args:
            df: 价格数据

        Returns:
            包含各项指标的字典
        """
        if df.empty:
            return {}

        close = df['Close']

        # 基础收益率
        total_return = ((close.iloc[-1] - close.iloc[0]) / close.iloc[0]) * 100

        # 最大涨幅和最大回撤
        cummax = close.cummax()
        drawdown = ((close - cummax) / cummax) * 100
        max_drawdown = drawdown.min()

        running_min = close.cummin()
        gain_from_min = ((close - running_min) / running_min) * 100
        max_gain = gain_from_min.max()

        # 波动率(年化)
        daily_returns = close.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100

        # 夏普比率(假设无风险利率2%)
        risk_free_rate = 2.0
        annualized_return = total_return * (252 / len(close))
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0

        # 胜率(上涨天数比例)
        win_rate = (daily_returns > 0).sum() / len(daily_returns) * 100

        return {
            "总收益率(%)": round(total_return, 2),
            "最大回撤(%)": round(max_drawdown, 2),
            "最大涨幅(%)": round(max_gain, 2),
            "年化波动率(%)": round(volatility, 2),
            "夏普比率": round(sharpe_ratio, 2),
            "胜率(%)": round(win_rate, 2),
            "交易天数": len(close),
        }

    def analyze_cycle(self, cycle: RateCutCycle, market: str = "all") -> Dict:
        """分析单个降息周期

        Args:
            cycle: 降息周期
            market: 市场代码 ('us', 'cn', 'hk', 'all')

        Returns:
            分析结果字典
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"分析降息周期: {cycle.name}")
        logger.info(f"{'='*60}")

        # 获取日期范围
        date_range = self.provider.get_date_range_for_cycle(cycle)

        results = {
            "cycle_info": cycle,
            "date_range": date_range,
            "indices_analysis": {},
        }

        # 选择要分析的市场
        if market == "all":
            indices = self.provider.get_all_indices()
            all_indices = {}
            for mkt, idx in indices.items():
                all_indices.update(idx)
        else:
            all_indices = self.provider.get_indices_by_market(market)

        # 分析各个阶段
        stages = {
            "降息前90天": (date_range["pre_start"], date_range["cycle_start"]),
            "降息周期中": (date_range["cycle_start"], date_range["cycle_end"]),
            "降息后180天": (date_range["cycle_end"], date_range["post_end"]),
            "完整周期": (date_range["pre_start"], date_range["post_end"]),
        }

        for symbol, name in all_indices.items():
            logger.info(f"\n分析指数: {name} ({symbol})")
            results["indices_analysis"][symbol] = {
                "name": name,
                "stages": {}
            }

            for stage_name, (start, end) in stages.items():
                df = self.fetch_index_data(symbol, start, end)

                if not df.empty:
                    metrics = self.calculate_metrics(df)
                    results["indices_analysis"][symbol]["stages"][stage_name] = metrics
                    logger.info(f"  {stage_name}: 收益率 {metrics.get('总收益率(%)', 'N/A')}%")
                else:
                    results["indices_analysis"][symbol]["stages"][stage_name] = {}

        return results

    def analyze_all_cycles(self, market: str = "all") -> List[Dict]:
        """分析所有降息周期

        Args:
            market: 市场代码 ('us', 'cn', 'hk', 'all')

        Returns:
            所有周期的分析结果列表
        """
        cycles = self.provider.get_all_cycles()
        all_results = []

        for cycle in cycles:
            result = self.analyze_cycle(cycle, market)
            all_results.append(result)

        return all_results

    def compare_cycles(self, results: List[Dict]) -> pd.DataFrame:
        """对比不同降息周期的表现

        Args:
            results: 分析结果列表

        Returns:
            对比结果DataFrame
        """
        comparison_data = []

        for result in results:
            cycle_name = result["cycle_info"].name
            cycle_type = result["cycle_info"].cycle_type

            for symbol, analysis in result["indices_analysis"].items():
                index_name = analysis["name"]

                # 提取降息周期中的指标
                cycle_metrics = analysis["stages"].get("降息周期中", {})

                if cycle_metrics:
                    row = {
                        "降息周期": cycle_name,
                        "周期类型": cycle_type,
                        "指数": index_name,
                        "指数代码": symbol,
                        **cycle_metrics
                    }
                    comparison_data.append(row)

        df = pd.DataFrame(comparison_data)
        return df

    def analyze_pre_cut_performance(self, results: List[Dict]) -> Dict:
        """分析首次降息前的市场表现

        Args:
            results: 分析结果列表

        Returns:
            首次降息前表现统计
        """
        pre_cut_data = []

        for result in results:
            cycle = result["cycle_info"]

            for symbol, analysis in result["indices_analysis"].items():
                pre_metrics = analysis["stages"].get("降息前90天", {})
                cycle_metrics = analysis["stages"].get("降息周期中", {})

                if pre_metrics and cycle_metrics:
                    pre_cut_data.append({
                        "降息周期": cycle.name,
                        "周期类型": cycle.cycle_type,
                        "指数": analysis["name"],
                        "降息前90天收益(%)": pre_metrics.get("总收益率(%)", 0),
                        "降息周期收益(%)": cycle_metrics.get("总收益率(%)", 0),
                        "降息幅度": cycle.start_rate - cycle.end_rate,
                        "降息次数": cycle.total_cuts,
                    })

        return pd.DataFrame(pre_cut_data)

    def generate_summary_table(self, results: List[Dict]) -> str:
        """生成摘要表格

        Args:
            results: 分析结果列表

        Returns:
            格式化的摘要文本
        """
        df = self.compare_cycles(results)

        if df.empty:
            return "无数据可显示"

        summary = "\n" + "=" * 120 + "\n"
        summary += "美联储降息周期市场表现对比\n"
        summary += "=" * 120 + "\n\n"

        # 按降息周期分组
        for cycle_name in df["降息周期"].unique():
            cycle_df = df[df["降息周期"] == cycle_name]
            cycle_type = cycle_df["周期类型"].iloc[0]

            summary += f"\n【{cycle_name}】 - {cycle_type}\n"
            summary += "-" * 120 + "\n"

            # 格式化输出
            summary += f"{'指数':<15} {'总收益率(%)':<12} {'最大回撤(%)':<12} {'最大涨幅(%)':<12} "
            summary += f"{'波动率(%)':<12} {'夏普比率':<10} {'胜率(%)':<10}\n"
            summary += "-" * 120 + "\n"

            for _, row in cycle_df.iterrows():
                summary += f"{row['指数']:<15} "
                summary += f"{row.get('总收益率(%)', 'N/A'):<12} "
                summary += f"{row.get('最大回撤(%)', 'N/A'):<12} "
                summary += f"{row.get('最大涨幅(%)', 'N/A'):<12} "
                summary += f"{row.get('年化波动率(%)', 'N/A'):<12} "
                summary += f"{row.get('夏普比率', 'N/A'):<10} "
                summary += f"{row.get('胜率(%)', 'N/A'):<10}\n"

            summary += "\n"

        return summary

    def generate_enhanced_report(self, results: List[Dict]) -> str:
        """生成增强版分析报告

        包括：
        1. 基础市场表现
        2. 首次降息前后对比
        3. 降息幅度分析
        4. 预防式vs纾困式对比

        Args:
            results: 分析结果列表

        Returns:
            完整报告文本
        """
        report = "\n" + "=" * 100 + "\n"
        report += "美联储降息周期深度分析报告\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "=" * 100 + "\n\n"

        # 1. 基础表现对比
        report += self.generate_summary_table(results)

        # 2. 降息周期对比表
        report += "\n" + "=" * 100 + "\n"
        report += "降息周期对比 (降息幅度 & 市场表现)\n"
        report += "=" * 100 + "\n\n"

        cycle_comparison = []
        for result in results:
            cycle = result["cycle_info"]

            # 计算美股平均表现
            us_indices = ["^GSPC", "^IXIC", "^DJI"]
            total_returns = []
            for symbol in us_indices:
                if symbol in result["indices_analysis"]:
                    metrics = result["indices_analysis"][symbol]["stages"].get("降息周期中", {})
                    ret = metrics.get("总收益率(%)", None)
                    if ret is not None:
                        total_returns.append(ret)

            avg_return = sum(total_returns) / len(total_returns) if total_returns else 0

            cycle_comparison.append({
                "周期": cycle.name,
                "类型": cycle.cycle_type,
                "起始利率": f"{cycle.start_rate}%",
                "结束利率": f"{cycle.end_rate}%",
                "降息幅度": f"{cycle.start_rate - cycle.end_rate}%",
                "降息次数": cycle.total_cuts,
                "美股平均收益": f"{avg_return:.2f}%",
            })

        cycle_df = pd.DataFrame(cycle_comparison)
        report += cycle_df.to_string(index=False) + "\n\n"

        # 3. 首次降息前后市场表现
        report += "\n" + "=" * 100 + "\n"
        report += "首次降息前90天 vs 降息周期中 - 市场表现对比\n"
        report += "=" * 100 + "\n\n"

        pre_cut_df = self.analyze_pre_cut_performance(results)
        if not pre_cut_df.empty:
            report += f"{'周期':<20} {'类型':<10} {'指数':<12} {'降息前90天(%)':<15} {'降息周期中(%)':<15} {'降息幅度':<10}\n"
            report += "-" * 100 + "\n"
            for _, row in pre_cut_df.iterrows():
                report += f"{row['降息周期']:<20} {row['周期类型']:<10} {row['指数']:<12} "
                report += f"{row['降息前90天收益(%)']:>14.2f} {row['降息周期收益(%)']:>14.2f} "
                report += f"{row['降息幅度']:>9.2f}%\n"

        # 4. 关键发现总结
        report += "\n\n" + "=" * 100 + "\n"
        report += "关键发现总结\n"
        report += "=" * 100 + "\n\n"

        # 按类型分组统计
        preventive = pre_cut_df[pre_cut_df["周期类型"] == "预防式"]
        crisis = pre_cut_df[pre_cut_df["周期类型"] == "纾困式"]

        if not preventive.empty:
            report += "【预防式降息】：\n"
            report += f"  - 平均降息幅度: {preventive['降息幅度'].mean():.2f}%\n"
            report += f"  - 降息前90天平均收益: {preventive['降息前90天收益(%)'].mean():.2f}%\n"
            report += f"  - 降息周期中平均收益: {preventive['降息周期收益(%)'].mean():.2f}%\n"
            report += f"  - 特征: 市场提前反应，降息后继续上涨\n\n"

        if not crisis.empty:
            report += "【纾困式降息】：\n"
            report += f"  - 平均降息幅度: {crisis['降息幅度'].mean():.2f}%\n"
            report += f"  - 降息前90天平均收益: {crisis['降息前90天收益(%)'].mean():.2f}%\n"
            report += f"  - 降息周期中平均收益: {crisis['降息周期收益(%)'].mean():.2f}%\n"
            report += f"  - 特征: 降息前已大跌，降息也难止跌\n\n"

        report += "\n投资启示:\n"
        report += "  1. 预防式降息：降息幅度小(0.75-2%),市场通常上涨\n"
        report += "  2. 纾困式降息：降息幅度大(5-5.5%),市场往往继续下跌\n"
        report += "  3. 关键判断：观察降息前市场是否已大幅下跌\n"

        return report

    def get_best_performers(self, results: List[Dict], metric: str = "总收益率(%)") -> pd.DataFrame:
        """获取表现最佳的市场/周期组合

        Args:
            results: 分析结果列表
            metric: 评价指标

        Returns:
            排序后的DataFrame
        """
        df = self.compare_cycles(results)

        if df.empty or metric not in df.columns:
            return pd.DataFrame()

        # 按指标排序
        sorted_df = df.sort_values(by=metric, ascending=False)

        return sorted_df[["降息周期", "指数", metric, "最大回撤(%)", "夏普比率"]]


if __name__ == "__main__":
    # 测试分析器
    analyzer = FedCycleAnalyzer()

    # 分析最近一个周期(2024年)
    current_cycle = analyzer.provider.get_current_cycle()
    result = analyzer.analyze_cycle(current_cycle, market="us")

    print("\n单周期分析完成!")
