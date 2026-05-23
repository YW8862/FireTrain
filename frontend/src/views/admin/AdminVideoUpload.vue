<template>
  <div class="admin-video-upload">
    <div class="page-header">
      <div>
        <h2 class="page-title">管理员视频检测</h2>
        <p class="page-subtitle">上传训练视频、跟踪分析状态，并将结果归属到指定用户。</p>
      </div>
    </div>
    
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
          <el-select v-model="uploadForm.training_type" placeholder="选择训练类型" class="training-type-select">
            <el-option
              v-for="option in trainingTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
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
            {{ uploading ? '视频上传中...' : '开始上传并分析' }}
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
            <p><strong>状态：</strong>{{ getStatusLabel(uploadResult.status) }}</p>
          <p><strong>服务端保存耗时：</strong>{{ uploadResult.save_duration_ms }} ms</p>

            <!-- 细粒度阶段 & 进度条 -->
            <div v-if="uploadResult.status === 'processing'" class="analysis-progress">
              <div class="analysis-progress__header">
                <el-icon class="analysis-progress__spinner" :size="16"><Loading /></el-icon>
                <span class="analysis-progress__stage">{{ uploadResult.stage_label || '后台分析中' }}</span>
              </div>
              <el-progress
                :percentage="Math.round(uploadResult.progress || 0)"
                :stroke-width="10"
                :status="progressStatus(uploadResult)"
              />
              <p v-if="uploadResult.stage_message" class="analysis-progress__message">
                {{ uploadResult.stage_message }}
              </p>
              <p v-else class="analysis-progress__message analysis-progress__message--muted">
                {{ analysisPolling ? '页面会自动刷新，请稍候…' : '等待下一次状态刷新' }}
              </p>
              <ul class="analysis-progress__steps">
                <li
                  v-for="step in analysisSteps"
                  :key="step.code"
                  :class="stageStepClass(step.code, uploadResult)"
                >
                  <el-icon v-if="stageStepIcon(step.code, uploadResult) === 'done'" class="step-icon step-icon--done">
                    <CircleCheck />
                  </el-icon>
                  <el-icon v-else-if="stageStepIcon(step.code, uploadResult) === 'active'" class="step-icon step-icon--active">
                    <Loading />
                  </el-icon>
                  <span v-else class="step-icon step-icon--pending" />
                  <span>{{ step.label }}</span>
                </li>
              </ul>
            </div>

            <p v-if="uploadResult.status === 'done' && uploadResult.total_score !== null">
              <strong>总分：</strong>{{ uploadResult.total_score }}
            </p>
            <p v-if="uploadResult.feedback">
              <strong>{{ uploadResult.status === 'failed' ? '失败原因' : '反馈' }}：</strong>{{ uploadResult.feedback }}
            </p>
          <el-button 
            type="primary" 
            size="small" 
              :disabled="uploadResult.status !== 'done'"
            @click="viewReport(uploadResult.training_id)"
          >
              {{ uploadResult.status === 'done' ? '查看报告' : '分析中...' }}
          </el-button>
            <el-button
              v-if="uploadResult.status === 'processing'"
              size="small"
              @click="refreshStatus(uploadResult.training_id)"
            >
              立即刷新状态
            </el-button>
        </div>
      </el-alert>
    </el-card>
    
    <!-- 使用说明 -->
    <el-card shadow="hover" class="help-card">
      <template #header>
        <div class="card-header">
          <span>使用说明</span>
        </div>
      </template>
      <div class="help-content">
        <!-- <h4>功能说明</h4>
        <ul>
          <li>管理员可以上传视频并为指定用户进行检测</li>
          <li>系统会自动进行视频分析，生成完整的训练报告</li>
          <li>检测结果和评分会保存到目标用户的训练历史中</li>
          <li>用户可以像正常训练一样查看报告和改进建议</li>
        </ul> -->
<!--         
        <h4>使用流程</h4>
        <ol>
          <li>输入目标用户的用户名</li>
          <li>选择训练类型（默认为灭火器训练）</li>
          <li>上传视频文件</li>
          <li>点击"开始上传并分析"</li>
          <li>等待视频分析完成（通常需要 30-60 秒）</li>
          <li>点击查看报告按钮查看完整报告</li>
        </ol> -->
        
        <h4>注意事项</h4>
        <ul>
          <li>确保用户名存在，否则会上传失败</li>
          <li>视频文件不要超过 500MB</li>
          <!-- <li>视频分析需要一定时间，请耐心等待</li>
          <li>如果视频中未检测到有效动作，将返回 0 分</li> -->
        </ul>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Loading, CircleCheck } from '@element-plus/icons-vue'
