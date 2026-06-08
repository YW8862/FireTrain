<template>
  <div class="user-detail-page">
    <el-breadcrumb separator="/" class="breadcrumb">
      <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: '/admin/users' }">用户管理</el-breadcrumb-item>
      <el-breadcrumb-item>{{ isCreateMode ? '新增用户' : '用户详情' }}</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="hover" class="detail-card">
      <template #header>
        <div class="card-header">
          <span>{{ isCreateMode ? '新增普通用户' : `用户详情：${form.username || '-'}` }}</span>
          <div class="header-actions">
            <el-button @click="goBack">返回</el-button>
            <el-button v-if="!isCreateMode" type="warning" @click="handleResetPassword">
              重置密码
            </el-button>
            <el-button type="primary" :loading="saving" @click="handleSave">
              {{ isCreateMode ? '创建用户' : '保存修改' }}
            </el-button>
          </div>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        class="detail-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="请输入用户名" :disabled="!isCreateMode" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="form.phone" placeholder="请输入手机号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="isCreateMode ? '登录密码' : '新密码'">
              <el-input
                v-model="form.password"
                type="password"
                :placeholder="isCreateMode ? '请输入登录密码' : '留空则不修改密码'"
                show-password
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用状态">
              <el-switch v-model="form.is_active" />
            </el-form-item>
          </el-col>
                    <el-col v-if="!isCreateMode" :span="12">
            <el-form-item label="最后登录">
              <span>{{ formatDate(form.last_login_at) }}</span>
            </el-form-item>
          </el-col>
          <el-col v-if="!isCreateMode" :span="12">
            <el-form-item label="注册时间">
              <span>{{ formatDate(form.created_at) }}</span>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <template v-if="!isCreateMode && !isViewingSelfAsRoot">
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ userStats.total_trainings }}</div>
            <div class="stat-label">总训练次数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ userStats.completed_trainings }}</div>
            <div class="stat-label">完成次数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ userStats.average_score }}</div>
            <div class="stat-label">平均分</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ userStats.best_score }}</div>
            <div class="stat-label">最高分</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" class="stats-row">
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span>训练趋势（最近 {{ trendDays }} 天）</span>
                <el-select v-model="trendDays" style="width: 120px" @change="loadStatistics">
                  <el-option label="最近 7 天" :value="7" />
                  <el-option label="最近 15 天" :value="15" />
                  <el-option label="最近 30 天" :value="30" />
                </el-select>
              </div>
            </template>
            <el-table :data="trendData" size="small" stripe>
              <el-table-column prop="date" label="日期" />
              <el-table-column prop="training_count" label="训练次数" width="100" />
              <el-table-column prop="average_score" label="平均分" width="100" />
              <el-table-column prop="best_score" label="最高分" width="100" />
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>步骤分析</span>
            </template>
            <el-table :data="stepAnalysis" size="small" stripe>
              <el-table-column prop="step_name" label="步骤" />
              <el-table-column prop="average_score" label="平均分" width="90" />
              <el-table-column label="成功率" width="100">
                <template #default="{ row }">
                  {{ formatSuccessRate(row.success_rate) }}
                </template>
              </el-table-column>
              <el-table-column prop="improvement_suggestion" label="建议" min-width="180" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="hover" class="trainings-card">
        <template #header>
          <div class="card-header">
            <span>训练记录</span>
            <el-tag type="info">共 {{ trainings.total }} 条</el-tag>
          </div>
        </template>

        <el-table :data="trainings.records" v-loading="recordsLoading" stripe>
          <el-table-column prop="id" label="训练ID" width="100" />
          <el-table-column prop="training_type" label="训练类型" width="150" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="total_score" label="总分" width="100" />
          <el-table-column prop="duration_seconds" label="时长(秒)" width="110" />
          <el-table-column prop="created_at" label="开始时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="completed_at" label="完成时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.completed_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                type="primary"
                :disabled="row.status !== 'done'"
                @click="goToReport(row.id)"
              >
                查看报告
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="trainings.page"
          v-model:page-size="trainings.page_size"
          :total="trainings.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          class="pagination"
          @current-change="loadTrainings"
          @size-change="handlePageSizeChange"
        />
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createUser,
  getUserDetail,
  getUserStatistics,
  getUserTrainings,
  resetUserPassword,
  updateUser
} from '@/api/admin'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const saving = ref(false)
const recordsLoading = ref(false)
const trendDays = ref(7)

const isCreateMode = computed(() => route.name === 'AdminUserCreate')
const isSuperAdmin = computed(() => userStore.userInfo?.role === 'root')
// 当前登录的超级管理员查看自己详情时隐藏训练数据
const isViewingSelfAsRoot = computed(() => {
  const currentUserId = userStore.userInfo?.id
  const viewedUserId = Number(route.params.id)
  return currentUserId === viewedUserId && isSuperAdmin.value
})

