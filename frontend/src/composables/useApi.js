import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export async function getSettings() {
  const { data } = await api.get('/settings')
  return data
}

export async function saveSettings(config) {
  const { data } = await api.post('/settings', config)
  return data
}

export async function testProvider(providerIndex, model) {
  const { data } = await api.post('/settings/test-provider', { provider_index: providerIndex, model })
  return data
}

export async function getDashboard() {
  const { data } = await api.get('/dashboard')
  return data
}

export async function generateLinkCard(payload) {
  const { data } = await api.post('/linkcard/generate', payload)
  return data
}

export async function fetchMetadata(url) {
  const { data } = await api.post('/linkcard/fetch-metadata', { url })
  return data
}

export async function getWikiFiles() {
  const { data } = await api.get('/wiki/files')
  return data
}

export async function getWikiFile(name) {
  const { data } = await api.get(`/wiki/file/${encodeURIComponent(name)}`)
  return data
}

export async function parseFile(fileName) {
  const { data } = await api.post('/tweetgen/parse', { file_name: fileName })
  return data
}

export async function generateTweets(payload) {
  const { data } = await api.post('/tweetgen/generate', payload)
  return data
}

export async function* streamChat(messages, context, providerIndex, model) {
  const response = await fetch('/api/tweetgen/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, context, provider_index: providerIndex, model }),
  })
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        yield data
      }
    }
  }
}

export async function getTelegramDigestStatus() {
  const { data } = await api.get('/telegram-digest/status')
  return data
}

export async function runTelegramDigestNow() {
  const { data } = await api.post('/telegram-digest/run-now')
  return data
}

export async function getTelegramDigestHistory() {
  const { data } = await api.get('/telegram-digest/history')
  return data
}

export async function getTelegramFilesStatus() {
  const { data } = await api.get('/telegram-files/status')
  return data
}

export async function runTelegramFilesNow() {
  const { data } = await api.post('/telegram-files/run-now')
  return data
}

export async function getTelegramFilesHistory() {
  const { data } = await api.get('/telegram-files/history')
  return data
}

export async function getTelegramFilesList() {
  const { data } = await api.get('/telegram-files/list')
  return data
}

export async function getCronJobs() {
  const { data } = await api.get('/cron/jobs')
  return data
}

export async function updateCronJob(jobId, payload) {
  const { data } = await api.post(`/cron/jobs/${encodeURIComponent(jobId)}/update`, payload)
  return data
}

export async function runCronJobNow(jobId) {
  const { data } = await api.post(`/cron/jobs/${encodeURIComponent(jobId)}/run-now`)
  return data
}

export async function getCronJobHistory(jobId) {
  const { data } = await api.get(`/cron/jobs/${encodeURIComponent(jobId)}/history`)
  return data
}

export async function shutdownApp() {
  await api.post('/shutdown')
}
