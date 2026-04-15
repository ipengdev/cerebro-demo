<template>
  <div class="p-8">
    <div class="etax-page-header flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ __('Excise Duty Returns') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ __('Alcohol, tobacco, fuel and packaging excise filings') }}</p>
      </div>
      <a href="/app/excise-duty-return/new"
         class="inline-flex items-center gap-2 bg-cyan-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-cyan-700 transition-colors shadow-sm">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
        {{ __('New Excise Return') }}
      </a>
    </div>

    <!-- Mini stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="etax-card p-4">
        <p class="text-xs text-gray-400 font-medium">{{ __('Total') }}</p>
        <p class="text-xl font-bold text-gray-900">{{ records.length }}</p>
      </div>
      <div class="etax-card p-4">
        <p class="text-xs text-gray-400 font-medium">{{ __('Total Excise') }}</p>
        <p class="text-xl font-bold text-cyan-600">{{ fmt(totalExcise) }}</p>
      </div>
      <div class="etax-card p-4">
        <p class="text-xs text-gray-400 font-medium">{{ __('Approved') }}</p>
        <p class="text-xl font-bold text-green-600">{{ byStatus('Approved') }}</p>
      </div>
      <div class="etax-card p-4">
        <p class="text-xs text-gray-400 font-medium">{{ __('Pending') }}</p>
        <p class="text-xl font-bold text-amber-600">{{ byStatus('Submitted') + byStatus('Under Review') }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="etax-card p-4 mb-6 flex flex-wrap items-center gap-4">
      <div class="flex-1 min-w-[200px]">
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <input v-model="searchQuery" type="text" :placeholder="__('Search excise returns...')"
                 class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent" />
        </div>
      </div>
      <select v-model="filterExciseType" class="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-cyan-500">
        <option value="">{{ __('All Excise Types') }}</option>
        <option value="Alcohol">{{ __('Alcohol') }}</option>
        <option value="Tobacco">{{ __('Tobacco') }}</option>
        <option value="Fuel">{{ __('Fuel') }}</option>
        <option value="Packaging">{{ __('Packaging') }}</option>
      </select>
      <select v-model="filterStatus" class="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-cyan-500">
        <option value="">{{ __('All Statuses') }}</option>
        <option value="Draft">{{ __('Draft') }}</option>
        <option value="Submitted">{{ __('Submitted') }}</option>
        <option value="Under Review">{{ __('Under Review') }}</option>
        <option value="Approved">{{ __('Approved') }}</option>
        <option value="Rejected">{{ __('Rejected') }}</option>
      </select>
    </div>

    <!-- Table -->
    <div class="etax-card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">ID</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Taxpayer') }}</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Excise Type') }}</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Period') }}</th>
            <th class="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Total Excise') }}</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Status') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in filtered" :key="r.name"
              class="border-b border-gray-50 hover:bg-cyan-50/50 transition-colors cursor-pointer"
              @click="open(r.name)">
            <td class="py-3 px-4 text-sm font-medium text-cyan-600">{{ r.name }}</td>
            <td class="py-3 px-4 text-sm text-gray-700">{{ r.taxpayer_name }}</td>
            <td class="py-3 px-4">
              <span class="text-xs font-medium px-2 py-1 rounded-md"
                    :class="exciseClass(r.excise_type)">
                {{ __(r.excise_type) }}
              </span>
            </td>
            <td class="py-3 px-4 text-sm text-gray-600">{{ r.period_start }} — {{ r.period_end }}</td>
            <td class="py-3 px-4 text-sm text-gray-900 font-semibold text-right">{{ fmt(r.total_excise_duty) }}</td>
            <td class="py-3 px-4"><span :class="statusClass(r.status)">{{ __(r.status) }}</span></td>
          </tr>
          <tr v-if="loading">
            <td colspan="6" class="py-16 text-center text-gray-400">
              <div class="inline-block w-6 h-6 border-2 border-cyan-200 border-t-cyan-600 rounded-full animate-spin"></div>
            </td>
          </tr>
          <tr v-else-if="!filtered.length">
            <td colspan="6" class="py-16 text-center text-gray-400 text-sm">{{ __('No data available') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { call } from 'frappe-ui'

const __ = inject('__')
const records = ref([])
const searchQuery = ref('')
const filterExciseType = ref('')
const filterStatus = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await call('frappe.client.get_list', {
      doctype: 'Excise Duty Return',
      fields: ['name','taxpayer_name','excise_type','period_start','period_end','total_excise_duty','status'],
      limit_page_length: 100,
      order_by: 'creation desc'
    })
    records.value = data || []
  } catch (e) { console.warn('ExciseDutyReturn load error:', e) } finally { loading.value = false }
})

const totalExcise = computed(() => records.value.reduce((s, r) => s + (r.total_excise_duty || 0), 0))
const byStatus = (s) => records.value.filter(r => r.status === s).length

const filtered = computed(() => {
  let list = records.value
  if (filterExciseType.value) list = list.filter(r => r.excise_type === filterExciseType.value)
  if (filterStatus.value) list = list.filter(r => r.status === filterStatus.value)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(r => (r.name || '').toLowerCase().includes(q) || (r.taxpayer_name || '').toLowerCase().includes(q))
  }
  return list
})

function exciseClass(t) {
  const m = { Alcohol: 'bg-purple-50 text-purple-700', Tobacco: 'bg-amber-50 text-amber-700', Fuel: 'bg-red-50 text-red-700', Packaging: 'bg-teal-50 text-teal-700' }
  return m[t] || 'bg-gray-100 text-gray-700'
}

function fmt(v) { return v ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v) : '$0' }

function statusClass(s) {
  return { Draft:'etax-badge-draft', Submitted:'etax-badge-submitted', 'Under Review':'etax-badge-review', Approved:'etax-badge-approved', Rejected:'etax-badge-rejected' }[s] || 'etax-badge-draft'
}

function open(name) { window.location.href = `/app/excise-duty-return/${name}` }
</script>
