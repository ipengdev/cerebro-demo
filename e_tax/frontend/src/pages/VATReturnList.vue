<template>
  <div class="p-8">
    <div class="etax-page-header flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ __('VAT Returns') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ __('Value Added Tax filing and management') }}</p>
      </div>
      <a href="/app/vat-return/new"
         class="inline-flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors shadow-sm">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
        {{ __('New VAT Return') }}
      </a>
    </div>

    <!-- Mini stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="etax-card p-4">
        <p class="text-xs text-gray-400 font-medium">{{ __('Total') }}</p>
        <p class="text-xl font-bold text-gray-900">{{ records.length }}</p>
      </div>
      <div class="etax-card p-4">
        <p class="text-xs text-gray-400 font-medium">{{ __('Net VAT Payable') }}</p>
        <p class="text-xl font-bold text-green-600">{{ fmt(totalNet) }}</p>
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
          <input v-model="searchQuery" type="text" :placeholder="__('Search VAT returns...')"
                 class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent" />
        </div>
      </div>
      <select v-model="filterStatus" class="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-green-500">
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
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Period') }}</th>
            <th class="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Output VAT') }}</th>
            <th class="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Input VAT') }}</th>
            <th class="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Net VAT') }}</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Status') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in filtered" :key="r.name"
              class="border-b border-gray-50 hover:bg-green-50/50 transition-colors cursor-pointer"
              @click="open(r.name)">
            <td class="py-3 px-4 text-sm font-medium text-green-600">{{ r.name }}</td>
            <td class="py-3 px-4 text-sm text-gray-700">{{ r.taxpayer_name }}</td>
            <td class="py-3 px-4 text-sm text-gray-600">{{ r.period_start }} — {{ r.period_end }}</td>
            <td class="py-3 px-4 text-sm text-gray-900 text-right">{{ fmt(r.output_vat) }}</td>
            <td class="py-3 px-4 text-sm text-gray-900 text-right">{{ fmt(r.input_vat) }}</td>
            <td class="py-3 px-4 text-sm font-semibold text-right" :class="r.net_vat >= 0 ? 'text-red-600' : 'text-green-600'">{{ fmt(r.net_vat) }}</td>
            <td class="py-3 px-4"><span :class="statusClass(r.status)">{{ __(r.status) }}</span></td>
          </tr>
          <tr v-if="loading">
            <td colspan="7" class="py-16 text-center text-gray-400">
              <div class="inline-block w-6 h-6 border-2 border-green-200 border-t-green-600 rounded-full animate-spin"></div>
            </td>
          </tr>
          <tr v-else-if="!filtered.length">
            <td colspan="7" class="py-16 text-center text-gray-400 text-sm">{{ __('No data available') }}</td>
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
const filterStatus = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await call('frappe.client.get_list', {
      doctype: 'VAT Return',
      fields: ['name','taxpayer_name','period_start','period_end','output_vat','input_vat','net_vat','status'],
      limit_page_length: 100,
      order_by: 'creation desc'
    })
    records.value = data || []
  } catch (e) { console.warn('VATReturn load error:', e) } finally { loading.value = false }
})

const totalNet = computed(() => records.value.reduce((s, r) => s + (r.net_vat || 0), 0))
const byStatus = (s) => records.value.filter(r => r.status === s).length

const filtered = computed(() => {
  let list = records.value
  if (filterStatus.value) list = list.filter(r => r.status === filterStatus.value)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(r => (r.name || '').toLowerCase().includes(q) || (r.taxpayer_name || '').toLowerCase().includes(q))
  }
  return list
})

function fmt(v) { return v ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v) : '$0' }

function statusClass(s) {
  return { Draft:'etax-badge-draft', Submitted:'etax-badge-submitted', 'Under Review':'etax-badge-review', Approved:'etax-badge-approved', Rejected:'etax-badge-rejected' }[s] || 'etax-badge-draft'
}

function open(name) { window.location.href = `/app/vat-return/${name}` }
</script>
