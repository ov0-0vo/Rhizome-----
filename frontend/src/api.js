import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const chatApi = {
  send(message) {
    return api.post('/chat', { message })
  },

  sendStream(message, onChunk, onDone, onError) {
    const eventSource = new EventSource(`/api/chat/stream?message=${encodeURIComponent(message)}`, {
      withCredentials: true
    })

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'chunk') {
          onChunk(data.content)
        } else if (data.type === 'done') {
          onDone(data.metadata)
          eventSource.close()
        } else if (data.type === 'error') {
          onError(data.message)
          eventSource.close()
        }
      } catch (e) {
        console.error('Parse error:', e)
      }
    }

    eventSource.onerror = (error) => {
      onError('连接错误')
      eventSource.close()
    }

    return eventSource
  },

  sendStreamPost(message, onChunk, onDone, onError) {
    fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    }).then(response => {
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            if (onDone) onDone()
            return
          }

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === 'chunk') {
                  onChunk(data.content)
                } else if (data.type === 'done') {
                  onDone(data.metadata)
                } else if (data.type === 'error') {
                  onError(data.message)
                }
              } catch (e) {
                console.error('Parse error:', e)
              }
            }
          }

          read()
        })
      }

      read()
    }).catch(error => {
      onError(error.message)
    })
  },

  getHistory(limit = 20) {
    return api.get('/chat/history', { params: { limit } })
  }
}

export const knowledgeApi = {
  getAll() {
    return api.get('/knowledge')
  },

  getStatistics() {
    return api.get('/knowledge/statistics')
  },

  search(query, limit = 5) {
    return api.get('/knowledge/search', { params: { query, limit } })
  },

  getByCatalog(catalogId) {
    return api.get(`/knowledge/catalog/${catalogId}`)
  },

  getUncategorized() {
    return api.get('/knowledge/uncategorized')
  },

  getUncategorizedCount() {
    return api.get('/knowledge/uncategorized/count')
  },

  get(id) {
    return api.get(`/knowledge/${id}`)
  },

  create(data) {
    return api.post('/knowledge', data)
  },

  update(id, data) {
    return api.put(`/knowledge/${id}`, data)
  },

  delete(id) {
    return api.delete(`/knowledge/${id}`)
  }
}

export const catalogApi = {
  getTree() {
    return api.get('/catalog/tree')
  },

  getAll() {
    return api.get('/catalog')
  },

  create(data) {
    return api.post('/catalog', data)
  },

  update(id, data) {
    return api.put(`/catalog/${id}`, data)
  },

  delete(id) {
    return api.delete(`/catalog/${id}`)
  }
}

export const graphApi = {
  getGraph() {
    return api.get('/graph')
  },

  getKeywordNetwork(limit = 50) {
    return api.get('/graph/keywords', { params: { limit } })
  },

  getCatalogGraph(catalogId) {
    return api.get(`/graph/catalog/${catalogId}`)
  }
}

export const reviewApi = {
  getKnowledgeForReview(catalogId = null, includeReviewed = true) {
    return api.get('/review/knowledge', {
      params: { catalog_id: catalogId, include_reviewed: includeReviewed }
    })
  },

  getKnowledgeStats(knowledgeId) {
    return api.get(`/review/knowledge/${knowledgeId}/stats`)
  },

  generateQuiz(knowledgeId, quizType = 'multiple_choice', difficulty = 'medium', count = 3) {
    return api.post('/review/quiz/generate', {
      knowledge_id: knowledgeId,
      quiz_type: quizType,
      difficulty: difficulty,
      count: count
    })
  },

  generateQuizStream(knowledgeId, quizType = 'multiple_choice', difficulty = 'medium', count = 3, onEvent) {
    return new Promise((resolve, reject) => {
      fetch('/api/review/quiz/generate/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          knowledge_id: knowledgeId,
          quiz_type: quizType,
          difficulty: difficulty,
          count: count
        })
      }).then(response => {
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        const quizzes = []
        let buffer = ''

        function read() {
          reader.read().then(({ done, value }) => {
            if (done) {
              resolve(quizzes)
              return
            }

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const event = JSON.parse(line.slice(6))
                  
                  if (event.type === 'quiz') {
                    quizzes.push(event.quiz)
                  }
                  
                  if (onEvent) {
                    onEvent(event)
                  }
                } catch (e) {
                  console.error('Parse error:', e)
                }
              }
            }

            read()
          })
        }

        read()
      }).catch(error => {
        reject(error)
      })
    })
  },

  evaluateQuiz(quizToken, userAnswer) {
    return api.post('/review/quiz/evaluate', {
      quiz_id: quizToken,
      user_answer: userAnswer
    })
  },

  recordReview(knowledgeId, reviewMode, quizResults = [], reviewDuration = 0) {
    return api.post('/review/record', {
      knowledge_id: knowledgeId,
      review_mode: reviewMode,
      quiz_results: quizResults,
      review_duration: reviewDuration
    })
  },

  getCatalogStats(catalogId) {
    return api.get(`/review/catalog/${catalogId}/stats`)
  },

  getSchedule(days = 7) {
    return api.get('/review/schedule', { params: { days } })
  },

  getSummary() {
    return api.get('/review/summary')
  }
}

