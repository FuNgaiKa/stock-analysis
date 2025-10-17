#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一资产配置文件
Unified Asset Configuration

整合所有标的(指数、板块、个股)的配置
支持一次运行分析所有标的

作者: Claude Code
日期: 2025-10-16
"""

# 统一资产定义字典
# 整合了 comprehensive_asset_analysis 和 sector_analysis 的所有标的
UNIFIED_ASSETS = {
    # ==================== 指数类 ====================
    # 四大科技指数
    'CYBZ': {
        'type': 'index',
        'analyzer_type': 'comprehensive',  # 使用 ComprehensiveAssetReporter
        'market': 'CN',
        'name': '创业板指',
        'code': 'CYBZ',
        'category': 'tech_index',
        'description': 'A股创业板指数，科技成长股聚集地'
    },
    'KECHUANG50': {
        'type': 'index',
        'analyzer_type': 'comprehensive',
        'market': 'CN',
        'name': '科创50',
        'code': 'KECHUANG50',
        'category': 'tech_index',
        'description': 'A股科创板50指数，硬科技龙头聚集地'
    },
    'HKTECH': {
        'type': 'index',
        'analyzer_type': 'comprehensive',
        'market': 'HK',
        'name': '恒生科技',
        'code': 'HSTECH',
        'category': 'tech_index',
        'description': '港股科技指数，包含腾讯、阿里等科技龙头'
    },
    'NASDAQ': {
        'type': 'index',
        'analyzer_type': 'comprehensive',
        'market': 'US',
        'name': '纳斯达克',
        'code': 'NASDAQ',
        'category': 'tech_index',
        'description': '美股纳斯达克指数，全球科技股风向标'
    },

    # 宽基指数
    'HS300': {
        'type': 'index',
        'analyzer_type': 'comprehensive',
        'market': 'CN',
        'name': '沪深300',
        'code': 'HS300',
        'category': 'broad_index',
        'description': 'A股蓝筹指数，覆盖沪深两市市值最大的300只股票'
    },

    # 大宗商品
    'GOLD': {
        'type': 'commodity',
        'analyzer_type': 'comprehensive',
        'market': 'US',
        'name': '黄金',
        'code': 'GOLD',
        'category': 'commodity',
        'description': '黄金现货，避险资产'
    },

    # 加密货币
    'BTC': {
        'type': 'crypto',
        'analyzer_type': 'comprehensive',
        'market': 'US',
        'name': '比特币',
        'code': 'BTC',
        'category': 'crypto',
        'description': '比特币，数字黄金'
    },

    # ==================== 板块ETF类 ====================
    # 港股创新药板块
    'HK_BIOTECH': {
        'type': 'etf',
        'analyzer_type': 'sector',  # 使用 SectorReporter
        'market': 'CN',
        'name': '港股创新药',
        'symbols': ['513120'],
        'weights': None,
        'category': 'healthcare',
        'description': '跟踪港股通创新药板块，覆盖信达生物、君实生物、药明生物等龙头'
    },

    # 港股电池板块
    'HK_BATTERY': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': '港股电池',
        'symbols': ['159755'],
        'weights': None,
        'category': 'energy',
        'description': '跟踪新能源车电池产业链，覆盖宁德时代、比亚迪、赣锋锂业等'
    },

    # A股化工板块
    'CN_CHEMICAL': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股化工',
        'symbols': ['516020'],
        'weights': None,
        'category': 'chemical',
        'description': '跟踪化工产业链，覆盖万华化学、恒力石化等龙头'
    },

    # A股煤炭板块
    'CN_COAL': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股煤炭',
        'symbols': ['515220'],
        'weights': None,
        'category': 'coal',
        'description': '跟踪煤炭产业链，覆盖中国神华、陕西煤业等龙头'
    },

    # A股白酒板块
    'CN_LIQUOR': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股白酒',
        'symbols': ['512690'],
        'weights': None,
        'category': 'consumer',
        'description': '跟踪白酒产业，覆盖茅台、五粮液、泸州老窖等龙头'
    },

    # A股证券板块
    'CN_SECURITIES': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股证券',
        'symbols': ['512880'],
        'weights': None,
        'category': 'finance',
        'description': '跟踪证券行业，覆盖中信证券、华泰证券等龙头券商'
    },

    # A股游戏板块
    'CN_GAME': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股游戏',
        'symbols': ['159869'],
        'weights': None,
        'category': 'media',
        'description': '跟踪动漫游戏产业，覆盖腾讯控股、网易、三七互娱等游戏龙头'
    },

    # A股传媒板块
    'CN_MEDIA': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股传媒',
        'symbols': ['512980'],
        'weights': None,
        'category': 'media',
        'description': '跟踪文化传媒行业，覆盖影视、广告、出版等传媒龙头企业'
    },

    # A股半导体板块
    'CN_SEMICONDUCTOR': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股半导体',
        'symbols': ['512480'],
        'weights': None,
        'category': 'tech',
        'description': '跟踪中证半导体指数，覆盖芯片设计、制造、封测等半导体产业链'
    },

    # A股钢铁板块
    'CN_STEEL': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股钢铁',
        'symbols': ['515210'],
        'weights': None,
        'category': 'materials',
        'description': '跟踪钢铁行业，覆盖宝钢股份、鞍钢股份等钢铁龙头企业'
    },

    # A股有色金属板块
    'CN_METALS': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股有色金属',
        'symbols': ['159871'],
        'weights': None,
        'category': 'materials',
        'description': '跟踪有色金属行业，覆盖紫金矿业、洛阳钼业、云南铜业等龙头'
    },

    # A股银行板块
    'CN_BANK': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股银行',
        'symbols': ['512800'],
        'weights': None,
        'category': 'finance',
        'description': '跟踪银行行业，覆盖工商银行、建设银行、招商银行等银行龙头'
    },

    # A股保险板块
    'CN_INSURANCE': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股保险',
        'symbols': ['512910'],
        'weights': None,
        'category': 'finance',
        'description': '跟踪保险行业，覆盖中国平安、中国人寿、中国太保等保险龙头'
    },

    # A股软件板块
    'CN_SOFTWARE': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股软件',
        'symbols': ['515230'],
        'weights': None,
        'category': 'tech',
        'description': '跟踪中证全指软件指数，覆盖金山办公、用友网络、恒生电子等软件龙头'
    },

    # A股稀土板块
    'CN_RARE_EARTH': {
        'type': 'etf',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': 'A股稀土',
        'symbols': ['516780'],
        'weights': None,
        'category': 'materials',
        'description': '跟踪中证稀土产业指数，覆盖北方稀土、盛和资源、五矿稀土等稀土龙头'
    },

    # ==================== 个股类 ====================
    # 三花智控
    'SANHUA_A': {
        'type': 'stock',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': '三花智控(A股)',
        'symbols': ['002050'],
        'weights': None,
        'category': 'manufacturing',
        'description': '汽车零部件龙头，专注热管理系统，受益新能源汽车发展'
    },

    # 阿里巴巴港股
    'BABA_HK': {
        'type': 'stock',
        'analyzer_type': 'sector',
        'market': 'HK',
        'name': '阿里巴巴(港股)',
        'symbols': ['9988.HK'],
        'weights': None,
        'category': 'tech',
        'description': '中国电商及云计算巨头，覆盖电商、云计算、数字娱乐等业务',
        'data_source': 'yfinance'
    },

    # 指南针
    'ZHINANZHEN': {
        'type': 'stock',
        'analyzer_type': 'sector',
        'market': 'CN',
        'name': '指南针',
        'symbols': ['300803'],
        'weights': None,
        'category': 'tech',
        'description': '证券投资软件龙头，主营炒股软件及金融信息服务'
    },
}


# 资产分类
ASSET_CATEGORIES = {
    'tech_index': '科技指数',
    'broad_index': '宽基指数',
    'commodity': '大宗商品',
    'crypto': '加密货币',
    'healthcare': '医疗健康',
    'energy': '新能源',
    'tech': '科技',
    'defense': '国防军工',
    'consumer': '消费',
    'finance': '金融',
    'realestate': '地产',
    'chemical': '化工',
    'coal': '煤炭',
    'media': '传媒娱乐',
    'manufacturing': '先进制造',
    'materials': '有色金属材料'
}


def get_asset_config(asset_key: str) -> dict:
    """
    获取资产配置

    Args:
        asset_key: 资产代码

    Returns:
        资产配置字典

    Raises:
        KeyError: 资产不存在
    """
    if asset_key not in UNIFIED_ASSETS:
        available = ', '.join(UNIFIED_ASSETS.keys())
        raise KeyError(f"资产 '{asset_key}' 不存在。可用资产: {available}")

    return UNIFIED_ASSETS[asset_key]


def list_all_assets() -> list:
    """
    列出所有可用资产

    Returns:
        资产列表 [(key, name, category, analyzer_type), ...]
    """
    result = []
    for key, config in UNIFIED_ASSETS.items():
        result.append((
            key,
            config['name'],
            ASSET_CATEGORIES.get(config['category'], config['category']),
            config['analyzer_type']
        ))
    return result


def list_assets_by_analyzer(analyzer_type: str) -> list:
    """
    按分析器类型筛选资产

    Args:
        analyzer_type: 分析器类型 ('comprehensive' 或 'sector')

    Returns:
        资产代码列表
    """
    return [
        key for key, config in UNIFIED_ASSETS.items()
        if config['analyzer_type'] == analyzer_type
    ]


if __name__ == '__main__':
    """测试代码"""
    print("=" * 80)
    print("统一资产配置测试")
    print("=" * 80)

    print("\n所有可用资产:")
    print(f"{'代码':<20} {'名称':<20} {'类别':<15} {'分析器':<15}")
    print("-" * 80)

    for key, name, category, analyzer_type in list_all_assets():
        print(f"{key:<20} {name:<20} {category:<15} {analyzer_type:<15}")

    print("\n" + "=" * 80)
    print(f"总计: {len(UNIFIED_ASSETS)} 个资产")
    print(f"指数分析器(comprehensive): {len(list_assets_by_analyzer('comprehensive'))} 个")
    print(f"板块分析器(sector): {len(list_assets_by_analyzer('sector'))} 个")
    print("=" * 80)
