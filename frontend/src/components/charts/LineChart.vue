<template>
  <div ref="chartRef" :style="{ height, width }" v-loading="loading"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

interface Props {
  data: any[]
  height?: string
  width?: string
  loading?: boolean
  xField?: string
  yField?: string
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  width: '100%',
  loading: false,
  xField: 'date',
  yField: 'value',
})

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)
  updateChart()

  // 响应式调整
  window.addEventListener('resize', handleResize)
}

// 更新图表
const updateChart = () => {
  if (!chart || !props.data || props.data.length === 0) return

  const xData = props.data.map((item) => item[props.xField])
  const yData = props.data.map((item) => item[props.yField])

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
      trigger: 'axis',
      formatter: (params: any) => {
        const param = params[0]
        return `${param.name}<br/>${param.seriesName}: ${param.value}`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: xData,
      boundaryGap: false,
      axisLine: {
        lineStyle: {
          color: '#8c8c8c',
        },
      },
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: '#8c8c8c',
        },
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
        },
      },
    },
    series: [
      {
        name: props.title || 'Value',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: yData,
        itemStyle: {
          color: '#1890ff',
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.05)' },
          ]),
        },
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
