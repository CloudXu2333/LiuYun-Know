<template>
  <div class="space-y-6">
    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="loading-gemini w-6 h-6"></div>
    </div>

    <!-- 统计卡片 -->
    <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <!-- 文件统计 -->
      <div class="card-gemini p-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-gemini-lg bg-gemini-blue-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-gemini-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-gemini-text-primary">{{ stats.total_files }}</p>
            <p class="text-sm text-gemini-text-tertiary">文件总数</p>
          </div>
        </div>
      </div>

      <!-- 分片统计 -->
      <div class="card-gemini p-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-gemini-lg bg-gemini-purple-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-gemini-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-gemini-text-primary">{{ stats.total_chunks }}</p>
            <p class="text-sm text-gemini-text-tertiary">分片总数</p>
          </div>
        </div>
      </div>

      <!-- 实体统计 -->
      <div class="card-gemini p-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-gemini-lg bg-gemini-green-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-gemini-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-gemini-text-primary">{{ stats.total_entities }}</p>
            <p class="text-sm text-gemini-text-tertiary">实体总数</p>
          </div>
        </div>
      </div>

      <!-- 关系统计 -->
      <div class="card-gemini p-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-gemini-lg bg-gemini-yellow-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-gemini-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-gemini-text-primary">{{ stats.total_relations }}</p>
            <p class="text-sm text-gemini-text-tertiary">关系总数</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 文件状态详情 -->
    <div v-if="!loading" class="card-gemini p-6">
      <h3 class="text-lg font-bold text-gemini-text-primary mb-4">文件处理状态</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 rounded-full bg-gemini-green-500"></div>
          <span class="text-sm text-gemini-text-secondary">已完成: {{ stats.completed_files }}</span>
        </div>
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 rounded-full bg-gemini-blue-500"></div>
          <span class="text-sm text-gemini-text-secondary">处理中: {{ stats.processing_files }}</span>
        </div>
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 rounded-full bg-gemini-yellow-500"></div>
          <span class="text-sm text-gemini-text-secondary">等待中: {{ stats.pending_files }}</span>
        </div>
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 rounded-full bg-gemini-red-500"></div>
          <span class="text-sm text-gemini-text-secondary">失败: {{ stats.failed_files }}</span>
        </div>
      </div>

      <!-- Token统计 -->
      <div class="mt-4 pt-4 border-t border-gemini-border">
        <div class="flex items-center space-x-2">
          <svg class="w-4 h-4 text-gemini-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
          </svg>
          <span class="text-sm text-gemini-text-secondary">Token 总数: {{ formatNumber(stats.total_tokens) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { getKnowledgeBaseStats } from '@/api/knowledge'

const props = defineProps({
  knowledgeBaseId: {
    type: Number,
    required: true
  }
})

const loading = ref(false)
const stats = ref({
  total_files: 0,
  completed_files: 0,
  processing_files: 0,
  failed_files: 0,
  pending_files: 0,
  total_chunks: 0,
  total_entities: 0,
  total_relations: 0,
  total_tokens: 0
})

const loadStats = async () => {
  loading.value = true
  try {
    stats.value = await getKnowledgeBaseStats(props.knowledgeBaseId)
  } catch (err) {
    console.error('Failed to load stats:', err)
  } finally {
    loading.value = false
  }
}

const formatNumber = (num) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

watch(() => props.knowledgeBaseId, loadStats)
onMounted(loadStats)
</script>
