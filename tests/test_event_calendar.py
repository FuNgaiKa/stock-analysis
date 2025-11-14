#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件日历分析器单元测试
不依赖pytest,直接运行测试
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from russ_trading.analyzers.event_calendar_analyzer import EventCalendarAnalyzer


def test_event_loading():
    """测试事件加载"""
    print("\n" + "="*60)
    print("测试1: 事件加载")
    print("="*60)

    eca = EventCalendarAnalyzer()

    print(f"加载事件数: {len(eca.events)}个")

    # 验证事件列表不为空
    assert len(eca.events) > 0, "事件列表不应为空"

    # 验证事件格式
    for event in eca.events:
        assert 'date' in event, "事件应包含日期"
        assert 'event' in event, "事件应包含名称"
        assert 'type' in event, "事件应包含类型"
        assert 'impact_level' in event, "事件应包含影响级别"

    print(f"✅ 成功加载{len(eca.events)}个事件")

    # 显示前3个事件
    print("\n前3个事件:")
    for i, event in enumerate(eca.events[:3], 1):
        print(f"  {i}. {event['date']}: {event['event']} ({event['type']}, {event['impact_level']})")

    print("\n✅ 事件加载测试通过!")
    return True


def test_get_upcoming_events():
    """测试获取未来事件"""
    print("\n" + "="*60)
    print("测试2: 获取未来事件")
    print("="*60)

    eca = EventCalendarAnalyzer()

    # 获取未来30天的所有事件
    all_events = eca.get_all_upcoming_events(days=30)

    print(f"未来30天所有事件: {len(all_events)}个")

    # 验证事件按日期排序
    if len(all_events) > 1:
        for i in range(len(all_events)-1):
            date1 = datetime.strptime(all_events[i]['date'], '%Y-%m-%d')
            date2 = datetime.strptime(all_events[i+1]['date'], '%Y-%m-%d')
            assert date1 <= date2, "事件应按日期排序"

    print("✅ 事件按日期正确排序")

    # 验证日期在未来30天内
    today = datetime.now().date()
    end_date = today + timedelta(days=30)

    for event in all_events:
        event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
        assert today <= event_date <= end_date, f"事件日期{event_date}应在未来30天内"

    print("✅ 所有事件日期都在未来30天内")

    print("\n✅ 获取未来事件测试通过!")
    return True


def test_filter_by_positions():
    """测试按持仓过滤事件"""
    print("\n" + "="*60)
    print("测试3: 按持仓过滤事件")
    print("="*60)

    eca = EventCalendarAnalyzer()

    # 模拟持仓
    positions = [
        {'asset_name': '证券ETF', 'current_ratio': 0.40}
    ]

    print("当前持仓:")
    for pos in positions:
        print(f"  - {pos['asset_name']}: {pos['current_ratio']*100:.0f}%")

    # 获取相关事件
    related_events = eca.get_upcoming_events(days=60, positions=positions)

    print(f"\n与持仓相关的事件: {len(related_events)}个")

    # 验证所有事件都与持仓相关
    for event in related_events:
        affected_assets = event.get('affected_assets', [])
        print(f"  - {event['date']}: {event['event']}")
        print(f"    影响资产: {', '.join(affected_assets)}")

        # 验证至少有一个受影响资产与持仓匹配
        assert any('证券ETF' in asset for asset in affected_assets), \
            f"事件{event['event']}应与持仓相关"

    print("\n✅ 按持仓过滤事件测试通过!")
    return True


def test_event_report_format():
    """测试事件报告格式"""
    print("\n" + "="*60)
    print("测试4: 事件报告格式")
    print("="*60)

    eca = EventCalendarAnalyzer()

    positions = [
        {'asset_name': '恒生科技ETF', 'current_ratio': 0.30},
        {'asset_name': '证券ETF', 'current_ratio': 0.40}
    ]

    upcoming_events = eca.get_upcoming_events(days=60, positions=positions)

    report = eca.format_event_calendar_report(upcoming_events, positions)

    print("\n生成的报告:")
    print("-" * 60)
    print(report)
    print("-" * 60)

    # 验证报告包含关键元素
    assert '📅' in report, "报告应包含日历emoji"
    assert '重要事件' in report, "报告应包含'重要事件'标题"

    if upcoming_events:
        assert '事件类型' in report, "报告应包含事件类型"
        assert '影响市场' in report, "报告应包含影响市场"
        assert '影响程度' in report, "报告应包含影响程度"

    print("\n✅ 事件报告格式测试通过!")
    return True


def test_event_suggestion():
    """测试事件建议生成"""
    print("\n" + "="*60)
    print("测试5: 事件建议生成")
    print("="*60)

    eca = EventCalendarAnalyzer()

    # 测试不同影响级别的建议
    test_events = [
        {
            'type': '货币政策',
            'impact_level': '高',
            'event': '测试高影响货币政策事件'
        },
        {
            'type': '财报',
            'impact_level': '中',
            'event': '测试中影响财报事件'
        },
        {
            'type': '宏观数据',
            'impact_level': '低',
            'event': '测试低影响宏观事件'
        }
    ]

    print("\n测试建议生成:")
    for event in test_events:
        suggestion = eca._generate_event_suggestion(event, None)
        print(f"  {event['impact_level']}影响{event['type']}: {suggestion}")

        # 验证建议不为空
        assert suggestion, f"{event['event']}应该有建议"

    print("\n✅ 事件建议生成测试通过!")
    return True


def test_empty_positions():
    """测试无持仓情况"""
    print("\n" + "="*60)
    print("测试6: 无持仓情况")
    print("="*60)

    eca = EventCalendarAnalyzer()

    # 无持仓时获取事件
    upcoming_events = eca.get_upcoming_events(days=7, positions=[])

    print(f"无持仓时未来7天事件数: {len(upcoming_events)}个")

    # 验证无持仓时应该没有相关事件
    assert len(upcoming_events) == 0, "无持仓时不应该有相关事件"

    # 生成报告
    report = eca.format_event_calendar_report(upcoming_events, [])

    print("\n无持仓时的报告:")
    print("-" * 60)
    print(report)
    print("-" * 60)

    # 验证报告包含"暂无"提示
    assert '暂无' in report, "无相关事件时报告应包含'暂无'提示"

    print("\n✅ 无持仓情况测试通过!")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀"*30)
    print("事件日历分析器测试套件")
    print("🚀"*30)

    tests = [
        test_event_loading,
        test_get_upcoming_events,
        test_filter_by_positions,
        test_event_report_format,
        test_event_suggestion,
        test_empty_positions
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ 测试出错: {test.__name__}")
            print(f"   异常: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"测试汇总: 通过{passed}个, 失败{failed}个")
    print("="*60)

    if failed == 0:
        print("\n🎉 所有测试通过! 事件日历分析器运行正常!")
        return True
    else:
        print(f"\n⚠️  有{failed}个测试失败,请检查代码")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
