<template>
  <div ref="chartRef" :style="{ height, width }" v-loading="loading"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

interface Props {
  data: Array<{ name: string; value: number }>
  height?: string
  width?: string
  loading?: boolean
  title?: string
  maxValue?: number
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  width: '100%',
  loading: false,
  maxValue: 100,
})

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)
  updateChart()

  window.addEventListener('resize', handleResize)
}

// 更新图表
const updateChart = () => {
  if (!chart || !props.data || props.data.length === 0) return

  // 准备雷达图指标
  const indicators = props.data.map((item) => ({
    name: item.name,
    max: props.maxValue,
  }))

  // 准备数据
  const seriesData = props.data.map((item) => item.value)

  const option: EChartsOption = {
    title: props.title
      ? {
          text: props.title,
          left: 'center',
          textStyle: {
            fontSize: 16,
            fontWeight: 'normal',
          },
        }
      : undefined,
    tooltip: {
      trigger: 'item',
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitNumber: 4,
      name: {
        textStyle: {
          color: '#666',
          fontSize: 12,
        },
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(24, 144, 255, 0.2)',
        },
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(24, 144, 255, 0.05)', 'rgba(24, 144, 255, 0.1)'],
        },
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(24, 144, 255, 0.5)',
        },
      },
    },
    series: [
      {
        name: props.title || 'Data',
        type: 'radar',
        data: [
          {
            value: seriesData,
            name: props.title || 'Data',
            itemStyle: {
              color: '#1890ff',
            },
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
                { offset: 1, color: 'rgba(24, 144, 255, 0.1)' },
              ]),
            },
            lineStyle: {
              width: 2,
              color: '#1890ff',
            },
          },
        ],
      },
    ],
  }

  chart.setOption(option)
}

// 响应式调整
const handleResize = () => {
  chart?.resize()
}

// 监听数据变化
watch(
  () => props.data,
  () => {
    nextTick(() => {
      updateChart()
    })
  },
  { deep: true }
)

// 监听加载状态
watch(
  () => props.loading,
  (newVal) => {
    if (!newVal) {
      nextTick(() => {
        updateChart()
      })
    }
  }
)

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
/* ECharts容器 */
</style>
