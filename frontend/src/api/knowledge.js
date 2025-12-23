/**
 * 知识库 API
 */
import axios from './axios'

/**
 * 创建知识库
 */
export const createKnowledgeBase = async (data) => {
  const response = await axios.post('/knowledge-bases', data)
  return response.data
}

/**
 * 获取知识库列表
 */
export const getKnowledgeBases = async (params = {}) => {
  const response = await axios.get('/knowledge-bases', { params })
  return response.data
}

/**
 * 获取知识库详情
 */
export const getKnowledgeBase = async (id) => {
  const response = await axios.get(`/knowledge-bases/${id}`)
  return response.data
}

/**
 * 更新知识库
 */
export const updateKnowledgeBase = async (id, data) => {
  const response = await axios.put(`/knowledge-bases/${id}`, data)
  return response.data
}

/**
 * 删除知识库
 */
export const deleteKnowledgeBase = async (id) => {
  const response = await axios.delete(`/knowledge-bases/${id}`)
  return response.data
}

/**
 * 上传文件到知识库
 */
export const uploadFile = async (kbId, file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post(`/knowledge-bases/${kbId}/files`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percentCompleted)
      }
    },
  })
  return response.data
}

/**
 * 上传文件到知识库（别名，兼容旧代码）
 */
export const uploadFileToKnowledgeBase = uploadFile

/**
 * 获取知识库文件列表
 */
export const getKnowledgeBaseFiles = async (kbId) => {
  const response = await axios.get(`/knowledge-bases/${kbId}/files`)
  return response.data
}

/**
 * 删除文件
 */
export const deleteFile = async (kbId, fileId) => {
  const response = await axios.delete(`/knowledge-bases/${kbId}/files/${fileId}`)
  return response.data
}

/**
 * 删除知识库文件（别名，兼容旧代码）
 */
export const deleteKnowledgeBaseFile = deleteFile

/**
 * 查询知识库
 */
export const queryKnowledgeBase = async (kbId, data) => {
  const response = await axios.post(`/knowledge-bases/${kbId}/query`, data)
  return response.data
}


// ============ 统计信息 API ============

/**
 * 获取知识库统计信息
 */
export const getKnowledgeBaseStats = async (kbId) => {
  const response = await axios.get(`/knowledge-bases/${kbId}/stats`)
  return response.data
}

// ============ 分片数据 API ============

/**
 * 获取知识库分片列表（分页）
 */
export const getChunks = async (kbId, params = {}) => {
  const response = await axios.get(`/knowledge-bases/${kbId}/chunks`, { params })
  return response.data
}

// ============ 知识图谱 API ============

/**
 * 获取知识图谱数据
 */
export const getKnowledgeGraph = async (kbId, params = {}) => {
  const response = await axios.get(`/knowledge-bases/${kbId}/graph`, { params })
  return response.data
}

/**
 * 获取实体详情
 */
export const getEntityDetail = async (kbId, entityName) => {
  const response = await axios.get(`/knowledge-bases/${kbId}/entities/${encodeURIComponent(entityName)}`)
  return response.data
}

/**
 * 删除实体
 */
export const deleteEntity = async (kbId, entityName) => {
  const response = await axios.delete(`/knowledge-bases/${kbId}/entities/${encodeURIComponent(entityName)}`)
  return response.data
}

/**
 * 删除关系
 */
export const deleteRelation = async (kbId, source, target) => {
  const response = await axios.delete(`/knowledge-bases/${kbId}/relations`, {
    params: { source, target }
  })
  return response.data
}

// ============ 文件操作扩展 API ============

/**
 * 重试文件处理
 */
export const retryFileProcessing = async (kbId, fileId) => {
  const response = await axios.post(`/knowledge-bases/${kbId}/files/${fileId}/retry`)
  return response.data
}

/**
 * 获取文件预览URL
 */
export const getFilePreviewUrl = async (kbId, fileId) => {
  const response = await axios.get(`/knowledge-bases/${kbId}/files/${fileId}/preview-url`)
  return response.data
}

/**
 * 批量删除文件
 */
export const batchDeleteFiles = async (kbId, fileIds) => {
  const response = await axios.delete(`/knowledge-bases/${kbId}/files/batch`, {
    data: { file_ids: fileIds }
  })
  return response.data
}

// ============ 图谱导出 API ============

/**
 * 导出知识图谱
 * @param {number} kbId - 知识库ID
 * @param {string} format - 导出格式: 'json' | 'csv'
 */
export const exportKnowledgeGraph = async (kbId, format = 'json') => {
  const response = await axios.get(`/knowledge-bases/${kbId}/graph/export`, {
    params: { format },
    responseType: format === 'json' ? 'json' : 'blob'
  })
  return response.data
}

/**
 * 下载知识图谱导出文件
 */
export const downloadKnowledgeGraph = async (kbId, format = 'json') => {
  const response = await axios.get(`/knowledge-bases/${kbId}/graph/export`, {
    params: { format },
    responseType: 'blob'
  })
  
  // 创建下载链接
  const blob = new Blob([response.data], { 
    type: format === 'json' ? 'application/json' : 'text/csv' 
  })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `knowledge_graph_${kbId}.${format}`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
