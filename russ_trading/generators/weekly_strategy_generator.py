#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周度操作策略生成器 (极简版)
Weekly Strategy Generator (Minimalist Edition)

基于最新的持仓调整建议和市场洞察报告,生成极简版周度操作策略

运行方式:
    python russ_trading/weekly_strategy_generator.py

作者: Claude Code
日期: 2025-11-09
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class WeeklyStrategyGenerator:
    """周度策略生成器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports" / "daily"
        self.docs_dir = self.project_root / "docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def find_latest_reports(self) -> Dict[str, Path]:
        """查找最新的每日报告"""
        latest_position_report = None
        latest_market_report = None

        # 查找2025-11目录
        monthly_dir = self.reports_dir / "2025-11"
        if not monthly_dir.exists():
            raise FileNotFoundError(f"报告目录不存在: {monthly_dir}")

        # 查找持仓调整建议报告
        position_reports = list(monthly_dir.glob("持仓调整建议_*.md"))
        if position_reports:
            latest_position_report = max(position_reports, key=lambda p: p.stem)

        # 查找市场洞察报告
        market_reports = list(monthly_dir.glob("市场洞察报告_*.md"))
        if market_reports:
            latest_market_report = max(market_reports, key=lambda p: p.stem)

        return {
            "position": latest_position_report,
            "market": latest_market_report
        }

    def extract_key_info(self, position_report_path: Path, market_report_path: Path) -> Dict:
        """从报告中提取关键信息"""
        info = {
            "current_position": {},
            "market_status": {},
            "recommendations": []
        }

        # 读取持仓报告
        if position_report_path and position_report_path.exists():
            with open(position_report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # TODO: 解析持仓数据
                info["position_content"] = content[:500]  # 前500字符作为示例

        # 读取市场报告
        if market_report_path and market_report_path.exists():
            with open(market_report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # TODO: 解析市场数据
                info["market_content"] = content[:500]  # 前500字符作为示例

        return info

    def generate_strategy_markdown(self, info: Dict, week_info: Dict) -> str:
        """生成策略markdown文档"""

        today = datetime.now()
        week_start = today + timedelta(days=(7 - today.weekday()))  # 下周一
        week_end = week_start + timedelta(days=6)  # 下周日

        content = f"""# 本周操作策略 ({week_start.strftime('%m.%d')}-{week_end.strftime('%m.%d')})

**生成时间**: {today.strftime('%Y-%m-%d')}
**当前仓位**: {week_info.get('current_position', '78%')} | 现金: {week_info.get('cash', '22%')}
**上周目标完成情况**: {week_info.get('last_week_summary', '待填写')}

---

## 📋 上周执行复盘

### ✅ 完成良好
{week_info.get('completed_items', '- 待手动填写')}

### ⚠️ 待改进
{week_info.get('improvement_items', '- 待手动填写')}

### 💡 关键洞察
{week_info.get('insights', '- 待手动填写')}

---

## 📊 一、市场判断

### 趋势分析

**宏观环境**:
- 待手动填写

**市场情绪**: 震荡分化
- A股: 震荡市
- 港股: 底部区域震荡

**关键节点**:
- 本周重要事件待填写

### 本周核心任务

**🎯 主要目标**:
1. **维持仓位**: 78%左右,不轻易调整
2. **观察为主**: 等待更好的加仓时机
3. **战略优化**: 按方案C+逐步调整持仓结构

---

## 二、本周核心策略 (T0/T1/T2分级)

### 🟢 T0 优先级 (立即执行)

#### 1. 仓位管理 - 维持现状 ✅

**当前配置**: 非常健康,无需调整

| 标的名称 | 当前仓位 | 健康度 | 说明 |
|---------|---------|--------|------|
| 待填写 | 待填写 | ✅ | 待填写 |

**执行策略**:
- **本周**: 维持现状,观察为主
- **不做**: 不追涨,不恐慌
- **关注**: 关键支撑位和恐慌指数

#### 2. 止损纪律 - 严格执行 🛡️

**单笔止损线**: -8% (无条件执行)
**组合止损线**: -6% (周回撤控制)

---

### 🟡 T1 次优先级 (观察择机)

#### 3. 待观察标的

**建仓条件**:
- 技术面触发: 待填写
- 恐慌指数触发: CNVI > 30

---

### 🟢 T2 低优先级 (等待信号)

#### 4. 战略调整

待填写

---

## 三、本周重点观察

### 🔍 核心关注点

**1. 恐慌指数监控** 🎯

