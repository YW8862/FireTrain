import request from './request'

/**
 * 获取所有用户列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.role - 角色过滤
 * @param {string} params.keyword - 搜索关键词
 */
export function getUsers(params) {
  return request({
    url: '/admin/users',
    method: 'get',
    params
  })
}

/**
 * 删除用户
 * @param {number} userId - 用户ID
 */
export function deleteUser(userId) {
  return request({
    url: `/admin/users/${userId}`,
    method: 'delete'
  })
}

/**
 * 重置用户密码
 * @param {number} userId - 用户ID
 */
export function resetUserPassword(userId) {
  return request({
    url: `/admin/users/${userId}/reset-password`,
    method: 'put'
  })
}

/**
 * 获取所有训练记录
 * @param {Object} params - 查询参数
 */
export function getTrainings(params) {
  return request({
    url: '/admin/trainings',
    method: 'get',
    params
  })
}

/**
 * 删除训练记录
 * @param {number} trainingId - 训练记录ID
 */
export function deleteTraining(trainingId) {
  return request({
    url: `/admin/trainings/${trainingId}`,
    method: 'delete'
  })
}

/**
 * 获取仪表盘统计数据
 */
export function getDashboardStats() {
  return request({
    url: '/admin/statistics/dashboard',
    method: 'get'
  })
}

/**
 * 获取管理员操作日志
 * @param {Object} params - 查询参数
 */
export function getAdminLogs(params) {
  return request({
    url: '/admin/logs',
    method: 'get',
    params
  })
}
