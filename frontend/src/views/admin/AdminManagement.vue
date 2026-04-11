<template>
  <div class="admin-management">
    <h2 class="page-title">👮 管理员管理</h2>

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

    <!-- 管理员表格 -->
    <el-card shadow="hover">
      <el-table
        :data="adminList"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="220" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="可切换角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.can_switch_role ? 'success' : 'info'" size="small">
              {{ row.can_switch_role ? '是' : '否' }}
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
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-dropdown @command="(cmd) => handleRoleChange(row, cmd)">
              <el-button type="primary" size="small">
                修改角色 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="user" :disabled="row.role === 'user'">
                    普通用户
                  </el-dropdown-item>
                  <el-dropdown-item command="admin" :disabled="row.role === 'admin'">
                    管理员
                  </el-dropdown-item>
                  <el-dropdown-item command="root" :disabled="row.role === 'root'">
                    Root
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <el-popconfirm
              title="确定要删除该管理员吗？此操作不可恢复！"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" size="small" style="margin-left: 8px">
                  删除
                </el-button>
              </template>
            </el-popconfirm>
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

    <!-- 新增管理员对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新增管理员"
      width="500px"
      @close="resetCreateForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名（3-20字符）" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" placeholder="请输入邮箱" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="createForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            show-password
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="createForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="Root" value="root" />
          </el-select>
        </el-form-item>

        <el-form-item label="可切换角色">
          <el-switch v-model="createForm.can_switch_role" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            允许在管理员和用户身份间切换
          </span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus, ArrowDown } from '@element-plus/icons-vue'
import { getAdmins, createAdmin, deleteAdmin, updateAdminRole } from '@/api/admin'

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

// 创建对话框
const createDialogVisible = ref(false)
const createFormRef = ref(null)
const creating = ref(false)
const createForm = reactive({
  username: '',
  email: '',
  password: '',
  role: 'admin',
  can_switch_role: true
})

const createRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3-20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

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
    adminList.value = response.data.admins
    pagination.total = response.data.total
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

const showCreateDialog = () => {
  createDialogVisible.value = true
}

const resetCreateForm = () => {
  createFormRef.value?.resetFields()
  createForm.username = ''
  createForm.email = ''
  createForm.password = ''
  createForm.role = 'admin'
  createForm.can_switch_role = true
}

const handleCreate = async () => {
  const valid = await createFormRef.value?.validate()
  if (!valid) return

  creating.value = true
  try {
    await createAdmin(createForm)
    ElMessage.success('管理员创建成功')
    createDialogVisible.value = false
    fetchAdmins()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '创建管理员失败')
  } finally {
    creating.value = false
  }
}

const handleRoleChange = async (row, newRole) => {
  if (row.role === newRole) return

  try {
    await updateAdminRole(row.id, newRole)
    ElMessage.success('角色修改成功')
    fetchAdmins()
  } catch (error) {
    const errorMsg = error.response?.data?.detail || '修改角色失败'
    if (errorMsg.includes('最后一个')) {
      ElMessage.error('无法修改最后一个 Root 用户的角色')
    } else {
      ElMessage.error(errorMsg)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await deleteAdmin(row.id)
    ElMessage.success('管理员删除成功')
    fetchAdmins()
  } catch (error) {
    const errorMsg = error.response?.data?.detail || '删除管理员失败'
    if (errorMsg.includes('最后一个')) {
      ElMessage.error('无法删除最后一个 Root 用户')
    } else {
      ElMessage.error(errorMsg)
    }
  }
}

const getRoleType = (role) => {
  const types = {
    root: 'danger',
    admin: 'primary',
    user: 'info'
  }
  return types[role] || 'info'
}

const getRoleLabel = (role) => {
  const labels = {
    root: 'Root',
    admin: '管理员',
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

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
