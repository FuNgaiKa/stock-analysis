<template>
  <div class="compound-calculator fade-in">
    <el-card class="header-card" shadow="never">
      <div class="page-header">
        <div>
          <h1 class="gradient-text">💰 复合收益计算器</h1>
          <p class="subtitle">计算投资复合收益,让时间成为您财富增长的朋友</p>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- 左侧:参数输入 -->
      <el-col :xs="24" :md="12">
        <el-card class="input-card modern-card" shadow="hover">
          <template #header>
            <span class="card-title">
              <el-icon><Edit /></el-icon>
              计算参数
            </span>
          </template>

          <el-form :model="form" label-width="120px" label-position="left">
            <el-form-item label="初始本金 (元)">
              <el-input-number
                v-model="form.principal"
                :min="1"
                :max="100000000"
                :step="1000"
                :controls="true"
                style="width: 100%"
                @change="calculate"
              />
            </el-form-item>

            <el-form-item label="年化收益率 (%)">
              <el-slider
                v-model="form.annualRate"
                :min="-20"
                :max="50"
                :step="0.1"
                :marks="rateMarks"
                show-input
                @change="calculate"
              />
            </el-form-item>

            <el-form-item label="投资年限 (年)">
              <el-slider
                v-model="form.years"
                :min="1"
                :max="50"
                :marks="yearMarks"
                show-input
                @change="calculate"
              />
            </el-form-item>

            <el-form-item label="定投金额 (元/月)">
              <el-input-number
                v-model="form.monthlyInvestment"
                :min="0"
                :max="1000000"
                :step="100"
                :controls="true"
                style="width: 100%"
                @change="calculate"
              />
              <span class="form-tip">可选,0表示不定投</span>
            </el-form-item>
          </el-form>

          <!-- 快速预设 -->
          <el-divider>快速预设</el-divider>
          <el-space wrap>
            <el-button size="small" @click="applyPreset('conservative')">
              保守型 (6%)
            </el-button>
            <el-button size="small" type="primary" @click="applyPreset('balanced')">
              平衡型 (10%)
            </el-button>
            <el-button size="small" type="warning" @click="applyPreset('aggressive')">
              进取型 (15%)
            </el-button>
            <el-button size="small" type="danger" @click="applyPreset('high-risk')">
              高风险 (20%)
            </el-button>
          </el-space>
        </el-card>
      </el-col>

      <!-- 右侧:计算结果 -->
      <el-col :xs="24" :md="12">
        <el-card class="result-card modern-card" shadow="hover">
          <template #header>
            <span class="card-title">
              <el-icon><TrendCharts /></el-icon>
              计算结果
            </span>
          </template>

          <div class="result-summary">
            <div class="result-item main-result">
              <div class="result-label">最终金额</div>
              <div class="result-value highlight">
                ¥{{ formatNumber(result.finalAmount) }}
              </div>
            </div>

            <el-divider />

            <div class="result-grid">
              <div class="result-item">
                <div class="result-label">
                  <el-icon><Money /></el-icon>
                  初始投入
                </div>
                <div class="result-value">¥{{ formatNumber(form.principal) }}</div>
              </div>

              <div class="result-item" v-if="form.monthlyInvestment > 0">
                <div class="result-label">
                  <el-icon><Calendar /></el-icon>
                  定投总额
                </div>
                <div class="result-value">¥{{ formatNumber(result.totalInvestment) }}</div>
              </div>

              <div class="result-item">
                <div class="result-label">
                  <el-icon><PieChart /></el-icon>
                  总收益
                </div>
                <div class="result-value" :class="result.totalProfit >= 0 ? 'profit' : 'loss'">
                  ¥{{ formatNumber(result.totalProfit) }}
                </div>
              </div>

              <div class="result-item">
                <div class="result-label">
                  <el-icon><DataAnalysis /></el-icon>
                  收益率
                </div>
                <div class="result-value" :class="result.returnRate >= 0 ? 'profit' : 'loss'">
                  {{ result.returnRate.toFixed(2) }}%
                </div>
              </div>
            </div>
          </div>

          <!-- 收益分解图 -->
          <el-divider />
          <div class="chart-section">
            <div class="chart-title">收益构成</div>
            <pie-chart
              :data="profitBreakdownData"
              height="250px"
              :radius="['40%', '70%']"
            />
          </div>
        </el-card>

        <!-- 年度明细 -->
        <el-card class="detail-card modern-card" shadow="hover" style="margin-top: 20px">
          <template #header>
            <span class="card-title">
              <el-icon><Document /></el-icon>
              年度明细
            </span>
          </template>

          <el-table
            :data="yearlyDetails"
            stripe
            style="width: 100%"
            max-height="400"
            size="small"
          >
            <el-table-column prop="year" label="年份" width="80" align="center" />
            <el-table-column prop="amount" label="年末金额" align="right">
              <template #default="{ row }">
                ¥{{ formatNumber(row.amount) }}
              </template>
            </el-table-column>
            <el-table-column prop="yearProfit" label="当年收益" align="right">
              <template #default="{ row }">
                <span :class="row.yearProfit >= 0 ? 'profit' : 'loss'">
                  ¥{{ formatNumber(row.yearProfit) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="totalProfit" label="累计收益" align="right">
              <template #default="{ row }">
                <span :class="row.totalProfit >= 0 ? 'profit' : 'loss'">
                  ¥{{ formatNumber(row.totalProfit) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 增长趋势图 -->
    <el-card class="chart-card modern-card" shadow="hover" style="margin-top: 20px">
      <template #header>
        <span class="card-title">
          <el-icon><DataLine /></el-icon>
          资产增长趋势
        </span>
      </template>
      <line-chart
        :data="trendData"
        height="400px"
        :smooth="true"
        :show-area="true"
      />
    </el-card>

    <!-- 说明信息 -->
    <el-card class="info-card modern-card" shadow="never" style="margin-top: 20px">
      <el-alert
        title="计算说明"
        type="info"
        :closable="false"
      >
        <template #default>
          <ul class="info-list">
            <li>复利公式: FV = PV × (1 + r)^n</li>
            <li>定投复利: 采用逐月复利计算,更准确反映实际收益</li>
            <li>本计算器仅供参考,实际投资收益受市场波动影响</li>
            <li>历史收益不代表未来表现,投资需谨慎</li>
          </ul>
        </template>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import PieChart from '@/components/charts/PieChart.vue'
import LineChart from '@/components/charts/LineChart.vue'

// 表单数据
const form = ref({
  principal: 100000, // 初始本金
  annualRate: 10, // 年化收益率(%)
  years: 10, // 投资年限
  monthlyInvestment: 0, // 定投金额
})

// 滑块标记
const rateMarks = {
  0: '0%',
  10: '10%',
  20: '20%',
  30: '30%',
}

const yearMarks = {
  1: '1年',
  10: '10年',
  20: '20年',
  30: '30年',
  50: '50年',
}

// 计算结果
const result = ref({
  finalAmount: 0, // 最终金额
  totalInvestment: 0, // 总投入
  totalProfit: 0, // 总收益
  returnRate: 0, // 收益率
})

// 年度明细
const yearlyDetails = ref<any[]>([])

// 计算复合收益
const calculate = () => {
  const { principal, annualRate, years, monthlyInvestment } = form.value
  const rate = annualRate / 100
  const monthlyRate = rate / 12

  let currentAmount = principal
  let totalInvested = principal
  const details: any[] = []

  // 逐年计算
  for (let year = 1; year <= years; year++) {
    let yearStartAmount = currentAmount

    // 逐月计算(如果有定投)
    for (let month = 1; month <= 12; month++) {
      currentAmount = currentAmount * (1 + monthlyRate)
      if (monthlyInvestment > 0) {
        currentAmount += monthlyInvestment
        totalInvested += monthlyInvestment
      }
    }

    const yearProfit = currentAmount - yearStartAmount - (monthlyInvestment * 12)
    const totalProfit = currentAmount - totalInvested

    details.push({
      year,
      amount: currentAmount,
      yearProfit,
      totalProfit,
    })
  }

  yearlyDetails.value = details

  // 计算最终结果
  result.value = {
    finalAmount: currentAmount,
    totalInvestment: totalInvested,
    totalProfit: currentAmount - totalInvested,
    returnRate: ((currentAmount - totalInvested) / totalInvested) * 100,
  }
}

// 格式化数字
const formatNumber = (num: number) => {
  return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 收益构成饼图数据
const profitBreakdownData = computed(() => {
  const data = []

  if (form.value.principal > 0) {
    data.push({
      name: '初始本金',
      value: form.value.principal,
      color: '#409eff',
    })
  }

  if (form.value.monthlyInvestment > 0) {
    const monthlyTotal = form.value.monthlyInvestment * form.value.years * 12
    data.push({
      name: '定投本金',
      value: monthlyTotal,
      color: '#67c23a',
    })
  }

  if (result.value.totalProfit > 0) {
    data.push({
      name: '复利收益',
      value: result.value.totalProfit,
      color: '#e6a23c',
    })
  }

  return data
})

// 趋势图数据
const trendData = computed(() => {
  return yearlyDetails.value.map((item) => ({
    name: `第${item.year}年`,
    value: item.amount,
  }))
})

// 应用预设
const applyPreset = (type: string) => {
  const presets: Record<string, any> = {
    conservative: { annualRate: 6, principal: 100000, years: 10 },
    balanced: { annualRate: 10, principal: 100000, years: 10 },
    aggressive: { annualRate: 15, principal: 100000, years: 10 },
    'high-risk': { annualRate: 20, principal: 100000, years: 10 },
  }

  if (presets[type]) {
    Object.assign(form.value, presets[type])
    calculate()
  }
}

// 初始化
onMounted(() => {
  calculate()
})
</script>

<style scoped>
.compound-calculator {
  width: 100%;
}

.header-card {
  margin-bottom: 20px;
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

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.form-tip {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-left: 8px;
}

.result-summary {
  padding: 10px 0;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.result-item.main-result {
  padding: 20px 0;
}

.result-label {
  font-size: 14px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.result-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.result-value.highlight {
  font-size: 32px;
  color: #409eff;
  font-weight: 700;
}

.result-value.profit {
  color: #67c23a;
}

.result-value.loss {
  color: #f56c6c;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-top: 10px;
}

.chart-section {
  margin-top: 10px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 15px;
  color: var(--text-primary);
}

.info-list {
  margin: 10px 0;
  padding-left: 20px;
}

.info-list li {
  margin: 8px 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.profit {
  color: #67c23a;
}

.loss {
  color: #f56c6c;
}

@media (max-width: 768px) {
  .page-header h1 {
    font-size: 24px;
  }

  .result-value.highlight {
    font-size: 24px;
  }

  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
