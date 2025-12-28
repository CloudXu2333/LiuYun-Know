<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
    <div v-if="loading" class="p-12 text-center">
      <svg class="animate-spin h-8 w-8 mx-auto text-blue-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>
    
    <div v-else-if="tools.length === 0" class="p-12 text-center text-gray-500">
      <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
      </svg>
      <p>暂无工具配置</p>
    </div>
    
    <div v-else class="divide-y divide-gray-100">
      <div
        v-for="tool in tools"
        :key="tool.id"
        class="p-4 hover:bg-gray-50 transition-colors"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <div class="flex items-center space-x-2">
              <span class="text-lg">🔧</span>
              <h3 class="text-sm font-medium text-gray-900 truncate">{{ tool.name }}</h3>
              <span
                :class="tool.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
                class="px-2 py-0.5 text-xs rounded-full"
              >
                {{ tool.enabled ? '已启用' : '已禁用' }}
              </span>
            </div>
            <p v-if="tool.description" class="mt-1 text-sm text-gray-500 line-clamp-2">
              {{ tool.description }}
            </p>
            <div class="mt-2 flex items-center space-x-4 text-xs text-gray-400">
              <span class="flex items-center space-x-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
                <code class="bg-gray-100 px-1 rounded">{{ tool.config.command }}</code>
              </span>
              <span v-if="tool.config.args?.length">
                {{ tool.config.args.length }} 个参数
              </span>
            </div>
          </div>
          
          <div class="flex items-center space-x-2 ml-4">
            <button
              @click="$emit('test', tool)"
              :disabled="testingId === tool.id"
              class="px-3 py-1.5 text-xs text-green-600 hover:text-green-700 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
            >
              {{ testingId === tool.id ? '测试中...' : '测试' }}
            </button>
            <button
              v-if="canEdit(tool)"
              @click="$emit('edit', tool)"
              class="px-3 py-1.5 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
            >
              编辑
            </button>
            <button
              v-if="canEdit(tool)"
              @click="$emit('delete', tool)"
              class="px-3 py-1.5 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  tools: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  isAdmin: {
    type: Boolean,
    default: false
  },
  testingId: {
    type: String,
    default: null
  }
})

defineEmits(['test', 'edit', 'delete'])

const canEdit = (tool) => {
  // 用户工具可以编辑，平台工具需要管理员权限
  return tool.tool_type === 'user' || props.isAdmin
}
</script>
