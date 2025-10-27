<template>
  <div class="slope-analysis">
    <div class="page-header">
      <h1>📈 趋势斜率分析</h1>
      <p class="subtitle">检测市场过热/修复状态 - 基于线性回归斜率</p>
    </div>

    <!-- 参数配置 -->
    <el-card class="modern-card config-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">⚙️ 分析配置</span>
        </div>
      </template>

      <el-form :model="config" label-width="120px" class="config-form">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="标的选择">
              <el-select v-model="config.symbol" placeholder="选择标的" style="width: 100%">
                <el-option-group label="美股指数">
                  <el-option label="纳斯达克 (^IXIC)" value="^IXIC" />
                  <el-option label="标普500 (^GSPC)" value="^GSPC" />
                  <el-option label="道琼斯 (^DJI)" value="^DJI" />
                </el-option-group>
                <el-option-group label="港股指数">
                  <el-option label="恒生指数 (^HSI)" value="^HSI" />
                  <el-option label="恒生科技 (HSTECH.HK)" value="HSTECH.HK" />
                </el-option-group>
                <el-option-group label="A股指数">
                  <el-option label="上证指数 (000001.SS)" value="000001.SS" />
                  <el-option label="深证成指 (399001.SZ)" value="399001.SZ" />
                  <el-option label="沪深300 (000300.SS)" value="000300.SS" />
                  <el-option label="创业板指 (399006.SZ)" value="399006.SZ" />
                  <el-option label="科创50 (000688.SS)" value="000688.SS" />
                </el-option-group>
                <el-option-group label="大宗商品">
                  <el-option label="黄金 (GC=F)" value="GC=F" />
                  <el-option label="白银 (SI=F)" value="SI=F" />
                  <el-option label="原油 (CL=F)" value="CL=F" />
                </el-option-group>
                <el-option-group label="加密货币">
                  <el-option label="比特币 (BTC-USD)" value="BTC-USD" />
                  <el-option label="以太坊 (ETH-USD)" value="ETH-USD" />
                </el-option-group>
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="分析周期">
              <el-select v-model="config.period" placeholder="选择周期" style="width: 100%">
                <el-option label="1年" value="1y" />
                <el-option label="6个月" value="6mo" />
                <el-option label="3个月" value="3mo" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="analyzeSlope" style="width: 100%">
                <el-icon><TrendCharts /></el-icon>
                开始分析
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 综合评估 -->
    <el-card v-if="result" class="modern-card summary-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">🎯 综合评估</span>
          <el-tag :type="getRiskType(result.risk_score)" size="large">
            {{ result.risk_level }}
          </el-tag>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box gradient-1">
            <div class="stat-icon">💰</div>
            <div class="stat-value">${{ result.current_price.toFixed(2) }}</div>
            <div class="stat-label">当前价格</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box gradient-2">
            <div class="stat-icon">📊</div>
            <div class="stat-value">{{ result.slope_60d.annual_return.toFixed(1) }}%</div>
            <div class="stat-label">60日年化收益</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box gradient-3">
            <div class="stat-icon">📈</div>
            <div class="stat-value">{{ result.slope_120d.annual_return.toFixed(1) }}%</div>
            <div class="stat-label">120日年化收益</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box gradient-4">
            <div class="stat-icon">⚠️</div>
            <div class="stat-value">{{ result.risk_score.toFixed(1) }}</div>
            <div class="stat-label">风险评分 (0-100)</div>
          </div>
        </el-col>
      </el-row>

      <el-alert
        :title="result.recommendation"
        :type="getRecommendationType(result.risk_score)"
        show-icon
        :closable="false"
        class="recommendation-alert"
      />
    </el-card>

    <!-- 详细指标 -->
    <el-row v-if="result" :gutter="20">
      <!-- Z-Score -->
      <el-col :xs="24" :md="12">
        <el-card class="modern-card detail-card hover-lift fade-in">
          <template #header>
            <div class="card-header">
              <span class="card-title">🎯 Z-Score (均值回归)</span>
            </div>
          </template>

          <div class="detail-content">
            <div class="gauge-container">
              <el-progress
                type="dashboard"
                :percentage="getZScorePercentage(result.zscore.value)"
                :color="getZScoreColor(result.zscore.value)"
                :width="180"
              >
                <template #default>
                  <div class="gauge-text">
                    <div class="gauge-value">{{ result.zscore.value.toFixed(2) }}</div>
                    <div class="gauge-label">Z-Score</div>
                  </div>
                </template>
              </el-progress>
            </div>

            <div class="detail-info">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="等级">
                  <el-tag :type="getZScoreLevelType(result.zscore.level)">
                    {{ result.zscore.level }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="信号">
                  {{ result.zscore.signal }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 加速度 -->
      <el-col :xs="24" :md="12">
        <el-card class="modern-card detail-card hover-lift fade-in">
          <template #header>
            <div class="card-header">
              <span class="card-title">⚡ 趋势加速度</span>
            </div>
          </template>

          <div class="detail-content">
            <div class="acceleration-display">
              <div class="acceleration-icon" :class="result.acceleration.is_accelerating ? 'accelerating' : 'decelerating'">
                {{ result.acceleration.is_accelerating ? '🔥' : '❄️' }}
              </div>
              <div class="acceleration-status">
                {{ result.acceleration.is_accelerating ? '加速中' : '减速中' }}
              </div>
              <div class="acceleration-level">{{ result.acceleration.level }}</div>
            </div>

            <div class="detail-info">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="加速度值">
                  {{ (result.acceleration.value * 1000000).toFixed(2) }} × 10⁻⁶
                </el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="result.acceleration.is_accelerating ? 'danger' : 'info'">
                    {{ result.acceleration.is_accelerating ? '趋势加强' : '趋势减弱' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 斜率详情 -->
    <el-card v-if="result" class="modern-card slope-detail-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">📊 斜率指标详情</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :xs="24" :md="12">
          <div class="indicator-group">
            <h4>📈 60日斜率指标</h4>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="年化收益率">
                <span :class="getReturnClass(result.slope_60d.annual_return)">
                  {{ result.slope_60d.annual_return.toFixed(2) }}%
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="R² (拟合度)">
                {{ result.slope_60d.r_squared.toFixed(3) }}
              </el-descriptions-item>
              <el-descriptions-item label="日斜率">
                {{ (result.slope_60d.daily_slope * 100).toFixed(4) }}%
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>

        <el-col :xs="24" :md="12">
          <div class="indicator-group">
            <h4>📈 120日斜率指标</h4>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="年化收益率">
                <span :class="getReturnClass(result.slope_120d.annual_return)">
                  {{ result.slope_120d.annual_return.toFixed(2) }}%
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="R² (拟合度)">
                {{ result.slope_120d.r_squared.toFixed(3) }}
              </el-descriptions-item>
              <el-descriptions-item label="日斜率">
                {{ (result.slope_120d.daily_slope * 100).toFixed(4) }}%
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
      </el-row>

      <div class="indicator-group" style="margin-top: 20px">
        <h4>📊 其他指标</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="斜率波动率">
            {{ (result.volatility.slope_std * 1000).toFixed(3) }} × 10⁻³
          </el-descriptions-item>
          <el-descriptions-item label="变异系数">
            {{ result.volatility.slope_cv.toFixed(3) }}
          </el-descriptions-item>
          <el-descriptions-item label="相对MA偏离">
            <span :class="getDeviationClass(result.ma_relative.deviation_pct)">
              {{ result.ma_relative.deviation_pct.toFixed(2) }}%
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="偏离等级">
            <el-tag>{{ result.ma_relative.deviation_level }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-if="!loading && !result" description="请选择指数并开始分析" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts } from '@element-plus/icons-vue'

// 配置
const config = ref({
  symbol: '^IXIC',
  period: '1y'
})

const loading = ref(false)
const result = ref<any>(null)

// 分析函数
const analyzeSlope = async () => {
  loading.value = true

  try {
    // TODO: 调用后端API
    // const response = await fetch(`/api/slope/analyze?symbol=${config.value.symbol}`)
    // result.value = await response.json()

    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 1500))

    result.value = {
      symbol: config.value.symbol,
      current_price: 22204.43,
      slope_60d: {
        annual_return: 62.30,
        r_squared: 0.871,
        daily_slope: 0.001707
      },
      slope_120d: {
        annual_return: 100.07,
        r_squared: 0.945,
        daily_slope: 0.002741
      },
      volatility: {
        slope_std: 0.002222,
        slope_cv: 2.769,
        percentile: 60.0
      },
      ma_relative: {
        deviation_pct: 12.56,
        deviation_level: '中度偏离',
        is_above_ma: true
      },
      zscore: {
        value: 0.41,
        level: '正常区间',
        signal: '中性'
      },
      acceleration: {
        value: -0.000017,
        is_accelerating: false,
        level: '温和减速'
      },
      risk_score: 79.3,
      risk_level: '高风险',
      recommendation: '⚠️ 高风险区域，建议降低仓位'
    }

    ElMessage.success('分析完成！')
  } catch (error) {
    ElMessage.error('分析失败，请重试')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 辅助函数
const getRiskType = (score: number) => {
  if (score > 75) return 'danger'
  if (score > 60) return 'warning'
  if (score > 40) return 'info'
  return 'success'
}

const getRecommendationType = (score: number) => {
  if (score > 75) return 'error'
  if (score > 60) return 'warning'
  return 'info'
}

const getZScorePercentage = (zscore: number) => {
  return Math.min(100, Math.abs(zscore) * 25)
}

const getZScoreColor = (zscore: number) => {
  const abs = Math.abs(zscore)
  if (abs > 2) return '#F56C6C'
  if (abs > 1.5) return '#E6A23C'
  return '#67C23A'
}

const getZScoreLevelType = (level: string) => {
  if (level.includes('极端')) return 'danger'
  if (level.includes('异常')) return 'warning'
  return 'success'
}

const getReturnClass = (value: number) => {
  if (value > 40) return 'text-danger'
  if (value > 20) return 'text-warning'
  if (value > 0) return 'text-success'
  return 'text-info'
}

const getDeviationClass = (value: number) => {
  const abs = Math.abs(value)
  if (abs > 15) return 'text-danger'
  if (abs > 10) return 'text-warning'
  return 'text-success'
}
</script>

<style scoped lang="scss">
.slope-analysis {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;

  h1 {
    font-size: 28px;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: #303133;
  }

  .subtitle {
    font-size: 14px;
    color: #909399;
    margin: 0;
  }
}

.modern-card {
  margin-bottom: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.hover-lift:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.fade-in {
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .card-title {
    font-size: 16px;
    font-weight: 600;
  }
}

.stat-box {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  color: white;
  margin-bottom: 15px;

  .stat-icon {
    font-size: 32px;
    margin-bottom: 8px;
  }

  .stat-value {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .stat-label {
    font-size: 14px;
    opacity: 0.9;
  }
}

.gradient-1 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.gradient-2 {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.gradient-3 {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.gradient-4 {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.recommendation-alert {
  margin-top: 20px;
  font-size: 15px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.gauge-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.gauge-text {
  text-align: center;

  .gauge-value {
    font-size: 32px;
    font-weight: 700;
    color: #303133;
  }

  .gauge-label {
    font-size: 14px;
    color: #909399;
    margin-top: 8px;
  }
}

.acceleration-display {
  text-align: center;
  padding: 20px;

  .acceleration-icon {
    font-size: 64px;
    margin-bottom: 12px;

    &.accelerating {
      animation: pulse 2s infinite;
    }
  }

  .acceleration-status {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  .acceleration-level {
    font-size: 14px;
    color: #909399;
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.detail-info {
  width: 100%;
}

.indicator-group {
  h4 {
    margin: 0 0 12px 0;
    color: #303133;
    font-weight: 600;
  }
}

.text-danger {
  color: #F56C6C;
  font-weight: 600;
}

.text-warning {
  color: #E6A23C;
  font-weight: 600;
}

.text-success {
  color: #67C23A;
  font-weight: 600;
}

.text-info {
  color: #909399;
}

@media (max-width: 768px) {
  .page-header h1 {
    font-size: 24px;
  }

  .stat-box {
    .stat-value {
      font-size: 28px;
    }
  }
}
</style>
