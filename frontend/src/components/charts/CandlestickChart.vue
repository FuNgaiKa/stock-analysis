<template>
  <div ref="chartRef" :style="{ width: '100%', height: height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

interface Props {
  ohlc: Array<{
    date: string
    open: number
    high: number
    low: number
    close: number
    volume: number
  }>
  indicators?: {
    ma5?: number[]
    ma20?: number[]
    ma60?: number[]
    kdj?: {
      k: number[]
      d: number[]
      j: number[]
    }
    dmi_adx?: {
      adx: number[]
      '+di': number[]
      '-di': number[]
    }
    macd?: {
      macd: number[]
      signal: number[]
      histogram: number[]
    }
    volume_ma?: number[]
  }
  title?: string
  height?: string
  showKDJ?: boolean
  showDMI?: boolean
  showMACD?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'K线图',
  height: '600px',
  showKDJ: true,
  showDMI: true,
  showMACD: false
})

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

// 计算网格布局
const calculateGrids = () => {
  const grids = []
  let top = 60
  const mainHeight = props.showKDJ || props.showDMI || props.showMACD ? 45 : 60

  // 主图 (K线 + 成交量)
  grids.push({ left: '8%', right: '3%', top: `${top}px`, height: `${mainHeight}%` })
  top += mainHeight + 5

  // 副图
  let subCount = 0
  if (props.showKDJ) subCount++
  if (props.showDMI) subCount++
  if (props.showMACD) subCount++

  if (subCount > 0) {
    const subHeight = (90 - mainHeight - 10) / subCount
    if (props.showKDJ) {
      grids.push({ left: '8%', right: '3%', top: `${top}%`, height: `${subHeight}%` })
      top += subHeight + 2
    }
    if (props.showDMI) {
      grids.push({ left: '8%', right: '3%', top: `${top}%`, height: `${subHeight}%` })
      top += subHeight + 2
    }
    if (props.showMACD) {
      grids.push({ left: '8%', right: '3%', top: `${top}%`, height: `${subHeight}%` })
    }
  }

  return grids
}

