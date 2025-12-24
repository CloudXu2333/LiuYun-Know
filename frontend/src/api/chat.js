/**
 * 对话相关 API
 */
import axios from './axios'

/**
 * 创建对话
 */
export const createConversation = async (data) => {
  const response = await axios.post('/chat/conversations', data)
  return response.data
}

/**
 * 获取对话列表
 */
export const getConversations = async (params) => {
  const response = await axios.get('/chat/conversations', { params })
  return response.data
}

/**
 * 获取对话详情
 */
export const getConversation = async (conversationId) => {
  const response = await axios.get(`/chat/conversations/${conversationId}`)
  return response.data
}

/**
 * 获取对话详情（别名，为了兼容）
 */
export const getConversationDetail = async (conversationId) => {
  const response = await axios.get(`/chat/conversations/${conversationId}`)
  return response.data
}

/**
 * 分页获取对话消息
 * @param {string} conversationId - 对话 ID
 * @param {Object} params - 分页参数
 * @param {number} params.limit - 每页数量（默认20）
 * @param {number} params.offset - 偏移量
 * @returns {Promise<{messages: Array, total: number, has_more: boolean}>}
 */
export const getConversationMessages = async (conversationId, params = {}) => {
  const response = await axios.get(`/chat/conversations/${conversationId}/messages`, { params })
  return response.data
}

/**
 * 更新对话
 */
export const updateConversation = async (conversationId, data) => {
  const response = await axios.put(`/chat/conversations/${conversationId}`, data)
  return response.data
}

/**
 * 删除对话
 */
export const deleteConversation = async (conversationId) => {
  const response = await axios.delete(`/chat/conversations/${conversationId}`)
  return response.data
}

/**
 * 获取对话历史
 */
export const getChatHistory = async (params) => {
  const response = await axios.get('/chat/history', { params })
  return response.data
}

