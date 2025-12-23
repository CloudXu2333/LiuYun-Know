<template>
  <div class="min-h-screen bg-gemini-bg">
    <!-- 顶部导航 -->
    <header class="glass-gemini border-b border-gemini-border sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-14">
          <div class="flex items-center space-x-3">
            <router-link to="/" class="btn-gemini-icon">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
              </svg>
            </router-link>
            <div class="flex items-center space-x-2">
              <svg class="w-5 h-5 text-gemini-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
              </svg>
              <span class="font-medium text-gemini-text-primary">知识库</span>
            </div>
          </div>

          <button @click="handleLogout" class="btn-gemini-ghost text-sm">
            登出
          </button>
        </div>
      </div>
    </header>

    <!-- 主要内容 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 顶部操作栏 -->
      <div class="flex justify-between items-center mb-8">
        <div>
          <h1 class="text-3xl font-bold text-gemini-text-primary mb-2">我的知识库</h1>
          <p class="text-gemini-text-secondary">管理您的文档和知识库，构建智能知识体系</p>
        </div>
        <button
          @click="showCreateModal = true"
          class="btn-gemini-primary flex items-center space-x-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
          </svg>
          <span>创建知识库</span>
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="flex justify-center items-center py-20">
        <div class="loading-gemini w-8 h-8"></div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="knowledgeBases.length === 0" class="text-center py-20 animate-fade-in">
        <div class="w-20 h-20 rounded-gemini-2xl bg-gradient-to-br from-gemini-purple-500 to-gemini-purple-700 flex items-center justify-center mx-auto mb-6 shadow-gemini-lg">
          <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
          </svg>
        </div>
        <h3 class="text-2xl font-bold text-gemini-text-primary mb-3">还没有知识库</h3>
        <p class="text-gemini-text-secondary mb-8 max-w-md mx-auto">
          创建您的第一个知识库，上传文档，开始构建您的智能知识体系
        </p>
        <button
          @click="showCreateModal = true"
          class="btn-gemini-primary"
        >
          创建第一个知识库
        </button>
      </div>

      <!-- 知识库列表 -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="(kb, index) in knowledgeBases"
          :key="kb.id"
          @click="openKnowledgeBase(kb)"
          class="card-gemini p-6 cursor-pointer hover-lift group animate-slide-up"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <!-- 头部 -->
          <div class="flex items-start justify-between mb-4">
            <div class="w-12 h-12 rounded-gemini-xl bg-gradient-to-br from-gemini-purple-500 to-gemini-purple-700 flex items-center justify-center group-hover:scale-110 transition-transform shadow-gemini">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
              </svg>
            </div>
            <div class="relative" @click.stop>
              <button
                @click="toggleMenu(kb.id)"
                class="btn-gemini-icon"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path>
                </svg>
              </button>
              <!-- 下拉菜单 -->
              <div
                v-show="activeMenu === kb.id"
                class="dropdown-gemini right-0 w-40 py-1"
                :class="{ 'show': activeMenu === kb.id }"
              >
                <button
                  @click="editKnowledgeBase(kb)"
                  class="w-full px-4 py-2 text-left text-sm text-gemini-text-secondary hover:bg-gemini-bg transition-colors"
                >
                  编辑
                </button>
                <button
                  @click="confirmDelete(kb)"
                  class="w-full px-4 py-2 text-left text-sm text-gemini-red-600 hover:bg-gemini-red-50 transition-colors"
                >
                  删除
                </button>
              </div>
            </div>
          </div>

          <!-- 内容 -->
          <h3 class="text-lg font-bold text-gemini-text-primary mb-2 truncate">{{ kb.name }}</h3>
          <p class="text-sm text-gemini-text-secondary mb-4 truncate-2">
            {{ kb.description || '暂无描述' }}
          </p>

          <!-- 底部信息 -->
          <div class="flex items-center justify-between text-sm">
            <div class="flex items-center space-x-1 text-gemini-text-tertiary">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              <span>{{ kb.file_count || 0 }} 个文档</span>
            </div>
            <span class="badge-gemini">{{ kb.status }}</span>
          </div>
        </div>
      </div>
    </main>

    <!-- 创建/编辑知识库模态框 -->
    <div
      v-if="showCreateModal"
      class="modal-gemini"
      :class="{ 'show': showCreateModal }"
      @click.self="closeCreateModal"
    >
      <div class="modal-gemini-content max-w-lg">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-bold text-gemini-text-primary">
              {{ editingKb ? '编辑知识库' : '创建知识库' }}
            </h2>
            <button @click="closeCreateModal" class="btn-gemini-icon">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gemini-text-primary mb-2">
                知识库名称 <span class="text-gemini-red-500">*</span>
              </label>
              <input
                v-model="formData.name"
                type="text"
                class="input-gemini"
                placeholder="例如：技术文档库"
                required
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gemini-text-primary mb-2">
                描述
              </label>
              <textarea
                v-model="formData.description"
                class="input-gemini"
                rows="3"
                placeholder="简单描述这个知识库的用途..."
              ></textarea>
            </div>

            <div class="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                @click="closeCreateModal"
                class="btn-gemini-secondary"
              >
                取消
              </button>
              <button
                type="submit"
                class="btn-gemini-primary"
                :disabled="submitting"
              >
                <span v-if="submitting" class="flex items-center space-x-2">
                  <div class="loading-gemini w-4 h-4"></div>
                  <span>{{ editingKb ? '保存中...' : '创建中...' }}</span>
                </span>
                <span v-else>{{ editingKb ? '保存' : '创建' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  getKnowledgeBases,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
} from '@/api/knowledge'

const router = useRouter()
const authStore = useAuthStore()

// 状态
const loading = ref(false)
const knowledgeBases = ref([])
const showCreateModal = ref(false)
const submitting = ref(false)
const editingKb = ref(null)
const activeMenu = ref(null)

// 表单数据
const formData = ref({
  name: '',
  description: '',
})

// 计算属性
const userInitial = computed(() => authStore.user?.username?.charAt(0).toUpperCase() || 'U')

// 方法
const loadKnowledgeBases = async () => {
  loading.value = true
  try {
    const data = await getKnowledgeBases()
    console.log('Knowledge bases loaded:', data)
    knowledgeBases.value = data
  } catch (error) {
    console.error('Failed to load knowledge bases:', error)
    // 显示错误但不阻塞页面
    knowledgeBases.value = []
  } finally {
    loading.value = false
  }
}

const openKnowledgeBase = (kb) => {
  router.push(`/knowledge-base/${kb.id}`)
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    if (editingKb.value) {
      await updateKnowledgeBase(editingKb.value.id, formData.value)
    } else {
      await createKnowledgeBase(formData.value)
    }
    closeCreateModal()
    await loadKnowledgeBases()
  } catch (error) {
    console.error('Failed to save knowledge base:', error)
  } finally {
    submitting.value = false
  }
}

const editKnowledgeBase = (kb) => {
  editingKb.value = kb
  formData.value = {
    name: kb.name,
    description: kb.description || '',
  }
  showCreateModal.value = true
  activeMenu.value = null
}

const confirmDelete = async (kb) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库"${kb.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteKnowledgeBase(kb.id)
    await loadKnowledgeBases()
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete knowledge base:', error)
      ElMessage.error('删除失败')
    }
  }
  activeMenu.value = null
}

const closeCreateModal = () => {
  showCreateModal.value = false
  editingKb.value = null
  formData.value = { name: '', description: '' }
}

const toggleMenu = (id) => {
  activeMenu.value = activeMenu.value === id ? null : id
}

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}

// 点击外部关闭菜单
const handleClickOutside = (event) => {
  if (activeMenu.value) {
    activeMenu.value = null
  }
}

onMounted(() => {
  loadKnowledgeBases()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
