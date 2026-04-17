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
