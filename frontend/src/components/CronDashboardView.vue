<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Cron Dashboard</h2>
      <button @click="refreshJobs" class="btn-secondary">
        <i class="pi pi-refresh"></i> Refresh
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <i class="pi pi-spin pi-spinner"></i> Loading jobs...
    </div>

    <div v-else class="jobs-table-wrapper">
      <table class="jobs-table">
        <thead>
          <tr>
            <th>App</th>
            <th>Job Name</th>
            <th>Schedule</th>
            <th>Status</th>
            <th>Last Run</th>
            <th>Total Runs</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="job in jobs" :key="job.job_id" class="job-row">
            <td class="app-cell">
              <span class="app-icon" :class="'app-' + job.app">
                <i class="pi" :class="appIcon(job.app)"></i>
              </span>
              {{ job.app }}
            </td>
            <td class="job-name">{{ job.name }}</td>
            <td class="schedule-cell">
              <code class="cron-expr">{{ job.cron_expression }}</code>
              <span class="cron-human" :title="job.cron_expression">{{ cronToHuman(job.cron_expression) }}</span>
            </td>
            <td class="status-cell">
              <span :class="['badge', job.enabled ? 'badge-success' : 'badge-disabled']">
                {{ job.enabled ? 'Enabled' : 'Disabled' }}
              </span>
              <span class="next-run" v-if="job.next_run">
                Next: {{ formatTime(job.next_run) }}
              </span>
            </td>
            <td class="last-run-cell">
              <template v-if="job.last_run">
                <span class="run-time">{{ formatTime(job.last_run) }}</span>
                <span v-if="job.last_result && !job.last_result.error" class="badge badge-success">
                  <i class="pi pi-check"></i> OK
                </span>
                <span v-else-if="job.last_result && job.last_result.error" class="badge badge-error">
                  <i class="pi pi-times"></i> Error
                </span>
              </template>
              <span v-else class="never-run">Never</span>
            </td>
            <td class="total-runs">{{ job.total_runs }}</td>
            <td class="actions-cell">
              <button @click="startEdit(job)" class="btn-icon" title="Edit schedule">
                <i class="pi pi-pencil"></i>
              </button>
              <button @click="runNow(job.job_id)" class="btn-icon" title="Run now">
                <i class="pi pi-play"></i>
              </button>
              <button @click="toggleEnabled(job)" :class="['btn-icon', job.enabled ? 'btn-disable' : 'btn-enable']" :title="job.enabled ? 'Disable' : 'Enable'">
                <i class="pi" :class="job.enabled ? 'pi-pause' : 'pi-play-circle'"></i>
              </button>
              <button @click="viewHistory(job.job_id)" class="btn-icon" title="View history">
                <i class="pi pi-history"></i>
              </button>
            </td>
          </tr>
          <tr v-if="jobs.length === 0">
            <td colspan="7" class="empty-state">No cron jobs found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="editingJob" class="modal-overlay" @click.self="editingJob = null">
      <div class="modal-content">
        <h3>Edit Schedule: {{ editingJob.name }}</h3>
        <div class="form-group">
          <label for="cron-input">Cron Expression</label>
          <input
            id="cron-input"
            v-model="editCron"
            type="text"
            class="cron-input"
            placeholder="* * * * *"
          />
          <p class="cron-preview" v-if="editCron">
            <i class="pi pi-info-circle"></i>
            {{ cronToHuman(editCron) }}
          </p>
        </div>
        <div class="form-group">
          <label class="toggle-label">
            <input type="checkbox" v-model="editEnabled" class="toggle-checkbox" />
            <span class="toggle-slider"></span>
            {{ editEnabled ? 'Enabled' : 'Disabled' }}
          </label>
        </div>
        <div class="modal-actions">
          <button @click="saveEdit" class="btn-primary">Save</button>
          <button @click="editingJob = null" class="btn-secondary">Cancel</button>
        </div>
      </div>
    </div>

    <div v-if="showHistory" class="history-panel">
      <div class="history-header">
        <h3>History: {{ selectedJob }}</h3>
        <button @click="showHistory = false" class="btn-icon btn-close">
          <i class="pi pi-times"></i>
        </button>
      </div>
      <div class="history-table-wrapper">
        <table class="history-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Result</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, idx) in jobHistory" :key="idx">
              <td>{{ formatTime(entry.timestamp) }}</td>
              <td>
                <span :class="['badge', entry.result === 'success' ? 'badge-success' : 'badge-error']">
                  {{ entry.result }}
                </span>
              </td>
              <td class="details-cell">{{ entry.details || '-' }}</td>
            </tr>
            <tr v-if="jobHistory.length === 0">
              <td colspan="3" class="empty-state">No history records.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  getCronJobs,
  updateCronJob,
  runCronJobNow,
  getCronJobHistory
} from '../composables/useApi.js'

