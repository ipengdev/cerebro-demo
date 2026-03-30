import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createResource } from 'frappe-ui'
import { DUMMY_EMPLOYEE, DUMMY_LEAVE_BALANCE, isDummyMode } from '@/data/dummy'

export const useEmployeeStore = defineStore('employee', () => {
  const employee = ref(null)
  const leaveBalance = ref([])
  const loading = ref(false)
  const usingDummy = ref(false)

  const employeeResource = createResource({
    url: 'employee_self_service.api.get_employee_details',
    auto: false,
    onSuccess(data) {
      employee.value = data
      usingDummy.value = false
    },
    onError() {
      // Fallback to dummy data — remove when real Employee records exist
      employee.value = { ...DUMMY_EMPLOYEE }
      usingDummy.value = true
      isDummyMode.value = true
    },
  })

  const leaveBalanceResource = createResource({
    url: 'employee_self_service.api.get_leave_balance',
    auto: false,
    onSuccess(data) {
      leaveBalance.value = data
    },
    onError() {
      leaveBalance.value = [...DUMMY_LEAVE_BALANCE]
    },
  })

  function fetchEmployee() {
    if (!employee.value) {
      loading.value = true
      employeeResource.fetch().catch(() => {}).finally(() => {
        loading.value = false
      })
    }
  }

  function fetchLeaveBalance() {
    leaveBalanceResource.fetch().catch(() => {})
  }

  return {
    employee,
    leaveBalance,
    loading,
    usingDummy,
    fetchEmployee,
    fetchLeaveBalance,
  }
})