import { DEFAULT_UPLOAD_TIMEOUT, uploadRequest } from '@/api/upload'
import { getAdminVideoStatus } from '@/api/admin'
import { TRAINING_TYPE_OPTIONS } from '@/utils/trainingType'

// 分析流水线阶段定义（和后端 analysis_progress.py STAGE_LABELS 对齐）
const analysisSteps = [
  { code: 'loading_model', label: '加载 AI 模型' },
  { code: 'video_analysis', label: '视频帧分析' },
  { code: 'rule_scoring', label: '规则评分计算' },
  { code: 'llm_scoring', label: '大模型点评' },
  { code: 'saving', label: '结果保存' }
]
const stageOrder = ['queued', ...analysisSteps.map((s) => s.code), 'done']

const stageIndex = (stage) => {
  const idx = stageOrder.indexOf(stage)
  return idx === -1 ? 0 : idx
}

const stageStepClass = (code, result) => {
  if (!result) return 'step'
  if (result.status === 'failed') {
    return stageIndex(code) <= stageIndex(result.stage) ? 'step step--failed' : 'step'
  }
  if (stageIndex(code) < stageIndex(result.stage)) return 'step step--done'
  if (code === result.stage) return 'step step--active'
  return 'step'
}

const stageStepIcon = (code, result) => {
  if (!result) return 'pending'
  if (result.status === 'failed') return 'pending'
  if (stageIndex(code) < stageIndex(result.stage)) return 'done'
  if (code === result.stage) return 'active'
  return 'pending'
}

const progressStatus = (result) => {
  if (!result) return ''
  if (result.status === 'failed') return 'exception'
  if (result.status === 'done') return 'success'
  return ''
}

const router = useRouter()

// 上传表单
const uploadForm = reactive({
  username: '',
  training_type: 'fire_extinguisher'
})

const trainingTypeOptions = TRAINING_TYPE_OPTIONS

// 文件相关
const selectedFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const uploadStatusText = ref('')
const uploadResult = ref(null)
const analysisPolling = ref(false)

// 取消令牌
let abortController = null
let uploadStartedAt = 0
let pollingTimer = null
const POLL_INTERVAL_MS = 3000

