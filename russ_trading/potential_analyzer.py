"""
潜在空间评估模块

基于历史牛市数据,评估各指数的上涨潜力:
1. 沪深300: 历史涨幅1.69-4.82倍
2. 创业板: 历史涨幅1.97-3.33倍
3. 科创50: 历史涨幅1.7倍
4. 计算风险收益比
5. 评估当前位置的投资价值
"""

from typing import Dict, List
from datetime import datetime


class PotentialAnalyzer:
    """潜在空间分析器"""

    # 历史牛市涨幅数据
    HISTORICAL_BULL_DATA = {
        'HS300': {
            'name': '沪深300',
            'current_base': 3145,  # 2025年起点
            'bull_markets': [
                {'year': '2008', 'low': 1221, 'high': 5891, 'multiple': 4.82},
                {'year': '2015', 'low': 2077, 'high': 5380, 'multiple': 2.59},
                {'year': '2021', 'low': 3503, 'high': 5930, 'multiple': 1.69}
            ],
            'avg_multiple': 3.03,  # 平均涨幅
            'conservative_multiple': 1.69,  # 保守估计
            'optimistic_multiple': 4.82   # 乐观估计
        },
        'CYBZ': {
            'name': '创业板指',
            'current_base': 2060,  # 2025年起点
            'bull_markets': [
                {'year': '2015', 'low': 1200, 'high': 4000, 'multiple': 3.33},
                {'year': '2021', 'low': 1817, 'high': 3576, 'multiple': 1.97}
            ],
            'avg_multiple': 2.65,
            'conservative_multiple': 1.97,
            'optimistic_multiple': 3.33
        },
        'KECHUANG50': {
            'name': '科创50',
            'current_base': 955,  # 2025年起点
            'bull_markets': [
                {'year': '2021', 'low': 1000, 'high': 1700, 'multiple': 1.70}
            ],
            'avg_multiple': 1.70,
            'conservative_multiple': 1.70,
            'optimistic_multiple': 2.50  # 假设科创有更大潜力
        }
    }

    def __init__(self):
        """初始化潜在空间分析器"""
        pass

    def analyze_potential(
        self,
        asset_key: str,
        current_price: float,
        scenario: str = 'all'
    ) -> Dict:
        """
        分析资产的潜在空间

        Args:
            asset_key: 资产代码 ('HS300', 'CYBZ', 'KECHUANG50')
            current_price: 当前点位
            scenario: 场景选择 ('conservative'保守, 'average'平均, 'optimistic'乐观, 'all'全部)

        Returns:
            潜在空间分析结果
        """
        if asset_key not in self.HISTORICAL_BULL_DATA:
            return {
                'error': f'不支持的资产代码: {asset_key}',
                'supported_assets': list(self.HISTORICAL_BULL_DATA.keys())
            }

        data = self.HISTORICAL_BULL_DATA[asset_key]
        base_price = data['current_base']

        # 计算当前位置相对于基准的涨跌
        from_base_return = (current_price - base_price) / base_price
        from_base_return_pct = from_base_return * 100

        results = {
            'asset_key': asset_key,
            'asset_name': data['name'],
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'base_price': base_price,
            'current_price': current_price,
            'from_base_return': from_base_return,
            'from_base_return_pct': f"{from_base_return_pct:.2f}%",
            'historical_data': data['bull_markets'],
            'scenarios': {},
            'risk_reward_ratio': {},
            'recommendations': []
        }

        # 计算各场景目标位
        scenarios_to_calc = ['conservative', 'average', 'optimistic'] if scenario == 'all' else [scenario]

        for scen in scenarios_to_calc:
            if scen == 'conservative':
                multiple = data['conservative_multiple']
                label = '保守场景'
            elif scen == 'average':
                multiple = data['avg_multiple']
                label = '平均场景'
            elif scen == 'optimistic':
                multiple = data['optimistic_multiple']
                label = '乐观场景'
            else:
                continue

            target_price = current_price * multiple
            upside = (target_price - current_price) / current_price
            upside_pct = upside * 100

            results['scenarios'][scen] = {
                'label': label,
                'multiple': multiple,
                'target_price': target_price,
                'target_price_text': f"{target_price:.0f}",
                'upside': upside,
                'upside_pct': f"{upside_pct:.1f}%",
                'description': self._get_scenario_description(scen, multiple)
            }

        # 计算风险收益比
        # 假设回撤风险为20%,计算各场景的风险收益比
        downside_risk = 0.20
        for scen, scen_data in results['scenarios'].items():
            upside = scen_data['upside']
            risk_reward = upside / downside_risk
            results['risk_reward_ratio'][scen] = {
                'ratio': risk_reward,
                'ratio_text': f"{risk_reward:.2f}",
                'evaluation': self._evaluate_risk_reward(risk_reward)
            }

        # 生成投资建议
        results['recommendations'] = self._generate_recommendations(
            asset_key,
            current_price,
            base_price,
            results['scenarios'],
            results['risk_reward_ratio']
        )

        return results

    def analyze_multiple_assets(
        self,
        assets: List[Dict],
        scenario: str = 'average'
    ) -> Dict:
        """
        批量分析多个资产的潜在空间

        Args:
            assets: 资产列表,每个资产包含:
                - asset_key: 资产代码
                - current_price: 当前点位
            scenario: 场景选择

        Returns:
            批量分析结果
        """
        results = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'scenario': scenario,
            'assets': {},
            'comparison': None
        }

        # 逐个分析
        for asset in assets:
            asset_key = asset['asset_key']
            current_price = asset['current_price']

            analysis = self.analyze_potential(asset_key, current_price, scenario)
            if 'error' not in analysis:
                results['assets'][asset_key] = analysis

        # 生成对比
        if len(results['assets']) > 1:
            results['comparison'] = self._generate_comparison(results['assets'], scenario)

        return results

    def _get_scenario_description(self, scenario: str, multiple: float) -> str:
        """获取场景描述"""
        descriptions = {
            'conservative': f'基于历史最低涨幅{multiple:.2f}倍,适合稳健投资者',
            'average': f'基于历史平均涨幅{multiple:.2f}倍,作为中性预期',
            'optimistic': f'基于历史最高涨幅{multiple:.2f}倍,适合进取投资者'
        }
        return descriptions.get(scenario, '')

    def _evaluate_risk_reward(self, ratio: float) -> str:
        """评估风险收益比"""
        if ratio >= 3.0:
            return '优秀 (风险收益比≥3)'
        elif ratio >= 2.0:
            return '良好 (风险收益比2-3)'
        elif ratio >= 1.0:
            return '中等 (风险收益比1-2)'
        else:
            return '较低 (风险收益比<1)'

    def _generate_recommendations(
        self,
        asset_key: str,
        current_price: float,
        base_price: float,
        scenarios: Dict,
        risk_reward_ratios: Dict
    ) -> List[str]:
        """生成投资建议"""
        recommendations = []

        # 判断当前位置
        from_base_return = (current_price - base_price) / base_price

        if from_base_return < -0.10:
            recommendations.append("✅ 当前位置显著低于年初,处于较好的买入区域")
        elif from_base_return < 0:
            recommendations.append("✅ 当前位置略低于年初,性价比尚可")
        elif from_base_return < 0.20:
            recommendations.append("⚖️ 当前位置略高于年初,建议控制仓位")
        else:
            recommendations.append("⚠️ 当前位置显著高于年初,建议谨慎追高")

        # 根据风险收益比给建议
        avg_scenario = scenarios.get('average', scenarios.get('conservative'))
        avg_rr = risk_reward_ratios.get('average', risk_reward_ratios.get('conservative'))

        if avg_rr and avg_rr['ratio'] >= 2.0:
            recommendations.append(
                f"📈 {avg_scenario['label']}下目标位{avg_scenario['target_price_text']},"
                f"上涨空间{avg_scenario['upside_pct']},值得关注"
            )
        elif avg_rr and avg_rr['ratio'] >= 1.0:
            recommendations.append(
                f"⚖️ {avg_scenario['label']}下目标位{avg_scenario['target_price_text']},"
                f"上涨空间{avg_scenario['upside_pct']},适度配置"
            )

        # 特定资产建议
        if asset_key == 'CYBZ':
            recommendations.append("💡 创业板具备翻倍潜力,适合作为核心配置")
        elif asset_key == 'KECHUANG50':
            recommendations.append("💡 科创板可能复刻2015年创业板行情,值得重点关注")
        elif asset_key == 'HS300':
            recommendations.append("💡 沪深300作为大盘基准,适合作为底仓配置")

        return recommendations

    def _generate_comparison(self, assets_data: Dict, scenario: str) -> Dict:
        """生成资产对比"""
        comparison = {
            'scenario': scenario,
            'ranking': []
        }

        # 按上涨空间排序
        for asset_key, data in assets_data.items():
            scen_data = data['scenarios'].get(scenario, {})
            if scen_data:
                comparison['ranking'].append({
                    'asset_key': asset_key,
                    'asset_name': data['asset_name'],
                    'current_price': data['current_price'],
                    'target_price': scen_data['target_price'],
                    'upside_pct': scen_data['upside_pct'],
                    'upside': scen_data['upside']
                })

        # 排序:按上涨空间降序
        comparison['ranking'].sort(key=lambda x: x['upside'], reverse=True)

        return comparison

    def format_potential_report(
        self,
        result: Dict,
        format_type: str = 'markdown',
        single_asset: bool = True
    ) -> str:
        """
        格式化潜在空间报告

        Args:
            result: analyze_potential() 或 analyze_multiple_assets() 的结果
            format_type: 报告格式 ('markdown' 或 'text')
            single_asset: 是否为单资产报告

        Returns:
            格式化后的报告文本
        """
        if format_type == 'markdown':
            if single_asset:
                return self._format_single_markdown_report(result)
            else:
                return self._format_multiple_markdown_report(result)
        else:
            if single_asset:
                return self._format_single_text_report(result)
            else:
                return self._format_multiple_text_report(result)

    def _format_single_markdown_report(self, result: Dict) -> str:
        """生成单资产Markdown报告"""
        lines = []

        lines.append(f"## 🚀 潜在空间评估 - {result['asset_name']}")
        lines.append("")
        lines.append(f"**分析日期**: {result['analysis_date']}")
        lines.append("")

        # 当前位置
        lines.append("### 当前位置")
        lines.append("")
        lines.append(f"- **基准点位** (2025年初): {result['base_price']:.0f}")
        lines.append(f"- **当前点位**: {result['current_price']:.0f}")
        lines.append(f"- **相对基准涨跌**: {result['from_base_return_pct']}")
        lines.append("")

        # 历史牛市数据
        lines.append("### 📊 历史牛市涨幅")
        lines.append("")
        lines.append("| 年份 | 底部 | 顶部 | 涨幅倍数 |")
        lines.append("|------|------|------|---------|")

        for bull in result['historical_data']:
            lines.append(
                f"| {bull['year']} | {bull['low']} | {bull['high']} | "
                f"**{bull['multiple']:.2f}倍** |"
            )
        lines.append("")

        # 各场景目标位
        lines.append("### 🎯 各场景目标位预测")
        lines.append("")
        lines.append("| 场景 | 涨幅倍数 | 目标点位 | 上涨空间 | 风险收益比 |")
        lines.append("|------|---------|---------|---------|-----------|")

        for scen_key, scen_data in result['scenarios'].items():
            rr_data = result['risk_reward_ratio'].get(scen_key, {})
            rr_text = rr_data.get('ratio_text', '-') if rr_data else '-'
            rr_eval = rr_data.get('evaluation', '') if rr_data else ''

            lines.append(
                f"| {scen_data['label']} | {scen_data['multiple']:.2f}倍 | "
                f"{scen_data['target_price_text']} | {scen_data['upside_pct']} | "
                f"{rr_text} ({rr_eval}) |"
            )
        lines.append("")

        # 场景说明
        lines.append("### 📖 场景说明")
        lines.append("")
        for scen_key, scen_data in result['scenarios'].items():
            lines.append(f"**{scen_data['label']}**: {scen_data['description']}")
        lines.append("")

        # 投资建议
        if result['recommendations']:
            lines.append("### 💡 投资建议")
            lines.append("")
            for rec in result['recommendations']:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)

    def _format_multiple_markdown_report(self, result: Dict) -> str:
        """生成多资产对比Markdown报告"""
        lines = []

        lines.append("## 🚀 潜在空间对比评估")
        lines.append("")
        lines.append(f"**分析日期**: {result['analysis_date']}")
        lines.append(f"**场景**: {result['scenario']}")
        lines.append("")

        # 对比排名
        if result['comparison']:
            lines.append("### 📊 上涨空间排名")
            lines.append("")
            lines.append("| 排名 | 指数 | 当前点位 | 目标点位 | 上涨空间 |")
            lines.append("|------|------|---------|---------|---------|")

            for i, item in enumerate(result['comparison']['ranking'], 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                lines.append(
                    f"| {emoji} | {item['asset_name']} | {item['current_price']:.0f} | "
                    f"{item['target_price']:.0f} | **{item['upside_pct']}** |"
                )
            lines.append("")

        # 各资产详情
        lines.append("### 📈 各指数详细分析")
        lines.append("")

        for asset_key, asset_data in result['assets'].items():
            lines.append(f"#### {asset_data['asset_name']}")
            lines.append("")
            lines.append(f"- **当前点位**: {asset_data['current_price']:.0f}")
            lines.append(f"- **相对年初**: {asset_data['from_base_return_pct']}")

            scenario_key = result['scenario']
            if scenario_key in asset_data['scenarios']:
                scen = asset_data['scenarios'][scenario_key]
                lines.append(f"- **目标点位**: {scen['target_price_text']}")
                lines.append(f"- **上涨空间**: {scen['upside_pct']}")

            if asset_data['recommendations']:
                lines.append(f"- **建议**: {asset_data['recommendations'][0]}")

            lines.append("")

        return "\n".join(lines)

    def _format_single_text_report(self, result: Dict) -> str:
        """生成单资产纯文本报告"""
        lines = []

        lines.append("=" * 60)
        lines.append(f"潜在空间评估 - {result['asset_name']}")
        lines.append("=" * 60)
        lines.append(f"分析日期: {result['analysis_date']}")
        lines.append("")

        lines.append("当前位置:")
        lines.append(f"  基准点位: {result['base_price']:.0f}")
        lines.append(f"  当前点位: {result['current_price']:.0f}")
        lines.append(f"  相对涨跌: {result['from_base_return_pct']}")
        lines.append("")

        lines.append("各场景目标位:")
        for scen_key, scen_data in result['scenarios'].items():
            lines.append(f"  {scen_data['label']}: {scen_data['target_price_text']} (上涨空间{scen_data['upside_pct']})")
        lines.append("")

        lines.append("投资建议:")
        for rec in result['recommendations']:
            lines.append(f"  - {rec}")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _format_multiple_text_report(self, result: Dict) -> str:
        """生成多资产对比纯文本报告"""
        lines = []

        lines.append("=" * 60)
        lines.append("潜在空间对比评估")
        lines.append("=" * 60)
        lines.append(f"分析日期: {result['analysis_date']}")
        lines.append("")

        if result['comparison']:
            lines.append("上涨空间排名:")
            for i, item in enumerate(result['comparison']['ranking'], 1):
                lines.append(f"  {i}. {item['asset_name']}: {item['upside_pct']}")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


# 示例用法
if __name__ == "__main__":
    analyzer = PotentialAnalyzer()

    # 单个资产分析
    result = analyzer.analyze_potential('CYBZ', 2993.45, scenario='all')
    report = analyzer.format_potential_report(result, format_type='markdown', single_asset=True)
    print(report)
    print("\n" + "=" * 80 + "\n")

    # 多资产对比
    assets = [
        {'asset_key': 'HS300', 'current_price': 4538.22},
        {'asset_key': 'CYBZ', 'current_price': 2993.45},
        {'asset_key': 'KECHUANG50', 'current_price': 1367.90}
    ]
    result_multi = analyzer.analyze_multiple_assets(assets, scenario='average')
    report_multi = analyzer.format_potential_report(result_multi, format_type='markdown', single_asset=False)
    print(report_multi)
