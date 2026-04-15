import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/e-tax/dashboard',
  },
  {
    path: '/e-tax',
    name: 'ETax',
    redirect: '/e-tax/dashboard',
  },
  {
    path: '/e-tax/dashboard',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    path: '/e-tax/taxpayers',
    name: 'Taxpayers',
    component: () => import('@/pages/TaxpayerList.vue'),
  },
  {
    path: '/e-tax/enterprise-declarations',
    name: 'EnterpriseDeclarations',
    component: () => import('@/pages/EnterpriseDeclarationList.vue'),
  },
  {
    path: '/e-tax/vat-returns',
    name: 'VATReturns',
    component: () => import('@/pages/VATReturnList.vue'),
  },
  {
    path: '/e-tax/personal-income-tax',
    name: 'PersonalIncomeTax',
    component: () => import('@/pages/PersonalIncomeTaxList.vue'),
  },
  {
    path: '/e-tax/customs-declarations',
    name: 'CustomsDeclarations',
    component: () => import('@/pages/CustomsDeclarationList.vue'),
  },
  {
    path: '/e-tax/excise-duty-returns',
    name: 'ExciseDutyReturns',
    component: () => import('@/pages/ExciseDutyReturnList.vue'),
  },
  {
    path: '/e-tax/settings',
    name: 'Settings',
    component: () => import('@/pages/Settings.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
