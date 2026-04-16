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

export function createUser(data) {
  return request({
    url: '/admin/users',
    method: 'post',
    data
  })
}

export function getUserDetail(userId) {
  return request({
    url: `/admin/users/${userId}`,
    method: 'get'
  })
}

export function updateUser(userId, data) {
  return request({
    url: `/admin/users/${userId}`,
    method: 'put',
    data
  })
}

export function getUserStatistics(userId, params) {
  return request({
    url: `/admin/users/${userId}/stats/overview`,
    method: 'get',
    params
  })
}

export function getUserTrainings(userId, params) {
  return request({
    url: `/admin/users/${userId}/trainings`,
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

/**
 * 获取管理员列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.keyword - 搜索关键词
 */
export function getAdmins(params) {
  return request({
    url: '/admin/admins',
    method: 'get',
    params
  })
}

export function getAdminDetail(adminId) {
  return request({
    url: `/admin/admins/${adminId}`,
    method: 'get'
  })
}

/**
 * 创建管理员
 * @param {Object} data - 管理员数据
 * @param {string} data.username - 用户名
 * @param {string} data.email - 邮箱
 * @param {string} data.password - 密码
 * @param {string} data.role - 角色 (admin 或 root)
 */
export function createAdmin(data) {
  return request({
    url: '/admin/admins',
    method: 'post',
    data
  })
}

/**
 * 删除管理员
 * @param {number} adminId - 管理员ID
 */
export function deleteAdmin(adminId) {
  return request({
    url: `/admin/admins/${adminId}`,
    method: 'delete'
  })
}

export function updateAdmin(adminId, data) {
  return request({
    url: `/admin/admins/${adminId}`,
    method: 'put',
    data
  })
}

export function resetAdminPassword(adminId) {
  return request({
    url: `/admin/admins/${adminId}/reset-password`,
    method: 'put'
  })
}

/**
 * 修改管理员角色
 * @param {number} adminId - 管理员ID
 * @param {string} role - 新角色
 */
export function updateAdminRole(adminId, role) {
  return request({
    url: `/admin/admins/${adminId}/role`,
    method: 'put',
    data: { role }
  })
}
