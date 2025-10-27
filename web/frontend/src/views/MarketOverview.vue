<template>
  <div class="market-overview fade-in">
    <el-card class="header-card" shadow="never">
      <div class="page-header">
        <div>
          <h1 class="gradient-text">🌍 全球市场概览</h1>
          <p v-if="lastRefreshTime" class="last-update">
            最后更新: {{ formatTime(lastRefreshTime) }}
          </p>
        </div>
        <div class="header-actions">
          <market-selector v-model="selectedMarket" @change="handleMarketChange" />
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

    <!-- 实时数据组件 -->
    <real-time-data v-if="!loading" />

    <!-- 市场指标卡片 -->
    <transition name="fade-slide" mode="out-in">
      <div v-if="marketData && !loading" class="content-section" :key="selectedMarket">
      <el-row :gutter="20" class="metric-row">
        <el-col
          :xs="24"
          :sm="getColSpan(marketIndices.length).sm"
          :md="getColSpan(marketIndices.length).md"
          :lg="getColSpan(marketIndices.length).lg"
          v-for="(item, index) in marketIndices"
          :key="item.code"
          class="slide-in"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <el-card
            class="index-card hover-lift modern-card clickable-card"
            shadow="hover"
            @click="handleIndexClick(item.code)"
          >
            <div class="index-header">
              <div class="index-info">
                <h3>{{ item.name }}</h3>
                <el-tag size="small" type="info">{{ item.code }}</el-tag>
              </div>
              <el-icon :size="32" :color="item.change_pct >= 0 ? '#67c23a' : '#f56c6c'">
                <TrendCharts />
              </el-icon>
            </div>

            <el-divider style="margin: 15px 0" />

            <div class="index-stats">
              <div class="stat-item">
                <span class="stat-label">当前点位</span>
                <span class="stat-value">{{ item.price.toFixed(2) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">涨跌幅</span>
                <span
                  class="stat-value"
                  :style="{ color: item.change_pct >= 0 ? '#67c23a' : '#f56c6c' }"
                >
                  {{ item.change_pct >= 0 ? '+' : '' }}{{ item.change_pct.toFixed(2) }}%
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">更新时间</span>
                <span class="stat-value small">{{ item.date }}</span>
              </div>
            </div>

            <div class="index-trend">
              <el-progress
                :percentage="getTrendPercentage(item.change_pct)"
                :color="item.change_pct >= 0 ? '#67c23a' : '#f56c6c'"
                :show-text="false"
              />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 市场统计 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :xs="24" :md="12">
          <el-card class="stats-card modern-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon><DataLine /></el-icon>
                市场统计
              </span>
            </template>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-statistic title="上涨指数" :value="marketStats.upCount">
                  <template #prefix>
                    <el-icon color="#67c23a"><CaretTop /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="12">
                <el-statistic title="下跌指数" :value="marketStats.downCount">
                  <template #prefix>
                    <el-icon color="#f56c6c"><CaretBottom /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="12" style="margin-top: 20px">
                <el-statistic title="平均涨跌" :value="marketStats.avgChange" :precision="2" suffix="%">
                  <template #prefix>
                    <el-icon><TrendCharts /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="12" style="margin-top: 20px">
                <el-statistic title="总指数数" :value="marketStats.totalCount">
                  <template #prefix>
                    <el-icon><Grid /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>
          </el-card>
        </el-col>

        <!-- 涨跌分布饼图 -->
        <el-col :xs="24" :md="12">
          <el-card class="chart-card modern-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon><PieChart /></el-icon>
                涨跌分布
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
      </el-row>

      <!-- 指数涨跌幅排行 -->
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
          height="400px"
          :horizontal="true"
        />
      </el-card>

      <!-- 快速操作 -->
      <el-card class="actions-card modern-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><Operation /></el-icon>
            快速操作
          </span>
        </template>

        <el-space wrap :size="15">
          <el-button type="primary" @click="goToAnalysis">
            <el-icon><TrendCharts /></el-icon>
            深度分析
          </el-button>
          <el-button type="success" @click="goToVix">
            <el-icon><Orange /></el-icon>
            VIX恐慌指数
          </el-button>
          <el-button type="warning" @click="goToSector">
            <el-icon><Refresh /></el-icon>
            行业轮动
          </el-button>
          <el-button type="info" @click="goToBacktest">
            <el-icon><DataAnalysis /></el-icon>
            策略回测
          </el-button>
        </el-space>
      </el-card>
    </div>
    </transition>

    <!-- 空数据状态 -->
    <el-empty v-if="!loading && !marketData" description="暂无市场数据" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import MarketSelector from '@/components/common/MarketSelector.vue'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import RealTimeData from '@/components/RealTimeData.vue'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

const router = useRouter()
const loading = ref(false)
const selectedMarket = ref('US')
const marketData = ref<any>(null)

// 根据指数数量动态调整列宽
const getColSpan = (count: number) => {
  if (count <= 2) {
    // 1-2个指数：每行2个
    return { sm: 12, md: 12, lg: 12 }
  } else if (count <= 3) {
    // 3个指数：每行3个
    return { sm: 12, md: 8, lg: 8 }
  } else if (count <= 4) {
    // 4个指数：每行4个
    return { sm: 12, md: 6, lg: 6 }
  } else {
    // 5个及以上：每行3个
    return { sm: 12, md: 8, lg: 8 }
  }
}

// 市场指数列表
const marketIndices = computed(() => {
  if (!marketData.value) return []
  return Object.entries(marketData.value).map(([code, data]: [string, any]) => ({
    code,
    ...data,
  }))
})

// 市场统计
const marketStats = computed(() => {
  const indices = marketIndices.value
  if (indices.length === 0) {
    return { upCount: 0, downCount: 0, avgChange: 0, totalCount: 0 }
  }

  const upCount = indices.filter((item: any) => item.change_pct > 0).length
  const downCount = indices.filter((item: any) => item.change_pct < 0).length
  const avgChange = indices.reduce((sum: number, item: any) => sum + item.change_pct, 0) / indices.length

  return {
    upCount,
    downCount,
    avgChange,
    totalCount: indices.length,
  }
})

// 获取趋势百分比（用于进度条）
const getTrendPercentage = (changePct: number) => {
  // 将-10%到+10%映射到0-100
  const normalized = ((changePct + 10) / 20) * 100
  return Math.max(0, Math.min(100, normalized))
}

// 饼图数据 - 涨跌分布
const pieChartData = computed(() => {
  const stats = marketStats.value
  return [
    {
      name: '上涨',
      value: stats.upCount,
      color: '#67c23a',
    },
    {
      name: '下跌',
      value: stats.downCount,
      color: '#f56c6c',
    },
    {
      name: '平盘',
      value: Math.max(0, stats.totalCount - stats.upCount - stats.downCount),
      color: '#909399',
    },
  ].filter(item => item.value > 0)
})

// 柱状图数据 - 按涨跌幅排序
const barChartData = computed(() => {
  const indices = marketIndices.value
  if (indices.length === 0) return []

  return indices
    .map((item: any) => ({
      name: item.name,
      value: item.change_pct,
      color: item.change_pct >= 0 ? '#67c23a' : '#f56c6c',
    }))
    .sort((a, b) => b.value - a.value)
})

// 获取市场数据
const fetchMarketData = async () => {
  try {
    loading.value = true
    const apiMap: Record<string, string> = {
      US: '/api/current-positions',
      HK: '/api/hk/current-positions',
      CN: '/api/cn/current-positions',
    }

    const response = await fetch(`http://localhost:8000${apiMap[selectedMarket.value]}`)
    const result = await response.json()

    if (result.success) {
      marketData.value = result.data
    } else {
      ElMessage.error('获取市场数据失败')
    }
  } catch (error) {
    console.error('获取市场数据失败:', error)
    ElMessage.error('获取市场数据失败')
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  fetchMarketData()
  ElMessage.success('数据刷新中...')
}

// 市场切换
const handleMarketChange = (market: string) => {
  selectedMarket.value = market
  fetchMarketData()
}

// 快速导航
const goToAnalysis = () => router.push('/index-analysis')
const goToVix = () => router.push('/vix-analysis')
const goToSector = () => router.push('/sector-rotation')
const goToBacktest = () => router.push('/backtest')

// 点击指数卡片，跳转到详细分析
const handleIndexClick = (code: string) => {
  ElMessage.info(`点击了 ${code}，跳转到深度分析页面`)
  router.push('/index-analysis')
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
    minute: '2-digit'
  })
}

// 自动刷新功能
const { lastRefreshTime } = useAutoRefresh({
  onRefresh: fetchMarketData,
  interval: 60000, // 60秒刷新一次
  immediate: true,
  enabled: true,
})
</script>

<style scoped>
.market-overview {
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
  font-weight: 400;
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

/* Transition 动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.metric-row,
.stats-row {
  margin-bottom: 20px;
}

.index-card {
  height: 100%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.clickable-card {
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.clickable-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.clickable-card:hover::before {
  left: 100%;
}

.clickable-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.clickable-card:active {
  transform: translateY(-4px) scale(1.01);
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
  color: var(--text-primary);
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

.stats-card,
.actions-card {
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
    align-items: flex-start;
  }

  .page-header h1 {
    font-size: 24px;
  }
}
</style>
