import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function getRules() {
  return api.get('/rules')
}
