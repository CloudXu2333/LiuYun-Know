<template>
  <div class="space-y-6">
    <!-- 上传区域 -->
    <div
      @click="triggerFileInput"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
      class="border-2 border-dashed rounded-gemini-xl p-8 text-center cursor-pointer transition-all duration-200"
      :class="isDragging ? 'border-gemini-blue-500 bg-gemini-blue-50' : 'border-gemini-border hover:border-gemini-blue-400 hover:bg-gemini-bg'"
    >
      <svg class="w-12 h-12 mx-auto mb-4 text-gemini-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
      </svg>
      <p class="text-gemini-text-primary font-medium mb-1">点击上传或拖拽文件到这里</p>
      <p class="text-sm text-gemini-text-tertiary">支持 PDF、Word、Excel、CSV、TXT、MD 格式</p>
      <input ref="fileInput" type="file" class="hidden" accept=".pdf,.txt,.md,.doc,.docx,.csv,.xlsx,.xls" multiple @change="handleFileSelect" />
    </div>

    <!-- 上传进度 -->
    <div v-if="uploadingFiles.length > 0" class="space-y-3">
      <div class="text-sm font-medium text-gemini-text-secondary mb-2">
        正在上传 {{ uploadingFiles.length }} 个文件
      </div>
      <div v-for="file in uploadingFiles" :key="file.id" class="card-gemini p-4">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center space-x-2 flex-1 min-w-0">
            <span :class="getUploadStatusIcon(file.status)" class="w-5 h-5 flex-shrink-0">
              <svg v-if="file.status === 'uploading'" class="animate-spin w-5 h-5 text-gemini-blue-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else-if="file.status === 'success'" class="w-5 h-5 text-gemini-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <svg v-else-if="file.status === 'error'" class="w-5 h-5 text-gemini-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
              <svg v-else class="w-5 h-5 text-gemini-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </span>
            <span class="text-sm font-medium text-gemini-text-primary truncate">{{ file.name }}</span>
          </div>
          <span class="text-sm text-gemini-text-tertiary ml-2">
            <template v-if="file.status === 'uploading'">{{ file.progress }}%</template>
            <template v-else-if="file.status === 'success'">已完成</template>
            <template v-else-if="file.status === 'error'">失败</template>
            <template v-else>等待中</template>
          </span>
        </div>
        <div class="w-full bg-gemini-bg rounded-full h-2">
          <div 
            class="h-full rounded-full transition-all" 
            :class="file.status === 'error' ? 'bg-gemini-red-500' : file.status === 'success' ? 'bg-gemini-green-500' : 'bg-gradient-gemini'"
            :style="{ width: `${file.progress}%` }"
          ></div>
        </div>
        <div v-if="file.error" class="mt-1 text-xs text-gemini-red-500">{{ file.error }}</div>
      </div>
    </div>

    <!-- 搜索和批量操作 -->
    <div class="flex items-center justify-between">
      <div class="relative flex-1 max-w-md">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索文件..."
          class="input-gemini pl-10"
        />
        <svg class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gemini-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
        </svg>
      </div>
      <div class="flex items-center space-x-2">
        <!-- 刷新按钮 -->
        <button
          @click="loadFiles"
          :disabled="loading"
          class="btn-gemini-icon"
          title="刷新文件列表"
        >
          <svg 
            class="w-5 h-5" 
            :class="{ 'animate-spin': loading }"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
        </button>
        <button
          v-if="selectedFiles.length > 0"
          @click="batchDelete"
          class="btn-gemini-secondary text-gemini-red-600 text-sm"
        >
          删除选中 ({{ selectedFiles.length }})
        </button>
      </div>
    </div>

    <!-- 文件列表 -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="loading-gemini w-6 h-6"></div>
    </div>

    <div v-else-if="filteredFiles.length === 0" class="text-center py-12 text-gemini-text-tertiary">
      {{ searchQuery ? '没有找到匹配的文件' : '还没有上传文件' }}
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="file in filteredFiles"
        :key="file.id"
        class="card-gemini p-4 flex items-center justify-between hover:shadow-gemini-hover transition-all"
      >
        <div class="flex items-center space-x-3 flex-1 min-w-0">
          <input
            type="checkbox"
            :checked="selectedFiles.includes(file.id)"
            @change="toggleSelect(file.id)"
            class="w-4 h-4 rounded border-gemini-border text-gemini-blue-600 focus:ring-gemini-blue-500"
          />
          <div :class="getFileIconClass(file.file_type)" class="w-10 h-10 rounded-gemini-lg flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gemini-text-primary truncate">{{ file.original_filename }}</p>
            <p class="text-xs text-gemini-text-tertiary">
              {{ formatFileSize(file.file_size) }} • {{ file.file_type.toUpperCase() }} • {{ formatDate(file.created_at) }}
            </p>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <span :class="getStatusClass(file.status)" class="text-xs px-2 py-1 rounded-full">
            {{ getStatusText(file.status) }}
          </span>
          <button v-if="file.status === 'failed'" @click="retryFile(file)" class="btn-gemini-icon text-gemini-blue-600" title="重试">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
          </button>
          <button @click="previewFile(file)" class="btn-gemini-icon" title="预览">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
            </svg>
          </button>
          <button @click="confirmDelete(file)" class="btn-gemini-icon text-gemini-red-600" title="删除">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  getKnowledgeBaseFiles,
  uploadFile,
  deleteFile,
  retryFileProcessing,
  getFilePreviewUrl,
  batchDeleteFiles
} from '@/api/knowledge'

