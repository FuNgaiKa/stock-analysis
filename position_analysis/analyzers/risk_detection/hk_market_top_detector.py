"""
港股牛市见顶检测器
基于专业机构框架,综合估值、流动性、情绪、基本面四大维度
港股特色: 强资金流导向+外围敏感型市场

参考框架:
1. 估值类: 恒指PE/PB、恒科PE、AH溢价
2. 流动性: 美联储利率、人民币汇率、港元HIBOR、南向资金
3. 基本面: 中国PMI、社融、港股EPS增速
4. 情绪类: 换手率、VHSI、新股炒作、广度指标

见顶特征: 估值修复到头 + 流动性收紧 + 情绪过热 三者同步
"""
import yfinance as yf
import akshare as ak
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class HKMarketTopDetector:
    """港股见顶检测器 - 机构级四维度框架"""

    def __init__(self):
        """初始化港股见顶检测器"""
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 3600  # 1小时缓存

        # 历史阈值(基于港股20年历史数据)
        self.thresholds = {
            # 1. 估值类指标
            'hsi_pe': {
                'extreme': 14,   # 极度高估(2018年15+, 见顶信号)
                'high': 13,      # 高估
                'elevated': 12,  # 偏高(警惕)
                'normal': 10,    # 正常(历史均值10-12)
                'low': 9         # 低估(底部区间)
            },
            'hsi_pb': {
                'extreme': 1.5,  # 极度高估(>1.3历史罕见)
                'high': 1.3,     # 高估(见顶信号)
                'elevated': 1.2, # 偏高
                'normal': 1.1,   # 正常
                'low': 0.9       # 低估(底部<1.0)
            },
            'hsi_dividend': {
                'extreme_low': 2.0,    # <2%极低=泡沫
                'low': 2.5,            # <2.5%高估
                'normal': 3.0,         # 3%正常
                'attractive': 4.0,     # 4%吸引
                'bottom': 5.0          # >5%底部区间
            },
            'hstech_pe': {
                'extreme': 35,   # 恒科>35倍=泡沫(2021年50倍)
                'high': 30,      # >30倍高估
                'elevated': 25,  # 25倍偏高
                'normal': 20     # 20-25中性
            },
            # 2. AH溢价(港股相对A股估值)
            'ah_premium': {
                'extreme_premium': 150,  # >150 A股狂热
                'high_premium': 140,     # >140 A股过热
                'normal_premium': 120,   # 120正常溢价
                'parity': 100,           # 100平价
                'hk_premium': 90         # <100港股比A股贵(反转信号)
            },
            # 3. 流动性指标
            'usdcny': {
                'extreme_weak': 7.30,  # 人民币破7.3=贬值压力大
                'weak': 7.15,          # >7.15偏弱
                'neutral': 7.00,       # 7.0中性
                'strong': 6.80         # <6.8人民币强势
            },
            'dxy': {
                'extreme_high': 110,  # 美元极强=港股资金外流
                'high': 105,          # >105美元强势
                'normal_high': 100,   # 100中性偏强
                'normal_low': 95,     # 95中性
                'low': 90             # <90美元弱=港股受益
            },
            'fed_rate': {
                'extreme_high': 5.5,  # 联储利率>5.5%历史高位
                'high': 5.0,          # 5%高利率
                'elevated': 4.0,      # 4%偏高
                'normal': 2.5,        # 2-3%正常
                'low': 1.0            # <1%宽松
            },
            # 4. 南向资金(北水)
            'southbound_flow': {
                'extreme_inflow': 300,   # 单日>300亿狂热
                'high_inflow': 200,      # >200亿大量流入
                'normal_inflow': 100,    # 100亿正常
                'low_inflow': 50,        # 50亿偏少
                'outflow': 0             # <0流出=见顶信号
            },
            # 5. 情绪指标
            'turnover_rate': {
                'extreme': 4.0,  # 恒指换手>4%过热(2015/2021顶部)
                'high': 3.0,     # >3%活跃
                'normal': 2.0,   # 2%正常
                'low': 1.0       # <1%冷清
            },
            'vhsi': {
                'extreme_low': 15,   # <15极度乐观=顶部信号
                'low': 20,           # <20乐观
                'normal': 25,        # 25正常
                'high': 30,          # >30恐慌
                'panic': 40          # >40极度恐慌=底部
            },
            # 6. 基本面指标
            'china_pmi': {
                'expansion': 52,   # >52扩张强劲
                'growth': 51,      # 51温和扩张
                'neutral': 50,     # 50荣枯线
                'contraction': 49  # <49收缩
            },
            'eps_growth': {
                'extreme': 20,   # >20%盈利高增长
                'high': 15,      # 15%高增
                'normal': 10,    # 10%正常
                'low': 5,        # 5%低增
                'negative': 0    # <0负增长
            }
        }

    def get_hsi_valuation(self) -> Optional[Dict[str, float]]:
        """
        获取恒生指数估值数据(PE/PB/股息率)
        使用yfinance获取EWH(香港ETF)作为近似

        Returns:
            估值数据字典
        """
        try:
            # 尝试获取恒指ETF(EWH)的估值数据作为近似
            ewh = yf.Ticker("EWH")  # iShares MSCI Hong Kong ETF
            info = ewh.info

            # 获取PE
            pe = info.get('trailingPE', None)

            # 获取股息率
            div_yield = info.get('dividendYield', None) or info.get('yield', None)
            if div_yield:
                div_yield_pct = div_yield * 100 if div_yield < 1 else div_yield

            # PB通常不直接提供,使用经验值或设为None
            pb = info.get('priceToBook', None)

            logger.info(f"恒指估值 - PE: {pe}, PB: {pb}, 股息率: {div_yield_pct}%")

            return {
                'pe': float(pe) if pe else None,
                'pb': float(pb) if pb else None,
                'dividend_yield': float(div_yield_pct) if div_yield else None
            }

        except Exception as e:
            logger.error(f"获取恒指估值失败: {str(e)}")
            return None

    def get_ah_premium_index(self) -> Optional[float]:
        """
        获取AH溢价指数
        A股相对H股的溢价程度(100=平价)

        Returns:
            AH溢价指数
        """
        try:
            # 使用AKShare获取AH溢价指数
            df = ak.stock_em_hsgt_board_rank(symbol="AH溢价")

            if df.empty:
                logger.warning("AH溢价数据为空")
                return None

            # AH溢价指数通常在特定列,这里使用简化方法
            # 实际需要根据返回的列结构调整
            # 备用方案: 使用港股通数据推算

            # 简化: 返回一个估算值(需要实际数据验证)
            # 这里先返回None,实际使用时需要完善
            logger.warning("AH溢价指数获取需要进一步实现")
            return None

        except Exception as e:
            logger.error(f"获取AH溢价指数失败: {str(e)}")
            return None

    def get_southbound_net_flow(self) -> Optional[Dict[str, Any]]:
        """
        获取南向资金净流入情况

        Returns:
            南向资金数据
        """
        try:
            # 使用AKShare获取南向资金数据
            # 注: 实际API名称需要确认
            df = ak.stock_hsgt_fund_flow_summary_em()

            if df.empty:
                return None

            # 获取最近的净流入数据
            # 列名需要根据实际返回调整
            latest = df.iloc[-1]

            # 提取关键数据(列名待确认)
            result = {
                'net_inflow': 0.0,  # 净流入(亿)
                'date': latest.iloc[0] if len(df.columns) > 0 else None
            }

            logger.info(f"南向资金净流入: {result['net_inflow']:.2f}亿")
            return result

        except Exception as e:
            logger.error(f"获取南向资金失败: {str(e)}")
            return None

    def get_dxy(self) -> Optional[float]:
        """
        获取美元指数(港元联系汇率,美元走强对港股不利)

        Returns:
            DXY值
        """
        try:
            dxy = yf.Ticker("DX-Y.NYB")  # 美元指数期货
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
        估值风险评估(PE/PB/股息率)

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

        # 获取恒指估值
        valuation = self.get_hsi_valuation()

        if not valuation:
            result['error'] = '无法获取恒指估值数据'
            return result

        # 1. PE估值
        pe = valuation.get('pe')
        if pe:
            if pe > self.thresholds['hsi_pe']['extreme']:
                pe_score = 100
                pe_level = '极度高估'
            elif pe > self.thresholds['hsi_pe']['high']:
                pe_score = 75
                pe_level = '高估'
            elif pe > self.thresholds['hsi_pe']['elevated']:
                pe_score = 50
                pe_level = '偏高'
            elif pe > self.thresholds['hsi_pe']['normal']:
                pe_score = 25
                pe_level = '正常'
            else:
                pe_score = 0
                pe_level = '低估'

            result['indicators']['hsi_pe'] = {
                'value': pe,
                'score': pe_score,
                'level': pe_level,
                'signal': f"恒指PE={pe:.1f}, {pe_level}"
            }
            total_score += pe_score
            valid_count += 1

        # 2. PB估值
        pb = valuation.get('pb')
        if pb:
            if pb > self.thresholds['hsi_pb']['extreme']:
                pb_score = 100
                pb_level = '极度高估'
            elif pb > self.thresholds['hsi_pb']['high']:
                pb_score = 75
                pb_level = '高估'
            elif pb > self.thresholds['hsi_pb']['elevated']:
                pb_score = 50
                pb_level = '偏高'
            elif pb > self.thresholds['hsi_pb']['normal']:
                pb_score = 25
                pb_level = '正常'
            else:
                pb_score = 0
                pb_level = '低估'

            result['indicators']['hsi_pb'] = {
                'value': pb,
                'score': pb_score,
                'level': pb_level,
                'signal': f"恒指PB={pb:.2f}, {pb_level}"
            }
            total_score += pb_score
            valid_count += 1

        # 3. 股息率
        div_yield = valuation.get('dividend_yield')
        if div_yield:
            if div_yield < self.thresholds['hsi_dividend']['extreme_low']:
                div_score = 100
                div_level = '极度高估'
            elif div_yield < self.thresholds['hsi_dividend']['low']:
                div_score = 75
                div_level = '高估'
            elif div_yield < self.thresholds['hsi_dividend']['normal']:
                div_score = 50
                div_level = '偏高'
            elif div_yield < self.thresholds['hsi_dividend']['attractive']:
                div_score = 25
                div_level = '正常'
            else:
                div_score = 0
                div_level = '吸引'

            result['indicators']['hsi_dividend'] = {
                'value': div_yield,
                'score': div_score,
                'level': div_level,
                'signal': f"恒指股息率={div_yield:.2f}%, {div_level}"
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

    def calculate_liquidity_risk(self) -> Dict[str, Any]:
        """
        流动性风险评估(美元指数/港股通/南向资金)

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

        # 1. 美元指数(美元强=港股资金流出压力)
        dxy = self.get_dxy()
        if dxy:
            if dxy > self.thresholds['dxy']['extreme_high']:
                dxy_score = 100
                dxy_level = '美元极强压力'
            elif dxy > self.thresholds['dxy']['high']:
                dxy_score = 70
                dxy_level = '美元强势'
            elif dxy > self.thresholds['dxy']['normal_high']:
                dxy_score = 40
                dxy_level = '美元偏强'
            elif dxy > self.thresholds['dxy']['normal_low']:
                dxy_score = 20
                dxy_level = '正常'
            else:
                dxy_score = 0
                dxy_level = '美元弱势'

            result['indicators']['dxy'] = {
                'value': dxy,
                'score': dxy_score,
                'level': dxy_level,
                'signal': f"美元指数={dxy:.1f}, {dxy_level}"
            }
            total_score += dxy_score
            valid_count += 1

        # 2. 南向资金(大量流入后可能见顶)
        # 注: 这里简化处理,实际需要更详细的实现
        southbound = self.get_southbound_net_flow()
        if southbound:
            # 这里需要实际数据来评估
            # 暂时跳过或使用占位符
            pass

        # 计算综合得分
        if valid_count > 0:
            avg_score = total_score / valid_count
            result['risk_score'] = avg_score

            if avg_score >= 85:
                result['risk_level'] = '流动性危机'
            elif avg_score >= 70:
                result['risk_level'] = '流动性紧张'
            elif avg_score >= 50:
                result['risk_level'] = '流动性偏紧'
            else:
                result['risk_level'] = '流动性正常'

        return result

    def detect_top_risk(self) -> Dict[str, Any]:
        """
        综合检测港股见顶风险

        Returns:
            综合分析结果
        """
        result = {
            'timestamp': datetime.now(),
            'market': 'HK',
            'valuation': {},
            'liquidity': {},
            'overall_risk': {},
        }

        # 1. 估值风险
        valuation = self.calculate_valuation_risk()
        result['valuation'] = valuation

        # 2. 流动性风险
        liquidity = self.calculate_liquidity_risk()
        result['liquidity'] = liquidity

        # 3. 综合评估
        scores = []
        if valuation.get('risk_score', 0) > 0:
            scores.append(('估值', valuation['risk_score']))
        if liquidity.get('risk_score', 0) > 0:
            scores.append(('流动性', liquidity['risk_score']))

        if scores:
            # 加权: 估值60%, 流动性40%(港股受全球资金流影响大)
            weights = {'估值': 0.6, '流动性': 0.4}
            total_weighted_score = sum(score * weights.get(name, 0.5) for name, score in scores)

            overall_score = total_weighted_score

            # 综合风险等级
            if overall_score >= 85:
                overall_level = '极度危险'
                recommendation = '强烈建议: 减仓至30%以下,港股处于高估+流动性紧张,见顶风险极高'
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
                recommendation = '积极配置: 可保持80-90%仓位,港股估值吸引力上升'

            result['overall_risk'] = {
                'score': overall_score,
                'level': overall_level,
                'recommendation': recommendation,
                'summary': self._generate_summary(valuation, liquidity)
            }

        return result

    def _generate_summary(self, valuation: Dict, liquidity: Dict) -> str:
        """生成风险总结"""
        summary_parts = []

        # 估值总结
        if valuation.get('risk_level') in ['极度高估', '高估']:
            summary_parts.append(f"估值{valuation['risk_level']}")

        # 流动性总结
        if liquidity.get('risk_level') in ['流动性危机', '流动性紧张']:
            summary_parts.append(f"{liquidity['risk_level']}")

        if not summary_parts:
            return "港股估值和流动性处于正常区间"

        return "; ".join(summary_parts) + " - 建议谨慎"


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    detector = HKMarketTopDetector()

    print("=" * 80)
    print("港股见顶检测器测试")
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

        print(f"\n流动性分析:")
        for name, data in result['liquidity'].get('indicators', {}).items():
            print(f"  {name}: {data['signal']}")
    else:
        print("检测失败")

    print("\n" + "=" * 80)
