/**
 * 国际化配置
 */

import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import enUS from './en-US'

// 支持的语言类型
export type LocaleType = 'zh-CN' | 'en-US'

// 语言包
const messages = {
  'zh-CN': zhCN,
  'en-US': enUS,
}

// 获取浏览器语言
function getBrowserLocale(): LocaleType {
  const browserLang = navigator.language
  if (browserLang.startsWith('zh')) {
    return 'zh-CN'
  }
  return 'en-US'
}

// 获取本地存储的语言
function getStoredLocale(): LocaleType | null {
  const stored = localStorage.getItem('locale')
  if (stored && (stored === 'zh-CN' || stored === 'en-US')) {
    return stored as LocaleType
  }
  return null
}

// 获取默认语言
function getDefaultLocale(): LocaleType {
  return getStoredLocale() || getBrowserLocale()
}

// 创建i18n实例
const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  locale: getDefaultLocale(),
  fallbackLocale: 'en-US',
  messages,
  globalInjection: true, // 全局注入 $t 函数
})

// 切换语言
export function setLocale(locale: LocaleType) {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale
}

// 获取当前语言
export function getLocale(): LocaleType {
  return i18n.global.locale.value as LocaleType
}

export default i18n
