<template>
  <FrappeUIProvider>
    <router-view v-if="isLoggedIn" />
    <div v-else class="h-screen flex items-center justify-center dark:bg-gray-900">
      <p class="text-gray-500 dark:text-gray-400">Redirecting to login...</p>
    </div>
  </FrappeUIProvider>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { FrappeUIProvider } from 'frappe-ui'

const isLoggedIn = computed(() => {
  return document.cookie.includes('user_id') || window.csrf_token
})

// Theme from boot data (injected server-side in ess.html)
let userTheme = window.desk_theme || 'light'

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme === 'dark' ? 'dark' : 'light')
}

function applySystemTheme() {
  setTheme(window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
}

function applyUserTheme() {
  if (userTheme === 'automatic') {
    applySystemTheme()
  } else {
    setTheme(userTheme)
  }
}

// Apply immediately
applyUserTheme()

let mql
onMounted(() => {
  mql = window.matchMedia('(prefers-color-scheme: dark)')
  mql.addEventListener('change', () => {
    if (userTheme === 'automatic') {
      applySystemTheme()
    }
  })
})
onUnmounted(() => {
  mql?.removeEventListener('change', applySystemTheme)
})
</script>
