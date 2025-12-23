<template>
  <div class="knowledge-graph-page">
    <!-- 顶部导航栏 -->
    <div class="page-header">
      <div class="header-left">
        <button @click="goBack" class="back-btn">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
          </svg>
          返回
        </button>
        <div class="page-title">
          <h1>{{ knowledgeBaseName }}</h1>
          <span class="subtitle">知识图谱</span>
        </div>
      </div>
      <div class="header-right">
        <div class="stats-badge">
          <span class="stats-icon">◉</span>
          <span>{{ graphData.total_nodes }} 实体</span>
          <span class="divider">|</span>
          <span>{{ graphData.total_edges }} 关系</span>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="page-content">
      <!-- 左侧工具栏 -->
      <div class="left-toolbar">
        <div class="tool-group">
          <button @click="zoomIn" class="tool-btn" title="放大">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"></path></svg>
          </button>
          <button @click="zoomOut" class="tool-btn" title="缩小">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7"></path></svg>
          </button>
          <button @click="fitGraph" class="tool-btn" title="适应屏幕">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
          </button>
        </div>
        <div class="tool-group">
          <button @click="togglePanel" class="tool-btn" :class="{ active: showPanel }" title="操作面板">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7"></path></svg>
          </button>
        </div>
      </div>

      <!-- 图谱主区域 -->
      <div class="graph-area" :class="{ 'panel-open': showPanel }">
        <!-- 搜索框 -->
        <div class="search-container">
          <div class="search-box">
            <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            <input v-model="searchQuery" type="text" placeholder="搜索实体节点..." @input="debouncedSearch" />
            <button v-if="searchQuery" @click="clearFilter" class="clear-btn">✕</button>
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
          </div>
          <div class="panel-content">
            <!-- 选中节点详情 -->
            <div v-if="selectedNode" class="panel-section">
              <div class="section-title"><span class="dot selected"></span>选中实体</div>
              <div class="entity-card">
                <div class="entity-name">{{ selectedNode.label }}</div>
                <div class="entity-type"><span class="type-badge">{{ selectedNode.type || 'entity' }}</span></div>
                <div v-if="entityDetail?.description" class="entity-desc">{{ entityDetail.description }}</div>
                <div v-if="entityDetail?.relations?.length" class="entity-relations">
                  <div class="relations-title">相关关系 ({{ entityDetail.relations.length }})</div>
                  <div class="relations-list">
                    <div v-for="rel in entityDetail.relations.slice(0, 5)" :key="rel.id" class="relation-item">
                      <span class="rel-source">{{ rel.source }}</span>
                      <span class="rel-arrow">→</span>
                      <span class="rel-target">{{ rel.target }}</span>
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
              <div class="section-title"><span class="dot export"></span>导出数据</div>
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
              <div class="section-title"><span class="dot legend"></span>图例说明</div>
              <div class="legend-list">
                <div class="legend-item"><span class="legend-node"></span><span>实体节点</span></div>
                <div class="legend-item"><span class="legend-edge"></span><span>关系连线</span></div>
                <div class="legend-item"><span class="legend-selected"></span><span>选中节点</span></div>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getKnowledgeBase, getKnowledgeGraph, getEntityDetail, deleteEntity, downloadKnowledgeGraph } from '@/api/knowledge'

const route = useRoute()
const router = useRouter()

const knowledgeBaseId = ref(Number(route.params.id))
const knowledgeBaseName = ref('知识库')
const graphContainer = ref(null)
const loading = ref(false)
const searchQuery = ref('')
const showPanel = ref(true)
const selectedNode = ref(null)
const entityDetail = ref(null)
const skip = ref(0)
const limit = ref(500)
const graphData = ref({ nodes: [], edges: [], total_nodes: 0, total_edges: 0 })

let network = null
let searchTimeout = null

const goBack = () => router.push(`/knowledge-base/${knowledgeBaseId.value}`)

const loadKnowledgeBase = async () => {
  try {
    const kb = await getKnowledgeBase(knowledgeBaseId.value)
    knowledgeBaseName.value = kb.name
  } catch (err) {
    console.error('Failed to load knowledge base:', err)
  }
}

const loadGraph = async () => {
  console.log('[KnowledgeGraphPage] loadGraph called')
  loading.value = true
  try {
    graphData.value = await getKnowledgeGraph(knowledgeBaseId.value, {
      skip: skip.value, limit: limit.value, search: searchQuery.value || undefined
    })
    console.log('[KnowledgeGraphPage] Graph data:', graphData.value)
  } catch (err) {
    console.error('[KnowledgeGraphPage] Failed to load graph:', err)
  } finally {
    loading.value = false
    await nextTick()
    renderGraph()
  }
}

