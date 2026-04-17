<template>
  <div class="user-management">
    <div class="page-header">
      <div class="page-header-text">
        <h2 class="page-title">用户管理</h2>
        <p class="page-subtitle">统一管理训练系统账号，支持按角色筛选、搜索与批量操作。</p>
      </div>
      <el-button type="primary" @click="goToCreateUser">
        <el-icon><Plus /></el-icon>
        新增用户
      </el-button>
    </div>

    <!-- 搜索和过滤 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent>
        <el-form-item label="账号信息">
          <el-input
            v-model="filterForm.keyword"
            placeholder="输入用户名或邮箱进行搜索"
            clearable
            style="width: 220px"
            @keydown.enter.prevent="handleSearch"
          />
        </el-form-item>

        <el-form-item v-if="isRoot" label="账号角色">
          <el-select
            v-model="filterForm.role"
            placeholder="全部角色"
            style="width: 160px"
            @change="handleSearch"
          >
            <el-option label="全部" value="all" />
            <el-option label="普通用户" value="student" />
            <el-option label="管理员" value="admin" />
            <el-option label="Root" value="root" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 批量操作工具栏 -->
    <el-card shadow="hover" class="batch-toolbar">
      <div class="batch-toolbar-content">
        <div class="selection-summary">
          <el-icon class="selection-icon"><Select /></el-icon>
          <span class="summary-text">
            已选
            <strong>{{ selectionStats.total }}</strong>
            项
          </span>
          <template v-if="selectionStats.total > 0">
            <el-divider direction="vertical" />
            <span v-if="selectionStats.student > 0" class="stat-chip stat-chip--student">
              普通用户 {{ selectionStats.student }}
            </span>
            <span v-if="selectionStats.admin > 0" class="stat-chip stat-chip--admin">
              管理员 {{ selectionStats.admin }}
            </span>
            <el-button text type="primary" size="small" @click="clearSelection">
              清空选择
            </el-button>
          </template>
          <span v-else class="summary-hint">勾选左侧复选框后可执行批量操作</span>
        </div>

        <div class="batch-actions">
          <el-tooltip
            content="请至少选择一个普通用户"
            placement="top"
            :disabled="selectionStats.student > 0"
          >
            <span class="action-wrap">
              <el-button
                type="warning"
                :disabled="selectionStats.student === 0"
                @click="handleBatchResetPassword"
              >
                <el-icon><Key /></el-icon>
                重置密码
              </el-button>
            </span>
          </el-tooltip>

          <el-tooltip
            v-if="isRoot"
            content="请至少选择一个普通用户"
            placement="top"
            :disabled="selectionStats.student > 0"
          >
            <span class="action-wrap">
              <el-button
                type="success"
                :disabled="selectionStats.student === 0"
                @click="handleBatchPromote"
              >
                <el-icon><Top /></el-icon>
                设为管理员
              </el-button>
            </span>
          </el-tooltip>

          <el-tooltip
            v-if="isRoot"
            content="请至少选择一个管理员"
            placement="top"
            :disabled="selectionStats.admin > 0"
          >
            <span class="action-wrap">
              <el-button
                :disabled="selectionStats.admin === 0"
                @click="handleBatchDemote"
              >
                <el-icon><Bottom /></el-icon>
                撤销管理员
              </el-button>
            </span>
          </el-tooltip>

          <el-tooltip
            content="请至少选择一个普通用户"
            placement="top"
            :disabled="selectionStats.student > 0"
          >
            <span class="action-wrap">
              <el-button
                type="danger"
                :disabled="selectionStats.student === 0"
                @click="handleBatchDelete"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </span>
          </el-tooltip>
        </div>
      </div>
    </el-card>

    <!-- 用户表格 -->
    <el-card shadow="hover">
      <el-table
        :data="userList"
        v-loading="loading"
        stripe
        style="width: 100%"
        :row-class-name="tableRowClassName"
      >
        <el-table-column width="55" align="center" class-name="selection-cell">
          <template #header>
            <el-tooltip
              content="全选当前页可选账号"
              placement="top"
              :disabled="selectableRows.length === 0"
            >
              <span class="selection-header-wrap">
                <el-checkbox
                  :model-value="headerChecked"
                  :indeterminate="headerIndeterminate"
                  :disabled="selectableRows.length === 0"
                  @change="toggleSelectAll"
                />
              </span>
            </el-tooltip>
          </template>
          <template #default="{ row }">
            <el-tooltip
              v-if="!isRowSelectable(row)"
              :content="getRowDisableReason(row)"
              placement="top"
            >
              <span class="selection-cell-wrap">
                <el-checkbox :model-value="false" disabled />
              </span>
            </el-tooltip>
            <el-checkbox
              v-else
              :model-value="isRowSelected(row)"
              @change="(val) => toggleRowSelection(row, val)"
            />
          </template>
        </el-table-column>

        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="phone" label="手机号" width="120" />
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
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="180">
          <template #default="{ row }">
            {{ formatDate(row.last_login_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="140">
          <template #default="{ row }">
            <el-tooltip
              v-if="!canViewDetail(row)"
              content="当前账号无权查看该用户详情"
              placement="top"
            >
              <span class="action-wrap">
                <el-button type="primary" size="small" disabled>
                  详情/编辑
                </el-button>
              </span>
            </el-tooltip>
            <el-button
              v-else
              type="primary"
              size="small"
              @click="goToDetail(row)"
            >
              详情/编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handlePageChange"
        @size-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 批量密码重置结果弹窗 -->
    <el-dialog
      v-model="resetResultVisible"
      title="密码重置结果"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-alert
        type="warning"
        show-icon
        :closable="false"
        title="临时密码只展示一次，请及时复制并告知用户。"
        style="margin-bottom: 12px"
      />
      <el-table :data="resetResults" size="small" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" min-width="110" />
        <el-table-column label="临时密码" min-width="140">
          <template #default="{ row }">
            <span v-if="row.success" class="temp-password">{{ row.tempPassword }}</span>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="说明" min-width="160">
          <template #default="{ row }">
            <span>{{ row.message }}</span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="resetResultVisible = false">关闭</el-button>
        <el-button
          type="primary"
          :disabled="!hasResetSuccess"
          @click="copyResetPasswords"
        >
          复制全部成功项
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search,
  Plus,
  Key,
  Top,
  Bottom,
  Delete,
  Select
} from '@element-plus/icons-vue'
import {
  getUsers,
  deleteUser,
  resetUserPassword,
  updateAdminRole
} from '@/api/admin'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const userStore = useUserStore()
const router = useRouter()
const currentUserId = computed(() => userStore.userInfo?.id)
const isRoot = computed(() => userStore.effectiveRole === 'root')

const STUDENT_ROLES = ['student', 'user']
const isStudentRow = (row) => STUDENT_ROLES.includes(row.role)

const userList = ref([])
const loading = ref(false)

const filterForm = reactive({
  keyword: '',
  role: 'all'
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// ========== 选择状态管理 ==========
const selectedIds = ref(new Set())

const isRowSelectable = (row) => {
  if (!row) return false
  if (row.role === 'root') return false
  if (row.id === currentUserId.value) return false
  return true
}

const getRowDisableReason = (row) => {
  if (row.role === 'root') {
    return 'Root 账号不可被批量操作，请到 "管理员管理" 菜单维护'
  }
  if (row.id === currentUserId.value) {
    return '不能对当前登录账号执行批量操作'
  }
  return '该账号暂不支持批量操作'
}

const selectableRows = computed(() =>
  userList.value.filter((row) => isRowSelectable(row))
)

const isRowSelected = (row) => selectedIds.value.has(row.id)

const toggleRowSelection = (row, checked) => {
  const next = new Set(selectedIds.value)
  if (checked) {
    next.add(row.id)
  } else {
    next.delete(row.id)
  }
  selectedIds.value = next
}

const headerChecked = computed(() => {
  const rows = selectableRows.value
  if (rows.length === 0) return false
  return rows.every((row) => selectedIds.value.has(row.id))
})

const headerIndeterminate = computed(() => {
  const rows = selectableRows.value
  if (rows.length === 0) return false
  const selected = rows.filter((row) => selectedIds.value.has(row.id)).length
  return selected > 0 && selected < rows.length
})

const toggleSelectAll = (checked) => {
  const next = new Set(selectedIds.value)
  if (checked) {
    selectableRows.value.forEach((row) => next.add(row.id))
  } else {
    selectableRows.value.forEach((row) => next.delete(row.id))
  }
  selectedIds.value = next
}

const selectedRows = computed(() =>
  userList.value.filter((row) => selectedIds.value.has(row.id))
)

const selectionStats = computed(() => {
  const rows = selectedRows.value
  return {
    total: rows.length,
    student: rows.filter((row) => isStudentRow(row)).length,
    admin: rows.filter((row) => row.role === 'admin').length
  }
})

const clearSelection = () => {
  selectedIds.value = new Set()
}

const tableRowClassName = ({ row }) => {
  if (!isRowSelectable(row)) return 'row-disabled'
  if (isRowSelected(row)) return 'row-selected'
  return ''
}

// ========== 数据加载 ==========
const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filterForm.keyword || undefined
    }

    if (isRoot.value) {
      params.role = filterForm.role || 'all'
    }

    const response = await getUsers(params)

    userList.value = response.users
    pagination.total = response.total

    // 清理不在当前页的选择
    const visibleIds = new Set(userList.value.map((row) => row.id))
    const next = new Set(
      [...selectedIds.value].filter((id) => visibleIds.has(id))
    )
    selectedIds.value = next
  } catch (error) {
    ElMessage.error(
      '获取用户列表失败: ' +
        (error.response?.data?.detail || error.message)
    )
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  clearSelection()
  fetchUsers()
}

const handleReset = () => {
  filterForm.keyword = ''
  filterForm.role = 'all'
  pagination.page = 1
  clearSelection()
  fetchUsers()
}

const handlePageChange = () => {
  clearSelection()
  fetchUsers()
}

const goToCreateUser = () => {
  router.push('/admin/users/new')
}

const canViewDetail = (row) => {
  if (!row) return false
  if (isStudentRow(row)) return true
  // 管理员 / Root 行仅 Root 可查看
  return isRoot.value
}

const goToDetail = (row) => {
  if (!canViewDetail(row)) return
  if (isStudentRow(row)) {
    router.push(`/admin/users/${row.id}`)
  } else {
    router.push(`/admin/admins/${row.id}`)
  }
}

// ========== 批量操作 ==========
const confirmBatchAction = async ({ title, message, confirmText, type = 'warning' }) => {
  try {
    await ElMessageBox.confirm(message, title, {
      confirmButtonText: confirmText || '确认',
      cancelButtonText: '取消',
      type
    })
    return true
  } catch (error) {
    if (error === 'cancel' || error === 'close') return false
    throw error
  }
}

const summarizeBatchResult = (results, successTip, failureTip) => {
  const successes = results.filter((r) => r.ok).length
  const failures = results.filter((r) => !r.ok)

  if (failures.length === 0) {
    ElMessage.success(`${successTip}（共 ${successes} 项）`)
    return
  }

  const reasons = failures
    .slice(0, 3)
    .map((item) => `${item.username}：${item.message}`)
    .join('；')
  ElMessage.warning(
    `${failureTip}：成功 ${successes} 项，失败 ${failures.length} 项${reasons ? '（' + reasons + '）' : ''}`
  )
}

const pickErrorMessage = (error) =>
  error?.response?.data?.detail || error?.message || '操作失败'

// 批量重置密码
const resetResultVisible = ref(false)
const resetResults = ref([])
const hasResetSuccess = computed(() =>
  resetResults.value.some((item) => item.success)
)

const handleBatchResetPassword = async () => {
  const targets = selectedRows.value.filter((row) => isStudentRow(row))
  if (targets.length === 0) return

  const confirmed = await confirmBatchAction({
    title: '批量重置密码',
    message: `将对选中的 ${targets.length} 个普通用户重置密码，操作不可撤销，确认继续？`,
    confirmText: '确认重置',
    type: 'warning'
  })
  if (!confirmed) return

  loading.value = true
  try {
    const results = await Promise.allSettled(
      targets.map((user) => resetUserPassword(user.id))
    )

    resetResults.value = results.map((result, index) => {
      const user = targets[index]
      if (result.status === 'fulfilled') {
        return {
          username: user.username,
          success: true,
          tempPassword: result.value.temp_password,
          message: '已重置，请复制临时密码发送给用户'
        }
      }
      return {
        username: user.username,
        success: false,
        tempPassword: '',
        message: pickErrorMessage(result.reason)
      }
    })
    resetResultVisible.value = true
    clearSelection()
    fetchUsers()
  } finally {
    loading.value = false
  }
}

const copyResetPasswords = async () => {
  const lines = resetResults.value
    .filter((item) => item.success)
    .map((item) => `${item.username}: ${item.tempPassword}`)
  if (lines.length === 0) return
  const text = lines.join('\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制全部成功项到剪贴板')
  } catch {
    ElMessage.warning('浏览器不支持复制，请手动选择文本进行复制')
  }
}

// 批量设为管理员
const handleBatchPromote = async () => {
  const targets = selectedRows.value.filter((row) => isStudentRow(row))
  if (targets.length === 0) return

  const confirmed = await confirmBatchAction({
    title: '批量设为管理员',
    message: `将提升选中的 ${targets.length} 个普通用户为管理员，确认继续？`,
    confirmText: '确认提升',
    type: 'warning'
  })
  if (!confirmed) return

  loading.value = true
  try {
    const results = await Promise.allSettled(
      targets.map((user) => updateAdminRole(user.id, 'admin'))
    )
    const mapped = results.map((result, index) => ({
      username: targets[index].username,
      ok: result.status === 'fulfilled',
      message: result.status === 'fulfilled' ? '已提升' : pickErrorMessage(result.reason)
    }))
    summarizeBatchResult(mapped, '批量设为管理员成功', '批量提升完成')
  } finally {
    clearSelection()
    await fetchUsers()
    loading.value = false
  }
}

// 批量撤销管理员
const handleBatchDemote = async () => {
  const targets = selectedRows.value.filter((row) => row.role === 'admin')
  if (targets.length === 0) return

  const confirmed = await confirmBatchAction({
    title: '批量撤销管理员',
    message: `将撤销选中的 ${targets.length} 个管理员权限，降级为普通用户，确认继续？`,
    confirmText: '确认撤销',
    type: 'warning'
  })
  if (!confirmed) return

  loading.value = true
  try {
    const results = await Promise.allSettled(
      targets.map((user) => updateAdminRole(user.id, 'student'))
    )
    const mapped = results.map((result, index) => ({
      username: targets[index].username,
      ok: result.status === 'fulfilled',
      message: result.status === 'fulfilled' ? '已撤销' : pickErrorMessage(result.reason)
    }))
    summarizeBatchResult(mapped, '批量撤销管理员成功', '批量撤销完成')
  } finally {
    clearSelection()
    await fetchUsers()
    loading.value = false
  }
}

// 批量删除
const handleBatchDelete = async () => {
  const targets = selectedRows.value.filter((row) => isStudentRow(row))
  if (targets.length === 0) return

  const confirmed = await confirmBatchAction({
    title: '批量删除用户',
    message: `确定要删除选中的 ${targets.length} 个普通用户吗？该操作不可恢复！`,
    confirmText: '确认删除',
    type: 'warning'
  })
  if (!confirmed) return

  loading.value = true
  try {
    const results = await Promise.allSettled(
      targets.map((user) => deleteUser(user.id))
    )
    const mapped = results.map((result, index) => ({
      username: targets[index].username,
      ok: result.status === 'fulfilled',
      message: result.status === 'fulfilled' ? '已删除' : pickErrorMessage(result.reason)
    }))
    summarizeBatchResult(mapped, '批量删除成功', '批量删除完成')
  } finally {
    clearSelection()
    await fetchUsers()
    loading.value = false
  }
}

// ========== 辅助函数 ==========
const getRoleType = (role) => {
  const roleMap = {
    root: 'danger',
    admin: 'warning',
    student: 'info',
    user: 'info'
  }
  return roleMap[role] || 'info'
}

const getRoleLabel = (role) => {
  const labelMap = {
    root: 'Root',
    admin: '管理员',
    student: '普通用户',
    user: '普通用户'
  }
  return labelMap[role] || role
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-management {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.page-header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  margin: 0;
  color: #303133;
  font-size: 22px;
  font-weight: 600;
}

.page-subtitle {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.filter-card {
  margin-bottom: 16px;
}

.batch-toolbar {
  margin-bottom: 16px;
  background: linear-gradient(135deg, #fafbff 0%, #f4f6fb 100%);
  border: 1px solid #e4e7ed;
}

.batch-toolbar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.selection-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #606266;
  flex-wrap: wrap;
}

.selection-icon {
  color: var(--el-color-primary);
  font-size: 18px;
}

.summary-text strong {
  margin: 0 2px;
  color: var(--el-color-primary);
  font-size: 16px;
  font-weight: 700;
}

.summary-hint {
  color: #909399;
  font-size: 12px;
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  background: #eef2fb;
  color: #4361ee;
}

.stat-chip--admin {
  background: #fff4e6;
  color: #d97706;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.action-wrap {
  display: inline-block;
}

.selection-cell {
  text-align: center;
}

.selection-cell-wrap,
.selection-header-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

:deep(.row-selected) td {
  background-color: #f0f5ff !important;
}

:deep(.row-disabled) {
  color: #a8abb2;
}

:deep(.row-disabled) td {
  background-color: #fafafa;
}

.temp-password {
  font-family: 'Fira Code', 'SFMono-Regular', Menlo, Monaco, Consolas, monospace;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
  color: #303133;
  font-size: 13px;
}

.text-muted {
  color: #909399;
}

@media (max-width: 768px) {
  .batch-toolbar-content {
    flex-direction: column;
    align-items: stretch;
  }

  .batch-actions {
    justify-content: flex-start;
  }
}
</style>
