# -*- coding: utf-8 -*-
"""
聚宽平台 - A股市场火热程度量化模型（数据获取优化版）
基于聚宽平台API实现市场情绪和风险水平的综合评估
"""

import jqdata
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import talib
import math


def initialize(context):
    """初始化函数"""
    # 设置基准
    g.benchmark = "000001.XSHG"  # 上证综指

    # 设置股票池
    g.index_stocks = {
        "sz_index": "000001.XSHG",  # 上证综指
        "sz_component": "000300.XSHG",  # 沪深300
        "cyb_index": "399006.XSHE",  # 创业板指
        "sz50": "000016.XSHG",  # 上证50
    }

    # 模型参数
    g.weights = {
        "volume_ratio": 0.25,  # 成交量比率权重
        "price_momentum": 0.20,  # 价格动量权重
        "market_breadth": 0.20,  # 市场广度权重
        "volatility": 0.15,  # 波动率权重
        "sentiment": 0.20,  # 情绪指标权重
    }

    # 历史数据窗口
    g.lookback_days = 20
    g.heat_threshold = 0.6  # 高风险阈值

    # 初始化历史数据存储 - 改为持久化存储
    g.heat_history = []
    g.last_analysis_date = None

    # 只在收盘前统计一次
    run_daily(analyze_market_heat, time="14:50")  # 收盘前10分钟
    run_daily(before_market_open, time="08:30")  # 盘前准备

    log.info("A股市场火热程度分析模型初始化完成")


def analyze_market_heat(context):
    """主分析函数 - 计算市场火热程度"""
    try:
        current_time = context.current_dt
        current_date = current_time.date()

        # 避免重复分析同一天
        if g.last_analysis_date == current_date:
            log.info(f"今日已完成分析，跳过重复执行")
            return

        log.info(f"开始执行市场火热程度分析-时间: {current_time}")

        # 获取市场数据
        market_data = get_market_data(context, current_time)
        if not market_data:
            log.warn("无法获取市场数据，跳过本次分析")
            return

        # 计算各项指标
        indicators = calculate_all_indicators(context, market_data)

        # 计算综合火热程度评分
        heat_score = calculate_heat_score(context, indicators)

        # 风险评估和建议
        risk_assessment = assess_risk_level(heat_score, indicators)

        # 输出分析结果
        output_analysis_result(context, heat_score, indicators, risk_assessment)

        # 存储历史数据用于趋势分析
        store_heat_history(context, heat_score, indicators)

        # 趋势分析
        trend_analysis = get_heat_trend_analysis(context)
        log.info(f"趋势分析: {trend_analysis}")

        # 输出交易建议
        output_trading_advice(heat_score)

        # 标记今日已分析
        g.last_analysis_date = current_date

    except Exception as e:
        log.error(f"市场火热程度分析失败: {str(e)}")


def get_market_data(context, current_time):
    """获取市场基础数据 - 优化版"""
    try:
        end_date = current_time.date()
        start_date = end_date - timedelta(days=g.lookback_days)

        market_data = {}

        # 获取主要指数数据
        for name, code in g.index_stocks.items():
            try:
                price_data = get_price(
                    code,
                    start_date=start_date,
                    end_date=end_date,
                    frequency="daily",
                    fields=["open", "high", "low", "close", "volume", "money"],
                )
                if not price_data.empty:
                    market_data[name] = price_data
                    log.info(f"获取{name}数据成功，数据量: {len(price_data)}")
            except Exception as e:
                log.warn(f"获取{name}({code})数据失败: {str(e)}")

        # 获取涨跌停数据（优化版）
        limit_data = get_limit_stocks_enhanced(context, end_date)
        market_data["limit_stocks"] = limit_data

        # 获取北向资金数据（优化版）
        try:
            northbound_flow = get_northbound_money_flow_enhanced(end_date)
            market_data["northbound"] = northbound_flow
        except Exception as e:
            log.warn(f"获取北向资金数据失败: {str(e)}")
            market_data["northbound"] = 0

        log.info("市场数据获取完成")
        return market_data

    except Exception as e:
        log.error(f"获取市场数据失败: {str(e)}")
        return None


