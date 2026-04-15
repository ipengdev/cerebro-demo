import './index.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import translationPlugin from './translation'
import App from './App.vue'

import {
  FrappeUI,
  Button,
  Input,
  TextInput,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  setConfig,
  frappeRequest,
  FeatherIcon,
} from 'frappe-ui'

let globalComponents = {
  Button,
  TextInput,
  Input,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  FeatherIcon,
}

let pinia = createPinia()
let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(pinia)
app.use(router)
app.use(translationPlugin)

for (let key in globalComponents) {
  app.component(key, globalComponents[key])
}

if (import.meta.env.DEV) {
  frappeRequest({
    url: '/api/method/e_tax.www.e-tax.get_context_for_dev',
  }).then((values) => {
    for (let key in values) {
      window[key] = values[key]
    }
    app.mount('#app')
  }).catch(() => {
    app.mount('#app')
  })
} else {
  app.mount('#app')
}
