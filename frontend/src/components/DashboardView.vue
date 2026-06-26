<script setup>
import { ref, onMounted } from 'vue'
import { getDashboard, getSettings } from '../composables/useApi.js'

const apps = ref([])
const configValid = ref(false)
const loading = ref(true)

const emit = defineEmits(['navigate'])

onMounted(async () => {
  try {
    const data = await getDashboard()
    apps.value = data.apps
    configValid.value = data.config_valid
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const quickActions = [
  { label: 'Create Link Card', icon: 'pi-link', view: 'linkcard', needsConfig: false },
  { label: 'Generate Tweets', icon: 'pi-twitter', view: 'tweetgen', needsConfig: true },
  { label: 'Browse Wiki', icon: 'pi-book', view: 'wiki', needsConfig: false },
  { label: 'Run Digest Now', icon: 'pi-envelope', view: 'tg-digest', needsConfig: true },
  { label: 'Run Files Now', icon: 'pi-download', view: 'tg-files', needsConfig: true },
  { label: 'View Cron Jobs', icon: 'pi-calendar', view: 'cron', needsConfig: false },
]
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Dashboard</h2>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <template v-else>
      <div v-if="!configValid" class="config-banner">
        <i class="pi pi-exclamation-triangle"></i>
        <div>
          <strong>LLM not configured</strong>
          <p>Tweet Generator requires an API key. <span class="link" @click="emit('navigate', 'settings')">Go to Settings</span></p>
        </div>
      </div>

      <h3 class="section-title">Apps</h3>
      <div class="dashboard-grid">
        <div
          v-for="app in apps"
          :key="app.name"
          class="dashboard-card"
          @click="emit('navigate', app.name === 'Link Card' ? 'linkcard' : app.name === 'Tweet Gen' ? 'tweetgen' : app.name === 'Wiki' ? 'wiki' : app.name === 'TG Digest' ? 'tg-digest' : app.name === 'TG Files' ? 'tg-files' : 'cron')"
        >
          <div class="card-icon">
            <i :class="'pi ' + app.icon"></i>
          </div>
          <h3>{{ app.name }}</h3>
          <p>{{ app.description }}</p>
          <span class="status-badge" :class="{ warning: !configValid && (app.name === 'Tweet Gen' || app.name === 'TG Digest' || app.name === 'TG Files') }">
            {{ (app.name === 'Tweet Gen' || app.name === 'TG Digest' || app.name === 'TG Files') && !configValid ? 'Configure LLM' : app.status }}
          </span>
        </div>
      </div>

      <h3 class="section-title">Quick Actions</h3>
      <div class="quick-actions">
        <button
          v-for="action in quickActions"
          :key="action.view"
          class="quick-action-btn"
          :class="{ disabled: action.needsConfig && !configValid }"
          @click="action.needsConfig && !configValid ? emit('navigate', 'settings') : emit('navigate', action.view)"
        >
          <i :class="'pi ' + action.icon"></i>
          <span>{{ action.label }}</span>
          <i v-if="action.needsConfig && !configValid" class="pi pi-exclamation-circle"></i>
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.config-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid var(--warning);
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 24px;
  font-size: 0.9em;
}

.config-banner i {
  color: var(--warning);
  font-size: 1.4em;
}

.config-banner p {
  color: var(--text-secondary);
  margin-top: 2px;
  font-size: 0.9em;
}

.config-banner .link {
  color: var(--accent);
  cursor: pointer;
  text-decoration: underline;
}

.section-title {
  font-size: 0.85em;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  margin-top: 24px;
}

.quick-actions {
  display: flex;
  gap: 12px;
}

.quick-action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.15s;
}

.quick-action-btn:hover {
  border-color: var(--accent);
  background: var(--bg-secondary);
}

.quick-action-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quick-action-btn.disabled:hover {
  border-color: var(--border);
  background: var(--bg-card);
}

.quick-action-btn i:first-child {
  color: var(--accent);
  font-size: 1.1em;
}
</style>
