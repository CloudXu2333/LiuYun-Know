<template>
  <div class="relative" ref="dropdownRef">
    <!-- 触发按钮 -->
    <button
      @click="toggleDropdown"
      class="flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs transition-all duration-200"
      :class="hasCustomConfig ? 'bg-purple-50 text-purple-600 hover:bg-purple-100' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
    >
      <span class="text-base">{{ currentModelIcon }}</span>
      <span class="max-w-[120px] truncate">{{ currentModelName }}</span>
      <svg class="w-3 h-3 transition-transform" :class="showDropdown ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    </button>

    <!-- 下拉面板 -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-show="showDropdown"
        class="absolute bottom-full left-0 mb-2 w-80 rounded-xl shadow-xl bg-white ring-1 ring-black ring-opacity-5 focus:outline-none overflow-hidden z-50"
      >
        <!-- 标签页 -->
        <div class="flex border-b border-gray-100">
          <button
            @click="activeTab = 'models'"
            class="flex-1 px-4 py-2.5 text-sm font-medium transition-colors"
            :class="activeTab === 'models' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'"
          >
            选择模型
          </button>
          <button
            @click="activeTab = 'custom'"
            class="flex-1 px-4 py-2.5 text-sm font-medium transition-colors"
            :class="activeTab === 'custom' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'"
          >
            添加配置
          </button>
        </div>

        <!-- 模型选择面板 -->
        <div v-show="activeTab === 'models'" class="max-h-96 overflow-y-auto p-2">
          <!-- 提供商选择 -->
          <div class="flex space-x-1 mb-2 p-1 bg-gray-50 rounded-lg">
            <button
              v-for="provider in allProviders"
              :key="provider.id"
              @click="selectedProvider = provider.id"
              class="flex-1 px-2 py-1.5 text-xs rounded-md transition-colors"
              :class="selectedProvider === provider.id ? 'bg-white shadow text-blue-600' : 'text-gray-500 hover:text-gray-700'"
            >
              {{ provider.name }}
              <span v-if="provider.id === 'custom' && userConfigs.length > 0" class="ml-1 text-purple-500">({{ userConfigs.length }})</span>
            </button>
          </div>

          <!-- 平台模型列表 -->
          <div v-if="selectedProvider === 'platform'" class="space-y-1">
            <div v-if="platformConfigs.length === 0" class="text-center py-8 text-gray-500">
              <p class="text-sm">暂无可用模型</p>
              <p class="text-xs mt-1">请联系管理员添加模型配置</p>
            </div>
            <button
              v-for="config in platformConfigs"
              :key="config.id"
              @click="selectPlatformConfig(config)"
              class="w-full flex items-center justify-between p-2.5 rounded-lg transition-colors text-left"
              :class="currentPlatformConfigId === config.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-700'"
            >
              <div class="flex items-center space-x-2">
                <span class="text-base">{{ getModelIcon(config.model) }}</span>
                <div>
                  <p class="text-sm font-medium">{{ config.name }}</p>
                  <p class="text-xs text-gray-400">{{ config.description || config.model }}</p>
                </div>
              </div>
              <svg v-if="currentPlatformConfigId === config.id" class="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
              </svg>
            </button>
          </div>

          <!-- 自定义配置列表 -->
          <div v-else class="space-y-1">
            <!-- 用户保存的配置 -->
            <div v-if="userConfigs.length > 0">
              <div
                v-for="config in userConfigs"
                :key="config.id"
                class="w-full flex items-center justify-between p-2.5 rounded-lg transition-colors text-left group"
                :class="currentConfigId === config.id ? 'bg-purple-50 text-purple-700' : 'hover:bg-gray-50 text-gray-700'"
              >
                <button
                  @click="useSavedConfig(config)"
                  class="flex items-center space-x-2 flex-1 min-w-0"
                >
                  <span class="text-base">⚙️</span>
                  <div class="min-w-0">
                    <p class="text-sm font-medium truncate">{{ config.name }}</p>
                    <p class="text-xs text-gray-400 truncate">{{ config.model }}</p>
                  </div>
                </button>
                <div class="flex items-center space-x-1">
                  <svg v-if="currentConfigId === config.id" class="w-4 h-4 text-purple-600 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                  </svg>
                  <button
                    @click.stop="deleteSavedConfig(config.id)"
                    class="p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                    title="删除配置"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            
            <!-- 无配置提示 -->
            <div v-else class="text-center py-8 text-gray-500">
              <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              <p class="text-sm">暂无自定义配置</p>
              <p class="text-xs mt-1">点击"添加配置"创建</p>
            </div>
            
            <!-- 添加配置按钮 -->
            <button
              @click="activeTab = 'custom'"
              class="w-full flex items-center justify-center space-x-2 p-2.5 mt-2 rounded-lg border-2 border-dashed border-gray-200 text-gray-500 hover:border-blue-300 hover:text-blue-500 transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
              </svg>
              <span class="text-sm">添加新配置</span>
            </button>
          </div>
        </div>

        <!-- 添加配置面板 -->
        <div v-show="activeTab === 'custom'" class="max-h-96 overflow-y-auto p-4 space-y-4">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">配置名称 *</label>
            <input
              v-model="customConfigName"
              type="text"
              placeholder="我的 GPT-4"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
            />
          </div>
          
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">模型名称 *</label>
            <input
              v-model="customModel"
              type="text"
              placeholder="gpt-4o / claude-3-opus / gemini-pro"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
            />
          </div>
          
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">API 标准</label>
            <select
              v-model="customApiStandard"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
            >
              <option value="openai">OpenAI 兼容 (GPT/Claude/DeepSeek)</option>
              <option value="gemini">Google Gemini</option>
              <option value="anthropic">Anthropic Claude</option>
            </select>
          </div>
          
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">API Base URL *</label>
            <input
              v-model="customBaseUrl"
              type="text"
              placeholder="https://api.openai.com/v1"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
            />
          </div>
          
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">API Key *</label>
            <input
              v-model="customApiKey"
              type="password"
              placeholder="sk-..."
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
            />
          </div>
          
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">上下文限制 (Token)</label>
            <input
              v-model.number="customMaxContextTokens"
              type="number"
              min="1000"
              step="1000"
              placeholder="65536"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
            />
            <div class="flex flex-wrap gap-1 mt-1">
              <button
                v-for="preset in [16000, 32000, 65536, 131072, 200000]"
                :key="preset"
                @click="customMaxContextTokens = preset"
                type="button"
                class="px-2 py-0.5 text-xs rounded transition-colors"
                :class="customMaxContextTokens === preset ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
              >
                {{ preset >= 1000 ? (preset / 1000) + 'K' : preset }}
              </button>
            </div>
          </div>
          
          <div class="flex space-x-2">
            <button
              @click="testConnection"
              :disabled="testing || !customModel || !customApiKey"
              class="flex-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              {{ testing ? '测试中...' : '测试连接' }}
            </button>
            <button
              @click="saveCurrentConfig"
              :disabled="!canSaveConfig"
              class="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              保存配置
            </button>
          </div>
          
          <!-- 测试结果 -->
          <div v-if="testResult" class="p-3 rounded-lg text-sm" :class="testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
            {{ testResult.message }}
          </div>
          
          <!-- 返回按钮 -->
          <button
            @click="activeTab = 'models'; selectedProvider = 'custom'"
            class="w-full px-3 py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            ← 返回模型列表
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { testLLMConnection, getModelGroup, getUserConfigs, createUserConfig, deleteUserConfig } from '@/api/llm'
import { getActivePlatformConfigs } from '@/api/platformLlm'

