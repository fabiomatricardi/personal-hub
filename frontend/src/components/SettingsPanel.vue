<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { getSettings, saveSettings, testProvider } from '../composables/useApi.js'

const config = ref({})
const saving = ref(false)
const message = ref('')
const activeTab = ref(0)
const testResults = ref({})
const testing = ref(null)

const emit = defineEmits(['theme-changed'])

onMounted(async () => {
  config.value = await getSettings()
  activeTab.value = config.value.active_provider || 0
})

watch(() => config.value.card_theme, (newTheme) => {
  if (newTheme) {
    emit('theme-changed', newTheme)
  }
})

const activeProvider = computed(() => {
  return config.value.providers?.[activeTab.value] || {}
})

function addModel(idx) {
  const provider = config.value.providers?.[idx]
  if (provider && !provider.models) provider.models = []
  provider.models.push('')
}

function removeModel(idx, modelIdx) {
  config.value.providers[idx].models.splice(modelIdx, 1)
}

async function handleSave() {
  saving.value = true
  message.value = ''
  config.value.active_provider = activeTab.value
  try {
    const result = await saveSettings(config.value)
    config.value = result.config
    message.value = 'Settings saved'
  } catch (e) {
    message.value = 'Error: ' + (e.response?.data?.detail || e.message)
  } finally {
    saving.value = false
  }
}

async function handleTest(idx) {
  testing.value = idx
  testResults.value[idx] = null
  try {
    const result = await testProvider(idx)
    testResults.value[idx] = result
  } catch (e) {
    testResults.value[idx] = { ok: false, error: e.response?.data?.detail || e.message }
  } finally {
    testing.value = null
  }
}

