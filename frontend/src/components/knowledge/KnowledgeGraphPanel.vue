<template>
  <div class="knowledge-graph-fullscreen">
    <!-- 全屏图谱容器 -->
    <div class="graph-main" :class="{ 'panel-open': showPanel }">
      <!-- 顶部工具栏 -->
      <div class="graph-toolbar">
        <div class="toolbar-left">
          <div class="stats-badge">
            <span class="stats-icon">◉</span>
            <span>{{ graphData.total_nodes }} 实体</span>
            <span class="divider">|</span>
            <span>{{ graphData.total_edges }} 关系</span>
          </div>
        </div>
        <div class="toolbar-center">
          <div class="search-box">
            <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            <input v-model="searchQuery" type="text" placeholder="搜索实体节点..." @input="debouncedSearch" />
            <button v-if="searchQuery" @click="clearFilter" class="clear-btn">✕</button>
          </div>
        </div>
        <div class="toolbar-right">
          <button @click="zoomIn" class="tool-btn" title="放大">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"></path></svg>
          </button>
          <button @click="zoomOut" class="tool-btn" title="缩小">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7"></path></svg>
          </button>
          <button @click="fitGraph" class="tool-btn" title="适应屏幕">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
          </button>
          <div class="toolbar-divider"></div>
          <button @click="togglePanel" class="tool-btn" :class="{ active: showPanel }" title="操作面板">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7"></path></svg>
          </button>
          <button @click="openFullscreen" class="tool-btn fullscreen-btn" title="全屏查看">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
            <span class="btn-text">全屏</span>
          </button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="graph-loading">
        <div class="loading-spinner"></div>
        <span>加载知识图谱...</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="graphData.nodes.length === 0" class="graph-empty">
        <div class="empty-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
          </svg>
        </div>
        <h3>暂无知识图谱数据</h3>
        <p>上传文件并处理后，知识图谱将自动生成</p>
      </div>

      <!-- 图谱画布 -->
      <div v-else ref="graphContainer" class="graph-canvas"></div>

      <!-- 底部分页 -->
      <div v-if="graphData.total_nodes > limit" class="graph-pagination">
        <button @click="prevPage" :disabled="skip === 0" class="page-btn">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>
        </button>
        <span class="page-info">{{ Math.floor(skip / limit) + 1 }} / {{ Math.ceil(graphData.total_nodes / limit) }}</span>
        <button @click="nextPage" :disabled="skip + limit >= graphData.total_nodes" class="page-btn">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
        </button>
      </div>
    </div>

    <!-- 右侧操作面板 -->
    <transition name="slide">
      <div v-show="showPanel" class="side-panel">
        <div class="panel-header">
          <h3>操作面板</h3>
          <button @click="showPanel = false" class="close-btn">✕</button>
        </div>

        <div class="panel-content">
          <!-- 选中节点详情 -->
          <div v-if="selectedNode" class="panel-section">
            <div class="section-title">
              <span class="dot selected"></span>
              选中实体
            </div>
            <div class="entity-card">
              <div class="entity-name">{{ selectedNode.label }}</div>
              <div class="entity-type">
                <span class="type-badge">{{ selectedNode.type || 'entity' }}</span>
              </div>
              <div v-if="entityDetail?.description" class="entity-desc">
                {{ entityDetail.description }}
              </div>
              <div v-if="entityDetail?.relations?.length" class="entity-relations">
                <div class="relations-title">相关关系 ({{ entityDetail.relations.length }})</div>
                <div class="relations-list">
                  <div v-for="rel in entityDetail.relations.slice(0, 5)" :key="rel.id" class="relation-item">
                    <span class="rel-source">{{ rel.source }}</span>
                    <span class="rel-arrow">→</span>
                    <span class="rel-target">{{ rel.target }}</span>
                  </div>
                  <div v-if="entityDetail.relations.length > 5" class="relations-more">
                    还有 {{ entityDetail.relations.length - 5 }} 个关系...
                  </div>
                </div>
              </div>
              <button @click="deleteSelectedEntity" class="delete-btn">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                删除实体
              </button>
            </div>
          </div>

          <!-- 未选中提示 -->
          <div v-else class="panel-section">
            <div class="no-selection">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"></path></svg>
              <p>点击图谱中的节点查看详情</p>
            </div>
          </div>

          <!-- 导出选项 -->
          <div class="panel-section">
            <div class="section-title">
              <span class="dot export"></span>
              导出数据
            </div>
            <div class="export-buttons">
              <button @click="exportGraph('json')" class="export-btn">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                JSON 格式
              </button>
              <button @click="exportGraph('csv')" class="export-btn">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                CSV 格式
              </button>
            </div>
          </div>

          <!-- 图例 -->
          <div class="panel-section">
            <div class="section-title">
              <span class="dot legend"></span>
              图例说明
            </div>
            <div class="legend-list">
              <div class="legend-item">
                <span class="legend-node"></span>
                <span>实体节点</span>
              </div>
              <div class="legend-item">
                <span class="legend-edge"></span>
                <span>关系连线</span>
              </div>
              <div class="legend-item">
                <span class="legend-selected"></span>
                <span>选中节点</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getKnowledgeGraph, getEntityDetail, deleteEntity, downloadKnowledgeGraph } from '@/api/knowledge'

