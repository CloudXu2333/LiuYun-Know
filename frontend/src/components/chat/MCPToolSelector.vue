<template>
  <div class="relative" ref="dropdownRef">
    <!-- 触发按钮 -->
    <button 
      @click="toggleDropdown"
      class="p-2 rounded-full transition-colors mr-1 mb-1"
      :class="selectedTools.length > 0 ? 'text-purple-600 bg-purple-50 hover:bg-purple-100' : 'text-gray-400 hover:text-purple-500 hover:bg-purple-50'"
      :title="selectedTools.length > 0 ? `已选择 ${selectedTools.length} 个 MCP 工具` : '选择 MCP 工具'"
    >
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
      </svg>
      <!-- 选中数量徽章 -->
      <span 
        v-if="selectedTools.length > 0"
        class="absolute -top-1 -right-1 w-4 h-4 bg-purple-600 text-white text-xs rounded-full flex items-center justify-center"
      >
        {{ selectedTools.length }}
      </span>
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
        class="absolute bottom-full left-0 mb-2 w-80 rounded-xl shadow-xl bg-white ring-1 ring-black ring-opacity-5 focus:outline-none py-3 max-h-96 overflow-hidden flex flex-col"
      >
        <!-- 头部 -->
        <div class="flex items-center justify-between px-4 pb-3 border-b">
          <h3 class="text-sm font-medium text-gray-900">MCP 工具</h3>
          <div class="flex items-center space-x-2">
            <button 
              @click="router.push('/mcp-tools')"
              class="text-xs text-blue-500 hover:text-blue-600"
            >
              管理工具
            </button>
            <button @click="showDropdown = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- 工具列表 -->
        <div class="flex-1 overflow-y-auto px-2 py-2">
          <!-- 加载中 -->
          <div v-if="loading" class="flex items-center justify-center py-8">
            <svg class="animate-spin h-5 w-5 text-purple-500" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          
          <!-- 无工具 -->
          <div v-else-if="allTools.length === 0" class="text-center py-8 text-gray-500 text-sm">
            <p>暂无可用的 MCP 工具</p>
            <button 
              @click="router.push('/mcp-tools')"
              class="mt-2 text-blue-500 hover:text-blue-600"
            >
              去添加工具
            </button>
          </div>
          
          <!-- 工具列表 -->
          <div v-else class="space-y-1">
            <!-- 平台工具 -->
            <div v-if="platformTools.length > 0">
              <div class="px-2 py-1 text-xs text-gray-400 font-medium">平台工具</div>
              <label
                v-for="tool in platformTools"
                :key="tool.id"
                class="flex items-start p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  :value="tool.id"
                  v-model="selectedTools"
                  class="w-4 h-4 mt-0.5 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <div class="ml-3 flex-1 min-w-0">
                  <div class="flex items-center space-x-2">
                    <span class="text-sm font-medium text-gray-900">{{ tool.name }}</span>
                    <span v-if="!tool.enabled" class="text-xs text-gray-400">(已禁用)</span>
                  </div>
                  <p v-if="tool.description" class="text-xs text-gray-500 truncate">{{ tool.description }}</p>
                </div>
              </label>
            </div>
            
            <!-- 用户工具 -->
            <div v-if="userTools.length > 0">
              <div class="px-2 py-1 text-xs text-gray-400 font-medium mt-2">我的工具</div>
              <label
                v-for="tool in userTools"
                :key="tool.id"
                class="flex items-start p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  :value="tool.id"
                  v-model="selectedTools"
                  class="w-4 h-4 mt-0.5 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <div class="ml-3 flex-1 min-w-0">
                  <div class="flex items-center space-x-2">
                    <span class="text-sm font-medium text-gray-900">{{ tool.name }}</span>
                    <span v-if="!tool.enabled" class="text-xs text-gray-400">(已禁用)</span>
                  </div>
                  <p v-if="tool.description" class="text-xs text-gray-500 truncate">{{ tool.description }}</p>
                </div>
              </label>
            </div>
          </div>
        </div>
        
        <!-- 底部操作 -->
        <div v-if="selectedTools.length > 0" class="px-4 pt-2 border-t">
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-500">已选择 {{ selectedTools.length }} 个工具</span>
            <button 
              @click="clearSelection"
              class="text-xs text-red-500 hover:text-red-600"
            >
              清除选择
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getMCPTools } from '@/api/mcp'

const router = useRouter()

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

// 状态
const showDropdown = ref(false)
const loading = ref(false)
const platformTools = ref([])
const userTools = ref([])
const dropdownRef = ref(null)

// 选中的工具
const selectedTools = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 所有工具
const allTools = computed(() => [...platformTools.value, ...userTools.value])

// 切换下拉框
const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value
  if (showDropdown.value) {
    loadTools()
  }
}

// 加载工具列表
const loadTools = async () => {
  if (platformTools.value.length > 0 || userTools.value.length > 0) {
    return // 已加载过
  }
  
  loading.value = true
  try {
    const data = await getMCPTools()
    platformTools.value = (data.platform_tools || []).filter(t => t.enabled)
    userTools.value = (data.user_tools || []).filter(t => t.enabled)
  } catch (error) {
    console.error('Failed to load MCP tools:', error)
  } finally {
    loading.value = false
  }
}

// 清除选择
const clearSelection = () => {
  selectedTools.value = []
}

// 点击外部关闭
const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    showDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
