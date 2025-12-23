/**
 * Vue 应用入口
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import router from './router'
import App from './App.vue'

// KaTeX 数学公式样式
import 'katex/dist/katex.min.css'

import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// 初始化认证状态
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
authStore.initialize().then(() => {
  app.mount('#app')
})

