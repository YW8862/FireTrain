<template>
  <div class="training-container">
    <!-- 顶部导航栏 - 训练期间隐藏 -->
    <NavBar :visible="!currentTraining" />

    <div class="main-content">
      <el-card class="training-card">
      <!-- 未开始训练 -->
      <div v-if="!currentTraining">
        <div class="training-header">
          <h2>📋 训练准备</h2>
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
          <p>请按照标准流程完成灭火器操作训练：</p>
          <ol>
            <li>准备阶段：做好个人防护，确认逃生路线</li>
            <li>提起灭火器：用腿部力量提起灭火器</li>
            <li>拔保险销：握住拉环用力拔出</li>
            <li>握喷管：双手稳固握持喷管</li>
            <li>瞄准火源：对准火焰根部，保持 2-3 米距离</li>
            <li>压把手：均匀用力下压，左右扫射</li>
          </ol>
        </el-alert>

        <el-form :model="trainingForm" class="training-form">
          <div class="form-row">
            <div class="form-item">
              <label class="form-label">
                <el-icon><Document /></el-icon>
                训练类型
              </label>
              <el-select v-model="trainingForm.training_type" placeholder="请选择训练类型" class="form-select">
                <el-option label="🔥 灭火器操作" value="fire_extinguisher" />
                <el-option label="📋 其他训练" value="other" />
              </el-select>
            </div>
            
            <div class="form-item">
              <label class="form-label">
                <el-icon><Timer /></el-icon>
                预计时长
              </label>
              <el-input-number 
                v-model="trainingForm.duration_seconds" 
                :min="60" 
                :max="300" 
                :step="10"
                class="form-timer"
                controls-position="right"
              >
                <template #prefix>
                  <el-icon><Clock /></el-icon>
                </template>
              </el-input-number>
              <span class="duration-hint">60-300 秒</span>
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

      <!-- 训练中 -->
      <div v-else class="training-content">
        <el-row :gutter="20">
          <!-- 左侧：视频预览区 -->
          <el-col :span="14">
            <el-card class="video-card">
              <template #header>
                <div class="card-header">
                  <span>📹 视频预览区</span>
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
                  type="success" 
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
            </el-card>
          </el-col>

          <!-- 右侧：训练步骤 -->
          <el-col :span="10">
            <el-card class="steps-card">
              <template #header>
                <span>📋 训练步骤</span>
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
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoCamera, Document, Timer, Clock, VideoPlay, VideoPause } from '@element-plus/icons-vue'
import { startTraining, completeTraining } from '@/api/training'
import { useUserStore } from '@/store/user'
import NavBar from '@/components/NavBar.vue'

const router = useRouter()
const userStore = useUserStore()

// 状态
const starting = ref(false)
const completing = ref(false)
const cameraStarted = ref(false)
const countdown = ref(0)
const videoRef = ref(null)
let stream = null
let countdownTimer = null
const realtimeFeedback = ref('')
const isPaused = ref(false) // 暂停状态

// 训练表单
const trainingForm = reactive({
  training_type: 'fire_extinguisher',
  duration_seconds: 120
})

// 当前训练
const currentTraining = ref(null)

// 步骤状态
const steps = reactive([
  { name: '准备阶段', status: 'pending' },
  { name: '提灭火器', status: 'pending' },
  { name: '拔保险销', status: 'pending' },
  { name: '握喷管', status: 'pending' },
  { name: '瞄准火源', status: 'pending' },
  { name: '压把手', status: 'pending' }
])

// 开启摄像头
const startCamera = async () => {
  try {
    const mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 }
      }
    })
    
    stream = mediaStream
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      cameraStarted.value = true
      ElMessage.success('摄像头已开启')
      
      // TODO: 这里可以添加 AI 分析逻辑
      // 实时分析视频帧，更新步骤状态
    }
  } catch (error) {
    console.error('无法访问摄像头:', error)
    ElMessage.error('无法访问摄像头，请检查权限设置')
  }
}

// 停止摄像头
const stopCamera = () => {
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
      '准备好开始训练了吗？\n\n请确保：\n• 已做好个人防护\n• 确认逃生路线畅通\n• 灭火器在有效期内',
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
    currentTraining.value = res
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
    await ElMessageBox.confirm('确定要完成训练吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    completing.value = true
    const res = await completeTraining(currentTraining.value.training_id)
    
    ElMessage.success('训练已完成')
    stopCamera()
    
    // 更新当前训练状态
    currentTraining.value = res
    
    // 跳转到报告页面
    router.push(`/report/${res.training_id}`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('完成训练失败:', error)
      // 如果是状态错误，给出更友好的提示
      if (error.response?.data?.detail?.includes('当前状态')) {
        ElMessage.error('训练状态异常，请刷新页面后重试')
      } else {
        ElMessage.error(error.response?.data?.detail || '完成训练失败，请稍后重试')
      }
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
    stopCamera()
    
    // TODO: 调用后端 API 删除训练记录
    // await deleteTraining(currentTraining.value.training_id)
    
    // 清空当前训练状态
    currentTraining.value = null
    isPaused.value = false
    
    ElMessage.success('已取消训练')
  } catch {
    // 用户取消操作，继续训练
    if (isPaused.value) {
      isPaused.value = false
    }
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
  ElMessage.success('已准备就绪，可以开始新的训练')
}

// 组件卸载时清理
onUnmounted(() => {
  stopCamera()
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})

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
  stopCamera()
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style scoped>
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

/* 响应式设计 */
@media (max-width: 1024px) {
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
}
</style>
