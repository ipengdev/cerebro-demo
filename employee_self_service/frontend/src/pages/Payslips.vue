<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Payslips</h1>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Your salary slips and payment history</p>
    </div>

    <div v-if="loading" class="flex justify-center py-12"><div class="ess-spinner w-8 h-8"></div></div>

    <div v-else-if="!payslipData.length" class="ess-card p-12 text-center text-sm text-gray-500 dark:text-gray-400">No payslips found.</div>

    <div v-else class="space-y-4">
      <div v-for="slip in payslipData" :key="slip.name" class="ess-card overflow-hidden">
        <button @click="toggle(slip.name)" class="w-full flex items-center justify-between p-5 hover:bg-gray-50/60 dark:hover:bg-gray-700/50 transition-colors">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 flex flex-col items-center justify-center text-white shadow-md shadow-brand-200/50 dark:shadow-none leading-none">
              <span class="text-[11px] font-semibold uppercase tracking-wide opacity-90">{{ getMonth(slip).short }}</span>
              <span class="text-base font-bold -mt-0.5">{{ getMonth(slip).year }}</span>
            </div>
            <div class="text-left">
              <div class="font-semibold text-gray-900 dark:text-gray-100">{{ getMonth(slip).full }} {{ getMonth(slip).year }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Posted {{ formatDate(slip.posting_date) }}</div>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <div class="text-right">
              <div class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ formatCurrency(slip.net_pay) }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 font-medium">Net Pay</div>
            </div>
            <svg class="w-5 h-5 text-gray-400 dark:text-gray-500 transition-transform duration-200" :class="{'rotate-180': expanded === slip.name}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
          </div>
        </button>

        <div v-if="expanded === slip.name" class="border-t border-gray-100 dark:border-gray-700 bg-gray-50/40 dark:bg-gray-900/40 p-5 space-y-5">
          <!-- Summary cards -->
          <div class="grid grid-cols-3 gap-3">
            <div class="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-4 text-center">
              <div class="text-[11px] text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Gross Pay</div>
              <div class="text-base font-bold text-gray-900 dark:text-gray-100 mt-1">{{ formatCurrency(slip.gross_pay) }}</div>
            </div>
            <div class="rounded-xl bg-brand-50 dark:bg-brand-900/30 border border-brand-100 dark:border-brand-800 p-4 text-center">
              <div class="text-[11px] text-brand-600 dark:text-brand-400 uppercase tracking-wider font-semibold">Deductions</div>
              <div class="text-base font-bold text-brand-700 dark:text-brand-300 mt-1">{{ formatCurrency(slip.total_deduction) }}</div>
            </div>
            <div class="rounded-xl bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-100 dark:border-emerald-800 p-4 text-center">
              <div class="text-[11px] text-emerald-600 dark:text-emerald-400 uppercase tracking-wider font-semibold">Net Pay</div>
              <div class="text-base font-bold text-emerald-700 dark:text-emerald-300 mt-1">{{ formatCurrency(slip.net_pay) }}</div>
            </div>
          </div>

          <!-- Earnings -->
          <div v-if="slip.earnings?.length">
            <div class="flex items-center gap-2 mb-3">
              <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
              <div class="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Earnings</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 divide-y divide-gray-50 dark:divide-gray-700">
              <div v-for="e in slip.earnings" :key="e.salary_component" class="flex justify-between items-center px-4 py-3 text-sm">
                <span class="text-gray-700 dark:text-gray-300">{{ e.salary_component }}</span>
                <span class="font-semibold text-gray-900 dark:text-gray-100">{{ formatCurrency(e.amount) }}</span>
              </div>
            </div>
          </div>

          <!-- Deductions -->
          <div v-if="slip.deductions?.length">
            <div class="flex items-center gap-2 mb-3">
              <div class="w-1.5 h-1.5 rounded-full bg-brand-500"></div>
              <div class="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Deductions</div>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 divide-y divide-gray-50 dark:divide-gray-700">
              <div v-for="d in slip.deductions" :key="d.salary_component" class="flex justify-between items-center px-4 py-3 text-sm">
                <span class="text-gray-700 dark:text-gray-300">{{ d.salary_component }}</span>
                <span class="font-semibold text-brand-700 dark:text-brand-400">{{ formatCurrency(d.amount) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { DUMMY_PAYSLIPS, isDummyMode } from '@/data/dummy'

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
const SHORT_MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

const expanded = ref(null)
const payslips = createResource({ url: 'employee_self_service.api.get_payslips', auto: true, onError() {} })
const loading = computed(() => payslips.loading)

const payslipData = computed(() => {
  if (payslips.data?.length) return payslips.data
  if (isDummyMode.value) return DUMMY_PAYSLIPS
  return []
})

function getMonth(slip) {
  const d = new Date(slip.start_date || slip.posting_date)
  const m = d.getMonth()
  return { full: MONTHS[m], short: SHORT_MONTHS[m], year: d.getFullYear() }
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function toggle(name) { expanded.value = expanded.value === name ? null : name }
function formatCurrency(v) { return v != null ? Number(v).toLocaleString('en-US', { minimumFractionDigits: 0 }) + ' LBP' : '—' }
</script>