const getStatusLabel = (status) => {
  const labels = {
    processing: '分析中',
    done: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

const stopStatusPolling = () => {
  if (pollingTimer) {
    clearTimeout(pollingTimer)
    pollingTimer = null
  }
  analysisPolling.value = false
}

const scheduleNextPoll = (trainingId) => {
  pollingTimer = window.setTimeout(() => {
    pollTrainingStatus(trainingId, { silent: true })
  }, POLL_INTERVAL_MS)
}

const pollTrainingStatus = async (trainingId, { silent = false } = {}) => {
  const previousStatus = uploadResult.value?.status

  try {
    const statusResult = await getAdminVideoStatus(trainingId)

    if (!uploadResult.value || uploadResult.value.training_id !== trainingId) {
      return
    }

    uploadResult.value = {
      ...uploadResult.value,
      status: statusResult.status,
      total_score: statusResult.total_score,
      feedback: statusResult.feedback,
      stage: statusResult.stage,
      stage_label: statusResult.stage_label,
      progress: statusResult.progress,
      stage_message: statusResult.stage_message
    }

    if (statusResult.status === 'done') {
      stopStatusPolling()
      if (previousStatus !== 'done') {
        ElMessage.success('视频分析已完成，现在可以查看报告')
      }
      return
    }

    if (statusResult.status === 'failed') {
      stopStatusPolling()
      if (previousStatus !== 'failed') {
        ElMessage.error(statusResult.feedback || '视频分析失败，请检查后端日志')
      }
      return
    }

    analysisPolling.value = true
    scheduleNextPoll(trainingId)
  } catch (error) {
    analysisPolling.value = true
    scheduleNextPoll(trainingId)
    if (!silent) {
      ElMessage.warning(error.customMessage || error.response?.data?.detail || '状态刷新失败，稍后会自动重试')
    }
  }
}

const refreshStatus = async (trainingId) => {
  stopStatusPolling()
  await pollTrainingStatus(trainingId)
}

const formatUploadSpeed = (bytesPerSecond) => {
  if (!bytesPerSecond || bytesPerSecond <= 0) return ''
  if (bytesPerSecond >= 1024 * 1024) {
    return `${(bytesPerSecond / (1024 * 1024)).toFixed(1)} MB/s`
  }
  if (bytesPerSecond >= 1024) {
    return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`
  }
  return `${Math.round(bytesPerSecond)} B/s`
}

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
  stopStatusPolling()
  
  // 创建取消控制器
  abortController = new AbortController()
  uploadStartedAt = Date.now()
  
  try {
    // 创建 FormData
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('username', uploadForm.username)
    formData.append('training_type', uploadForm.training_type)
    
    uploadStatusText.value = '正在上传视频...'
    uploadProgress.value = 0
    
    // 调用 API（使用原生 axios 以支持进度监控）
    const response = await uploadRequest({
      url: '/admin/video/upload',
      method: 'post',
      data: formData,
      timeout: DEFAULT_UPLOAD_TIMEOUT,
      signal: abortController.signal,
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          const elapsedSeconds = Math.max((Date.now() - uploadStartedAt) / 1000, 0.1)
          const speed = formatUploadSpeed(progressEvent.loaded / elapsedSeconds)
          uploadProgress.value = percentCompleted
          uploadStatusText.value = speed
            ? `正在上传视频... ${percentCompleted}% (${speed})`
            : `正在上传视频... ${percentCompleted}%`
        }
      }
    })
    
    uploadProgress.value = 100
    uploadStatus.value = 'success'
    uploadStatusText.value = '上传完成，后台正在进行视频分析...'
    
    uploadResult.value = {
      success: true,
      message: response.message,
      training_id: response.training_id,
      username: response.username,
      file_name: response.file_name,
      status: response.status,
      save_duration_ms: response.save_duration_ms,
      total_score: null,
      feedback: '',
      stage: 'queued',
      stage_label: '任务已提交，等待分析',
      progress: 0,
      stage_message: null
    }
    
    ElMessage.success('视频上传成功，结果分析已开始')
    await pollTrainingStatus(response.training_id, { silent: true })
    
    // 清空表单
    resetForm()
    
  } catch (error) {
    // 如果是取消操作，不显示错误
    if (error.code === 'ERR_CANCELED') {
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
    abortController = null
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
    if (abortController) {
      abortController.abort()
    }
    
    uploadStatusText.value = '正在取消...'
    
    // 如果已经有 training_id，通知后端删除
    if (uploadResult.value?.training_id) {
      try {
        await uploadRequest({
          url: `/admin/video/upload/${uploadResult.value.training_id}`,
          method: 'delete'
        })
        console.log('已通知后端删除训练记录')
      } catch (deleteError) {
        console.error('删除训练记录失败:', deleteError)
      }
    }
    
    // 重置状态
    stopStatusPolling()
    uploading.value = false
    uploadStatus.value = 'warning'
    uploadStatusText.value = '上传已取消'
    abortController = null
    
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
  uploadForm.training_type = 'fire_extinguisher'
  selectedFile.value = null
  uploadProgress.value = 0
  uploadStatus.value = ''
  uploadStatusText.value = ''
}

// 查看报告
const viewReport = (trainingId) => {
  if (uploadResult.value?.status !== 'done') {
    ElMessage.warning('视频分析尚未完成，请等待状态变为“已完成”后再查看报告')
    return
  }
  router.push(`/admin/report/${trainingId}`)
}

onUnmounted(() => {
  stopStatusPolling()
})
</script>

<style scoped>
.admin-video-upload {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
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

.training-type-select {
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

.analysis-progress {
  margin: 14px 0 10px;
  padding: 14px 16px;
  background: linear-gradient(180deg, #f0f7ff 0%, #f8fbff 100%);
  border: 1px solid #d6e8ff;
  border-radius: 8px;
}

.analysis-progress__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-weight: 600;
  color: #1d4ed8;
  font-size: 14px;
}

.analysis-progress__spinner {
  animation: ft-spin 1.2s linear infinite;
}

@keyframes ft-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.analysis-progress__message {
  margin: 8px 0 0;
  font-size: 13px;
  color: #475569;
}

.analysis-progress__message--muted {
  color: #94a3b8;
  font-style: italic;
}

.analysis-progress__steps {
  list-style: none;
  padding: 0;
  margin: 12px 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
}

.analysis-progress__steps .step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
  padding: 2px 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7);
  transition: color 0.2s, background 0.2s;
}

.analysis-progress__steps .step--done {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.08);
}

.analysis-progress__steps .step--active {
  color: #1d4ed8;
  background: rgba(29, 78, 216, 0.1);
  font-weight: 600;
}

.analysis-progress__steps .step--failed {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.08);
}

.step-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 50%;
}

.step-icon--pending {
  border: 1.5px dashed #cbd5e1;
  background: transparent;
}

.step-icon--done {
  color: #16a34a;
}

.step-icon--active {
  color: #1d4ed8;
  animation: ft-spin 1.2s linear infinite;
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
