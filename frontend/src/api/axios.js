/**
 * Axios 实例配置和拦截器
 */
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// 创建 axios 实例
const instance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 自动添加 JWT token
instance.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 标记是否正在刷新 token
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  
  failedQueue = []
}

// 响应拦截器 - 处理错误和 token 刷新
instance.interceptors.response.use(
  (response) => {
    // 直接返回 response，让调用方自己处理 data
    return response
  },
  async (error) => {
    const authStore = useAuthStore()
    const originalRequest = error.config
    
    // 如果是 401 错误且不是刷新/登出请求，尝试刷新 token
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes('/auth/refresh') &&
      !originalRequest.url.includes('/auth/logout') &&
      authStore.refreshToken
    ) {
      if (isRefreshing) {
        // 如果正在刷新，将请求加入队列
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return instance(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }
      
      originalRequest._retry = true
      isRefreshing = true
      
      try {
        await authStore.refreshAccessToken()
        const token = authStore.accessToken
        
        // 处理队列中的请求
        processQueue(null, token)
        
        // 重新发送原始请求
        originalRequest.headers.Authorization = `Bearer ${token}`
        return instance(originalRequest)
      } catch (refreshError) {
        // 刷新 token 失败，清除队列并登出
        processQueue(refreshError, null)
        authStore.clearAuth() // 使用新的清除方法，不发送 API 请求
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    
    // 处理其他错误
    const errorMessage = error.response?.data?.detail || error.message || '请求失败'
    
    return Promise.reject({
      status: error.response?.status,
      message: errorMessage,
      data: error.response?.data,
    })
  }
)

export default instance

