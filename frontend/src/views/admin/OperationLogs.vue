<template>
  <div class="operation-logs">
    <h2 class="page-title">📜 操作日志</h2>
    
    <!-- 搜索和过滤 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="操作类型">
          <el-select v-model="filterForm.action" placeholder="全部" clearable style="width: 180px">
            <el-option label="删除用户" value="DELETE_USER" />
            <el-option label="更新用户" value="UPDATE_USER" />
            <el-option label="创建用户" value="CREATE_USER" />
            <el-option label="重置用户密码" value="RESET_USER_PASSWORD" />
            <el-option label="删除训练记录" value="DELETE_TRAINING" />
            <el-option label="上传视频" value="UPLOAD_VIDEO" />
            <el-option label="删除视频" value="DELETE_VIDEO" />
            <el-option label="创建管理员" value="CREATE_ADMIN" />
            <el-option label="删除管理员" value="DELETE_ADMIN" />
            <el-option label="更新管理员" value="UPDATE_ADMIN" />
            <el-option label="更新角色" value="UPDATE_ROLE" />
            <el-option label="重置管理员密码" value="RESET_ADMIN_PASSWORD" />
            <el-option label="切换到用户" value="SWITCH_TO_USER" />
            <el-option label="切换到管理员" value="SWITCH_TO_ADMIN" />
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
    
    <!-- 日志表格 -->
    <el-card shadow="hover">
      <el-table
        :data="logList"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="操作ID" width="80" />
        <el-table-column prop="admin_id" label="管理员ID" width="100" />
        <el-table-column label="操作类型" width="180">
          <template #default="{ row }">
            <el-tag size="small">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标类型" width="120">
          <template #default="{ row }">
            {{ row.target_type || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="目标ID" width="100">
          <template #default="{ row }">
            {{ row.target_id || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作详情" min-width="200">
          <template #default="{ row }">
            <span v-if="row.details" class="details-text">
              {{ formatDetails(row.details) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="150" />
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
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
        @current-change="fetchLogs"
        @size-change="fetchLogs"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getAdminLogs } from '@/api/admin'
import { ElMessage } from 'element-plus'

const logList = ref([])
const loading = ref(false)

const filterForm = reactive({
  action: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 获取操作日志列表
const fetchLogs = async () => {
  loading.value = true
  try {
    const response = await getAdminLogs({
      page: pagination.page,
      page_size: pagination.pageSize,
      action: filterForm.action || undefined
    })
    
    logList.value = response.logs
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('获取操作日志失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchLogs()
}

// 重置
const handleReset = () => {
  filterForm.action = ''
  pagination.page = 1
  fetchLogs()
}

// 格式化详情
const formatDetails = (details) => {
  if (typeof details === 'object') {
    return Object.entries(details)
      .map(([key, value]) => `${key}: ${value}`)
      .join(', ')
  }
  return String(details)
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.operation-logs {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  margin-bottom: 20px;
  color: #303133;
}

.filter-card {
  margin-bottom: 20px;
}

.details-text {
  font-size: 12px;
  color: #606266;
}
</style>
