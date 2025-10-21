"""
持仓健康度检查模块

基于用户的投资策略,检查持仓是否符合以下规则:
1. 仓位控制在5-9成(50%-90%)
2. 单一ETF仓位不超过30%, 单一个股仓位不超过20%
3. 预留至少1成(10%)应对黑天鹅事件
4. 标的数量控制在3-5只
"""

from typing import Dict, List, Tuple
from datetime import datetime


class PositionHealthChecker:
    """持仓健康度检查器"""

    def __init__(self, strategy_config: Dict = None):
        """
        初始化持仓健康度检查器

        Args:
            strategy_config: 策略配置字典,包含:
                - min_position: 最小仓位 (默认50%)
                - max_position: 最大仓位 (默认90%)
                - max_single_position_etf: 单一ETF最大仓位 (默认30%)
                - max_single_position_stock: 单一个股最大仓位 (默认20%)
                - black_swan_reserve: 黑天鹅预留 (默认10%)
                - min_assets: 最少标的数量 (默认3)
                - max_assets: 最多标的数量 (默认5)
        """
        if strategy_config is None:
            strategy_config = {}

        self.min_position = strategy_config.get('min_position', 0.50)
        self.max_position = strategy_config.get('max_position', 0.90)
        self.max_single_position_etf = strategy_config.get('max_single_position_etf', 0.30)
        self.max_single_position_stock = strategy_config.get('max_single_position_stock', 0.20)
        self.black_swan_reserve = strategy_config.get('black_swan_reserve', 0.10)
        self.min_assets = strategy_config.get('min_assets', 3)
        self.max_assets = strategy_config.get('max_assets', 5)

    def check_position_health(self, positions: List[Dict]) -> Dict:
        """
        检查持仓健康度

        Args:
            positions: 持仓列表,每个持仓包含:
                - asset_name: 标的名称
                - asset_key: 标的代码
                - position_ratio: 持仓占比 (0-1之间)
                - current_value: 当前市值

        Returns:
            健康度检查结果字典
        """
        # 计算总仓位
        total_position = sum(p['position_ratio'] for p in positions)

        # 计算现金预留
        cash_reserve = 1.0 - total_position

        # 检查各项指标
        results = {
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'total_position': total_position,
            'total_position_pct': f"{total_position * 100:.1f}%",
            'cash_reserve': cash_reserve,
            'cash_reserve_pct': f"{cash_reserve * 100:.1f}%",
            'asset_count': len(positions),
            'positions': positions,
            'checks': {},
            'warnings': [],
            'suggestions': [],
            'health_score': 100.0,  # 初始健康分100分
            'health_level': 'excellent'  # excellent/good/warning/danger
        }

        # 1. 检查总仓位
        position_check = self._check_total_position(total_position)
        results['checks']['total_position'] = position_check
        if not position_check['passed']:
            results['warnings'].append(position_check['message'])
            results['suggestions'].extend(position_check['suggestions'])
            results['health_score'] -= position_check['penalty']

        # 2. 检查现金预留
        reserve_check = self._check_cash_reserve(cash_reserve)
        results['checks']['cash_reserve'] = reserve_check
        if not reserve_check['passed']:
            results['warnings'].append(reserve_check['message'])
            results['suggestions'].extend(reserve_check['suggestions'])
            results['health_score'] -= reserve_check['penalty']

        # 3. 检查单一标的仓位
        single_position_check = self._check_single_positions(positions)
        results['checks']['single_positions'] = single_position_check
        if not single_position_check['passed']:
            results['warnings'].extend(single_position_check['warnings'])
            results['suggestions'].extend(single_position_check['suggestions'])
            results['health_score'] -= single_position_check['penalty']

        # 4. 检查标的数量
        asset_count_check = self._check_asset_count(len(positions))
        results['checks']['asset_count'] = asset_count_check
        if not asset_count_check['passed']:
            results['warnings'].append(asset_count_check['message'])
            results['suggestions'].extend(asset_count_check['suggestions'])
            results['health_score'] -= asset_count_check['penalty']

        # 5. 确定健康等级
        results['health_level'] = self._determine_health_level(results['health_score'])

        return results

    def _check_total_position(self, total_position: float) -> Dict:
        """检查总仓位是否在合理区间"""
        if total_position < self.min_position:
            return {
                'passed': False,
                'message': f"⚠️ 总仓位{total_position*100:.1f}%偏低,低于最低建议{self.min_position*100:.0f}%",
                'suggestions': [
                    f"建议加仓至{self.min_position*100:.0f}%-{self.max_position*100:.0f}%区间",
                    "可以考虑在市场回调时逐步建仓"
                ],
                'penalty': 15.0
            }
        elif total_position > self.max_position:
            return {
                'passed': False,
                'message': f"🚨 总仓位{total_position*100:.1f}%偏高,超过最高建议{self.max_position*100:.0f}%",
                'suggestions': [
                    f"建议减仓至{self.max_position*100:.0f}%以下",
                    "可以考虑在超买品种上止盈",
                    "为市场回调预留加仓空间"
                ],
                'penalty': 20.0
            }
        else:
            return {
                'passed': True,
                'message': f"✅ 总仓位{total_position*100:.1f}%在合理区间({self.min_position*100:.0f}%-{self.max_position*100:.0f}%)",
                'suggestions': [],
                'penalty': 0
            }

    def _check_cash_reserve(self, cash_reserve: float) -> Dict:
        """检查现金预留是否充足"""
        if cash_reserve < self.black_swan_reserve:
            return {
                'passed': False,
                'message': f"🚨 现金预留{cash_reserve*100:.1f}%不足,低于最低要求{self.black_swan_reserve*100:.0f}%",
                'suggestions': [
                    f"建议保留至少{self.black_swan_reserve*100:.0f}%现金应对黑天鹅事件",
                    "可以考虑止盈部分盈利品种"
                ],
                'penalty': 25.0
            }
        else:
            return {
                'passed': True,
                'message': f"✅ 现金预留{cash_reserve*100:.1f}%充足,满足{self.black_swan_reserve*100:.0f}%最低要求",
                'suggestions': [],
                'penalty': 0
            }

    def _is_etf(self, asset_name: str, asset_key: str) -> bool:
        """判断是否为ETF"""
        # ETF判断逻辑: 名称包含ETF，或代码符合ETF特征
        if 'ETF' in asset_name.upper():
            return True
        # 常见ETF代码特征
        etf_code_patterns = ['51', '56', '58', '15']  # A股ETF常见代码开头
        for pattern in etf_code_patterns:
            if asset_key.startswith(pattern):
                return True
        return False

    def _check_single_positions(self, positions: List[Dict]) -> Dict:
        """检查单一标的仓位(ETF和个股分开限制)"""
        warnings = []
        suggestions = []
        penalty = 0

        overweight_assets = []
        for pos in positions:
            is_etf = self._is_etf(pos['asset_name'], pos.get('asset_key', ''))
            max_limit = self.max_single_position_etf if is_etf else self.max_single_position_stock
            asset_type = "ETF" if is_etf else "个股"

            if pos['position_ratio'] > max_limit:
                overweight_assets.append({
                    'name': pos['asset_name'],
                    'type': asset_type,
                    'ratio': pos['position_ratio'],
                    'limit': max_limit,
                    'excess': pos['position_ratio'] - max_limit
                })
                warnings.append(
                    f"⚠️ {pos['asset_name']}({asset_type})仓位{pos['position_ratio']*100:.1f}%超过{max_limit*100:.0f}%限制"
                )
                penalty += 10.0

        if overweight_assets:
            suggestions.append(f"建议将ETF仓位控制在{self.max_single_position_etf*100:.0f}%以内, 个股控制在{self.max_single_position_stock*100:.0f}%以内")
            for asset in overweight_assets:
                excess_pct = asset['excess'] * 100
                suggestions.append(f"- {asset['name']}({asset['type']}): 建议减仓{excess_pct:.1f}%")

            return {
                'passed': False,
                'warnings': warnings,
                'suggestions': suggestions,
                'overweight_assets': overweight_assets,
                'penalty': min(penalty, 30.0)  # 最多扣30分
            }
        else:
            return {
                'passed': True,
                'warnings': [],
                'suggestions': [],
                'overweight_assets': [],
                'penalty': 0
            }

    def _check_asset_count(self, asset_count: int) -> Dict:
        """检查标的数量"""
        if asset_count < self.min_assets:
            return {
                'passed': False,
                'message': f"⚠️ 持仓标的数量{asset_count}只偏少,建议{self.min_assets}-{self.max_assets}只",
                'suggestions': [
                    f"建议增加标的至{self.min_assets}-{self.max_assets}只",
                    "过度集中可能增加风险"
                ],
                'penalty': 10.0
            }
        elif asset_count > self.max_assets:
            return {
                'passed': False,
                'message': f"⚠️ 持仓标的数量{asset_count}只偏多,建议{self.min_assets}-{self.max_assets}只",
                'suggestions': [
                    f"建议减少标的至{self.min_assets}-{self.max_assets}只",
                    "过度分散可能降低收益"
                ],
                'penalty': 10.0
            }
        else:
            return {
                'passed': True,
                'message': f"✅ 持仓标的数量{asset_count}只在合理区间({self.min_assets}-{self.max_assets}只)",
                'suggestions': [],
                'penalty': 0
            }

    def _determine_health_level(self, score: float) -> str:
        """根据健康分确定健康等级"""
        if score >= 90:
            return 'excellent'  # 优秀
        elif score >= 70:
            return 'good'  # 良好
        elif score >= 50:
            return 'warning'  # 警告
        else:
            return 'danger'  # 危险

    def format_health_report(self, health_result: Dict, format_type: str = 'markdown') -> str:
        """
        格式化健康度报告

        Args:
            health_result: check_position_health()返回的结果
            format_type: 报告格式 ('markdown' 或 'text')

        Returns:
            格式化后的报告文本
        """
        if format_type == 'markdown':
            return self._format_markdown_health_report(health_result)
        else:
            return self._format_text_health_report(health_result)

    def _format_markdown_health_report(self, result: Dict) -> str:
        """生成Markdown格式的健康度报告"""
        lines = []

        # 标题(不要重复,外层已有"持仓健康度诊断")
        lines.append(f"**检查时间**: {result['check_time']}")
        lines.append("")

        # 健康评分
        score = result['health_score']
        level = result['health_level']
        level_emoji = {
            'excellent': '🟢',
            'good': '🟡',
            'warning': '🟠',
            'danger': '🔴'
        }
        level_text = {
            'excellent': '优秀',
            'good': '良好',
            'warning': '警告',
            'danger': '危险'
        }

        lines.append(f"### {level_emoji[level]} 健康评分: {score:.1f}分 ({level_text[level]})")
        lines.append("")

        # 持仓概况
        lines.append("### 持仓概况")
        lines.append("")
        lines.append(f"- **总仓位**: {result['total_position_pct']}")
        lines.append(f"- **现金预留**: {result['cash_reserve_pct']}")
        lines.append(f"- **标的数量**: {result['asset_count']}只")
        lines.append("")

        # 各项检查结果
        lines.append("### 检查结果")
        lines.append("")

        checks = result['checks']
        for check_name, check_result in checks.items():
            if check_name == 'single_positions':
                if check_result['passed']:
                    lines.append("✅ **单一标的仓位**: 全部符合要求(ETF≤30%, 个股≤20%)")
                else:
                    lines.append("⚠️ **单一标的仓位**: 存在超标")
                    for warning in check_result['warnings']:
                        lines.append(f"  - {warning}")
            else:
                message = check_result.get('message', '')
                if message:
                    lines.append(f"- {message}")

        lines.append("")

        # 持仓明细
        if result['positions']:
            lines.append("### 持仓明细")
            lines.append("")
            lines.append("| 标的名称 | 标的代码 | 仓位占比 | 当前市值 | 状态 |")
            lines.append("|---------|---------|---------|---------|------|")

            for pos in result['positions']:
                is_etf = self._is_etf(pos['asset_name'], pos.get('asset_key', ''))
                max_limit = self.max_single_position_etf if is_etf else self.max_single_position_stock
                status = "✅" if pos['position_ratio'] <= max_limit else "⚠️超标"
                lines.append(
                    f"| {pos['asset_name']} | {pos['asset_key']} | "
                    f"{pos['position_ratio']*100:.1f}% | "
                    f"¥{pos.get('current_value', 0):,.0f} | {status} |"
                )

            lines.append("")

        # 警告信息
        if result['warnings']:
            lines.append("### ⚠️ 警告信息")
            lines.append("")
            for warning in result['warnings']:
                lines.append(f"- {warning}")
            lines.append("")

        # 优化建议
        if result['suggestions']:
            lines.append("### 💡 优化建议")
            lines.append("")
            for suggestion in result['suggestions']:
                lines.append(f"- {suggestion}")
            lines.append("")

        # 策略原则
        lines.append("### 📖 策略原则")
        lines.append("")
        lines.append(f"- 仓位控制: {self.min_position*100:.0f}%-{self.max_position*100:.0f}%")
        lines.append(f"- 现金预留: ≥{self.black_swan_reserve*100:.0f}%")
        lines.append(f"- 单一ETF: ≤{self.max_single_position_etf*100:.0f}%")
        lines.append(f"- 单一个股: ≤{self.max_single_position_stock*100:.0f}%")
        lines.append(f"- 标的数量: {self.min_assets}-{self.max_assets}只")
        lines.append("")

        return "\n".join(lines)

    def _format_text_health_report(self, result: Dict) -> str:
        """生成纯文本格式的健康度报告"""
        lines = []

        lines.append("=" * 60)
        lines.append("持仓健康度检查报告")
        lines.append("=" * 60)
        lines.append(f"检查时间: {result['check_time']}")
        lines.append("")

        # 健康评分
        level_text = {
            'excellent': '优秀',
            'good': '良好',
            'warning': '警告',
            'danger': '危险'
        }
        lines.append(f"健康评分: {result['health_score']:.1f}分 ({level_text[result['health_level']]})")
        lines.append("")

        # 持仓概况
        lines.append("持仓概况:")
        lines.append(f"  总仓位: {result['total_position_pct']}")
        lines.append(f"  现金预留: {result['cash_reserve_pct']}")
        lines.append(f"  标的数量: {result['asset_count']}只")
        lines.append("")

        # 警告信息
        if result['warnings']:
            lines.append("警告信息:")
            for warning in result['warnings']:
                lines.append(f"  - {warning}")
            lines.append("")

        # 优化建议
        if result['suggestions']:
            lines.append("优化建议:")
            for suggestion in result['suggestions']:
                lines.append(f"  - {suggestion}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


# 示例用法
if __name__ == "__main__":
    # 创建检查器
    checker = PositionHealthChecker()

    # 示例持仓数据
    positions = [
        {
            'asset_name': '证券ETF',
            'asset_key': 'CN_SECURITIES',
            'position_ratio': 0.40,  # 40%
            'current_value': 200000
        },
        {
            'asset_name': '恒生科技',
            'asset_key': 'HKTECH',
            'position_ratio': 0.30,  # 30%
            'current_value': 150000
        },
        {
            'asset_name': '煤炭ETF',
            'asset_key': 'CN_COAL',
            'position_ratio': 0.15,  # 15%
            'current_value': 75000
        },
        {
            'asset_name': '白酒ETF',
            'asset_key': 'CN_LIQUOR',
            'position_ratio': 0.08,  # 8%
            'current_value': 40000
        }
    ]

    # 执行检查
    result = checker.check_position_health(positions)

    # 打印报告
    report = checker.format_health_report(result, format_type='markdown')
    print(report)
