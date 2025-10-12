#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据分析器
Financial Data Analyzer

基本面分析,包括:
- ROE (净资产收益率)
- 营收增长率
- 净利润增长率
- 毛利率
- 资产负债率
- PE/PB估值

作者: Claude Code
日期: 2025-10-12
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """
    财务数据分析器

    功能:
    1. 获取公司财务指标
    2. 计算成长性指标
    3. 计算盈利能力指标
    4. 估值分析
    5. 综合评分
    """

    def __init__(self):
        """初始化"""
        logger.info("财务数据分析器初始化完成")

    def get_financial_indicators(self, symbol: str, report_date: str = '20240930') -> Dict:
        """
        获取个股财务指标

        Args:
            symbol: 股票代码 (如 '000001' 或 '600519')
            report_date: 报告日期,默认最新季度

        Returns:
            财务指标字典
        """
        try:
            logger.info(f"获取{symbol}财务指标...")

            # 使用stock_yjbb_em获取业绩报表(包含ROE/毛利率等)
            df = ak.stock_yjbb_em(date=report_date)

            if df is None or df.empty:
                logger.warning(f"业绩报表数据为空")
                return {}

            # 筛选目标股票
            stock_data = df[df['股票代码'] == symbol]

            if stock_data.empty:
                logger.warning(f"{symbol}财务数据为空")
                return {}

            latest = stock_data.iloc[0]

            indicators = {
                'date': report_date,
                'stock_name': latest.get('股票简称', ''),
                'eps': float(latest.get('每股收益', 0)),
                'roe': float(latest.get('净资产收益率', 0)),
                'eps_nav': float(latest.get('每股净资产', 0)),
                'gross_margin': float(latest.get('销售毛利率', 0)),
                'eps_cf': float(latest.get('每股经营现金流量', 0)),
                'revenue': float(latest.get('营业总收入-营业总收入', 0)),
                'revenue_growth': float(latest.get('营业总收入-同比增长', 0)),
                'revenue_qoq': float(latest.get('营业总收入-季度环比增长', 0)),
                'profit': float(latest.get('净利润-净利润', 0)),
                'profit_growth': float(latest.get('净利润-同比增长', 0)),
                'profit_qoq': float(latest.get('净利润-季度环比增长', 0)),
                'industry': latest.get('所处行业', ''),
            }

            logger.info(f"{symbol}财务指标获取成功")
            return indicators

        except Exception as e:
            logger.error(f"获取{symbol}财务指标失败: {str(e)}")
            return {}

    def calculate_growth_rate(self, symbol: str, indicators: Dict = None) -> Dict:
        """
        从业绩报表中提取增长率数据

        Args:
            symbol: 股票代码
            indicators: 如果已有财务指标数据,直接使用

        Returns:
            {
                'revenue_growth': 营收同比增长率(%),
                'profit_growth': 净利润同比增长率(%),
                'revenue_qoq': 营收环比增长率(%),
                'profit_qoq': 净利润环比增长率(%)
            }
        """
        try:
            logger.info(f"提取{symbol}增长率...")

            # 如果已提供指标数据,直接提取
            if indicators and 'revenue_growth' in indicators:
                growth = {
                    'revenue_growth': indicators.get('revenue_growth', 0),
                    'profit_growth': indicators.get('profit_growth', 0),
                    'revenue_qoq': indicators.get('revenue_qoq', 0),
                    'profit_qoq': indicators.get('profit_qoq', 0),
                }
                logger.info(f"{symbol}增长率提取完成")
                return growth

            # 否则重新获取数据
            indicators = self.get_financial_indicators(symbol)
            if not indicators:
                return {}

            growth = {
                'revenue_growth': indicators.get('revenue_growth', 0),
                'profit_growth': indicators.get('profit_growth', 0),
                'revenue_qoq': indicators.get('revenue_qoq', 0),
                'profit_qoq': indicators.get('profit_qoq', 0),
            }

            logger.info(f"{symbol}增长率提取完成")
            return growth

        except Exception as e:
            logger.error(f"提取{symbol}增长率失败: {str(e)}")
            return {}

    def get_valuation_metrics(self, symbol: str) -> Dict:
        """
        获取估值指标

        Args:
            symbol: 股票代码

        Returns:
            {
                'pe': 市盈率,
                'pb': 市净率,
                'market_cap': 总市值(亿),
                'price': 最新价
            }
        """
        try:
            logger.info(f"获取{symbol}估值指标...")

            # 使用stock_individual_info_em获取个股信息
            df = ak.stock_individual_info_em(symbol=symbol)

            if df is None or df.empty:
                return {}

            # 转换为字典
            info_dict = dict(zip(df['item'], df['value']))

            valuation = {
                'price': float(info_dict.get('最新', 0)),
                'market_cap': float(info_dict.get('总市值', 0)),
                'circulating_market_cap': float(info_dict.get('流通市值', 0)),
                'total_shares': float(info_dict.get('总股本', 0)),
                'circulating_shares': float(info_dict.get('流通股', 0)),
            }

            # 计算PE和PB (需要结合财务数据)
            # 这里仅返回基础估值数据
            logger.info(f"{symbol}估值指标获取成功")
            return valuation

        except Exception as e:
            logger.error(f"获取{symbol}估值指标失败: {str(e)}")
            return {}

    def analyze_profitability(self, indicators: Dict) -> Dict:
        """
        分析盈利能力

        Args:
            indicators: 财务指标字典

        Returns:
            盈利能力分析结果
        """
        if not indicators:
            return {'level': '未知', 'score': 0}

        roe = indicators.get('roe', 0)
        net_margin = indicators.get('net_margin', 0)
        gross_margin = indicators.get('gross_margin', 0)

        score = 0
        reasons = []

        # ROE评分
        if roe >= 20:
            score += 40
            reasons.append(f'ROE {roe:.1f}%,盈利能力优秀')
        elif roe >= 15:
            score += 30
            reasons.append(f'ROE {roe:.1f}%,盈利能力良好')
        elif roe >= 10:
            score += 20
            reasons.append(f'ROE {roe:.1f}%,盈利能力一般')
        else:
            score += 10
            reasons.append(f'ROE {roe:.1f}%,盈利能力较弱')

        # 净利率评分
        if net_margin >= 20:
            score += 30
            reasons.append(f'净利率{net_margin:.1f}%,利润率高')
        elif net_margin >= 10:
            score += 20
            reasons.append(f'净利率{net_margin:.1f}%,利润率正常')
        else:
            score += 10
            reasons.append(f'净利率{net_margin:.1f}%,利润率偏低')

        # 毛利率评分
        if gross_margin >= 40:
            score += 30
            reasons.append(f'毛利率{gross_margin:.1f}%,竞争力强')
        elif gross_margin >= 20:
            score += 20
            reasons.append(f'毛利率{gross_margin:.1f}%,竞争力一般')
        else:
            score += 10
            reasons.append(f'毛利率{gross_margin:.1f}%,竞争力弱')

        # 评级
        if score >= 80:
            level = '优秀'
        elif score >= 60:
            level = '良好'
        elif score >= 40:
            level = '一般'
        else:
            level = '较弱'

        return {
            'level': level,
            'score': score,
            'reasons': reasons
        }

    def analyze_growth(self, growth: Dict) -> Dict:
        """
        分析成长性

        Args:
            growth: 增长率字典

        Returns:
            成长性分析结果
        """
        if not growth:
            return {'level': '未知', 'score': 0}

        revenue_growth = growth.get('revenue_growth', 0)
        profit_growth = growth.get('profit_growth', 0)

        score = 0
        reasons = []

        # 营收增长评分
        if revenue_growth >= 30:
            score += 40
            reasons.append(f'营收增长{revenue_growth:.1f}%,高速增长')
        elif revenue_growth >= 15:
            score += 30
            reasons.append(f'营收增长{revenue_growth:.1f}%,稳定增长')
        elif revenue_growth >= 0:
            score += 20
            reasons.append(f'营收增长{revenue_growth:.1f}%,增长放缓')
        else:
            score += 10
            reasons.append(f'营收下滑{abs(revenue_growth):.1f}%,业绩下降')

        # 净利润增长评分
        if profit_growth >= 30:
            score += 40
            reasons.append(f'利润增长{profit_growth:.1f}%,盈利大增')
        elif profit_growth >= 15:
            score += 30
            reasons.append(f'利润增长{profit_growth:.1f}%,盈利提升')
        elif profit_growth >= 0:
            score += 20
            reasons.append(f'利润增长{profit_growth:.1f}%,盈利增速放缓')
        else:
            score += 10
            reasons.append(f'利润下滑{abs(profit_growth):.1f}%,盈利恶化')

        # 成长性与盈利性匹配度
        if revenue_growth > 0 and profit_growth > revenue_growth:
            score += 20
            reasons.append('利润增速超营收,盈利能力提升')

        # 评级
        if score >= 80:
            level = '高成长'
        elif score >= 60:
            level = '稳健成长'
        elif score >= 40:
            level = '低成长'
        else:
            level = '负增长'

        return {
            'level': level,
            'score': score,
            'reasons': reasons
        }

    def analyze_valuation(self, valuation: Dict, indicators: Dict) -> Dict:
        """
        分析估值水平

        Args:
            valuation: 估值指标
            indicators: 财务指标

        Returns:
            估值分析结果
        """
        if not valuation or not indicators:
            return {'level': '未知', 'score': 0, 'reasons': []}

        # 计算PE和PB
        market_cap = valuation.get('market_cap', 0)
        price = valuation.get('price', 0)
        eps = indicators.get('eps', 0)
        eps_nav = indicators.get('eps_nav', 0)
        roe = indicators.get('roe', 0)
        profit = indicators.get('profit', 0)

        # PE = 市值 / 净利润 或 价格 / 每股收益
        pe = (price / eps) if eps > 0 else 0
        # PB = 价格 / 每股净资产
        pb = (price / eps_nav) if eps_nav > 0 else 0

        score = 50  # 基础分
        reasons = []

        # PE估值
        if 0 < pe < 15:
            score += 20
            reasons.append(f'PE {pe:.1f},估值偏低')
        elif 15 <= pe < 30:
            score += 10
            reasons.append(f'PE {pe:.1f},估值合理')
        elif 30 <= pe < 50:
            score -= 5
            reasons.append(f'PE {pe:.1f},估值偏高')
        elif pe >= 50:
            score -= 15
            reasons.append(f'PE {pe:.1f},估值很高')
        else:
            reasons.append('PE无法计算')

        # PB估值
        if 0 < pb < 2:
            score += 15
            reasons.append(f'PB {pb:.2f},相对便宜')
        elif 2 <= pb < 5:
            score += 5
            reasons.append(f'PB {pb:.2f},估值正常')
        elif pb >= 5:
            score -= 10
            reasons.append(f'PB {pb:.2f},估值较贵')
        else:
            reasons.append('PB无法计算')

        # PEG分析 (PE/ROE比率,作为PEG的替代)
        if roe > 0 and pe > 0:
            peg = pe / roe
            if peg < 1:
                score += 15
                reasons.append(f'PE/ROE {peg:.2f},性价比高')
            elif peg < 1.5:
                score += 5
                reasons.append(f'PE/ROE {peg:.2f},性价比合理')
            else:
                reasons.append(f'PE/ROE {peg:.2f},性价比一般')

        # 市值大小(流动性考量)
        market_cap_billion = market_cap / 1e8  # 转换为亿
        if market_cap_billion > 5000:
            reasons.append(f'总市值{market_cap_billion:.0f}亿,超大盘股')
        elif market_cap_billion > 1000:
            reasons.append(f'总市值{market_cap_billion:.0f}亿,大盘股')
        elif market_cap_billion > 500:
            reasons.append(f'总市值{market_cap_billion:.0f}亿,中盘股')
        else:
            reasons.append(f'总市值{market_cap_billion:.0f}亿,小盘股')

        # 评级
        if score >= 70:
            level = '低估'
        elif score >= 50:
            level = '合理'
        else:
            level = '高估'

        return {
            'level': level,
            'score': score,
            'pe': pe,
            'pb': pb,
            'reasons': reasons
        }

    def comprehensive_analysis(self, symbol: str) -> Dict:
        """
        综合财务分析

        Args:
            symbol: 股票代码

        Returns:
            完整的财务分析结果
        """
        try:
            logger.info(f"开始{symbol}综合财务分析...")

            result = {
                'symbol': symbol,
                'timestamp': datetime.now()
            }

            # 1. 获取财务指标 (包含增长率)
            indicators = self.get_financial_indicators(symbol)
            if indicators:
                result['financial_indicators'] = indicators

            # 2. 提取增长率
            growth = self.calculate_growth_rate(symbol, indicators)
            if growth:
                result['growth_metrics'] = growth

            # 3. 获取估值指标
            valuation = self.get_valuation_metrics(symbol)
            if valuation:
                result['valuation_metrics'] = valuation

            # 4. 分析盈利能力
            profitability_analysis = self.analyze_profitability(indicators)
            result['profitability_analysis'] = profitability_analysis

            # 5. 分析成长性
            growth_analysis = self.analyze_growth(growth)
            result['growth_analysis'] = growth_analysis

            # 6. 分析估值
            valuation_analysis = self.analyze_valuation(valuation, indicators)
            result['valuation_analysis'] = valuation_analysis

            # 7. 综合评分
            total_score = (
                profitability_analysis.get('score', 0) * 0.4 +
                growth_analysis.get('score', 0) * 0.35 +
                valuation_analysis.get('score', 0) * 0.25
            )

            result['overall_score'] = total_score

            # 综合评级
            if total_score >= 80:
                overall_rating = '优秀'
                investment_advice = '值得重点关注,基本面优秀'
            elif total_score >= 65:
                overall_rating = '良好'
                investment_advice = '基本面良好,可适度配置'
            elif total_score >= 50:
                overall_rating = '一般'
                investment_advice = '基本面一般,谨慎对待'
            else:
                overall_rating = '较弱'
                investment_advice = '基本面较弱,规避风险'

            result['overall_rating'] = overall_rating
            result['investment_advice'] = investment_advice

            logger.info(f"{symbol}综合财务分析完成")
            return result

        except Exception as e:
            logger.error(f"{symbol}综合财务分析失败: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now()
            }


