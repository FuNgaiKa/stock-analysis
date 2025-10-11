<template>
  <div ref="chartRef" :style="{ height, width }" v-loading="loading"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

interface Props {
  data: Array<{ name: string; value: number; color?: string }>
  height?: string
  width?: string
  loading?: boolean
  title?: string
  horizontal?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  width: '100%',
  loading: false,
  horizontal: false,
})

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  updateChart()
  window.addEventListener('resize', handleResize)
}

const updateChart = () => {
  if (!chart || !props.data || props.data.length === 0) return

  const names = props.data.map((item) => item.name)
  const values = props.data.map((item) => item.value)
  const colors = props.data.map((item) => item.color || '#1890ff')

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
      axisPointer: {
        type: 'shadow',
      },
      formatter: (params: any) => {
        const param = params[0]
        return `${param.name}<br/>${param.seriesName}: ${param.value}%`
      },
    },
    grid: {
      left: props.horizontal ? '15%' : '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: props.horizontal
      ? {
          type: 'value',
          axisLine: {
            lineStyle: { color: '#8c8c8c' },
          },
        }
      : {
          type: 'category',
          data: names,
          axisLine: {
            lineStyle: { color: '#8c8c8c' },
          },
          axisLabel: {
            rotate: names.length > 6 ? 45 : 0,
            interval: 0,
          },
        },
    yAxis: props.horizontal
      ? {
          type: 'category',
          data: names,
          axisLine: {
            lineStyle: { color: '#8c8c8c' },
          },
        }
      : {
          type: 'value',
          axisLine: {
            lineStyle: { color: '#8c8c8c' },
          },
          splitLine: {
            lineStyle: { type: 'dashed' },
          },
        },
    series: [
      {
        name: props.title || 'Value',
        type: 'bar',
        data: values.map((val, idx) => ({
          value: val,
          itemStyle: {
            color: colors[idx],
          },
        })),
        barWidth: '60%',
        label: {
          show: true,
          position: props.horizontal ? 'right' : 'top',
          formatter: '{c}%',
        },
      },
    ],
  }

  chart.setOption(option)
}

const handleResize = () => {
  chart?.resize()
}

watch(
  () => props.data,
  () => {
    nextTick(() => {
      updateChart()
    })
  },
  { deep: true }
)

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
