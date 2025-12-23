<template>
  <div id="app" class="min-h-screen bg-dark-bg">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // 应用已在 main.js 中初始化
})
</script>

