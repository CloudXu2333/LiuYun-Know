/**
 * 平台级 LLM 配置 API
 */
import api from './axios'

/**
 * 获取所有平台配置（管理员）
 */
export const getPlatformConfigs = async () => {
  const response = await api.get('/llm/platform-configs')
  return response.data
}

/**
 * 获取启用的平台配置（普通用户）
 */
export const getActivePlatformConfigs = async () => {
  const response = await api.get('/llm/platform-configs/active')
  return response.data
}

/**
 * 创建平台配置
 */
export const createPlatformConfig = async (data) => {
  const response = await api.post('/llm/platform-configs', data)
  return response.data
}

/**
 * 更新平台配置
 */
export const updatePlatformConfig = async (configId, data) => {
  const response = await api.put(`/llm/platform-configs/${configId}`, data)
  return response.data
}

/**
 * 删除平台配置
 */
export const deletePlatformConfig = async (configId) => {
  await api.delete(`/llm/platform-configs/${configId}`)
}

/**
 * 测试平台配置连接
 * @param {string|null} configId - 配置 ID（测试已保存的配置）
 * @param {object|null} data - 配置数据（测试新配置）
 */
export const testPlatformConfig = async (configId, data = null) => {
  if (configId) {
    const response = await api.post(`/llm/platform-configs/${configId}/test`)
    return response.data
  } else {
    const response = await api.post('/llm/platform-configs/test', data)
    return response.data
  }
}
