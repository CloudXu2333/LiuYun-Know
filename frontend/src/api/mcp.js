/**
 * MCP 工具 API
 */
import axios from './axios'

/**
 * 获取 MCP 工具列表（平台工具 + 用户工具）
 */
export const getMCPTools = async () => {
  const response = await axios.get('/mcp-tools')
  return response.data
}

/**
 * 创建用户 MCP 工具
 * @param {Object} data - 工具数据
 */
export const createMCPTool = async (data) => {
  const response = await axios.post('/mcp-tools', data)
  return response.data
}

/**
 * 获取单个 MCP 工具
 * @param {string} toolId - 工具 ID
 */
export const getMCPTool = async (toolId) => {
  const response = await axios.get(`/mcp-tools/${toolId}`)
  return response.data
}

/**
 * 更新 MCP 工具
 * @param {string} toolId - 工具 ID
 * @param {Object} data - 更新数据
 */
export const updateMCPTool = async (toolId, data) => {
  const response = await axios.put(`/mcp-tools/${toolId}`, data)
  return response.data
}

/**
 * 删除 MCP 工具
 * @param {string} toolId - 工具 ID
 */
export const deleteMCPTool = async (toolId) => {
  const response = await axios.delete(`/mcp-tools/${toolId}`)
  return response.data
}

/**
 * 测试 MCP 工具连接
 * @param {string} toolId - 工具 ID
 */
export const testMCPTool = async (toolId) => {
  const response = await axios.post(`/mcp-tools/${toolId}/test`)
  return response.data
}

/**
 * 测试 MCP 配置（不保存）
 * @param {Object} config - MCP 配置
 */
export const testMCPConfig = async (config) => {
  const response = await axios.post('/mcp-tools/test-config', config)
  return response.data
}

/**
 * 获取 MCP Server 提供的工具列表
 * @param {string} toolId - 工具 ID
 */
export const getMCPServerTools = async (toolId) => {
  const response = await axios.get(`/mcp-tools/${toolId}/server-tools`)
  return response.data
}

// ============ 管理员接口 ============

/**
 * 创建平台 MCP 工具（管理员）
 * @param {Object} data - 工具数据
 */
export const createPlatformMCPTool = async (data) => {
  const response = await axios.post('/mcp-tools/platform', data)
  return response.data
}

/**
 * 更新平台 MCP 工具（管理员）
 * @param {string} toolId - 工具 ID
 * @param {Object} data - 更新数据
 */
export const updatePlatformMCPTool = async (toolId, data) => {
  const response = await axios.put(`/mcp-tools/platform/${toolId}`, data)
  return response.data
}

/**
 * 删除平台 MCP 工具（管理员）
 * @param {string} toolId - 工具 ID
 */
export const deletePlatformMCPTool = async (toolId) => {
  const response = await axios.delete(`/mcp-tools/platform/${toolId}`)
  return response.data
}
