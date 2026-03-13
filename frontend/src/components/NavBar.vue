<template>
  <div class="top-nav" v-if="visible">
    <h1 @click="goToHome" class="logo-title">🔥 消防技能训练系统</h1>
    <div class="nav-links">
      <router-link to="/" class="nav-item" :class="{ active: isActive('/') }">首页</router-link>
      <router-link to="/training" class="nav-item" :class="{ active: isActive('/training') }">训练</router-link>
      <router-link to="/history" class="nav-item" :class="{ active: isActive('/history') }">历史</router-link>
      <router-link to="/stats" class="nav-item" :class="{ active: isActive('/stats') }">统计</router-link>
      
      <!-- 用户下拉菜单 -->
      <el-dropdown @command="handleCommand" class="user-dropdown" v-if="isLoggedIn">
        <span class="user-info">
          <el-avatar :size="32" icon="UserFilled" />
          <span class="user-name">{{ userName }}</span>
          <el-icon class="el-icon--right"><arrow-down /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, UserFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

// 定义 props - 控制导航栏是否可见
defineProps({
  visible: {
    type: Boolean,
    default: true
  }
})

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 用户信息
const isLoggedIn = computed(() => !!localStorage.getItem('token'))
const userName = computed(() => {
  return userStore.user?.username || '用户'
})

// 判断当前路由
const isActive = (path) => {
  return route.path === path
}

// 跳转到首页
const goToHome = () => {
  router.push('/')
}

// 处理下拉菜单命令
const handleCommand = (command) => {
  if (command === 'logout') {
    handleLogout()
  }
}

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }).catch(() => {})
}
</script>

<style scoped>
.top-nav {
  background: rgba(255, 255, 255, 0.95);
  padding: 15px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.logo-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
  cursor: pointer;
  transition: opacity 0.3s;
}

.logo-title:hover {
  opacity: 0.8;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-item {
  color: #606266;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s;
  padding: 8px 16px;
  border-radius: 4px;
}

.nav-item:hover,
.nav-item.active {
  color: #409EFF;
  background: #ecf5ff;
}

.user-dropdown {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background 0.3s;
}

.user-info:hover {
  background: #f5f5f5;
}

.user-name {
  font-weight: 500;
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .top-nav {
    padding: 15px 20px;
  }

  .logo-title {
    font-size: 20px;
  }

  .nav-links {
    gap: 10px;
  }

  .nav-item {
    padding: 6px 12px;
    font-size: 14px;
  }

  .user-name {
    display: none;
  }
}
</style>
