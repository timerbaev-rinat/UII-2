// Точка входа фронтенда.

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { registerSW } from 'virtual:pwa-register'

import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'

import './styles/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(vuetify)

app.mount('#app')

// Регистрация Service Worker (PWA)
registerSW({ immediate: true })