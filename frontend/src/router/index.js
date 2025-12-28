/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false, layout: 'auth' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { requiresAuth: false, layout: 'auth' },
  },
  {
    path: '/',
    redirect: '/chat',
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatGemini.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/views/KnowledgeBaseGemini.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge-base/:id',
    name: 'KnowledgeBaseDetail',
    component: () => import('@/views/KnowledgeBaseDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge-base/:id/graph',
    name: 'KnowledgeGraph',
    component: () => import('@/views/KnowledgeGraphPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/memory',
    name: 'Memory',
    component: () => import('@/views/Memory.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/diagram',
    name: 'Diagram',
    component: () => import('@/views/DiagramPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('@/views/AdminUsers.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/llm-configs',
    name: 'AdminLLMConfigs',
    component: () => import('@/views/AdminLLMConfigs.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/mcp-tools',
    name: 'MCPTools',
    component: () => import('@/views/MCPTools.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查是否需要认证
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth !== false)
  const requiresAdmin = to.matched.some((record) => record.meta.requiresAdmin === true)
  
  if (requiresAuth && !authStore.isAuthenticated) {
    // 需要认证但未登录，跳转到登录页
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (requiresAdmin && !authStore.user?.is_superuser) {
    // 需要管理员权限但不是管理员，跳转到对话页面
    next({ name: 'Chat' })
  } else if (!requiresAuth && authStore.isAuthenticated && (to.name === 'Login' || to.name === 'Register')) {
    // 已登录用户访问登录/注册页，跳转到对话页面
    next({ name: 'Chat' })
  } else {
    next()
  }
})

export default router

