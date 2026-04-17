<template>
  <div class="admin-layout">
    <el-header class="admin-header">
      <div class="header-left">
        <div class="admin-brand">
          <div class="admin-brand-mark">FT</div>
          <div>
            <h2>灭火器实操训练测评系统后台管理</h2>
            <p>训练数据、用户信息与视频分析管理</p>
          </div>
        </div>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-icon><User /></el-icon>
            {{ userStore.userInfo?.username }}
            <el-tag size="small" :type="getRoleType(userStore.effectiveRole)">
              {{ getRoleLabel(userStore.effectiveRole) }}
            </el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="canSwitchToUser" command="switch-to-user">
                <el-icon><User /></el-icon>
                切换到用户模式
              </el-dropdown-item>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container class="admin-container">
      <!-- 侧边栏 -->
      <el-aside width="200px" class="admin-sidebar">
        <el-menu
          :default-active="activeMenu"
          router
          class="admin-menu"
        >
          <el-menu-item index="/admin/dashboard">
            <el-icon><DataLine /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          
          <el-menu-item index="/admin/trainings">
            <el-icon><Document /></el-icon>
            <span>训练数据</span>
          </el-menu-item>
          
          <el-menu-item index="/admin/video-upload">
            <el-icon><Upload /></el-icon>
            <span>上传视频检测</span>
          </el-menu-item>
          
          <el-menu-item index="/admin/logs">
            <el-icon><List /></el-icon>
            <span>操作日志</span>
          </el-menu-item>
          
          <!-- 仅 Root 可见（基于有效角色） -->
          <el-menu-item 
            v-if="userStore.effectiveRole === 'root'" 
            index="/admin/admins"
          >
            <el-icon><Key /></el-icon>
            <span>管理员管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { logout } from '@/api/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 是否为用户模式（基于有效角色）
const isUserMode = computed(() => userStore.effectiveRole === 'user')
const canSwitchToUser = computed(() => userStore.canSwitchRole && !isUserMode.value)

onMounted(async () => {
  if (userStore.token && !userStore.userInfo) {
    console.log('🔄 AdminLayout: userInfo 为空，开始补拉用户信息')
    try {
      await userStore.fetchUserInfo()
      console.log('✅ AdminLayout: 用户信息已加载', userStore.userInfo)
    } catch (error) {
      console.error('❌ AdminLayout: 获取用户信息失败', error)
    }
  }
})

// 获取角色标签类型
const getRoleType = (role) => {
  const roleMap = {
    'root': 'danger',
    'admin': 'warning',
    'student': 'info',
    'user': 'info'
  }
  return roleMap[role] || 'info'
}

// 获取角色标签文本
const getRoleLabel = (role) => {
  const labelMap = {
    'root': 'Root',
    'admin': '管理员',
    'student': '普通用户',
    'user': '普通用户'
  }
  return labelMap[role] || role
}

// 下拉菜单命令处理
const handleCommand = async (command) => {
  console.log('🧭 AdminLayout handleCommand:', command)
  switch (command) {
    case 'switch-to-user':
      await handleSwitchRole()
      break
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      await handleLogout()
      break
  }
}

// 切换到用户模式（不修改数据库，只改变视图）
const handleSwitchRole = async () => {
  try {
    if (!userStore.userInfo && userStore.token) {
      console.log('🔄 切换前先补拉用户信息')
      await userStore.fetchUserInfo()
    }

    console.log('🎭 当前用户信息:', userStore.userInfo)
    console.log('🎭 当前有效角色:', userStore.effectiveRole)
    console.log('🎭 是否可切换:', userStore.canSwitchRole)

    // 使用纯前端切换，不调用后端 API，也不修改数据库角色字段
    const success = userStore.switchViewRole('user')
    
    if (success) {
      console.log('✅ 已切换到用户模式，准备跳转首页')
      ElMessage.success('已切换到用户模式')
      router.push('/')
    } else {
      console.warn('⚠️ 当前账号不满足切换到用户模式的条件')
      ElMessage.error('您没有权限切换角色')
    }
  } catch (error) {
    console.error('切换角色失败:', error)
    ElMessage.error('切换角色失败')
  }
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await logout()
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.admin-header {
  background-color: #fff;
  border-bottom: 1px solid var(--ft-color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 72px;
}

.admin-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--ft-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
  color: var(--ft-color-text-primary);
}

.header-left p {
  margin: 4px 0 0;
  color: var(--ft-color-text-tertiary);
  font-size: 12px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--ft-color-border);
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.admin-container {
  flex: 1;
  overflow: hidden;
}

.admin-sidebar {
  background: #16327d;
  overflow-y: auto;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}

.admin-main {
  background-color: var(--ft-color-page-bg);
  padding: 24px;
  overflow-y: auto;
}

.admin-menu {
  border-right: 0;
  --el-menu-bg-color: #16327d;
  --el-menu-text-color: rgba(255, 255, 255, 0.78);
  --el-menu-active-color: #ffffff;
  --el-menu-hover-bg-color: rgba(255, 255, 255, 0.08);
}

.admin-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.14);
  border-left: 3px solid var(--ft-color-danger);
}
</style>
