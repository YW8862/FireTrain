<template>
  <div v-if="visible" class="top-nav">
    <h1 @click="goToHome" class="logo-title">🔥 消防技能训练系统</h1>
    <div class="nav-links">
      <router-link to="/" class="nav-item" active-class="active" exact>首页</router-link>
      <router-link to="/training" class="nav-item" active-class="active">训练</router-link>
      <router-link to="/history" class="nav-item" active-class="active">历史</router-link>
      <router-link to="/stats" class="nav-item" active-class="active">统计</router-link>
      <el-dropdown @command="handleCommand" class="user-dropdown">
        <span class="user-info">
          <el-avatar :size="32" icon="UserFilled" />
          <span class="user-name">{{ userName }}</span>
          <!-- 管理员显示角色标签 -->
          <el-tag v-if="isAdmin" size="small" :type="getRoleType(userStore.effectiveRole)">
            {{ getRoleLabel(userStore.effectiveRole) }}
          </el-tag>
          <el-icon class="el-icon--right"><arrow-down /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <!-- 管理员可进入后台 -->
            <el-dropdown-item v-if="isAdmin" command="admin">
              <el-icon><Monitor /></el-icon>
              管理后台
            </el-dropdown-item>
            <!-- 显示切换回管理员模式选项 -->
            <el-dropdown-item v-if="canSwitchBack" command="switch-back">
              <el-icon><Monitor /></el-icon>
              切换回管理员模式
            </el-dropdown-item>
            <el-dropdown-item command="profile">个人中心</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, UserFilled, Monitor } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

// 组件挂载时，如果 token 存在但 userInfo 为空，自动获取用户信息
onMounted(async () => {
  if (userStore.token && !userStore.userInfo) {
    console.log('🔄 NavBar: Token 存在但 userInfo 为空，自动获取用户信息')
    try {
      await userStore.fetchUserInfo()
      console.log('✅ NavBar: 用户信息已加载', userStore.userInfo)
    } catch (error) {
      console.error('❌ NavBar: 获取用户信息失败', error)
    }
  }
})

// 属性
defineProps({
  visible: {
    type: Boolean,
    default: true
  }
})

// 用户信息
const userName = computed(() => {
  return userStore.user?.username || '用户'
})

// 是否为管理员或 Root（基于有效角色）
const isAdmin = computed(() => {
  const role = userStore.effectiveRole
  return role === 'admin' || role === 'root'
})

// 是否可以切换角色
const canSwitchRole = computed(() => {
  return userStore.canSwitchRole
})

// 是否可以切换回管理员模式（当前是用户模式且有原始角色）
const canSwitchBack = computed(() => {
  return userStore.viewRole === 'user' && ['admin', 'root'].includes(userStore.userInfo?.role)
})

// 是否为用户模式
const isUserMode = computed(() => {
  return userStore.effectiveRole === 'user'
})

// 获取角色标签类型
const getRoleType = (role) => {
  const roleMap = {
    'root': 'danger',
    'admin': 'warning',
    'user': 'info'
  }
  return roleMap[role] || 'info'
}

// 获取角色标签文本
const getRoleLabel = (role) => {
  const labelMap = {
    'root': 'Root',
    'admin': '管理员',
    'user': '普通用户'
  }
  return labelMap[role] || role
}

// 返回首页
const goToHome = () => {
  router.push('/')
}

// 处理下拉菜单命令
const handleCommand = async (command) => {
  switch (command) {
    case 'admin':
      router.push('/admin/dashboard')
      break
    case 'switch-back':
      await handleSwitchBackToAdmin()
      break
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 切换回管理员模式（纯前端切换）
const handleSwitchBackToAdmin = async () => {
  // 清除视图角色，恢复为数据库中的真实角色
  userStore.setViewRole(null)
  
  ElMessage.success(`已切换回${userStore.userInfo?.role === 'root' ? 'Root' : '管理员'}模式`)
  router.push('/admin/dashboard')
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.top-nav h1 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.top-nav h1:hover {
  color: #409EFF;
  transform: scale(1.02);
}

.logo-title {
  cursor: pointer;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-item {
  text-decoration: none;
  color: #606266;
  font-size: 16px;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.nav-item:hover {
  background: #f5f7fa;
  color: #409EFF;
}

.nav-item.active {
  background: #409EFF;
  color: #fff;
}

.user-dropdown {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.user-info:hover {
  background: #f5f7fa;
}

.user-name {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .top-nav {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }

  .nav-links {
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
  }

  .top-nav h1 {
    font-size: 20px;
  }

  .nav-item {
    font-size: 14px;
    padding: 6px 12px;
  }

  .user-name {
    display: none;
  }
}
</style>
