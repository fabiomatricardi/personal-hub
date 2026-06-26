<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { getSettings, parseFile, generateTweets, streamChat } from '../composables/useApi.js'

const inputText = ref('')
const tweets = ref([])
const chatMessages = ref([])
const chatInput = ref('')
const chatContext = ref('')
const loading = ref(false)
const parsing = ref(false)
const chatLoading = ref(false)
const error = ref(null)
const warning = ref(null)
const chatContainer = ref(null)
const activeTab = ref('input')
const config = ref({})
const selectedProvider = ref(0)
const selectedModel = ref('')

onMounted(async () => {
  config.value = await getSettings()
  selectedProvider.value = config.value.active_provider || 0
  const models = activeProvider.value?.models || []
  if (models.length > 0) selectedModel.value = models[0]
})

const activeProvider = computed(() => {
  return config.value.providers?.[selectedProvider.value] || {}
})

const availableModels = computed(() => {
  return activeProvider.value?.models || []
})

function onProviderChange() {
  const models = activeProvider.value?.models || []
  selectedModel.value = models.length > 0 ? models[0] : ''
}

async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  parsing.value = true
  error.value = null
  try {
    const formData = new FormData()
    formData.append('file', file)
    const resp = await fetch('/api/tweetgen/upload', { method: 'POST', body: formData })
    const data = await resp.json()

    const result = await parseFile(data.filename)
    inputText.value = result.text
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    parsing.value = false
  }
}

