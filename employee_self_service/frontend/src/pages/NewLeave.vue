<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <router-link to="/ess/leaves" class="p-2 rounded-xl hover:bg-white dark:hover:bg-gray-700 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-gray-600 hover:shadow-sm">
        <svg class="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </router-link>
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Apply for Leave</h1>
        <p class="mt-1 text-sm text-gray-400 dark:text-gray-500">Submit a new leave application</p>
      </div>
    </div>

    <div class="ess-card max-w-2xl overflow-hidden">
      <div class="p-6 sm:p-8 space-y-6">
        <div>
          <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Leave Type</label>
          <select v-model="form.leave_type" class="w-full border border-gray-200 dark:border-gray-600 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-300 transition-all">
            <option value="" disabled>Select leave type</option>
            <option v-for="lt in leaveTypesData" :key="lt.name" :value="lt.name">{{ lt.name }}</option>
          </select>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">From Date</label>
            <input v-model="form.from_date" type="date" class="w-full border border-gray-200 dark:border-gray-600 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-300 transition-all" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">To Date</label>
            <input v-model="form.to_date" type="date" class="w-full border border-gray-200 dark:border-gray-600 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-300 transition-all" />
          </div>
        </div>

        <div class="flex items-center gap-3">
          <input v-model="form.half_day" type="checkbox" id="half_day" class="w-4 h-4 text-brand-600 border-gray-300 dark:border-gray-600 rounded focus:ring-brand-500 dark:bg-gray-700" />
          <label for="half_day" class="text-sm font-medium text-gray-700 dark:text-gray-300">Half Day</label>
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Reason</label>
          <textarea v-model="form.reason" rows="4" placeholder="Enter your reason for leave..." class="w-full border border-gray-200 dark:border-gray-600 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-300 transition-all resize-none placeholder:dark:text-gray-500"></textarea>
        </div>

        <div v-if="submitLeave.error" class="bg-brand-50 dark:bg-brand-900/30 border border-brand-200 dark:border-brand-800 rounded-xl p-4">
          <p class="text-sm text-brand-700 dark:text-brand-300">{{ submitLeave.error }}</p>
        </div>
        <div v-if="successMessage" class="bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 rounded-xl p-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <p class="text-sm font-medium text-emerald-700 dark:text-emerald-300">{{ successMessage }}</p>
        </div>

        <div class="flex items-center gap-3 pt-2">
          <button @click="handleSubmit" :disabled="submitLeave.loading || !isFormValid" class="ess-btn-primary disabled:opacity-50 disabled:cursor-not-allowed">
            <div v-if="submitLeave.loading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            {{ submitLeave.loading ? 'Submitting...' : 'Submit Application' }}
          </button>
          <router-link to="/ess/leaves" class="ess-btn-secondary">Cancel</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { DUMMY_LEAVE_TYPES, isDummyMode } from '@/data/dummy'

const router = useRouter()
const successMessage = ref('')
const form = ref({ leave_type: '', from_date: '', to_date: '', half_day: false, reason: '' })

const leaveTypes = createResource({ url: 'employee_self_service.api.get_leave_types', auto: true, onError() {} })
const leaveTypesData = computed(() => leaveTypes.data?.length ? leaveTypes.data : (isDummyMode.value ? DUMMY_LEAVE_TYPES : []))

const submitLeave = createResource({
  url: 'employee_self_service.api.apply_leave',
  onSuccess() {
    successMessage.value = 'Leave application submitted successfully!'
    setTimeout(() => router.push('/ess/leaves'), 1500)
  },
})

const isFormValid = computed(() => form.value.leave_type && form.value.from_date && form.value.to_date)

function handleSubmit() {
  if (isDummyMode.value) {
    successMessage.value = 'Demo mode — leave application would be submitted here.'
    return
  }
  submitLeave.fetch({ leave_type: form.value.leave_type, from_date: form.value.from_date, to_date: form.value.to_date, half_day: form.value.half_day ? 1 : 0, reason: form.value.reason })
}
</script>
