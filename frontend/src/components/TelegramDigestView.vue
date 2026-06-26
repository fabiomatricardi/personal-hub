<script setup>
import { ref, onMounted } from 'vue'
import { getSettings, getTelegramDigestStatus, runTelegramDigestNow, getTelegramDigestHistory } from '../composables/useApi.js'

const status = ref({})
const history = ref([])
const loading = ref(false)
const running = ref(false)
const result = ref(null)
const config = ref({})

onMounted(async () => {
  loading.value = true
  try {
    const [s, h, c] = await Promise.all([
      getTelegramDigestStatus(),
      getTelegramDigestHistory(),
      getSettings(),
    ])
    status.value = s
    history.value = h
    config.value = c
  } finally {
    loading.value = false
  }
})

async function runNow() {
  running.value = true
  result.value = null
  try {
    result.value = await runTelegramDigestNow()
    const s = await getTelegramDigestStatus()
    status.value = s
    const h = await getTelegramDigestHistory()
    history.value = h
  } catch (e) {
    result.value = { errors: [e.response?.data?.detail || e.message] }
  } finally {
    running.value = false
  }
}

function formatTimestamp(ts) {
  if (!ts) return 'Never'
  const d = new Date(ts)
  return d.toLocaleString()
}

function maskToken(token) {
  if (!token) return ''
  if (token.length <= 8) return '****'
  return token.slice(0, 4) + '****' + token.slice(-4)
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Telegram Digest</h2>
      <button @click="runNow" :disabled="running" class="btn-primary">
        <i v-if="running" class="pi pi-spin pi-spinner"></i>
        {{ running ? 'Running...' : 'Run Now' }}
      </button>
    </div>

    <div v-if="loading" class="loading-banner">
      <i class="pi pi-spin pi-spinner"></i> Loading...
    </div>

    <div class="config-card">
      <h3>Configuration</h3>
      <div class="config-grid">
        <div class="config-item">
          <span class="config-label">Bot Token</span>
          <span class="config-value" :class="config.telegram_bot_token ? 'configured' : 'not-configured'">
            {{ config.telegram_bot_token ? maskToken(config.telegram_bot_token) : 'Not configured' }}
          </span>
        </div>
        <div class="config-item">
          <span class="config-label">Gmail</span>
          <span class="config-value" :class="config.gmail_address ? 'configured' : 'not-configured'">
            {{ config.gmail_address || 'Not configured' }}
          </span>
        </div>
        <div class="config-item">
          <span class="config-label">Recipient</span>
          <span class="config-value" :class="config.recipient_email ? 'configured' : 'not-configured'">
            {{ config.recipient_email || 'Not configured' }}
          </span>
        </div>
        <div class="config-item">
          <span class="config-label">LLM Provider</span>
          <span class="config-value">
            {{ config.providers?.[config.digest_llm_provider || 0]?.name || 'Not configured' }}
          </span>
        </div>
        <div class="config-item">
          <span class="config-label">Cron Schedule</span>
          <span class="config-value">{{ config.digest_cron || 'Not set' }}</span>
        </div>
      </div>
    </div>

    <div class="status-card">
      <h3>Status</h3>
      <div class="status-grid">
        <div class="stat-item">
          <div class="stat-number">{{ status.messages_processed || 0 }}</div>
          <div class="stat-label">Messages Processed</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ status.emails_sent || 0 }}</div>
          <div class="stat-label">Emails Sent</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ formatTimestamp(status.last_run) }}</div>
          <div class="stat-label">Last Run</div>
        </div>
      </div>
    </div>

    <div v-if="result" class="result-card" :class="result.errors?.length ? 'error' : 'success'">
      <h3>Run Result</h3>
      <div class="result-grid">
        <div class="result-item">
          <span class="result-label">Messages Found</span>
          <span class="result-value">{{ result.messages_found ?? 0 }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Processed</span>
          <span class="result-value">{{ result.messages_processed ?? 0 }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">Emails Sent</span>
          <span class="result-value">{{ result.emails_sent ?? 0 }}</span>
        </div>
      </div>
      <div v-if="result.errors?.length" class="result-errors">
        <div v-for="(err, i) in result.errors" :key="i" class="error-item">
          <i class="pi pi-exclamation-circle"></i> {{ err }}
        </div>
      </div>
    </div>

    <div class="history-card">
      <h3>Run History</h3>
      <div v-if="history.length === 0" class="empty-state">No runs yet.</div>
      <table v-else class="history-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Found</th>
            <th>Processed</th>
            <th>Emails</th>
            <th>Errors</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(entry, i) in history.slice().reverse().slice(0, 20)" :key="i">
            <td>{{ formatTimestamp(entry.timestamp) }}</td>
            <td>{{ entry.messages_found ?? 0 }}</td>
            <td>{{ entry.messages_processed ?? 0 }}</td>
            <td>{{ entry.emails_sent ?? 0 }}</td>
            <td :class="{ 'has-errors': entry.errors?.length }">
              {{ entry.errors?.length || 0 }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.config-card,
.status-card,
.result-card,
.history-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
}

.config-card h3,
.status-card h3,
.result-card h3,
.history-card h3 {
  font-size: 0.9em;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 14px 0;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-label {
  font-size: 0.75em;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.config-value {
  font-size: 0.9em;
  color: var(--text-primary);
  word-break: break-all;
}

.config-value.configured {
  color: #4ade80;
}

.config-value.not-configured {
  color: var(--text-secondary);
  font-style: italic;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 1.4em;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 0.75em;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.result-card.success {
  border-color: #4ade80;
}

.result-card.error {
  border-color: var(--error);
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.result-item {
  text-align: center;
}

.result-label {
  display: block;
  font-size: 0.75em;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  margin-bottom: 4px;
}

.result-value {
  font-size: 1.2em;
  font-weight: 600;
  color: var(--text-primary);
}

.result-errors {
  border-top: 1px solid var(--border);
  padding-top: 12px;
}

.error-item {
  color: var(--error);
  font-size: 0.85em;
  padding: 4px 0;
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.empty-state {
  color: var(--text-secondary);
  text-align: center;
  padding: 24px;
  font-size: 0.9em;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85em;
}

.history-table th {
  text-align: left;
  padding: 8px 10px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  font-weight: 500;
  font-size: 0.85em;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.history-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
}

.history-table tbody tr:hover {
  background: var(--bg-secondary);
}

.history-table td.has-errors {
  color: var(--error);
  font-weight: 600;
}
</style>
