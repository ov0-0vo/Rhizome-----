<template>
  <div class="graph-view">
    <div class="graph-header">
      <h1>知识图谱</h1>
      <div class="graph-controls">
        <select v-model="viewMode" @change="loadGraph">
          <option value="full">完整图谱</option>
          <option value="keywords">关键词网络</option>
        </select>
        <button @click="resetZoom" class="btn-reset">重置视图</button>
      </div>
    </div>
    
    <div class="graph-container" ref="graphContainer">
      <canvas ref="canvas" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @wheel="onWheel"></canvas>
      
      <div v-if="selectedNode" class="node-info" :style="{ left: infoPos.x + 'px', top: infoPos.y + 'px' }">
        <div class="node-info-header">
          <span :class="['node-type', selectedNode.type]">{{ getTypeLabel(selectedNode.type) }}</span>
          <button @click="selectedNode = null" class="btn-close">&times;</button>
        </div>
        <div class="node-info-content">
          <h3>{{ selectedNode.label }}</h3>
          <p v-if="selectedNode.type === 'catalog'">知识条目: {{ selectedNode.size }}</p>
          <p v-if="selectedNode.type === 'keyword'">关联知识: {{ selectedNode.size }}</p>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
    
    <div v-if="error" class="error">
      {{ error }}
    </div>
    
    <div class="graph-legend">
      <div class="legend-item">
        <span class="legend-color catalog"></span>
        <span>知识目录</span>
      </div>
      <div class="legend-item">
        <span class="legend-color knowledge"></span>
        <span>知识条目</span>
      </div>
      <div class="legend-item">
        <span class="legend-color keyword"></span>
        <span>关键词</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { graphApi } from '../api.js'

const graphContainer = ref(null)
const canvas = ref(null)
const viewMode = ref('full')
const loading = ref(false)
const error = ref(null)
const selectedNode = ref(null)
const infoPos = ref({ x: 0, y: 0 })

let ctx = null
let nodes = []
let edges = []
let animationId = null
let scale = 1
let offsetX = 0
let offsetY = 0
let isDragging = false
let dragNode = null
let lastMouseX = 0
let lastMouseY = 0

const colors = {
  catalog: '#4CAF50',
  knowledge: '#2196F3',
  keyword: '#FF9800'
}

onMounted(() => {
  initCanvas()
  loadGraph()
  window.addEventListener('resize', resizeCanvas)
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  window.removeEventListener('resize', resizeCanvas)
})

function initCanvas() {
  const container = graphContainer.value
  const cvs = canvas.value
  if (!container || !cvs) return
  
  cvs.width = container.clientWidth
  cvs.height = container.clientHeight
  ctx = cvs.getContext('2d')
}

function resizeCanvas() {
  initCanvas()
}

async function loadGraph() {
  loading.value = true
  error.value = null
  selectedNode.value = null
  
  try {
    let response
    if (viewMode.value === 'keywords') {
      response = await graphApi.getKeywordNetwork(50)
      nodes = response.data.nodes.map(n => ({
        ...n,
        x: Math.random() * (canvas.value?.width || 800),
        y: Math.random() * (canvas.value?.height || 600),
        vx: 0,
        vy: 0
      }))
      edges = response.data.edges.map(e => ({
        source: nodes.find(n => n.id === e.source),
        target: nodes.find(n => n.id === e.target),
        weight: e.weight
      }))
    } else {
      response = await graphApi.getGraph()
      nodes = response.data.nodes.map(n => ({
        ...n,
        x: Math.random() * (canvas.value?.width || 800),
        y: Math.random() * (canvas.value?.height || 600),
        vx: 0,
        vy: 0
      }))
      edges = response.data.edges.map(e => ({
        source: nodes.find(n => n.id === e.source),
        target: nodes.find(n => n.id === e.target),
        type: e.type,
        weight: e.weight || 1
      }))
    }
    
    resetZoom()
    startSimulation()
  } catch (e) {
    error.value = '加载知识图谱失败: ' + e.message
  } finally {
    loading.value = false
  }
}

function startSimulation() {
  const centerX = (canvas.value?.width || 800) / 2
  const centerY = (canvas.value?.height || 600) / 2
  
  function simulate() {
    nodes.forEach(node => {
      node.vx += (centerX - node.x) * 0.001
      node.vy += (centerY - node.y) * 0.001
    })
    
    edges.forEach(edge => {
      if (!edge.source || !edge.target) return
      
      const dx = edge.target.x - edge.source.x
      const dy = edge.target.y - edge.source.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = (dist - 150) * 0.01 * edge.weight
      
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      
      edge.source.vx += fx
      edge.source.vy += fy
      edge.target.vx -= fx
      edge.target.vy -= fy
    })
    
    nodes.forEach(n1 => {
      nodes.forEach(n2 => {
        if (n1 === n2) return
        
        const dx = n2.x - n1.x
        const dy = n2.y - n1.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        
        if (dist < 100) {
          const force = (100 - dist) * 0.05
          n1.vx -= (dx / dist) * force
          n1.vy -= (dy / dist) * force
        }
      })
    })
    
    nodes.forEach(node => {
      node.vx *= 0.9
      node.vy *= 0.9
      node.x += node.vx
      node.y += node.vy
    })
    
    draw()
    animationId = requestAnimationFrame(simulate)
  }
  
  simulate()
}