const props = defineProps({
  knowledgeBaseId: { type: Number, required: true }
})

const router = useRouter()

const openFullscreen = () => {
  router.push(`/knowledge-base/${props.knowledgeBaseId}/graph`)
}

const graphContainer = ref(null)
const loading = ref(false)
const searchQuery = ref('')
const showPanel = ref(true)
const selectedNode = ref(null)
const entityDetail = ref(null)
const skip = ref(0)
const limit = ref(100)
const graphData = ref({ nodes: [], edges: [], total_nodes: 0, total_edges: 0 })

let network = null
let searchTimeout = null

const loadGraph = async () => {
  console.log('[KnowledgeGraph] loadGraph called, knowledgeBaseId:', props.knowledgeBaseId)
  loading.value = true
  try {
    const params = {
      skip: skip.value,
      limit: limit.value,
      search: searchQuery.value || undefined
    }
    console.log('[KnowledgeGraph] Fetching graph with params:', params)
    graphData.value = await getKnowledgeGraph(props.knowledgeBaseId, params)
    console.log('[KnowledgeGraph] Graph data received:', {
      nodes: graphData.value.nodes?.length || 0,
      edges: graphData.value.edges?.length || 0,
      total_nodes: graphData.value.total_nodes,
      total_edges: graphData.value.total_edges,
      rawData: graphData.value
    })
  } catch (err) {
    console.error('[KnowledgeGraph] Failed to load graph:', err)
  } finally {
    loading.value = false
    // 等待 DOM 更新后再渲染图谱
    await nextTick()
    console.log('[KnowledgeGraph] loading set to false, nextTick done, calling renderGraph')
    renderGraph()
  }
}

const renderGraph = async () => {
  console.log('[KnowledgeGraph] renderGraph called')
  console.log('[KnowledgeGraph] graphContainer.value:', graphContainer.value)
  console.log('[KnowledgeGraph] nodes count:', graphData.value.nodes?.length)
  
  if (!graphContainer.value) {
    console.warn('[KnowledgeGraph] graphContainer is null, cannot render')
    return
  }
  if (!graphData.value.nodes || graphData.value.nodes.length === 0) {
    console.warn('[KnowledgeGraph] No nodes to render')
    return
  }
  
  console.log('[KnowledgeGraph] Importing vis-network...')
  const { Network, DataSet } = await import('vis-network/standalone')
  console.log('[KnowledgeGraph] vis-network imported successfully')
  
  // 根据节点类型分配颜色
  const typeColors = {
    person: { bg: '#8B5CF6', border: '#7C3AED' },
    organization: { bg: '#3B82F6', border: '#2563EB' },
    location: { bg: '#10B981', border: '#059669' },
    event: { bg: '#F59E0B', border: '#D97706' },
    concept: { bg: '#EC4899', border: '#DB2777' },
    default: { bg: '#6366F1', border: '#4F46E5' }
  }

  const nodes = new DataSet(graphData.value.nodes.map(n => {
    const colors = typeColors[n.type?.toLowerCase()] || typeColors.default
    return {
      id: n.id,
      label: n.label,
      title: `${n.label}\n类型: ${n.type || 'entity'}`,
      color: { background: colors.bg, border: colors.border, highlight: { background: '#FBBF24', border: '#F59E0B' } },
      font: { color: '#ffffff', size: 12 },
      borderWidth: 2,
      shadow: true
    }
  }))
  
  const edges = new DataSet(graphData.value.edges.map(e => ({
    id: e.id,
    from: e.source,
    to: e.target,
    label: e.label,
    arrows: { to: { enabled: true, scaleFactor: 0.8 } },
    font: { size: 10, color: '#6B7280', strokeWidth: 0, background: 'rgba(255,255,255,0.8)' },
    color: { color: '#9CA3AF', highlight: '#6366F1' },
    smooth: { type: 'curvedCW', roundness: 0.2 }
  })))
  
  const options = {
    nodes: { shape: 'dot', size: 20, borderWidth: 2 },
    edges: { width: 1.5 },
    physics: {
      solver: 'forceAtlas2Based',
      forceAtlas2Based: { gravitationalConstant: -50, centralGravity: 0.01, springLength: 150, springConstant: 0.08 },
      stabilization: { iterations: 150, fit: true }
    },
    interaction: { hover: true, tooltipDelay: 100, zoomView: true, dragView: true, navigationButtons: false, keyboard: true }
  }
  
  if (network) {
    console.log('[KnowledgeGraph] Destroying existing network')
    network.destroy()
  }
  
  console.log('[KnowledgeGraph] Creating new Network with:', {
    container: graphContainer.value,
    nodesCount: nodes.length,
    edgesCount: edges.length
  })
  
  try {
    network = new Network(graphContainer.value, { nodes, edges }, options)
    console.log('[KnowledgeGraph] Network created successfully')
  } catch (err) {
    console.error('[KnowledgeGraph] Failed to create Network:', err)
    return
  }
  
  network.on('click', async (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0]
      const node = graphData.value.nodes.find(n => n.id === nodeId)
      selectedNode.value = node
      showPanel.value = true
      try {
        entityDetail.value = await getEntityDetail(props.knowledgeBaseId, nodeId)
      } catch (err) {
        console.error('Failed to load entity detail:', err)
        entityDetail.value = null
      }
    } else {
      selectedNode.value = null
      entityDetail.value = null
    }
  })
}

