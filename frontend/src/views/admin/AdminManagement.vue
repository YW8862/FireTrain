<template>
  <div class="admin-management">
    <h2 class="page-title">权限管理</h2>

    <!-- 搜索和操作 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="用户名/邮箱"
            clearable
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>

        <el-form-item style="float: right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新增管理员
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 批量操作工具栏 -->
    <el-card shadow="hover" class="batch-toolbar">
      <div class="batch-toolbar-content">
        <div class="selection-summary">
          <el-icon class="selection-icon"><Select /></el-icon>
          <span class="summary-text">
            已选 <strong>{{ selectionCount }}</strong> 个管理员
          </span>
          <el-divider direction="vertical" />
          <el-button text type="primary" size="small" @click="clearSelection">
            清空选择
          </el-button>
        </div>

        <div class="batch-actions">
          <el-button type="warning" @click="handleBatchResetPassword">
            <el-icon><Key /></el-icon>
            重置密码
          </el-button>
          <el-button @click="handleBatchDemote">
            <el-icon><Bottom /></el-icon>
            撤销管理员
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 管理员表格 -->
    <el-card shadow="hover">
      <el-table
        :data="adminList"
        v-loading="loading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" :selectable="checkSelectable" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '冻结' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="120">
          <template #default="{ row }">
            <el-button type="success" size="small" @click="goToDetail(row)">
              详情/编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchAdmins"
          @current-change="fetchAdmins"
        />
      </div>
    </el-card>

    <!-- 新增管理员对话框 - 从普通用户中选择 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新增管理员"
      width="600px"
      @close="resetCreateForm"
    >
      <div class="create-tip">请从下方普通用户列表中选择一个或多个用户，点击"确认添加"将其提升为管理员</div>

      <el-form :inline="true" :model="createFilterForm" class="user-search-form">
        <el-form-item label="搜索用户">
          <el-input
            v-model="createFilterForm.keyword"
            placeholder="输入用户名或邮箱搜索"
            clearable
            style="width: 200px"
            @keydown.enter="searchNormalUsers"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchNormalUsers">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table
        ref="userTableRef"
        :data="normalUsers"
        v-loading="usersLoading"
        stripe
        height="300"
        @selection-change="handleUserSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="phone" label="手机号" width="120" />
      </el-table>

      <div class="selected-count" v-if="selectedUsers.length > 0">
        已选择 {{ selectedUsers.length }} 个用户
      </div>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="creating"
          :disabled="selectedUsers.length === 0"
          @click="handleCreate"
        >
          确认添加 ({{ selectedUsers.length }})
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Key, Bottom, Select } from '@element-plus/icons-vue'
import {
  getAdmins,
  getUsers,
  resetAdminPassword,
  updateAdminRole
} from '@/api/admin'

const router = useRouter()

// 数据
const loading = ref(false)
const adminList = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const filterForm = reactive({
  keyword: ''
})

// 批量选择相关
const selectedAdmins = ref([])
const selectionCount = computed(() => selectedAdmins.value.length)

const checkSelectable = (row) => {
  return row.role !== 'root'
}

// 创建对话框 - 从普通用户选择
const createDialogVisible = ref(false)
const usersLoading = ref(false)
const normalUsers = ref([])
const selectedUsers = ref([])
const creating = ref(false)
const createFilterForm = reactive({
  keyword: ''
})

// 批量操作结果
const resultDialogVisible = ref(false)
const resultDialogTitle = ref('')
const operationResults = ref([])

// 方法
const fetchAdmins = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: filterForm.keyword || undefined
    }

    const response = await getAdmins(params)
    adminList.value = response.admins
    pagination.total = response.total
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取管理员列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchAdmins()
}

const handleReset = () => {
  filterForm.keyword = ''
  pagination.page = 1
  fetchAdmins()
}

const handleSelectionChange = (selection) => {
  selectedAdmins.value = selection
}

const clearSelection = () => {
  selectedAdmins.value = []
}

const showCreateDialog = async () => {
  createDialogVisible.value = true
  await searchNormalUsers()
}

const searchNormalUsers = async () => {
  usersLoading.value = true
  try {
    const response = await getUsers({
      page: 1,
      page_size: 100,
      role: 'student',
      keyword: createFilterForm.keyword || undefined
    })
    // 过滤掉已经是管理员的用户
    normalUsers.value = (response.users || []).filter(
      (u) => u.role === 'student' || u.role === 'user'
    )
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取用户列表失败')
  } finally {
    usersLoading.value = false
  }
}