const emit = defineEmits(['update:config'])

const props = defineProps({
  config: {
    type: Object,
    default: () => ({
      provider: 'platform',
      model: '',
      apiKey: null,
      baseUrl: null,
      configId: null,
      platformConfigId: null,  // 平台配置 ID
      maxContextTokens: 65536
    })
  }
})

// 状态
const showDropdown = ref(false)
const activeTab = ref('models')
const dropdownRef = ref(null)
const platformConfigs = ref([])  // 平台配置列表
const selectedProvider = ref('platform')  // 默认选择平台配置
const testing = ref(false)
const testResult = ref(null)
const userConfigs = ref([])

// 自定义配置表单
const customConfigName = ref('')
const customBaseUrl = ref('')
const customApiKey = ref('')
const customModel = ref('')
const customApiStandard = ref('openai')
const customMaxContextTokens = ref(65536)

// 当前配置
const currentProvider = ref(props.config.provider || 'platform')
const currentModel = ref(props.config.model || '')
const currentApiKey = ref(props.config.apiKey || null)
const currentBaseUrl = ref(props.config.baseUrl || null)
const currentConfigId = ref(props.config.configId || null)
const currentPlatformConfigId = ref(props.config.platformConfigId || null)
const currentMaxContextTokens = ref(props.config.maxContextTokens || 65536)

