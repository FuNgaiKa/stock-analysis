<template>
  <div class="backtest">
    <el-card class="header-card" shadow="never">
      <div class="page-header">
        <h1>📊 历史回测</h1>
      </div>
    </el-card>

    <!-- 回测配置 -->
    <el-card class="config-card" shadow="hover">
      <template #header>
        <span class="card-title">
          <el-icon><Setting /></el-icon>
          回测配置
        </span>
      </template>

      <el-form :model="backtestConfig" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="回测指数">
              <el-select v-model="backtestConfig.index_code" placeholder="选择指数" style="width: 100%">
                <el-option
                  v-for="index in availableIndices"
                  :key="index.code"
                  :label="`${index.name} (${index.symbol})`"
                  :value="index.code"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="回测天数">
              <el-input-number
                v-model="backtestConfig.days"
                :min="100"
                :max="2000"
                :step="100"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="初始资金">
              <el-input-number
                v-model="backtestConfig.initial_capital"
                :min="10000"
                :max="10000000"
                :step="10000"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手续费率">
              <el-input value="0.03%" disabled style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="止损比例">
              <el-slider
                v-model="backtestConfig.stop_loss_pct"
                :min="1"
                :max="20"
                :format-tooltip="(val) => `${val}%`"
              />
              <span style="color: #909399">{{ backtestConfig.stop_loss_pct }}%</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="止盈比例">
              <el-slider
                v-model="backtestConfig.take_profit_pct"
                :min="5"
                :max="50"
                :format-tooltip="(val) => `${val}%`"
              />
              <span style="color: #909399">{{ backtestConfig.take_profit_pct }}%</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" @click="runBacktest" :loading="loading" size="large">
            <el-icon><CaretRight /></el-icon>
            开始回测
          </el-button>
          <el-button @click="resetConfig" size="large">
            <el-icon><Refresh /></el-icon>
            重置配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 回测结果 -->
    <div v-if="backtestResult">
      <!-- 性能指标 -->
      <el-card class="metrics-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><DataAnalysis /></el-icon>
            回测性能指标
          </span>
        </template>

        <el-row :gutter="20" class="metric-row">
          <el-col :xs="12" :sm="6">
            <metric-card
              label="总收益率"
              :value="`${(backtestResult.performance.total_return * 100).toFixed(2)}%`"
              :trend="backtestResult.performance.total_return > 0 ? 'up' : 'down'"
            />
          </el-col>
          <el-col :xs="12" :sm="6">
            <metric-card
              label="年化收益率"
              :value="`${(backtestResult.performance.annual_return * 100).toFixed(2)}%`"
              :trend="backtestResult.performance.annual_return > 0 ? 'up' : 'down'"
            />
          </el-col>
          <el-col :xs="12" :sm="6">
            <metric-card
              label="最大回撤"
              :value="`${Math.abs(backtestResult.performance.max_drawdown * 100).toFixed(2)}%`"
              trend="down"
            />
          </el-col>
          <el-col :xs="12" :sm="6">
            <metric-card
              label="夏普比率"
              :value="backtestResult.performance.sharpe_ratio.toFixed(2)"
            />
          </el-col>
        </el-row>

        <el-divider />

        <el-row :gutter="20">
          <el-col :span="12">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="初始资金">
                {{ backtestResult.config.initial_capital.toLocaleString() }} 元
              </el-descriptions-item>
              <el-descriptions-item label="期末资金">
                {{ backtestResult.performance.final_capital.toFixed(0) }} 元
              </el-descriptions-item>
              <el-descriptions-item label="盈亏金额">
                <span :style="{ color: backtestResult.performance.profit > 0 ? '#67c23a' : '#f56c6c' }">
                  {{ backtestResult.performance.profit.toFixed(0) }} 元
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="年化波动率">
                {{ (backtestResult.performance.volatility * 100).toFixed(2) }}%
              </el-descriptions-item>
              <el-descriptions-item label="卡玛比率">
                {{ backtestResult.performance.calmar_ratio.toFixed(2) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-col>

          <el-col :span="12">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="交易次数">
                {{ backtestResult.performance.total_trades }}
              </el-descriptions-item>
              <el-descriptions-item label="胜率">
                {{ (backtestResult.performance.win_rate * 100).toFixed(2) }}%
              </el-descriptions-item>
              <el-descriptions-item label="盈亏比">
                {{ backtestResult.performance.profit_factor.toFixed(2) }}
              </el-descriptions-item>
              <el-descriptions-item label="平均持仓天数">
                {{ backtestResult.performance.avg_holding_days.toFixed(1) }} 天
              </el-descriptions-item>
              <el-descriptions-item label="最大连胜">
                {{ backtestResult.performance.max_consecutive_wins }} 次
              </el-descriptions-item>
            </el-descriptions>
          </el-col>
        </el-row>
      </el-card>

      <!-- 权益曲线 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><TrendCharts /></el-icon>
            权益曲线
          </span>
        </template>

        <line-chart
          v-if="equityCurveData.length > 0"
          :data="equityCurveData"
          height="400px"
          title="策略权益曲线"
          x-field="date"
          y-field="value"
        />
      </el-card>

      <!-- 交易记录 -->
      <el-card class="table-card" shadow="hover">
        <template #header>
          <span class="card-title">
            <el-icon><Tickets /></el-icon>
            交易记录 (前20笔)
          </span>
        </template>

        <el-table :data="backtestResult.trades" stripe border>
          <el-table-column prop="entry_date" label="入场日期" width="120" />
          <el-table-column prop="exit_date" label="出场日期" width="120" />
          <el-table-column prop="entry_price" label="入场价" width="100" align="right" />
          <el-table-column prop="exit_price" label="出场价" width="100" align="right" />
          <el-table-column prop="shares" label="持仓数" width="100" align="right" />
          <el-table-column prop="return" label="收益率" width="100" sortable>
            <template #default="{ row }">
              <span :style="{ color: row.return > 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.return.toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="pnl" label="盈亏金额" width="120" sortable align="right">
            <template #default="{ row }">
              <span :style="{ color: row.pnl > 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.pnl.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="signal" label="出场信号" width="120">
            <template #default="{ row }">
              <el-tag :type="getSignalType(row.signal)" size="small">
                {{ row.signal }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <el-empty v-else-if="!loading" description="请配置参数后开始回测" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import MetricCard from '@/components/cards/MetricCard.vue'
import LineChart from '@/components/charts/LineChart.vue'

const loading = ref(false)
const availableIndices = ref<any[]>([])
const backtestResult = ref<any>(null)

// 回测配置
const backtestConfig = ref({
  index_code: 'SPY',
  days: 500,
  initial_capital: 100000,
  stop_loss_pct: 8,
  take_profit_pct: 15,
})

// 权益曲线数据
const equityCurveData = computed(() => {
  if (!backtestResult.value?.equity_curve) return []
  return backtestResult.value.equity_curve.map((item: any) => ({
    date: item.date,
    value: item.value,
  }))
})

// 获取信号标签类型
const getSignalType = (signal: string) => {
  if (signal === 'STOP_LOSS') return 'danger'
  if (signal === 'TAKE_PROFIT') return 'success'
  if (signal.includes('SELL')) return 'warning'
  return 'info'
}

// 获取可用指数
const fetchIndices = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/indices')
    const result = await response.json()
    availableIndices.value = result
  } catch (error) {
    console.error('获取指数列表失败:', error)
  }
}

// 运行回测
const runBacktest = async () => {
  if (!backtestConfig.value.index_code) {
    ElMessage.warning('请选择回测指数')
    return
  }

  try {
    loading.value = true
    backtestResult.value = null

    const params = new URLSearchParams({
      index_code: backtestConfig.value.index_code,
      days: backtestConfig.value.days.toString(),
      initial_capital: backtestConfig.value.initial_capital.toString(),
      stop_loss: (backtestConfig.value.stop_loss_pct / 100).toString(),
      take_profit: (backtestConfig.value.take_profit_pct / 100).toString(),
    })

    const response = await fetch(`http://localhost:8000/api/backtest/run?${params}`, {
      method: 'POST',
    })

    const result = await response.json()

    if (result.success) {
      backtestResult.value = result.data
      ElMessage.success('回测完成')
    } else {
      ElMessage.error('回测失败')
    }
  } catch (error: any) {
    console.error('运行回测失败:', error)
    ElMessage.error(error.message || '回测失败，请检查配置')
  } finally {
    loading.value = false
  }
}

// 重置配置
const resetConfig = () => {
  backtestConfig.value = {
    index_code: 'SPY',
    days: 500,
    initial_capital: 100000,
    stop_loss_pct: 8,
    take_profit_pct: 15,
  }
  backtestResult.value = null
}

onMounted(() => {
  fetchIndices()
})
</script>

<style scoped>
.backtest {
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

.config-card,
.metrics-card,
.chart-card,
.table-card {
  margin-bottom: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.metric-row {
  margin-bottom: 20px;
}

:deep(.el-slider__runway) {
  margin: 16px 0;
}
</style>
