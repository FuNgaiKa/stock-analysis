#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股市场分析系统 - FastAPI后端
提供RESTful API给前端调用
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sys
import os

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
