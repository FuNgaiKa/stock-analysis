"""
特殊时期市场分析器
分析特朗普执政期、A股牛市等特殊时期的市场表现
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List
import logging

from special_period_provider import SpecialPeriodProvider, SpecialPeriod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpecialPeriodAnalyzer:
    """特殊时期分析器"""

    def __init__(self):
        """初始化分析器"""
        self.provider = SpecialPeriodProvider()

    def fetch_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取指数数据"""
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
        """计算关键指标"""
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

        # 夏普比率
        risk_free_rate = 2.0
        annualized_return = total_return * (252 / len(close))
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0

        # 胜率
        win_rate = (daily_returns > 0).sum() / len(daily_returns) * 100

        # 年化收益率
        years = len(close) / 252
        annualized_return_real = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0

        return {
            "总收益率(%)": round(total_return, 2),
            "年化收益率(%)": round(annualized_return_real, 2),
            "最大回撤(%)": round(max_drawdown, 2),
            "最大涨幅(%)": round(max_gain, 2),
            "年化波动率(%)": round(volatility, 2),
            "夏普比率": round(sharpe_ratio, 2),
            "胜率(%)": round(win_rate, 2),
            "交易天数": len(close),
        }

    def analyze_special_period(self, period: SpecialPeriod, indices: Dict[str, str]) -> Dict:
        """分析特殊时期

        Args:
            period: 特殊时期
            indices: 要分析的指数字典 {代码: 名称}

        Returns:
            分析结果字典
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"分析时期: {period.name}")
        logger.info(f"{'='*80}")

        results = {
            "period_info": period,
            "indices_analysis": {},
        }

        for symbol, name in indices.items():
            logger.info(f"\n分析指数: {name} ({symbol})")

            df = self.fetch_index_data(symbol, period.start_date, period.end_date)

            if not df.empty:
                metrics = self.calculate_metrics(df)
                results["indices_analysis"][symbol] = {
                    "name": name,
                    "metrics": metrics
                }
                logger.info(f"  总收益率: {metrics.get('总收益率(%)', 'N/A')}%")
                logger.info(f"  年化收益率: {metrics.get('年化收益率(%)', 'N/A')}%")
            else:
                results["indices_analysis"][symbol] = {
                    "name": name,
                    "metrics": {}
                }

        return results

    def analyze_trump_periods(self, market: str = "all") -> List[Dict]:
        """分析特朗普执政期"""
        results = []

        # 定义要分析的指数
        if market == "all":
            indices = {
                "^GSPC": "标普500",
                "^IXIC": "纳斯达克",
                "^DJI": "道琼斯",
                "000001.SS": "上证指数",
                "^HSI": "恒生指数",
            }
        elif market == "us":
            indices = {
                "^GSPC": "标普500",
                "^IXIC": "纳斯达克",
                "^DJI": "道琼斯",
            }
        elif market == "cn":
            indices = {
                "000001.SS": "上证指数",
                "399001.SZ": "深证成指",
                "000300.SS": "沪深300",
            }
        elif market == "hk":
            indices = {
                "^HSI": "恒生指数",
                "^HSCE": "恒生国企",
            }
        else:
            indices = {"^GSPC": "标普500"}

        # 分析第一任期
        period1 = self.provider.get_trump_first_term()
        result1 = self.analyze_special_period(period1, indices)
        results.append(result1)

        # 分析第二任期(仅到当前日期)
        period2 = self.provider.get_trump_second_term()
        # 修改结束日期为当前日期
        from datetime import datetime
        period2.end_date = datetime.now().strftime("%Y-%m-%d")
        result2 = self.analyze_special_period(period2, indices)
        results.append(result2)

        return results

    def analyze_cn_bull_markets(self) -> List[Dict]:
        """分析A股历史牛市"""
        results = []

        # A股主要指数
        indices = {
            "000001.SS": "上证指数",
            "399001.SZ": "深证成指",
        }

        # 分析三次牛市
        for bull in self.provider.get_all_cn_bull_markets():
            result = self.analyze_special_period(bull, indices)
            results.append(result)

        return results

    def generate_comparison_table(self, results: List[Dict]) -> str:
        """生成对比表格"""
        summary = "\n" + "=" * 120 + "\n"
        summary += "特殊时期市场表现对比\n"
        summary += "=" * 120 + "\n\n"

        for result in results:
            period_name = result["period_info"].name
            category = result["period_info"].category

            summary += f"\n【{period_name}】 - {category}\n"
            summary += f"时间: {result['period_info'].start_date} ~ {result['period_info'].end_date}\n"
            summary += "-" * 120 + "\n"

            summary += f"{'指数':<15} {'总收益率(%)':<12} {'年化收益率(%)':<14} {'最大回撤(%)':<12} "
            summary += f"{'最大涨幅(%)':<12} {'夏普比率':<10} {'胜率(%)':<10}\n"
            summary += "-" * 120 + "\n"

            for symbol, analysis in result["indices_analysis"].items():
                metrics = analysis["metrics"]
                if metrics:
                    summary += f"{analysis['name']:<15} "
                    summary += f"{metrics.get('总收益率(%)', 'N/A'):<12} "
                    summary += f"{metrics.get('年化收益率(%)', 'N/A'):<14} "
                    summary += f"{metrics.get('最大回撤(%)', 'N/A'):<12} "
                    summary += f"{metrics.get('最大涨幅(%)', 'N/A'):<12} "
                    summary += f"{metrics.get('夏普比率', 'N/A'):<10} "
                    summary += f"{metrics.get('胜率(%)', 'N/A'):<10}\n"

            summary += "\n"

        return summary


if __name__ == "__main__":
    # 测试分析器
    analyzer = SpecialPeriodAnalyzer()

    # 测试特朗普执政期分析
    print("\n分析特朗普执政期...")
    results = analyzer.analyze_trump_periods(market="us")
    print(analyzer.generate_comparison_table(results))