def get_northbound_money_flow_enhanced(date):
    """获取北向资金数据 - 增强版"""
    try:
        # 方式1：使用正确的jqdata.finance模块查询
        try:
            from jqdata import finance, query

            q = query(
                finance.STK_ML_QUOTA.link_id,
                finance.STK_ML_QUOTA.day,
                finance.STK_ML_QUOTA.quota_daily,
                finance.STK_ML_QUOTA.quota_daily_balance,
            ).filter(
                finance.STK_ML_QUOTA.day == date,
                finance.STK_ML_QUOTA.link_id.in_(["310001", "310002"]),
            )

            df = finance.run_query(q)
            if not df.empty:
                # 净流入 = 当日额度 - 当日余额
                net_inflow = (df["quota_daily"] - df["quota_daily_balance"]).sum()
                log.info(f"北向资金净流入: {net_inflow / 100000000:.2f}亿元")
                return net_inflow

        except Exception as e1:
            log.info(f"方式1获取北向资金失败: {str(e1)}")

        # 方式2：使用get_money_flow获取主要北向标的资金流
        try:
            # 北向资金重仓股代表
            northbound_representatives = [
                "000858.XSHE",  # 五粮液
                "000002.XSHE",  # 万科A
                "600036.XSHG",  # 招商银行
                "000001.XSHE",  # 平安银行
                "600519.XSHG",  # 贵州茅台
            ]

            total_flow = 0
            valid_stocks = 0

            for stock in northbound_representatives:
                try:
                    flow_data = get_money_flow([stock], start_date=date, end_date=date)
                    if not flow_data.empty and "net_amount_main" in flow_data.columns:
                        stock_flow = flow_data["net_amount_main"].iloc[0]
                        if not pd.isna(stock_flow):
                            total_flow += stock_flow
                            valid_stocks += 1
                except:
                    continue

            if valid_stocks > 0:
                # 按比例估算全市场北向资金流向
                estimated_northbound = total_flow * 10  # 经验系数
                log.info(f"北向资金估算值: {estimated_northbound / 100000000:.2f}亿元")
                return estimated_northbound

        except Exception as e2:
            log.info(f"方式2获取北向资金失败: {str(e2)}")

        # 方式3：基于ETF资金流向估算
        try:
            etf_codes = ["510300.XSHG", "159915.XSHE", "510500.XSHG"]  # 主要宽基ETF
            etf_flow = 0
            valid_etf = 0

            for etf in etf_codes:
                try:
                    flow_data = get_money_flow([etf], start_date=date, end_date=date)
                    if not flow_data.empty and "net_amount_main" in flow_data.columns:
                        etf_net = flow_data["net_amount_main"].iloc[0]
                        if not pd.isna(etf_net):
                            etf_flow += etf_net
                            valid_etf += 1
                except:
                    continue

            if valid_etf > 0:
                # ETF流向作为北向资金的代理指标
                northbound_estimate = etf_flow * 3  # ETF与北向资金相关系数
                log.info(f"北向资金ETF估算: {northbound_estimate / 100000000:.2f}亿元")
                return northbound_estimate

        except Exception as e3:
            log.info(f"方式3获取北向资金失败: {str(e3)}")

        # 所有方式失败，使用默认值
        log.warn("北向资金数据获取失败，使用默认值0")
        return 0

    except Exception as e:
        log.error(f"北向资金数据获取完全失败: {str(e)}")
        return 0


def get_limit_stocks_enhanced(context, date):
    """增强版涨跌停股票统计"""
    try:
        log.info(f"开始分析涨跌停数据-日期: {date}")

        # 获取多样化样本股票
        sample_stocks = []
        sample_info = {}

        # 配置多个指数作为样本来源
        index_configs = [
            ("000300.XSHG", 150, "沪深300"),
            ("399006.XSHE", 80, "创业板指"),
            ("000016.XSHG", 30, "上证50"),
            ("399905.XSHE", 50, "中证500"),
            ("000905.XSHG", 40, "中证800"),
        ]

        # 收集样本股票
        for index_code, limit, name in index_configs:
            try:
                index_stocks = get_index_stocks(index_code, date=date)
                selected_stocks = list(index_stocks)[:limit]
                sample_stocks.extend(selected_stocks)
                sample_info[name] = len(selected_stocks)
                log.info(f"获取{name}成分股: {len(selected_stocks)}只")
            except Exception as e:
                log.warn(f"获取{name}成分股失败: {str(e)}")

        # 去重
        sample_stocks = list(set(sample_stocks))[:400]  # 限制总样本数量
        log.info(f"样本股票总数: {len(sample_stocks)}")

        if not sample_stocks:
            log.warn("无法获取样本股票，使用指数估算")
            return estimate_market_from_index_enhanced(context, date)

        # 分析样本股票涨跌停情况
        result = analyze_sample_stocks(sample_stocks, date)

        # 验证数据合理性
        if is_data_reasonable(result):
            return result
        else:
            log.warn("样本数据异常，使用指数估算方案")
            return estimate_market_from_index_enhanced(context, date)

    except Exception as e:
        log.error(f"增强版涨跌停分析失败: {str(e)}")
        return estimate_market_from_index_enhanced(context, date)


