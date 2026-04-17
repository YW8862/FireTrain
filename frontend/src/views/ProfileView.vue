<template>
  <div class="app-page profile-page">
    <NavBar />
    <div class="app-shell app-shell--narrow">
      <div class="app-title-row">
        <div>
          <h1 class="app-page-title">个人中心</h1>
          <p class="app-page-subtitle">查看账号信息、训练概况和最近训练记录。</p>
        </div>
        <el-button @click="goBack">返回上一页</el-button>
      </div>

      <el-row :gutter="24" v-loading="loading">
        <el-col :lg="8" :md="24">
          <el-card class="section-card profile-card">
            <div class="profile-summary">
              <div class="profile-avatar">{{ (userInfo.username || 'U').slice(0, 1).toUpperCase() }}</div>
              <h2>{{ userInfo.username || '未知用户' }}</h2>
              <p>{{ userInfo.email || '未设置邮箱' }}</p>
              <el-tag :type="getRoleType(userInfo.role)" effect="plain">{{ userInfo.role || '普通用户' }}</el-tag>
            </div>

            <div class="profile-meta">
              <div class="meta-item">
                <span>账号角色</span>
                <strong>{{ userInfo.role || '普通用户' }}</strong>
              </div>
              <div class="meta-item">
                <span>邮箱</span>
                <strong>{{ userInfo.email || '未设置邮箱' }}</strong>
              </div>
              <div class="meta-item">
                <span>手机号</span>
                <strong>{{ userInfo.phone || '未设置手机号' }}</strong>
              </div>
              <div class="meta-item">
                <span>注册时间</span>
                <strong>{{ userInfo.createdAt ? formatDate(userInfo.createdAt) : '-' }}</strong>
              </div>
              <div class="meta-item">
                <span>最近登录</span>
                <strong>{{ userInfo.lastLoginAt ? formatDate(userInfo.lastLoginAt) : '暂无记录' }}</strong>
              </div>
              <div class="meta-item">
                <span>训练总次数</span>
                <strong>{{ stats.total_training_count }}</strong>
              </div>
              <div class="meta-item">
                <span>平均得分</span>
                <strong>{{ stats.average_score.toFixed(1) }} 分</strong>
              </div>
            </div>

            <el-button type="primary" plain class="edit-btn" @click="openEditDialog">
              编辑个人信息
            </el-button>
            <el-button type="danger" class="logout-btn" @click="handleLogout">
              退出登录
            </el-button>
          </el-card>
        </el-col>

        <el-col :lg="16" :md="24">
          <div class="profile-content">
            <div class="stat-grid">
              <div class="stat-panel">
                <div class="stat-label">训练总次数</div>
                <div class="stat-value">{{ stats.total_training_count }}</div>
              </div>
              <div class="stat-panel">
                <div class="stat-label">平均得分</div>
                <div class="stat-value">{{ stats.average_score.toFixed(1) }}</div>
              </div>
              <div class="stat-panel">
                <div class="stat-label">最佳得分</div>
                <div class="stat-value">{{ stats.best_score.toFixed(1) }}</div>
              </div>
              <div class="stat-panel">
                <div class="stat-label">最近训练</div>
                <div class="stat-value profile-date">{{ stats.last_training_date ? formatDate(stats.last_training_date) : '暂无' }}</div>
              </div>
            </div>

            <el-card class="section-card recent-card">
              <template #header>
                <div class="recent-header">
                  <div>
                    <h3>最近训练记录</h3>
                    <p>优先展示最近 5 条训练结果，便于快速回顾。</p>
                  </div>
                  <el-button type="primary" link @click="goToHistory">查看全部</el-button>
                </div>
              </template>

              <el-table :data="recentTrainings" empty-text="暂无训练记录">
                <el-table-column prop="started_at" label="训练时间" min-width="170">
                  <template #default="{ row }">
                    {{ formatDate(row.started_at) }}
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="110">
                  <template #default="{ row }">
                    <el-tag :type="getStatusType(row.status)" effect="plain">{{ getStatusLabel(row.status) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="total_score" label="得分" width="100">
                  <template #default="{ row }">
                    <span v-if="row.status === 'done'" :class="getScoreClass(row.total_score)">
                      {{ row.total_score ?? '-' }}
                    </span>
                    <span v-else class="muted-text">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="110">
                  <template #default="{ row }">
                    <el-button v-if="row.status === 'done'" link type="primary" @click="goToReport(row.id)">查看报告</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </el-col>
      </el-row>
    </div>

    <el-dialog v-model="editDialogVisible" title="更新个人信息" width="560px" class="profile-edit-dialog">
      <div class="profile-edit-layout">
        <div class="edit-panel">
          <div class="edit-panel-header">
            <h3>账号资料</h3>
            <p>用户名保持只读，邮箱和手机号可自行更新。</p>
          </div>
          <el-form label-position="top">
            <el-form-item label="用户名">
              <el-input :model-value="userInfo.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input
                v-model="editForm.email"
                placeholder="请输入邮箱"
                clearable
              />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input
                v-model="editForm.phone"
                placeholder="请输入手机号"
                maxlength="20"
                clearable
              />
            </el-form-item>
          </el-form>
        </div>

        <div class="edit-panel edit-panel--muted">
          <div class="edit-panel-header">
            <h3>密码设置</h3>
            <p>如需修改密码，请填写当前密码并输入新的登录密码。</p>
          </div>
          <el-form label-position="top">
            <el-form-item label="当前密码">
              <el-input
                v-model="editForm.currentPassword"
                type="password"
                show-password
                placeholder="请输入当前密码"
                clearable
              />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input
                v-model="editForm.newPassword"
                type="password"
                show-password
                placeholder="不少于 6 位"
                clearable
              />
            </el-form-item>
            <el-form-item label="确认新密码">
              <el-input
                v-model="editForm.confirmPassword"
                type="password"
                show-password
                placeholder="请再次输入新密码"
                clearable
              />
            </el-form-item>
          </el-form>
          <div class="edit-tip">如果本次不修改密码，密码相关输入框可以留空。</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveProfile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'
import { getUserInfo, logout as logoutApi, updateUserInfo } from '@/api/user'
import { getPersonalStatistics } from '@/api/statistics'
import { getTrainingHistory } from '@/api/training'
import NavBar from '@/components/NavBar.vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const saving = ref(false)
const editDialogVisible = ref(false)
const recentTrainings = ref([])
const stats = reactive({
  total_training_count: 0,
  average_score: 0,
  best_score: 0,
  last_training_date: null
})

// 返回上一页
const goBack = () => {
  router.back()
}

const userInfo = reactive({
  username: '',
  email: '',
  phone: '',
  role: '',
  createdAt: '',
  lastLoginAt: ''
})

const editForm = reactive({
  email: '',
  phone: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const res = await getUserInfo()
    userInfo.username = res.username || userStore.username || '未知用户'
    userInfo.email = res.email || ''
    userInfo.phone = res.phone || ''
    userInfo.role = res.role || '普通用户'
    userInfo.createdAt = res.created_at || ''
    userInfo.lastLoginAt = res.last_login_at || ''
    
    // 更新 store 中的用户信息
    userStore.setUserInfo(res)
  } catch (error) {
    console.error('获取用户信息失败:', error)
    // 如果获取失败，使用 store 中已有的信息
    if (userStore.userInfo) {
      userInfo.username = userStore.userInfo.username || '未知用户'
      userInfo.email = userStore.userInfo.email || ''
      userInfo.phone = userStore.userInfo.phone || ''
      userInfo.role = userStore.userInfo.role || '普通用户'
      userInfo.createdAt = userStore.userInfo.created_at || ''
      userInfo.lastLoginAt = userStore.userInfo.last_login_at || ''
    }
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await getPersonalStatistics()
    stats.total_training_count = res.total_training_count || res.total_trainings || 0
    stats.average_score = parseFloat(res.average_score) || 0
    stats.best_score = parseFloat(res.best_score) || 0
    stats.last_training_date = res.last_training_date || res.last_training_at || null
  } catch (error) {
    console.error('加载个人统计失败:', error)
  }
}

const loadRecentTrainings = async () => {
  try {
    const res = await getTrainingHistory({ page: 1, page_size: 5 })
    recentTrainings.value = res.records || []
  } catch (error) {
    console.error('加载最近训练记录失败:', error)
  }
}

const openEditDialog = () => {
  editForm.email = userInfo.email || ''
  editForm.phone = userInfo.phone || ''
  editForm.currentPassword = ''
  editForm.newPassword = ''
  editForm.confirmPassword = ''
  editDialogVisible.value = true
}

const handleSaveProfile = async () => {
  if (!editForm.email?.trim()) {
    ElMessage.warning('请输入邮箱')
    return
  }

  if (editForm.currentPassword || editForm.newPassword || editForm.confirmPassword) {
    if (!editForm.currentPassword) {
      ElMessage.warning('修改密码时请输入当前密码')
      return
    }
    if (!editForm.newPassword) {
      ElMessage.warning('请输入新密码')
      return
    }
    if (editForm.newPassword.length < 6) {
      ElMessage.warning('新密码长度至少为 6 位')
      return
    }
    if (editForm.newPassword !== editForm.confirmPassword) {
      ElMessage.warning('两次输入的新密码不一致')
      return
    }
  }

  saving.value = true
  try {
    const payload = {
      email: editForm.email.trim(),
      phone: editForm.phone?.trim() || null
    }

    if (editForm.newPassword) {
      payload.current_password = editForm.currentPassword
      payload.new_password = editForm.newPassword
    }

    const response = await updateUserInfo(payload)
    userInfo.email = response.email || ''
    userInfo.phone = response.phone || ''
    userInfo.lastLoginAt = response.last_login_at || userInfo.lastLoginAt
    userStore.setUserInfo({
      ...(userStore.userInfo || {}),
      ...response
    })
    editDialogVisible.value = false
    editForm.currentPassword = ''
    editForm.newPassword = ''
    editForm.confirmPassword = ''
    ElMessage.success('个人信息已更新')
  } catch (error) {
    ElMessage.error(error.customMessage || error.response?.data?.detail || '个人信息更新失败')
  } finally {
    saving.value = false
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
    // 清理本地状态
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    ElMessage.error(error.customMessage || error.response?.data?.detail || '退出登录失败')
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

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusType = (status) => {
  const map = {
    created: 'info',
    processing: 'warning',
    done: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status) => {
  const map = {
    created: '未开始',
    processing: '进行中',
    done: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const getScoreClass = (score) => {
  if (score >= 90) return 'score-good'
  if (score >= 60) return 'score-pass'
  return 'score-bad'
}

const goToHistory = () => {
  router.push('/history')
}

const goToReport = (id) => {
  router.push(`/report/${id}`)
}

onMounted(() => {
  loading.value = true
  Promise.all([fetchUserInfo(), loadStats(), loadRecentTrainings()]).finally(() => {
    loading.value = false
  })
})
</script>

<style scoped>
.profile-page {
  padding-bottom: 24px;
}

.profile-card {
  height: 100%;
}

.profile-summary {
  text-align: center;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--ft-color-border);
}

.profile-avatar {
  width: 76px;
  height: 76px;
  margin: 0 auto 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(30, 64, 175, 0.12);
  color: var(--ft-color-primary);
  font-size: 28px;
  font-weight: 700;
}

.profile-summary h2 {
  margin: 0;
}

.profile-summary p {
  margin: 8px 0 12px;
  color: var(--ft-color-text-tertiary);
}

.profile-meta {
  display: grid;
  gap: 14px;
  margin-top: 20px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--ft-color-surface-muted);
}

.meta-item span {
  color: var(--ft-color-text-tertiary);
}

.meta-item strong {
  text-align: right;
}

.logout-btn {
  width: 100%;
  margin-top: 20px;
}

.edit-btn {
  width: 100%;
  margin-top: 20px;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.recent-card h3 {
  margin: 0;
  font-size: 18px;
}

.recent-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.recent-header p {
  margin: 6px 0 0;
  color: var(--ft-color-text-tertiary);
  font-size: 14px;
}

.profile-date {
  font-size: 18px;
  line-height: 1.4;
}

.edit-tip {
  color: var(--ft-color-text-tertiary);
  font-size: 13px;
  line-height: 1.6;
}

.profile-edit-layout {
  display: grid;
  gap: 16px;
}

.edit-panel {
  padding: 18px;
  border-radius: 14px;
  border: 1px solid var(--ft-color-border);
  background: #fff;
}

.edit-panel--muted {
  background:
    linear-gradient(180deg, rgba(30, 64, 175, 0.04), rgba(30, 64, 175, 0)),
    #f8fafc;
}

.edit-panel-header {
  margin-bottom: 12px;
}

.edit-panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.edit-panel-header p {
  margin: 6px 0 0;
  color: var(--ft-color-text-tertiary);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .recent-header {
    flex-direction: column;
  }
}
</style>
