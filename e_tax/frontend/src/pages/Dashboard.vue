<template>
  <div class="p-8">
    <!-- Header -->
    <div class="etax-page-header flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ __('Dashboard') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ __('Overview of your tax administration') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="text-right">
          <p class="text-xs text-gray-400">{{ __('Fiscal Year') }}</p>
          <p class="text-sm font-semibold text-gray-700">{{ currentYear }}</p>
        </div>
      </div>
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="text-center py-12 text-gray-500">{{ __('Loading dashboard...') }}</div>
    <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">{{ error }}</div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      <div class="etax-stat-card group">
        <div class="absolute top-0 right-0 w-24 h-24 transform translate-x-8 -translate-y-8">
          <div class="w-full h-full bg-blue-500 opacity-5 rounded-full group-hover:opacity-10 transition-opacity"></div>
        </div>
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="text-xs font-medium text-gray-400 uppercase tracking-wide">{{ __('Total Revenue') }}</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">{{ formatCurrency(stats.total_revenue) }}</p>
        <p class="text-xs text-green-600 mt-1 font-medium">{{ __('Filed This Month') }}</p>
      </div>

      <div class="etax-stat-card group">
        <div class="absolute top-0 right-0 w-24 h-24 transform translate-x-8 -translate-y-8">
          <div class="w-full h-full bg-emerald-500 opacity-5 rounded-full group-hover:opacity-10 transition-opacity"></div>
        </div>
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <span class="text-xs font-medium text-gray-400 uppercase tracking-wide">{{ __('Active Taxpayers') }}</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">{{ stats.total_taxpayers || 0 }}</p>
        <div class="flex gap-4 mt-1">
          <span class="text-xs text-gray-500">{{ stats.enterprise_taxpayers || 0 }} {{ __('Enterprises') }}</span>
          <span class="text-xs text-gray-500">{{ stats.individual_taxpayers || 0 }} {{ __('Individuals') }}</span>
        </div>
      </div>

      <div class="etax-stat-card group">
        <div class="absolute top-0 right-0 w-24 h-24 transform translate-x-8 -translate-y-8">
          <div class="w-full h-full bg-amber-500 opacity-5 rounded-full group-hover:opacity-10 transition-opacity"></div>
        </div>
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="text-xs font-medium text-gray-400 uppercase tracking-wide">{{ __('Pending Reviews') }}</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">{{ totalPending }}</p>
        <p class="text-xs text-amber-600 mt-1 font-medium">{{ __('Awaiting approval') }}</p>
      </div>

      <div class="etax-stat-card group">
        <div class="absolute top-0 right-0 w-24 h-24 transform translate-x-8 -translate-y-8">
          <div class="w-full h-full bg-violet-500 opacity-5 rounded-full group-hover:opacity-10 transition-opacity"></div>
        </div>
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 bg-violet-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <span class="text-xs font-medium text-gray-400 uppercase tracking-wide">Total Filings</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">{{ totalFilings }}</p>
        <p class="text-xs text-violet-600 mt-1 font-medium">All declaration types</p>
      </div>
    </div>

    <!-- Revenue Breakdown Cards -->
    <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
      <div v-for="(item, idx) in revenueCards" :key="idx"
           class="etax-card px-4 py-4 flex items-center gap-3 cursor-pointer hover:border-blue-200"
           @click="$router.push(item.route)">
        <div class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
             :class="item.bgColor">
          <component :is="item.icon" :class="['w-4 h-4', item.iconColor]" />
        </div>
        <div class="min-w-0">
          <p class="text-xs text-gray-400 font-medium truncate">{{ __(item.label) }}</p>
          <p class="text-sm font-bold text-gray-900">{{ formatCurrency(item.amount) }}</p>
          <p class="text-[10px] text-gray-400">{{ item.count }} {{ __('filings') }}</p>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- Revenue by Type Donut -->
      <div class="etax-card p-6">
        <h3 class="etax-section-title mb-4">{{ __('Revenue by Tax Type') }}</h3>
        <div class="space-y-3">
          <div v-for="(item, idx) in revenueBreakdown" :key="idx" class="flex items-center gap-3">
            <div class="w-3 h-3 rounded-full flex-shrink-0" :style="{ backgroundColor: item.color }"></div>
            <span class="text-sm text-gray-600 flex-1">{{ __(item.label) }}</span>
            <span class="text-sm font-semibold text-gray-900">{{ formatCurrency(item.value) }}</span>
            <div class="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all duration-500" :style="{ width: item.percent + '%', backgroundColor: item.color }"></div>
            </div>
            <span class="text-xs text-gray-400 w-10 text-right">{{ item.percent }}%</span>
          </div>
        </div>
      </div>

      <!-- Filing Status Overview -->
      <div class="etax-card p-6">
        <h3 class="etax-section-title mb-4">Filing Status Overview</h3>
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span class="text-xs font-medium text-gray-500">{{ __('Submitted') }}</span>
            </div>
            <p class="text-xl font-bold text-gray-900">{{ stats.total_pending || totalPending }}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-2 h-2 bg-green-500 rounded-full"></div>
              <span class="text-xs font-medium text-gray-500">{{ __('Approved') }}</span>
            </div>
            <p class="text-xl font-bold text-gray-900">{{ stats.total_approved || 0 }}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-2 h-2 bg-emerald-500 rounded-full"></div>
              <span class="text-xs font-medium text-gray-500">{{ __('Tax Types') }}</span>
            </div>
            <p class="text-xl font-bold text-gray-900">{{ stats.tax_types || 0 }}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-4">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-2 h-2 bg-violet-500 rounded-full"></div>
              <span class="text-xs font-medium text-gray-500">{{ __('Total Filings') }}</span>
            </div>
            <p class="text-xl font-bold text-gray-900">{{ stats.total_filings || totalFilings }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Filings Table -->
    <div class="etax-card p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="etax-section-title">{{ __('Recent Filings') }}</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">ID</th>
              <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Type</th>
              <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Taxpayer Name') }}</th>
              <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Filing Date') }}</th>
              <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Status') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="filing in recentFilings" :key="filing.name"
                class="border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer">
              <td class="py-3 px-4">
                <span class="text-sm font-medium text-blue-600">{{ filing.name }}</span>
              </td>
              <td class="py-3 px-4">
                <span class="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded-md">{{ filing.declaration_type }}</span>
              </td>
              <td class="py-3 px-4 text-sm text-gray-700">{{ filing.taxpayer_name }}</td>
              <td class="py-3 px-4 text-sm text-gray-500">{{ filing.filing_date }}</td>
              <td class="py-3 px-4">
                <span :class="getStatusClass(filing.status)">{{ __(filing.status) }}</span>
              </td>
            </tr>
            <tr v-if="!recentFilings.length">
              <td colspan="5" class="py-12 text-center text-gray-400">
                <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p class="text-sm">{{ __('No data available') }}</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="mt-8 grid grid-cols-2 md:grid-cols-5 gap-3">
      <a v-for="action in quickActions" :key="action.doctype"
         :href="`/app/${action.doctype.toLowerCase().replace(/ /g, '-')}/new`"
         class="etax-card p-4 text-center hover:border-blue-200 group">
        <div class="w-10 h-10 mx-auto mb-2 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform"
             :class="action.bgColor">
          <svg class="w-5 h-5" :class="action.iconColor" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        </div>
        <p class="text-xs font-medium text-gray-600 group-hover:text-blue-600 transition-colors">{{ __(action.label) }}</p>
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, h } from 'vue'
import { call } from 'frappe-ui'