const jobs = ref([])
const loading = ref(true)
const editingJob = ref(null)
const editCron = ref('')
const editEnabled = ref(false)
const jobHistory = ref([])
const selectedJob = ref(null)
const showHistory = ref(false)

onMounted(() => {
  refreshJobs()
})

async function refreshJobs() {
  loading.value = true
  try {
    jobs.value = await getCronJobs()
  } catch (e) {
    console.error('Failed to load cron jobs:', e)
  } finally {
    loading.value = false
  }
}

function startEdit(job) {
  editingJob.value = job
  editCron.value = job.cron_expression
  editEnabled.value = job.enabled
}

async function saveEdit() {
  if (!editingJob.value) return
  try {
    await updateCronJob(editingJob.value.job_id, {
      cron_expression: editCron.value,
      enabled: editEnabled.value
    })
    editingJob.value = null
    await refreshJobs()
  } catch (e) {
    console.error('Failed to save cron job:', e)
  }
}

async function toggleEnabled(job) {
  try {
    await updateCronJob(job.job_id, { enabled: !job.enabled })
    await refreshJobs()
  } catch (e) {
    console.error('Failed to toggle cron job:', e)
  }
}

async function runNow(jobId) {
  try {
    await runCronJobNow(jobId)
    await refreshJobs()
  } catch (e) {
    console.error('Failed to run cron job:', e)
  }
}

async function viewHistory(jobId) {
  selectedJob.value = jobs.value.find(j => j.job_id === jobId)?.name || jobId
  showHistory.value = true
  try {
    jobHistory.value = await getCronJobHistory(jobId)
  } catch (e) {
    console.error('Failed to load job history:', e)
    jobHistory.value = []
  }
}

function cronToHuman(cron) {
  if (!cron) return ''
  const parts = cron.trim().split(/\s+/)
  if (parts.length !== 5) return cron

  const [min, hour, dom, month, dow] = parts

  if (cron === '* * * * *') return 'Every minute'
  if (cron === '0 * * * *') return 'Every hour'
  if (cron === '0 0 * * *') return 'Every day at midnight'
  if (cron === '0 0 * * 1') return 'Every Monday at midnight'

  const parts2 = []
  if (min !== '*') {
    if (min.startsWith('*/')) parts2.push(`Every ${min.slice(2)} minutes`)
    else parts2.push(`At minute ${min}`)
  }
  if (hour !== '*') {
    if (hour.startsWith('*/')) parts2.push(`Every ${hour.slice(2)} hours`)
    else parts2.push(`At hour ${hour}`)
  }
  if (dom !== '*') parts2.push(`On day ${dom}`)
  if (month !== '*') {
    const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    const m = parseInt(month)
    parts2.push(m >= 1 && m <= 12 ? `In ${monthNames[m]}` : `In month ${month}`)
  }
  if (dow !== '*') {
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    const d = parseInt(dow)
    parts2.push(d >= 0 && d <= 6 ? `On ${dayNames[d]}` : `On day-of-week ${d}`)
  }

  return parts2.length > 0 ? parts2.join(', ') : cron
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toLocaleString()
}

