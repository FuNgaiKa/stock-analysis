"""
A股历史牛市分析器 - 使用akshare数据源
支持创业板指、科创50、沪深300等更多指数
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List


class CNBullMarketAnalyzer:
    """A股牛市分析器"""

    def __init__(self):
        """初始化分析器"""
        self.bull_markets = self._define_bull_markets()

    def _define_bull_markets(self) -> List[Dict]:
        """定义A股牛市周期"""
        return [
            {
                "name": "2007年大牛市",
                "start_date": "20060101",
                "end_date": "20071016",
                "background": "股权分置改革,经济高速增长,流动性宽松"
            },
            {
                "name": "2015年杠杆牛市",
                "start_date": "20140701",
                "end_date": "20150612",
                "background": "融资融券扩容,场外配资盛行,互联网金融崛起"
            },
            {
                "name": "2021年结构性牛市",
                "start_date": "20200701",
                "end_date": "20210218",
                "background": "疫后经济复苏,流动性充裕,机构抱团,核心资产行情"
            },
        ]

    def fetch_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取指数数据

        Args:
            symbol: 指数代码 (如 '000001' 表示上证指数)
            start_date: 开始日期 (格式: YYYYMMDD)
            end_date: 结束日期 (格式: YYYYMMDD)
        """
        try:
            print(f"正在获取 {symbol} 数据: {start_date} ~ {end_date}")

            # 使用akshare获取指数数据
            df = ak.stock_zh_index_daily(symbol=symbol)

            if df.empty:
                print(f"  警告: {symbol} 未获取到数据")
                return pd.DataFrame()

            # 筛选日期范围
            df['date'] = pd.to_datetime(df['date'])
            start = pd.to_datetime(start_date, format='%Y%m%d')
            end = pd.to_datetime(end_date, format='%Y%m%d')

            df = df[(df['date'] >= start) & (df['date'] <= end)]

            if df.empty:
                print(f"  警告: {symbol} 在指定日期范围内无数据")
                return pd.DataFrame()

            # 使用收盘价
            df = df.set_index('date')
            df = df.sort_index()

            return df

        except Exception as e:
            print(f"  错误: 获取 {symbol} 数据失败 - {e}")
            return pd.DataFrame()

    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """计算关键指标"""
        if df.empty or 'close' not in df.columns:
            return {}

        close = df['close']

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

        # 年化收益率
        years = len(close) / 252
        annualized_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0

        # 夏普比率
        risk_free_rate = 2.0
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0

        # 胜率
        win_rate = (daily_returns > 0).sum() / len(daily_returns) * 100 if len(daily_returns) > 0 else 0

        return {
            "总收益率(%)": round(total_return, 2),
            "年化收益率(%)": round(annualized_return, 2),
            "最大回撤(%)": round(max_drawdown, 2),
            "最大涨幅(%)": round(max_gain, 2),
            "年化波动率(%)": round(volatility, 2),
            "夏普比率": round(sharpe_ratio, 2),
            "胜率(%)": round(win_rate, 2),
            "交易天数": len(close),
        }

    def analyze_all_bull_markets(self):
        """分析所有牛市"""
        # 定义要分析的指数
        # akshare的指数代码: sh000001=上证, sz399001=深证成指, sz399006=创业板指,
        # sh000300=沪深300, sh000688=科创50
        indices = {
            "sh000001": "上证指数",
            "sz399001": "深证成指",
            "sz399006": "创业板指",
            "sh000300": "沪深300",
            "sh000688": "科创50",
        }

        all_results = []

        for bull_market in self.bull_markets:
            print(f"\n{'='*80}")
            print(f"分析牛市: {bull_market['name']}")
            print(f"时间: {bull_market['start_date']} ~ {bull_market['end_date']}")
            print(f"背景: {bull_market['background']}")
            print(f"{'='*80}\n")

            results = {
                "name": bull_market['name'],
                "start_date": bull_market['start_date'],
                "end_date": bull_market['end_date'],
                "background": bull_market['background'],
                "indices": {}
            }

            for symbol, name in indices.items():
                df = self.fetch_index_data(symbol, bull_market['start_date'], bull_market['end_date'])

                if not df.empty:
                    metrics = self.calculate_metrics(df)
                    results["indices"][name] = metrics
                    print(f"  [OK] {name}: 总收益 {metrics.get('总收益率(%)', 'N/A')}%, "
                          f"最大回撤 {metrics.get('最大回撤(%)', 'N/A')}%")
                else:
                    results["indices"][name] = {}
                    print(f"  [FAIL] {name}: 无数据")

            all_results.append(results)

        return all_results

    def print_summary_table(self, results: List[Dict]):
        """打印汇总表格"""
        print("\n" + "="*120)
        print("A股历史牛市表现汇总")
        print("="*120 + "\n")

        for result in results:
            print(f"【{result['name']}】")
            print(f"时间: {result['start_date']} ~ {result['end_date']}")
            print("-"*120)
            print(f"{'指数':<12} {'总收益率(%)':<12} {'年化收益率(%)':<14} {'最大回撤(%)':<12} "
                  f"{'最大涨幅(%)':<12} {'夏普比率':<10} {'交易天数':<10}")
            print("-"*120)

            for index_name, metrics in result['indices'].items():
                if metrics:
                    print(f"{index_name:<12} {metrics.get('总收益率(%)', 'N/A'):<12} "
                          f"{metrics.get('年化收益率(%)', 'N/A'):<14} {metrics.get('最大回撤(%)', 'N/A'):<12} "
                          f"{metrics.get('最大涨幅(%)', 'N/A'):<12} {metrics.get('夏普比率', 'N/A'):<10} "
                          f"{metrics.get('交易天数', 'N/A'):<10}")

            print()

    def save_report(self, results: List[Dict], filename: str = None):
        """保存分析报告为Markdown格式"""
        if filename is None:
            from pathlib import Path
            # 统一保存到项目根目录的 reports 文件夹
            project_root = Path(__file__).parent.parent.parent
            report_dir = project_root / "reports"
            report_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = report_dir / f"cn_bull_markets_analysis_{timestamp}.md"

        with open(filename, 'w', encoding='utf-8') as f:
            # Markdown 标题
            f.write("# A股历史牛市分析报告\n\n")
            f.write(f"**数据来源**: akshare  \n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n\n")
            f.write("---\n\n")

            # 为每个牛市生成报告
            for idx, result in enumerate(results, 1):
                f.write(f"## {idx}. {result['name']}\n\n")
                f.write(f"**时间周期**: {result['start_date']} ~ {result['end_date']}  \n")
                f.write(f"**市场背景**: {result['background']}  \n\n")

                # Markdown 表格
                if result['indices']:
                    f.write("| 指数 | 总收益率(%) | 年化收益率(%) | 最大回撤(%) | 最大涨幅(%) | 年化波动率(%) | 夏普比率 | 胜率(%) | 交易天数 |\n")
                    f.write("|------|------------|--------------|-----------|-----------|-------------|---------|--------|--------|\n")

                    for index_name, metrics in result['indices'].items():
                        if metrics:
                            f.write(f"| {index_name} | "
                                  f"{metrics.get('总收益率(%)', 'N/A')} | "
                                  f"{metrics.get('年化收益率(%)', 'N/A')} | "
                                  f"{metrics.get('最大回撤(%)', 'N/A')} | "
                                  f"{metrics.get('最大涨幅(%)', 'N/A')} | "
                                  f"{metrics.get('年化波动率(%)', 'N/A')} | "
                                  f"{metrics.get('夏普比率', 'N/A')} | "
                                  f"{metrics.get('胜率(%)', 'N/A')} | "
                                  f"{metrics.get('交易天数', 'N/A')} |\n")
                        else:
                            f.write(f"| {index_name} | 无数据 | - | - | - | - | - | - | - |\n")

                f.write("\n")

            # 添加总结分析
            f.write("---\n\n")
            f.write("## 关键发现\n\n")

            # 找出最大回撤和最高收益
            f.write("### 最大回撤对比\n\n")
            for result in results:
                f.write(f"**{result['name']}**:\n\n")
                for index_name, metrics in result['indices'].items():
                    if metrics:
                        f.write(f"- {index_name}: {metrics.get('最大回撤(%)', 'N/A')}%\n")
                f.write("\n")

            f.write("### 收益率对比\n\n")
            for result in results:
                f.write(f"**{result['name']}**:\n\n")
                for index_name, metrics in result['indices'].items():
                    if metrics:
                        f.write(f"- {index_name}: 总收益 {metrics.get('总收益率(%)', 'N/A')}%, "
                              f"年化 {metrics.get('年化收益率(%)', 'N/A')}%\n")
                f.write("\n")

        print(f"\n>> 报告已保存至: {filename}")


if __name__ == "__main__":
    print("A股历史牛市分析系统 (基于akshare)\n")

    analyzer = CNBullMarketAnalyzer()
    results = analyzer.analyze_all_bull_markets()
    analyzer.print_summary_table(results)
    analyzer.save_report(results)
