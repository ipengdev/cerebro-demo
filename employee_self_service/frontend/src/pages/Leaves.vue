<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">My Leaves</h1>
        <p class="mt-1 text-sm text-gray-400 dark:text-gray-500">Manage your leave applications and check balances</p>
      </div>
      <router-link to="/ess/leaves/new" class="ess-btn-primary self-start">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Apply Leave
      </router-link>
    </div>

    <!-- Leave Balance Cards -->
    <div>
      <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-3">Leave Balance</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="balance in leaveBalanceData"
          :key="balance.leave_type"
          class="ess-card p-5 hover:shadow-md dark:hover:shadow-black/20 transition-all duration-200"
        >
          <p class="text-sm font-semibold text-gray-700 dark:text-gray-300">{{ balance.leave_type }}</p>
          <div class="mt-3 flex items-end gap-2">
            <span class="text-3xl font-bold text-gray-900 dark:text-gray-100">{{ balance.remaining_leaves }}</span>
            <span class="text-sm text-gray-300 dark:text-gray-600 mb-1 font-medium">/ {{ balance.total_leaves_allocated }}</span>
          </div>
          <div class="mt-3 w-full bg-gray-100 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
            <div
              class="h-2 rounded-full transition-all duration-700 ease-out"
              :class="balance.remaining_leaves > 2 ? 'bg-gradient-to-r from-brand-600 to-brand-600' : 'bg-gradient-to-r from-brand-500 to-brand-600'"
              :style="{ width: Math.min(100, ((balance.total_leaves_allocated - balance.remaining_leaves) / Math.max(balance.total_leaves_allocated, 1)) * 100) + '%' }"
            ></div>
          </div>
          <p class="mt-2 text-[11px] text-gray-400 dark:text-gray-500 font-medium">{{ balance.leaves_taken }} taken</p>
        </div>
      </div>
    </div>

    <!-- Leave Applications Table -->
    <div class="ess-card overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Leave Applications</h3>
        <select v-model="statusFilter" class="text-xs font-medium border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-1.5 text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-300 transition-all">
          <option value="">All Status</option>
          <option value="Open">Pending</option>
          <option value="Approved">Approved</option>
          <option value="Rejected">Rejected</option>
        </select>
      </div>
      <div v-if="filteredLeaves.length" class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-left text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider bg-gray-50/50 dark:bg-gray-800/50">
              <th class="px-6 py-3">Leave Type</th>
              <th class="px-6 py-3">From</th>
              <th class="px-6 py-3">To</th>
              <th class="px-6 py-3">Days</th>
              <th class="px-6 py-3">Status</th>
              <th class="px-6 py-3">Reason</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50 dark:divide-gray-700">
            <tr v-for="leave in filteredLeaves" :key="leave.name" class="hover:bg-brand-50/30 dark:hover:bg-brand-900/20 transition-colors">
              <td class="px-6 py-4 text-sm font-semibold text-gray-900 dark:text-gray-100">{{ leave.leave_type }}</td>
              <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{{ formatDate(leave.from_date) }}</td>
              <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{{ formatDate(leave.to_date) }}</td>
              <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 font-medium">{{ leave.total_leave_days }}</td>
              <td class="px-6 py-4"><span :class="statusBadge(leave.status)">{{ leave.status }}</span></td>
              <td class="px-6 py-4 text-sm text-gray-400 dark:text-gray-500 max-w-xs truncate">{{ leave.description || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="p-12 text-center">
        <div class="w-14 h-14 rounded-2xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center mx-auto mb-3">
          <svg class="w-7 h-7 text-gray-300 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
        </div>
        <p class="text-sm font-medium text-gray-400 dark:text-gray-500">No leave applications found</p>
        <router-link to="/ess/leaves/new" class="mt-3 inline-block text-sm font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300">
          Apply for leave →
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { DUMMY_LEAVE_BALANCE, DUMMY_LEAVE_APPLICATIONS, isDummyMode } from '@/data/dummy'

const statusFilter = ref('')

const leaveBalance = createResource({ url: 'employee_self_service.api.get_leave_balance', auto: true, onError() {} })
const leaveApplications = createResource({ url: 'employee_self_service.api.get_leave_applications', auto: true, onError() {} })

const leaveBalanceData = computed(() => leaveBalance.data?.length ? leaveBalance.data : (isDummyMode.value ? DUMMY_LEAVE_BALANCE : []))
const leaveAppsData = computed(() => leaveApplications.data?.length ? leaveApplications.data : (isDummyMode.value ? DUMMY_LEAVE_APPLICATIONS : []))

const filteredLeaves = computed(() => {
  const leaves = leaveAppsData.value
  if (!statusFilter.value) return leaves
  return leaves.filter(l => l.status === statusFilter.value)
})

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function statusBadge(status) {
  return { 'Open': 'ess-badge-warning', 'Approved': 'ess-badge-success', 'Rejected': 'ess-badge-danger', 'Cancelled': 'ess-badge-neutral' }[status] || 'ess-badge-info'
}
</script>
