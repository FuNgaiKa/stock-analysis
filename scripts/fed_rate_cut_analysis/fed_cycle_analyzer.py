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