def analyze_sample_stocks(sample_stocks, date):
    """分析样本股票的涨跌停情况 - 修复版"""
    try:
        limit_up_count = 0
        limit_down_count = 0
        total_up = 0
        total_down = 0
        valid_count = 0

        # 分批处理避免API限制
        batch_size = 50  # 降低批次大小

        for i in range(0, len(sample_stocks), batch_size):
            batch_stocks = sample_stocks[i : i + batch_size]

            try:
                # 获取当日价格数据 - 修复数据格式
                current_data = get_price(
                    batch_stocks,
                    start_date=date,
                    end_date=date,
                    frequency="daily",
                    fields=["close", "high_limit", "low_limit"],
                    panel=False,
                )

                # 获取前一交易日数据
                prev_date = None
                prev_data = pd.DataFrame()
                for days_back in [1, 2, 3]:
                    try:
                        prev_date = date - timedelta(days=days_back)
                        prev_data = get_price(
                            batch_stocks,
                            start_date=prev_date,
                            end_date=prev_date,
                            frequency="daily",
                            fields=["close"],
                            panel=False,
                        )
                        if not prev_data.empty:
                            break
                    except:
                        continue

                if current_data.empty:
                    log.warn(f"批次 {i}-{i + batch_size} 当日数据为空")
                    continue

                log.info(
                    f"批次 {i}-{i + batch_size}: 当日数据{len(current_data)}条, 前日数据{len(prev_data)}条"
                )

                # 按股票代码处理数据 - 基于实际数据结构
                for _, row in current_data.iterrows():
                    try:
                        stock_code = row["code"]
                        close_price = row["close"]
                        high_limit = row.get("high_limit", np.nan)
                        low_limit = row.get("low_limit", np.nan)

                        if pd.isna(close_price) or close_price <= 0:
                            continue

                        valid_count += 1

                        # 涨跌停判断
                        is_limit_up = False
                        is_limit_down = False

                        if not pd.isna(high_limit) and high_limit > 0:
                            if abs(close_price - high_limit) / high_limit <= 0.003:
                                limit_up_count += 1
                                total_up += 1
                                is_limit_up = True
                                continue  # 涨停股票不再判断普通涨跌

                        if not pd.isna(low_limit) and low_limit > 0:
                            if abs(close_price - low_limit) / low_limit <= 0.003:
                                limit_down_count += 1
                                total_down += 1
                                is_limit_down = True
                                continue  # 跌停股票不再判断普通涨跌

                        # 计算普通涨跌
                        if not prev_data.empty:
                            prev_row = prev_data[prev_data["code"] == stock_code]
                            if not prev_row.empty:
                                yesterday_close = prev_row["close"].iloc[0]
                                if not pd.isna(yesterday_close) and yesterday_close > 0:
                                    change_pct = (
                                        close_price - yesterday_close
                                    ) / yesterday_close
                                    if change_pct > 0.005:  # 上涨超过0.5%
                                        total_up += 1
                                    elif change_pct < -0.005:  # 下跌超过0.5%
                                        total_down += 1

                    except Exception as stock_error:
                        log.warn(
                            f"处理股票 {stock_code if 'stock_code' in locals() else '未知'} 失败: {str(stock_error)}"
                        )
                        continue

            except Exception as batch_error:
                log.warn(f"处理批次 {i}-{i + batch_size} 失败: {str(batch_error)}")
                continue

        # 数据有效性检查
        if valid_count == 0:
            log.warn("没有有效的样本数据")
            return get_empty_limit_result(5000)

        # 获取全市场股票总数
        try:
            all_stocks = get_all_securities(["stock"], date=date)
            total_market_stocks = len(all_stocks)
        except:
            total_market_stocks = 5000  # 默认值

        # 按样本比例扩放到全市场
        scale_factor = total_market_stocks / len(sample_stocks)

        result = {
            "limit_up_count": max(0, int(limit_up_count * scale_factor)),
            "limit_down_count": max(0, int(limit_down_count * scale_factor)),
            "total_up": max(0, int(total_up * scale_factor)),
            "total_down": max(0, int(total_down * scale_factor)),
            "total_stocks": total_market_stocks,
            "sample_stocks": valid_count,
            "scale_factor": scale_factor,
        }

        log.info(f"样本分析完成-有效样本:{valid_count}, 扩放系数:{scale_factor:.2f}")
        log.info(
            f"估算全市场 涨停:{result['limit_up_count']}, 跌停:{result['limit_down_count']}, 上涨:{result['total_up']}, 下跌:{result['total_down']}"
        )

        return result

    except Exception as e:
        log.error(f"分析样本股票失败: {str(e)}")
        return get_empty_limit_result(5000)


