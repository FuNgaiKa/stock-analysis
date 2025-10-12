<template>
  <div class="position-analysis fade-in">
    <el-card class="header-card" shadow="never">
      <div class="page-header">
        <div>
          <h1 class="gradient-text">📊 历史点位对比分析</h1>
          <p class="subtitle">通过历史数据对比,洞察市场当前位置</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="runAnalysis" :loading="analyzing">
            <el-icon><DataAnalysis /></el-icon>
            {{ analyzing ? '分析中...' : '开始分析' }}
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 参数配置 -->
    <el-card class="config-card modern-card" shadow="hover">
      <template #header>
        <span class="card-title">
          <el-icon><Setting /></el-icon>
          分析参数
        </span>
      </template>

      <el-form :model="params" label-width="120px" label-position="left">
        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-form-item label="选择指数">
              <el-select
                v-model="params.indexCode"
                placeholder="请选择指数"
                style="width: 100%"
              >
                <el-option
                  v-for="index in availableIndices"
                  :key="index.code"
                  :label="`${index.name} (${index.code})`"
                  :value="index.code"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="相似度容差">
              <el-slider
                v-model="params.tolerance"
                :min="0.01"
                :max="0.2"
                :step="0.01"
                :format-tooltip="(val: number) => `${(val * 100).toFixed(0)}%`"
                show-input
              />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="分析周期">
              <el-checkbox-group v-model="params.periods">
                <el-checkbox :label="5">5日</el-checkbox>
                <el-checkbox :label="10">10日</el-checkbox>
                <el-checkbox :label="20">20日</el-checkbox>
                <el-checkbox :label="60">60日</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="高级选项">
              <el-checkbox v-model="params.usePhase2">Phase 2 增强分析</el-checkbox>
              <el-checkbox v-model="params.usePhase3">Phase 3 深度分析</el-checkbox>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 分析结果 -->
    <transition name="fade-slide" mode="out-in">
      <div v-if="analysisResult" class="result-section">
        <!-- 当前状态 -->
        <el-card class="status-card modern-card" shadow="hover">
          <template #header>
            <span class="card-title">
              <el-icon><Position /></el-icon>
              当前市场状态
            </span>
          </template>

          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" :md="6">
              <el-statistic title="当前价格" :value="analysisResult.current_price" :precision="2">
                <template #prefix>¥</template>
              </el-statistic>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-statistic title="数据日期" :value="analysisResult.current_date">
                <template #prefix>
                  <el-icon><Calendar /></el-icon>
                </template>
              </el-statistic>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-statistic
                title="相似时期"
                :value="analysisResult.similar_periods?.length || 0"
              >
                <template #prefix>
                  <el-icon><Connection /></el-icon>
                </template>
              </el-statistic>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-statistic title="置信度" :value="getAverageConfidence()" :precision="1" suffix="%">
                <template #prefix>
                  <el-icon><Trophy /></el-icon>
                </template>
              </el-statistic>
            </el-col>
          </el-row>
        </el-card>

        <!-- 市场环境 -->
        <el-card
          v-if="analysisResult.market_environment"
          class="environment-card modern-card"
          shadow="hover"
        >
          <template #header>
            <span class="card-title">
              <el-icon><Compass /></el-icon>
              市场环境识别
            </span>
          </template>

          <div class="environment-content">
            <div class="environment-type">
              <el-tag :type="getEnvironmentType(analysisResult.market_environment.environment)" size="large">
                {{ analysisResult.market_environment.environment }}
              </el-tag>
            </div>

            <el-divider />

            <el-row :gutter="20" class="environment-details">
              <el-col :xs="24" :sm="8">
                <div class="env-item">
                  <span class="env-label">RSI指标:</span>
                  <span class="env-value">{{ analysisResult.market_environment.rsi?.toFixed(2) }}</span>
                </div>
              </el-col>
              <el-col :xs="24" :sm="8">
                <div class="env-item">
                  <span class="env-label">距52周高点:</span>
                  <span class="env-value">{{ (analysisResult.market_environment.dist_from_high * 100).toFixed(2) }}%</span>
                </div>
              </el-col>
              <el-col :xs="24" :sm="8">
                <div class="env-item">
                  <span class="env-label">均线状态:</span>
                  <span class="env-value">{{ analysisResult.market_environment.ma_state }}</span>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>

        <!-- 周期分析 -->
        <el-card class="periods-card modern-card" shadow="hover">
          <template #header>
            <span class="card-title">
              <el-icon><DataLine /></el-icon>
              周期分析详情
            </span>
          </template>

          <el-table :data="periodTableData" stripe style="width: 100%">
            <el-table-column prop="period" label="周期" width="100" align="center">
              <template #default="{ row }">
                <el-tag>{{ row.period }}日</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="sample_size" label="样本数" width="100" align="center" />
            <el-table-column prop="up_prob" label="上涨概率" align="center">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.up_prob * 100"
                  :color="row.up_prob >= 0.6 ? '#67c23a' : row.up_prob >= 0.4 ? '#e6a23c' : '#f56c6c'"
                />
              </template>
            </el-table-column>
            <el-table-column prop="mean_return" label="平均收益" align="right">
              <template #default="{ row }">
                <span :class="row.mean_return >= 0 ? 'profit' : 'loss'">
                  {{ (row.mean_return * 100).toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="median_return" label="中位收益" align="right">
              <template #default="{ row }">
                <span :class="row.median_return >= 0 ? 'profit' : 'loss'">
                  {{ (row.median_return * 100).toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="confidence" label="置信度" width="100" align="center">
              <template #default="{ row }">
                {{ (row.confidence * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column prop="signal" label="操作信号" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="getSignalType(row.signal)">{{ row.signal }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 综合建议 -->
        <el-card class="advice-card modern-card" shadow="hover">
          <template #header>
            <span class="card-title">
              <el-icon><Reading /></el-icon>
              综合操作建议
            </span>
          </template>

          <el-alert
            :title="getOverallAdvice().title"
            :type="getOverallAdvice().type"
            :description="getOverallAdvice().description"
            show-icon
            :closable="false"
          />
        </el-card>

        <!-- Phase 3 深度分析 -->
        <div v-if="analysisResult.phase3_analysis">
          <!-- VIX分析 -->
          <el-card
            v-if="analysisResult.phase3_analysis.vix"
            class="vix-card modern-card"
            shadow="hover"
          >
            <template #header>
              <span class="card-title">
                <el-icon><Orange /></el-icon>
                VIX恐慌指数分析
              </span>
            </template>

            <el-row :gutter="20">
              <el-col :xs="24" :md="12">
                <el-statistic
                  title="VIX当前值"
                  :value="analysisResult.phase3_analysis.vix.current_vix"
                  :precision="2"
                >
                  <template #suffix>
                    <el-tag :type="getVixType(analysisResult.phase3_analysis.vix.vix_status)" size="small">
                      {{ analysisResult.phase3_analysis.vix.vix_status }}
                    </el-tag>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :xs="24" :md="12">
                <div class="vix-signal">
                  <div class="signal-label">交易信号</div>
                  <el-tag :type="getSignalType(analysisResult.phase3_analysis.vix.signal)" size="large">
                    {{ analysisResult.phase3_analysis.vix.signal }}
                  </el-tag>
                </div>
              </el-col>
            </el-row>
          </el-card>

          <!-- 行业轮动 -->
          <el-card
            v-if="analysisResult.phase3_analysis.sector"
            class="sector-card modern-card"
            shadow="hover"
          >
            <template #header>
              <span class="card-title">
                <el-icon><Refresh /></el-icon>
                行业轮动分析
              </span>
            </template>

            <div class="sector-content">
              <div class="rotation-pattern">
                <span class="label">轮动模式:</span>
                <el-tag type="primary" size="large">
                  {{ analysisResult.phase3_analysis.sector.rotation_pattern }}
                </el-tag>
              </div>

              <el-divider />

              <div class="recommended-sectors">
                <div class="label">推荐行业:</div>
                <el-space wrap>
                  <el-tag
                    v-for="sector in analysisResult.phase3_analysis.sector.recommended_sectors"
                    :key="sector"
                    type="success"
                  >
                    {{ sector }}
                  </el-tag>
                </el-space>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </transition>

    <!-- 空状态 -->
    <el-empty v-if="!analyzing && !analysisResult" description="请点击'开始分析'按钮进行历史点位对比分析" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 可用指数列表
const availableIndices = ref([
  { code: '^GSPC', name: '标普500' },
  { code: '^DJI', name: '道琼斯' },
  { code: '^IXIC', name: '纳斯达克' },
  { code: '^HSI', name: '恒生指数' },
])

// 分析参数
const params = ref({
  indexCode: '^GSPC',
  tolerance: 0.05,
  periods: [5, 10, 20, 60],
  usePhase2: true,
  usePhase3: false,
})

// 分析状态
const analyzing = ref(false)
const analysisResult = ref<any>(null)

// 运行分析
const runAnalysis = async () => {
  if (params.value.periods.length === 0) {
    ElMessage.warning('请至少选择一个分析周期')
    return
  }

  try {
    analyzing.value = true
    const response = await fetch('http://localhost:8000/api/analyze/single', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        index_code: params.value.indexCode,
        tolerance: params.value.tolerance,
        periods: params.value.periods,
        use_phase2: params.value.usePhase2,
        use_phase3: params.value.usePhase3,
      }),
    })

    const result = await response.json()

    if (result.success) {
      analysisResult.value = result.data
      ElMessage.success('分析完成!')
    } else {
      ElMessage.error('分析失败')
    }
  } catch (error) {
    console.error('分析失败:', error)
    ElMessage.error('分析失败')
  } finally {
    analyzing.value = false
  }
}

// 周期表格数据
const periodTableData = computed(() => {
  if (!analysisResult.value?.period_analysis) return []

  return Object.entries(analysisResult.value.period_analysis).map(([period, data]: [string, any]) => ({
    period: parseInt(period),
    ...data,
  }))
})

// 获取平均置信度
const getAverageConfidence = () => {
  if (!analysisResult.value?.period_analysis) return 0

  const confidences = Object.values(analysisResult.value.period_analysis).map(
    (data: any) => data.confidence
  )
  const avg = confidences.reduce((sum: number, val: number) => sum + val, 0) / confidences.length
  return avg * 100
}

// 获取环境类型
const getEnvironmentType = (env: string) => {
  const typeMap: Record<string, any> = {
    牛市顶部: 'danger',
    牛市中期: 'success',
    熊市底部: 'info',
    熊市中期: 'warning',
    震荡市: '',
  }
  return typeMap[env] || ''
}

// 获取信号类型
const getSignalType = (signal: string) => {
  const typeMap: Record<string, any> = {
    强烈买入: 'success',
    买入: 'success',
    持有: 'info',
    观望: 'warning',
    减仓: 'warning',
    卖出: 'danger',
  }
  return typeMap[signal] || 'info'
}

// 获取VIX类型
const getVixType = (status: string) => {
  const typeMap: Record<string, any> = {
    极度恐慌: 'success',
    恐慌上升: 'warning',
    正常: 'info',
    过度乐观: 'danger',
  }
  return typeMap[status] || 'info'
}

// 获取综合建议
const getOverallAdvice = () => {
  if (!analysisResult.value?.period_analysis) {
    return { title: '暂无建议', type: 'info', description: '' }
  }

  const periods = Object.values(analysisResult.value.period_analysis)
  const avgUpProb = periods.reduce((sum: number, p: any) => sum + p.up_prob, 0) / periods.length
  const avgReturn = periods.reduce((sum: number, p: any) => sum + p.mean_return, 0) / periods.length

  if (avgUpProb >= 0.7 && avgReturn >= 0.03) {
    return {
      title: '强烈看好',
      type: 'success',
      description: `历史数据显示,当前点位后续上涨概率较高(${(avgUpProb * 100).toFixed(1)}%),平均收益为${(avgReturn * 100).toFixed(2)}%。建议积极配置。`,
    }
  } else if (avgUpProb >= 0.5 && avgReturn >= 0) {
    return {
      title: '谨慎乐观',
      type: 'success',
      description: `当前点位具有一定投资价值,上涨概率${(avgUpProb * 100).toFixed(1)}%。建议适度参与,注意风险控制。`,
    }
  } else if (avgUpProb >= 0.4) {
    return {
      title: '中性观望',
      type: 'warning',
      description: `当前点位方向不明确,建议观望为主,等待更明确的信号。`,
    }
  } else {
    return {
      title: '保守谨慎',
      type: 'danger',
      description: `历史数据显示当前点位风险较高,下跌概率较大。建议降低仓位,规避风险。`,
    }
  }
}
</script>

<style scoped>
.position-analysis {
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

.subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: 15px;
}

.config-card {
  margin-bottom: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.result-section > * {
  margin-bottom: 20px;
}

.environment-content {
  text-align: center;
}

.environment-type {
  padding: 20px 0;
}

.environment-details {
  padding: 10px 0;
}

.env-item {
  text-align: center;
  padding: 10px;
}

.env-label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.env-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.profit {
  color: #67c23a;
}

.loss {
  color: #f56c6c;
}

.vix-signal {
  text-align: center;
  padding: 20px 0;
}

.signal-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.sector-content {
  padding: 10px 0;
}

.rotation-pattern,
.recommended-sectors {
  padding: 15px 0;
}

.rotation-pattern .label,
.recommended-sectors .label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  display: block;
}

@media (max-width: 768px) {
  .page-header h1 {
    font-size: 24px;
  }
}
</style>
