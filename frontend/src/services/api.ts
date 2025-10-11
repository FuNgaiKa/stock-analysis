/**
 * API客户端服务
 * 封装所有后端API调用
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  IndexInfo,
  SingleIndexAnalysis,
  MultiIndexAnalysis,
  ApiResponse,
} from '@/types'

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 60000, // 60秒超时(分析可能需要时间)
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError) => {
    // 统一错误处理
    if (error.response) {
      // 服务器返回错误
      const status = error.response.status
      let message = '请求失败'

      switch (status) {
        case 400:
          message = '请求参数错误'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        case 502:
          message = '网关错误'
          break
        case 503:
          message = '服务暂时不可用'
          break
        default:
          message = `请求失败(${status})`
      }

      ElMessage.error(message)
    } else if (error.request) {
      // 请求发送但没有响应
      ElMessage.error('网络连接失败,请检查您的网络')
    } else {
      // 其他错误
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

// ==================== API方法 ====================

/**
 * 市场分析API
 */
export const marketApi = {
  /**
   * 获取支持的指数列表
   */
  async getIndices(): Promise<IndexInfo[]> {
    const { data } = await apiClient.get<IndexInfo[]>('/api/indices')
    return data
  },

  /**
   * 获取默认指数列表
   */
  async getDefaultIndices(): Promise<string[]> {
    const { data } = await apiClient.get<{ indices: string[] }>('/api/indices/default')
    return data.indices
  },

  /**
   * 获取当前点位
   * @param indices 指数代码列表(可选)
   */
  async getCurrentPositions(indices?: string[]): Promise<any> {
    const params = indices ? { indices } : {}
    const { data } = await apiClient.get<ApiResponse>('/api/current-positions', { params })
    return data.data
  },

  /**
   * 单指数分析
   * @param params 分析参数
   */
  async analyzeSingle(params: {
    index_code: string
    tolerance?: number
    periods?: number[]
    use_phase2?: boolean
    use_phase3?: boolean
  }): Promise<SingleIndexAnalysis> {
    const {
      index_code,
      tolerance = 0.05,
      periods = [5, 10, 20, 60],
      use_phase2 = false,
      use_phase3 = false,
    } = params

    const { data } = await apiClient.post<ApiResponse<SingleIndexAnalysis>>(
      '/api/analyze/single',
      null,
      {
        params: {
          index_code,
          tolerance,
          periods: periods.join(','), // 数组转字符串
          use_phase2,
          use_phase3,
        },
      }
    )

    return data.data
  },

  /**
   * 多指数联合分析
   * @param params 分析参数
   */
  async analyzeMultiple(params: {
    indices: string[]
    tolerance?: number
    periods?: number[]
    use_phase2?: boolean
    use_phase3?: boolean
  }): Promise<MultiIndexAnalysis> {
    const {
      indices,
      tolerance = 0.05,
      periods = [5, 10, 20, 60],
      use_phase2 = false,
      use_phase3 = false,
    } = params

    const { data } = await apiClient.post<ApiResponse<MultiIndexAnalysis>>(
      '/api/analyze/multiple',
      {
        indices,
        tolerance,
        periods,
        use_phase2,
        use_phase3,
      }
    )

    return data.data
  },

  /**
   * 健康检查
   */
  async healthCheck(): Promise<any> {
    const { data } = await apiClient.get('/api/health')
    return data
  },
}

/**
 * 导出axios实例,供其他地方使用
 */
export default apiClient
