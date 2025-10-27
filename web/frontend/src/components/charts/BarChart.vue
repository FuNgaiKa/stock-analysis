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
            fontWeight: 600,
          },
        }
      : undefined,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
        shadowStyle: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
      formatter: (params: any) => {
        const param = params[0]
        return `${param.name}<br/>${param.seriesName}: <strong>${param.value.toFixed(2)}%</strong>`
      },
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: 'transparent',
      textStyle: {
        color: '#fff',
      },
    },
    grid: {
      left: props.horizontal ? '15%' : '3%',
      right: '4%',
      bottom: '3%',
      top: props.title ? '12%' : '3%',
      containLabel: true,
    },
    xAxis: props.horizontal
      ? {
          type: 'value',
          axisLine: {
            lineStyle: { color: '#d9d9d9' },
          },
          splitLine: {
            lineStyle: {
              type: 'dashed',
              color: '#e8e8e8',
            },
          },
        }
      : {
          type: 'category',
          data: names,
          axisLine: {
            lineStyle: { color: '#d9d9d9' },
          },
          axisLabel: {
            rotate: names.length > 6 ? 45 : 0,
            interval: 0,
            fontSize: 12,
          },
        },
    yAxis: props.horizontal
      ? {
          type: 'category',
          data: names,
          axisLine: {
            lineStyle: { color: '#d9d9d9' },
          },
          axisLabel: {
            fontSize: 12,
          },
        }
      : {
          type: 'value',
          axisLine: {
            lineStyle: { color: '#d9d9d9' },
          },
          splitLine: {
            lineStyle: {
              type: 'dashed',
              color: '#e8e8e8',
            },
          },
        },
    series: [
      {
        name: props.title || '涨跌幅',
        type: 'bar',
        data: values.map((val, idx) => ({
          value: val,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(
              props.horizontal ? 1 : 0,
              props.horizontal ? 0 : 0,
              props.horizontal ? 0 : 0,
              props.horizontal ? 0 : 1,
              [
                { offset: 0, color: colors[idx] },
                { offset: 1, color: colors[idx] + 'aa' }, // 添加透明度
              ]
            ),
            borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0],
          },
        })),
        barWidth: '60%',
        label: {
          show: true,
          position: props.horizontal ? 'right' : 'top',
          formatter: '{c}%',
          fontSize: 12,
          fontWeight: 600,
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
          },
        },
        animationDelay: (idx) => idx * 50,
        animationEasing: 'cubicOut',
      },
    ],
  }

  chart.setOption(option, true)
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
