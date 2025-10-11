<template>
  <el-card class="metric-card" :class="cardClass" shadow="hover">
    <div class="metric-content">
      <div class="metric-label">{{ label }}</div>
      <div class="metric-value">
        {{ prefix }}{{ formattedValue }}{{ suffix }}
      </div>
      <div v-if="change !== undefined" class="metric-change" :class="changeClass">
        <el-icon>
          <CaretTop v-if="change > 0" />
          <CaretBottom v-if="change < 0" />
          <Minus v-if="change === 0" />
        </el-icon>
        <span>{{ formatChange(change) }}</span>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  label: string
  value: string | number
  change?: number
  prefix?: string
  suffix?: string
  trend?: 'up' | 'down' | 'neutral'
}

const props = withDefaults(defineProps<Props>(), {
  prefix: '',
  suffix: '',
})

// 格式化值
const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})

// 格式化变化值
const formatChange = (val: number) => {
  const formatted = Math.abs(val)
  return val > 0 ? `+${formatted}%` : `${formatted}%`
}

// 卡片样式类
const cardClass = computed(() => {
  if (props.trend) {
    return `trend-${props.trend}`
  }
  if (props.change !== undefined) {
    if (props.change > 0) return 'trend-up'
    if (props.change < 0) return 'trend-down'
  }
  return ''
})

// 变化值样式类
const changeClass = computed(() => {
  if (props.change === undefined) return ''
  if (props.change > 0) return 'change-up'
  if (props.change < 0) return 'change-down'
  return 'change-neutral'
})
</script>

<style scoped>
.metric-card {
  height: 100%;
  transition: all 0.3s;
}

.metric-card:hover {
  transform: translateY(-4px);
}

.metric-content {
  text-align: center;
}

.metric-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
}

.dark .metric-label {
  color: #a8abb2;
}

.metric-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.dark .metric-value {
  color: #e5eaf3;
}

.metric-change {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 500;
}

.change-up {
  color: #67c23a;
}

.change-down {
  color: #f56c6c;
}

.change-neutral {
  color: #909399;
}

/* 趋势边框 */
.trend-up {
  border-left: 4px solid #67c23a;
}

.trend-down {
  border-left: 4px solid #f56c6c;
}

.trend-neutral {
  border-left: 4px solid #909399;
}
</style>
