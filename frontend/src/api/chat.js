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

