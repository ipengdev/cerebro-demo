// ============================================================
// DUMMY / DEMO DATA for Employee Self Service Portal
// Generic placeholder data used as fallback when API is unavailable
// ============================================================

export const DUMMY_EMPLOYEE = {
  name: 'HR-EMP-00001',
  employee_name: 'John Doe',
  company: 'My Company',
  department: 'Engineering',
  designation: 'Software Engineer',
  date_of_joining: '2024-01-15',
  date_of_birth: '1990-06-01',
  gender: 'Male',
  status: 'Active',
  personal_email: 'john.doe@example.com',
  company_email: 'john@example.com',
  cell_phone: '+1 555 123 4567',
  emergency_phone_number: '+1 555 987 6543',
  reports_to: 'HR-EMP-00002',
  reports_to_name: 'Jane Smith',
  image: null,
  holiday_list: null,
}

export const DUMMY_LEAVE_BALANCE = [
  { leave_type: 'Annual Leave', total_leaves_allocated: 21, leaves_taken: 8, remaining_leaves: 13 },
  { leave_type: 'Sick Leave', total_leaves_allocated: 12, leaves_taken: 2, remaining_leaves: 10 },
  { leave_type: 'Casual Leave', total_leaves_allocated: 7, leaves_taken: 3, remaining_leaves: 4 },
  { leave_type: 'Compensatory Off', total_leaves_allocated: 3, leaves_taken: 1, remaining_leaves: 2 },
]

export const DUMMY_LEAVE_APPLICATIONS = [
  { name: 'HR-LAP-00005', leave_type: 'Annual Leave', from_date: '2026-04-14', to_date: '2026-04-18', total_leave_days: 5, status: 'Open', description: 'Family vacation', posting_date: '2026-03-25' },
  { name: 'HR-LAP-00004', leave_type: 'Sick Leave', from_date: '2026-03-10', to_date: '2026-03-11', total_leave_days: 2, status: 'Approved', description: 'Doctor appointment', posting_date: '2026-03-10' },
  { name: 'HR-LAP-00003', leave_type: 'Casual Leave', from_date: '2026-02-20', to_date: '2026-02-20', total_leave_days: 1, status: 'Approved', description: 'Personal errand', posting_date: '2026-02-18' },
  { name: 'HR-LAP-00002', leave_type: 'Annual Leave', from_date: '2026-01-06', to_date: '2026-01-10', total_leave_days: 5, status: 'Approved', description: 'Winter holiday', posting_date: '2025-12-20' },
  { name: 'HR-LAP-00001', leave_type: 'Compensatory Off', from_date: '2025-12-24', to_date: '2025-12-24', total_leave_days: 1, status: 'Rejected', description: 'Worked on Saturday', posting_date: '2025-12-15' },
]

export const DUMMY_RECENT_LEAVES = DUMMY_LEAVE_APPLICATIONS.slice(0, 5).map(l => ({
  name: l.name,
  leave_type: l.leave_type,
  from_date: l.from_date,
  to_date: l.to_date,
  status: l.status,
}))

export const DUMMY_LEAVE_TYPES = [
  { name: 'Annual Leave' },
  { name: 'Sick Leave' },
  { name: 'Casual Leave' },
  { name: 'Compensatory Off' },
  { name: 'Unpaid Leave' },
]