const zoomIn = () => { if (network) network.moveTo({ scale: network.getScale() * 1.3 }) }
const zoomOut = () => { if (network) network.moveTo({ scale: network.getScale() / 1.3 }) }
const fitGraph = () => { if (network) network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } }) }
const togglePanel = () => { showPanel.value = !showPanel.value }

const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => { skip.value = 0; loadGraph() }, 300)
}

const clearFilter = () => { searchQuery.value = ''; skip.value = 0; loadGraph() }
const prevPage = () => { if (skip.value > 0) { skip.value = Math.max(0, skip.value - limit.value); loadGraph() } }
const nextPage = () => { if (skip.value + limit.value < graphData.value.total_nodes) { skip.value += limit.value; loadGraph() } }

const deleteSelectedEntity = async () => {
  if (!selectedNode.value) return
  try {
    await ElMessageBox.confirm(
      `确定要删除实体"${selectedNode.value.label}"及其所有关系吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteEntity(props.knowledgeBaseId, selectedNode.value.id)
    selectedNode.value = null
    entityDetail.value = null
    ElMessage.success('删除成功')
    loadGraph()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('Failed to delete entity:', err)
      ElMessage.error('删除失败')
    }
  }
}

const exportGraph = async (format) => {
  try { await downloadKnowledgeGraph(props.knowledgeBaseId, format) }
  catch (err) { console.error('Export failed:', err) }
}

watch(() => props.knowledgeBaseId, (newId, oldId) => { 
  console.log('[KnowledgeGraph] knowledgeBaseId changed:', oldId, '->', newId)
  skip.value = 0
  loadGraph() 
})
onMounted(() => { 
  console.log('[KnowledgeGraph] Component mounted, knowledgeBaseId:', props.knowledgeBaseId)
  loadGraph() 
})
onUnmounted(() => { if (network) network.destroy() })
</script>

<style scoped>
.knowledge-graph-fullscreen {
  position: relative;
  display: flex;
  height: calc(100vh - 280px);
  min-height: 500px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.graph-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: margin-right 0.3s ease;
}
.graph-main.panel-open { margin-right: 320px; }

.graph-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 10;
}

.toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 8px; }
.toolbar-center { flex: 1; display: flex; justify-content: center; padding: 0 20px; }

.stats-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 20px;
  font-size: 13px;
  color: #a5b4fc;
}
.stats-icon { color: #818cf8; }
.divider { color: rgba(255, 255, 255, 0.2); }

.search-box {
  position: relative;
  width: 100%;
  max-width: 400px;
}
.search-box input {
  width: 100%;
  padding: 8px 36px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  transition: all 0.2s;
}
.search-box input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.15);
  border-color: #6366f1;
}
.search-box input::placeholder { color: rgba(255, 255, 255, 0.4); }
.search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); width: 18px; height: 18px; color: rgba(255, 255, 255, 0.4); }
.clear-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  font-size: 14px;
}
.clear-btn:hover { color: #fff; }

.tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.2s;
}
.tool-btn:hover { background: rgba(255, 255, 255, 0.2); color: #fff; }
.tool-btn.active { background: #6366f1; border-color: #6366f1; color: #fff; }
.tool-btn svg { width: 18px; height: 18px; }
.tool-btn.fullscreen-btn {
  width: auto;
  padding: 0 12px;
  gap: 6px;
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.3);
  color: #a5b4fc;
}
.tool-btn.fullscreen-btn:hover { background: rgba(99, 102, 241, 0.3); color: #fff; }
.tool-btn.fullscreen-btn .btn-text { font-size: 13px; }
.toolbar-divider { width: 1px; height: 24px; background: rgba(255, 255, 255, 0.1); margin: 0 4px; }

.graph-canvas { flex: 1; width: 100%; }
.graph-loading, .graph-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.6);
}
.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.graph-empty .empty-icon { margin-bottom: 16px; }
.graph-empty .empty-icon svg { width: 64px; height: 64px; color: rgba(255, 255, 255, 0.2); }
.graph-empty h3 { font-size: 18px; color: rgba(255, 255, 255, 0.8); margin-bottom: 8px; }
.graph-empty p { font-size: 14px; color: rgba(255, 255, 255, 0.4); }

.graph-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 12px;
  background: rgba(30, 41, 59, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.2s;
}
.page-btn:hover:not(:disabled) { background: rgba(255, 255, 255, 0.2); color: #fff; }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-btn svg { width: 16px; height: 16px; }
.page-info { font-size: 13px; color: rgba(255, 255, 255, 0.6); }

/* 右侧面板 */
.side-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 320px;
  height: 100%;
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(10px);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 20;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.panel-header h3 { font-size: 16px; font-weight: 600; color: #fff; margin: 0; }
.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s;
}
.close-btn:hover { background: rgba(255, 255, 255, 0.2); color: #fff; }

.panel-content { flex: 1; overflow-y: auto; padding: 16px; }
.panel-section { margin-bottom: 24px; }
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.dot.selected { background: #fbbf24; }
.dot.export { background: #10b981; }
.dot.legend { background: #6366f1; }

.entity-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
}
.entity-name { font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 8px; }
.entity-type { margin-bottom: 12px; }
.type-badge {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 12px;
  font-size: 12px;
  color: #a5b4fc;
}
.entity-desc { font-size: 13px; color: rgba(255, 255, 255, 0.6); line-height: 1.5; margin-bottom: 12px; }
.entity-relations { margin-bottom: 16px; }
.relations-title { font-size: 12px; color: rgba(255, 255, 255, 0.5); margin-bottom: 8px; }
.relations-list { display: flex; flex-direction: column; gap: 6px; }
.relation-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  font-size: 12px;
}
.rel-source, .rel-target { color: rgba(255, 255, 255, 0.8); }
.rel-arrow { color: rgba(255, 255, 255, 0.3); }
.relations-more { font-size: 11px; color: rgba(255, 255, 255, 0.4); text-align: center; padding: 4px; }

.delete-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #fca5a5;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.delete-btn:hover { background: rgba(239, 68, 68, 0.2); color: #fecaca; }
.delete-btn svg { width: 16px; height: 16px; }

.no-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}
.no-selection svg { width: 48px; height: 48px; color: rgba(255, 255, 255, 0.2); margin-bottom: 12px; }
.no-selection p { font-size: 13px; color: rgba(255, 255, 255, 0.4); }

.export-buttons { display: flex; flex-direction: column; gap: 8px; }
.export-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.export-btn:hover { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.2); }
.export-btn svg { width: 18px; height: 18px; color: #10b981; }

.legend-list { display: flex; flex-direction: column; gap: 10px; }
.legend-item { display: flex; align-items: center; gap: 10px; font-size: 13px; color: rgba(255, 255, 255, 0.6); }
.legend-node { width: 16px; height: 16px; background: #6366f1; border-radius: 50%; border: 2px solid #4f46e5; }
.legend-edge { width: 24px; height: 2px; background: #9ca3af; }
.legend-selected { width: 16px; height: 16px; background: #fbbf24; border-radius: 50%; border: 2px solid #f59e0b; }

/* 动画 */
.slide-enter-active, .slide-leave-active { transition: transform 0.3s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); }
</style>
