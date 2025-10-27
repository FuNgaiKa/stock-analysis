/**
 * 自动刷新数据 Composable
 * 提供定时刷新和手动刷新功能
 */

import { ref, onMounted, onUnmounted } from 'vue'

interface UseAutoRefreshOptions {
  /** 刷新回调函数 */
  onRefresh: () => Promise<void> | void
  /** 刷新间隔(毫秒)，默认60秒 */
  interval?: number
  /** 是否立即执行，默认true */
  immediate?: boolean
  /** 是否启用自动刷新，默认true */
  enabled?: boolean
}

export function useAutoRefresh(options: UseAutoRefreshOptions) {
  const {
    onRefresh,
    interval = 60000, // 默认60秒
    immediate = true,
    enabled = true,
  } = options

  const isRefreshing = ref(false)
  const lastRefreshTime = ref<Date | null>(null)
  let timer: number | null = null

  // 执行刷新
  const refresh = async () => {
    if (isRefreshing.value) return

    try {
      isRefreshing.value = true
      await onRefresh()
      lastRefreshTime.value = new Date()
    } catch (error) {
      console.error('数据刷新失败:', error)
    } finally {
      isRefreshing.value = false
    }
  }

  // 启动自动刷新
  const start = () => {
    if (!enabled) return

    stop() // 先停止之前的定时器

    if (immediate) {
      refresh()
    }

    timer = window.setInterval(() => {
      refresh()
    }, interval)
  }

  // 停止自动刷新
  const stop = () => {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  }

  // 组件挂载时启动
  onMounted(() => {
    if (enabled) {
      start()
    }
  })

  // 组件卸载时停止
  onUnmounted(() => {
    stop()
  })

  return {
    isRefreshing,
    lastRefreshTime,
    refresh,
    start,
    stop,
  }
}
