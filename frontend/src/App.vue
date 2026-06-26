<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import DashboardView from './components/DashboardView.vue'
import LinkCardView from './components/LinkCardView.vue'
import TweetGenView from './components/TweetGenView.vue'
import WikiView from './components/WikiView.vue'
import TelegramDigestView from './components/TelegramDigestView.vue'
import TelegramFilesView from './components/TelegramFilesView.vue'
import CronDashboardView from './components/CronDashboardView.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import { getSettings } from './composables/useApi.js'

const currentView = ref('dashboard')

function applyTheme(theme) {
  if (theme === 'light') {
    document.documentElement.classList.add('light-theme')
  } else {
    document.documentElement.classList.remove('light-theme')
  }
}

onMounted(async () => {
  try {
    const config = await getSettings()
    applyTheme(config.card_theme || 'dark')
  } catch (e) {
    // use default dark
  }
})

defineExpose({ applyTheme })
</script>

<template>
  <div class="app-layout">
    <Sidebar :currentView="currentView" @navigate="currentView = $event" @theme-toggle="applyTheme" />
    <main class="main-content">
      <DashboardView v-if="currentView === 'dashboard'" @navigate="currentView = $event" />
      <LinkCardView v-else-if="currentView === 'linkcard'" />
      <TweetGenView v-else-if="currentView === 'tweetgen'" />
      <WikiView v-else-if="currentView === 'wiki'" />
      <TelegramDigestView v-else-if="currentView === 'tg-digest'" />
      <TelegramFilesView v-else-if="currentView === 'tg-files'" />
      <CronDashboardView v-else-if="currentView === 'cron'" />
      <SettingsPanel v-else-if="currentView === 'settings'" @theme-changed="applyTheme" />
    </main>
  </div>
</template>
