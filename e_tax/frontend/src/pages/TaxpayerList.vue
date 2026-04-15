<template>
  <div class="p-8">
    <div class="etax-page-header flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ __('Taxpayers') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ __('Manage taxpayer records') }}</p>
      </div>
      <a href="/app/taxpayer/new"
         class="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
        {{ __('New Taxpayer') }}
      </a>
    </div>

    <!-- Search & Filters -->
    <div class="etax-card p-4 mb-6 flex flex-wrap items-center gap-4">
      <div class="flex-1 min-w-[200px]">
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <input v-model="searchQuery" type="text" :placeholder="__('Search by name or TIN...')"
                 class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
        </div>
      </div>
      <select v-model="filterType" class="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500">
        <option value="">{{ __('All Types') }}</option>
        <option value="Individual">{{ __('Individual') }}</option>
        <option value="Enterprise">{{ __('Enterprise') }}</option>
        <option value="Government">{{ __('Government') }}</option>
        <option value="Non-Profit">{{ __('Non-Profit') }}</option>
      </select>
    </div>

    <!-- Table -->
    <div class="etax-card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">TIN</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Name') }}</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Type') }}</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Phone') }}</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Email') }}</th>
            <th class="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ __('Status') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tp in filteredTaxpayers" :key="tp.name"
              class="border-b border-gray-50 hover:bg-blue-50/50 transition-colors cursor-pointer"
              @click="openTaxpayer(tp.name)">
            <td class="py-3 px-4 text-sm font-mono text-blue-600 font-medium">{{ tp.tax_identification_number }}</td>
            <td class="py-3 px-4">
              <div>
                <p class="text-sm font-medium text-gray-900">{{ tp.taxpayer_name }}</p>
                <p v-if="tp.enterprise_name" class="text-xs text-gray-400">{{ tp.enterprise_name }}</p>
              </div>
            </td>
            <td class="py-3 px-4">
              <span class="text-xs font-medium px-2 py-1 rounded-md"
                    :class="typeClass(tp.taxpayer_type)">{{ __(tp.taxpayer_type) }}</span>
            </td>
            <td class="py-3 px-4 text-sm text-gray-600">{{ tp.phone || '—' }}</td>
            <td class="py-3 px-4 text-sm text-gray-600">{{ tp.email || '—' }}</td>
            <td class="py-3 px-4">
              <span class="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-full">
                <span class="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                {{ __('Active') }}
              </span>
            </td>
          </tr>
          <tr v-if="loading">
            <td colspan="6" class="py-16 text-center text-gray-400">
              <div class="inline-block w-6 h-6 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
              <p class="text-sm mt-2">{{ __('Loading') }}...</p>
            </td>
          </tr>
          <tr v-else-if="!filteredTaxpayers.length">
            <td colspan="6" class="py-16 text-center text-gray-400">
              <p class="text-sm">{{ __('No data available') }}</p>
            </td>
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
const taxpayers = ref([])
const searchQuery = ref('')
const filterType = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await call('frappe.client.get_list', {
      doctype: 'Taxpayer',
      fields: ['name','taxpayer_name','tax_identification_number','taxpayer_type','enterprise_name','phone','email'],
      limit_page_length: 100,
      order_by: 'creation desc'
    })
    taxpayers.value = data || []
  } catch (e) {
    console.warn('Taxpayer load error:', e)
  } finally {
    loading.value = false
  }
})

const filteredTaxpayers = computed(() => {
  let list = taxpayers.value
  if (filterType.value) {
    list = list.filter(t => t.taxpayer_type === filterType.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(t =>
      (t.taxpayer_name || '').toLowerCase().includes(q) ||
      (t.tax_identification_number || '').toLowerCase().includes(q) ||
      (t.enterprise_name || '').toLowerCase().includes(q)
    )
  }
  return list
})

function typeClass(type) {
  const m = {
    'Individual': 'bg-blue-50 text-blue-700',
    'Enterprise': 'bg-purple-50 text-purple-700',
    'Government': 'bg-amber-50 text-amber-700',
    'Non-Profit': 'bg-green-50 text-green-700',
  }
  return m[type] || 'bg-gray-50 text-gray-700'
}

function openTaxpayer(name) {
  window.location.href = `/app/taxpayer/${name}`
}
</script>