const renderGraph = async () => {
  console.log('[KnowledgeGraphPage] renderGraph called')
  if (!graphContainer.value || !graphData.value.nodes?.length) return
  
  const { Network, DataSet } = await import('vis-network/standalone')
  
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
      id: n.id, label: n.label, title: `${n.label}\n类型: ${n.type || 'entity'}`,
      color: { background: colors.bg, border: colors.border, highlight: { background: '#FBBF24', border: '#F59E0B' } },
      font: { color: '#ffffff', size: 14 }, borderWidth: 2, shadow: true, size: 25
    }
  }))
  
  const edges = new DataSet(graphData.value.edges.map(e => ({
    id: e.id, from: e.source, to: e.target, label: e.label,
    arrows: { to: { enabled: true, scaleFactor: 0.8 } },
    font: { size: 11, color: '#94A3B8', strokeWidth: 0, background: 'rgba(15,23,42,0.8)' },
    color: { color: '#475569', highlight: '#6366F1' },
    smooth: { type: 'curvedCW', roundness: 0.2 }, width: 2
  })))
  
  const options = {
    nodes: { shape: 'dot', borderWidth: 2 },
    edges: { width: 2 },
    physics: {
      solver: 'forceAtlas2Based',
      forceAtlas2Based: { gravitationalConstant: -80, centralGravity: 0.005, springLength: 200, springConstant: 0.05 },
      stabilization: { iterations: 200, fit: true }
    },
    interaction: { hover: true, tooltipDelay: 100, zoomView: true, dragView: true, keyboard: true }
  }
  
  if (network) network.destroy()
  network = new Network(graphContainer.value, { nodes, edges }, options)
  
  network.on('click', async (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0]
      selectedNode.value = graphData.value.nodes.find(n => n.id === nodeId)
      showPanel.value = true
      try { entityDetail.value = await getEntityDetail(knowledgeBaseId.value, nodeId) }
      catch { entityDetail.value = null }
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
const prevPage = () => { if (skip.value > 0) { skip.value -= limit.value; loadGraph() } }
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
    await deleteEntity(knowledgeBaseId.value, selectedNode.value.id)
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
  try { await downloadKnowledgeGraph(knowledgeBaseId.value, format) }
  catch (err) { console.error('Export failed:', err) }
}

watch(() => route.params.id, (newId) => {
  knowledgeBaseId.value = Number(newId)
  loadKnowledgeBase()
  loadGraph()
})

onMounted(() => { loadKnowledgeBase(); loadGraph() })
onUnmounted(() => { if (network) network.destroy() })
</script>


