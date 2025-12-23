<template>
  <div class="space-y-6">
    <!-- 查询输入 -->
    <div class="card-gemini p-6">
      <h3 class="text-lg font-bold text-gemini-text-primary mb-4">知识库查询测试</h3>
      
      <div class="space-y-4">
        <!-- 查询模式选择 -->
        <div>
          <label class="block text-sm font-medium text-gemini-text-primary mb-2">查询模式</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="mode in queryModes"
              :key="mode.value"
              @click="selectedMode = mode.value"
              class="px-4 py-2 text-sm rounded-gemini-lg transition-colors"
              :class="selectedMode === mode.value 
                ? 'bg-gemini-blue-600 text-white' 
                : 'bg-gemini-bg text-gemini-text-secondary hover:bg-gemini-border'"
            >
              {{ mode.label }}
            </button>
          </div>
          <p class="mt-2 text-xs text-gemini-text-tertiary">{{ getModeDescription(selectedMode) }}</p>
        </div>

        <!-- 查询输入框 -->
        <div>
          <label class="block text-sm font-medium text-gemini-text-primary mb-2">查询问题</label>
          <textarea
            v-model="queryText"
            class="input-gemini"
            rows="3"
            placeholder="输入您想查询的问题..."
            @keydown.ctrl.enter="submitQuery"
          ></textarea>
        </div>

        <!-- 提交按钮 -->
        <div class="flex justify-end">
          <button
            @click="submitQuery"
            :disabled="!queryText.trim() || querying"
            class="btn-gemini-primary"
            :class="{ 'opacity-50 cursor-not-allowed': !queryText.trim() || querying }"
          >
            <span v-if="querying" class="flex items-center space-x-2">
              <div class="loading-gemini w-4 h-4 border-white border-t-transparent"></div>
              <span>查询中...</span>
            </span>
            <span v-else>发送查询</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 查询结果 -->
    <div v-if="queryResult || queryError" class="card-gemini p-6">
      <h3 class="text-lg font-bold text-gemini-text-primary mb-4">查询结果</h3>
      
      <!-- 错误状态 -->
      <div v-if="queryError" class="p-4 bg-gemini-red-50 rounded-gemini-lg">
        <div class="flex items-start space-x-3">
          <svg class="w-5 h-5 text-gemini-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <div>
            <p class="font-medium text-gemini-red-700">查询失败</p>
            <p class="text-sm text-gemini-red-600 mt-1">{{ queryError }}</p>
          </div>
        </div>
      </div>

      <!-- 成功结果 -->
      <div v-else-if="queryResult" class="space-y-4">
        <div class="flex items-center space-x-2 text-sm text-gemini-text-tertiary">
          <span class="badge-gemini">{{ queryResult.mode }}</span>
          <span>•</span>
          <span>查询: {{ queryResult.query }}</span>
        </div>
        
        <div class="p-4 bg-gemini-bg rounded-gemini-lg">
          <div class="prose prose-sm max-w-none text-gemini-text-primary markdown-gemini" v-html="formatAnswer(queryResult.answer)"></div>
        </div>
      </div>
    </div>

    <!-- 历史查询 -->
    <div v-if="queryHistory.length > 0" class="card-gemini p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-gemini-text-primary">历史查询</h3>
        <button @click="clearHistory" class="text-sm text-gemini-text-tertiary hover:text-gemini-text-primary">
          清空历史
        </button>
      </div>
      
      <div class="space-y-3">
        <div
          v-for="(item, index) in queryHistory"
          :key="index"
          @click="loadHistoryQuery(item)"
          class="p-3 bg-gemini-bg rounded-gemini-lg cursor-pointer hover:bg-gemini-border transition-colors"
        >
          <div class="flex items-center justify-between mb-1">
            <span class="badge-gemini text-xs">{{ item.mode }}</span>
            <span class="text-xs text-gemini-text-tertiary">{{ formatTime(item.timestamp) }}</span>
          </div>
          <p class="text-sm text-gemini-text-primary truncate">{{ item.query }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { queryKnowledgeBase } from '@/api/knowledge'
import { marked } from 'marked'

const props = defineProps({
  knowledgeBaseId: {
    type: Number,
    required: true
  }
})

const queryText = ref('')
const selectedMode = ref('mix')
const querying = ref(false)
const queryResult = ref(null)
const queryError = ref(null)
const queryHistory = ref([])

const queryModes = [
  { value: 'naive', label: 'Naive' },
  { value: 'local', label: 'Local' },
  { value: 'global', label: 'Global' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'mix', label: 'Mix' },
]

const getModeDescription = (mode) => {
  const descriptions = {
    naive: '简单检索模式，直接匹配相关文档片段',
    local: '局部检索模式，关注实体的直接关系',
    global: '全局检索模式，考虑整体知识图谱结构',
    hybrid: '混合检索模式，结合局部和全局信息',
    mix: '综合检索模式，自动选择最佳策略',
  }
  return descriptions[mode] || ''
}

const submitQuery = async () => {
  if (!queryText.value.trim() || querying.value) return
  
  querying.value = true
  queryError.value = null
  queryResult.value = null
  
  try {
    const result = await queryKnowledgeBase(props.knowledgeBaseId, {
      query: queryText.value,
      mode: selectedMode.value,
      top_k: 5
    })
    
    queryResult.value = result
    
    // 添加到历史
    queryHistory.value.unshift({
      query: queryText.value,
      mode: selectedMode.value,
      timestamp: Date.now()
    })
    
    // 限制历史数量
    if (queryHistory.value.length > 10) {
      queryHistory.value = queryHistory.value.slice(0, 10)
    }
  } catch (err) {
    console.error('Query failed:', err)
    queryError.value = err.response?.data?.detail || '查询失败，请稍后重试'
  } finally {
    querying.value = false
  }
}

const formatAnswer = (answer) => {
  if (!answer) return ''
  return marked(answer)
}

const loadHistoryQuery = (item) => {
  queryText.value = item.query
  selectedMode.value = item.mode
}

const clearHistory = () => {
  queryHistory.value = []
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>