if __name__ == '__main__':
    """测试代码"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 70)
    print("财务数据分析器测试")
    print("=" * 70)

    analyzer = FinancialAnalyzer()

    # 测试贵州茅台 (600519)
    print("\n测试股票: 贵州茅台 (600519)")
    print("-" * 70)
    result = analyzer.comprehensive_analysis('600519')

    if 'error' not in result:
        print(f"\n📊 财务指标:")
        if 'financial_indicators' in result:
            ind = result['financial_indicators']
            print(f"  股票简称: {ind.get('stock_name', '')}")
            print(f"  所属行业: {ind.get('industry', '')}")
            print(f"  每股收益: {ind.get('eps', 0):.2f}元")
            print(f"  ROE: {ind.get('roe', 0):.2f}%")
            print(f"  毛利率: {ind.get('gross_margin', 0):.2f}%")

        print(f"\n📈 成长性指标:")
        if 'growth_metrics' in result:
            growth = result['growth_metrics']
            print(f"  营收同比增长: {growth.get('revenue_growth', 0):+.2f}%")
            print(f"  净利润同比增长: {growth.get('profit_growth', 0):+.2f}%")
            print(f"  营收环比增长: {growth.get('revenue_qoq', 0):+.2f}%")
            print(f"  净利润环比增长: {growth.get('profit_qoq', 0):+.2f}%")

        print(f"\n💰 估值指标:")
        if 'valuation_metrics' in result and 'valuation_analysis' in result:
            val = result['valuation_metrics']
            val_analysis = result['valuation_analysis']
            print(f"  最新价: {val.get('price', 0):.2f}元")
            print(f"  PE: {val_analysis.get('pe', 0):.2f}")
            print(f"  PB: {val_analysis.get('pb', 0):.2f}")
            print(f"  总市值: {val.get('market_cap', 0) / 1e8:.0f}亿")

        print(f"\n💡 分析结果:")
        print(f"  盈利能力: {result['profitability_analysis']['level']} ({result['profitability_analysis']['score']}分)")
        for reason in result['profitability_analysis'].get('reasons', [])[:2]:
            print(f"    - {reason}")
        print(f"  成长能力: {result['growth_analysis']['level']} ({result['growth_analysis']['score']}分)")
        for reason in result['growth_analysis'].get('reasons', [])[:2]:
            print(f"    - {reason}")
        print(f"  估值水平: {result['valuation_analysis']['level']} ({result['valuation_analysis']['score']}分)")
        for reason in result['valuation_analysis'].get('reasons', [])[:2]:
            print(f"    - {reason}")

        print(f"\n🎯 综合评价:")
        print(f"  综合评分: {result['overall_score']:.1f}/100")
        print(f"  综合评级: {result['overall_rating']}")
        print(f"  投资建议: {result['investment_advice']}")
    else:
        print(f"  ❌ 分析失败: {result['error']}")

    print("\n" + "=" * 70)
    print("✅ 财务数据分析器测试完成")
    print("=" * 70)
