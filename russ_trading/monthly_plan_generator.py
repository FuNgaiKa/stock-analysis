"""
月度计划生成器

基于以下数据生成月度投资计划:
1. 大盘数据(市场走势、技术面、资金面)
2. 博主观点(雪球、公众号等外部观点)
3. 机构数据(券商研报、基金持仓)
4. 个人策略(仓位管理、收益目标、风险偏好)
"""

from typing import Dict, List, Optional
from datetime import datetime
import calendar
import logging

# 导入机构级核心指标分析器 (Phase 3.3)
try:
    from strategies.position.analyzers.valuation.index_valuation_analyzer import IndexValuationAnalyzer
    from strategies.position.analyzers.market_structure.market_breadth_analyzer import MarketBreadthAnalyzer
    from strategies.position.analyzers.market_specific.margin_trading_analyzer import MarginTradingAnalyzer
    HAS_CORE_ANALYZERS = True
except ImportError:
    HAS_CORE_ANALYZERS = False
    if __name__ != '__main__':
        logging.warning("机构级核心分析器未找到（估值/宽度/融资）")


class MonthlyPlanGenerator:
    """月度计划生成器"""

    def __init__(self, strategy_config: Dict = None):
        """
        初始化月度计划生成器

        Args:
            strategy_config: 策略配置,包含:
                - min_position: 最小仓位
                - max_position: 最大仓位
                - target_annual_return: 目标年化收益率
                - risk_preference: 风险偏好 ('conservative', 'moderate', 'aggressive')
        """
        if strategy_config is None:
            strategy_config = {}

        self.min_position = strategy_config.get('min_position', 0.50)
        self.max_position = strategy_config.get('max_position', 0.90)
        self.target_annual_return = strategy_config.get('target_annual_return', 0.15)
        self.risk_preference = strategy_config.get('risk_preference', 'moderate')

        # 初始化机构级核心分析器 (Phase 3.3)
        if HAS_CORE_ANALYZERS:
            self.valuation_analyzer = IndexValuationAnalyzer(lookback_days=2520)  # 10年估值历史
            self.breadth_analyzer = MarketBreadthAnalyzer(lookback_days=60)  # 60日市场宽度
            self.margin_analyzer = MarginTradingAnalyzer(lookback_days=252)  # 1年融资数据
        else:
            self.valuation_analyzer = None
            self.breadth_analyzer = None
            self.margin_analyzer = None

    def generate_monthly_plan(
        self,
        plan_month: str,
        market_data: Dict,
        blogger_insights: Optional[List[str]] = None,
        institution_data: Optional[Dict] = None,
        current_positions: Optional[List[Dict]] = None
    ) -> Dict:
        """
        生成月度投资计划

        Args:
            plan_month: 计划月份,格式 'YYYY-MM'
            market_data: 大盘数据字典,包含:
                - indices: 各指数数据 {'HS300': {...}, 'CYBZ': {...}}
                - market_sentiment: 市场情绪 ('bullish', 'neutral', 'bearish')
                - trend: 趋势判断 ('uptrend', 'sideways', 'downtrend')
            blogger_insights: 博主观点列表 (可选)
            institution_data: 机构数据字典 (可选)
            current_positions: 当前持仓列表 (可选)

        Returns:
            月度计划字典
        """
        # 解析月份
        year, month = map(int, plan_month.split('-'))
        month_name = calendar.month_name[month]
        _, last_day = calendar.monthrange(year, month)

        plan = {
            'plan_month': plan_month,
            'plan_month_text': f"{year}年{month}月",
            'month_name': month_name,
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'plan_period': {
                'start': f"{year}-{month:02d}-01",
                'end': f"{year}-{month:02d}-{last_day}"
            },
            'market_assessment': {},
            'position_strategy': {},
            'asset_allocation': {},
            'action_items': [],
            'risk_warnings': [],
            'opportunities': [],
            'monthly_targets': {},
            'review_checklist': []
        }

        # 1. 市场评估
        plan['market_assessment'] = self._assess_market(market_data, blogger_insights, institution_data)

        # 2. 仓位策略
        plan['position_strategy'] = self._determine_position_strategy(
            plan['market_assessment'],
            current_positions
        )

        # 3. 资产配置建议
        plan['asset_allocation'] = self._suggest_asset_allocation(
            plan['market_assessment'],
            current_positions
        )

        # 4. 具体行动清单
        plan['action_items'] = self._generate_action_items(
            plan['market_assessment'],
            plan['position_strategy'],
            plan['asset_allocation'],
            current_positions
        )

        # 5. 风险提示
        plan['risk_warnings'] = self._identify_risks(plan['market_assessment'], market_data)

        # 6. 投资机会
        plan['opportunities'] = self._identify_opportunities(plan['market_assessment'], market_data)

        # 7. 月度目标
        plan['monthly_targets'] = self._set_monthly_targets(plan_month, plan['market_assessment'])

        # 8. 复盘检查清单
        plan['review_checklist'] = self._create_review_checklist()

        return plan

    def _assess_market(
        self,
        market_data: Dict,
        blogger_insights: Optional[List[str]],
        institution_data: Optional[Dict]
    ) -> Dict:
        """综合评估市场状况"""
        assessment = {
            'market_sentiment': market_data.get('market_sentiment', 'neutral'),
            'trend': market_data.get('trend', 'sideways'),
            'indices_summary': {},
            'key_insights': [],
            'institution_view': '',
            '综合判断': ''
        }

        # 分析各指数
        indices = market_data.get('indices', {})
        for key, data in indices.items():
            assessment['indices_summary'][key] = {
                'name': data.get('name', key),
                'current': data.get('current', 0),
                'change_pct': data.get('change_pct', '0%'),
                'judgment': data.get('judgment', '中性')
            }

        # 博主观点
        if blogger_insights:
            assessment['key_insights'] = blogger_insights[:5]  # 最多5条

        # 机构观点
        if institution_data:
            assessment['institution_view'] = institution_data.get('summary', '暂无机构观点')

        # 综合判断
        sentiment = assessment['market_sentiment']
        trend = assessment['trend']

        if sentiment == 'bullish' and trend == 'uptrend':
            assessment['综合判断'] = '市场处于上升趋势,情绪乐观,可积极配置'
        elif sentiment == 'bearish' and trend == 'downtrend':
            assessment['综合判断'] = '市场处于下跌趋势,情绪悲观,建议控制仓位'
        elif sentiment == 'neutral' and trend == 'sideways':
            assessment['综合判断'] = '市场震荡整理,情绪中性,可逢低布局'
        else:
            assessment['综合判断'] = '市场处于转换期,建议谨慎观察'

        return assessment

    def _determine_position_strategy(
        self,
        market_assessment: Dict,
        current_positions: Optional[List[Dict]]
    ) -> Dict:
        """确定仓位策略"""
        sentiment = market_assessment['market_sentiment']
        trend = market_assessment['trend']

        # 当前总仓位
        current_total = 0
        if current_positions:
            current_total = sum(p.get('position_ratio', 0) for p in current_positions)

        strategy = {
            'current_position': current_total,
            'current_position_pct': f"{current_total * 100:.1f}%",
            'target_position_range': {},
            'adjustment': '',
            'rationale': ''
        }

        # 根据市场判断确定目标仓位
        if sentiment == 'bullish' and trend == 'uptrend':
            # 牛市上升期: 7-9成
            target_min = 0.70
            target_max = 0.90
            strategy['rationale'] = '牛市上升期,适合较高仓位'
        elif sentiment == 'bearish' and trend == 'downtrend':
            # 熊市下跌期: 3-5成
            target_min = 0.30
            target_max = 0.50
            strategy['rationale'] = '熊市下跌期,控制仓位,保留现金'
        else:
            # 震荡期: 5-7成
            target_min = 0.50
            target_max = 0.70
            strategy['rationale'] = '震荡期,中等仓位,灵活调整'

        strategy['target_position_range'] = {
            'min': target_min,
            'max': target_max,
            'min_pct': f"{target_min * 100:.0f}%",
            'max_pct': f"{target_max * 100:.0f}%"
        }

        # 调整建议
        if current_total < target_min:
            diff = target_min - current_total
            strategy['adjustment'] = f"建议加仓{diff*100:.0f}%至{target_min*100:.0f}%以上"
        elif current_total > target_max:
            diff = current_total - target_max
            strategy['adjustment'] = f"建议减仓{diff*100:.0f}%至{target_max*100:.0f}%以下"
        else:
            strategy['adjustment'] = "当前仓位合理,可维持或微调"

        return strategy

    def _suggest_asset_allocation(
        self,
        market_assessment: Dict,
        current_positions: Optional[List[Dict]]
    ) -> Dict:
        """建议资产配置"""
        allocation = {
            'recommended_assets': [],
            'reduce_assets': [],
            'hold_assets': [],
            'allocation_rationale': []
        }

        # 根据市场情况推荐资产
        sentiment = market_assessment['market_sentiment']

        if sentiment == 'bullish':
            allocation['recommended_assets'] = [
                {'name': '创业板指', 'key': 'CYBZ', 'ratio': '30-40%', 'reason': '成长股牛市受益'},
                {'name': '科创50', 'key': 'KECHUANG50', 'ratio': '20-30%', 'reason': '科技股高弹性'},
                {'name': '纳斯达克', 'key': 'NASDAQ', 'ratio': '10-20%', 'reason': '全球科技龙头'}
            ]
            allocation['allocation_rationale'].append('牛市偏好高弹性成长股')

        elif sentiment == 'bearish':
            allocation['recommended_assets'] = [
                {'name': '沪深300', 'key': 'HS300', 'ratio': '20-30%', 'reason': '大盘蓝筹相对抗跌'},
                {'name': '白酒ETF', 'key': 'CN_LIQUOR', 'ratio': '10-15%', 'reason': '消费防御'},
                {'name': '黄金', 'key': 'GOLD', 'ratio': '5-10%', 'reason': '避险资产'}
            ]
            allocation['reduce_assets'] = [
                {'name': '证券ETF', 'key': 'CN_SECURITIES', 'reason': '熊市券商承压'},
                {'name': '周期股', 'key': 'CYCLE', 'reason': '经济下行周期股承压'}
            ]
            allocation['allocation_rationale'].append('熊市偏好防御性资产')

        else:  # neutral
            allocation['recommended_assets'] = [
                {'name': '创业板指', 'key': 'CYBZ', 'ratio': '25-35%', 'reason': '逢低布局成长'},
                {'name': '沪深300', 'key': 'HS300', 'ratio': '15-25%', 'reason': '底仓配置'},
                {'name': '恒生科技', 'key': 'HKTECH', 'ratio': '15-25%', 'reason': '港股估值低'}
            ]
            allocation['allocation_rationale'].append('震荡期平衡配置,逢低布局')

        return allocation

    def _generate_action_items(
        self,
        market_assessment: Dict,
        position_strategy: Dict,
        asset_allocation: Dict,
        current_positions: Optional[List[Dict]]
    ) -> List[Dict]:
        """生成具体行动清单"""
        actions = []

        # 1. 仓位调整行动
        adjustment = position_strategy.get('adjustment', '')
        if '加仓' in adjustment:
            actions.append({
                'priority': 'high',
                'category': '仓位调整',
                'action': adjustment,
                'deadline': '本月前两周'
            })
        elif '减仓' in adjustment:
            actions.append({
                'priority': 'high',
                'category': '仓位调整',
                'action': adjustment,
                'deadline': '本月第一周'
            })

        # 2. 资产配置行动
        for asset in asset_allocation.get('recommended_assets', []):
            actions.append({
                'priority': 'medium',
                'category': '资产配置',
                'action': f"配置{asset['name']},建议仓位{asset['ratio']}",
                'rationale': asset['reason'],
                'deadline': '本月分批建仓'
            })

        # 3. 减仓行动
        for asset in asset_allocation.get('reduce_assets', []):
            actions.append({
                'priority': 'high',
                'category': '风险控制',
                'action': f"减仓{asset['name']}",
                'rationale': asset['reason'],
                'deadline': '本月第一周'
            })

        # 4. 定期复盘
        actions.append({
            'priority': 'medium',
            'category': '复盘',
            'action': '每周复盘持仓,检查止盈止损',
            'deadline': '每周日'
        })

        # 5. 月度总结
        actions.append({
            'priority': 'low',
            'category': '总结',
            'action': '月末总结收益,评估策略执行情况',
            'deadline': '月末最后一天'
        })

        return actions

    def _identify_risks(self, market_assessment: Dict, market_data: Dict) -> List[str]:
        """识别风险点"""
        risks = []

        sentiment = market_assessment['market_sentiment']
        trend = market_assessment['trend']

        if sentiment == 'bearish':
            risks.append("🚨 市场处于下跌趋势,整体风险较高")
            risks.append("⚠️ 建议降低仓位,保留充足现金应对进一步下跌")

        if trend == 'downtrend':
            risks.append("📉 技术面处于下行通道,短期反弹后可能继续下跌")

        # 检查恐慌指数
        fear_greed = market_data.get('fear_greed_index', 50)
        if fear_greed < 30:
            risks.append(f"😱 恐慌指数{fear_greed}处于极度恐慌区域,市场情绪脆弱")
        elif fear_greed > 70:
            risks.append(f"🔥 恐慌指数{fear_greed}处于贪婪区域,警惕回调风险")

        # 杠杆风险
        risks.append("⚠️ 严禁使用杠杆,保持至少10%现金应对黑天鹅")

        return risks

    def _identify_opportunities(self, market_assessment: Dict, market_data: Dict) -> List[str]:
        """识别投资机会"""
        opportunities = []

        sentiment = market_assessment['market_sentiment']
        trend = market_assessment['trend']

        if sentiment == 'bullish' and trend == 'uptrend':
            opportunities.append("🚀 市场上升趋势明确,可积极把握成长股机会")
            opportunities.append("💡 创业板、科创板具备翻倍潜力")

        if sentiment == 'bearish':
            opportunities.append("💎 市场恐慌是黄金买点,关注优质资产的底部机会")
            opportunities.append("📊 逢低分批布局沪深300、创业板等核心资产")

        # 检查具体指数机会
        indices = market_data.get('indices', {})
        for key, data in indices.items():
            judgment = data.get('judgment', '')
            if '加仓' in judgment or '买入' in judgment:
                opportunities.append(f"✅ {data.get('name', key)}: {judgment}")

        return opportunities

    def _set_monthly_targets(self, plan_month: str, market_assessment: Dict) -> Dict:
        """设置月度目标"""
        # 月度收益目标 = 年化目标 / 12
        monthly_return_target = self.target_annual_return / 12

        targets = {
            'return_target': monthly_return_target,
            'return_target_pct': f"{monthly_return_target * 100:.2f}%",
            'action_targets': [],
            'discipline_targets': []
        }

        # 操作目标
        targets['action_targets'] = [
            "完成仓位调整至目标区间",
            "完成资产配置优化",
            "执行至少1次止盈或止损操作"
        ]

        # 纪律目标
        targets['discipline_targets'] = [
            "不情绪化操作,严格按计划执行",
            "每周复盘一次",
            "不追涨杀跌",
            "控制单一标的仓位≤20%"
        ]

        return targets

    def _create_review_checklist(self) -> List[str]:
        """创建复盘检查清单"""
        checklist = [
            "✅ 月度收益率是否达标?",
            "✅ 是否跑赢沪深300?",
            "✅ 仓位是否在目标区间?",
            "✅ 是否有单一标的超过20%?",
            "✅ 是否保留了至少10%现金?",
            "✅ 本月操作是否符合预定计划?",
            "✅ 是否出现情绪化操作?",
            "✅ 止盈止损是否及时?",
            "✅ 有哪些经验教训?",
            "✅ 下月需要优化哪些方面?"
        ]
        return checklist

    def format_monthly_plan(self, plan: Dict, format_type: str = 'markdown') -> str:
        """
        格式化月度计划

        Args:
            plan: generate_monthly_plan()返回的计划
            format_type: 格式类型 ('markdown', 'markdown_new' 或 'text')

        Returns:
            格式化后的计划文本
        """
        if format_type == 'markdown_new':
            return self._format_markdown_plan_new(plan)
        elif format_type == 'markdown':
            return self._format_markdown_plan(plan)
        else:
            return self._format_text_plan(plan)

    def _format_markdown_plan(self, plan: Dict) -> str:
        """生成Markdown格式的月度计划 - 采用新的简洁风格"""
        lines = []

        # 标题 - 采用新格式
        lines.append(f"# 📅 投资计划 - {plan['plan_month']}")
        lines.append("")
        lines.append(f"**生成时间**: {plan['generation_date']} 当前仓位: {plan['position_strategy']['current_position_pct']} | 目标仓位: {plan['position_strategy']['target_position_range']['min_pct']}-{plan['position_strategy']['target_position_range']['max_pct']}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. 市场判断 - 简化版
        assessment = plan['market_assessment']
        lines.append("## 一、市场判断")
        lines.append("")
        lines.append("### 趋势分析")
        lines.append(f"- **宏观环境**: {assessment['market_sentiment']}市场，{assessment['trend']}")
        lines.append(f"- **综合判断**: {assessment['综合判断']}")
        lines.append(f"- **关键节点**: 本月关注政策面、资金面变化")
        lines.append("")

        # 本月核心任务
        position = plan['position_strategy']
        current_pos = position['current_position']
        target_min = position['target_position_range']['min']
        target_max = position['target_position_range']['max']

        lines.append("### 本月核心任务")
        if current_pos > target_max:
            need_reduce = current_pos - target_max
            lines.append(f"1. **降低仓位**: {position['current_position_pct']} → {position['target_position_range']['max_pct']} (减仓{need_reduce*100:.0f}%)")
            lines.append(f"2. **增加现金**: 补充至安全线以上")
            lines.append("3. **优化结构**: 降低超仓品种风险")
            lines.append("4. **严控纪律**: 严格执行止损")
        elif current_pos < target_min:
            need_add = target_min - current_pos
            lines.append(f"1. **提升仓位**: {position['current_position_pct']} → {position['target_position_range']['min_pct']} (加仓{need_add*100:.0f}%)")
            lines.append("2. **把握机会**: 市场机会逢低布局")
            lines.append("3. **分批建仓**: 避免一次性重仓")
            lines.append("4. **做好风控**: 设置合理止损")
        else:
            lines.append("1. **维持仓位**: 当前仓位在合理区间")
            lines.append("2. **优化结构**: 微调持仓配置")
            lines.append("3. **保持纪律**: 严格执行操作计划")
            lines.append("4. **定期复盘**: 每周检查持仓表现")
        lines.append("")

        # 核心指数情况 - 简化版
        if assessment['indices_summary']:
            lines.append("### 核心指数表现")
            for key, data in list(assessment['indices_summary'].items())[:3]:  # 只显示前3个
                lines.append(f"- **{data['name']}**: {data['current']:.0f} ({data['change_pct']}) - {data['judgment']}")
            lines.append("")

        # 机构级核心指标参考 (Phase 3.3)
        if HAS_CORE_ANALYZERS and self.valuation_analyzer:
            lines.append("### 🏛️ 机构级核心指标参考")
            lines.append("")
            lines.append("**说明**: 基于沪深300，这三个指标帮助判断市场位置")
            lines.append("")

            try:
                # 1. 估值分析
                val_data = self.valuation_analyzer.calculate_valuation_percentile(
                    index_code='000300',  # 沪深300
                    periods=[2520]  # 10年
                )
                if val_data and 'error' not in val_data and val_data.get('percentiles'):
                    pct_data = val_data['percentiles'].get('2520', {})
                    if pct_data:
                        pe_pct = pct_data.get('pe_percentile', 0) * 100
                        pb_pct = pct_data.get('pb_percentile', 0) * 100
                        level = pct_data.get('level', '未知')
                        level_emoji = {'极低估': '🟢🟢', '低估': '🟢', '合理': '🟡', '高估': '🔴', '极高估': '🔴🔴'}.get(level, '⚪')
                        lines.append(f"- **估值水平(10年)**: {level_emoji} {level} (PE分位{pe_pct:.1f}%, PB分位{pb_pct:.1f}%)")

                # 2. 市场宽度
                breadth_data = self.breadth_analyzer.analyze_market_breadth(periods=[60])
                if breadth_data and 'error' not in breadth_data and breadth_data.get('periods'):
                    period_data = breadth_data['periods'].get('60', {})
                    if period_data:
                        score = period_data.get('breadth_score', 50)
                        strength = period_data.get('market_strength', '中性')
                        strength_emoji = {'强势': '🟢', '健康': '🟢', '中性': '🟡', '弱势': '🔴', '极弱': '🔴🔴'}.get(strength, '⚪')
                        lines.append(f"- **市场宽度(60日)**: {strength_emoji} {strength} (得分{score:.0f}/100)")

                # 3. 融资融券
                margin_data = self.margin_analyzer.analyze_margin_trading()
                if margin_data and 'error' not in margin_data and margin_data.get('current'):
                    sentiment_score = margin_data.get('sentiment_score', 50)
                    sentiment_level = margin_data.get('sentiment_level', '中性')
                    sentiment_emoji = '⚠️' if sentiment_score >= 80 or sentiment_score <= 20 else '🟡'
                    lines.append(f"- **市场情绪**: {sentiment_emoji} {sentiment_level} (融资情绪{sentiment_score:.0f}/100)")

                lines.append("")

            except Exception as e:
                lines.append(f"⚠️ 机构级核心指标获取失败: {str(e)}")
                lines.append("")

        lines.append("## 二、本月核心策略（T0/T1/T2分级）")
        lines.append("")

        # 按优先级分组行动项
        high_priority = [a for a in plan['action_items'] if a.get('priority') == 'high']
        medium_priority = [a for a in plan['action_items'] if a.get('priority') == 'medium']
        low_priority = [a for a in plan['action_items'] if a.get('priority') == 'low']

        if high_priority:
            lines.append("### 🔴 T0 优先级（立即执行）")
            lines.append("")
            for i, action in enumerate(high_priority, 1):
                lines.append(f"**{i}. {action['action']}**")
                if 'rationale' in action:
                    lines.append(f"- **理由**: {action['rationale']}")
                lines.append(f"- **截止时间**: {action['deadline']}")
            lines.append("")

        if medium_priority:
            lines.append("### 🟡 T1 次优先级（观察择机）")
            lines.append("")
            for i, action in enumerate(medium_priority, 1):
                lines.append(f"**{i}. {action['action']}**")
                if 'rationale' in action:
                    lines.append(f"- **条件**: {action['rationale']}")
                lines.append(f"- **时机**: {action['deadline']}")
            lines.append("")

        if low_priority:
            lines.append("### 🟢 T2 低优先级（等待信号）")
            lines.append("")
            for i, action in enumerate(low_priority, 1):
                lines.append(f"**{i}. {action['action']}**")
                lines.append(f"- **时间**: {action['deadline']}")
            lines.append("")

        # 3. 资产配置
        allocation = plan['asset_allocation']
        lines.append("## 💼 资产配置建议")
        lines.append("")

        if allocation['recommended_assets']:
            lines.append("### ✅ 推荐配置")
            lines.append("")
            for asset in allocation['recommended_assets']:
                lines.append(f"- **{asset['name']}** ({asset['key']})")
                lines.append(f"  - 建议仓位: {asset['ratio']}")
                lines.append(f"  - 理由: {asset['reason']}")
            lines.append("")

        if allocation['reduce_assets']:
            lines.append("### ⚠️ 建议减仓")
            lines.append("")
            for asset in allocation['reduce_assets']:
                lines.append(f"- **{asset['name']}**: {asset['reason']}")
            lines.append("")

        # 4. 行动清单
        lines.append("## ✅ 本月行动清单")
        lines.append("")

        # 按优先级分组
        high_priority = [a for a in plan['action_items'] if a.get('priority') == 'high']
        medium_priority = [a for a in plan['action_items'] if a.get('priority') == 'medium']
        low_priority = [a for a in plan['action_items'] if a.get('priority') == 'low']

        if high_priority:
            lines.append("### 🔥 高优先级")
            lines.append("")
            for action in high_priority:
                lines.append(f"- [ ] **{action['action']}**")
                if 'rationale' in action:
                    lines.append(f"  - 理由: {action['rationale']}")
                lines.append(f"  - 截止: {action['deadline']}")
            lines.append("")

        if medium_priority:
            lines.append("### ⚖️ 中优先级")
            lines.append("")
            for action in medium_priority:
                lines.append(f"- [ ] {action['action']}")
                if 'rationale' in action:
                    lines.append(f"  - 理由: {action['rationale']}")
                lines.append(f"  - 截止: {action['deadline']}")
            lines.append("")

        if low_priority:
            lines.append("### 📝 低优先级")
            lines.append("")
            for action in low_priority:
                lines.append(f"- [ ] {action['action']}")
                lines.append(f"  - 截止: {action['deadline']}")
            lines.append("")

        # 5. 风险提示
        if plan['risk_warnings']:
            lines.append("## ⚠️ 风险提示")
            lines.append("")
            for risk in plan['risk_warnings']:
                lines.append(f"- {risk}")
            lines.append("")

        # 6. 投资机会
        if plan['opportunities']:
            lines.append("## 💡 投资机会")
            lines.append("")
            for opp in plan['opportunities']:
                lines.append(f"- {opp}")
            lines.append("")

        # 7. 月度目标
        targets = plan['monthly_targets']
        lines.append("## 🎯 月度目标")
        lines.append("")
        lines.append(f"**收益目标**: {targets['return_target_pct']}")
        lines.append("")

        lines.append("### 操作目标")
        lines.append("")
        for target in targets['action_targets']:
            lines.append(f"- [ ] {target}")
        lines.append("")

        lines.append("### 纪律目标")
        lines.append("")
        for target in targets['discipline_targets']:
            lines.append(f"- [ ] {target}")
        lines.append("")

        # 8. 月末复盘清单
        lines.append("## 📋 月末复盘清单")
        lines.append("")
        for item in plan['review_checklist']:
            lines.append(f"- [ ] {item}")
        lines.append("")

        # 免责声明
        lines.append("---")
        lines.append("")
        lines.append("**免责声明**: 本计划基于历史数据和技术分析,仅供参考,不构成投资建议。投资有风险,入市需谨慎。")
        lines.append("")

        return "\n".join(lines)

    def _format_markdown_plan_new(self, plan: Dict) -> str:
        """生成新的简洁格式月度计划"""
        lines = []

        # 标题 - 采用新格式
        lines.append(f"# 📅 投资计划 - {plan['plan_month']}")
        lines.append("")
        lines.append(f"**生成时间**: {plan['generation_date']} 当前仓位: {plan['position_strategy']['current_position_pct']} | 目标仓位: {plan['position_strategy']['target_position_range']['min_pct']}-{plan['position_strategy']['target_position_range']['max_pct']}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. 市场判断
        assessment = plan['market_assessment']
        lines.append("## 一、市场判断")
        lines.append("")
        lines.append("### 趋势分析")
        lines.append(f"- **宏观环境**: {assessment['market_sentiment']}市场，{assessment['trend']}")
        lines.append(f"- **综合判断**: {assessment['综合判断']}")
        lines.append(f"- **关键节点**: 本月关注政策面、资金面变化")
        lines.append("")

        # 核心指数情况
        if assessment['indices_summary']:
            lines.append("### 核心指数表现")
            for key, data in list(assessment['indices_summary'].items())[:3]:
                lines.append(f"- **{data['name']}**: {data['current']:.0f} ({data['change_pct']}) - {data['judgment']}")
            lines.append("")

        # 2. 本月核心策略
        lines.append("## 二、本月核心策略（T0/T1/T2分级）")
        lines.append("")

        # 按优先级分��行动项
        high_priority = [a for a in plan['action_items'] if a.get('priority') == 'high']
        medium_priority = [a for a in plan['action_items'] if a.get('priority') == 'medium']
        low_priority = [a for a in plan['action_items'] if a.get('priority') == 'low']

        if high_priority:
            lines.append("### 🔴 T0 优先级（立即执行）")
            lines.append("")
            for i, action in enumerate(high_priority, 1):
                lines.append(f"**{i}. {action['action']}**")
                if 'rationale' in action:
                    lines.append(f"- **理由**: {action['rationale']}")
                lines.append(f"- **截止时间**: {action['deadline']}")
            lines.append("")

        if medium_priority:
            lines.append("### 🟡 T1 次优先级（观察择机）")
            lines.append("")
            for i, action in enumerate(medium_priority, 1):
                lines.append(f"**{i}. {action['action']}**")
                if 'rationale' in action:
                    lines.append(f"- **条件**: {action['rationale']}")
                lines.append(f"- **时机**: {action['deadline']}")
            lines.append("")

        if low_priority:
            lines.append("### 🟢 T2 低优先级（等待信号）")
            lines.append("")
            for i, action in enumerate(low_priority, 1):
                lines.append(f"**{i}. {action['action']}**")
                lines.append(f"- **时间**: {action['deadline']}")
            lines.append("")

        # 3. 本月重点观察
        lines.append("## 三、本月重点观察")
        lines.append("")
        lines.append("### 🔍 核心关注点")
        lines.append("- **仓位管理**: 确保仓位在目标区间内")
        lines.append("- **市场机会**: 关注政策催化和板块轮动")
        lines.append("- **风险控制**: 严格执行止损纪律")
        lines.append("- **现金储备**: 保持充足流动性")
        lines.append("")

        # 风险���机会
        if plan['risk_warnings'] or plan['opportunities']:
            lines.append("### 📊 风险与机会")
            if plan['opportunities']:
                for opp in plan['opportunities'][:2]:
                    lines.append(f"- **机会**: {opp}")
            if plan['risk_warnings']:
                for risk in plan['risk_warnings'][:2]:
                    lines.append(f"- **风险**: {risk}")
            lines.append("")

        # 4. 预期效果
        position = plan['position_strategy']
        lines.append("## 四、预期效果")
        lines.append("")
        lines.append("### 仓位变化")
        lines.append(f"```\n当前仓位: {position['current_position_pct']} → 目标: {position['target_position_range']['min_pct']}-{position['target_position_range']['max_pct']}\n```")
        lines.append("")
        lines.append("### 风险改善")
        lines.append("✅ **仓位优化**: 仓位控制在合理区间")
        lines.append("✅ **纪律执行**: 严格止损，控制风险")
        lines.append("✅ **灵活性**: 充足现金应对变化")
        lines.append("")

        # 5. 投资心法
        lines.append("## 五、本月投资心法")
        lines.append("")
        lines.append("**核心原则**:")
        lines.append("- 弱水三千，我只取一瓢 - 专注确定性机会")
        lines.append("- 现金是看涨期权 - 下跌时反而兴奋")
        lines.append("- 保本第一 - 严格控制回撤")
        lines.append("- 纪律为王 - 计划制定就要严格执行")
        lines.append("")

        # 免责声明
        lines.append("---")
        lines.append("")
        lines.append("**免责声明**: 本计划仅供个人��考，不构成投资建议")
        lines.append("")

        return "\n".join(lines)

    def _format_text_plan(self, plan: Dict) -> str:
        """生成纯文本格式的月度计划"""
        lines = []

        lines.append("=" * 60)
        lines.append(f"{plan['plan_month_text']}投资计划")
        lines.append("=" * 60)
        lines.append(f"生成时间: {plan['generation_date']}")
        lines.append("")

        lines.append("市场评估:")
        lines.append(f"  {plan['market_assessment']['综合判断']}")
        lines.append("")

        lines.append("仓位策略:")
        lines.append(f"  {plan['position_strategy']['adjustment']}")
        lines.append("")

        lines.append("本月行动:")
        for action in plan['action_items'][:5]:  # 只显示前5项
            lines.append(f"  - {action['action']}")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


# 示例用法
if __name__ == "__main__":
    # 创建计划生成器
    generator = MonthlyPlanGenerator({
        'min_position': 0.50,
        'max_position': 0.90,
        'target_annual_return': 0.15,
        'risk_preference': 'moderate'
    })

    # 准备市场数据
    market_data = {
        'market_sentiment': 'bullish',
        'trend': 'uptrend',
        'fear_greed_index': 65,
        'indices': {
            'HS300': {'name': '沪深300', 'current': 4538, 'change_pct': '+0.53%', 'judgment': '企稳'},
            'CYBZ': {'name': '创业板指', 'current': 2993, 'change_pct': '+1.98%', 'judgment': '底部反弹,可加仓'},
            'KECHUANG50': {'name': '科创50', 'current': 1368, 'change_pct': '+0.35%', 'judgment': '震荡'}
        }
    }

    # 博主观点
    blogger_insights = [
        "创业板2935点确认历史底部,未来有翻倍潜力",
        "证券板块建议减仓,历史胜率较低",
        "纳斯达克继续强势,可适当配置",
        "煤炭板块RSI超买,建议止盈"
    ]

    # 当前持仓
    current_positions = [
        {'asset_name': '证券ETF', 'asset_key': 'CN_SECURITIES', 'position_ratio': 0.40},
        {'asset_name': '恒生科技', 'asset_key': 'HKTECH', 'position_ratio': 0.30},
        {'asset_name': '煤炭ETF', 'asset_key': 'CN_COAL', 'position_ratio': 0.15},
        {'asset_name': '白酒ETF', 'asset_key': 'CN_LIQUOR', 'position_ratio': 0.08}
    ]

    # 生成月度计划
    plan = generator.generate_monthly_plan(
        plan_month='2025-11',
        market_data=market_data,
        blogger_insights=blogger_insights,
        current_positions=current_positions
    )

    # 打印报告
    report = generator.format_monthly_plan(plan, format_type='markdown')
    print(report)
