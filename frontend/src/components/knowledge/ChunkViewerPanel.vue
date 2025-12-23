<template>
  <div class="space-y-6">
    <!-- 搜索和统计 -->
    <div class="flex items-center justify-between">
      <div class="relative flex-1 max-w-md">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索分片内容..."
          class="input-gemini pl-10"
          @input="debouncedSearch"
        />
        <svg class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gemini-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
        </svg>
      </div>
      <div class="text-sm text-gemini-text-tertiary">
        共 {{ total }} 个分片
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="loading-gemini w-6 h-6"></div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="chunks.length === 0" class="text-center py-12 text-gemini-text-tertiary">
      {{ searchQuery ? '没有找到匹配的分片' : '暂无分片数据' }}
    </div>

    <!-- 分片列表 -->
    <div v-else class="space-y-4">
      <div
        v-for="(chunk, index) in chunks"
        :key="chunk.id"
        class="card-gemini overflow-hidden"
      >
        <!-- 分片头部 -->
        <div
          @click="toggleChunk(chunk.id)"
          class="p-4 flex items-center justify-between cursor-pointer hover:bg-gemini-bg transition-colors"
        >
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 rounded-gemini-lg bg-gemini-purple-100 flex items-center justify-center text-sm font-medium text-gemini-purple-600">
              {{ (skip + index + 1) }}
            </div>
            <div>
              <p class="text-sm font-medium text-gemini-text-primary">
                分片 #{{ chunk.chunk_order_index + 1 }}
              </p>
              <p class="text-xs text-gemini-text-tertiary">
                {{ chunk.tokens }} tokens
              </p>
            </div>
          </div>
          <svg
            class="w-5 h-5 text-gemini-text-tertiary transition-transform"
            :class="{ 'rotate-180': expandedChunks.includes(chunk.id) }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
          </svg>
        </div>

        <!-- 分片内容 -->
        <div
          v-show="expandedChunks.includes(chunk.id)"
          class="px-4 pb-4 border-t border-gemini-border"
        >
          <div class="mt-4 p-4 bg-gemini-bg rounded-gemini-lg">
            <pre class="text-sm text-gemini-text-primary whitespace-pre-wrap font-mono">{{ chunk.content }}</pre>
          </div>
          <div class="mt-3 flex items-center space-x-4 text-xs text-gemini-text-tertiary">
            <span>文档ID: {{ chunk.full_doc_id?.slice(0, 16) }}...</span>
            <span>创建时间: {{ formatTimestamp(chunk.create_time) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > limit" class="flex items-center justify-center space-x-2">
      <button
        @click="prevPage"
        :disabled="skip === 0"
        class="btn-gemini-secondary text-sm"
        :class="{ 'opacity-50 cursor-not-allowed': skip === 0 }"
      >
        上一页
      </button>
      <span class="text-sm text-gemini-text-tertiary">
        {{ Math.floor(skip / limit) + 1 }} / {{ Math.ceil(total / limit) }}
      </span>
      <button
        @click="nextPage"
        :disabled="skip + limit >= total"
        class="btn-gemini-secondary text-sm"
        :class="{ 'opacity-50 cursor-not-allowed': skip + limit >= total }"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { getChunks } from '@/api/knowledge'

const props = defineProps({
  knowledgeBaseId: {
    type: Number,
    required: true
  }
})

const chunks = ref([])
const loading = ref(false)
const searchQuery = ref('')
const expandedChunks = ref([])
const skip = ref(0)
const limit = ref(20)
const total = ref(0)

let searchTimeout = null

const loadChunks = async () => {
  loading.value = true
  try {
    const result = await getChunks(props.knowledgeBaseId, {
      skip: skip.value,
      limit: limit.value,
      search: searchQuery.value || undefined
    })
    chunks.value = result.items
    total.value = result.total
  } catch (err) {
    console.error('Failed to load chunks:', err)
  } finally {
    loading.value = false
  }
}

const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    skip.value = 0
    loadChunks()
  }, 300)
}

const toggleChunk = (id) => {
  const idx = expandedChunks.value.indexOf(id)
  if (idx > -1) expandedChunks.value.splice(idx, 1)
  else expandedChunks.value.push(id)
}

const prevPage = () => {
  if (skip.value > 0) {
    skip.value = Math.max(0, skip.value - limit.value)
    loadChunks()
  }
}

const nextPage = () => {
  if (skip.value + limit.value < total.value) {
    skip.value += limit.value
    loadChunks()
  }
}

const formatTimestamp = (ts) => {
  if (!ts) return ''
  const date = new Date(ts * 1000)
  return date.toLocaleString('zh-CN')
}

watch(() => props.knowledgeBaseId, () => {
  skip.value = 0
  loadChunks()
})

onMounted(loadChunks)
</script>
