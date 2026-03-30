<template>
  <div class="space-y-8">
    <!-- Welcome header with gradient -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-700 via-brand-800 to-brand-900 p-6 sm:p-8 text-white">
      <div class="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -mr-20 -mt-20"></div>
      <div class="absolute bottom-0 left-1/2 w-48 h-48 bg-white/5 rounded-full -mb-24"></div>
      <div class="relative">
        <p class="text-brand-200 text-sm font-medium">Good {{ greeting }} 👋</p>
        <h1 class="mt-1 text-2xl sm:text-3xl font-bold tracking-tight">{{ firstName }}</h1>
        <p class="mt-2 text-brand-200 text-sm">Here's a summary of your employee information</p>
      </div>
    </div>

    <!-- Quick stats -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="(stat, idx) in stats" :key="idx" class="ess-card p-5 group hover:shadow-md dark:hover:shadow-black/20 transition-all duration-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ stat.label }}</p>
            <p class="mt-2 text-2xl sm:text-3xl font-bold" :class="stat.color">{{ stat.value }}</p>
          </div>
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center transition-transform duration-200 group-hover:scale-110" :class="stat.bgColor">
            <div v-html="stat.icon" class="w-6 h-6"></div>
          </div>
        </div>
        <p class="mt-3 text-[11px] text-gray-400 dark:text-gray-500 font-medium">{{ stat.sub }}</p>
      </div>
    </div>

    <!-- Quick actions -->
    <div>
      <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100 mb-4">Quick Actions</h2>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <router-link
          v-for="action in quickActions"
          :key="action.label"
          :to="action.route"
          class="ess-card-interactive p-4 flex flex-col items-center text-center gap-3"
        >
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center" :class="action.bgColor">
            <div v-html="action.icon" class="w-5 h-5"></div>
          </div>
          <span class="text-xs font-semibold text-gray-600 dark:text-gray-300">{{ action.label }}</span>
        </router-link>
      </div>
    </div>

    <!-- Recent leaves & Upcoming holidays -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Leave Applications -->
      <div class="ess-card overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Recent Leave Applications</h3>
          <router-link to="/ess/leaves" class="text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 transition-colors">
            View all →
          </router-link>
        </div>
        <div v-if="recentLeavesLoading" class="p-8 flex justify-center">
          <div class="ess-spinner"></div>
        </div>
        <div v-else-if="recentLeavesData.length" class="divide-y divide-gray-50 dark:divide-gray-700">
          <div v-for="leave in recentLeavesData" :key="leave.name" class="px-6 py-4 flex items-center justify-between hover:bg-gray-50/50 dark:hover:bg-gray-700/50 transition-colors">
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ leave.leave_type }}</p>
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{{ formatDate(leave.from_date) }} — {{ formatDate(leave.to_date) }}</p>
            </div>
            <span :class="statusBadge(leave.status)">{{ leave.status }}</span>
          </div>
        </div>
        <div v-else class="p-10 text-center">
          <div class="w-12 h-12 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-3">
            <svg class="w-6 h-6 text-gray-300 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
          </div>
          <p class="text-sm text-gray-400 dark:text-gray-500">No recent leave applications</p>
        </div>
      </div>

      <!-- Upcoming Holidays -->
      <div class="ess-card overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Upcoming Holidays</h3>
          <router-link to="/ess/holidays" class="text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 transition-colors">
            View all →
          </router-link>
        </div>
        <div v-if="upcomingHolidaysLoading" class="p-8 flex justify-center">
          <div class="ess-spinner"></div>
        </div>
        <div v-else-if="upcomingHolidaysData.length" class="divide-y divide-gray-50 dark:divide-gray-700">
          <div v-for="holiday in upcomingHolidaysData" :key="holiday.name" class="px-6 py-4 flex items-center gap-4 hover:bg-gray-50/50 dark:hover:bg-gray-700/50 transition-colors">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/30 border border-amber-100 dark:border-amber-800 flex flex-col items-center justify-center flex-shrink-0">
              <span class="text-sm font-bold text-amber-700 dark:text-amber-400 leading-none">{{ getDay(holiday.holiday_date) }}</span>
              <span class="text-[9px] font-bold text-amber-500 dark:text-amber-500 uppercase mt-0.5">{{ getMonth(holiday.holiday_date) }}</span>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ holiday.description }}</p>
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{{ getDayOfWeek(holiday.holiday_date) }}</p>
            </div>
          </div>
        </div>
        <div v-else class="p-10 text-center">
          <div class="w-12 h-12 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-3">
            <svg class="w-6 h-6 text-gray-300 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
          </div>
          <p class="text-sm text-gray-400 dark:text-gray-500">No upcoming holidays</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { useEmployeeStore } from '@/stores/employee'
