<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Attendance</h1>
      <p class="mt-1 text-sm text-gray-400 dark:text-gray-500">Your daily attendance records</p>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <input v-model="monthInput" type="month" class="border border-gray-200 dark:border-gray-600 rounded-xl px-4 py-2.5 text-sm bg-white dark:bg-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-300 transition-all" />
      <button @click="fetchData" class="ess-btn-primary text-sm">Load</button>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div v-for="s in summary" :key="s.label" class="ess-stat-card text-center">
        <div class="text-3xl font-bold" :class="s.color">{{ s.value }}</div>
        <div class="mt-1 text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide">{{ s.label }}</div>
      </div>
    </div>

    <!-- Table -->
    <div class="ess-card overflow-hidden">
      <div v-if="loading" class="p-12 flex justify-center"><div class="ess-spinner w-8 h-8"></div></div>
      <div v-else-if="!rows.length" class="p-12 text-center text-sm text-gray-400 dark:text-gray-500">No attendance records found for this month.</div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-100 dark:border-gray-700 bg-gray-50/60 dark:bg-gray-800/60">
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Date</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Status</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide hidden sm:table-cell">Check-in</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide hidden sm:table-cell">Check-out</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide hidden md:table-cell">Hours</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rows" :key="r.attendance_date" class="border-b border-gray-50 dark:border-gray-700 hover:bg-brand-50/40 dark:hover:bg-brand-900/20 transition-colors">
              <td class="px-5 py-3.5 font-medium text-gray-800 dark:text-gray-200">{{ formatDate(r.attendance_date) }}</td>
              <td class="px-5 py-3.5">
                <span :class="statusBadge(r.status)">{{ r.status }}</span>
              </td>
              <td class="px-5 py-3.5 text-gray-500 dark:text-gray-400 hidden sm:table-cell">{{ r.check_in || '—' }}</td>
              <td class="px-5 py-3.5 text-gray-500 dark:text-gray-400 hidden sm:table-cell">{{ r.check_out || '—' }}</td>
              <td class="px-5 py-3.5 text-gray-500 dark:text-gray-400 hidden md:table-cell">{{ r.working_hours ? r.working_hours.toFixed(1) + 'h' : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { DUMMY_ATTENDANCE, isDummyMode } from '@/data/dummy'

const now = new Date()
const monthInput = ref(`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`)

const attendance = createResource({ url: 'employee_self_service.api.get_attendance', onError() {} })
const loading = computed(() => attendance.loading)

function fetchData() {
  const [y,m] = monthInput.value.split('-')
  attendance.fetch({ month: parseInt(m), year: parseInt(y) })
}
onMounted(fetchData)

const rows = computed(() => {
  if (attendance.data?.length) return attendance.data
  if (isDummyMode.value) return DUMMY_ATTENDANCE
  return []
})

const summary = computed(() => {
  const data = rows.value
  const present = data.filter(r => r.status === 'Present').length
  const absent = data.filter(r => r.status === 'Absent').length
  const leave = data.filter(r => r.status === 'On Leave').length
  const halfDay = data.filter(r => r.status === 'Half Day').length
  return [
    { label: 'Present', value: present, color: 'text-emerald-600' },
    { label: 'Absent', value: absent, color: 'text-brand-500' },
    { label: 'On Leave', value: leave, color: 'text-amber-500' },
    { label: 'Half Day', value: halfDay, color: 'text-brand-500' },
  ]
})

function formatDate(d) { return new Date(d+'T00:00:00').toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short'}) }
function statusBadge(s) {
  const m = { Present:'ess-badge-success', Absent:'ess-badge-danger', 'On Leave':'ess-badge-warning', 'Half Day':'ess-badge-info' }
  return m[s] || 'ess-badge-neutral'
}
</script>
