import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const queryRAG = async (query, nResults = 5, filters = null) => {
  try {
    const response = await api.post('/api/v1/query', {
      query,
      n_results: nResults,
      filters,
    })
    return response.data
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}

export const uploadDocument = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const response = await api.post('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  } catch (error) {
    console.error('Upload Error:', error)
    throw error
  }
}

export const getDocuments = async () => {
  try {
    const response = await api.get('/api/v1/documents/')
    return response.data
  } catch (error) {
    console.error('Get Documents Error:', error)
    throw error
  }
}

export default api