function cronToHuman(expr) {
  if (!expr) return ''
  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5) return ''
  const [min, hour, day, month, dow] = parts
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  if (min === '*' && hour === '*' && day === '*' && month === '*' && dow === '*') return 'Every minute'
  if (min.startsWith('*/') && hour === '*') return `Every ${min.slice(2)} minutes`
  if (hour.startsWith('*/') && min === '0') return `Every ${hour.slice(2)} hours`
  let desc = 'At '
  if (min !== '*') desc += min.padStart(2, '0')
  if (hour !== '*') desc += `:${hour.padStart(2, '0')}`
  if (dow !== '*') {
    if (dow.includes('-')) {
      const [a, b] = dow.split('-')
      desc += ` on days ${a}-${b}`
    } else {
      desc += ` on ${days[parseInt(dow)] || dow}`
    }
  }
  if (day !== '*') desc += `, day ${day}`
  return desc
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Settings</h2>
    </div>

    <div class="settings-form">
      <div class="form-group">
        <label>App Name</label>
        <input v-model="config.app_name" type="text" />
      </div>

      <div class="section-divider">
        <h3>API Providers</h3>
        <p class="section-desc">Configure up to 2 LLM providers. The active provider is used by Tweet Generator.</p>
      </div>

      <div class="provider-tabs">
        <button
          v-for="(provider, i) in config.providers"
          :key="i"
          class="provider-tab"
          :class="{ active: activeTab === i }"
          @click="activeTab = i"
        >
          <span class="tab-dot" :class="{ filled: provider.api_key }"></span>
          {{ provider.name || `Provider ${i + 1}` }}
          <span v-if="activeTab === i" class="active-badge">active</span>
        </button>
      </div>

      <div v-for="(provider, i) in config.providers" :key="i" v-show="activeTab === i" class="provider-config">
        <div class="form-group">
          <label>Provider Name</label>
          <input v-model="provider.name" type="text" :placeholder="`Provider ${i + 1}`" />
        </div>

        <div class="form-group">
          <label>API Base URL</label>
          <input v-model="provider.base_url" type="text" placeholder="https://api.openai.com/v1" />
        </div>

        <div class="form-group">
          <label>API Key</label>
          <input v-model="provider.api_key" type="password" placeholder="sk-..." />
        </div>

        <div class="form-group">
          <label>Models (one per line)</label>
          <div class="models-list">
            <div v-for="(model, mi) in provider.models" :key="mi" class="model-row">
              <input v-model="provider.models[mi]" type="text" placeholder="model-name" />
              <button class="btn-icon-danger" @click="removeModel(i, mi)" title="Remove">
                <i class="pi pi-times"></i>
              </button>
            </div>
            <button class="btn-add" @click="addModel(i)">
              <i class="pi pi-plus"></i> Add Model
            </button>
          </div>
        </div>

        <div class="test-row">
          <button class="btn-test" @click="handleTest(i)" :disabled="testing === i || !provider.api_key || !provider.base_url">
            <i v-if="testing === i" class="pi pi-spin pi-spinner"></i>
            <i v-else class="pi pi-check-circle"></i>
            {{ testing === i ? 'Testing...' : 'Test Connection' }}
          </button>
          <span v-if="testResults[i]" class="test-result" :class="{ ok: testResults[i].ok, fail: !testResults[i].ok }">
            <i :class="testResults[i].ok ? 'pi pi-check' : 'pi pi-times'"></i>
            {{ testResults[i].ok ? `OK — ${testResults[i].model}: "${testResults[i].response}"` : testResults[i].error }}
          </span>
        </div>
      </div>

      <div class="section-divider" style="margin-top: 8px;">
        <h3>General</h3>
      </div>

      <div class="form-group">
        <label>Wiki Directory</label>
        <input v-model="config.wiki_dir" type="text" placeholder="./wiki/" />
      </div>

      <div class="form-group">
        <label>Theme</label>
        <select v-model="config.card_theme">
          <option value="dark">Dark</option>
          <option value="light">Light</option>
        </select>
      </div>

      <div class="section-divider">
        <h3>Telegram</h3>
        <p class="section-desc">Bot token for Telegram Digest and Telegram Files apps.</p>
      </div>

      <div class="form-group">
        <label>Bot Token</label>
        <input v-model="config.telegram_bot_token" type="password" placeholder="123456:ABC-DEF..." />
      </div>

      <div class="section-divider">
        <h3>Email (Gmail)</h3>
        <p class="section-desc">Gmail credentials for sending digest emails. Use a Gmail App Password.</p>
      </div>

      <div class="form-group">
        <label>Gmail Address</label>
        <input v-model="config.gmail_address" type="email" placeholder="you@gmail.com" />
      </div>

      <div class="form-group">
        <label>Gmail App Password</label>
        <input v-model="config.gmail_app_password" type="password" placeholder="xxxx-xxxx-xxxx-xxxx" />
      </div>

      <div class="form-group">
        <label>Recipient Email</label>
        <input v-model="config.recipient_email" type="email" placeholder="recipient@example.com" />
      </div>

      <div class="section-divider">
        <h3>Digest LLM</h3>
        <p class="section-desc">Provider and model used for generating Telegram message summaries.</p>
      </div>

      <div class="form-group">
        <label>LLM Provider</label>
        <select v-model.number="config.digest_llm_provider">
          <option v-for="(p, i) in config.providers" :key="i" :value="i">
            {{ p.name || `Provider ${i + 1}` }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label>Model</label>
        <input v-model="config.digest_llm_model" type="text" placeholder="Model name (uses first available if empty)" />
      </div>

      <div class="section-divider">
        <h3>Schedules</h3>
        <p class="section-desc">Cron expressions for automated tasks. Format: minute hour day month day_of_week</p>
      </div>

      <div class="form-group">
        <label>Daily Digest Cron</label>
        <input v-model="config.digest_cron" type="text" placeholder="0 8 * * *" />
        <span class="field-hint">{{ cronToHuman(config.digest_cron) }}</span>
      </div>

      <div class="form-group">
        <label>Weekly Digest Cron</label>
        <input v-model="config.weekly_digest_cron" type="text" placeholder="0 9 * * 1" />
        <span class="field-hint">{{ cronToHuman(config.weekly_digest_cron) }}</span>
      </div>

      <div class="form-group">
        <label>Files Check Cron</label>
        <input v-model="config.files_cron" type="text" placeholder="*/30 * * * *" />
        <span class="field-hint">{{ cronToHuman(config.files_cron) }}</span>
      </div>

      <div class="section-divider">
        <h3>Telegram Files</h3>
      </div>

      <div class="form-group">
        <label>Save Directory</label>
        <input v-model="config.telegram_files_dir" type="text" placeholder="./telegram_files/" />
      </div>

      <div class="form-actions">
        <button class="btn-primary" @click="handleSave" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Settings' }}
        </button>
        <span v-if="message" class="form-message" :class="{ error: message.startsWith('Error') }">
          {{ message }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-divider {
  margin: 8px 0 4px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.section-divider h3 {
  font-size: 0.95em;
  font-weight: 600;
  margin-bottom: 4px;
}

.section-desc {
  font-size: 0.8em;
  color: var(--text-secondary);
}

.provider-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.provider-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85em;
  transition: all 0.15s;
}

.provider-tab:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.provider-tab.active {
  border-color: var(--accent);
  background: rgba(59, 130, 246, 0.1);
  color: var(--accent);
}

.tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-secondary);
  flex-shrink: 0;
}

.tab-dot.filled {
  background: var(--success);
}

.active-badge {
  font-size: 0.7em;
  background: var(--accent);
  color: white;
  padding: 1px 6px;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.provider-config {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.models-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.model-row {
  display: flex;
  gap: 6px;
}

.model-row input {
  flex: 1;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 0.85em;
  outline: none;
}

.model-row input:focus {
  border-color: var(--accent);
}

.btn-icon-danger {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.btn-icon-danger:hover {
  color: var(--error);
  background: rgba(239, 68, 68, 0.1);
}

.btn-add {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: 1px dashed var(--border);
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8em;
  transition: all 0.15s;
}

.btn-add:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.test-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.btn-test {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8em;
  transition: all 0.15s;
  flex-shrink: 0;
}

.btn-test:hover:not(:disabled) {
  border-color: var(--success);
  color: var(--success);
}

.btn-test:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.test-result {
  font-size: 0.8em;
  display: flex;
  align-items: center;
  gap: 6px;
}

.test-result.ok {
  color: var(--success);
}

.test-result.fail {
  color: var(--error);
}

.field-hint {
  font-size: 0.75em;
  color: var(--text-secondary);
  font-style: italic;
}
</style>
