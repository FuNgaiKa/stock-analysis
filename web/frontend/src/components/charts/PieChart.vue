<template>
  <div ref="chartRef" :style="{ width: '100%', height }" class="pie-chart" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

interface Props {
  data: Array<{ name: string; value: number; color?: string }>
  title?: string
  height?: string
  loading?: boolean
  radius?: string | string[] // 支持环形图
  roseType?: boolean | 'radius' | 'area' // 南丁格尔玫瑰图
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  height: '400px',
  loading: false,
  radius: '50%',
  roseType: false,
})

const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

// 更新图表
const updateChart = () => {
  if (!chartInstance) return

  const option: EChartsOption = {
    title: {
      text: props.title,
      left: 'center',
      top: 0,
      textStyle: {
        fontSize: 16,
        fontWeight: 600,
      },
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: 'transparent',
      textStyle: {
        color: '#fff',
      },
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      left: 'center',
      icon: 'circle',
      textStyle: {
        fontSize: 13,
      },
    },
    series: [
      {
        name: props.title || '数据分布',
        type: 'pie',
        radius: props.radius,
        center: ['50%', '48%'],
        roseType: props.roseType,
        data: props.data.map((item) => ({
          name: item.name,
          value: item.value,
          itemStyle: item.color ? { color: item.color } : undefined,
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 15,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
          scaleSize: 10, // 高亮时放大
        },
        label: {
          show: true,
          formatter: '{b}: {d}%',
          fontSize: 13,
          fontWeight: 600,
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 10,
        },
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: (idx) => idx * 100,
      },
    ],
  }

  chartInstance.setOption(option, true)
}

// 响应式处理
const handleResize = () => {
  chartInstance?.resize()
}

// 监听数据变化
watch(
  () => [props.data, props.loading],
  () => {
    if (!props.loading) {
      updateChart()
    }
  },
  { deep: true }
)

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.pie-chart {
  min-height: 300px;
}
</style>
