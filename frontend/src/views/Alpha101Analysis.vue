<template>
  <div class="alpha101-analysis">
    <div class="page-header">
      <h1>📊 Alpha101 因子分析</h1>
      <p class="subtitle">WorldQuant 顶级量化因子 - 智能信号生成</p>
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
              <el-button type="primary" :loading="loading" @click="analyzeAlpha" style="width: 100%">
                <el-icon><DataAnalysis /></el-icon>
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
          <span class="card-title">📈 综合评估</span>
          <el-tag :type="getSignalType(result.summary.signal_strength)" size="large">
            {{ result.summary.signal_strength }}
          </el-tag>
        </div>
      </template>

      <el-row :gutter="20" class="summary-row">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box bullish-box">
            <div class="stat-icon">📈</div>
            <div class="stat-value">{{ result.summary.positive_count }}</div>
            <div class="stat-label">看多因子</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box bearish-box">
            <div class="stat-icon">📉</div>
            <div class="stat-value">{{ result.summary.negative_count }}</div>
            <div class="stat-label">看空因子</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box neutral-box">
            <div class="stat-icon">➡️</div>
            <div class="stat-value">{{ result.summary.neutral_count }}</div>
            <div class="stat-label">中性因子</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box signal-box">
            <div class="stat-icon">💡</div>
            <div class="stat-value">{{ result.summary.avg_signal.toFixed(2) }}</div>
            <div class="stat-label">平均信号</div>
          </div>
        </el-col>
      </el-row>

      <el-alert
        :title="result.summary.recommendation"
        :type="getAlertType(result.summary.signal_strength)"
        show-icon
        :closable="false"
        class="recommendation-alert"
      />
    </el-card>

    <!-- 因子信号详情 -->
    <el-card v-if="result" class="modern-card signals-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">🔢 Top 10 因子信号</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col
          v-for="(value, name) in result.signals"
          :key="name"
          :xs="24" :sm="12" :md="8" :lg="6"
        >
          <div class="factor-card" :class="getFactorClass(value)">
            <div class="factor-header">
              <span class="factor-name">{{ name }}</span>
              <span class="factor-icon">{{ getFactorIcon(value) }}</span>
            </div>
            <div class="factor-value">{{ value.toFixed(4) }}</div>
            <div class="factor-label">{{ getFactorType(name) }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 因子统计 -->
    <el-card v-if="result && result.alpha_stats" class="modern-card stats-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">📊 因子统计详情</span>
        </div>
      </template>

      <el-table :data="statsTableData" stripe class="stats-table">
        <el-table-column prop="name" label="因子名称" width="120" />
        <el-table-column prop="current" label="当前值" width="100" align="right" />
        <el-table-column prop="mean" label="均值" width="100" align="right" />
        <el-table-column prop="std" label="标准差" width="100" align="right" />
        <el-table-column prop="min" label="最小值" width="100" align="right" />
        <el-table-column prop="max" label="最大值" width="100" align="right" />
        <el-table-column label="百分位" width="150">
          <template #default="scope">
            <el-progress
              :percentage="scope.row.percentile"
              :color="getPercentileColor(scope.row.percentile)"
              :stroke-width="12"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-if="!loading && !result" description="请选择指数并开始分析" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis } from '@element-plus/icons-vue'

// 配置
const config = ref({
  symbol: '^IXIC',
  period: '1y'
})

const loading = ref(false)
const result = ref<any>(null)