const form = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  is_active: true,
  last_login_at: null,
  created_at: null
})

const userStats = reactive({
  total_trainings: 0,
  completed_trainings: 0,
  average_score: 0,
  best_score: 0
})

const trendData = ref([])
const stepAnalysis = ref([])

const trainings = reactive({
  total: 0,
  page: 1,
  page_size: 10,
  records: []
})

const validatePassword = (rule, value, callback) => {
  if (isCreateMode.value && !value) {
    callback(new Error('请输入密码'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为 3-50 个字符', trigger: 'blur' }
  ],
  password: [
    { validator: validatePassword, trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const resetFormData = () => {
  form.username = ''
  form.email = ''
  form.phone = ''
  form.password = ''
  form.is_active = true
  form.last_login_at = null
  form.created_at = null
}

const applyUserInfo = (user) => {
  form.username = user.username || ''
  form.email = user.email || ''
  form.phone = user.phone || ''
  form.password = ''
  form.is_active = user.is_active ?? true
  form.last_login_at = user.last_login_at || null
  form.created_at = user.created_at || null
}

const loadDetail = async () => {
  if (isCreateMode.value) {
    resetFormData()
    return
  }

  const user = await getUserDetail(route.params.id)
  applyUserInfo(user)
}

const loadStatistics = async () => {
  if (isCreateMode.value) return

  const response = await getUserStatistics(route.params.id, { days: trendDays.value })
  userStats.total_trainings = response.personal_stats?.total_trainings || 0
  userStats.completed_trainings = response.personal_stats?.completed_trainings || 0
  userStats.average_score = Number(response.personal_stats?.average_score || 0).toFixed(1)
  userStats.best_score = Number(response.personal_stats?.best_score || 0).toFixed(1)
  trendData.value = response.recent_trend?.trend_data || []
  stepAnalysis.value = response.step_analysis?.step_analysis || []
}

const loadTrainings = async () => {
  if (isCreateMode.value) return

  recordsLoading.value = true
  try {
    const response = await getUserTrainings(route.params.id, {
      page: trainings.page,
      page_size: trainings.page_size
    })
    trainings.total = response.total
    trainings.page = response.page
    trainings.page_size = response.page_size
    trainings.records = response.records
  } finally {
    recordsLoading.value = false
  }
}

const handlePageSizeChange = () => {
  trainings.page = 1
  loadTrainings()
}

const loadPageData = async () => {
  try {
    await loadDetail()
    await Promise.all([loadStatistics(), loadTrainings()])
  } catch (error) {
    ElMessage.error(error.customMessage || error.response?.data?.detail || '加载用户详情失败')
  }
}

const handleSave = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return

  if (isCreateMode.value && !form.password) {
    ElMessage.error('请填写登录密码')
    return
  }

  saving.value = true
  try {
    const payload = {
      username: form.username,
      email: form.email || null,
      phone: form.phone || null,
      password: form.password,
      is_active: form.is_active
    }
    console.log('Creating user with payload:', JSON.stringify(payload, null, 2))

    if (isCreateMode.value) {
      await createUser(payload)
      ElMessage.success('普通用户创建成功')
      router.push('/admin/users')
      return
    }

    const updated = await updateUser(route.params.id, payload)
    applyUserInfo(updated)
    ElMessage.success('用户信息更新成功')
  } catch (error) {
    ElMessage.error(error.customMessage || error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleResetPassword = async () => {
  if (isCreateMode.value) return

  try {
    const response = await resetUserPassword(route.params.id)
    await ElMessageBox.alert(
      `临时密码：${response.temp_password}\n\n${response.warning}`,
      '密码重置成功',
      {
        confirmButtonText: '知道了',
        type: 'success'
      }
    )
  } catch (error) {
    ElMessage.error(error.customMessage || error.response?.data?.detail || '重置密码失败')
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatSuccessRate = (value) => {
  const rate = Number(value || 0)
  return `${rate.toFixed(1)}%`
}

const goToReport = (trainingId) => {
  router.push(`/admin/report/${trainingId}`)
}

const goBack = () => {
  // 根据来源路由返回
  if (route.query.from === 'admin-management') {
    router.push('/admin/admins')
  } else {
    router.push('/admin/users')
  }
}

onMounted(() => {
  loadPageData()
})
</script>

<style scoped>
.user-detail-page {
  max-width: 1400px;
  margin: 0 auto;
}

.breadcrumb {
  margin-bottom: 16px;
}

.detail-card,
.trainings-card,
.stats-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.detail-form {
  padding-top: 8px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 30px;
  font-weight: 700;
  color: #409eff;
}

.stat-label {
  margin-top: 8px;
  color: #606266;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