const initChart = () => {
  if (!chartRef.value || !props.ohlc || props.ohlc.length === 0) return

  if (chart) {
    chart.dispose()
  }

  chart = echarts.init(chartRef.value)

  // 提取数据
  const dates = props.ohlc.map(item => item.date)
  const ohlcData = props.ohlc.map(item => [item.open, item.close, item.low, item.high])
  const volumes = props.ohlc.map(item => item.volume)

  const grids = calculateGrids()
  const xAxes = grids.map((_, index) => ({
    type: 'category',
    data: dates,
    gridIndex: index,
    boundaryGap: true,
    axisLine: { lineStyle: { color: '#8392A5' } },
    axisLabel: {
      show: index === grids.length - 1, // 只在最后一个x轴显示标签
      formatter: (value: string) => {
        const date = new Date(value)
        return `${date.getMonth() + 1}/${date.getDate()}`
      }
    },
    splitLine: { show: false }
  }))

  let yAxisIndex = 0
  const yAxes = []
  const series: any[] = []

  // Y轴: 主图价格
  yAxes.push({
    scale: true,
    gridIndex: 0,
    splitNumber: 4,
    axisLine: { lineStyle: { color: '#8392A5' } },
    splitLine: { show: true, lineStyle: { color: '#E5E9EF' } }
  })

  // 系列: K线
  series.push({
    name: 'K线',
    type: 'candlestick',
    data: ohlcData,
    xAxisIndex: 0,
    yAxisIndex: yAxisIndex++,
    itemStyle: {
      color: '#EF5350',      // 阳线
      color0: '#26A69A',     // 阴线
      borderColor: '#EF5350',
      borderColor0: '#26A69A'
    }
  })

  // 系列: 均线
  if (props.indicators?.ma5) {
    series.push({
      name: 'MA5',
      type: 'line',
      data: props.indicators.ma5,
      xAxisIndex: 0,
      yAxisIndex: 0,
      smooth: true,
      lineStyle: { width: 1, color: '#FF6B6B' },
      showSymbol: false
    })
  }
  if (props.indicators?.ma20) {
    series.push({
      name: 'MA20',
      type: 'line',
      data: props.indicators.ma20,
      xAxisIndex: 0,
      yAxisIndex: 0,
      smooth: true,
      lineStyle: { width: 1, color: '#4ECDC4' },
      showSymbol: false
    })
  }
  if (props.indicators?.ma60) {
    series.push({
      name: 'MA60',
      type: 'line',
      data: props.indicators.ma60,
      xAxisIndex: 0,
      yAxisIndex: 0,
      smooth: true,
      lineStyle: { width: 1, color: '#95E1D3' },
      showSymbol: false
    })
  }

  // Y轴: 成交量
  yAxes.push({
    scale: true,
    gridIndex: 0,
    position: 'right',
    splitNumber: 2,
    axisLabel: { show: false },
    axisLine: { show: false },
    splitLine: { show: false }
  })

  // 系列: 成交量柱状图
  series.push({
    name: '成交量',
    type: 'bar',
    data: volumes,
    xAxisIndex: 0,
    yAxisIndex: yAxisIndex++,
    itemStyle: {
      color: (params: any) => {
        const dataIndex = params.dataIndex
        if (dataIndex === 0) return '#26A69A'
        const current = props.ohlc[dataIndex]
        const prev = props.ohlc[dataIndex - 1]
        return current.close >= prev.close ? '#EF5350' : '#26A69A'
      }
    },
    barWidth: '60%',
    z: -1,
    opacity: 0.3
  })

  let gridIndex = 1

  // KDJ副图
  if (props.showKDJ && props.indicators?.kdj) {
    yAxes.push({
      scale: true,
      gridIndex: gridIndex,
      splitNumber: 2,
      axisLine: { lineStyle: { color: '#8392A5' } },
      splitLine: { show: true, lineStyle: { color: '#E5E9EF' } }
    })

    series.push(
      {
        name: 'K',
        type: 'line',
        data: props.indicators.kdj.k,
        xAxisIndex: gridIndex,
        yAxisIndex: yAxisIndex,
        smooth: true,
        lineStyle: { width: 1.5, color: '#FF6B6B' },
        showSymbol: false
      },
      {
        name: 'D',
        type: 'line',
        data: props.indicators.kdj.d,
        xAxisIndex: gridIndex,
        yAxisIndex: yAxisIndex,
        smooth: true,
        lineStyle: { width: 1.5, color: '#4ECDC4' },
        showSymbol: false
      },
      {
        name: 'J',
        type: 'line',
        data: props.indicators.kdj.j,
        xAxisIndex: gridIndex,
        yAxisIndex: yAxisIndex,
        smooth: true,
        lineStyle: { width: 1.5, color: '#95E1D3' },
        showSymbol: false
      }
    )

    yAxisIndex++
    gridIndex++
  }

  // DMI/ADX副图
  if (props.showDMI && props.indicators?.dmi_adx) {
    yAxes.push({
      scale: true,
      gridIndex: gridIndex,
      splitNumber: 2,
      axisLine: { lineStyle: { color: '#8392A5' } },
      splitLine: { show: true, lineStyle: { color: '#E5E9EF' } }
    })

    series.push(
      {
        name: 'ADX',
        type: 'line',
        data: props.indicators.dmi_adx.adx,
        xAxisIndex: gridIndex,
        yAxisIndex: yAxisIndex,
        smooth: true,
        lineStyle: { width: 2, color: '#FFA726' },
        showSymbol: false
      },
      {
        name: '+DI',
        type: 'line',
        data: props.indicators.dmi_adx['+di'],
        xAxisIndex: gridIndex,
        yAxisIndex: yAxisIndex,
        smooth: true,
        lineStyle: { width: 1.5, color: '#66BB6A' },
        showSymbol: false
      },
      {
        name: '-DI',
        type: 'line',
        data: props.indicators.dmi_adx['-di'],
        xAxisIndex: gridIndex,
        yAxisIndex: yAxisIndex,
        smooth: true,
        lineStyle: { width: 1.5, color: '#EF5350' },
        showSymbol: false
      }
    )

    yAxisIndex++
    gridIndex++
  }

  // MACD副图
  if (props.showMACD && props.indicators?.macd) {
    yAxes.push({
      scale: true,
      gridIndex: gridIndex,
      splitNumber: 2,
      axisLine: { lineStyle: { color: '#8392A5' } },
      splitLine: { show: true, lineStyle: { color: '#E5E9EF' } }
    })

    series.push(
      {
        name: 'MACD',
        type: 'line',
        data: props.indicators.macd.macd,
        xAxisIndex: gridIndex,
        yAxisIndex: yAxisIndex,
        smooth: true,
        lineStyle: { width: 1.5, color: '#2196F3' },
        showSymbol: false
      },
      {
        name: 'Signal',
        type: 'line',
        data: props.indicators.macd.signal,
        xAxisIndex: gridIndex,
        yAxisIndex: yAxisIndex,
        smooth: true,
        lineStyle: { width: 1.5, color: '#FFA726' },
        showSymbol: false
      },
      {
        name: 'Histogram',
        type: 'bar',
        data: props.indicators.macd.histogram,
        xAxisIndex: gridIndex,
        yAxisIndex: yAxisIndex,
        itemStyle: {
          color: (params: any) => params.value >= 0 ? '#EF5350' : '#26A69A'
        }
      }
    )
  }

  const option: echarts.EChartOption = {
    title: {
      text: props.title,
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderWidth: 1,
      borderColor: '#ccc',
      textStyle: { color: '#000' },
      formatter: (params: any) => {
        if (!params || params.length === 0) return ''
        const dateIndex = params[0].dataIndex
        const date = dates[dateIndex]
        const ohlcItem = props.ohlc[dateIndex]

        let html = `<div style="padding: 8px;">
          <div style="font-weight: bold; margin-bottom: 8px;">${date}</div>
          <div style="margin-bottom: 4px;">
            开: ${ohlcItem.open.toFixed(2)} &nbsp;
            高: ${ohlcItem.high.toFixed(2)} &nbsp;
            低: ${ohlcItem.low.toFixed(2)} &nbsp;
            收: ${ohlcItem.close.toFixed(2)}
          </div>
          <div style="margin-bottom: 4px;">成交量: ${(ohlcItem.volume / 1000000).toFixed(2)}M</div>`

        // 显示技术指标
        params.forEach((param: any) => {
          if (param.seriesName && param.value && param.seriesName !== 'K线' && param.seriesName !== '成交量') {
            html += `<div>${param.marker} ${param.seriesName}: ${typeof param.value === 'number' ? param.value.toFixed(2) : param.value}</div>`
          }
        })

        html += '</div>'
        return html
      }
    },
    legend: {
      top: 30,
      data: ['K线', 'MA5', 'MA20', 'MA60', '成交量', 'K', 'D', 'J', 'ADX', '+DI', '-DI', 'MACD', 'Signal', 'Histogram']
    },
    grid: grids,
    xAxis: xAxes,
    yAxis: yAxes,
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: Array.from({ length: grids.length }, (_, i) => i),
        start: 0,
        end: 100
      },
      {
        show: true,
        xAxisIndex: Array.from({ length: grids.length }, (_, i) => i),
        type: 'slider',
        bottom: 10,
        start: 0,
        end: 100
      }
    ],
    series
  }

  chart.setOption(option)

  // 响应式
  const resizeObserver = new ResizeObserver(() => {
    chart?.resize()
  })
  resizeObserver.observe(chartRef.value)
}

watch(() => [props.ohlc, props.indicators, props.showKDJ, props.showDMI, props.showMACD], () => {
  initChart()
}, { deep: true })

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
/* 图表容器样式 */
</style>
