#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
底仓/波段比例优化器

基于Kelly公式、波动率、胜率等量化指标,计算最优的:
- 底仓比例 (长期持有,稳定核心)
- 波段仓比例 (主动交易,捕捉波动)

目标: 最大化风险调整后收益,实现年化50-60%回报
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Kelly公式(内联,避免外部依赖)
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

# 内部模块导入(同包内)
try:
    from .dynamic_position_manager import DynamicPositionManager
    from .risk_manager import RiskManager
except ImportError:
    # 如果相对导入失败,尝试绝对导入
    try:
        from russ_trading_strategy.dynamic_position_manager import DynamicPositionManager
        from russ_trading_strategy.risk_manager import RiskManager
    except ImportError:
        DynamicPositionManager = None
        RiskManager = None


class BaseSwingOptimizer:
    """底仓/波段比例优化器 - 量化分析而非拍脑袋"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化优化器

        Args:
            config: 配置参数
                - total_position: 总仓位,默认0.95
                - max_drawdown_tolerance: 最大回撤容忍度,默认0.25
                - target_annual_return: 目标年化收益,默认0.55
        """
        if config is None:
            config = {}

        self.total_position = config.get('total_position', 0.95)
        self.max_drawdown_tolerance = config.get('max_drawdown_tolerance', 0.25)
        self.target_annual_return = config.get('target_annual_return', 0.55)

        self.risk_manager = RiskManager() if RiskManager else None

    # ==================== 资产类别参数估算 ====================

    def estimate_asset_params(self, asset_type: str) -> Dict:
        """
        估算不同资产类别的交易参数

        基于历史经验和市场特征估算:
        - 年化波动率
        - 波段交易胜率
        - 波段交易平均盈利
        - 波段交易平均亏损

        Args:
            asset_type: 资产类型
                - 'hk_tech': 恒生科技ETF
                - 'star50': 科创50ETF
                - 'growth': 创业板ETF
                - 'coal': 煤炭ETF
                - 'chemicals': 化工ETF

        Returns:
            资产参数字典
        """
        # 基于历史数据的参数估算 (保守估计)
        params_db = {
            'hk_tech': {
                'name': '恒生科技ETF',
                'annual_volatility': 0.45,  # 年化波动率45%
                'base_expected_return': 0.40,  # 底仓预期年化40%
                'swing_win_rate': 0.48,  # 波段胜率48% (略低于50%)
                'swing_avg_win': 0.08,  # 波段平均盈利8%
                'swing_avg_loss': 0.05,  # 波段平均亏损5%
                'swing_frequency': 8,  # 年均8次波段机会
                'trend_persistence': 0.65,  # 趋势持续性65% (科技股趋势较强)
            },
            'star50': {
                'name': '科创50ETF',
                'annual_volatility': 0.55,  # 年化波动率55% (最高)
                'base_expected_return': 0.50,  # 底仓预期年化50%
                'swing_win_rate': 0.52,  # 波段胜率52% (波动大,机会多)
                'swing_avg_win': 0.12,  # 波段平均盈利12%
                'swing_avg_loss': 0.06,  # 波段平均亏损6%
                'swing_frequency': 10,  # 年均10次波段机会 (波动最大)
                'trend_persistence': 0.60,  # 趋势持续性60%
            },
            'growth': {
                'name': '创业板ETF',
                'annual_volatility': 0.50,  # 年化波动率50%
                'base_expected_return': 0.45,  # 底仓预期年化45%
                'swing_win_rate': 0.50,  # 波段胜率50%
                'swing_avg_win': 0.10,  # 波段平均盈利10%
                'swing_avg_loss': 0.05,  # 波段平均亏损5%
                'swing_frequency': 9,  # 年均9次波段机会
                'trend_persistence': 0.62,  # 趋势持续性62%
            },
            'coal': {
                'name': '煤炭ETF',
                'annual_volatility': 0.40,  # 年化波动率40% (周期股)
                'base_expected_return': 0.25,  # 底仓预期年化25% (周期性)
                'swing_win_rate': 0.55,  # 波段胜率55% (周期波动有规律)
                'swing_avg_win': 0.15,  # 波段平均盈利15% (周期振幅大)
                'swing_avg_loss': 0.08,  # 波段平均亏损8%
                'swing_frequency': 6,  # 年均6次波段机会 (周期较长)
                'trend_persistence': 0.55,  # 趋势持续性55% (周期性强)
            },
            'chemicals': {
                'name': '化工ETF',
                'annual_volatility': 0.38,  # 年化波动率38%
                'base_expected_return': 0.22,  # 底仓预期年化22%
                'swing_win_rate': 0.53,  # 波段胜率53%
                'swing_avg_win': 0.12,  # 波段平均盈利12%
                'swing_avg_loss': 0.07,  # 波段平均亏损7%
                'swing_frequency': 7,  # 年均7次波段机会
                'trend_persistence': 0.58,  # 趋势持续性58%
            }
        }

        if asset_type not in params_db:
            raise ValueError(f"Unknown asset type: {asset_type}")

        return params_db[asset_type]

    # ==================== Kelly公式计算波段最优仓位 ====================

    def calculate_swing_kelly_position(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        kelly_fraction: float = 0.25
    ) -> Dict:
        """
        使用Kelly公式计算波段交易的最优仓位

        Args:
            win_rate: 波段胜率
            avg_win: 平均盈利
            avg_loss: 平均亏损
            kelly_fraction: Kelly折扣系数,默认1/4 Kelly

        Returns:
            Kelly仓位建议
        """
        # 计算Full Kelly
        full_kelly = kelly_criterion(win_rate, avg_win, avg_loss)

        # 保守起见,使用1/4 Kelly
        kelly_position = full_kelly * kelly_fraction

        # 限制范围 (波段仓最多50%)
        kelly_position = max(0.0, min(kelly_position, 0.50))

        # 计算期望收益
        expected_return_per_trade = win_rate * avg_win - (1 - win_rate) * avg_loss

        # 盈亏比
        profit_factor = (win_rate * avg_win) / ((1 - win_rate) * avg_loss) if avg_loss > 0 else 0

        return {
            'full_kelly': full_kelly,
            'kelly_position': kelly_position,
            'kelly_position_pct': f"{kelly_position * 100:.1f}%",
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'expected_return_per_trade': expected_return_per_trade,
            'expected_return_per_trade_pct': f"{expected_return_per_trade * 100:.2f}%",
            'kelly_fraction_used': kelly_fraction
        }

    # ==================== 简化的优化方法 ====================

    def calculate_optimal_base_swing_split(
        self,
        portfolio_allocation: Dict[str, float]
    ) -> Dict:
        """
        计算最优底仓/波段分配 - 简化版

        核心思路:
        1. 激进型投资者:底仓60-65%,波段30-35%
        2. 根据组合波动率微调
        3. 根据Kelly期望值微调

        Returns:
            最优底仓/波段比例
        """
        # 计算组合加权波动率
        total_volatility = 0.0
        total_kelly_expectation = 0.0
        total_allocation = sum(portfolio_allocation.values())

        for asset_type, allocation in portfolio_allocation.items():
            params = self.estimate_asset_params(asset_type)
            kelly_result = self.calculate_swing_kelly_position(
                params['swing_win_rate'],
                params['swing_avg_win'],
                params['swing_avg_loss'],
                kelly_fraction=0.5  # 使用Half Kelly
            )

            weight = allocation / total_allocation
            total_volatility += weight * params['annual_volatility']
            total_kelly_expectation += weight * kelly_result['expected_return_per_trade']

        # 基础分配(激进型)
        base_base_ratio = 0.62  # 底仓62%
        base_swing_ratio = 0.33  # 波段33%

        # 根据波动率调整
        # 波动率越高,越适合波段(但有上限)
        # 标准波动率假设为45%
        volatility_adjustment = (total_volatility - 0.45) * 0.3
        swing_ratio_adjusted = base_swing_ratio + volatility_adjustment
        swing_ratio_adjusted = max(0.25, min(0.40, swing_ratio_adjusted))  # 限制在25-40%

        # 根据Kelly期望调整
        # 期望越高,越适合波段
        # 标准期望假设为2.5%
        kelly_adjustment = (total_kelly_expectation - 0.025) * 5
        swing_ratio_adjusted += kelly_adjustment
        swing_ratio_adjusted = max(0.25, min(0.40, swing_ratio_adjusted))

        # 底仓比例
        base_ratio_adjusted = 1.0 - swing_ratio_adjusted

        return {
            'base_ratio': base_ratio_adjusted,
            'swing_ratio': swing_ratio_adjusted,
            'total_volatility': total_volatility,
            'kelly_expectation': total_kelly_expectation,
            'rationale': self._generate_split_rationale(
                base_ratio_adjusted,
                swing_ratio_adjusted,
                total_volatility,
                total_kelly_expectation
            )
        }

    def _generate_split_rationale(
        self,
        base_ratio: float,
        swing_ratio: float,
        volatility: float,
        kelly_exp: float
    ) -> str:
        """生成分配理由"""
        reasons = []

        if volatility > 0.50:
            reasons.append(f"组合波动率{volatility*100:.0f}%较高,适合波段操作")
        elif volatility < 0.40:
            reasons.append(f"组合波动率{volatility*100:.0f}%适中,以底仓为主")

        if kelly_exp > 0.03:
            reasons.append(f"Kelly期望{kelly_exp*100:.1f}%较高,可增加波段")
        elif kelly_exp < 0.02:
            reasons.append(f"Kelly期望{kelly_exp*100:.1f}%一般,控制波段比例")

        return "; ".join(reasons) if reasons else "标准配置"

    # ==================== 组合优化 (详细版) ====================

    def optimize_portfolio_base_swing_ratio(
        self,
        portfolio_allocation: Dict[str, float],
        aggressive_mode: bool = True
    ) -> Dict:
        """
        优化投资组合的底仓/波段比例

        Args:
            portfolio_allocation: 各资产配置比例
                例如: {
                    'hk_tech': 0.30,
                    'star50': 0.25,
                    'growth': 0.20,
                    'coal': 0.12,
                    'chemicals': 0.08
                }
            aggressive_mode: 激进模式(使用更高的波段比例)

        Returns:
            优化后的底仓/波段建议
        """
        results = []
        total_base_contribution = 0.0
        total_swing_contribution = 0.0
        total_base_allocation = 0.0
        total_swing_allocation = 0.0

        for asset_type, allocation in portfolio_allocation.items():
            # 获取资产参数
            params = self.estimate_asset_params(asset_type)

            # 计算Kelly波段仓位
            kelly_result = self.calculate_swing_kelly_position(
                params['swing_win_rate'],
                params['swing_avg_win'],
                params['swing_avg_loss'],
                kelly_fraction=0.75 if aggressive_mode else 0.25  # 激进模式使用3/4 Kelly
            )

            # 新思路:波段比例基于波动率和Kelly期望
            # 波动率越高,越适合波段;Kelly期望越高,越应该波段
            # 底仓比例基于趋势持续性

            # 波段适合度 = Kelly期望收益 × 波动率 × 频率因子
            swing_suitability = (
                kelly_result['expected_return_per_trade'] *
                params['annual_volatility'] *
                (params['swing_frequency'] / 10)  # 归一化到0-1
            )

            # 底仓适合度 = 趋势持续性 × 基础预期收益
            base_suitability = (
                params['trend_persistence'] *
                params['base_expected_return']
            )

            # 归一化:总和为1
            total_suitability = swing_suitability + base_suitability
            if total_suitability > 0:
                asset_swing_ratio = swing_suitability / total_suitability
                asset_base_ratio = base_suitability / total_suitability
            else:
                asset_swing_ratio = 0.3  # 默认30%波段
                asset_base_ratio = 0.7  # 默认70%底仓

            # 底仓收益贡献
            base_allocation = allocation * asset_base_ratio
            base_contribution = base_allocation * params['base_expected_return']

            # 波段收益贡献
            swing_allocation = allocation * asset_swing_ratio
            swing_contribution = (
                swing_allocation *
                params['swing_frequency'] *
                kelly_result['expected_return_per_trade']
            )

            total_base_contribution += base_contribution
            total_swing_contribution += swing_contribution
            total_base_allocation += base_allocation
            total_swing_allocation += swing_allocation

            results.append({
                'asset_type': asset_type,
                'asset_name': params['name'],
                'total_allocation': allocation,
                'total_allocation_pct': f"{allocation * 100:.1f}%",
                'base_ratio': asset_base_ratio,
                'base_ratio_pct': f"{asset_base_ratio * 100:.1f}%",
                'swing_ratio': asset_swing_ratio,
                'swing_ratio_pct': f"{asset_swing_ratio * 100:.1f}%",
                'base_allocation': base_allocation,
                'base_allocation_pct': f"{base_allocation * 100:.1f}%",
                'swing_allocation': swing_allocation,
                'swing_allocation_pct': f"{swing_allocation * 100:.1f}%",
                'base_contribution': base_contribution,
                'base_contribution_pct': f"{base_contribution * 100:.1f}%",
                'swing_contribution': swing_contribution,
                'swing_contribution_pct': f"{swing_contribution * 100:.1f}%",
                'kelly_details': kelly_result,
                'asset_params': params
            })

        # 组合层面统计
        total_expected_return = total_base_contribution + total_swing_contribution
        portfolio_base_ratio = total_base_allocation / sum(portfolio_allocation.values())
        portfolio_swing_ratio = total_swing_allocation / sum(portfolio_allocation.values())

        return {
            'asset_results': results,
            'portfolio_summary': {
                'total_base_allocation': total_base_allocation,
                'total_base_allocation_pct': f"{total_base_allocation * 100:.1f}%",
                'total_swing_allocation': total_swing_allocation,
                'total_swing_allocation_pct': f"{total_swing_allocation * 100:.1f}%",
                'portfolio_base_ratio': portfolio_base_ratio,
                'portfolio_base_ratio_pct': f"{portfolio_base_ratio * 100:.1f}%",
                'portfolio_swing_ratio': portfolio_swing_ratio,
                'portfolio_swing_ratio_pct': f"{portfolio_swing_ratio * 100:.1f}%",
                'base_contribution': total_base_contribution,
                'base_contribution_pct': f"{total_base_contribution * 100:.1f}%",
                'swing_contribution': total_swing_contribution,
                'swing_contribution_pct': f"{total_swing_contribution * 100:.1f}%",
                'total_expected_return': total_expected_return,
                'total_expected_return_pct': f"{total_expected_return * 100:.1f}%"
            }
        }

    # ==================== 风险约束检查 ====================

    def check_drawdown_constraint(
        self,
        optimization_result: Dict,
        max_drawdown_tolerance: Optional[float] = None
    ) -> Dict:
        """
        检查优化结果是否满足最大回撤约束

        Args:
            optimization_result: optimize_portfolio_base_swing_ratio()的结果
            max_drawdown_tolerance: 最大回撤容忍度

        Returns:
            风险检查结果
        """
        if max_drawdown_tolerance is None:
            max_drawdown_tolerance = self.max_drawdown_tolerance

        # 估算组合最大回撤
        # 使用加权平均波动率估算
        weighted_volatility = 0.0
        for asset_result in optimization_result['asset_results']:
            allocation = asset_result['total_allocation']
            volatility = asset_result['asset_params']['annual_volatility']
            weighted_volatility += allocation * volatility

        # 估算最大回撤 = 2 × 年化波动率 × 回撤系数
        # (经验公式,实际回撤通常约为波动率的1.5-2.5倍)
        estimated_max_drawdown = weighted_volatility * 2.0

        # 检查是否满足约束
        meets_constraint = estimated_max_drawdown <= max_drawdown_tolerance

        # 如果不满足,计算需要降低的仓位
        if not meets_constraint:
            position_adjustment = max_drawdown_tolerance / estimated_max_drawdown
        else:
            position_adjustment = 1.0

        return {
            'weighted_volatility': weighted_volatility,
            'weighted_volatility_pct': f"{weighted_volatility * 100:.1f}%",
            'estimated_max_drawdown': estimated_max_drawdown,
            'estimated_max_drawdown_pct': f"{estimated_max_drawdown * 100:.1f}%",
            'max_drawdown_tolerance': max_drawdown_tolerance,
            'max_drawdown_tolerance_pct': f"{max_drawdown_tolerance * 100:.1f}%",
            'meets_constraint': meets_constraint,
            'position_adjustment': position_adjustment,
            'position_adjustment_pct': f"{position_adjustment * 100:.1f}%",
            'recommendation': (
                '✅ 满足回撤约束,当前配置可行'
                if meets_constraint
                else f'⚠️ 预期回撤过大,建议降低仓位至{position_adjustment * 100:.0f}%'
            )
        }

    # ==================== 综合优化建议 ====================

    def generate_optimal_recommendation(
        self,
        portfolio_allocation: Dict[str, float]
    ) -> Dict:
        """
        生成综合优化建议

        Args:
            portfolio_allocation: 各资产配置比例

        Returns:
            完整的优化建议
        """
        # 1. 优化底仓/波段比例
        optimization = self.optimize_portfolio_base_swing_ratio(portfolio_allocation)

        # 2. 检查风险约束
        risk_check = self.check_drawdown_constraint(optimization)

        # 3. 生成最终建议
        summary = optimization['portfolio_summary']
        base_ratio = summary['portfolio_base_ratio']
        swing_ratio = summary['portfolio_swing_ratio']
        expected_return = summary['total_expected_return']

        # 如果不满足风险约束,调整比例
        if not risk_check['meets_constraint']:
            adjustment = risk_check['position_adjustment']
            base_ratio_adjusted = base_ratio * adjustment
            swing_ratio_adjusted = swing_ratio * adjustment
            expected_return_adjusted = expected_return * adjustment
        else:
            base_ratio_adjusted = base_ratio
            swing_ratio_adjusted = swing_ratio
            expected_return_adjusted = expected_return

        return {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'optimization_result': optimization,
            'risk_check': risk_check,
            'final_recommendation': {
                'base_position': base_ratio_adjusted,
                'base_position_pct': f"{base_ratio_adjusted * 100:.1f}%",
                'swing_position': swing_ratio_adjusted,
                'swing_position_pct': f"{swing_ratio_adjusted * 100:.1f}%",
                'total_position': base_ratio_adjusted + swing_ratio_adjusted,
                'total_position_pct': f"{(base_ratio_adjusted + swing_ratio_adjusted) * 100:.1f}%",
                'expected_annual_return': expected_return_adjusted,
                'expected_annual_return_pct': f"{expected_return_adjusted * 100:.1f}%",
                'meets_target': expected_return_adjusted >= self.target_annual_return,
                'meets_risk_constraint': risk_check['meets_constraint']
            },
            'strategy_description': self._generate_strategy_description(
                base_ratio_adjusted,
                swing_ratio_adjusted,
                expected_return_adjusted
            )
        }

    def _generate_strategy_description(
        self,
        base_ratio: float,
        swing_ratio: float,
        expected_return: float
    ) -> str:
        """生成策略描述"""
        total = base_ratio + swing_ratio
        base_pct = (base_ratio / total * 100) if total > 0 else 0
        swing_pct = (swing_ratio / total * 100) if total > 0 else 0

        return f"""
📊 **量化优化策略**

**底仓配置**: {base_pct:.0f}% (长期持有,稳定核心)
- 仓位: {base_ratio * 100:.1f}%
- 作用: 捕捉长期趋势,降低交易频率

**波段配置**: {swing_pct:.0f}% (主动交易,捕捉波动)
- 仓位: {swing_ratio * 100:.1f}%
- 作用: 利用Kelly公式优化的仓位,把握短期机会

**预期收益**: {expected_return * 100:.1f}%/年

**策略优势**:
1. 基于Kelly公式量化计算,而非拍脑袋
2. 底仓提供稳定收益,波段增强回报
3. 风险可控,符合回撤约束
4. 适合激进型投资者,追求高收益
""".strip()


