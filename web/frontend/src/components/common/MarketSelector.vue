<template>
  <div class="market-selector">
    <el-radio-group v-model="selectedMarket" size="large" @change="handleMarketChange">
      <el-radio-button label="US">
        <span class="market-option">
          <span class="market-icon">🇺🇸</span>
          <span class="market-name">美股</span>
        </span>
      </el-radio-button>
      <el-radio-button label="HK">
        <span class="market-option">
          <span class="market-icon">🇭🇰</span>
          <span class="market-name">港股</span>
        </span>
      </el-radio-button>
      <el-radio-button label="CN">
        <span class="market-option">
          <span class="market-icon">🇨🇳</span>
          <span class="market-name">A股</span>
        </span>
      </el-radio-button>
    </el-radio-group>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  modelValue?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 'US',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  change: [value: string]
}>()

const selectedMarket = ref(props.modelValue)

const handleMarketChange = (value: string) => {
  emit('update:modelValue', value)
  emit('change', value)
}

watch(
  () => props.modelValue,
  (newValue) => {
    selectedMarket.value = newValue
  }
)
</script>

<style scoped>
.market-selector {
  display: inline-block;
}

.market-option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.market-icon {
  font-size: 18px;
}

.market-name {
  font-weight: 500;
  font-size: 14px;
}

:deep(.el-radio-button__inner) {
  padding: 10px 20px;
  transition: all var(--transition-base);
  border-radius: var(--radius-md);
}

:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--primary-gradient);
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

:deep(.el-radio-button:not(:first-child) .el-radio-button__inner) {
  border-left: 1px solid var(--border-color);
}

:deep(.el-radio-button:hover .el-radio-button__inner) {
  transform: translateY(-2px);
}
</style>
