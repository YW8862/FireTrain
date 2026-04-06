import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getUserInfo } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const user = computed(() => userInfo.value)  // 别名，方便使用
  
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
    isLoggedIn,
    username,
    setToken,
    setUserInfo,
    logout,
    fetchUserInfo  // 导出新方法
  }
})
