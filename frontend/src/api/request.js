import axios from 'axios'

// 创建 axios 实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 添加请求日志
request.interceptors.request.use(
  config => {
    console.log('[API 请求]', config.method.toUpperCase(), config.url, config.data)
    // 添加 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('[API 请求错误]:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    console.log('[API 响应成功]', response.config.url, response.data)
    return response.data
  },
  error => {
    console.error('[API 响应错误]', error)
    if (error.response) {
      switch (error.response.status) {
        case 401:
          console.error('未授权，请重新登录')
          localStorage.removeItem('token')
          window.location.href = '/login'
          break
        case 403:
          console.error('拒绝访问')
          break
        case 404:
          console.error('请求资源不存在')
          break
        case 500:
          console.error('服务器错误')
          break
        default:
          console.error(`请求失败：${error.response.status}`)
      }
    } else if (error.request) {
      console.error('网络错误：已发送请求但未收到响应', error.request)
      console.error('请求详情:', {
        url: error.config?.url,
        method: error.config?.method,
        baseURL: error.config?.baseURL
      })
    } else {
      console.error('网络错误:', error.message)
    }
    return Promise.reject(error)
  }
)

export default request
