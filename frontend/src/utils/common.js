/**
 * 通用工具函数
 */

/**
 * 获取分数对应的标签类型
 * @param {number} score - 分数
 * @returns {string} - Element Plus tag 类型
 */
export function getScoreTagType(score) {
  if (score >= 90) return 'success'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

/**
 * 获取等级对应的标签类型
 * @param {string} level - 等级
 * @returns {string} - Element Plus tag 类型
 */
export function getLevelTagType(level) {
  const types = {
    excellent: 'success',
    good: 'success',
    pass: 'warning',
    fail: 'danger'
  }
  return types[level] || 'info'
}
