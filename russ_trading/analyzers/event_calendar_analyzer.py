#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件日历分析器
Event Calendar Analyzer

提前布局重要事件窗口,比肩投研级别的事件驱动分析
"""

import yaml
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


class EventCalendarAnalyzer:
    """
    事件日历分析器

    功能:
    - 加载事件日历配置
    - 获取未来N天的重要事件
    - 匹配与当前持仓相关的事件
    - 生成事件应对建议

    使用方法:

    ```python
    from russ_trading.analyzers.event_calendar_analyzer import EventCalendarAnalyzer

    eca = EventCalendarAnalyzer()

    # 获取未来7天的事件
    positions = [
        {'asset_name': '恒生科技ETF', 'current_ratio': 0.30},
        {'asset_name': '证券ETF', 'current_ratio': 0.40}
    ]

    upcoming_events = eca.get_upcoming_events(days=7, positions=positions)
    report = eca.format_event_calendar_report(upcoming_events, positions)

    print(report)
    ```
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化事件日历分析器

        Args:
            config_path: 事件日历配置文件路径
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'data' / 'event_calendar.yaml'

        self.events = self._load_events(config_path)

    def _load_events(self, config_path: Path) -> List[Dict]:
        """
        加载事件日历

        Args:
            config_path: 配置文件路径

        Returns:
            事件列表
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('events', [])
        except Exception as e:
            print(f"⚠️ 加载事件日历失败: {e}")
            return []

    def get_upcoming_events(
        self,
        days: int = 7,
        positions: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        获取未来N天的重要事件

        Args:
            days: 未来天数 (默认7天)
            positions: 当前持仓列表 (用于匹配相关事件)

        Returns:
            相关事件列表

        示例:
            >>> eca = EventCalendarAnalyzer()
            >>> positions = [{'asset_name': '证券ETF', 'current_ratio': 0.40}]
            >>> events = eca.get_upcoming_events(days=7, positions=positions)
            >>> print(f"未来7天有{len(events)}个相关事件")
        """
        today = datetime.now().date()
        end_date = today + timedelta(days=days)

        upcoming_events = []

        for event in self.events:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()

            if today <= event_date <= end_date:
                # 如果有持仓,只返回相关事件
                if positions is not None:
                    affected_assets = event.get('affected_assets', [])
                    position_names = [p.get('asset_name', '') for p in positions]

                    # 检查是否有交集
                    if not any(asset in ' '.join(position_names) for asset in affected_assets):
                        continue

                upcoming_events.append(event)

        # 按日期排序
        upcoming_events.sort(key=lambda x: x['date'])

        return upcoming_events

    def get_all_upcoming_events(self, days: int = 30) -> List[Dict]:
        """
        获取未来N天的所有事件 (不考虑持仓过滤)

        Args:
            days: 未来天数 (默认30天)

        Returns:
            所有事件列表
        """
        today = datetime.now().date()
        end_date = today + timedelta(days=days)

        upcoming_events = []

        for event in self.events:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()

            if today <= event_date <= end_date:
                upcoming_events.append(event)

        # 按日期排序
        upcoming_events.sort(key=lambda x: x['date'])

        return upcoming_events

    def format_event_calendar_report(
        self,
        upcoming_events: List[Dict],
        positions: Optional[List[Dict]] = None
    ) -> str:
        """
        格式化事件日历报告

        Args:
            upcoming_events: 即将发生的事件列表
            positions: 当前持仓列表

        Returns:
            Markdown格式报告
        """
        if not upcoming_events:
            return "### 📅 本周重要事件\n\n暂无重要事件影响当前持仓。\n\n"

        lines = []
        lines.append("### 📅 本周重要事件")
        lines.append("")

        for i, event in enumerate(upcoming_events, 1):
            event_date = event['date']
            event_name = event['event']
            event_type = event['type']
            impact_level = event['impact_level']
            markets = ', '.join(event.get('markets', []))
            affected_assets = event.get('affected_assets', [])
            notes = event.get('notes', '')

            # 历史影响
            historical_impact = ""
            if 'historical_volatility' in event:
                vol = event['historical_volatility'] * 100
                historical_impact = f"历史平均波动±{vol:.1f}%"
            elif 'historical_return' in event:
                ret = event['historical_return'] * 100
                historical_impact = f"历史前3天平均涨{ret:.1f}%"

            # 持仓暴露
            exposure = ""
            if positions and affected_assets:
                for pos in positions:
                    if any(asset in pos.get('asset_name', '') for asset in affected_assets):
                        exposure = f"你持有{pos['asset_name']}{pos.get('current_ratio',0)*100:.0f}%,高度相关"
                        break

            # 建议
            suggestion = self._generate_event_suggestion(event, positions)

            # 影响程度emoji
            if impact_level == '高':
                impact_emoji = '🔴 高'
            elif impact_level == '中':
                impact_emoji = '🟡 中'
            else:
                impact_emoji = '🟢 低'

            # 格式化输出
            lines.append(f"#### {i}. {event_date} {event_name}")
            lines.append(f"- **事件类型**: {event_type}")
            lines.append(f"- **影响市场**: {markets}")
            lines.append(f"- **影响程度**: {impact_emoji}")
            if historical_impact:
                lines.append(f"- **历史影响**: {historical_impact}")
            if exposure:
                lines.append(f"- **持仓暴露**: {exposure}")
            if suggestion:
                lines.append(f"- **建议**: {suggestion}")
            if notes:
                lines.append(f"- **备注**: {notes}")
            lines.append("")

        # 风险提示
        high_impact_count = sum(1 for e in upcoming_events if e.get('impact_level') == '高')
        if high_impact_count > 0:
            lines.append(f"**⚠️ 风险提示**: 本周有{high_impact_count}个高影响事件,建议预留5-10%现金应对波动。")
            lines.append("")

        return '\n'.join(lines)

    def _generate_event_suggestion(
        self, event: Dict, positions: Optional[List[Dict]]
    ) -> str:
        """
        生成事件应对建议

        Args:
            event: 事件信息
            positions: 当前持仓

        Returns:
            建议文本
        """
        impact_level = event.get('impact_level', '中')
        event_type = event['type']

        # 根据事件类型和影响程度生成建议
        if impact_level == '高':
            if event_type == '货币政策':
                return "降低相关标的至25%,预留5%现金应对波动"
            elif event_type == '财报':
                # 财报事件通常有正面预期
                if 'historical_return' in event and event['historical_return'] > 0:
                    return "关注业绩预告,可适当加仓至45%"
                else:
                    return "密切关注业绩预告,谨慎操作"
            elif event_type == '政策':
                return "政策窗口期,预留现金观望,不急于加仓"
            elif event_type == '宏观数据':
                return "关注数据公布,预留现金应对波动"
            else:
                return "密切关注,做好应对准备"
        elif impact_level == '中':
            return "观望为主,不调整仓位"
        else:
            return "影响较小,正常持仓"


