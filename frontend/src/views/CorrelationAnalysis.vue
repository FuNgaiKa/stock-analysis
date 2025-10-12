<template>
  <div class="correlation-analysis">
    <div class="page-header">
      <h1>🔗 跨资产相关性分析</h1>
      <p class="subtitle">识别市场联动与对冲机会 - 多资产相关性热力图</p>
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
            <el-form-item label="资产选择">
              <el-select
                v-model="config.symbols"
                multiple
                placeholder="选择至少2个资产"
                style="width: 100%"
              >
                <el-option-group label="美股指数">
                  <el-option label="纳斯达克" value="^IXIC" />
                  <el-option label="标普500" value="^GSPC" />
                  <el-option label="道琼斯" value="^DJI" />
                </el-option-group>
                <el-option-group label="A股指数">
                  <el-option label="上证指数" value="000001.SS" />
                  <el-option label="深证成指" value="399001.SZ" />
                  <el-option label="沪深300" value="000300.SS" />
                </el-option-group>
                <el-option-group label="港股指数">
                  <el-option label="恒生指数" value="^HSI" />
                  <el-option label="恒生科技" value="HSTECH.HK" />
                </el-option-group>
                <el-option-group label="大宗商品">
                  <el-option label="黄金" value="GC=F" />
                  <el-option label="白银" value="SI=F" />
                  <el-option label="原油" value="CL=F" />
                </el-option-group>
                <el-option-group label="加密货币">
                  <el-option label="比特币" value="BTC-USD" />
                  <el-option label="以太坊" value="ETH-USD" />
                </el-option-group>
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="回溯天数">
              <el-select v-model="config.lookback" placeholder="选择天数" style="width: 100%">
                <el-option label="60天" :value="60" />
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
                @click="analyzeCorrelation"
                :disabled="config.symbols.length < 2"
                style="width: 100%"
              >
                <el-icon><Connection /></el-icon>
                开始分析
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 分析摘要 -->
    <el-card v-if="result" class="modern-card summary-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">📊 分析摘要</span>
          <el-tag size="large">{{ result.num_assets }} 个资产</el-tag>
        </div>
      </template>

      <el-row :gutter="20" class="summary-row">
        <el-col :xs="24" :sm="12" :md="8">
          <div class="stat-box gradient-1">
            <div class="stat-icon">📈</div>
            <div class="stat-value">{{ result.high_correlations.length }}</div>
            <div class="stat-label">高相关性对</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <div class="stat-box gradient-2">
            <div class="stat-icon">📉</div>
            <div class="stat-value">{{ result.negative_correlations.length }}</div>
            <div class="stat-label">负相关对冲对</div>
          </div>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <div class="stat-box gradient-3">
            <div class="stat-icon">📅</div>
            <div class="stat-value">{{ result.lookback_days }}</div>
            <div class="stat-label">回溯天数</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 高相关性资产对 -->
    <el-card v-if="result && result.high_correlations.length > 0" class="modern-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">🔥 高相关性资产对 (正相关)</span>
        </div>
      </template>

      <el-table :data="result.high_correlations" stripe>
        <el-table-column prop="asset1_name" label="资产1" min-width="120" />
        <el-table-column prop="asset2_name" label="资产2" min-width="120" />
        <el-table-column label="相关系数" width="150" align="center">
          <template #default="scope">
            <el-tag :type="getCorrelationType(scope.row.correlation)" size="large">
              {{ scope.row.correlation.toFixed(3) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="strength" label="强度" width="150" align="center">
          <template #default="scope">
            <el-tag>{{ scope.row.strength }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关系" min-width="200">
          <template #default="scope">
            <span class="correlation-desc">
              {{ getCorrelationDesc(scope.row) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 负相关对冲对 -->
    <el-card v-if="result && result.negative_correlations.length > 0" class="modern-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">🛡️ 负相关对冲对</span>
        </div>
      </template>

      <el-table :data="result.negative_correlations" stripe>
        <el-table-column prop="asset1_name" label="资产1" min-width="120" />
        <el-table-column prop="asset2_name" label="资产2" min-width="120" />
        <el-table-column label="相关系数" width="150" align="center">
          <template #default="scope">
            <el-tag type="info" size="large">
              {{ scope.row.correlation.toFixed(3) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="hedge_potential" label="对冲潜力" width="120" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.hedge_potential === '高' ? 'success' : 'info'">
              {{ scope.row.hedge_potential }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="策略建议" min-width="250">
          <template #default="scope">
            <span class="hedge-advice">
              {{ getHedgeAdvice(scope.row) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 相关性热力图 (将来实现) -->
    <el-card v-if="result" class="modern-card hover-lift fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-title">🌡️ 相关性热力图</span>
        </div>
      </template>

      <div class="heatmap-container">
        <el-alert
          title="热力图可视化正在开发中..."
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <p>将使用 ECharts 展示相关性矩阵热力图</p>
            <p>- 红色: 强正相关 (联动上涨/下跌)</p>
            <p>- 蓝色: 强负相关 (对冲机会)</p>
            <p>- 灰色: 弱相关/无相关</p>
          </template>
        </el-alert>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-if="!loading && !result" description="请至少选择2个资产并开始分析">
      <el-button type="primary" @click="setDefaultAssets">加载默认配置</el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection } from '@element-plus/icons-vue'

// 配置
const config = ref({
  symbols: ['^IXIC', '^GSPC', '^HSI', 'GC=F', 'BTC-USD'],
  lookback: 252
})

const loading = ref(false)
const result = ref<any>(null)

// 资产名称映射
const assetNames: Record<string, string> = {
  '^IXIC': '纳斯达克',
  '^GSPC': '标普500',
  '^DJI': '道琼斯',
  '000001.SS': '上证指数',
  '399001.SZ': '深证成指',
  '000300.SS': '沪深300',
  '^HSI': '恒生指数',
  'HSTECH.HK': '恒生科技',
  'GC=F': '黄金',
  'SI=F': '白银',
  'CL=F': '原油',
  'BTC-USD': '比特币',
  'ETH-USD': '以太坊'
}

// 分析函数
const analyzeCorrelation = async () => {
  if (config.value.symbols.length < 2) {
    ElMessage.warning('请至少选择2个资产')
    return
  }

  loading.value = true

  try {
    // TODO: 调用后端API
    // const response = await fetch('/api/correlation/analyze', {
    //   method: 'POST',
    //   body: JSON.stringify(config.value)
    // })
    // result.value = await response.json()

    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 1500))

    result.value = {
      lookback_days: config.value.lookback,
      num_assets: config.value.symbols.length,
      high_correlations: [
        {
          asset1: '^IXIC',
          asset1_name: assetNames['^IXIC'],
          asset2: '^GSPC',
          asset2_name: assetNames['^GSPC'],
          correlation: 0.973,
          strength: '极强正相关'
        },
        {
          asset1: '^GSPC',
          asset1_name: assetNames['^GSPC'],
          asset2: '^HSI',
          asset2_name: assetNames['^HSI'],
          correlation: 0.756,
          strength: '强正相关'
        },
        {
          asset1: 'BTC-USD',
          asset1_name: assetNames['BTC-USD'],
          asset2: '^IXIC',
          asset2_name: assetNames['^IXIC'],
          correlation: 0.682,
          strength: '中等正相关'
        }
      ],
      negative_correlations: [
        {
          asset1: 'GC=F',
          asset1_name: assetNames['GC=F'],
          asset2: '^GSPC',
          asset2_name: assetNames['^GSPC'],
          correlation: -0.612,
          hedge_potential: '中'
        },
        {
          asset1: 'GC=F',
          asset1_name: assetNames['GC=F'],
          asset2: '^IXIC',
          asset2_name: assetNames['^IXIC'],
          correlation: -0.589,
          hedge_potential: '中'
        }
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

// 设置默认资产
const setDefaultAssets = () => {
  config.value.symbols = ['^IXIC', '^GSPC', '^HSI', 'GC=F', 'BTC-USD']
}

// 辅助函数
const getCorrelationType = (corr: number) => {
  if (corr > 0.9) return 'danger'
  if (corr > 0.7) return 'warning'
  if (corr > 0.5) return 'success'
  return 'info'
}

const getCorrelationDesc = (pair: any) => {
  const corr = pair.correlation
  if (corr > 0.9) {
    return `${pair.asset1_name}和${pair.asset2_name}高度联动，同涨同跌`
  } else if (corr > 0.7) {
    return `两者趋势一致，可用于趋势确认`
  } else {
    return `存在一定联动性，需结合其他指标`
  }
}

const getHedgeAdvice = (pair: any) => {
  const corr = Math.abs(pair.correlation)
  if (corr > 0.7) {
    return `强对冲：${pair.asset1_name}可有效对冲${pair.asset2_name}风险`
  } else {
    return `中度对冲：可用于分散风险，但效果有限`
  }
}
</script>

<style scoped lang="scss">
.correlation-analysis {
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

.correlation-desc {
  color: #606266;
  font-size: 14px;
}

.hedge-advice {
  color: #606266;
  font-size: 14px;
}

.heatmap-container {
  min-height: 300px;
  padding: 20px;
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