const __ = inject('__')
const currentYear = new Date().getFullYear()

const stats = ref({})
const recentFilings = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const [statsData, filingsData] = await Promise.all([
      call('e_tax.api.get_dashboard_stats'),
      call('e_tax.api.get_recent_filings'),
    ])
    stats.value = statsData || {}
    recentFilings.value = filingsData || []
  } catch (e) {
    console.error('[e-tax] Dashboard data load error:', e)
    error.value = 'Failed to load dashboard: ' + (e.message || e)
  } finally {
    loading.value = false
  }
})

const totalPending = computed(() => {
  return (stats.value.enterprise_declarations_pending || 0)
    + (stats.value.vat_returns_pending || 0)
    + (stats.value.pit_pending || 0)
    + (stats.value.customs_pending || 0)
    + (stats.value.excise_pending || 0)
})

const totalFilings = computed(() => {
  return (stats.value.enterprise_declarations || 0)
    + (stats.value.vat_returns || 0)
    + (stats.value.personal_income_tax || 0)
    + (stats.value.customs_declarations || 0)
    + (stats.value.excise_returns || 0)
})

const revenueBreakdown = computed(() => {
  const total = stats.value.total_revenue || 1
  const items = [
    { label: 'Income Tax', value: stats.value.total_income_tax || 0, color: '#2563eb' },
    { label: 'VAT', value: stats.value.total_vat_collected || 0, color: '#16a34a' },
    { label: 'Personal Income Tax', value: stats.value.total_pit_collected || 0, color: '#9333ea' },
    { label: 'Customs Duty', value: stats.value.total_customs_duty || 0, color: '#ea580c' },
    { label: 'Excise Duty', value: stats.value.total_excise_duty || 0, color: '#0891b2' },
  ]
  return items.map(i => ({ ...i, percent: Math.round((i.value / total) * 100) || 0 }))
})

