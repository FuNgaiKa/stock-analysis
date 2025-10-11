<template>
  <div class="header">
    <!-- Logo和标题 -->
    <div class="header-left">
      <el-icon :size="28" color="#1890ff">
        <TrendCharts />
      </el-icon>
      <span class="title">金融工具平台</span>
      <el-tag type="primary" size="small" class="version-tag">v1.0</el-tag>
    </div>

    <!-- 右侧操作区 -->
    <div class="header-right">
      <!-- 语言切换 -->
      <el-dropdown @command="handleLanguageChange">
        <el-button circle>
          <el-icon><Operation /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="zh-CN" :disabled="currentLocale === 'zh-CN'">
              🇨🇳 简体中文
            </el-dropdown-item>
            <el-dropdown-item command="en-US" :disabled="currentLocale === 'en-US'">
              🇺🇸 English
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 暗黑模式切换 -->
      <el-tooltip :content="$t('header.toggleTheme')">
        <el-button circle @click="toggleDark">
          <el-icon v-if="isDark"><Moon /></el-icon>
          <el-icon v-else><Sunny /></el-icon>
        </el-button>
      </el-tooltip>

      <!-- 刷新 -->
      <el-tooltip :content="$t('header.refresh')">
        <el-button circle @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </el-tooltip>

      <!-- 文档 -->
      <el-tooltip :content="$t('header.docs')">
        <el-button circle @click="goToDocs">
          <el-icon><Document /></el-icon>
        </el-button>
      </el-tooltip>

      <!-- GitHub -->
      <el-tooltip :content="$t('header.github')">
        <el-button circle @click="goToGithub">
          <el-icon><Link /></el-icon>
        </el-button>
      </el-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { setLocale, getLocale, type LocaleType } from '@/locales'

const router = useRouter()
const { t } = useI18n()

// 当前语言
const currentLocale = ref<LocaleType>(getLocale())

// 切换语言
const handleLanguageChange = (locale: LocaleType) => {
  setLocale(locale)
  currentLocale.value = locale
  ElMessage.success(
    locale === 'zh-CN' ? '语言已切换为简体中文' : 'Language switched to English'
  )
}

// 暗黑模式
const isDark = ref(false)

// 切换暗黑模式
const toggleDark = () => {
  isDark.value = !isDark.value
  const html = document.documentElement
  if (isDark.value) {
    html.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    html.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

// 初始化主题
onMounted(() => {
  const theme = localStorage.getItem('theme')
  if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
})

// 刷新页面
const handleRefresh = () => {
  location.reload()
}

// 跳转文档
const goToDocs = () => {
  router.push('/docs')
}

// 跳转GitHub
const goToGithub = () => {
  window.open('https://github.com/your-username/stock-analysis', '_blank')
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.dark .header {
  background-color: #141414;
  border-bottom-color: #424242;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.dark .title {
  color: #fff;
}

.version-tag {
  margin-left: 8px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
