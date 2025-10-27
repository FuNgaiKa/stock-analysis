#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kelly公式计算器
用于计算不同策略的最优杠杆倍数
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    Kelly公式: f* = (p × b - q) / b

    Args:
        win_rate: 胜率 (0-1)
        avg_win: 平均盈利 (例如 0.05 表示5%)
        avg_loss: 平均亏损 (例如 0.03 表示3%, 传入正数)

    Returns:
        最优仓位比例 (0-1)
    """
    if avg_loss <= 0:
        return 0.0

    p = win_rate  # 胜率
    q = 1 - win_rate  # 败率
    b = avg_win / avg_loss  # 赔率 (盈亏比)

    # Kelly公式
    kelly = (p * b - q) / b

    return max(0.0, kelly)


def calculate_leverage_recommendations(
    win_rate: float,
    avg_win: float,
    avg_loss: float
) -> Dict:
    """
    计算不同保守程度的杠杆建议

    Returns:
        包含Full Kelly, Half Kelly, Quarter Kelly的建议
    """
    full_kelly = kelly_criterion(win_rate, avg_win, avg_loss)

    return {
        'full_kelly': full_kelly,
        'half_kelly': full_kelly * 0.5,
        'quarter_kelly': full_kelly * 0.25,
        'full_kelly_leverage': 1.0 + full_kelly,  # 转换为杠杆倍数
        'half_kelly_leverage': 1.0 + full_kelly * 0.5,
        'quarter_kelly_leverage': 1.0 + full_kelly * 0.25,
        'win_rate': win_rate,
        'profit_factor': (win_rate * avg_win) / ((1 - win_rate) * avg_loss),
        'expected_return': win_rate * avg_win - (1 - win_rate) * avg_loss
    }


def simulate_growth_rate(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    position_size: float,
    n_simulations: int = 10000
) -> Dict:
    """
    蒙特卡洛模拟不同仓位大小的长期增长率

    Args:
        position_size: 仓位大小 (0-2, 表示杠杆倍数-1)

    Returns:
        包含平均增长率、破产概率等
    """
    np.random.seed(42)

    results = []
    bankrupt_count = 0

    for _ in range(n_simulations):
        capital = 1.0

        # 模拟100次交易
        for _ in range(100):
            # 随机决定盈亏
            if np.random.random() < win_rate:
                # 盈利
                capital *= (1 + position_size * avg_win)
            else:
                # 亏损
                capital *= (1 - position_size * avg_loss)

            # 检查破产
            if capital < 0.1:  # 亏损90%视为破产
                bankrupt_count += 1
                break

        results.append(capital)

    results = np.array(results)

    return {
        'mean_final_capital': np.mean(results),
        'median_final_capital': np.median(results),
        'max_final_capital': np.max(results),
        'min_final_capital': np.min(results),
        'bankruptcy_rate': bankrupt_count / n_simulations,
        'growth_rate': (np.mean(results) ** (1/100) - 1)  # 几何平均增长率
    }


# ==================== 实战案例分析 ====================

def analyze_common_strategies():
    """分析常见交易策略的Kelly杠杆"""

    strategies = {
        '超级量化策略 (理想)': {
            'win_rate': 0.70,
            'avg_win': 0.08,
            'avg_loss': 0.04,
            'description': '高胜率+高赔率,极罕见'
        },
        '优秀量化策略': {
            'win_rate': 0.60,
            'avg_win': 0.06,
            'avg_loss': 0.04,
            'description': '专业机构级别'
        },
        '普通趋势策略': {
            'win_rate': 0.45,
            'avg_win': 0.10,
            'avg_loss': 0.05,
            'description': '低胜率高赔率'
        },
        '四指标共振策略 (假设)': {
            'win_rate': 0.55,
            'avg_win': 0.05,
            'avg_loss': 0.03,
            'description': '你的项目策略'
        },
        '散户平均水平': {
            'win_rate': 0.40,
            'avg_win': 0.08,
            'avg_loss': 0.10,
            'description': '负期望,不应交易'
        },
        'A股指数长期持有': {
            'win_rate': 0.53,  # 上涨年份占比
            'avg_win': 0.30,   # 上涨年平均30%
            'avg_loss': 0.20,  # 下跌年平均20%
            'description': '被动投资基准'
        }
    }

    print("=" * 100)
    print("Kelly公式 - 常见策略杠杆分析")
    print("=" * 100)

    results = []

    for name, params in strategies.items():
        rec = calculate_leverage_recommendations(
            params['win_rate'],
            params['avg_win'],
            params['avg_loss']
        )

        results.append({
            'strategy': name,
            'description': params['description'],
            'win_rate': f"{params['win_rate']:.0%}",
            'avg_win': f"{params['avg_win']:.1%}",
            'avg_loss': f"{params['avg_loss']:.1%}",
            'full_kelly': f"{rec['full_kelly']:.2%}",
            'quarter_kelly': f"{rec['quarter_kelly']:.2%}",
            'quarter_kelly_leverage': f"{rec['quarter_kelly_leverage']:.2f}x",
            'profit_factor': f"{rec['profit_factor']:.2f}",
            'expected_return': f"{rec['expected_return']:.2%}"
        })

    df = pd.DataFrame(results)
    print("\n" + df.to_string(index=False))

    return df


def analyze_leverage_risk(win_rate: float, avg_win: float, avg_loss: float):
    """分析不同杠杆倍数的风险收益特征"""

    kelly_rec = calculate_leverage_recommendations(win_rate, avg_win, avg_loss)

    print("\n" + "=" * 100)
    print(f"策略参数: 胜率{win_rate:.0%}, 平均盈利{avg_win:.1%}, 平均亏损{avg_loss:.1%}")
    print("=" * 100)

    # 测试不同杠杆倍数
    leverage_levels = {
        '无杠杆': 0.0,
        '1/4 Kelly': kelly_rec['quarter_kelly'],
        '1/2 Kelly': kelly_rec['half_kelly'],
        'Full Kelly': kelly_rec['full_kelly'],
        '2x Kelly (过度杠杆)': kelly_rec['full_kelly'] * 2
    }

    print("\n不同杠杆水平的长期表现 (10000次模拟, 每次100笔交易):\n")

    for name, position_size in leverage_levels.items():
        if position_size < 0:
            print(f"{name}: 负期望,不适合交易")
            continue

        leverage = 1.0 + position_size
        sim_result = simulate_growth_rate(win_rate, avg_win, avg_loss, position_size, n_simulations=10000)

        print(f"{name} (杠杆{leverage:.2f}x):")
        print(f"  最终资金中位数: {sim_result['median_final_capital']:.2f}x")
        print(f"  最终资金平均值: {sim_result['mean_final_capital']:.2f}x")
        print(f"  破产概率: {sim_result['bankruptcy_rate']:.1%}")
        print(f"  几何平均增长率: {sim_result['growth_rate']:.2%}/次")
        print()


def calculate_a_share_safe_leverage():
    """计算A股市场的实际安全杠杆"""

    print("\n" + "=" * 100)
    print("A股实战杠杆建议")
    print("=" * 100)

    scenarios = [
        {
            'name': '沪深300指数增强策略',
            'win_rate': 0.58,
            'avg_win': 0.12,
            'avg_loss': 0.08,
            'max_leverage_allowed': 2.0  # 融资融券限制
        },
        {
            'name': '短线技术分析策略',
            'win_rate': 0.48,
            'avg_win': 0.05,
            'avg_loss': 0.04,
            'max_leverage_allowed': 1.5
        },
        {
            'name': '价值投资策略',
            'win_rate': 0.62,
            'avg_win': 0.25,
            'avg_loss': 0.15,
            'max_leverage_allowed': 1.5
        }
    ]

    for scenario in scenarios:
        print(f"\n【{scenario['name']}】")
        rec = calculate_leverage_recommendations(
            scenario['win_rate'],
            scenario['avg_win'],
            scenario['avg_loss']
        )

        quarter_kelly_lev = rec['quarter_kelly_leverage']
        safe_leverage = min(quarter_kelly_lev, scenario['max_leverage_allowed'])

        print(f"  理论1/4 Kelly杠杆: {quarter_kelly_lev:.2f}x")
        print(f"  监管允许最大杠杆: {scenario['max_leverage_allowed']:.2f}x")
        print(f"  [建议] 实际杠杆: {safe_leverage:.2f}x")

        if rec['expected_return'] > 0:
            print(f"  [OK] 期望收益: {rec['expected_return']:.2%}/笔")
        else:
            print(f"  [WARN] 期望收益为负,不应交易")

        print(f"  盈亏比: {rec['profit_factor']:.2f}")


if __name__ == '__main__':
    print("\n" + "=" * 100)
    print("Kelly公式杠杆计算器 - 完整分析")
    print("=" * 100)

    # 1. 常见策略分析
    analyze_common_strategies()

    # 2. 风险分析 (以优秀量化策略为例)
    print("\n\n")
    analyze_leverage_risk(
        win_rate=0.60,
        avg_win=0.06,
        avg_loss=0.04
    )

    # 3. A股实战建议
    print("\n\n")
    calculate_a_share_safe_leverage()

    # 4. 关键结论
    print("\n" + "=" * 100)
    print("核心结论")
    print("=" * 100)
    print("""
1. 即使是优秀策略(胜率60%, 盈亏比1.5), Full Kelly也只建议30%额外仓位 (1.3x杠杆)
2. 1/4 Kelly通常在 1.05x - 1.15x 杠杆范围 (非常保守!)
3. A股散户由于胜率不足50%、盈亏比不佳,Kelly公式常给出 "0杠杆" 或 "负值" (不应交易)
4. 只有统计验证过的、有正期望的策略才应该考虑杠杆
5. 超过Full Kelly的杠杆会导致破产概率快速上升

关键警告:
- 如果你的策略未经过样本外验证,先假设Kelly = 0 (无杠杆)
- A股融资融券允许2倍杠杆,但Kelly公式很少建议超过1.5倍
- 期货市场允许10倍杠杆,但这是"杠杆陷阱",绝大多数情况下不应使用
    """)
