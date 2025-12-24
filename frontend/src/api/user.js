/**
 * 用户管理相关 API
 */
import axios from './axios'

/**
 * 获取个人信息
 */
export const getMyProfile = () => {
  return axios.get('/users/me')
}

/**
 * 更新个人信息
 */
export const updateMyProfile = (data) => {
  return axios.put('/users/me', data)
}

/**
 * 修改密码
 */
export const changePassword = (data) => {
  return axios.put('/users/password', data)
}

/**
 * 获取记忆设置
 * @returns {Promise<{memory_top_k: number, core_memory_threshold: number}>}
 */
export const getMemorySettings = async () => {
  const response = await axios.get('/users/me/memory-settings')
  return response.data
}

/**
 * 更新记忆设置
 * @param {Object} data - 设置数据
 * @param {number} data.memory_top_k - 普通记忆检索数量 (1-20)
 * @param {number} data.core_memory_threshold - 核心记忆优先级阈值 (0-100)
 * @returns {Promise<{memory_top_k: number, core_memory_threshold: number}>}
 */
export const updateMemorySettings = async (data) => {
  const response = await axios.put('/users/me/memory-settings', data)
  return response.data
}

