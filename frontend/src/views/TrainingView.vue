<template>
  <div class="app-page training-page">
    <NavBar :visible="!currentTraining" />

    <div class="app-shell">
      <div class="training-page-header">
        <div>
          <div class="training-title-meta">
            <img :src="flameSymbol" alt="" class="title-meta-icon" />
            <p class="training-eyebrow">用户训练页</p>
          </div>
          <h1 class="training-page-title">
            {{ currentTraining ? `${selectedTrainingTypeLabel} · ${currentStepTitle}` : `${selectedTrainingTypeLabel}训练准备` }}
          </h1>
          <p class="training-page-subtitle">
            训练过程中请保持人员完整入镜，按规范步骤完成操作，系统将生成本次实操测评结果。
          </p>
        </div>
        <el-tag class="status-pill" :type="getStatusType(currentTraining?.status || 'created')" size="large">
          {{ currentTraining ? getStatusText(currentTraining.status) : '未开始' }}
        </el-tag>
      </div>

      <div class="safety-banner training-banner">
        <el-icon><WarningFilled /></el-icon>
        <div>
          <strong>训练中请注意</strong>
          <div>{{ trainingTypeConfig.bannerMessage }}</div>
        </div>
      </div>

      <el-card class="training-card section-card">
      <!-- 未开始训练 -->
      <div v-if="!currentTraining">
        <div class="prep-layout">
          <div class="prep-main">
            <div class="training-header">
              <h2>训练准备</h2>
              <el-tag :type="getStatusType('created')" size="large">
                {{ getStatusText('created') }}
              </el-tag>
            </div>

            <el-alert
              title="训练说明"
              type="info"
              :closable="false"
              show-icon
              class="mb-4"
            >
              <p>请按照标准流程完成{{ selectedTrainingTypeLabel }}：</p>
              <ol>
                <li v-for="(step, index) in trainingTypeConfig.instructions" :key="index">{{ step }}</li>
              </ol>
            </el-alert>

            <el-form :model="trainingForm" class="training-form">
              <div class="training-type-field">
                <span class="prep-info-label">训练类型</span>
                <el-select
                  v-model="trainingForm.training_type"
                  placeholder="请选择训练类型"
                  class="training-type-select"
                >
                  <el-option
                    v-for="option in trainingTypeOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
              </div>

              <div class="prep-info-strip">
                <div class="prep-info-item">
                  <span class="prep-info-label">训练项目</span>
                  <strong>{{ selectedTrainingTypeLabel }}</strong>
                </div>
                <div class="prep-info-item">
                  <span class="prep-info-label">步骤数量</span>
                  <strong>{{ trainingTypeConfig.stepCount }} 个标准步骤</strong>
                </div>
                <div class="prep-info-item">
                  <span class="prep-info-label">系统设置</span>
                  <strong>自动记录训练过程</strong>
                </div>
              </div>

              <div class="form-actions">
                <el-button 
                  type="primary" 
                  @click="handleStartTraining" 
                  :loading="starting" 
                  size="large"
                  class="start-training-btn"
                >
                  <el-icon><VideoPlay /></el-icon>
                  开始训练
                </el-button>
              </div>
            </el-form>
          </div>

          <div class="prep-side">
            <div class="prep-side-card">
              <img :src="fireExtinguisherSymbol" alt="" class="prep-illustration" />
              <div class="prep-side-title">操作步骤速览</div>
              <div class="prep-step-list">
                <div v-for="(step, index) in steps" :key="step.name" class="prep-step-item">
                  <span class="prep-step-index">{{ index + 1 }}</span>
                  <span>{{ step.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 训练中 -->
      <div v-else class="training-content">
        <div class="training-runtime-head">
          <div class="runtime-stat">
            <span class="runtime-label">当前状态</span>
            <strong>{{ getStatusText(currentTraining.status) }}</strong>
          </div>
          <div class="runtime-stat">
            <span class="runtime-label">训练类型</span>
            <strong>{{ selectedTrainingTypeLabel }}</strong>
          </div>
          <div class="runtime-stat">
            <span class="runtime-label">训练目标</span>
            <strong>动作完整、姿态规范、流程正确</strong>
          </div>
        </div>

        <el-row :gutter="20">
          <!-- 左侧：视频预览区 -->
          <el-col :lg="15" :md="24">
            <el-card class="video-card">
              <template #header>
                <div class="card-header">
                  <span>训练视频画面</span>
                  <el-tag :type="getStatusType(currentTraining.status)">
                    {{ getStatusText(currentTraining.status) }}
                  </el-tag>
                </div>
              </template>
              
              <div class="video-container">
                <video ref="videoRef" autoplay playsinline class="video-element"></video>
                
                <!-- 未开启摄像头遮罩 -->
                <div v-if="!cameraStarted" class="video-overlay">
                  <el-button type="primary" @click="startCamera" size="large">
                    <el-icon><VideoCamera /></el-icon>
                    开启摄像头
                  </el-button>
                </div>
                
                <!-- 暂停状态遮罩 -->
                <div v-if="isPaused" class="video-overlay paused-overlay">
                  <div class="paused-content">
                    <el-icon :size="80" color="#F59E0B"><VideoPause /></el-icon>
                    <h3>训练已暂停</h3>
                    <p>点击"继续"按钮恢复训练</p>
                  </div>
                </div>
              </div>
              
              <div class="video-controls">
                <el-button 
                  type="primary" 
                  @click="handleCompleteTraining" 
                  :loading="completing" 
                  :disabled="!currentTraining || currentTraining?.status === 'done' || isPaused"
                  size="large"
                >
                  完成训练
                </el-button>
                <el-button 
                  type="warning" 
                  @click="handlePause" 
                  :disabled="!currentTraining || currentTraining?.status === 'done'"
                  size="large"
                >
                  {{ isPaused ? '继续' : '暂停' }}
                </el-button>
                <el-button 
                  type="danger" 
                  @click="handleCancel" 
                  :disabled="!currentTraining || currentTraining?.status === 'done'"
                  size="large"
                >
                  取消训练
                </el-button>
                <el-button 
                  v-if="currentTraining?.status === 'done'" 
                  type="primary" 
                  @click="resetTraining"
                  size="large"
                >
                  新的训练
                </el-button>
              </div>

              <div v-if="uploadState.visible" class="upload-status-box">
                <el-progress
                  :percentage="uploadState.percentage"
                  :status="uploadState.status"
                  :indeterminate="uploadState.indeterminate"
                  :duration="2"
                />
                <p>{{ uploadState.text }}</p>
              </div>

              <div class="camera-tip">
                <span>建议拍摄角度：</span>
                <span>人物完整入镜、画面稳定、关键动作无遮挡。</span>
              </div>
            </el-card>
          </el-col>

          <!-- 右侧：训练步骤 -->
          <el-col :lg="9" :md="24">
            <el-card class="steps-card">
              <template #header>
                <span>操作指引</span>
              </template>
              
              <div class="steps-list">
                <div v-for="(step, index) in steps" :key="index" class="step-item">
                  <div class="step-header">
                    <span class="step-number">{{ index + 1 }}</span>
                    <span class="step-name">{{ step.name }}</span>
                    <el-icon :class="['step-status', getStepStatusClass(step.status)]">
                      <component :is="getStepIcon(step.status)" />
                    </el-icon>
                  </div>
                  <el-progress 
                    :percentage="getStepProgress(step.status)" 
                    :color="getStepColor(step.status)"
                    :show-text="false"
                    :stroke-width="3"
                  />
                </div>
              </div>
              
              <div v-if="realtimeFeedback" class="feedback-box">
                <el-alert :title="realtimeFeedback" type="info" :closable="false" show-icon />
              </div>

              <div class="step-legend">
                <span><i class="legend-dot pending"></i>未开始</span>
                <span><i class="legend-dot doing"></i>进行中</span>
                <span><i class="legend-dot done"></i>已完成</span>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoCamera, VideoPlay, VideoPause, WarningFilled } from '@element-plus/icons-vue'
import { startTraining, completeTraining, preCheckTraining, uploadVideoFile, deleteTrainingRecord } from '@/api/training'
import NavBar from '@/components/NavBar.vue'
import fireExtinguisherSymbol from '@/assets/illustrations/fire-extinguisher-symbol.svg'
import flameSymbol from '@/assets/illustrations/flame-symbol.svg'
import { TRAINING_TYPE_OPTIONS, getTrainingTypeLabel, getTrainingTypeConfig } from '@/utils/trainingType'

const router = useRouter()

// 状态
const starting = ref(false)
const completing = ref(false)
const cameraStarted = ref(false)
const countdown = ref(0)
const videoRef = ref(null)
let stream = null
let mediaRecorder = null  // 视频录制器
let recordedChunks = []    // 录制的视频片段
let countdownTimer = null
const realtimeFeedback = ref('')
const isPaused = ref(false) // 暂停状态
const recordedVideoBlob = ref(null)
const uploadState = reactive({
  visible: false,
  percentage: 0,
  status: '',
  text: '',
  indeterminate: false
})
let uploadAbortController = null

// 训练表单
const trainingForm = reactive({
  training_type: 'fire_extinguisher',
  duration_seconds: 120
})

// 当前训练
const currentTraining = ref(null)

const currentStepTitle = computed(() => {
  const currentStep = steps.find((step) => step.status === 'doing')
  if (currentStep) return currentStep.name
  const finishedCount = steps.filter((step) => step.status === 'done').length
  return finishedCount ? `步骤 ${finishedCount + 1}` : '训练准备'
})

const trainingTypeOptions = TRAINING_TYPE_OPTIONS
const selectedTrainingTypeLabel = computed(() =>
  getTrainingTypeLabel(currentTraining.value?.training_type || trainingForm.training_type)
)
const trainingTypeConfig = computed(() => getTrainingTypeConfig(trainingForm.training_type))

// 步骤状态 - 根据选择的训练类型动态生成
const steps = computed(() => {
  const config = getTrainingTypeConfig(trainingForm.training_type)
  return config.steps.map(s => ({ name: s.name, status: 'pending' }))
})

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

const updateUploadState = ({
  visible = true,
  percentage = uploadState.percentage,
  status = uploadState.status,
  text = uploadState.text,
  indeterminate = uploadState.indeterminate
}) => {
  uploadState.visible = visible
  uploadState.percentage = percentage
  uploadState.status = status
  uploadState.text = text
  uploadState.indeterminate = indeterminate
}

const resetUploadState = () => {
  uploadState.visible = false
  uploadState.percentage = 0
  uploadState.status = ''
  uploadState.text = ''
  uploadState.indeterminate = false
}

// 开启摄像头并开始录制
const startCamera = async () => {
  try {
    recordedVideoBlob.value = null
    const mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false  // 不需要录音
    })
    
    stream = mediaStream
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      cameraStarted.value = true
      ElMessage.success('摄像头已开启，开始录制')
      
      // 启动视频录制
      startRecording(mediaStream)
    }
  } catch (error) {
    console.error('无法访问摄像头:', error)
    ElMessage.error('无法访问摄像头，请检查权限设置')
  }
}