// 分析函数
const analyzeAlpha = async () => {
  loading.value = true

  try {
    // TODO: 调用后端API
    // const response = await fetch(`/api/alpha101/analyze?symbol=${config.value.symbol}`)
    // result.value = await response.json()

    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 1500))

    result.value = {
      symbol: config.value.symbol,
      signals: {
        alpha001: 0.3130,
        alpha002: -0.7229,
        alpha003: -0.6544,
        alpha004: -0.1111,
        alpha006: -0.7329,
        alpha007: 0.8000,
        alpha009: 820.2012,
        alpha012: 0.0000,
        alpha017: -0.0003,
        alpha021: -0.0260
      },
      summary: {
        positive_count: 3,
        negative_count: 6,
        neutral_count: 1,
        avg_signal: 81.9066,
        signal_strength: 'bearish',
        recommendation: '⬇️ 看空 - 因子偏空，建议谨慎或减仓'
      },
      alpha_stats: {
        alpha001: {
          current: 0.3130,
          mean: 0.5022,
          std: 0.2753,
          min: 0.0,
          max: 1.0,
          percentile: 31.3
        },
        alpha002: {
          current: -0.7229,
          mean: -0.0117,
          std: 0.4287,
          min: -1.0,
          max: 1.0,
          percentile: 5.0
        },
        alpha003: {
          current: -0.6544,
          mean: -0.1531,
          std: 0.4208,
          min: -1.0,
          max: 1.0,
          percentile: 11.7
        }
      }
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
const getSignalType = (strength: string) => {
  const types: Record<string, any> = {
    'strong_bullish': 'success',
    'bullish': 'success',
    'neutral': 'info',
    'bearish': 'warning',
    'strong_bearish': 'danger'
  }
  return types[strength] || 'info'
}

const getAlertType = (strength: string) => {
  const types: Record<string, any> = {
    'strong_bullish': 'success',
    'bullish': 'success',
    'neutral': 'info',
    'bearish': 'warning',
    'strong_bearish': 'error'
  }
  return types[strength] || 'info'
}

const getFactorIcon = (value: number) => {
  if (value > 0.5) return '📈'
  if (value < -0.5) return '📉'
  return '➡️'
}

const getFactorClass = (value: number) => {
  if (value > 0.5) return 'factor-bullish'
  if (value < -0.5) return 'factor-bearish'
  return 'factor-neutral'
}

const getFactorType = (name: string) => {
  const types: Record<string, string> = {
    alpha001: '动量反转',
    alpha002: '价量相关',
    alpha003: '开盘量相关',
    alpha004: '低价动量',
    alpha006: '开盘量相关2',
    alpha007: '振幅成交量',
    alpha009: '收盘价Delta',
    alpha012: '符号成交量',
    alpha017: 'VWAP相关',
    alpha021: '线性回归'
  }
  return types[name] || '未知'
}

const getPercentileColor = (percentile: number) => {
  if (percentile > 80) return '#67C23A'
  if (percentile > 60) return '#409EFF'
  if (percentile > 40) return '#E6A23C'
  return '#F56C6C'
}

// 统计表格数据
const statsTableData = computed(() => {
  if (!result.value || !result.value.alpha_stats) return []

  return Object.entries(result.value.alpha_stats).map(([name, stats]: [string, any]) => ({
    name,
    current: stats.current.toFixed(4),
    mean: stats.mean.toFixed(4),
    std: stats.std.toFixed(4),
    min: stats.min.toFixed(4),
    max: stats.max.toFixed(4),
    percentile: stats.percentile
  }))
})
</script>

<style scoped lang="scss">
.alpha101-analysis {
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

.summary-row {
  margin-bottom: 20px;
}

.stat-box {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

.bullish-box {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.bearish-box {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.neutral-box {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.signal-box {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.recommendation-alert {
  margin-top: 20px;
  font-size: 15px;
}

.factor-card {
  padding: 16px;
  border-radius: 8px;
  border: 2px solid #E4E7ED;
  margin-bottom: 15px;
  transition: all 0.3s ease;

  &:hover {
    border-color: #409EFF;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  }

  .factor-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;

    .factor-name {
      font-weight: 600;
      font-size: 14px;
    }

    .factor-icon {
      font-size: 18px;
    }
  }

  .factor-value {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .factor-label {
    font-size: 12px;
    color: #909399;
  }
}

.factor-bullish {
  border-color: #67C23A;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);

  .factor-value {
    color: #67C23A;
  }
}

.factor-bearish {
  border-color: #F56C6C;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);

  .factor-value {
    color: #F56C6C;
  }
}

.factor-neutral {
  background: #F5F7FA;

  .factor-value {
    color: #909399;
  }
}

.stats-table {
  margin-top: 10px;
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
