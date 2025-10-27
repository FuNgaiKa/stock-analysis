<template>
  <div class="index-analysis">
    <!-- 配置区 -->
    <el-card class="config-card" shadow="never">
      <el-form :inline="true" :model="formData">
        <el-form-item :label="$t('indexAnalysis.selectIndex')">
          <el-select
            v-model="formData.selectedIndex"
            :placeholder="$t('indexAnalysis.selectIndex')"
            style="width: 200px"
          >
            <el-option
              v-for="idx in indices"
              :key="idx.code"
              :label="`${idx.name} (${idx.code})`"
              :value="idx.code"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('indexAnalysis.selectPhase')">
          <el-select v-model="formData.phase" style="width: 150px">
            <el-option label="Phase 1" value="1" />
            <el-option label="Phase 2" value="2" />
            <el-option label="Phase 3" value="3" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('indexAnalysis.tolerance')">
          <el-input-number
            v-model="formData.tolerance"
            :min="0.01"
            :max="0.2"
            :step="0.01"
            :precision="2"
            style="width: 150px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleAnalyze" :loading="analyzing">
            <el-icon><TrendCharts /></el-icon>
            {{ $t('indexAnalysis.startAnalysis') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 结果展示区 -->
    <div v-if="result" class="result-section">
      <!-- 指标卡片 -->
      <el-row :gutter="20" class="metric-row">
        <el-col :xs="12" :sm="6">
          <metric-card
            :label="$t('indexAnalysis.currentPrice')"
            :value="result.current_price.toFixed(2)"
            :change="result.current_change_pct"
          />
        </el-col>
        <el-col :xs="12" :sm="6">
          <metric-card
            :label="$t('indexAnalysis.dataDate')"
            :value="result.current_date"
          />
        </el-col>
        <el-col :xs="12" :sm="6">
          <metric-card
            :label="$t('indexAnalysis.similarPeriods')"
            :value="result.similar_periods_count"
            suffix=" 个"
          />
        </el-col>
        <el-col :xs="12" :sm="6">
          <metric-card
            :label="$t('indexAnalysis.selectPhase')"
            :value="`Phase ${formData.phase}`"
          />
        </el-col>
      </el-row>

      <!-- Phase 2 市场环境 -->
      <el-card
        v-if="result.market_environment"
        class="analysis-card"
        shadow="hover"
      >
        <template #header>
          <span class="card-title">
            <el-icon><Opportunity /></el-icon>
            {{ $t('marketEnvironment.title') }} (Phase 2)
          </span>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('marketEnvironment.environment')">
            <el-tag :type="getEnvironmentType(result.market_environment.environment)">
              {{ result.market_environment.environment }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('marketEnvironment.rsi')">
            {{ result.market_environment.rsi.toFixed(1) }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('marketEnvironment.distToHigh')">
            {{ result.market_environment.dist_to_high_pct.toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item :label="$t('marketEnvironment.maState')">
            {{ result.market_environment.ma_state }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 周期分析 -->
      <el-card class="analysis-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><DataAnalysis /></el-icon>
            {{ $t('periodAnalysis.title') }}
          </span>
        </template>

        <el-table :data="periodTableData" stripe border>
          <el-table-column prop="period" :label="$t('periodAnalysis.period')" width="100" />
          <el-table-column prop="sampleSize" :label="$t('periodAnalysis.sampleSize')" width="100" />
          <el-table-column prop="upProb" :label="$t('periodAnalysis.upProb')" width="120">
            <template #default="{ row }">
              <span :style="{ color: row.upProb >= 60 ? '#67c23a' : '#f56c6c' }">
                {{ row.upProb }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="meanReturn" :label="$t('periodAnalysis.meanReturn')" width="120">
            <template #default="{ row }">
              <span :style="{ color: parseFloat(row.meanReturn) > 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.meanReturn }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="medianReturn" :label="$t('periodAnalysis.medianReturn')" width="120" />
          <el-table-column prop="confidence" :label="$t('periodAnalysis.confidence')" width="100" />
          <el-table-column prop="recommendedPosition" :label="$t('periodAnalysis.recommendedPosition')" width="120" />
          <el-table-column prop="signal" :label="$t('periodAnalysis.signal')" min-width="150" />
        </el-table>
      </el-card>

      <!-- 20日核心结论 -->
      <el-card v-if="result.period_analysis?.['20d']" class="analysis-card conclusion-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><StarFilled /></el-icon>
            💡 20{{ $t('periodAnalysis.days') }}{{ $t('periodAnalysis.title') }}
          </span>
        </template>

        <el-row :gutter="20">
          <el-col :xs="12" :sm="6">
            <metric-card
              :label="$t('periodAnalysis.upProb')"
              :value="`${(result.period_analysis['20d'].up_prob * 100).toFixed(1)}%`"
              :trend="result.period_analysis['20d'].up_prob >= 0.6 ? 'up' : 'down'"
            />
          </el-col>
          <el-col :xs="12" :sm="6">
            <metric-card
              :label="$t('periodAnalysis.meanReturn')"
              :value="`${(result.period_analysis['20d'].mean_return * 100).toFixed(2)}%`"
              :trend="result.period_analysis['20d'].mean_return > 0 ? 'up' : 'down'"
            />
          </el-col>
          <el-col :xs="12" :sm="6">
            <metric-card
              :label="$t('periodAnalysis.confidence')"
              :value="`${(result.period_analysis['20d'].confidence * 100).toFixed(1)}%`"
            />
          </el-col>
          <el-col :xs="12" :sm="6">
            <metric-card
              v-if="result.period_analysis['20d'].position_advice"
              :label="$t('periodAnalysis.recommendedPosition')"
              :value="`${(result.period_analysis['20d'].position_advice.recommended_position * 100).toFixed(1)}%`"
            />
          </el-col>
        </el-row>

        <el-alert
          v-if="result.period_analysis['20d'].position_advice"
          :title="result.period_analysis['20d'].position_advice.signal"
          :description="result.period_analysis['20d'].position_advice.description"
          :type="getAlertType(result.period_analysis['20d'].position_advice.signal)"
          show-icon
          :closable="false"
          style="margin-top: 20px"
        />
      </el-card>

      <!-- Phase 3 深度分析 -->
      <div v-if="result.phase3_analysis" class="phase3-section">
        <el-divider content-position="left">
          <span style="font-size: 18px; font-weight: 600">
            🚀 {{ $t('phase3.title') }}
          </span>
        </el-divider>

        <!-- VIX分析 -->
        <el-card v-if="result.phase3_analysis.vix" class="analysis-card" shadow="hover">
          <template #header>
            <span class="card-title">
              <el-icon><Orange /></el-icon>
              🔥 {{ $t('phase3.vix') }}
            </span>
          </template>

          <el-descriptions :column="2" border>
            <el-descriptions-item :label="$t('vixAnalysis.currentValue')">
              {{ result.phase3_analysis.vix.current_state.vix_value.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item :label="$t('vixAnalysis.status')">
              <el-tag>{{ result.phase3_analysis.vix.current_state.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('vixAnalysis.change')">
              <span :style="{ color: result.phase3_analysis.vix.current_state.change_pct < 0 ? '#67c23a' : '#f56c6c' }">
                {{ result.phase3_analysis.vix.current_state.change_pct.toFixed(2) }}%
              </span>
            </el-descriptions-item>
            <el-descriptions-item v-if="result.phase3_analysis.vix.current_state.week_change_pct" :label="$t('vixAnalysis.weekChange')">
              <span :style="{ color: result.phase3_analysis.vix.current_state.week_change_pct < 0 ? '#67c23a' : '#f56c6c' }">
                {{ result.phase3_analysis.vix.current_state.week_change_pct.toFixed(2) }}%
              </span>
            </el-descriptions-item>
          </el-descriptions>

          <el-alert
            v-if="result.phase3_analysis.vix.signal"
            :title="result.phase3_analysis.vix.signal.signal"
            :description="`${result.phase3_analysis.vix.signal.description}\n${result.phase3_analysis.vix.signal.action}`"
            type="info"
            show-icon
            :closable="false"
            style="margin-top: 16px"
          />
        </el-card>

        <!-- 行业轮动 -->
        <el-card v-if="result.phase3_analysis.sector_rotation" class="analysis-card" shadow="hover">
          <template #header>
            <span class="card-title">
              <el-icon><Refresh /></el-icon>
              🔄 {{ $t('phase3.sector') }}
            </span>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item :label="$t('sectorAnalysis.rotationPattern')">
              <el-tag type="success">
                {{ result.phase3_analysis.sector_rotation.rotation_pattern.pattern }}
              </el-tag>
              - {{ result.phase3_analysis.sector_rotation.rotation_pattern.description }}
            </el-descriptions-item>
            <el-descriptions-item :label="$t('sectorAnalysis.allocation')">
              {{ result.phase3_analysis.sector_rotation.allocation_recommendation.recommendation }}
            </el-descriptions-item>
            <el-descriptions-item
              v-if="result.phase3_analysis.sector_rotation.allocation_recommendation.recommended_sectors"
              :label="$t('sectorAnalysis.recommendedSectors')"
            >
              <el-tag
                v-for="sector in result.phase3_analysis.sector_rotation.allocation_recommendation.recommended_sectors"
                :key="sector"
                type="primary"
                style="margin-right: 8px"
              >
                {{ sector }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 成交量分析 -->
        <el-card v-if="result.phase3_analysis.volume" class="analysis-card" shadow="hover">
          <template #header>
            <span class="card-title">
              <el-icon><Histogram /></el-icon>
              📊 {{ $t('phase3.volume') }}
            </span>
          </template>

          <el-descriptions :column="2" border>
            <el-descriptions-item :label="$t('volumeAnalysis.status')">
              <el-tag>{{ result.phase3_analysis.volume.volume_status.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="result.phase3_analysis.volume.volume_status.volume_ratio" :label="$t('volumeAnalysis.ratio')">
              {{ result.phase3_analysis.volume.volume_status.volume_ratio.toFixed(2) }}倍
            </el-descriptions-item>
            <el-descriptions-item :label="$t('volumeAnalysis.priceVolumeRelation')" :span="2">
              {{ result.phase3_analysis.volume.price_volume_relationship.pattern }} -
              {{ result.phase3_analysis.volume.price_volume_relationship.description }}
            </el-descriptions-item>
          </el-descriptions>

          <el-alert
            v-if="result.phase3_analysis.volume.signal"
            :title="result.phase3_analysis.volume.signal.signal"
            :description="result.phase3_analysis.volume.signal.description"
            type="info"
            show-icon
            :closable="false"
            style="margin-top: 16px"
          />
        </el-card>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-else :description="$t('indexAnalysis.analyzing')" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useMarketStore } from '@/stores/market'
import MetricCard from '@/components/cards/MetricCard.vue'
import type { SingleIndexAnalysis, IndexInfo } from '@/types'

const marketStore = useMarketStore()

// 表单数据
const formData = ref({
  selectedIndex: 'SPX',
  phase: '3',
  tolerance: 0.05,
})

// 数据
const indices = ref<IndexInfo[]>([])
const result = ref<SingleIndexAnalysis | null>(null)
const analyzing = ref(false)

// 周期表格数据
const periodTableData = computed(() => {
  if (!result.value?.period_analysis) return []

  return Object.entries(result.value.period_analysis).map(([key, stats]) => ({
    period: key.replace('d', '日'),
    sampleSize: stats.sample_size,
    upProb: `${(stats.up_prob * 100).toFixed(1)}%`,
    meanReturn: `${(stats.mean_return * 100).toFixed(2)}%`,
    medianReturn: `${(stats.median_return * 100).toFixed(2)}%`,
    confidence: `${(stats.confidence * 100).toFixed(1)}%`,
    recommendedPosition: stats.position_advice
      ? `${(stats.position_advice.recommended_position * 100).toFixed(1)}%`
      : '-',
    signal: stats.position_advice?.signal || '-',
  }))
})

// 获取环境类型标签
const getEnvironmentType = (env: string) => {
  if (env.includes('牛市')) return 'success'
  if (env.includes('熊市')) return 'danger'
  return 'info'
}

// 获取Alert类型
const getAlertType = (signal: string) => {
  if (signal.includes('买入')) return 'success'
  if (signal.includes('卖出') || signal.includes('减仓')) return 'danger'
  if (signal.includes('观望') || signal.includes('谨慎')) return 'warning'
  return 'info'
}

// 执行分析
const handleAnalyze = async () => {
  try {
    analyzing.value = true
    result.value = null

    const res = await marketStore.analyzeSingle(formData.value.selectedIndex)
    result.value = res
  } catch (error) {
    console.error('分析失败:', error)
  } finally {
    analyzing.value = false
  }
}

// 初始化
onMounted(async () => {
  try {
    indices.value = await marketStore.fetchIndices()
  } catch (error) {
    console.error('获取指数列表失败:', error)
  }
})
</script>

<style scoped>
.index-analysis {
  width: 100%;
}

.config-card {
  margin-bottom: 20px;
}

.metric-row {
  margin-bottom: 20px;
}

.analysis-card {
  margin-bottom: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.conclusion-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.conclusion-card :deep(.el-card__header) {
  border-bottom-color: rgba(255, 255, 255, 0.2);
}

.conclusion-card .card-title {
  color: white;
}

.phase3-section {
  margin-top: 20px;
}

/* 动画效果 */
@keyframes slide-in {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.analysis-card,
.conclusion-card {
  animation: slide-in 0.5s ease-out backwards;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.analysis-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

.result-section .analysis-card:nth-child(1) {
  animation-delay: 0.1s;
}

.result-section .analysis-card:nth-child(2) {
  animation-delay: 0.2s;
}

.result-section .analysis-card:nth-child(3) {
  animation-delay: 0.3s;
}

.phase3-section .analysis-card:nth-child(1) {
  animation-delay: 0.4s;
}

.phase3-section .analysis-card:nth-child(2) {
  animation-delay: 0.5s;
}

.phase3-section .analysis-card:nth-child(3) {
  animation-delay: 0.6s;
}

@media (max-width: 768px) {
  .config-card :deep(.el-form) {
    .el-form-item {
      margin-bottom: 15px;
    }

    .el-form--inline .el-form-item {
      display: block;
      margin-right: 0;
    }

    .el-select,
    .el-input-number {
      width: 100% !important;
    }
  }

  .card-title {
    font-size: 14px;
  }

  .result-section {
    .el-descriptions {
      font-size: 13px;
    }

    .el-table {
      font-size: 12px;
    }
  }

  .conclusion-card :deep(.el-alert) {
    font-size: 13px;
  }

  .phase3-section {
    .el-divider__text {
      font-size: 16px !important;
    }
  }
}
</style>
