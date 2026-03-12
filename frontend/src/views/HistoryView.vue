<template>
  <div class="history-container">
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <h1>📜 训练历史</h1>
          <el-button type="primary" @click="goToTraining">开始新训练</el-button>
        </div>
      </template>

      <div v-loading="loading">
        <!-- 搜索筛选 -->
        <el-form :inline="true" :model="queryForm" class="search-form">
          <el-form-item label="状态">
            <el-select v-model="queryForm.status" placeholder="全部状态" clearable>
              <el-option label="已完成" value="done" />
              <el-option label="进行中" value="processing" />
              <el-option label="未开始" value="created" />
            </el-select>
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="loadHistory">查询</el-button>
          </el-form-item>
        </el-form>

        <!-- 历史记录列表 -->
        <el-table :data="historyList" style="width: 100%" @row-click="goToDetail">
          <el-table-column prop="training_type" label="训练类型" width="120">
            <template #default="{ row }">
              {{ getTrainingTypeName(row.training_type) }}
            </template>
          </el-table-column>
          
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="total_score" label="总分" width="100" sortable>
            <template #default="{ row }">
              <span v-if="row.status === 'done'">{{ row.total_score }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="duration_seconds" label="时长 (秒)" width="100" sortable>
            <template #default="{ row }">
              {{ row.duration_seconds || '-' }}
            </template>
          </el-table-column>
          
          <el-table-column prop="started_at" label="开始时间" width="180" sortable>
            <template #default="{ row }">
              {{ formatDate(row.started_at) }}
            </template>
          </el-table-column>
          
          <el-table-column prop="completed_at" label="完成时间" width="180" sortable>
            <template #default="{ row }">
              {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" fixed="right" width="120">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'done'"
                type="primary"
                size="small"
                @click.stop="goToDetail(row.id)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

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
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTrainingHistory } from '@/api/training'

const router = useRouter()

const loading = ref(false)

// 查询表单
const queryForm = reactive({
  status: ''
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
const getTrainingTypeName = (type) => {
  const names = {
    fire_extinguisher: '灭火器操作',
    other: '其他训练'
  }
  return names[type] || type
}

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
    
    if (queryForm.status) {
      params.status = queryForm.status
    }
    
    const res = await getTrainingHistory(params)
    
    historyList.value = res.records || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载历史记录失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载历史记录失败')
  } finally {
    loading.value = false
  }
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
.history-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.history-card {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