export const configApi = {
  get() {
    return api.get('/config')
  },

  update(config) {
    return api.put('/config', config)
  }
}

export const analysisApi = {
  getDistribution(threshold = 0.85) {
    return api.get('/analysis/distribution', { params: { threshold } })
  },

  getDistributionChart() {
    return api.get('/analysis/distribution/chart')
  },

  getSimilarPairs(threshold = 0.85, limit = 50) {
    return api.get('/analysis/similar-pairs', { params: { threshold, limit } })
  },

  getDuplicates(threshold = 0.90) {
    return api.get('/analysis/duplicates', { params: { threshold } })
  },

  getCatalogDistribution() {
    return api.get('/analysis/catalog-distribution')
  },

  getReorganizationSuggestions(maxItems = 20) {
    return api.get('/analysis/reorganization-suggestions', { params: { max_items: maxItems } })
  },

  getMergeSuggestions(threshold = 0.90) {
    return api.get('/analysis/merge-suggestions', { params: { threshold } })
  },

  mergeKnowledge(primaryId, duplicateIds, mergedQuestion = null, mergedAnswer = null) {
    return api.post('/analysis/merge', {
      primary_id: primaryId,
      duplicate_ids: duplicateIds,
      merged_question: mergedQuestion,
      merged_answer: mergedAnswer
    })
  },

  generateMergedContent(primaryId, duplicateIds) {
    return api.post('/analysis/generate-merged-content', {
      primary_id: primaryId,
      duplicate_ids: duplicateIds
    })
  },

  getCatalogSplitSuggestion(catalogId, maxItems = 20) {
    return api.get(`/analysis/catalog-split-suggestion/${catalogId}`, { params: { max_items: maxItems } })
  },

  splitCatalog(catalogId, subCatalogConfigs) {
    return api.post('/analysis/split-catalog', {
      catalog_id: catalogId,
      sub_catalog_configs: subCatalogConfigs
    })
  },

  autoOrganize(mergeThreshold = 0.90, maxItemsPerCatalog = 20) {
    return api.post('/analysis/auto-organize', {
      merge_threshold: mergeThreshold,
      max_items_per_catalog: maxItemsPerCatalog
    })
  },

  getOrganizationSummary() {
    return api.get('/analysis/organization-summary')
  },

  refreshCache() {
    return api.post('/analysis/refresh-cache')
  },

  getKnowledgeSpace() {
    return api.get('/analysis/knowledge-space')
  },

  getSimilarityHeatmap(maxItems = 50, clusterByCatalog = true) {
    return api.get('/analysis/similarity-heatmap', { 
      params: { max_items: maxItems, cluster_by_catalog: clusterByCatalog } 
    })
  },

  getSimilarityNetwork(threshold = 0.7, maxNodes = 100) {
    return api.get('/analysis/similarity-network', { 
      params: { threshold, max_nodes: maxNodes } 
    })
  },

  getKnowledgeClusters(nClusters = null) {
    return api.get('/analysis/knowledge-clusters', { 
      params: { n_clusters: nClusters } 
    })
  },

  syncCatalogCounts() {
    return api.post('/analysis/sync-catalog-counts')
  }
}

