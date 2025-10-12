/**
 * Vue Router配置
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/components/layout/MainLayout.vue'),
    redirect: '/market-overview',
    children: [
      {
        path: '/market-overview',
        name: 'MarketOverview',
        component: () => import('@/views/MarketOverview.vue'),
        meta: {
          title: '市场概览',
          icon: 'DataLine',
        },
      },
      {
        path: '/index-analysis',
        name: 'IndexAnalysis',
        component: () => import('@/views/IndexAnalysis.vue'),
        meta: {
          title: '指数分析',
          icon: 'TrendCharts',
        },
      },
      {
        path: '/vix-analysis',
        name: 'VixAnalysis',
        component: () => import('@/views/VixAnalysis.vue'),
        meta: {
          title: 'VIX恐慌指数',
          icon: 'Orange',
        },
      },
      {
        path: '/sector-rotation',
        name: 'SectorRotation',
        component: () => import('@/views/SectorRotation.vue'),
        meta: {
          title: '行业轮动',
          icon: 'Refresh',
        },
      },
      {
        path: '/backtest',
        name: 'Backtest',
        component: () => import('@/views/Backtest.vue'),
        meta: {
          title: '历史回测',
          icon: 'DataAnalysis',
        },
      },
      {
        path: '/position-analysis',
        name: 'PositionAnalysis',
        component: () => import('@/views/PositionAnalysis.vue'),
        meta: {
          title: '历史点位对比',
          icon: 'Position',
        },
      },
      {
        path: '/hk-stock-analysis',
        name: 'HKStockAnalysis',
        component: () => import('@/views/HKStockAnalysis.vue'),
        meta: {
          title: '港股市场分析',
          icon: 'Location',
        },
      },
      {
        path: '/compound-calculator',
        name: 'CompoundCalculator',
        component: () => import('@/views/CompoundCalculator.vue'),
        meta: {
          title: '复合收益计算器',
          icon: 'Money',
        },
      },
      {
        path: '/docs',
        name: 'Docs',
        component: () => import('@/views/Docs.vue'),
        meta: {
          title: '使用文档',
          icon: 'Document',
        },
      },
    ],
  },
]

// 创建路由器
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 金融工具平台`
  }
  next()
})

export default router
