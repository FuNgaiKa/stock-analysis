<template>
  <div class="support-resistance">
    <div class="page-header">
      <h1>📊 支撑/压力位分析</h1>
      <p class="subtitle">5种计算方法 - 精准识别关键价位 - 智能交易建议</p>
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
            <el-form-item label="回溯天数">
              <el-select v-model="config.lookback" placeholder="选择天数" style="width: 100%">
                <el-option label="120天" :value="120" />
                <el-option label="252天(1年)" :value="252" />
                <el-option label="504天(2年)" :value="504" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                @click="analyzeSR"
                style="width: 100%"
              >
                <el-icon><TrendCharts /></el-icon>
                开始分析
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 当前价格概览 -->
    <el-card v-if="result" class="modern-card summary-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">💰 当前价格概览</span>
          <el-tag size="large">{{ result.symbol }}</el-tag>
        </div>
      </template>

      <el-row :gutter="20" class="summary-row">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box gradient-1">
            <div class="stat-icon">💵</div>
            <div class="stat-value">${{ result.current_price.toFixed(2) }}</div>
            <div class="stat-label">当前价格</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box gradient-2">
            <div class="stat-icon">🔺</div>
            <div class="stat-value">${{ result['52_week_high'].toFixed(2) }}</div>
            <div class="stat-label">52周最高</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box gradient-3">
            <div class="stat-icon">🔻</div>
            <div class="stat-value">${{ result['52_week_low'].toFixed(2) }}</div>
            <div class="stat-label">52周最低</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-box gradient-4">
            <div class="stat-icon">📏</div>
            <div class="stat-value">{{ result.dist_to_52w_high_pct.toFixed(1) }}%</div>
            <div class="stat-label">距52周高点</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 交易建议 -->
    <el-card v-if="result && result.trading_advice.length > 0" class="modern-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">💡 交易建议</span>
        </div>
      </template>

      <el-space direction="vertical" :size="12" style="width: 100%">
        <el-alert
          v-for="(advice, index) in result.trading_advice"
          :key="index"
          :title="advice"
          :type="getAdviceType(advice)"
          show-icon
          :closable="false"
        />
      </el-space>
    </el-card>

    <!-- 压力位列表 -->
    <el-card v-if="result && result.key_resistances.length > 0" class="modern-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">⬆️ 关键压力位</span>
        </div>
      </template>

      <el-table :data="result.key_resistances" stripe>
        <el-table-column label="价格" width="150" align="center">
          <template #default="scope">
            <span class="price-value">${{ scope.row.price.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="距离" width="120" align="center">
          <template #default="scope">
            <el-tag :type="getDistanceType(scope.row.distance)">
              {{ scope.row.distance > 0 ? '+' : '' }}{{ scope.row.distance.toFixed(2) }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="strength" label="强度" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getStrengthType(scope.row.strength)">
              {{ scope.row.strength }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作建议" min-width="250">
          <template #default="scope">
            <span class="advice-text">{{ getResistanceAdvice(scope.row) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 支撑位列表 -->
    <el-card v-if="result && result.key_supports.length > 0" class="modern-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">⬇️ 关键支撑位</span>
        </div>
      </template>

      <el-table :data="result.key_supports" stripe>
        <el-table-column label="价格" width="150" align="center">
          <template #default="scope">
            <span class="price-value">${{ scope.row.price.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="距离" width="120" align="center">
          <template #default="scope">
            <el-tag :type="getSupportDistanceType(scope.row.distance)">
              {{ scope.row.distance.toFixed(2) }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="strength" label="强度" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getStrengthType(scope.row.strength)">
              {{ scope.row.strength }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作建议" min-width="250">
          <template #default="scope">
            <span class="advice-text">{{ getSupportAdvice(scope.row) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 技术指标详情 -->
    <el-row v-if="result" :gutter="20">
      <!-- 枢轴点 -->
      <el-col :xs="24" :md="12">
        <el-card class="modern-card detail-card hover-lift fade-in">
          <template #header>
            <div class="card-header">
              <span class="card-title">🎯 枢轴点分析</span>
            </div>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="Pivot">
              ${{ result.pivot_points.pivot.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="R1">
              ${{ result.pivot_points.resistance_1.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="R2">
              ${{ result.pivot_points.resistance_2.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="R3">
              ${{ result.pivot_points.resistance_3.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="S1">
              ${{ result.pivot_points.support_1.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="S2">
              ${{ result.pivot_points.support_2.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="S3">
              ${{ result.pivot_points.support_3.toFixed(2) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 斐波那契回调 -->
      <el-col :xs="24" :md="12">
        <el-card class="modern-card detail-card hover-lift fade-in">
          <template #header>
            <div class="card-header">
              <span class="card-title">🌀 斐波那契回调</span>
            </div>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="High">
              ${{ result.fibonacci_levels.high.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="Fib 0.236">
              ${{ result.fibonacci_levels['fib_0.236'].toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="Fib 0.382">
              ${{ result.fibonacci_levels['fib_0.382'].toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="Fib 0.500">
              ${{ result.fibonacci_levels['fib_0.500'].toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="Fib 0.618">
              ${{ result.fibonacci_levels['fib_0.618'].toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="Fib 0.786">
              ${{ result.fibonacci_levels['fib_0.786'].toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="Low">
              ${{ result.fibonacci_levels.low.toFixed(2) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <!-- 均线支撑/压力 -->
    <el-card v-if="result && result.ma_levels" class="modern-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">📈 均线支撑/压力</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col
          v-for="(value, name) in result.ma_levels"
          :key="name"
          :xs="12" :sm="8" :md="6" :lg="4"
        >
          <div class="ma-box" :class="getMaClass(value, result.current_price)">
            <div class="ma-name">{{ name }}</div>
            <div class="ma-value">${{ value.toFixed(2) }}</div>
            <div class="ma-diff">
              {{ getMaDiff(value, result.current_price) }}%
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-if="!loading && !result" description="请选择标的并开始分析" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts } from '@element-plus/icons-vue'

// 配置
const config = ref({
  symbol: 'GC=F',
  lookback: 252
})

const loading = ref(false)
const result = ref<any>(null)

// 分析函数
const analyzeSR = async () => {
  loading.value = true

  try {
    // TODO: 调用后端API
    // const response = await fetch(`/api/sr/analyze?symbol=${config.value.symbol}`)
    // result.value = await response.json()

    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 1500))

    result.value = {
      symbol: config.value.symbol,
      current_price: 4000.40,
      '52_week_high': 4049.20,
      '52_week_low': 2658.30,
      dist_to_52w_high_pct: -1.21,
      dist_to_52w_low_pct: 50.48,
      key_resistances: [
        { price: 4015.20, distance: 0.37, strength: '强' },
        { price: 4049.20, distance: 1.22, strength: '中' },
        { price: 4092.50, distance: 2.30, strength: '弱' }
      ],
      key_supports: [
        { price: 3909.20, distance: -2.28, strength: '强' },
        { price: 3850.00, distance: -3.76, strength: '中' },
        { price: 3780.50, distance: -5.50, strength: '中' }
      ],
      pivot_points: {
        pivot: 3985.60,
        resistance_1: 4021.30,
        resistance_2: 4049.80,
        resistance_3: 4085.50,
        support_1: 3957.10,
        support_2: 3921.40,
        support_3: 3892.90
      },
      fibonacci_levels: {
        high: 4049.20,
        'fib_0.236': 3977.20,
        'fib_0.382': 3935.60,
        'fib_0.500': 3853.75,
        'fib_0.618': 3771.90,
        'fib_0.786': 3652.40,
        low: 2658.30
      },
      ma_levels: {
        MA20: 3956.80,
        MA50: 3889.20,
        MA60: 3867.50,
        MA120: 3756.90,
        MA200: 3612.40,
        MA250: 3498.20
      },
      trading_advice: [
        '⚠️ 当前价接近压力位 $4015.20，突破确认后可追涨',
        '🟢 如跌破支撑位 $3909.20，及时止损',
        '🔥 接近52周高点，突破后空间打开'
      ]
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
const getAdviceType = (advice: string) => {
  if (advice.includes('⚠️')) return 'warning'
  if (advice.includes('🟢')) return 'success'
  if (advice.includes('🔥')) return 'danger'
  return 'info'
}

const getDistanceType = (distance: number) => {
  const abs = Math.abs(distance)
  if (abs < 2) return 'danger'
  if (abs < 5) return 'warning'
  return 'info'
}

const getSupportDistanceType = (distance: number) => {
  const abs = Math.abs(distance)
  if (abs < 2) return 'success'
  if (abs < 5) return 'warning'
  return 'info'
}

const getStrengthType = (strength: string) => {
  if (strength === '强') return 'danger'
  if (strength === '中') return 'warning'
  return 'info'
}

const getResistanceAdvice = (resistance: any) => {
  const dist = Math.abs(resistance.distance)
  if (dist < 2) {
    return '价格接近此压力位，关注突破情况'
  } else if (dist < 5) {
    return '中期目标位，突破后有望继续上涨'
  } else {
    return '长期阻力位，需要强势突破'
  }
}

const getSupportAdvice = (support: any) => {
  const dist = Math.abs(support.distance)
  if (dist < 2) {
    return '价格接近此支撑位，回踩可考虑买入'
  } else if (dist < 5) {
    return '重要支撑位，跌破需谨慎'
  } else {
    return '深度支撑位，恐慌性下跌才会触及'
  }
}

const getMaClass = (maValue: number, currentPrice: number) => {
  if (maValue > currentPrice) return 'ma-resistance'
  return 'ma-support'
}

const getMaDiff = (maValue: number, currentPrice: number) => {
  const diff = ((maValue - currentPrice) / currentPrice * 100)
  return diff > 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2)
}
</script>

<style scoped lang="scss">
.support-resistance {
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
  margin-bottom: 0;
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

.price-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.advice-text {
  color: #606266;
  font-size: 14px;
}

.ma-box {
  text-align: center;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  border: 2px solid #E4E7ED;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .ma-name {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
    color: #606266;
  }

  .ma-value {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .ma-diff {
    font-size: 12px;
    color: #909399;
  }
}

.ma-resistance {
  border-color: #F56C6C;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);

  .ma-value {
    color: #F56C6C;
  }
}

.ma-support {
  border-color: #67C23A;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);

  .ma-value {
    color: #67C23A;
  }
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
