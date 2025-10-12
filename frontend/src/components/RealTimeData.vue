<template>
  <el-card class="realtime-card">
    <template #header>
      <div class="card-header">
        <span class="card-title">📡 实时市场数据</span>
        <el-tag :type="connectionStatus === 'connected' ? 'success' : 'danger'" size="small">
          {{ connectionStatus === 'connected' ? '● 已连接' : '○ 未连接' }}
        </el-tag>
      </div>
    </template>

    <div class="realtime-content">
      <!-- 市场情绪指数 -->
      <div v-if="marketData.sentiment" class="sentiment-section">
        <h4>市场情绪指数</h4>
        <div class="sentiment-display">
          <div class="sentiment-emoji">{{ marketData.sentiment.emoji }}</div>
          <div class="sentiment-score">{{ marketData.sentiment.score?.toFixed(1) || '-' }}</div>
          <div class="sentiment-rating">{{ marketData.sentiment.rating || '-' }}</div>
        </div>
      </div>

      <!-- 主要指数 -->
      <div v-if="marketData.indices" class="indices-section">
        <h4>主要指数</h4>
        <el-row :gutter="15">
          <el-col
            v-for="(data, symbol) in marketData.indices"
            :key="symbol"
            :xs="24" :sm="12" :md="8"
          >
            <div class="index-box">
              <div class="index-name">{{ data.name }}</div>
              <div class="index-price">{{ data.price?.toFixed(2) || '-' }}</div>
              <div
                class="index-change"
                :class="getChangeClass(data.change_pct)"
              >
                {{ data.change_pct > 0 ? '+' : '' }}{{ data.change_pct?.toFixed(2) || '-' }}%
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 更新时间 -->
      <div class="update-time">
        最后更新: {{ lastUpdate || '-' }}
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

const connectionStatus = ref<'connected' | 'disconnected'>('disconnected')
const marketData = ref<any>({
  sentiment: null,
  indices: null
})
const lastUpdate = ref('')
let ws: WebSocket | null = null

const connectWebSocket = () => {
  try {
    ws = new WebSocket('ws://localhost:8000/ws/market-data')

    ws.onopen = () => {
      connectionStatus.value = 'connected'
      ElMessage.success('实时数据连接成功')
      console.log('WebSocket已连接')
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        console.log('收到WebSocket消息:', message)

        if (message.type === 'market_data') {
          marketData.value = message.data
          lastUpdate.value = new Date(message.timestamp).toLocaleTimeString('zh-CN')
        } else if (message.type === 'error') {
          console.error('数据错误:', message.message)
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      connectionStatus.value = 'disconnected'
    }

    ws.onclose = () => {
      connectionStatus.value = 'disconnected'
      console.log('WebSocket已断开')

      // 3秒后尝试重连
      setTimeout(() => {
        if (connectionStatus.value === 'disconnected') {
          console.log('尝试重新连接WebSocket...')
          connectWebSocket()
        }
      }, 3000)
    }
  } catch (error) {
    console.error('创建WebSocket连接失败:', error)
    connectionStatus.value = 'disconnected'
  }
}

const getChangeClass = (change: number) => {
  if (!change) return ''
  return change > 0 ? 'positive' : 'negative'
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
})
</script>

<style scoped lang="scss">
.realtime-card {
  margin-bottom: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
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

.realtime-content {
  h4 {
    margin: 0 0 15px 0;
    font-size: 14px;
    color: #909399;
  }
}

.sentiment-section {
  margin-bottom: 25px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;

  .sentiment-display {
    display: flex;
    align-items: center;
    gap: 20px;

    .sentiment-emoji {
      font-size: 48px;
    }

    .sentiment-score {
      font-size: 36px;
      font-weight: 700;
    }

    .sentiment-rating {
      font-size: 18px;
      opacity: 0.9;
    }
  }
}

.indices-section {
  margin-bottom: 20px;
}

.index-box {
  padding: 15px;
  border-radius: 8px;
  background: #f5f7fa;
  text-align: center;
  margin-bottom: 15px;

  .index-name {
    font-size: 14px;
    color: #909399;
    margin-bottom: 8px;
  }

  .index-price {
    font-size: 24px;
    font-weight: 700;
    color: #303133;
    margin-bottom: 4px;
  }

  .index-change {
    font-size: 16px;
    font-weight: 600;

    &.positive {
      color: #67c23a;
    }

    &.negative {
      color: #f56c6c;
    }
  }
}

.update-time {
  text-align: center;
  font-size: 12px;
  color: #909399;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
}
</style>
