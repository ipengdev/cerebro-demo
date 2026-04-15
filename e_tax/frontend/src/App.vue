<template>
  <div class="h-screen flex bg-gray-50" v-if="isLoggedIn">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col fixed h-full z-30">
      <!-- Logo -->
      <div class="p-5 border-b border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center shadow-sm">
            <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h1 class="text-lg font-bold text-gray-900">e-Tax</h1>
            <p class="text-[10px] text-gray-400 font-medium uppercase tracking-wider">{{ __('Tax and Customs Board') }}</p>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 p-3 space-y-1 overflow-y-auto">
        <div class="mb-4">
          <p class="px-3 mb-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ __('Overview') }}</p>
          <router-link
            to="/e-tax/dashboard"
            class="etax-nav-item"
            :class="{ active: $route.name === 'Dashboard' }"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v2a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 11a1 1 0 011-1h4a1 1 0 011 1v8a1 1 0 01-1 1h-4a1 1 0 01-1-1v-8z" />
            </svg>
            {{ __('Dashboard') }}
          </router-link>
        </div>

        <div class="mb-4">
          <p class="px-3 mb-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ __('Tax Filing') }}</p>
          <router-link
            v-for="item in taxNavItems"
            :key="item.route"
            :to="item.route"
            class="etax-nav-item"
            :class="{ active: $route.name === item.name }"
          >
            <component :is="item.icon" class="w-5 h-5" />
            {{ __(item.label) }}
          </router-link>
        </div>

        <div class="mb-4">
          <p class="px-3 mb-2 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{{ __('Management') }}</p>
          <router-link
            to="/e-tax/taxpayers"
            class="etax-nav-item"
            :class="{ active: $route.name === 'Taxpayers' }"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {{ __('Taxpayers') }}
          </router-link>
          <router-link
            to="/e-tax/settings"
            class="etax-nav-item"
            :class="{ active: $route.name === 'Settings' }"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {{ __('Settings') }}
          </router-link>
        </div>
      </nav>

      <!-- Language Switcher & User -->
      <div class="p-3 border-t border-gray-100">
        <div class="flex items-center gap-2 mb-3">
          <button
            @click="setLanguage('en')"
            class="flex-1 py-1.5 px-2 text-xs font-medium rounded-lg transition-colors"
            :class="currentLang === 'en' ? 'bg-blue-100 text-blue-700' : 'bg-gray-50 text-gray-500 hover:bg-gray-100'"
          >
            🇬🇧 English
          </button>
          <button
            @click="setLanguage('fr')"
            class="flex-1 py-1.5 px-2 text-xs font-medium rounded-lg transition-colors"
            :class="currentLang === 'fr' ? 'bg-blue-100 text-blue-700' : 'bg-gray-50 text-gray-500 hover:bg-gray-100'"
          >
            🇫🇷 Français
          </button>
        </div>
        <a
          href="/app"
          class="etax-nav-item text-gray-500 hover:text-gray-700"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
          </svg>
          Back to Desk
        </a>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 ml-64 overflow-y-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, inject, h } from 'vue'

const __ = inject('__')
const setLang = inject('setLang')
const getLang = inject('getLang')
const currentLang = ref(getLang())
const isLoggedIn = ref(true)

function setLanguage(lang) {
  currentLang.value = lang
  setLang(lang)
}

// Icon components for navigation
const IconEnterprise = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' })
    ])
  }
}

const IconVAT = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z' })
    ])
  }
}

const IconPIT = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' })
    ])
  }
}

const IconCustoms = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z' })
    ])
  }
}

const IconExcise = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '1.5', d: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' })
    ])
  }
}

const taxNavItems = [
  { route: '/e-tax/enterprise-declarations', name: 'EnterpriseDeclarations', label: 'Enterprise Declarations', icon: IconEnterprise },
  { route: '/e-tax/vat-returns', name: 'VATReturns', label: 'VAT Returns', icon: IconVAT },
  { route: '/e-tax/personal-income-tax', name: 'PersonalIncomeTax', label: 'Personal Income Tax', icon: IconPIT },
  { route: '/e-tax/customs-declarations', name: 'CustomsDeclarations', label: 'Customs Declarations', icon: IconCustoms },
  { route: '/e-tax/excise-duty-returns', name: 'ExciseDutyReturns', label: 'Excise Duty Returns', icon: IconExcise },
]
</script>
