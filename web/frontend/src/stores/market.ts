/**
 * 市场数据状态管理
 */

import { defineStore } from 'pinia'
import { marketApi } from '@/services/api'
import type {
  IndexInfo,
  SingleIndexAnalysis,
  MultiIndexAnalysis,
} from '@/types'

interface MarketState {
  // 指数列表
  indices: IndexInfo[]
  defaultIndices: string[]

  // 当前选中
  selectedIndex: string
  selectedIndices: string[]

  // 分析配置
  tolerance: number
  periods: number[]
  phase: '1' | '2' | '3'

  // 分析结果
  singleResult: SingleIndexAnalysis | null
  multipleResult: MultiIndexAnalysis | null

  // 加载状态
  loading: boolean
  analyzing: boolean
}

export const useMarketStore = defineStore('market', {
  state: (): MarketState => ({
    indices: [],
    defaultIndices: [],
    selectedIndex: 'SPX',
    selectedIndices: ['SPX', 'NASDAQ', 'NDX'],
    tolerance: 0.05,
    periods: [5, 10, 20, 60],
    phase: '3',
    singleResult: null,
    multipleResult: null,
    loading: false,
    analyzing: false,
  }),

  getters: {
    /**
     * 获取Phase配置
     */
    phaseConfig(state) {
      return {
        use_phase2: state.phase >= '2',
        use_phase3: state.phase === '3',
      }
    },

    /**
     * 获取当前选中指数的信息
     */
    currentIndexInfo(state): IndexInfo | undefined {
      return state.indices.find((idx) => idx.code === state.selectedIndex)
    },

    /**
     * 检查是否有分析结果
     */
    hasResults(state): boolean {
      return !!(state.singleResult || state.multipleResult)
    },
  },

  actions: {
    /**
     * 获取指数列表
     */
    async fetchIndices() {
      try {
        this.loading = true
        const [indices, defaultIndices] = await Promise.all([
          marketApi.getIndices(),
          marketApi.getDefaultIndices(),
        ])

        this.indices = indices
        this.defaultIndices = defaultIndices

        // 设置默认选中
        if (defaultIndices.length > 0) {
          this.selectedIndex = defaultIndices[0]
          this.selectedIndices = defaultIndices
        }

        return indices
      } catch (error) {
        console.error('获取指数列表失败:', error)
        ElMessage.error('获取指数列表失败')
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 单指数分析
     * @param indexCode 指数代码(可选,默认使用selectedIndex)
     */
    async analyzeSingle(indexCode?: string) {
      try {
        this.analyzing = true
        this.singleResult = null

        const code = indexCode || this.selectedIndex

        ElMessage.info(`正在分析 ${code}...`)

        const result = await marketApi.analyzeSingle({
          index_code: code,
          tolerance: this.tolerance,
          periods: this.periods,
          ...this.phaseConfig,
        })

        this.singleResult = result

        ElMessage.success('分析完成!')

        return result
      } catch (error) {
        console.error('单指数分析失败:', error)
        ElMessage.error('分析失败,请稍后重试')
        throw error
      } finally {
        this.analyzing = false
      }
    },

    /**
     * 多指数联合分析
     * @param indices 指数代码列表(可选,默认使用selectedIndices)
     */
    async analyzeMultiple(indices?: string[]) {
      try {
        this.analyzing = true
        this.multipleResult = null

        const codes = indices || this.selectedIndices

        if (codes.length === 0) {
          ElMessage.warning('请至少选择一个指数')
          return
        }

        ElMessage.info(`正在分析 ${codes.join(', ')}...`)

        const result = await marketApi.analyzeMultiple({
          indices: codes,
          tolerance: this.tolerance,
          periods: this.periods,
          ...this.phaseConfig,
        })

        this.multipleResult = result

        ElMessage.success('分析完成!')

        return result
      } catch (error) {
        console.error('多指数分析失败:', error)
        ElMessage.error('分析失败,请稍后重试')
        throw error
      } finally {
        this.analyzing = false
      }
    },

    /**
     * 设置分析配置
     */
    setConfig(config: {
      tolerance?: number
      periods?: number[]
      phase?: '1' | '2' | '3'
    }) {
      if (config.tolerance !== undefined) {
        this.tolerance = config.tolerance
      }
      if (config.periods !== undefined) {
        this.periods = config.periods
      }
      if (config.phase !== undefined) {
        this.phase = config.phase
      }
    },

    /**
     * 重置结果
     */
    resetResults() {
      this.singleResult = null
      this.multipleResult = null
    },
  },
})