def is_data_reasonable(result):
    """验证数据合理性"""
    try:
        total_up = result.get("total_up", 0)
        total_down = result.get("total_down", 0)
        limit_up = result.get("limit_up_count", 0)
        limit_down = result.get("limit_down_count", 0)
        total_stocks = result.get("total_stocks", 5000)

        # 基本合理性检查
        if total_up < 0 or total_down < 0 or limit_up < 0 or limit_down < 0:
            log.warn("数据异常：存在负数")
            return False

        # 涨跌停数量不能超过总涨跌数量
        if limit_up > total_up or limit_down > total_down:
            log.warn("数据异常：涨跌停数量超过总涨跌数量")
            return False

        # 极端情况检查：所有股票都涨停/跌停的情况很异常
        if limit_up > total_stocks * 0.5 or limit_down > total_stocks * 0.5:
            log.warn("数据异常：涨跌停比例过高")
            return False

        # 总涨跌数量不合理
        if (total_up + total_down) == 0:
            log.warn("数据异常：没有涨跌股票")
            return False

        if (total_up + total_down) > total_stocks * 1.2:  # 允许20%误差
            log.warn("数据异常：涨跌股票总数超过市场总数")
            return False

        return True

    except Exception as e:
        log.warn(f"数据合理性检查失败: {str(e)}")
        return False


def estimate_market_from_index_enhanced(context, date):
    """增强版基于指数数据估算市场涨跌停情况"""
    try:
        log.info("使用增强版指数数据估算市场情况")

        # 获取多个指数的当日涨跌幅
        indices_data = {}
        index_codes = {
            "000001.XSHG": "上证指数",
            "000300.XSHG": "沪深300",
            "399006.XSHE": "创业板指",
            "000016.XSHG": "上证50",
            "399905.XSHE": "中证500",
        }

        valid_changes = []

        for index_code, index_name in index_codes.items():
            try:
                index_data = get_price(
                    index_code,
                    start_date=date - timedelta(days=3),  # 多取几天数据
                    end_date=date,
                    frequency="daily",
                    fields=["close", "volume"],
                )

                if len(index_data) >= 2:
                    today_close = index_data["close"].iloc[-1]
                    yesterday_close = index_data["close"].iloc[-2]
                    change_pct = (today_close - yesterday_close) / yesterday_close

                    # 获取成交量变化
                    today_volume = index_data["volume"].iloc[-1]
                    avg_volume = index_data["volume"].iloc[:-1].mean()
                    volume_ratio = today_volume / avg_volume if avg_volume > 0 else 1.0

                    valid_changes.append(
                        {
                            "change_pct": change_pct,
                            "volume_ratio": volume_ratio,
                            "index_name": index_name,
                        }
                    )

                    log.info(
                        f"{index_name}涨跌幅: {change_pct:.4f}, 量比: {volume_ratio:.2f}"
                    )

            except Exception as e:
                log.warn(f"获取{index_name}数据失败: {str(e)}")
                continue

        if not valid_changes:
            log.warn("无法获取任何指数数据，使用默认值")
            return get_empty_limit_result(5000)

        # 计算加权平均变化（考虑成交量）
        total_weight = sum([data["volume_ratio"] for data in valid_changes])
        if total_weight > 0:
            weighted_change = (
                sum(
                    [
                        data["change_pct"] * data["volume_ratio"]
                        for data in valid_changes
                    ]
                )
                / total_weight
            )
        else:
            weighted_change = sum([data["change_pct"] for data in valid_changes]) / len(
                valid_changes
            )

        avg_volume_ratio = sum([data["volume_ratio"] for data in valid_changes]) / len(
            valid_changes
        )

        log.info(f"市场加权平均涨跌幅: {weighted_change:.4f}, 平均量比: {avg_volume_ratio:.2f}")

        # 基于指数涨跌幅和成交量估算市场情况
        total_stocks = 5000

        # 情绪因子：结合涨跌幅和成交量
        emotion_factor = weighted_change * (1 + (avg_volume_ratio - 1) * 0.5)

        if emotion_factor > 0.04:  # 强势市场
            up_ratio = 0.75
            limit_up_ratio = 0.025
            limit_down_ratio = 0.003
        elif emotion_factor > 0.02:  # 偏强市场
            up_ratio = 0.65
            limit_up_ratio = 0.015
            limit_down_ratio = 0.005
        elif emotion_factor > 0:  # 偏弱市场
            up_ratio = 0.45
            limit_up_ratio = 0.008
            limit_down_ratio = 0.008
        elif emotion_factor > -0.02:  # 弱势市场
            up_ratio = 0.35
            limit_up_ratio = 0.005
            limit_down_ratio = 0.015
        else:  # 大跌市场
            up_ratio = 0.20
            limit_up_ratio = 0.003
            limit_down_ratio = 0.025

        down_ratio = 1 - up_ratio

        estimated_up = int(total_stocks * up_ratio)
        estimated_down = int(total_stocks * down_ratio)
        estimated_limit_up = int(total_stocks * limit_up_ratio)
        estimated_limit_down = int(total_stocks * limit_down_ratio)

        # 确保涨跌停数量不超过总数
        estimated_limit_up = min(estimated_limit_up, estimated_up)
        estimated_limit_down = min(estimated_limit_down, estimated_down)

        result = {
            "limit_up_count": estimated_limit_up,
            "limit_down_count": estimated_limit_down,
            "total_up": estimated_up,
            "total_down": estimated_down,
            "total_stocks": total_stocks,
            "estimation_method": "enhanced_index_based",
            "emotion_factor": emotion_factor,
        }

        log.info(
            f"增强估算完成-情绪因子:{emotion_factor:.4f}, 涨停:{estimated_limit_up}, 跌停:{estimated_limit_down}"
        )
        return result

    except Exception as e:
        log.error(f"增强版指数估算失败: {str(e)}")
        return get_empty_limit_result(5000)


