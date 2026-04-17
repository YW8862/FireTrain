<template>
  <div v-if="visible" class="top-nav">
    <div class="brand-block" @click="goToHome">
      <div class="brand-mark">FT</div>
      <div>
        <h1 class="logo-title">智能消防训练评测系统</h1>
        <p class="logo-subtitle">规范操作 · 训练记录 · 实操测评</p>
      </div>
    </div>
    <div class="nav-links">
      <div class="nav-tabs">
        <router-link to="/" class="nav-item" active-class="active" exact>首页</router-link>
        <router-link to="/training" class="nav-item" active-class="active">实操训练</router-link>
        <router-link to="/history" class="nav-item" active-class="active">训练记录</router-link>
        <router-link to="/stats" class="nav-item" active-class="active">统计分析</router-link>
      </div>
      <el-dropdown @command="handleCommand" class="user-dropdown">
        <span class="user-info">
          <el-avatar :size="34" icon="UserFilled" class="user-avatar" />
          <span class="user-name">{{ userName }}</span>
          <el-tag v-if="isAdmin" size="small" :type="getRoleType(userStore.effectiveRole)" effect="plain">
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
              切换管理员空间
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

// 是否可以切换回管理员模式（当前是用户模式且有原始角色）
const canSwitchBack = computed(() => {
  return userStore.viewRole === 'user' && ['admin', 'root'].includes(userStore.userInfo?.role)
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
  gap: 20px;
  padding: 16px 28px;
  background: rgba(255, 255, 255, 0.98);
  border-bottom: 1px solid var(--ft-color-border);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  cursor: pointer;
}

.brand-mark {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: var(--ft-color-primary);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.logo-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--ft-color-text-primary);
}

.logo-subtitle {
  margin: 4px 0 0;
  color: var(--ft-color-text-tertiary);
  font-size: 12px;
}

.nav-links {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  flex: 1;
}

.nav-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border: 1px solid var(--ft-color-border);
  border-radius: 999px;
  background: var(--ft-color-surface-muted);
}

.nav-item {
  text-decoration: none;
  color: var(--ft-color-text-secondary);
  font-size: 14px;
  font-weight: 500;
  padding: 9px 16px;
  border-radius: 999px;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.nav-item:hover {
  background: #fff;
  color: var(--ft-color-primary);
}

.nav-item.active {
  background: var(--ft-color-primary);
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
  border-radius: 999px;
  border: 1px solid var(--ft-color-border);
  background: #fff;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.user-info:hover {
  background: var(--ft-color-surface-muted);
  border-color: var(--ft-color-border-strong);
}

.user-name {
  font-size: 14px;
  color: var(--ft-color-text-secondary);
  font-weight: 500;
}

.user-avatar {
  background: rgba(30, 64, 175, 0.12);
  color: var(--ft-color-primary);
}

/* 响应式设计 */
@media (max-width: 960px) {
  .top-nav {
    flex-direction: column;
    align-items: stretch;
    padding: 16px;
  }

  .nav-links {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .nav-tabs {
    justify-content: center;
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .brand-block {
    align-items: flex-start;
  }

  .brand-mark {
    width: 38px;
    height: 38px;
  }

  .logo-title {
    font-size: 18px;
  }

  .logo-subtitle {
    display: none;
  }

  .nav-item {
    text-align: center;
  }

  .user-info {
    justify-content: center;
  }
}
</style>
