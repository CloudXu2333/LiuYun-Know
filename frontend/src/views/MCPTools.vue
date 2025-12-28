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
            <span class="text-gray-600">MCP 工具管理</span>
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
      <!-- Tab 切换 -->
      <div class="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          @click="activeTab = 'platform'"
          :class="activeTab === 'platform' ? 'bg-white shadow-sm' : 'hover:bg-gray-50'"
          class="px-4 py-2 text-sm font-medium rounded-md transition-all"
        >
          平台工具
        </button>
        <button
          @click="activeTab = 'user'"
          :class="activeTab === 'user' ? 'bg-white shadow-sm' : 'hover:bg-gray-50'"
          class="px-4 py-2 text-sm font-medium rounded-md transition-all"
        >
          我的工具
        </button>
      </div>

      <!-- 平台工具 -->
      <div v-if="activeTab === 'platform'">
        <div class="flex justify-between items-center mb-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">平台工具</h2>
            <p class="text-sm text-gray-500">由管理员配置的公共 MCP 工具</p>
          </div>
          <button
            v-if="isAdmin"
            @click="openCreateDialog('platform')"
            class="flex items-center space-x-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            <span>添加平台工具</span>
          </button>
        </div>
        <ToolList
          :tools="platformTools"
          :loading="loading"
          :is-admin="isAdmin"
          :testing-id="testingId"
          @test="handleTest"
          @edit="openEditDialog"
          @delete="confirmDelete"
        />
      </div>

      <!-- 用户工具 -->
      <div v-if="activeTab === 'user'">
        <div class="flex justify-between items-center mb-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">我的工具</h2>
            <p class="text-sm text-gray-500">自定义的 MCP 工具配置</p>
          </div>
          <button
            @click="openCreateDialog('user')"
            class="flex items-center space-x-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            <span>添加工具</span>
          </button>
        </div>
        <ToolList
          :tools="userTools"
          :loading="loading"
          :is-admin="false"
          :testing-id="testingId"
          @test="handleTest"
          @edit="openEditDialog"
          @delete="confirmDelete"
        />
      </div>
    </main>

    <!-- 创建/编辑对话框 -->
    <MCPConfigDialog
      v-if="showDialog"
      :is-editing="isEditing"
      :is-platform="isPlatformEdit"
      :initial-data="editingTool"
      @close="closeDialog"
      @submit="handleSubmit"
    />

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/50" @click="showDeleteConfirm = false"></div>
      <div class="relative bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-2">确认删除</h3>
        <p class="text-gray-600 mb-6">确定要删除工具 "{{ deletingTool?.name }}" 吗？此操作不可恢复。</p>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import {
  getMCPTools,
  createMCPTool,
  updateMCPTool,
  deleteMCPTool,
  testMCPTool,
  createPlatformMCPTool,
  updatePlatformMCPTool,
  deletePlatformMCPTool
} from '@/api/mcp'
import ToolList from '@/components/mcp/ToolList.vue'
import MCPConfigDialog from '@/components/mcp/MCPConfigDialog.vue'

const router = useRouter()
const authStore = useAuthStore()

// 状态
const activeTab = ref('user')
const platformTools = ref([])
const userTools = ref([])
const loading = ref(false)
const testingId = ref(null)

const showDialog = ref(false)
const isEditing = ref(false)
const isPlatformEdit = ref(false)
const editingTool = ref(null)

const showDeleteConfirm = ref(false)
const deletingTool = ref(null)
const submitting = ref(false)

const isAdmin = computed(() => authStore.user?.is_superuser)

// 加载工具列表
const loadTools = async () => {
  loading.value = true
  try {
    const data = await getMCPTools()
    platformTools.value = data.platform_tools || []
    userTools.value = data.user_tools || []
  } catch (error) {
    console.error('Failed to load MCP tools:', error)
    ElMessage.error('加载工具列表失败')
  } finally {
    loading.value = false
  }
}

// 测试工具
const handleTest = async (tool) => {
  testingId.value = tool.id
  try {
    const result = await testMCPTool(tool.id)
    if (result.success) {
      ElMessage.success(`${tool.name}: 连接成功，发现 ${result.tools_count} 个工具`)
    } else {
      ElMessage.error(`${tool.name}: ${result.message}`)
    }
  } catch (error) {
    ElMessage.error(`${tool.name}: 测试失败`)
  } finally {
    testingId.value = null
  }
}

// 打开创建对话框
const openCreateDialog = (type) => {
  isEditing.value = false
  isPlatformEdit.value = type === 'platform'
  editingTool.value = null
  showDialog.value = true
}

// 打开编辑对话框
const openEditDialog = (tool) => {
  isEditing.value = true
  isPlatformEdit.value = tool.tool_type === 'platform'
  editingTool.value = tool
  showDialog.value = true
}

// 关闭对话框
const closeDialog = () => {
  showDialog.value = false
  editingTool.value = null
}

// 提交表单
const handleSubmit = async (formData) => {
  try {
    if (isEditing.value) {
      if (isPlatformEdit.value) {
        await updatePlatformMCPTool(editingTool.value.id, formData)
      } else {
        await updateMCPTool(editingTool.value.id, formData)
      }
      ElMessage.success('更新成功')
    } else {
      if (isPlatformEdit.value) {
        await createPlatformMCPTool(formData)
      } else {
        await createMCPTool(formData)
      }
      ElMessage.success('创建成功')
    }
    closeDialog()
    loadTools()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  }
}

// 确认删除
const confirmDelete = (tool) => {
  deletingTool.value = tool
  showDeleteConfirm.value = true
}

// 删除工具
const handleDelete = async () => {
  submitting.value = true
  try {
    if (deletingTool.value.tool_type === 'platform') {
      await deletePlatformMCPTool(deletingTool.value.id)
    } else {
      await deleteMCPTool(deletingTool.value.id)
    }
    ElMessage.success('删除成功')
    showDeleteConfirm.value = false
    deletingTool.value = null
    loadTools()
  } catch (error) {
    ElMessage.error('删除失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadTools()
})
</script>

<style scoped>
.glass-gemini {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}
</style>
