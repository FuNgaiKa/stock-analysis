/**
 * 金融工具平台 - TypeScript类型定义
 */

// ==================== 基础类型 ====================

/** 指数信息 */
export interface IndexInfo {
  code: string
  name: string
  symbol: string
}

/** 分析请求参数 */
export interface AnalysisParams {
  index_code?: string
  indices?: string[]
  tolerance: number
  periods: number[]
  use_phase2: boolean
  use_phase3: boolean
}

// ==================== 分析结果类型 ====================

/** 市场环境识别 */
export interface MarketEnvironment {
  environment: string
  rsi: number
  dist_to_high_pct: number
  ma_state: string
  description: string
}

/** 周期分析统计 */
export interface PeriodStats {
  sample_size: number
  up_count: number
  down_count: number
  up_prob: number
  mean_return: number
  median_return: number
  std_return: number
  min_return: number
  max_return: number
  confidence: number
  position_advice?: PositionAdvice
}

/** 仓位建议 */
export interface PositionAdvice {
  signal: string
  description: string
  recommended_position: number
  warning?: string
}

/** VIX分析结果 */
export interface VixAnalysis {
  current_state: {
    vix_value: number
    status: string
    change: number
    change_pct: number
    week_change_pct?: number
  }
  percentiles?: {
    '30d': number
    '60d': number
    '252d': number
    '1260d': number
  }
  signal: {
    signal: string
    description: string
    action: string
  }
}

/** 行业轮动分析 */
export interface SectorRotation {
  rotation_pattern: {
    pattern: string
    description: string
  }
  sector_performance: {
    [key: string]: {
      symbol: string
      name: string
      rs_score: number
      return_1d: number
      return_5d: number
      return_20d: number
      return_60d: number
    }
  }
  allocation_recommendation: {
    recommendation: string
    recommended_sectors: string[]
  }
}

/** 成交量分析 */
export interface VolumeAnalysis {
  volume_status: {
    status: string
    description: string
    volume_ratio?: number
  }
  price_volume_relationship: {
    pattern: string
    description: string
  }
  signal: {
    signal: string
    description: string
  }
}

/** Phase 3 深度分析 */
export interface Phase3Analysis {
  vix?: VixAnalysis
  sector_rotation?: SectorRotation
  volume?: VolumeAnalysis
}

/** 单指数分析结果 */
export interface SingleIndexAnalysis {
  index_code: string
  index_name: string
  current_price: number
  current_date: string
  current_change_pct: number
  similar_periods_count: number
  market_environment?: MarketEnvironment
  period_analysis: {
    [key: string]: PeriodStats
  }
  phase3_analysis?: Phase3Analysis
  warning?: string
  error?: string
  timestamp: string
}

/** 多指数分析结果 */
export interface MultiIndexAnalysis {
  individual_analysis: {
    [key: string]: SingleIndexAnalysis
  }
  timestamp: string
}

/** API响应 */
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  timestamp?: string
}

// ==================== 图表数据类型 ====================

/** 折线图数据点 */
export interface LineChartDataPoint {
  date: string
  value: number
}

/** 雷达图数据 */
export interface RadarChartData {
  name: string
  value: number
}

/** 柱状图数据 */
export interface BarChartData {
  name: string
  value: number
  color?: string
}

// ==================== 组件Props类型 ====================

/** 指标卡片Props */
export interface MetricCardProps {
  label: string
  value: string | number
  change?: number
  prefix?: string
  suffix?: string
  trend?: 'up' | 'down' | 'neutral'
}

/** 图表组件Props */
export interface ChartProps {
  data: any[]
  height?: string
  width?: string
  loading?: boolean
}
