import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  
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
  
  return {
    token,
    userInfo,
    isLoggedIn,
    username,
    setToken,
    setUserInfo,
    logout
  }
})
