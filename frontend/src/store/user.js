import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getUserInfo } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  const viewRole = ref(localStorage.getItem('view_role') || null) // 视图角色（不修改数据库）
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const user = computed(() => userInfo.value)  // 别名，方便使用
  
  // 获取实际用于显示和路由的角色
  const effectiveRole = computed(() => {
    return viewRole.value || userInfo.value?.role
  })
  
  // 是否可以切换角色
  const canSwitchRole = computed(() => {
    return userInfo.value?.can_switch_role === true
  })
  
  // 方法
  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }
  
  function setUserInfo(info) {
    userInfo.value = info
  }
  
  function logout() {
    setToken('')
    setUserInfo(null)
    setViewRole(null)
  }
  
  // 设置视图角色（不修改数据库）
  function setViewRole(role) {
    viewRole.value = role
    if (role) {
      localStorage.setItem('view_role', role)
    } else {
      localStorage.removeItem('view_role')
    }
  }
  
  // 切换视图角色
  function switchViewRole(role) {
    if (canSwitchRole.value) {
      setViewRole(role)
      return true
    }
    return false
  }
  
  // 获取用户信息
  async function fetchUserInfo() {
    try {
      const info = await getUserInfo()
      setUserInfo(info)
      return info
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }
  
  return {
    token,
    userInfo,
    user,  // 导出别名
    viewRole,  // 视图角色
    effectiveRole,  // 有效角色（用于权限判断）
    canSwitchRole,  // 是否可以切换角色
    isLoggedIn,
    username,
    setToken,
    setUserInfo,
    setViewRole,
    switchViewRole,
    logout,
    fetchUserInfo  // 导出新方法
  }
})