const handleUserSelectionChange = (selection) => {
  selectedUsers.value = selection
}

const resetCreateForm = () => {
  createFilterForm.keyword = ''
  normalUsers.value = []
  selectedUsers.value = []
}

const goToDetail = (row) => {
  // 跳转到用户详情页（复用用户详情界面），并标记来源
  router.push({
    path: `/admin/users/${row.id}`,
    query: { from: 'admin-management' }
  })
}

const handleCreate = async () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('请至少选择一个用户')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要将选中的 ${selectedUsers.value.length} 个普通用户提升为管理员吗？`,
      '确认提升',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  loading.value = true
  creating.value = true
  try {
    const results = await Promise.allSettled(
      selectedUsers.value.map((user) => updateAdminRole(user.id, 'admin'))
    )
    operationResults.value = results.map((result, index) => ({
      username: selectedUsers.value[index].username,
      success: result.status === 'fulfilled',
      message: result.status === 'fulfilled' ? '已提升为管理员' : (result.reason?.response?.data?.detail || '操作失败')
    }))
    resultDialogTitle.value = `新增管理员结果（${operationResults.value.filter(r => r.success).length} 成功）`
    resultDialogVisible.value = true
    createDialogVisible.value = false
    clearSelection()
    fetchAdmins()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
    creating.value = false
  }
}

const handleResetPassword = async (row) => {
  try {
    const response = await resetAdminPassword(row.id)
    ElMessage.success(`已重置密码，临时密码：${response.temp_password}`)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '重置管理员密码失败')
  }
}

// 批量操作
const handleBatchResetPassword = async () => {
  if (selectedAdmins.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要重置选中的 ${selectedAdmins.value.length} 个管理员的密码吗？`,
      '确认重置密码',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  loading.value = true
  try {
    const results = await Promise.allSettled(
      selectedAdmins.value.map((admin) => resetAdminPassword(admin.id))
    )
    const successCount = results.filter((r) => r.status === 'fulfilled').length
    operationResults.value = results.map((result, index) => ({
      username: selectedAdmins.value[index].username,
      success: result.status === 'fulfilled',
      message: result.status === 'fulfilled'
        ? `新密码：${result.value.temp_password}`
        : (result.reason?.response?.data?.detail || '操作失败')
    }))
    resultDialogTitle.value = `重置密码结果（${successCount} 成功）`
    resultDialogVisible.value = true
    clearSelection()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
  }
}

const handleBatchDemote = async () => {
  if (selectedAdmins.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要将选中的 ${selectedAdmins.value.length} 个管理员降级为普通用户吗？`,
      '确认降级',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  loading.value = true
  try {
    const results = await Promise.allSettled(
      selectedAdmins.value.map((admin) => updateAdminRole(admin.id, 'student'))
    )
    const successCount = results.filter((r) => r.status === 'fulfilled').length
    operationResults.value = results.map((result, index) => ({
      username: selectedAdmins.value[index].username,
      success: result.status === 'fulfilled',
      message: result.status === 'fulfilled' ? '已降级为普通用户' : (result.reason?.response?.data?.detail || '操作失败')
    }))
    resultDialogTitle.value = `撤销管理员结果（${successCount} 成功）`
    resultDialogVisible.value = true
    clearSelection()
    fetchAdmins()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
  }
}

const getRoleType = (role) => {
  const types = {
    root: 'danger',
    admin: 'primary',
    student: 'info',
    user: 'info'
  }
  return types[role] || 'info'
}

const getRoleLabel = (role) => {
  const labels = {
    root: 'Root',
    admin: '管理员',
    student: '普通用户',
    user: '普通用户'
  }
  return labels[role] || role
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchAdmins()
})
</script>

<style scoped>
.admin-management {
  padding: 20px;
}

.page-title {
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.filter-card {
  margin-bottom: 20px;
}

.batch-toolbar {
  margin-bottom: 20px;
  border: 1px solid var(--el-color-primary-light-7);
  background: var(--el-color-primary-light-9);
}

.batch-toolbar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  gap: 20px;
}

.selection-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.selection-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}

.summary-text {
  font-size: 14px;
}

.batch-actions {
  display: flex;
  gap: 12px;
}

.create-tip {
  margin-bottom: 16px;
  padding: 12px;
  background: #fdf6ec;
  border-radius: 4px;
  color: #909399;
  font-size: 13px;
}

.user-search-form {
  margin-bottom: 16px;
}

.selected-count {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--el-color-primary-light-9);
  border-radius: 4px;
  color: var(--el-color-primary);
  font-size: 13px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>