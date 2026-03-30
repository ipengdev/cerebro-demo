import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

import {
  FrappeUI,
  setConfig,
  frappeRequest,
} from 'frappe-ui'

let pinia = createPinia()
let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(pinia)
app.use(router)

if (import.meta.env.DEV) {
  frappeRequest({ url: '/api/method/employee_self_service.www.ess.get_context_for_dev' }).then(
    (values) => {
      for (let key in values) {
        window[key] = values[key]
      }
      app.mount('#app')
    },
  )
} else {
  app.mount('#app')
}