<style scoped>
.knowledge-graph-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-left { display: flex; align-items: center; gap: 20px; }

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.back-btn:hover { background: rgba(255, 255, 255, 0.2); color: #fff; }
.back-btn svg { width: 18px; height: 18px; }

.page-title h1 { font-size: 20px; font-weight: 600; color: #fff; margin: 0; }
.page-title .subtitle { font-size: 13px; color: rgba(255, 255, 255, 0.5); }

.stats-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 20px;
  font-size: 14px;
  color: #a5b4fc;
}
.stats-icon { color: #818cf8; }
.divider { color: rgba(255, 255, 255, 0.2); }

.page-content { flex: 1; display: flex; position: relative; overflow: hidden; }

.left-toolbar {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 16px;
  z-index: 10;
}

.tool-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.2s;
}
.tool-btn:hover { background: rgba(255, 255, 255, 0.2); color: #fff; }
.tool-btn.active { background: #6366f1; color: #fff; }
.tool-btn svg { width: 20px; height: 20px; }

.graph-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: margin-right 0.3s ease;
}
.graph-area.panel-open { margin-right: 360px; }

.search-container { position: absolute; top: 16px; left: 50%; transform: translateX(-50%); z-index: 10; }

.search-box { position: relative; width: 400px; }
.search-box input {
  width: 100%;
  padding: 12px 44px;
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: #fff;
  font-size: 14px;
  backdrop-filter: blur(10px);
}
.search-box input:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2); }
.search-box input::placeholder { color: rgba(255, 255, 255, 0.4); }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); width: 20px; height: 20px; color: rgba(255, 255, 255, 0.4); }
.clear-btn { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); background: none; border: none; color: rgba(255, 255, 255, 0.4); cursor: pointer; }
.clear-btn:hover { color: #fff; }

.graph-canvas { flex: 1; width: 100%; }

.graph-loading, .graph-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: rgba(255, 255, 255, 0.6); }
.loading-spinner { width: 48px; height: 48px; border: 3px solid rgba(255, 255, 255, 0.1); border-top-color: #6366f1; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }
.graph-empty .empty-icon svg { width: 80px; height: 80px; color: rgba(255, 255, 255, 0.2); }
.graph-empty h3 { font-size: 20px; color: rgba(255, 255, 255, 0.8); margin: 16px 0 8px; }
.graph-empty p { font-size: 14px; color: rgba(255, 255, 255, 0.4); }

.graph-pagination {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}
.page-btn { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: rgba(255, 255, 255, 0.1); border: none; border-radius: 6px; color: rgba(255, 255, 255, 0.7); cursor: pointer; }
.page-btn:hover:not(:disabled) { background: rgba(255, 255, 255, 0.2); color: #fff; }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-btn svg { width: 16px; height: 16px; }
.page-info { font-size: 13px; color: rgba(255, 255, 255, 0.6); }

.side-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 360px;
  height: 100%;
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(10px);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 20;
}
.panel-header { display: flex; align-items: center; padding: 20px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.panel-header h3 { font-size: 18px; font-weight: 600; color: #fff; margin: 0; }

.panel-content { flex: 1; overflow-y: auto; padding: 20px; }
.panel-section { margin-bottom: 28px; }
.section-title { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 600; color: rgba(255, 255, 255, 0.5); text-transform: uppercase; margin-bottom: 14px; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.selected { background: #fbbf24; }
.dot.export { background: #10b981; }
.dot.legend { background: #6366f1; }

.entity-card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; }
.entity-name { font-size: 18px; font-weight: 600; color: #fff; margin-bottom: 10px; }
.entity-type { margin-bottom: 14px; }
.type-badge { display: inline-block; padding: 5px 12px; background: rgba(99, 102, 241, 0.2); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; font-size: 13px; color: #a5b4fc; }
.entity-desc { font-size: 14px; color: rgba(255, 255, 255, 0.6); line-height: 1.6; margin-bottom: 14px; }
.entity-relations { margin-bottom: 18px; }
.relations-title { font-size: 13px; color: rgba(255, 255, 255, 0.5); margin-bottom: 10px; }
.relations-list { display: flex; flex-direction: column; gap: 8px; }
.relation-item { display: flex; align-items: center; gap: 8px; padding: 10px 12px; background: rgba(255, 255, 255, 0.05); border-radius: 8px; font-size: 13px; }
.rel-source, .rel-target { color: rgba(255, 255, 255, 0.8); }
.rel-arrow { color: rgba(255, 255, 255, 0.3); }

.delete-btn { width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; color: #fca5a5; font-size: 14px; cursor: pointer; }
.delete-btn:hover { background: rgba(239, 68, 68, 0.2); color: #fecaca; }
.delete-btn svg { width: 18px; height: 18px; }

.no-selection { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px 24px; text-align: center; }
.no-selection svg { width: 56px; height: 56px; color: rgba(255, 255, 255, 0.2); margin-bottom: 16px; }
.no-selection p { font-size: 14px; color: rgba(255, 255, 255, 0.4); }

.export-buttons { display: flex; flex-direction: column; gap: 10px; }
.export-btn { display: flex; align-items: center; gap: 12px; padding: 14px 18px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: rgba(255, 255, 255, 0.8); font-size: 14px; cursor: pointer; }
.export-btn:hover { background: rgba(255, 255, 255, 0.1); }
.export-btn svg { width: 20px; height: 20px; color: #10b981; }

.legend-list { display: flex; flex-direction: column; gap: 12px; }
.legend-item { display: flex; align-items: center; gap: 12px; font-size: 14px; color: rgba(255, 255, 255, 0.6); }
.legend-node { width: 18px; height: 18px; background: #6366f1; border-radius: 50%; border: 2px solid #4f46e5; }
.legend-edge { width: 28px; height: 2px; background: #475569; }
.legend-selected { width: 18px; height: 18px; background: #fbbf24; border-radius: 50%; border: 2px solid #f59e0b; }

.slide-enter-active, .slide-leave-active { transition: transform 0.3s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); }
</style>
