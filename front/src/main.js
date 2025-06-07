import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import axios from 'axios'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

axios.defaults.baseURL = "http://127.0.0.1:5000"

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')