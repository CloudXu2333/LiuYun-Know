<template>
  <div class="min-h-screen h-screen bg-gemini-bg flex flex-col overflow-hidden font-sans">
    <!-- 顶部导航栏 -->
    <header class="glass-gemini border-b border-gemini-border sticky top-0 z-50">
      <div class="w-full px-4">
        <div class="flex justify-between items-center h-14">
          <!-- 左侧 -->
          <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-2 cursor-pointer" @click="router.push('/chat')">
              <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm">
                <span class="text-white text-xs font-bold">L</span>
              </div>
              <span class="text-lg font-semibold text-gemini-text-primary tracking-tight">LiuYun</span>
            </div>
          </div>

          <!-- 中间标题 -->
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"></path>
            </svg>
            <h1 class="text-base font-medium text-gemini-text-primary">AI 流程图生成器</h1>
          </div>

          <!-- 右侧 -->
          <div class="flex items-center space-x-3">
            <button
              @click="router.push('/chat')"
              class="flex items-center space-x-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
              </svg>
              <span>返回对话</span>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- 主要内容 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 左侧对话区域 -->
      <div class="w-96 bg-white border-r border-gray-200 flex flex-col">
        <!-- 对话历史 -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="chatContainer">
          <!-- 欢迎信息 -->
          <div v-if="messages.length === 0" class="text-center py-8">
            <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"></path>
              </svg>
            </div>
            <h2 class="text-lg font-semibold text-gray-800 mb-2">AI 流程图助手</h2>
            <p class="text-sm text-gray-500 mb-4">描述你想要的流程图，AI 会帮你生成</p>
            
            <!-- 示例 -->
            <div class="space-y-2">
              <p class="text-xs text-gray-400 mb-2">💡 试试这些示例</p>
              <button
                v-for="example in examples"
                :key="example"
                @click="inputMessage = example"
                class="block w-full text-left px-3 py-2 text-sm text-gray-600 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
              >
                {{ example }}
              </button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div v-for="(msg, idx) in messages" :key="idx" class="space-y-2">
            <!-- 用户消息 -->
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="max-w-[85%] bg-blue-500 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm">
                {{ msg.content }}
              </div>
            </div>
            <!-- AI 消息 -->
            <div v-else class="flex justify-start">
              <div class="max-w-[85%] bg-gray-100 text-gray-800 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm">
                {{ msg.content }}
              </div>
            </div>
          </div>

          <!-- 生成日志 -->
          <div v-if="logs.length > 0" class="bg-gray-900 rounded-xl p-3 text-xs font-mono">
            <div class="flex items-center gap-2 text-cyan-400 mb-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
              </svg>
              <span>生成日志</span>
            </div>
            <div v-for="(log, idx) in logs" :key="idx" :class="getLogClass(log.type)" class="py-0.5">
              {{ log.text }}
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="p-4 border-t border-gray-200">
          <div class="relative">
            <textarea
              v-model="inputMessage"
              @keydown.enter.exact.prevent="handleSend"
              placeholder="描述你想要的流程图..."
              class="w-full px-4 py-3 pr-12 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent text-sm"
              rows="3"
              :disabled="loading"
            ></textarea>
            <button
              @click="handleSend"
              :disabled="!inputMessage.trim() || loading"
              class="absolute right-2 bottom-2 p-2 rounded-lg transition-all"
              :class="inputMessage.trim() && !loading ? 'bg-purple-500 text-white hover:bg-purple-600' : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
            >
              <svg v-if="!loading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
              </svg>
              <svg v-else class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
            </button>
          </div>
          <div class="flex items-center justify-between mt-2">
            <button
              @click="clearAll"
              class="text-xs text-gray-500 hover:text-gray-700 transition-colors"
            >
              🗑️ 清空对话
            </button>
            <span class="text-xs text-gray-400">Ctrl+Enter 发送</span>
          </div>
        </div>
      </div>

      <!-- 右侧 Draw.io 预览 -->
      <div class="flex-1 bg-gray-50 p-4">
        <div class="h-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <iframe
            ref="drawioFrame"
            src="https://embed.diagrams.net/?embed=1&ui=atlas&spin=1&proto=json"
            class="w-full h-full border-0"
          ></iframe>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 状态
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const logs = ref([])
const drawioFrame = ref(null)
const chatContainer = ref(null)
const conversationHistory = ref([])

