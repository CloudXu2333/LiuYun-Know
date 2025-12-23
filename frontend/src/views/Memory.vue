<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部导航 -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div class="max-w-6xl mx-auto px-4">
        <div class="flex justify-between items-center h-14">
          <div class="flex items-center space-x-3">
            <button @click="router.push('/chat')" class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
              </svg>
            </button>
            <div class="flex items-center space-x-2">
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                </svg>
              </div>
              <span class="text-lg font-semibold text-gray-800">长期记忆</span>
            </div>
          </div>
          <button
            @click="openCreateDialog"
            class="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            <span>添加记忆</span>
          </button>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="max-w-6xl mx-auto px-4 py-6">
      <!-- 说明卡片 -->
      <div class="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-4 mb-6 border border-purple-100">
        <div class="flex items-start space-x-3">
          <div class="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
            <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <div>
            <h3 class="font-medium text-purple-900">什么是长期记忆？</h3>
            <p class="text-sm text-purple-700 mt-1">
              长期记忆是跨对话持久化的信息，每次对话时 AI 都会参考这些记忆。
              你可以添加个人偏好、重要事实、特殊指令等，让 AI 更好地理解你。
            </p>
          </div>
        </div>
      </div>

      <!-- AI智能提取输入框 -->
      <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6 shadow-sm">
        <div class="flex items-center space-x-2 mb-3">
          <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
          </svg>
          <span class="font-medium text-gray-800">AI 智能提取</span>
          <span class="text-xs text-gray-500">输入任意内容，AI 自动分析分类</span>
        </div>
        <div class="flex space-x-3">
          <textarea
            v-model="autoExtractInput"
            rows="2"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            placeholder="输入任意内容，如：我喜欢简洁的代码风格，不喜欢过多注释..."
          ></textarea>
          <button
            @click="handleAutoExtract"
            :disabled="!autoExtractInput.trim() || extracting"
            class="px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg hover:from-purple-600 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <svg v-if="extracting" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            <span>{{ extracting ? '提取中...' : '智能提取' }}</span>
          </button>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="flex items-center space-x-4 mb-4">
        <select
          v-model="filterCategory"
          class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="">全部分类</option>
          <option v-for="cat in categories" :key="cat.value" :value="cat.value">
            {{ cat.label }}
          </option>
        </select>
        <label class="flex items-center space-x-2 text-sm text-gray-600">
          <input type="checkbox" v-model="showInactiveOnly" class="rounded text-purple-600 focus:ring-purple-500">
          <span>显示已禁用</span>
        </label>
        <span class="text-sm text-gray-500">共 {{ memories.length }} 条记忆</span>
      </div>

      <!-- 记忆列表 -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>

      <div v-else-if="memories.length === 0" class="text-center py-12">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
          <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
          </svg>
        </div>
        <p class="text-gray-500">还没有添加任何记忆</p>
        <button @click="openCreateDialog" class="mt-4 text-purple-600 hover:text-purple-700">
          添加第一条记忆 →
        </button>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="memory in memories"
          :key="memory.id"
          class="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow"
          :class="{ 'opacity-60': !memory.is_active }"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <div class="flex items-center space-x-2 mb-2">
                <span
                  class="px-2 py-0.5 text-xs rounded-full"
                  :class="getCategoryClass(memory.category)"
                >
                  {{ getCategoryLabel(memory.category) }}
                </span>
                <span v-if="memory.priority > 0" class="text-xs text-orange-600">
                  优先级: {{ memory.priority }}
                </span>
                <span v-if="!memory.is_active" class="text-xs text-gray-400">已禁用</span>
              </div>
              <h3 class="font-medium text-gray-900 mb-1">{{ memory.title }}</h3>
              <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ memory.content }}</p>
              <p class="text-xs text-gray-400 mt-2">
                创建于 {{ formatDate(memory.created_at) }}
              </p>
            </div>
            <div class="flex items-center space-x-1 ml-4">
              <button
                @click="toggleMemoryStatus(memory)"
                class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                :title="memory.is_active ? '禁用' : '启用'"
              >
                <svg v-if="memory.is_active" class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                </svg>
                <svg v-else class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path>
                </svg>
              </button>
              <button
                @click="openEditDialog(memory)"
                class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="编辑"
              >
                <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
                </svg>
              </button>
              <button
                @click="confirmDelete(memory)"
                class="p-2 hover:bg-red-50 rounded-lg transition-colors"
                title="删除"
              >
                <svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 创建/编辑对话框 -->
    <div v-if="showDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-lg shadow-xl">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">
            {{ editingMemory ? '编辑记忆' : '添加记忆' }}
          </h2>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">标题</label>
            <input
              v-model="formData.title"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="简短描述这条记忆"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">内容</label>
            <textarea
              v-model="formData.content"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
              placeholder="详细内容..."
            ></textarea>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
              <select
                v-model="formData.category"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option v-for="cat in categories" :key="cat.value" :value="cat.value">
                  {{ cat.label }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">优先级 (0-100)</label>
              <input
                v-model.number="formData.priority"
                type="number"
                min="0"
                max="100"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <input
              type="checkbox"
              v-model="formData.is_active"
              id="is_active"
              class="rounded text-purple-600 focus:ring-purple-500"
            >
            <label for="is_active" class="text-sm text-gray-700">启用此记忆</label>
          </div>
        </div>
        <div class="p-6 border-t border-gray-200 flex justify-end space-x-3">
          <button
            @click="closeDialog"
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="saveMemory"
            :disabled="saving || !formData.title || !formData.content"
            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-sm shadow-xl p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-2">确认删除</h3>
        <p class="text-gray-600 mb-6">确定要删除记忆「{{ deletingMemory?.title }}」吗？此操作不可撤销。</p>
        <div class="flex justify-end space-x-3">
          <button
            @click="showDeleteConfirm = false"
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="doDelete"
            :disabled="deleting"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            {{ deleting ? '删除中...' : '删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getMemories,
  getMemoryCategories,
  createMemory,
  updateMemory,
  deleteMemory,
  toggleMemory,
  autoExtractMemory
} from '@/api/memory'

const router = useRouter()

// 状态
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const extracting = ref(false)
const memories = ref([])
const autoExtractInput = ref('')
const categories = ref([
  { value: 'general', label: '通用' },
  { value: 'preference', label: '偏好' },
  { value: 'fact', label: '事实' },
  { value: 'instruction', label: '指令' }
])

// 筛选
const filterCategory = ref('')
const showInactiveOnly = ref(false)

// 对话框
const showDialog = ref(false)
const editingMemory = ref(null)
const formData = ref({
  title: '',
  content: '',
  category: 'general',
  priority: 0,
  is_active: true
})

// 删除确认
const showDeleteConfirm = ref(false)
const deletingMemory = ref(null)

// 加载记忆列表
const loadMemories = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterCategory.value) {
      params.category = filterCategory.value
    }
    params.active_only = !showInactiveOnly.value
    
    const res = await getMemories(params)
    memories.value = res.items || []
  } catch (error) {
    console.error('加载记忆失败:', error)
    ElMessage.error('加载记忆失败')
  } finally {
    loading.value = false
  }
}

