"""
美股见顶检测器
综合估值、流动性、情绪等多维度指标判断美股周期顶部风险
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class USMarketTopDetector:
    """美股见顶检测器"""

    def __init__(self):
        """初始化美股见顶检测器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 3600  # 1小时缓存

        # 历史阈值
        self.thresholds = {
            'shiller_cape': {
                'extreme': 35,   # 极度高估(2000年44, 2021年38)
                'high': 30,      # 高估
                'elevated': 25,  # 偏高
                'normal': 20     # 正常(历史均值约16-17)
            },
            'forward_pe': {
                'extreme': 24,   # 极度高估
                'high': 22,      # 高估
                'elevated': 20,  # 偏高
                'normal': 17     # 正常(历史均值约16-17)
            },
            'dividend_yield': {
                'extreme': 1.2,  # 极低股息=高估
                'high': 1.5,
                'normal': 2.0,
                'attractive': 3.0  # 吸引人的股息
            },
            'buffett_indicator': {
                'extreme': 180,  # 极度泡沫
                'high': 150,     # 高估
                'elevated': 120, # 偏高
                'normal': 100    # 正常
            },
            'vix': {
                'complacent': 12,  # 过度乐观
                'normal_low': 15,
                'normal_high': 20,
                'fear': 30         # 恐慌
            },
            'put_call_ratio': {
                'extreme_optimism': 0.6,  # 过度乐观
                'optimism': 0.7,
                'normal': 0.8,
                'pessimism': 1.0         # 看跌
            },
            # 美元指数(DXY强=跨国公司盈利受损+新兴市场资金回流美债)
            'dxy': {
                'extreme_high': 110,  # 极强美元(2022年114暴跌)
                'high': 105,          # 强势美元(美股压力)
                'elevated': 103,      # 偏强
                'normal_high': 100,   # 中性偏强
                'normal_low': 95,     # 中性
                'low': 90             # 弱势美元(美股受益)
            }
        }

    def get_shiller_cape(self) -> Optional[float]:
        """
        获取Shiller CAPE (周期调整市盈率)
        简化版: 使用SPY ETF的PE近似

        Returns:
            CAPE值
        """
        try:
            # 使用SPY ETF获取PE(指数本身不提供PE数据)
            spy = yf.Ticker("SPY")
            info = spy.info

            # 尝试获取PE
            pe = info.get('trailingPE', None)
            if pe:
                # 注: 这是简化版,真实CAPE需要10年平均盈利
                # 可以用PE * 调整因子近似
                cape_approx = pe * 0.85  # 经验调整
                logger.info(f"标普500 PE (CAPE近似): {cape_approx:.2f}")
                return cape_approx

            return None
        except Exception as e:
            logger.error(f"获取CAPE失败: {str(e)}")
            return None

    def get_forward_pe(self) -> Optional[float]:
        """
        获取标普500前瞻市盈率
        使用SPY ETF数据

        Returns:
            Forward PE值
        """
        try:
            # 使用SPY ETF获取PE
            spy = yf.Ticker("SPY")
            info = spy.info

            forward_pe = info.get('forwardPE', None)
            if forward_pe:
                logger.info(f"标普500 Forward PE: {forward_pe:.2f}")
                return forward_pe

            # 备用: 使用trailing PE
            trailing_pe = info.get('trailingPE', None)
            if trailing_pe:
                logger.info(f"标普500 Trailing PE (备用): {trailing_pe:.2f}")
                return trailing_pe

            return None
        except Exception as e:
            logger.error(f"获取Forward PE失败: {str(e)}")
            return None

    def get_dividend_yield(self) -> Optional[float]:
        """
        获取标普500股息收益率

        Returns:
            股息收益率(%)
        """
        try:
            # 使用SPY ETF获取股息率
            spy = yf.Ticker("SPY")
            info = spy.info

            div_yield = info.get('dividendYield', None) or info.get('yield', None)
            if div_yield:
                # yfinance已经返回百分比格式(如0.0109),直接使用
                # 如果值>1说明是百分比,否则需要*100
                if div_yield > 1:
                    div_yield_pct = div_yield
                else:
                    div_yield_pct = div_yield * 100
                logger.info(f"标普500股息率: {div_yield_pct:.2f}%")
                return div_yield_pct

            return None
        except Exception as e:
            logger.error(f"获取股息率失败: {str(e)}")
            return None

    def get_vix(self) -> Optional[float]:
        """
        获取VIX恐慌指数

        Returns:
            VIX值
        """
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="1d")

            if not hist.empty:
                vix_value = float(hist['Close'].iloc[-1])
                logger.info(f"VIX: {vix_value:.2f}")
                return vix_value

            return None
        except Exception as e:
            logger.error(f"获取VIX失败: {str(e)}")
            return None

    def get_dxy(self) -> Optional[float]:
        """
        获取美元指数DXY
        强美元→美股压力(跨国公司盈利受损+资金回流美债)

        Returns:
            DXY值
        """
        try:
            dxy = yf.Ticker("DX-Y.NYB")
            hist = dxy.history(period="1d")

            if not hist.empty:
                dxy_value = float(hist['Close'].iloc[-1])
                logger.info(f"美元指数DXY: {dxy_value:.2f}")
                return dxy_value

            return None
        except Exception as e:
            logger.error(f"获取美元指数失败: {str(e)}")
            return None

    def calculate_valuation_risk(self) -> Dict[str, Any]:
        """
        估值风险评估

        Returns:
            估值风险分析
        """
        result = {
            'indicators': {},
            'risk_score': 0,
            'risk_level': '',
        }

        total_score = 0
        valid_count = 0

        # 1. Shiller CAPE
        cape = self.get_shiller_cape()
        if cape:
            if cape > self.thresholds['shiller_cape']['extreme']:
                cape_score = 100
                cape_level = '极度高估'
            elif cape > self.thresholds['shiller_cape']['high']:
                cape_score = 75
                cape_level = '高估'
            elif cape > self.thresholds['shiller_cape']['elevated']:
                cape_score = 50
                cape_level = '偏高'
            elif cape > self.thresholds['shiller_cape']['normal']:
                cape_score = 25
                cape_level = '正常'
            else:
                cape_score = 0
                cape_level = '低估'

            result['indicators']['shiller_cape'] = {
                'value': cape,
                'score': cape_score,
                'level': cape_level,
                'signal': f"Shiller CAPE={cape:.1f}, {cape_level}"
            }
            total_score += cape_score
            valid_count += 1

        # 2. Forward PE
        forward_pe = self.get_forward_pe()
        if forward_pe:
            if forward_pe > self.thresholds['forward_pe']['extreme']:
                pe_score = 100
                pe_level = '极度高估'
            elif forward_pe > self.thresholds['forward_pe']['high']:
                pe_score = 75
                pe_level = '高估'
            elif forward_pe > self.thresholds['forward_pe']['elevated']:
                pe_score = 50
                pe_level = '偏高'
            elif forward_pe > self.thresholds['forward_pe']['normal']:
                pe_score = 25
                pe_level = '正常'
            else:
                pe_score = 0
                pe_level = '低估'

            result['indicators']['forward_pe'] = {
                'value': forward_pe,
                'score': pe_score,
                'level': pe_level,
                'signal': f"Forward PE={forward_pe:.1f}, {pe_level}"
            }
            total_score += pe_score
            valid_count += 1

        # 3. 股息收益率
        div_yield = self.get_dividend_yield()
        if div_yield:
            if div_yield < self.thresholds['dividend_yield']['extreme']:
                div_score = 100
                div_level = '极度高估'
            elif div_yield < self.thresholds['dividend_yield']['high']:
                div_score = 75
                div_level = '高估'
            elif div_yield < self.thresholds['dividend_yield']['normal']:
                div_score = 50
                div_level = '偏高'
            elif div_yield < self.thresholds['dividend_yield']['attractive']:
                div_score = 25
                div_level = '正常'
            else:
                div_score = 0
                div_level = '吸引'

            result['indicators']['dividend_yield'] = {
                'value': div_yield,
                'score': div_score,
                'level': div_level,
                'signal': f"股息率={div_yield:.2f}%, {div_level}"
            }
            total_score += div_score
            valid_count += 1

        # 计算综合得分
        if valid_count > 0:
            avg_score = total_score / valid_count
            result['risk_score'] = avg_score

            if avg_score >= 85:
                result['risk_level'] = '极度高估'
            elif avg_score >= 70:
                result['risk_level'] = '高估'
            elif avg_score >= 50:
                result['risk_level'] = '偏高'
            elif avg_score >= 25:
                result['risk_level'] = '正常'
            else:
                result['risk_level'] = '低估'

        return result

    def calculate_sentiment_risk(self) -> Dict[str, Any]:
        """
        情绪风险评估

        Returns:
            情绪风险分析
        """
        result = {
            'indicators': {},
            'risk_score': 0,
            'risk_level': '',
        }

        total_score = 0
        valid_count = 0

        # 1. VIX
        vix = self.get_vix()
        if vix:
            if vix < self.thresholds['vix']['complacent']:
                vix_score = 100
                vix_level = '过度自满'
            elif vix < self.thresholds['vix']['normal_low']:
                vix_score = 60
                vix_level = '乐观'
            elif vix < self.thresholds['vix']['normal_high']:
                vix_score = 30
                vix_level = '正常'
            elif vix < self.thresholds['vix']['fear']:
                vix_score = 10
                vix_level = '警惕'
            else:
                vix_score = 0
                vix_level = '恐慌'

            result['indicators']['vix'] = {
                'value': vix,
                'score': vix_score,
                'level': vix_level,
                'signal': f"VIX={vix:.1f}, {vix_level}"
            }
            total_score += vix_score
            valid_count += 1

        # 计算综合得分
        if valid_count > 0:
            avg_score = total_score / valid_count
            result['risk_score'] = avg_score

            if avg_score >= 85:
                result['risk_level'] = '极度过热'
            elif avg_score >= 70:
                result['risk_level'] = '过热'
            elif avg_score >= 50:
                result['risk_level'] = '乐观'
            else:
                result['risk_level'] = '正常'

        return result

    def calculate_liquidity_risk(self) -> Dict[str, Any]:
        """
        流动性风险评估(美元指数)

        Returns:
            流动性风险分析
        """
        result = {
            'indicators': {},
            'risk_score': 0,
            'risk_level': '',
        }

        total_score = 0
        valid_count = 0

        # DXY美元指数
        dxy = self.get_dxy()
        if dxy:
            if dxy > self.thresholds['dxy']['extreme_high']:
                dxy_score = 100
                dxy_level = '极强美元'
            elif dxy > self.thresholds['dxy']['high']:
                dxy_score = 75
                dxy_level = '强势美元'
            elif dxy > self.thresholds['dxy']['elevated']:
                dxy_score = 50
                dxy_level = '偏强美元'
            elif dxy > self.thresholds['dxy']['normal_high']:
                dxy_score = 30
                dxy_level = '中性偏强'
            elif dxy > self.thresholds['dxy']['normal_low']:
                dxy_score = 10
                dxy_level = '中性'
            else:
                dxy_score = 0
                dxy_level = '弱势美元'

            result['indicators']['dxy'] = {
                'value': dxy,
                'score': dxy_score,
                'level': dxy_level,
                'signal': f"DXY={dxy:.1f}, {dxy_level}(强美元→美股压力)"
            }
            total_score += dxy_score
            valid_count += 1

        # 计算综合得分
        if valid_count > 0:
            avg_score = total_score / valid_count
            result['risk_score'] = avg_score

            if avg_score >= 85:
                result['risk_level'] = '极度紧缩'
            elif avg_score >= 70:
                result['risk_level'] = '紧缩'
            elif avg_score >= 50:
                result['risk_level'] = '偏紧'
            else:
                result['risk_level'] = '正常'

        return result

    def detect_top_risk(self) -> Dict[str, Any]:
        """
        综合检测美股见顶风险

        Returns:
            综合分析结果
        """
        result = {
            'timestamp': datetime.now(),
            'market': 'US',
            'valuation': {},
            'sentiment': {},
            'liquidity': {},
            'overall_risk': {},
        }

        # 1. 估值风险
        valuation = self.calculate_valuation_risk()
        result['valuation'] = valuation

        # 2. 情绪风险
        sentiment = self.calculate_sentiment_risk()
        result['sentiment'] = sentiment

        # 3. 流动性风险
        liquidity = self.calculate_liquidity_risk()
        result['liquidity'] = liquidity

        # 4. 综合评估
        scores = []
        if valuation.get('risk_score', 0) > 0:
            scores.append(('估值', valuation['risk_score']))
        if sentiment.get('risk_score', 0) > 0:
            scores.append(('情绪', sentiment['risk_score']))
        if liquidity.get('risk_score', 0) > 0:
            scores.append(('流动性', liquidity['risk_score']))

        if scores:
            # 加权: 估值60%, 情绪20%, 流动性20%
            weights = {'估值': 0.6, '情绪': 0.2, '流动性': 0.2}
            total_weighted_score = sum(score * weights.get(name, 0.33) for name, score in scores)

            overall_score = total_weighted_score

            # 综合风险等级
            if overall_score >= 85:
                overall_level = '极度危险'
                recommendation = '强烈建议: 减仓至30%以下,美股处于历史高估+情绪过热,见顶风险极高'
            elif overall_score >= 70:
                overall_level = '高风险'
                recommendation = '建议: 减仓至50%,多项指标接近历史极值,警惕回调'
            elif overall_score >= 50:
                overall_level = '警惕'
                recommendation = '谨慎: 控制仓位在60-70%,估值偏高,密切关注'
            elif overall_score >= 30:
                overall_level = '正常'
                recommendation = '正常配置: 维持标准仓位70-80%'
            else:
                overall_level = '安全'
                recommendation = '积极配置: 可保持80-90%仓位'

            result['overall_risk'] = {
                'score': overall_score,
                'level': overall_level,
                'recommendation': recommendation,
                'summary': self._generate_summary(valuation, sentiment, liquidity)
            }

        return result

    def _generate_summary(self, valuation: Dict, sentiment: Dict, liquidity: Dict) -> str:
        """生成风险总结"""
        summary_parts = []

        # 估值总结
        if valuation.get('risk_level') in ['极度高估', '高估']:
            summary_parts.append(f"估值{valuation['risk_level']}")

        # 情绪总结
        if sentiment.get('risk_level') in ['极度过热', '过热']:
            summary_parts.append(f"情绪{sentiment['risk_level']}")

        # 流动性总结
        if liquidity.get('risk_level') in ['极度紧缩', '紧缩']:
            summary_parts.append(f"流动性{liquidity['risk_level']}")

        if not summary_parts:
            return "美股估值、情绪和流动性处于正常区间"

        return "; ".join(summary_parts) + " - 建议谨慎"


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    detector = USMarketTopDetector()

    print("=" * 80)
    print("美股见顶检测器测试")
    print("=" * 80)

    result = detector.detect_top_risk()

    if 'overall_risk' in result:
        overall = result['overall_risk']
        print(f"\n综合风险评分: {overall['score']:.1f}/100")
        print(f"风险等级: {overall['level']}")
        print(f"建议: {overall['recommendation']}")
        print(f"风险总结: {overall['summary']}")

        print(f"\n估值分析:")
        for name, data in result['valuation'].get('indicators', {}).items():
            print(f"  {name}: {data['signal']}")

        print(f"\n情绪分析:")
        for name, data in result['sentiment'].get('indicators', {}).items():
            print(f"  {name}: {data['signal']}")

        print(f"\n流动性分析:")
        for name, data in result['liquidity'].get('indicators', {}).items():
            print(f"  {name}: {data['signal']}")
    else:
        print("检测失败")

    print("\n" + "=" * 80)