// Simple icon components for revenue cards
const IconBuilding = { render() { return h('svg', { fill:'none', viewBox:'0 0 24 24', stroke:'currentColor' }, [h('path', { 'stroke-linecap':'round', 'stroke-linejoin':'round', 'stroke-width':'2', d:'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' })]) } }
const IconReceipt = { render() { return h('svg', { fill:'none', viewBox:'0 0 24 24', stroke:'currentColor' }, [h('path', { 'stroke-linecap':'round', 'stroke-linejoin':'round', 'stroke-width':'2', d:'M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z' })]) } }
const IconUser = { render() { return h('svg', { fill:'none', viewBox:'0 0 24 24', stroke:'currentColor' }, [h('path', { 'stroke-linecap':'round', 'stroke-linejoin':'round', 'stroke-width':'2', d:'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' })]) } }
const IconGlobe = { render() { return h('svg', { fill:'none', viewBox:'0 0 24 24', stroke:'currentColor' }, [h('path', { 'stroke-linecap':'round', 'stroke-linejoin':'round', 'stroke-width':'2', d:'M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z' })]) } }
const IconFlask = { render() { return h('svg', { fill:'none', viewBox:'0 0 24 24', stroke:'currentColor' }, [h('path', { 'stroke-linecap':'round', 'stroke-linejoin':'round', 'stroke-width':'2', d:'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' })]) } }

const revenueCards = computed(() => [
  { label: 'Income Tax', route: '/e-tax/enterprise-declarations', amount: stats.value.total_income_tax || 0, count: stats.value.enterprise_declarations || 0, bgColor: 'bg-blue-100', iconColor: 'text-blue-600', icon: IconBuilding },
  { label: 'VAT', route: '/e-tax/vat-returns', amount: stats.value.total_vat_collected || 0, count: stats.value.vat_returns || 0, bgColor: 'bg-green-100', iconColor: 'text-green-600', icon: IconReceipt },
  { label: 'Personal Income Tax', route: '/e-tax/personal-income-tax', amount: stats.value.total_pit_collected || 0, count: stats.value.personal_income_tax || 0, bgColor: 'bg-purple-100', iconColor: 'text-purple-600', icon: IconUser },
  { label: 'Customs Duty', route: '/e-tax/customs-declarations', amount: stats.value.total_customs_duty || 0, count: stats.value.customs_declarations || 0, bgColor: 'bg-orange-100', iconColor: 'text-orange-600', icon: IconGlobe },
  { label: 'Excise Duty', route: '/e-tax/excise-duty-returns', amount: stats.value.total_excise_duty || 0, count: stats.value.excise_returns || 0, bgColor: 'bg-cyan-100', iconColor: 'text-cyan-600', icon: IconFlask },
])

const quickActions = [
  { doctype: 'Enterprise Declaration', label: 'Enterprise Declaration', bgColor: 'bg-blue-50', iconColor: 'text-blue-500' },
  { doctype: 'VAT Return', label: 'VAT Return', bgColor: 'bg-green-50', iconColor: 'text-green-500' },
  { doctype: 'Personal Income Tax', label: 'Personal Income Tax', bgColor: 'bg-purple-50', iconColor: 'text-purple-500' },
  { doctype: 'Customs Declaration', label: 'Customs Declaration', bgColor: 'bg-orange-50', iconColor: 'text-orange-500' },
  { doctype: 'Excise Duty Return', label: 'Excise Duty Return', bgColor: 'bg-cyan-50', iconColor: 'text-cyan-500' },
]

function formatCurrency(value) {
  if (!value) return '0'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value)
}

function getStatusClass(status) {
  const classes = {
    'Draft': 'etax-badge-draft',
    'Submitted': 'etax-badge-submitted',
    'Under Review': 'etax-badge-review',
    'Under Assessment': 'etax-badge-review',
    'Approved': 'etax-badge-approved',
    'Assessed': 'etax-badge-approved',
    'Cleared': 'etax-badge-approved',
    'Rejected': 'etax-badge-rejected',
    'Held': 'etax-badge-rejected',
  }
  return classes[status] || 'etax-badge-draft'
}
</script>
