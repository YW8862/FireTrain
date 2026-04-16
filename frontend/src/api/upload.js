import axios from 'axios'

export const DEFAULT_UPLOAD_TIMEOUT = 10 * 60 * 1000

const trimTrailingSlash = (value) => value.replace(/\/+$/, '')

export const resolveUploadBaseUrl = () => {
  const explicitBaseUrl = import.meta.env.VITE_UPLOAD_BASE_URL?.trim()
  if (explicitBaseUrl) {
    return trimTrailingSlash(explicitBaseUrl)
  }

  return import.meta.env.VITE_API_BASE_URL || '/api'
}

const uploadClient = axios.create({
  timeout: DEFAULT_UPLOAD_TIMEOUT
})

uploadClient.interceptors.request.use(
  config => {
    config.baseURL = resolveUploadBaseUrl()
    config.headers = config.headers || {}

    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    return config
  },
  error => Promise.reject(error)
)

uploadClient.interceptors.response.use(
  response => response.data,
  error => {
    if (error.code === 'ERR_CANCELED') {
      error.customMessage = '上传已取消'
      return Promise.reject(error)
    }

    if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
      error.customMessage = '上传超时'
      error.suggestion = '请检查网络连接，或缩短视频时长后重试'
    } else if (error.message === 'Network Error') {
      error.customMessage = '网络错误'
      error.suggestion = '请检查上传地址、证书信任状态和后端服务是否可用'
    }

    if (error.response) {
      const status = error.response.status
      switch (status) {
        case 401:
          error.customMessage = '未授权，请重新登录'
          break
        case 403:
          error.customMessage = '拒绝访问'
          break
        case 404:
          error.customMessage = '上传接口不存在'
          break
        case 413:
          error.customMessage = '文件过大，服务器拒绝接收'
          break
        case 500:
          error.customMessage = '服务器内部错误'
          break
        default:
          error.customMessage = error.response.data?.detail || `请求失败：${status}`
      }
    }

    return Promise.reject(error)
  }
)

export const uploadRequest = (config) => {
  return uploadClient({
    timeout: DEFAULT_UPLOAD_TIMEOUT,
    ...config
  })
}
