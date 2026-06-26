<script setup>
import { ref, watch } from 'vue'
import { generateLinkCard, fetchMetadata } from '../composables/useApi.js'

const url = ref('')
const title = ref('')
const description = ref('')
const imageUrl = ref('')
const result = ref('')
const loading = ref(false)
const error = ref(null)
const copied = ref(false)
const fetchStatus = ref('')

let fetchTimeout = null
watch(url, (newUrl) => {
  if (fetchTimeout) clearTimeout(fetchTimeout)
  if (!newUrl || !newUrl.startsWith('http')) {
    fetchStatus.value = ''
    return
  }
  fetchTimeout = setTimeout(async () => {
    if (title.value || description.value || imageUrl.value) return
    fetchStatus.value = 'fetching'
    try {
      const meta = await fetchMetadata(newUrl)
      if (meta.title && !title.value) title.value = meta.title
      if (meta.description && !description.value) description.value = meta.description
      if (meta.image_url && !imageUrl.value) imageUrl.value = meta.image_url
      fetchStatus.value = meta.error ? 'error' : 'done'
    } catch (e) {
      fetchStatus.value = 'error'
    }
  }, 800)
})

async function handleGenerate() {
  loading.value = true
  error.value = null
  result.value = ''
  copied.value = false
  try {
    const data = await generateLinkCard({
      url: url.value,
      title: title.value,
      description: description.value,
      image_url: imageUrl.value,
    })
    result.value = data.html
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

async function copyHtml() {
  try {
    await navigator.clipboard.writeText(result.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch (e) {
    error.value = 'Failed to copy'
  }
}

function clear() {
  url.value = ''
  title.value = ''
  description.value = ''
  imageUrl.value = ''
  result.value = ''
  error.value = null
  fetchStatus.value = ''
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Link Card Creator</h2>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="form-grid">
      <div class="form-group">
        <label>
          URL *
          <span v-if="fetchStatus === 'fetching'" class="fetch-status">
            <i class="pi pi-spin pi-spinner"></i> Fetching metadata...
          </span>
          <span v-else-if="fetchStatus === 'done'" class="fetch-status done">
            <i class="pi pi-check"></i> Auto-filled
          </span>
        </label>
        <input v-model="url" type="url" placeholder="https://example.com" @keyup.enter="handleGenerate" />
      </div>

      <div class="form-group">
        <label>Title</label>
        <input v-model="title" type="text" placeholder="Page title (auto-filled from URL)" />
      </div>

      <div class="form-group">
        <label>Description</label>
        <input v-model="description" type="text" placeholder="Short description (auto-filled from URL)" />
      </div>

      <div class="form-group">
        <label>Image URL</label>
        <input v-model="imageUrl" type="url" placeholder="https://example.com/image.jpg (auto-filled from URL)" />
      </div>
    </div>

    <div class="form-actions">
      <button class="btn-primary" @click="handleGenerate" :disabled="loading || !url">
        {{ loading ? 'Generating...' : 'Generate Card' }}
      </button>
      <button class="btn-secondary" @click="clear">Clear</button>
    </div>

    <div v-if="result" class="result-section">
      <div class="result-header">
        <h3>Preview</h3>
        <button class="btn-small" @click="copyHtml">
          <i :class="copied ? 'pi pi-check' : 'pi pi-copy'"></i>
          {{ copied ? 'Copied!' : 'Copy HTML' }}
        </button>
      </div>
      <div class="card-preview" v-html="result"></div>
      <details class="html-source">
        <summary>HTML Source</summary>
        <pre><code>{{ result }}</code></pre>
      </details>
    </div>
  </div>
</template>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.form-grid .form-group:first-child {
  grid-column: 1 / -1;
}

.fetch-status {
  font-size: 0.75em;
  font-weight: 400;
  margin-left: 8px;
  color: var(--accent);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.fetch-status.done {
  color: var(--success);
}

.result-section {
  margin-top: 24px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.result-header h3 {
  font-size: 1em;
  font-weight: 600;
}

.btn-secondary {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
}

.btn-secondary:hover {
  background: var(--bg-secondary);
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

.card-preview {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 12px;
}

.html-source {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.html-source summary {
  padding: 10px 16px;
  cursor: pointer;
  font-size: 0.85em;
  color: var(--text-secondary);
}

.html-source pre {
  padding: 16px;
  overflow-x: auto;
  font-size: 0.8em;
  line-height: 1.5;
}

.html-source code {
  background: none;
  padding: 0;
}
</style>