def get_empty_limit_result(total_stocks):
    """返回空的涨跌停结果"""
    return {
        "limit_up_count": 0,
        "limit_down_count": 0,
        "total_up": 0,
        "total_down": 0,
        "total_stocks": total_stocks,
    }


def calculate_all_indicators(context, market_data):
    """计算所有技术指标"""
    indicators = {}

    try:
        # 1. 成交量比率指标
        indicators["volume_ratio"] = calculate_volume_ratio(market_data)

        # 2. 价格动量指标
        indicators["price_momentum"] = calculate_price_momentum(market_data)

        # 3. 市场广度指标
        indicators["market_breadth"] = calculate_market_breadth(market_data)

        # 4. 波动率指标
        indicators["volatility"] = calculate_volatility(market_data)

        # 5. 情绪指标
        indicators["sentiment"] = calculate_sentiment_indicator(market_data)

        log.info("所有指标计算完成")
        return indicators

    except Exception as e:
        log.error(f"指标计算失败: {str(e)}")
        return {}


def calculate_volume_ratio(market_data):
    """计算成交量比率"""
    try:
        sz_data = market_data.get("sz_index")
        if sz_data is None or len(sz_data) < 2:
            return 1.0

        # 计算最近成交量与历史均值的比率
        recent_volume = sz_data["money"].iloc[-1]
        avg_volume = sz_data["money"].iloc[:-1].mean()

        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0

        # 限制异常值
        volume_ratio = min(max(volume_ratio, 0.1), 5.0)

        log.info(f"成交量比率: {volume_ratio:.2f}")
        return volume_ratio

    except Exception as e:
        log.warn(f"成交量比率计算失败: {str(e)}")
        return 1.0


def calculate_price_momentum(market_data):
    """计算价格动量"""
    try:
        momentum_sum = 0
        weight_sum = 0
        weights = {"sz_index": 0.4, "sz_component": 0.3, "cyb_index": 0.3}

        for name, weight in weights.items():
            data = market_data.get(name)
            if data is not None and len(data) >= 2:
                # 计算当日涨跌幅
                today_close = data["close"].iloc[-1]
                yesterday_close = data["close"].iloc[-2]
                change_pct = (today_close - yesterday_close) / yesterday_close

                momentum_sum += change_pct * weight
                weight_sum += weight

        momentum = momentum_sum / weight_sum if weight_sum > 0 else 0.0

        log.info(f"价格动量: {momentum:.4f}")
        return momentum

    except Exception as e:
        log.warn(f"价格动量计算失败: {str(e)}")
        return 0.0


