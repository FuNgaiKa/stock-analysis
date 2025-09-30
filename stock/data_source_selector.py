#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源选择器 - 交互式选择数据源
支持用户选择不同的数据源进行量化分析
"""

import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class DataSourceSelector:
    """数据源选择器"""

    def __init__(self):
        self.available_sources = {
            '1': {
                'name': 'efinance (东方财富)',
                'code': 'efinance',
                'description': '实时数据，响应快速 (~1-2s)',
                'features': ['实时行情', '涨跌停数据', '全市场覆盖'],
                'recommended': '实时监控'
            },
            '2': {
                'name': 'baostock (证券宝)',
                'code': 'baostock',
                'description': '历史数据完整 (~5-10s)',
                'features': ['历史数据', '分钟级数据', '免费无限制'],
                'recommended': '历史回测'
            },
            '3': {
                'name': 'akshare优化版',
                'code': 'akshare_optimized',
                'description': '全市场数据 (~49s)',
                'features': ['5434只股票', '涨跌停数据', '市场全貌'],
                'recommended': '全市场分析'
            },
            '4': {
                'name': '腾讯财经',
                'code': 'tencent',
                'description': '快速指数查询 (~0.2s)',
                'features': ['三大指数', '极速响应', '稳定可靠'],
                'recommended': '快速查看'
            },
            '5': {
                'name': '多源自动切换',
                'code': 'multi_source',
                'description': '智能选择最佳数据源',
                'features': ['自动切换', '容错能力强', '推荐使用'],
                'recommended': '日常使用'
            }
        }

    def display_menu(self):
        """显示数据源选择菜单"""
        print("\n" + "=" * 70)
        print("请选择数据源：")
        print("=" * 70)

        for key, source in self.available_sources.items():
            print(f"\n{key}. {source['name']}")
            print(f"   {source['description']}")
            print(f"   特点: {', '.join(source['features'])}")
            print(f"   推荐场景: {source['recommended']}")

        print("\n" + "=" * 70)

    def select_source(self) -> Optional[str]:
        """
        交互式选择数据源

        Returns:
            数据源代码，如 'efinance', 'baostock' 等
        """
        self.display_menu()

        while True:
            try:
                choice = input("\n请输入数字选择数据源 (1-5，默认5): ").strip()

                # 默认选择多源自动切换
                if not choice:
                    choice = '5'

                if choice in self.available_sources:
                    selected = self.available_sources[choice]
                    print(f"\n✓ 已选择: {selected['name']}")
                    return selected['code']
                else:
                    print("✗ 无效选择，请输入1-5之间的数字")

            except KeyboardInterrupt:
                print("\n\n已取消选择，使用默认数据源")
                return 'multi_source'
            except Exception as e:
                logger.error(f"选择数据源时出错: {str(e)}")
                return 'multi_source'

    def get_source_instance(self, source_code: str):
        """
        获取数据源实例

        Args:
            source_code: 数据源代码

        Returns:
            数据源实例
        """
        try:
            if source_code == 'efinance':
                from efinance_source import EfinanceDataSource
                return EfinanceDataSource()

            elif source_code == 'baostock':
                from baostock_source import BaostockDataSource
                return BaostockDataSource()

            elif source_code == 'akshare_optimized':
                from akshare_optimized import OptimizedAkshareSource
                return OptimizedAkshareSource()

            elif source_code == 'tencent':
                from tencent_source import TencentDataSource
                return TencentDataSource()

            elif source_code == 'multi_source':
                from enhanced_data_sources import MultiSourceDataProvider
                return MultiSourceDataProvider()

            else:
                logger.warning(f"未知数据源: {source_code}，使用多源自动切换")
                from enhanced_data_sources import MultiSourceDataProvider
                return MultiSourceDataProvider()

        except Exception as e:
            logger.error(f"创建数据源实例失败: {str(e)}")
            # 失败时返回多源备份
            from enhanced_data_sources import MultiSourceDataProvider
            return MultiSourceDataProvider()

    def get_quick_recommendation(self, scenario: str) -> str:
        """
        根据场景快速推荐数据源

        Args:
            scenario: 场景类型，如 'realtime', 'backtest', 'analysis', 'quick'

        Returns:
            推荐的数据源代码
        """
        recommendations = {
            'realtime': 'efinance',      # 实时监控
            'backtest': 'baostock',      # 历史回测
            'analysis': 'akshare_optimized',  # 全市场分析
            'quick': 'tencent',          # 快速查看
            'default': 'multi_source'    # 默认
        }

        return recommendations.get(scenario, 'multi_source')


def test_selector():
    """测试数据源选择器"""
    selector = DataSourceSelector()

    print("\n测试1: 交互式选择")
    source_code = selector.select_source()
    print(f"选择的数据源代码: {source_code}")

    print("\n测试2: 场景推荐")
    scenarios = ['realtime', 'backtest', 'analysis', 'quick']
    for scenario in scenarios:
        recommended = selector.get_quick_recommendation(scenario)
        print(f"{scenario}: {recommended}")

    print("\n测试3: 获取数据源实例")
    instance = selector.get_source_instance(source_code)
    print(f"数据源实例: {type(instance).__name__}")


if __name__ == "__main__":
    test_selector()