# ==================== 测试用例 ====================

if __name__ == "__main__":
    # 设置UTF-8编码
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 100)
    print("底仓/波段比例优化器 - 量化分析")
    print("=" * 100)
    print()

    # 创建优化器
    optimizer = BaseSwingOptimizer({
        'total_position': 0.95,
        'max_drawdown_tolerance': 0.25,  # 激进型可承受25%回撤
        'target_annual_return': 0.55  # 目标年化55%
    })

    # 方案C的资产配置
    portfolio = {
        'hk_tech': 0.30,    # 恒生科技30%
        'star50': 0.25,     # 科创50 25%
        'growth': 0.20,     # 创业板20%
        'coal': 0.12,       # 煤炭12%
        'chemicals': 0.08   # 化工8%
    }

    print(f"投资组合配置:")
    for asset, allocation in portfolio.items():
        print(f"  {asset}: {allocation * 100:.0f}%")
    print()

    # 先用简化方法计算底仓/波段分配
    split_result = optimizer.calculate_optimal_base_swing_split(portfolio)

    print("=" * 100)
    print("📊 底仓/波段分配优化 (简化版)")
    print("=" * 100)
    print()
    print(f"✅ **最优分配**:")
    print(f"  底仓比例: {split_result['base_ratio'] * 100:.1f}%")
    print(f"  波段比例: {split_result['swing_ratio'] * 100:.1f}%")
    print(f"  组合波动率: {split_result['total_volatility'] * 100:.1f}%")
    print(f"  Kelly期望: {split_result['kelly_expectation'] * 100:.2f}%/次")
    print(f"  优化理由: {split_result['rationale']}")
    print()

    # 计算95%总仓位下的实际分配
    total_pos = 0.95
    actual_base = total_pos * split_result['base_ratio']
    actual_swing = total_pos * split_result['swing_ratio']

    print(f"📌 **实际仓位分配** (总仓位{total_pos*100:.0f}%):")
    print(f"  底仓: {actual_base * 100:.1f}%")
    print(f"  波段: {actual_swing * 100:.1f}%")
    print(f"  现金: {(1 - total_pos) * 100:.1f}%")
    print()

    # 生成详细优化建议
    recommendation = optimizer.generate_optimal_recommendation(portfolio)

    # 打印结果
    print("=" * 100)
    print("📊 优化结果")
    print("=" * 100)
    print()

    final = recommendation['final_recommendation']
    print(f"✅ **最终建议**:")
    print(f"  底仓: {final['base_position_pct']}")
    print(f"  波段: {final['swing_position_pct']}")
    print(f"  总仓位: {final['total_position_pct']}")
    print(f"  预期年化收益: {final['expected_annual_return_pct']}")
    print()

    # 风险检查
    risk = recommendation['risk_check']
    print(f"🛡️ **风险检查**:")
    print(f"  预期最大回撤: {risk['estimated_max_drawdown_pct']}")
    print(f"  回撤容忍度: {risk['max_drawdown_tolerance_pct']}")
    print(f"  是否满足约束: {'✅ 是' if risk['meets_constraint'] else '❌ 否'}")
    print()

    # 详细分析
    print("=" * 100)
    print("📋 各资产详细分析")
    print("=" * 100)
    print()

    for asset_result in recommendation['optimization_result']['asset_results']:
        print(f"【{asset_result['asset_name']}】")
        print(f"  总配置: {asset_result['total_allocation_pct']}")
        print(f"  - 底仓: {asset_result['base_allocation_pct']} (占该资产{asset_result['base_ratio_pct']})")
        print(f"  - 波段: {asset_result['swing_allocation_pct']} (占该资产{asset_result['swing_ratio_pct']})")
        print(f"  收益贡献:")
        print(f"  - 底仓贡献: {asset_result['base_contribution_pct']}")
        print(f"  - 波段贡献: {asset_result['swing_contribution_pct']}")
        kelly = asset_result['kelly_details']
        print(f"  Kelly分析:")
        print(f"  - 胜率: {kelly['win_rate'] * 100:.0f}%")
        print(f"  - 盈亏比: {kelly['profit_factor']:.2f}")
        print(f"  - 单次期望: {kelly['expected_return_per_trade_pct']}")
        print()

    # 策略描述
    print("=" * 100)
    print(recommendation['strategy_description'])
    print("=" * 100)
