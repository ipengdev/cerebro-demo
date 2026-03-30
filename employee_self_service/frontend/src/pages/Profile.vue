<template>
  <div class="space-y-6">
    <!-- Loading state -->
    <div v-if="!emp.name" class="flex items-center justify-center py-20">
      <div class="ess-spinner"></div>
    </div>

    <template v-else>
      <!-- Profile header -->
      <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-700 via-brand-800 to-brand-900 p-6 sm:p-8">
        <div class="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -mr-20 -mt-20"></div>
        <div class="absolute bottom-0 left-1/3 w-48 h-48 bg-white/5 rounded-full -mb-32"></div>
        <div class="relative flex flex-col sm:flex-row items-start sm:items-center gap-5">
          <div class="w-20 h-20 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center ring-4 ring-white/20 flex-shrink-0">
            <span class="text-2xl font-bold text-white">{{ initials }}</span>
          </div>
          <div class="text-white">
            <h1 class="text-2xl font-bold tracking-tight">{{ emp.employee_name }}</h1>
            <p class="text-brand-200 text-sm mt-1">{{ emp.designation || 'Employee' }}</p>
            <div class="flex flex-wrap items-center gap-2 mt-3">
              <span class="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-white/20 text-white backdrop-blur-sm">
                {{ emp.name }}
              </span>
              <span v-if="emp.department" class="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-white/10 text-brand-100">
                {{ emp.department }}
              </span>
              <span v-if="emp.status" class="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold"
                    :class="emp.status === 'Active' ? 'bg-emerald-400/20 text-emerald-100' : 'bg-brand-400/20 text-brand-100'">
                <span class="w-1.5 h-1.5 rounded-full mr-1.5" :class="emp.status === 'Active' ? 'bg-emerald-300' : 'bg-red-300'"></span>
                {{ emp.status }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Info sections -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Personal Information -->
        <div class="ess-card overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-brand-50 dark:bg-brand-900/40 flex items-center justify-center">
              <svg class="w-4 h-4 text-brand-600 dark:text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </div>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Personal Information</h3>
          </div>
          <div class="p-6 space-y-4">
            <InfoRow label="Full Name" :value="emp.employee_name" />
            <InfoRow label="Date of Birth" :value="formatDate(emp.date_of_birth)" />
            <InfoRow label="Gender" :value="emp.gender" />
            <InfoRow label="Personal Email" :value="emp.personal_email" />
            <InfoRow label="Cell Phone" :value="emp.cell_phone" />
            <InfoRow label="Emergency Contact" :value="emp.emergency_phone_number" />
          </div>
        </div>

        <!-- Employment Information -->
        <div class="ess-card overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-brand-50 dark:bg-brand-900/40 flex items-center justify-center">
              <svg class="w-4 h-4 text-brand-600 dark:text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
            </div>
            <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Employment Information</h3>
          </div>
          <div class="p-6 space-y-4">
            <InfoRow label="Employee ID" :value="emp.name" />
            <InfoRow label="Company" :value="emp.company" />
            <InfoRow label="Department" :value="emp.department" />
            <InfoRow label="Designation" :value="emp.designation" />
            <InfoRow label="Date of Joining" :value="formatDate(emp.date_of_joining)" />
            <InfoRow label="Reports To" :value="emp.reports_to_name || emp.reports_to" />
            <InfoRow label="Company Email" :value="emp.company_email" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, h } from 'vue'
import { useEmployeeStore } from '@/stores/employee'

const employeeStore = useEmployeeStore()
const emp = computed(() => employeeStore.employee || {})

const initials = computed(() => {
  const name = emp.value.employee_name || ''
  const parts = name.split(' ')
  return parts.length >= 2
    ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    : name.substring(0, 2).toUpperCase()
})

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
}

const InfoRow = {
  props: ['label', 'value'],
  setup(props) {
    return () => h('div', { class: 'flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-0 py-0.5' }, [
      h('span', { class: 'text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide sm:w-40 flex-shrink-0' }, props.label),
      h('span', { class: 'text-sm font-medium text-gray-900 dark:text-gray-200' }, props.value || '—'),
    ])
  },
}
</script>
