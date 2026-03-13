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
 */
export function getTrainingTrend(days = 7) {
  return request({
    url: `/stats/trend?days=${days}`,
    method: 'get'
  })
}

/**
 * 获取步骤分析
 */
export function getStepAnalysis() {
  return request({
    url: '/stats/step-analysis',
    method: 'get'
  })
}

/**
 * 获取统计概览
 * @param {number} days - 趋势天数
 */
export function getStatisticsOverview(days = 7) {
  return request({
    url: `/stats/overview?days=${days}`,
    method: 'get'
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
