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
    
    // 添加详细的错误信息到 error 对象，供上层使用
    if (error.code === 'ERR_CERT_AUTHORITY_INVALID') {
      error.customMessage = 'SSL 证书错误：证书颁发机构不受信任'
      error.suggestion = '请检查服务器 SSL 证书配置，或使用 HTTP 连接进行测试'
    } else if (error.code === 'ECONNREFUSED') {
      error.customMessage = '连接被拒绝'
      error.suggestion = '请检查后端服务是否启动，端口是否正确'
    } else if (error.code === 'ETIMEDOUT') {
      error.customMessage = '请求超时'
      error.suggestion = '请检查网络连接或增加超时时间'
    }
    
    if (error.response) {
      // 服务器返回了响应
      const status = error.response.status
      console.error('服务器响应状态码:', status)
      console.error('响应数据:', error.response.data)
      
      switch (status) {
        case 401:
          error.customMessage = '未授权，请重新登录'
          localStorage.removeItem('token')
          window.location.href = '/login'
          break
        case 403:
          error.customMessage = '拒绝访问'
          break
        case 404:
          error.customMessage = '请求资源不存在'
          break
        case 500:
          error.customMessage = '服务器内部错误'
          break
        default:
          error.customMessage = `请求失败：${status}`
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      error.customMessage = '网络错误：无法连接到服务器'
      error.suggestion = '请检查：\n1. 后端服务是否正常运行\n2. 网络连接是否稳定\n3. 防火墙设置是否阻止请求'
      console.error('网络错误详情:', {
        url: error.config?.url,
        method: error.config?.method,
        baseURL: error.config?.baseURL,
        timeout: error.config?.timeout
      })
    } else {
      // 其他错误（如解析错误等）
      error.customMessage = `请求错误：${error.message}`
    }
    
    return Promise.reject(error)
  }
)

export default request