import { DUMMY_LEAVE_BALANCE, DUMMY_RECENT_LEAVES, DUMMY_UPCOMING_HOLIDAYS, isDummyMode } from '@/data/dummy'

const employeeStore = useEmployeeStore()

const firstName = computed(() => {
  const name = employeeStore.employee?.employee_name || 'Employee'
  return name.split(' ')[0]
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'morning'
  if (hour < 17) return 'afternoon'
  return 'evening'
})

// Resources with dummy fallback
const leaveBalanceResource = createResource({ url: 'employee_self_service.api.get_leave_balance', auto: true, onError() {} })
const recentLeavesResource = createResource({ url: 'employee_self_service.api.get_recent_leaves', auto: true, onError() {} })
const upcomingHolidaysResource = createResource({ url: 'employee_self_service.api.get_upcoming_holidays', auto: true, onError() {} })

const recentLeavesLoading = computed(() => recentLeavesResource.loading && !isDummyMode.value)
const upcomingHolidaysLoading = computed(() => upcomingHolidaysResource.loading && !isDummyMode.value)

const recentLeavesData = computed(() => recentLeavesResource.data?.length ? recentLeavesResource.data : (isDummyMode.value ? DUMMY_RECENT_LEAVES : (recentLeavesResource.data || [])))
const upcomingHolidaysData = computed(() => upcomingHolidaysResource.data?.length ? upcomingHolidaysResource.data : (isDummyMode.value ? DUMMY_UPCOMING_HOLIDAYS : (upcomingHolidaysResource.data || [])))

const stats = computed(() => {
  const balance = leaveBalanceResource.data?.length ? leaveBalanceResource.data : (isDummyMode.value ? DUMMY_LEAVE_BALANCE : [])
  const totalLeaves = balance.reduce((sum, b) => sum + (b.total_leaves_allocated || 0), 0)
  const usedLeaves = balance.reduce((sum, b) => sum + (b.leaves_taken || 0), 0)
  const remainingLeaves = balance.reduce((sum, b) => sum + (b.remaining_leaves || 0), 0)
  const pendingLeaves = recentLeavesData.value?.filter(l => l.status === 'Open').length || 0

  return [
    {
      label: 'Total Allocated', value: totalLeaves, color: 'text-brand-700', bgColor: 'bg-brand-50',
      icon: '<svg fill="none" stroke="currentColor" class="text-brand-500" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
      sub: 'Annual allocation',
    },
    {
      label: 'Leaves Taken', value: usedLeaves, color: 'text-amber-700', bgColor: 'bg-amber-50',
      icon: '<svg fill="none" stroke="currentColor" class="text-amber-500" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
      sub: 'This year',
    },
    {
      label: 'Balance Left', value: remainingLeaves, color: 'text-emerald-700', bgColor: 'bg-emerald-50',
      icon: '<svg fill="none" stroke="currentColor" class="text-emerald-500" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
      sub: 'Available leaves',
    },
    {
      label: 'Pending', value: pendingLeaves, color: 'text-brand-700', bgColor: 'bg-brand-50',
      icon: '<svg fill="none" stroke="currentColor" class="text-brand-500" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
      sub: 'Awaiting approval',
    },
  ]
})

const quickActions = [
  { label: 'Apply Leave', route: '/ess/leaves/new', bgColor: 'bg-brand-50', icon: '<svg fill="none" stroke="currentColor" class="text-brand-600" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>' },
  { label: 'View Payslips', route: '/ess/payslips', bgColor: 'bg-emerald-50', icon: '<svg fill="none" stroke="currentColor" class="text-emerald-600" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/></svg>' },
  { label: 'Holidays', route: '/ess/holidays', bgColor: 'bg-amber-50', icon: '<svg fill="none" stroke="currentColor" class="text-amber-600" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>' },
  { label: 'Certificates', route: '/ess/certificates', bgColor: 'bg-sky-50', icon: '<svg fill="none" stroke="currentColor" class="text-sky-600" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/></svg>' },
]

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function statusBadge(status) {
  return { 'Open': 'ess-badge-warning', 'Approved': 'ess-badge-success', 'Rejected': 'ess-badge-danger', 'Cancelled': 'ess-badge-neutral' }[status] || 'ess-badge-info'
}

function getDay(d) { return new Date(d).getDate() }
function getMonth(d) { return new Date(d).toLocaleDateString('en-US', { month: 'short' }) }
function getDayOfWeek(d) { return new Date(d).toLocaleDateString('en-US', { weekday: 'long' }) }
</script>