// 开始录制视频
const startRecording = (mediaStream) => {
  try {
    // 初始化录制器
    recordedChunks = []
    mediaRecorder = new MediaRecorder(mediaStream, {
      mimeType: 'video/webm;codecs=vp9'
    })
    
    // 监听数据可用事件
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunks.push(event.data)
        console.log(`录制中... 已录制 ${recordedChunks.length} 个片段`)
      }
    }
    
    // 监听录制停止事件
    mediaRecorder.onstop = () => {
      console.log('录制停止，总片段数:', recordedChunks.length)
    }
    
    // 开始录制
    mediaRecorder.start(1000)  // 每秒收集一次数据
    console.log('视频录制已开始')
  } catch (error) {
    console.error('录制失败:', error)
    ElMessage.error('视频录制失败：' + error.message)
  }
}

// 停止录制并获取视频 Blob
const stopRecording = () => {
  return new Promise((resolve, reject) => {
    if (!mediaRecorder) {
      resolve(null)
      return
    }
    
    mediaRecorder.onstop = () => {
      console.log('录制已停止，准备生成 Blob')
      // 生成 Blob 对象
      const blob = new Blob(recordedChunks, { type: 'video/webm' })
      console.log('生成的视频 Blob 大小:', blob.size, 'bytes')
      resolve(blob)
    }
    
    mediaRecorder.onerror = (event) => {
      console.error('录制过程中发生错误:', event.error)
      reject(event.error)
    }
    
    // 停止录制
    mediaRecorder.stop()
    console.log('正在停止录制...')
  })
}

