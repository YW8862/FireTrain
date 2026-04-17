<template>
  <div class="admin-detail-page">
    <el-breadcrumb separator="/" class="breadcrumb">
      <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: '/admin/users' }">用户管理</el-breadcrumb-item>
      <el-breadcrumb-item>管理员详情</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="hover" class="detail-card" v-loading="loadingDetail">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span class="header-title-text">管理员详情：{{ form.username || '-' }}</span>
            <el-tag :type="getRoleType(form.role)" size="small">
              {{ getRoleLabel(form.role) }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button @click="goBack">返回</el-button>
            <el-button type="warning" :disabled="isSelf" @click="handleResetPassword">
              重置密码
            </el-button>
            <el-button type="primary" :loading="saving" @click="handleSave">
              保存修改
            </el-button>
          </div>
        </div>
      </template>

      <el-alert
        v-if="isSelf"
        title="当前查看的是你自己的账号，部分敏感操作已禁用，请到「个人中心」管理个人信息。"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 16px"
      />

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
              <el-input v-model="form.username" placeholder="请输入用户名" />
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
            <el-form-item label="新密码">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="留空则不修改密码"
                show-password
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用状态">
              <el-switch
                v-model="form.is_active"
                :disabled="form.role === 'root' && isSelf"
              />
              <span v-if="form.role === 'root' && isSelf" class="field-hint">
                不能禁用自己
              </span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="允许切换角色">
              <el-switch v-model="form.can_switch_role" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="原始角色">
              <el-select
                v-model="form.original_role"
                clearable
                :disabled="!form.can_switch_role || form.role === 'root'"
                placeholder="无"
                style="width: 100%"
              >
                <el-option label="管理员" value="admin" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最后登录">
              <span>{{ formatDate(form.last_login_at) }}</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="注册时间">
              <span>{{ formatDate(form.created_at) }}</span>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card shadow="hover" class="role-card">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span class="header-title-text">角色管理</span>
          </div>
        </div>
      </template>
      <div class="role-panel">
        <div class="role-info">
          <div class="role-info-item">
            <span class="role-info-label">当前角色</span>
            <el-tag :type="getRoleType(form.role)">{{ getRoleLabel(form.role) }}</el-tag>
          </div>
          <p class="role-tip">
            只能在"普通用户"和"管理员"之间切换；系统内 Root 账号唯一且不可新增或升级。
          </p>
        </div>
        <div class="role-actions">
          <el-select
            v-model="newRole"
            placeholder="选择目标角色"
            style="width: 180px"
            :disabled="isSelf || form.role === 'root'"
          >
            <el-option label="普通用户" value="student" />
            <el-option label="管理员" value="admin" />
          </el-select>
          <el-button
            type="primary"
            :disabled="!newRole || newRole === form.role || isSelf || form.role === 'root'"
            @click="handleChangeRole"
          >
            应用角色变更
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAdminDetail,
  resetAdminPassword,
  updateAdmin,
  updateAdminRole
} from '@/api/admin'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const saving = ref(false)
const loadingDetail = ref(false)
const newRole = ref('')

const adminId = computed(() => Number(route.params.id))
const isSelf = computed(() => adminId.value === userStore.userInfo?.id)

const form = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  role: '',
  is_active: true,
  can_switch_role: false,
  original_role: null,
  last_login_at: null,
  created_at: null
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为 3-50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const applyAdminInfo = (admin) => {
  form.username = admin.username || ''
  form.email = admin.email || ''
  form.phone = admin.phone || ''
  form.password = ''
  form.role = admin.role || ''
  form.is_active = admin.is_active ?? true
  form.can_switch_role = admin.can_switch_role ?? false
  form.original_role = admin.original_role || null
  form.last_login_at = admin.last_login_at || null
  form.created_at = admin.created_at || null
  newRole.value = admin.role || ''
}

const loadDetail = async () => {
  loadingDetail.value = true
  try {
    const admin = await getAdminDetail(adminId.value)
    applyAdminInfo(admin)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载管理员详情失败')
  } finally {
    loadingDetail.value = false
  }
}

const handleSave = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  if (!form.can_switch_role) {
    form.original_role = null
  }

  saving.value = true
  try {
    const payload = {
      username: form.username,
      email: form.email,
      phone: form.phone || null,
      password: form.password || undefined,
      is_active: form.is_active,
      can_switch_role: form.can_switch_role,
      original_role: form.original_role || null
    }
    const updated = await updateAdmin(adminId.value, payload)
    applyAdminInfo(updated)
    ElMessage.success('管理员信息更新成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleResetPassword = async () => {
  if (isSelf.value) return
  try {
    await ElMessageBox.confirm(
      `确定要重置 "${form.username}" 的登录密码？临时密码生成后请立即保存。`,
      '重置管理员密码',
      {
        confirmButtonText: '确认重置',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }

  try {
    const response = await resetAdminPassword(adminId.value)
    await ElMessageBox.alert(
      `临时密码：${response.temp_password}\n\n${response.warning || '请立即告知该管理员。'}`,
      '密码重置成功',
      { confirmButtonText: '知道了', type: 'success' }
    )
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '重置密码失败')
  }
}

const handleChangeRole = async () => {
  if (!newRole.value || newRole.value === form.role) return
  if (isSelf.value) {
    ElMessage.warning('不能修改自己的角色')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定将 "${form.username}" 的角色由 "${getRoleLabel(form.role)}" 变更为 "${getRoleLabel(newRole.value)}"？`,
      '角色变更确认',
      {
        confirmButtonText: '确认变更',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }

  try {
    await updateAdminRole(adminId.value, newRole.value)
    ElMessage.success('角色变更成功')
    await loadDetail()
  } catch (error) {
    const detail = error.response?.data?.detail || '角色变更失败'
    if (String(detail).includes('最后一个')) {
      ElMessage.error('无法修改最后一个 Root 用户的角色')
    } else {
      ElMessage.error(detail)
    }
  }
}

const getRoleType = (role) => {
  const map = { root: 'danger', admin: 'warning', student: 'info', user: 'info' }
  return map[role] || 'info'
}

const getRoleLabel = (role) => {
  const map = { root: 'Root', admin: '管理员', student: '普通用户', user: '普通用户' }
  return map[role] || role || '-'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const goBack = () => {
  router.push('/admin/users')
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.admin-detail-page {
  max-width: 1400px;
  margin: 0 auto;
}

.breadcrumb {
  margin-bottom: 16px;
}

.detail-card,
.role-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title-text {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.detail-form {
  padding-top: 8px;
}

.field-hint {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}

.role-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.role-info {
  flex: 1;
  min-width: 220px;
}

.role-info-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.role-info-label {
  color: #606266;
  font-size: 13px;
}

.role-tip {
  margin: 8px 0 0;
  color: #909399;
  font-size: 12px;
  line-height: 1.6;
}

.role-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>
