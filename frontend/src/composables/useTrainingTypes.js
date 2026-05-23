import { ref, computed } from 'vue'
import request from '@/api/request'

// 模块级缓存
let cachedTypes = null
let cachePromise = null

// 硬编码的兜底配置，确保页面首次渲染时就有数据
const FALLBACK_TYPES = [
  {
    value: 'fire_extinguisher',
    label: '灭火器训练',
    steps: [
      { name: '准备阶段', description: '做好个人防护，确认逃生路线' },
      { name: '提灭火器', description: '用腿部力量提起灭火器' },
      { name: '拔保险销', description: '握住拉环用力拔出' },
      { name: '握喷管', description: '双手稳固握持喷管' },
      { name: '瞄准火源', description: '对准火焰根部，保持 2-3 米距离' },
      { name: '压把手', description: '均匀用力下压，左右扫射' }
    ],
    instructions: [
      '准备阶段：做好个人防护，确认逃生路线',
      '提起灭火器：用腿部力量提起灭火器',
      '拔保险销：握住拉环用力拔出',
      '握喷管：双手稳固握持喷管',
      '瞄准火源：对准火焰根部，保持 2-3 米距离',
      '压把手：均匀用力下压，左右扫射'
    ],
    bannerMessage: '请保持摄像头对准训练人员全身，避免遮挡关键动作，确保动作连续清晰。',
    confirmMessage: '准备好开始训练了吗？请确保已做好个人防护，确认逃生路线畅通，灭火器在有效期内。',
    stepCount: 6
  }
]

/**
 * 获取训练类型配置（从后端统一 API 获取）
 * 使用单例模式，首次调用时立即返回兜底数据，同时异步拉取后端配置
 */
export function useTrainingTypes() {
  const loading = ref(false)
  const error = ref(null)

  // 立即返回兜底数据，同时在后台更新
  const types = computed(() => cachedTypes || FALLBACK_TYPES)

  const TRAINING_TYPE_OPTIONS = computed(() =>
    (cachedTypes || FALLBACK_TYPES).map(t => ({
      label: t.label,
      value: t.value
    }))
  )

  const TRAINING_TYPE_CONFIG = computed(() => {
    const config = {}
    for (const type of (cachedTypes || FALLBACK_TYPES)) {
      config[type.value] = {
        steps: type.steps,
        instructions: type.instructions,
        bannerMessage: type.bannerMessage,
        confirmMessage: type.confirmMessage,
        stepCount: type.stepCount
      }
    }
    return config
  })

  async function fetchTypes() {
    if (cachedTypes) return cachedTypes
    if (cachePromise) return cachePromise

    loading.value = true
    error.value = null

    cachePromise = request({
      url: '/training/types',
      method: 'get'
    })
      .then(res => {
        cachedTypes = res.types || []
        return cachedTypes
      })
      .catch(err => {
        error.value = err
        console.error('Failed to fetch training types:', err)
        // 出错时使用兜底数据
        return FALLBACK_TYPES
      })
      .finally(() => {
        loading.value = false
      })

    return cachePromise
  }

  function getTrainingTypeLabel(type) {
    const typeItem = (cachedTypes || FALLBACK_TYPES).find(t => t.value === type)
    return typeItem ? typeItem.label : type || '未设置'
  }

  function getTrainingTypeConfig(type) {
    return TRAINING_TYPE_CONFIG.value[type] || TRAINING_TYPE_CONFIG.value.fire_extinguisher || null
  }

  // 初始化时立即返回兜底数据，同时异步获取后端配置
  fetchTypes()

  return {
    types,
    loading,
    error,
    TRAINING_TYPE_OPTIONS,
    TRAINING_TYPE_CONFIG,
    fetchTypes,
    getTrainingTypeLabel,
    getTrainingTypeConfig
  }
}