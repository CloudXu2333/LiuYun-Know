<template>
  <div class="min-h-screen flex items-center justify-center bg-gemini-bg relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-blue-400/10 rounded-full blur-3xl animate-pulse-soft"></div>
      <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-400/10 rounded-full blur-3xl animate-pulse-soft" style="animation-delay: 1s;"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="card-gemini w-full max-w-md p-8 m-4 relative z-10 animate-fade-in bg-white/80 backdrop-blur-md">
      <!-- Logo 和标题 -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 mb-6 shadow-lg transform hover:scale-110 transition-transform duration-300">
          <svg class="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M15.25,18L14,14.25L10.25,13L14,11.75L15.25,8L16.5,11.75L20.25,13L16.5,14.25L15.25,18Z"></path>
          </svg>
        </div>
        <h1 class="text-3xl font-bold mb-2 text-gray-900">
          欢迎回来
        </h1>
        <p class="text-gray-500">登录 LiuYun-Know 开启知识之旅</p>
      </div>

      <!-- 登录表单 -->
      <form @submit.prevent="handleLogin" class="space-y-6">
        <!-- 用户名 -->
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 mb-1.5 ml-1">
            用户名或邮箱
          </label>
          <div class="relative">
            <input
              id="username"
              v-model="form.username"
              type="text"
              required
              placeholder="请输入用户名或邮箱"
              class="input-gemini pl-10"
              :disabled="loading"
            />
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
              </svg>
            </div>
          </div>
        </div>

        <!-- 密码 -->
        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-1.5 ml-1">
            密码
          </label>
          <div class="relative">
            <input
              id="password"
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              required
              placeholder="请输入密码"
              class="input-gemini pl-10 pr-10"
              :disabled="loading"
            />
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
              </svg>
            </div>
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
              tabindex="-1"
            >
              <svg v-if="!showPassword" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
              <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path>
              </svg>
            </button>
          </div>
        </div>

        <!-- 图形验证码 -->
        <div>
          <label for="captcha" class="block text-sm font-medium text-gray-700 mb-1.5 ml-1">
            验证码
          </label>
          <div class="flex space-x-3">
            <div class="relative flex-1">
              <input
                id="captcha"
                v-model="form.captcha"
                type="text"
                required
                placeholder="请输入验证码"
                class="input-gemini pl-10"
                :disabled="loading"
                maxlength="4"
              />
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                </svg>
              </div>
            </div>
            <div 
              @click="refreshCaptcha"
              class="w-32 h-12 rounded-xl cursor-pointer hover:shadow-md transition-all duration-200 border border-gray-200 select-none overflow-hidden"
              :class="loading ? 'opacity-50 cursor-not-allowed' : ''"
            >
              <canvas id="captchaCanvas" width="128" height="48" class="w-full h-full"></canvas>
            </div>
          </div>
        </div>

        <!-- 记住密码 -->
        <div class="flex items-center">
          <label class="flex items-center cursor-pointer group">
            <input
              type="checkbox"
              v-model="form.rememberMe"
              class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 cursor-pointer"
            />
            <span class="ml-2 text-sm text-gray-600 group-hover:text-blue-600 transition-colors">记住账号密码</span>
          </label>
        </div>

        <!-- 错误提示 -->
        <transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="transform opacity-0 -translate-y-2"
          enter-to-class="transform opacity-100 translate-y-0"
        >
          <div v-if="error" class="p-4 bg-red-50 border border-red-100 rounded-xl flex items-start">
            <svg class="w-5 h-5 text-red-500 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <p class="text-red-600 text-sm">{{ error }}</p>
          </div>
        </transition>

        <!-- 登录按钮 -->
        <button
          type="submit"
          class="btn-gemini-primary w-full flex items-center justify-center space-x-2 py-3.5 text-base"
          :disabled="loading"
        >
          <span v-if="!loading">登录</span>
          <span v-else class="flex items-center">
            <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            登录中...
          </span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  username: '',
  password: '',
  captcha: '',
  rememberMe: false,
})

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const captchaText = ref('')
const captchaStyle = ref({})

// 从 localStorage 加载保存的账号密码
const loadSavedCredentials = () => {
  const savedUsername = localStorage.getItem('saved_username')
  const savedPassword = localStorage.getItem('saved_password')
  const rememberMe = localStorage.getItem('remember_me') === 'true'
  
  if (rememberMe && savedUsername) {
    form.value.username = savedUsername
    form.value.rememberMe = true
    
    // 如果保存了密码，也加载密码
    if (savedPassword) {
      try {
        // 简单的 base64 解码（注意：这不是安全的加密，只是混淆）
        form.value.password = atob(savedPassword)
      } catch (e) {
        console.error('Failed to decode password')
      }
    }
  }
}

