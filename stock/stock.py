#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股市场火热程度量化模型
基于多维度指标综合判断市场情绪和风险水平
"""

import akshare as ak
import pandas as pd
import numpy as np
import logging
import warnings
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import time

warnings.filterwarnings("ignore")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("market_heat.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AStockHeatAnalyzer:
    """A股市场火热程度分析器"""

    def __init__(self):
        self.indicators = {}
        self.weights = {
            "volume_ratio": 0.25,  # 成交量比率权重
            "price_momentum": 0.20,  # 价格动量权重
            "market_breadth": 0.20,  # 市场广度权重
            "volatility": 0.15,  # 波动率权重
            "sentiment": 0.20,  # 情绪指标权重
        }
        logger.info("A股市场火热程度分析器初始化完成")

    def get_market_data(self) -> Optional[Dict]:
        """获取市场基础数据"""
        try:
            logger.info("开始获取市场数据...")

            # 获取上证指数实时数据
            sz_index = ak.stock_zh_index_spot_em(symbol="000001")

            # 获取深证成指实时数据
            sz_component = ak.stock_zh_index_spot_em(symbol="399001")

            # 获取创业板指数据
            cyb_index = ak.stock_zh_index_spot_em(symbol="399006")

            # 获取市场概况
            market_summary = ak.stock_zh_a_spot_em()

            # 获取涨跌停数据
            limit_up = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
            limit_down = ak.stock_dt_pool_em(date=datetime.now().strftime("%Y%m%d"))

            data = {
                "sz_index": sz_index,
                "sz_component": sz_component,
                "cyb_index": cyb_index,
                "market_summary": market_summary,
                "limit_up": limit_up,
                "limit_down": limit_down,
                "timestamp": datetime.now(),
            }

            logger.info(f"市场数据获取成功，时间戳: {data['timestamp']}")
            return data

        except Exception as e:
            logger.error(f"获取市场数据失败: {str(e)}")
            return None

    def calculate_volume_ratio(self, market_data: Dict) -> float:
        """计算成交量比率指标"""
        try:
            market_summary = market_data["market_summary"]

            # 计算当日总成交量与均值的比率
            total_volume = market_summary["成交量"].sum()
            avg_volume = market_summary["成交量"].mean()

            volume_ratio = (
                total_volume / (avg_volume * len(market_summary))
                if avg_volume > 0
                else 1.0
            )

            logger.info(f"成交量比率计算完成: {volume_ratio:.2f}")
            return min(volume_ratio, 3.0)  # 限制最大值避免异常

        except Exception as e:
            logger.warn(f"成交量比率计算失败: {str(e)}")
            return 1.0

    def calculate_price_momentum(self, market_data: Dict) -> float:
        """计算价格动量指标"""
        try:
            sz_data = market_data["sz_index"]
            sz_component_data = market_data["sz_component"]
            cyb_data = market_data["cyb_index"]

            # 提取涨跌幅
            sz_change = float(str(sz_data.iloc[0]["涨跌幅"]).replace("%", ""))
            szc_change = float(str(sz_component_data.iloc[0]["涨跌幅"]).replace("%", ""))
            cyb_change = float(str(cyb_data.iloc[0]["涨跌幅"]).replace("%", ""))

            # 加权平均动量
            momentum = (sz_change * 0.4 + szc_change * 0.3 + cyb_change * 0.3) / 100

            logger.info(f"价格动量计算完成: {momentum:.4f}")
            return momentum

        except Exception as e:
            logger.warn(f"价格动量计算失败: {str(e)}")
            return 0.0

    def calculate_market_breadth(self, market_data: Dict) -> float:
        """计算市场广度指标"""
        try:
            market_summary = market_data["market_summary"]
            limit_up = market_data["limit_up"]
            limit_down = market_data["limit_down"]

            # 计算涨跌个股比例
            up_stocks = len(market_summary[market_summary["涨跌幅"] > 0])
            down_stocks = len(market_summary[market_summary["涨跌幅"] < 0])
            total_stocks = len(market_summary)

            # 涨跌停个股数量
            limit_up_count = len(limit_up) if not limit_up.empty else 0
            limit_down_count = len(limit_down) if not limit_down.empty else 0

            # 综合广度指标
            breadth_ratio = (
                (up_stocks - down_stocks) / total_stocks if total_stocks > 0 else 0
            )
            limit_ratio = (limit_up_count - limit_down_count) / 100  # 归一化处理

            breadth = breadth_ratio + limit_ratio * 0.3

            logger.info(
                f"市场广度计算完成: {breadth:.4f} (涨{up_stocks}/跌{down_stocks}/涨停{limit_up_count}/跌停{limit_down_count})"
            )
            return breadth

        except Exception as e:
            logger.warn(f"市场广度计算失败: {str(e)}")
            return 0.0

    def calculate_volatility(self, market_data: Dict) -> float:
        """计算波动率指标"""
        try:
            market_summary = market_data["market_summary"]

            # 计算市场平均波动率
            changes = (
                market_summary["涨跌幅"].astype(str).str.replace("%", "").astype(float)
            )
            volatility = changes.std() / 100

            logger.info(f"市场波动率计算完成: {volatility:.4f}")
            return volatility

        except Exception as e:
            logger.warn(f"波动率计算失败: {str(e)}")
            return 0.02  # 默认2%波动率

    def calculate_sentiment_indicator(self, market_data: Dict) -> float:
        """计算情绪指标"""
        try:
            limit_up = market_data["limit_up"]
            limit_down = market_data["limit_down"]
            market_summary = market_data["market_summary"]

            limit_up_count = len(limit_up) if not limit_up.empty else 0
            limit_down_count = len(limit_down) if not limit_down.empty else 0

            # 大涨大跌股票比例
            big_up = len(
                market_summary[
                    market_summary["涨跌幅"].astype(str).str.replace("%", "").astype(float)
                    > 5
                ]
            )
            big_down = len(
                market_summary[
                    market_summary["涨跌幅"].astype(str).str.replace("%", "").astype(float)
                    < -5
                ]
            )

            # 情绪指标综合计算
            sentiment = (limit_up_count - limit_down_count + big_up - big_down) / 100

            logger.info(f"情绪指标计算完成: {sentiment:.4f}")
            return sentiment

        except Exception as e:
            logger.warn(f"情绪指标计算失败: {str(e)}")
            return 0.0

    def calculate_heat_score(self, market_data: Dict) -> Tuple[float, Dict]:
        """计算综合火热程度评分"""
        try:
            # 计算各项指标
            volume_ratio = self.calculate_volume_ratio(market_data)
            price_momentum = self.calculate_price_momentum(market_data)
            market_breadth = self.calculate_market_breadth(market_data)
            volatility = self.calculate_volatility(market_data)
            sentiment = self.calculate_sentiment_indicator(market_data)

            # 指标标准化处理
            normalized_volume = min(volume_ratio / 2.0, 1.0)  # 2倍成交量为满分
            normalized_momentum = np.tanh(price_momentum * 10)  # tanh函数平滑处理
            normalized_breadth = np.tanh(market_breadth * 3)
            normalized_volatility = min(volatility / 0.05, 1.0)  # 5%波动率为满分
            normalized_sentiment = np.tanh(sentiment * 2)

            # 计算加权综合得分
            heat_score = (
                normalized_volume * self.weights["volume_ratio"]
                + normalized_momentum * self.weights["price_momentum"]
                + normalized_breadth * self.weights["market_breadth"]
                + normalized_volatility * self.weights["volatility"]
                + normalized_sentiment * self.weights["sentiment"]
            )

            # 详细指标字典
            indicators_detail = {
                "volume_ratio": volume_ratio,
                "price_momentum": price_momentum,
                "market_breadth": market_breadth,
                "volatility": volatility,
                "sentiment": sentiment,
                "normalized_scores": {
                    "volume": normalized_volume,
                    "momentum": normalized_momentum,
                    "breadth": normalized_breadth,
                    "volatility": normalized_volatility,
                    "sentiment": normalized_sentiment,
                },
            }

            logger.info(f"综合火热程度评分计算完成: {heat_score:.3f}")
            return heat_score, indicators_detail

        except Exception as e:
            logger.error(f"火热程度评分计算失败: {str(e)}")
            return 0.5, {}

    def get_risk_level(self, heat_score: float) -> str:
        """根据火热程度评分判断风险等级"""
        if heat_score >= 0.8:
            return "极高风险"
        elif heat_score >= 0.6:
            return "高风险"
        elif heat_score >= 0.4:
            return "中等风险"
        elif heat_score >= 0.2:
            return "低风险"
        else:
            return "极低风险"

    def get_position_suggestion(self, heat_score: float) -> str:
        """根据火热程度给出仓位建议"""
        if heat_score >= 0.8:
            return "建议减仓至3-4成，保持高度警惕"
        elif heat_score >= 0.6:
            return "建议减仓至5-6成，控制风险"
        elif heat_score >= 0.4:
            return "建议保持6-7成仓位，适度参与"
        elif heat_score >= 0.2:
            return "可适度加仓至7-8成"
        else:
            return "可考虑满仓操作，但需关注基本面"

    def analyze_market_heat(self) -> Optional[Dict]:
        """执行完整的市场火热程度分析"""
        try:
            logger.info("=" * 50)
            logger.info("开始执行A股市场火热程度分析")

            # 获取市场数据
            market_data = self.get_market_data()
            if not market_data:
                logger.error("无法获取市场数据，分析终止")
                return None

            # 计算火热程度评分
            heat_score, indicators = self.calculate_heat_score(market_data)

            # 生成分析结果
            risk_level = self.get_risk_level(heat_score)
            position_suggestion = self.get_position_suggestion(heat_score)

            result = {
                "timestamp": market_data["timestamp"],
                "heat_score": heat_score,
                "risk_level": risk_level,
                "position_suggestion": position_suggestion,
                "indicators": indicators,
                "market_data_summary": {
                    "sz_index_change": market_data["sz_index"].iloc[0]["涨跌幅"],
                    "limit_up_count": len(market_data["limit_up"])
                    if not market_data["limit_up"].empty
                    else 0,
                    "limit_down_count": len(market_data["limit_down"])
                    if not market_data["limit_down"].empty
                    else 0,
                },
            }

            logger.info(f"分析完成 - 火热程度: {heat_score:.3f}, 风险等级: {risk_level}")
            logger.info(f"仓位建议: {position_suggestion}")
            logger.info("=" * 50)

            return result

        except Exception as e:
            logger.error(f"市场火热程度分析失败: {str(e)}")
            return None


def main():
    """主函数 - 执行市场分析"""
    analyzer = AStockHeatAnalyzer()

    # 执行分析
    result = analyzer.analyze_market_heat()

    if result:
        print(f"\n{'=' * 60}")
        print(f"A股市场火热程度分析报告")
        print(f"分析时间: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 60}")
        print(f"综合火热程度评分: {result['heat_score']:.3f}")
        print(f"风险等级: {result['risk_level']}")
        print(f"仓位建议: {result['position_suggestion']}")
        print(f"\n指标详情:")
        print(f"- 成交量比率: {result['indicators']['volume_ratio']:.2f}")
        print(f"- 价格动量: {result['indicators']['price_momentum']:.4f}")
        print(f"- 市场广度: {result['indicators']['market_breadth']:.4f}")
        print(f"- 波动率: {result['indicators']['volatility']:.4f}")
        print(f"- 情绪指标: {result['indicators']['sentiment']:.4f}")
        print(f"\n市场概况:")
        print(f"- 上证指数涨跌幅: {result['market_data_summary']['sz_index_change']}")
        print(f"- 涨停股票数: {result['market_data_summary']['limit_up_count']}")
        print(f"- 跌停股票数: {result['market_data_summary']['limit_down_count']}")
        print(f"{'=' * 60}")
    else:
        print("分析失败，请检查网络连接和数据源")


if __name__ == "__main__":
    main()
