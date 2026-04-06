<template>
  <div class="video-detection">
    <h2 class="page-title">📹 视频上传检测</h2>
    
    <!-- 上传区域 -->
    <el-card shadow="hover" class="upload-card">
      <el-upload
        class="upload-demo"
        drag
        :action="uploadUrl"
        :headers="uploadHeaders"
        :before-upload="beforeUpload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :show-file-list="false"
        accept=".mp4,.avi,.mov,.webm"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽视频文件到此处或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持格式：MP4, AVI, MOV, WebM | 最大文件大小：500MB
          </div>
        </template>
      </el-upload>
      
      <!-- 上传进度 -->
      <div v-if="uploading" class="upload-progress">
        <el-progress :percentage="uploadProgress" :status="uploadStatus" />
        <p>{{ uploadStatusText }}</p>
      </div>
    </el-card>
    
    <!-- 搜索和过滤 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 150px">
            <el-option label="等待中" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
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
    
    <!-- 任务列表 -->
    <el-card shadow="hover">
      <el-table
        :data="taskList"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="file_name" label="文件名" min-width="200" show-overflow-tooltip />
        <el-table-column label="文件大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="{ row }">
            {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleViewDetail(row)"
              :disabled="row.status !== 'completed'"
            >
              查看详情
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="handleReDetect(row)"
              :disabled="row.status === 'processing'"
            >
              重新检测
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(row)"
              :disabled="row.status === 'processing'"
            >
              删除
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
        @current-change="fetchTasks"
        @size-change="fetchTasks"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>
    
    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="检测结果详情"
      width="60%"
    >
      <div v-if="currentTask" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务 ID">{{ currentTask.id }}</el-descriptions-item>
          <el-descriptions-item label="文件名">{{ currentTask.file_name }}</el-descriptions-item>
          <el-descriptions-item label="文件大小">{{ formatFileSize(currentTask.file_size) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentTask.status)">
              {{ getStatusLabel(currentTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ formatDate(currentTask.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ currentTask.completed_at ? formatDate(currentTask.completed_at) : '-' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider />
        
        <h4>AI 检测结果</h4>
        <pre class="ai-result">{{ JSON.stringify(currentTask.ai_result, null, 2) }}</pre>
        
        <el-divider />
        
        <div v-if="currentTask.error_message">
          <h4 style="color: #f56c6c">错误信息</h4>
          <p>{{ currentTask.error_message }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Search } from '@element-plus/icons-vue'
import axios from 'axios'

const taskList = ref([])
const loading = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const uploadStatusText = ref('')
const detailDialogVisible = ref(false)
const currentTask = ref(null)

const filterForm = reactive({
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 上传配置
const uploadUrl = import.meta.env.VITE_API_BASE_URL + '/admin/videos/upload'
const uploadHeaders = {
  Authorization: `Bearer ${localStorage.getItem('token')}`
}

// 上传前验证
const beforeUpload = (file) => {
  const allowedTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/webm']
  const maxSize = 500 * 1024 * 1024 // 500MB
  
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('不支持的文件格式')
    return false
  }
  
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 500MB')
    return false
  }
  
  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''
  uploadStatusText.value = '正在上传...'
  
  return true
}

// 上传成功
const handleUploadSuccess = (response) => {
  uploading.value = false
  uploadProgress.value = 100
  uploadStatus.value = 'success'
  uploadStatusText.value = '上传成功，开始 AI 检测'
  
  ElMessage.success(response.message || '视频上传成功')
  
  // 刷新任务列表
  setTimeout(() => {
    fetchTasks()
    uploading.value = false
  }, 1000)
}

// 上传失败
const handleUploadError = (error) => {
  uploading.value = false
  uploadStatus.value = 'exception'
  uploadStatusText.value = '上传失败'
  
  ElMessage.error(error.message || '视频上传失败')
}

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/admin/videos/tasks`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        },
        params: {
          page: pagination.page,
          page_size: pagination.pageSize,
          status_filter: filterForm.status || undefined
        }
      }
    )
    
    taskList.value = response.data.tasks
    pagination.total = response.data.total
  } catch (error) {
    ElMessage.error('获取任务列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchTasks()
}

// 重置
const handleReset = () => {
  filterForm.status = ''
  pagination.page = 1
  fetchTasks()
}

// 查看详情
const handleViewDetail = (task) => {
  currentTask.value = task
  detailDialogVisible.value = true
}

// 重新检测
const handleReDetect = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要重新检测视频 "${task.file_name}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/admin/videos/tasks/${task.id}/re-detect`,
      {},
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      }
    )
    
    ElMessage.success(response.data.message || '重新检测已开始')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重新检测失败: ' + error.message)
    }
  }
}

// 删除任务
const handleDelete = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.file_name}" 吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(
      `${import.meta.env.VITE_API_BASE_URL}/admin/videos/tasks/${task.id}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      }
    )
    
    ElMessage.success('任务删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const mb = bytes / (1024 * 1024)
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(2)} GB`
  }
  return `${mb.toFixed(2)} MB`
}

// 获取状态标签类型
const getStatusType = (status) => {
  const typeMap = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取状态标签文本
const getStatusLabel = (status) => {
  const labelMap = {
    'pending': '等待中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return labelMap[status] || status
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.video-detection {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  margin-bottom: 20px;
  color: #303133;
}

.upload-card {
  margin-bottom: 20px;
}

.upload-demo {
  width: 100%;
}

.upload-progress {
  margin-top: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.upload-progress p {
  margin-top: 10px;
  text-align: center;
  color: #606266;
}

.filter-card {
  margin-bottom: 20px;
}

.detail-content {
  max-height: 60vh;
  overflow-y: auto;
}

.ai-result {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.6;
  max-height: 300px;
  overflow-y: auto;
}
</style>
