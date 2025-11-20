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

    # A股电力板块
    'CN_POWER': {
        'name': 'A股电力',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['159611'],  # 电力ETF
        'weights': None,
        'category': 'utilities',
        'description': '跟踪电力行业，覆盖电力生产、输配电及新能源发电等电力产业链'
    },

    # 三花智控(个股)
    'SANHUA_A': {
        'name': '三花智控(A股)',
        'market': 'CN',
        'type': 'stock',
        'symbols': ['002050'],  # 三花智控A股
        'weights': None,
        'category': 'manufacturing',
        'description': '汽车零部件龙头，专注热管理系统，受益新能源汽车发展'
    },

    # 阿里巴巴港股 (优先使用港股，流动性更好)
    'BABA_HK': {
        'name': '阿里巴巴(港股)',
        'market': 'HK',
        'type': 'stock',
        'symbols': ['9988.HK'],  # 阿里巴巴港股
        'weights': None,
        'category': 'tech',
        'description': '中国电商及云计算巨头，覆盖电商、云计算、数字娱乐等业务',
        'data_source': 'yfinance'  # 使用yfinance数据源
    },

    # A股半导体板块
    'CN_SEMICONDUCTOR': {
        'name': 'A股半导体',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['512480'],  # 国联安中证半导体ETF
        'weights': None,
        'category': 'tech',
        'description': '跟踪中证半导体指数，覆盖芯片设计、制造、封测等半导体产业链'
    },

    # A股钢铁板块
    'CN_STEEL': {
        'name': 'A股钢铁',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['515210'],  # 国泰中证钢铁ETF
        'weights': None,
        'category': 'materials',
        'description': '跟踪钢铁行业，覆盖宝钢股份、鞍钢股份等钢铁龙头企业'
    },

    # A股有色金属板块
    'CN_METALS': {
        'name': 'A股有色金属',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['159871'],  # 有色金属ETF
        'weights': None,
        'category': 'materials',
        'description': '跟踪有色金属行业，覆盖紫金矿业、洛阳钼业、云南铜业等龙头'
    },

    # A股银行板块
    'CN_BANK': {
        'name': 'A股银行',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['512800'],  # 华宝中证银行ETF
        'weights': None,
        'category': 'finance',
        'description': '跟踪银行行业，覆盖工商银行、建设银行、招商银行等银行龙头'
    },

    # A股保险板块
    'CN_INSURANCE': {
        'name': 'A股保险',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['512910'],  # 广发中证保险ETF
        'weights': None,
        'category': 'finance',
        'description': '跟踪保险行业，覆盖中国平安、中国人寿、中国太保等保险龙头'
    },

    # A股软件板块
    'CN_SOFTWARE': {
        'name': 'A股软件',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['515230'],  # 国泰中证全指软件ETF
        'weights': None,
        'category': 'tech',
        'description': '跟踪中证全指软件指数，覆盖金山办公、用友网络、恒生电子等软件龙头'
    },

    # A股稀土板块
    'CN_RARE_EARTH': {
        'name': 'A股稀土',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['516780'],  # 华泰柏瑞中证稀土产业ETF
        'weights': None,
        'category': 'materials',
        'description': '跟踪中证稀土产业指数，覆盖北方稀土、盛和资源、五矿稀土等稀土龙头'
    },

    # A股科创芯片板块
    'CN_CHIP': {
        'name': 'A股科创芯片',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['588200'],  # 科创芯片ETF
        'weights': None,
        'category': 'tech',
        'description': '跟踪科创芯片指数，覆盖科创板芯片设计、制造等半导体产业链龙头'
    },

    # 指南针(个股)
    'ZHINANZHEN': {
        'name': '指南针',
        'market': 'CN',
        'type': 'stock',
        'symbols': ['300803'],  # 指南针股票代码
        'weights': None,
        'category': 'tech',
        'description': '证券投资软件龙头，主营炒股软件及金融信息服务'
    },

    # A股通信板块
    'CN_TELECOM': {
        'name': 'A股通信',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['515880'],  # 通信ETF
        'weights': None,
        'category': 'tech',
        'description': '跟踪中证800通信行业，覆盖中国移动、中国电信、中兴通讯等通信龙头'
    },

    # A股红利低波板块
    'CN_DIVIDEND_LOW_VOL': {
        'name': 'A股红利低波',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['512890'],  # 红利低波ETF
        'weights': None,
        'category': 'dividend',
        'description': '跟踪中证红利低波动指数，覆盖高股息低波动股票，适合稳健配置'
    },

    # A股大数据板块
    'CN_BIG_DATA': {
        'name': 'A股大数据',
        'market': 'CN',
        'type': 'etf',
        'symbols': ['516000'],  # 大数据ETF
        'weights': None,
        'category': 'tech',
        'description': '跟踪中证大数据产业指数，覆盖数据存储、处理、应用等大数据产业链'
    },

    # 奇安信(个股)
    'QIANXIN': {
        'name': '奇安信',
        'market': 'CN',
        'type': 'stock',
        'symbols': ['688561'],  # 奇安信股票代码
        'weights': None,
        'category': 'tech',
        'description': '网络安全龙头企业，主营企业级网络安全产品和服务'
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
    'coal': '煤炭',
    'utilities': '电力公用',
    'manufacturing': '先进制造',
    'materials': '有色金属材料',
    'dividend': '红利'
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