// 计算属性
const hasCustomConfig = computed(() => {
  return currentConfigId.value !== null
})

const currentModelName = computed(() => {
  // 如果使用的是用户自定义配置
  if (currentConfigId.value) {
    const config = userConfigs.value.find(c => c.id === currentConfigId.value)
    return config?.name || currentModel.value
  }
  // 如果使用的是平台配置
  if (currentPlatformConfigId.value) {
    const config = platformConfigs.value.find(c => c.id === currentPlatformConfigId.value)
    return config?.name || currentModel.value
  }
  return currentModel.value || '选择模型'
})

const currentModelIcon = computed(() => {
  if (currentConfigId.value) {
    return '⚙️'
  }
  if (currentPlatformConfigId.value) {
    const config = platformConfigs.value.find(c => c.id === currentPlatformConfigId.value)
    if (config) {
      return getModelIcon(config.model)
    }
  }
  return getModelIcon(currentModel.value)
})

// 提供商列表：平台配置 + 自定义
const allProviders = computed(() => {
  return [
    { id: 'platform', name: '平台模型' },
    { id: 'custom', name: '自定义' }
  ]
})

const canSaveConfig = computed(() => {
  return customConfigName.value.trim() && customModel.value.trim() && customApiKey.value.trim() && customBaseUrl.value.trim()
})

// 方法
function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

function getModelIcon(modelId) {
  if (!modelId) return '🤖'
  const group = getModelGroup(modelId)
  return group.icon
}

function selectPlatformConfig(config) {
  currentModel.value = config.model
  currentProvider.value = 'platform'
  currentPlatformConfigId.value = config.id
  currentConfigId.value = null
  currentApiKey.value = null  // 平台配置不暴露 API Key
  currentBaseUrl.value = config.base_url
  currentMaxContextTokens.value = config.max_context_tokens || 65536
  emitConfig()
  showDropdown.value = false
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  
  try {
    const result = await testLLMConnection({
      provider: 'custom',
      model: customModel.value,
      apiKey: customApiKey.value,
      baseUrl: customBaseUrl.value
    })
    testResult.value = result
  } catch (error) {
    testResult.value = {
      success: false,
      message: error.message || '连接测试失败'
    }
  } finally {
    testing.value = false
  }
}

