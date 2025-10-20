#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理器模块
提供统一的数据接口和交易日志管理

功能:
1. 统一数据接口(历史价格、指数数据)
2. 交易日志管理(记录、查询、导出)
3. 持仓历史跟踪
4. 数据缓存机制

Author: Russ
Created: 2025-10-20
"""

import json
import csv
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """交易记录"""
    trade_id: str
    date: str
    action: str  # 'BUY' 或 'SELL'
    asset_code: str
    asset_name: str
    price: float
    quantity: int
    amount: float
    commission: float
    note: str = ""

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class Position:
    """持仓记录"""
    date: str
    asset_code: str
    asset_name: str
    quantity: int
    cost_price: float
    current_price: float
    market_value: float
    profit_loss: float
    profit_loss_pct: float
    weight: float  # 仓位权重

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class DailySnapshot:
    """每日资产快照"""
    date: str
    total_capital: float
    cash: float
    market_value: float
    total_return: float
    daily_return: float
    positions: List[Dict]

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


class DataManager:
    """数据管理器"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化数据管理器

        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.trades_file = os.path.join(data_dir, "trades.json")
        self.snapshots_file = os.path.join(data_dir, "snapshots.json")
        self.cache_dir = os.path.join(data_dir, "cache")

        # 确保目录存在
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        # 加载数据
        self.trades: List[Trade] = self._load_trades()
        self.snapshots: List[DailySnapshot] = self._load_snapshots()

    # ========== 交易日志管理 ==========

    def add_trade(
        self,
        date: str,
        action: str,
        asset_code: str,
        asset_name: str,
        price: float,
        quantity: int,
        commission: float = 0,
        note: str = ""
    ) -> Trade:
        """
        添加交易记录

        Args:
            date: 交易日期
            action: 交易动作 ('BUY' 或 'SELL')
            asset_code: 资产代码
            asset_name: 资产名称
            price: 交易价格
            quantity: 交易数量
            commission: 手续费
            note: 备注

        Returns:
            交易记录对象
        """
        trade_id = f"{date}_{action}_{asset_code}_{len(self.trades)+1}"
        amount = price * quantity

        trade = Trade(
            trade_id=trade_id,
            date=date,
            action=action,
            asset_code=asset_code,
            asset_name=asset_name,
            price=price,
            quantity=quantity,
            amount=amount,
            commission=commission,
            note=note
        )

        self.trades.append(trade)
        self._save_trades()

        logger.info(f"添加交易记录: {action} {asset_name} {quantity}股 @ ¥{price:.2f}")

        return trade

    def get_trades(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        asset_code: Optional[str] = None,
        action: Optional[str] = None
    ) -> List[Trade]:
        """
        查询交易记录

        Args:
            start_date: 开始日期
            end_date: 结束日期
            asset_code: 资产代码
            action: 交易动作

        Returns:
            交易记录列表
        """
        filtered_trades = self.trades

        if start_date:
            filtered_trades = [t for t in filtered_trades if t.date >= start_date]

        if end_date:
            filtered_trades = [t for t in filtered_trades if t.date <= end_date]

        if asset_code:
            filtered_trades = [t for t in filtered_trades if t.asset_code == asset_code]

        if action:
            filtered_trades = [t for t in filtered_trades if t.action == action]

        return filtered_trades

    def get_trade_statistics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        获取交易统计

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            交易统计字典
        """
        trades = self.get_trades(start_date, end_date)

        if not trades:
            return {
                'total_trades': 0,
                'buy_count': 0,
                'sell_count': 0,
                'total_buy_amount': 0,
                'total_sell_amount': 0,
                'total_commission': 0
            }

        buy_trades = [t for t in trades if t.action == 'BUY']
        sell_trades = [t for t in trades if t.action == 'SELL']

        return {
            'total_trades': len(trades),
            'buy_count': len(buy_trades),
            'sell_count': len(sell_trades),
            'total_buy_amount': sum(t.amount for t in buy_trades),
            'total_sell_amount': sum(t.amount for t in sell_trades),
            'total_commission': sum(t.commission for t in trades),
            'assets_traded': len(set(t.asset_code for t in trades))
        }

    def export_trades_to_csv(self, filepath: str):
        """
        导出交易记录到CSV

        Args:
            filepath: 导出文件路径
        """
        if not self.trades:
            logger.warning("没有交易记录可导出")
            return

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['trade_id', 'date', 'action', 'asset_code', 'asset_name',
                         'price', 'quantity', 'amount', 'commission', 'note']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for trade in self.trades:
                writer.writerow(trade.to_dict())

        logger.info(f"交易记录已导出到: {filepath}")

    # ========== 持仓快照管理 ==========

    def add_daily_snapshot(
        self,
        date: str,
        total_capital: float,
        cash: float,
        positions: List[Dict],
        previous_capital: Optional[float] = None
    ) -> DailySnapshot:
        """
        添加每日资产快照

        Args:
            date: 日期
            total_capital: 总资金
            cash: 现金
            positions: 持仓列表
            previous_capital: 前一日资金

        Returns:
            快照对象
        """
        market_value = sum(p.get('market_value', 0) for p in positions)

        # 计算收益率
        if previous_capital is None and len(self.snapshots) > 0:
            previous_capital = self.snapshots[-1].total_capital

        if previous_capital and previous_capital > 0:
            daily_return = (total_capital - previous_capital) / previous_capital
        else:
            daily_return = 0

        # 计算总收益率(假设初始资金为第一个快照的资金)
        if len(self.snapshots) > 0:
            initial_capital = self.snapshots[0].total_capital
            total_return = (total_capital - initial_capital) / initial_capital
        else:
            total_return = 0

        snapshot = DailySnapshot(
            date=date,
            total_capital=total_capital,
            cash=cash,
            market_value=market_value,
            total_return=total_return,
            daily_return=daily_return,
            positions=positions
        )

        self.snapshots.append(snapshot)
        self._save_snapshots()

        logger.info(f"添加快照: {date} 总资金¥{total_capital:,.0f} 收益率{total_return*100:.2f}%")

        return snapshot

    def get_snapshots(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[DailySnapshot]:
        """
        获取资产快照

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            快照列表
        """
        filtered = self.snapshots

        if start_date:
            filtered = [s for s in filtered if s.date >= start_date]

        if end_date:
            filtered = [s for s in filtered if s.date <= end_date]

        return filtered

    def get_equity_curve(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[List[str], List[float]]:
        """
        获取权益曲线

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            (日期列表, 资金列表)
        """
        snapshots = self.get_snapshots(start_date, end_date)

        dates = [s.date for s in snapshots]
        capitals = [s.total_capital for s in snapshots]

        return dates, capitals

    def get_returns_series(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[List[str], List[float]]:
        """
        获取收益率序列

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            (日期列表, 收益率列表)
        """
        snapshots = self.get_snapshots(start_date, end_date)

        dates = [s.date for s in snapshots]
        returns = [s.daily_return for s in snapshots]

        return dates, returns

    # ========== 数据持久化 ==========

    def _load_trades(self) -> List[Trade]:
        """加载交易记录"""
        if not os.path.exists(self.trades_file):
            return []

        try:
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Trade(**t) for t in data]
        except Exception as e:
            logger.error(f"加载交易记录失败: {e}")
            return []

    def _save_trades(self):
        """保存交易记录"""
        try:
            with open(self.trades_file, 'w', encoding='utf-8') as f:
                data = [t.to_dict() for t in self.trades]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存交易记录失败: {e}")

    def _load_snapshots(self) -> List[DailySnapshot]:
        """加载快照"""
        if not os.path.exists(self.snapshots_file):
            return []

        try:
            with open(self.snapshots_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [DailySnapshot(**s) for s in data]
        except Exception as e:
            logger.error(f"加载快照失败: {e}")
            return []

    def _save_snapshots(self):
        """保存快照"""
        try:
            with open(self.snapshots_file, 'w', encoding='utf-8') as f:
                data = [s.to_dict() for s in self.snapshots]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存快照失败: {e}")

    # ========== 数据分析 ==========

    def generate_summary_report(self, format_type: str = 'markdown') -> str:
        """
        生成汇总报告

        Args:
            format_type: 输出格式 ('markdown' 或 'text')

        Returns:
            格式化的报告
        """
        if not self.snapshots:
            return "暂无数据"

        # 基础统计
        first_snapshot = self.snapshots[0]
        last_snapshot = self.snapshots[-1]

        initial_capital = first_snapshot.total_capital
        current_capital = last_snapshot.total_capital
        total_return = (current_capital - initial_capital) / initial_capital

        # 交易统计
        trade_stats = self.get_trade_statistics()

        # 格式化输出
        lines = []

        if format_type == 'markdown':
            lines.append("# 📊 数据管理器汇总报告")
            lines.append("")
            lines.append(f"**数据周期**: {first_snapshot.date} 至 {last_snapshot.date}")
            lines.append(f"**总天数**: {len(self.snapshots)} 天")
            lines.append("")

            lines.append("## 资金概况")
            lines.append("")
            lines.append(f"- **初始资金**: ¥{initial_capital:,.0f}")
            lines.append(f"- **当前资金**: ¥{current_capital:,.0f}")
            lines.append(f"- **总收益率**: {total_return*100:.2f}%")
            lines.append(f"- **当前现金**: ¥{last_snapshot.cash:,.0f}")
            lines.append(f"- **当前市值**: ¥{last_snapshot.market_value:,.0f}")
            lines.append("")

            lines.append("## 交易统计")
            lines.append("")
            lines.append(f"- **总交易次数**: {trade_stats['total_trades']}")
            lines.append(f"- **买入次数**: {trade_stats['buy_count']}")
            lines.append(f"- **卖出次数**: {trade_stats['sell_count']}")
            lines.append(f"- **买入总额**: ¥{trade_stats['total_buy_amount']:,.0f}")
            lines.append(f"- **卖出总额**: ¥{trade_stats['total_sell_amount']:,.0f}")
            lines.append(f"- **手续费总额**: ¥{trade_stats['total_commission']:,.2f}")
            lines.append(f"- **交易资产数**: {trade_stats['assets_traded']}")
            lines.append("")

            # 当前持仓
            if last_snapshot.positions:
                lines.append("## 当前持仓")
                lines.append("")
                lines.append("| 资产 | 数量 | 成本价 | 现价 | 市值 | 盈亏 | 仓位 |")
                lines.append("|------|------|--------|------|------|------|------|")

                for pos in last_snapshot.positions:
                    lines.append(
                        f"| {pos.get('asset_name', '')} | "
                        f"{pos.get('quantity', 0)} | "
                        f"¥{pos.get('cost_price', 0):.2f} | "
                        f"¥{pos.get('current_price', 0):.2f} | "
                        f"¥{pos.get('market_value', 0):,.0f} | "
                        f"{pos.get('profit_loss_pct', 0)*100:.2f}% | "
                        f"{pos.get('weight', 0)*100:.1f}% |"
                    )
                lines.append("")

        else:  # text format
            lines.append("=" * 60)
            lines.append("数据管理器汇总报告")
            lines.append("=" * 60)
            lines.append(f"数据周期: {first_snapshot.date} 至 {last_snapshot.date}")
            lines.append(f"总天数: {len(self.snapshots)} 天")
            lines.append("")
            lines.append(f"初始资金: ¥{initial_capital:,.0f}")
            lines.append(f"当前资金: ¥{current_capital:,.0f}")
            lines.append(f"总收益率: {total_return*100:.2f}%")
            lines.append("")
            lines.append(f"总交易次数: {trade_stats['total_trades']}")
            lines.append("=" * 60)

        return "\n".join(lines)


# 示例用法
if __name__ == "__main__":
    # 创建数据管理器
    dm = DataManager(data_dir="data/russ_trading")

    # 添加交易记录
    dm.add_trade(
        date="2025-01-02",
        action="BUY",
        asset_code="512690",
        asset_name="酒ETF",
        price=1.256,
        quantity=10000,
        commission=3.77
    )

    dm.add_trade(
        date="2025-02-15",
        action="SELL",
        asset_code="512690",
        asset_name="酒ETF",
        price=1.35,
        quantity=10000,
        commission=4.05
    )

    # 添加快照
    dm.add_daily_snapshot(
        date="2025-01-02",
        total_capital=500000,
        cash=487440,
        positions=[{
            'asset_code': '512690',
            'asset_name': '酒ETF',
            'quantity': 10000,
            'cost_price': 1.256,
            'current_price': 1.256,
            'market_value': 12560,
            'profit_loss': 0,
            'profit_loss_pct': 0,
            'weight': 0.025
        }]
    )

    dm.add_daily_snapshot(
        date="2025-02-15",
        total_capital=550000,
        cash=550000,
        positions=[]
    )

    # 生成报告
    print(dm.generate_summary_report(format_type='markdown'))

    # 导出交易记录
    dm.export_trades_to_csv("trades_export.csv")
