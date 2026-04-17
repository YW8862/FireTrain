const PERFORMANCE_LEVEL_LABELS = {
  excellent: '优秀',
  good: '良好',
  pass: '合格',
  fail: '待改进'
}

const PERFORMANCE_LEVEL_TAG_TYPES = {
  excellent: 'success',
  good: 'success',
  pass: 'warning',
  fail: 'danger'
}

const DIMENSION_KEYS = [
  ['action_completeness', '动作完整性'],
  ['pose_standardization', '姿态规范性'],
  ['timeliness', '操作时效性']
]

export function normalizePerformanceLevel(level) {
  return Object.prototype.hasOwnProperty.call(PERFORMANCE_LEVEL_LABELS, level) ? level : null
}

export function getPerformanceLabel(level) {
  const normalizedLevel = normalizePerformanceLevel(level)
  return normalizedLevel ? PERFORMANCE_LEVEL_LABELS[normalizedLevel] : '暂无评级'
}

export function getPerformanceTagType(level) {
  const normalizedLevel = normalizePerformanceLevel(level)
  return normalizedLevel ? PERFORMANCE_LEVEL_TAG_TYPES[normalizedLevel] : 'info'
}

export function extractPerformanceLevel(trainingDetail) {
  return normalizePerformanceLevel(
    trainingDetail?.performance_level ?? trainingDetail?.step_scores?._performance_level
  )
}

export function normalizeSuggestions(suggestions) {
  if (!Array.isArray(suggestions)) {
    return []
  }

  return suggestions.filter(item => typeof item === 'string' && item.trim())
}

export function extractStepScores(stepScores) {
  if (!stepScores || typeof stepScores !== 'object') {
    return []
  }

  return Object.entries(stepScores)
    .filter(([key, value]) => !key.startsWith('_') && value && typeof value === 'object')
    .map(([key, value]) => ({
      step_name: value.step_name || `步骤${key.replace('step', '')}`,
      score: parseFloat(value.score) || 0,
      feedback: value.feedback || ''
    }))
}

export function getDimensionItems(dimensionScores) {
  return DIMENSION_KEYS.map(([key, label]) => {
    const rawDimension = dimensionScores?.[key]
    const score = rawDimension?.score
    const parsedScore = score === undefined || score === null ? null : parseFloat(score)

    return {
      key,
      label,
      score: Number.isFinite(parsedScore) ? parsedScore : null,
      comment: rawDimension?.comment || '',
      hasData: Number.isFinite(parsedScore)
    }
  })
}

export function hasDimensionScores(dimensionScores) {
  return getDimensionItems(dimensionScores).some(item => item.hasData)
}