def calculate_market_breadth(market_data):
    """计算市场广度 - 优化版"""
    try:
        limit_data = market_data.get("limit_stocks", {})

        total_up = limit_data.get("total_up", 0)
        total_down = limit_data.get("total_down", 0)
        total_stocks = limit_data.get("total_stocks", 1)
        limit_up = limit_data.get("limit_up_count", 0)
        limit_down = limit_data.get("limit_down_count", 0)

        # 数据有效性检查
        if total_stocks <= 0:
            total_stocks = 5000

        # 基础广度指标 - 优化计算逻辑
        if (total_up + total_down) == 0:
            # 如果没有涨跌数据，基于涨跌停推算
            if limit_up > 0 or limit_down > 0:
                breadth_ratio = (limit_up - limit_down) / max(total_stocks * 0.01, 1)
            else:
                breadth_ratio = 0
        else:
            breadth_ratio = (total_up - total_down) / total_stocks

        # 极端情绪调整 - 涨跌停的额外权重
        limit_impact = 0
        if limit_up > 0 or limit_down > 0:
            limit_ratio = (limit_up - limit_down) / max(total_stocks * 0.01, 1)
            limit_impact = limit_ratio * 0.2  # 降低权重避免过度影响

        breadth = breadth_ratio + limit_impact

        # 限制异常值
        breadth = max(-2.0, min(breadth, 2.0))

        log.info(
            f"市场广度: {breadth:.4f} (涨{total_up}/跌{total_down}/涨停{limit_up}/跌停{limit_down})"
        )
        return breadth

    except Exception as e:
        log.warn(f"市场广度计算失败: {str(e)}")
        return 0.0


def calculate_volatility(market_data):
    """计算波动率"""
    try:
        sz_data = market_data.get("sz_index")
        if sz_data is None or len(sz_data) < 5:
            return 0.02

        # 计算近期收益率
        returns = sz_data["close"].pct_change().dropna()

        # 年化波动率
        volatility = returns.std() * math.sqrt(252)

        # 限制异常值
        volatility = max(0.005, min(volatility, 0.5))

        log.info(f"市场波动率: {volatility:.4f}")
        return volatility

    except Exception as e:
        log.warn(f"波动率计算失败: {str(e)}")
        return 0.02


def calculate_sentiment_indicator(market_data):
    """计算情绪指标 - 优化版"""
    try:
        limit_data = market_data.get("limit_stocks", {})

        limit_up = limit_data.get("limit_up_count", 0)
        limit_down = limit_data.get("limit_down_count", 0)
        total_stocks = limit_data.get("total_stocks", 1)

        # 基于涨跌停比例的情绪指标
        if total_stocks <= 0:
            total_stocks = 5000

        # 优化情绪计算逻辑
        if limit_up == 0 and limit_down == 0:
            sentiment_base = 0
        else:
            # 使用更合理的基准值
            sentiment_base = (limit_up - limit_down) / (total_stocks * 0.02)  # 2%作为基准

        # 北向资金情绪修正 - 优化权重
        northbound = market_data.get("northbound", 0)
        northbound_sentiment = 0
        if northbound != 0:
            # 以30亿为基准进行标准化，降低影响权重
            northbound_sentiment = min(max(northbound / 3000000000, -0.15), 0.15)

        sentiment = sentiment_base + northbound_sentiment

        # 限制异常值
        sentiment = max(-3.0, min(sentiment, 3.0))

        log.info(
            f"情绪指标: {sentiment:.4f} (涨停{limit_up}/跌停{limit_down}/北向资金修正{northbound_sentiment:.4f})"
        )
        return sentiment

    except Exception as e:
        log.warn(f"情绪指标计算失败: {str(e)}")
        return 0.0


