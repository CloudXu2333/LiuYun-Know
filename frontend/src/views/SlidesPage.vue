<template>
  <div class="h-screen w-full relative bg-gray-50 flex flex-col">
    <!-- 返回按钮 -->
    <button
      v-if="showBackButton"
      @click="router.push('/chat')"
      class="absolute top-4 right-4 z-50 bg-white/90 hover:bg-white text-gray-700 hover:text-blue-600 px-4 py-2 rounded-lg shadow-md border border-gray-200 transition-all duration-200 flex items-center space-x-2 backdrop-blur-sm"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
      </svg>
      <span class="font-medium">返回对话</span>
    </button>
    
    <!-- Iframe 容器 -->
    <div class="flex-1 w-full h-full">
      <iframe
        v-if="iframeUrl"
        :src="iframeUrl"
        class="w-full h-full border-none"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
      ></iframe>
      <div v-else class="flex flex-col items-center justify-center h-full text-gray-400">
        <svg class="w-12 h-12 mb-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        <p>正在加载 AI 幻灯片...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const iframeUrl = ref('')
const showBackButton = ref(true)

const handleMessage = (event) => {
  // 确保消息来源安全（可选：检查 origin）
  // if (event.origin !== 'http://localhost:5174') return
  
  const data = event.data
  if (data && data.type === 'ROUTE_CHANGE') {
    // 只有在 Banana-Slides 首页 ("/") 时才显示返回按钮
    // 允许 "/?uid=..." 这种带参数的情况
    const path = data.path
    showBackButton.value = path === '/'
  }
}

onMounted(() => {
  const userId = authStore.user?.id
  const isAdmin = authStore.user?.is_superuser

  // 动态获取当前访问的主机名和端口
  // 如果是通过 IP 访问的,iframe 也使用相同的 IP,避免跨域问题
  const hostname = window.location.hostname
  const protocol = window.location.protocol

  // Banana-Slides 前端端口固定为 5174
  // 注意：需要确保 Banana-Slides 服务已在 5174 端口启动
  // 通过 uid 参数传递用户 ID 实现隔离，is_admin 参数控制设置按钮显示
  const baseUrl = `${protocol}//${hostname}:5174`
  iframeUrl.value = userId
    ? `${baseUrl}?uid=${userId}&is_admin=${isAdmin}`
    : baseUrl

  // 监听 iframe 消息
  window.addEventListener('message', handleMessage)
})

onUnmounted(() => {
  window.removeEventListener('message', handleMessage)
})
</script>

<style scoped>
/* 确保 iframe 占满容器 */
iframe {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
