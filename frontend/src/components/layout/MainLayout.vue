<template>
  <el-container class="main-layout">
    <!-- 顶部Header -->
    <el-header height="60px">
      <Header />
    </el-header>

    <!-- 主体内容 -->
    <el-container>
      <!-- 左侧Sidebar -->
      <el-aside :width="collapsed ? '64px' : '200px'" class="sidebar-container">
        <Sidebar :collapsed="collapsed" @toggle="handleToggle" />
      </el-aside>

      <!-- 右侧主内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Header from './Header.vue'
import Sidebar from './Sidebar.vue'

// 侧边栏折叠状态
const collapsed = ref(false)

// 切换折叠状态
const handleToggle = () => {
  collapsed.value = !collapsed.value
}
</script>

<style scoped>
.main-layout {
  width: 100%;
  height: 100vh;
}

.sidebar-container {
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  transition: width 0.3s;
}

.dark .sidebar-container {
  background-color: #141414;
  border-right-color: #424242;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.dark .main-content {
  background-color: #000;
}

/* 页面切换动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
