<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Holidays</h1>
      <p class="mt-1 text-sm text-gray-400 dark:text-gray-500">Company holiday calendar for the year</p>
    </div>

    <!-- Upcoming -->
    <div v-if="upcoming.length" class="ess-card overflow-hidden">
      <div class="px-5 py-4 border-b border-gray-100 dark:border-gray-700 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20">
        <h2 class="text-sm font-semibold text-amber-800 dark:text-amber-400">Upcoming Holidays</h2>
      </div>
      <div class="divide-y divide-gray-50 dark:divide-gray-700">
        <div v-for="h in upcoming" :key="h.name" class="flex items-center gap-4 px-5 py-4 hover:bg-amber-50/30 dark:hover:bg-amber-900/20 transition-colors">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex flex-col items-center justify-center text-white shadow-md shadow-orange-200/50 dark:shadow-none">
            <div class="text-[10px] font-bold uppercase leading-none">{{ monthShort(h.holiday_date) }}</div>
            <div class="text-lg font-bold leading-tight">{{ dayNum(h.holiday_date) }}</div>
          </div>
          <div>
            <div class="font-semibold text-gray-900 dark:text-gray-100">{{ h.description || h.holiday_date }}</div>
            <div class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{{ weekday(h.holiday_date) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- All Holidays -->
    <div class="ess-card overflow-hidden">
      <div v-if="loading" class="p-12 flex justify-center"><div class="ess-spinner w-8 h-8"></div></div>
      <div v-else-if="!holidayData.length" class="p-12 text-center text-sm text-gray-400 dark:text-gray-500">No holidays found.</div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-gray-700 bg-gray-50/60 dark:bg-gray-800/60">
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Date</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Day</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Holiday</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in holidayData" :key="h.name" class="border-b border-gray-50 dark:border-gray-700 hover:bg-brand-50/40 dark:hover:bg-brand-900/20 transition-colors" :class="isPast(h.holiday_date) ? 'opacity-50' : ''">
              <td class="px-5 py-3.5 font-medium text-gray-800 dark:text-gray-200">{{ formatDate(h.holiday_date) }}</td>
              <td class="px-5 py-3.5 text-gray-500 dark:text-gray-400">{{ weekday(h.holiday_date) }}</td>
              <td class="px-5 py-3.5 text-gray-700 dark:text-gray-300">{{ h.description }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { createResource } from 'frappe-ui'
import { DUMMY_HOLIDAYS, DUMMY_UPCOMING_HOLIDAYS, isDummyMode } from '@/data/dummy'

const holidays = createResource({ url: 'employee_self_service.api.get_holidays', auto: true, onError() {} })
const loading = computed(() => holidays.loading)

const holidayData = computed(() => {
  if (holidays.data?.length) return holidays.data
  if (isDummyMode.value) return DUMMY_HOLIDAYS
  return []
})

const upcoming = computed(() => {
  const today = new Date().toISOString().slice(0,10)
  const fromApi = holidayData.value.filter(h => h.holiday_date >= today).slice(0,5)
  return fromApi.length ? fromApi : (isDummyMode.value ? DUMMY_UPCOMING_HOLIDAYS : [])
})

function formatDate(d) { return new Date(d+'T00:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}) }
function weekday(d) { return new Date(d+'T00:00:00').toLocaleDateString('en-GB',{weekday:'long'}) }
function monthShort(d) { return new Date(d+'T00:00:00').toLocaleDateString('en-GB',{month:'short'}) }
function dayNum(d) { return new Date(d+'T00:00:00').getDate() }
function isPast(d) { return d < new Date().toISOString().slice(0,10) }
</script>