当前: CNVI = 15.45 (正常区间)

| 区间 | 状态 | 操作策略 |
|------|------|---------|
| < 15 | 市场平静 | 正常操作 ✅ |
| 15-25 | 正常波动 | 保持观察 |
| 25-30 | 恐慌上升 | 🔥准备加仓 |
| > 30 | 极度恐慌 | 🚀大举加仓良机 |

**2. 关键支撑位监控**

| 标的 | 当前价格 | 关键支撑 | 距离 | 状态 |
|------|---------|---------|------|------|
| 待填写 | 待填写 | 待填写 | 待填写 | 🟡观察 |

---

## 四、预期效果

### 仓位变化预期

**如果按计划执行**:

| 阶段 | 当前 | 本周目标 | 2周目标 | 说明 |
|------|------|---------|---------|------|
| **总仓位** | 78% | 75-78% | 70-75% | 逐步降低 |
| **现金储备** | 22% | 22-25% | 25-30% | 增强灵活性 |

---

## 五、本周特别提醒

### ⚠️ 操作原则

**核心心法**:

1. **"涨上去就是风险,跌下来就是机会"**
   - 不追涨,反弹时减仓
   - 回调时加仓,恐慌时重仓

2. **"仓位保持在6-8层合适"**
   - 当前78%合理,不轻易调整
   - 等待更好时机再加仓

### 🎯 本周操作纪律

**必须做**:
- ✅ 严格执行止损(-8%无条件)
- ✅ 每日监控关键支撑位
- ✅ 保持现金储备22%以上
- ✅ 耐心等待加仓时机

**绝对不做**:
- ❌ 不追涨
- ❌ 不满仓操作
- ❌ 不在支撑位破位时幻想
- ❌ 不听小道消息

---

## 总结: 本周一句话策略

**"守正出奇,以静制动"**

- **守正**: 维持78%仓位,保持22%现金,严守止损纪律
- **出奇**: 等待关键时机果断加仓
- **以静制动**: 不追涨,不恐慌,让市场来找我们

**核心执行**:
1. 本周维持现状,观察为主
2. 耐心等待加仓时机
3. 严格执行止损,保护本金

---

**下周更新**: {(today + timedelta(days=7)).strftime('%Y-%m-%d')} (周末)
**免责声明**: 本报告仅供个人参考,不构成投资建议

**报告生成**: {today.strftime('%Y-%m-%d')}
**系统版本**: Weekly Strategy Generator v1.0
**核心原则**: 仓位管理 + 择时加仓 + 纪律执行
"""
        return content

    def generate(self, user_input: Optional[Dict] = None) -> str:
        """生成周度策略"""
        print("🔍 查找最新报告...")
        reports = self.find_latest_reports()

        if not reports["position"]:
            print("⚠️ 未找到持仓调整建议报告")
        else:
            print(f"✅ 找到持仓报告: {reports['position'].name}")

        if not reports["market"]:
            print("⚠️ 未找到市场洞察报告")
        else:
            print(f"✅ 找到市场报告: {reports['market'].name}")

        print("\n📊 提取关键信息...")
        info = self.extract_key_info(reports["position"], reports["market"])

        # 如果用户提供了额外信息,合并
        week_info = user_input or {}

        print("\n📝 生成策略文档...")
        content = self.generate_strategy_markdown(info, week_info)

        # 保存文件
        today = datetime.now()
        filename = f"本周操作策略_{today.strftime('%Y%m%d')}.md"
        output_path = self.docs_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n✅ 策略文档已生成: {output_path}")
        return str(output_path)


def main():
    """主函数"""
    print("=" * 60)
    print("周度操作策略生成器 (极简版)")
    print("=" * 60)
    print()

    # 提示用户输入上周信息
    print("请提供上周执行情况 (可选,直接回车跳过):")
    print()

    user_input = {}

    # 获取用户输入
    current_position = input("当前仓位% (默认78): ").strip() or "78"
    cash = input("现金% (默认22): ").strip() or "22"

    user_input["current_position"] = f"{current_position}%"
    user_input["cash"] = f"{cash}%"

    # 生成策略
    generator = WeeklyStrategyGenerator()
    output_path = generator.generate(user_input)

    print()
    print("=" * 60)
    print("✅ 生成完成!")
    print()
    print("💡 下一步:")
    print("1. 手动编辑生成的文档,补充具体内容")
    print("2. 参考 reports/daily/ 最新报告")
    print("3. 结合方案C+长期配置方案")
    print("=" * 60)


if __name__ == "__main__":
    main()
