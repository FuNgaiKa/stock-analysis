<template>
  <div class="vix-analysis">
    <el-card class="header-card" shadow="never">
      <div class="page-header">
        <h1>🔥 {{ $t('vixAnalysis.title') }}</h1>
        <el-button type="primary" @click="fetchVixData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          {{ $t('header.refresh') }}
        </el-button>
      </div>
    </el-card>

    <div v-if="vixData" class="content-section">
      <!-- 当前状态 -->
      <el-row :gutter="20" class="metric-row">
        <el-col :xs="12" :sm="6">
          <metric-card
            :label="$t('vixAnalysis.currentValue')"
            :value="vixData.current_state.vix_value.toFixed(2)"
            :change="vixData.current_state.change_pct"
          />
        </el-col>
        <el-col :xs="12" :sm="6">
          <metric-card
            :label="$t('vixAnalysis.status')"
            :value="vixData.current_state.status"
          />
        </el-col>
        <el-col :xs="12" :sm="6">
          <metric-card
            :label="$t('vixAnalysis.change')"
            :value="`${vixData.current_state.change_pct.toFixed(2)}%`"
            :trend="vixData.current_state.change_pct < 0 ? 'up' : 'down'"
          />
        </el-col>
        <el-col v-if="vixData.current_state.week_change_pct" :xs="12" :sm="6">
          <metric-card
            :label="$t('vixAnalysis.weekChange')"
            :value="`${vixData.current_state.week_change_pct.toFixed(2)}%`"
            :trend="vixData.current_state.week_change_pct < 0 ? 'up' : 'down'"
          />
        </el-col>
      </el-row>

      <!-- 历史走势图 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><TrendCharts /></el-icon>
            VIX历史走势
          </span>
        </template>
        <line-chart
          v-if="vixHistoryData.length > 0"
          :data="vixHistoryData"
          :loading="loading"
          height="400px"
          title="VIX恐慌指数"
          x-field="date"
          y-field="value"
        />
      </el-card>

      <!-- VIX分位数 -->
      <el-card v-if="vixData.percentiles" class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><DataAnalysis /></el-icon>
            VIX分位数分析
          </span>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="30天分位数">
            {{ vixData.percentiles['30d'].toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item label="60天分位数">
            {{ vixData.percentiles['60d'].toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item label="1年分位数">
            {{ vixData.percentiles['252d'].toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item label="5年分位数">
            {{ vixData.percentiles['1260d'].toFixed(1) }}%
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <bar-chart
          v-if="percentileChartData.length > 0"
          :data="percentileChartData"
          height="300px"
          title="VIX分位数分布"
        />
      </el-card>

      <!-- VIX-SPX相关性 -->
      <el-card v-if="vixData.correlation" class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><Connection /></el-icon>
            VIX-SPX相关性分析
          </span>
        </template>

        <el-statistic
          title="相关系数"
          :value="vixData.correlation.correlation_coef"
          :precision="2"
        >
          <template #suffix>
            <span :style="{ color: vixData.correlation.correlation_coef < 0 ? '#67c23a' : '#f56c6c' }">
              ({{ vixData.correlation.correlation_coef < -0.5 ? '强负相关' : '负相关' }})
            </span>
          </template>
        </el-statistic>

        <el-divider />

        <p style="color: #606266; line-height: 1.8">
          VIX与SPX呈现
          <strong>{{ Math.abs(vixData.correlation.correlation_coef) > 0.7 ? '强' : '' }}负相关</strong>关系。
          当VIX上升时，市场通常下跌；当VIX下降时，市场通常上涨。
          相关系数为 <strong>{{ vixData.correlation.correlation_coef.toFixed(2) }}</strong>，
          说明两者关系{{ Math.abs(vixData.correlation.correlation_coef) > 0.7 ? '非常密切' : '较为密切' }}。
        </p>
      </el-card>

      <!-- 交易信号 -->
      <el-card class="signal-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><Bell /></el-icon>
            {{ $t('vixAnalysis.signal') }}
          </span>
        </template>

        <el-alert
          :title="vixData.signal.signal"
          :description="`${vixData.signal.description}\n\n${vixData.signal.action}`"
          :type="getAlertType(vixData.signal.signal)"
          show-icon
          :closable="false"
        />
      </el-card>

      <!-- VIX解读指南 -->
      <el-card class="guide-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><Document /></el-icon>
            VIX解读指南
          </span>
        </template>

        <el-timeline>
          <el-timeline-item
            v-for="(item, index) in vixGuide"
            :key="index"
            :icon="item.icon"
            :type="item.type"
            :color="item.color"
          >
            <h4>{{ item.title }}</h4>
            <p>{{ item.description }}</p>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>

    <el-empty v-else :description="$t('common.loading')" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { marketApi } from '@/services/api'
import MetricCard from '@/components/cards/MetricCard.vue'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const loading = ref(false)
const vixData = ref<any>(null)

// VIX历史数据
const vixHistoryData = computed(() => {
  if (!vixData.value?.history) return []
  return vixData.value.history.map((item: any) => ({
    date: item.date,
    value: item.vix,
  }))
})

// 分位数图表数据
const percentileChartData = computed(() => {
  if (!vixData.value?.percentiles) return []
  return [
    { name: '30天', value: vixData.value.percentiles['30d'], color: '#1890ff' },
    { name: '60天', value: vixData.value.percentiles['60d'], color: '#52c41a' },
    { name: '1年', value: vixData.value.percentiles['252d'], color: '#faad14' },
    { name: '5年', value: vixData.value.percentiles['1260d'], color: '#f5222d' },
  ]
})

// VIX解读指南
const vixGuide = [
  {
    icon: 'WarningFilled',
    type: 'danger',
    color: '#f5222d',
    title: 'VIX > 30 - 极度恐慌',
    description: '市场处于极度恐慌状态，通常出现在重大危机时期。历史上这种情况较少，但往往是买入机会。',
  },
  {
    icon: 'Warning',
    type: 'warning',
    color: '#faad14',
    title: 'VIX 25-30 - 恐慌上升',
    description: '市场担忧情绪较高，波动性显著增加。需要谨慎操作，但也可能是逢低布局的时机。',
  },
  {
    icon: 'CircleCheck',
    type: 'success',
    color: '#52c41a',
    title: 'VIX 15-20 - 正常区间',
    description: '市场波动性处于正常水平，投资者情绪相对平稳。这是市场的常态。',
  },
  {
    icon: 'InfoFilled',
    type: 'info',
    color: '#1890ff',
    title: 'VIX < 15 - 过度乐观',
    description: '市场过于平静，投资者可能过度乐观。历史上VIX极低后往往会出现反弹，需要警惕风险。',
  },
]

// 获取Alert类型
const getAlertType = (signal: string) => {
  if (signal.includes('极度恐慌') || signal.includes('恐慌')) return 'warning'
  if (signal.includes('正常')) return 'success'
  if (signal.includes('乐观')) return 'info'
  return 'info'
}

// 获取VIX数据
const fetchVixData = async () => {
  try {
    loading.value = true
    const response = await fetch('http://localhost:8000/api/vix/current')
    const result = await response.json()
    vixData.value = result.data
  } catch (error) {
    console.error('获取VIX数据失败:', error)
    ElMessage.error('获取VIX数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchVixData()
})
</script>

<style scoped>
.vix-analysis {
  width: 100%;
}

.header-card {
  margin-bottom: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.metric-row {
  margin-bottom: 20px;
}

.chart-card,
.signal-card,
.guide-card {
  margin-bottom: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .page-header h1 {
    font-size: 20px;
  }

  .card-title {
    font-size: 14px;
  }
}
</style>