def calculate_heat_score(context, indicators):
    """计算综合火热程度评分 - 修复版"""
    try:
        # 指标标准化处理 - 优化归一化方法，避免0分
        volume_ratio = indicators.get("volume_ratio", 1.0)
        normalized_volume = min(max(volume_ratio / 2.5, 0), 1.0)

        momentum = indicators.get("price_momentum", 0.0)
        # 修改momentum的标准化，避免负值导致0分
        normalized_momentum = (math.tanh(momentum * 8) + 1) / 2  # 范围[0,1]

        breadth = indicators.get("market_breadth", 0.0)
        # 修改breadth的标准化，避免负值导致0分
        normalized_breadth = (math.tanh(breadth * 2) + 1) / 2  # 范围[0,1]

        volatility = indicators.get("volatility", 0.02)
        normalized_volatility = min(max(volatility / 0.15, 0.1), 1.0)  # 保证最小值0.1

        sentiment = indicators.get("sentiment", 0.0)
        # 修改sentiment的标准化，避免负值导致0分
        normalized_sentiment = (math.tanh(sentiment * 1.5) + 1) / 2  # 范围[0,1]

        # 计算加权综合得分
        heat_score = (
            normalized_volume * g.weights["volume_ratio"]
            + normalized_momentum * g.weights["price_momentum"]
            + normalized_breadth * g.weights["market_breadth"]
            + normalized_volatility * g.weights["volatility"]
            + normalized_sentiment * g.weights["sentiment"]
        )

        # 确保评分在合理区间，避免极端值
        heat_score = max(0.05, min(heat_score, 0.95))  # 限制在[0.05, 0.95]范围内

        log.info(f"综合火热程度评分: {heat_score:.3f}")
        return heat_score

    except Exception as e:
        log.error(f"火热程度评分计算失败: {str(e)}")
        return 0.5


def assess_risk_level(heat_score, indicators):
    """评估风险等级和给出建议"""
    try:
        # 风险等级判断
        if heat_score >= 0.8:
            risk_level = "极高风险"
            position_advice = "建议减仓至3-4成，保持高度警惕"
            action = "REDUCE_HEAVY"
        elif heat_score >= 0.6:
            risk_level = "高风险"
            position_advice = "建议减仓至5-6成，控制风险"
            action = "REDUCE_MODERATE"
        elif heat_score >= 0.4:
            risk_level = "中等风险"
            position_advice = "建议保持6-7成仓位，适度参与"
            action = "HOLD"
        elif heat_score >= 0.2:
            risk_level = "低风险"
            position_advice = "可适度加仓至7-8成"
            action = "INCREASE_MODERATE"
        else:
            risk_level = "极低风险"
            position_advice = "可考虑满仓操作，但需关注基本面"
            action = "INCREASE_HEAVY"

        return {
            "risk_level": risk_level,
            "position_advice": position_advice,
            "action": action,
            "heat_score": heat_score,
        }

    except Exception as e:
        log.error(f"风险评估失败: {str(e)}")
        return {
            "risk_level": "未知",
            "position_advice": "建议保持当前仓位",
            "action": "HOLD",
            "heat_score": 0.5,
        }


def output_analysis_result(context, heat_score, indicators, risk_assessment):
    """输出分析结果"""
    try:
        current_time = context.current_dt.strftime("%Y-%m-%d %H:%M:%S")

        log.info("=" * 60)
        log.info(f"A股市场火热程度分析报告-{current_time}")
        log.info("=" * 60)
        log.info(f"综合火热程度评分: {heat_score:.3f}")
        log.info(f"风险等级: {risk_assessment['risk_level']}")
        log.info(f"仓位建议: {risk_assessment['position_advice']}")

        log.info("\n指标详情:")
        log.info(f"- 成交量比率: {indicators.get('volume_ratio', 0):.2f}")
        log.info(f"- 价格动量: {indicators.get('price_momentum', 0):.4f}")
        log.info(f"- 市场广度: {indicators.get('market_breadth', 0):.4f}")
        log.info(f"- 波动率: {indicators.get('volatility', 0):.4f}")
        log.info(f"- 情绪指标: {indicators.get('sentiment', 0):.4f}")
        log.info("=" * 60)

        # 风险预警
        if heat_score >= g.heat_threshold:
            log.warn(f"⚠️ 市场火热程度超过阈值({g.heat_threshold})，建议降低仓位！")

    except Exception as e:
        log.error(f"输出分析结果失败: {str(e)}")


