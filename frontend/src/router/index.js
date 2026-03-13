import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { title: '注册' }
  },
  {
    path: '/training',
    name: 'Training',
    component: () => import('@/views/TrainingView.vue'),
    meta: { title: '训练', requiresAuth: true }
  },
  {
    path: '/report/:id',
    name: 'Report',
    component: () => import('@/views/ReportView.vue'),
    meta: { title: '训练报告', requiresAuth: true }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/HistoryView.vue'),
    meta: { title: '训练历史', requiresAuth: true }
  },
  {
    path: '/stats',
    name: 'Stats',
    component: () => import('@/views/StatsView.vue'),
    meta: { title: '数据统计', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - FireTrain` : 'FireTrain'
  
  // 检查是否需要登录
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return '/login'
  }
})

export default router
