<template>
  <div class="min-h-screen bg-gemini-bg">
    <!-- 顶部导航 -->
    <header class="glass-gemini border-b border-gemini-border sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-14">
          <div class="flex items-center space-x-3">
            <button @click="goBack" class="btn-gemini-icon">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
              </svg>
            </button>
            <div class="flex items-center space-x-2">
              <div class="w-8 h-8 rounded-gemini-lg bg-gradient-to-br from-gemini-purple-500 to-gemini-purple-700 flex items-center justify-center">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                </svg>
              </div>
              <span class="font-medium text-gemini-text-primary truncate max-w-xs">
                {{ knowledgeBase?.name || '加载中...' }}
              </span>
              <span v-if="knowledgeBase" class="badge-gemini">{{ knowledgeBase.status }}</span>
            </div>
          </div>
          <button @click="refreshData" class="btn-gemini-icon" :disabled="loading">
            <svg class="w-5 h-5" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- 加载状态 -->
    <div v-if="loading && !knowledgeBase" class="flex justify-center items-center py-20">
      <div class="loading-gemini w-8 h-8"></div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
      <div class="text-center">
        <div class="w-16 h-16 rounded-full bg-gemini-red-100 flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-gemini-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gemini-text-primary mb-2">{{ error }}</h3>
        <router-link to="/knowledge" class="btn-gemini-primary mt-4 inline-block">
          返回知识库列表
        </router-link>
      </div>
    </div>

    <!-- 主内容 -->
    <main v-else class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <!-- 知识库信息头部 -->
      <div class="card-gemini p-6 mb-6">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <h1 class="text-2xl font-bold text-gemini-text-primary mb-2">{{ knowledgeBase?.name }}</h1>
            <p class="text-gemini-text-secondary mb-4">{{ knowledgeBase?.description || '暂无描述' }}</p>
            <div class="flex items-center space-x-4 text-sm text-gemini-text-tertiary">
              <span class="flex items-center space-x-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
                <span>创建于 {{ formatDate(knowledgeBase?.created_at) }}</span>
              </span>
              <span class="flex items-center space-x-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <span>{{ knowledgeBase?.file_count || 0 }} 个文件</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 标签页导航 -->
      <div class="flex space-x-1 mb-6 border-b border-gemini-border">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-4 py-3 text-sm font-medium transition-colors relative"
          :class="activeTab === tab.id 
            ? 'text-gemini-blue-600' 
            : 'text-gemini-text-secondary hover:text-gemini-text-primary'"
        >
          {{ tab.name }}
          <div
            v-if="activeTab === tab.id"
            class="absolute bottom-0 left-0 right-0 h-0.5 bg-gemini-blue-600"
          ></div>
        </button>
      </div>

      <!-- 标签页内容 -->
      <div class="animate-fade-in">
        <!-- 概览 -->
        <StatisticsPanel 
          v-if="activeTab === 'overview'" 
          :knowledge-base-id="kbId"
          :key="'stats-' + refreshKey"
        />

        <!-- 文件管理 -->
        <FileListPanel 
          v-else-if="activeTab === 'files'" 
          :knowledge-base-id="kbId"
          :key="'files-' + refreshKey"
        />

        <!-- 分片信息 -->
        <ChunkViewerPanel 
          v-else-if="activeTab === 'chunks'" 
          :knowledge-base-id="kbId"
          :key="'chunks-' + refreshKey"
        />

        <!-- 知识图谱 -->
        <KnowledgeGraphPanel 
          v-else-if="activeTab === 'graph'" 
          :knowledge-base-id="kbId"
          :key="'graph-' + refreshKey"
        />

        <!-- 查询测试 -->
        <QueryTestPanel 
          v-else-if="activeTab === 'query'" 
          :knowledge-base-id="kbId"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getKnowledgeBase } from '@/api/knowledge'
import StatisticsPanel from '@/components/knowledge/StatisticsPanel.vue'
import FileListPanel from '@/components/knowledge/FileListPanel.vue'
import ChunkViewerPanel from '@/components/knowledge/ChunkViewerPanel.vue'
import KnowledgeGraphPanel from '@/components/knowledge/KnowledgeGraphPanel.vue'
import QueryTestPanel from '@/components/knowledge/QueryTestPanel.vue'

const route = useRoute()
const router = useRouter()

// 状态
const knowledgeBase = ref(null)
const loading = ref(false)
const error = ref(null)
const activeTab = ref('overview')
const refreshKey = ref(0)

// 计算属性
const kbId = computed(() => parseInt(route.params.id))

// 标签页配置
const tabs = [
  { id: 'overview', name: '概览' },
  { id: 'files', name: '文件管理' },
  { id: 'chunks', name: '分片信息' },
  { id: 'graph', name: '知识图谱' },
  { id: 'query', name: '查询测试' },
]

// 方法
const loadKnowledgeBase = async () => {
  loading.value = true
  error.value = null
  try {
    knowledgeBase.value = await getKnowledgeBase(kbId.value)
  } catch (err) {
    console.error('Failed to load knowledge base:', err)
    if (err.response?.status === 404) {
      error.value = '知识库不存在'
    } else if (err.response?.status === 403) {
      error.value = '无权访问此知识库'
    } else {
      error.value = '加载失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  refreshKey.value++
  loadKnowledgeBase()
}

const goBack = () => {
  router.push('/knowledge')
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

onMounted(() => {
  loadKnowledgeBase()
})
</script>