// 示例
const examples = [
  '用户登录流程',
  '电商订单处理流程',
  '请假审批流程',
  '软件开发生命周期'
]

// 获取日志样式
const getLogClass = (type) => {
  const classes = {
    step: 'text-cyan-400 font-semibold',
    node: 'text-green-400',
    edge: 'text-yellow-400',
    error: 'text-red-400',
    complete: 'text-green-300 font-semibold'
  }
  return classes[type] || 'text-gray-400'
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// 加载图表到 Draw.io
const loadDiagram = (xmlContent) => {
  if (drawioFrame.value) {
    drawioFrame.value.contentWindow.postMessage(JSON.stringify({
      action: 'load',
      xml: xmlContent,
      autosave: 0
    }), '*')
  }
}

// 清空
const clearAll = () => {
  messages.value = []
  logs.value = []
  conversationHistory.value = []
  const emptyXml = `<?xml version="1.0"?><mxfile><diagram><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel></diagram></mxfile>`
  loadDiagram(emptyXml)
}

// 发送消息
const handleSend = async () => {
  const content = inputMessage.value.trim()
  if (!content || loading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content })
  inputMessage.value = ''
  loading.value = true
  logs.value = []
  scrollToBottom()

  // 获取用户选择的 LLM 配置（与主对话页面一致），默认使用 DeepSeek
  let llmConfig = {
    model: 'deepseek-chat',
    api_key: null,
    base_url: 'https://api.deepseek.com',
    provider: 'deepseek'
  }
  try {
    const saved = localStorage.getItem('llm_config')
    if (saved) {
      const config = JSON.parse(saved)
      // 只有当用户明确选择了其他模型时才覆盖默认的 DeepSeek
      if (config.model && config.provider !== 'deepseek') {
        llmConfig.model = config.model
        llmConfig.api_key = config.apiKey
        llmConfig.base_url = config.baseUrl
        llmConfig.provider = config.provider
      }
    }
  } catch (e) {
    console.error('Failed to load LLM config:', e)
  }

  try {
    const response = await fetch('/api/diagram/generate-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        description: content,
        conversation_history: conversationHistory.value,
        model: llmConfig.model,
        api_key: llmConfig.api_key,
        base_url: llmConfig.base_url
      })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            handleStreamData(data)
          } catch (e) {}
        }
      }
    }

    // 更新对话历史
    conversationHistory.value.push({ role: 'user', content })

  } catch (error) {
    logs.value.push({ type: 'error', text: `错误: ${error.message}` })
    messages.value.push({ role: 'assistant', content: `生成失败: ${error.message}` })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 处理流式数据
const handleStreamData = (data) => {
  switch (data.type) {
    case 'step':
      logs.value.push({ type: 'step', text: `[步骤${data.step}] ${data.title}: ${data.content}` })
      break
    case 'node':
      logs.value.push({ type: 'node', text: `  + ${data.info}` })
      break
    case 'edge':
      logs.value.push({ type: 'edge', text: `  → ${data.info}` })
      break
    case 'error':
      logs.value.push({ type: 'error', text: `❌ ${data.content}` })
      messages.value.push({ role: 'assistant', content: `生成失败: ${data.content}` })
      break
    case 'message':
      // AI 的纯文本回复（没有调用工具）
      messages.value.push({ role: 'assistant', content: data.content })
      break
    case 'complete':
      logs.value.push({ type: 'complete', text: `✅ 完成！${data.nodes.length} 个节点，${data.edges.length} 条连接` })
      messages.value.push({ role: 'assistant', content: data.ai_response })
      conversationHistory.value.push({ role: 'assistant', content: data.ai_response })
      loadDiagram(data.xml)
      break
  }
  scrollToBottom()
}

// 监听 Draw.io 消息
onMounted(() => {
  window.addEventListener('message', (evt) => {
    if (evt.data && typeof evt.data === 'string') {
      try {
        const msg = JSON.parse(evt.data)
        if (msg.event === 'init') {
          console.log('Draw.io 已就绪')
        }
      } catch (e) {}
    }
  })
})
</script>

<style scoped>
.glass-gemini {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}
</style>
