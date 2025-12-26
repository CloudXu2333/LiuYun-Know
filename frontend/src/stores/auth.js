/**
 * 认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authAPI from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user = ref(null)
  
  // Getters
  const isAuthenticated = computed(() => !!accessToken.value)
  
  // Actions
  
  /**
   * 登录
   */
  const login = async (credentials) => {
    try {
      const data = await authAPI.login(credentials)
      
      accessToken.value = data.access_token
      refreshToken.value = data.refresh_token
      
      // 保存到 localStorage
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      
      // 获取用户信息
      await fetchUser()
      
      return data
    } catch (error) {
      throw error
    }
  }
  
  /**
   * 注册
   */
  const register = async (userData) => {
    try {
      const data = await authAPI.register(userData)
      return data
    } catch (error) {
      throw error
    }
  }
  
  /**
   * 清除认证信息（不发送 API 请求）
   */
  const clearAuth = () => {
    // 清除状态
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    
    // 清除 localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('llm_config')
  }
  
  /**
   * 登出
   */
  const logout = async () => {
    try {
      if (accessToken.value) {
        await authAPI.logout()
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuth()
    }
  }
  
  /**
   * 刷新访问令牌
   */
  const refreshAccessToken = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('No refresh token')
      }
      
      const data = await authAPI.refreshToken(refreshToken.value)
      
      accessToken.value = data.access_token
      
      // 更新 localStorage
      localStorage.setItem('access_token', data.access_token)
      
      return data
    } catch (error) {
      // 刷新失败，清除所有认证信息（不发送 API 请求）
      clearAuth()
      throw error
    }
  }
  
  /**
   * 获取用户信息
   */
  const fetchUser = async () => {
    try {
      const data = await authAPI.getCurrentUser()
      user.value = data
      return data
    } catch (error) {
      throw error
    }
  }
  
  /**
   * 初始化（从 localStorage 恢复状态）
   */
  const initialize = async () => {
    if (accessToken.value) {
      try {
        await fetchUser()
      } catch (error) {
        // token 无效，清除
        await logout()
      }
    }
  }
  
  return {
    // State
    accessToken,
    refreshToken,
    user,
    
    // Getters
    isAuthenticated,
    
    // Actions
    login,
    register,
    logout,
    clearAuth,
    refreshAccessToken,
    fetchUser,
    initialize,
  }
})

