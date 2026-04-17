import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

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
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { title: '个人中心', requiresAuth: true }
  },
  {
    path: '/stats',
    name: 'Stats',
    component: () => import('@/views/StatsView.vue'),
    meta: { title: '数据统计', requiresAuth: true }
  },
  // 后台管理路由
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresRole: ['admin', 'root'] },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UserManagement.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'users/new',
        name: 'AdminUserCreate',
        component: () => import('@/views/admin/UserDetailView.vue'),
        meta: { title: '新增用户' }
      },
      {
        path: 'users/:id',
        name: 'AdminUserDetail',
        component: () => import('@/views/admin/UserDetailView.vue'),
        meta: { title: '用户详情' }
      },
      {
        path: 'trainings',
        name: 'AdminTrainings',
        component: () => import('@/views/admin/TrainingManagement.vue'),
        meta: { title: '训练数据管理' }
      },
      // {
      //   path: 'videos',
      //   name: 'AdminVideos',
      //   component: () => import('@/views/admin/VideoDetection.vue'),
      //   meta: { title: '视频检测' }
      // },
      {
        path: 'video-upload',
        name: 'AdminVideoUpload',
        component: () => import('@/views/admin/AdminVideoUpload.vue'),
        meta: { title: '管理员视频检测' }
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/OperationLogs.vue'),
        meta: { title: '操作日志' }
      },
      {
        path: 'admins',
        name: 'AdminManagement',
        component: () => import('@/views/admin/AdminManagement.vue'),
        meta: { title: '管理员管理', requiresRole: ['root'] }
      },
      {
        path: 'admins/:id',
        name: 'AdminAccountDetail',
        component: () => import('@/views/admin/AdminDetailView.vue'),
        meta: { title: '管理员详情', requiresRole: ['root'] }
      },
      {
        path: 'report/:id',
        name: 'AdminReport',
        component: () => import('@/views/admin/AdminReportView.vue'),
        meta: { title: '训练报告' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, _from) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - FireTrain` : 'FireTrain'
  
  console.log('🔍 路由守卫:', to.path)
  
  // 检查是否需要登录
  const token = localStorage.getItem('token')
  console.log('🔑 Token 存在:', !!token)
  
  if (to.meta.requiresAuth && !token) {
    console.log('❌ 未登录，重定向到 /login')
    return '/login'
  }
  
  // 检查角色权限（基于视图角色）
  if (to.meta.requiresRole && token) {
    try {
      const userStore = useUserStore()
      
      // 优先使用前端视图角色，确保“不改数据库字段”的身份切换在刷新后仍生效。
      let userRole = userStore.effectiveRole
      if (userRole) {
        console.log('🎭 使用 store 中的有效角色:', userRole)
      } else {
        // 否则从 token 中解析（fallback）
        const payload = JSON.parse(atob(token.split('.')[1]))
        userRole = payload.role || 'user'
        console.log('🎭 从 Token 中解析角色:', userRole)
      }
      
      console.log('📋 需要的角色:', to.meta.requiresRole)
      
      if (!to.meta.requiresRole.includes(userRole)) {
        // 权限不足，重定向到首页
        console.log('❌ 权限不足，重定向到 /')
        return '/'
      } else {
        console.log('✅ 权限验证通过')
      }
    } catch (error) {
      console.error('权限验证失败:', error)
      return '/login'
    }
  }
})

export default router
