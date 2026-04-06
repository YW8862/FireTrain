<template>
  <div class="admin-video-upload">
    <h2 class="page-title">📹 管理员视频检测</h2>
    
    <!-- 上传表单 -->
    <el-card shadow="hover" class="upload-card">
      <el-form :model="uploadForm" label-width="120px" class="upload-form">
        <el-form-item label="目标用户" required>
          <el-input 
            v-model="uploadForm.username" 
            placeholder="请输入用户名（视频结果将保存给该用户）"
            clearable
          />
          <div class="form-tip">提示：视频的检测报告和评分将归属到该用户账户</div>
        </el-form-item>
        
        <el-form-item label="训练类型">
          <el-select v-model="uploadForm.training_type" placeholder="选择训练类型">
            <el-option label="灭火器训练" value="extinguisher" />
            <el-option label="其他训练" value="other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="视频文件" required>
          <el-upload
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            :disabled="uploading"
            accept=".mp4,.avi,.mov,.webm"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽视频文件到此处或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持格式：MP4, AVI, MOV, WebM | 最大文件大小：500MB
                <span v-if="uploading" style="color: #f56c6c; margin-left: 10px;">⚠️ 上传中，无法选择新文件</span>
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="uploading" 
            @click="handleUpload"
            :disabled="!uploadForm.username || !selectedFile"
          >
            {{ uploading ? '上传并分析中...' : '开始上传并检测' }}
          </el-button>
          <el-button 
            v-if="uploading" 
            type="danger" 
            @click="handleCancel"
          >
            取消上传
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
      
      <!-- 上传进度 -->
      <div v-if="uploading" class="upload-progress">
        <el-progress :percentage="uploadProgress" :status="uploadStatus" />
        <p>{{ uploadStatusText }}</p>
      </div>
      
      <!-- 上传结果 -->
      <el-alert
        v-if="uploadResult"
        :title="uploadResult.message"
        :type="uploadResult.success ? 'success' : 'error'"
        show-icon
        closable
        class="upload-result"
      >
        <div v-if="uploadResult.success" class="result-details">
          <p><strong>训练ID：</strong>{{ uploadResult.training_id }}</p>
          <p><strong>目标用户：</strong>{{ uploadResult.username }}</p>
          <p><strong>文件名：</strong>{{ uploadResult.file_name }}</p>
          <p><strong>状态：</strong>{{ uploadResult.status }}</p>
          <el-button 
            type="primary" 
            size="small" 
            @click="viewReport(uploadResult.training_id)"
          >
            查看报告
          </el-button>
        </div>
      </el-alert>
    </el-card>
    
    <!-- 使用说明 -->
    <el-card shadow="hover" class="help-card">
      <template #header>
        <div class="card-header">
          <span>💡 使用说明</span>
        </div>
      </template>
      <div class="help-content">
        <h4>功能说明</h4>
        <ul>
          <li>管理员可以上传视频并为指定用户进行检测</li>
          <li>系统会自动进行 AI 分析，生成完整的训练报告</li>
          <li>检测结果和评分会保存到目标用户的训练历史中</li>
          <li>用户可以像正常训练一样查看报告和改进建议</li>
        </ul>
        
        <h4>使用流程</h4>
        <ol>
          <li>输入目标用户的用户名</li>
          <li>选择训练类型（默认为灭火器训练）</li>
          <li>上传视频文件</li>
          <li>点击"开始上传并检测"</li>
          <li>等待 AI 分析完成（通常需要 30-60 秒）</li>
          <li>点击查看报告按钮查看完整报告</li>
        </ol>
        
        <h4>注意事项</h4>
        <ul>
          <li>确保用户名存在，否则会上传失败</li>
          <li>视频文件不要超过 500MB</li>
          <li>AI 分析需要一定时间，请耐心等待</li>
          <li>如果视频中未检测到有效动作，将返回 0 分</li>
        </ul>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()

// 上传表单
const uploadForm = reactive({
  username: '',
  training_type: 'extinguisher'
})

// 文件相关
const selectedFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const uploadStatusText = ref('')
const uploadResult = ref(null)

// 取消令牌
let cancelSource = null

// 处理文件选择
const handleFileChange = (file) => {
  // 如果正在上传，阻止选择新文件
  if (uploading.value) {
    ElMessage.warning('当前正在上传文件，请先取消或等待上传完成')
    return false
  }
  
  selectedFile.value = file.raw
  
  // 验证文件大小（500MB）
  const maxSize = 500 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 500MB')
    selectedFile.value = null
    return false
  }
  
  // 验证文件类型
  const allowedTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/webm']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.warning('建议上传 MP4、AVI、MOV 或 WebM 格式的视频')
  }
}

