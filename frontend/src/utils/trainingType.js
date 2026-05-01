export const TRAINING_TYPE_OPTIONS = [
  {
    label: '灭火器训练',
    value: 'fire_extinguisher'
  },
  {
    label: '其他训练',
    value: 'other'
  }
]

const TRAINING_TYPE_LABELS = TRAINING_TYPE_OPTIONS.reduce((map, item) => {
  map[item.value] = item.label
  return map
}, {
  extinguisher: '灭火器训练',
  extinguisher_use: '灭火器训练'
})

export function getTrainingTypeLabel(type) {
  return TRAINING_TYPE_LABELS[type] || type || '未设置'
}

/** 训练类型配置：步骤、操作指引、提示文字 */
export const TRAINING_TYPE_CONFIG = {
  fire_extinguisher: {
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
    stepCount: 6,
    // 以后新增其他训练类型在这里加配置即可
  },
  other: {
    steps: [
      { name: '步骤一', description: '按规范完成操作' },
      { name: '步骤二', description: '按规范完成操作' },
      { name: '步骤三', description: '按规范完成操作' }
    ],
    instructions: [
      '按系统指引完成操作',
      '注意动作规范',
      '确保安全'
    ],
    bannerMessage: '请保持摄像头对准训练人员全身，确保动作完整清晰。',
    confirmMessage: '准备好开始训练了吗？',
    stepCount: 3
  }
}

export function getTrainingTypeConfig(type) {
  return TRAINING_TYPE_CONFIG[type] || TRAINING_TYPE_CONFIG.fire_extinguisher
}
