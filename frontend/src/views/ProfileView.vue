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

    <el-dialog v-model="editDialogVisible" width="760px" class="profile-edit-dialog">
      <template #header>
        <div class="profile-edit-header">
          <div>
            <p class="profile-edit-eyebrow">PROFILE SETTINGS</p>
            <h2>更新个人信息</h2>
            <p>维护你的账号资料与登录安全设置，修改后立即生效。</p>
          </div>
          <div class="profile-edit-header-badge">用户名保持只读</div>
        </div>
      </template>

      <div class="profile-edit-layout">
        <aside class="profile-edit-aside">
          <div class="profile-edit-aside-card">
            <div class="profile-edit-avatar">{{ (userInfo.username || 'U').slice(0, 1).toUpperCase() }}</div>
            <h3>{{ userInfo.username || '未知用户' }}</h3>
            <p>{{ userInfo.email || '未设置邮箱' }}</p>
            <div class="profile-edit-meta">
              <div class="profile-edit-meta-item">
                <span>当前手机号</span>
                <strong>{{ userInfo.phone || '未设置' }}</strong>
              </div>
              <div class="profile-edit-meta-item">
                <span>账号角色</span>
                <strong>{{ userInfo.role || '普通用户' }}</strong>
              </div>
              <div class="profile-edit-meta-item">
                <span>最近登录</span>
                <strong>{{ userInfo.lastLoginAt ? formatDate(userInfo.lastLoginAt) : '暂无记录' }}</strong>
              </div>
            </div>
            <div class="profile-edit-note">
              建议优先维护常用邮箱和手机号，便于后续账号通知与身份确认。
            </div>
          </div>
        </aside>

        <div class="profile-edit-main">
          <section class="edit-panel edit-panel--primary">
            <div class="edit-panel-header">
              <h3>账号资料</h3>
              <p>这里用于更新基础联系信息，保存后会同步刷新个人中心展示内容。</p>
            </div>
            <el-form label-position="top" class="profile-edit-form">
              <div class="profile-form-grid">
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
              </div>
              <el-form-item label="手机号">
                <el-input
                  v-model="editForm.phone"
                  placeholder="请输入手机号"
                  maxlength="20"
                  clearable
                />
              </el-form-item>
            </el-form>
          </section>

          <section class="edit-panel edit-panel--muted">
            <div class="edit-panel-header">
              <h3>密码设置</h3>
              <p>如需更新登录密码，请按顺序填写当前密码、新密码和确认密码。</p>
            </div>
            <el-form label-position="top" class="profile-edit-form">
              <div class="profile-form-grid">
                <el-form-item label="当前密码">
                  <el-input
                    v-model="editForm.currentPassword"
                    type="password"
                    show-password
                    placeholder="请输入当前密码"
                  maxlength="50"
                  autocomplete="current-password"
                    clearable
                  />
                </el-form-item>
                <el-form-item label="新密码">
                  <el-input
                    v-model="editForm.newPassword"
                    type="password"
                    show-password
                    placeholder="不少于 6 位"
                  maxlength="50"
                  autocomplete="new-password"
                    clearable
                  />
                </el-form-item>
              </div>
              <el-form-item label="确认新密码">
                <el-input
                  v-model="editForm.confirmPassword"
                  type="password"
                  show-password
                  placeholder="请再次输入新密码"
                  maxlength="50"
                  autocomplete="new-password"
                  clearable
                />
              </el-form-item>
            </el-form>
            <div class="edit-tip">如果本次不修改密码，密码相关输入框可以留空。</div>
          </section>
        </div>
      </div>
      <template #footer>
        <div class="profile-edit-footer">
          <div class="profile-edit-footer-text">保存后将立即更新当前账号资料。</div>
          <div class="profile-edit-footer-actions">
            <el-button @click="editDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="saving" @click="handleSaveProfile">保存更改</el-button>
          </div>
        </div>
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

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailPattern.test(editForm.email.trim())) {
    ElMessage.warning('邮箱格式不正确')
    return
  }

  if (editForm.currentPassword || editForm.newPassword || editForm.confirmPassword) {
    if (!editForm.currentPassword) {
      ElMessage.warning('修改密码时请输入当前密码')
      return
    }
    if (editForm.currentPassword.length > 50) {
      ElMessage.warning('当前密码长度不能超过 50 位')
      return
    }
    if (editForm.currentPassword.length < 6) {
      ElMessage.warning('当前密码长度至少为 6 位')
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
    if (editForm.newPassword.length > 50) {
      ElMessage.warning('新密码长度不能超过 50 位')
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
    const detail = error.response?.data?.detail
    if (Array.isArray(detail) && detail.length > 0) {
      const firstError = detail[0] || {}
      const field = firstError?.loc?.[firstError.loc.length - 1]
      const fieldLabelMap = {
        email: '邮箱',
        phone: '手机号',
        current_password: '当前密码',
        new_password: '新密码'
      }
      const fieldLabel = fieldLabelMap[field]
      if (fieldLabel) {
        ElMessage.error(`${fieldLabel}格式不正确：${firstError.msg || '请检查后重试'}`)
      } else {
        ElMessage.error(firstError.msg || '提交信息格式不正确，请检查后重试')
      }
    } else {
      ElMessage.error(error.customMessage || detail || '个人信息更新失败')
    }
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
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 20px;
}

.profile-edit-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding-right: 24px;
}

.profile-edit-eyebrow {
  margin: 0 0 8px;
  color: var(--ft-color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.profile-edit-header h2 {
  margin: 0;
  font-size: 26px;
}

.profile-edit-header p {
  margin: 8px 0 0;
  color: var(--ft-color-text-tertiary);
  line-height: 1.6;
}

.profile-edit-header-badge {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(30, 64, 175, 0.08);
  color: var(--ft-color-primary);
  font-size: 12px;
  font-weight: 600;
}

.profile-edit-aside-card {
  height: 100%;
  padding: 22px 18px;
  border-radius: 18px;
  border: 1px solid rgba(30, 64, 175, 0.12);
  background:
    radial-gradient(circle at top, rgba(30, 64, 175, 0.12), transparent 40%),
    linear-gradient(180deg, #ffffff, #f8fbff);
}

.profile-edit-avatar {
  width: 72px;
  height: 72px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  background: linear-gradient(135deg, var(--ft-color-primary), #4360bb);
  color: #fff;
  font-size: 28px;
  font-weight: 700;
  box-shadow: 0 12px 24px rgba(30, 64, 175, 0.18);
}

.profile-edit-aside-card h3 {
  margin: 0;
  font-size: 22px;
}

.profile-edit-aside-card > p {
  margin: 8px 0 18px;
  color: var(--ft-color-text-tertiary);
  line-height: 1.6;
  word-break: break-all;
}

.profile-edit-meta {
  display: grid;
  gap: 12px;
}

.profile-edit-meta-item {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(30, 64, 175, 0.08);
}

.profile-edit-meta-item span {
  display: block;
  margin-bottom: 6px;
  color: var(--ft-color-text-tertiary);
  font-size: 12px;
}

.profile-edit-meta-item strong {
  display: block;
  line-height: 1.5;
}

.profile-edit-note {
  margin-top: 16px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.04);
  color: var(--ft-color-text-secondary);
  font-size: 13px;
  line-height: 1.7;
}

.profile-edit-main {
  display: grid;
  gap: 16px;
}

.edit-panel {
  padding: 22px;
  border-radius: 18px;
  border: 1px solid var(--ft-color-border);
  background: #fff;
}

.edit-panel--primary {
  background:
    linear-gradient(180deg, rgba(30, 64, 175, 0.03), rgba(30, 64, 175, 0)),
    #fff;
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

.profile-edit-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.profile-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.profile-edit-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.profile-edit-footer-text {
  color: var(--ft-color-text-tertiary);
  font-size: 13px;
}

.profile-edit-footer-actions {
  display: flex;
  gap: 12px;
}

:deep(.profile-edit-dialog .el-dialog) {
  overflow: hidden;
  border-radius: 22px;
}

:deep(.profile-edit-dialog .el-dialog__header) {
  padding: 22px 24px 8px;
  margin-right: 0;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  background:
    radial-gradient(circle at top left, rgba(30, 64, 175, 0.08), transparent 34%),
    #fff;
}

:deep(.profile-edit-dialog .el-dialog__body) {
  padding: 20px 24px 16px;
  background: #fcfdff;
}

:deep(.profile-edit-dialog .el-dialog__footer) {
  padding: 16px 24px 22px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
  background: #fff;
}

@media (max-width: 768px) {
  .recent-header {
    flex-direction: column;
  }

  .profile-edit-layout,
  .profile-form-grid {
    grid-template-columns: 1fr;
  }

  .profile-edit-header,
  .profile-edit-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .profile-edit-footer-actions {
    justify-content: stretch;
  }

  .profile-edit-footer-actions .el-button {
    flex: 1;
  }
}
</style>