def store_heat_history(context, heat_score, indicators):
    """存储历史数据用于趋势分析 - 优化版"""
    try:
        # 存储当前数据
        record = {
            "timestamp": context.current_dt,
            "date": context.current_dt.date(),  # 添加日期便于查询
            "heat_score": heat_score,
            "volume_ratio": indicators.get("volume_ratio", 0),
            "price_momentum": indicators.get("price_momentum", 0),
            "market_breadth": indicators.get("market_breadth", 0),
            "volatility": indicators.get("volatility", 0),
            "sentiment": indicators.get("sentiment", 0),
        }

        # 避免重复添加同一天的数据
        today = context.current_dt.date()
        g.heat_history = [r for r in g.heat_history if r.get("date") != today]

        g.heat_history.append(record)

        # 保持最近30条记录
        if len(g.heat_history) > 30:
            g.heat_history = g.heat_history[-30:]

        log.info(f"历史数据存储完成，当前记录数: {len(g.heat_history)}")

    except Exception as e:
        log.warn(f"存储历史数据失败: {str(e)}")


def get_heat_trend_analysis(context):
    """获取火热程度趋势分析 - 优化版"""
    try:
        if len(g.heat_history) < 3:
            return "历史数据不足，无法进行趋势分析"

        # 获取最近的评分
        recent_scores = [
            record["heat_score"]
            for record in g.heat_history[-min(10, len(g.heat_history)) :]
        ]

        # 计算趋势
        if len(recent_scores) >= 3:
            # 使用线性回归计算趋势
            x = np.arange(len(recent_scores))
            trend_slope = np.polyfit(x, recent_scores, 1)[0]

            # 计算趋势强度
            if abs(trend_slope) > 0.02:
                trend_strength = "明显"
            elif abs(trend_slope) > 0.01:
                trend_strength = "轻微"
            else:
                trend_strength = "平稳"

            if trend_slope > 0.005:
                trend_desc = f"火热程度{trend_strength}上升趋势"
            elif trend_slope < -0.005:
                trend_desc = f"火热程度{trend_strength}下降趋势"
            else:
                trend_desc = "火热程度相对稳定"

            # 添加近期变化信息
            if len(recent_scores) >= 2:
                recent_change = recent_scores[-1] - recent_scores[-2]
                change_desc = (
                    f"较昨日{'上升' if recent_change > 0 else '下降'}{abs(recent_change):.3f}"
                )
                return f"{trend_desc} (斜率: {trend_slope:.4f}, {change_desc})"
            else:
                return f"{trend_desc} (斜率: {trend_slope:.4f})"

        return "趋势数据不足"

    except Exception as e:
        log.warn(f"趋势分析失败: {str(e)}")
        return "趋势分析失败"


def output_trading_advice(heat_score):
    """输出交易建议"""
    try:
        if heat_score >= 0.7:
            log.warn("🔴 市场过热，建议减仓规避风险")
        elif heat_score <= 0.3:
            log.info("🟢 市场相对冷静，可考虑适度加仓")
        else:
            log.info("🟡 市场处于中性状态，保持观望")
    except Exception as e:
        log.warn(f"输出交易建议失败: {str(e)}")


def before_market_open(context):
    """盘前准备 - 优化版"""
    try:
        log.info("盘前准备-清理缓存数据")

        # 重置当日分析标记
        g.last_analysis_date = None

        # 预热数据连接并记录详细信息
        current_date = context.current_dt.date()
        try:
            test_data = get_price(
                "000001.XSHG",
                start_date=current_date - timedelta(days=1),
                end_date=current_date,
                frequency="daily",
            )
            if not test_data.empty:
                log.info("数据连接测试成功")
            else:
                log.warn("数据连接测试返回空数据")
        except Exception as e:
            log.warn(f"数据连接测试失败: {str(e)}")

        # 清理过期的历史数据
        if hasattr(g, "heat_history") and g.heat_history:
            cutoff_date = current_date - timedelta(days=45)  # 保留45天数据
            g.heat_history = [
                r for r in g.heat_history if r.get("date", current_date) >= cutoff_date
            ]
            log.info(f"历史数据清理完成，保留记录数: {len(g.heat_history)}")

    except Exception as e:
        log.warn(f"盘前准备失败: {str(e)}")


def handle_data(context, data):
    """实时数据处理函数"""
    # 在聚宽中可以通过此函数处理实时数据
    # 由于我们只需要收盘前分析，这里暂时不做处理
    pass


# 策略入口函数
def run_strategy(context):
    """策略主入口 - 可被外部调用"""
    try:
        result = analyze_market_heat(context)
        return result
    except Exception as e:
        log.error(f"策略运行失败: {str(e)}")
        return None
