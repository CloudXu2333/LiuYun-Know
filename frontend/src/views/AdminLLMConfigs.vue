<template>
  <div class="min-h-screen bg-gemini-bg">
    <!-- 顶部导航 -->
    <header class="glass-gemini border-b border-gemini-border sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-14">
          <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-2 cursor-pointer" @click="router.push('/chat')">
              <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm">
                <span class="text-white text-xs font-bold">L</span>
              </div>
              <span class="text-lg font-semibold text-gemini-text-primary">LiuYun</span>
            </div>
            <span class="text-gray-300">|</span>
            <span class="text-gray-600">模型配置管理</span>
          </div>
          <button
            @click="router.push('/chat')"
            class="flex items-center space-x-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
            <span>返回</span>
          </button>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 操作栏 -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-xl font-semibold text-gray-900">平台模型配置</h1>
          <p class="text-sm text-gray-500 mt-1">管理所有用户可用的 LLM 模型配置</p>
        </div>
        <button
          @click="openCreateDialog"
          class="flex items-center space-x-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
          </svg>
          <span>添加配置</span>
        </button>
      </div>

      <!-- 配置列表 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">名称</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">模型</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">上下文限制</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">排序</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-if="loading" class="animate-pulse">
              <td colspan="6" class="px-6 py-12 text-center text-gray-500">
                <svg class="animate-spin h-8 w-8 mx-auto text-blue-500" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </td>
            </tr>
            <tr v-else-if="configs.length === 0">
              <td colspan="6" class="px-6 py-12 text-center text-gray-500">暂无配置，点击"添加配置"创建</td>
            </tr>
            <tr v-for="config in configs" :key="config.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4 whitespace-nowrap">
                <div>
                  <div class="text-sm font-medium text-gray-900">{{ config.name }}</div>
                  <div class="text-xs text-gray-400">{{ config.provider }}</div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ config.model }}</div>
                <div class="text-xs text-gray-400 truncate max-w-xs">{{ config.base_url }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ formatTokens(config.max_context_tokens) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span
                  :class="config.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'"
                  class="px-2 py-1 text-xs font-medium rounded-full"
                >
                  {{ config.is_active ? '启用' : '禁用' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ config.sort_order }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button 
                  @click="testConfig(config)" 
                  :disabled="testingConfigId === config.id"
                  class="text-green-600 hover:text-green-900 mr-3 disabled:opacity-50"
                >
                  {{ testingConfigId === config.id ? '测试中...' : '测试' }}
                </button>
                <button @click="openEditDialog(config)" class="text-blue-600 hover:text-blue-900 mr-3">编辑</button>
                <button @click="confirmDelete(config)" class="text-red-600 hover:text-red-900">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>

    <!-- 创建/编辑对话框 -->
    <div v-if="showDialog" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/50" @click="closeDialog"></div>
      <div class="relative bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          {{ isEditing ? '编辑配置' : '添加配置' }}
        </h3>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">配置名称 *</label>
            <input
              v-model="formData.name"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="如：GPT-4o"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">提供商 *</label>
              <input
                v-model="formData.provider"
                type="text"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="如：openai"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">模型名称 *</label>
              <input
                v-model="formData.model"
                type="text"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="如：gpt-4o"
              />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">API Base URL *</label>
            <input
              v-model="formData.base_url"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="https://api.openai.com/v1"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">API Key *</label>
            <input
              v-model="formData.api_key"
              type="password"
              :required="!isEditing"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              :placeholder="isEditing ? '留空则不修改' : 'sk-...'"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">API 标准</label>
              <select
                v-model="formData.api_standard"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                <option value="openai">OpenAI 兼容</option>
                <option value="gemini">Google Gemini</option>
                <option value="anthropic">Anthropic</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">上下文限制</label>
              <input
                v-model.number="formData.max_context_tokens"
                type="number"
                min="1000"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <div class="flex flex-wrap gap-1 mt-1">
                <button
                  v-for="preset in [32000, 65536, 131072, 200000]"
                  :key="preset"
                  @click.prevent="formData.max_context_tokens = preset"
                  type="button"
                  class="px-2 py-0.5 text-xs rounded transition-colors"
                  :class="formData.max_context_tokens === preset ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
                >
                  {{ preset / 1000 }}K
                </button>
              </div>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
            <textarea
              v-model="formData.description"
              rows="2"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="可选描述"
            ></textarea>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">排序</label>
              <input
                v-model.number="formData.sort_order"
                type="number"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
            </div>
            <div class="flex items-end">
              <label class="flex items-center">
                <input
                  v-model="formData.is_active"
                  type="checkbox"
                  class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span class="ml-2 text-sm text-gray-700">启用此配置</span>
              </label>
            </div>
          </div>
          <div v-if="formError" class="text-red-500 text-sm">{{ formError }}</div>
          <div v-if="testResult" class="p-3 rounded-lg text-sm" :class="testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
            {{ testResult.message }}
          </div>
          <div class="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              @click="testFormConfig"
              :disabled="testing || !formData.model || !formData.api_key || !formData.base_url"
              class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              {{ testing ? '测试中...' : '测试连接' }}
            </button>
            <button
              type="button"
              @click="closeDialog"
              class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              {{ submitting ? '提交中...' : '确定' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/50" @click="showDeleteConfirm = false"></div>
      <div class="relative bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-2">确认删除</h3>
        <p class="text-gray-600 mb-6">确定要删除配置 "{{ deletingConfig?.name }}" 吗？此操作不可恢复。</p>
        <div class="flex justify-end space-x-3">
          <button
            @click="showDeleteConfirm = false"
            class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm"
          >
            取消
          </button>
          <button
            @click="handleDelete"
            :disabled="submitting"
            class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm disabled:opacity-50"
          >
            {{ submitting ? '删除中...' : '删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getPlatformConfigs,
  createPlatformConfig,
  updatePlatformConfig,
  deletePlatformConfig,
  testPlatformConfig
} from '@/api/platformLlm'

const router = useRouter()

// 状态
const configs = ref([])
const loading = ref(false)

const showDialog = ref(false)
const isEditing = ref(false)
const editingConfig = ref(null)
const formData = ref({
  name: '',
  provider: '',
  model: '',
  api_key: '',
  base_url: '',
  api_standard: 'openai',
  max_context_tokens: 65536,
  description: '',
  is_active: true,
  sort_order: 0
})
const formError = ref('')
const submitting = ref(false)
const testing = ref(false)
const testResult = ref(null)
const testingConfigId = ref(null)

const showDeleteConfirm = ref(false)
const deletingConfig = ref(null)

// 格式化 token 数
const formatTokens = (tokens) => {
  if (tokens >= 1000) {
    return (tokens / 1000) + 'K'
  }
  return tokens
}

// 加载配置列表
const loadConfigs = async () => {
  loading.value = true
  try {
    configs.value = await getPlatformConfigs()
  } catch (error) {
    console.error('Failed to load configs:', error)
  } finally {
    loading.value = false
  }
}

// 打开创建对话框
const openCreateDialog = () => {
  isEditing.value = false
  editingConfig.value = null
  formData.value = {
    name: '',
    provider: '',
    model: '',
    api_key: '',
    base_url: '',
    api_standard: 'openai',
    max_context_tokens: 65536,
    description: '',
    is_active: true,
    sort_order: 0
  }
  formError.value = ''
  testResult.value = null
  showDialog.value = true
}

// 打开编辑对话框
const openEditDialog = (config) => {
  isEditing.value = true
  editingConfig.value = config
  formData.value = {
    name: config.name,
    provider: config.provider,
    model: config.model,
    api_key: '',  // 不显示原有 key
    base_url: config.base_url,
    api_standard: config.api_standard || 'openai',
    max_context_tokens: config.max_context_tokens,
    description: config.description || '',
    is_active: config.is_active,
    sort_order: config.sort_order
  }
  formError.value = ''
  testResult.value = null
  showDialog.value = true
}

// 关闭对话框
const closeDialog = () => {
  showDialog.value = false
  editingConfig.value = null
  testResult.value = null
}

// 测试表单中的配置
const testFormConfig = async () => {
  testing.value = true
  testResult.value = null
  
  try {
    // 如果是编辑模式且没有填写新的 api_key，需要使用已保存配置的 id 来测试
    if (isEditing.value && !formData.value.api_key) {
      const result = await testPlatformConfig(editingConfig.value.id)
      testResult.value = result
    } else {
      // 新建或有新 api_key，直接测试
      const result = await testPlatformConfig(null, {
        model: formData.value.model,
        api_key: formData.value.api_key,
        base_url: formData.value.base_url
      })
      testResult.value = result
    }
  } catch (error) {
    testResult.value = {
      success: false,
      message: error.response?.data?.detail || error.message || '连接测试失败'
    }
  } finally {
    testing.value = false
  }
}

// 测试列表中的配置
const testConfig = async (config) => {
  testingConfigId.value = config.id
  
  try {
    const result = await testPlatformConfig(config.id)
    if (result.success) {
      ElMessage.success(`${config.name}: 连接成功`)
    } else {
      ElMessage.error(`${config.name}: ${result.message}`)
    }
  } catch (error) {
    ElMessage.error(`${config.name}: ${error.response?.data?.detail || '连接测试失败'}`)
  } finally {
    testingConfigId.value = null
  }
}

// 提交表单
const handleSubmit = async () => {
  formError.value = ''
  submitting.value = true

  try {
    const data = { ...formData.value }
    
    if (isEditing.value) {
      // 编辑时，如果 api_key 为空则不更新
      if (!data.api_key) {
        delete data.api_key
      }
      await updatePlatformConfig(editingConfig.value.id, data)
    } else {
      await createPlatformConfig(data)
    }
    closeDialog()
    loadConfigs()
  } catch (error) {
    formError.value = error.response?.data?.detail || '操作失败'
  } finally {
    submitting.value = false
  }
}

// 确认删除
const confirmDelete = (config) => {
  deletingConfig.value = config
  showDeleteConfirm.value = true
}

// 删除配置
const handleDelete = async () => {
  submitting.value = true
  try {
    await deletePlatformConfig(deletingConfig.value.id)
    showDeleteConfirm.value = false
    deletingConfig.value = null
    loadConfigs()
  } catch (error) {
    console.error('Failed to delete config:', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.glass-gemini {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}
</style>
