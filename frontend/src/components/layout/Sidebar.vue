<template>
  <div class="sidebar">
    <!-- 折叠按钮 -->
    <div class="toggle-btn" @click="handleToggle">
      <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
    </div>

    <!-- 导航菜单 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="collapsed"
      :collapse-transition="false"
      router
      class="sidebar-menu"
    >
      <el-menu-item index="/market-overview">
        <el-icon><DataLine /></el-icon>
        <template #title>{{ $t('menu.marketOverview') }}</template>
      </el-menu-item>

      <el-menu-item index="/index-analysis">
        <el-icon><TrendCharts /></el-icon>
        <template #title>{{ $t('menu.indexAnalysis') }}</template>
      </el-menu-item>

      <el-menu-item index="/vix-analysis">
        <el-icon><Orange /></el-icon>
        <template #title>{{ $t('menu.vixAnalysis') }}</template>
      </el-menu-item>

      <el-menu-item index="/sector-rotation">
        <el-icon><Refresh /></el-icon>
        <template #title>{{ $t('menu.sectorRotation') }}</template>
      </el-menu-item>

      <el-menu-item index="/backtest">
        <el-icon><DataAnalysis /></el-icon>
        <template #title>{{ $t('menu.backtest') }}</template>
      </el-menu-item>

      <el-menu-item index="/position-analysis">
        <el-icon><Position /></el-icon>
        <template #title>{{ $t('menu.positionAnalysis') }}</template>
      </el-menu-item>

      <el-divider />

      <el-menu-item index="/hk-stock-analysis">
        <el-icon><Location /></el-icon>
        <template #title>{{ $t('menu.hkStockAnalysis') }}</template>
      </el-menu-item>

      <el-menu-item index="/compound-calculator">
        <el-icon><Money /></el-icon>
        <template #title>{{ $t('menu.compoundCalculator') }}</template>
      </el-menu-item>

      <el-divider />

      <el-menu-item index="/docs">
        <el-icon><Document /></el-icon>
        <template #title>{{ $t('menu.docs') }}</template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

// Props
interface Props {
  collapsed: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  toggle: []
}>()

const route = useRoute()

// 当前激活菜单
const activeMenu = computed(() => route.path)

// 切换折叠
const handleToggle = () => {
  emit('toggle')
}
</script>

<style scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toggle-btn {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-bottom: 1px solid #e4e7ed;
  transition: all 0.3s;
}

.toggle-btn:hover {
  background-color: #f5f7fa;
}

.dark .toggle-btn {
  border-bottom-color: #424242;
}

.dark .toggle-btn:hover {
  background-color: #262626;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
}

.el-divider {
  margin: 12px 0;
}
</style>