function appIcon(app) {
  const icons = {
    telegram_digest: 'pi-envelope',
    telegram_files: 'pi-download',
    cron: 'pi-calendar'
  }
  return icons[app] || 'pi-cog'
}
</script>

<style scoped>
.loading-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
  font-size: 1rem;
}

.jobs-table-wrapper {
  overflow-x: auto;
}

.jobs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.jobs-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  border-bottom: 2px solid var(--border);
  color: var(--text-secondary);
  font-weight: 600;
  white-space: nowrap;
}

.jobs-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.job-row:hover {
  background: var(--bg-secondary);
}

.app-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.app-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(59, 130, 246, 0.15);
  color: var(--accent);
  font-size: 0.75rem;
}

.job-name {
  font-weight: 500;
}

.schedule-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.cron-expr {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.8rem;
  padding: 0.15rem 0.4rem;
  background: var(--bg-secondary);
  border-radius: 4px;
  color: var(--text-primary);
}

.cron-human {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.status-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.next-run {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
  width: fit-content;
}

.badge-success {
  background: rgba(34, 197, 94, 0.15);
  color: var(--success);
}

.badge-error {
  background: rgba(239, 68, 68, 0.15);
  color: var(--error);
}

.badge-disabled {
  background: rgba(148, 163, 184, 0.15);
  color: var(--text-secondary);
}

.last-run-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.run-time {
  font-size: 0.8rem;
}

.never-run {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-style: italic;
}

.total-runs {
  font-variant-numeric: tabular-nums;
}

.actions-cell {
  display: flex;
  gap: 0.375rem;
}

.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.8rem;
}

.btn-icon:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-color: var(--accent);
}

.btn-enable:hover {
  color: var(--success);
  border-color: var(--success);
}

.btn-disable:hover {
  color: var(--error);
  border-color: var(--error);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-content h3 {
  margin: 0 0 1.25rem 0;
  font-size: 1.1rem;
  color: var(--text-primary);
}

.modal-content .form-group {
  margin-bottom: 1rem;
}

.modal-content .form-group label {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.cron-input {
  width: 100%;
  padding: 0.6rem 0.8rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.95rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s ease;
}

.cron-input:focus {
  border-color: var(--accent);
}

.cron-preview {
  margin: 0.5rem 0 0 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.toggle-label {
  display: flex !important;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
  font-size: 0.9rem !important;
  text-transform: none !important;
  letter-spacing: normal !important;
  color: var(--text-primary) !important;
}

.toggle-checkbox {
  display: none;
}

.toggle-slider {
  position: relative;
  width: 40px;
  height: 22px;
  background: var(--border);
  border-radius: 11px;
  transition: background 0.2s ease;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background: var(--text-primary);
  border-radius: 50%;
  transition: transform 0.2s ease;
}

.toggle-checkbox:checked + .toggle-slider {
  background: var(--accent);
}

.toggle-checkbox:checked + .toggle-slider::after {
  transform: translateX(18px);
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
  justify-content: flex-end;
}

.modal-actions .btn-primary {
  padding: 0.5rem 1.25rem;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.modal-actions .btn-primary:hover {
  opacity: 0.85;
}

.modal-actions .btn-secondary {
  padding: 0.5rem 1.25rem;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.modal-actions .btn-secondary:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.history-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 480px;
  max-width: 90vw;
  height: 100vh;
  background: var(--bg-card);
  border-left: 1px solid var(--border);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  box-shadow: -10px 0 40px rgba(0, 0, 0, 0.4);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
}

.history-header h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--text-primary);
}

.btn-close {
  border: none;
}

.history-table-wrapper {
  flex: 1;
  overflow-y: auto;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.history-table th {
  text-align: left;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
  font-weight: 600;
  position: sticky;
  top: 0;
  background: var(--bg-card);
}

.history-table td {
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
}

.details-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  color: var(--text-secondary);
  padding: 2rem !important;
  font-style: italic;
}
</style>
