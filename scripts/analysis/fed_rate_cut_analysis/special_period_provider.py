"""
特殊时期数据提供器
提供特朗普执政期、A股历史牛市等特殊时期的数据
"""
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class SpecialPeriod:
    """特殊时期数据结构"""
    name: str                    # 时期名称
    start_date: str             # 开始日期
    end_date: str               # 结束日期
    category: str               # 类别: 政治周期/牛市周期
    background: str             # 背景描述
    key_events: List[str]       # 关键事件


class SpecialPeriodProvider:
    """特殊时期数据提供器"""

    def __init__(self):
        """初始化数据提供器"""
        self.trump_periods = self._define_trump_periods()
        self.cn_bull_markets = self._define_cn_bull_markets()

    def _define_trump_periods(self) -> List[SpecialPeriod]:
        """定义特朗普执政期"""
        return [
            SpecialPeriod(
                name="特朗普第一任期",
                start_date="2017-01-20",
                end_date="2021-01-20",
                category="政治周期",
                background="美国优先政策,贸易保护主义,减税政策,中美贸易摩擦",
                key_events=[
                    "2017年12月: 税改法案通过",
                    "2018年3月: 中美贸易战开启",
                    "2019年8月: 美联储预防式降息",
                    "2020年3月: 疫情爆发,股市熔断"
                ]
            ),
            SpecialPeriod(
                name="特朗普第二任期",
                start_date="2025-01-20",
                end_date="2029-01-20",
                category="政治周期",
                background="第二次执政,政策延续性,关税政策回归",
                key_events=[
                    "2025年1月: 就职典礼",
                    "待观察: 对华政策调整",
                    "待观察: 能源政策变化"
                ]
            ),
        ]

    def _define_cn_bull_markets(self) -> List[SpecialPeriod]:
        """定义A股历史牛市"""
        return [
            SpecialPeriod(
                name="2007年大牛市",
                start_date="2006-01-01",
                end_date="2007-10-16",
                category="牛市周期",
                background="股权分置改革,经济高速增长,流动性宽松",
                key_events=[
                    "2005年: 股权分置改革启动",
                    "2006年: 上证指数突破2000点",
                    "2007年5月: 上证指数突破4000点",
                    "2007年10月16日: 上证指数见顶6124点"
                ]
            ),
            SpecialPeriod(
                name="2015年杠杆牛市",
                start_date="2014-07-01",
                end_date="2015-06-12",
                category="牛市周期",
                background="融资融券扩容,场外配资盛行,互联网金融崛起",
                key_events=[
                    "2014年下半年: 牛市启动",
                    "2015年4月: 上证指数突破4000点",
                    "2015年6月12日: 上证指数见顶5178点",
                    "2015年6月15日: 股灾开始"
                ]
            ),
            SpecialPeriod(
                name="2021年结构性牛市",
                start_date="2020-07-01",
                end_date="2021-02-18",
                category="牛市周期",
                background="疫后经济复苏,流动性充裕,机构抱团,核心资产行情",
                key_events=[
                    "2020年7月: 牛市启动",
                    "2020年12月: 上证指数突破3500点",
                    "2021年2月18日: 上证指数见顶3731点",
                    "2021年春节后: 抱团瓦解,调整开始"
                ]
            ),
        ]

    def get_all_trump_periods(self) -> List[SpecialPeriod]:
        """获取所有特朗普执政期"""
        return self.trump_periods

    def get_trump_first_term(self) -> SpecialPeriod:
        """获取特朗普第一任期"""
        return self.trump_periods[0]

    def get_trump_second_term(self) -> SpecialPeriod:
        """获取特朗普第二任期"""
        return self.trump_periods[1]

    def get_all_cn_bull_markets(self) -> List[SpecialPeriod]:
        """获取所有A股牛市"""
        return self.cn_bull_markets

    def get_cn_bull_by_year(self, year: int) -> SpecialPeriod:
        """根据年份获取A股牛市

        Args:
            year: 牛市年份 (2007, 2015, 2021)
        """
        for bull in self.cn_bull_markets:
            if str(year) in bull.name:
                return bull
        raise ValueError(f"未找到 {year} 年的牛市数据")

    def get_special_period_summary(self, category: str = "all") -> str:
        """获取特殊时期摘要信息

        Args:
            category: 类别 ('all', 'trump', 'bull')
        """
        summary = "=" * 80 + "\n"
        summary += "特殊时期数据概览\n"
        summary += "=" * 80 + "\n\n"

        if category in ["all", "trump"]:
            summary += "【特朗普执政期】\n"
            summary += "-" * 80 + "\n"
            for i, period in enumerate(self.trump_periods, 1):
                summary += f"\n{i}. {period.name}\n"
                summary += f"   时间: {period.start_date} ~ {period.end_date}\n"
                summary += f"   背景: {period.background}\n"
                summary += f"   关键事件:\n"
                for event in period.key_events:
                    summary += f"     - {event}\n"

        if category in ["all", "bull"]:
            summary += "\n【A股历史牛市】\n"
            summary += "-" * 80 + "\n"
            for i, period in enumerate(self.cn_bull_markets, 1):
                summary += f"\n{i}. {period.name}\n"
                summary += f"   时间: {period.start_date} ~ {period.end_date}\n"
                summary += f"   背景: {period.background}\n"
                summary += f"   关键事件:\n"
                for event in period.key_events:
                    summary += f"     - {event}\n"

        return summary


if __name__ == "__main__":
    # 测试数据提供器
    provider = SpecialPeriodProvider()
    print(provider.get_special_period_summary())
