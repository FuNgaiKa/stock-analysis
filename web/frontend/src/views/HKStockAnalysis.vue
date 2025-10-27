<template>
  <div class="hk-stock-analysis fade-in">
    <el-card class="header-card" shadow="never">
      <div class="page-header">
        <div>
          <h1 class="gradient-text">🇭🇰 港股市场分析</h1>
          <p v-if="lastRefreshTime" class="last-update">
            最后更新: {{ formatTime(lastRefreshTime) }}
          </p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="refreshData" :loading="loading" circle>
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 加载动画 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
      <el-skeleton :rows="3" animated style="margin-top: 20px" />
    </div>

    <!-- 市场概览 -->
    <transition name="fade-slide" mode="out-in">
      <div v-if="marketData && !loading" class="content-section">
        <!-- 主要指数 -->
        <el-row :gutter="20" class="metric-row">
          <el-col
            :xs="24"
            :sm="12"
            :md="8"
            v-for="(index, key) in mainIndices"
            :key="key"
          >
            <el-card class="index-card hover-lift modern-card" shadow="hover">
              <div class="index-header">
                <div class="index-info">
                  <h3>{{ index.name }}</h3>
                  <el-tag size="small" type="info">{{ key }}</el-tag>
                </div>
                <el-icon :size="32" :color="index.change_pct >= 0 ? '#67c23a' : '#f56c6c'">
                  <TrendCharts />
                </el-icon>
              </div>

              <el-divider style="margin: 15px 0" />

              <div class="index-stats">
                <div class="stat-item">
                  <span class="stat-label">当前点位</span>
                  <span class="stat-value">{{ index.price.toFixed(2) }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">涨跌幅</span>
                  <span
                    class="stat-value"
                    :style="{ color: index.change_pct >= 0 ? '#67c23a' : '#f56c6c' }"
                  >
                    {{ index.change_pct >= 0 ? '+' : '' }}{{ index.change_pct.toFixed(2) }}%
                  </span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">更新时间</span>
                  <span class="stat-value small">{{ index.date }}</span>
                </div>
              </div>

              <div class="index-trend">
                <el-progress
                  :percentage="getTrendPercentage(index.change_pct)"
                  :color="index.change_pct >= 0 ? '#67c23a' : '#f56c6c'"
                  :show-text="false"
                />
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 市场统计与分析 -->
        <el-row :gutter="20" class="stats-row">
          <!-- 市场热度 -->
          <el-col :xs="24" :md="12">
            <el-card class="stats-card modern-card" shadow="hover">
              <template #header>
                <span class="card-title">
                  <el-icon><Compass /></el-icon>
                  市场热度分析
                </span>
              </template>

              <div v-if="marketData.heat_analysis" class="heat-analysis">
                <div class="heat-score">
                  <el-progress
                    type="dashboard"
                    :percentage="marketData.heat_analysis.heat_score * 10"
                    :color="getHeatColor(marketData.heat_analysis.heat_score)"
                    :width="180"
                  >
                    <template #default="{ percentage }">
                      <span class="percentage-value">{{ marketData.heat_analysis.heat_score.toFixed(1) }}</span>
                      <span class="percentage-label">热度评分</span>
                    </template>
                  </el-progress>
                </div>

                <el-divider />

                <div class="heat-details">
                  <div class="detail-item">
                    <el-tag :type="getRiskLevelType(marketData.heat_analysis.risk_level)" size="large">
                      {{ marketData.heat_analysis.risk_level }}
                    </el-tag>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">仓位建议:</span>
                    <span class="detail-value">{{ marketData.heat_analysis.position_suggestion }}</span>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>

          <!-- 市场指标 -->
          <el-col :xs="24" :md="12">
            <el-card class="stats-card modern-card" shadow="hover">
              <template #header>
                <span class="card-title">
                  <el-icon><DataLine /></el-icon>
                  关键指标
                </span>
              </template>

              <div v-if="marketData.heat_analysis" class="indicators-grid">
                <div
                  class="indicator-item"
                  v-for="(value, key) in marketData.heat_analysis.indicators"
                  :key="key"
                >
                  <div class="indicator-name">{{ formatIndicatorName(key) }}</div>
                  <div class="indicator-value">{{ formatIndicatorValue(value) }}</div>
                  <el-progress
                    :percentage="normalizeIndicator(value) * 100"
                    :show-text="false"
                    :color="getIndicatorColor(value)"
                  />
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 市场概况 -->
        <el-card class="summary-card modern-card" shadow="hover">
          <template #header>
            <span class="card-title">
              <el-icon><Histogram /></el-icon>
              市场概况
            </span>
          </template>

          <el-row :gutter="20" v-if="marketData.heat_analysis?.market_data_summary">
            <el-col :xs="12" :sm="6">
              <el-statistic title="恒指涨跌幅" :value="parseFloat(marketData.heat_analysis.market_data_summary.hsi_change || '0')" :precision="2" suffix="%">
                <template #prefix>
                  <el-icon><TrendCharts /></el-icon>
                </template>
              </el-statistic>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-statistic title="涨停股票" :value="marketData.heat_analysis.market_data_summary.limit_up_count || 0">
                <template #prefix>
                  <el-icon color="#67c23a"><CaretTop /></el-icon>
                </template>
              </el-statistic>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-statistic title="跌停股票" :value="marketData.heat_analysis.market_data_summary.limit_down_count || 0">
                <template #prefix>
                  <el-icon color="#f56c6c"><CaretBottom /></el-icon>
                </template>
              </el-statistic>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-statistic title="活跃股票" :value="marketData.heat_analysis.market_data_summary.active_stocks || 0">
                <template #prefix>
                  <el-icon><Opportunity /></el-icon>
                </template>
              </el-statistic>
            </el-col>
          </el-row>
        </el-card>

        <!-- 涨跌分布 -->
        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :xs="24" :md="12">
            <el-card class="chart-card modern-card" shadow="hover">
              <template #header>
                <span class="card-title">
                  <el-icon><PieChart /></el-icon>
                  指数涨跌分布
                </span>
              </template>
              <pie-chart
                v-if="pieChartData.length > 0"
                :data="pieChartData"
                height="300px"
                :radius="['40%', '70%']"
              />
            </el-card>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-card class="chart-card modern-card" shadow="hover">
              <template #header>
                <span class="card-title">
                  <el-icon><Histogram /></el-icon>
                  指数涨跌幅排行
                </span>
              </template>
              <bar-chart
                v-if="barChartData.length > 0"
                :data="barChartData"
                height="300px"
                :horizontal="true"
              />
            </el-card>
          </el-col>
        </el-row>

        <!-- 操作建议 -->
        <el-card class="advice-card modern-card" shadow="hover" style="margin-top: 20px">
          <template #header>
            <span class="card-title">
              <el-icon><ChatLineSquare /></el-icon>
              操作建议
            </span>
          </template>

          <el-alert
            :title="getAdviceTitle()"
            :type="getAdviceType()"
            :description="getAdviceDescription()"
            show-icon
            :closable="false"
          />
        </el-card>
      </div>
    </transition>

    <!-- 空数据状态 -->
    <el-empty v-if="!loading && !marketData" description="暂无市场数据" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

const loading = ref(false)
const marketData = ref<any>(null)

// 主要指数
const mainIndices = computed(() => {
  if (!marketData.value) return {}
  const { HSI, HSCEI, HSTECH } = marketData.value
  return { HSI, HSCEI, HSTECH }
})

// 获取市场数据
const fetchMarketData = async () => {
  try {
    loading.value = true
    const response = await fetch('http://localhost:8000/api/hk/market-analysis')
    const result = await response.json()

    if (result.success) {
      marketData.value = result.data
    } else {
      ElMessage.error('获取港股市场数据失败')
    }
  } catch (error) {
    console.error('获取港股市场数据失败:', error)
    ElMessage.error('获取港股市场数据失败')
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  fetchMarketData()
  ElMessage.success('数据刷新中...')
}

// 获取趋势百分比
const getTrendPercentage = (changePct: number) => {
  const normalized = ((changePct + 10) / 20) * 100
  return Math.max(0, Math.min(100, normalized))
}

// 获取热度颜色
const getHeatColor = (score: number) => {
  if (score >= 8) return '#f56c6c'
  if (score >= 6) return '#e6a23c'
  if (score >= 4) return '#409eff'
  return '#67c23a'
}

// 获取风险等级类型
const getRiskLevelType = (level: string) => {
  const typeMap: Record<string, any> = {
    '极高风险': 'danger',
    '高风险': 'warning',
    '中等风险': 'info',
    '低风险': 'success',
  }
  return typeMap[level] || 'info'
}

// 格式化指标名称
const formatIndicatorName = (key: string) => {
  const nameMap: Record<string, string> = {
    volume_ratio: '成交量比率',
    price_momentum: '价格动量',
    market_breadth: '市场广度',
    volatility: '波动率',
    sentiment: '情绪指标',
  }
  return nameMap[key] || key
}

// 格式化指标值
const formatIndicatorValue = (value: number) => {
  return value.toFixed(4)
}

// 归一化指标值
const normalizeIndicator = (value: number) => {
  return Math.min(1, Math.max(0, value))
}

// 获取指标颜色
const getIndicatorColor = (value: number) => {
  if (value >= 0.8) return '#f56c6c'
  if (value >= 0.6) return '#e6a23c'
  if (value >= 0.4) return '#409eff'
  return '#67c23a'
}

// 饼图数据
const pieChartData = computed(() => {
  const indices = Object.values(mainIndices.value) as any[]
  if (indices.length === 0) return []

  const upCount = indices.filter((item: any) => item.change_pct > 0).length
  const downCount = indices.filter((item: any) => item.change_pct < 0).length
  const flatCount = indices.length - upCount - downCount

  return [
    { name: '上涨', value: upCount, color: '#67c23a' },
    { name: '下跌', value: downCount, color: '#f56c6c' },
    { name: '平盘', value: flatCount, color: '#909399' },
  ].filter((item) => item.value > 0)
})

// 柱状图数据
const barChartData = computed(() => {
  const indices = Object.entries(mainIndices.value).map(([code, data]: [string, any]) => ({
    name: data.name,
    value: data.change_pct,
    color: data.change_pct >= 0 ? '#67c23a' : '#f56c6c',
  }))

  return indices.sort((a, b) => b.value - a.value)
})

// 获取操作建议标题
const getAdviceTitle = () => {
  if (!marketData.value?.heat_analysis) return '暂无建议'
  const score = marketData.value.heat_analysis.heat_score
  if (score >= 8) return '市场过热,建议谨慎'
  if (score >= 6) return '市场活跃,注意风险'
  if (score >= 4) return '市场正常,可适度参与'
  return '市场低迷,寻找机会'
}

// 获取操作建议类型
const getAdviceType = () => {
  if (!marketData.value?.heat_analysis) return 'info'
  const score = marketData.value.heat_analysis.heat_score
  if (score >= 8) return 'error'
  if (score >= 6) return 'warning'
  if (score >= 4) return 'success'
  return 'info'
}

// 获取操作建议描述
const getAdviceDescription = () => {
  if (!marketData.value?.heat_analysis) return ''
  const { risk_level, position_suggestion } = marketData.value.heat_analysis
  return `当前风险等级为${risk_level},建议仓位: ${position_suggestion}。请根据自身风险承受能力做出投资决策。`
}

// 格式化时间
const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)

  if (seconds < 60) return `${seconds}秒前`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟前`

  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 自动刷新
const { lastRefreshTime } = useAutoRefresh({
  onRefresh: fetchMarketData,
  interval: 60000,
  immediate: true,
  enabled: true,
})
</script>

<style scoped>
.hk-stock-analysis {
  width: 100%;
}

.header-card {
  margin-bottom: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.page-header h1 {
  margin: 0 0 5px 0;
  font-size: 28px;
  font-weight: 700;
}

.last-update {
  margin: 0;
  font-size: 13px;
  color: var(--text-tertiary);
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.loading-container {
  padding: 20px 0;
}

.content-section {
  animation: fade-in 0.5s ease-out;
}

.metric-row,
.stats-row {
  margin-bottom: 20px;
}

.index-card {
  height: 100%;
}

.index-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.index-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.index-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-value.small {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-tertiary);
}

.index-trend {
  margin-top: 15px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.heat-analysis {
  text-align: center;
}

.heat-score {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.percentage-value {
  display: block;
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}

.percentage-label {
  display: block;
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.heat-details {
  padding: 20px 0;
}

.detail-item {
  margin: 15px 0;
}

.detail-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-right: 8px;
}

.detail-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.indicators-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.indicator-item {
  padding: 10px 0;
}

.indicator-name {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.indicator-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .page-header h1 {
    font-size: 24px;
  }
}
</style>
