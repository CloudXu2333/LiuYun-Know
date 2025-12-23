/**
 * LLM 配置 API
 */
import axios from './axios'

/**
 * 获取所有 LLM 提供商
 */
export const getProviders = async () => {
  const response = await axios.get('/llm/providers')
  return response.data
}

/**
 * 获取模型列表
 * @param {string} provider - 提供商 ID（可选）
 */
export const getModels = async (provider = null) => {
  const params = provider ? { provider } : {}
  const response = await axios.get('/llm/models', { params })
  return response.data
}

/**
 * 获取当前 LLM 配置
 */
export const getLLMConfig = async () => {
  const response = await axios.get('/llm/config')
  return response.data
}

/**
 * 测试 LLM 连接
 * @param {Object} params - 测试参数
 */
export const testLLMConnection = async (params) => {
  const response = await axios.post('/llm/test', null, {
    params: {
      provider: params.provider,
      model: params.model,
      api_key: params.apiKey,
      base_url: params.baseUrl
    }
  })
  return response.data
}

/**
 * 使用指定模型进行流式对话
 * @param {Object} data - 对话数据
 * @param {Function} onMessage - 消息回调
 * @param {Function} onError - 错误回调
 * @param {Function} onDone - 完成回调
 * @returns {AbortController} - 用于取消请求
 */
export function chatWithModelStream(data, onMessage, onError, onDone) {
  const controller = new AbortController()
  const token = localStorage.getItem('access_token')

  fetch(`/api/llm/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(data),
    signal: controller.signal
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      function read() {
        reader
          .read()
          .then(({ done, value }) => {
            if (done) {
              onDone && onDone()
              return
            }

            const text = decoder.decode(value, { stream: true })
            const lines = text.split('\n')

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6)
                if (data === '[DONE]') {
                  onDone && onDone()
                  return
                }

                try {
                  const parsed = JSON.parse(data)
                  onMessage && onMessage(parsed)
                } catch (e) {
                  // 忽略解析错误
                }
              }
            }

            read()
          })
          .catch((err) => {
            if (err.name !== 'AbortError') {
              onError && onError(err)
            }
          })
      }

      read()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError && onError(err)
      }
    })

  return controller
}

// 预定义的模型分组
export const MODEL_GROUPS = {
  claude: {
    name: 'Claude',
    icon: '🟣',
    models: ['claude-sonnet-4-5-20250929', 'claude-opus-4-5-20251101']
  },
  gpt: {
    name: 'GPT',
    icon: '🟢',
    models: ['gpt-5.2', 'gpt-5.1']
  },
  gemini: {
    name: 'Gemini',
    icon: '🔵',
    models: ['gemini-3-pro-preview', 'gemini-2.5-pro']
  },
  deepseek: {
    name: 'DeepSeek',
    icon: '🔴',
    models: ['deepseek-chat']
  }
}

// 获取模型的分组
export function getModelGroup(modelId) {
  for (const [key, group] of Object.entries(MODEL_GROUPS)) {
    if (group.models.includes(modelId)) {
      return { key, ...group }
    }
  }
  return { key: 'other', name: '其他', icon: '⚪' }
}

// ============ 用户配置管理 ============

/**
 * 创建用户 LLM 配置
 */
export const createUserConfig = async (data) => {
  const response = await axios.post('/llm/configs', data)
  return response.data
}

/**
 * 获取用户的所有配置
 */
export const getUserConfigs = async () => {
  const response = await axios.get('/llm/configs')
  return response.data
}

/**
 * 获取单个配置
 */
export const getUserConfig = async (configId) => {
  const response = await axios.get(`/llm/configs/${configId}`)
  return response.data
}

/**
 * 更新配置
 */
export const updateUserConfig = async (configId, data) => {
  const response = await axios.put(`/llm/configs/${configId}`, data)
  return response.data
}

/**
 * 删除配置
 */
export const deleteUserConfig = async (configId) => {
  const response = await axios.delete(`/llm/configs/${configId}`)
  return response.data
}
