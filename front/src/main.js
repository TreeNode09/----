import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import axios from 'axios'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

axios.defaults.baseURL = import.meta.env.VITE_BASE_URL

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')