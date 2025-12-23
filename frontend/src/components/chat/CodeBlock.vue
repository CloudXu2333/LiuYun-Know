<template>
  <div class="code-block">
    <!-- 头部：语言标签 + 复制按钮 -->
    <div class="code-header">
      <span class="code-lang">{{ language || 'text' }}</span>
      <el-button 
        :icon="copied ? Check : DocumentCopy" 
        size="small" 
        text
        @click="copyCode"
        class="copy-btn"
      >
        {{ copied ? '已复制' : '复制' }}
      </el-button>
    </div>
    <!-- 代码内容区域 -->
    <el-scrollbar class="code-scrollbar" :max-height="maxHeight">
      <pre class="code-content"><code :class="`language-${language}`" v-html="highlightedCode"></code></pre>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { DocumentCopy, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import hljs from 'highlight.js'

const props = defineProps({
  code: {
    type: String,
    required: true
  },
  language: {
    type: String,
    default: 'text'
  },
  maxHeight: {
    type: [String, Number],
    default: 400
  }
})

const copied = ref(false)

const highlightedCode = computed(() => {
  if (props.language && hljs.getLanguage(props.language)) {
    try {
      return hljs.highlight(props.code, { language: props.language, ignoreIllegals: true }).value
    } catch (e) {
      return escapeHtml(props.code)
    }
  }
  return escapeHtml(props.code)
})

const escapeHtml = (text) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
    ElMessage.success('代码已复制到剪贴板')
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.code-block {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-light);
  background: #1e1e1e;
  margin: 12px 0;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #2d2d2d;
  border-bottom: 1px solid #3d3d3d;
}

.code-lang {
  font-size: 12px;
  color: #888;
  text-transform: uppercase;
  font-weight: 500;
}

.copy-btn {
  color: #888 !important;
}

.copy-btn:hover {
  color: #fff !important;
}

.code-scrollbar {
  background: #1e1e1e;
}

.code-content {
  margin: 0;
  padding: 16px;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
}

.code-content code {
  background: transparent;
  padding: 0;
  font-size: inherit;
  color: inherit;
}

/* 代码高亮主题 - VS Code Dark+ */
:deep(.hljs-keyword) { color: #569cd6; }
:deep(.hljs-string) { color: #ce9178; }
:deep(.hljs-number) { color: #b5cea8; }
:deep(.hljs-comment) { color: #6a9955; }
:deep(.hljs-function) { color: #dcdcaa; }
:deep(.hljs-class) { color: #4ec9b0; }
:deep(.hljs-variable) { color: #9cdcfe; }
:deep(.hljs-operator) { color: #d4d4d4; }
:deep(.hljs-punctuation) { color: #d4d4d4; }
:deep(.hljs-property) { color: #9cdcfe; }
:deep(.hljs-attr) { color: #9cdcfe; }
:deep(.hljs-tag) { color: #569cd6; }
:deep(.hljs-name) { color: #4ec9b0; }
:deep(.hljs-attribute) { color: #9cdcfe; }
:deep(.hljs-selector-tag) { color: #d7ba7d; }
:deep(.hljs-selector-class) { color: #d7ba7d; }
:deep(.hljs-selector-id) { color: #d7ba7d; }
:deep(.hljs-built_in) { color: #4ec9b0; }
:deep(.hljs-type) { color: #4ec9b0; }
:deep(.hljs-params) { color: #9cdcfe; }
:deep(.hljs-meta) { color: #569cd6; }
:deep(.hljs-title) { color: #dcdcaa; }
</style>
