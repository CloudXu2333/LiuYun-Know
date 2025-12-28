<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center">
    <div class="absolute inset-0 bg-black/50" @click="$emit('close')"></div>
    <div class="relative bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">
        {{ isEditing ? '编辑 MCP 工具' : '添加 MCP 工具' }}
        <span v-if="isPlatform" class="text-sm font-normal text-blue-500 ml-2">(平台工具)</span>
      </h3>
      
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- 基本信息 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">工具名称 *</label>
          <input
            v-model="formData.name"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="如：文件系统工具"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
          <textarea
            v-model="formData.description"
            rows="2"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="工具的功能描述"
          ></textarea>
        </div>
        
        <!-- stdio JSON 配置 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">stdio 配置 (JSON) *</label>
          <textarea
            v-model="jsonConfig"
            rows="8"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 font-mono text-sm"
            placeholder='{
  "command": "npx",
  "args": ["-y", "@anthropic/mcp-server-xxx"],
  "env": {
    "API_KEY": "your-key"
  }
}'
          ></textarea>
          <p v-if="jsonError" class="text-xs text-red-500 mt-1">{{ jsonError }}</p>
          <p class="text-xs text-gray-400 mt-1">格式: {"command": "...", "args": [...], "env": {...}}</p>
        </div>
        
        <!-- 启用状态 -->
        <div class="flex items-center">
          <input
            v-model="formData.enabled"
            type="checkbox"
            id="enabled"
            class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label for="enabled" class="ml-2 text-sm text-gray-700">启用此工具</label>
        </div>
        
        <!-- 测试结果 -->
        <div v-if="testResult" class="p-3 rounded-lg text-sm" :class="testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
          <p>{{ testResult.message }}</p>
          <div v-if="testResult.tools?.length" class="mt-2">
            <p class="font-medium">发现的工具：</p>
            <ul class="mt-1 space-y-1">
              <li v-for="tool in testResult.tools" :key="tool.name" class="text-xs">
                • {{ tool.name }}: {{ tool.description || '无描述' }}
              </li>
            </ul>
          </div>
        </div>
        
        <!-- 按钮 -->
        <div class="flex justify-end space-x-3 pt-4 border-t">
          <button
            type="button"
            @click="handleTest"
            :disabled="testing || !jsonConfig"
            class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors disabled:opacity-50"
          >
            {{ testing ? '测试中...' : '测试连接' }}
          </button>
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors"
          >
            取消
          </button>
          <button
            type="submit"
            :disabled="submitting || !!jsonError"
            class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
          >
            {{ submitting ? '提交中...' : '确定' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { testMCPConfig } from '@/api/mcp'

const props = defineProps({
  isEditing: {
    type: Boolean,
    default: false
  },
  isPlatform: {
    type: Boolean,
    default: false
  },
  initialData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'submit'])

// 表单数据
const formData = ref({
  name: '',
  description: '',
  enabled: true
})

// JSON 配置
const jsonConfig = ref('')
const jsonError = ref('')

// 初始化
if (props.initialData) {
  formData.value = {
    name: props.initialData.name,
    description: props.initialData.description || '',
    enabled: props.initialData.enabled
  }
  jsonConfig.value = JSON.stringify(props.initialData.config, null, 2)
} else {
  // 默认模板
  jsonConfig.value = `{
  "command": "npx",
  "args": [],
  "env": {}
}`
}

// 验证 JSON
watch(jsonConfig, (val) => {
  try {
    const parsed = JSON.parse(val)
    if (!parsed.command) {
      jsonError.value = '缺少 command 字段'
    } else {
      jsonError.value = ''
    }
  } catch (e) {
    jsonError.value = 'JSON 格式错误'
  }
})

// 测试
const testing = ref(false)
const testResult = ref(null)

const handleTest = async () => {
  if (jsonError.value) return
  
  testing.value = true
  testResult.value = null
  
  try {
    const config = JSON.parse(jsonConfig.value)
    const result = await testMCPConfig(config)
    testResult.value = result
  } catch (error) {
    testResult.value = {
      success: false,
      message: error.message || '测试失败'
    }
  } finally {
    testing.value = false
  }
}

// 提交
const submitting = ref(false)

const handleSubmit = () => {
  if (jsonError.value) return
  
  try {
    const config = JSON.parse(jsonConfig.value)
    submitting.value = true
    emit('submit', {
      name: formData.value.name,
      description: formData.value.description || null,
      config: config,
      enabled: formData.value.enabled
    })
  } catch (e) {
    jsonError.value = 'JSON 格式错误'
  }
  submitting.value = false
}
</script>
