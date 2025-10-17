"""
美联储降息周期数据提供器
提供历史降息周期的时间范围、背景信息和市场指数代码
"""
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime


@dataclass
class RateCutCycle:
    """降息周期数据结构"""
    name: str                    # 周期名称
    start_date: str             # 开始日期
    end_date: str               # 结束日期
    start_rate: float           # 起始利率(%)
    end_rate: float             # 结束利率(%)
    total_cuts: int             # 降息次数
    background: str             # 经济背景
    cycle_type: str             # 周期类型: 预防式/纾困式


class FedRateCutDataProvider:
    """美联储降息周期数据提供器"""

    def __init__(self):
        """初始化数据提供器"""
        self.cycles = self._define_cycles()
        self.indices = self._define_indices()

    def _define_cycles(self) -> List[RateCutCycle]:
        """定义历史降息周期"""
        return [
            RateCutCycle(
                name="1995年软着陆",
                start_date="1995-07-06",
                end_date="1996-01-31",
                start_rate=6.0,
                end_rate=5.25,
                total_cuts=3,
                background="经济温和放缓,主动预防衰退,实现软着陆",
                cycle_type="预防式"
            ),
            RateCutCycle(
                name="2001年互联网泡沫",
                start_date="2001-01-03",
                end_date="2003-06-25",
                start_rate=6.5,
                end_rate=1.0,
                total_cuts=13,
                background="互联网泡沫破裂,经济衰退,911事件冲击",
                cycle_type="纾困式"
            ),
            RateCutCycle(
                name="2007-2008年金融危机",
                start_date="2007-09-18",
                end_date="2008-12-16",
                start_rate=5.25,
                end_rate=0.25,
                total_cuts=10,
                background="次贷危机引发全球金融危机,雷曼兄弟破产",
                cycle_type="纾困式"
            ),
            RateCutCycle(
                name="2019年预防式降息",
                start_date="2019-08-01",
                end_date="2020-03-16",
                start_rate=2.25,
                end_rate=0.25,
                total_cuts=3,
                background="贸易摩擦担忧,全球经济放缓,后期疫情爆发",
                cycle_type="预防式"
            ),
            RateCutCycle(
                name="2024年软着陆降息",
                start_date="2024-09-19",
                end_date="2024-12-31",  # 周期仍在进行
                start_rate=5.5,
                end_rate=4.5,
                total_cuts=3,
                background="通胀回落,经济软着陆,就业市场稳定",
                cycle_type="预防式"
            ),
        ]

    def _define_indices(self) -> Dict[str, Dict[str, str]]:
        """定义要分析的市场指数

        Returns:
            包含指数代码和名称的字典
        """
        return {
            # 美股指数
            "us": {
                "^GSPC": "标普500",
                "^IXIC": "纳斯达克",
                "^DJI": "道琼斯",
            },
            # A股指数
            "cn": {
                "000001.SS": "上证指数",
                "399001.SZ": "深证成指",
                "399006.SZ": "创业板指",
                "000300.SS": "沪深300",
            },
            # 港股指数
            "hk": {
                "^HSI": "恒生指数",
                "^HSCE": "恒生国企",
                "HSTECH.HK": "恒生科技",
            }
        }

    def get_all_cycles(self) -> List[RateCutCycle]:
        """获取所有降息周期"""
        return self.cycles

    def get_cycle_by_name(self, name: str) -> RateCutCycle:
        """根据名称获取周期"""
        for cycle in self.cycles:
            if cycle.name == name:
                return cycle
        raise ValueError(f"未找到名为 '{name}' 的降息周期")

    def get_recent_cycles(self, n: int = 2) -> List[RateCutCycle]:
        """获取最近N个降息周期"""
        return self.cycles[-n:]

    def get_current_cycle(self) -> RateCutCycle:
        """获取当前降息周期(2024年)"""
        return self.cycles[-1]

    def get_all_indices(self) -> Dict[str, Dict[str, str]]:
        """获取所有市场指数"""
        return self.indices

    def get_indices_by_market(self, market: str) -> Dict[str, str]:
        """根据市场获取指数

        Args:
            market: 市场代码 ('us', 'cn', 'hk')
        """
        if market not in self.indices:
            raise ValueError(f"不支持的市场: {market}")
        return self.indices[market]

    def get_cycle_summary(self) -> str:
        """获取降息周期摘要信息"""
        summary = "=" * 60 + "\n"
        summary += "美联储历史降息周期概览\n"
        summary += "=" * 60 + "\n\n"

        for i, cycle in enumerate(self.cycles, 1):
            summary += f"{i}. {cycle.name}\n"
            summary += f"   时间: {cycle.start_date} ~ {cycle.end_date}\n"
            summary += f"   利率: {cycle.start_rate}% → {cycle.end_rate}%\n"
            summary += f"   降息次数: {cycle.total_cuts}次\n"
            summary += f"   类型: {cycle.cycle_type}\n"
            summary += f"   背景: {cycle.background}\n\n"

        return summary

    def get_date_range_for_cycle(self, cycle: RateCutCycle,
                                  pre_days: int = 90,
                                  post_days: int = 180) -> Dict[str, str]:
        """获取降息周期的扩展日期范围(包含前后对比期)

        Args:
            cycle: 降息周期
            pre_days: 降息前天数
            post_days: 降息后天数

        Returns:
            包含各阶段日期的字典
        """
        from datetime import timedelta

        start = datetime.strptime(cycle.start_date, "%Y-%m-%d")
        end = datetime.strptime(cycle.end_date, "%Y-%m-%d")

        pre_start = start - timedelta(days=pre_days)
        post_end = end + timedelta(days=post_days)

        return {
            "pre_start": pre_start.strftime("%Y-%m-%d"),
            "cycle_start": cycle.start_date,
            "cycle_end": cycle.end_date,
            "post_end": post_end.strftime("%Y-%m-%d"),
        }


if __name__ == "__main__":
    # 测试数据提供器
    provider = FedRateCutDataProvider()

    print(provider.get_cycle_summary())

    print("\n支持的市场指数:")
    print("-" * 60)
    for market, indices in provider.get_all_indices().items():
        print(f"\n{market.upper()}市场:")
        for code, name in indices.items():
            print(f"  {code}: {name}")
