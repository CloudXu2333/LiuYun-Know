/**
 * 长期记忆 API
 */
import axios from './axios'

/**
 * 获取记忆分类选项
 */
export const getMemoryCategories = async () => {
  const response = await axios.get('/memory/categories')
  return response.data
}

/**
 * 获取记忆列表
 * @param {Object} params - 查询参数
 * @param {string} params.category - 分类筛选
 * @param {boolean} params.active_only - 是否只返回启用的
 * @param {number} params.skip - 跳过数量
 * @param {number} params.limit - 返回数量
 */
export const getMemories = async (params = {}) => {
  const response = await axios.get('/memory', { params })
  return response.data
}

/**
 * 获取单条记忆
 * @param {string} id - 记忆 ID
 */
export const getMemory = async (id) => {
  const response = await axios.get(`/memory/${id}`)
  return response.data
}

/**
 * 创建记忆
 * @param {Object} data - 记忆数据
 * @param {string} data.title - 标题
 * @param {string} data.content - 内容
 * @param {string} data.category - 分类
 * @param {number} data.priority - 优先级
 * @param {boolean} data.is_active - 是否启用
 */
export const createMemory = async (data) => {
  const response = await axios.post('/memory', data)
  return response.data
}

/**
 * 更新记忆
 * @param {string} id - 记忆 ID
 * @param {Object} data - 更新数据
 */
export const updateMemory = async (id, data) => {
  const response = await axios.put(`/memory/${id}`, data)
  return response.data
}

/**
 * 删除记忆
 * @param {string} id - 记忆 ID
 */
export const deleteMemory = async (id) => {
  const response = await axios.delete(`/memory/${id}`)
  return response.data
}

/**
 * 切换记忆启用状态
 * @param {string} id - 记忆 ID
 */
export const toggleMemory = async (id) => {
  const response = await axios.post(`/memory/${id}/toggle`)
  return response.data
}

/**
 * AI自动提取记忆
 * @param {string} content - 要提取的内容
 * @param {Object} options - 可选参数
 * @param {string} options.config_id - 用户配置 ID
 * @param {string} options.platform_config_id - 平台配置 ID
 * @returns {Promise<{title: string, content: string, category: string, priority: number}>}
 */
export const autoExtractMemory = async (content, options = {}) => {
  const response = await axios.post('/memory/auto-extract', {
    content,
    config_id: options.config_id || null,
    platform_config_id: options.platform_config_id || null
  })
  return response.data
}