// 加载分类
const loadCategories = async () => {
  try {
    const res = await getMemoryCategories()
    if (res && res.length > 0) {
      categories.value = res
    }
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

// 打开创建对话框
const openCreateDialog = () => {
  editingMemory.value = null
  formData.value = {
    title: '',
    content: '',
    category: 'general',
    priority: 0,
    is_active: true
  }
  showDialog.value = true
}

// AI智能提取
const handleAutoExtract = async () => {
  if (!autoExtractInput.value.trim()) return
  
  extracting.value = true
  try {
    const result = await autoExtractMemory(autoExtractInput.value.trim())
    // 用提取结果填充表单并打开对话框
    formData.value = {
      title: result.title,
      content: result.content,
      category: result.category,
      priority: result.priority,
      is_active: true
    }
    editingMemory.value = null
    showDialog.value = true
    autoExtractInput.value = ''
    ElMessage.success('AI已提取记忆，请确认后保存')
  } catch (error) {
    console.error('AI提取失败:', error)
    ElMessage.error('AI提取失败，请重试')
  } finally {
    extracting.value = false
  }
}

// 打开编辑对话框
const openEditDialog = (memory) => {
  editingMemory.value = memory
  formData.value = {
    title: memory.title,
    content: memory.content,
    category: memory.category,
    priority: memory.priority,
    is_active: memory.is_active
  }
  showDialog.value = true
}

// 关闭对话框
const closeDialog = () => {
  showDialog.value = false
  editingMemory.value = null
}

// 保存记忆
const saveMemory = async () => {
  if (!formData.value.title || !formData.value.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  
  saving.value = true
  try {
    if (editingMemory.value) {
      await updateMemory(editingMemory.value.id, formData.value)
      ElMessage.success('记忆已更新')
    } else {
      await createMemory(formData.value)
      ElMessage.success('记忆已添加')
    }
    closeDialog()
    loadMemories()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 切换启用状态
const toggleMemoryStatus = async (memory) => {
  try {
    await toggleMemory(memory.id)
    memory.is_active = !memory.is_active
    ElMessage.success(memory.is_active ? '已启用' : '已禁用')
  } catch (error) {
    console.error('切换状态失败:', error)
    ElMessage.error('操作失败')
  }
}

// 确认删除
const confirmDelete = (memory) => {
  deletingMemory.value = memory
  showDeleteConfirm.value = true
}

// 执行删除
const doDelete = async () => {
  if (!deletingMemory.value) return
  
  deleting.value = true
  try {
    await deleteMemory(deletingMemory.value.id)
    ElMessage.success('已删除')
    showDeleteConfirm.value = false
    loadMemories()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  } finally {
    deleting.value = false
  }
}

// 获取分类样式
const getCategoryClass = (category) => {
  const classes = {
    general: 'bg-gray-100 text-gray-700',
    preference: 'bg-blue-100 text-blue-700',
    fact: 'bg-green-100 text-green-700',
    instruction: 'bg-orange-100 text-orange-700'
  }
  return classes[category] || classes.general
}

// 获取分类标签
const getCategoryLabel = (category) => {
  const cat = categories.value.find(c => c.value === category)
  return cat ? cat.label : category
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 监听筛选变化
watch([filterCategory, showInactiveOnly], () => {
  loadMemories()
})

onMounted(() => {
  loadCategories()
  loadMemories()
})
</script>