// 上传视频
const handleUpload = async () => {
  if (!uploadForm.username) {
    ElMessage.error('请输入目标用户名')
    return
  }
  
  if (!selectedFile.value) {
    ElMessage.error('请选择视频文件')
    return
  }
  
  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''
  uploadStatusText.value = '准备上传...'
  uploadResult.value = null
  
  // 创建取消令牌
  cancelSource = axios.CancelToken.source()
  
  try {
    // 创建 FormData
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('username', uploadForm.username)
    formData.append('training_type', uploadForm.training_type)
    
    uploadStatusText.value = '正在上传视频...'
    uploadProgress.value = 0
    
    // 调用 API（使用原生 axios 以支持进度监控）
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/admin/video/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        timeout: 300000,  // 5分钟超时
        cancelToken: cancelSource.token,
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            uploadProgress.value = percentCompleted
            uploadStatusText.value = `正在上传视频... ${percentCompleted}%`
          }
        }
      }
    )
    
    uploadProgress.value = 100
    uploadStatus.value = 'success'
    uploadStatusText.value = '上传成功！AI 正在分析中...'
    
    uploadResult.value = {
      success: true,
      message: response.data.message,
      training_id: response.data.training_id,
      username: response.data.username,
      file_name: response.data.file_name,
      status: response.data.status
    }
    
    ElMessage.success('视频上传成功，AI 正在分析中...')
    
    // 清空表单
    resetForm()
    
  } catch (error) {
    // 如果是取消操作，不显示错误
    if (axios.isCancel(error)) {
      console.log('上传已取消')
      uploadStatusText.value = '上传已取消'
      uploadStatus.value = 'warning'
      ElMessage.info('上传已取消')
    } else {
      console.error('上传失败:', error)
      uploadProgress.value = 100
      uploadStatus.value = 'exception'
      uploadStatusText.value = '上传失败'
      
      uploadResult.value = {
        success: false,
        message: error.response?.data?.detail || error.message || '上传失败，请重试'
      }
      
      ElMessage.error(uploadResult.value.message)
    }
  } finally {
    uploading.value = false
    cancelSource = null
  }
}

// 取消上传
const handleCancel = async () => {
  if (!uploading.value) {
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要取消上传吗？已上传的内容将被删除。',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '继续上传',
        type: 'warning'
      }
    )
    
    // 取消上传
    if (cancelSource) {
      cancelSource.cancel('用户取消上传')
    }
    
    uploadStatusText.value = '正在取消...'
    
    // 如果已经有 training_id，通知后端删除
    if (uploadResult.value?.training_id) {
      try {
        await axios.delete(
          `${import.meta.env.VITE_API_BASE_URL}/admin/video/upload/${uploadResult.value.training_id}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )
        console.log('已通知后端删除训练记录')
      } catch (deleteError) {
        console.error('删除训练记录失败:', deleteError)
      }
    }
    
    // 重置状态
    uploading.value = false
    uploadStatus.value = 'warning'
    uploadStatusText.value = '上传已取消'
    cancelSource = null
    
    ElMessage.success('已取消上传')
    
  } catch (error) {
    // 用户选择继续上传
    if (error === 'cancel') {
      console.log('用户选择继续上传')
    }
  }
}

// 重置表单
const resetForm = () => {
  uploadForm.username = ''
  uploadForm.training_type = 'extinguisher'
  selectedFile.value = null
  uploadProgress.value = 0
  uploadStatus.value = ''
  uploadStatusText.value = ''
}

// 查看报告
const viewReport = (trainingId) => {
  router.push(`/report/${trainingId}`)
}
</script>

<style scoped>
.admin-video-upload {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #303133;
}

.upload-card {
  margin-bottom: 20px;
}

.upload-form {
  margin-top: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.upload-demo {
  width: 100%;
}

.upload-progress {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.upload-progress p {
  margin: 10px 0 0 0;
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.upload-result {
  margin-top: 20px;
}

.result-details {
  margin-top: 10px;
  padding: 10px;
  background-color: #fff;
  border-radius: 4px;
}

.result-details p {
  margin: 5px 0;
  font-size: 14px;
  color: #606266;
}

.help-card {
  margin-top: 20px;
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}

.help-content {
  line-height: 1.8;
}

.help-content h4 {
  margin: 15px 0 10px 0;
  color: #303133;
  font-size: 15px;
}

.help-content ul,
.help-content ol {
  margin: 10px 0;
  padding-left: 20px;
}

.help-content li {
  margin: 5px 0;
  color: #606266;
  font-size: 14px;
}
</style>
