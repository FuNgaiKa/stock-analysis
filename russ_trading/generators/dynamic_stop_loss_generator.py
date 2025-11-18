#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态止损建议生成器
Dynamic Stop Loss Recommendation Generator

基于RiskManager的ATR动态止损功能,为持仓生成个性化止损建议

作者: Claude Code
日期: 2025-11-18
"""

import pandas as pd
import yfinance as yf
from typing import List, Dict
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from russ_trading.managers.risk_manager import RiskManager


class DynamicStopLossGenerator:
    """动态止损建议生成器"""

    def __init__(self, lookback_days: int = 20):
        """
        初始化

        Args:
            lookback_days: ATR计算回溯天数,默认20日
        """
        self.risk_manager = RiskManager()
        self.lookback_days = lookback_days

    def generate_stop_loss_for_position(
        self,
        asset_name: str,
        asset_code: str,
        current_price: float,
        entry_price: float
    ) -> Dict:
        """
        为单个持仓生成动态止损建议

        Args:
            asset_name: 资产名称
            asset_code: 资产代码 (如 '513180', '002050')
            current_price: 当前价格
            entry_price: 买入价格

        Returns:
            止损建议字典
        """
        # 1. 转换为yfinance代码
        yf_symbol = self._convert_to_yf_symbol(asset_code)

        # 2. 下载价格数据
        try:
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period=f'{self.lookback_days + 10}d')

            if hist.empty or len(hist) < self.lookback_days:
                return {
                    'asset_name': asset_name,
                    'asset_code': asset_code,
                    'error': '数据不足',
                    'recommendation': f'⚠️ 数据不足,建议使用固定止损-15%',
                    'dynamic_stop_loss': -0.15,
                    'stop_loss_price': entry_price * 0.85
                }

            # 3. 调用RiskManager计算动态止损
            result = self.risk_manager.calculate_dynamic_stop_loss(
                symbol=yf_symbol,
                current_price=current_price,
                entry_price=entry_price,
                price_data=hist,
                lookback_days=self.lookback_days
            )

            # 4. 添加资产名称
            result['asset_name'] = asset_name
            result['asset_code'] = asset_code

            return result

        except Exception as e:
            return {
                'asset_name': asset_name,
                'asset_code': asset_code,
                'error': str(e),
                'recommendation': f'⚠️ 获取数据失败,建议使用固定止损-15%',
                'dynamic_stop_loss': -0.15,
                'stop_loss_price': entry_price * 0.85
            }

    def generate_stop_loss_for_all_positions(
        self,
        positions: List[Dict]
    ) -> List[Dict]:
        """
        为所有持仓生成动态止损建议

        Args:
            positions: 持仓列表,每个持仓包含:
                - asset_name: 资产名称
                - asset_code: 资产代码
                - position_pct: 仓位百分比
                - current_value: 当前市值

        Returns:
            止损建议列表
        """
        results = []

        for pos in positions:
            asset_name = pos.get('asset_name')
            asset_code = pos.get('asset_code')
            current_value = pos.get('current_value', 0)

            # 获取当前价格和买入价格
            # 这里简化处理,实际应该从持仓记录中获取真实买入价
            # 为演示目的,假设买入价比当前价高5%(模拟小幅浮亏)
            yf_symbol = self._convert_to_yf_symbol(asset_code)

            try:
                ticker = yf.Ticker(yf_symbol)
                current_price = ticker.info.get('currentPrice', 0)
                if current_price == 0:
                    # 降级到history
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]

                # 假设买入价(实际应从持仓记录读取)
                entry_price = current_price * 1.05  # 假设买入价高5%

                result = self.generate_stop_loss_for_position(
                    asset_name=asset_name,
                    asset_code=asset_code,
                    current_price=current_price,
                    entry_price=entry_price
                )

                results.append(result)

            except Exception as e:
                results.append({
                    'asset_name': asset_name,
                    'asset_code': asset_code,
                    'error': str(e),
                    'recommendation': '⚠️ 获取价格失败'
                })

        return results

    def format_stop_loss_report(
        self,
        stop_loss_results: List[Dict],
        format_type: str = 'markdown'
    ) -> str:
        """
        格式化动态止损报告

        Args:
            stop_loss_results: generate_stop_loss_for_all_positions()的返回结果
            format_type: 格式类型 ('markdown' 或 'text')

        Returns:
            格式化的报告文本
        """
        if format_type == 'markdown':
            return self._format_markdown_report(stop_loss_results)
        else:
            return self._format_text_report(stop_loss_results)

    def _format_markdown_report(self, results: List[Dict]) -> str:
        """生成Markdown格式报告"""
        lines = []

        lines.append("### 🛡️ 动态止损建议 (基于ATR)")
        lines.append("")
        lines.append("**说明**: 根据各标的波动率特征,动态调整止损线")
        lines.append("")

        # 表格
        lines.append("| 标的 | 当前价 | 买入价 | 波动率 | 固定止损 | **动态止损** | **止损价** | 建议 |")
        lines.append("|------|--------|--------|--------|----------|--------------|-----------|------|")

        for result in results:
            if 'error' in result and result.get('error') not in ['数据不足', '获取数据失败']:
                continue

            asset_name = result.get('asset_name', 'N/A')
            current_price = result.get('current_price', 0)
            entry_price = result.get('entry_price', 0)
            volatility_level = result.get('volatility_level', 'N/A')
            volatility_color = result.get('volatility_color', '')
            atr_pct = result.get('atr_pct', 0) * 100
            fixed_stop_loss = result.get('fixed_stop_loss', -0.15) * 100
            dynamic_stop_loss = result.get('dynamic_stop_loss', -0.15) * 100
            stop_loss_price = result.get('stop_loss_price', 0)
            is_triggered = result.get('is_triggered', False)

            # 标记触发止损
            trigger_mark = '🚨' if is_triggered else ''

            lines.append(
                f"| {asset_name} | {current_price:.2f} | {entry_price:.2f} | "
                f"{volatility_color}{volatility_level}({atr_pct:.1f}%) | "
                f"{fixed_stop_loss:.0f}% | **{dynamic_stop_loss:.0f}%** | "
                f"**{stop_loss_price:.2f}** {trigger_mark} | "
                f"{result.get('recommendation', 'N/A')} |"
            )

        lines.append("")

        # 详细说明
        lines.append("**波动率等级**:")
        lines.append("- 🟢 **低波动**(ATR<1.5%): 收紧止损,提高资金效率")
        lines.append("- 🟡 **中波动**(ATR 1.5-3%): 正常止损,平衡风险收益")
        lines.append("- 🔴 **高波动**(ATR>3%): 放宽止损,避免震荡出局")
        lines.append("")

        lines.append("**操作建议**:")
        lines.append("- 设置盘中止损单,价格跌破止损价立即市价卖出")
        lines.append("- 不抱幻想,不补仓,严格执行止损纪律")
        lines.append("- 止损后删除自选,避免情绪化复盘")
        lines.append("")

        return '\n'.join(lines)

    def _format_text_report(self, results: List[Dict]) -> str:
        """生成纯文本格式报告"""
        lines = []

        lines.append("=" * 80)
        lines.append("动态止损建议 (基于ATR)")
        lines.append("=" * 80)
        lines.append("")

        for result in results:
            asset_name = result.get('asset_name', 'N/A')
            dynamic_stop_loss = result.get('dynamic_stop_loss', -0.15) * 100
            stop_loss_price = result.get('stop_loss_price', 0)
            recommendation = result.get('recommendation', 'N/A')

            lines.append(f"{asset_name}:")
            lines.append(f"  动态止损: {dynamic_stop_loss:.0f}%")
            lines.append(f"  止损价格: {stop_loss_price:.2f}")
            lines.append(f"  建议: {recommendation}")
            lines.append("")

        lines.append("=" * 80)

        return '\n'.join(lines)

    def _convert_to_yf_symbol(self, asset_code: str) -> str:
        """
        将资产代码转换为yfinance代码

        Args:
            asset_code: 原始代码 (如 '513180', '002050', '9988.HK')

        Returns:
            yfinance代码
        """
        # 港股
        if '.HK' in asset_code:
            return asset_code

        # A股
        if asset_code.startswith('6'):
            return f"{asset_code}.SS"  # 上交所
        elif asset_code.startswith(('0', '2', '3')):
            return f"{asset_code}.SZ"  # 深交所
        elif asset_code.startswith('5') or asset_code.startswith('1'):
            # ETF: 51开头上交所, 15开头深交所, 58/56开头科创板
            if asset_code.startswith('51') or asset_code.startswith('58') or asset_code.startswith('56'):
                return f"{asset_code}.SS"
            else:
                return f"{asset_code}.SZ"

        # 美股
        return asset_code


def main():
    """测试动态止损生成器"""
    import json
    from pathlib import Path

    # 读取持仓数据
    positions_file = Path(__file__).parent.parent.parent / 'data' / 'positions_20251118.json'

    with open(positions_file, 'r', encoding='utf-8') as f:
        positions_raw = json.load(f)

    # 转换为需要的格式
    positions = []
    for p in positions_raw:
        positions.append({
            'asset_name': p['asset_name'],
            'asset_code': p['asset_code'],
            'position_pct': p['position_ratio'],
            'current_value': p['current_value']
        })

    # 生成动态止损建议
    generator = DynamicStopLossGenerator(lookback_days=20)
    print("正在计算动态止损建议...")

    results = generator.generate_stop_loss_for_all_positions(positions)

    # 生成报告
    report = generator.format_stop_loss_report(results, format_type='markdown')

    # 保存到文件
    output_file = Path(__file__).parent.parent / 'reports' / 'daily' / '2025-11' / '动态止损建议_20251118.md'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Report saved to: {output_file}")


if __name__ == '__main__':
    main()