if __name__ == '__main__':
    """测试事件日历分析器"""
    print("\n" + "="*60)
    print("事件日历分析器测试")
    print("="*60)

    # 初始化分析器
    eca = EventCalendarAnalyzer()

    print(f"\n加载事件数: {len(eca.events)}个")

    # 测试1: 获取所有未来30天的事件
    print("\n" + "-"*60)
    print("测试1: 未来30天所有事件")
    print("-"*60)

    all_events = eca.get_all_upcoming_events(days=30)
    print(f"未来30天共有{len(all_events)}个事件")

    for event in all_events[:3]:  # 只显示前3个
        print(f"  - {event['date']}: {event['event']} ({event['type']}, {event['impact_level']})")

    # 测试2: 获取与持仓相关的事件
    print("\n" + "-"*60)
    print("测试2: 与持仓相关的事件")
    print("-"*60)

    positions = [
        {'asset_name': '恒生科技ETF', 'current_ratio': 0.30},
        {'asset_name': '证券ETF', 'current_ratio': 0.40}
    ]

    print(f"\n当前持仓:")
    for pos in positions:
        print(f"  - {pos['asset_name']}: {pos['current_ratio']*100:.0f}%")

    upcoming_events = eca.get_upcoming_events(days=60, positions=positions)
    print(f"\n未来60天与持仓相关的事件: {len(upcoming_events)}个")

    # 测试3: 生成事件报告
    print("\n" + "-"*60)
    print("测试3: 事件日历报告")
    print("-"*60)

    report = eca.format_event_calendar_report(upcoming_events, positions)
    print(report)

    print("\n" + "="*60)
    print("✅ 事件日历分析器测试完成!")
    print("="*60)
