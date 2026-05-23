import request from './request'

/**
 * 获取个人统计数据
 */
export function getPersonalStatistics() {
  return request({
    url: '/stats/personal',
    method: 'get'
  })
}

/**
 * 获取训练趋势
 * @param {number} days - 查询天数
 * @param {string} trainingType - 训练类型（可选）
 */
export function getTrainingTrend(days = 7, trainingType = null) {
  const params = { days }
  if (trainingType) {
    params.training_type = trainingType
  }
  return request({
    url: '/stats/trend',
    method: 'get',
    params
  })
}

/**
 * 获取步骤分析
 * @param {string} trainingType - 训练类型（可选）
 */
export function getStepAnalysis(trainingType = null) {
  const params = {}
  if (trainingType) {
    params.training_type = trainingType
  }
  return request({
    url: '/stats/step-analysis',
    method: 'get',
    params
  })
}

/**
 * 获取统计概览
 * @param {number} days - 趋势天数
 * @param {string} trainingType - 训练类型（可选）
 */
export function getStatisticsOverview(days = 7, trainingType = null) {
  const params = { days }
  if (trainingType) {
    params.training_type = trainingType
  }
  return request({
    url: '/stats/overview',
    method: 'get',
    params
  })
}

/**
 * 获取训练历史记录
 * @param {Object} params - 查询参数
 */
export function getTrainingHistory(params) {
  return request({
    url: '/training/history',
    method: 'get',
    params
  })
}