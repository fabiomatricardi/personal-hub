<script setup>
import { ref, onMounted, computed } from 'vue'
import { getWikiFiles, getWikiFile } from '../composables/useApi.js'
import { marked } from 'marked'

const files = ref([])
const selectedFile = ref('')
const content = ref('')
const loading = ref(true)
const loadingContent = ref(false)
const error = ref(null)
const search = ref('')

const filteredFiles = computed(() => {
  if (!search.value) return files.value
  const q = search.value.toLowerCase()
  return files.value.filter(f => f.title.toLowerCase().includes(q) || f.name.toLowerCase().includes(q))
})

const renderedContent = computed(() => marked(content.value))

onMounted(async () => {
  try {
    files.value = await getWikiFiles()
    if (files.value.length > 0) {
      await selectFile(files.value[0].name)
    }
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
})

async function selectFile(name) {
  selectedFile.value = name
  loadingContent.value = true
  error.value = null
  try {
    const data = await getWikiFile(name)
    content.value = data.content
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
    content.value = ''
  } finally {
    loadingContent.value = false
  }
}

async function refresh() {
  loading.value = true
  try {
    files.value = await getWikiFiles()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Command Wiki</h2>
      <button class="btn-small" @click="refresh">
        <i class="pi pi-refresh"></i> Refresh
      </button>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="loading" class="loading">Loading wiki files...</div>

    <div v-else class="wiki-layout">
      <div class="wiki-sidebar">
        <div class="search-box">
          <i class="pi pi-search"></i>
          <input v-model="search" type="text" placeholder="Search..." />
        </div>
        <div class="file-list">
          <button
            v-for="file in filteredFiles"
            :key="file.name"
            class="file-item"
            :class="{ active: selectedFile === file.name }"
            @click="selectFile(file.name)"
          >
            <i class="pi pi-file"></i>
            <span>{{ file.title }}</span>
          </button>
          <div v-if="filteredFiles.length === 0" class="empty-state">
            No wiki files found
          </div>
        </div>
      </div>

      <div class="wiki-content">
        <div v-if="loadingContent" class="loading">Loading...</div>
        <div v-else class="markdown-content" v-html="renderedContent"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wiki-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 120px);
}

.wiki-sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 12px;
}

.search-box i {
  color: var(--text-secondary);
  font-size: 0.85em;
}

.search-box input {
  background: none;
  border: none;
  color: var(--text-primary);
  outline: none;
  font-size: 0.85em;
  width: 100%;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 0.85em;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  width: 100%;
}

.file-item:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.file-item.active {
  background: var(--accent);
  color: white;
}

.file-item i {
  font-size: 0.8em;
}

.empty-state {
  color: var(--text-secondary);
  font-size: 0.85em;
  text-align: center;
  padding: 20px;
}

.wiki-content {
  flex: 1;
  overflow-y: auto;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 24px;
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
</style>
