<template>
  <div class="analysis-view">
    <div class="card">
      <div class="card-header">
        <h2>📈 知识分析</h2>
        <div class="header-actions">
          <button class="btn btn-secondary" @click="refreshAll" :disabled="loading">
            <span class="btn-icon">🔄</span>
            <span class="btn-text">刷新</span>
          </button>
        </div>
      </div>

      <div class="tabs">
        <div 
          class="tab" 
          :class="{ active: activeTab === 'space' }"
          @click="activeTab = 'space'"
        >
          🌐 知识空间
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'distribution' }"
          @click="activeTab = 'distribution'"
        >
          📊 相似度分布
        </div>
        <div 
          class="tab" 
          :class="{ active: activeTab === 'organization' }"
          @click="activeTab = 'organization'"
        >
          🗂️ 知识整理
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>

      <div v-else class="tab-content">
        <div v-if="activeTab === 'space'" class="space-tab">
          <div class="visualization-controls">
            <div class="control-group">
              <label>可视化方式:</label>
              <select v-model="vizMode">
                <option value="scatter">散点图</option>
                <option value="heatmap">热力图</option>
                <option value="network">网络图</option>
              </select>
            </div>
            <div class="control-group" v-if="vizMode === 'network'">
              <label>相似度阈值:</label>
              <input 
                type="range" 
                v-model.number="networkThreshold" 
                min="0.5" 
                max="0.95" 
                step="0.05"
                @change="loadNetworkData"
              />
              <span>{{ networkThreshold.toFixed(2) }}</span>
            </div>
            <div class="control-group" v-if="vizMode === 'heatmap'">
              <label>显示数量:</label>
              <select v-model.number="heatmapMaxItems" @change="loadHeatmapData">
                <option :value="30">30</option>
                <option :value="50">50</option>
                <option :value="80">80</option>
              </select>
            </div>
          </div>

          <div class="visualization-container">
            <div v-if="vizMode === 'scatter'" class="scatter-view">
              <div class="scatter-canvas-wrapper">
                <canvas 
                  ref="scatterCanvas" 
                  @mousedown="onScatterMouseDown" 
                  @mousemove="onScatterMouseMove" 
                  @mouseup="onScatterMouseUp"
                  @wheel="onScatterWheel"
                ></canvas>
                <div v-if="hoveredPoint" class="point-tooltip" :style="tooltipStyle">
                  <div class="tooltip-catalog">{{ hoveredPoint.catalog_name }}</div>
                  <div class="tooltip-question">{{ hoveredPoint.full_question }}</div>
                </div>
              </div>
              <div class="scatter-legend" v-if="spaceData.catalogs && spaceData.catalogs.length > 0">
                <h4>目录图例</h4>
                <div class="legend-items">
                  <div 
                    v-for="catalog in spaceData.catalogs" 
                    :key="catalog.id"
                    class="legend-item"
                    @click="toggleCatalog(catalog.id)"
                    :class="{ dimmed: hiddenCatalogs.includes(catalog.id) }"
                  >
                    <span class="legend-color" :style="{ background: catalog.color }"></span>
                    <span class="legend-name">{{ catalog.name }}</span>
                  </div>
                </div>
              </div>
              <div class="scatter-stats" v-if="spaceData.statistics">
                <div class="stat-item">
                  <span class="stat-label">总知识数:</span>
                  <span class="stat-value">{{ spaceData.statistics.total_knowledge }}</span>
                </div>
                <div class="stat-item" v-if="spaceData.statistics.variance_explained && spaceData.statistics.variance_explained.length > 0">
                  <span class="stat-label">方差解释率:</span>
                  <span class="stat-value">{{ (spaceData.statistics.variance_explained[0].cumulative * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </div>

            <div v-if="vizMode === 'heatmap'" class="heatmap-view">
              <div class="heatmap-canvas-wrapper">
                <canvas ref="heatmapCanvas"></canvas>
              </div>
              <div class="heatmap-legend">
                <div class="legend-gradient"></div>
                <div class="legend-labels">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>
              <div class="heatmap-info">
                <span>鼠标悬停查看详细相似度</span>
              </div>
            </div>

            <div v-if="vizMode === 'network'" class="network-view">
              <div class="network-canvas-wrapper">
                <canvas 
                  ref="networkCanvas"
                  @mousedown="onNetworkMouseDown"
                  @mousemove="onNetworkMouseMove"
                  @mouseup="onNetworkMouseUp"
                  @wheel="onNetworkWheel"
                ></canvas>
                <div v-if="hoveredNode" class="node-tooltip" :style="nodeTooltipStyle">
                  <div class="tooltip-catalog">{{ hoveredNode.catalog_name }}</div>
                  <div class="tooltip-question">{{ hoveredNode.full_question }}</div>
                  <div class="tooltip-degree">连接数: {{ hoveredNode.degree }}</div>
                </div>
              </div>
              <div class="network-stats" v-if="networkData.statistics">
                <div class="stat-item">
                  <span class="stat-label">节点数:</span>
                  <span class="stat-value">{{ networkData.statistics.total_nodes }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">边数:</span>
                  <span class="stat-value">{{ networkData.statistics.total_edges }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'distribution'" class="distribution-tab">
          <div class="section-header">
            <h3>相似度分布统计</h3>
            <div class="threshold-control">
              <label>高相似度阈值:</label>
              <input 
                type="range" 
                v-model.number="similarityThreshold" 
                min="0.5" 
                max="0.99" 
                step="0.01"
                @change="loadDistribution"
              />
              <span>{{ similarityThreshold.toFixed(2) }}</span>
            </div>
          </div>

          <div class="stats-cards">
            <div class="stat-card">
              <div class="stat-icon">📚</div>
              <div class="stat-info">
                <div class="stat-value">{{ distribution.total_knowledge }}</div>
                <div class="stat-label">总知识数</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📊</div>
              <div class="stat-info">
                <div class="stat-value">{{ distribution.mean_similarity?.toFixed(3) || '-' }}</div>
                <div class="stat-label">平均相似度</div>
              </div>
            </div>
            <div class="stat-card highlight">
              <div class="stat-icon">⚠️</div>
              <div class="stat-info">
                <div class="stat-value">{{ distribution.high_similarity_count }}</div>
                <div class="stat-label">高相似度对</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📈</div>
              <div class="stat-info">
                <div class="stat-value">{{ distribution.std_similarity?.toFixed(3) || '-' }}</div>
                <div class="stat-label">标准差</div>
              </div>
            </div>
          </div>

          <div class="distribution-chart" v-if="chartData.length > 0">
            <h4>相似度分布图</h4>
            <div class="chart-container">
              <div class="bar-chart">
                <div 
                  v-for="(bin, index) in chartData" 
                  :key="index"
                  class="bar-item"
                >
                  <div class="bar-wrapper">
                    <div 
                      class="bar" 
                      :style="{ height: getBarHeight(bin.count) }"
                      :class="{ highlight: bin.range_start >= similarityThreshold }"
                    ></div>
                  </div>
                  <div class="bar-label">{{ bin.range_start.toFixed(1) }}</div>
                  <div class="bar-count">{{ bin.count }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="similar-pairs-section">
            <div class="section-header">
              <h3>高相似度知识对</h3>
              <div class="limit-control">
                <label>显示数量:</label>
                <select v-model.number="pairsLimit" @change="loadSimilarPairs">
                  <option :value="20">20</option>
                  <option :value="50">50</option>
                  <option :value="100">100</option>
                </select>
              </div>
            </div>
            
            <div v-if="similarPairs.length === 0" class="empty-state">
              没有发现高相似度的知识对
            </div>
            
            <div v-else class="pairs-list">
              <div 
                v-for="pair in similarPairs" 
                :key="`${pair.id1}-${pair.id2}`"
                class="pair-item"
              >
                <div class="pair-similarity">
                  <div 
                    class="similarity-bar"
                    :style="{ width: (pair.similarity * 100) + '%' }"
                  ></div>
                  <span class="similarity-value">{{ (pair.similarity * 100).toFixed(1) }}%</span>
                </div>
                <div class="pair-content">
                  <div class="pair-question">
                    <span class="pair-label">Q1:</span>
                    {{ pair.question1 }}
                  </div>
                  <div class="pair-question">
                    <span class="pair-label">Q2:</span>
                    {{ pair.question2 }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'organization'" class="organization-tab">
          <div class="org-summary">
            <h3>整理概览</h3>
            <div class="summary-cards">
              <div class="summary-card">
                <div class="summary-value">{{ orgSummary.total_knowledge }}</div>
                <div class="summary-label">总知识数</div>
              </div>
              <div class="summary-card">
                <div class="summary-value">{{ orgSummary.total_catalogs }}</div>
                <div class="summary-label">目录数</div>
              </div>
              <div class="summary-card warning">
                <div class="summary-value">{{ orgSummary.uncategorized_count }}</div>
                <div class="summary-label">未分类</div>
              </div>
              <div class="summary-card danger">
                <div class="summary-value">{{ orgSummary.duplicate_groups_count }}</div>
                <div class="summary-label">重复组</div>
              </div>
            </div>
          </div>

          <div class="merge-suggestions-section">
            <div class="section-header">
              <h3>合并建议</h3>
              <button 
                class="btn btn-primary btn-sm"
                @click="autoMerge"
                :disabled="mergeSuggestions.length === 0 || merging"
              >
                {{ merging ? '合并中...' : '一键合并所有' }}
              </button>
            </div>

            <div v-if="mergeSuggestions.length === 0" class="empty-state">
              没有需要合并的知识
            </div>

            <div v-else class="merge-list">
              <div 
                v-for="suggestion in mergeSuggestions" 
                :key="suggestion.primary_id"
                class="merge-item"
              >
                <div class="merge-header">
                  <span class="merge-badge">主条目</span>
                  <span class="merge-question">{{ suggestion.primary_question }}</span>
                </div>
                <div class="merge-duplicates">
                  <div 
                    v-for="(dupId, index) in suggestion.duplicate_ids" 
                    :key="dupId"
                    class="merge-dup"
                  >
                    <span class="dup-similarity">{{ (suggestion.similarity_scores[index] * 100).toFixed(1) }}%</span>
                    {{ suggestion.duplicate_questions[index] }}
                  </div>
                </div>
                <div class="merge-actions">
                  <button 
                    class="btn btn-primary btn-sm"
                    @click="mergeSingle(suggestion)"
                    :disabled="merging"
                  >
                    合并此组
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="auto-organize-section">
            <h3>自动整理</h3>
            <p class="section-desc">自动执行知识整理操作，包括合并重复知识和重组目录结构。</p>
            <div class="organize-controls">
              <div class="control-item">
                <label>合并阈值:</label>
                <input 
                  type="range" 
                  v-model.number="autoMergeThreshold" 
                  min="0.8" 
                  max="0.99" 
                  step="0.01"
                />
                <span>{{ autoMergeThreshold.toFixed(2) }}</span>
              </div>
              <div class="control-item">
                <label>目录最大条目:</label>
                <input 
                  type="number" 
                  v-model.number="maxItemsPerCatalog" 
                  min="5" 
                  max="50"
                />
              </div>
            </div>
            <div class="button-group">
              <button 
                class="btn btn-primary"
                @click="autoOrganize"
                :disabled="organizing"
              >
                {{ organizing ? '整理中...' : '开始自动整理' }}
              </button>
              <button 
                class="btn btn-secondary"
                @click="syncCatalogCounts"
                :disabled="syncing"
              >
                {{ syncing ? '同步中...' : '同步目录计数' }}
              </button>
            </div>
            <div v-if="syncResult" class="sync-result">
              <h4>同步结果</h4>
              <div class="result-stats">
                <div class="result-item">
                  <span class="result-label">更新目录数:</span>
                  <span class="result-value">{{ syncResult.catalogs_updated }}</span>
                </div>
                <div class="result-item">
                  <span class="result-label">新增条目:</span>
                  <span class="result-value">{{ syncResult.items_added }}</span>
                </div>
                <div class="result-item">
                  <span class="result-label">移除无效条目:</span>
                  <span class="result-value">{{ syncResult.items_removed }}</span>
                </div>
              </div>
            </div>
            <div v-if="organizeResult" class="organize-result">
              <h4>整理结果</h4>
              <div class="result-stats">
                <div class="result-item">
                  <span class="result-label">合并的知识:</span>
                  <span class="result-value">{{ organizeResult.merged_count || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { analysisApi } from '../api'

const activeTab = ref('space')
const loading = ref(false)
const merging = ref(false)
const organizing = ref(false)
const syncing = ref(false)

const vizMode = ref('scatter')
const similarityThreshold = ref(0.85)
const pairsLimit = ref(50)
const autoMergeThreshold = ref(0.90)
const maxItemsPerCatalog = ref(20)
const networkThreshold = ref(0.7)
const heatmapMaxItems = ref(50)

const distribution = ref({})
const chartData = ref([])
const similarPairs = ref([])
const mergeSuggestions = ref([])
const orgSummary = ref({})
const organizeResult = ref(null)
const syncResult = ref(null)

const spaceData = ref({ points: [], catalogs: [], statistics: {} })
const heatmapData = ref({ matrix: [], labels: [], catalogs: [] })
const networkData = ref({ nodes: [], edges: [], statistics: {} })

const hiddenCatalogs = ref([])
const hoveredPoint = ref(null)
const hoveredNode = ref(null)
const tooltipStyle = ref({})
const nodeTooltipStyle = ref({})

const scatterCanvas = ref(null)
const heatmapCanvas = ref(null)
const networkCanvas = ref(null)

let scatterScale = 1
let scatterOffsetX = 0
let scatterOffsetY = 0
let isScatterDragging = false
let lastScatterX = 0
let lastScatterY = 0

let networkScale = 1
let networkOffsetX = 0
let networkOffsetY = 0
let isNetworkDragging = false
let lastNetworkX = 0
let lastNetworkY = 0
let networkNodes = []

const loadDistribution = async () => {
  try {
    const response = await analysisApi.getDistribution(similarityThreshold.value)
    distribution.value = response.data
  } catch (error) {
    console.error('Failed to load distribution:', error)
  }
}

const loadChartData = async () => {
  try {
    const response = await analysisApi.getDistributionChart()
    chartData.value = response.data.distribution_bins || []
  } catch (error) {
    console.error('Failed to load chart data:', error)
  }
}

const loadSimilarPairs = async () => {
  try {
    const response = await analysisApi.getSimilarPairs(similarityThreshold.value, pairsLimit.value)
    similarPairs.value = response.data
  } catch (error) {
    console.error('Failed to load similar pairs:', error)
  }
}

const loadMergeSuggestions = async () => {
  try {
    const response = await analysisApi.getMergeSuggestions(autoMergeThreshold.value)
    mergeSuggestions.value = response.data
  } catch (error) {
    console.error('Failed to load merge suggestions:', error)
  }
}

const loadOrgSummary = async () => {
  try {
    const response = await analysisApi.getOrganizationSummary()
    orgSummary.value = response.data
  } catch (error) {
    console.error('Failed to load organization summary:', error)
  }
}

const loadSpaceData = async () => {
  try {
    const response = await analysisApi.getKnowledgeSpace()
    spaceData.value = response.data
    await nextTick()
    drawScatterPlot()
  } catch (error) {
    console.error('Failed to load space data:', error)
  }
}

const loadHeatmapData = async () => {
  try {
    const response = await analysisApi.getSimilarityHeatmap(heatmapMaxItems.value)
    heatmapData.value = response.data
    await nextTick()
    drawHeatmap()
  } catch (error) {
    console.error('Failed to load heatmap data:', error)
  }
}

const loadNetworkData = async () => {
  try {
    const response = await analysisApi.getSimilarityNetwork(networkThreshold.value)
    networkData.value = response.data
    initNetworkNodes()
    await nextTick()
    drawNetwork()
  } catch (error) {
    console.error('Failed to load network data:', error)
  }
}

const initNetworkNodes = () => {
  const canvas = networkCanvas.value
  if (!canvas) return
  
  const width = canvas.width
  const height = canvas.height
  
  networkNodes = networkData.value.nodes.map(node => ({
    ...node,
    x: Math.random() * width,
    y: Math.random() * height,
    vx: 0,
    vy: 0
  }))
}

const drawScatterPlot = () => {
  const canvas = scatterCanvas.value
  if (!canvas || !spaceData.value.points.length) return
  
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  
  ctx.clearRect(0, 0, width, height)
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--bg-secondary').trim() || '#f5f5f5'
  ctx.fillRect(0, 0, width, height)
  
  const points = spaceData.value.points.filter(p => !hiddenCatalogs.value.includes(p.catalog_id))
  if (points.length === 0) return
  
  let minX = Math.min(...points.map(p => p.x))
  let maxX = Math.max(...points.map(p => p.x))
  let minY = Math.min(...points.map(p => p.y))
  let maxY = Math.max(...points.map(p => p.y))
  
  const padding = 50
  const rangeX = maxX - minX || 1
  const rangeY = maxY - minY || 1
  
  const scale = Math.min((width - padding * 2) / rangeX, (height - padding * 2) / rangeY)
  
  ctx.save()
  ctx.translate(width / 2 + scatterOffsetX, height / 2 + scatterOffsetY)
  ctx.scale(scatterScale, scatterScale)
  
  points.forEach(point => {
    const x = (point.x - (minX + maxX) / 2) * scale
    const y = (point.y - (minY + maxY) / 2) * scale
    
    ctx.beginPath()
    ctx.arc(x, y, 6, 0, Math.PI * 2)
    ctx.fillStyle = point.color
    ctx.fill()
    
    ctx.strokeStyle = 'rgba(255,255,255,0.5)'
    ctx.lineWidth = 1
    ctx.stroke()
  })
  
  ctx.restore()
}

const drawHeatmap = () => {
  const canvas = heatmapCanvas.value
  if (!canvas || !heatmapData.value.matrix.length) return
  
  const ctx = canvas.getContext('2d')
  const matrix = heatmapData.value.matrix
  const n = matrix.length
  
  const cellSize = Math.min(600 / n, 20)
  const width = n * cellSize
  const height = n * cellSize
  
  canvas.width = width
  canvas.height = height
  
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      const sim = matrix[i][j]
      const hue = (1 - sim) * 240
      ctx.fillStyle = `hsl(${hue}, 80%, ${50 + sim * 20}%)`
      ctx.fillRect(j * cellSize, i * cellSize, cellSize - 1, cellSize - 1)
    }
  }
}

const drawNetwork = () => {
  const canvas = networkCanvas.value
  if (!canvas || !networkNodes.length) return
  
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  
  ctx.clearRect(0, 0, width, height)
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--bg-secondary').trim() || '#f5f5f5'
  ctx.fillRect(0, 0, width, height)
  
  ctx.save()
  ctx.translate(width / 2 + networkOffsetX, height / 2 + networkOffsetY)
  ctx.scale(networkScale, networkScale)
  
  const edges = networkData.value.edges
  const nodeMap = new Map(networkNodes.map(n => [n.id, n]))
  
  ctx.strokeStyle = 'rgba(100, 100, 100, 0.3)'
  ctx.lineWidth = 0.5
  edges.forEach(edge => {
    const source = nodeMap.get(edge.source)
    const target = nodeMap.get(edge.target)
    if (source && target) {
      ctx.beginPath()
      ctx.moveTo(source.x - width / 2, source.y - height / 2)
      ctx.lineTo(target.x - width / 2, target.y - height / 2)
      ctx.stroke()
    }
  })
  
  networkNodes.forEach(node => {
    const x = node.x - width / 2
    const y = node.y - height / 2
    
    ctx.beginPath()
    ctx.arc(x, y, node.size / 2, 0, Math.PI * 2)
    ctx.fillStyle = node.catalog_id ? getColorForCatalog(node.catalog_id) : '#999'
    ctx.fill()
    
    ctx.strokeStyle = 'rgba(255,255,255,0.5)'
    ctx.lineWidth = 1
    ctx.stroke()
  })
  
  ctx.restore()
}

const catalogColorMap = new Map()
const colorPalette = [
  '#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336',
  '#00BCD4', '#795548', '#607D8B', '#E91E63', '#3F51B5'
]
let colorIndex = 0

const getColorForCatalog = (catalogId) => {
  if (!catalogColorMap.has(catalogId)) {
    catalogColorMap.set(catalogId, colorPalette[colorIndex % colorPalette.length])
    colorIndex++
  }
  return catalogColorMap.get(catalogId)
}

let networkStableFrames = 0

const simulateNetwork = () => {
  const canvas = networkCanvas.value
  if (!canvas) return
  
  const width = canvas.width
  const height = canvas.height
  const centerX = width / 2
  const centerY = height / 2
  
  const edges = networkData.value.edges
  const nodeMap = new Map(networkNodes.map(n => [n.id, n]))
  let totalKineticEnergy = 0
  
  networkNodes.forEach(node => {
    node.vx += (centerX - node.x) * 0.001
    node.vy += (centerY - node.y) * 0.001
  })
  
  edges.forEach(edge => {
    const source = nodeMap.get(edge.source)
    const target = nodeMap.get(edge.target)
    if (!source || !target) return
    
    const dx = target.x - source.x
    const dy = target.y - source.y
    const dist = Math.sqrt(dx * dx + dy * dy) || 1
    const force = (dist - 100) * 0.01
    
    const fx = (dx / dist) * force
    const fy = (dy / dist) * force
    
    source.vx += fx
    source.vy += fy
    target.vx -= fx
    target.vy -= fy
  })
  
  networkNodes.forEach(n1 => {
    networkNodes.forEach(n2 => {
      if (n1 === n2) return
      const dx = n2.x - n1.x
      const dy = n2.y - n1.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      
      if (dist < 50) {
        const force = (50 - dist) * 0.05
        n1.vx -= (dx / dist) * force
        n1.vy -= (dy / dist) * force
      }
    })
  })
  
  networkNodes.forEach(node => {
    node.vx *= 0.9
    node.vy *= 0.9
    totalKineticEnergy += node.vx * node.vx + node.vy * node.vy
    node.x += node.vx
    node.y += node.vy
  })
  
  drawNetwork()
  
  if (totalKineticEnergy < 0.01) {
    networkStableFrames++
    if (networkStableFrames > 30) return
  } else {
    networkStableFrames = 0
  }
  
  requestAnimationFrame(simulateNetwork)
}

const toggleCatalog = (catalogId) => {
  const index = hiddenCatalogs.value.indexOf(catalogId)
  if (index === -1) {
    hiddenCatalogs.value.push(catalogId)
  } else {
    hiddenCatalogs.value.splice(index, 1)
  }
  drawScatterPlot()
}

const onScatterMouseDown = (e) => {
  isScatterDragging = true
  lastScatterX = e.clientX
  lastScatterY = e.clientY
}

const onScatterMouseMove = (e) => {
  const canvas = scatterCanvas.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  if (isScatterDragging) {
    scatterOffsetX += e.clientX - lastScatterX
    scatterOffsetY += e.clientY - lastScatterY
    lastScatterX = e.clientX
    lastScatterY = e.clientY
    drawScatterPlot()
  } else {
    const points = spaceData.value.points.filter(p => !hiddenCatalogs.value.includes(p.catalog_id))
    if (!points.length) return
    
    const width = canvas.width
    const height = canvas.height
    const padding = 50
    
    let minX = Math.min(...points.map(p => p.x))
    let maxX = Math.max(...points.map(p => p.x))
    let minY = Math.min(...points.map(p => p.y))
    let maxY = Math.max(...points.map(p => p.y))
    
    const rangeX = maxX - minX || 1
    const rangeY = maxY - minY || 1
    const scale = Math.min((width - padding * 2) / rangeX, (height - padding * 2) / rangeY)
    
    let found = null
    for (const point of points) {
      const x = width / 2 + scatterOffsetX + (point.x - (minX + maxX) / 2) * scale * scatterScale
      const y = height / 2 + scatterOffsetY + (point.y - (minY + maxY) / 2) * scale * scatterScale
      
      const dist = Math.sqrt((mouseX - x) ** 2 + (mouseY - y) ** 2)
      if (dist < 10) {
        found = point
        break
      }
    }
    
    hoveredPoint.value = found
    if (found) {
      tooltipStyle.value = {
        left: `${mouseX + 15}px`,
        top: `${mouseY + 15}px`
      }
    }
  }
}

const onScatterMouseUp = () => {
  isScatterDragging = false
}

const onScatterWheel = (e) => {
  e.preventDefault()
  const zoom = e.deltaY > 0 ? 0.9 : 1.1
  scatterScale = Math.max(0.1, Math.min(5, scatterScale * zoom))
  drawScatterPlot()
}

const onNetworkMouseDown = (e) => {
  isNetworkDragging = true
  lastNetworkX = e.clientX
  lastNetworkY = e.clientY
}

const onNetworkMouseMove = (e) => {
  const canvas = networkCanvas.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  if (isNetworkDragging) {
    networkOffsetX += e.clientX - lastNetworkX
    networkOffsetY += e.clientY - lastNetworkY
    lastNetworkX = e.clientX
    lastNetworkY = e.clientY
  } else {
    const width = canvas.width
    const height = canvas.height
    
    let found = null
    for (const node of networkNodes) {
      const x = width / 2 + networkOffsetX + (node.x - width / 2) * networkScale
      const y = height / 2 + networkOffsetY + (node.y - height / 2) * networkScale
      
      const dist = Math.sqrt((mouseX - x) ** 2 + (mouseY - y) ** 2)
      if (dist < node.size / 2 + 5) {
        found = node
        break
      }
    }
    
    hoveredNode.value = found
    if (found) {
      nodeTooltipStyle.value = {
        left: `${mouseX + 15}px`,
        top: `${mouseY + 15}px`
      }
    }
  }
}

const onNetworkMouseUp = () => {
  isNetworkDragging = false
}

const onNetworkWheel = (e) => {
  e.preventDefault()
  const zoom = e.deltaY > 0 ? 0.9 : 1.1
  networkScale = Math.max(0.1, Math.min(5, networkScale * zoom))
}

const refreshAll = async () => {
  loading.value = true
  try {
    await analysisApi.refreshCache()
    await Promise.all([
      loadDistribution(),
      loadChartData(),
      loadSimilarPairs(),
      loadMergeSuggestions(),
      loadOrgSummary(),
      loadSpaceData(),
      loadHeatmapData(),
      loadNetworkData()
    ])
  } finally {
    loading.value = false
  }
}

const getBarHeight = (count) => {
  const max = Math.max(...chartData.value.map(b => b.count), 1)
  return `${(count / max) * 100}%`
}

const mergeSingle = async (suggestion) => {
  merging.value = true
  try {
    await analysisApi.mergeKnowledge(
      suggestion.primary_id,
      suggestion.duplicate_ids,
      suggestion.merged_question,
      suggestion.merged_answer
    )
    await loadMergeSuggestions()
    await loadOrgSummary()
  } catch (error) {
    console.error('Failed to merge:', error)
  } finally {
    merging.value = false
  }
}

const autoMerge = async () => {
  merging.value = true
  try {
    for (const suggestion of mergeSuggestions.value) {
      await analysisApi.mergeKnowledge(
        suggestion.primary_id,
        suggestion.duplicate_ids,
        suggestion.merged_question,
        suggestion.merged_answer
      )
    }
    await loadMergeSuggestions()
    await loadOrgSummary()
  } finally {
    merging.value = false
  }
}

const autoOrganize = async () => {
  organizing.value = true
  organizeResult.value = null
  try {
    const response = await analysisApi.autoOrganize(
      autoMergeThreshold.value,
      maxItemsPerCatalog.value
    )
    organizeResult.value = response.data
    await refreshAll()
  } catch (error) {
    console.error('Failed to auto organize:', error)
  } finally {
    organizing.value = false
  }
}

const syncCatalogCounts = async () => {
  syncing.value = true
  syncResult.value = null
  try {
    const response = await analysisApi.syncCatalogCounts()
    syncResult.value = response.data
    await refreshAll()
  } catch (error) {
    console.error('Failed to sync catalog counts:', error)
  } finally {
    syncing.value = false
  }
}

const initCanvases = () => {
  if (scatterCanvas.value) {
    const parent = scatterCanvas.value.parentElement
    scatterCanvas.value.width = parent.clientWidth
    scatterCanvas.value.height = 500
  }
  if (heatmapCanvas.value) {
    heatmapCanvas.value.width = 600
    heatmapCanvas.value.height = 600
  }
  if (networkCanvas.value) {
    const parent = networkCanvas.value.parentElement
    networkCanvas.value.width = parent.clientWidth
    networkCanvas.value.height = 500
  }
}

watch(vizMode, async (newMode) => {
  await nextTick()
  initCanvases()
  if (newMode === 'scatter') {
    drawScatterPlot()
  } else if (newMode === 'heatmap') {
    drawHeatmap()
  } else if (newMode === 'network') {
    initNetworkNodes()
    simulateNetwork()
  }
})

watch(activeTab, async (newTab) => {
  if (newTab === 'space') {
    await nextTick()
    initCanvases()
    if (vizMode.value === 'scatter') {
      drawScatterPlot()
    } else if (vizMode.value === 'heatmap') {
      drawHeatmap()
    } else if (vizMode.value === 'network') {
      initNetworkNodes()
      simulateNetwork()
    }
  }
})

onMounted(async () => {
  await refreshAll()
  initCanvases()
  if (vizMode.value === 'scatter') {
    drawScatterPlot()
  }
})
</script>

<style scoped>
.analysis-view {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.card-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: var(--radius-lg);
}

.tab {
  flex: 1;
  padding: 12px 20px;
  text-align: center;
  cursor: pointer;
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.tab.active {
  background: var(--primary-color);
  color: white;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.visualization-controls {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.control-group select {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 13px;
}

.control-group input[type="range"] {
  width: 80px;
}

.visualization-container {
  min-height: 500px;
}

.scatter-view,
.heatmap-view,
.network-view {
  position: relative;
}

.scatter-canvas-wrapper,
.network-canvas-wrapper {
  position: relative;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.scatter-canvas-wrapper canvas,
.network-canvas-wrapper canvas {
  display: block;
  width: 100%;
  cursor: grab;
}

.scatter-canvas-wrapper canvas:active,
.network-canvas-wrapper canvas:active {
  cursor: grabbing;
}

.point-tooltip,
.node-tooltip {
  position: absolute;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px;
  max-width: 300px;
  box-shadow: var(--shadow-lg);
  z-index: 100;
  pointer-events: none;
}

.tooltip-catalog {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.tooltip-question {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.4;
}

.tooltip-degree {
  font-size: 12px;
  color: var(--primary-color);
  margin-top: 4px;
}

.scatter-legend {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.scatter-legend h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.legend-item:hover {
  background: var(--bg-hover);
}

.legend-item.dimmed {
  opacity: 0.3;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-name {
  font-size: 13px;
  color: var(--text-secondary);
}

.scatter-stats,
.network-stats {
  display: flex;
  gap: 24px;
  margin-top: 16px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-item .stat-label {
  font-size: 13px;
  color: var(--text-muted);
}

.stat-item .stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.heatmap-canvas-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.heatmap-canvas-wrapper canvas {
  border: 1px solid var(--border-light);
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.legend-gradient {
  width: 200px;
  height: 16px;
  background: linear-gradient(to right, hsl(240, 80%, 50%), hsl(120, 80%, 70%));
  border-radius: var(--radius-sm);
}

.legend-labels {
  display: flex;
  justify-content: space-between;
  width: 200px;
  font-size: 12px;
  color: var(--text-muted);
}

.heatmap-info {
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.threshold-control,
.limit-control {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.threshold-control input[type="range"] {
  width: 100px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.stat-card.highlight {
  background: linear-gradient(135deg, #FFF7E6 0%, #FFE7BA 100%);
  border: 1px solid #FFD591;
}

.stat-icon {
  font-size: 24px;
  margin-right: 12px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.distribution-chart {
  margin-bottom: 24px;
}

.distribution-chart h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.chart-container {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  height: 150px;
  gap: 4px;
}

.bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bar-wrapper {
  flex: 1;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: var(--primary-color);
  border-radius: 2px 2px 0 0;
  min-height: 2px;
  transition: height 0.3s ease;
}

.bar.highlight {
  background: #FA8C16;
}

.bar-label {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 4px;
}

.bar-count {
  font-size: 10px;
  color: var(--text-secondary);
}

.similar-pairs-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
  font-size: 14px;
}

.pairs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.pair-item {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 12px;
  border: 1px solid var(--border-light);
}

.pair-similarity {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.similarity-bar {
  height: 6px;
  background: var(--primary-color);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.similarity-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--primary-color);
  min-width: 45px;
}

.pair-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pair-question {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.4;
}

.pair-label {
  font-weight: 600;
  color: var(--text-secondary);
  margin-right: 4px;
}

.org-summary {
  margin-bottom: 24px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.summary-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 16px;
  text-align: center;
}

.summary-card.warning {
  background: linear-gradient(135deg, #FFF7E6 0%, #FFE7BA 100%);
}

.summary-card.danger {
  background: linear-gradient(135deg, #FFF1F0 0%, #FFCCC7 100%);
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.summary-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.merge-suggestions-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 20px;
}

.merge-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.merge-item {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 16px;
  border: 1px solid var(--border-light);
}

.merge-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.merge-badge {
  background: var(--primary-color);
  color: white;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
}

.merge-question {
  font-weight: 500;
  color: var(--text-primary);
}

.merge-duplicates {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 12px;
  border-left: 2px solid var(--border-light);
  margin-bottom: 12px;
}

.merge-dup {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.dup-similarity {
  background: #FFF7E6;
  color: #D46B08;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 500;
}

.merge-actions {
  display: flex;
  gap: 8px;
}

.auto-organize-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.auto-organize-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.section-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 16px;
}

.organize-controls {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.control-item input[type="range"] {
  width: 80px;
}

.control-item input[type="number"] {
  width: 60px;
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 13px;
  background: var(--bg-card);
  color: var(--text-primary);
}

.organize-result {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
}

.organize-result h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.sync-result {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
}

.sync-result h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.button-group {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.result-stats {
  display: flex;
  gap: 24px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.result-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-color);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-dark);
}

.btn-secondary {
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .organize-controls {
    flex-direction: column;
    gap: 12px;
  }
  
  .result-stats {
    flex-direction: column;
    gap: 8px;
  }
  
  .btn-text {
    display: none;
  }
  
  .visualization-controls {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
