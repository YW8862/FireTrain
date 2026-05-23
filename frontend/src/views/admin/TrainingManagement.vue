<template>
  <div class="training-management">
    <div class="page-header">
      <div>
        <h2 class="page-title">训练数据管理</h2>
        <p class="page-subtitle">筛选训练记录、查看报告并执行删除等管理操作。</p>
      </div>
    </div>

    <!-- 搜索和过滤 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="用户ID">
          <el-input
            v-model="filterForm.user_id"
            placeholder="用户ID"
            clearable
            style="width: 120px"
          />
        </el-form-item>

        <el-form-item label="训练类型">
          <el-select v-model="filterForm.training_type" placeholder="全部" clearable style="width: 150px">
            <el-option label="灭火器操作" value="fire_extinguisher" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="等待检测中" value="pending" />
            <el-option label="检测中" value="processing" />
            <el-option label="已完成" value="done" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
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
            已选 <strong>{{ selectedTrainings.length }}</strong> 条训练记录
          </span>
          <el-divider direction="vertical" />
          <el-button text type="primary" size="small" @click="clearSelection">
            清空选择
          </el-button>
        </div>

        <div class="batch-actions">
          <el-popconfirm
            title="确定要删除选中的训练记录吗？此操作不可恢复！"
            confirm-button-text="确定"
            cancel-button-text="取消"
            @confirm="handleBatchDelete"
          >
            <template #reference>
              <el-button type="danger" :disabled="selectedTrainings.length === 0">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </el-card>

    <!-- 训练记录表格 -->
    <el-card shadow="hover">
      <el-table
        :data="trainingList"
        v-loading="loading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" :selectable="checkSelectable" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="training_type" label="训练类型" width="150" />
        <el-table-column label="分数" width="100">
          <template #default="{ row }">
            <span :style="{ color: getScoreColor(row.score) }">
              {{ row.score ? row.score.toFixed(1) : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="训练时长(秒)" width="100" />
        <el-table-column prop="created_at" label="开始时间" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" min-width="160">
          <template #default="{ row }">
            {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="120">
          <template #default="{ row }">
            <el-button
              type="success"
              size="small"
              @click="handleViewReport(row)"
            >
              查看报告
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
        @size-change="handlePageSizeChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getTrainings, deleteTraining } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Select, Delete } from '@element-plus/icons-vue'

const router = useRouter()

const trainingList = ref([])
const loading = ref(false)
const selectedTrainings = ref([])

const filterForm = reactive({
  user_id: '',
  training_type: '',
  status: '',
  dateRange: []
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})
const skipNextCurrentChange = ref(false)

// 获取训练记录列表
const fetchTrainings = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      user_id: filterForm.user_id || undefined,
      training_type: filterForm.training_type || undefined,
      status: filterForm.status || undefined
    }

    // 添加日期范围
    if (filterForm.dateRange && filterForm.dateRange.length === 2) {
      params.start_date = filterForm.dateRange[0]
      params.end_date = filterForm.dateRange[1]
    }

    const response = await getTrainings(params)

    trainingList.value = response.trainings
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('获取训练记录失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchTrainings()
}

// 重置
const handleReset = () => {
  filterForm.user_id = ''
  filterForm.training_type = ''
  filterForm.status = ''
  filterForm.dateRange = []
  pagination.page = 1
  fetchTrainings()
}

const handlePageChange = () => {
  if (skipNextCurrentChange.value) {
    skipNextCurrentChange.value = false
    return
  }

  fetchTrainings()
}

const handlePageSizeChange = () => {
  if (pagination.page !== 1) {
    skipNextCurrentChange.value = true
    pagination.page = 1
  }

  fetchTrainings()
}

const handleSelectionChange = (selection) => {
  selectedTrainings.value = selection
}

const clearSelection = () => {
  selectedTrainings.value = []
}

const checkSelectable = (row) => {
  return row.status === 'done'
}

// 查看报告
const handleViewReport = (training) => {
  router.push(`/admin/report/${training.id}`)
}

// 获取分数颜色
const getScoreColor = (score) => {
  if (!score) return '#909399'
  if (score >= 90) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

// 获取状态标签类型
const getStatusType = (status) => {
  const typeMap = {
    'done': 'success',
    'completed': 'success',
    'pending': 'info',
    'processing': 'warning',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取状态标签文本
const getStatusLabel = (status) => {
  const labelMap = {
    'done': '已完成',
    'completed': '已完成',
    'pending': '等待检测中',
    'processing': '检测中',
    'failed': '失败'
  }
  return labelMap[status] || status
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedTrainings.value.length === 0) return

  loading.value = true
  try {
    const results = await Promise.allSettled(
      selectedTrainings.value.map((t) => deleteTraining(t.id))
    )
    const successCount = results.filter((r) => r.status === 'fulfilled').length
    ElMessage.success(`成功删除 ${successCount} 条训练记录`)
    clearSelection()
    fetchTrainings()
  } catch (error) {
    ElMessage.error('批量删除失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTrainings()
})
</script>

<style scoped>
.training-management {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  margin: 0;
  color: var(--ft-color-text-primary);
}

.page-header {
  margin-bottom: 20px;
}

.page-subtitle {
  margin: 6px 0 0;
  color: var(--ft-color-text-tertiary);
  font-size: 14px;
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
</style>