const props = defineProps({
  knowledgeBaseId: {
    type: Number,
    required: true
  }
})

const files = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedFiles = ref([])
const isDragging = ref(false)
const uploadingFiles = ref([])
const fileInput = ref(null)

const filteredFiles = computed(() => {
  if (!searchQuery.value) return files.value
  const query = searchQuery.value.toLowerCase()
  return files.value.filter(f => f.original_filename.toLowerCase().includes(query))
})

const loadFiles = async () => {
  loading.value = true
  try {
    files.value = await getKnowledgeBaseFiles(props.knowledgeBaseId)
  } catch (err) {
    console.error('Failed to load files:', err)
  } finally {
    loading.value = false
  }
}

const triggerFileInput = () => fileInput.value?.click()

const handleFileSelect = (e) => {
  const selectedFiles = Array.from(e.target.files)
  uploadFiles(selectedFiles)
  e.target.value = ''
}

const handleDrop = (e) => {
  isDragging.value = false
  const droppedFiles = Array.from(e.dataTransfer.files)
  uploadFiles(droppedFiles)
}

const uploadFiles = async (fileList) => {
  // 为每个文件创建上传状态
  const newUploadingFiles = fileList.map(file => ({
    id: Date.now() + Math.random(),
    name: file.name,
    progress: 0,
    status: 'pending', // pending, uploading, success, error
    error: null,
    file: file
  }))
  
  uploadingFiles.value.push(...newUploadingFiles)
  
  // 并行上传所有文件
  const uploadPromises = newUploadingFiles.map(async (uploadingFile) => {
    uploadingFile.status = 'uploading'
    try {
      await uploadFile(props.knowledgeBaseId, uploadingFile.file, (progress) => {
        uploadingFile.progress = progress
      })
      uploadingFile.status = 'success'
      uploadingFile.progress = 100
      
      // 成功后 2 秒移除
      setTimeout(() => {
        uploadingFiles.value = uploadingFiles.value.filter(f => f.id !== uploadingFile.id)
      }, 2000)
    } catch (err) {
      console.error('Upload failed:', err)
      uploadingFile.status = 'error'
      uploadingFile.error = err.response?.data?.detail || '上传失败'
      
      // 失败后 5 秒移除
      setTimeout(() => {
        uploadingFiles.value = uploadingFiles.value.filter(f => f.id !== uploadingFile.id)
      }, 5000)
    }
  })
  
  // 等待所有上传完成后刷新文件列表
  await Promise.allSettled(uploadPromises)
  loadFiles()
}

const getUploadStatusIcon = (status) => {
  return '' // 图标在模板中直接处理
}

const toggleSelect = (id) => {
  const idx = selectedFiles.value.indexOf(id)
  if (idx > -1) selectedFiles.value.splice(idx, 1)
  else selectedFiles.value.push(id)
}

const confirmDelete = async (file) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件"${file.original_filename}"吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteFile(props.knowledgeBaseId, file.id)
    ElMessage.success('删除成功')
    loadFiles()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('Delete failed:', err)
      ElMessage.error('删除失败')
    }
  }
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedFiles.value.length} 个文件吗？`,
      '批量删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await batchDeleteFiles(props.knowledgeBaseId, selectedFiles.value)
    selectedFiles.value = []
    ElMessage.success('批量删除成功')
    loadFiles()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('Batch delete failed:', err)
      ElMessage.error('批量删除失败')
    }
  }
}

const retryFile = async (file) => {
  try {
    await retryFileProcessing(props.knowledgeBaseId, file.id)
    loadFiles()
  } catch (err) {
    console.error('Retry failed:', err)
  }
}

const previewFile = async (file) => {
  try {
    const { url } = await getFilePreviewUrl(props.knowledgeBaseId, file.id)
    window.open(url, '_blank')
  } catch (err) {
    console.error('Preview failed:', err)
  }
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

const getFileIconClass = (type) => {
  const classes = {
    pdf: 'bg-gemini-red-100 text-gemini-red-600',
    txt: 'bg-gemini-blue-100 text-gemini-blue-600',
    md: 'bg-gemini-purple-100 text-gemini-purple-600',
    markdown: 'bg-gemini-purple-100 text-gemini-purple-600',
    doc: 'bg-gemini-blue-100 text-gemini-blue-600',
    docx: 'bg-gemini-blue-100 text-gemini-blue-600',
    csv: 'bg-gemini-green-100 text-gemini-green-600',
    xlsx: 'bg-gemini-green-100 text-gemini-green-600',
    xls: 'bg-gemini-green-100 text-gemini-green-600',
  }
  return classes[type?.toLowerCase()] || 'bg-gemini-bg text-gemini-text-tertiary'
}

const getStatusClass = (status) => ({
  pending: 'bg-gemini-yellow-50 text-gemini-yellow-700',
  processing: 'bg-gemini-blue-50 text-gemini-blue-700',
  completed: 'bg-gemini-green-50 text-gemini-green-700',
  failed: 'bg-gemini-red-50 text-gemini-red-700',
}[status] || 'bg-gemini-bg text-gemini-text-tertiary')

const getStatusText = (status) => ({
  pending: '等待中', processing: '处理中', completed: '已完成', failed: '失败'
}[status] || status)

watch(() => props.knowledgeBaseId, loadFiles)
onMounted(loadFiles)
</script>
