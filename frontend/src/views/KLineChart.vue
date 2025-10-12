<template>
  <div class="kline-container">
    <el-card class="header-card">
      <div class="controls">
        <div class="control-group">
          <el-select
            v-model="selectedSymbol"
            placeholder="选择标的"
            style="width: 200px"
            @change="loadData"
          >
            <el-option-group label="美股指数">
              <el-option label="纳斯达克综合指数" value="^IXIC" />
              <el-option label="标普500指数" value="^GSPC" />
              <el-option label="道琼斯工业指数" value="^DJI" />
              <el-option label="纳斯达克100指数" value="^NDX" />
            </el-option-group>
            <el-option-group label="A股指数">
              <el-option label="上证指数" value="000001.SS" />
              <el-option label="深证成指" value="399001.SZ" />
              <el-option label="创业板指" value="399006.SZ" />
              <el-option label="沪深300" value="000300.SS" />
            </el-option-group>
            <el-option-group label="港股指数">
              <el-option label="恒生指数" value="^HSI" />
              <el-option label="恒生国企指数" value="^HSCE" />
            </el-option-group>
            <el-option-group label="热门ETF">
              <el-option label="标普500 ETF (SPY)" value="SPY" />
              <el-option label="纳斯达克100 ETF (QQQ)" value="QQQ" />
            </el-option-group>
            <el-option-group label="加密货币">
              <el-option label="比特币" value="BTC-USD" />
              <el-option label="以太坊" value="ETH-USD" />
            </el-option-group>
          </el-select>

          <el-select v-model="period" placeholder="时间周期" style="width: 120px" @change="loadData">
            <el-option label="1个月" value="1mo" />
            <el-option label="3个月" value="3mo" />
            <el-option label="6个月" value="6mo" />
            <el-option label="1年" value="1y" />
            <el-option label="2年" value="2y" />
            <el-option label="5年" value="5y" />
          </el-select>

          <el-select v-model="interval" placeholder="K线周期" style="width: 100px" @change="loadData">
            <el-option label="日线" value="1d" />
            <el-option label="周线" value="1wk" />
            <el-option label="月线" value="1mo" />
          </el-select>

          <el-button type="primary" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <div class="indicator-switches">
          <el-checkbox v-model="showKDJ" @change="updateChart">显示KDJ</el-checkbox>
          <el-checkbox v-model="showDMI" @change="updateChart">显示DMI/ADX</el-checkbox>
          <el-checkbox v-model="showMACD" @change="updateChart">显示MACD</el-checkbox>
        </div>
      </div>
    </el-card>

    <el-card class="chart-card" v-loading="loading">
      <div v-if="error" class="error-message">
        <el-alert type="error" :title="error" :closable="false" />
      </div>

      <div v-else-if="chartData">
        <CandlestickChart
          :ohlc="chartData.ohlc"
          :indicators="chartData.indicators"
          :title="`${chartData.name} K线图`"
          :show-k-d-j="showKDJ"
          :show-d-m-i="showDMI"
          :show-m-a-c-d="showMACD"
          height="700px"
        />

        <!-- 当前指标信息 -->
        <el-card class="indicator-info" v-if="chartData.current_indicators">
          <div class="indicator-grid">
            <div class="indicator-item">
              <span class="label">最新价格:</span>
              <span class="value price">{{ chartData.current_indicators.latest_price?.toFixed(2) }}</span>
            </div>
            <div class="indicator-item">
              <span class="label">涨跌幅:</span>
              <span :class="['value', chartData.current_indicators.change_pct >= 0 ? 'up' : 'down']">
                {{ chartData.current_indicators.change_pct?.toFixed(2) }}%
              </span>
            </div>
            <div class="indicator-item">
              <span class="label">RSI:</span>
              <span class="value">{{ chartData.current_indicators.rsi?.toFixed(2) }}</span>
            </div>
            <div class="indicator-item" v-if="chartData.current_indicators.kdj_k">
              <span class="label">KDJ:</span>
              <span class="value">
                K={{ chartData.current_indicators.kdj_k?.toFixed(2) }},
                D={{ chartData.current_indicators.kdj_d?.toFixed(2) }},
                J={{ chartData.current_indicators.kdj_j?.toFixed(2) }}
              </span>
            </div>
            <div class="indicator-item" v-if="chartData.current_indicators.adx">
              <span class="label">DMI/ADX:</span>
              <span class="value">
                ADX={{ chartData.current_indicators.adx?.toFixed(2) }},
                +DI={{ chartData.current_indicators['+di']?.toFixed(2) }},
                -DI={{ chartData.current_indicators['-di']?.toFixed(2) }}
              </span>
            </div>
            <div class="indicator-item">
              <span class="label">MACD:</span>
              <span class="value">{{ chartData.current_indicators.macd?.toFixed(4) }}</span>
            </div>
          </div>
        </el-card>

        <!-- 数据统计 -->
        <el-card class="stats-card">
          <el-statistic-group>
            <el-statistic title="数据点数" :value="chartData.data_points" />
            <el-statistic title="时间周期" :value="periodLabels[period]" />
            <el-statistic title="K线间隔" :value="intervalLabels[interval]" />
          </el-statistic-group>
        </el-card>
      </div>

      <div v-else class="empty-state">
        <el-empty description="请选择标的并加载数据" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import CandlestickChart from '@/components/charts/CandlestickChart.vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

