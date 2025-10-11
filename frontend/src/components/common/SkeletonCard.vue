<template>
  <el-card class="skeleton-card" shadow="hover">
    <div class="skeleton-header">
      <el-skeleton :rows="0" animated>
        <template #template>
          <el-skeleton-item variant="h3" style="width: 60%" />
        </template>
      </el-skeleton>
    </div>

    <el-divider style="margin: 15px 0" />

    <div class="skeleton-content">
      <el-skeleton :rows="rows" animated>
        <template #template>
          <div v-for="i in rows" :key="i" class="skeleton-row">
            <el-skeleton-item variant="text" :style="{ width: getRandomWidth() }" />
          </div>
        </template>
      </el-skeleton>
    </div>

    <div v-if="showChart" class="skeleton-chart">
      <el-skeleton animated>
        <template #template>
          <el-skeleton-item variant="rect" style="width: 100%; height: 200px; border-radius: 8px" />
        </template>
      </el-skeleton>
    </div>
  </el-card>
</template>

<script setup lang="ts">
interface Props {
  rows?: number
  showChart?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  rows: 3,
  showChart: false,
})

// 随机宽度，让骨架屏更自然
const getRandomWidth = () => {
  const widths = ['70%', '80%', '90%', '85%', '75%']
  return widths[Math.floor(Math.random() * widths.length)]
}
</script>

<style scoped>
.skeleton-card {
  margin-bottom: 20px;
}

.skeleton-header {
  padding: 10px 0;
}

.skeleton-content {
  margin-bottom: 20px;
}

.skeleton-row {
  margin-bottom: 12px;
}

.skeleton-chart {
  margin-top: 20px;
}

/* 自定义骨架屏颜色 */
:deep(.el-skeleton__item) {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 37%,
    #f0f0f0 63%
  );
  background-size: 400% 100%;
  animation: skeleton-loading 1.4s ease infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

.dark :deep(.el-skeleton__item) {
  background: linear-gradient(
    90deg,
    #2a2a2a 25%,
    #3a3a3a 37%,
    #2a2a2a 63%
  );
  background-size: 400% 100%;
}
</style>
