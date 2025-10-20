"""
收益追踪对比模块

追踪投资收益并与基准对比:
1. 阶段性目标进度(50万→60万→70万→100万)
2. 与沪深300涨幅对比
3. 翻倍目标进度(100%涨幅)
4. 年化收益率计算
"""

from typing import Dict, Optional
from datetime import datetime
import math


class PerformanceTracker:
    """投资收益追踪器"""

    def __init__(self, targets_config: Dict = None):
        """
        初始化收益追踪器

        Args:
            targets_config: 目标配置字典,包含:
                - stage_targets: 阶段性目标列表 (默认[50万,60万,70万,100万])
                - base_date: 基准日期 (默认'2025-01-01')
                - initial_capital: 初始资金
                - target_annual_return: 目标年化收益率 (默认15%)
        """
        if targets_config is None:
            targets_config = {}

        self.stage_targets = targets_config.get('stage_targets', [500000, 600000, 700000, 1000000])
        self.base_date = targets_config.get('base_date', '2025-01-01')
        self.initial_capital = targets_config.get('initial_capital', 500000)
        self.target_annual_return = targets_config.get('target_annual_return', 0.15)

    def track_performance(
        self,
        current_capital: float,
        hs300_current: float,
        hs300_base: float = 3145.0,
        current_date: Optional[str] = None
    ) -> Dict:
        """
        追踪收益表现

        Args:
            current_capital: 当前资金
            hs300_current: 沪深300当前点位
            hs300_base: 沪深300基准点位 (2025.1.1约3145点)
            current_date: 当前日期,格式'YYYY-MM-DD'

        Returns:
            收益追踪结果字典
        """
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')

        # 计算收益率
        total_return = (current_capital - self.initial_capital) / self.initial_capital
        total_return_pct = total_return * 100

        # 计算沪深300收益率
        hs300_return = (hs300_current - hs300_base) / hs300_base
        hs300_return_pct = hs300_return * 100

        # 计算超额收益
        excess_return = total_return - hs300_return
        excess_return_pct = excess_return * 100

        # 计算年化收益率
        days = self._calculate_days(self.base_date, current_date)
        years = days / 365.0
        annual_return = self._calculate_annualized_return(total_return, years) if years > 0 else 0
        annual_return_pct = annual_return * 100

        # 翻倍进度
        double_target = self.initial_capital * 2
        double_progress = current_capital / double_target
        double_progress_pct = double_progress * 100

        # 当前阶段目标
        current_stage = self._find_current_stage(current_capital)

        results = {
            'track_date': current_date,
            'days_since_base': days,
            'years_since_base': round(years, 2),
            'current_capital': current_capital,
            'initial_capital': self.initial_capital,
            'total_return': total_return,
            'total_return_pct': f"{total_return_pct:.2f}%",
            'annual_return': annual_return,
            'annual_return_pct': f"{annual_return_pct:.2f}%",
            'target_annual_return_pct': f"{self.target_annual_return*100:.0f}%",
            'hs300_base': hs300_base,
            'hs300_current': hs300_current,
            'hs300_return': hs300_return,
            'hs300_return_pct': f"{hs300_return_pct:.2f}%",
            'excess_return': excess_return,
            'excess_return_pct': f"{excess_return_pct:.2f}%",
            'double_target': double_target,
            'double_progress': double_progress,
            'double_progress_pct': f"{double_progress_pct:.1f}%",
            'current_stage': current_stage,
            'achievements': self._calculate_achievements(current_capital, total_return, hs300_return, annual_return),
            'warnings': [],
            'suggestions': []
        }

        # 生成警告和建议
        self._generate_warnings_and_suggestions(results)

        return results

    def _calculate_days(self, start_date: str, end_date: str) -> int:
        """计算日期间隔天数"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        return (end - start).days

    def _calculate_annualized_return(self, total_return: float, years: float) -> float:
        """计算年化收益率"""
        if years <= 0:
            return 0
        return math.pow(1 + total_return, 1 / years) - 1

    def _find_current_stage(self, current_capital: float) -> Dict:
        """找到当前所处的阶段目标"""
        completed_stages = []
        next_stage = None
        current_stage_progress = 0

        for i, target in enumerate(self.stage_targets):
            if current_capital >= target:
                completed_stages.append({
                    'stage': i + 1,
                    'target': target,
                    'target_text': f"{target/10000:.0f}万",
                    'completed': True
                })
            else:
                if next_stage is None:
                    next_stage = {
                        'stage': i + 1,
                        'target': target,
                        'target_text': f"{target/10000:.0f}万",
                        'remaining': target - current_capital,
                        'remaining_text': f"{(target - current_capital)/10000:.1f}万"
                    }
                    # 计算当前阶段进度
                    if i == 0:
                        prev_target = self.initial_capital
                    else:
                        prev_target = self.stage_targets[i - 1]
                    current_stage_progress = (current_capital - prev_target) / (target - prev_target)

        return {
            'completed_stages': completed_stages,
            'completed_count': len(completed_stages),
            'total_stages': len(self.stage_targets),
            'next_stage': next_stage,
            'current_stage_progress': current_stage_progress,
            'current_stage_progress_pct': f"{current_stage_progress * 100:.1f}%"
        }

    def _calculate_achievements(
        self,
        current_capital: float,
        total_return: float,
        hs300_return: float,
        annual_return: float
    ) -> Dict:
        """计算各项成就达成情况"""
        achievements = {
            'target_100w': {
                'name': '资金达到100万',
                'achieved': current_capital >= 1000000,
                'progress': current_capital / 1000000,
                'progress_pct': f"{(current_capital / 1000000) * 100:.1f}%"
            },
            'beat_hs300': {
                'name': '跑赢沪深300',
                'achieved': total_return > hs300_return,
                'excess_return': (total_return - hs300_return) * 100,
                'excess_return_pct': f"{(total_return - hs300_return) * 100:.2f}%"
            },
            'double_capital': {
                'name': '资金翻倍(100%涨幅)',
                'achieved': total_return >= 1.0,
                'progress': (1 + total_return) / 2.0,
                'progress_pct': f"{((1 + total_return) / 2.0) * 100:.1f}%"
            },
            'annual_15pct': {
                'name': f'年化收益达到{self.target_annual_return*100:.0f}%',
                'achieved': annual_return >= self.target_annual_return,
                'current_annual': annual_return * 100,
                'current_annual_pct': f"{annual_return * 100:.2f}%"
            }
        }

        return achievements

    def _generate_warnings_and_suggestions(self, results: Dict):
        """生成警告和建议"""
        # 检查是否跑赢沪深300
        if results['excess_return'] < 0:
            results['warnings'].append(
                f"⚠️ 当前收益率落后沪深300约{abs(float(results['excess_return_pct'][:-1])):.2f}%"
            )
            results['suggestions'].append("建议复盘投资策略,考虑增加指数ETF配置")

        # 检查年化收益率
        annual_return = results['annual_return']
        if annual_return < self.target_annual_return:
            gap = (self.target_annual_return - annual_return) * 100
            results['warnings'].append(
                f"⚠️ 当前年化收益率{results['annual_return_pct']}低于目标{results['target_annual_return_pct']}"
            )
            results['suggestions'].append(f"需要提升{gap:.2f}%年化收益率才能达到目标")

        # 翻倍进度提示
        double_progress = results['double_progress']
        if double_progress < 0.3:
            results['suggestions'].append("翻倍目标进度较慢,建议关注高潜力品种")
        elif double_progress >= 0.5:
            results['suggestions'].append("翻倍目标已完成过半,继续保持!")

        # 阶段目标提示
        next_stage = results['current_stage']['next_stage']
        if next_stage:
            results['suggestions'].append(
                f"距离下一个阶段目标{next_stage['target_text']}还需{next_stage['remaining_text']}"
            )

    def format_performance_report(self, result: Dict, format_type: str = 'markdown') -> str:
        """
        格式化收益追踪报告

        Args:
            result: track_performance()返回的结果
            format_type: 报告格式 ('markdown' 或 'text')

        Returns:
            格式化后的报告文本
        """
        if format_type == 'markdown':
            return self._format_markdown_report(result)
        else:
            return self._format_text_report(result)

    def _format_markdown_report(self, result: Dict) -> str:
        """生成Markdown格式的收益报告"""
        lines = []

        # 标题
        lines.append("## 📈 收益追踪对比")
        lines.append("")
        lines.append(f"**追踪日期**: {result['track_date']}")
        lines.append(f"**基准日期**: {self.base_date} (已运行{result['days_since_base']}天/{result['years_since_base']}年)")
        lines.append("")

        # 收益概况
        lines.append("### 收益概况")
        lines.append("")
        lines.append(f"- **初始资金**: ¥{result['initial_capital']:,.0f}")
        lines.append(f"- **当前资金**: ¥{result['current_capital']:,.0f}")
        lines.append(f"- **总收益率**: {result['total_return_pct']}")
        lines.append(f"- **年化收益率**: {result['annual_return_pct']}")
        lines.append(f"- **目标年化**: {result['target_annual_return_pct']}")
        lines.append("")

        # 基准对比
        lines.append("### 📊 基准对比(沪深300)")
        lines.append("")
        lines.append("| 指标 | 我的收益 | 沪深300 | 超额收益 |")
        lines.append("|------|---------|---------|---------|")
        lines.append(
            f"| 总收益率 | {result['total_return_pct']} | "
            f"{result['hs300_return_pct']} | {result['excess_return_pct']} |"
        )

        excess = float(result['excess_return_pct'][:-1])
        if excess > 0:
            lines.append(f"\n✅ **跑赢沪深300约{excess:.2f}%!**")
        else:
            lines.append(f"\n⚠️ **落后沪深300约{abs(excess):.2f}%**")
        lines.append("")

        # 三大目标达成情况
        lines.append("### 🎯 三大目标达成情况")
        lines.append("")

        achievements = result['achievements']

        # 目标1: 100万
        target_100w = achievements['target_100w']
        status_emoji = "✅" if target_100w['achieved'] else "🔄"
        lines.append(f"#### {status_emoji} 目标1: 资金达到100万")
        lines.append(f"- 当前进度: {target_100w['progress_pct']}")
        if not target_100w['achieved']:
            remaining = 1000000 - result['current_capital']
            lines.append(f"- 还需: ¥{remaining:,.0f} ({remaining/10000:.1f}万)")
        lines.append("")

        # 目标2: 跑赢沪深300
        beat_hs300 = achievements['beat_hs300']
        status_emoji = "✅" if beat_hs300['achieved'] else "❌"
        lines.append(f"#### {status_emoji} 目标2: 跑赢沪深300")
        if beat_hs300['achieved']:
            lines.append(f"- 超额收益: {beat_hs300['excess_return_pct']}")
        else:
            lines.append(f"- 落后幅度: {beat_hs300['excess_return_pct']}")
        lines.append("")

        # 目标3: 翻倍
        double = achievements['double_capital']
        status_emoji = "✅" if double['achieved'] else "🔄"
        lines.append(f"#### {status_emoji} 目标3: 资金翻倍(100%涨幅)")
        lines.append(f"- 当前进度: {double['progress_pct']}")
        lines.append(f"- 翻倍目标: ¥{result['double_target']:,.0f}")
        if not double['achieved']:
            remaining = result['double_target'] - result['current_capital']
            lines.append(f"- 还需: ¥{remaining:,.0f} ({remaining/10000:.1f}万)")
        lines.append("")

        # 阶段性目标
        lines.append("### 🏆 阶段性目标进度")
        lines.append("")

        stage_info = result['current_stage']
        completed_count = stage_info['completed_count']
        total_stages = stage_info['total_stages']

        lines.append(f"**已完成阶段**: {completed_count}/{total_stages}")
        lines.append("")

        # 已完成的阶段
        if stage_info['completed_stages']:
            for stage in stage_info['completed_stages']:
                lines.append(f"- ✅ 阶段{stage['stage']}: {stage['target_text']}")
            lines.append("")

        # 当前阶段
        if stage_info['next_stage']:
            next_stage = stage_info['next_stage']
            lines.append(f"**当前阶段**: 第{next_stage['stage']}阶段 - 目标{next_stage['target_text']}")
            lines.append(f"- 进度: {stage_info['current_stage_progress_pct']}")
            lines.append(f"- 还需: {next_stage['remaining_text']}")
            lines.append("")
        else:
            lines.append("🎉 **恭喜!所有阶段目标已完成!**")
            lines.append("")

        # 警告信息
        if result['warnings']:
            lines.append("### ⚠️ 注意事项")
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

        return "\n".join(lines)

    def _format_text_report(self, result: Dict) -> str:
        """生成纯文本格式的收益报告"""
        lines = []

        lines.append("=" * 60)
        lines.append("收益追踪对比报告")
        lines.append("=" * 60)
        lines.append(f"追踪日期: {result['track_date']}")
        lines.append(f"运行天数: {result['days_since_base']}天")
        lines.append("")

        lines.append("收益概况:")
        lines.append(f"  当前资金: ¥{result['current_capital']:,.0f}")
        lines.append(f"  总收益率: {result['total_return_pct']}")
        lines.append(f"  年化收益: {result['annual_return_pct']}")
        lines.append("")

        lines.append("基准对比:")
        lines.append(f"  我的收益: {result['total_return_pct']}")
        lines.append(f"  沪深300: {result['hs300_return_pct']}")
        lines.append(f"  超额收益: {result['excess_return_pct']}")
        lines.append("")

        lines.append("三大目标:")
        achievements = result['achievements']
        lines.append(f"  [{'√' if achievements['target_100w']['achieved'] else ' '}] 资金达到100万 ({achievements['target_100w']['progress_pct']})")
        lines.append(f"  [{'√' if achievements['beat_hs300']['achieved'] else ' '}] 跑赢沪深300 ({achievements['beat_hs300']['excess_return_pct']})")
        lines.append(f"  [{'√' if achievements['double_capital']['achieved'] else ' '}] 资金翻倍 ({achievements['double_capital']['progress_pct']})")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


# 示例用法
if __name__ == "__main__":
    # 创建追踪器
    tracker = PerformanceTracker({
        'initial_capital': 500000,  # 50万起步
        'base_date': '2025-01-01',
        'target_annual_return': 0.15  # 15%年化
    })

    # 追踪当前收益
    result = tracker.track_performance(
        current_capital=550000,  # 当前55万
        hs300_current=4538.22,   # 沪深300当前点位
        hs300_base=3145.0,       # 2025.1.1基准点位
        current_date='2025-10-20'
    )

    # 打印报告
    report = tracker.format_performance_report(result, format_type='markdown')
    print(report)