// 停止摄像头和录制
const stopCamera = () => {
  // 停止录制
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  
  // 停止摄像头
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  cameraStarted.value = false
}

// 开始训练
const handleStartTraining = async () => {
  // 显示确认对话框
  try {
    await ElMessageBox.confirm(
      trainingTypeConfig.value.confirmMessage,
      '开始训练',
      {
        confirmButtonText: '开始',
        cancelButtonText: '取消',
        type: 'info',
        dangerouslyUseHTMLString: false
      }
    )
  } catch {
    return // 用户取消
  }
  
  starting.value = true
  try {
    const res = await startTraining(trainingForm)
    currentTraining.value = {
      ...res,
      training_type: trainingForm.training_type
    }
    ElMessage.success('训练已开始，请按照步骤操作')
    
    // 自动开启摄像头
    setTimeout(() => startCamera(), 500)
  } catch (error) {
    console.error('启动训练失败:', error)
    ElMessage.error(error.customMessage || error.response?.data?.detail || '启动训练失败')
  } finally {
    starting.value = false
  }
}

// 完成训练
const handleCompleteTraining = async () => {
  // 检查当前状态
  if (currentTraining.value?.status === 'done') {
    ElMessage.warning('该训练已完成，请勿重复提交')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要完成训练吗？\n\n' +
      '系统将进行以下检查：\n' +
      '1. 验证视频已上传\n' +
      '2. 分析训练动作\n' +
      `3. 检测 ${trainingTypeConfig.value.stepCount} 个标准步骤\n\n` +
      '⚠️ 如果预检测判定无有效动作，继续提交通常会得到 0 分。',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    completing.value = true
    
    // 1. 停止录制
    ElMessage.info('正在保存视频...')
    updateUploadState({
      percentage: 0,
      status: '',
      text: '正在整理录制视频...',
      indeterminate: true
    })
    let videoBlob = recordedVideoBlob.value
    if (!videoBlob) {
      videoBlob = await stopRecording()
      recordedVideoBlob.value = videoBlob
    }
    
    // 2. 如果有视频，先上传视频
    if (videoBlob && videoBlob.size > 0) {
      ElMessage.info('正在上传视频...')
      try {
        const uploadStartedAt = Date.now()
        uploadAbortController = new AbortController()
        updateUploadState({
          percentage: 0,
          status: '',
          text: '正在上传视频...',
          indeterminate: false
        })
        await uploadVideoFile(currentTraining.value.training_id, videoBlob, {
          signal: uploadAbortController.signal,
          onUploadProgress: (progressEvent) => {
            if (!progressEvent.total) return
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            const elapsedSeconds = Math.max((Date.now() - uploadStartedAt) / 1000, 0.1)
            const speed = formatUploadSpeed(progressEvent.loaded / elapsedSeconds)
            updateUploadState({
              percentage: percentCompleted,
              status: '',
              text: speed
                ? `正在上传视频... ${percentCompleted}% (${speed})`
                : `正在上传视频... ${percentCompleted}%`,
              indeterminate: false
            })
          }
        })
        uploadAbortController = null
        updateUploadState({
          percentage: 100,
          status: 'success',
          text: '视频上传完成，正在进行视频预检...',
          indeterminate: false
        })
        console.log('视频上传成功')
      } catch (uploadError) {
        console.error('视频上传失败:', uploadError)
        updateUploadState({
          percentage: 100,
          status: 'exception',
          text: uploadError.customMessage || uploadError.response?.data?.detail || '视频上传失败，请重试',
          indeterminate: false
        })
        ElMessage.error(uploadError.customMessage || uploadError.response?.data?.detail || '视频上传失败，请重新提交')
        return
      } finally {
        uploadAbortController = null
      }
    } else {
      console.warn('没有录制到视频，无法继续提交训练')
      updateUploadState({
        percentage: 0,
        status: 'exception',
        text: '未录制到有效视频，无法完成训练',
        indeterminate: false
      })
      ElMessage.error('未录制到有效视频，请重新录制后再提交')
      return
    }
    
    // 3. 视频预检（快速分析）
    let shouldContinue = true
    try {
      ElMessage.info('正在进行视频预检...')
      updateUploadState({
        percentage: 100,
        status: '',
        text: '视频已上传，正在进行视频预检...',
        indeterminate: true
      })
      // 调用预检测 API（稍后实现）
      const preCheckResult = await preCheckTraining(currentTraining.value.training_id)
      
      // 如果未检测到有效动作，显示警告对话框
      if (!preCheckResult.is_valid) {
        try {
          await ElMessageBox.confirm(
            '⚠️ 未检测到有效训练动作\n\n' +
            `原因：${preCheckResult.reason}\n\n` +
            '是否继续提交？\n' +
            '继续提交将获得 0 分，但会记录到训练历史中。',
            '警告',
            {
              confirmButtonText: '继续提交',
              cancelButtonText: '取消',
              type: 'warning'
            }
          )
          ElMessage.warning('已继续提交。根据当前预检测结果，本次训练大概率会得到 0 分。')
        } catch {
          // 用户选择取消
          shouldContinue = false
          ElMessage.info('已取消提交')
        }
      }
    } catch (preCheckError) {
      console.warn('预检测失败，继续提交流程:', preCheckError)
      // 预检测失败不影响提交
    }
    
    // 如果用户选择取消，不继续提交
    if (!shouldContinue) {
      completing.value = false
      return
    }
    
    // 4. 完成训练（显示加载动画）
    ElMessage.info('正在计算评分...')
    updateUploadState({
      percentage: 100,
      status: '',
      text: '正在生成测评结果，请稍候...',
      indeterminate: true
    })
    const res = await completeTraining(currentTraining.value.training_id, true)
    
    ElMessage.success('训练已完成')
    resetUploadState()
    stopCamera()
    
    // 更新当前训练状态
    currentTraining.value = res
    
    // 跳转到报告页面
    router.push(`/report/${res.training_id}`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('完成训练失败:', error)
      updateUploadState({
        percentage: uploadState.percentage || 100,
        status: 'exception',
        text: error.customMessage || error.response?.data?.detail || '训练完成失败',
        indeterminate: false
      })
      ElMessage.error(error.customMessage || error.response?.data?.detail || '完成训练失败，请稍后重试')
    }
  } finally {
    completing.value = false
  }
}

