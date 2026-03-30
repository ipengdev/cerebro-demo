<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Certificates</h1>
        <p class="mt-1 text-sm text-gray-400 dark:text-gray-500">Request and track employee certificates</p>
      </div>
      <button @click="showModal = true" class="ess-btn-primary">
        <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Request
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-12"><div class="ess-spinner w-8 h-8"></div></div>

    <div v-else-if="!certData.length" class="ess-card p-12 text-center text-sm text-gray-400 dark:text-gray-500">No certificate requests found.</div>

    <div v-else class="space-y-3">
      <div v-for="c in certData" :key="c.name" class="ess-card p-5 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-brand-600 to-brand-700 flex items-center justify-center shadow-md shadow-brand-200/50 dark:shadow-none">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          </div>
          <div>
            <div class="font-semibold text-gray-900 dark:text-gray-100">{{ c.certificate_type || c.name }}</div>
            <div class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">Requested {{ c.requested_date || c.creation }}</div>
          </div>
        </div>
        <span :class="statusBadge(c.status)">{{ c.status }}</span>
      </div>
    </div>

    <!-- Request Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm" @click="showModal = false"></div>
        <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-5">
          <h2 class="text-lg font-bold text-gray-900 dark:text-gray-100">Request Certificate</h2>
          <div>
            <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Certificate Type</label>
            <select v-model="reqForm.certificate_type" class="w-full border border-gray-200 dark:border-gray-600 rounded-xl px-4 py-3 text-sm bg-white dark:bg-gray-700 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-300">
              <option value="" disabled>Select type</option>
              <option>Employment Certificate</option>
              <option>Salary Certificate</option>
              <option>Experience Certificate</option>
              <option>Service Certificate</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Reason / Notes</label>
            <textarea v-model="reqForm.reason" rows="3" placeholder="Optional notes..." class="w-full border border-gray-200 dark:border-gray-600 rounded-xl px-4 py-3 text-sm bg-white dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-300 resize-none"></textarea>
          </div>
          <div v-if="successMsg" class="bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 rounded-xl p-3 text-sm text-emerald-700 dark:text-emerald-300">{{ successMsg }}</div>
          <div class="flex items-center gap-3 pt-1">
            <button @click="submitRequest" :disabled="!reqForm.certificate_type" class="ess-btn-primary disabled:opacity-50">Submit Request</button>
            <button @click="showModal = false" class="ess-btn-secondary">Cancel</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { DUMMY_CERTIFICATES, isDummyMode } from '@/data/dummy'

const showModal = ref(false)
const successMsg = ref('')
const reqForm = ref({ certificate_type: '', reason: '' })

const certs = createResource({ url: 'employee_self_service.api.get_certificates', auto: true, onError() {} })
const loading = computed(() => certs.loading)

const certData = computed(() => {
  if (certs.data?.length) return certs.data
  if (isDummyMode.value) return DUMMY_CERTIFICATES
  return []
})

const submitCert = createResource({ url: 'employee_self_service.api.request_certificate', onSuccess() { successMsg.value = 'Certificate request submitted!'; certs.reload(); setTimeout(() => { showModal.value = false; successMsg.value = '' }, 1200) } })

function submitRequest() {
  if (isDummyMode.value) { successMsg.value = 'Demo mode — request would be submitted here.'; return }
  submitCert.fetch({ certificate_type: reqForm.value.certificate_type, reason: reqForm.value.reason })
}

function statusBadge(s) {
  const m = { Approved:'ess-badge-success', Pending:'ess-badge-warning', Rejected:'ess-badge-danger', Completed:'ess-badge-info' }
  return m[s] || 'ess-badge-neutral'
}
</script>
