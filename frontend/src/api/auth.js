/**
 * 认证相关 API
 */
import axios from './axios'

/**
 * 用户注册
 */
export const register = async (data) => {
  const response = await axios.post('/auth/register', data)
  return response.data
}

/**
 * 用户登录
 */
export const login = async (data) => {
  const response = await axios.post('/auth/login', data)
  return response.data
}

/**
 * 刷新 token
 */
export const refreshToken = async (refreshToken) => {
  const response = await axios.post('/auth/refresh', { refresh_token: refreshToken })
  return response.data
}

/**
 * 用户登出
 */
export const logout = async () => {
  const response = await axios.post('/auth/logout')
  return response.data
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = async () => {
  const response = await axios.get('/auth/me')
  return response.data
}

