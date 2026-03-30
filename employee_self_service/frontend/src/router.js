import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/ess',
  },
  {
    path: '/ess',
    name: 'ESS',
    component: () => import('@/components/AppLayout.vue'),
    redirect: '/ess/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard.vue'),
      },
      {
        path: 'leaves',
        name: 'Leaves',
        component: () => import('@/pages/Leaves.vue'),
      },
      {
        path: 'leaves/new',
        name: 'NewLeave',
        component: () => import('@/pages/NewLeave.vue'),
      },
      {
        path: 'attendance',
        name: 'Attendance',
        component: () => import('@/pages/Attendance.vue'),
      },
      {
        path: 'payslips',
        name: 'Payslips',
        component: () => import('@/pages/Payslips.vue'),
      },
      {
        path: 'holidays',
        name: 'Holidays',
        component: () => import('@/pages/Holidays.vue'),
      },
      {
        path: 'certificates',
        name: 'Certificates',
        component: () => import('@/pages/Certificates.vue'),
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/pages/Profile.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  // Simple auth check
  if (window.csrf_token && window.csrf_token !== 'None') {
    next()
  } else if (to.name !== 'Login') {
    window.location.href = '/login?redirect-to=' + to.fullPath
  } else {
    next()
  }
})

export default router
