<template>
  <div class="app-page history-page">
    <NavBar />

    <div class="app-shell">
      <el-card class="history-card section-card">
        <template #header>
          <div class="card-header">
            <div>
              <h1 class="page-title">训练记录查询</h1>
              <p class="page-subtitle">查看历次训练时间、状态、得分结果和对应报告。</p>
            </div>
            <el-button type="primary" @click="goToTraining">开始新训练</el-button>
          </div>
        </template>

        <div v-loading="loading">
        <!-- 搜索筛选 -->
          <div class="search-panel soft-panel">
            <el-form :inline="true" :model="queryForm" class="search-form">
              <el-form-item label="训练状态">
                <el-select
                  v-model="queryForm.status"
                  placeholder="全部状态"
                  clearable
                  class="status-select"
                >
                  <el-option
                    v-for="option in statusOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="handleSearch">查询记录</el-button>
                <el-button @click="handleReset">重置</el-button>
              </el-form-item>
            </el-form>
          </div>

        <!-- 历史记录列表 -->
          <div class="table-panel">
            <el-table
              :data="historyList"
              style="width: 100%"
              @row-click="goToDetail"
              empty-text="暂无训练记录"
              class="history-table"
            >
              <el-table-column prop="training_type" label="训练类型" min-width="140">
                <template #default="{ row }">
                  {{ getTrainingTypeName(row.training_type) }}
                </template>
              </el-table-column>

              <el-table-column prop="status" label="状态" min-width="120">
                <template #default="{ row }">
                  <el-tag :type="getStatusTagType(row.status)">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column prop="total_score" label="总分" min-width="100" sortable>
                <template #default="{ row }">
                  <span v-if="row.status === 'done'">{{ row.total_score }}</span>
                  <span v-else>-</span>
                </template>
              </el-table-column>

              <el-table-column prop="duration_seconds" label="时长 (秒)" min-width="110" sortable>
                <template #default="{ row }">
                  {{ row.duration_seconds || '-' }}
                </template>
              </el-table-column>

              <el-table-column prop="started_at" label="开始时间" min-width="180" sortable>
                <template #default="{ row }">
                  {{ formatDate(row.started_at) }}
                </template>
              </el-table-column>

              <el-table-column prop="completed_at" label="完成时间" min-width="180" sortable>
                <template #default="{ row }">
                  {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
                </template>
              </el-table-column>

              <el-table-column label="操作" min-width="140" align="right">
                <template #default="{ row }">
                  <el-button
                    v-if="row.status === 'done'"
                    type="primary"
                    size="small"
                    @click.stop="goToDetail(row.id)"
                  >
                    查看报告
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

        <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.page_size"
              :total="pagination.total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadHistory"
              @current-change="loadHistory"
            />
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTrainingHistory } from '@/api/training'
import NavBar from '@/components/NavBar.vue'
import { getTrainingTypeLabel } from '@/utils/trainingType'

const router = useRouter()

const loading = ref(false)
const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '已完成', value: 'done' },
  { label: '进行中', value: 'processing' },
  { label: '未开始', value: 'created' }
]

// 查询表单
const queryForm = reactive({
  status: '' // 默认不筛选，可以显示所有状态的记录
})

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 历史记录列表
const historyList = ref([])

// 获取训练类型名称
const getTrainingTypeName = (type) => getTrainingTypeLabel(type)

// 获取状态标签类型
const getStatusTagType = (status) => {
  const types = {
    created: 'info',
    processing: 'warning',
    done: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    created: '未开始',
    processing: '进行中',
    done: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载历史记录
const loadHistory = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    // 只在用户选择了状态时才传递 status 参数
    if (queryForm.status) {
      params.status = queryForm.status
    }
    
    const res = await getTrainingHistory(params)
    
    historyList.value = res.records || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载历史记录失败:', error)
    ElMessage.error(error.customMessage || error.response?.data?.detail || '加载历史记录失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadHistory()
}

const handleReset = () => {
  queryForm.status = ''
  pagination.page = 1
  loadHistory()
}

// 跳转到训练页面
const goToTraining = () => {
  router.push('/training')
}

// 跳转到详情报告
const goToDetail = (trainingId) => {
  router.push(`/report/${trainingId}`)
}

// 组件挂载时加载数据
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.history-page {
  padding-bottom: 24px;
}

.history-card {
  flex: 1;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 24px;
}

.page-subtitle {
  margin: 6px 0 0;
  color: var(--ft-color-text-tertiary);
  font-size: 14px;
}

.search-panel {
  margin-bottom: 20px;
  padding: 16px;
}

.search-form {
  margin-bottom: 0;
}

.status-select {
  width: 220px;
}

.table-panel {
  width: 100%;
  min-height: 420px;
}

.history-table {
  width: 100%;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .status-select {
    width: 100%;
  }
}
</style>
