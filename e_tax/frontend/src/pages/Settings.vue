<template>
  <div class="p-8">
    <div class="etax-page-header">
      <h1 class="text-2xl font-bold text-gray-900">{{ __('Settings') }}</h1>
      <p class="text-sm text-gray-500 mt-1">{{ __('Configure your tax system') }}</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- General Settings -->
      <div class="etax-card p-6">
        <h3 class="etax-section-title mb-4">{{ __('General Settings') }}</h3>
        <p class="text-sm text-gray-500 mb-4">{{ __('Configure tax authority and system defaults') }}</p>
        <a href="/app/tax-settings"
           class="inline-flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          {{ __('Open Settings') }}
        </a>
      </div>

      <!-- Fiscal Years -->
      <div class="etax-card p-6">
        <h3 class="etax-section-title mb-4">{{ __('Fiscal Years') }}</h3>
        <p class="text-sm text-gray-500 mb-4">{{ __('Manage fiscal year periods') }}</p>
        <a href="/app/tax-fiscal-year"
           class="inline-flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          {{ __('Manage Fiscal Years') }}
        </a>
      </div>

      <!-- Tax Types -->
      <div class="etax-card p-6">
        <h3 class="etax-section-title mb-4">{{ __('Tax Types') }}</h3>
        <p class="text-sm text-gray-500 mb-4">{{ __('Define and manage tax type categories') }}</p>
        <a href="/app/tax-type"
           class="inline-flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
          {{ __('Manage Tax Types') }}
        </a>
      </div>

      <!-- Tax Rates -->
      <div class="etax-card p-6">
        <h3 class="etax-section-title mb-4">{{ __('Tax Rates') }}</h3>
        <p class="text-sm text-gray-500 mb-4">{{ __('Set tax rates per type and fiscal year') }}</p>
        <a href="/app/tax-rate"
           class="inline-flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
          {{ __('Manage Tax Rates') }}
        </a>
      </div>

      <!-- Roles & Permissions -->
      <div class="etax-card p-6">
        <h3 class="etax-section-title mb-4">{{ __('Roles') }}</h3>
        <p class="text-sm text-gray-500 mb-4">{{ __('Manage e-Tax system roles') }}</p>
        <div class="flex flex-wrap gap-2 mb-4">
          <span class="text-xs font-medium bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full">Tax Officer</span>
          <span class="text-xs font-medium bg-green-50 text-green-700 px-2.5 py-1 rounded-full">Tax Filer</span>
          <span class="text-xs font-medium bg-orange-50 text-orange-700 px-2.5 py-1 rounded-full">Customs Officer</span>
          <span class="text-xs font-medium bg-purple-50 text-purple-700 px-2.5 py-1 rounded-full">Tax Auditor</span>
        </div>
        <a href="/app/role"
           class="inline-flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
          {{ __('Manage Roles') }}
        </a>
      </div>

      <!-- Language -->
      <div class="etax-card p-6">
        <h3 class="etax-section-title mb-4">{{ __('Language') }}</h3>
        <p class="text-sm text-gray-500 mb-4">{{ __('Select your preferred language for e-Tax') }}</p>
        <div class="flex gap-3">
          <button @click="setLang('en')"
                  class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  :class="currentLang === 'en' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'">
            EN English
          </button>
          <button @click="setLang('fr')"
                  class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  :class="currentLang === 'fr' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'">
            FR Français
          </button>
        </div>
      </div>

      <!-- Demo Data -->
      <div class="etax-card p-6 md:col-span-2 border-2 border-dashed border-amber-200 bg-amber-50/30">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>
          </div>
          <div class="flex-1">
            <h3 class="etax-section-title mb-1">{{ __('Demo Data') }}</h3>
            <p class="text-sm text-gray-500 mb-4">
              {{ __('Generate sample taxpayers, declarations, and demo users for testing. Demo users: company@etax.demo, person@etax.demo, agent@etax.demo (password: Demo@1234)') }}
            </p>

            <!-- Status indicator -->
            <div v-if="demoStatus" class="mb-4 flex items-center gap-2">
              <span class="relative flex h-2.5 w-2.5">
                <span v-if="demoStatus.has_demo_data" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2.5 w-2.5"
                      :class="demoStatus.has_demo_data ? 'bg-green-500' : 'bg-gray-300'"></span>
              </span>
              <span class="text-sm" :class="demoStatus.has_demo_data ? 'text-green-700' : 'text-gray-500'">
                {{ demoStatus.has_demo_data
                  ? __('Demo data is active') + ` (${demoStatus.demo_taxpayers} ` + __('taxpayers') + ')'
                  : __('No demo data loaded')
                }}
              </span>
            </div>

            <!-- Action buttons -->
            <div class="flex flex-wrap gap-3">
              <button @click="onCreateDemo"
                      :disabled="demoLoading"
                      class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                <svg v-if="demoLoading && demoAction === 'create'" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
                <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
                {{ demoLoading && demoAction === 'create' ? __('Creating...') : __('Create Demo Data') }}
              </button>
              <button @click="onClearDemo"
                      :disabled="demoLoading || (demoStatus && !demoStatus.has_demo_data)"
                      class="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                <svg v-if="demoLoading && demoAction === 'clear'" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
                <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                {{ demoLoading && demoAction === 'clear' ? __('Clearing...') : __('Clear Demo Data') }}
              </button>
            </div>

            <!-- Result message -->
            <div v-if="demoMessage" class="mt-3 text-sm px-3 py-2 rounded-lg"
                 :class="demoError ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'">
              {{ demoMessage }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { call } from 'frappe-ui'

const __ = inject('__')
const currentLang = ref(localStorage.getItem('etax_lang') || 'en')
const demoStatus = ref(null)
const demoLoading = ref(false)
const demoAction = ref('')
const demoMessage = ref('')
const demoError = ref(false)

function setLang(lang) {
  currentLang.value = lang
  localStorage.setItem('etax_lang', lang)
  window.location.reload()
}

async function fetchDemoStatus() {
  try {
    console.log('[e-tax] Fetching demo status...')
    console.log('[e-tax] csrf_token:', window.csrf_token ? 'SET' : 'MISSING')
    const data = await call('e_tax.api.get_demo_data_status')
    console.log('[e-tax] Demo status:', data)
    demoStatus.value = data
  } catch (e) {
    console.error('[e-tax] Failed to fetch demo status', e)
  }
}

async function onCreateDemo() {
  demoLoading.value = true
  demoAction.value = 'create'
  demoMessage.value = ''
  demoError.value = false
  try {
    console.log('[e-tax] Creating demo data...')
    const result = await call('e_tax.api.create_demo_data')
    console.log('[e-tax] Create result:', result)
    demoMessage.value = __('Demo data created successfully! 3 users, 5 taxpayers, and sample declarations added.')
    fetchDemoStatus()
  } catch (e) {
    demoError.value = true
    demoMessage.value = e.messages?.[0] || e.message || __('Failed to create demo data')
  } finally {
    demoLoading.value = false
  }
}

async function onClearDemo() {
  if (!confirm(__('Are you sure you want to remove all demo data? This will delete demo users, taxpayers, and all their declarations.'))) {
    return
  }
  demoLoading.value = true
  demoAction.value = 'clear'
  demoMessage.value = ''
  demoError.value = false
  try {
    await call('e_tax.api.clear_demo_data')
    demoMessage.value = __('All demo data has been cleared.')
    fetchDemoStatus()
  } catch (e) {
    demoError.value = true
    demoMessage.value = e.messages?.[0] || e.message || __('Failed to clear demo data')
  } finally {
    demoLoading.value = false
  }
}

onMounted(() => {
  fetchDemoStatus()
})
</script>