function draw() {
  if (!ctx || !canvas.value) return
  
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  ctx.save()
  ctx.translate(offsetX, offsetY)
  ctx.scale(scale, scale)
  
  ctx.strokeStyle = '#e0e0e0'
  ctx.lineWidth = 1 / scale
  edges.forEach(edge => {
    if (!edge.source || !edge.target) return
    
    ctx.beginPath()
    ctx.moveTo(edge.source.x, edge.source.y)
    ctx.lineTo(edge.target.x, edge.target.y)
    
    if (edge.type === 'parent-child') {
      ctx.strokeStyle = '#81C784'
    } else if (edge.type === 'contains') {
      ctx.strokeStyle = '#90CAF9'
    } else if (edge.type === 'has-keyword') {
      ctx.strokeStyle = '#FFCC80'
      ctx.setLineDash([5, 5])
    } else {
      ctx.strokeStyle = '#e0e0e0'
    }
    
    ctx.stroke()
    ctx.setLineDash([])
  })
  
  nodes.forEach(node => {
    const radius = Math.max(5, node.size / 2)
    
    ctx.beginPath()
    ctx.arc(node.x, node.y, radius, 0, Math.PI * 2)
    ctx.fillStyle = colors[node.type] || '#999'
    ctx.fill()
    
    if (node === selectedNode.value) {
      ctx.strokeStyle = '#333'
      ctx.lineWidth = 3 / scale
      ctx.stroke()
    }
    
    ctx.fillStyle = '#333'
    ctx.font = `${12 / scale}px sans-serif`
    ctx.textAlign = 'center'
    ctx.fillText(node.label, node.x, node.y + radius + 15 / scale)
  })
  
  ctx.restore()
}

function onMouseDown(e) {
  const rect = canvas.value.getBoundingClientRect()
  const x = (e.clientX - rect.left - offsetX) / scale
  const y = (e.clientY - rect.top - offsetY) / scale
  
  dragNode = nodes.find(node => {
    const dx = node.x - x
    const dy = node.y - y
    return Math.sqrt(dx * dx + dy * dy) < node.size / 2 + 5
  })
  
  if (dragNode) {
    isDragging = true
    selectedNode.value = dragNode
    infoPos.value = { x: e.clientX + 10, y: e.clientY + 10 }
  } else {
    isDragging = true
    lastMouseX = e.clientX
    lastMouseY = e.clientY
  }
}

function onMouseMove(e) {
  if (!isDragging) return
  
  if (dragNode) {
    const rect = canvas.value.getBoundingClientRect()
    dragNode.x = (e.clientX - rect.left - offsetX) / scale
    dragNode.y = (e.clientY - rect.top - offsetY) / scale
    dragNode.vx = 0
    dragNode.vy = 0
  } else {
    offsetX += e.clientX - lastMouseX
    offsetY += e.clientY - lastMouseY
    lastMouseX = e.clientX
    lastMouseY = e.clientY
  }
}

function onMouseUp() {
  isDragging = false
  dragNode = null
}

function onWheel(e) {
  e.preventDefault()
  const rect = canvas.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  const zoom = e.deltaY > 0 ? 0.9 : 1.1
  const newScale = Math.max(0.1, Math.min(3, scale * zoom))
  
  offsetX = mouseX - (mouseX - offsetX) * (newScale / scale)
  offsetY = mouseY - (mouseY - offsetY) * (newScale / scale)
  scale = newScale
}

function resetZoom() {
  scale = 1
  offsetX = 0
  offsetY = 0
}

function getTypeLabel(type) {
  const labels = {
    catalog: '目录',
    knowledge: '知识',
    keyword: '关键词'
  }
  return labels[type] || type
}
</script>

<style scoped>
.graph-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.graph-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.graph-controls {
  display: flex;
  gap: 12px;
}

.graph-controls select {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.btn-reset {
  padding: 8px 16px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-reset:hover {
  background: #1976D2;
}

.graph-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
  cursor: grab;
}

canvas:active {
  cursor: grabbing;
}

.node-info {
  position: fixed;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 12px 16px;
  min-width: 200px;
  max-width: 300px;
  z-index: 100;
}

.node-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.node-type {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: white;
}

.node-type.catalog {
  background: #4CAF50;
}

.node-type.knowledge {
  background: #2196F3;
}

.node-type.keyword {
  background: #FF9800;
}

.btn-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #999;
}

.btn-close:hover {
  color: #333;
}

.node-info-content h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
  word-break: break-word;
}

.node-info-content p {
  margin: 0;
  font-size: 12px;
  color: #666;
}

.loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e0e0e0;
  border-top-color: #2196F3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #ffebee;
  color: #c62828;
  padding: 16px 24px;
  border-radius: 8px;
}

.graph-legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-color.catalog {
  background: #4CAF50;
}

.legend-color.knowledge {
  background: #2196F3;
}

.legend-color.keyword {
  background: #FF9800;
}
</style>