// 保存或清除账号密码
const saveCredentials = () => {
  if (form.value.rememberMe) {
    // 保存账号密码
    localStorage.setItem('saved_username', form.value.username)
    // 简单的 base64 编码（注意：这不是安全的加密，只是混淆）
    localStorage.setItem('saved_password', btoa(form.value.password))
    localStorage.setItem('remember_me', 'true')
  } else {
    // 清除保存的账号密码
    localStorage.removeItem('saved_username')
    localStorage.removeItem('saved_password')
    localStorage.removeItem('remember_me')
  }
}

// 生成随机验证码
const generateCaptcha = () => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789' // 去除易混淆字符
  let text = ''
  for (let i = 0; i < 4; i++) {
    text += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  captchaText.value = text
  
  // 生成复杂的验证码图片
  drawCaptcha(text)
}

// 在 canvas 上绘制验证码
const drawCaptcha = (text) => {
  const canvas = document.getElementById('captchaCanvas')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  
  // 清空画布
  ctx.clearRect(0, 0, width, height)
  
  // 随机背景渐变
  const gradient = ctx.createLinearGradient(0, 0, width, height)
  const colors = [
    ['#E0F2FE', '#DBEAFE'],
    ['#F3E8FF', '#EDE9FE'],
    ['#FCE7F3', '#FDF2F8'],
    ['#D1FAE5', '#ECFDF5'],
    ['#FEF3C7', '#FEF9C3']
  ]
  const colorPair = colors[Math.floor(Math.random() * colors.length)]
  gradient.addColorStop(0, colorPair[0])
  gradient.addColorStop(1, colorPair[1])
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, width, height)
  
  // 添加噪点
  for (let i = 0; i < 50; i++) {
    ctx.fillStyle = `rgba(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255}, 0.3)`
    ctx.beginPath()
    ctx.arc(Math.random() * width, Math.random() * height, Math.random() * 2, 0, 2 * Math.PI)
    ctx.fill()
  }
  
  // 添加干扰线
  for (let i = 0; i < 3; i++) {
    ctx.strokeStyle = `rgba(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255}, 0.3)`
    ctx.lineWidth = 1 + Math.random()
    ctx.beginPath()
    ctx.moveTo(Math.random() * width, Math.random() * height)
    ctx.bezierCurveTo(
      Math.random() * width, Math.random() * height,
      Math.random() * width, Math.random() * height,
      Math.random() * width, Math.random() * height
    )
    ctx.stroke()
  }
  
  // 绘制文字
  const textColors = ['#3B82F6', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#EF4444']
  const charWidth = width / text.length
  
  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    const x = charWidth * i + charWidth / 2
    const y = height / 2
    
    // 随机颜色
    ctx.fillStyle = textColors[Math.floor(Math.random() * textColors.length)]
    
    // 随机字体大小
    const fontSize = 24 + Math.random() * 8
    ctx.font = `bold ${fontSize}px Arial, sans-serif`
    
    // 保存当前状态
    ctx.save()
    
    // 移动到字符位置
    ctx.translate(x, y)
    
    // 随机旋转
    const rotation = (Math.random() - 0.5) * 0.5 // -0.25 到 0.25 弧度
    ctx.rotate(rotation)
    
    // 随机倾斜
    ctx.transform(1, Math.random() * 0.3 - 0.15, Math.random() * 0.3 - 0.15, 1, 0, 0)
    
    // 绘制字符
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(char, 0, 0)
    
    // 添加描边
    ctx.strokeStyle = `rgba(0, 0, 0, 0.2)`
    ctx.lineWidth = 0.5
    ctx.strokeText(char, 0, 0)
    
    // 恢复状态
    ctx.restore()
  }
  
  // 添加更多噪点覆盖
  for (let i = 0; i < 30; i++) {
    ctx.fillStyle = `rgba(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255}, 0.2)`
    ctx.beginPath()
    ctx.arc(Math.random() * width, Math.random() * height, Math.random() * 1.5, 0, 2 * Math.PI)
    ctx.fill()
  }
}

const refreshCaptcha = () => {
  if (!loading.value) {
    generateCaptcha()
    form.value.captcha = ''
  }
}

// 页面加载后初始化
import { onMounted } from 'vue'
onMounted(() => {
  generateCaptcha()
  loadSavedCredentials()
})

const handleLogin = async () => {
  error.value = ''
  
  // 验证码校验
  if (form.value.captcha.toUpperCase() !== captchaText.value) {
    error.value = '验证码错误'
    refreshCaptcha()
    return
  }
  
  loading.value = true

  try {
    await authStore.login({
      username: form.value.username,
      password: form.value.password,
    })
    
    // 登录成功，保存或清除账号密码
    saveCredentials()
    
    // 跳转到对话页面
    router.push('/chat')
  } catch (err) {
    error.value = err.message || '登录失败，请检查用户名和密码'
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}


</script>

