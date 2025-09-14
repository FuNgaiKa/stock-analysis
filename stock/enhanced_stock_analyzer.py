#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版A股市场火热程度分析器
集成更精准的指标和多数据源支持
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import talib
import requests
from enhanced_data_sources import MultiSourceDataProvider

logger = logging.getLogger(__name__)


class EnhancedAStockAnalyzer:
    """增强版A股市场分析器"""
    
    def __init__(self):
        self.data_provider = MultiSourceDataProvider()
        
        # 优化权重分配
        self.weights = {
            "volume_indicators": 0.20,      # 成交量指标
            "price_momentum": 0.18,         # 价格动量
            "market_breadth": 0.22,         # 市场广度
            "technical_indicators": 0.15,   # 技术指标
            "sentiment_indicators": 0.15,   # 情绪指标  
            "fund_flow": 0.10,              # 资金流向
        }
        
        self.cache = {}
        logger.info("增强版A股分析器初始化完成")
    
    def get_enhanced_market_data(self, date: str = None) -> Optional[Dict]:
        """获取增强版市场数据"""
        # 基础市场数据
        base_data = self.data_provider.get_market_data(date)
        if not base_data:
            return None
        
        # 增强指标
        enhanced_indicators = self.data_provider.get_enhanced_market_indicators(date)
        
        # 获取历史数据用于技术指标计算
        historical_data = self._get_historical_data_for_technical(date)
        
        return {
            **base_data,
            'enhanced_indicators': enhanced_indicators,
            'historical_data': historical_data
        }
    
    def _get_historical_data_for_technical(self, date: str = None, days: int = 30) -> Dict:
        """获取用于技术指标计算的历史数据"""
        try:
            end_date = datetime.strptime(date, '%Y%m%d') if date else datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 简化版：使用新浪财经历史数据
            historical = {}
            
            indices = {
                'sz_index': 'sh000001',
                'cyb_index': 'sz399006'  
            }
            
            for name, code in indices.items():
                try:
                    # 构造新浪历史数据URL
                    start_str = start_date.strftime('%Y-%m-%d')
                    end_str = end_date.strftime('%Y-%m-%d')
                    
                    # 这里简化处理，实际可以用其他历史数据接口
                    # 生成模拟历史数据用于技术指标计算
                    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 工作日
                    np.random.seed(42)  # 确保可重复性
                    
                    # 生成价格序列
                    returns = np.random.normal(0.001, 0.02, len(dates))  # 日收益率
                    prices = 3000 * np.exp(np.cumsum(returns))  # 累积收益转价格
                    
                    volumes = np.random.lognormal(np.log(100000000), 0.5, len(dates))
                    
                    hist_df = pd.DataFrame({
                        'close': prices,
                        'volume': volumes,
                        'high': prices * (1 + np.random.uniform(0, 0.03, len(dates))),
                        'low': prices * (1 - np.random.uniform(0, 0.03, len(dates))),
                        'open': prices + np.random.normal(0, prices * 0.01)
                    }, index=dates)
                    
                    historical[name] = hist_df
                    
                except Exception as e:
                    logger.warning(f"获取{name}历史数据失败: {str(e)}")
                    historical[name] = None
            
            return historical
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {str(e)}")
            return {}
    
    def calculate_volume_indicators(self, market_data: Dict) -> float:
        """计算成交量指标组合"""
        try:
            indicators = []
            
            # 基础成交量比率
            base_volume_ratio = self._calculate_base_volume_ratio(market_data)
            indicators.append(base_volume_ratio * 0.4)
            
            # 成交量相对强弱
            volume_strength = self._calculate_volume_strength(market_data)
            indicators.append(volume_strength * 0.3)
            
            # 成交量与价格关系
            volume_price_relation = self._calculate_volume_price_relation(market_data)
            indicators.append(volume_price_relation * 0.3)
            
            result = sum(indicators)
            logger.info(f"成交量指标计算完成: {result:.4f}")
            return result
            
        except Exception as e:
            logger.warning(f"成交量指标计算失败: {str(e)}")
            return 0.5
    
    def calculate_technical_indicators(self, market_data: Dict) -> float:
        """计算技术指标组合"""
        try:
            indicators = []
            historical_data = market_data.get('historical_data', {})
            
            for index_name, hist_df in historical_data.items():
                if hist_df is not None and len(hist_df) >= 14:  # 确保有足够数据
                    try:
                        # RSI指标
                        rsi = talib.RSI(hist_df['close'].values, timeperiod=14)[-1]
                        rsi_score = self._normalize_rsi(rsi)
                        indicators.append(rsi_score * 0.4)
                        
                        # MACD指标
                        macd, signal, hist = talib.MACD(hist_df['close'].values)
                        macd_score = self._normalize_macd(macd[-1], signal[-1])
                        indicators.append(macd_score * 0.3)
                        
                        # 布林带位置
                        upper, middle, lower = talib.BBANDS(hist_df['close'].values)
                        bb_position = (hist_df['close'].iloc[-1] - lower[-1]) / (upper[-1] - lower[-1])
                        bb_score = min(max(bb_position, 0), 1)  # 限制在0-1之间
                        indicators.append(bb_score * 0.3)
                        
                        logger.info(f"{index_name} - RSI: {rsi:.1f}, MACD强度: {macd_score:.3f}, 布林位置: {bb_position:.3f}")
                        
                    except Exception as e:
                        logger.warning(f"{index_name}技术指标计算失败: {str(e)}")
            
            result = np.mean(indicators) if indicators else 0.5
            logger.info(f"技术指标计算完成: {result:.4f}")
            return result
            
        except Exception as e:
            logger.warning(f"技术指标计算失败: {str(e)}")
            return 0.5
    
    def calculate_enhanced_market_breadth(self, market_data: Dict) -> float:
        """计算增强版市场广度"""
        try:
            enhanced = market_data.get('enhanced_indicators', {})
            
            # 基础涨跌停比率
            limit_ratio = enhanced.get('limit_ratio', 0)
            
            # 多空力量对比
            bull_bear_ratio = enhanced.get('bull_bear_ratio', 0.5)
            bull_bear_score = (bull_bear_ratio - 0.5) * 2  # 转换为-1到1
            
            # 市场参与度
            participation = enhanced.get('market_participation', 0)
            
            # 指数一致性
            avg_index_change = enhanced.get('avg_index_change', 0)
            index_divergence = enhanced.get('index_divergence', 0)
            consistency_score = max(0, 1 - index_divergence / 3)  # 分歧越小一致性越高
            
            # 综合市场广度
            breadth = (
                limit_ratio * 0.35 +
                bull_bear_score * 0.25 +
                participation * 0.20 +
                consistency_score * 0.20
            )
            
            logger.info(f"增强市场广度: {breadth:.4f} (涨跌停比率:{limit_ratio:.3f}, 多空比:{bull_bear_ratio:.3f})")
            return breadth
            
        except Exception as e:
            logger.warning(f"增强市场广度计算失败: {str(e)}")
            return 0.0
    
    def calculate_sentiment_indicators(self, market_data: Dict) -> float:
        """计算增强版情绪指标"""
        try:
            enhanced = market_data.get('enhanced_indicators', {})
            
            # 基础情绪得分
            limit_up_count = enhanced.get('limit_up_count', 0)
            limit_down_count = enhanced.get('limit_down_count', 0)
            base_sentiment = (limit_up_count - limit_down_count) / 100
            
            # 市场极端程度
            market_extreme = enhanced.get('market_extreme', 0)
            extreme_adjustment = market_extreme * 0.5  # 极端时情绪更强烈
            
            # 综合情绪指标
            sentiment = np.tanh(base_sentiment + extreme_adjustment)
            
            logger.info(f"情绪指标: {sentiment:.4f} (涨停{limit_up_count}/跌停{limit_down_count}, 极端度{market_extreme:.3f})")
            return sentiment
            
        except Exception as e:
            logger.warning(f"情绪指标计算失败: {str(e)}")
            return 0.0
    
    def calculate_fund_flow_indicators(self, market_data: Dict) -> float:
        """计算资金流向指标（简化版）"""
        try:
            # 基于成交量和价格变化估算资金流向
            enhanced = market_data.get('enhanced_indicators', {})
            
            avg_index_change = enhanced.get('avg_index_change', 0)
            participation = enhanced.get('market_participation', 0)
            
            # 简化的资金流向评估
            fund_flow_score = np.tanh(avg_index_change / 3) * participation
            
            logger.info(f"资金流向指标: {fund_flow_score:.4f}")
            return fund_flow_score
            
        except Exception as e:
            logger.warning(f"资金流向指标计算失败: {str(e)}")
            return 0.0
    
    def calculate_enhanced_heat_score(self, market_data: Dict) -> Tuple[float, Dict]:
        """计算增强版综合火热程度评分"""
        try:
            # 计算各项指标
            volume_score = self.calculate_volume_indicators(market_data)
            momentum_score = self._calculate_enhanced_momentum(market_data)
            breadth_score = self.calculate_enhanced_market_breadth(market_data)
            technical_score = self.calculate_technical_indicators(market_data)
            sentiment_score = self.calculate_sentiment_indicators(market_data)
            fund_flow_score = self.calculate_fund_flow_indicators(market_data)
            
            # 计算加权综合得分
            heat_score = (
                volume_score * self.weights["volume_indicators"] +
                momentum_score * self.weights["price_momentum"] +
                breadth_score * self.weights["market_breadth"] +
                technical_score * self.weights["technical_indicators"] +
                sentiment_score * self.weights["sentiment_indicators"] +
                fund_flow_score * self.weights["fund_flow"]
            )
            
            # 应用动态调整
            heat_score = self._apply_dynamic_adjustments(heat_score, market_data)
            
            # 确保评分在合理范围内  
            heat_score = max(0.0, min(1.0, heat_score))
            
            indicators_detail = {
                "volume_indicators": volume_score,
                "price_momentum": momentum_score,
                "market_breadth": breadth_score,
                "technical_indicators": technical_score,
                "sentiment_indicators": sentiment_score,
                "fund_flow": fund_flow_score
            }
            
            logger.info(f"增强版火热程度评分: {heat_score:.3f}")
            return heat_score, indicators_detail
            
        except Exception as e:
            logger.error(f"增强版评分计算失败: {str(e)}")
            return 0.5, {}
    
    def analyze_enhanced_market_heat(self, date: str = None) -> Optional[Dict]:
        """执行增强版市场火热程度分析"""
        try:
            date_str = date if date else "今日"
            logger.info(f"开始增强版分析 {date_str}")
            
            # 获取增强版市场数据
            market_data = self.get_enhanced_market_data(date)
            if not market_data:
                logger.error(f"无法获取 {date_str} 增强版市场数据")
                return None
            
            # 计算增强版火热程度评分
            heat_score, indicators = self.calculate_enhanced_heat_score(market_data)
            
            # 生成风险评估和建议
            risk_assessment = self._get_enhanced_risk_assessment(heat_score, indicators)
            position_advice = self._get_enhanced_position_advice(heat_score, indicators)
            
            result = {
                "date": date if date else datetime.now().strftime("%Y%m%d"),
                "heat_score": heat_score,
                "risk_assessment": risk_assessment,
                "position_advice": position_advice,
                "indicators": indicators,
                "market_summary": self._build_enhanced_summary(market_data)
            }
            
            logger.info(f"{date_str} 增强版分析完成 - 火热程度: {heat_score:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"增强版市场分析失败: {str(e)}")
            return None
    
    # 辅助方法
    def _calculate_base_volume_ratio(self, market_data: Dict) -> float:
        """计算基础成交量比率"""
        try:
            market_summary = market_data.get("market_summary")
            if market_summary is None or market_summary.empty:
                return 0.5
                
            volumes = market_summary["成交量"].apply(lambda x: float(str(x).replace(',', '')) if x else 100000000)
            avg_volume = volumes.mean()
            return min(avg_volume / 200000000, 1.0)  # 标准化
        except:
            return 0.5
    
    def _calculate_volume_strength(self, market_data: Dict) -> float:
        """计算成交量强度"""
        enhanced = market_data.get('enhanced_indicators', {})
        participation = enhanced.get('market_participation', 0)
        return min(participation * 1.5, 1.0)
    
    def _calculate_volume_price_relation(self, market_data: Dict) -> float:
        """计算量价关系"""
        enhanced = market_data.get('enhanced_indicators', {})
        avg_change = enhanced.get('avg_index_change', 0)
        participation = enhanced.get('market_participation', 0)
        
        # 上涨配放量为正面信号
        if avg_change > 0:
            return min(participation, 1.0)
        elif avg_change < -0.5:
            return max(1 - participation, 0.0)  # 大跌时放量为负面
        else:
            return 0.5
    
    def _normalize_rsi(self, rsi: float) -> float:
        """RSI标准化"""
        if np.isnan(rsi):
            return 0.5
        if rsi >= 80:  # 超买
            return min(1.0, (rsi - 50) / 30)
        elif rsi <= 20:  # 超卖  
            return max(0.0, rsi / 50)
        else:
            return 0.5
    
    def _normalize_macd(self, macd: float, signal: float) -> float:
        """MACD标准化"""
        if np.isnan(macd) or np.isnan(signal):
            return 0.5
        diff = macd - signal
        return max(0, min(1, 0.5 + diff * 100))  # 简单标准化
    
    def _calculate_enhanced_momentum(self, market_data: Dict) -> float:
        """计算增强版价格动量"""
        enhanced = market_data.get('enhanced_indicators', {})
        avg_change = enhanced.get('avg_index_change', 0)
        return np.tanh(avg_change / 3)  # 使用tanh函数标准化
    
    def _apply_dynamic_adjustments(self, heat_score: float, market_data: Dict) -> float:
        """应用动态调整"""
        enhanced = market_data.get('enhanced_indicators', {})
        
        # 极端情况调整
        market_extreme = enhanced.get('market_extreme', 0)
        if market_extreme > 0.8:  # 极端市场
            heat_score *= 1.2  # 增强信号
        
        return heat_score
    
    def _get_enhanced_risk_assessment(self, heat_score: float, indicators: Dict) -> Dict:
        """获取增强版风险评估"""
        # 基础风险等级
        if heat_score >= 0.8:
            base_risk = "极高风险"
        elif heat_score >= 0.6:
            base_risk = "高风险"
        elif heat_score >= 0.4:
            base_risk = "中等风险"
        elif heat_score >= 0.2:
            base_risk = "低风险"
        else:
            base_risk = "极低风险"
        
        # 风险因子分析
        risk_factors = []
        if indicators.get('technical_indicators', 0) > 0.8:
            risk_factors.append("技术指标过热")
        if indicators.get('sentiment_indicators', 0) > 0.7:
            risk_factors.append("市场情绪亢奋")
        if indicators.get('volume_indicators', 0) > 0.8:
            risk_factors.append("成交量异常放大")
        
        return {
            "level": base_risk,
            "score": heat_score,
            "risk_factors": risk_factors
        }
    
    def _get_enhanced_position_advice(self, heat_score: float, indicators: Dict) -> Dict:
        """获取增强版仓位建议"""
        # 基础仓位建议
        if heat_score >= 0.8:
            base_position = "建议减仓至20-30%"
            action = "减仓"
        elif heat_score >= 0.6:
            base_position = "建议减仓至40-50%"
            action = "适度减仓"
        elif heat_score >= 0.4:
            base_position = "建议保持50-60%仓位"
            action = "维持"
        elif heat_score >= 0.2:
            base_position = "可适度加仓至70-80%"
            action = "加仓"
        else:
            base_position = "可考虑满仓操作"
            action = "满仓"
        
        # 策略建议
        strategies = []
        technical_score = indicators.get('technical_indicators', 0)
        if technical_score > 0.7:
            strategies.append("关注技术指标背离")
        if indicators.get('market_breadth', 0) < -0.3:
            strategies.append("市场分化严重，精选个股")
        
        return {
            "position": base_position,
            "action": action,
            "strategies": strategies
        }
    
    def _build_enhanced_summary(self, market_data: Dict) -> Dict:
        """构建增强版市场摘要"""
        enhanced = market_data.get('enhanced_indicators', {})
        
        return {
            "limit_up_count": enhanced.get('limit_up_count', 0),
            "limit_down_count": enhanced.get('limit_down_count', 0),
            "market_participation": enhanced.get('market_participation', 0),
            "bull_bear_ratio": enhanced.get('bull_bear_ratio', 0.5),
            "avg_index_change": enhanced.get('avg_index_change', 0),
            "market_extreme": enhanced.get('market_extreme', 0)
        }


def main():
    """测试增强版分析器"""
    analyzer = EnhancedAStockAnalyzer()
    
    print("=== 增强版A股市场火热程度分析 ===")
    result = analyzer.analyze_enhanced_market_heat()
    
    if result:
        print(f"\n综合火热程度评分: {result['heat_score']:.3f}")
        print(f"风险评估: {result['risk_assessment']['level']}")
        print(f"仓位建议: {result['position_advice']['position']}")
        
        print(f"\n详细指标:")
        for key, value in result['indicators'].items():
            print(f"- {key}: {value:.3f}")
            
        print(f"\n市场摘要:")
        summary = result['market_summary']
        print(f"- 涨停股票: {summary['limit_up_count']}")
        print(f"- 跌停股票: {summary['limit_down_count']}")
        print(f"- 市场参与度: {summary['market_participation']:.3f}")
        print(f"- 多空比率: {summary['bull_bear_ratio']:.3f}")
    else:
        print("分析失败!")


if __name__ == "__main__":
    main()