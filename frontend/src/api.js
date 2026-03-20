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

  delete(id) {
    return api.delete(`/catalog/${id}`)
  }
}

export default api