export const reflectionApi = {
  createSession(topic = '') {
    return api.post('/reflection/session', { topic })
  },

  getSession(sessionId) {
    return api.get(`/reflection/session/${sessionId}`)
  },

  deleteSession(sessionId) {
    return api.delete(`/reflection/session/${sessionId}`)
  },

  chatStream(sessionId, message, topic, onChunk, onDone, onError) {
    const body = JSON.stringify({
      session_id: sessionId,
      message,
      topic
    })
    
    console.log('[Reflection API] Starting stream request...')
    
    fetch('/api/reflection/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body
    }).then(response => {
      console.log('[Reflection API] Response received, status:', response.status)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            console.log('[Reflection API] Stream complete')
            onDone && onDone()
            return
          }
          
          const text = decoder.decode(value, { stream: true })
          console.log('[Reflection API] Raw chunk received:', text.substring(0, 100))
          
          buffer += text
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') {
                console.log('[Reflection API] Received [DONE]')
                onDone && onDone()
                return
              }
              try {
                const json = JSON.parse(data)
                if (json.content) {
                  console.log('[Reflection API] Content chunk:', json.content.substring(0, 50))
                  onChunk && onChunk(json.content)
                }
                if (json.session_id) {
                  console.log('[Reflection API] Session ID:', json.session_id)
                  onChunk && onChunk({ sessionId: json.session_id })
                }
              } catch (e) {
                console.error('[Reflection API] Parse error:', e, 'data:', data)
              }
            }
          }
          
          read()
        }).catch(err => {
          console.error('[Reflection API] Read error:', err)
          onError && onError(err)
        })
      }
      
      read()
    }).catch(err => {
      console.error('[Reflection API] Fetch error:', err)
      onError && onError(err)
    })
  },

  archive(sessionId, catalogId = null) {
    return api.post('/reflection/archive', {
      session_id: sessionId,
      catalog_id: catalogId
    })
  },

  archiveStream(sessionId, onSummary, onDone, onError) {
    console.log('[Reflection API] Starting archive stream request...')
    
    fetch('/api/reflection/archive/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId
      })
    }).then(response => {
      console.log('[Reflection API] Archive stream response, status:', response.status)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            console.log('[Reflection API] Archive stream complete')
            onDone && onDone()
            return
          }
          
          const text = decoder.decode(value, { stream: true })
          
          buffer += text
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') {
                console.log('[Reflection API] Archive received [DONE]')
                onDone && onDone()
                return
              }
              try {
                const json = JSON.parse(data)
                if (json.summary) {
                  onSummary && onSummary(json.summary)
                }
                if (json.done) {
                  const result = JSON.parse(json.done)
                  onSummary && onSummary({ done: result })
                }
                if (json.error) {
                  onError && onError(json.error)
                }
              } catch (e) {
                console.error('[Reflection API] Archive parse error:', e, 'data:', data)
              }
            }
          }
          
          read()
        }).catch(err => {
          console.error('[Reflection API] Archive read error:', err)
          onError && onError(err)
        })
      }
      
      read()
    }).catch(err => {
      console.error('[Reflection API] Archive fetch error:', err)
      onError && onError(err)
    })
  }
}

export const discoveryApi = {
  getHotspots(maxItems = 10) {
    return api.get('/discovery/hotspots', { params: { max_items: maxItems } })
  },

  getRecommendations() {
    return api.get('/discovery/recommendations')
  },

  getGaps() {
    return api.get('/discovery/gaps')
  },

  getSummary() {
    return api.get('/discovery/summary')
  },

  refreshCache() {
    return api.post('/discovery/refresh-cache')
  }
}

export const importApi = {
  importFile(file, options = {}) {
    const formData = new FormData()
    formData.append('file', file)
    if (options.catalog_id) {
      formData.append('catalog_id', options.catalog_id)
    }
    formData.append('auto_create_catalog', options.auto_create_catalog !== false)
    formData.append('use_llm_analysis', options.use_llm_analysis === true)
    
    return api.post('/import/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 120000
    })
  },

  importText(content, options = {}) {
    return api.post('/import/text', {
      content,
      catalog_id: options.catalog_id || null,
      split_by: options.split_by || 'paragraph'
    })
  }
}

export default api