async function handleGenerate() {
  if (!inputText.value.trim()) return
  loading.value = true
  error.value = null
  warning.value = null
  try {
    const result = await generateTweets({
      text: inputText.value,
      file_name: '',
      provider_index: selectedProvider.value,
      model: selectedModel.value || undefined,
    })
    tweets.value = result.tweets
    warning.value = result.warning || null
    chatContext.value = inputText.value
    activeTab.value = 'result'
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

async function handleChat() {
  if (!chatInput.value.trim() || chatLoading.value) return
  const userMsg = chatInput.value.trim()
  chatInput.value = ''
  chatMessages.value.push({ role: 'user', content: userMsg })
  chatLoading.value = true
  error.value = null

  await nextTick()
  scrollChat()

  let assistantMsg = ''
  chatMessages.value.push({ role: 'assistant', content: '' })

  try {
    const stream = streamChat(
      chatMessages.value.slice(0, -1),
      chatContext.value,
      selectedProvider.value,
      selectedModel.value || undefined,
    )
    for await (const chunk of stream) {
      if (chunk.error) {
        error.value = chunk.error
        break
      }
      if (chunk.done) break
      if (chunk.content) {
        assistantMsg += chunk.content
        chatMessages.value[chatMessages.value.length - 1].content = assistantMsg
        await nextTick()
        scrollChat()
      }
    }
  } catch (e) {
    error.value = e.message
    chatMessages.value.pop()
  } finally {
    chatLoading.value = false
  }
}

function scrollChat() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

function copyTweet(tweet) {
  navigator.clipboard.writeText(tweet)
}

function copyAll() {
  navigator.clipboard.writeText(tweets.value.join('\n\n---\n\n'))
}

function saveChatAsMarkdown() {
  let md = '# Tweet Generator Chat\n\n'
  md += `**Provider:** ${activeProvider.value.name || 'N/A'}  \n`
  md += `**Model:** ${selectedModel.value || 'N/A'}  \n`
  md += `**Date:** ${new Date().toLocaleString()}\n\n---\n\n`

  if (tweets.value.length > 0) {
    md += '## Generated Tweets\n\n'
    tweets.value.forEach((t, i) => {
      md += `### Tweet ${i + 1}/${tweets.value.length}\n${t}\n\n`
    })
    md += '---\n\n'
  }

  if (chatMessages.value.length > 0) {
    md += '## Chat History\n\n'
    for (const msg of chatMessages.value) {
      const role = msg.role === 'user' ? '**You**' : '**AI**'
      md += `${role}:\n${msg.content}\n\n`
    }
  }

  const blob = new Blob([md], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `tweetgen-chat-${Date.now()}.md`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Tweet Generator</h2>
      <div class="provider-selector">
        <select v-model="selectedProvider" @change="onProviderChange">
          <option v-for="(p, i) in config.providers" :key="i" :value="i">
            {{ p.name || `Provider ${i + 1}` }}
          </option>
        </select>
        <select v-model="selectedModel" v-if="availableModels.length > 0">
          <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
        </select>
        <span v-else class="no-models">No models configured</span>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="loading" class="loading-banner">
      <i class="pi pi-spin pi-spinner"></i> Generating tweets...
    </div>

    <div class="tabs">
      <button :class="{ active: activeTab === 'input' }" @click="activeTab = 'input'">
        <i class="pi pi-pencil"></i> Input
      </button>
      <button :class="{ active: activeTab === 'result' }" @click="activeTab = 'result'" :disabled="tweets.length === 0">
        <i class="pi pi-list"></i> Tweets ({{ tweets.length }})
      </button>
      <button :class="{ active: activeTab === 'chat' }" @click="activeTab = 'chat'">
        <i class="pi pi-comments"></i> Chat
      </button>
    </div>

    <!-- Input Tab -->
    <div v-if="activeTab === 'input'" class="tab-content">
      <div class="input-section">
        <div class="form-group">
          <label class="form-label-row">
            <span>Paste text or upload a file</span>
            <span v-if="parsing" class="spinner-inline"><i class="pi pi-spin pi-spinner"></i> Parsing file...</span>
          </label>
          <textarea
            v-model="inputText"
            rows="12"
            placeholder="Paste your article or text here...&#10;&#10;Supports: plain text, markdown, or upload PDF/docx/excel files.&#10;After uploading, the converted text will appear here for you to review before generating."
          ></textarea>
        </div>

        <div class="form-actions">
          <button class="btn-primary" @click="handleGenerate" :disabled="loading || !inputText.trim() || parsing">
            <i v-if="loading" class="pi pi-spin pi-spinner"></i>{{ loading ? ' Generating...' : 'Generate Tweets' }}
          </button>
          <label class="btn-secondary" :class="{ disabled: parsing }">
            <i v-if="parsing" class="pi pi-spin pi-spinner"></i>
            <i v-else class="pi pi-upload"></i>
            {{ parsing ? 'Parsing...' : 'Upload File' }}
            <input type="file" accept=".md,.txt,.pdf,.docx,.xlsx,.xls" @change="handleFileUpload" hidden :disabled="parsing" />
          </label>
        </div>
      </div>
    </div>

    <!-- Result Tab -->
    <div v-if="activeTab === 'result'" class="tab-content">
      <div v-if="tweets.length === 0" class="empty-state">
        No tweets generated yet. Go to Input to generate some.
      </div>
      <div v-else>
        <div v-if="warning" class="warning-banner">
          <i class="pi pi-exclamation-triangle"></i> {{ warning }}
        </div>
        <div class="result-actions">
          <button class="btn-small" @click="copyAll">
            <i class="pi pi-copy"></i> Copy All
          </button>
        </div>
        <div class="tweet-list">
          <div v-for="(tweet, i) in tweets" :key="i" class="tweet-card">
            <div class="tweet-number">{{ i + 1 }}/{{ tweets.length }}</div>
            <div class="tweet-text">{{ tweet }}</div>
            <div class="tweet-footer">
              <span class="char-count" :class="{ over: tweet.length > 280 }">
                {{ tweet.length }}/280
              </span>
              <button class="btn-icon" @click="copyTweet(tweet)" title="Copy">
                <i class="pi pi-copy"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Tab -->
    <div v-if="activeTab === 'chat'" class="tab-content chat-tab">
      <div class="chat-messages" ref="chatContainer">
        <div v-if="chatMessages.length === 0" class="empty-state">
          Ask follow-up questions about your tweets. For example: "Make the first tweet more punchy" or "Add more hashtags".
        </div>
        <div v-for="(msg, i) in chatMessages" :key="i" class="chat-msg" :class="msg.role">
          <div class="msg-role">{{ msg.role === 'user' ? 'You' : 'AI' }}</div>
          <div class="msg-content">{{ msg.content }}</div>
        </div>
        <div v-if="chatLoading" class="chat-msg assistant">
          <div class="msg-role">AI</div>
          <div class="msg-content typing">Thinking...</div>
        </div>
      </div>
      <div class="chat-footer">
        <div class="chat-actions">
          <button
            class="btn-small"
            @click="saveChatAsMarkdown"
            :disabled="chatMessages.length === 0 && tweets.length === 0"
          >
            <i class="pi pi-download"></i> Save Chat
          </button>
        </div>
        <div class="chat-input">
          <input
            v-model="chatInput"
            type="text"
            placeholder="Ask about your tweets..."
            @keyup.enter="handleChat"
            :disabled="chatLoading"
          />
          <button class="btn-primary" @click="handleChat" :disabled="chatLoading || !chatInput.trim()">
            <i class="pi pi-send"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.provider-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.provider-selector select {
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.8em;
  outline: none;
}

.provider-selector select:focus {
  border-color: var(--accent);
}

.no-models {
  font-size: 0.8em;
  color: var(--text-secondary);
  font-style: italic;
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0;
}

.tabs button {
  padding: 10px 16px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.85em;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.15s;
}

.tabs button:hover {
  color: var(--text-primary);
}

.tabs button.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.tabs button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.tab-content {
  min-height: 400px;
}

.form-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.spinner-inline {
  font-size: 0.8em;
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 6px;
}

textarea {
  width: 100%;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 12px;
  border-radius: 8px;
  font-family: inherit;
  font-size: 0.9em;
  resize: vertical;
  outline: none;
  line-height: 1.6;
}

textarea:focus {
  border-color: var(--accent);
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-actions {
  margin-bottom: 12px;
  display: flex;
  justify-content: flex-end;
}

.tweet-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tweet-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
}

.tweet-number {
  font-size: 0.75em;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.tweet-text {
  font-size: 0.95em;
  line-height: 1.5;
  white-space: pre-wrap;
  margin-bottom: 8px;
}

.tweet-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.char-count {
  font-size: 0.75em;
  color: var(--text-secondary);
}

.char-count.over {
  color: var(--error);
  font-weight: 600;
}

.btn-icon {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.btn-icon:hover {
  color: var(--accent);
  background: var(--bg-secondary);
}

.empty-state {
  color: var(--text-secondary);
  text-align: center;
  padding: 40px 20px;
  font-size: 0.9em;
}

.warning-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid var(--warning);
  color: var(--warning);
  padding: 10px 14px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 0.85em;
}

.loading-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid var(--accent);
  color: var(--accent);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 0.95em;
}

.btn-secondary {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-secondary:hover:not(.disabled) {
  background: var(--bg-secondary);
}

.btn-secondary.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Chat */
.chat-tab {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  padding-bottom: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px 10px 0 0;
}

.chat-footer {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-top: none;
  border-radius: 0 0 10px 10px;
}

.chat-actions {
  padding: 8px 12px 0;
  display: flex;
  justify-content: flex-end;
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px;
}

.chat-input input {
  flex: 1;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 10px 14px;
  border-radius: 6px;
  outline: none;
  font-size: 0.9em;
}

.chat-input input:focus {
  border-color: var(--accent);
}

.chat-input .btn-primary {
  padding: 10px 14px;
}

.chat-msg {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 0.9em;
  line-height: 1.5;
  white-space: pre-wrap;
}

.chat-msg.user {
  align-self: flex-end;
  background: var(--accent);
  color: white;
  border-bottom-right-radius: 2px;
}

.chat-msg.assistant {
  align-self: flex-start;
  background: var(--bg-secondary);
  border-bottom-left-radius: 2px;
}

.msg-role {
  font-size: 0.7em;
  color: var(--text-secondary);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.chat-msg.user .msg-role {
  color: rgba(255,255,255,0.7);
}

.typing {
  color: var(--text-secondary);
  font-style: italic;
}

.btn-small {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8em;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-small:hover {
  background: var(--bg-secondary);
}

.btn-small:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
