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

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            return
          }

          const text = decoder.decode(value, { stream: true })
          const lines = text.split('\n')

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

export default api
