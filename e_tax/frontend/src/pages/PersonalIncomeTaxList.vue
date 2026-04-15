<template>
  <div class="p-8">
    <div class="etax-page-header flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ __('Personal Income Tax') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ __('Individual income tax declarations') }}</p>
      </div>
      <a href="/app/personal-income-tax/new"
         class="inline-flex items-center gap-2 bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors shadow-sm">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
        {{ __('New Declaration') }}
      </a>
    </div>

    <!-- Mini stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="etax-card p-4">
        <p class="text-xs text-gray-400 font-medium">{{ __('Total') }}</p>
        <p class="text-xl font-bold text-gray-900">{{ records.length }}</p>
      </div>
      <div class="etax-card p-4">
        <p class="text-xs text-gray-400 font-medium">{{ __('Total Tax') }}</p>
        <p class="text-xl font-bold text-violet-600">{{ fmt(totalTax) }}</p>
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
          <input v-model="searchQuery" type="text" :placeholder="__('Search by name...')"
                 class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent" />
        </div>
      </div>
      <select v-model="filterStatus" class="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-violet-500">
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
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Fiscal Year') }}</th>
            <th class="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Total Income') }}</th>
            <th class="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Tax Payable') }}</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Filing Date') }}</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Status') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in filtered" :key="r.name"
              class="border-b border-gray-50 hover:bg-violet-50/50 transition-colors cursor-pointer"
              @click="open(r.name)">
            <td class="py-3 px-4 text-sm font-medium text-violet-600">{{ r.name }}</td>
            <td class="py-3 px-4 text-sm text-gray-700">{{ r.taxpayer_name }}</td>
            <td class="py-3 px-4 text-sm text-gray-600">{{ r.fiscal_year }}</td>
            <td class="py-3 px-4 text-sm text-gray-900 text-right">{{ fmt(r.total_income) }}</td>
            <td class="py-3 px-4 text-sm text-gray-900 font-semibold text-right">{{ fmt(r.tax_payable) }}</td>
            <td class="py-3 px-4 text-sm text-gray-500">{{ r.filing_date }}</td>
            <td class="py-3 px-4"><span :class="statusClass(r.status)">{{ __(r.status) }}</span></td>
          </tr>
          <tr v-if="loading">
            <td colspan="7" class="py-16 text-center text-gray-400">
              <div class="inline-block w-6 h-6 border-2 border-violet-200 border-t-violet-600 rounded-full animate-spin"></div>
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
      doctype: 'Personal Income Tax',
      fields: ['name','taxpayer_name','fiscal_year','total_income','tax_payable','filing_date','status'],
      limit_page_length: 100,
      order_by: 'creation desc'
    })
    records.value = data || []
  } catch (e) { console.warn('PIT load error:', e) } finally { loading.value = false }
})

const totalTax = computed(() => records.value.reduce((s, r) => s + (r.tax_payable || 0), 0))
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

function open(name) { window.location.href = `/app/personal-income-tax/${name}` }
</script>