async function saveCurrentConfig() {
  if (!canSaveConfig.value) return
  
  try {
    await createUserConfig({
      name: customConfigName.value.trim(),
      provider: 'custom',
      model: customModel.value.trim(),
      api_key: customApiKey.value.trim(),
      base_url: customBaseUrl.value.trim() || null,
      api_standard: customApiStandard.value,
      max_context_tokens: customMaxContextTokens.value
    })
    
    // 重新加载配置列表
    await loadUserConfigs()
    
    // 清空表单
    customConfigName.value = ''
    customApiKey.value = ''
    customBaseUrl.value = ''
    customModel.value = ''
    customApiStandard.value = 'openai'
    customMaxContextTokens.value = 65536
    
    testResult.value = {
      success: true,
      message: '配置保存成功！'
    }
    
    // 切换到模型列表并选中自定义
    setTimeout(() => {
      testResult.value = null
      activeTab.value = 'models'
      selectedProvider.value = 'custom'
    }, 1500)
  } catch (error) {
    testResult.value = {
      success: false,
      message: error.message || '保存失败'
    }
  }
}

async function useSavedConfig(config) {
  currentModel.value = config.model
  currentApiKey.value = config.api_key
  currentBaseUrl.value = config.base_url
  currentProvider.value = 'custom'
  currentConfigId.value = config.id
  currentPlatformConfigId.value = null
  currentMaxContextTokens.value = config.max_context_tokens || 65536
  emitConfig()
  showDropdown.value = false
}

async function deleteSavedConfig(configId) {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个配置吗？',
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await deleteUserConfig(configId)
    await loadUserConfigs()
    
    // 如果删除的是当前使用的配置，重置为默认（选择第一个平台配置）
    if (currentConfigId.value === configId) {
      currentConfigId.value = null
      currentApiKey.value = null
      currentBaseUrl.value = null
      currentProvider.value = 'platform'
      if (platformConfigs.value.length > 0) {
        selectPlatformConfig(platformConfigs.value[0])
      } else {
        currentModel.value = ''
        currentPlatformConfigId.value = null
        currentMaxContextTokens.value = 65536
        emitConfig()
      }
    }
    
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除配置失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

function emitConfig() {
  emit('update:config', {
    provider: currentProvider.value,
    model: currentModel.value,
    apiKey: currentApiKey.value,
    baseUrl: currentBaseUrl.value,
    configId: currentConfigId.value,
    platformConfigId: currentPlatformConfigId.value,
    maxContextTokens: currentMaxContextTokens.value
  })
}

// 点击外部关闭
function handleClickOutside(event) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    showDropdown.value = false
  }
}

// 加载平台配置
async function loadPlatformConfigs() {
  try {
    platformConfigs.value = await getActivePlatformConfigs()
    // 如果当前没有选择任何配置，默认选择第一个平台配置
    if (!currentPlatformConfigId.value && !currentConfigId.value && platformConfigs.value.length > 0) {
      selectPlatformConfig(platformConfigs.value[0])
    }
  } catch (error) {
    console.error('加载平台配置失败:', error)
  }
}

// 加载用户配置
async function loadUserConfigs() {
  try {
    userConfigs.value = await getUserConfigs()
  } catch (error) {
    console.error('加载用户配置失败:', error)
  }
}

// 监听 props 变化
watch(() => props.config, (newConfig) => {
  if (newConfig) {
    currentProvider.value = newConfig.provider || 'platform'
    currentModel.value = newConfig.model || ''
    currentApiKey.value = newConfig.apiKey || null
    currentBaseUrl.value = newConfig.baseUrl || null
    currentConfigId.value = newConfig.configId || null
    currentPlatformConfigId.value = newConfig.platformConfigId || null
    currentMaxContextTokens.value = newConfig.maxContextTokens || 65536
    if (newConfig.provider === 'platform') {
      selectedProvider.value = 'platform'
    } else if (newConfig.configId) {
      selectedProvider.value = 'custom'
    }
  }
}, { deep: true })

onMounted(() => {
  loadPlatformConfigs()
  loadUserConfigs()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* 移除输入框聚焦时的黑色边框 */
input:focus,
select:focus,
button:focus {
  outline: none !important;
  box-shadow: none !important;
}

input,
select {
  outline: none !important;
}
</style>
