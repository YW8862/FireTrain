<template>
  <div class="admin-layout">
    <!-- 顶部导航栏 -->
    <el-header class="admin-header">
      <div class="header-left">
        <h2>🔥 FireTrain 后台管理</h2>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-icon><User /></el-icon>
            {{ userStore.userInfo?.username }}
            <el-tag size="small" :type="getRoleType(userStore.userInfo?.role)">
              {{ getRoleLabel(userStore.userInfo?.role) }}
            </el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="user-view">
                <el-icon><User /></el-icon>
                用户界面
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
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409eff"
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
          
          <el-menu-item index="/admin/videos">
            <el-icon><VideoCamera /></el-icon>
            <span>视频检测</span>
          </el-menu-item>
          
          <el-menu-item index="/admin/video-upload">
            <el-icon><Upload /></el-icon>
            <span>上传视频检测</span>
          </el-menu-item>
          
          <el-menu-item index="/admin/logs">
            <el-icon><List /></el-icon>
            <span>操作日志</span>
          </el-menu-item>
          
          <!-- 仅 Root 可见 -->
          <el-menu-item 
            v-if="userStore.userInfo?.role === 'root'" 
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
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { logout } from '@/api/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 是否为用户模式
const isUserMode = computed(() => userStore.userInfo?.role === 'user')

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

// 下拉菜单命令处理
const handleCommand = async (command) => {
  switch (command) {
    case 'user-view':
      // 管理员查看用户界面（不改变身份）
      router.push('/training')
      break
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      await handleLogout()
      break
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
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
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
  border-radius: 4px;
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
  background-color: #304156;
  overflow-y: auto;
}

.admin-main {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