// 暂停训练
const handlePause = () => {
  if (!currentTraining.value) {
    ElMessage.warning('请先开始训练')
    return
  }
  
  if (currentTraining.value.status === 'done') {
    ElMessage.warning('训练已完成')
    return
  }
  
  if (isPaused.value) {
    // 恢复训练
    isPaused.value = false
    ElMessage.success('训练已恢复')
  } else {
    // 暂停训练
    isPaused.value = true
    ElMessage.info('训练已暂停')
  }
}

// 取消训练
const handleCancel = async () => {
  if (!currentTraining.value) {
    ElMessage.warning('没有正在进行的训练')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要取消本次训练吗？\n\n取消后训练记录将被删除，此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定取消',
        cancelButtonText: '继续训练',
        type: 'warning'
      }
    )
    
    // 停止摄像头
    if (uploadAbortController) {
      uploadAbortController.abort()
      uploadAbortController = null
    }
    stopCamera()
    
    await deleteTrainingRecord(currentTraining.value.training_id)
    
    // 清空当前训练状态
    currentTraining.value = null
    isPaused.value = false
    recordedVideoBlob.value = null
    resetUploadState()
    
    ElMessage.success('已取消训练')
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      if (isPaused.value) {
        isPaused.value = false
      }
      return
    }
    ElMessage.error(error.customMessage || error.response?.data?.detail || '取消训练失败')
  }
}

