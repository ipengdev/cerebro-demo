<template>
  <FrappeUIProvider>
    <router-view v-if="isLoggedIn" />
    <div v-else class="h-screen flex items-center justify-center dark:bg-gray-900">
      <p class="text-gray-500 dark:text-gray-400">Redirecting to login...</p>
    </div>
  </FrappeUIProvider>
</template>

<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { FrappeUIProvider, createResource } from 'frappe-ui'

const isLoggedIn = computed(() => {
  return document.cookie.includes('user_id') || window.csrf_token
})

function setTheme(theme) {
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark')
  } else {
    document.documentElement.setAttribute('data-theme', 'light')
  }
}

function applySystemTheme() {
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    setTheme('dark')
  } else {
    setTheme('light')
  }
}

let mql
let userTheme = null

const themeResource = createResource({
  url: 'employee_self_service.api.get_user_theme',
  auto: true,
  onSuccess(data) {
    userTheme = data || 'light'
    applyUserTheme()
  },
  onError() {
    // If API fails, fall back to system preference
    applySystemTheme()
  },
})

// Also watch the resource data as a fallback
watch(() => themeResource.data, (val) => {
  if (val) {
    userTheme = val
    applyUserTheme()
  }
})

function applyUserTheme() {
  if (userTheme === 'automatic') {
    applySystemTheme()
  } else if (userTheme === 'dark') {
    setTheme('dark')
  } else {
    setTheme('light')
  }
}

onMounted(() => {
  mql = window.matchMedia('(prefers-color-scheme: dark)')
  // Listen for OS theme changes (applies when user chose "Automatic")
  mql.addEventListener('change', () => {
    if (userTheme === 'automatic') {
      applySystemTheme()
    }
  })
  // Fallback: apply system theme until API responds
  applySystemTheme()
})
onUnmounted(() => {
  mql?.removeEventListener('change', applySystemTheme)
})
</script>