interface ChartData {
  symbol: string
  name: string
  period: string
  interval: string
  ohlc: Array<{
    date: string
    open: number
    high: number
    low: number
    close: number
    volume: number
  }>
  indicators: {
    ma5?: number[]
    ma20?: number[]
    ma60?: number[]
    kdj?: {
      k: number[]
      d: number[]
      j: number[]
    }
    dmi_adx?: {
      adx: number[]
      '+di': number[]
      '-di': number[]
    }
    macd?: {
      macd: number[]
      signal: number[]
      histogram: number[]
    }
    volume_ma?: number[]
  }
  current_indicators: {
    latest_price: number
    change_pct: number
    rsi: number
    kdj_k?: number
    kdj_d?: number
    kdj_j?: number
    adx?: number
    '+di'?: number
    '-di'?: number
    macd?: number
  }
  data_points: number
}

const selectedSymbol = ref('^IXIC')
const period = ref('3mo')
const interval = ref('1d')
const loading = ref(false)
const error = ref('')
const chartData = ref<ChartData | null>(null)

const showKDJ = ref(true)
const showDMI = ref(true)
const showMACD = ref(false)

const periodLabels: Record<string, string> = {
  '1mo': '1个月',
  '3mo': '3个月',
  '6mo': '6个月',
  '1y': '1年',
  '2y': '2年',
  '5y': '5年'
}

const intervalLabels: Record<string, string> = {
  '1d': '日线',
  '1wk': '周线',
  '1mo': '月线'
}

const loadData = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await axios.get(`${API_BASE}/api/kline/data`, {
      params: {
        symbol: selectedSymbol.value,
        period: period.value,
        interval: interval.value
      }
    })

    if (response.data.success) {
      chartData.value = response.data.data
      ElMessage.success('数据加载成功')
    } else {
      error.value = '加载失败'
      ElMessage.error('数据加载失败')
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || err.message || '网络错误'
    ElMessage.error(`加载失败: ${error.value}`)
    console.error('加载K线数据失败:', err)
  } finally {
    loading.value = false
  }
}

const updateChart = () => {
  // 触发图表更新 (通过改变showKDJ/showDMI/showMACD的值，CandlestickChart会自动重绘)
}

onMounted(() => {
  // 初始加载纳斯达克指数
  loadData()
})
</script>

<style scoped>
.kline-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.control-group {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.indicator-switches {
  display: flex;
  gap: 16px;
}

.chart-card {
  margin-bottom: 20px;
}

.error-message {
  margin-bottom: 20px;
}

.indicator-info {
  margin-top: 20px;
}

.indicator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.indicator-item {
  display: flex;
  align-items: center;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.indicator-item .label {
  font-weight: 500;
  color: #606266;
  margin-right: 8px;
  min-width: 80px;
}

.indicator-item .value {
  font-weight: 600;
  color: #303133;
}

.indicator-item .value.price {
  font-size: 18px;
  color: #409eff;
}

.indicator-item .value.up {
  color: #f56c6c;
}

.indicator-item .value.down {
  color: #67c23a;
}

.stats-card {
  margin-top: 20px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}
</style>