// 获取步骤图标
const getStepIcon = (status) => {
  switch (status) {
    case 'done':
      return 'Check'
    case 'doing':
      return 'Loading'
    case 'error':
      return 'Close'
    default:
      return 'Clock'
  }
}

// 获取步骤颜色
const getStepColor = (status) => {
  switch (status) {
    case 'done':
      return '#67C23A'
    case 'doing':
      return '#409EFF'
    case 'error':
      return '#F56C6C'
    default:
      return '#909399'
  }
}

// 获取状态标签类型
const getStatusType = (status) => {
  const map = {
    created: 'info',
    processing: 'warning',
    done: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const map = {
    created: '未开始',
    processing: '进行中',
    done: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

// 重置训练状态
const resetTraining = () => {
  stopCamera()
  currentTraining.value = null
  recordedVideoBlob.value = null
  resetUploadState()
  ElMessage.success('已准备就绪，可以开始新的训练')
}

// 获取步骤进度
const getStepProgress = (status) => {
  switch (status) {
    case 'done':
      return 100
    case 'doing':
      return 60
    case 'error':
      return 30
    default:
      return 0
  }
}

// 获取步骤状态样式
const getStepStatusClass = (status) => {
  const map = {
    pending: '',
    doing: 'doing',
    done: 'done',
    error: 'error'
  }
  return map[status] || ''
}

// 组件卸载时清理
onUnmounted(() => {
  if (uploadAbortController) {
    uploadAbortController.abort()
    uploadAbortController = null
  }
  resetUploadState()
  stopCamera()
  recordedVideoBlob.value = null
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style scoped>
.training-page {
  padding-bottom: 24px;
}

.training-page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 18px;
}

.training-title-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.training-eyebrow {
  margin: 0 0 10px;
  color: var(--ft-color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.title-meta-icon {
  width: 18px;
  height: 18px;
  margin-bottom: 10px;
}

.training-page-title {
  margin: 0;
  font-size: 30px;
  line-height: 1.25;
}

.training-page-subtitle {
  margin: 10px 0 0;
  max-width: 760px;
  color: var(--ft-color-text-secondary);
  line-height: 1.7;
}

.status-pill {
  margin-top: 4px;
}

.training-banner {
  margin-bottom: 20px;
}

.prep-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(260px, 360px);
  gap: 20px;
}

.prep-side-card {
  position: relative;
  height: 100%;
  padding: 24px 20px 20px;
  border: 1px solid rgba(217, 33, 33, 0.12);
  border-radius: 18px;
  background:
    radial-gradient(circle at top right, rgba(245, 158, 11, 0.14), transparent 34%),
    linear-gradient(180deg, rgba(30, 64, 175, 0.04), rgba(30, 64, 175, 0));
}

.prep-illustration {
  position: absolute;
  right: 18px;
  top: 18px;
  width: 54px;
  opacity: 0.14;
}

.prep-side-title {
  margin-bottom: 16px;
  color: var(--ft-color-danger);
  font-size: 15px;
  font-weight: 700;
}

.prep-step-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prep-step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--ft-color-border);
}

.prep-step-index {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(30, 64, 175, 0.12);
  color: var(--ft-color-primary);
  font-size: 13px;
  font-weight: 700;
}

.prep-info-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.training-type-field {
  margin-bottom: 16px;
}

.training-type-select {
  width: 100%;
}

.prep-info-item {
  padding: 16px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--ft-color-border);
}

.prep-info-label {
  display: block;
  margin-bottom: 8px;
  color: var(--ft-color-text-tertiary);
  font-size: 12px;
}

.training-runtime-head {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.runtime-stat {
  padding: 14px 16px;
  border: 1px solid var(--ft-color-border);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
}

.runtime-label {
  display: block;
  margin-bottom: 6px;
  color: var(--ft-color-text-tertiary);
  font-size: 12px;
}

.runtime-stat strong {
  color: var(--ft-color-text-primary);
  font-size: 15px;
}

.training-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  padding: 30px 20px;
  flex: 1;
}

.training-card {
  max-width: 1400px;
  margin: 0 auto;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* 训练准备区域 */
.training-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
}

.training-header h2 {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.mb-4 {
  margin-bottom: 24px;
}

/* 优化警告框 */
:deep(.el-alert) {
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px !important;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
}

:deep(.el-alert__title) {
  font-size: 18px;
  font-weight: 600;
  color: #0369a1;
}

:deep(.el-alert__content) {
  font-size: 15px;
  line-height: 1.8;
  color: #0c4a6e;
}

:deep(.el-alert ol) {
  margin: 12px 0 0 0;
  padding-left: 24px;
}

:deep(.el-alert li) {
  margin-bottom: 8px;
  line-height: 1.6;
}

/* 优化表单 */
.training-form {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #475569;
  font-size: 15px;
}

.form-label .el-icon {
  color: #3b82f6;
  font-size: 18px;
}

.form-select,
.form-timer {
  width: 100%;
}

:deep(.el-select .el-input__wrapper),
:deep(.el-input-number__wrapper) {
  border-radius: 8px;
  border: 2px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  padding: 10px 16px;
  height: 48px;
}

:deep(.el-select .el-input__wrapper:hover),
:deep(.el-input-number__wrapper:hover) {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

:deep(.el-select .el-input__wrapper.is-focus),
:deep(.el-input-number__wrapper.is-focus) {
  border-color: #2563eb;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.25);
}

:deep(.el-input-number__wrapper) {
  display: flex;
  align-items: center;
}

:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  border-radius: 0 6px 6px 0 !important;
  background: #f1f5f9 !important;
  border: none !important;
  width: 32px !important;
}

:deep(.el-input-number__decrease:hover),
:deep(.el-input-number__increase:hover) {
  background: #e2e8f0 !important;
}

.duration-hint {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.form-actions {
  display: flex;
  justify-content: center;
  padding-top: 8px;
}

.start-training-btn {
  padding: 14px 48px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.start-training-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}

.start-training-btn:active {
  transform: translateY(0);
}

.start-training-btn .el-icon {
  margin-right: 8px;
  font-size: 20px;
}

/* 训练内容区域 */
.training-content {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.video-card {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  height: 100%;
}

.video-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #cbd5e1;
}

.video-card .card-header span {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.video-container {
  position: relative;
  background: #000;
  border-radius: 0;
  overflow: hidden;
  aspect-ratio: 16/9;
  margin-bottom: 0;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  transition: all 0.3s ease;
}

.video-overlay:hover {
  background: rgba(0, 0, 0, 0.5);
}

/* 暂停状态遮罩 */
.paused-overlay {
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
}

.paused-content {
  text-align: center;
  color: #fff;
  animation: fadeIn 0.5s ease-in-out;
}

.paused-content h3 {
  font-size: 28px;
  margin: 16px 0 8px;
  color: #F59E0B;
}

.paused-content p {
  font-size: 16px;
  opacity: 0.9;
}

.video-controls {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 20px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.video-controls .el-button {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.video-controls .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.upload-status-box {
  padding: 16px 20px 20px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.upload-status-box p {
  margin: 10px 0 0;
  color: #475569;
  font-size: 14px;
  text-align: center;
}

.camera-tip {
  display: flex;
  gap: 8px;
  padding: 14px 18px 18px;
  color: var(--ft-color-text-tertiary);
  font-size: 13px;
  line-height: 1.7;
  background: #fff;
  border-top: 1px dashed var(--ft-color-border);
}

/* 步骤卡片优化 */
.steps-card {
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.steps-card .card-header {
  padding: 16px 20px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-bottom: 1px solid #fcd34d;
}

.steps-card .card-header span {
  font-size: 18px;
  font-weight: 600;
  color: #92400e;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
}

.step-item {
  padding: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border-radius: 10px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.step-item:hover {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-color: #3b82f6;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.step-item.doing {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #2563eb;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.2);
}

.step-item.done {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  border-color: #16a34a;
  box-shadow: 0 2px 8px rgba(22, 163, 74, 0.15);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: #fff;
  border-radius: 50%;
  font-size: 14px;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.step-item.doing .step-number {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.4);
}

.step-item.done .step-number {
  background: linear-gradient(135deg, #16a34a 0%, #059669 100%);
  box-shadow: 0 2px 12px rgba(22, 163, 74, 0.4);
}

.step-name {
  flex: 1;
  font-weight: 600;
  color: #1f2937;
  font-size: 16px;
}

.step-status {
  font-size: 20px;
  transition: all 0.3s ease;
}

.step-status.doing {
  color: #3b82f6;
  animation: pulse 1.5s infinite;
  filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.6));
}

.step-status.done {
  color: #16a34a;
  filter: drop-shadow(0 0 8px rgba(22, 163, 74, 0.6));
}

.step-status.error {
  color: #dc2626;
  filter: drop-shadow(0 0 8px rgba(220, 38, 38, 0.6));
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

/* 进度条优化 */
:deep(.el-progress__bar) {
  border-radius: 4px;
  overflow: hidden;
}

:deep(.el-progress__text) {
  font-weight: 600;
}

.feedback-box {
  margin-top: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 8px;
  border-left: 4px solid #f59e0b;
}

.step-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin: 0 20px 20px;
  color: var(--ft-color-text-tertiary);
  font-size: 12px;
}

.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}

.legend-dot.pending {
  background: var(--ft-color-text-tertiary);
}

.legend-dot.doing {
  background: var(--ft-color-primary);
}

.legend-dot.done {
  background: var(--ft-color-success);
}

.training-card {
  max-width: none;
  margin: 0;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: var(--ft-shadow-sm);
}

.training-header {
  border-bottom: 1px solid var(--ft-color-border);
}

.training-header h2,
.video-card .card-header span,
.step-name {
  color: var(--ft-color-text-primary);
}

::deep(.el-alert) {
  background: #f8fbff;
  border: 1px solid rgba(30, 64, 175, 0.16);
}

::deep(.el-alert__title) {
  color: var(--ft-color-primary);
}

::deep(.el-alert__content) {
  color: var(--ft-color-text-secondary);
}

.training-form {
  background:
    linear-gradient(180deg, rgba(30, 64, 175, 0.03), rgba(30, 64, 175, 0)),
    #f8fafc;
  border-color: var(--ft-color-border);
}

.form-label {
  color: var(--ft-color-text-secondary);
}

.form-label .el-icon {
  color: var(--ft-color-primary);
}

::deep(.el-select .el-input__wrapper),
::deep(.el-input-number__wrapper) {
  border: 1px solid var(--ft-color-border);
  box-shadow: none;
}

::deep(.el-select .el-input__wrapper:hover),
::deep(.el-input-number__wrapper:hover),
::deep(.el-select .el-input__wrapper.is-focus),
::deep(.el-input-number__wrapper.is-focus) {
  border-color: var(--ft-color-primary);
  box-shadow: none;
}

.duration-hint,
.upload-status-box p {
  color: var(--ft-color-text-tertiary);
}

.start-training-btn {
  background: var(--ft-color-primary);
  box-shadow: none;
}

.start-training-btn:hover {
  box-shadow: var(--ft-shadow-sm);
}

.video-card,
.steps-card {
  box-shadow: none;
}

.video-card .card-header {
  background:
    linear-gradient(180deg, rgba(30, 64, 175, 0.04), rgba(30, 64, 175, 0)),
    #f8fafc;
  border-bottom: 1px solid var(--ft-color-border);
}

.video-container {
  background: var(--ft-color-video);
}

.video-overlay,
.paused-overlay {
  backdrop-filter: none;
}

.video-controls,
.upload-status-box {
  border-top: 1px solid var(--ft-color-border);
}

.steps-card .card-header {
  background:
    linear-gradient(180deg, rgba(245, 158, 11, 0.08), rgba(245, 158, 11, 0)),
    #fff8f1;
  border-bottom: 1px solid rgba(217, 119, 6, 0.16);
}

.steps-card .card-header span {
  color: var(--ft-color-warning);
}

.step-item {
  background: #fff;
  border: 1px solid var(--ft-color-border);
  box-shadow: none;
}

.step-item:hover {
  background: #fff;
  border-color: var(--ft-color-primary);
  transform: translateX(2px);
  box-shadow: none;
}

.step-item.doing {
  background: rgba(30, 64, 175, 0.06);
  border-color: var(--ft-color-primary);
  box-shadow: none;
}

.step-item.done {
  background: rgba(16, 185, 129, 0.08);
  border-color: var(--ft-color-success);
  box-shadow: none;
}

.step-number {
  background: var(--ft-color-text-tertiary);
  box-shadow: none;
}

.step-item.doing .step-number {
  background: var(--ft-color-primary);
}

.step-item.done .step-number {
  background: var(--ft-color-success);
}

.step-status.doing {
  color: var(--ft-color-primary);
  filter: none;
}

.step-status.done {
  color: var(--ft-color-success);
  filter: none;
}

.step-status.error {
  color: var(--ft-color-danger);
  filter: none;
}

.feedback-box {
  background: #fff8f1;
  border-left-color: var(--ft-color-warning);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .prep-layout,
  .training-runtime-head,
  .prep-info-strip {
    grid-template-columns: 1fr;
  }

  .main-content {
    padding: 20px 15px;
  }
  
  .training-header h2 {
    font-size: 24px;
  }
  
  .form-row {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 15px 10px;
  }
  
  .training-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .training-header h2 {
    font-size: 22px;
  }
  
  .video-controls {
    flex-wrap: wrap;
  }
  
  .video-controls .el-button {
    flex: 1;
    min-width: 120px;
  }

  .camera-tip {
    flex-direction: column;
  }
  
  .step-item {
    padding: 12px;
  }
  
  .step-name {
    font-size: 14px;
  }
  
  .training-form {
    padding: 16px;
  }
  
  .start-training-btn {
    width: 100%;
    padding: 14px 24px;
    font-size: 16px;
  }

  .training-page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .training-page-title {
    font-size: 24px;
  }
}
</style>
