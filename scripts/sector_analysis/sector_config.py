#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块配置文件
Sector Configuration

定义所有支持的板块及其配置
支持灵活扩展，可以随时添加新板块

作者: Claude Code
日期: 2025-10-16
"""

# 板块定义字典
SECTOR_DEFINITIONS = {
    # 港股创新药板块
    'HK_BIOTECH': {
        'name': '港股创新药',
        'market': 'CN',  # A股市场交易的港股ETF
        'type': 'etf',  # etf/sector/stock_basket
        'symbols': ['513120'],  # 广发中证香港创新药ETF
        'weights': None,  # None表示等权，或自定义权重字典 {'513120': 1.0}
        'category': 'healthcare',
        'description': '跟踪港股通创新药板块，覆盖信达生物、君实生物、药明生物等龙头'
    },

    # 港股电池板块
    'HK_BATTERY': {
        'name': '港股电池',
        'market': 'CN',  # A股市场交易的港股ETF
        'type': 'etf',
        'symbols': ['159755'],  # 广发国证新能源车电池ETF
        'weights': None,
        'category': 'energy',
        'description': '跟踪新能源车电池产业链，覆盖宁德时代、比亚迪、赣锋锂业等'
    },

    # A股化工板块
    'CN_CHEMICAL': {
        'name': 'A股化工',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['516020'],  # 华宝化工ETF
        'weights': None,
        'category': 'chemical',
        'description': '跟踪化工产业链，覆盖万华化学、恒力石化等龙头'
    },

    # A股煤炭板块
    'CN_COAL': {
        'name': 'A股煤炭',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['515220'],  # 国泰中证煤炭ETF
        'weights': None,
        'category': 'coal',
        'description': '跟踪煤炭产业链，覆盖中国神华、陕西煤业等龙头'
    },

    # A股白酒板块
    'CN_LIQUOR': {
        'name': 'A股白酒',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['512690'],  # 鹏华中证酒ETF
        'weights': None,
        'category': 'consumer',
        'description': '跟踪白酒产业，覆盖茅台、五粮液、泸州老窖等龙头'
    },

    # A股证券板块
    'CN_SECURITIES': {
        'name': 'A股证券',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['512880'],  # 证券ETF
        'weights': None,
        'category': 'finance',
        'description': '跟踪证券行业，覆盖中信证券、华泰证券等龙头券商'
    },

    # 以下为示例配置，可根据需要启用

    # A股半导体板块(示例，未来可扩展)
    # 'CN_SEMICONDUCTOR': {
    #     'name': 'A股半导体',
    #     'market': 'CN',
    #     'type': 'etf',
    #     'symbols': ['512480'],  # 半导体ETF
    #     'weights': None,
    #     'category': 'tech',
    #     'description': '跟踪A股半导体产业链'
    # },

    # A股军工板块(示例，未来可扩展)
    # 'CN_DEFENSE': {
    #     'name': 'A股军工',
    #     'market': 'CN',
    #     'type': 'etf',
    #     'symbols': ['512660'],  # 军工ETF
    #     'weights': None,
    #     'category': 'defense',
    #     'description': '跟踪A股军工产业链'
    # },
}


# 板块分类
SECTOR_CATEGORIES = {
    'healthcare': '医疗健康',
    'energy': '新能源',
    'tech': '科技',
    'defense': '国防军工',
    'consumer': '消费',
    'finance': '金融',
    'realestate': '地产',
    'chemical': '化工',
    'coal': '煤炭'
}


def get_sector_config(sector_key: str) -> dict:
    """
    获取板块配置

    Args:
        sector_key: 板块代码(如 'HK_BIOTECH')

    Returns:
        板块配置字典

    Raises:
        KeyError: 板块不存在
    """
    if sector_key not in SECTOR_DEFINITIONS:
        available = ', '.join(SECTOR_DEFINITIONS.keys())
        raise KeyError(f"板块 '{sector_key}' 不存在。可用板块: {available}")

    return SECTOR_DEFINITIONS[sector_key]


def list_all_sectors() -> list:
    """
    列出所有可用板块

    Returns:
        板块列表 [(key, name, category), ...]
    """
    result = []
    for key, config in SECTOR_DEFINITIONS.items():
        result.append((
            key,
            config['name'],
            SECTOR_CATEGORIES.get(config['category'], config['category'])
        ))
    return result


if __name__ == '__main__':
    """测试代码"""
    print("=" * 60)
    print("板块配置测试")
    print("=" * 60)

    print("\n所有可用板块:")
    for key, name, category in list_all_sectors():
        config = get_sector_config(key)
        print(f"\n  [{key}] {name} ({category})")
        print(f"    市场: {config['market']}")
        print(f"    类型: {config['type']}")
        print(f"    标的: {', '.join(config['symbols'])}")
        print(f"    描述: {config['description']}")

    print("\n" + "=" * 60)
    print("测试完成")
