import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import axios from 'axios'

axios.defaults.baseURL = "http://127.0.0.1:5000"
// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
})
