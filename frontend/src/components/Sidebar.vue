<script setup>
import { ref, onMounted } from 'vue'
import { shutdownApp, getSettings, saveSettings } from '../composables/useApi.js'

defineProps({ currentView: String })
const emit = defineEmits(['navigate', 'theme-toggle'])

const isDark = ref(true)

onMounted(async () => {
  try {
    const config = await getSettings()
    isDark.value = (config.card_theme || 'dark') === 'dark'
  } catch (e) {}
})

async function toggleTheme() {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  emit('theme-toggle', theme)
  try {
    const config = await getSettings()
    config.card_theme = theme
    await saveSettings(config)
  } catch (e) {}
}

const navItems = [
  { key: 'dashboard', icon: 'pi-home', label: 'Dashboard' },
  { key: 'linkcard', icon: 'pi-link', label: 'Link Card' },
  { key: 'tweetgen', icon: 'pi-twitter', label: 'Tweet Gen' },
  { key: 'wiki', icon: 'pi-book', label: 'Wiki' },
  { key: 'tg-digest', icon: 'pi-envelope', label: 'TG Digest' },
  { key: 'tg-files', icon: 'pi-download', label: 'TG Files' },
  { key: 'cron', icon: 'pi-calendar', label: 'Cron Jobs' },
]

async function handleShutdown() {
  if (!confirm('Are you sure you want to exit MyHub?')) return
  try {
    await shutdownApp()
    setTimeout(() => window.close(), 1500)
  } catch (e) {
    setTimeout(() => window.close(), 1000)
  }
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <i class="pi pi-th-large"></i>
      <span>MyHub</span>
    </div>

    <nav class="sidebar-nav">
      <button
        v-for="item in navItems"
        :key="item.key"
        class="nav-item"
        :class="{ active: currentView === item.key }"
        @click="emit('navigate', item.key)"
      >
        <i :class="'pi ' + item.icon"></i>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <div class="sidebar-footer">
      <button class="nav-item theme-toggle" @click="toggleTheme" :title="isDark ? 'Switch to light theme' : 'Switch to dark theme'">
        <i :class="isDark ? 'pi pi-sun' : 'pi pi-moon'"></i>
        <span>{{ isDark ? 'Light Mode' : 'Dark Mode' }}</span>
      </button>
      <button
        class="nav-item"
        :class="{ active: currentView === 'settings' }"
        @click="emit('navigate', 'settings')"
      >
        <i class="pi pi-cog"></i>
        <span>Settings</span>
      </button>
      <button class="nav-item shutdown-btn" @click="handleShutdown">
        <i class="pi pi-power-off"></i>
        <span>Exit</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.theme-toggle:hover {
  background: var(--bg-card);
  color: var(--warning);
}
</style>
