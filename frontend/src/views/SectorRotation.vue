<template>
  <div class="sector-rotation">
    <el-card class="header-card" shadow="never">
      <div class="page-header">
        <h1>🔄 {{ $t('sectorAnalysis.title') }}</h1>
        <el-button type="primary" @click="fetchSectorData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          {{ $t('header.refresh') }}
        </el-button>
      </div>
    </el-card>

    <div v-if="sectorData" class="content-section">
      <!-- 轮动模式 -->
      <el-card class="pattern-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><Compass /></el-icon>
            {{ $t('sectorAnalysis.rotationPattern') }}
          </span>
        </template>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-statistic
              :title="$t('sectorAnalysis.rotationPattern')"
              :value="sectorData.rotation_pattern.pattern"
            >
              <template #prefix>
                <el-icon :color="getPatternColor(sectorData.rotation_pattern.pattern)">
                  <TrendCharts />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="12">
            <p style="color: #606266; line-height: 1.8; margin-top: 10px">
              {{ sectorData.rotation_pattern.description }}
            </p>
          </el-col>
        </el-row>
      </el-card>

      <!-- 行业雷达图 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><Radar /></el-icon>
            {{ $t('sectorAnalysis.sectorPerformance') }}
          </span>
        </template>

        <radar-chart
          v-if="radarChartData.length > 0"
          :data="radarChartData"
          height="500px"
          title="行业相对强度雷达图"
          :max-value="100"
        />
      </el-card>

      <!-- 行业排名 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><Histogram /></el-icon>
            行业表现排名
          </span>
        </template>

        <bar-chart
          v-if="barChartData.length > 0"
          :data="barChartData"
          height="600px"
          title="行业相对强度排名"
          :horizontal="true"
        />
      </el-card>

      <!-- 行业详细数据 -->
      <el-card class="table-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><Grid /></el-icon>
            行业详细表现
          </span>
        </template>

        <el-table :data="sectorTableData" stripe border>
          <el-table-column prop="sector" label="行业" width="120" fixed />
          <el-table-column prop="rsScore" label="相对强度" width="100" sortable>
            <template #default="{ row }">
              <el-tag :type="getRSTagType(row.rsScore)">
                {{ row.rsScore }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="return1d" label="1日涨跌" width="100" sortable>
            <template #default="{ row }">
              <span :style="{ color: parseFloat(row.return1d) > 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.return1d }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="return5d" label="5日涨跌" width="100" sortable>
            <template #default="{ row }">
              <span :style="{ color: parseFloat(row.return5d) > 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.return5d }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="return20d" label="20日涨跌" width="100" sortable>
            <template #default="{ row }">
              <span :style="{ color: parseFloat(row.return20d) > 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.return20d }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="return60d" label="60日涨跌" width="100" sortable>
            <template #default="{ row }">
              <span :style="{ color: parseFloat(row.return60d) > 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.return60d }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 配置建议 -->
      <el-card class="recommendation-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><Guide /></el-icon>
            {{ $t('sectorAnalysis.allocation') }}
          </span>
        </template>

        <el-alert
          :title="sectorData.allocation_recommendation.recommendation"
          type="success"
          show-icon
          :closable="false"
        />

        <el-divider />

        <div v-if="sectorData.allocation_recommendation.recommended_sectors" class="recommended-sectors">
          <h4>{{ $t('sectorAnalysis.recommendedSectors') }}</h4>
          <el-tag
            v-for="sector in sectorData.allocation_recommendation.recommended_sectors"
            :key="sector"
            type="primary"
            size="large"
            style="margin: 5px"
          >
            {{ sector }}
          </el-tag>
        </div>
      </el-card>
    </div>

    <el-empty v-else :description="$t('common.loading')" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import RadarChart from '@/components/charts/RadarChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const loading = ref(false)
const sectorData = ref<any>(null)

// 雷达图数据
const radarChartData = computed(() => {
  if (!sectorData.value?.sector_performance) return []
  return Object.entries(sectorData.value.sector_performance).map(([code, data]: [string, any]) => ({
    name: data.name,
    value: data.rs_score,
  }))
})

// 柱状图数据
const barChartData = computed(() => {
  if (!sectorData.value?.sector_performance) return []
  return Object.entries(sectorData.value.sector_performance)
    .map(([code, data]: [string, any]) => ({
      name: data.name,
      value: data.rs_score,
      color: getBarColor(data.rs_score),
    }))
    .sort((a, b) => b.value - a.value)
})

// 表格数据
const sectorTableData = computed(() => {
  if (!sectorData.value?.sector_performance) return []
  return Object.entries(sectorData.value.sector_performance)
    .map(([code, data]: [string, any]) => ({
      sector: data.name,
      rsScore: data.rs_score.toFixed(1),
      return1d: `${(data.return_1d * 100).toFixed(2)}%`,
      return5d: `${(data.return_5d * 100).toFixed(2)}%`,
      return20d: `${(data.return_20d * 100).toFixed(2)}%`,
      return60d: `${(data.return_60d * 100).toFixed(2)}%`,
    }))
    .sort((a, b) => parseFloat(b.rsScore) - parseFloat(a.rsScore))
})

// 获取轮动模式颜色
const getPatternColor = (pattern: string) => {
  if (pattern.includes('进攻')) return '#67c23a'
  if (pattern.includes('防守')) return '#f56c6c'
  return '#1890ff'
}

// 获取RS标签类型
const getRSTagType = (score: string) => {
  const val = parseFloat(score)
  if (val >= 70) return 'success'
  if (val >= 50) return ''
  return 'info'
}

// 获取柱状图颜色
const getBarColor = (score: number) => {
  if (score >= 70) return '#67c23a'
  if (score >= 60) return '#52c41a'
  if (score >= 50) return '#1890ff'
  if (score >= 40) return '#faad14'
  return '#f56c6c'
}

// 获取行业数据
const fetchSectorData = async () => {
  try {
    loading.value = true
    const response = await fetch('http://localhost:8000/api/sectors/current')
    const result = await response.json()
    sectorData.value = result.data
  } catch (error) {
    console.error('获取行业数据失败:', error)
    ElMessage.error('获取行业数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSectorData()
})
</script>

<style scoped>
.sector-rotation {
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

.pattern-card,
.chart-card,
.table-card,
.recommendation-card {
  margin-bottom: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.recommended-sectors h4 {
  margin-top: 10px;
  margin-bottom: 15px;
  color: #303133;
}

.dark .recommended-sectors h4 {
  color: #e5eaf3;
}
</style>