export const DUMMY_ATTENDANCE = (() => {
  const data = []
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const daysInMonth = new Date(year, month, 0).getDate()
  const statuses = ['Present', 'Present', 'Present', 'Present', 'Present', 'Absent', 'Half Day', 'On Leave', 'Work From Home']
  const today = now.getDate()

  for (let day = 1; day <= Math.min(daysInMonth, today); day++) {
    const d = new Date(year, month - 1, day)
    const dow = d.getDay()
    if (dow === 0 || dow === 6) continue // skip weekends

    const status = day === 10 ? 'Absent' : day === 15 ? 'Half Day' : day === 20 ? 'On Leave' : day === 12 ? 'Work From Home' : 'Present'
    const hours = status === 'Present' ? (7.5 + Math.random() * 1.5) : status === 'Half Day' ? (3.5 + Math.random()) : status === 'Work From Home' ? (7 + Math.random() * 2) : 0

    data.push({
      name: `ATT-2026-${String(day).padStart(4, '0')}`,
      attendance_date: `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
      status,
      working_hours: hours > 0 ? parseFloat(hours.toFixed(1)) : 0,
    })
  }
  return data
})()

export const DUMMY_PAYSLIPS = [
  {
    name: 'SAL-SLP-00003',
    start_date: '2026-03-01',
    end_date: '2026-03-31',
    gross_pay: 5000,
    total_deduction: 750,
    net_pay: 4250,
    posting_date: '2026-03-28',
    earnings: [
      { salary_component: 'Basic Salary', amount: 3500 },
      { salary_component: 'Housing Allowance', amount: 800 },
      { salary_component: 'Transportation', amount: 400 },
      { salary_component: 'Other Allowance', amount: 300 },
    ],
    deductions: [
      { salary_component: 'Social Security', amount: 375 },
      { salary_component: 'Income Tax', amount: 250 },
      { salary_component: 'Health Insurance', amount: 125 },
    ],
  },
  {
    name: 'SAL-SLP-00002',
    start_date: '2026-02-01',
    end_date: '2026-02-28',
    gross_pay: 5000,
    total_deduction: 750,
    net_pay: 4250,
    posting_date: '2026-02-28',
    earnings: [
      { salary_component: 'Basic Salary', amount: 3500 },
      { salary_component: 'Housing Allowance', amount: 800 },
      { salary_component: 'Transportation', amount: 400 },
      { salary_component: 'Other Allowance', amount: 300 },
    ],
    deductions: [
      { salary_component: 'Social Security', amount: 375 },
      { salary_component: 'Income Tax', amount: 250 },
      { salary_component: 'Health Insurance', amount: 125 },
    ],
  },
  {
    name: 'SAL-SLP-00001',
    start_date: '2026-01-01',
    end_date: '2026-01-31',
    gross_pay: 5000,
    total_deduction: 750,
    net_pay: 4250,
    posting_date: '2026-01-31',
    earnings: [
      { salary_component: 'Basic Salary', amount: 3500 },
      { salary_component: 'Housing Allowance', amount: 800 },
      { salary_component: 'Transportation', amount: 400 },
      { salary_component: 'Other Allowance', amount: 300 },
    ],
    deductions: [
      { salary_component: 'Social Security', amount: 375 },
      { salary_component: 'Income Tax', amount: 250 },
      { salary_component: 'Health Insurance', amount: 125 },
    ],
  },
]

export const DUMMY_HOLIDAYS = [
  { name: 'HOL-001', holiday_date: '2026-01-01', description: "New Year's Day", weekly_off: 0 },
  { name: 'HOL-002', holiday_date: '2026-05-01', description: 'Labour Day', weekly_off: 0 },
  { name: 'HOL-003', holiday_date: '2026-12-25', description: 'Christmas Day', weekly_off: 0 },
]

export const DUMMY_UPCOMING_HOLIDAYS = DUMMY_HOLIDAYS.filter(h => new Date(h.holiday_date) >= new Date()).slice(0, 5)

export const DUMMY_CERTIFICATES = [
  { name: 'TODO-00003', certificate_type: 'Employment Certificate', status: 'Completed', creation: '2026-03-15', description: '[Certificate Request] Employment Certificate' },
  { name: 'TODO-00002', certificate_type: 'Salary Certificate', status: 'Open', creation: '2026-03-22', description: '[Certificate Request] Salary Certificate' },
  { name: 'TODO-00001', certificate_type: 'Experience Certificate', status: 'Open', creation: '2026-02-10', description: '[Certificate Request] Experience Certificate' },
]

// Flag to check if we're using dummy data — shown as banner in UI
export const isDummyMode = { value: false }
