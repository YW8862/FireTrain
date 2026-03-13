<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button @click="goBack" icon="ArrowLeft">
              返回
            </el-button>
          </div>
          <span class="page-title">👤 个人中心</span>
          <div class="header-right">
            <el-button type="primary" size="small" @click="handleEdit" disabled>
              <el-icon><edit /></el-icon>
              编辑资料
            </el-button>
          </div>
        </div>
      </template>
      
      <el-form :model="userInfo" label-width="100px" v-loading="loading">
        <el-form-item label="用户名">
          <el-input v-model="userInfo.username" disabled />
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="userInfo.email" disabled />
        </el-form-item>
        
        <el-form-item label="角色">
          <el-tag :type="getRoleType(userInfo.role)">{{ userInfo.role || '普通用户' }}</el-tag>
        </el-form-item>
        
        <el-divider />
        
        <el-form-item>
          <el-button type="danger" @click="handleLogout" style="width: 100%">
            退出登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, ArrowLeft } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { getUserInfo, logout as logoutApi } from '@/api/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

// 返回上一页
const goBack = () => {
  router.back()
}

const userInfo = reactive({
  username: '',
  email: '',
  role: ''
})

// 获取用户信息
const fetchUserInfo = async () => {
  loading.value = true
  try {
    const res = await getUserInfo()
    userInfo.username = res.username || userStore.username || '未知用户'
    userInfo.email = res.email || '未设置'
    userInfo.role = res.role || '普通用户'
    
    // 更新 store 中的用户信息
    userStore.setUserInfo(res)
  } catch (error) {
    console.error('获取用户信息失败:', error)
    // 如果获取失败，使用 store 中已有的信息
    if (userStore.userInfo) {
      userInfo.username = userStore.userInfo.username || '未知用户'
      userInfo.email = userStore.userInfo.email || '未设置'
      userInfo.role = userStore.userInfo.role || '普通用户'
    }
  } finally {
    loading.value = false
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
    
    // 调用 API 退出
    await logoutApi()
  } catch {
    // 用户取消退出，继续执行
  } finally {
    // 清理本地状态
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

// 获取角色标签类型
const getRoleType = (role) => {
  const roleMap = {
    'admin': 'danger',
    'trainer': 'warning',
    'user': 'info'
  }
  return roleMap[role] || 'info'
}

// 编辑资料（占位功能）
const handleEdit = () => {
  ElMessage.info('编辑功能开发中，敬请期待...')
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.profile-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.profile-card {
  width: 100%;
  max-width: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}
</style>
