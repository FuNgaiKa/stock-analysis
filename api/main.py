#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股市场分析系统 - FastAPI后端
提供RESTful API给前端调用
"""

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sys
import os
import asyncio
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from position_analysis.us_market_analyzer import (
    USMarketAnalyzer,
    US_INDICES,
    DEFAULT_US_INDICES
)

# 创建FastAPI应用
app = FastAPI(
    title="美股市场分析API",
    description="基于历史数据的量化投资决策辅助API",
    version="3.0.0"
)

# 配置CORS(允许前端跨域访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局分析器实例
analyzer = None


def get_analyzer():
    """获取分析器实例(懒加载)"""
    global analyzer
    if analyzer is None:
        analyzer = USMarketAnalyzer()
    return analyzer


# ==================== 数据模型 ====================

class IndexInfo(BaseModel):
    """指数信息"""
    code: str
    name: str
    symbol: str


class AnalysisRequest(BaseModel):
    """分析请求"""
    indices: List[str]
    tolerance: float = 0.05
    periods: List[int] = [5, 10, 20, 60]
    use_phase2: bool = False
    use_phase3: bool = False


# ==================== API接口 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "美股市场分析API",
        "version": "3.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/api/indices", response_model=List[IndexInfo])
async def get_indices():
    """
    获取支持的指数列表

    Returns:
        指数列表
    """
    return [
        IndexInfo(
            code=code,
            name=config.name,
            symbol=config.symbol
        )
        for code, config in US_INDICES.items()
    ]


@app.get("/api/indices/default")
async def get_default_indices():
    """
    获取默认指数

    Returns:
        默认指数代码列表
    """
    return {"indices": DEFAULT_US_INDICES}


@app.get("/api/current-positions")
async def get_current_positions(
    indices: Optional[List[str]] = Query(None)
):
    """
    获取当前点位

    Args:
        indices: 指数代码列表,不传则使用默认指数

    Returns:
        当前点位信息
    """
    try:
        analyzer = get_analyzer()

        if indices is None:
            indices = DEFAULT_US_INDICES

        positions = analyzer.get_current_positions(indices)

        return {
            "success": True,
            "data": positions,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/single")
async def analyze_single(
    index_code: str = Query(..., description="指数代码"),
    tolerance: float = Query(0.05, ge=0.01, le=0.2, description="相似度容差"),
    periods: List[int] = Query([5, 10, 20, 60], description="分析周期"),
    use_phase2: bool = Query(False, description="是否使用Phase 2"),
    use_phase3: bool = Query(False, description="是否使用Phase 3")
):
    """
    单指数分析

    Args:
        index_code: 指数代码
        tolerance: 相似度容差(0.01-0.2)
        periods: 分析周期列表
        use_phase2: 是否使用Phase 2增强分析
        use_phase3: 是否使用Phase 3深度分析

    Returns:
        分析结果
    """
    try:
        if index_code not in US_INDICES:
            raise HTTPException(status_code=400, detail=f"不支持的指数代码: {index_code}")

        analyzer = get_analyzer()

        result = analyzer.analyze_single_index(
            index_code=index_code,
            tolerance=tolerance,
            periods=periods,
            use_phase2=use_phase2,
            use_phase3=use_phase3
        )

        # 转换datetime为字符串
        if 'timestamp' in result:
            result['timestamp'] = result['timestamp'].isoformat()

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/multiple")
async def analyze_multiple(request: AnalysisRequest):
    """
    多指数联合分析

    Args:
        request: 分析请求

    Returns:
        多指数分析结果
    """
    try:
        # 验证指数代码
        for code in request.indices:
            if code not in US_INDICES:
                raise HTTPException(status_code=400, detail=f"不支持的指数代码: {code}")

        analyzer = get_analyzer()

        result = analyzer.analyze_multiple_indices(
            indices=request.indices,
            tolerance=request.tolerance,
            periods=request.periods,
            use_phase2=request.use_phase2,
            use_phase3=request.use_phase3
        )

        # 转换datetime为字符串
        if 'timestamp' in result:
            result['timestamp'] = result['timestamp'].isoformat()

        # 转换individual_analysis中的datetime
        if 'individual_analysis' in result:
            for analysis in result['individual_analysis'].values():
                if 'timestamp' in analysis:
                    analysis['timestamp'] = analysis['timestamp'].isoformat()

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# ==================== VIX专用API ====================

@app.get("/api/vix/current")
async def get_vix_current():
    """
    获取VIX当前状态

    Returns:
        VIX当前数据和状态
    """
    try:
        analyzer = get_analyzer()

        # 获取VIX分析数据
        vix_analysis = analyzer.vix_analyzer.analyze_vix(period="5y")

        return {
            "success": True,
            "data": vix_analysis,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 行业轮动API ====================

@app.get("/api/sectors/current")
async def get_sectors_current():
    """
    获取当前行业表现

    Returns:
        11个行业ETF当前表现数据
    """
    try:
        analyzer = get_analyzer()

        # 获取行业轮动分析
        sector_analysis = analyzer.sector_analyzer.analyze_sector_rotation(
            periods=[1, 5, 20, 60]
        )

        return {
            "success": True,
            "data": sector_analysis,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 回测API ====================

@app.post("/api/backtest/run")
async def run_backtest(
    index_code: str = Query(..., description="指数代码或ETF代码"),
    days: int = Query(500, ge=100, le=2000, description="回测天数"),
    initial_capital: float = Query(100000, ge=10000, description="初始资金"),
    stop_loss: float = Query(0.08, ge=0.01, le=0.5, description="止损比例"),
    take_profit: float = Query(0.15, ge=0.05, le=1.0, description="止盈比例")
):
    """
    运行策略回测

    Args:
        index_code: 指数代码(SPX/NASDAQ/NDX等)或直接使用yfinance symbol
        days: 回测天数
        initial_capital: 初始资金
        stop_loss: 止损比例
        take_profit: 止盈比例

    Returns:
        回测结果
    """
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from trading_strategies.signal_generators.technical_indicators import TechnicalIndicators
        from trading_strategies.signal_generators.resonance_signals import ResonanceSignalGenerator
        from trading_strategies.backtesting.backtest_engine import BacktestEngine
        from trading_strategies.backtesting.performance_metrics import PerformanceMetrics
        import yfinance as yf
        import pandas as pd

        # 获取数据 - 支持指数代码或直接使用symbol
        if index_code in US_INDICES:
            index_info = US_INDICES[index_code]
            symbol = index_info.symbol
            index_name = index_info.name
        else:
            # 直接使用提供的代码作为symbol (支持SPY, QQQ等ETF)
            symbol = index_code
            index_name = index_code

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d")

        if df.empty:
            raise HTTPException(status_code=500, detail="获取历史数据失败")

        # 重命名列
        df = df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })

        # 计算技术指标
        calculator = TechnicalIndicators()
        df = calculator.calculate_all_indicators(df)

        # 运行回测
        generator = ResonanceSignalGenerator()
        engine = BacktestEngine(
            initial_capital=initial_capital,
            commission=0.0003,
            slippage=0.0001,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        result = engine.run_backtest_with_strategy(df, generator)

        # 计算性能指标
        metrics = PerformanceMetrics()
        performance = metrics.generate_performance_report(
            returns=result['daily_returns'],
            trades=result['trades'],
            initial_capital=initial_capital
        )

        # 准备返回数据
        # 权益曲线数据
        equity_curve = [
            {"date": str(df.index[i].date() if hasattr(df.index[i], 'date') else df.index[i]),
             "value": result['portfolio_value'][i]}
            for i in range(len(result['portfolio_value']))
        ]

        # 交易记录（前20笔）
        trades_data = []
        for trade in result['trades'][:20]:
            trades_data.append({
                'entry_date': str(trade['entry_date']),
                'exit_date': str(trade['exit_date']),
                'entry_price': round(trade['entry_price'], 2),
                'exit_price': round(trade['exit_price'], 2),
                'shares': trade['shares'],
                'return': round(trade['return'] * 100, 2),
                'pnl': round(trade['pnl'], 2),
                'signal': trade.get('signal', 'SELL')
            })

        return {
            "success": True,
            "data": {
                "performance": performance,
                "equity_curve": equity_curve,
                "trades": trades_data,
                "config": {
                    "index_code": index_code,
                    "index_name": index_name,
                    "days": days,
                    "initial_capital": initial_capital,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 港股市场API ====================

@app.get("/api/hk/indices")
async def get_hk_indices():
    """获取支持的港股指数列表"""
    try:
        from position_analysis.hk_market_analyzer import HK_INDICES
        return [
            {
                "code": code,
                "name": config.name,
                "symbol": config.symbol,
                "market": "HK"
            }
            for code, config in HK_INDICES.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hk/current-positions")
async def get_hk_current_positions(
    indices: Optional[List[str]] = Query(None)
):
    """获取港股指数当前点位"""
    try:
        from position_analysis.hk_market_analyzer import HKMarketAnalyzer, DEFAULT_HK_INDICES

        analyzer = HKMarketAnalyzer()

        if indices is None:
            indices = DEFAULT_HK_INDICES

        positions = analyzer.get_current_positions(indices)

        return {
            "success": True,
            "data": positions,
            "market": "HK",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== A股市场API ====================

@app.get("/api/cn/indices")
async def get_cn_indices():
    """获取支持的A股指数列表"""
    try:
        from position_analysis.cn_market_analyzer import CN_INDICES
        return [
            {
                "code": code,
                "name": config.name,
                "symbol": config.symbol,
                "market": "CN"
            }
            for code, config in CN_INDICES.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cn/current-positions")
async def get_cn_current_positions(
    indices: Optional[List[str]] = Query(None)
):
    """获取A股指数当前点位"""
    try:
        from position_analysis.cn_market_analyzer import CNMarketAnalyzer, DEFAULT_CN_INDICES

        analyzer = CNMarketAnalyzer()

        if indices is None:
            indices = DEFAULT_CN_INDICES

        positions = analyzer.get_current_positions(indices)

        return {
            "success": True,
            "data": positions,
            "market": "CN",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 相关性分析API ====================

@app.post("/api/correlation/analyze")
async def analyze_correlation(
    symbols: List[str] = Query(..., description="资产代码列表"),
    lookback_days: int = Query(252, ge=60, le=1000, description="回溯天数")
):
    """
    跨资产相关性分析

    Args:
        symbols: 资产代码列表(至少2个)
        lookback_days: 回溯天数

    Returns:
        相关性分析结果
    """
    try:
        if len(symbols) < 2:
            raise HTTPException(status_code=400, detail="至少需要2个资产代码")

        from position_analysis.analyzers.correlation_analyzer import CorrelationAnalyzer

        # 资产名称映射
        asset_names = {
            '^IXIC': '纳斯达克',
            '^GSPC': '标普500',
            '^DJI': '道琼斯',
            '000001.SS': '上证指数',
            '399001.SZ': '深证成指',
            '000300.SS': '沪深300',
            '399006.SZ': '创业板指',
            '000688.SS': '科创50',
            '^HSI': '恒生指数',
            'HSTECH.HK': '恒生科技',
            'GC=F': '黄金',
            'SI=F': '白银',
            'CL=F': '原油',
            'BTC-USD': '比特币',
            'ETH-USD': '以太坊'
        }

        analyzer = CorrelationAnalyzer(lookback_days=lookback_days)
        result = analyzer.comprehensive_analysis(symbols, asset_names)

        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])

        # 转换datetime为字符串
        if 'timestamp' in result:
            result['timestamp'] = result['timestamp'].isoformat()

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 支撑/压力位分析API ====================

@app.get("/api/support-resistance/analyze")
async def analyze_support_resistance(
    symbol: str = Query(..., description="资产代码"),
    lookback_days: int = Query(252, ge=120, le=1000, description="回溯天数")
):
    """
    支撑/压力位分析

    Args:
        symbol: 资产代码
        lookback_days: 回溯天数

    Returns:
        支撑/压力位分析结果
    """
    try:
        from position_analysis.analyzers.support_resistance import SupportResistanceAnalyzer

        analyzer = SupportResistanceAnalyzer(symbol, lookback_days=lookback_days)
        result = analyzer.comprehensive_analysis()

        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])

        # 转换datetime为字符串
        if 'timestamp' in result:
            result['timestamp'] = result['timestamp'].isoformat()

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 市场情绪指数API ====================

@app.get("/api/sentiment/analyze")
async def analyze_market_sentiment():
    """
    市场情绪综合指数分析

    Returns:
        市场情绪指数(0-100)和各维度评分
    """
    try:
        from position_analysis.analyzers.sentiment_index import MarketSentimentIndex

        analyzer = MarketSentimentIndex()
        result = analyzer.calculate_comprehensive_sentiment()

        # 转换datetime为字符串
        if 'timestamp' in result:
            result['timestamp'] = result['timestamp'].isoformat()

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WebSocket实时数据推送 ====================

# 存储所有活跃的WebSocket连接
active_connections: List[WebSocket] = []


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


manager = ConnectionManager()


@app.websocket("/ws/market-data")
async def websocket_market_data(websocket: WebSocket):
    """
    WebSocket端点 - 实时推送市场数据

    推送频率: 每30秒
    数据内容:
    - 市场情绪指数
    - 主要指数当前价格
    - VIX当前值
    """
    await manager.connect(websocket)
    print(f"WebSocket客户端已连接,当前连接数: {len(manager.active_connections)}")

    try:
        while True:
            # 获取实时数据
            try:
                from position_analysis.analyzers.sentiment_index import MarketSentimentIndex
                from data_sources.us_stock_source import USStockDataSource

                # 1. 市场情绪指数
                sentiment_analyzer = MarketSentimentIndex()
                sentiment = sentiment_analyzer.calculate_comprehensive_sentiment()

                # 2. 主要指数当前价格
                data_source = USStockDataSource()
                indices_data = {}

                for symbol, name in [
                    ('^IXIC', '纳斯达克'),
                    ('^GSPC', '标普500'),
                    ('^VIX', 'VIX')
                ]:
                    try:
                        df = data_source.get_us_index_daily(symbol, period='5d')
                        if not df.empty:
                            indicators = data_source.calculate_technical_indicators(df)
                            indices_data[symbol] = {
                                'name': name,
                                'price': indicators.get('latest_price', 0),
                                'change_pct': indicators.get('change_pct', 0),
                                'date': indicators.get('latest_date', '')
                            }
                    except:
                        pass

                # 转换datetime为字符串
                if 'timestamp' in sentiment:
                    sentiment['timestamp'] = sentiment['timestamp'].isoformat()

                # 构建推送消息
                message = {
                    "type": "market_data",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "sentiment": {
                            "score": sentiment.get('sentiment_score', 0),
                            "rating": sentiment.get('rating', ''),
                            "emoji": sentiment.get('emoji', ''),
                        },
                        "indices": indices_data
                    }
                }

                await websocket.send_json(message)

            except Exception as e:
                print(f"获取数据失败: {str(e)}")
                # 发送错误消息
                await websocket.send_json({
                    "type": "error",
                    "message": "数据获取失败",
                    "timestamp": datetime.now().isoformat()
                })

            # 等待30秒
            await asyncio.sleep(30)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"WebSocket客户端已断开,当前连接数: {len(manager.active_connections)}")
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        manager.disconnect(websocket)


# ==================== 启动配置 ====================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("美股市场分析API服务")
    print("=" * 60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API文档: http://localhost:8000/docs")
    print(f"健康检查: http://localhost:8000/api/health")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
